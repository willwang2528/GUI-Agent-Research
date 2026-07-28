from __future__ import annotations

import copy
import hashlib
import html
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PATH = ROOT / "tools" / "verify_stage0f_osworld2_archived_source.py"
AUDITOR_PATH = ROOT / "tools" / "audit_stage0f_detail_pages.py"
SCHEMA_PATH = (
    ROOT / "schemas" / "stage0f_osworld2_archived_source_receipt.schema.json"
)
REPLAY_CONTENT_RE = re.compile(
    rb'(<script type="application/json" id="trajectory-replay-data">)'
    rb"(.*?)"
    rb"(</script>)",
    re.DOTALL,
)


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFIER = load_module("verify_stage0f_osworld2_archived_source", VERIFIER_PATH)
AUDITOR = load_module("audit_stage0f_detail_pages_for_adapter", AUDITOR_PATH)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_step(index: int) -> dict[str, Any]:
    timestamp = f"20260101@{index:012d}"
    return {
        "category": "click",
        "detail": {"coordinate": [index, index + 1]},
        "index": index,
        "label": f"Left click ({index}, {index + 1})",
        "screenshot_exists": True,
        "screenshot_file": f"step_{index}_{timestamp}.png",
        "screenshot_url": (
            "https://example.invalid/archive/"
            f"step_{index}_{timestamp}.png"
        ),
        "status": "ok",
        "subactions": [
            {
                "category": "click",
                "detail": {"coordinate": [index, index + 1]},
                "label": f"Left click ({index}, {index + 1})",
            }
        ],
        "timestamp": timestamp,
    }


def replay_html(
    task_id: str,
    config_id: str,
    *,
    root_task_id: str | None = None,
    root_config_id: str | None = None,
    trajectory_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> bytes:
    steps = [make_step(index) for index in range(1, 4)]
    replay = payload or {"steps": steps, "total_steps": len(steps)}
    return (
        '<div id="trajectory-replay-root" '
        f'data-task-id="{root_task_id or task_id}" '
        f'data-model-name="{root_config_id or config_id}" '
        f'data-trajectory-id="{trajectory_id or task_id}"></div>'
        '<script type="application/json" id="trajectory-replay-data">'
        f"{json.dumps(replay, sort_keys=True)}</script>"
    ).encode("utf-8")


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.detail_dir = (
            root / "source_provenance/osworld2/raw/detail_pages"
        )
        self.audit_path = (
            root / "source_provenance/osworld2/detail_audit.json"
        )
        self.manifest_path = (
            root / "source_provenance/osworld2/manifest.json"
        )
        self.detail_dir.mkdir(parents=True)
        (root / "tools").mkdir()
        shutil.copy2(AUDITOR_PATH, root / "tools/audit_stage0f_detail_pages.py")
        for filename in VERIFIER.EXPECTED_FILENAMES:
            task_id, config_with_suffix = filename.split("__", 1)
            config_id = config_with_suffix.removesuffix(".html")
            if filename == VERIFIER.NO_STEP_FILENAME:
                page = b'<div class="no-steps">No step data available</div>'
            else:
                page = replay_html(task_id, config_id)
            (self.detail_dir / filename).write_bytes(page)
        self.reseal()

    def reseal(self) -> None:
        audit = AUDITOR.audit_directory(self.detail_dir)
        self.audit_path.write_text(
            json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        summary = audit["summary"]
        manifest = {
            "source_origin": VERIFIER.SOURCE_ORIGIN,
            "validation": {
                "block_a_task_count_per_config": 8,
                "block_a_expected_detail_pages": 48,
                "block_a_detail_pages_present": summary["file_count"],
                "block_a_detail_availability_audit_complete": summary[
                    "audit_complete"
                ],
                "block_a_replay_availability_status": summary[
                    "replay_availability_status"
                ],
                "block_a_replay_available_pages": summary[
                    "replay_available_files"
                ],
                "block_a_explicit_no_step_pages": summary[
                    "explicit_no_step_files"
                ],
            },
            "files": [
                {
                    "path": "source_provenance/osworld2/detail_audit.json",
                    "source_directory": (
                        "source_provenance/osworld2/raw/detail_pages"
                    ),
                    "audit_protocol": VERIFIER.AUDIT_PROTOCOL,
                    "sha256": sha256_file(self.audit_path),
                    "detail_tree_sha256": summary["detail_tree_sha256"],
                    "auditor": "tools/audit_stage0f_detail_pages.py",
                    "auditor_sha256": sha256_file(
                        self.root / "tools/audit_stage0f_detail_pages.py"
                    ),
                }
            ],
        }
        self.manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def verify(
        self,
        *,
        schema_path: Path = SCHEMA_PATH,
        detail_dir: Path | None = None,
    ) -> dict[str, Any]:
        return VERIFIER.verify_archive(
            self.manifest_path,
            self.audit_path,
            detail_dir or self.detail_dir,
            schema_path,
            self.root,
        )

    def mutate_payload(
        self,
        filename: str,
        mutation: Callable[[dict[str, Any]], None],
    ) -> None:
        path = self.detail_dir / filename
        page = path.read_bytes()
        matches = REPLAY_CONTENT_RE.findall(page)
        assert len(matches) == 1
        prefix, content, suffix = matches[0]
        payload = json.loads(html.unescape(content.decode("utf-8")))
        mutation(payload)
        replacement = json.dumps(payload, sort_keys=True).encode("utf-8")
        path.write_bytes(
            page.replace(prefix + content + suffix, prefix + replacement + suffix, 1)
        )

    def reseal_hashes_only(self) -> None:
        audit = json.loads(self.audit_path.read_text(encoding="utf-8"))
        units = {unit["file"]: unit for unit in audit["units"]}
        for filename in VERIFIER.EXPECTED_FILENAMES:
            units[filename]["sha256"] = sha256_file(self.detail_dir / filename)
        files = sorted(
            self.detail_dir.glob("*.html"),
            key=lambda path: path.name.encode("utf-8"),
        )
        tree_sha = VERIFIER.tree_hash(files, self.detail_dir)
        audit["summary"]["detail_tree_sha256"] = tree_sha
        self.audit_path.write_text(
            json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        detail_entry = manifest["files"][0]
        detail_entry["sha256"] = sha256_file(self.audit_path)
        detail_entry["detail_tree_sha256"] = tree_sha
        self.manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def issue_codes(receipt: dict[str, Any]) -> set[str]:
    return {issue["code"] for issue in receipt["issues"]}


class OSWorld2ArchivedSourceAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixture = Fixture(Path(self.temp.name))

    def test_clean_fixed_frame_projects_literals_but_not_assets(self) -> None:
        receipt = self.fixture.verify()

        self.assertTrue(receipt["valid"], receipt["issues"])
        self.assertEqual(receipt["issues"], [])
        self.assertEqual(receipt["frame"]["actual_page_count"], 48)
        self.assertEqual(receipt["projection"]["projected_replay_units"], 47)
        self.assertEqual(receipt["projection"]["explicit_no_step_units"], 1)
        self.assertEqual(receipt["projection"]["projected_steps"], 141)
        self.assertEqual(receipt["parser"]["status"], "LOCAL_HASH_MATCH")
        self.assertEqual(
            receipt["authority_status"]["archived_source_projection"],
            "LOCAL_ARCHIVED_BYTES_LITERAL_PROJECTION_VERIFIED",
        )
        self.assertEqual(
            receipt["authority_status"]["source_origin_authenticity"],
            "SOURCE_ORIGIN_AUTHENTICITY_UNVERIFIED",
        )
        self.assertEqual(
            receipt["authority_status"]["manifest_authority"],
            "LOCAL_MANIFEST_SELF_SEALED",
        )
        self.assertEqual(
            receipt["authority_status"]["capture_time_authority"],
            "TRUSTED_CAPTURE_TIME_MISSING",
        )
        self.assertEqual(
            receipt["authority_status"]["parser_schema_authority"],
            "LOCAL_PARSER_SCHEMA_SELF_SEALED",
        )
        self.assertEqual(
            receipt["parser"]["registration_scope"],
            "LOCAL_SCHEMA_SELF_REGISTRATION_ONLY",
        )
        self.assertEqual(
            receipt["authority_status"]["screenshot_urls"],
            "REFERENCE_ONLY_NOT_FETCHED_OR_VERIFIED",
        )
        self.assertEqual(receipt["claim_ceiling"], VERIFIER.CLAIM_CEILING)

        no_step = next(
            unit
            for unit in receipt["units"]
            if unit["file"] == VERIFIER.NO_STEP_FILENAME
        )
        self.assertEqual(no_step["availability_status"], "EXPLICIT_NO_STEP")
        self.assertNotIn("steps", no_step)
        self.assertNotIn("total_steps", no_step)
        self.assertNotIn("root_identity", no_step)

        replay = next(
            unit
            for unit in receipt["units"]
            if unit["availability_status"] == "REPLAY_PROJECTED"
        )
        step = replay["steps"][0]
        self.assertEqual(step["index"], 1)
        self.assertEqual(step["action"]["category"], "click")
        self.assertEqual(step["subactions"][0]["category"], "click")
        self.assertEqual(step["timestamp"], "20260101@000000000001")
        self.assertEqual(
            step["screenshot_reference"]["authority_status"],
            "REFERENCE_ONLY_NOT_FETCHED_OR_VERIFIED",
        )

    def test_benign_root_attribute_reordering_is_accepted(self) -> None:
        target = self.fixture.detail_dir / "009__MiniMax-M3.html"
        page = target.read_bytes()
        old = (
            b'<div id="trajectory-replay-root" '
            b'data-task-id="009" '
            b'data-model-name="MiniMax-M3" '
            b'data-trajectory-id="009">'
        )
        new = (
            b'<div data-trajectory-id="009" '
            b'data-model-name="MiniMax-M3" '
            b'id="trajectory-replay-root" '
            b'data-task-id="009">'
        )
        self.assertIn(old, page)
        target.write_bytes(page.replace(old, new, 1))
        self.fixture.reseal_hashes_only()

        receipt = self.fixture.verify()

        self.assertTrue(receipt["valid"], receipt["issues"])

    def test_hidden_duplicate_root_and_data_ids_are_rejected(self) -> None:
        target = self.fixture.detail_dir / "009__MiniMax-M3.html"
        injected = (
            b'<div hidden id="trajectory-replay-root" '
            b'data-task-id="009" data-model-name="MiniMax-M3" '
            b'data-trajectory-id="009"></div>'
            b'<script hidden type="application/json" '
            b'id="trajectory-replay-data">'
            b'{"steps":[],"total_steps":0}</script>'
        )
        target.write_bytes(target.read_bytes() + injected)
        self.fixture.reseal_hashes_only()

        receipt = self.fixture.verify()

        self.assertFalse(receipt["valid"])
        codes = issue_codes(receipt)
        self.assertIn("HTML_RESERVED_ID_HIDDEN_NODE", codes)
        self.assertIn("REPLAY_ROOT_CARDINALITY_INVALID", codes)
        self.assertIn("REPLAY_PAYLOAD_CARDINALITY_INVALID", codes)

    def test_manifest_duplicate_json_member_is_rejected(self) -> None:
        raw = self.fixture.manifest_path.read_bytes()
        self.fixture.manifest_path.write_bytes(
            raw.replace(
                b"{",
                (
                    b'{"source_origin":'
                    b'"https://osworld-v2-monitor.xlang.ai",'
                ),
                1,
            )
        )

        receipt = self.fixture.verify()

        self.assertFalse(receipt["valid"])
        self.assertIn("MANIFEST_DUPLICATE_KEY", issue_codes(receipt))

    def test_detail_audit_duplicate_json_member_is_rejected(self) -> None:
        raw = self.fixture.audit_path.read_bytes()
        self.fixture.audit_path.write_bytes(
            raw.replace(
                b"{",
                b'{"audit_protocol":"stage0f-detail-availability-v1",',
                1,
            )
        )

        receipt = self.fixture.verify()

        self.assertFalse(receipt["valid"])
        self.assertIn("DETAIL_AUDIT_DUPLICATE_KEY", issue_codes(receipt))

    def test_schema_duplicate_json_member_is_rejected(self) -> None:
        schema_path = Path(self.temp.name) / "duplicate.schema.json"
        raw = SCHEMA_PATH.read_bytes()
        schema_path.write_bytes(
            raw.replace(
                b"{",
                (
                    b'{"$schema":'
                    b'"https://json-schema.org/draft/2020-12/schema",'
                ),
                1,
            )
        )

        receipt = self.fixture.verify(schema_path=schema_path)

        self.assertFalse(receipt["valid"])
        self.assertIn("RECEIPT_SCHEMA_DUPLICATE_KEY", issue_codes(receipt))

    def test_embedded_replay_duplicate_json_member_is_rejected(self) -> None:
        target = self.fixture.detail_dir / "009__MiniMax-M3.html"
        page = target.read_bytes()
        self.assertIn(b'"total_steps": 3', page)
        target.write_bytes(
            page.replace(
                b'"total_steps": 3',
                b'"total_steps": 3, "total_steps": 3',
                1,
            )
        )
        self.fixture.reseal()

        receipt = self.fixture.verify()

        self.assertFalse(receipt["valid"])
        self.assertIn(
            "REPLAY_PAYLOAD_DUPLICATE_KEY", issue_codes(receipt)
        )

    def test_local_reseal_changes_projection_but_never_origin_claim(self) -> None:
        before = self.fixture.verify()

        def change_literal(payload: dict[str, Any]) -> None:
            payload["steps"][0]["detail"]["coordinate"] = [900, 901]
            payload["steps"][0]["label"] = "Left click (900, 901)"

        self.fixture.mutate_payload("009__MiniMax-M3.html", change_literal)
        self.fixture.reseal()
        after = self.fixture.verify()

        self.assertTrue(before["valid"], before["issues"])
        self.assertTrue(after["valid"], after["issues"])
        self.assertNotEqual(
            before["projection"]["archive_literal_projection_sha256"],
            after["projection"]["archive_literal_projection_sha256"],
        )
        for receipt in (before, after):
            self.assertEqual(
                receipt["authority_status"]["source_origin_authenticity"],
                "SOURCE_ORIGIN_AUTHENTICITY_UNVERIFIED",
            )
            self.assertEqual(
                receipt["authority_status"]["manifest_authority"],
                "LOCAL_MANIFEST_SELF_SEALED",
            )
            self.assertEqual(receipt["claim_ceiling"], VERIFIER.CLAIM_CEILING)

    def test_source_directory_outside_project_root_is_rejected(self) -> None:
        outside_root = Path(self.temp.name).parent / (
            Path(self.temp.name).name + "-outside"
        )
        self.addCleanup(lambda: shutil.rmtree(outside_root, ignore_errors=True))
        shutil.copytree(self.fixture.detail_dir, outside_root)

        receipt = self.fixture.verify(detail_dir=outside_root)

        self.assertFalse(receipt["valid"])
        self.assertIn(
            "SOURCE_DIRECTORY_OUTSIDE_PROJECT_ROOT", issue_codes(receipt)
        )
        self.assertEqual(receipt["units"], [])

    def test_symlinked_source_page_is_rejected_before_reading(self) -> None:
        target = self.fixture.detail_dir / "009__MiniMax-M3.html"
        outside = self.fixture.root / "outside-page.html"
        target.rename(outside)
        target.symlink_to(outside)

        receipt = self.fixture.verify()

        self.assertFalse(receipt["valid"])
        self.assertIn("SOURCE_PAGE_SYMLINK_REJECTED", issue_codes(receipt))
        self.assertEqual(receipt["units"], [])

    def test_no_step_page_rejects_hidden_reserved_data_id(self) -> None:
        target = self.fixture.detail_dir / VERIFIER.NO_STEP_FILENAME
        target.write_bytes(
            target.read_bytes()
            + (
                b'<script hidden id="trajectory-replay-data" '
                b'type="application/json">'
                b'{"steps":[],"total_steps":0}</script>'
            )
        )
        self.fixture.reseal_hashes_only()

        receipt = self.fixture.verify()

        self.assertFalse(receipt["valid"])
        self.assertIn(
            "EXPLICIT_NO_STEP_FABRICATION_OR_AMBIGUITY",
            issue_codes(receipt),
        )

    def test_single_byte_page_mutation_is_rejected(self) -> None:
        target = self.fixture.detail_dir / "009__MiniMax-M3.html"
        target.write_bytes(target.read_bytes() + b" ")

        receipt = self.fixture.verify()

        self.assertFalse(receipt["valid"])
        self.assertTrue(
            {"DETAIL_TREE_SHA256_MISMATCH", "DETAIL_AUDIT_UNIT_MISMATCH"}
            <= issue_codes(receipt)
        )

    def test_filename_content_swap_is_rejected_even_after_reseal(self) -> None:
        left = self.fixture.detail_dir / "009__MiniMax-M3.html"
        right = self.fixture.detail_dir / "020__MiniMax-M3.html"
        left_bytes = left.read_bytes()
        right_bytes = right.read_bytes()
        left.write_bytes(right_bytes)
        right.write_bytes(left_bytes)
        self.fixture.reseal()

        receipt = self.fixture.verify()

        self.assertFalse(receipt["valid"])
        self.assertIn("REPLAY_ROOT_IDENTITY_MISMATCH", issue_codes(receipt))

    def test_task_config_and_trajectory_root_swaps_are_rejected(self) -> None:
        cases = (
            (b'data-task-id="009"', b'data-task-id="020"'),
            (
                b'data-model-name="MiniMax-M3"',
                b'data-model-name="qwen37"',
            ),
            (b'data-trajectory-id="009"', b'data-trajectory-id="020"'),
        )
        for old, new in cases:
            with self.subTest(old=old):
                with tempfile.TemporaryDirectory() as raw_dir:
                    fixture = Fixture(Path(raw_dir))
                    target = fixture.detail_dir / "009__MiniMax-M3.html"
                    target.write_bytes(target.read_bytes().replace(old, new, 1))
                    fixture.reseal()

                    receipt = fixture.verify()

                    self.assertFalse(receipt["valid"])
                    self.assertIn(
                        "REPLAY_ROOT_IDENTITY_MISMATCH",
                        issue_codes(receipt),
                    )

    def test_step_deletion_is_rejected_after_reseal(self) -> None:
        def delete_first(payload: dict[str, Any]) -> None:
            del payload["steps"][0]
            payload["total_steps"] = len(payload["steps"])

        self.fixture.mutate_payload("009__MiniMax-M3.html", delete_first)
        self.fixture.reseal()

        receipt = self.fixture.verify()

        self.assertFalse(receipt["valid"])
        self.assertIn("REPLAY_STEP_ORDER_MISMATCH", issue_codes(receipt))

    def test_step_reorder_is_rejected_after_reseal(self) -> None:
        def reorder(payload: dict[str, Any]) -> None:
            payload["steps"][0], payload["steps"][1] = (
                payload["steps"][1],
                payload["steps"][0],
            )

        self.fixture.mutate_payload("009__MiniMax-M3.html", reorder)
        self.fixture.reseal()

        receipt = self.fixture.verify()

        self.assertFalse(receipt["valid"])
        self.assertIn("REPLAY_STEP_ORDER_MISMATCH", issue_codes(receipt))

    def test_total_steps_change_is_rejected_after_reseal(self) -> None:
        def change_total(payload: dict[str, Any]) -> None:
            payload["total_steps"] += 1

        self.fixture.mutate_payload("009__MiniMax-M3.html", change_total)
        self.fixture.reseal()

        receipt = self.fixture.verify()

        self.assertFalse(receipt["valid"])
        self.assertIn("REPLAY_TOTAL_STEPS_MISMATCH", issue_codes(receipt))

    def test_parser_hash_mismatch_is_rejected(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        schema["$defs"]["registered_parser"]["properties"][
            "registered_sha256"
        ]["const"] = "0" * 64
        schema_path = Path(self.temp.name) / "wrong-hash.schema.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")

        receipt = self.fixture.verify(schema_path=schema_path)

        self.assertFalse(receipt["valid"])
        self.assertEqual(receipt["parser"]["status"], "LOCAL_HASH_MISMATCH")
        self.assertIn("PARSER_SHA256_MISMATCH", issue_codes(receipt))

    def test_missing_page_is_rejected(self) -> None:
        (self.fixture.detail_dir / "009__MiniMax-M3.html").unlink()

        receipt = self.fixture.verify()

        self.assertFalse(receipt["valid"])
        self.assertIn("ARCHIVED_PAGE_MISSING", issue_codes(receipt))
        self.assertIn("ARCHIVED_PAGE_FRAME_MISMATCH", issue_codes(receipt))

    def test_explicit_no_step_cannot_be_fabricated_as_trajectory(self) -> None:
        target = self.fixture.detail_dir / VERIFIER.NO_STEP_FILENAME
        target.write_bytes(replay_html("050", "MiniMax-M3"))
        self.fixture.reseal()

        receipt = self.fixture.verify()

        self.assertFalse(receipt["valid"])
        self.assertIn(
            "EXPLICIT_NO_STEP_FABRICATION_OR_AMBIGUITY",
            issue_codes(receipt),
        )
        no_step = next(
            unit
            for unit in receipt["units"]
            if unit["file"] == VERIFIER.NO_STEP_FILENAME
        )
        self.assertNotIn("steps", no_step)
        self.assertNotIn("total_steps", no_step)

    def test_schema_registration_tamper_is_rejected(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        schema["$defs"]["registered_parser"]["properties"][
            "parser_id"
        ]["const"] = "unregistered-parser"
        schema_path = Path(self.temp.name) / "tampered.schema.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")

        receipt = self.fixture.verify(schema_path=schema_path)

        self.assertFalse(receipt["valid"])
        self.assertIn(
            "PARSER_REGISTRATION_IDENTITY_MISMATCH",
            issue_codes(receipt),
        )

    def test_receipt_schema_compiles_with_ajv2020_strict(self) -> None:
        script = r"""
const fs = require("fs");
let Ajv2020;
try {
  Ajv2020 = require("ajv/dist/2020").default;
} catch (firstError) {
  Ajv2020 = require(
    "/opt/homebrew/lib/node_modules/openclaw/node_modules/ajv/dist/2020"
  ).default;
}
const schema = JSON.parse(
  fs.readFileSync(
    "schemas/stage0f_osworld2_archived_source_receipt.schema.json",
    "utf8"
  )
);
const ajv = new Ajv2020({strict: true, allErrors: true});
ajv.addSchema(schema);
if (typeof ajv.getSchema(schema.$id) !== "function") {
  throw new Error("strict compile did not produce a validator");
}
process.stdout.write("AJV2020_STRICT_PASS\n");
"""
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=str(ROOT),
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "AJV2020_STRICT_PASS")


if __name__ == "__main__":
    unittest.main()
