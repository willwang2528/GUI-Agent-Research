#!/usr/bin/env python3
"""Audit availability, not truth, in frozen OSWorld 2.0 detail pages.

The audit has a fixed 8-task x 6-hosted-config frame.  A unit is available
when it contains either a structurally valid replay with a consistent page
identity or the explicit page-level marker ``No step data available``.  These
states are intentionally mutually exclusive.

Passing this audit does not establish outcome truth, evaluator reproducibility,
UACF-D status, or successful environment replay.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any


EXPECTED_TASK_IDS = ("009", "020", "024", "029", "050", "066", "073", "083")
HOSTED_CONFIG_FILENAMES = (
    "MiniMax-M3",
    "claude-opus-4-7",
    "claude-sonnet-4-6-max",
    "claude-sonnet-4-6-medium",
    "gpt-5.5",
    "qwen37",
)
EXPECTED_FILENAMES = tuple(
    f"{task_id}__{config}.html"
    for task_id in EXPECTED_TASK_IDS
    for config in HOSTED_CONFIG_FILENAMES
)
EXPECTED_FILENAME_SET = frozenset(EXPECTED_FILENAMES)

REPLAY_RE = re.compile(
    r'<script type="application/json" id="trajectory-replay-data">(.*?)</script>',
    re.DOTALL,
)
RAW_RE = re.compile(
    r'<pre class="step-action-content raw-json collapsed" data-raw-json="true">(.*?)</pre>',
    re.DOTALL,
)
ROOT_RE = re.compile(
    r'id="trajectory-replay-root".*?data-task-id="([^"]+)".*?'
    r'data-model-name="([^"]+)".*?data-trajectory-id="([^"]+)"',
    re.DOTALL,
)
NO_STEP_RE = re.compile(r"\bNo step data available\b")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hash(files: list[Path], root: Path) -> str:
    """Hash ``relative-path NUL lowercase-file-sha256 LF`` in UTF-8 byte order."""

    digest = hashlib.sha256()
    for path in sorted(
        files,
        key=lambda item: item.relative_to(root).as_posix().encode("utf-8"),
    ):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def expected_identity(filename: str) -> tuple[str, str] | None:
    if filename not in EXPECTED_FILENAME_SET:
        return None
    task_id, config_and_suffix = filename.split("__", maxsplit=1)
    return task_id, config_and_suffix.removesuffix(".html")


def _parse_replay(
    text: str,
) -> tuple[bool, dict[str, Any], list[dict[str, Any]], str | None]:
    replay_match = REPLAY_RE.search(text)
    if replay_match is None:
        return False, {}, [], "missing embedded replay JSON"

    try:
        payload = json.loads(html.unescape(replay_match.group(1)))
    except json.JSONDecodeError as error:
        return True, {}, [], f"invalid embedded replay JSON: {error}"

    if not isinstance(payload, dict):
        return True, {}, [], "embedded replay JSON is not an object"
    steps = payload.get("steps")
    if not isinstance(steps, list) or not all(isinstance(step, dict) for step in steps):
        return True, payload, [], "replay steps is not a list of objects"
    if not steps:
        return True, payload, [], "replay steps is empty"
    if payload.get("total_steps") != len(steps):
        return True, payload, steps, "replay total_steps does not equal steps length"
    return True, payload, steps, None


def audit_unit(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    identity_expected = expected_identity(path.name)
    root_match = ROOT_RE.search(text)
    root_identity = list(root_match.groups()) if root_match else None
    replay_script_present, replay, steps, replay_error = _parse_replay(text)
    replay_json_valid = replay_error is None
    no_step_marker_present = NO_STEP_RE.search(text) is not None

    root_identity_consistent = False
    if identity_expected is not None and root_identity is not None:
        task_id, model_slug = identity_expected
        root_identity_consistent = root_identity == [task_id, model_slug, task_id]

    # The frozen replay payloads expose only ``steps`` and ``total_steps``.
    # Therefore the strongest reliable identity check is a consistent replay
    # root bound to the expected filename plus total_steps consistency.
    replay_identity_fields = sorted(
        key
        for key in ("task_id", "model_name", "trajectory_id")
        if key in replay
    )
    replay_available = (
        replay_json_valid
        and root_identity_consistent
        and not no_step_marker_present
    )
    explicit_no_step = (
        no_step_marker_present
        and not replay_script_present
        and root_identity is None
    )

    if replay_available:
        availability_state = "REPLAY_VALID"
    elif explicit_no_step:
        availability_state = "EXPLICIT_NO_STEP"
    else:
        availability_state = "INVALID_OR_AMBIGUOUS"

    screenshot_url_count = sum(bool(step.get("screenshot_url")) for step in steps)
    timestamp_count = sum(bool(step.get("timestamp")) for step in steps)
    labeled_action_count = sum(bool(step.get("label")) for step in steps)

    raw_blocks = RAW_RE.findall(text)
    raw_valid = 0
    for raw in raw_blocks:
        try:
            json.loads(html.unescape(raw))
            raw_valid += 1
        except json.JSONDecodeError:
            pass

    return {
        "file": path.name,
        "sha256": sha256_file(path),
        "expected_unit": identity_expected is not None,
        "expected_identity": list(identity_expected) if identity_expected else None,
        "root_identity": root_identity,
        "root_identity_consistent": root_identity_consistent,
        "replay_script_present": replay_script_present,
        "replay_json_valid": replay_json_valid,
        "replay_error": replay_error,
        "replay_identity_fields_present": replay_identity_fields,
        "no_step_marker_present": no_step_marker_present,
        "explicit_no_step": explicit_no_step,
        "replay_available": replay_available,
        "availability_state": availability_state,
        "unit_availability_valid": availability_state
        in {"REPLAY_VALID", "EXPLICIT_NO_STEP"},
        "step_count": len(steps),
        "screenshot_url_count": screenshot_url_count,
        "timestamp_count": timestamp_count,
        "labeled_action_count": labeled_action_count,
        "raw_block_count": len(raw_blocks),
        "raw_json_valid_count": raw_valid,
    }


def audit_directory(detail_dir: Path) -> dict[str, object]:
    files = sorted(
        detail_dir.glob("*.html"),
        key=lambda path: path.name.encode("utf-8"),
    )
    actual_names = {path.name for path in files}
    missing_files = sorted(EXPECTED_FILENAME_SET - actual_names)
    unexpected_files = sorted(actual_names - EXPECTED_FILENAME_SET)
    units = [audit_unit(path) for path in files]
    expected_units = [unit for unit in units if unit["expected_unit"]]

    replay_available_files = sum(
        bool(unit["replay_available"]) for unit in expected_units
    )
    explicit_no_step_files = sum(
        bool(unit["explicit_no_step"]) for unit in expected_units
    )
    if replay_available_files == len(EXPECTED_FILENAMES):
        replay_availability_status = "COMPLETE"
    elif replay_available_files == 0:
        replay_availability_status = "NONE"
    else:
        replay_availability_status = "PARTIAL"

    exact_expected_frame = not missing_files and not unexpected_files
    all_expected_units_available = (
        len(expected_units) == len(EXPECTED_FILENAMES)
        and all(bool(unit["unit_availability_valid"]) for unit in expected_units)
    )
    audit_complete = exact_expected_frame and all_expected_units_available

    summary = {
        "audit_complete": audit_complete,
        "expected_file_count": len(EXPECTED_FILENAMES),
        "file_count": len(files),
        "expected_files_present": len(EXPECTED_FILENAME_SET & actual_names),
        "missing_files": missing_files,
        "unexpected_files": unexpected_files,
        "detail_tree_sha256": tree_hash(files, detail_dir),
        "replay_availability_status": replay_availability_status,
        "replay_available_files": replay_available_files,
        "replay_json_valid_files": sum(
            bool(unit["replay_json_valid"]) for unit in expected_units
        ),
        "explicit_no_step_files": explicit_no_step_files,
        "invalid_or_ambiguous_files": sum(
            unit["availability_state"] == "INVALID_OR_AMBIGUOUS"
            for unit in expected_units
        ),
        "replay_units_with_consistent_root_binding": sum(
            bool(unit["replay_available"]) for unit in expected_units
        ),
        "replay_payloads_with_identity_fields": sum(
            bool(unit["replay_identity_fields_present"]) for unit in expected_units
        ),
        "files_with_all_step_screenshot_urls": sum(
            int(unit["step_count"]) > 0
            and unit["screenshot_url_count"] == unit["step_count"]
            for unit in expected_units
        ),
        "files_with_all_step_timestamps": sum(
            int(unit["step_count"]) > 0
            and unit["timestamp_count"] == unit["step_count"]
            for unit in expected_units
        ),
        "files_with_all_steps_labeled": sum(
            int(unit["step_count"]) > 0
            and unit["labeled_action_count"] == unit["step_count"]
            for unit in expected_units
        ),
        "total_steps": sum(int(unit["step_count"]) for unit in expected_units),
        "total_raw_blocks": sum(
            int(unit["raw_block_count"]) for unit in expected_units
        ),
        "total_valid_raw_json_blocks": sum(
            int(unit["raw_json_valid_count"]) for unit in expected_units
        ),
    }
    return {
        "audit_protocol": "stage0f-detail-availability-v1",
        "expected_frame": {
            "task_ids": list(EXPECTED_TASK_IDS),
            "hosted_config_filenames": list(HOSTED_CONFIG_FILENAMES),
            "filenames": list(EXPECTED_FILENAMES),
        },
        "summary": summary,
        "identity_check_scope": (
            "Replay payloads contain only steps and total_steps. Identity is checked "
            "by binding each valid replay page root to the fixed filename and by "
            "requiring root trajectory_id == task_id and total_steps == len(steps)."
        ),
        "claim_ceiling": (
            "This report establishes local snapshot and field availability only. "
            "It does not establish outcome truth, UACF-D status, evaluator "
            "reproducibility, causal mechanism, or successful environment replay."
        ),
        "units": units,
    }


def exit_code(report: dict[str, object], require_all_replay: bool) -> int:
    summary = report["summary"]
    assert isinstance(summary, dict)
    if not summary["audit_complete"]:
        return 1
    if require_all_replay and summary["replay_availability_status"] != "COMPLETE":
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("detail_dir", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the JSON report to this path instead of stdout.",
    )
    parser.add_argument(
        "--require-all-replay",
        action="store_true",
        help="Fail unless all 48 units expose valid replay data.",
    )
    args = parser.parse_args()

    report = audit_directory(args.detail_dir)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return exit_code(report, args.require_all_replay)


if __name__ == "__main__":
    raise SystemExit(main())
