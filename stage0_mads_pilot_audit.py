#!/usr/bin/env python3
"""Read-only structural audit for MaDS selected decision traces.

The script never writes files. It reports what the released decision records
contain and identifies commit-like actions for manual causal annotation.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
from typing import Any, Iterable


COMMIT_PATTERNS = {
    "payment": ("立即支付", "付款", "支付"),
    "send": ("发送", "send"),
    "purchase_entry": ("立即购买", "购买按钮", "buy now"),
    "delete_or_clear": ("删除", "清除", "delete", "clear"),
    "publish_or_submit": ("发布", "提交", "授权", "publish", "submit", "authorize"),
}

VERIFY_TERMS = ("检查", "核对", "确认", "验证", "verify", "check", "confirm")
RECOVERY_TERMS = ("恢复", "重试", "返回", "重新", "失败后", "recover", "retry", "rollback")
VALIDITY_KEYS = {
    "valid_until",
    "expires_at",
    "expiry",
    "invalidation_condition",
    "validity_condition",
    "staleness",
}
VERIFICATION_KEYS = {"verification", "verify", "probe", "evidence_check"}
RECOVERY_KEYS = {"recovery", "rollback", "fallback", "compensation"}


def iter_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from iter_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_keys(child)


def flatten_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(flatten_text(child) for child in value.values())
    if isinstance(value, list):
        return " ".join(flatten_text(child) for child in value)
    return str(value or "")


def classify_commit(text: str) -> list[str]:
    lowered = text.lower()
    return [
        name
        for name, patterns in COMMIT_PATTERNS.items()
        if any(pattern.lower() in lowered for pattern in patterns)
    ]


def case_name(path: pathlib.Path) -> str:
    for part in path.parts:
        if re.fullmatch(r"case\d+", part):
            return part
    return "unknown_case"


def load_step_result(path: pathlib.Path, step_id: int | None) -> dict[str, Any]:
    if step_id is None:
        return {}
    case_dir = next((parent for parent in path.parents if re.fullmatch(r"case\d+", parent.name)), None)
    if case_dir is None:
        return {}
    step_path = case_dir / f"step_{step_id:02d}.json"
    if not step_path.exists():
        return {}
    return json.loads(step_path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=pathlib.Path("external/MaDS/Data/execution_traces/01_ours_mads"),
    )
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    paths = sorted(args.root.rglob("*_analysis.json"))
    records = [(path, json.loads(path.read_text(encoding="utf-8"))) for path in paths]

    key_counts: collections.Counter[str] = collections.Counter()
    commit_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    record_counts: collections.Counter[str] = collections.Counter()

    for path, record in records:
        memory = record.get("step_experiences") or {}
        memory_keys = set(iter_keys(memory))
        key_counts.update(memory_keys)
        memory_text = flatten_text(memory)
        subtask = str(record.get("current_subtask") or "")
        categories = classify_commit(subtask)

        experiences = memory.get("experiences") or []
        facts = memory.get("facts") or []
        model_response = str(record.get("model_response") or "")
        action = (record.get("parsed_action") or {}).get("action")
        step_result = load_step_result(path, record.get("step_id"))

        record_counts["total"] += 1
        record_counts["has_experiences"] += bool(experiences)
        record_counts["has_facts"] += bool(facts)
        record_counts["has_precondition_field"] += "preconditions" in memory_keys
        record_counts["has_provenance_field"] += bool({"source", "source_task_id"} & memory_keys)
        record_counts["has_validity_field"] += bool(VALIDITY_KEYS & memory_keys)
        record_counts["has_verification_field"] += bool(VERIFICATION_KEYS & memory_keys)
        record_counts["has_recovery_field"] += bool(RECOVERY_KEYS & memory_keys)
        record_counts["verification_term_in_memory_text"] += any(term in memory_text for term in VERIFY_TERMS)
        record_counts["recovery_term_in_memory_text"] += any(term in memory_text for term in RECOVERY_TERMS)
        record_counts["recorded_step_success"] += step_result.get("success") is True
        record_counts["recorded_step_failure"] += step_result.get("success") is False
        record_counts["recorded_step_outcome_missing"] += step_result.get("success") is None

        if step_result.get("success") is False:
            failure_rows.append(
                {
                    "case": case_name(path),
                    "step_id": record.get("step_id"),
                    "subtask": subtask,
                    "action": action,
                    "experience_count": len(experiences),
                    "fact_count": len(facts),
                    "verifier_reason": str(step_result.get("reason") or ""),
                }
            )

        if not categories:
            continue

        verifier_reason = str(step_result.get("reason") or "")
        commit_rows.append(
            {
                "case": case_name(path),
                "step_id": record.get("step_id"),
                "categories": categories,
                "subtask": subtask,
                "action": action,
                "direct_action_only": bool(action) and model_response.strip().lower().startswith(str(action).lower()),
                "experience_count": len(experiences),
                "fact_count": len(facts),
                "has_precondition_field": "preconditions" in memory_keys,
                "has_provenance_field": bool({"source", "source_task_id"} & memory_keys),
                "has_validity_field": bool(VALIDITY_KEYS & memory_keys),
                "has_verification_field": bool(VERIFICATION_KEYS & memory_keys),
                "has_recovery_field": bool(RECOVERY_KEYS & memory_keys),
                "model_response_mentions_verification": any(term in model_response for term in VERIFY_TERMS),
                "model_response_mentions_recovery": any(term in model_response for term in RECOVERY_TERMS),
                "recorded_step_success": step_result.get("success"),
                "verifier_reason": verifier_reason,
            }
        )

    output = {
        "root": str(args.root),
        "record_counts": dict(record_counts),
        "commit_like_count": len(commit_rows),
        "commit_like_cases": sorted({row["case"] for row in commit_rows}),
        "commit_category_counts": dict(
            collections.Counter(category for row in commit_rows for category in row["categories"])
        ),
        "memory_key_document_frequency": dict(key_counts.most_common()),
        "commit_rows": commit_rows,
        "failure_rows": failure_rows,
        "interpretation_limits": [
            "Selected traces are not a random natural-failure sample.",
            "Structural absence of a field does not prove the model ignored the concept in latent reasoning.",
            "Recorded step success is a local verifier outcome, not proof of correct long-horizon semantics.",
            "No causal claim is allowed without paired memory intervention under a frozen policy.",
        ],
    }
    if args.summary_only:
        output.pop("memory_key_document_frequency")
        output.pop("commit_rows")
        output.pop("failure_rows")
    print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
