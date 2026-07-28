#!/usr/bin/env python3
"""Validate a physically separated Stage 0F A0/A1 measurement bundle.

The validator deliberately has no partial-schema fallback.  If the pinned
``jsonschema`` implementation is unavailable, validation stops with a
machine-readable dependency error rather than pretending that hand-written
checks implement JSON Schema Draft 2020-12.

Validation order is fixed:

1. duplicate-key rejection
2. schema meta-validation
3. Draft 2020-12 instance validation
4. cross-artifact semantics and A0/A1 reveal gate
5. canonical/content-hash verification
6. append-only hash-chain and role-exposure audit
7. machine-readable verdict
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlparse

try:
    import jsonschema
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
except ImportError as exc:  # pragma: no cover - exercised with a subprocess.
    jsonschema = None
    Draft202012Validator = None
    FormatChecker = None
    Registry = None
    Resource = None
    JSONSCHEMA_IMPORT_ERROR: Optional[BaseException] = exc
else:
    JSONSCHEMA_IMPORT_ERROR = None


SCHEMA_VERSION = "stage0f-measurement-v0.6.0-draft"
CANONICALIZATION = "stage0f-canonical-json-v1"
PREFIX_PAYLOAD_SERIALIZATION = "stage0f-a0-prefix-payload-v1"
LOCATION_SERIALIZATION = "stage0f-boundary-location-v1"
ADJUDICATED_EVENT_SERIALIZATION = "stage0f-adjudicated-event-id-v1"

ARTIFACT_FILES: Mapping[str, str] = {
    "coordinator_envelope": "coordinator_envelope.json",
    "a0_input": "a0_input.json",
    "a0_label": "a0_label.json",
    "a1_reveal": "a1_reveal.json",
    "a1_label": "a1_label.json",
}

SCHEMA_FILES: Mapping[str, str] = {
    "common": "stage0f_common.schema.json",
    "coordinator_envelope": "stage0f_coordinator_envelope.schema.json",
    "a0_input": "stage0f_a0_input.schema.json",
    "a0_raw_labels": "stage0f_a0_raw_labels.schema.json",
    "a0_label": "stage0f_a0_label.schema.json",
    "a1_reveal": "stage0f_a1_reveal.schema.json",
    "a1_label": "stage0f_a1_label.schema.json",
    "audit_event": "stage0f_audit_event.schema.json",
    "prefix_commit": "stage0f_prefix_commit.schema.json",
    "block_barrier": "stage0f_block_barrier.schema.json",
    "omission_interval": "stage0f_omission_interval.schema.json",
}

AUDIT_LOG_FILE = "audit_events.ndjson"
PREFIX_COMMIT_LOG_FILE = "prefix_commits.ndjson"
BLOCK_BARRIER_FILE = "block_barrier.json"
OMISSION_INTERVAL_FILE = "omission_interval.json"
STAGE_ORDER = (
    "duplicate_key_rejection",
    "schema_meta_validation",
    "draft2020_instance_validation",
    "cross_artifact_semantics",
    "canonical_content_hash",
    "hash_chain_exposure",
)

SOURCE_PRECEDENCE = (
    "world_truth_changed",
    "task_goal_changed",
    "previously_true_fact_newly_revealed",
    "explicit_corrective_feedback",
    "source_unidentifiable",
)

EXPECTED_AUDIT_TYPES = (
    "coordinator_envelope_created",
    "a0_input_frozen",
    "a0_label_frozen",
    "a1_reveal_authorized",
    "a1_revealed",
    "a1_label_frozen",
)

EXPECTED_OMISSION_AUDIT_TYPES = (
    "coordinator_envelope_created",
    "a0_input_frozen",
    "a0_label_frozen",
    "omission_interval_frozen",
    "a1_reveal_authorized",
    "a1_revealed",
    "a1_label_frozen",
)

EVENT_ARTIFACT_TYPE = {
    "coordinator_envelope_created": "coordinator_envelope",
    "a0_input_frozen": "a0_input",
    "a0_label_frozen": "a0_label",
    "omission_interval_frozen": "omission_interval",
    "a1_reveal_authorized": "a1_reveal",
    "a1_revealed": "a1_reveal",
    "a1_label_frozen": "a1_label",
}

FORBIDDEN_PUBLIC_KEYS = {
    "task_id",
    "hosted_config_id",
    "model_family_id",
    "trajectory_id",
    "trajectory_mode",
    "source_detail_url",
    "raw_response_relative_path",
    "local_path",
    "path",
    "model",
    "model_name",
    "score",
    "result",
    "result_url",
    "reward",
    "outcome",
    "final_state",
    "evaluator",
    "evaluator_truth",
    "future_steps",
    "termination",
    "done",
    "author_label",
    "challenge_tag",
    "failure_label",
    "other_model_results",
}

URL_OR_PATH_RE = re.compile(
    r"(?:https?://|file://|(?:^|[\s\"'])/Users/|(?:^|[\s\"'])\.\./)"
)


class DuplicateKeyError(ValueError):
    """Raised before any schema or semantic processing."""

    def __init__(self, key: str) -> None:
        super().__init__("duplicate JSON key: %s" % key)
        self.key = key


def _reject_duplicate_pairs(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def load_json_no_duplicates(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_pairs,
    )


def load_ndjson_no_duplicates(path: Path) -> List[Any]:
    events: List[Any] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            raise ValueError("blank NDJSON line at %d" % line_number)
        try:
            value = json.loads(
                raw_line,
                object_pairs_hook=_reject_duplicate_pairs,
            )
        except DuplicateKeyError:
            raise
        except json.JSONDecodeError as exc:
            raise ValueError(
                "invalid NDJSON at line %d: %s" % (line_number, exc)
            ) from exc
        events.append(value)
    return events


def canonical_bytes(value: Any) -> bytes:
    """Restricted canonical JSON: UTF-8, sorted keys, no floats or NaN."""

    def reject_float(node: Any, path: str = "$") -> None:
        if isinstance(node, float):
            raise ValueError("%s: floats are outside stage0f-canonical-json-v1" % path)
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


def utf8_sorted(values: Iterable[str]) -> List[str]:
    return sorted(values, key=lambda value: value.encode("utf-8"))


IDENTITY_KEYS_EXCLUDED_FROM_PREFIX_PAYLOAD = {
    "artifact_id",
    "unit_alias",
    "asset_id",
    "source_ref_id",
    "source_ref_ids",
    "obligation_id",
    "probe_id",
    "prefix_commit_log_id",
    "prefix_chain_tip_sha256",
    "boundary_namespace",
    "a0_prefix_payload_sha256",
    "boundary_location_id",
    "coordinator_envelope_commitment_sha256",
}


def _without_identity_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_identity_keys(child)
            for key, child in value.items()
            if key not in IDENTITY_KEYS_EXCLUDED_FROM_PREFIX_PAYLOAD
        }
    if isinstance(value, list):
        return [_without_identity_keys(child) for child in value]
    return value


def a0_prefix_payload(
    a0_input: Mapping[str, Any],
    cutoff_observation_ordinal: Optional[int] = None,
) -> List[Any]:
    cutoff = (
        a0_input["cutoff_observation_ordinal"]
        if cutoff_observation_ordinal is None
        else cutoff_observation_ordinal
    )
    projection = {
        "source_protocol": a0_input["source_protocol"],
        "agent_visible_instruction": a0_input["agent_visible_instruction"],
        "normative_schema": a0_input["normative_schema"],
        "prefix_observations": [
            entry
            for entry in a0_input["prefix_observations"]
            if entry["observation_ordinal"] <= cutoff
        ],
        "cutoff_observation_ordinal": cutoff,
        "allowed_probes": a0_input["allowed_probes"],
        "exposure_class": a0_input["exposure_class"],
    }
    return [
        PREFIX_PAYLOAD_SERIALIZATION,
        _without_identity_keys(projection),
    ]


def a0_prefix_payload_sha256(
    a0_input: Mapping[str, Any],
    cutoff_observation_ordinal: Optional[int] = None,
) -> str:
    return canonical_sha256(
        a0_prefix_payload(a0_input, cutoff_observation_ordinal)
    )


def location_payload(
    namespace: str,
    unit_alias: str,
    cutoff_observation_ordinal: int,
    prefix_payload_sha256: str,
) -> List[Any]:
    return [
        LOCATION_SERIALIZATION,
        namespace,
        unit_alias,
        cutoff_observation_ordinal,
        prefix_payload_sha256,
    ]


def boundary_location_id(
    namespace: str,
    unit_alias: str,
    cutoff_observation_ordinal: int,
    prefix_payload_sha256: str,
) -> str:
    return canonical_sha256(
        location_payload(
            namespace,
            unit_alias,
            cutoff_observation_ordinal,
            prefix_payload_sha256,
        )
    )


def adjudicated_event_payload(preimage: Mapping[str, Any]) -> List[Any]:
    return [
        ADJUDICATED_EVENT_SERIALIZATION,
        preimage["boundary_location_id"],
        preimage["p_old_proposition_id"],
        preimage["p_new_proposition_id"],
        preimage["normative_action_difference_sha256"],
        preimage["sorted_obligation_ids"],
        preimage["boundary_type"],
        preimage["schema_bundle_sha256"],
        preimage["codebook_sha256"],
        preimage["supporting_a0_raw_label_ids"],
    ]


def adjudicated_event_id(preimage: Mapping[str, Any]) -> str:
    return canonical_sha256(adjudicated_event_payload(preimage))


def chained_entry_sha256(entry: Mapping[str, Any]) -> str:
    preimage = dict(entry)
    preimage.pop("entry_sha256", None)
    return canonical_sha256(preimage)


def audit_entry_sha256(event: Mapping[str, Any]) -> str:
    return chained_entry_sha256(event)


def schema_bundle_sha256(schemas: Mapping[str, Any]) -> str:
    entries = [
        [SCHEMA_FILES[name], canonical_sha256(schemas[name])]
        for name in sorted(SCHEMA_FILES)
    ]
    return canonical_sha256(["stage0f-schema-bundle-v1", entries])


def validator_file_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def artifact_ref(artifact: Mapping[str, Any]) -> Dict[str, str]:
    return {
        "artifact_id": str(artifact["artifact_id"]),
        "sha256": canonical_sha256(artifact),
    }


def make_error(
    stage: str,
    code: str,
    message: str,
    artifact: Optional[str] = None,
    path: str = "$",
) -> Dict[str, Any]:
    return {
        "stage": stage,
        "code": code,
        "artifact": artifact,
        "path": path,
        "message": message,
    }


def parse_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timezone is required")
    return parsed


def json_path(parts: Iterable[Any]) -> str:
    result = "$"
    for part in parts:
        if isinstance(part, int):
            result += "[%d]" % part
        else:
            result += ".%s" % part
    return result


def walk_objects(value: Any, path: str = "$") -> Iterable[Tuple[str, Mapping[str, Any]]]:
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk_objects(child, "%s.%s" % (path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_objects(child, "%s[%d]" % (path, index))


def walk_strings(value: Any, path: str = "$") -> Iterable[Tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from walk_strings(child, "%s.%s" % (path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_strings(child, "%s[%d]" % (path, index))


def ensure_within_bundle(bundle_dir: Path, relative_path: str) -> Optional[Path]:
    candidate = bundle_dir / relative_path
    try:
        resolved_root = bundle_dir.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (FileNotFoundError, RuntimeError, ValueError):
        return None
    return resolved


def load_bundle_and_schemas(
    bundle_dir: Path,
    schema_dir: Path,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    stage = STAGE_ORDER[0]
    errors: List[Dict[str, Any]] = []
    artifacts: Dict[str, Any] = {}
    schemas: Dict[str, Any] = {}

    for name, filename in SCHEMA_FILES.items():
        path = schema_dir / filename
        if not path.is_file():
            errors.append(
                make_error(stage, "SCHEMA_FILE_MISSING", "required schema file is missing", filename)
            )
            continue
        try:
            schemas[name] = load_json_no_duplicates(path)
        except DuplicateKeyError as exc:
            errors.append(
                make_error(
                    stage,
                    "DUPLICATE_JSON_KEY",
                    str(exc),
                    filename,
                    "$.%s" % exc.key,
                )
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(
                make_error(stage, "INVALID_JSON", str(exc), filename)
            )

    for name, filename in ARTIFACT_FILES.items():
        path = bundle_dir / filename
        if not path.is_file():
            errors.append(
                make_error(stage, "ARTIFACT_FILE_MISSING", "required artifact is missing", filename)
            )
            continue
        try:
            artifacts[name] = load_json_no_duplicates(path)
        except DuplicateKeyError as exc:
            errors.append(
                make_error(
                    stage,
                    "DUPLICATE_JSON_KEY",
                    str(exc),
                    filename,
                    "$.%s" % exc.key,
                )
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(
                make_error(stage, "INVALID_JSON", str(exc), filename)
            )

    audit_path = bundle_dir / AUDIT_LOG_FILE
    if not audit_path.is_file():
        errors.append(
            make_error(stage, "ARTIFACT_FILE_MISSING", "required audit log is missing", AUDIT_LOG_FILE)
        )
    else:
        try:
            artifacts["audit_events"] = load_ndjson_no_duplicates(audit_path)
        except DuplicateKeyError as exc:
            errors.append(
                make_error(
                    stage,
                    "DUPLICATE_JSON_KEY",
                    str(exc),
                    AUDIT_LOG_FILE,
                    "$.%s" % exc.key,
                )
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(
                make_error(stage, "INVALID_JSON", str(exc), AUDIT_LOG_FILE)
            )

    prefix_path = bundle_dir / PREFIX_COMMIT_LOG_FILE
    if not prefix_path.is_file():
        errors.append(
            make_error(
                stage,
                "ARTIFACT_FILE_MISSING",
                "rolling prefix commit log is required",
                PREFIX_COMMIT_LOG_FILE,
            )
        )
    else:
        try:
            artifacts["prefix_commits"] = load_ndjson_no_duplicates(prefix_path)
        except DuplicateKeyError as exc:
            errors.append(
                make_error(
                    stage,
                    "DUPLICATE_JSON_KEY",
                    str(exc),
                    PREFIX_COMMIT_LOG_FILE,
                    "$.%s" % exc.key,
                )
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(
                make_error(stage, "INVALID_JSON", str(exc), PREFIX_COMMIT_LOG_FILE)
            )

    omission_path = bundle_dir / OMISSION_INTERVAL_FILE
    if omission_path.is_file():
        try:
            artifacts["omission_interval"] = load_json_no_duplicates(omission_path)
        except DuplicateKeyError as exc:
            errors.append(
                make_error(
                    stage,
                    "DUPLICATE_JSON_KEY",
                    str(exc),
                    OMISSION_INTERVAL_FILE,
                    "$.%s" % exc.key,
                )
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(
                make_error(stage, "INVALID_JSON", str(exc), OMISSION_INTERVAL_FILE)
            )

    if errors:
        return None, errors
    return {"artifacts": artifacts, "schemas": schemas}, []


def validate_schema_meta(schemas: Mapping[str, Any]) -> List[Dict[str, Any]]:
    stage = STAGE_ORDER[1]
    errors: List[Dict[str, Any]] = []
    assert Draft202012Validator is not None
    for name, schema in schemas.items():
        filename = SCHEMA_FILES[name]
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append(
                make_error(stage, "SCHEMA_META_INVALID", str(exc), filename)
            )
            continue
        for path, node in walk_objects(schema):
            if node.get("type") == "object" and node.get("additionalProperties") is not False:
                errors.append(
                    make_error(
                        stage,
                        "SCHEMA_OPEN_OBJECT",
                        "every instance object schema must set additionalProperties=false",
                        filename,
                        path,
                    )
                )
    return errors


def make_registry(schemas: Mapping[str, Any]) -> Any:
    assert Registry is not None
    assert Resource is not None
    registry = Registry()
    for schema in schemas.values():
        registry = registry.with_resource(
            schema["$id"],
            Resource.from_contents(schema),
        )
    return registry


def validate_instances(
    artifacts: Mapping[str, Any],
    schemas: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    stage = STAGE_ORDER[2]
    errors: List[Dict[str, Any]] = []
    assert Draft202012Validator is not None
    assert FormatChecker is not None
    registry = make_registry(schemas)

    for name in ARTIFACT_FILES:
        validator = Draft202012Validator(
            schemas[name],
            registry=registry,
            format_checker=FormatChecker(),
        )
        for error in sorted(
            validator.iter_errors(artifacts[name]),
            key=lambda item: list(item.absolute_path),
        ):
            errors.append(
                make_error(
                    stage,
                    "SCHEMA_INSTANCE_INVALID",
                    error.message,
                    ARTIFACT_FILES[name],
                    json_path(error.absolute_path),
                )
            )

    audit_validator = Draft202012Validator(
        schemas["audit_event"],
        registry=registry,
        format_checker=FormatChecker(),
    )
    for index, event in enumerate(artifacts["audit_events"]):
        for error in sorted(
            audit_validator.iter_errors(event),
            key=lambda item: list(item.absolute_path),
        ):
            errors.append(
                make_error(
                    stage,
                    "SCHEMA_INSTANCE_INVALID",
                    error.message,
                    AUDIT_LOG_FILE,
                    "$[%d]%s" % (
                        index,
                        json_path(error.absolute_path)[1:],
                    ),
                )
            )
    prefix_validator = Draft202012Validator(
        schemas["prefix_commit"],
        registry=registry,
        format_checker=FormatChecker(),
    )
    for index, entry in enumerate(artifacts["prefix_commits"]):
        for error in sorted(
            prefix_validator.iter_errors(entry),
            key=lambda item: list(item.absolute_path),
        ):
            errors.append(
                make_error(
                    stage,
                    "SCHEMA_INSTANCE_INVALID",
                    error.message,
                    PREFIX_COMMIT_LOG_FILE,
                    "$[%d]%s"
                    % (index, json_path(error.absolute_path)[1:]),
                )
            )
    if "omission_interval" in artifacts:
        omission_validator = Draft202012Validator(
            schemas["omission_interval"],
            registry=registry,
            format_checker=FormatChecker(),
        )
        for error in sorted(
            omission_validator.iter_errors(artifacts["omission_interval"]),
            key=lambda item: list(item.absolute_path),
        ):
            errors.append(
                make_error(
                    stage,
                    "SCHEMA_INSTANCE_INVALID",
                    error.message,
                    OMISSION_INTERVAL_FILE,
                    json_path(error.absolute_path),
                )
            )
    return errors


def first_semantic_error(
    artifacts: Mapping[str, Any],
) -> Optional[Dict[str, Any]]:
    stage = STAGE_ORDER[3]
    coordinator = artifacts["coordinator_envelope"]
    a0_input = artifacts["a0_input"]
    a0_label = artifacts["a0_label"]
    a1_reveal = artifacts["a1_reveal"]
    a1_label = artifacts["a1_label"]

    artifact_ids = [artifacts[name]["artifact_id"] for name in ARTIFACT_FILES]
    if len(artifact_ids) != len(set(artifact_ids)):
        return make_error(
            stage,
            "SEM_ARTIFACT_ID_COLLISION",
            "artifact_id values must be unique inside a bundle",
        )

    aliases = {artifacts[name]["unit_alias"] for name in ARTIFACT_FILES}
    if len(aliases) != 1:
        return make_error(
            stage,
            "SEM_UNIT_ALIAS_MISMATCH",
            "all physical artifacts must carry the same unit_alias",
        )

    observations = a0_input["prefix_observations"]
    ordinals = [entry["observation_ordinal"] for entry in observations]
    expected_ordinals = list(range(a0_input["cutoff_observation_ordinal"] + 1))
    if ordinals != expected_ordinals:
        return make_error(
            stage,
            "SEM_OBSERVATION_ORDINAL_SEQUENCE",
            "Agent-visible observation ordinals must be contiguous, zero-based, and ordered; batch model_steps do not create a second ordinal system",
            ARTIFACT_FILES["a0_input"],
            "$.prefix_observations",
        )

    try:
        observation_times = [parse_timestamp(item["observed_at"]) for item in observations]
        input_frozen = parse_timestamp(a0_input["frozen_at"])
        label_frozen = parse_timestamp(a0_label["frozen_at"])
        reveal_time = parse_timestamp(a1_reveal["revealed_at"])
        a1_label_frozen = parse_timestamp(a1_label["frozen_at"])
    except (TypeError, ValueError) as exc:
        return make_error(
            stage,
            "SEM_TIMESTAMP_INVALID",
            str(exc),
        )

    if any(left >= right for left, right in zip(observation_times, observation_times[1:])):
        return make_error(
            stage,
            "SEM_OBSERVATION_TIME_ORDER",
            "observation timestamps must be strictly increasing",
            ARTIFACT_FILES["a0_input"],
            "$.prefix_observations",
        )
    if observation_times[-1] > input_frozen:
        return make_error(
            stage,
            "SEM_INPUT_FREEZE_BEFORE_PREFIX",
            "A0 input cannot freeze before its last prefix observation",
            ARTIFACT_FILES["a0_input"],
            "$.frozen_at",
        )

    prefix_commits = artifacts["prefix_commits"]
    if len(prefix_commits) != len(observations):
        return make_error(
            stage,
            "SEM_ROLLING_PREFIX_COVERAGE",
            "every observation through the A0 cutoff requires one rolling prefix commitment",
            PREFIX_COMMIT_LOG_FILE,
        )
    if [entry["sequence"] for entry in prefix_commits] != list(range(len(observations))):
        return make_error(
            stage,
            "SEM_ROLLING_PREFIX_SEQUENCE",
            "rolling prefix commitments must be contiguous and append ordered",
            PREFIX_COMMIT_LOG_FILE,
        )
    if [entry["observation_ordinal"] for entry in prefix_commits] != expected_ordinals:
        return make_error(
            stage,
            "SEM_ROLLING_PREFIX_ORDINAL",
            "rolling prefix commitments must bind the same observation ordinal system as A0",
            PREFIX_COMMIT_LOG_FILE,
        )
    prefix_log_ids = {entry["prefix_commit_log_id"] for entry in prefix_commits}
    if prefix_log_ids != {a0_input["prefix_commit_log_id"]}:
        return make_error(
            stage,
            "SEM_ROLLING_PREFIX_LOG_ID",
            "A0 input must bind exactly one prefix commit log",
            PREFIX_COMMIT_LOG_FILE,
        )
    for index, (entry, observation) in enumerate(zip(prefix_commits, observations)):
        if entry["unit_alias"] != a0_input["unit_alias"]:
            return make_error(
                stage,
                "SEM_ROLLING_PREFIX_UNIT",
                "prefix commit unit alias does not match A0",
                PREFIX_COMMIT_LOG_FILE,
                "$[%d].unit_alias" % index,
            )
        generator_aliases = [
            item["generator_alias"] for item in entry["generator_decisions"]
        ]
        if len(generator_aliases) != len(set(generator_aliases)):
            return make_error(
                stage,
                "SEM_ROLLING_PREFIX_GENERATOR_COLLISION",
                "the two prefix-only generator decisions require distinct generator aliases",
                PREFIX_COMMIT_LOG_FILE,
                "$[%d].generator_decisions" % index,
            )
        expected_prefix_payload_hash = a0_prefix_payload_sha256(
            a0_input,
            entry["observation_ordinal"],
        )
        if entry["a0_prefix_payload_sha256"] != expected_prefix_payload_hash:
            return make_error(
                stage,
                "SEM_PREFIX_PAYLOAD_DERIVATION",
                "rolling entry must hash the ID-free A0 prefix payload visible at that ordinal",
                PREFIX_COMMIT_LOG_FILE,
                "$[%d].a0_prefix_payload_sha256" % index,
            )
        if entry["boundary_namespace"] != a0_input["boundary_namespace"]:
            return make_error(
                stage,
                "SEM_BOUNDARY_NAMESPACE_MISMATCH",
                "rolling entry and A0 input must use the same frozen boundary namespace",
                PREFIX_COMMIT_LOG_FILE,
                "$[%d].boundary_namespace" % index,
            )
        expected_location = boundary_location_id(
            a0_input["boundary_namespace"],
            a0_input["unit_alias"],
            entry["observation_ordinal"],
            expected_prefix_payload_hash,
        )
        if entry["boundary_location_id"] != expected_location:
            return make_error(
                stage,
                "SEM_LOCATION_ID_DERIVATION",
                "rolling boundary location must bind namespace, unit, cutoff, and ID-free prefix payload",
                PREFIX_COMMIT_LOG_FILE,
                "$[%d].boundary_location_id" % index,
            )
        commit_time = parse_timestamp(entry["committed_at"])
        if commit_time < observation_times[index]:
            return make_error(
                stage,
                "SEM_ROLLING_PREFIX_COMMIT_BEFORE_OBSERVATION",
                "an observation cannot be committed before it is observed",
                PREFIX_COMMIT_LOG_FILE,
                "$[%d].committed_at" % index,
            )
        if index + 1 < len(observations) and commit_time >= observation_times[index + 1]:
            return make_error(
                stage,
                "SEM_ROLLING_PREFIX_LATE_COMMIT",
                "each prefix and generator decision must freeze before the next observation becomes visible",
                PREFIX_COMMIT_LOG_FILE,
                "$[%d].committed_at" % index,
            )
        if index + 1 == len(observations) and commit_time >= input_frozen:
            return make_error(
                stage,
                "SEM_ROLLING_PREFIX_LATE_COMMIT",
                "the final prefix commitment must precede A0 input freeze",
                PREFIX_COMMIT_LOG_FILE,
                "$[%d].committed_at" % index,
            )
        for decision_index, decision in enumerate(entry["generator_decisions"]):
            if (
                decision["visible_through_observation_ordinal"]
                != entry["observation_ordinal"]
            ):
                return make_error(
                    stage,
                    "SEM_ROLLING_PREFIX_FUTURE_EXPOSURE",
                    "a streaming generator may see only observations through the committed ordinal",
                    PREFIX_COMMIT_LOG_FILE,
                    "$[%d].generator_decisions[%d].visible_through_observation_ordinal"
                    % (index, decision_index),
                )
            if decision["boundary_location_id"] != expected_location:
                return make_error(
                    stage,
                    "SEM_LOCATION_ID_DERIVATION",
                    "generator identity may commit only to unit alias plus location ordinal, never A0 semantics",
                    PREFIX_COMMIT_LOG_FILE,
                    "$[%d].generator_decisions[%d].boundary_location_id"
                    % (index, decision_index),
                )
            decision_time = parse_timestamp(decision["decided_at"])
            if not (observation_times[index] <= decision_time <= commit_time):
                return make_error(
                    stage,
                    "SEM_ROLLING_PREFIX_DECISION_TIME",
                    "generator decision must occur after observation and no later than its rolling commit",
                    PREFIX_COMMIT_LOG_FILE,
                    "$[%d].generator_decisions[%d].decided_at"
                    % (index, decision_index),
                )

    locator_ordinal = a0_input["candidate_locator"]["update_observation_ordinal"]
    cutoff = a0_input["cutoff_observation_ordinal"]
    expected_selected_prefix_hash = a0_prefix_payload_sha256(a0_input)
    if a0_input["a0_prefix_payload_sha256"] != expected_selected_prefix_hash:
        return make_error(
            stage,
            "SEM_PREFIX_PAYLOAD_DERIVATION",
            "A0 input must commit to its exact ID-free prefix payload",
            ARTIFACT_FILES["a0_input"],
            "$.a0_prefix_payload_sha256",
        )
    expected_selected_location = boundary_location_id(
        a0_input["boundary_namespace"],
        a0_input["unit_alias"],
        cutoff,
        expected_selected_prefix_hash,
    )
    if a0_input["boundary_location_id"] != expected_selected_location:
        return make_error(
            stage,
            "SEM_LOCATION_ID_DERIVATION",
            "boundary_location_id must hash namespace, unit alias, cutoff, and ID-free prefix payload",
            ARTIFACT_FILES["a0_input"],
            "$.boundary_location_id",
        )
    if not any(
        decision["decision"] == "propose_location"
        for decision in prefix_commits[-1]["generator_decisions"]
    ):
        return make_error(
            stage,
            "SEM_LOCATION_NOT_PROPOSED",
            "at least one independent prefix-only generator must propose the selected location",
            PREFIX_COMMIT_LOG_FILE,
            "$[%d].generator_decisions" % (len(prefix_commits) - 1),
        )
    p_new_pointer = a0_label["p_new"]["evidence_pointer"]
    p_new_ordinal = p_new_pointer["observation_ordinal"]
    if p_new_ordinal > cutoff:
        return make_error(
            stage,
            "SEM_FUTURE_EVIDENCE_ORDINAL",
            "p_new evidence is after the A0 cutoff",
            ARTIFACT_FILES["a0_label"],
            "$.p_new.evidence_pointer.observation_ordinal",
        )
    if locator_ordinal != p_new_ordinal:
        return make_error(
            stage,
            "SEM_CANDIDATE_LOCATOR_MISMATCH",
            "candidate locator must equal the p_new evidence observation ordinal",
            ARTIFACT_FILES["a0_label"],
            "$.p_new.evidence_pointer.observation_ordinal",
        )

    p_old = a0_label["p_old"]
    p_old_pointer = p_old["evidence_pointer"]
    if p_old["status"] == "pre_update_frozen":
        if p_old_pointer is None:
            return make_error(
                stage,
                "SEM_P_OLD_POINTER_REQUIRED",
                "pre_update_frozen p_old requires a structured evidence pointer",
                ARTIFACT_FILES["a0_label"],
                "$.p_old.evidence_pointer",
            )
        if p_old_pointer["observation_ordinal"] >= p_new_ordinal:
            return make_error(
                stage,
                "SEM_P_OLD_NOT_PRE_UPDATE",
                "p_old evidence must precede p_new evidence",
                ARTIFACT_FILES["a0_label"],
                "$.p_old.evidence_pointer.observation_ordinal",
            )
    elif p_old_pointer is not None:
        return make_error(
            stage,
            "SEM_HYPOTHESIZED_P_OLD_HAS_POINTER",
            "old_state_hypothesized must not masquerade as pre-update evidence",
            ARTIFACT_FILES["a0_label"],
            "$.p_old.evidence_pointer",
        )

    source_entries = a0_label["update_source_evidence"]
    source_labels = [entry["label"] for entry in source_entries]
    if len(source_labels) != len(set(source_labels)):
        return make_error(
            stage,
            "SEM_DUPLICATE_SOURCE_LABEL",
            "each factual update-source label may appear once",
            ARTIFACT_FILES["a0_label"],
            "$.update_source_evidence",
        )
    if "source_unidentifiable" in source_labels and len(source_labels) != 1:
        return make_error(
            stage,
            "SEM_SOURCE_UNIDENTIFIABLE_NOT_EXCLUSIVE",
            "source_unidentifiable is mutually exclusive with factual source labels",
            ARTIFACT_FILES["a0_label"],
            "$.update_source_evidence",
        )
    expected_label_order = [label for label in SOURCE_PRECEDENCE if label in source_labels]
    if source_labels != expected_label_order:
        return make_error(
            stage,
            "SEM_SOURCE_LABEL_ORDER",
            "source labels must follow the frozen precedence order",
            ARTIFACT_FILES["a0_label"],
            "$.update_source_evidence",
        )
    if a0_label["primary_update_source"] != expected_label_order[0]:
        return make_error(
            stage,
            "SEM_PRIMARY_SOURCE_DERIVATION",
            "primary_update_source is not the first evidenced label in frozen precedence",
            ARTIFACT_FILES["a0_label"],
            "$.primary_update_source",
        )

    expected_primary = p_old["status"] == "pre_update_frozen"
    if a0_label["primary_analysis_eligible"] is not expected_primary:
        return make_error(
            stage,
            "SEM_PRIMARY_ELIGIBILITY_DERIVATION",
            "primary_analysis_eligible must be derived from pre-update p_old status",
            ARTIFACT_FILES["a0_label"],
            "$.primary_analysis_eligible",
        )
    expected_environment = expected_primary and source_labels == ["world_truth_changed"]
    if a0_label["environment_primary_eligible"] is not expected_environment:
        return make_error(
            stage,
            "SEM_ENVIRONMENT_ELIGIBILITY_DERIVATION",
            "environment_primary_eligible is true only for an otherwise eligible pure-world transition",
            ARTIFACT_FILES["a0_label"],
            "$.environment_primary_eligible",
        )

    normative_sources = {
        entry["source_ref_id"] for entry in a0_input["normative_schema"]["sources"]
    }
    if len(normative_sources) != len(a0_input["normative_schema"]["sources"]):
        return make_error(
            stage,
            "SEM_NORMATIVE_SOURCE_ID_COLLISION",
            "normative source ids must be unique",
            ARTIFACT_FILES["a0_input"],
            "$.normative_schema.sources",
        )
    obligations = a0_input["normative_schema"]["obligations"]
    obligation_ids = [item["obligation_id"] for item in obligations]
    if len(obligation_ids) != len(set(obligation_ids)):
        return make_error(
            stage,
            "SEM_OBLIGATION_ID_COLLISION",
            "normative obligation ids must be unique",
            ARTIFACT_FILES["a0_input"],
            "$.normative_schema.obligations",
        )
    for index, obligation in enumerate(obligations):
        if not set(obligation["source_ref_ids"]).issubset(normative_sources):
            return make_error(
                stage,
                "SEM_DANGLING_NORMATIVE_SOURCE",
                "obligation references a source absent from the A0 normative schema",
                ARTIFACT_FILES["a0_input"],
                "$.normative_schema.obligations[%d].source_ref_ids" % index,
            )

    assessment_ids = [
        entry["obligation_id"] for entry in a0_label["obligation_assessments"]
    ]
    if len(assessment_ids) != len(set(assessment_ids)):
        return make_error(
            stage,
            "SEM_DUPLICATE_OBLIGATION_ASSESSMENT",
            "an obligation may be assessed only once",
            ARTIFACT_FILES["a0_label"],
            "$.obligation_assessments",
        )
    if set(assessment_ids) != set(obligation_ids):
        return make_error(
            stage,
            "SEM_OBLIGATION_COVERAGE_INCOMPLETE",
            "A0 must assess every frozen normative obligation exactly once",
            ARTIFACT_FILES["a0_label"],
            "$.obligation_assessments",
        )
    affected_ids = a0_label["affected_obligation_ids"]
    dangling = [item for item in affected_ids if item not in set(obligation_ids)]
    if dangling:
        return make_error(
            stage,
            "SEM_DANGLING_AFFECTED_OBLIGATION",
            "affected obligation is absent from the frozen normative schema",
            ARTIFACT_FILES["a0_label"],
            "$.affected_obligation_ids",
        )
    expected_affected = {
        entry["obligation_id"]
        for entry in a0_label["obligation_assessments"]
        if entry["affected"]
    }
    if set(affected_ids) != expected_affected:
        return make_error(
            stage,
            "SEM_AFFECTED_OBLIGATION_DERIVATION",
            "affected_obligation_ids must equal the obligations assessed as affected",
            ARTIFACT_FILES["a0_label"],
            "$.affected_obligation_ids",
        )

    if a0_label["boundary_location_id"] != a0_input["boundary_location_id"]:
        return make_error(
            stage,
            "SEM_A0_LOCATION_LINK",
            "A0 label must bind the semantics-free candidate location",
            ARTIFACT_FILES["a0_label"],
            "$.boundary_location_id",
        )
    preimage = a0_label["adjudicated_event_preimage"]
    if preimage["boundary_location_id"] != a0_input["boundary_location_id"]:
        return make_error(
            stage,
            "SEM_A0_EVENT_LOCATION",
            "A0 event identity must derive from the semantics-free location id",
            ARTIFACT_FILES["a0_label"],
            "$.adjudicated_event_preimage.boundary_location_id",
        )
    if preimage["p_old_proposition_id"] != a0_label["p_old"]["proposition_id"]:
        return make_error(
            stage,
            "SEM_A0_EVENT_P_OLD",
            "A0 event identity must use the independently frozen p_old proposition",
            ARTIFACT_FILES["a0_label"],
            "$.adjudicated_event_preimage.p_old_proposition_id",
        )
    if preimage["p_new_proposition_id"] != a0_label["p_new"]["proposition_id"]:
        return make_error(
            stage,
            "SEM_A0_EVENT_P_NEW",
            "A0 event identity must use the independently frozen p_new proposition",
            ARTIFACT_FILES["a0_label"],
            "$.adjudicated_event_preimage.p_new_proposition_id",
        )
    if (
        preimage["normative_action_difference_sha256"]
        != hashlib.sha256(
            a0_label["normative_action_difference"].encode("utf-8")
        ).hexdigest()
    ):
        return make_error(
            stage,
            "SEM_A0_EVENT_NORMATIVE_DIFFERENCE",
            "A0 event identity must bind the independently frozen normative action difference",
            ARTIFACT_FILES["a0_label"],
            "$.adjudicated_event_preimage.normative_action_difference_sha256",
        )
    sorted_affected = utf8_sorted(affected_ids)
    if preimage["sorted_obligation_ids"] != sorted_affected:
        return make_error(
            stage,
            "SEM_A0_EVENT_OBLIGATION_ORDER",
            "A0 event obligation ids must exactly equal affected ids in UTF-8 byte order",
            ARTIFACT_FILES["a0_label"],
            "$.adjudicated_event_preimage.sorted_obligation_ids",
        )
    if (
        preimage["supporting_a0_raw_label_ids"]
        != utf8_sorted(a0_label["supporting_a0_raw_label_ids"])
    ):
        return make_error(
            stage,
            "SEM_ADJUDICATED_RAW_LABEL_SET",
            "adjudicated event must bind all supporting A0 raw label ids in UTF-8 order",
            ARTIFACT_FILES["a0_label"],
            "$.adjudicated_event_preimage.supporting_a0_raw_label_ids",
        )
    version_hashes = coordinator["provenance"]["version_hashes"]
    if (
        preimage["schema_bundle_sha256"]
        != version_hashes["schema_bundle_sha256"]
        or preimage["codebook_sha256"]
        != version_hashes["codebook_sha256"]
    ):
        return make_error(
            stage,
            "SEM_ADJUDICATED_VERSION_BINDING",
            "adjudicated event identity must bind the frozen schema and codebook hashes",
            ARTIFACT_FILES["a0_label"],
            "$.adjudicated_event_preimage",
        )
    required_action_spec = a0_label["required_action_spec"]
    if preimage["boundary_type"] == "required_action_omission":
        if required_action_spec is None:
            return make_error(
                stage,
                "SEM_OMISSION_REQUIRED_ACTION_SPEC",
                "omission boundary requires an A0-frozen action signature and deadline rule",
                ARTIFACT_FILES["a0_label"],
                "$.required_action_spec",
            )
        if set(required_action_spec["obligation_ids"]) != set(affected_ids):
            return make_error(
                stage,
                "SEM_OMISSION_REQUIRED_ACTION_OBLIGATIONS",
                "omission action specification must cover exactly the affected obligations",
                ARTIFACT_FILES["a0_label"],
                "$.required_action_spec.obligation_ids",
            )
    elif required_action_spec is not None:
        return make_error(
            stage,
            "SEM_NON_OMISSION_ACTION_SPEC",
            "required_action_spec is reserved for required-action omission boundaries",
            ARTIFACT_FILES["a0_label"],
            "$.required_action_spec",
        )

    decision_ordinal = a0_label["eligible_decision_point"]["observation_ordinal"]
    if decision_ordinal < p_new_ordinal or decision_ordinal > cutoff:
        return make_error(
            stage,
            "SEM_DECISION_POINT_OUTSIDE_PREFIX",
            "eligible decision point must be after p_new and no later than the A0 cutoff",
            ARTIFACT_FILES["a0_label"],
            "$.eligible_decision_point.observation_ordinal",
        )

    if not (input_frozen <= label_frozen < reveal_time < a1_label_frozen):
        return make_error(
            stage,
            "SEM_A0_A1_REVEAL_GATE",
            "required time order is A0 input freeze <= A0 label freeze < A1 reveal < A1 label freeze",
        )
    behavior_evidence = a1_reveal["behavior_evidence"]
    if a1_reveal["reveal_kind"] != behavior_evidence["kind"]:
        return make_error(
            stage,
            "SEM_REVEAL_KIND_MISMATCH",
            "reveal_kind must select the matching closed evidence branch",
            ARTIFACT_FILES["a1_reveal"],
            "$.reveal_kind",
        )
    if preimage["boundary_type"] == "required_action_omission":
        if a1_reveal["reveal_kind"] != "omission_interval":
            return make_error(
                stage,
                "SEM_OMISSION_INTERVAL_REQUIRED",
                "required-action omission cannot be inferred from a single action or terminal absence",
                ARTIFACT_FILES["a1_reveal"],
                "$.reveal_kind",
            )
        if "omission_interval" not in artifacts:
            return make_error(
                stage,
                "SEM_OMISSION_PACKET_REQUIRED",
                "omission claim requires a complete decision-to-deadline interval artifact",
                OMISSION_INTERVAL_FILE,
            )
    else:
        if a1_reveal["reveal_kind"] != "observed_action":
            return make_error(
                stage,
                "SEM_OBSERVED_ACTION_REQUIRED",
                "non-omission boundary requires an observed semantic action",
                ARTIFACT_FILES["a1_reveal"],
                "$.reveal_kind",
            )
        if "omission_interval" in artifacts:
            return make_error(
                stage,
                "SEM_UNEXPECTED_OMISSION_PACKET",
                "non-omission units must not carry a post-decision omission interval",
                OMISSION_INTERVAL_FILE,
            )
        if behavior_evidence["after_observation_ordinal"] != decision_ordinal:
            return make_error(
                stage,
                "SEM_ACTION_DECISION_POINT_MISMATCH",
                "revealed candidate action must be anchored after the frozen decision observation",
                ARTIFACT_FILES["a1_reveal"],
                "$.behavior_evidence.after_observation_ordinal",
            )

    if a0_label["annotator_alias"] == a1_label["annotator_alias"]:
        return make_error(
            stage,
            "SEM_ANNOTATOR_ROLE_COLLISION",
            "A0 normative and A1 behavioral labels require distinct annotator identities",
        )

    action = a1_label["action_assessment"]
    if a1_reveal["reveal_kind"] == "omission_interval":
        if (
            action["candidate_action_executed"]
            or not action["required_action_omission"]
            or not action["deadline_or_commit_reached"]
        ):
            return make_error(
                stage,
                "SEM_OMISSION_ASSESSMENT_BRANCH",
                "omission interval requires not-executed, omission=true, and deadline reached",
                ARTIFACT_FILES["a1_label"],
                "$.action_assessment",
            )
        omission = artifacts["omission_interval"]
        if omission["unit_alias"] != a0_input["unit_alias"]:
            return make_error(
                stage,
                "SEM_OMISSION_UNIT_MISMATCH",
                "omission interval unit alias must match A0",
                OMISSION_INTERVAL_FILE,
                "$.unit_alias",
            )
        if omission["decision_observation_ordinal"] != decision_ordinal:
            return make_error(
                stage,
                "SEM_OMISSION_DECISION_BOUNDARY",
                "omission interval must begin exclusively after the A0-frozen decision point",
                OMISSION_INTERVAL_FILE,
                "$.decision_observation_ordinal",
            )
        deadline_ordinal = omission["deadline_observation_ordinal"]
        interval_entries = omission["entries"]
        expected_interval_ordinals = list(
            range(decision_ordinal + 1, deadline_ordinal + 1)
        )
        if (
            [entry["sequence"] for entry in interval_entries]
            != list(range(len(interval_entries)))
            or [entry["observation_ordinal"] for entry in interval_entries]
            != expected_interval_ordinals
        ):
            return make_error(
                stage,
                "SEM_OMISSION_INTERVAL_INCOMPLETE",
                "omission packet must contain every observation from decision+1 through the deadline",
                OMISSION_INTERVAL_FILE,
                "$.entries",
            )
        if (
            omission["deadline_evidence"]["observation_ordinal"]
            != deadline_ordinal
        ):
            return make_error(
                stage,
                "SEM_OMISSION_DEADLINE_EVIDENCE",
                "deadline evidence must bind the final interval observation",
                OMISSION_INTERVAL_FILE,
                "$.deadline_evidence.observation_ordinal",
            )
        required_signature = required_action_spec["action_signature"]
        for entry_index, entry in enumerate(interval_entries):
            for action_index, interval_action in enumerate(
                entry["normalized_actions"]
            ):
                expected_match = (
                    interval_action["action_signature"] == required_signature
                )
                if interval_action["matches_required_action"] is not expected_match:
                    return make_error(
                        stage,
                        "SEM_OMISSION_ACTION_MATCH_DERIVATION",
                        "matches_required_action must be derived from the A0-frozen action signature",
                        OMISSION_INTERVAL_FILE,
                        "$.entries[%d].normalized_actions[%d].matches_required_action"
                        % (entry_index, action_index),
                    )
                if expected_match:
                    return make_error(
                        stage,
                        "SEM_OMISSION_REQUIRED_ACTION_PRESENT",
                        "a complete interval contains the required action and cannot support omission",
                        OMISSION_INTERVAL_FILE,
                        "$.entries[%d].normalized_actions[%d]" % (
                            entry_index,
                            action_index,
                        ),
                    )
    if action["candidate_action_executed"] and action["required_action_omission"]:
        return make_error(
            stage,
            "SEM_EXECUTED_AND_OMITTED",
            "the same candidate action cannot be both executed and omitted",
            ARTIFACT_FILES["a1_label"],
            "$.action_assessment",
        )
    if action["candidate_action_executed"]:
        if "unidentifiable" in (
            action["compatible_with_p_old"],
            action["compatible_with_p_new"],
        ):
            expected_phenotype = "unidentifiable"
        elif (
            action["compatible_with_p_old"] == "yes"
            and action["compatible_with_p_new"] == "no"
        ):
            expected_phenotype = "target_positive"
        else:
            expected_phenotype = "target_negative"
    elif action["required_action_omission"]:
        expected_phenotype = (
            "target_positive" if action["deadline_or_commit_reached"] else "unidentifiable"
        )
    elif "unidentifiable" in (
        action["compatible_with_p_old"],
        action["compatible_with_p_new"],
    ):
        expected_phenotype = "unidentifiable"
    else:
        expected_phenotype = "target_negative"

    if action["phenotype"] != expected_phenotype:
        return make_error(
            stage,
            "SEM_PHENOTYPE_DERIVATION",
            "behavioral phenotype is inconsistent with the frozen compatibility fields",
            ARTIFACT_FILES["a1_label"],
            "$.action_assessment.phenotype",
        )
    expected_positive = expected_primary and expected_phenotype == "target_positive"
    if a1_label["primary_uacf_d_positive"] is not expected_positive:
        return make_error(
            stage,
            "SEM_UACF_PRIMARY_DERIVATION",
            "primary_uacf_d_positive must be derived from A0 eligibility and A1 phenotype",
            ARTIFACT_FILES["a1_label"],
            "$.primary_uacf_d_positive",
        )

    behavioral_ids = [
        entry["obligation_id"]
        for entry in a1_label["affected_obligation_assessments"]
    ]
    if len(behavioral_ids) != len(set(behavioral_ids)):
        return make_error(
            stage,
            "SEM_DUPLICATE_BEHAVIORAL_OBLIGATION",
            "A1 may assess each affected obligation once",
            ARTIFACT_FILES["a1_label"],
            "$.affected_obligation_assessments",
        )
    if set(behavioral_ids) != set(affected_ids):
        return make_error(
            stage,
            "SEM_A1_OBLIGATION_COVERAGE",
            "A1 must assess every and only A0-affected obligations",
            ARTIFACT_FILES["a1_label"],
            "$.affected_obligation_assessments",
        )
    return None


def _verify_artifact_ref(
    actual_ref: Mapping[str, Any],
    expected_artifact: Mapping[str, Any],
    artifact_name: str,
    path: str,
) -> Optional[Dict[str, Any]]:
    expected = artifact_ref(expected_artifact)
    if dict(actual_ref) != expected:
        return make_error(
            STAGE_ORDER[4],
            "HASH_ARTIFACT_REF_MISMATCH",
            "artifact reference does not match the canonical content and artifact id",
            artifact_name,
            path,
        )
    return None


def _verify_evidence_pointer(
    pointer: Mapping[str, Any],
    a0_input: Mapping[str, Any],
    artifact_name: str,
    path: str,
) -> Optional[Dict[str, Any]]:
    stage = STAGE_ORDER[4]
    ordinal = pointer["observation_ordinal"]
    if ordinal > a0_input["cutoff_observation_ordinal"]:
        return make_error(
            stage,
            "HASH_EVIDENCE_POINTER_FUTURE",
            "evidence pointer exceeds the A0 cutoff",
            artifact_name,
            path,
        )
    source_kind = pointer["source_kind"]
    expected_hash: Optional[str] = None
    expected_artifact_id: Optional[str] = None

    if source_kind in ("observation", "user_input", "preexisting_artifact"):
        observations = {
            item["observation_ordinal"]: item
            for item in a0_input["prefix_observations"]
        }
        if ordinal not in observations:
            return make_error(
                stage,
                "HASH_EVIDENCE_POINTER_MISSING",
                "evidence observation does not exist",
                artifact_name,
                path,
            )
        expected_artifact_id = a0_input["artifact_id"]
        expected_hash = canonical_sha256(observations[ordinal])
    elif source_kind == "agent_visible_instruction":
        expected_artifact_id = a0_input["artifact_id"]
        expected_hash = a0_input["agent_visible_instruction"]["content_sha256"]
    elif source_kind == "normative_source":
        sources = {
            item["source_ref_id"]: item
            for item in a0_input["normative_schema"]["sources"]
        }
        if pointer["artifact_id"] not in sources:
            return make_error(
                stage,
                "HASH_EVIDENCE_POINTER_MISSING",
                "normative evidence source does not exist",
                artifact_name,
                path,
            )
        expected_artifact_id = pointer["artifact_id"]
        expected_hash = sources[pointer["artifact_id"]]["content_sha256"]

    if (
        pointer["artifact_id"] != expected_artifact_id
        or pointer["content_sha256"] != expected_hash
    ):
        return make_error(
            stage,
            "HASH_EVIDENCE_POINTER_CONTENT",
            "evidence pointer content commitment does not resolve",
            artifact_name,
            path,
        )
    return None


def first_content_hash_error(
    artifacts: Mapping[str, Any],
    schemas: Mapping[str, Any],
    bundle_dir: Path,
) -> Optional[Dict[str, Any]]:
    stage = STAGE_ORDER[4]
    coordinator = artifacts["coordinator_envelope"]
    a0_input = artifacts["a0_input"]
    a0_label = artifacts["a0_label"]
    a1_reveal = artifacts["a1_reveal"]
    a1_label = artifacts["a1_label"]

    expected_schema_hash = schema_bundle_sha256(schemas)
    expected_validator_hash = validator_file_sha256()
    version_hashes = coordinator["provenance"]["version_hashes"]
    if version_hashes["schema_bundle_sha256"] != expected_schema_hash:
        return make_error(
            stage,
            "HASH_SCHEMA_BUNDLE_MISMATCH",
            "provenance does not commit to the schemas used by this validation",
            ARTIFACT_FILES["coordinator_envelope"],
            "$.provenance.version_hashes.schema_bundle_sha256",
        )
    if version_hashes["validator_sha256"] != expected_validator_hash:
        return make_error(
            stage,
            "HASH_VALIDATOR_MISMATCH",
            "provenance does not commit to the validator executing this bundle",
            ARTIFACT_FILES["coordinator_envelope"],
            "$.provenance.version_hashes.validator_sha256",
        )

    if (
        a0_input["coordinator_envelope_commitment_sha256"]
        != canonical_sha256(coordinator)
    ):
        return make_error(
            stage,
            "HASH_COORDINATOR_COMMITMENT",
            "public A0 input does not bind the coordinator envelope content",
            ARTIFACT_FILES["a0_input"],
            "$.coordinator_envelope_commitment_sha256",
        )

    previous_prefix_hash: Optional[str] = None
    for index, (entry, observation) in enumerate(
        zip(artifacts["prefix_commits"], a0_input["prefix_observations"])
    ):
        if entry["previous_entry_sha256"] != previous_prefix_hash:
            return make_error(
                stage,
                "HASH_PREFIX_PREVIOUS_MISMATCH",
                "rolling prefix entry does not bind the previous commitment",
                PREFIX_COMMIT_LOG_FILE,
                "$[%d].previous_entry_sha256" % index,
            )
        if entry["observation_sha256"] != canonical_sha256(observation):
            return make_error(
                stage,
                "HASH_PREFIX_OBSERVATION_MISMATCH",
                "rolling prefix commitment does not bind the corresponding observation bytes",
                PREFIX_COMMIT_LOG_FILE,
                "$[%d].observation_sha256" % index,
            )
        expected_entry_hash = chained_entry_sha256(entry)
        if entry["entry_sha256"] != expected_entry_hash:
            return make_error(
                stage,
                "HASH_PREFIX_ENTRY_MISMATCH",
                "rolling prefix entry hash is invalid",
                PREFIX_COMMIT_LOG_FILE,
                "$[%d].entry_sha256" % index,
            )
        previous_prefix_hash = entry["entry_sha256"]
    if a0_input["prefix_chain_tip_sha256"] != previous_prefix_hash:
        return make_error(
            stage,
            "HASH_PREFIX_TIP_MISMATCH",
            "A0 input does not bind the complete rolling prefix chain tip",
            ARTIFACT_FILES["a0_input"],
            "$.prefix_chain_tip_sha256",
        )

    instruction = a0_input["agent_visible_instruction"]
    if hashlib.sha256(instruction["text"].encode("utf-8")).hexdigest() != instruction["content_sha256"]:
        return make_error(
            stage,
            "HASH_INSTRUCTION_CONTENT",
            "instruction content hash is incorrect",
            ARTIFACT_FILES["a0_input"],
            "$.agent_visible_instruction.content_sha256",
        )
    for index, source in enumerate(a0_input["normative_schema"]["sources"]):
        if hashlib.sha256(source["content"].encode("utf-8")).hexdigest() != source["content_sha256"]:
            return make_error(
                stage,
                "HASH_NORMATIVE_SOURCE_CONTENT",
                "normative source content hash is incorrect",
                ARTIFACT_FILES["a0_input"],
                "$.normative_schema.sources[%d].content_sha256" % index,
            )

    source_snapshot = coordinator["source_snapshot"]
    raw_path = ensure_within_bundle(
        bundle_dir,
        source_snapshot["raw_response_relative_path"],
    )
    if raw_path is None:
        return make_error(
            stage,
            "HASH_SOURCE_PATH_INVALID",
            "source snapshot path is missing or escapes the bundle",
            ARTIFACT_FILES["coordinator_envelope"],
            "$.source_snapshot.raw_response_relative_path",
        )
    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != source_snapshot["raw_response_sha256"]:
        return make_error(
            stage,
            "HASH_SOURCE_FILE_MISMATCH",
            "source snapshot bytes do not match the committed hash",
            ARTIFACT_FILES["coordinator_envelope"],
            "$.source_snapshot.raw_response_sha256",
        )

    asset_by_id: Dict[str, Mapping[str, Any]] = {}
    asset_paths: set = set()
    for index, asset in enumerate(coordinator["asset_manifest"]):
        if asset["asset_id"] in asset_by_id:
            return make_error(
                stage,
                "HASH_ASSET_ID_COLLISION",
                "asset ids must be unique",
                ARTIFACT_FILES["coordinator_envelope"],
                "$.asset_manifest[%d].asset_id" % index,
            )
        if asset["relative_path"] in asset_paths:
            return make_error(
                stage,
                "HASH_ASSET_PATH_COLLISION",
                "asset paths must be unique",
                ARTIFACT_FILES["coordinator_envelope"],
                "$.asset_manifest[%d].relative_path" % index,
            )
        asset_by_id[asset["asset_id"]] = asset
        asset_paths.add(asset["relative_path"])
        asset_path = ensure_within_bundle(bundle_dir, asset["relative_path"])
        if asset_path is None:
            return make_error(
                stage,
                "HASH_ASSET_PATH_INVALID",
                "asset path is missing or escapes the bundle",
                ARTIFACT_FILES["coordinator_envelope"],
                "$.asset_manifest[%d].relative_path" % index,
            )
        if hashlib.sha256(asset_path.read_bytes()).hexdigest() != asset["sha256"]:
            return make_error(
                stage,
                "HASH_ASSET_FILE_MISMATCH",
                "asset bytes do not match the committed hash",
                ARTIFACT_FILES["coordinator_envelope"],
                "$.asset_manifest[%d].sha256" % index,
            )

    for observation_index, observation in enumerate(a0_input["prefix_observations"]):
        if observation["missingness"] == "none" and not observation["assets"]:
            return make_error(
                stage,
                "HASH_AVAILABLE_OBSERVATION_WITHOUT_ASSET",
                "non-missing observation must expose at least one committed asset",
                ARTIFACT_FILES["a0_input"],
                "$.prefix_observations[%d].assets" % observation_index,
            )
        if observation["missingness"] != "none" and observation["assets"]:
            return make_error(
                stage,
                "HASH_MISSING_OBSERVATION_WITH_ASSET",
                "explicitly missing observation cannot expose an asset",
                ARTIFACT_FILES["a0_input"],
                "$.prefix_observations[%d].assets" % observation_index,
            )
        for asset_index, public_ref in enumerate(observation["assets"]):
            private_asset = asset_by_id.get(public_ref["asset_id"])
            if (
                private_asset is None
                or private_asset["sha256"] != public_ref["sha256"]
                or private_asset["observation_ordinal"]
                != observation["observation_ordinal"]
            ):
                return make_error(
                    stage,
                    "HASH_PUBLIC_ASSET_REF_MISMATCH",
                    "public asset reference does not resolve to the same-ordinal coordinator asset",
                    ARTIFACT_FILES["a0_input"],
                    "$.prefix_observations[%d].assets[%d]" % (
                        observation_index,
                        asset_index,
                    ),
                )

    ref_checks = (
        (
            a0_label["a0_input_ref"],
            a0_input,
            ARTIFACT_FILES["a0_label"],
            "$.a0_input_ref",
        ),
        (
            a1_reveal["a0_input_ref"],
            a0_input,
            ARTIFACT_FILES["a1_reveal"],
            "$.a0_input_ref",
        ),
        (
            a1_reveal["a0_label_ref"],
            a0_label,
            ARTIFACT_FILES["a1_reveal"],
            "$.a0_label_ref",
        ),
        (
            a1_label["a0_input_ref"],
            a0_input,
            ARTIFACT_FILES["a1_label"],
            "$.a0_input_ref",
        ),
        (
            a1_label["a0_label_ref"],
            a0_label,
            ARTIFACT_FILES["a1_label"],
            "$.a0_label_ref",
        ),
        (
            a1_label["a1_reveal_ref"],
            a1_reveal,
            ARTIFACT_FILES["a1_label"],
            "$.a1_reveal_ref",
        ),
    )
    for actual_ref, expected_artifact, artifact_name, path in ref_checks:
        error = _verify_artifact_ref(
            actual_ref,
            expected_artifact,
            artifact_name,
            path,
        )
        if error:
            return error

    expected_event_hash = adjudicated_event_id(
        a0_label["adjudicated_event_preimage"]
    )
    if a0_label["adjudicated_event_id"] != expected_event_hash:
        return make_error(
            stage,
            "HASH_A0_EVENT_PREIMAGE_MISMATCH",
            "A0 event sha256 does not match location plus independently frozen A0 semantics",
            ARTIFACT_FILES["a0_label"],
            "$.adjudicated_event_id",
        )
    for artifact_name, value, path in (
        (
            ARTIFACT_FILES["a1_reveal"],
            a1_reveal["adjudicated_event_id"],
            "$.adjudicated_event_id",
        ),
        (
            ARTIFACT_FILES["a1_label"],
            a1_label["adjudicated_event_id"],
            "$.adjudicated_event_id",
        ),
    ):
        if value != expected_event_hash:
            return make_error(
                stage,
                "HASH_A0_EVENT_LINK_MISMATCH",
                "A1 artifact does not bind the A0-derived event id",
                artifact_name,
                path,
            )

    evidence_entries: List[Tuple[Mapping[str, Any], str, str]] = []
    if a0_label["p_old"]["evidence_pointer"] is not None:
        evidence_entries.append(
            (
                a0_label["p_old"]["evidence_pointer"],
                ARTIFACT_FILES["a0_label"],
                "$.p_old.evidence_pointer",
            )
        )
    evidence_entries.append(
        (
            a0_label["p_new"]["evidence_pointer"],
            ARTIFACT_FILES["a0_label"],
            "$.p_new.evidence_pointer",
        )
    )
    for index, entry in enumerate(a0_label["update_source_evidence"]):
        evidence_entries.append(
            (
                entry["evidence_pointer"],
                ARTIFACT_FILES["a0_label"],
                "$.update_source_evidence[%d].evidence_pointer" % index,
            )
        )
    for pointer, artifact_name, path in evidence_entries:
        error = _verify_evidence_pointer(pointer, a0_input, artifact_name, path)
        if error:
            return error

    if a1_reveal["reveal_kind"] == "observed_action":
        evidence_artifact_id = a1_reveal["artifact_id"]
        evidence_ordinal = a1_reveal["behavior_evidence"][
            "after_observation_ordinal"
        ]
        evidence_hash = canonical_sha256(a1_reveal["behavior_evidence"])
        expected_source_kind = "candidate_action"
    else:
        omission = artifacts["omission_interval"]
        omission_ref = a1_reveal["behavior_evidence"]["omission_interval_ref"]
        error = _verify_artifact_ref(
            omission_ref,
            omission,
            ARTIFACT_FILES["a1_reveal"],
            "$.behavior_evidence.omission_interval_ref",
        )
        if error:
            return error
        if omission["adjudicated_event_id"] != expected_event_hash:
            return make_error(
                stage,
                "HASH_OMISSION_A0_EVENT_LINK",
                "omission interval must bind the A0-derived event id",
                OMISSION_INTERVAL_FILE,
                "$.adjudicated_event_id",
            )
        required_action_spec = a0_label["required_action_spec"]
        if (
            omission["required_action_spec_sha256"]
            != canonical_sha256(required_action_spec)
        ):
            return make_error(
                stage,
                "HASH_OMISSION_ACTION_SPEC",
                "omission interval must bind the complete A0-frozen action specification",
                OMISSION_INTERVAL_FILE,
                "$.required_action_spec_sha256",
            )
        if (
            omission["source_snapshot_sha256"]
            != coordinator["source_snapshot"]["raw_response_sha256"]
        ):
            return make_error(
                stage,
                "HASH_OMISSION_SOURCE_SNAPSHOT",
                "omission interval must bind the frozen source trajectory snapshot",
                OMISSION_INTERVAL_FILE,
                "$.source_snapshot_sha256",
            )
        previous_interval_hash: Optional[str] = None
        for interval_index, interval_entry in enumerate(omission["entries"]):
            if interval_entry["previous_entry_sha256"] != previous_interval_hash:
                return make_error(
                    stage,
                    "HASH_OMISSION_PREVIOUS_MISMATCH",
                    "omission interval chain does not bind the previous entry",
                    OMISSION_INTERVAL_FILE,
                    "$.entries[%d].previous_entry_sha256" % interval_index,
                )
            expected_interval_hash = chained_entry_sha256(interval_entry)
            if interval_entry["entry_sha256"] != expected_interval_hash:
                return make_error(
                    stage,
                    "HASH_OMISSION_ENTRY_MISMATCH",
                    "omission interval entry hash is invalid",
                    OMISSION_INTERVAL_FILE,
                    "$.entries[%d].entry_sha256" % interval_index,
                )
            previous_interval_hash = interval_entry["entry_sha256"]
        if omission["chain_tip_sha256"] != previous_interval_hash:
            return make_error(
                stage,
                "HASH_OMISSION_TIP_MISMATCH",
                "omission interval packet does not bind its complete chain tip",
                OMISSION_INTERVAL_FILE,
                "$.chain_tip_sha256",
            )
        last_interval_entry = omission["entries"][-1]
        if (
            omission["deadline_evidence"]["content_sha256"]
            != canonical_sha256(last_interval_entry)
        ):
            return make_error(
                stage,
                "HASH_OMISSION_DEADLINE_CONTENT",
                "deadline evidence must bind the final committed interval entry",
                OMISSION_INTERVAL_FILE,
                "$.deadline_evidence.content_sha256",
            )
        evidence_artifact_id = omission["artifact_id"]
        evidence_ordinal = omission["deadline_observation_ordinal"]
        evidence_hash = canonical_sha256(last_interval_entry)
        expected_source_kind = "omission_interval"

    for index, assessment in enumerate(a1_label["affected_obligation_assessments"]):
        pointer = assessment["evidence_pointer"]
        if (
            pointer["artifact_id"] != evidence_artifact_id
            or pointer["observation_ordinal"] != evidence_ordinal
            or pointer["content_sha256"] != evidence_hash
            or pointer["source_kind"] != expected_source_kind
        ):
            return make_error(
                stage,
                "HASH_A1_EVIDENCE_POINTER_CONTENT",
                "A1 behavioral evidence must resolve to the selected action or complete omission interval",
                ARTIFACT_FILES["a1_label"],
                "$.affected_obligation_assessments[%d].evidence_pointer" % index,
            )

    expected_artifacts_by_type = {
        name: artifacts[name] for name in ARTIFACT_FILES
    }
    if "omission_interval" in artifacts:
        expected_artifacts_by_type["omission_interval"] = artifacts[
            "omission_interval"
        ]
    for index, event in enumerate(artifacts["audit_events"]):
        event_type = event["event_type"]
        expected_type = EVENT_ARTIFACT_TYPE.get(event_type)
        if expected_type is None:
            continue
        expected_ref = artifact_ref(expected_artifacts_by_type[expected_type])
        if event["artifact_ref"] != expected_ref:
            return make_error(
                stage,
                "HASH_AUDIT_ARTIFACT_REF",
                "audit event artifact reference does not resolve",
                AUDIT_LOG_FILE,
                "$[%d].artifact_ref" % index,
            )
        if event["version_hashes"] != version_hashes:
            return make_error(
                stage,
                "HASH_VERSION_SET_MISMATCH",
                "all audit events must use the coordinator-frozen version hash set",
                AUDIT_LOG_FILE,
                "$[%d].version_hashes" % index,
            )
    return None


def first_chain_exposure_error(
    artifacts: Mapping[str, Any],
) -> Optional[Dict[str, Any]]:
    stage = STAGE_ORDER[5]
    events = artifacts["audit_events"]
    is_omission = "omission_interval" in artifacts
    expected_audit_types = (
        EXPECTED_OMISSION_AUDIT_TYPES if is_omission else EXPECTED_AUDIT_TYPES
    )
    sequences = [event["sequence"] for event in events]
    if len(sequences) != len(set(sequences)):
        return make_error(
            stage,
            "CHAIN_FORK",
            "duplicate sequence numbers constitute a detectable audit-log fork",
            AUDIT_LOG_FILE,
        )
    if len(events) != len(expected_audit_types):
        return make_error(
            stage,
            "CHAIN_REQUIRED_EVENT_SET",
            "all mandatory lifecycle events for the selected reveal branch must be present",
            AUDIT_LOG_FILE,
        )
    if sequences != list(range(len(events))):
        return make_error(
            stage,
            "CHAIN_SEQUENCE_REORDER",
            "audit events must remain in contiguous append order",
            AUDIT_LOG_FILE,
        )
    event_types = tuple(event["event_type"] for event in events)
    if event_types != expected_audit_types:
        return make_error(
            stage,
            "CHAIN_EVENT_ORDER",
            "audit lifecycle event order is invalid or an event was replaced",
            AUDIT_LOG_FILE,
        )
    log_ids = {event["audit_log_id"] for event in events}
    if len(log_ids) != 1:
        return make_error(
            stage,
            "CHAIN_LOG_ID_MISMATCH",
            "all audit events must share one audit_log_id",
            AUDIT_LOG_FILE,
        )

    previous_hash: Optional[str] = None
    previous_time: Optional[datetime] = None
    for index, event in enumerate(events):
        if event["previous_entry_sha256"] != previous_hash:
            return make_error(
                stage,
                "CHAIN_PREVIOUS_HASH_MISMATCH",
                "previous_entry_sha256 does not bind the preceding entry",
                AUDIT_LOG_FILE,
                "$[%d].previous_entry_sha256" % index,
            )
        expected_entry_hash = audit_entry_sha256(event)
        if event["entry_sha256"] != expected_entry_hash:
            return make_error(
                stage,
                "CHAIN_ENTRY_HASH_MISMATCH",
                "entry_sha256 does not match the canonical audit event preimage",
                AUDIT_LOG_FILE,
                "$[%d].entry_sha256" % index,
            )
        occurred_at = parse_timestamp(event["occurred_at"])
        if previous_time is not None and occurred_at <= previous_time:
            return make_error(
                stage,
                "CHAIN_TIME_ORDER",
                "audit timestamps must be strictly increasing",
                AUDIT_LOG_FILE,
                "$[%d].occurred_at" % index,
            )
        previous_time = occurred_at
        previous_hash = event["entry_sha256"]

    coordinator = artifacts["coordinator_envelope"]
    a0_input = artifacts["a0_input"]
    a0_label = artifacts["a0_label"]
    a1_reveal = artifacts["a1_reveal"]
    a1_label = artifacts["a1_label"]
    if is_omission:
        expected_event_times = (
            coordinator["created_at"],
            a0_input["frozen_at"],
            a0_label["frozen_at"],
            artifacts["omission_interval"]["frozen_at"],
            events[4]["occurred_at"],
            a1_reveal["revealed_at"],
            a1_label["frozen_at"],
        )
    else:
        expected_event_times = (
            coordinator["created_at"],
            a0_input["frozen_at"],
            a0_label["frozen_at"],
            events[3]["occurred_at"],
            a1_reveal["revealed_at"],
            a1_label["frozen_at"],
        )
    if tuple(event["occurred_at"] for event in events) != expected_event_times:
        return make_error(
            stage,
            "CHAIN_ARTIFACT_TIME_MISMATCH",
            "lifecycle event times must bind the corresponding artifact freeze/reveal times",
            AUDIT_LOG_FILE,
        )

    if is_omission:
        expected_roles = (
            "coordinator",
            "coordinator",
            "a0_annotator",
            "coordinator",
            "coordinator",
            "coordinator",
            "a1_annotator",
        )
        expected_recipients = (
            {"coordinator"},
            {"a0_annotator"},
            {"coordinator"},
            {"coordinator"},
            {"coordinator"},
            {"a1_annotator"},
            {"coordinator"},
        )
        expected_visible_types = (
            {"coordinator_envelope"},
            {"a0_input"},
            {"a0_label"},
            {"omission_interval"},
            {"a1_reveal"},
            {"a0_input", "a0_label", "omission_interval", "a1_reveal"},
            {"a1_label"},
        )
    else:
        expected_roles = (
            "coordinator",
            "coordinator",
            "a0_annotator",
            "coordinator",
            "coordinator",
            "a1_annotator",
        )
        expected_recipients = (
            {"coordinator"},
            {"a0_annotator"},
            {"coordinator"},
            {"coordinator"},
            {"a1_annotator"},
            {"coordinator"},
        )
        expected_visible_types = (
            {"coordinator_envelope"},
            {"a0_input"},
            {"a0_label"},
            {"a1_reveal"},
            {"a0_input", "a0_label", "a1_reveal"},
            {"a1_label"},
        )
    artifact_type_by_id = {
        artifacts[name]["artifact_id"]: name for name in ARTIFACT_FILES
    }
    if is_omission:
        artifact_type_by_id[artifacts["omission_interval"]["artifact_id"]] = (
            "omission_interval"
        )
    for index, event in enumerate(events):
        if event["actor"]["role"] != expected_roles[index]:
            return make_error(
                stage,
                "EXPOSURE_ACTOR_ROLE",
                "actor role violates the frozen lifecycle role separation",
                AUDIT_LOG_FILE,
                "$[%d].actor.role" % index,
            )
        recipients = set(event["exposure"]["recipient_roles"])
        if recipients != expected_recipients[index]:
            return make_error(
                stage,
                "EXPOSURE_RECIPIENT_ROLE",
                "recipient roles violate the frozen lifecycle exposure policy",
                AUDIT_LOG_FILE,
                "$[%d].exposure.recipient_roles" % index,
            )
        visible_types = {
            artifact_type_by_id.get(ref["artifact_id"], "unknown")
            for ref in event["exposure"]["visible_artifacts"]
        }
        if visible_types != expected_visible_types[index]:
            return make_error(
                stage,
                "EXPOSURE_VISIBLE_ARTIFACT_SET",
                "visible artifact set violates A0/A1 physical isolation",
                AUDIT_LOG_FILE,
                "$[%d].exposure.visible_artifacts" % index,
            )
        expected_refs = {
            tuple(sorted(artifact_ref(artifacts[name]).items()))
            for name in expected_visible_types[index]
        }
        actual_refs = {
            tuple(sorted(ref.items()))
            for ref in event["exposure"]["visible_artifacts"]
        }
        if actual_refs != expected_refs:
            return make_error(
                stage,
                "EXPOSURE_VISIBLE_ARTIFACT_HASH",
                "visible artifact commitment is stale or substituted",
                AUDIT_LOG_FILE,
                "$[%d].exposure.visible_artifacts" % index,
            )

    if events[2]["actor"]["actor_alias"] != a0_label["annotator_alias"]:
        return make_error(
            stage,
            "EXPOSURE_A0_ACTOR_MISMATCH",
            "A0 label annotator must match the A0 freeze audit actor",
            AUDIT_LOG_FILE,
            "$[2].actor.actor_alias",
        )
    a1_label_event_index = len(events) - 1
    if (
        events[a1_label_event_index]["actor"]["actor_alias"]
        != a1_label["annotator_alias"]
    ):
        return make_error(
            stage,
            "EXPOSURE_A1_ACTOR_MISMATCH",
            "A1 label annotator must match the A1 freeze audit actor",
            AUDIT_LOG_FILE,
            "$[%d].actor.actor_alias" % a1_label_event_index,
        )

    private_identity = coordinator["identity"]
    private_source = coordinator["source_snapshot"]
    sensitive_exact = {
        private_identity["task_id"],
        private_identity["hosted_config_id"],
        private_identity["model_family_id"],
        private_identity["trajectory_id"],
        private_source["source_detail_url"],
        private_source["raw_response_relative_path"],
    }
    public_names = ["a0_input", "a0_label", "a1_reveal", "a1_label"]
    if is_omission:
        public_names.append("omission_interval")
    for name in public_names:
        value = artifacts[name]
        for path, node in walk_objects(value):
            forbidden = set(node).intersection(FORBIDDEN_PUBLIC_KEYS)
            if forbidden:
                return make_error(
                    stage,
                    "EXPOSURE_FORBIDDEN_PUBLIC_KEY",
                    "public artifact contains coordinator-only or outcome-bearing key %s"
                    % sorted(forbidden)[0],
                    (
                        ARTIFACT_FILES[name]
                        if name in ARTIFACT_FILES
                        else OMISSION_INTERVAL_FILE
                    ),
                    path,
                )
        for path, text_value in walk_strings(value):
            if URL_OR_PATH_RE.search(text_value):
                return make_error(
                    stage,
                    "EXPOSURE_URL_OR_PATH_LEAK",
                    "public artifact contains a raw URL or filesystem path",
                    (
                        ARTIFACT_FILES[name]
                        if name in ARTIFACT_FILES
                        else OMISSION_INTERVAL_FILE
                    ),
                    path,
                )
            for secret in sensitive_exact:
                if text_value == secret or (
                    len(secret) >= 6 and secret in text_value
                ):
                    return make_error(
                        stage,
                        "EXPOSURE_IDENTITY_VALUE_LEAK",
                        "public artifact exposes an exact coordinator-only identity value",
                        (
                            ARTIFACT_FILES[name]
                            if name in ARTIFACT_FILES
                            else OMISSION_INTERVAL_FILE
                        ),
                        path,
                    )

    for index, event in enumerate(events):
        recipients = set(event["exposure"]["recipient_roles"])
        visible_ids = {
            item["artifact_id"] for item in event["exposure"]["visible_artifacts"]
        }
        if (
            recipients.intersection({"a0_annotator", "a1_annotator"})
            and coordinator["artifact_id"] in visible_ids
        ):
            return make_error(
                stage,
                "EXPOSURE_COORDINATOR_ENVELOPE",
                "annotators must never receive the coordinator envelope",
                AUDIT_LOG_FILE,
                "$[%d].exposure.visible_artifacts" % index,
            )
        if (
            "a0_annotator" in recipients
            and (
                a1_reveal["artifact_id"] in visible_ids
                or a1_label["artifact_id"] in visible_ids
            )
        ):
            return make_error(
                stage,
                "EXPOSURE_A0_SEES_A1",
                "A0 annotator exposure contains A1 information",
                AUDIT_LOG_FILE,
                "$[%d].exposure.visible_artifacts" % index,
            )
    return None


def bundle_digest(artifacts: Mapping[str, Any]) -> str:
    entries = [
        [ARTIFACT_FILES[name], canonical_sha256(artifacts[name])]
        for name in ARTIFACT_FILES
    ]
    if artifacts.get("audit_events"):
        entries.append(
            [AUDIT_LOG_FILE, artifacts["audit_events"][-1].get("entry_sha256")]
        )
    if artifacts.get("prefix_commits"):
        entries.append(
            [
                PREFIX_COMMIT_LOG_FILE,
                artifacts["prefix_commits"][-1].get("entry_sha256"),
            ]
        )
    if artifacts.get("omission_interval"):
        entries.append(
            [
                OMISSION_INTERVAL_FILE,
                canonical_sha256(artifacts["omission_interval"]),
            ]
        )
    return canonical_sha256(["stage0f-measurement-bundle-v1", entries])


def task_bundle_digest(
    barrier: Mapping[str, Any],
    units: Sequence[Mapping[str, Any]],
) -> str:
    unit_entries = sorted(
        [
            [
                unit["a0_input"]["unit_alias"],
                bundle_digest(unit),
            ]
            for unit in units
        ],
        key=lambda item: item[0].encode("utf-8"),
    )
    return canonical_sha256(
        [
            "stage0f-task-measurement-bundle-v1",
            canonical_sha256(barrier),
            unit_entries,
        ]
    )


def verdict(
    valid: bool,
    errors: Sequence[Mapping[str, Any]],
    completed_stages: Sequence[str],
    artifacts: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    stages = []
    failed_stage = errors[0]["stage"] if errors else None
    for stage in STAGE_ORDER:
        if stage in completed_stages:
            status = "PASS"
        elif stage == failed_stage:
            status = "FAIL"
        else:
            status = "SKIP"
        stages.append({"name": stage, "status": status})
    result: Dict[str, Any] = {
        "valid": valid,
        "verdict": "PASS" if valid else "FAIL",
        "validator": {
            "schema_version": SCHEMA_VERSION,
            "canonicalization": CANONICALIZATION,
            "jsonschema_version": (
                importlib.metadata.version("jsonschema")
                if jsonschema is not None
                else None
            ),
        },
        "stages": stages,
        "errors": list(errors),
    }
    if artifacts is not None:
        result["bundle_sha256"] = bundle_digest(artifacts)
    else:
        result["bundle_sha256"] = None
    return result


def _task_verdict(
    valid: bool,
    errors: Sequence[Mapping[str, Any]],
    completed_stages: Sequence[str],
    barrier: Optional[Mapping[str, Any]] = None,
    units: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    result = verdict(valid, errors, completed_stages)
    if barrier is not None and units is not None:
        result["bundle_sha256"] = task_bundle_digest(barrier, units)
        result["bundle_scope"] = "task_all_six_configs"
        result["unit_count"] = len(units)
    return result


def _load_task_components(
    task_dir: Path,
    schema_dir: Path,
) -> Tuple[
    Optional[Mapping[str, Any]],
    Optional[Mapping[str, Any]],
    Optional[List[Tuple[Path, Mapping[str, Any]]]],
    List[Dict[str, Any]],
]:
    stage = STAGE_ORDER[0]
    barrier_path = task_dir / TASK_BARRIER_FILE
    if not barrier_path.is_file():
        return None, None, None, [
            make_error(
                stage,
                "TASK_BARRIER_FILE_MISSING",
                "task-level validation requires task_barrier.json",
                TASK_BARRIER_FILE,
            )
        ]
    try:
        barrier = load_json_no_duplicates(barrier_path)
    except DuplicateKeyError as exc:
        return None, None, None, [
            make_error(
                stage,
                "DUPLICATE_JSON_KEY",
                str(exc),
                TASK_BARRIER_FILE,
                "$.%s" % exc.key,
            )
        ]
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return None, None, None, [
            make_error(stage, "INVALID_JSON", str(exc), TASK_BARRIER_FILE)
        ]

    units_dir = task_dir / "units"
    unit_dirs = (
        sorted(
            [path for path in units_dir.iterdir() if path.is_dir()],
            key=lambda path: path.name.encode("utf-8"),
        )
        if units_dir.is_dir()
        else []
    )
    loaded_units: List[Tuple[Path, Mapping[str, Any]]] = []
    schemas: Optional[Mapping[str, Any]] = None
    errors: List[Dict[str, Any]] = []
    for unit_dir in unit_dirs:
        loaded, unit_errors = load_bundle_and_schemas(unit_dir, schema_dir)
        if unit_errors:
            for error in unit_errors:
                copied = dict(error)
                artifact = copied.get("artifact")
                if artifact:
                    copied["artifact"] = "units/%s/%s" % (
                        unit_dir.name,
                        artifact,
                    )
                errors.append(copied)
            continue
        assert loaded is not None
        if schemas is None:
            schemas = loaded["schemas"]
        loaded_units.append((unit_dir, loaded["artifacts"]))
    if errors:
        return barrier, schemas, loaded_units, errors
    if schemas is None:
        schemas = {}
        for name, filename in SCHEMA_FILES.items():
            path = schema_dir / filename
            if not path.is_file():
                errors.append(
                    make_error(
                        stage,
                        "SCHEMA_FILE_MISSING",
                        "required schema file is missing",
                        filename,
                    )
                )
                continue
            try:
                schemas[name] = load_json_no_duplicates(path)
            except DuplicateKeyError as exc:
                errors.append(
                    make_error(
                        stage,
                        "DUPLICATE_JSON_KEY",
                        str(exc),
                        filename,
                        "$.%s" % exc.key,
                    )
                )
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                errors.append(
                    make_error(stage, "INVALID_JSON", str(exc), filename)
                )
    return barrier, schemas, loaded_units, errors


def validate_task_barrier_instance(
    barrier: Mapping[str, Any],
    schemas: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    stage = STAGE_ORDER[2]
    assert Draft202012Validator is not None
    assert FormatChecker is not None
    validator = Draft202012Validator(
        schemas["task_barrier"],
        registry=make_registry(schemas),
        format_checker=FormatChecker(),
    )
    return [
        make_error(
            stage,
            "SCHEMA_INSTANCE_INVALID",
            error.message,
            TASK_BARRIER_FILE,
            json_path(error.absolute_path),
        )
        for error in sorted(
            validator.iter_errors(barrier),
            key=lambda item: list(item.absolute_path),
        )
    ]


def first_task_barrier_semantic_error(
    barrier: Mapping[str, Any],
    units: Sequence[Mapping[str, Any]],
) -> Optional[Dict[str, Any]]:
    stage = STAGE_ORDER[3]
    if len(units) != 6:
        return make_error(
            stage,
            "SEM_TASK_BARRIER_UNIT_COUNT",
            "task barrier requires exactly six physically present hosted-config unit bundles",
            TASK_BARRIER_FILE,
            "$.unit_freezes",
        )
    aliases = [unit["a0_input"]["unit_alias"] for unit in units]
    if len(aliases) != len(set(aliases)):
        return make_error(
            stage,
            "SEM_TASK_BARRIER_UNIT_ALIAS_COLLISION",
            "six unit bundles require distinct unit aliases",
            TASK_BARRIER_FILE,
        )
    task_ids = {
        unit["coordinator_envelope"]["identity"]["task_id"] for unit in units
    }
    if task_ids != {barrier["task_id"]}:
        return make_error(
            stage,
            "SEM_TASK_BARRIER_TASK_MISMATCH",
            "all six coordinator envelopes must refer to the same frozen task",
            TASK_BARRIER_FILE,
            "$.task_id",
        )
    hosted_configs = [
        unit["coordinator_envelope"]["identity"]["hosted_config_id"]
        for unit in units
    ]
    if len(hosted_configs) != len(set(hosted_configs)):
        return make_error(
            stage,
            "SEM_TASK_BARRIER_CONFIG_COLLISION",
            "the barrier must cover six distinct hosted configs",
            TASK_BARRIER_FILE,
            "$.unit_freezes",
        )
    freeze_entries = barrier["unit_freezes"]
    freeze_aliases = [entry["unit_alias"] for entry in freeze_entries]
    if len(freeze_aliases) != len(set(freeze_aliases)) or set(freeze_aliases) != set(aliases):
        return make_error(
            stage,
            "SEM_TASK_BARRIER_FREEZE_SET",
            "barrier freeze set must contain every and only the six physical units",
            TASK_BARRIER_FILE,
            "$.unit_freezes",
        )
    entry_by_alias = {entry["unit_alias"]: entry for entry in freeze_entries}
    sealed_at = parse_timestamp(barrier["sealed_at"])
    latest_a0 = max(
        parse_timestamp(unit["a0_label"]["frozen_at"]) for unit in units
    )
    if latest_a0 >= sealed_at:
        return make_error(
            stage,
            "SEM_TASK_BARRIER_SEALED_EARLY",
            "barrier may seal only after all six A0 labels are frozen",
            TASK_BARRIER_FILE,
            "$.sealed_at",
        )
    for unit in units:
        alias = unit["a0_input"]["unit_alias"]
        entry = entry_by_alias[alias]
        if entry["hosted_config_id"] != unit["coordinator_envelope"]["identity"]["hosted_config_id"]:
            return make_error(
                stage,
                "SEM_TASK_BARRIER_CONFIG_LINK",
                "barrier hosted config does not match its coordinator envelope",
                TASK_BARRIER_FILE,
                "$.unit_freezes",
            )
        if entry["a0_label_frozen_at"] != unit["a0_label"]["frozen_at"]:
            return make_error(
                stage,
                "SEM_TASK_BARRIER_FREEZE_TIME",
                "barrier freeze timestamp does not match the A0 label artifact",
                TASK_BARRIER_FILE,
                "$.unit_freezes",
            )
        authorization_event = next(
            event
            for event in unit["audit_events"]
            if event["event_type"] == "a1_reveal_authorized"
        )
        if sealed_at >= parse_timestamp(authorization_event["occurred_at"]):
            return make_error(
                stage,
                "SEM_TASK_BARRIER_A1_OPENED_EARLY",
                "no A1 authorization may occur before the all-six A0 barrier seals",
                TASK_BARRIER_FILE,
                "$.sealed_at",
            )
        if sealed_at >= parse_timestamp(unit["a1_reveal"]["revealed_at"]):
            return make_error(
                stage,
                "SEM_TASK_BARRIER_A1_OPENED_EARLY",
                "no A1 reveal may occur before the all-six A0 barrier seals",
                TASK_BARRIER_FILE,
                "$.sealed_at",
            )
    return None


def first_task_barrier_hash_error(
    barrier: Mapping[str, Any],
    units: Sequence[Mapping[str, Any]],
) -> Optional[Dict[str, Any]]:
    stage = STAGE_ORDER[4]
    barrier_hash = canonical_sha256(barrier)
    entry_by_alias = {
        entry["unit_alias"]: entry for entry in barrier["unit_freezes"]
    }
    for unit in units:
        alias = unit["a0_input"]["unit_alias"]
        entry = entry_by_alias[alias]
        expected_values = {
            "coordinator_envelope_ref": artifact_ref(
                unit["coordinator_envelope"]
            ),
            "a0_input_ref": artifact_ref(unit["a0_input"]),
            "a0_label_ref": artifact_ref(unit["a0_label"]),
        }
        for key, expected in expected_values.items():
            if entry[key] != expected:
                return make_error(
                    stage,
                    "HASH_TASK_BARRIER_ARTIFACT_REF",
                    "task barrier contains a stale or substituted A0 artifact reference",
                    TASK_BARRIER_FILE,
                    "$.unit_freezes.%s.%s" % (alias, key),
                )
        if entry["prefix_chain_tip_sha256"] != unit["a0_input"]["prefix_chain_tip_sha256"]:
            return make_error(
                stage,
                "HASH_TASK_BARRIER_PREFIX_TIP",
                "task barrier must bind each unit rolling-prefix chain tip",
                TASK_BARRIER_FILE,
                "$.unit_freezes.%s.prefix_chain_tip_sha256" % alias,
            )
        if unit["a1_reveal"]["task_barrier_commitment_sha256"] != barrier_hash:
            return make_error(
                stage,
                "HASH_TASK_BARRIER_A1_LINK",
                "A1 reveal does not bind the all-six A0 barrier content",
                ARTIFACT_FILES["a1_reveal"],
                "$.task_barrier_commitment_sha256",
            )
    return None


def validate_task_bundle(task_dir: Path, schema_dir: Path) -> Dict[str, Any]:
    barrier, schemas, loaded_units, errors = _load_task_components(
        task_dir,
        schema_dir,
    )
    if errors:
        return _task_verdict(False, errors, [])
    assert barrier is not None
    assert schemas is not None
    assert loaded_units is not None
    units = [artifacts for _, artifacts in loaded_units]
    completed = [STAGE_ORDER[0]]

    if JSONSCHEMA_IMPORT_ERROR is not None:
        error = make_error(
            STAGE_ORDER[1],
            "DEPENDENCY_JSONSCHEMA_UNAVAILABLE",
            "Install the exact requirements-stage0f.txt environment; no hand-written Draft 2020-12 fallback is permitted: %s"
            % JSONSCHEMA_IMPORT_ERROR,
        )
        return _task_verdict(False, [error], completed, barrier, units)

    errors = validate_schema_meta(schemas)
    if errors:
        return _task_verdict(False, errors, completed, barrier, units)
    completed.append(STAGE_ORDER[1])

    errors = validate_task_barrier_instance(barrier, schemas)
    if not errors:
        for unit in units:
            errors = validate_instances(unit, schemas)
            if errors:
                break
    if errors:
        return _task_verdict(False, errors, completed, barrier, units)
    completed.append(STAGE_ORDER[2])

    for unit in units:
        error = first_semantic_error(unit)
        if error:
            return _task_verdict(False, [error], completed, barrier, units)
    error = first_task_barrier_semantic_error(barrier, units)
    if error:
        return _task_verdict(False, [error], completed, barrier, units)
    completed.append(STAGE_ORDER[3])

    for unit_dir, unit in loaded_units:
        error = first_content_hash_error(unit, schemas, unit_dir)
        if error:
            return _task_verdict(False, [error], completed, barrier, units)
    error = first_task_barrier_hash_error(barrier, units)
    if error:
        return _task_verdict(False, [error], completed, barrier, units)
    completed.append(STAGE_ORDER[4])

    for unit in units:
        error = first_chain_exposure_error(unit)
        if error:
            return _task_verdict(False, [error], completed, barrier, units)
    completed.append(STAGE_ORDER[5])
    return _task_verdict(True, [], completed, barrier, units)


def validate_task_bundle(task_dir: Path, schema_dir: Path) -> Dict[str, Any]:
    """Deprecated task gate: a task-local barrier is never sufficient."""

    return verdict(
        False,
        [
            make_error(
                STAGE_ORDER[3],
                "SEM_BLOCK_BARRIER_CONTEXT_REQUIRED",
                "task-level gating is prohibited; validate a full ontology/holdout block",
                str(task_dir),
            )
        ],
        [],
    )


def validate_bundle(bundle_dir: Path, schema_dir: Path) -> Dict[str, Any]:
    loaded, errors = load_bundle_and_schemas(bundle_dir, schema_dir)
    if errors:
        return verdict(False, errors, [])
    assert loaded is not None
    artifacts = loaded["artifacts"]
    schemas = loaded["schemas"]
    completed = [STAGE_ORDER[0]]

    if JSONSCHEMA_IMPORT_ERROR is not None:
        error = make_error(
            STAGE_ORDER[1],
            "DEPENDENCY_JSONSCHEMA_UNAVAILABLE",
            "Install the exact requirements-stage0f.txt environment; no hand-written Draft 2020-12 fallback is permitted: %s"
            % JSONSCHEMA_IMPORT_ERROR,
        )
        return verdict(False, [error], completed, artifacts)

    errors = validate_schema_meta(schemas)
    if errors:
        return verdict(False, errors, completed, artifacts)
    completed.append(STAGE_ORDER[1])

    errors = validate_instances(artifacts, schemas)
    if errors:
        return verdict(False, errors, completed, artifacts)
    completed.append(STAGE_ORDER[2])

    error = first_semantic_error(artifacts)
    if error:
        return verdict(False, [error], completed, artifacts)
    error = make_error(
        STAGE_ORDER[3],
        "SEM_BLOCK_BARRIER_CONTEXT_REQUIRED",
        "a single unit can never PASS: all block units/locations, A0 raw labels, and A0-only adjudications must freeze before any A1 reveal",
    )
    return verdict(False, [error], completed, artifacts)


def validate_block_bundle(block_dir: Path, schema_dir: Path) -> Dict[str, Any]:
    """Fail-closed block entry point pending the full multi-location ledger.

    A prior task-level six-config barrier was scientifically insufficient: it
    could still open one task's A1 while A0 annotation for another task in the
    same ontology/holdout block remained unfinished.  This entry point parses
    and formally validates the block-barrier schema, then deliberately returns
    NOT_READY until the block location manifest, all raw A0 labels, A0-only
    adjudications, and permanent role-exposure ledger are all implemented.
    """

    stage0 = STAGE_ORDER[0]
    barrier_path = block_dir / BLOCK_BARRIER_FILE
    if not barrier_path.is_file():
        return verdict(
            False,
            [
                make_error(
                    stage0,
                    "BLOCK_BARRIER_FILE_MISSING",
                    "full-block validation requires block_barrier.json",
                    BLOCK_BARRIER_FILE,
                )
            ],
            [],
        )
    try:
        barrier = load_json_no_duplicates(barrier_path)
        schemas = {
            name: load_json_no_duplicates(schema_dir / filename)
            for name, filename in SCHEMA_FILES.items()
        }
    except DuplicateKeyError as exc:
        return verdict(
            False,
            [
                make_error(
                    stage0,
                    "DUPLICATE_JSON_KEY",
                    str(exc),
                    BLOCK_BARRIER_FILE,
                    "$.%s" % exc.key,
                )
            ],
            [],
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return verdict(
            False,
            [make_error(stage0, "INVALID_JSON", str(exc), BLOCK_BARRIER_FILE)],
            [],
        )

    completed = [stage0]
    if JSONSCHEMA_IMPORT_ERROR is not None:
        return verdict(
            False,
            [
                make_error(
                    STAGE_ORDER[1],
                    "DEPENDENCY_JSONSCHEMA_UNAVAILABLE",
                    "Install requirements-stage0f.txt; no schema fallback is permitted: %s"
                    % JSONSCHEMA_IMPORT_ERROR,
                )
            ],
            completed,
        )
    errors = validate_schema_meta(schemas)
    if errors:
        return verdict(False, errors, completed)
    completed.append(STAGE_ORDER[1])
    assert Draft202012Validator is not None
    assert FormatChecker is not None
    validator = Draft202012Validator(
        schemas["block_barrier"],
        registry=make_registry(schemas),
        format_checker=FormatChecker(),
    )
    errors = [
        make_error(
            STAGE_ORDER[2],
            "SCHEMA_INSTANCE_INVALID",
            error.message,
            BLOCK_BARRIER_FILE,
            json_path(error.absolute_path),
        )
        for error in sorted(
            validator.iter_errors(barrier),
            key=lambda item: list(item.absolute_path),
        )
    ]
    if errors:
        return verdict(False, errors, completed)
    completed.append(STAGE_ORDER[2])
    return verdict(
        False,
        [
            make_error(
                STAGE_ORDER[3],
                "SEM_BLOCK_BARRIER_LEDGER_NOT_IMPLEMENTED",
                "NOT_READY: full block location manifest, all A0 raw labels, A0-only adjudications, multiple same-location events, permanent A0/A1/StageB actor separation, and block-wide leak invalidation are required before any A1",
                BLOCK_BARRIER_FILE,
            )
        ],
        completed,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Stage 0F physically separated A0/A1 bundle."
    )
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "schemas",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    if (args.bundle_dir / BLOCK_BARRIER_FILE).is_file():
        result = validate_block_bundle(args.bundle_dir, args.schema_dir)
    else:
        result = validate_bundle(args.bundle_dir, args.schema_dir)
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
            indent=2 if args.pretty else None,
            separators=None if args.pretty else (",", ":"),
        )
    )
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
