#!/usr/bin/env python3
"""Standalone Stage 0F raw-identity and conditional-redaction verifier.

This module deliberately does not register its schemas in the Stage A v0.6
validator.  A successful run establishes local L2 mechanics only:

* raw bytes, parser output, selectors, slots, and envelope IDs can be replayed;
* a reviewer packet is exactly regenerated from a declared allowed projection;
* enumerated forbidden-field mutations leave the normalized reviewer transcript
  unchanged.

It does not establish selector exogeneity, entropy/no-grinding, reviewer ACLs,
the complete pair universe, a frozen matcher, reliability, Block A, or Step 1.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import hmac
import importlib.metadata
import json
import os
import platform
import stat
import sys
import tempfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import jsonschema
from jsonschema import Draft202012Validator
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
SCHEMA_VERSION = "stage0f-measurement-v0.6.0-draft"
CANONICALIZATION = "stage0f-canonical-json-v1"
IDENTITY_STACK_VERSION = "stage0f-identity-mechanics-v0.1-draft"
POLICY_ID = "stage0f-conditional-identity-redaction-v2"
PARSER_ID = "stage0f-raw-identity-json-parser-v1"
PARSER_PROJECTION_ID = "typed-projection-plus-identity-evidence-v1"
ALIAS_SERIALIZATION = "stage0f-packet-alias-v1"
ATOMICITY_QUESTION_ID = "stage0f-independent-atomicity-question-v1"

IDENTITY_SCHEMA_FILES = (
    "stage0f_common.schema.json",
    "stage0f_a0_input.schema.json",
    "stage0f_identity_measurement_stack_manifest.schema.json",
    "stage0f_identity_submission_session.schema.json",
    "stage0f_raw_event_identity_envelope.schema.json",
    "stage0f_raw_envelope_verification_receipt.schema.json",
    "stage0f_identity_alias_sidecar.schema.json",
    "stage0f_pairwise_identity_review_packet.schema.json",
    "stage0f_identity_redaction_verification_receipt.schema.json",
)
POLICY_RELATIVE_PATH = "schemas/stage0f_identity_redaction_policy.json"
CODEBOOK_RELATIVE_PATH = "schemas/stage0f_identity_codebook.json"
MATCHER_SPEC_RELATIVE_PATH = (
    "stage0f_a0_pairwise_identity_partial_identification_spec.md"
)
REDACTOR_RELATIVE_PATH = "tools/stage0f_identity_redactor.py"
VERIFIER_RELATIVE_PATH = "tools/verify_stage0f_identity_mechanics.py"

BUNDLE_FILES = {
    "manifest": "identity_stack_manifest.json",
    "a0_input": "a0_input.json",
    "left_session": "left_submission_session.json",
    "right_session": "right_submission_session.json",
    "left_envelope": "left_raw_envelope.json",
    "right_envelope": "right_raw_envelope.json",
    "left_raw_receipt": "left_raw_verification_receipt.json",
    "right_raw_receipt": "right_raw_verification_receipt.json",
    "sidecar": "identity_alias_sidecar.json",
    "packet": "pairwise_identity_review_packet.json",
    "redaction_receipt": "identity_redaction_receipt.json",
}

RAW_CHECKS = [
    "RAW_BYTES_HASH_LENGTH_PASS",
    "RAW_DUPLICATE_KEY_PARSE_PASS",
    "RAW_TYPED_PROJECTION_REPLAY_PASS",
    "RAW_IDENTITY_EVIDENCE_BINDING_PASS",
    "RAW_SELECTOR_INTERVAL_CUTOFF_PASS",
    "RAW_STATEMENT_HASH_PASS",
    "RAW_SLOT_SESSION_BINDING_PASS",
    "RAW_ENVELOPE_ID_PASS",
]
REDACTION_CHECKS = [
    "ALIAS_DERIVATION_PASS",
    "ALIAS_DOMAIN_SEPARATION_PASS",
    "ALIAS_MAPPING_COVERAGE_PASS",
    "NO_PRIVATE_BINDING_FIELD_VISIBLE_PASS",
    "INDEPENDENT_PACKET_RECOMPUTATION_PASS",
    "CANONICAL_VIRTUAL_TRANSCRIPT_PASS",
    "VALID_TRACE_FORBIDDEN_MUTATION_INVARIANCE_PASS",
]


class DuplicateKeyError(ValueError):
    """Raised when JSON contains a duplicate object key."""


class MechanicsError(ValueError):
    """Machine-readable first-failure error."""

    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = path

    def as_dict(self) -> Dict[str, str]:
        return {
            "stage": "identity_mechanics_validation",
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


def _reject_duplicate_pairs(
    pairs: Sequence[Tuple[str, Any]],
) -> Dict[str, Any]:
    value: Dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise DuplicateKeyError(key)
        value[key] = child
    return value


def canonical_bytes(value: Any) -> bytes:
    """Restricted canonical JSON shared with the Stage A validator."""

    def reject_float(node: Any, path: str = "$") -> None:
        if isinstance(node, float):
            raise ValueError("%s: floats are not canonical" % path)
        if isinstance(node, dict):
            for key, child in node.items():
                reject_float(child, "%s.%s" % (path, key))
        elif isinstance(node, list):
            for index, child in enumerate(node):
                reject_float(child, "%s[%d]" % (path, index))

    reject_float(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def text_sha256(value: str) -> str:
    return bytes_sha256(value.encode("utf-8"))


def artifact_ref(artifact: Mapping[str, Any]) -> Dict[str, str]:
    return {
        "artifact_id": str(artifact["artifact_id"]),
        "sha256": canonical_sha256(artifact),
    }


def parse_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise MechanicsError(
            "SEM_A0_IDENTITY_TIMESTAMP_TZ",
            "timestamp requires an explicit timezone",
        )
    return parsed


def load_schemas(
    schema_dir: Path = SCHEMA_DIR,
) -> Tuple[Dict[str, Any], Registry]:
    schemas = {
        name: json.loads((schema_dir / name).read_text(encoding="utf-8"))
        for name in IDENTITY_SCHEMA_FILES
    }
    registry = Registry().with_resources(
        [
            (schema["$id"], Resource.from_contents(schema))
            for schema in schemas.values()
        ]
    )
    return schemas, registry


def identity_schema_bundle_sha256(
    schemas: Mapping[str, Any],
) -> str:
    entries = [
        [name, canonical_sha256(schemas[name])]
        for name in sorted(IDENTITY_SCHEMA_FILES)
    ]
    return canonical_sha256(["stage0f-identity-schema-bundle-v1", entries])


def verifier_file_sha256() -> str:
    return bytes_sha256(Path(__file__).read_bytes())


def project_file_sha256(relative_path: str) -> str:
    return bytes_sha256((ROOT / relative_path).read_bytes())


def runtime_contract() -> Dict[str, Any]:
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "dependencies": {
            name: importlib.metadata.version(name)
            for name in ("jsonschema", "referencing", "rpds-py")
        },
    }


def validate_schema_set(
    schemas: Mapping[str, Any],
    registry: Registry,
) -> None:
    for name in IDENTITY_SCHEMA_FILES:
        try:
            Draft202012Validator.check_schema(schemas[name])
        except jsonschema.SchemaError as exc:
            raise MechanicsError(
                "SCHEMA_IDENTITY_META_INVALID",
                "%s: %s" % (name, exc.message),
            ) from exc
    if len(list(registry)) != len(IDENTITY_SCHEMA_FILES):
        raise MechanicsError(
            "SCHEMA_IDENTITY_REGISTRY_INCOMPLETE",
            "identity schema registry is incomplete",
        )


def validate_instance(
    instance: Any,
    schema_name: str,
    schemas: Mapping[str, Any],
    registry: Registry,
) -> None:
    validator = Draft202012Validator(
        schemas[schema_name],
        registry=registry,
    )
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        error = errors[0]
        path = "$"
        for part in error.absolute_path:
            path += "[%d]" % part if isinstance(part, int) else ".%s" % part
        raise MechanicsError(
            "SCHEMA_IDENTITY_INSTANCE_INVALID",
            "%s: %s" % (schema_name, error.message),
            path,
        )


def load_json_no_duplicates(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
        )
    except DuplicateKeyError as exc:
        raise MechanicsError(
            "SEM_A0_RAW_DUPLICATE_JSON_KEY",
            "duplicate JSON key %s in %s" % (exc, path.name),
        ) from exc


def _safe_relative_parts(relative_path: str) -> Tuple[str, ...]:
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or not pure.parts or ".." in pure.parts:
        raise MechanicsError(
            "IO_A0_RAW_SOURCE_PATH_ESCAPE",
            "raw source path is not a contained relative path",
        )
    if any(part in ("", ".") for part in pure.parts):
        raise MechanicsError(
            "IO_A0_RAW_SOURCE_PATH_ESCAPE",
            "raw source path has an invalid component",
        )
    return tuple(pure.parts)


def read_immutable_contained_bytes(
    bundle_root: Path,
    relative_path: str,
) -> bytes:
    """Open once, reject symlinks, and hash/parse the same byte buffer."""

    parts = _safe_relative_parts(relative_path)
    current = bundle_root
    for part in parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError as exc:
            raise MechanicsError(
                "IO_A0_RAW_SOURCE_MISSING",
                "raw source is missing: %s" % relative_path,
            ) from exc
        if stat.S_ISLNK(mode):
            raise MechanicsError(
                "IO_A0_RAW_SOURCE_SYMLINK",
                "raw source path contains a symlink",
            )
    root_real = str(bundle_root.resolve())
    target_real = str(current.resolve())
    if os.path.commonpath([root_real, target_real]) != root_real:
        raise MechanicsError(
            "IO_A0_RAW_SOURCE_PATH_ESCAPE",
            "raw source resolves outside the bundle",
        )
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(str(current), flags)
    except OSError as exc:
        raise MechanicsError(
            "IO_A0_RAW_SOURCE_OPEN",
            "cannot open raw source once: %s" % exc,
        ) from exc
    try:
        before = os.fstat(descriptor)
        chunks: List[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise MechanicsError(
            "HASH_A0_RAW_ENVELOPE_TOCTOU",
            "raw source changed while it was read",
        )
    return b"".join(chunks)


def build_manifest(
    frozen_at: str,
    schemas: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    if schemas is None:
        schemas, _ = load_schemas()
    manifest: Dict[str, Any] = {
        "artifact_type": "identity_measurement_stack_manifest",
        "schema_version": SCHEMA_VERSION,
        "canonicalization": CANONICALIZATION,
        "artifact_id": "identity-stack-placeholder",
        "identity_stack_version": IDENTITY_STACK_VERSION,
        "identity_schema_bundle_sha256": identity_schema_bundle_sha256(
            schemas
        ),
        "identity_codebook": {
            "relative_path": CODEBOOK_RELATIVE_PATH,
            "sha256": project_file_sha256(CODEBOOK_RELATIVE_PATH),
        },
        "matcher_spec": {
            "relative_path": MATCHER_SPEC_RELATIVE_PATH,
            "sha256": project_file_sha256(MATCHER_SPEC_RELATIVE_PATH),
        },
        "redaction_policy": {
            "relative_path": POLICY_RELATIVE_PATH,
            "sha256": project_file_sha256(POLICY_RELATIVE_PATH),
        },
        "redactor_executable": {
            "relative_path": REDACTOR_RELATIVE_PATH,
            "sha256": project_file_sha256(REDACTOR_RELATIVE_PATH),
        },
        "raw_verifier_executable": {
            "relative_path": VERIFIER_RELATIVE_PATH,
            "sha256": verifier_file_sha256(),
        },
        "runtime_contract": runtime_contract(),
        "frozen_at": frozen_at,
    }
    manifest_id = derive_manifest_id(manifest)
    manifest["artifact_id"] = "identity-stack-" + manifest_id
    return manifest


def derive_manifest_id(manifest: Mapping[str, Any]) -> str:
    core = dict(manifest)
    core.pop("artifact_id", None)
    core.pop("frozen_at", None)
    return canonical_sha256(
        ["stage0f-identity-stack-manifest-v1", core]
    )


def derive_session_id(session: Mapping[str, Any]) -> str:
    return canonical_sha256(
        [
            "stage0f-identity-submission-session-v1",
            session["identity_stack_manifest_ref"]["sha256"],
            session["unit_alias"],
            session["boundary_location_id"],
            session["a0_input_ref"]["sha256"],
            session["side"],
            session["annotator_principal_commitment_sha256"],
            session["append_only_channel_id"],
            session["session_sequence"],
        ]
    )


def derive_slot_id(session: Mapping[str, Any], slot_ordinal: int) -> str:
    return canonical_sha256(
        [
            "stage0f-identity-submission-slot-v1",
            session["session_id"],
            slot_ordinal,
        ]
    )


def slot_entry_sha256(slot: Mapping[str, Any]) -> str:
    core = dict(slot)
    core.pop("slot_entry_sha256", None)
    return canonical_sha256(["stage0f-identity-slot-entry-v1", core])


def build_submission_session(
    manifest: Mapping[str, Any],
    a0_input: Mapping[str, Any],
    side: str,
    annotator_alias: str,
    principal_commitment_sha256: str,
    append_only_channel_id: str,
    session_sequence: int,
    raw_sources: Sequence[Tuple[str, bytes]],
    reserved_at: str,
    slot_reserved_at: str,
    sealed_at: str,
    closed_at: str,
) -> Dict[str, Any]:
    session: Dict[str, Any] = {
        "artifact_type": "identity_submission_session",
        "schema_version": SCHEMA_VERSION,
        "canonicalization": CANONICALIZATION,
        "artifact_id": "identity-session-placeholder",
        "identity_stack_manifest_ref": artifact_ref(manifest),
        "unit_alias": a0_input["unit_alias"],
        "boundary_location_id": a0_input["boundary_location_id"],
        "a0_input_ref": artifact_ref(a0_input),
        "side": side,
        "session_id": "1" * 64,
        "annotator_alias": annotator_alias,
        "annotator_principal_commitment_sha256": (
            principal_commitment_sha256
        ),
        "append_only_channel_id": append_only_channel_id,
        "session_sequence": session_sequence,
        "reserved_at": reserved_at,
        "slots": [],
        "closed_at": closed_at,
        "complete_search_attestation": (
            "self_reported_complete_search_only"
        ),
        "chain_tip_sha256": None,
    }
    session["session_id"] = derive_session_id(session)
    session["artifact_id"] = "identity-session-" + session["session_id"]
    previous: Optional[str] = None
    for index, (relative_path, raw_bytes) in enumerate(raw_sources):
        slot = {
            "slot_ordinal": index,
            "slot_id": derive_slot_id(session, index),
            "reserved_at": slot_reserved_at,
            "sealed_source": {
                "relative_path": relative_path,
                "content_sha256": bytes_sha256(raw_bytes),
                "byte_length": len(raw_bytes),
            },
            "sealed_at": sealed_at,
            "previous_slot_entry_sha256": previous,
            "slot_entry_sha256": "2" * 64,
        }
        slot["slot_entry_sha256"] = slot_entry_sha256(slot)
        previous = slot["slot_entry_sha256"]
        session["slots"].append(slot)
    session["chain_tip_sha256"] = previous
    return session


def verify_submission_session(
    session: Mapping[str, Any],
    manifest: Mapping[str, Any],
    a0_input: Mapping[str, Any],
) -> None:
    if session["identity_stack_manifest_ref"] != artifact_ref(manifest):
        raise MechanicsError(
            "SEM_A0_IDENTITY_SESSION_MANIFEST_BINDING",
            "submission session does not bind the current identity stack",
        )
    if session["a0_input_ref"] != artifact_ref(a0_input):
        raise MechanicsError(
            "SEM_A0_IDENTITY_SESSION_A0_BINDING",
            "submission session does not bind the current A0 input",
        )
    if (
        session["unit_alias"] != a0_input["unit_alias"]
        or session["boundary_location_id"]
        != a0_input["boundary_location_id"]
    ):
        raise MechanicsError(
            "SEM_A0_IDENTITY_SESSION_UNIT_LOCATION",
            "submission session unit/location mismatch",
        )
    expected_session_id = derive_session_id(session)
    if session["session_id"] != expected_session_id:
        raise MechanicsError(
            "SEM_A0_IDENTITY_SESSION_ID",
            "submission session id is not the canonical preimage hash",
        )
    if session["artifact_id"] != "identity-session-" + expected_session_id:
        raise MechanicsError(
            "SEM_A0_IDENTITY_SESSION_ARTIFACT_ID",
            "submission session artifact id is not derived",
        )
    reserved = parse_timestamp(session["reserved_at"])
    closed = parse_timestamp(session["closed_at"])
    if reserved >= closed:
        raise MechanicsError(
            "SEM_A0_IDENTITY_SESSION_ORDER",
            "session reservation must precede close",
        )
    previous: Optional[str] = None
    for index, slot in enumerate(session["slots"]):
        if slot["slot_ordinal"] != index:
            raise MechanicsError(
                "SEM_A0_IDENTITY_SLOT_ORDINAL",
                "slot ordinals must be contiguous",
            )
        if slot["slot_id"] != derive_slot_id(session, index):
            raise MechanicsError(
                "SEM_A0_IDENTITY_SLOT_ID",
                "slot id is not pre-content and canonical",
            )
        if slot["previous_slot_entry_sha256"] != previous:
            raise MechanicsError(
                "SEM_A0_IDENTITY_SLOT_CHAIN",
                "slot chain predecessor mismatch",
            )
        if slot["slot_entry_sha256"] != slot_entry_sha256(slot):
            raise MechanicsError(
                "SEM_A0_IDENTITY_SLOT_CHAIN",
                "slot entry hash mismatch",
            )
        slot_reserved = parse_timestamp(slot["reserved_at"])
        sealed = parse_timestamp(slot["sealed_at"])
        if not (reserved <= slot_reserved < sealed <= closed):
            raise MechanicsError(
                "SEM_A0_IDENTITY_SLOT_ORDER",
                "self-reported reservation/seal order is inconsistent",
            )
        previous = slot["slot_entry_sha256"]
    if session["chain_tip_sha256"] != previous:
        raise MechanicsError(
            "SEM_A0_IDENTITY_SLOT_CHAIN",
            "session chain tip mismatch",
        )


def _default_unparseable_identity_evidence(
    cutoff: int,
) -> Dict[str, Any]:
    return {
        "evidence_atoms": [],
        "target_state_variable_claims": [],
        "temporal_interval": {
            "start_observation_ordinal": 0,
            "end_observation_ordinal": cutoff,
        },
        "atomicity_claim": "unknown",
        "unanchored_discovery": True,
        "unanchored_reason": "raw_source_unparseable",
    }


def _schema_error_roster(
    value: Any,
    ref: str,
    registry: Registry,
    code: str,
) -> List[Dict[str, str]]:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$ref": ref,
    }
    errors = sorted(
        Draft202012Validator(schema, registry=registry).iter_errors(value),
        key=lambda item: list(item.absolute_path),
    )
    roster: List[Dict[str, str]] = []
    for error in errors:
        pointer = ""
        for part in error.absolute_path:
            pointer += "/%s" % str(part).replace("~", "~0").replace("/", "~1")
        roster.append(
            {
                "code": code,
                "json_pointer": pointer or "/",
            }
        )
    return roster


def parse_raw_identity_bytes(
    raw_bytes: bytes,
    cutoff: int,
    registry: Registry,
) -> Tuple[str, List[Dict[str, str]], Any, Dict[str, Any]]:
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return (
            "typed_projection_invalid",
            [{"code": "RAW_UTF8_INVALID", "json_pointer": "/"}],
            None,
            _default_unparseable_identity_evidence(cutoff),
        )
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
        )
    except DuplicateKeyError:
        return (
            "typed_projection_invalid",
            [{"code": "RAW_JSON_DUPLICATE_KEY", "json_pointer": "/"}],
            None,
            _default_unparseable_identity_evidence(cutoff),
        )
    except json.JSONDecodeError:
        return (
            "typed_projection_invalid",
            [{"code": "RAW_JSON_INVALID", "json_pointer": "/"}],
            None,
            _default_unparseable_identity_evidence(cutoff),
        )
    if not isinstance(parsed, dict):
        return (
            "typed_projection_invalid",
            [{"code": "RAW_TOP_LEVEL_OBJECT", "json_pointer": "/"}],
            None,
            _default_unparseable_identity_evidence(cutoff),
        )
    if set(parsed) != {"typed_projection", "identity_evidence"}:
        return (
            "typed_projection_invalid",
            [{"code": "RAW_TOP_LEVEL_FIELDS", "json_pointer": "/"}],
            None,
            _default_unparseable_identity_evidence(cutoff),
        )
    typed = parsed["typed_projection"]
    identity = parsed["identity_evidence"]
    raw_schema_id = (
        "https://gui-agent-memory.local/schemas/"
        "stage0f_raw_event_identity_envelope.schema.json"
    )
    errors = _schema_error_roster(
        typed,
        raw_schema_id + "#/$defs/typed_projection",
        registry,
        "TYPED_PROJECTION_SCHEMA",
    )
    errors.extend(
        _schema_error_roster(
            identity,
            raw_schema_id + "#/$defs/identity_evidence",
            registry,
            "IDENTITY_EVIDENCE_SCHEMA",
        )
    )
    errors = sorted(
        errors,
        key=lambda item: (item["code"], item["json_pointer"]),
    )
    if errors:
        return (
            "typed_projection_invalid",
            errors,
            None,
            (
                identity
                if not any(
                    item["code"] == "IDENTITY_EVIDENCE_SCHEMA"
                    for item in errors
                )
                else _default_unparseable_identity_evidence(cutoff)
            ),
        )
    return "typed_projection_valid", [], typed, identity


def derive_raw_envelope_id(envelope: Mapping[str, Any]) -> str:
    return canonical_sha256(
        [
            "stage0f-raw-envelope-v1",
            envelope["identity_stack_manifest_ref"]["sha256"],
            envelope["unit_alias"],
            envelope["boundary_location_id"],
            envelope["a0_input_ref"]["sha256"],
            envelope["submission_session_ref"]["sha256"],
            envelope["submission_slot_id"],
            envelope["annotator_principal_commitment_sha256"],
            envelope["raw_source"]["content_sha256"],
            envelope["raw_source"]["byte_length"],
            envelope["parse_status"],
            sorted(
                envelope["parse_errors"],
                key=lambda item: (item["code"], item["json_pointer"]),
            ),
            envelope["typed_projection"],
            envelope["identity_evidence"],
            envelope["parser_contract"],
            envelope["version_hashes"],
        ]
    )


def build_raw_envelope(
    manifest: Mapping[str, Any],
    a0_input: Mapping[str, Any],
    session: Mapping[str, Any],
    slot_index: int,
    raw_bytes: bytes,
    frozen_at: str,
    registry: Registry,
) -> Dict[str, Any]:
    slot = session["slots"][slot_index]
    status, errors, typed, identity = parse_raw_identity_bytes(
        raw_bytes,
        a0_input["cutoff_observation_ordinal"],
        registry,
    )
    envelope: Dict[str, Any] = {
        "artifact_type": "raw_event_identity_envelope",
        "schema_version": SCHEMA_VERSION,
        "canonicalization": CANONICALIZATION,
        "artifact_id": "raw-envelope-placeholder",
        "identity_stack_manifest_ref": artifact_ref(manifest),
        "unit_alias": a0_input["unit_alias"],
        "boundary_location_id": a0_input["boundary_location_id"],
        "a0_input_ref": artifact_ref(a0_input),
        "submission_session_ref": artifact_ref(session),
        "submission_slot_id": slot["slot_id"],
        "annotator_alias": session["annotator_alias"],
        "annotator_principal_commitment_sha256": session[
            "annotator_principal_commitment_sha256"
        ],
        "raw_envelope_id": "3" * 64,
        "raw_source": {
            "relative_path": slot["sealed_source"]["relative_path"],
            "content_sha256": bytes_sha256(raw_bytes),
            "media_type": "application/json",
            "byte_length": len(raw_bytes),
        },
        "parser_contract": {
            "parser_id": PARSER_ID,
            "parser_executable_sha256": verifier_file_sha256(),
            "projection_id": PARSER_PROJECTION_ID,
        },
        "parse_status": status,
        "parse_errors": errors,
        "typed_projection": typed,
        "identity_evidence": identity,
        "version_hashes": {
            "schema_bundle_sha256": manifest[
                "identity_schema_bundle_sha256"
            ],
            "codebook_sha256": manifest["identity_codebook"]["sha256"],
            "matcher_spec_sha256": manifest["matcher_spec"]["sha256"],
        },
        "frozen_at": frozen_at,
    }
    envelope["raw_envelope_id"] = derive_raw_envelope_id(envelope)
    envelope["artifact_id"] = (
        "raw-envelope-" + envelope["raw_envelope_id"]
    )
    return envelope


def _observation_map(a0_input: Mapping[str, Any]) -> Dict[int, Any]:
    return {
        item["observation_ordinal"]: item
        for item in a0_input["prefix_observations"]
    }


def verify_a0_identity_input(a0_input: Mapping[str, Any]) -> None:
    cutoff = a0_input["cutoff_observation_ordinal"]
    ordinals = [
        item["observation_ordinal"]
        for item in a0_input["prefix_observations"]
    ]
    if ordinals != list(range(cutoff + 1)):
        raise MechanicsError(
            "SEM_A0_IDENTITY_EXACT_ORDINAL_ROSTER",
            "A0 observations must be unique, ordered, and contiguous",
        )
    instruction = a0_input["agent_visible_instruction"]
    if instruction["content_sha256"] != text_sha256(
        instruction["text"]
    ):
        raise MechanicsError(
            "HASH_A0_IDENTITY_INSTRUCTION_CONTENT",
            "A0 instruction hash mismatch",
        )
    for source in a0_input["normative_schema"]["sources"]:
        if source["content_sha256"] != text_sha256(source["content"]):
            raise MechanicsError(
                "HASH_A0_IDENTITY_NORMATIVE_CONTENT",
                "A0 normative source hash mismatch",
            )
    if a0_input["candidate_locator"][
        "update_observation_ordinal"
    ] > cutoff:
        raise MechanicsError(
            "SEM_A0_IDENTITY_CANDIDATE_LOCATOR",
            "candidate locator exceeds A0 cutoff",
        )


def _selector_sort_key(atom: Mapping[str, Any]) -> Tuple[int, bytes]:
    return (
        int(atom["observation_ordinal"]),
        canonical_bytes(atom["selector"]),
    )


def _validate_and_render_evidence(
    envelope: Mapping[str, Any],
    a0_input: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    evidence = envelope["identity_evidence"]
    interval = evidence["temporal_interval"]
    start = interval["start_observation_ordinal"]
    end = interval["end_observation_ordinal"]
    cutoff = a0_input["cutoff_observation_ordinal"]
    if start > end:
        raise MechanicsError(
            "SEM_A0_IDENTITY_REVIEW_INTERVAL_ORDER",
            "identity interval start exceeds end",
        )
    if end > cutoff:
        raise MechanicsError(
            "SEM_A0_IDENTITY_REVIEW_CUTOFF",
            "identity interval exceeds A0 cutoff",
        )
    observations = _observation_map(a0_input)
    rendered: List[Dict[str, Any]] = []
    seen = set()
    for atom in sorted(evidence["evidence_atoms"], key=_selector_sort_key):
        ordinal = atom["observation_ordinal"]
        if ordinal not in observations or ordinal > cutoff:
            raise MechanicsError(
                "SEM_A0_IDENTITY_REVIEW_CUTOFF",
                "evidence ordinal is absent or after cutoff",
            )
        if ordinal < start or ordinal > end:
            raise MechanicsError(
                "SEM_A0_IDENTITY_REVIEW_INTERVAL_EVIDENCE",
                "evidence ordinal falls outside the event interval",
            )
        if atom["artifact_id"] != a0_input["artifact_id"]:
            raise MechanicsError(
                "SEM_A0_IDENTITY_REVIEW_CROSS_ARTIFACT_SPLICE",
                "evidence artifact does not match A0 input",
            )
        observation = observations[ordinal]
        if atom["content_sha256"] != canonical_sha256(observation):
            raise MechanicsError(
                "HASH_A0_IDENTITY_EVIDENCE_CONTENT",
                "evidence content hash does not bind the observation",
            )
        atom_key = canonical_sha256(atom)
        if atom_key in seen:
            raise MechanicsError(
                "SEM_A0_IDENTITY_REVIEW_DUPLICATE_EVIDENCE",
                "duplicate evidence atom",
            )
        seen.add(atom_key)
        selector = atom["selector"]
        selector_type = selector["selector_type"]
        text = observation["agent_visible_text"]
        if selector_type == "whole_observation":
            rendition = (
                {
                    "rendition_type": "utf8_text",
                    "text": text,
                }
                if isinstance(text, str) and text
                else {
                    "rendition_type": "unavailable",
                    "reason": "agent_visible_text_missing",
                }
            )
        elif selector_type == "text_span":
            if not isinstance(text, str):
                raise MechanicsError(
                    "SEM_A0_IDENTITY_REVIEW_SELECTOR_INVALID",
                    "text selector requires agent-visible text",
                )
            span_start = selector["start"]
            span_end = selector["end"]
            if not (0 <= span_start < span_end <= len(text)):
                raise MechanicsError(
                    "SEM_A0_IDENTITY_REVIEW_SELECTOR_INVALID",
                    "text selector is reversed or out of bounds",
                )
            selected = text[span_start:span_end]
            if not selected:
                raise MechanicsError(
                    "SEM_A0_IDENTITY_REVIEW_SELECTOR_INVALID",
                    "text selector produced an empty rendition",
                )
            rendition = {
                "rendition_type": "utf8_text",
                "text": selected,
            }
        else:
            raise MechanicsError(
                "SEM_A0_IDENTITY_REVIEW_SELECTOR_UNSUPPORTED",
                "bbox/DOM selector requires a separately verified asset",
            )
        rendered.append(
            {
                "source_observation_ordinal": ordinal,
                "rendition": rendition,
            }
        )
    for claim in evidence["target_state_variable_claims"]:
        statement = claim["statement"]
        if not statement.strip():
            raise MechanicsError(
                "SEM_A0_RAW_STATE_STATEMENT_EMPTY",
                "state-variable statement is blank",
            )
        if claim["statement_sha256"] != text_sha256(statement):
            raise MechanicsError(
                "SEM_A0_RAW_STATEMENT_HASH",
                "state-variable statement hash mismatch",
            )
    return rendered


def verify_raw_envelope(
    bundle_root: Path,
    envelope: Mapping[str, Any],
    session: Mapping[str, Any],
    manifest: Mapping[str, Any],
    a0_input: Mapping[str, Any],
    registry: Registry,
    verified_at: str,
) -> Dict[str, Any]:
    if envelope["identity_stack_manifest_ref"] != artifact_ref(manifest):
        raise MechanicsError(
            "SEM_A0_RAW_MANIFEST_BINDING",
            "raw envelope does not bind the current manifest",
        )
    if envelope["a0_input_ref"] != artifact_ref(a0_input):
        raise MechanicsError(
            "SEM_A0_RAW_A0_BINDING",
            "raw envelope does not bind the current A0 input",
        )
    if envelope["submission_session_ref"] != artifact_ref(session):
        raise MechanicsError(
            "SEM_A0_RAW_SLOT_BINDING",
            "raw envelope does not bind the submission session",
        )
    if (
        envelope["unit_alias"] != session["unit_alias"]
        or envelope["boundary_location_id"]
        != session["boundary_location_id"]
        or envelope["annotator_alias"] != session["annotator_alias"]
        or envelope["annotator_principal_commitment_sha256"]
        != session["annotator_principal_commitment_sha256"]
    ):
        raise MechanicsError(
            "SEM_A0_RAW_UNIT_LOCATION_PRINCIPAL",
            "raw envelope and submission session disagree",
        )
    slots = [
        slot
        for slot in session["slots"]
        if slot["slot_id"] == envelope["submission_slot_id"]
    ]
    if len(slots) != 1:
        raise MechanicsError(
            "SEM_A0_RAW_SLOT_BINDING",
            "raw envelope slot is missing or duplicated",
        )
    slot = slots[0]
    if envelope["raw_source"]["relative_path"] != slot["sealed_source"][
        "relative_path"
    ]:
        raise MechanicsError(
            "SEM_A0_RAW_SLOT_BINDING",
            "raw path differs from the sealed slot",
        )
    raw_bytes = read_immutable_contained_bytes(
        bundle_root,
        envelope["raw_source"]["relative_path"],
    )
    actual_hash = bytes_sha256(raw_bytes)
    actual_length = len(raw_bytes)
    if (
        actual_hash != envelope["raw_source"]["content_sha256"]
        or actual_length != envelope["raw_source"]["byte_length"]
        or actual_hash != slot["sealed_source"]["content_sha256"]
        or actual_length != slot["sealed_source"]["byte_length"]
    ):
        raise MechanicsError(
            "HASH_A0_RAW_BYTES_HASH_LENGTH",
            "hash and length must come from the same immutable byte buffer",
        )
    if envelope["parser_contract"] != {
        "parser_id": PARSER_ID,
        "parser_executable_sha256": verifier_file_sha256(),
        "projection_id": PARSER_PROJECTION_ID,
    }:
        raise MechanicsError(
            "HASH_A0_RAW_PARSER_IDENTITY",
            "raw parser contract does not bind this executable",
        )
    if envelope["version_hashes"] != {
        "schema_bundle_sha256": manifest[
            "identity_schema_bundle_sha256"
        ],
        "codebook_sha256": manifest["identity_codebook"]["sha256"],
        "matcher_spec_sha256": manifest["matcher_spec"]["sha256"],
    }:
        raise MechanicsError(
            "HASH_A0_RAW_VERSION_BINDING",
            "raw envelope versions do not match the frozen identity stack",
        )
    status, errors, typed, identity = parse_raw_identity_bytes(
        raw_bytes,
        a0_input["cutoff_observation_ordinal"],
        registry,
    )
    if envelope["parse_status"] != status:
        raise MechanicsError(
            "SEM_A0_RAW_PARSE_STATUS",
            "raw parse status differs from replay",
        )
    if envelope["parse_errors"] != errors:
        raise MechanicsError(
            "SEM_A0_RAW_ERROR_ROSTER",
            "raw parse-error roster differs from replay",
        )
    if envelope["typed_projection"] != typed:
        raise MechanicsError(
            "SEM_A0_RAW_TYPED_PROJECTION",
            "typed projection differs from parser replay",
        )
    if envelope["identity_evidence"] != identity:
        raise MechanicsError(
            "SEM_A0_RAW_IDENTITY_EVIDENCE",
            "identity evidence differs from parser replay",
        )
    _validate_and_render_evidence(envelope, a0_input)
    expected_id = derive_raw_envelope_id(envelope)
    if envelope["raw_envelope_id"] != expected_id:
        raise MechanicsError(
            "SEM_A0_RAW_ENVELOPE_ID",
            "raw envelope id is not the canonical preimage hash",
        )
    if envelope["artifact_id"] != "raw-envelope-" + expected_id:
        raise MechanicsError(
            "SEM_A0_RAW_ENVELOPE_ARTIFACT_ID",
            "raw envelope artifact id is not derived",
        )
    if parse_timestamp(envelope["frozen_at"]) < parse_timestamp(
        session["closed_at"]
    ):
        raise MechanicsError(
            "SEM_A0_RAW_FREEZE_ORDER",
            "raw envelope predates the closed submission session",
        )
    receipt: Dict[str, Any] = {
        "artifact_type": "raw_envelope_verification_receipt",
        "schema_version": SCHEMA_VERSION,
        "canonicalization": CANONICALIZATION,
        "artifact_id": "raw-receipt-placeholder",
        "receipt_id": "4" * 64,
        "identity_stack_manifest_ref": artifact_ref(manifest),
        "submission_session_ref": artifact_ref(session),
        "submission_slot_id": envelope["submission_slot_id"],
        "raw_envelope_ref": artifact_ref(envelope),
        "raw_source_sha256": actual_hash,
        "verifier_executable_sha256": verifier_file_sha256(),
        "checks": RAW_CHECKS,
        "authority": {
            "raw_byte_parse_binding": "verified_local_executable",
            "slot_ordering": "self_reported_local_order_only",
            "identity_evidence_provenance": (
                "partial_annotator_selected"
            ),
            "external_roster_authority": "not_established",
        },
        "verified_at": verified_at,
    }
    core = dict(receipt)
    core.pop("artifact_id")
    core.pop("receipt_id")
    core.pop("verified_at")
    receipt["receipt_id"] = canonical_sha256(
        ["stage0f-raw-envelope-receipt-v1", core]
    )
    receipt["artifact_id"] = "raw-receipt-" + receipt["receipt_id"]
    return receipt


def alias_key_commitment(key_hex: str, nonce_hex: str) -> str:
    return canonical_sha256(
        ["stage0f-alias-key-v1", nonce_hex, key_hex]
    )


def derive_alias(
    key_hex: str,
    nonce_hex: str,
    session_slot_id: str,
    domain: str,
    index: int,
) -> str:
    message = canonical_bytes(
        [
            ALIAS_SERIALIZATION,
            nonce_hex,
            session_slot_id,
            domain,
            index,
        ]
    )
    return hmac.new(
        bytes.fromhex(key_hex),
        message,
        hashlib.sha256,
    ).hexdigest()


def derive_real_pair_id(
    manifest: Mapping[str, Any],
    left_session: Mapping[str, Any],
    right_session: Mapping[str, Any],
    left_envelope: Mapping[str, Any],
    right_envelope: Mapping[str, Any],
) -> str:
    return canonical_sha256(
        [
            "stage0f-real-pair-v1",
            manifest["artifact_id"],
            left_envelope["unit_alias"],
            left_envelope["boundary_location_id"],
            left_session["session_id"],
            right_session["session_id"],
            left_envelope["raw_envelope_id"],
            right_envelope["raw_envelope_id"],
            artifact_ref(manifest)["sha256"],
        ]
    )


def derive_review_session_slot_id(
    manifest: Mapping[str, Any],
    a0_input: Mapping[str, Any],
    left_session: Mapping[str, Any],
    right_session: Mapping[str, Any],
) -> str:
    return canonical_sha256(
        [
            "stage0f-review-session-slot-v1",
            artifact_ref(manifest)["sha256"],
            a0_input["unit_alias"],
            a0_input["boundary_location_id"],
            left_session["session_id"],
            right_session["session_id"],
            0,
        ]
    )


def _binding_for_side(
    side: str,
    session: Mapping[str, Any],
    envelope: Mapping[str, Any],
    key_hex: str,
    nonce_hex: str,
    session_slot_id: str,
) -> Dict[str, Any]:
    evidence = sorted(
        envelope["identity_evidence"]["evidence_atoms"],
        key=_selector_sort_key,
    )
    return {
        "submission_session_ref": artifact_ref(session),
        "submission_slot_id": envelope["submission_slot_id"],
        "raw_envelope_ref": artifact_ref(envelope),
        "view_alias": derive_alias(
            key_hex,
            nonce_hex,
            session_slot_id,
            "view-%s" % side,
            0,
        ),
        "evidence_aliases": [
            {
                "evidence_index": index,
                "evidence_alias": derive_alias(
                    key_hex,
                    nonce_hex,
                    session_slot_id,
                    "evidence-%s" % side,
                    index,
                ),
            }
            for index in range(len(evidence))
        ],
    }


def derive_sidecar_id(sidecar: Mapping[str, Any]) -> str:
    return canonical_sha256(
        [
            "stage0f-alias-sidecar-v1",
            sidecar["identity_stack_manifest_ref"]["sha256"],
            sidecar["real_pair_id"],
            sorted(
                [
                    sidecar["left_binding"]["submission_session_ref"],
                    sidecar["right_binding"]["submission_session_ref"],
                ],
                key=canonical_bytes,
            ),
            sorted(
                sidecar["raw_verification_receipt_refs"],
                key=canonical_bytes,
            ),
            sidecar["alias_key_commitment_sha256"],
            sidecar["session_slot_id"],
            sidecar["pair_alias"],
            sidecar["packet_alias"],
            sidecar["context_alias"],
            sidecar["left_binding"],
            sidecar["right_binding"],
            sidecar["redaction_policy_sha256"],
            sidecar["redactor_executable_sha256"],
        ]
    )


def build_alias_sidecar(
    manifest: Mapping[str, Any],
    a0_input: Mapping[str, Any],
    left_session: Mapping[str, Any],
    right_session: Mapping[str, Any],
    left_envelope: Mapping[str, Any],
    right_envelope: Mapping[str, Any],
    left_raw_receipt: Mapping[str, Any],
    right_raw_receipt: Mapping[str, Any],
    alias_key_hex: str,
    alias_nonce_hex: str,
) -> Dict[str, Any]:
    session_slot_id = derive_review_session_slot_id(
        manifest,
        a0_input,
        left_session,
        right_session,
    )
    sidecar: Dict[str, Any] = {
        "artifact_type": "identity_alias_redaction_sidecar",
        "schema_version": SCHEMA_VERSION,
        "canonicalization": CANONICALIZATION,
        "artifact_id": "identity-sidecar-placeholder",
        "visibility": "coordinator_only_never_reviewer_visible",
        "sidecar_id": "5" * 64,
        "identity_stack_manifest_ref": artifact_ref(manifest),
        "a0_input_ref": artifact_ref(a0_input),
        "unit_alias": a0_input["unit_alias"],
        "boundary_location_id": a0_input["boundary_location_id"],
        "session_slot_id": session_slot_id,
        "alias_key_hex": alias_key_hex,
        "alias_nonce_hex": alias_nonce_hex,
        "alias_key_commitment_sha256": alias_key_commitment(
            alias_key_hex,
            alias_nonce_hex,
        ),
        "entropy_authority": "local_csprng_unattested",
        "key_draw_count": 1,
        "retry_count": 0,
        "real_pair_id": derive_real_pair_id(
            manifest,
            left_session,
            right_session,
            left_envelope,
            right_envelope,
        ),
        "pair_alias": derive_alias(
            alias_key_hex,
            alias_nonce_hex,
            session_slot_id,
            "pair",
            0,
        ),
        "packet_alias": derive_alias(
            alias_key_hex,
            alias_nonce_hex,
            session_slot_id,
            "packet",
            0,
        ),
        "context_alias": derive_alias(
            alias_key_hex,
            alias_nonce_hex,
            session_slot_id,
            "context",
            0,
        ),
        "left_binding": _binding_for_side(
            "left",
            left_session,
            left_envelope,
            alias_key_hex,
            alias_nonce_hex,
            session_slot_id,
        ),
        "right_binding": _binding_for_side(
            "right",
            right_session,
            right_envelope,
            alias_key_hex,
            alias_nonce_hex,
            session_slot_id,
        ),
        "raw_verification_receipt_refs": sorted(
            [
                artifact_ref(left_raw_receipt),
                artifact_ref(right_raw_receipt),
            ],
            key=canonical_bytes,
        ),
        "redaction_policy_sha256": manifest["redaction_policy"][
            "sha256"
        ],
        "redactor_executable_sha256": manifest[
            "redactor_executable"
        ]["sha256"],
    }
    sidecar["sidecar_id"] = derive_sidecar_id(sidecar)
    sidecar["artifact_id"] = "identity-sidecar-" + sidecar["sidecar_id"]
    return sidecar


def verify_sidecar(
    sidecar: Mapping[str, Any],
    manifest: Mapping[str, Any],
    a0_input: Mapping[str, Any],
    left_session: Mapping[str, Any],
    right_session: Mapping[str, Any],
    left_envelope: Mapping[str, Any],
    right_envelope: Mapping[str, Any],
    left_raw_receipt: Mapping[str, Any],
    right_raw_receipt: Mapping[str, Any],
) -> None:
    aliases = [
        sidecar["pair_alias"],
        sidecar["packet_alias"],
        sidecar["context_alias"],
        sidecar["left_binding"]["view_alias"],
        sidecar["right_binding"]["view_alias"],
    ]
    aliases.extend(
        item["evidence_alias"]
        for side in ("left_binding", "right_binding")
        for item in sidecar[side]["evidence_aliases"]
    )
    if len(aliases) != len(set(aliases)):
        raise MechanicsError(
            "SEM_A0_IDENTITY_REVIEW_ALIAS_COLLISION",
            "packet-local aliases are not injective",
        )
    expected = build_alias_sidecar(
        manifest,
        a0_input,
        left_session,
        right_session,
        left_envelope,
        right_envelope,
        left_raw_receipt,
        right_raw_receipt,
        sidecar["alias_key_hex"],
        sidecar["alias_nonce_hex"],
    )
    if sidecar != expected:
        raise MechanicsError(
            "SEM_A0_IDENTITY_ALIAS_DERIVATION",
            "sidecar aliases or private bindings do not exactly replay",
        )
    if left_session["side"] != "left" or right_session["side"] != "right":
        raise MechanicsError(
            "SEM_A0_IDENTITY_REVIEW_SIDE_ORDER",
            "left/right order is not the precommitted session order",
        )
    if (
        left_session["annotator_alias"] == right_session["annotator_alias"]
        or left_session["annotator_principal_commitment_sha256"]
        == right_session["annotator_principal_commitment_sha256"]
    ):
        raise MechanicsError(
            "SEM_A0_IDENTITY_REVIEW_CROSS_ANNOTATOR",
            "pair sides are not locally distinct principals",
        )
    if left_envelope["raw_envelope_id"] == right_envelope["raw_envelope_id"]:
        raise MechanicsError(
            "SEM_A0_IDENTITY_REVIEW_SAME_RAW",
            "same raw envelope cannot occupy both pair sides",
        )


def allowed_identity_projection(
    envelope: Mapping[str, Any],
    a0_input: Mapping[str, Any],
) -> Dict[str, Any]:
    rendered = _validate_and_render_evidence(envelope, a0_input)
    return {
        "evidence_presentations": rendered,
        "temporal_interval": copy.deepcopy(
            envelope["identity_evidence"]["temporal_interval"]
        ),
    }


def build_review_packet(
    sidecar: Mapping[str, Any],
    left_envelope: Mapping[str, Any],
    right_envelope: Mapping[str, Any],
    a0_input: Mapping[str, Any],
) -> Dict[str, Any]:
    def view(
        side: str,
        envelope: Mapping[str, Any],
    ) -> Dict[str, Any]:
        binding = sidecar["%s_binding" % side]
        projection = allowed_identity_projection(envelope, a0_input)
        aliases = binding["evidence_aliases"]
        presentations = projection["evidence_presentations"]
        if len(aliases) != len(presentations):
            raise MechanicsError(
                "SEM_A0_IDENTITY_ALIAS_MAPPING_COVERAGE",
                "evidence aliases do not cover the allowed projection",
            )
        return {
            "view_alias": binding["view_alias"],
            "evidence_presentations": [
                {
                    "evidence_alias": aliases[index]["evidence_alias"],
                    "source_observation_ordinal": item[
                        "source_observation_ordinal"
                    ],
                    "rendition": item["rendition"],
                }
                for index, item in enumerate(presentations)
            ],
            "temporal_interval": projection["temporal_interval"],
            "atomicity_question_id": ATOMICITY_QUESTION_ID,
        }

    packet_alias = sidecar["packet_alias"]
    return {
        "artifact_type": "pairwise_identity_review_packet",
        "schema_version": SCHEMA_VERSION,
        "canonicalization": CANONICALIZATION,
        "artifact_id": "identity-packet-" + packet_alias,
        "packet_alias": packet_alias,
        "pair_alias": sidecar["pair_alias"],
        "context_alias": sidecar["context_alias"],
        "review_protocol_id": (
            "stage0f-isolated-pairwise-identity-review-v1"
        ),
        "redaction_policy_id": POLICY_ID,
        "left_identity_view": view("left", left_envelope),
        "right_identity_view": view("right", right_envelope),
    }


def reviewer_transcript(packet: Mapping[str, Any]) -> Dict[str, Any]:
    packet_bytes = canonical_bytes(packet)
    return {
        "visible_files": [
            {
                "file_slot": "f0000",
                "safe_filename": "f0000.json",
                "media_type": "application/json",
                "canonical_bytes_sha256": bytes_sha256(packet_bytes),
                "byte_length": len(packet_bytes),
                "role": "identity_review_packet",
            }
        ],
        "events": [
            {
                "seq": 0,
                "phase": "delivery",
                "actor": "coordinator",
                "kind": "packet_delivered",
                "template_id": "stage0f-review-delivery-v1",
                "payload": {"file_slot": "f0000"},
            }
        ],
        "terminal_status": "READY",
    }


def _collect_string_values(node: Any) -> List[str]:
    values: List[str] = []
    if isinstance(node, dict):
        for value in node.values():
            values.extend(_collect_string_values(value))
    elif isinstance(node, list):
        for value in node:
            values.extend(_collect_string_values(value))
    elif isinstance(node, str):
        values.append(node)
    return values


def _private_sensitive_values(
    manifest: Mapping[str, Any],
    a0_input: Mapping[str, Any],
    sessions: Sequence[Mapping[str, Any]],
    envelopes: Sequence[Mapping[str, Any]],
) -> set:
    values = {
        manifest["artifact_id"],
        artifact_ref(manifest)["sha256"],
        a0_input["artifact_id"],
        artifact_ref(a0_input)["sha256"],
        a0_input["unit_alias"],
        a0_input["boundary_location_id"],
    }
    for session in sessions:
        values.update(
            {
                session["artifact_id"],
                artifact_ref(session)["sha256"],
                session["session_id"],
                session["annotator_alias"],
                session["annotator_principal_commitment_sha256"],
                session["append_only_channel_id"],
            }
        )
        for slot in session["slots"]:
            values.add(slot["slot_id"])
            values.add(slot["sealed_source"]["relative_path"])
            values.add(slot["sealed_source"]["content_sha256"])
    for envelope in envelopes:
        values.update(
            {
                envelope["artifact_id"],
                artifact_ref(envelope)["sha256"],
                envelope["raw_envelope_id"],
                envelope["raw_source"]["relative_path"],
                envelope["raw_source"]["content_sha256"],
            }
        )
        typed = envelope["typed_projection"]
        if isinstance(typed, dict):
            values.update(_collect_string_values(typed))
        values.update(
            _collect_string_values(
                envelope["identity_evidence"][
                    "target_state_variable_claims"
                ]
            )
        )
    return {value for value in values if isinstance(value, str)}


def assert_no_private_value_visible(
    packet: Mapping[str, Any],
    private_values: Iterable[str],
) -> None:
    visible = set(_collect_string_values(packet))
    leaked = sorted(visible.intersection(set(private_values)))
    if leaked:
        raise MechanicsError(
            "SEM_A0_IDENTITY_REVIEW_REAL_REF_LEAK",
            "review packet exposes private values: %s" % leaked[:3],
        )


def _mutate_forbidden_projection(
    envelope: Mapping[str, Any],
    suffix: str,
) -> Dict[str, Any]:
    mutated = copy.deepcopy(envelope)
    mutated["artifact_id"] = "raw-envelope-counterfactual-" + suffix
    mutated["raw_envelope_id"] = hashlib.sha256(
        ("counterfactual-" + suffix).encode("utf-8")
    ).hexdigest()
    mutated["annotator_alias"] = "counterfactual-" + suffix
    mutated["annotator_principal_commitment_sha256"] = hashlib.sha256(
        ("principal-" + suffix).encode("utf-8")
    ).hexdigest()
    mutated["raw_source"]["relative_path"] = (
        "counterfactual/%s.json" % suffix
    )
    mutated["raw_source"]["content_sha256"] = hashlib.sha256(
        ("raw-" + suffix).encode("utf-8")
    ).hexdigest()
    mutated["raw_source"]["byte_length"] += 17
    mutated["identity_evidence"]["atomicity_claim"] = (
        "split_merge_possible"
        if mutated["identity_evidence"]["atomicity_claim"] != (
            "split_merge_possible"
        )
        else "unknown"
    )
    mutated["identity_evidence"]["target_state_variable_claims"] = [
        {
            "claim_id": "STATE-COUNTERFACTUAL",
            "statement": "Forbidden counterfactual %s" % suffix,
            "statement_sha256": text_sha256(
                "Forbidden counterfactual %s" % suffix
            ),
        }
    ]
    typed = mutated["typed_projection"]
    if isinstance(typed, dict):
        typed["p_old_proposition_id"] = "PROP-CF-OLD-%s" % suffix.upper()
        typed["p_new_proposition_id"] = "PROP-CF-NEW-%s" % suffix.upper()
        typed["update_source_labels"] = ["task_goal_changed"]
        typed["normative_action_difference"] = (
            "Forbidden difference %s" % suffix
        )
        typed["affected_obligation_ids"] = [
            "O-CF-%s" % suffix.upper()
        ]
        typed["boundary_type"] = "artifact_write"
    mutated["frozen_at"] = "2026-07-28T19:59:59+08:00"
    return mutated


def verify_enumerated_conditional_noninterference(
    packet: Mapping[str, Any],
    sidecar: Mapping[str, Any],
    left_envelope: Mapping[str, Any],
    right_envelope: Mapping[str, Any],
    a0_input: Mapping[str, Any],
) -> None:
    baseline = canonical_bytes(reviewer_transcript(packet))
    mutations = [
        (
            _mutate_forbidden_projection(left_envelope, "left"),
            right_envelope,
        ),
        (
            left_envelope,
            _mutate_forbidden_projection(right_envelope, "right"),
        ),
        (
            _mutate_forbidden_projection(left_envelope, "both-left"),
            _mutate_forbidden_projection(right_envelope, "both-right"),
        ),
    ]
    for mutated_left, mutated_right in mutations:
        counterfactual_packet = build_review_packet(
            sidecar,
            mutated_left,
            mutated_right,
            a0_input,
        )
        transcript = canonical_bytes(
            reviewer_transcript(counterfactual_packet)
        )
        if transcript != baseline:
            raise MechanicsError(
                "SEM_A0_IDENTITY_REDACTOR_NONINTERFERENCE",
                "reviewer transcript changed under forbidden mutation",
            )
    allowed_mutation = copy.deepcopy(left_envelope)
    allowed_mutation["identity_evidence"]["temporal_interval"][
        "start_observation_ordinal"
    ] = 0
    changed_packet = build_review_packet(
        sidecar,
        allowed_mutation,
        right_envelope,
        a0_input,
    )
    if canonical_bytes(changed_packet) == canonical_bytes(packet):
        raise MechanicsError(
            "SEM_A0_IDENTITY_REDACTOR_ALLOWED_PROJECTION_IGNORED",
            "allowed projection mutation did not change the packet",
        )


def build_redaction_receipt(
    manifest: Mapping[str, Any],
    sidecar: Mapping[str, Any],
    left_raw_receipt: Mapping[str, Any],
    right_raw_receipt: Mapping[str, Any],
    packet: Mapping[str, Any],
    left_envelope: Mapping[str, Any],
    right_envelope: Mapping[str, Any],
    a0_input: Mapping[str, Any],
    verified_at: str,
) -> Dict[str, Any]:
    safe_projection = {
        "left": allowed_identity_projection(left_envelope, a0_input),
        "right": allowed_identity_projection(right_envelope, a0_input),
    }
    transcript = reviewer_transcript(packet)
    receipt: Dict[str, Any] = {
        "artifact_type": "identity_redaction_verification_receipt",
        "schema_version": SCHEMA_VERSION,
        "canonicalization": CANONICALIZATION,
        "artifact_id": "identity-redaction-receipt-placeholder",
        "receipt_id": "6" * 64,
        "identity_stack_manifest_ref": artifact_ref(manifest),
        "sidecar_ref": artifact_ref(sidecar),
        "raw_verification_receipt_refs": sorted(
            [
                artifact_ref(left_raw_receipt),
                artifact_ref(right_raw_receipt),
            ],
            key=canonical_bytes,
        ),
        "review_packet_ref": artifact_ref(packet),
        "redaction_policy_sha256": manifest["redaction_policy"][
            "sha256"
        ],
        "redactor_executable_sha256": manifest[
            "redactor_executable"
        ]["sha256"],
        "independent_verifier_sha256": verifier_file_sha256(),
        "safe_projection_sha256": canonical_sha256(safe_projection),
        "reviewer_transcript_sha256": canonical_sha256(transcript),
        "checks": REDACTION_CHECKS,
        "authority": {
            "alias_derivation": "local_recomputation_verified",
            "alias_randomness": (
                "key_grinding_and_origin_unattested"
                if sidecar["entropy_authority"] == (
                    "local_csprng_unattested"
                )
                else "external_commit_then_beacon_verified"
            ),
            "sidecar_confidentiality": (
                "self_reported_not_reviewer_visible"
            ),
            "conditional_noninterference": (
                "valid_trace_enumerated_tests_passed_not_universal_proof"
            ),
            "allowed_projection_provenance": (
                "partial_annotator_selected"
            ),
            "reviewer_blindness": (
                "partial_no_external_session_attestation"
            ),
            "virtual_transcript_scope": (
                "canonical_files_and_delivery_only_runtime_metadata_"
                "unattested"
            ),
        },
        "mechanics_level": (
            "l2_single_explicit_valid_pair_redaction_pass"
        ),
        "raw_roster_scope": (
            "exact_over_loaded_closed_single_slot_sessions"
        ),
        "integration_status": "not_integrated_no_a0_barrier",
        "pair_universe_authority": (
            "not_established_no_complete_pair_ledger"
        ),
        "downstream_eligible": False,
        "matcher_authority": (
            "not_established_no_frozen_case_matcher"
        ),
        "agreement_completeness": (
            "not_established_no_frozen_case_matcher"
        ),
        "primary_reliability_eligibility": False,
        "verified_at": verified_at,
    }
    core = dict(receipt)
    core.pop("artifact_id")
    core.pop("receipt_id")
    core.pop("verified_at")
    receipt["receipt_id"] = canonical_sha256(
        ["stage0f-redaction-receipt-v1", core]
    )
    receipt["artifact_id"] = (
        "identity-redaction-receipt-" + receipt["receipt_id"]
    )
    return receipt


def verify_manifest(
    manifest: Mapping[str, Any],
    schemas: Mapping[str, Any],
) -> None:
    if manifest["artifact_id"] != (
        "identity-stack-" + derive_manifest_id(manifest)
    ):
        raise MechanicsError(
            "SEM_IDENTITY_STACK_MANIFEST_ID",
            "identity stack manifest id is not canonical",
        )
    if manifest["identity_schema_bundle_sha256"] != (
        identity_schema_bundle_sha256(schemas)
    ):
        raise MechanicsError(
            "HASH_IDENTITY_SCHEMA_BUNDLE",
            "identity schema bundle hash mismatch",
        )
    expected_files = {
        "identity_codebook": CODEBOOK_RELATIVE_PATH,
        "matcher_spec": MATCHER_SPEC_RELATIVE_PATH,
        "redaction_policy": POLICY_RELATIVE_PATH,
        "redactor_executable": REDACTOR_RELATIVE_PATH,
        "raw_verifier_executable": VERIFIER_RELATIVE_PATH,
    }
    for key, relative_path in expected_files.items():
        commitment = manifest[key]
        if commitment["relative_path"] != relative_path:
            raise MechanicsError(
                "HASH_IDENTITY_STACK_FILE_PATH",
                "%s path is not the registered implementation" % key,
            )
        if commitment["sha256"] != project_file_sha256(relative_path):
            raise MechanicsError(
                "HASH_IDENTITY_STACK_FILE",
                "%s hash mismatch" % key,
            )
    if manifest["runtime_contract"] != runtime_contract():
        raise MechanicsError(
            "ENV_IDENTITY_RUNTIME_CONTRACT",
            "Python/dependency runtime differs from the frozen manifest",
        )
    policy = load_json_no_duplicates(ROOT / POLICY_RELATIVE_PATH)
    required_allowed = {
        "identity_evidence.evidence_atoms.observation_ordinal",
        "identity_evidence.evidence_atoms.selector",
        "identity_evidence.temporal_interval",
        (
            "derived_rendition := execute(selector, "
            "a0_input.prefix_observations[observation_ordinal]."
            "agent_visible_text)"
        ),
    }
    if (
        policy.get("policy_id") != POLICY_ID
        or set(policy.get("allowed_projection", [])) != required_allowed
        or policy.get("reviewer_visible_hashes") != "none"
        or policy.get("reviewer_visible_identifiers")
        != "packet_local_hmac_aliases_only"
    ):
        raise MechanicsError(
            "SEM_A0_REDACTION_POLICY_OUTPUT_MISMATCH",
            "policy does not declare the executable visible projection",
        )


def load_closed_bundle_artifact(path: Path) -> Any:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError as exc:
        raise MechanicsError(
            "IO_IDENTITY_ARTIFACT_LOAD_FAILURE",
            "required identity artifact is missing: %s" % path.name,
        ) from exc
    if stat.S_ISLNK(mode):
        raise MechanicsError(
            "IO_IDENTITY_BUNDLE_SYMLINK",
            "identity artifact must not be a symlink: %s" % path.name,
        )
    if not stat.S_ISREG(mode):
        raise MechanicsError(
            "IO_IDENTITY_ARTIFACT_LOAD_FAILURE",
            "identity artifact is not a regular file: %s" % path.name,
        )
    try:
        return load_json_no_duplicates(path)
    except (UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
        raise MechanicsError(
            "IO_IDENTITY_ARTIFACT_LOAD_FAILURE",
            "cannot load identity artifact %s: %s" % (path.name, exc),
        ) from exc


def verify_closed_bundle_inventory(
    bundle_root: Path,
    artifacts: Mapping[str, Any],
) -> None:
    sessions = [
        artifacts["left_session"],
        artifacts["right_session"],
    ]
    for session in sessions:
        if len(session["slots"]) != 1:
            raise MechanicsError(
                "SEM_A0_IDENTITY_SLOT_ENVELOPE_EXACT_COVERAGE",
                "L2 single-pair bundle requires exactly one slot per side",
            )
    raw_paths = [
        session["slots"][0]["sealed_source"]["relative_path"]
        for session in sessions
    ]
    if len(set(raw_paths)) != 2:
        raise MechanicsError(
            "SEM_A0_IDENTITY_SLOT_SOURCE_UNIQUE",
            "left and right slots require distinct raw source paths",
        )
    expected = set(BUNDLE_FILES.values()).union(raw_paths)
    actual = set()
    for path in bundle_root.rglob("*"):
        if path.is_file() or path.is_symlink():
            actual.add(path.relative_to(bundle_root).as_posix())
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise MechanicsError(
            "IO_IDENTITY_BUNDLE_CLOSED_INVENTORY",
            "closed inventory mismatch; missing=%s extra=%s"
            % (missing, extra),
        )


def verify_local_lifecycle_order(
    artifacts: Mapping[str, Any],
) -> None:
    manifest_time = parse_timestamp(artifacts["manifest"]["frozen_at"])
    a0_time = parse_timestamp(artifacts["a0_input"]["frozen_at"])
    if manifest_time > a0_time:
        raise MechanicsError(
            "SEM_A0_IDENTITY_LOCAL_LIFECYCLE_ORDER",
            "identity stack manifest must not postdate A0 input",
        )
    raw_verified_times = []
    for side in ("left", "right"):
        session = artifacts["%s_session" % side]
        envelope = artifacts["%s_envelope" % side]
        receipt = artifacts["%s_raw_receipt" % side]
        session_reserved = parse_timestamp(session["reserved_at"])
        session_closed = parse_timestamp(session["closed_at"])
        envelope_frozen = parse_timestamp(envelope["frozen_at"])
        receipt_verified = parse_timestamp(receipt["verified_at"])
        if not (
            a0_time
            <= session_reserved
            < session_closed
            <= envelope_frozen
            <= receipt_verified
        ):
            raise MechanicsError(
                "SEM_A0_IDENTITY_LOCAL_LIFECYCLE_ORDER",
                "%s artifact chronology is internally inconsistent" % side,
            )
        raw_verified_times.append(receipt_verified)
    redaction_verified = parse_timestamp(
        artifacts["redaction_receipt"]["verified_at"]
    )
    if redaction_verified < max(raw_verified_times):
        raise MechanicsError(
            "SEM_A0_IDENTITY_LOCAL_LIFECYCLE_ORDER",
            "redaction receipt predates raw verification receipts",
        )


def verify_l2_pair_scope(
    left_session: Mapping[str, Any],
    right_session: Mapping[str, Any],
    left_envelope: Mapping[str, Any],
    right_envelope: Mapping[str, Any],
) -> None:
    if (
        left_session["append_only_channel_id"]
        == right_session["append_only_channel_id"]
    ):
        raise MechanicsError(
            "SEM_A0_IDENTITY_CHANNEL_SEPARATION",
            "left and right sessions share an append-only channel",
        )
    if (
        left_envelope["parse_status"] != "typed_projection_valid"
        or right_envelope["parse_status"] != "typed_projection_valid"
    ):
        raise MechanicsError(
            "SEM_A0_TYPED_INVALID_NOT_REVIEWABLE",
            "typed-invalid raw envelopes cannot receive a review packet",
        )


def verify_bundle(
    bundle_root: Path,
    schema_dir: Path = SCHEMA_DIR,
) -> Dict[str, Any]:
    try:
        schemas, registry = load_schemas(schema_dir)
        validate_schema_set(schemas, registry)
        artifacts = {
            key: load_closed_bundle_artifact(bundle_root / filename)
            for key, filename in BUNDLE_FILES.items()
        }
        verify_closed_bundle_inventory(bundle_root, artifacts)
        schema_for = {
            "manifest": (
                "stage0f_identity_measurement_stack_manifest.schema.json"
            ),
            "a0_input": "stage0f_a0_input.schema.json",
            "left_session": (
                "stage0f_identity_submission_session.schema.json"
            ),
            "right_session": (
                "stage0f_identity_submission_session.schema.json"
            ),
            "left_envelope": (
                "stage0f_raw_event_identity_envelope.schema.json"
            ),
            "right_envelope": (
                "stage0f_raw_event_identity_envelope.schema.json"
            ),
            "left_raw_receipt": (
                "stage0f_raw_envelope_verification_receipt.schema.json"
            ),
            "right_raw_receipt": (
                "stage0f_raw_envelope_verification_receipt.schema.json"
            ),
            "sidecar": "stage0f_identity_alias_sidecar.schema.json",
            "packet": (
                "stage0f_pairwise_identity_review_packet.schema.json"
            ),
            "redaction_receipt": (
                "stage0f_identity_redaction_verification_receipt.schema.json"
            ),
        }
        for key, schema_name in schema_for.items():
            validate_instance(
                artifacts[key],
                schema_name,
                schemas,
                registry,
            )
        manifest = artifacts["manifest"]
        a0_input = artifacts["a0_input"]
        left_session = artifacts["left_session"]
        right_session = artifacts["right_session"]
        left_envelope = artifacts["left_envelope"]
        right_envelope = artifacts["right_envelope"]
        verify_manifest(manifest, schemas)
        verify_a0_identity_input(a0_input)
        verify_local_lifecycle_order(artifacts)
        verify_submission_session(left_session, manifest, a0_input)
        verify_submission_session(right_session, manifest, a0_input)
        verify_l2_pair_scope(
            left_session,
            right_session,
            left_envelope,
            right_envelope,
        )
        if {left_session["side"], right_session["side"]} != {
            "left",
            "right",
        }:
            raise MechanicsError(
                "SEM_A0_IDENTITY_REVIEW_SIDE_ORDER",
                "bundle must contain one left and one right session",
            )
        expected_left_receipt = verify_raw_envelope(
            bundle_root,
            left_envelope,
            left_session,
            manifest,
            a0_input,
            registry,
            artifacts["left_raw_receipt"]["verified_at"],
        )
        expected_right_receipt = verify_raw_envelope(
            bundle_root,
            right_envelope,
            right_session,
            manifest,
            a0_input,
            registry,
            artifacts["right_raw_receipt"]["verified_at"],
        )
        if artifacts["left_raw_receipt"] != expected_left_receipt:
            raise MechanicsError(
                "SEM_A0_RAW_RECEIPT_REPLAY",
                "left raw receipt does not exactly replay",
            )
        if artifacts["right_raw_receipt"] != expected_right_receipt:
            raise MechanicsError(
                "SEM_A0_RAW_RECEIPT_REPLAY",
                "right raw receipt does not exactly replay",
            )
        sidecar = artifacts["sidecar"]
        verify_sidecar(
            sidecar,
            manifest,
            a0_input,
            left_session,
            right_session,
            left_envelope,
            right_envelope,
            expected_left_receipt,
            expected_right_receipt,
        )
        expected_packet = build_review_packet(
            sidecar,
            left_envelope,
            right_envelope,
            a0_input,
        )
        if artifacts["packet"] != expected_packet:
            raise MechanicsError(
                "SEM_A0_IDENTITY_REDACTION_OUTPUT_MISMATCH",
                "review packet differs from exact redactor replay",
            )
        assert_no_private_value_visible(
            expected_packet,
            _private_sensitive_values(
                manifest,
                a0_input,
                [left_session, right_session],
                [left_envelope, right_envelope],
            ),
        )
        verify_enumerated_conditional_noninterference(
            expected_packet,
            sidecar,
            left_envelope,
            right_envelope,
            a0_input,
        )
        expected_redaction_receipt = build_redaction_receipt(
            manifest,
            sidecar,
            expected_left_receipt,
            expected_right_receipt,
            expected_packet,
            left_envelope,
            right_envelope,
            a0_input,
            artifacts["redaction_receipt"]["verified_at"],
        )
        if artifacts["redaction_receipt"] != expected_redaction_receipt:
            raise MechanicsError(
                "SEM_A0_IDENTITY_REDACTION_RECEIPT_REPLAY",
                "redaction receipt does not exactly replay",
            )
        return {
            "valid": True,
            "mechanics_level": (
                "L2_SINGLE_EXPLICIT_VALID_PAIR_REDACTION_PASS"
            ),
            "raw_envelope_mechanics": "VERIFIED_LOCAL_EXECUTABLE",
            "redaction_mechanics": (
                "INDEPENDENT_PACKET_RECOMPUTATION_VERIFIED"
            ),
            "raw_roster_scope": (
                "EXACT_OVER_LOADED_CLOSED_SINGLE_SLOT_SESSIONS"
            ),
            "conditional_noninterference": (
                "VALID_TRACE_ENUMERATED_TESTS_PASS_NOT_UNIVERSAL_PROOF"
            ),
            "allowed_projection_provenance": (
                "PARTIAL_ANNOTATOR_SELECTED"
            ),
            "alias_randomness": "KEY_GRINDING_AND_ORIGIN_UNATTESTED",
            "principal_independence": (
                "LOCAL_DISTINCT_COMMITMENTS_ONLY_NOT_EXTERNAL_AUTHORITY"
            ),
            "visible_evidence_semantic_leakage": (
                "NOT_ESTABLISHED_ALLOWED_RENDITION_MAY_REVEAL_ESTIMAND"
            ),
            "pair_universe_authority": (
                "NOT_ESTABLISHED_NO_COMPLETE_PAIR_LEDGER"
            ),
            "integration_status": "NOT_INTEGRATED_NO_A0_BARRIER",
            "matcher_authority": (
                "NOT_ESTABLISHED_NO_FROZEN_CASE_MATCHER"
            ),
            "downstream_eligible": False,
            "primary_reliability_eligibility": False,
            "claim_ceiling": [
                (
                    "MECHANISM_LEVEL_CONDITIONAL_NONINTERFERENCE_"
                    "UNDER_DECLARED_ALLOWED_PROJECTION"
                ),
                "PARTIAL_IDENTIFIABILITY_ONLY",
                "NO BLOCK A",
                "NO STEP 1 GO",
            ],
        }
    except MechanicsError as exc:
        return {
            "valid": False,
            "mechanics_level": "REJECTED",
            "errors": [exc.as_dict()],
            "downstream_eligible": False,
            "primary_reliability_eligibility": False,
            "claim_ceiling": ["NO BLOCK A", "NO STEP 1 GO"],
        }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument("--schema-dir", type=Path, default=SCHEMA_DIR)
    args = parser.parse_args(argv)
    report = verify_bundle(args.bundle_dir, args.schema_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
