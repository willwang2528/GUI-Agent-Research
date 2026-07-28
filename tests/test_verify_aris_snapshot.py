from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "verify_aris_snapshot.py"
SPEC = importlib.util.spec_from_file_location("verify_aris_snapshot", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VerifyArisSnapshotTests(unittest.TestCase):
    def test_tree_hash_uses_paths_nul_file_hex_and_lf(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            (root / "b.txt").write_bytes(b"B")
            (root / "nested").mkdir()
            (root / "nested" / "a.txt").write_bytes(b"A")

            entries = MODULE.snapshot_files(root)
            self.assertEqual(
                [name for name, _ in entries],
                ["b.txt", "nested/a.txt"],
            )

            manual = hashlib.sha256()
            for relative_path, payload in (
                ("b.txt", b"B"),
                ("nested/a.txt", b"A"),
            ):
                manual.update(relative_path.encode("utf-8"))
                manual.update(b"\x00")
                manual.update(hashlib.sha256(payload).hexdigest().encode("ascii"))
                manual.update(b"\n")

            self.assertEqual(MODULE.canonical_tree_hash(entries), manual.hexdigest())

    def test_path_changes_content_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            (root / "a.txt").write_bytes(b"same")
            before = MODULE.canonical_tree_hash(MODULE.snapshot_files(root))
            (root / "a.txt").rename(root / "b.txt")
            after = MODULE.canonical_tree_hash(MODULE.snapshot_files(root))
            self.assertNotEqual(before, after)

    def test_symlinks_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            (root / "target.txt").write_bytes(b"x")
            try:
                (root / "alias.txt").symlink_to(root / "target.txt")
            except OSError:
                self.skipTest("symlinks are unavailable on this platform")
            with self.assertRaisesRegex(ValueError, "contains symlinks"):
                MODULE.snapshot_files(root)


if __name__ == "__main__":
    unittest.main()
