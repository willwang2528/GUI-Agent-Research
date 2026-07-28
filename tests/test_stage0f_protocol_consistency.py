from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "check_stage0f_protocol_consistency.py"
)
SPEC = importlib.util.spec_from_file_location(
    "check_stage0f_protocol_consistency",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProtocolConsistencyTests(unittest.TestCase):
    def test_current_protocol_stack_passes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(MODULE.check(root), [])

    def test_legacy_token_and_unpaired_fence_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            for relative in MODULE.CORE_FILES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                required = "\n".join(MODULE.REQUIRED_BY_FILE[relative])
                path.write_text(required + "\n", encoding="utf-8")

            target = root / MODULE.CORE_FILES[0]
            target.write_text(
                target.read_text(encoding="utf-8")
                + "\nNARROW_SCOPE_STEP2_PROTOCOL_ONLY\n```text\n",
                encoding="utf-8",
            )

            errors = MODULE.check(root)
            self.assertTrue(any("banned legacy token" in error for error in errors))
            self.assertTrue(any("unpaired fenced-code" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
