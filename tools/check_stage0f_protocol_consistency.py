#!/usr/bin/env python3
"""Fail-closed textual consistency checks for the Stage 0F protocol stack.

This checker does not establish scientific validity.  It only detects known
cross-document drift and Markdown regressions before a measurement-stack hash
can be frozen.
"""

from __future__ import annotations

import argparse
from pathlib import Path


CORE_FILES = (
    Path("stage0f_osworld2_natural_burden_preregistration.md"),
    Path("stage0f_step1_decision_card.md"),
    Path("stage0f_step1_5_replay_identification_card.md"),
    Path("idea-stage/docs/research_contract.md"),
)

BANNED_TOKENS = (
    r"\[",
    r"\]",
    "NARROW_SCOPE_STEP2_PROTOCOL_ONLY",
    "SOURCE_UNIDENTIFIABLE",
    "P ∈ {absent, flat, dependency-aware}",
    "P ∈ {standard, repair-enabled}",
    "candidate_location_id",
    "a0_event_id",
)

REQUIRED_BY_FILE = {
    CORE_FILES[0]: (
        "boundary_location_id",
        "adjudicated_event_id",
        "BLOCK_A0_BARRIER_FROZEN",
        "omission_interval",
        "SOURCE_UNKNOWN",
        "INVALID_SOURCE_MEASUREMENT",
        "identity_no_propagation",
        "dependency_graph_propagation",
        "simultaneous",
    ),
    CORE_FILES[1]: (
        "U_B_tasks_global",
        "U_C_interface_tasks_global",
        "U_env_tasks",
        "Z_D",
        "Z_env_structure",
        "SOURCE_UNKNOWN",
        "INVALID_SOURCE_MEASUREMENT",
        "BROAD_SCOPE_REJECTED_NARROW_HYPOTHESIS_ONLY",
    ),
    CORE_FILES[2]: (
        "boundary_location_id",
        "adjudicated_event_id",
        "BLOCKED",
        "UNIDENTIFIABLE",
        "identity_no_propagation",
        "dependency_graph_propagation",
        "BROAD_SCOPE_REJECTED_NARROW_HYPOTHESIS_ONLY",
    ),
    CORE_FILES[3]: (
        "SOURCE_UNKNOWN",
        "INVALID_SOURCE_MEASUREMENT",
        "identity_no_propagation",
        "dependency_graph_propagation",
        "simultaneous",
        "source provenance",
    ),
}


def check(root: Path) -> list[str]:
    errors: list[str] = []
    texts: dict[Path, str] = {}
    for relative in CORE_FILES:
        path = root / relative
        if not path.is_file():
            errors.append(f"{relative}: missing core protocol file")
            continue
        text = path.read_text(encoding="utf-8")
        texts[relative] = text

        fence_count = sum(line.startswith("```") for line in text.splitlines())
        if fence_count % 2:
            errors.append(f"{relative}: unpaired fenced-code delimiter count={fence_count}")

        for token in BANNED_TOKENS:
            if token in text:
                errors.append(f"{relative}: banned legacy token {token!r}")

        for token in REQUIRED_BY_FILE[relative]:
            if token not in text:
                errors.append(f"{relative}: required protocol token missing {token!r}")

    replay_text = texts.get(CORE_FILES[2], "")
    blocked_position = replay_text.find(
        "| `A_reconstructed_freeze = FAIL`"
    )
    unknown_position = replay_text.find(
        "| 没有任何 `FAIL`，但 `A_reconstructed_freeze = UNIDENTIFIABLE`"
    )
    if min(blocked_position, unknown_position) < 0:
        errors.append(f"{CORE_FILES[2]}: Step 1.5 hard-fail/unknown rows not found")
    elif blocked_position > unknown_position:
        errors.append(f"{CORE_FILES[2]}: hard FAIL must precede unknown")

    decision_text = texts.get(CORE_FILES[1], "")
    if "MEASUREMENT STACK NOT FROZEN" not in decision_text:
        errors.append(f"{CORE_FILES[1]}: provisional stack status missing")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()

    errors = check(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    print("PASS stage0f protocol textual consistency")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
