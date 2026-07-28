from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "tools" / "audit_stage0f_detail_pages.py"
)
SPEC = importlib.util.spec_from_file_location("audit_stage0f_detail_pages", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def replay_html(
    task_id: str,
    model_slug: str,
    *,
    root_task_id: str | None = None,
    extra_body: str = "",
) -> str:
    root_task = root_task_id or task_id
    payload = {
        "steps": [
            {
                "index": 1,
                "label": "Observe",
                "category": "screenshot",
                "timestamp": "20260101@000000000000",
                "screenshot_url": "https://example.invalid/step.png",
            }
        ],
        "total_steps": 1,
    }
    return (
        '<div id="trajectory-replay-root" '
        f'data-task-id="{root_task}" '
        f'data-model-name="{model_slug}" '
        f'data-trajectory-id="{root_task}"></div>'
        '<script type="application/json" id="trajectory-replay-data">'
        f"{json.dumps(payload)}</script>{extra_body}"
    )


def write_complete_frame(root: Path) -> None:
    for filename in MODULE.EXPECTED_FILENAMES:
        task_id, model_filename = filename.split("__", maxsplit=1)
        model_slug = model_filename.removesuffix(".html")
        if filename == "050__MiniMax-M3.html":
            body = '<div class="no-steps">No step data available</div>'
        else:
            body = replay_html(task_id, model_slug)
        (root / filename).write_text(body, encoding="utf-8")


class AuditStage0fDetailPagesTests(unittest.TestCase):
    def test_complete_frame_accepts_one_explicit_no_step_as_partial_replay(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            write_complete_frame(root)

            report = MODULE.audit_directory(root)
            summary = report["summary"]

            self.assertTrue(summary["audit_complete"])
            self.assertEqual(summary["file_count"], 48)
            self.assertEqual(summary["replay_available_files"], 47)
            self.assertEqual(summary["explicit_no_step_files"], 1)
            self.assertEqual(summary["invalid_or_ambiguous_files"], 0)
            self.assertEqual(summary["replay_availability_status"], "PARTIAL")
            self.assertEqual(MODULE.exit_code(report, require_all_replay=False), 0)
            self.assertEqual(MODULE.exit_code(report, require_all_replay=True), 1)

    def test_missing_expected_file_fails_frame_completeness(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            write_complete_frame(root)
            missing = root / "009__MiniMax-M3.html"
            missing.unlink()

            report = MODULE.audit_directory(root)
            summary = report["summary"]

            self.assertFalse(summary["audit_complete"])
            self.assertEqual(summary["missing_files"], [missing.name])
            self.assertEqual(MODULE.exit_code(report, require_all_replay=False), 1)

    def test_replay_and_no_step_marker_are_rejected_as_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            write_complete_frame(root)
            target = root / "009__MiniMax-M3.html"
            target.write_text(
                replay_html(
                    "009",
                    "MiniMax-M3",
                    extra_body="<div>No step data available</div>",
                ),
                encoding="utf-8",
            )

            report = MODULE.audit_directory(root)
            unit = next(
                item for item in report["units"] if item["file"] == target.name
            )

            self.assertTrue(unit["replay_json_valid"])
            self.assertTrue(unit["no_step_marker_present"])
            self.assertFalse(unit["replay_available"])
            self.assertFalse(unit["explicit_no_step"])
            self.assertEqual(unit["availability_state"], "INVALID_OR_AMBIGUOUS")
            self.assertFalse(report["summary"]["audit_complete"])

    def test_replay_root_must_match_fixed_filename_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            write_complete_frame(root)
            target = root / "009__MiniMax-M3.html"
            target.write_text(
                replay_html("009", "MiniMax-M3", root_task_id="020"),
                encoding="utf-8",
            )

            report = MODULE.audit_directory(root)
            unit = next(
                item for item in report["units"] if item["file"] == target.name
            )

            self.assertFalse(unit["root_identity_consistent"])
            self.assertFalse(unit["replay_available"])
            self.assertEqual(unit["availability_state"], "INVALID_OR_AMBIGUOUS")
            self.assertFalse(report["summary"]["audit_complete"])

    def test_marker_with_malformed_replay_is_not_explicit_no_step(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            write_complete_frame(root)
            target = root / "050__MiniMax-M3.html"
            target.write_text(
                '<div>No step data available</div>'
                '<script type="application/json" id="trajectory-replay-data">{</script>',
                encoding="utf-8",
            )

            report = MODULE.audit_directory(root)
            unit = next(
                item for item in report["units"] if item["file"] == target.name
            )

            self.assertFalse(unit["replay_json_valid"])
            self.assertFalse(unit["explicit_no_step"])
            self.assertEqual(unit["availability_state"], "INVALID_OR_AMBIGUOUS")
            self.assertFalse(report["summary"]["audit_complete"])


if __name__ == "__main__":
    unittest.main()
