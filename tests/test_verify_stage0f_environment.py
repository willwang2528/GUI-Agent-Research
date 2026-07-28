from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "verify_stage0f_environment.py"
SPEC = importlib.util.spec_from_file_location("verify_stage0f_environment", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VerifyStage0fEnvironmentTests(unittest.TestCase):
    def write_requirements(self, content: str) -> Path:
        temporary = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        )
        self.addCleanup(Path(temporary.name).unlink, missing_ok=True)
        with temporary:
            temporary.write(content)
        return Path(temporary.name)

    def test_parse_exact_pins_and_normalize_names(self) -> None:
        path = self.write_requirements(
            "# lock\njsonschema==4.25.1\ntyping_extensions==4.16.0\n"
        )
        self.assertEqual(
            MODULE.parse_requirements(path),
            {"jsonschema": "4.25.1", "typing-extensions": "4.16.0"},
        )

    def test_reject_non_exact_requirement(self) -> None:
        path = self.write_requirements("jsonschema>=4.25.1\n")
        with self.assertRaisesRegex(ValueError, "exact name==version"):
            MODULE.parse_requirements(path)

    def test_reject_duplicate_normalized_name(self) -> None:
        path = self.write_requirements(
            "typing_extensions==4.16.0\ntyping-extensions==4.16.0\n"
        )
        with self.assertRaisesRegex(ValueError, "duplicate package"):
            MODULE.parse_requirements(path)

    def test_current_locked_environment_passes(self) -> None:
        result = MODULE.verify(ROOT / "requirements-stage0f.txt", (3, 9, 6))
        self.assertEqual(result["verdict"], "PASS")
        self.assertTrue(all(result["checks"].values()))
        self.assertGreater(result["distribution_file_count"], 0)
        self.assertRegex(result["distribution_content_sha256"], r"^[0-9a-f]{64}$")

    def test_wrong_python_version_fails(self) -> None:
        result = MODULE.verify(ROOT / "requirements-stage0f.txt", (9, 9, 9))
        self.assertEqual(result["verdict"], "FAIL")
        self.assertFalse(result["checks"]["python_version_matches"])

    def test_environment_manifest_binds_lock_verifier_and_contents(self) -> None:
        manifest = json.loads(
            (ROOT / "source_provenance" / "stage0f_environment.json").read_text(
                encoding="utf-8"
            )
        )

        def file_hash(relative: str) -> str:
            return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()

        self.assertEqual(
            file_hash(manifest["requirements"]["path"]),
            manifest["requirements"]["sha256"],
        )
        self.assertEqual(
            file_hash(manifest["verifier"]["path"]),
            manifest["verifier"]["sha256"],
        )
        result = MODULE.verify(ROOT / "requirements-stage0f.txt", (3, 9, 6))
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(
            result["distribution_content_sha256"],
            manifest["verification"]["distribution_content_sha256"],
        )
        self.assertEqual(
            result["distribution_file_count"],
            manifest["verification"]["distribution_file_count"],
        )


if __name__ == "__main__":
    unittest.main()
