#!/usr/bin/env python3
"""Verify a literal projection from the frozen OSWorld 2.0 detail HTML.

This adapter deliberately stops below Stage A.  It verifies the archived HTML
bytes against ``detail_audit.json`` and its manifest, binds every replay to the
fixed task/config/root identity, and emits the literal replay fields needed by
later annotation.  It does not fetch screenshot URLs, infer an initial
pre-action observation, align screenshots to actions, or create a trajectory
for the one explicit no-step unit.

The parser implementation is registered by exact SHA-256 in the receipt JSON
Schema.  That registration is local and post-hoc, so a valid receipt still has
the fixed claim ceiling ``PRODUCTION_AUTHORITY_INCOMPLETE / NO_BLOCK_A``.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Sequence


PARSER_ID = "stage0f-osworld2-archived-html-v1"
PARSER_IMPLEMENTATION_PATH = "tools/verify_stage0f_osworld2_archived_source.py"
SCHEMA_ID = (
    "https://gui-agent-memory.local/schemas/"
    "stage0f_osworld2_archived_source_receipt.schema.json"
)
AUDIT_PROTOCOL = "stage0f-detail-availability-v1"
SOURCE_ORIGIN = "https://osworld-v2-monitor.xlang.ai"
NO_STEP_FILENAME = "050__MiniMax-M3.html"
CLAIM_CEILING = (
    "REAL_ARCHIVED_SOURCE_PROJECTION_VERIFIED / "
    "OBSERVATION_ASSET_AUTHORITY_PARTIAL / "
    "PRODUCTION_AUTHORITY_INCOMPLETE / NO_BLOCK_A"
)

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
    rb'<script type="application/json" id="trajectory-replay-data">'
    rb"(.*?)</script>",
    re.DOTALL,
)
ROOT_RE = re.compile(
    rb'id="trajectory-replay-root".*?data-task-id="([^"]+)".*?'
    rb'data-model-name="([^"]+)".*?data-trajectory-id="([^"]+)"',
    re.DOTALL,
)
NO_STEP_RE = re.compile(rb"\bNo step data available\b")
TIMESTAMP_RE = re.compile(r"^[0-9]{8}@[0-9]{12}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
STEP_KEYS = frozenset(
    {
        "category",
        "detail",
        "index",
        "label",
        "screenshot_exists",
        "screenshot_file",
        "screenshot_url",
        "status",
        "subactions",
        "timestamp",
    }
)
SUBACTION_KEYS = frozenset({"category", "detail", "label"})


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def tree_hash(files: Iterable[Path], root: Path) -> str:
    """Hash ``relative-path NUL lowercase-file-sha256 LF`` in byte order."""

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
    task_id, remainder = filename.split("__", 1)
    return task_id, remainder.removesuffix(".html")


def _issue(
    issues: list[dict[str, str]],
    code: str,
    message: str,
    artifact: str,
    pointer: str = "$",
) -> None:
    issues.append(
        {
            "code": code,
            "message": message,
            "artifact": artifact,
            "pointer": pointer,
        }
    )


def _load_json(
    path: Path,
    issues: list[dict[str, str]],
    code: str,
) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        _issue(issues, code, str(error), str(path))
        return None
    if not isinstance(value, dict):
        _issue(issues, code, "JSON root must be an object", str(path))
        return None
    return value


def _schema_registration(
    schema: Mapping[str, Any],
    issues: list[dict[str, str]],
    schema_path: Path,
) -> tuple[str, str, str]:
    try:
        registration = schema["$defs"]["registered_parser"]
        properties = registration["properties"]
        parser_id = properties["parser_id"]["const"]
        parser_path = properties["implementation_path"]["const"]
        parser_sha = properties["registered_sha256"]["const"]
    except (KeyError, TypeError):
        _issue(
            issues,
            "SCHEMA_PARSER_REGISTRATION_MISSING",
            "schema must register parser id, path, and exact SHA-256",
            str(schema_path),
            "$.$defs.registered_parser",
        )
        return "", "", ""
    if (
        parser_id != PARSER_ID
        or parser_path != PARSER_IMPLEMENTATION_PATH
        or not isinstance(parser_sha, str)
        or SHA256_RE.fullmatch(parser_sha) is None
    ):
        _issue(
            issues,
            "PARSER_REGISTRATION_IDENTITY_MISMATCH",
            "schema registration does not match the fixed parser identity",
            str(schema_path),
            "$.$defs.registered_parser",
        )
    return str(parser_id), str(parser_path), str(parser_sha)


def _validate_receipt_schema(
    receipt: Mapping[str, Any],
    schema: Mapping[str, Any],
    issues: list[dict[str, str]],
    schema_path: Path,
) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        _issue(
            issues,
            "JSONSCHEMA_IMPLEMENTATION_UNAVAILABLE",
            "jsonschema is required to validate the receipt",
            str(schema_path),
        )
        return
    try:
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(receipt),
            key=lambda item: list(item.absolute_path),
        )
    except Exception as error:  # schema/ref implementation errors fail closed
        _issue(
            issues,
            "RECEIPT_SCHEMA_VALIDATOR_ERROR",
            str(error),
            str(schema_path),
        )
        return
    for error in errors:
        pointer = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}"
            for part in error.absolute_path
        )
        _issue(
            issues,
            "RECEIPT_SCHEMA_INVALID",
            error.message,
            str(schema_path),
            pointer,
        )


def _literal_projection(step: Mapping[str, Any]) -> dict[str, Any]:
    action = {
        "category": step["category"],
        "label": step["label"],
        "detail": step["detail"],
        "status": step["status"],
    }
    subactions = [
        {
            "category": subaction["category"],
            "label": subaction["label"],
            "detail": subaction["detail"],
        }
        for subaction in step["subactions"]
    ]
    screenshot_reference = {
        "declared_exists": step["screenshot_exists"],
        "file": step["screenshot_file"],
        "url": step["screenshot_url"],
        "authority_status": "REFERENCE_ONLY_NOT_FETCHED_OR_VERIFIED",
    }
    projected = {
        "index": step["index"],
        "action": action,
        "subactions": subactions,
        "timestamp": step["timestamp"],
        "screenshot_reference": screenshot_reference,
    }
    projected["literal_projection_sha256"] = sha256_bytes(
        canonical_json_bytes(projected)
    )
    return projected


def _check_step(
    step: Any,
    expected_index: int,
    filename: str,
    issues: list[dict[str, str]],
) -> dict[str, Any] | None:
    pointer = f"$.replay.steps[{expected_index - 1}]"
    if not isinstance(step, dict):
        _issue(
            issues,
            "REPLAY_STEP_NOT_OBJECT",
            "every replay step must be an object",
            filename,
            pointer,
        )
        return None
    if frozenset(step) != STEP_KEYS:
        _issue(
            issues,
            "REPLAY_STEP_FIELD_SET_MISMATCH",
            "step fields must equal the frozen literal replay field set",
            filename,
            pointer,
        )
        return None
    if (
        type(step["index"]) is not int
        or step["index"] != expected_index
    ):
        _issue(
            issues,
            "REPLAY_STEP_ORDER_MISMATCH",
            "step indexes must be exactly 1..total_steps in payload order",
            filename,
            pointer + ".index",
        )
    if (
        not isinstance(step["category"], str)
        or not step["category"]
        or not isinstance(step["label"], str)
        or not step["label"]
        or not isinstance(step["detail"], dict)
        or not isinstance(step["status"], str)
        or not step["status"]
    ):
        _issue(
            issues,
            "REPLAY_ACTION_LITERAL_INVALID",
            "action category/label/detail/status must preserve typed literals",
            filename,
            pointer,
        )
    subactions = step["subactions"]
    if not isinstance(subactions, list):
        _issue(
            issues,
            "REPLAY_SUBACTIONS_INVALID",
            "subactions must be an ordered list",
            filename,
            pointer + ".subactions",
        )
        return None
    for ordinal, subaction in enumerate(subactions):
        if (
            not isinstance(subaction, dict)
            or frozenset(subaction) != SUBACTION_KEYS
            or not isinstance(subaction.get("category"), str)
            or not subaction.get("category")
            or not isinstance(subaction.get("label"), str)
            or not subaction.get("label")
            or not isinstance(subaction.get("detail"), dict)
        ):
            _issue(
                issues,
                "REPLAY_SUBACTION_LITERAL_INVALID",
                "each subaction must preserve category/label/detail exactly",
                filename,
                pointer + f".subactions[{ordinal}]",
            )
    if (
        not isinstance(step["timestamp"], str)
        or TIMESTAMP_RE.fullmatch(step["timestamp"]) is None
    ):
        _issue(
            issues,
            "REPLAY_TIMESTAMP_LITERAL_INVALID",
            "timestamp must be the archived YYYYMMDD@12-digit literal",
            filename,
            pointer + ".timestamp",
        )
    if type(step["screenshot_exists"]) is not bool:
        _issue(
            issues,
            "SCREENSHOT_DECLARATION_INVALID",
            "screenshot_exists must remain a literal boolean",
            filename,
            pointer + ".screenshot_exists",
        )
    for key in ("screenshot_file", "screenshot_url"):
        if step[key] is not None and not isinstance(step[key], str):
            _issue(
                issues,
                "SCREENSHOT_REFERENCE_LITERAL_INVALID",
                f"{key} must be a string or null",
                filename,
                pointer + f".{key}",
            )
    try:
        return _literal_projection(step)
    except (KeyError, TypeError, ValueError):
        return None


def _expected_audit_unit_map(
    audit: Mapping[str, Any],
    issues: list[dict[str, str]],
    audit_path: Path,
) -> dict[str, Mapping[str, Any]]:
    units = audit.get("units")
    if not isinstance(units, list):
        _issue(
            issues,
            "DETAIL_AUDIT_UNITS_INVALID",
            "detail audit units must be a list",
            str(audit_path),
            "$.units",
        )
        return {}
    result: dict[str, Mapping[str, Any]] = {}
    for ordinal, unit in enumerate(units):
        if not isinstance(unit, dict) or not isinstance(unit.get("file"), str):
            _issue(
                issues,
                "DETAIL_AUDIT_UNIT_INVALID",
                "each audit unit must name one file",
                str(audit_path),
                f"$.units[{ordinal}]",
            )
            continue
        filename = unit["file"]
        if filename in result:
            _issue(
                issues,
                "DETAIL_AUDIT_DUPLICATE_UNIT",
                "audit file names must be unique",
                str(audit_path),
                f"$.units[{ordinal}].file",
            )
        result[filename] = unit
    return result


def _compare_audit_field(
    audit_unit: Mapping[str, Any],
    field: str,
    actual: Any,
    filename: str,
    issues: list[dict[str, str]],
) -> None:
    if audit_unit.get(field) != actual:
        _issue(
            issues,
            "DETAIL_AUDIT_UNIT_MISMATCH",
            f"detail audit {field!r} does not equal the archived page",
            filename,
            f"$.audit_unit.{field}",
        )


def _parse_page(
    path: Path,
    audit_unit: Mapping[str, Any],
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    filename = path.name
    identity = expected_identity(filename)
    assert identity is not None
    task_id, config_id = identity
    page_bytes = path.read_bytes()
    page_sha = sha256_bytes(page_bytes)

    _compare_audit_field(audit_unit, "sha256", page_sha, filename, issues)
    _compare_audit_field(
        audit_unit,
        "expected_identity",
        [task_id, config_id],
        filename,
        issues,
    )

    root_matches = ROOT_RE.findall(page_bytes)
    replay_matches = REPLAY_RE.findall(page_bytes)
    no_step_count = len(NO_STEP_RE.findall(page_bytes))
    expected_root = [
        task_id.encode("utf-8"),
        config_id.encode("utf-8"),
        task_id.encode("utf-8"),
    ]

    if filename == NO_STEP_FILENAME:
        if replay_matches or root_matches or no_step_count != 1:
            _issue(
                issues,
                "EXPLICIT_NO_STEP_FABRICATION_OR_AMBIGUITY",
                (
                    "050__MiniMax-M3 must remain exactly one explicit no-step "
                    "marker with no replay payload and no replay root"
                ),
                filename,
            )
        _compare_audit_field(
            audit_unit, "availability_state", "EXPLICIT_NO_STEP", filename, issues
        )
        _compare_audit_field(
            audit_unit, "explicit_no_step", True, filename, issues
        )
        _compare_audit_field(
            audit_unit, "replay_available", False, filename, issues
        )
        _compare_audit_field(audit_unit, "step_count", 0, filename, issues)
        return {
            "file": filename,
            "task_id": task_id,
            "hosted_config_id": config_id,
            "page_sha256": page_sha,
            "availability_status": "EXPLICIT_NO_STEP",
            "explicit_no_step_status": "VERIFIED_NO_TRAJECTORY_INFERRED",
            "screenshot_bytes_status": "MISSING_SCREENSHOT_BYTES",
            "initial_pre_action_observation_status": (
                "MISSING_INITIAL_PRE_ACTION_OBSERVATION"
            ),
            "timeline_alignment_status": "TIMELINE_ALIGNMENT_UNPROVEN",
        }

    if no_step_count:
        _issue(
            issues,
            "UNEXPECTED_NO_STEP_MARKER",
            "only 050__MiniMax-M3 may be the explicit no-step unit",
            filename,
        )
    if len(root_matches) != 1:
        _issue(
            issues,
            "REPLAY_ROOT_CARDINALITY_INVALID",
            "replay pages must contain exactly one replay root",
            filename,
        )
        root_identity: list[bytes] | None = None
    else:
        root_identity = list(root_matches[0])
        if root_identity != expected_root:
            _issue(
                issues,
                "REPLAY_ROOT_IDENTITY_MISMATCH",
                "root task/config/trajectory identity must equal the filename",
                filename,
            )
    if len(replay_matches) != 1:
        _issue(
            issues,
            "REPLAY_PAYLOAD_CARDINALITY_INVALID",
            "replay pages must contain exactly one embedded replay payload",
            filename,
        )
        payload: dict[str, Any] = {}
        embedded_bytes = b""
    else:
        embedded_bytes = replay_matches[0]
        try:
            decoded = html.unescape(embedded_bytes.decode("utf-8"))
            payload_value = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            _issue(
                issues,
                "REPLAY_PAYLOAD_JSON_INVALID",
                str(error),
                filename,
            )
            payload_value = {}
        if not isinstance(payload_value, dict):
            _issue(
                issues,
                "REPLAY_PAYLOAD_NOT_OBJECT",
                "embedded replay payload must be an object",
                filename,
            )
            payload = {}
        else:
            payload = payload_value

    if frozenset(payload) != frozenset({"steps", "total_steps"}):
        _issue(
            issues,
            "REPLAY_PAYLOAD_FIELD_SET_MISMATCH",
            "payload fields must be exactly steps and total_steps",
            filename,
        )
    steps_value = payload.get("steps")
    total_steps = payload.get("total_steps")
    if not isinstance(steps_value, list) or not steps_value:
        _issue(
            issues,
            "REPLAY_STEPS_INVALID",
            "replay steps must be a non-empty ordered list",
            filename,
            "$.replay.steps",
        )
        steps: list[Any] = []
    else:
        steps = steps_value
    if type(total_steps) is not int or total_steps != len(steps):
        _issue(
            issues,
            "REPLAY_TOTAL_STEPS_MISMATCH",
            "total_steps must exactly equal len(steps)",
            filename,
            "$.replay.total_steps",
        )

    projections: list[dict[str, Any]] = []
    previous_timestamp: str | None = None
    for expected_index, step in enumerate(steps, start=1):
        projected = _check_step(step, expected_index, filename, issues)
        if projected is not None:
            timestamp = projected["timestamp"]
            if (
                isinstance(timestamp, str)
                and previous_timestamp is not None
                and timestamp < previous_timestamp
            ):
                _issue(
                    issues,
                    "REPLAY_TIMESTAMP_ORDER_MISMATCH",
                    "archived timestamp literals must be nondecreasing",
                    filename,
                    f"$.replay.steps[{expected_index - 1}].timestamp",
                )
            if isinstance(timestamp, str):
                previous_timestamp = timestamp
            projections.append(projected)

    root_strings = (
        [part.decode("utf-8") for part in root_identity]
        if root_identity is not None
        else None
    )
    _compare_audit_field(
        audit_unit, "root_identity", root_strings, filename, issues
    )
    _compare_audit_field(
        audit_unit,
        "root_identity_consistent",
        root_identity == expected_root,
        filename,
        issues,
    )
    _compare_audit_field(
        audit_unit,
        "replay_json_valid",
        (
            frozenset(payload) == frozenset({"steps", "total_steps"})
            and bool(steps)
            and type(total_steps) is int
            and total_steps == len(steps)
        ),
        filename,
        issues,
    )
    _compare_audit_field(
        audit_unit, "availability_state", "REPLAY_VALID", filename, issues
    )
    _compare_audit_field(
        audit_unit, "replay_available", True, filename, issues
    )
    _compare_audit_field(
        audit_unit, "explicit_no_step", False, filename, issues
    )
    _compare_audit_field(
        audit_unit, "step_count", len(steps), filename, issues
    )
    _compare_audit_field(
        audit_unit,
        "timestamp_count",
        sum(
            isinstance(step, dict) and bool(step.get("timestamp"))
            for step in steps
        ),
        filename,
        issues,
    )
    _compare_audit_field(
        audit_unit,
        "labeled_action_count",
        sum(
            isinstance(step, dict) and bool(step.get("label"))
            for step in steps
        ),
        filename,
        issues,
    )
    _compare_audit_field(
        audit_unit,
        "screenshot_url_count",
        sum(
            isinstance(step, dict) and bool(step.get("screenshot_url"))
            for step in steps
        ),
        filename,
        issues,
    )

    projection_core = {
        "file": filename,
        "task_id": task_id,
        "hosted_config_id": config_id,
        "page_sha256": page_sha,
        "availability_status": "REPLAY_PROJECTED",
        "root_identity": root_strings,
        "embedded_replay_bytes_sha256": sha256_bytes(embedded_bytes),
        "decoded_replay_payload_sha256": sha256_bytes(
            canonical_json_bytes(payload)
        ),
        "total_steps": total_steps if type(total_steps) is int else len(steps),
        "steps": projections,
        "screenshot_bytes_status": "MISSING_SCREENSHOT_BYTES",
        "initial_pre_action_observation_status": (
            "MISSING_INITIAL_PRE_ACTION_OBSERVATION"
        ),
        "timeline_alignment_status": "TIMELINE_ALIGNMENT_UNPROVEN",
    }
    projection_core["unit_literal_projection_sha256"] = sha256_bytes(
        canonical_json_bytes(projection_core)
    )
    return projection_core


def _verify_manifest_and_audit(
    manifest: Mapping[str, Any],
    audit: Mapping[str, Any],
    manifest_path: Path,
    audit_path: Path,
    detail_dir: Path,
    project_root: Path,
    issues: list[dict[str, str]],
) -> None:
    if manifest.get("source_origin") != SOURCE_ORIGIN:
        _issue(
            issues,
            "MANIFEST_SOURCE_ORIGIN_MISMATCH",
            "manifest source_origin must equal the frozen official monitor",
            str(manifest_path),
            "$.source_origin",
        )
    entries = manifest.get("files")
    detail_entries = (
        [
            item
            for item in entries
            if isinstance(item, dict)
            and item.get("path") == "source_provenance/osworld2/detail_audit.json"
        ]
        if isinstance(entries, list)
        else []
    )
    if len(detail_entries) != 1:
        _issue(
            issues,
            "MANIFEST_DETAIL_AUDIT_ENTRY_INVALID",
            "manifest must contain exactly one fixed detail_audit entry",
            str(manifest_path),
            "$.files",
        )
        detail_entry: Mapping[str, Any] = {}
    else:
        detail_entry = detail_entries[0]
    expected_detail_sha = detail_entry.get("sha256")
    actual_detail_sha = sha256_file(audit_path)
    if expected_detail_sha != actual_detail_sha:
        _issue(
            issues,
            "DETAIL_AUDIT_SHA256_MISMATCH",
            "detail_audit bytes do not match the manifest",
            str(audit_path),
        )
    if detail_entry.get("audit_protocol") != AUDIT_PROTOCOL:
        _issue(
            issues,
            "MANIFEST_AUDIT_PROTOCOL_MISMATCH",
            "manifest audit protocol is not the fixed protocol",
            str(manifest_path),
        )
    if (
        detail_entry.get("source_directory")
        != "source_provenance/osworld2/raw/detail_pages"
    ):
        _issue(
            issues,
            "MANIFEST_SOURCE_DIRECTORY_MISMATCH",
            "manifest source directory must name the archived detail pages",
            str(manifest_path),
        )
    if detail_entry.get("auditor") != "tools/audit_stage0f_detail_pages.py":
        _issue(
            issues,
            "MANIFEST_AUDITOR_IDENTITY_MISMATCH",
            "manifest must identify the frozen availability auditor",
            str(manifest_path),
        )
    auditor_path = project_root / "tools" / "audit_stage0f_detail_pages.py"
    if (
        not auditor_path.is_file()
        or detail_entry.get("auditor_sha256") != sha256_file(auditor_path)
    ):
        _issue(
            issues,
            "MANIFEST_AUDITOR_SHA256_MISMATCH",
            "availability auditor bytes do not match the manifest",
            str(auditor_path),
        )

    if audit.get("audit_protocol") != AUDIT_PROTOCOL:
        _issue(
            issues,
            "DETAIL_AUDIT_PROTOCOL_MISMATCH",
            "detail audit protocol is not the fixed protocol",
            str(audit_path),
            "$.audit_protocol",
        )
    expected_frame = audit.get("expected_frame")
    fixed_frame = {
        "task_ids": list(EXPECTED_TASK_IDS),
        "hosted_config_filenames": list(HOSTED_CONFIG_FILENAMES),
        "filenames": list(EXPECTED_FILENAMES),
    }
    if expected_frame != fixed_frame:
        _issue(
            issues,
            "DETAIL_AUDIT_FRAME_MISMATCH",
            "detail audit frame must equal the fixed 8 x 6 roster",
            str(audit_path),
            "$.expected_frame",
        )
    summary = audit.get("summary")
    if not isinstance(summary, dict):
        _issue(
            issues,
            "DETAIL_AUDIT_SUMMARY_INVALID",
            "detail audit summary must be an object",
            str(audit_path),
            "$.summary",
        )
        return
    required_summary = {
        "audit_complete": True,
        "expected_file_count": 48,
        "file_count": 48,
        "expected_files_present": 48,
        "missing_files": [],
        "unexpected_files": [],
        "replay_availability_status": "PARTIAL",
        "replay_available_files": 47,
        "explicit_no_step_files": 1,
        "invalid_or_ambiguous_files": 0,
    }
    for field, expected in required_summary.items():
        if summary.get(field) != expected:
            _issue(
                issues,
                "DETAIL_AUDIT_SUMMARY_MISMATCH",
                f"summary {field!r} must equal {expected!r}",
                str(audit_path),
                f"$.summary.{field}",
            )

    actual_files = sorted(
        detail_dir.glob("*.html"),
        key=lambda path: path.name.encode("utf-8"),
    )
    actual_names = [path.name for path in actual_files]
    if set(actual_names) != EXPECTED_FILENAME_SET or len(actual_names) != 48:
        missing = sorted(EXPECTED_FILENAME_SET - set(actual_names))
        unexpected = sorted(set(actual_names) - EXPECTED_FILENAME_SET)
        _issue(
            issues,
            "ARCHIVED_PAGE_FRAME_MISMATCH",
            f"missing={missing!r}; unexpected={unexpected!r}",
            str(detail_dir),
        )
    actual_tree_sha = tree_hash(actual_files, detail_dir)
    if summary.get("detail_tree_sha256") != actual_tree_sha:
        _issue(
            issues,
            "DETAIL_TREE_SHA256_MISMATCH",
            "actual 48-page tree hash does not match detail_audit",
            str(detail_dir),
        )
    if detail_entry.get("detail_tree_sha256") != actual_tree_sha:
        _issue(
            issues,
            "MANIFEST_DETAIL_TREE_SHA256_MISMATCH",
            "actual 48-page tree hash does not match manifest",
            str(detail_dir),
        )

    validation = manifest.get("validation")
    if not isinstance(validation, dict):
        _issue(
            issues,
            "MANIFEST_VALIDATION_INVALID",
            "manifest validation must be an object",
            str(manifest_path),
            "$.validation",
        )
    else:
        expected_validation = {
            "block_a_task_count_per_config": 8,
            "block_a_expected_detail_pages": 48,
            "block_a_detail_pages_present": 48,
            "block_a_detail_availability_audit_complete": True,
            "block_a_replay_availability_status": "PARTIAL",
            "block_a_replay_available_pages": 47,
            "block_a_explicit_no_step_pages": 1,
        }
        for field, expected in expected_validation.items():
            if validation.get(field) != expected:
                _issue(
                    issues,
                    "MANIFEST_VALIDATION_MISMATCH",
                    f"validation {field!r} must equal {expected!r}",
                    str(manifest_path),
                    f"$.validation.{field}",
                )


def verify_archive(
    manifest_path: Path,
    audit_path: Path,
    detail_dir: Path,
    schema_path: Path,
    project_root: Path,
    *,
    parser_implementation_path: Path | None = None,
) -> dict[str, Any]:
    """Return a fail-closed receipt for one fixed archived-source frame."""

    manifest_path = manifest_path.resolve()
    audit_path = audit_path.resolve()
    detail_dir = detail_dir.resolve()
    schema_path = schema_path.resolve()
    project_root = project_root.resolve()
    parser_path = (
        parser_implementation_path.resolve()
        if parser_implementation_path is not None
        else Path(__file__).resolve()
    )
    issues: list[dict[str, str]] = []

    schema = _load_json(
        schema_path, issues, "RECEIPT_SCHEMA_JSON_INVALID"
    ) or {}
    registered_id, registered_path, registered_sha = _schema_registration(
        schema, issues, schema_path
    )
    actual_parser_sha = (
        sha256_file(parser_path) if parser_path.is_file() else "0" * 64
    )
    parser_status = "VERIFIED"
    if (
        registered_id != PARSER_ID
        or registered_path != PARSER_IMPLEMENTATION_PATH
        or registered_sha != actual_parser_sha
    ):
        parser_status = "MISMATCH"
        _issue(
            issues,
            "PARSER_SHA256_MISMATCH",
            "executing parser bytes do not match the schema registration",
            str(parser_path),
        )

    manifest = _load_json(
        manifest_path, issues, "MANIFEST_JSON_INVALID"
    ) or {}
    audit = _load_json(
        audit_path, issues, "DETAIL_AUDIT_JSON_INVALID"
    ) or {}
    if manifest and audit:
        _verify_manifest_and_audit(
            manifest,
            audit,
            manifest_path,
            audit_path,
            detail_dir,
            project_root,
            issues,
        )

    audit_units = _expected_audit_unit_map(audit, issues, audit_path)
    units: list[dict[str, Any]] = []
    for filename in EXPECTED_FILENAMES:
        path = detail_dir / filename
        audit_unit = audit_units.get(filename)
        if not path.is_file():
            _issue(
                issues,
                "ARCHIVED_PAGE_MISSING",
                "expected archived HTML page is missing",
                str(path),
            )
            continue
        if audit_unit is None:
            _issue(
                issues,
                "DETAIL_AUDIT_UNIT_MISSING",
                "detail audit has no unit for the expected page",
                str(audit_path),
                "$.units",
            )
            continue
        units.append(_parse_page(path, audit_unit, issues))

    replay_units = [
        unit for unit in units if unit["availability_status"] == "REPLAY_PROJECTED"
    ]
    no_step_units = [
        unit for unit in units if unit["availability_status"] == "EXPLICIT_NO_STEP"
    ]
    projected_steps = sum(
        int(unit["total_steps"]) for unit in replay_units
    )
    projected_steps_materialized = sum(
        len(unit["steps"]) for unit in replay_units
    )
    if projected_steps != projected_steps_materialized:
        _issue(
            issues,
            "PROJECTION_STEP_COUNT_MISMATCH",
            "materialized literal projection does not match total_steps",
            str(detail_dir),
        )

    summary = audit.get("summary")
    if isinstance(summary, dict) and summary.get("total_steps") != projected_steps:
        _issue(
            issues,
            "DETAIL_AUDIT_TOTAL_STEPS_MISMATCH",
            "projected total_steps does not match detail_audit summary",
            str(audit_path),
            "$.summary.total_steps",
        )

    archive_projection_sha = sha256_bytes(canonical_json_bytes(units))
    valid_before_schema = not issues
    receipt: dict[str, Any] = {
        "artifact_type": "stage0f_osworld2_archived_source_receipt",
        "schema_version": "1.0.0",
        "valid": valid_before_schema,
        "source_kind": "REAL_ARCHIVED_OSWORLD2_DETAIL_HTML",
        "manifest": {
            "path": str(manifest_path),
            "sha256": (
                sha256_file(manifest_path)
                if manifest_path.is_file()
                else "0" * 64
            ),
        },
        "detail_audit": {
            "path": str(audit_path),
            "sha256": (
                sha256_file(audit_path) if audit_path.is_file() else "0" * 64
            ),
            "protocol": AUDIT_PROTOCOL,
        },
        "parser": {
            "parser_id": registered_id or PARSER_ID,
            "implementation_path": registered_path or PARSER_IMPLEMENTATION_PATH,
            "registered_sha256": (
                registered_sha
                if SHA256_RE.fullmatch(registered_sha or "")
                else "0" * 64
            ),
            "actual_sha256": actual_parser_sha,
            "status": parser_status,
        },
        "frame": {
            "task_ids": list(EXPECTED_TASK_IDS),
            "hosted_config_ids": list(HOSTED_CONFIG_FILENAMES),
            "expected_page_count": 48,
            "actual_page_count": len(list(detail_dir.glob("*.html"))),
            "replay_page_count": len(replay_units),
            "explicit_no_step_page_count": len(no_step_units),
            "explicit_no_step_file": NO_STEP_FILENAME,
        },
        "projection": {
            "projected_replay_units": len(replay_units),
            "explicit_no_step_units": len(no_step_units),
            "projected_steps": projected_steps,
            "archive_literal_projection_sha256": archive_projection_sha,
        },
        "authority_status": {
            "archived_source_projection": (
                "REAL_ARCHIVED_SOURCE_PROJECTION_VERIFIED"
                if valid_before_schema
                else "ARCHIVED_SOURCE_PROJECTION_REJECTED"
            ),
            "observation_assets": "OBSERVATION_ASSET_AUTHORITY_PARTIAL",
            "screenshot_bytes": "MISSING_SCREENSHOT_BYTES",
            "screenshot_urls": "REFERENCE_ONLY_NOT_FETCHED_OR_VERIFIED",
            "initial_pre_action_observation": (
                "MISSING_INITIAL_PRE_ACTION_OBSERVATION"
            ),
            "timeline_alignment": "TIMELINE_ALIGNMENT_UNPROVEN",
            "production_authority": "PRODUCTION_AUTHORITY_INCOMPLETE",
            "block_a": "NO_BLOCK_A",
        },
        "units": units,
        "issues": issues,
        "claim_ceiling": CLAIM_CEILING,
        "receipt_sha256": "0" * 64,
    }
    receipt["receipt_sha256"] = sha256_bytes(
        canonical_json_bytes(
            {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        )
    )

    schema_issues: list[dict[str, str]] = []
    if schema:
        _validate_receipt_schema(receipt, schema, schema_issues, schema_path)
    if schema_issues:
        receipt["issues"].extend(schema_issues)
        receipt["valid"] = False
        receipt["authority_status"][
            "archived_source_projection"
        ] = "ARCHIVED_SOURCE_PROJECTION_REJECTED"
        receipt["receipt_sha256"] = sha256_bytes(
            canonical_json_bytes(
                {
                    key: value
                    for key, value in receipt.items()
                    if key != "receipt_sha256"
                }
            )
        )
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--detail-audit", type=Path, required=True)
    parser.add_argument("--detail-dir", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    receipt = verify_archive(
        args.manifest,
        args.detail_audit,
        args.detail_dir,
        args.schema,
        args.project_root,
    )
    rendered = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if receipt["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
