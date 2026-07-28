#!/usr/bin/env python3
"""Verify the local Stage 0F Python runtime against the exact dependency lock.

This verifier establishes the identity of the interpreter and installed
distribution contents used for local mechanical tests.  It does not prove that
the environment can be reconstructed from the public package index, and it
does not upgrade any scientific claim.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import sys
from pathlib import Path
from typing import Iterable


NAME_NORMALIZER = re.compile(r"[-_.]+")
EXCLUDED_DISTRIBUTION_FILES = {
    "INSTALLER",
    "REQUESTED",
    "direct_url.json",
}


def normalize_name(name: str) -> str:
    return NAME_NORMALIZER.sub("-", name).lower()


def parse_requirements(path: Path) -> dict[str, str]:
    requirements: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.count("==") != 1:
            raise ValueError(
                f"{path}:{line_number}: only exact name==version pins are allowed"
            )
        raw_name, version = (part.strip() for part in line.split("==", 1))
        name = normalize_name(raw_name)
        if not name or not version:
            raise ValueError(f"{path}:{line_number}: empty package name or version")
        if name in requirements:
            raise ValueError(f"{path}:{line_number}: duplicate package {name}")
        requirements[name] = version
    if not requirements:
        raise ValueError(f"{path}: no requirements found")
    return requirements


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def distribution_content_fingerprint(
    requirements: dict[str, str],
) -> tuple[str, int]:
    """Hash installed files for the required distributions.

    Cache files and installer-local metadata are excluded so that the
    fingerprint binds package contents rather than the path used to install
    them.
    """

    entries: list[tuple[str, str, str]] = []
    for name in sorted(requirements):
        distribution = importlib.metadata.distribution(name)
        files: Iterable[importlib.metadata.PackagePath] = distribution.files or ()
        for package_path in files:
            relative = package_path.as_posix()
            parts = package_path.parts
            if "__pycache__" in parts or relative.endswith((".pyc", ".pyo")):
                continue
            if parts and parts[-1] in EXCLUDED_DISTRIBUTION_FILES:
                continue
            absolute = Path(distribution.locate_file(package_path))
            if not absolute.is_file():
                continue
            entries.append((name, relative, sha256_file(absolute)))

    entries.sort(key=lambda item: (item[0].encode("utf-8"), item[1].encode("utf-8")))
    digest = hashlib.sha256()
    for name, relative, file_hash in entries:
        for value in (name, relative, file_hash):
            encoded = value.encode("utf-8")
            if b"\x00" in encoded or b"\n" in encoded:
                raise ValueError(f"invalid fingerprint field: {value!r}")
            digest.update(encoded)
            digest.update(b"\x00")
        digest.update(b"\n")
    return digest.hexdigest(), len(entries)


def verify(requirements_path: Path, required_python: tuple[int, int, int]) -> dict:
    requirements = parse_requirements(requirements_path)
    actual_python = tuple(sys.version_info[:3])
    package_results: dict[str, dict[str, object]] = {}
    versions_match = True

    for name, expected_version in sorted(requirements.items()):
        try:
            actual_version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual_version = None
        matches = actual_version == expected_version
        versions_match = versions_match and matches
        package_results[name] = {
            "expected": expected_version,
            "actual": actual_version,
            "matches": matches,
        }

    fingerprint = None
    file_count = 0
    fingerprint_error = None
    if versions_match:
        try:
            fingerprint, file_count = distribution_content_fingerprint(requirements)
        except (OSError, ValueError, importlib.metadata.PackageNotFoundError) as exc:
            fingerprint_error = str(exc)

    checks = {
        "python_version_matches": actual_python == required_python,
        "required_distribution_versions_match": versions_match,
        "distribution_content_fingerprint_computed": fingerprint is not None,
    }
    passed = all(checks.values())
    return {
        "verifier": "stage0f-python-environment-v1",
        "requirements_path": str(requirements_path.resolve()),
        "required_python": ".".join(map(str, required_python)),
        "actual_python": ".".join(map(str, actual_python)),
        "packages": package_results,
        "distribution_file_count": file_count,
        "distribution_content_sha256": fingerprint,
        "fingerprint_error": fingerprint_error,
        "checks": checks,
        "verdict": "PASS" if passed else "FAIL",
        "claim_ceiling": (
            "PASS establishes the local interpreter, exact required versions, and "
            "installed distribution contents used by mechanical tests. It does not "
            "establish fresh-install reproducibility, measurement validity, a Step 1 "
            "result, or any GUI Memory scientific claim."
        ),
    }


def parse_python_version(value: str) -> tuple[int, int, int]:
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise argparse.ArgumentTypeError("Python version must be MAJOR.MINOR.PATCH")
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--requirements",
        type=Path,
        default=Path("requirements-stage0f.txt"),
    )
    parser.add_argument(
        "--require-python",
        type=parse_python_version,
        default=(3, 9, 6),
    )
    args = parser.parse_args()
    try:
        result = verify(args.requirements, args.require_python)
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"verdict": "ERROR", "error": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
