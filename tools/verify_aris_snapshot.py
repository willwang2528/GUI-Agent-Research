#!/usr/bin/env python3
"""Recompute and verify the content identity of the local ARIS source snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Iterable


ALGORITHM_ID = "aris-tree-sha256-v1"
ALGORITHM_DESCRIPTION = (
    "root is local_path; reject symlinks; enumerate regular files recursively; "
    "sort POSIX paths relative to root by UTF-8 bytes; for each file append "
    "relative_path UTF-8, NUL, lowercase ASCII SHA-256(file bytes), LF; "
    "SHA-256 the concatenated byte stream"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_files(root: Path) -> list[tuple[str, Path]]:
    if not root.is_dir():
        raise ValueError(f"snapshot root is not a directory: {root}")

    symlinks = sorted(
        (path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_symlink()),
        key=lambda value: value.encode("utf-8"),
    )
    if symlinks:
        preview = ", ".join(symlinks[:5])
        raise ValueError(f"snapshot contains symlinks, which v1 rejects: {preview}")

    entries = [
        (path.relative_to(root).as_posix(), path)
        for path in root.rglob("*")
        if path.is_file()
    ]
    entries.sort(key=lambda item: item[0].encode("utf-8"))
    return entries


def canonical_tree_hash(entries: Iterable[tuple[str, Path]]) -> str:
    digest = hashlib.sha256()
    for relative_path, path in entries:
        relative_bytes = relative_path.encode("utf-8")
        if b"\x00" in relative_bytes or b"\n" in relative_bytes:
            raise ValueError(f"path contains forbidden NUL/LF: {relative_path!r}")
        file_digest = sha256_file(path).encode("ascii")
        digest.update(relative_bytes)
        digest.update(b"\x00")
        digest.update(file_digest)
        digest.update(b"\n")
    return digest.hexdigest()


def resolve_manifest_root(project_root: Path, manifest: dict[str, object]) -> Path:
    raw_path = manifest.get("local_path")
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError("manifest local_path must be a non-empty string")
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    return candidate.resolve()


def verify(project_root: Path, manifest_path: Path) -> tuple[dict[str, object], bool]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = resolve_manifest_root(project_root, manifest)
    entries = snapshot_files(root)
    actual_hash = canonical_tree_hash(entries)
    actual_count = len(entries)

    expected_hash = manifest.get("canonical_tree_sha256")
    expected_count = manifest.get("local_file_count")
    expected_algorithm = manifest.get("canonical_tree_hash_algorithm_id")
    checks = {
        "algorithm_id_matches": expected_algorithm == ALGORITHM_ID,
        "file_count_matches": expected_count == actual_count,
        "tree_sha256_matches": expected_hash == actual_hash,
    }
    result: dict[str, object] = {
        "verifier": ALGORITHM_ID,
        "algorithm": ALGORITHM_DESCRIPTION,
        "project_root": str(project_root),
        "manifest_path": str(manifest_path),
        "snapshot_root": str(root),
        "expected": {
            "algorithm_id": expected_algorithm,
            "file_count": expected_count,
            "tree_sha256": expected_hash,
        },
        "actual": {
            "algorithm_id": ALGORITHM_ID,
            "file_count": actual_count,
            "tree_sha256": actual_hash,
        },
        "checks": checks,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
    }
    return result, all(checks.values())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root against which a relative manifest local_path is resolved.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("source_provenance/aris.json"),
        help="Manifest path, relative to project root unless absolute.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = project_root / manifest_path
    try:
        result, passed = verify(project_root, manifest_path.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"verdict": "ERROR", "error": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
