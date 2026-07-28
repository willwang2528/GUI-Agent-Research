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
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple
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
BLOCK_A0_RAW_LABEL_SERIALIZATION = "stage0f-block-a0-raw-label-id-v1"
BLOCK_A0_CASE_SERIALIZATION = "stage0f-block-a0-case-id-v1"
BLOCK_A0_PATH_SERIALIZATION = "stage0f-block-a0-independent-path-id-v1"
A0_RAW_SUPPORT_ADJUDICATION_RULE = (
    "stage0f-a0-raw-support-adjudication-v2"
)
A0_RAW_FIELDS = (
    "p_old_proposition_id",
    "p_new_proposition_id",
    "update_source_labels",
    "normative_action_difference",
    "affected_obligation_ids",
    "boundary_type",
)
A0_FROZEN_TRANSFORM_ID = "sorted_set_union_utf8_v1"
BLOCK_EXPOSURE_ENTRY_SERIALIZATION = "stage0f-block-exposure-entry-v1"
RAW_TRAJECTORY_FORMAT = "stage0f-block-raw-trajectory-json-v1"
RAW_TRAJECTORY_PARSER_ID = (
    "stage0f-validator:synthetic-published-trajectory-v1"
)
RAW_TRAJECTORY_PROJECTION = "observation-current-action-v1"
SYNTHETIC_PUBLISHED_TRAJECTORY_FORMAT = (
    "stage0f-synthetic-published-trajectory-v1"
)

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
    "block_frame": "stage0f_block_frame.schema.json",
    "block_location_manifest": "stage0f_block_location_manifest.schema.json",
    "block_raw_trajectory": "stage0f_block_raw_trajectory.schema.json",
    "block_stream_ledger": "stage0f_block_stream_ledger.schema.json",
    "block_a0_submissions": "stage0f_block_a0_submissions.schema.json",
    "block_a0_adjudication": "stage0f_block_a0_adjudication.schema.json",
    "source_search_result": "stage0f_source_search_result.schema.json",
    "block_a1_barrier": "stage0f_block_a1_barrier.schema.json",
    "stage_b_gate": "stage0f_stage_b_gate.schema.json",
    "block_exposure_event": "stage0f_block_exposure_event.schema.json",
    "role_history": "stage0f_role_history.schema.json",
    "omission_interval": "stage0f_omission_interval.schema.json",
}

AUDIT_LOG_FILE = "audit_events.ndjson"
PREFIX_COMMIT_LOG_FILE = "prefix_commits.ndjson"
BLOCK_BARRIER_FILE = "block_barrier.json"
BLOCK_FRAME_FILE = "block_frame.json"
BLOCK_LOCATION_MANIFEST_FILE = "block_location_manifest.json"
BLOCK_A1_BARRIER_FILE = "block_a1_barrier.json"
STAGE_B_GATE_FILE = "stage_b_gate.json"
BLOCK_EXPOSURE_LOG_FILE = "block_exposure_events.ndjson"
ROLE_HISTORY_FILE = "role_history.json"
OMISSION_INTERVAL_FILE = "omission_interval.json"
BLOCK_FIXED_FILES: Mapping[str, str] = {
    "block_frame": BLOCK_FRAME_FILE,
    "block_location_manifest": BLOCK_LOCATION_MANIFEST_FILE,
    "block_barrier": BLOCK_BARRIER_FILE,
    "block_a1_barrier": BLOCK_A1_BARRIER_FILE,
    "stage_b_gate": STAGE_B_GATE_FILE,
    "role_history": ROLE_HISTORY_FILE,
}
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


def block_a0_raw_label_id(
    unit_alias: str,
    boundary_location_id_value: str,
    schema_bundle_hash: str,
    codebook_hash: str,
    annotator_alias: str,
    semantic_payload: Mapping[str, Any],
) -> str:
    """Derive a raw A0 id from an outcome-blind frozen preimage."""

    return canonical_sha256(
        [
            BLOCK_A0_RAW_LABEL_SERIALIZATION,
            unit_alias,
            boundary_location_id_value,
            schema_bundle_hash,
            codebook_hash,
            annotator_alias,
            semantic_payload,
        ]
    )


def block_a0_case_id(
    unit_alias: str,
    boundary_location_id_value: str,
    raw_label_ids: Iterable[str],
) -> str:
    """Derive a case identity from its immutable raw-label denominator."""

    return canonical_sha256(
        [
            BLOCK_A0_CASE_SERIALIZATION,
            unit_alias,
            boundary_location_id_value,
            utf8_sorted(raw_label_ids),
        ]
    )


def block_a0_independent_path_id(
    case_id: str,
    raw_label_ids: Iterable[str],
) -> str:
    """Derive a path identity without treating it as annotator agreement."""

    return canonical_sha256(
        [
            BLOCK_A0_PATH_SERIALIZATION,
            case_id,
            utf8_sorted(raw_label_ids),
        ]
    )


def a0_raw_semantic_projection(
    semantic_payload: Mapping[str, Any],
) -> Dict[str, Any]:
    """Normalize every substantive raw field without losing its value."""

    return {
        "p_old_proposition_id": semantic_payload[
            "p_old_proposition_id"
        ],
        "p_new_proposition_id": semantic_payload[
            "p_new_proposition_id"
        ],
        "update_source_labels": utf8_sorted(
            semantic_payload["update_source_labels"]
        ),
        "normative_action_difference": semantic_payload[
            "normative_action_difference"
        ],
        "affected_obligation_ids": utf8_sorted(
            semantic_payload["affected_obligation_ids"]
        ),
        "boundary_type": semantic_payload["boundary_type"],
    }


def a0_label_semantic_projection(
    label: Mapping[str, Any],
) -> Dict[str, Any]:
    """Project the final claim onto every substantive adjudicated field."""

    return {
        "p_old_proposition_id": label["p_old"]["proposition_id"],
        "p_new_proposition_id": label["p_new"]["proposition_id"],
        "update_source_labels": a0_label_source_projection(label),
        "normative_action_difference": label[
            "normative_action_difference"
        ],
        "affected_obligation_ids": utf8_sorted(
            label["affected_obligation_ids"]
        ),
        "boundary_type": label["adjudicated_event_preimage"][
            "boundary_type"
        ],
    }


def a0_label_source_projection(label: Mapping[str, Any]) -> List[str]:
    """Return the canonical set-valued update-source projection."""

    return utf8_sorted(
        {
            item["label"]
            for item in label["update_source_evidence"]
        }
    )


def expected_raw_support_adjudication(
    label: Mapping[str, Any],
    support_raws: Sequence[Mapping[str, Any]],
    *,
    selected_raw_label_ids: Optional[Mapping[str, str]] = None,
    deterministic_transform_fields: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Build the exact v2 per-field adjudication record.

    This helper is intentionally lossless: every raw value hash is retained.
    A disagreement is resolved only by selecting a recorded raw value or by
    the one registered deterministic transform.  Human evidence remains
    human evidence; this record does not mechanically verify semantic truth.
    """

    ordered_raws = sorted(
        support_raws,
        key=lambda item: item["a0_raw_label_id"].encode("utf-8"),
    )
    mode = label.get("adjudication_mode", "consensus")
    adjudicator = label["annotator_alias"]
    resolved_at = label["frozen_at"]
    selected = dict(selected_raw_label_ids or {})
    transform_fields = set(deterministic_transform_fields or set())
    final_projection = a0_label_semantic_projection(label)
    raw_projections = {
        raw["a0_raw_label_id"]: a0_raw_semantic_projection(
            raw["semantic_payload"]
        )
        for raw in ordered_raws
    }
    field_resolutions: List[Dict[str, Any]] = []
    for field in A0_RAW_FIELDS:
        value_rows = [
            {
                "a0_raw_label_id": raw_id,
                "value_sha256": canonical_sha256(projection[field]),
            }
            for raw_id, projection in raw_projections.items()
        ]
        raw_values = [
            projection[field] for projection in raw_projections.values()
        ]
        unique_hashes = {
            canonical_sha256(value) for value in raw_values
        }
        resolution_type = "exact_consensus"
        selected_raw_id: Optional[str] = None
        frozen_transform: Optional[Dict[str, Any]] = None
        if mode == "independent_paths":
            resolution_type = "independent_path_value"
        elif len(unique_hashes) > 1:
            if field in transform_fields:
                resolution_type = "frozen_deterministic_transform"
                frozen_transform = {
                    "transform_id": A0_FROZEN_TRANSFORM_ID,
                    "executable_sha256": validator_file_sha256(),
                    "input_values_sha256": canonical_sha256(
                        [
                            {
                                "a0_raw_label_id": row[
                                    "a0_raw_label_id"
                                ],
                                "value": raw_projections[
                                    row["a0_raw_label_id"]
                                ][field],
                            }
                            for row in value_rows
                        ]
                    ),
                    "output_value_sha256": canonical_sha256(
                        final_projection[field]
                    ),
                }
            else:
                resolution_type = "select_raw_value"
                selected_raw_id = selected.get(field)
                if selected_raw_id is None:
                    matching = [
                        raw_id
                        for raw_id, projection in raw_projections.items()
                        if projection[field] == final_projection[field]
                    ]
                    selected_raw_id = matching[0] if matching else ordered_raws[
                        0
                    ]["a0_raw_label_id"]
        record: Dict[str, Any] = {
            "field": field,
            "raw_value_hashes": value_rows,
            "resolution_type": resolution_type,
            "resolved_value": final_projection[field],
            "resolved_value_sha256": canonical_sha256(
                final_projection[field]
            ),
            "adjudicator_alias": adjudicator,
            "resolution_rule": (
                "exact_raw_value_equality"
                if resolution_type == "exact_consensus"
                else (
                    "preserve_independent_path_without_agreement_claim"
                    if resolution_type == "independent_path_value"
                    else (
                        A0_FROZEN_TRANSFORM_ID
                        if resolution_type
                        == "frozen_deterministic_transform"
                        else "blinded_adjudicator_selects_recorded_raw_value"
                    )
                )
            ),
            "resolved_at": resolved_at,
        }
        if selected_raw_id is not None:
            record["selected_raw_label_id"] = selected_raw_id
        if frozen_transform is not None:
            record["frozen_transform"] = frozen_transform
        field_resolutions.append(record)
    return {
        "rule_id": A0_RAW_SUPPORT_ADJUDICATION_RULE,
        "adjudicated_semantic_projection_sha256": canonical_sha256(
            final_projection
        ),
        "field_resolutions": field_resolutions,
        "resolved_at": resolved_at,
    }


def raw_case_agreement_status(
    raw_records: Sequence[Mapping[str, Any]],
) -> str:
    """Derive agreement only from pre-adjudication raw semantic payloads."""

    if len(raw_records) < 2:
        return "single_support_no_agreement"
    projections = [
        a0_raw_semantic_projection(raw["semantic_payload"])
        for raw in raw_records
    ]
    if all(item == projections[0] for item in projections[1:]):
        return "raw_exact_agreement"
    return "raw_substantive_disagreement"


def _raw_support_adjudication_error(
    label: Mapping[str, Any],
    container_event: Mapping[str, Any],
    support_raws: Sequence[Mapping[str, Any]],
    raw_to_annotator: Mapping[str, str],
    artifact_name: str,
) -> Optional[Dict[str, Any]]:
    """Validate v2 resolution without laundering human judgment as truth."""

    stage = STAGE_ORDER[3]
    mode = container_event["adjudication_mode"]
    record = container_event["raw_support_adjudication"]
    final_projection = a0_label_semantic_projection(label)
    ordered_raws = sorted(
        support_raws,
        key=lambda item: item["a0_raw_label_id"].encode("utf-8"),
    )
    raw_projections = {
        raw["a0_raw_label_id"]: a0_raw_semantic_projection(
            raw["semantic_payload"]
        )
        for raw in ordered_raws
    }
    expected_fields = list(A0_RAW_FIELDS)
    resolutions = record["field_resolutions"]
    if (
        record["rule_id"] != A0_RAW_SUPPORT_ADJUDICATION_RULE
        or [item["field"] for item in resolutions] != expected_fields
        or record["adjudicated_semantic_projection_sha256"]
        != canonical_sha256(final_projection)
        or record["resolved_at"] != label["frozen_at"]
    ):
        return _block_error(
            stage,
            "SEM_A0_RAW_SUPPORT_SEMANTICS",
            "v2 adjudication must freeze the exact six-field final projection and resolution time",
            artifact_name,
            "$.raw_support_adjudication",
        )
    unique_annotators = {
        raw_to_annotator[raw["a0_raw_label_id"]]
        for raw in ordered_raws
    }
    agreement = raw_case_agreement_status(ordered_raws)
    if mode == "consensus" and (
        len(unique_annotators) < 2
        or agreement != "raw_exact_agreement"
    ):
        return _block_error(
            stage,
            "SEM_A0_ADJUDICATION_MODE",
            "consensus requires exact pre-adjudication agreement from at least two independent annotators",
            artifact_name,
            "$.adjudication_mode",
        )
    if mode == "blinded_human_resolution" and (
        len(unique_annotators) < 2
        or agreement != "raw_substantive_disagreement"
    ):
        return _block_error(
            stage,
            "SEM_A0_ADJUDICATION_MODE",
            "blinded human resolution requires a recorded substantive raw disagreement",
            artifact_name,
            "$.adjudication_mode",
        )
    selected_baseline: Optional[str] = None
    for field, resolution in zip(expected_fields, resolutions):
        value_rows = [
            {
                "a0_raw_label_id": raw_id,
                "value_sha256": canonical_sha256(projection[field]),
            }
            for raw_id, projection in raw_projections.items()
        ]
        raw_values = [
            projection[field] for projection in raw_projections.values()
        ]
        unique_hashes = {
            canonical_sha256(value) for value in raw_values
        }
        if (
            resolution["raw_value_hashes"] != value_rows
            or resolution["resolved_value"] != final_projection[field]
            or resolution["resolved_value_sha256"]
            != canonical_sha256(final_projection[field])
            or resolution["adjudicator_alias"]
            != label["annotator_alias"]
            or resolution["resolved_at"] != label["frozen_at"]
        ):
            return _block_error(
                stage,
                "SEM_A0_RAW_SUPPORT_SEMANTICS",
                "field resolution must retain every exact raw value hash and the exact final value",
                artifact_name,
                "$.raw_support_adjudication.field_resolutions.%s"
                % field,
            )
        kind = resolution["resolution_type"]
        extra_selection = resolution.get("selected_raw_label_id")
        extra_transform = resolution.get("frozen_transform")
        if mode == "independent_paths":
            if (
                kind != "independent_path_value"
                or len(ordered_raws) < 1
                or any(value != final_projection[field] for value in raw_values)
                or extra_selection is not None
                or extra_transform is not None
            ):
                return _block_error(
                    stage,
                    "SEM_A0_RAW_SUPPORT_SEMANTICS",
                    "an independent path preserves its own raw value and cannot claim consensus",
                    artifact_name,
                    "$.raw_support_adjudication.field_resolutions.%s"
                    % field,
                )
            continue
        if len(unique_hashes) == 1:
            if (
                kind != "exact_consensus"
                or final_projection[field] != raw_values[0]
                or extra_selection is not None
                or extra_transform is not None
            ):
                return _block_error(
                    stage,
                    "SEM_A0_RAW_SUPPORT_SEMANTICS",
                    "an agreed field must remain the exact raw value",
                    artifact_name,
                    "$.raw_support_adjudication.field_resolutions.%s"
                    % field,
                )
            continue
        if mode != "blinded_human_resolution":
            return _block_error(
                stage,
                "SEM_A0_ADJUDICATION_MODE",
                "raw disagreement cannot be hidden under consensus",
                artifact_name,
                "$.adjudication_mode",
            )
        if kind == "select_raw_value":
            if (
                extra_selection not in raw_projections
                or raw_projections[extra_selection][field]
                != final_projection[field]
                or extra_transform is not None
            ):
                return _block_error(
                    stage,
                    "SEM_A0_RESOLUTION_OUT_OF_SUPPORT",
                    "human resolution must select a physically recorded raw value",
                    artifact_name,
                    "$.raw_support_adjudication.field_resolutions.%s"
                    % field,
                )
            if selected_baseline is None:
                selected_baseline = extra_selection
            elif selected_baseline != extra_selection:
                return _block_error(
                    stage,
                    "SEM_A0_RESOLUTION_FRANKENSTEIN",
                    "one final claim cannot splice substantive fields from different raw labels",
                    artifact_name,
                    "$.raw_support_adjudication.field_resolutions.%s"
                    % field,
                )
        elif kind == "frozen_deterministic_transform":
            transformed = utf8_sorted(
                {
                    item
                    for value in raw_values
                    for item in (
                        value if isinstance(value, list) else []
                    )
                }
            )
            expected_transform = {
                "transform_id": A0_FROZEN_TRANSFORM_ID,
                "executable_sha256": validator_file_sha256(),
                "input_values_sha256": canonical_sha256(
                    [
                        {
                            "a0_raw_label_id": raw_id,
                            "value": raw_projections[raw_id][field],
                        }
                        for raw_id in raw_projections
                    ]
                ),
                "output_value_sha256": canonical_sha256(
                    final_projection[field]
                ),
            }
            if (
                field != "update_source_labels"
                or final_projection[field] != transformed
                or extra_transform != expected_transform
                or extra_selection is not None
            ):
                return _block_error(
                    stage,
                    "SEM_A0_RESOLUTION_TRANSFORM",
                    "only the frozen source-label set union may synthesize a non-raw value",
                    artifact_name,
                    "$.raw_support_adjudication.field_resolutions.%s"
                    % field,
                )
        else:
            return _block_error(
                stage,
                "SEM_A0_RESOLUTION_MISSING",
                "every substantive disagreement needs a typed selection or frozen transform",
                artifact_name,
                "$.raw_support_adjudication.field_resolutions.%s"
                % field,
            )
    if selected_baseline is not None:
        for field in A0_RAW_FIELDS:
            if field == "update_source_labels" and next(
                item
                for item in resolutions
                if item["field"] == field
            )["resolution_type"] == "frozen_deterministic_transform":
                continue
            if (
                final_projection[field]
                != raw_projections[selected_baseline][field]
            ):
                return _block_error(
                    stage,
                    "SEM_A0_RESOLUTION_FRANKENSTEIN",
                    "the resolved projection must be one complete raw claim apart from registered transforms",
                    artifact_name,
                    "$.raw_support_adjudication",
                )
    return None


def chained_entry_sha256(entry: Mapping[str, Any]) -> str:
    preimage = dict(entry)
    preimage.pop("entry_sha256", None)
    return canonical_sha256(preimage)


def audit_entry_sha256(event: Mapping[str, Any]) -> str:
    return chained_entry_sha256(event)


def block_exposure_entry_sha256(event: Mapping[str, Any]) -> str:
    preimage = dict(event)
    preimage.pop("entry_sha256", None)
    return canonical_sha256([BLOCK_EXPOSURE_ENTRY_SERIALIZATION, preimage])


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




def validate_task_bundle(task_dir: Path, schema_dir: Path) -> Dict[str, Any]:
    """Legacy task entry point: permanently fail closed."""

    return verdict(
        False,
        [
            make_error(
                STAGE_ORDER[3],
                "FULL_BLOCK_REQUIRED",
                "legacy task validation can never PASS; use validate_full_block with an externally frozen frame commitment",
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
        "FULL_BLOCK_REQUIRED",
        "a single unit can never PASS; production validation requires the externally committed full block",
    )
    return verdict(False, [error], completed, artifacts)


def _block_error(
    stage: str,
    code: str,
    message: str,
    artifact: Optional[str] = None,
    path: Optional[str] = None,
) -> Dict[str, Any]:
    return make_error(stage, code, message, artifact, path)


def _load_block_json_reference(
    block_dir: Path,
    relative_path: str,
    kind: str,
    referenced: Dict[str, Dict[str, Any]],
    errors: List[Dict[str, Any]],
    ndjson: bool = False,
) -> None:
    stage = STAGE_ORDER[0]
    if relative_path in referenced.setdefault(kind, {}):
        return
    path = ensure_within_bundle(block_dir, relative_path)
    if path is None or not path.is_file():
        errors.append(
            _block_error(
                stage,
                "REFERENCED_ARTIFACT_MISSING",
                "referenced artifact must be a physical file inside the block bundle",
                relative_path,
            )
        )
        return
    try:
        value = (
            load_ndjson_no_duplicates(path)
            if ndjson
            else load_json_no_duplicates(path)
        )
    except DuplicateKeyError as exc:
        errors.append(
            _block_error(
                stage,
                "DUPLICATE_JSON_KEY",
                str(exc),
                relative_path,
                "$.%s" % exc.key,
            )
        )
        return
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(
            _block_error(stage, "INVALID_JSON", str(exc), relative_path)
        )
        return
    referenced[kind][relative_path] = value


def _string_field(value: Any, key: str) -> Optional[str]:
    if isinstance(value, Mapping):
        item = value.get(key)
        if isinstance(item, str):
            return item
    return None


def load_full_block(
    block_dir: Path,
    schema_dir: Path,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Load every fixed and manifest-referenced artifact before validation."""

    stage = STAGE_ORDER[0]
    errors: List[Dict[str, Any]] = []
    schemas: Dict[str, Any] = {}
    fixed: Dict[str, Any] = {}
    referenced: Dict[str, Dict[str, Any]] = {}

    for name, filename in SCHEMA_FILES.items():
        path = schema_dir / filename
        if not path.is_file():
            errors.append(
                _block_error(
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
                _block_error(
                    stage,
                    "DUPLICATE_JSON_KEY",
                    str(exc),
                    filename,
                    "$.%s" % exc.key,
                )
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(_block_error(stage, "INVALID_JSON", str(exc), filename))

    for name, filename in BLOCK_FIXED_FILES.items():
        path = block_dir / filename
        if not path.is_file():
            errors.append(
                _block_error(
                    stage,
                    "FULL_BLOCK_ARTIFACT_MISSING",
                    "required full-block artifact is missing",
                    filename,
                )
            )
            continue
        try:
            fixed[name] = load_json_no_duplicates(path)
        except DuplicateKeyError as exc:
            errors.append(
                _block_error(
                    stage,
                    "DUPLICATE_JSON_KEY",
                    str(exc),
                    filename,
                    "$.%s" % exc.key,
                )
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(_block_error(stage, "INVALID_JSON", str(exc), filename))

    exposure_path = block_dir / BLOCK_EXPOSURE_LOG_FILE
    if not exposure_path.is_file():
        errors.append(
            _block_error(
                stage,
                "FULL_BLOCK_ARTIFACT_MISSING",
                "complete block delivery/access ledger is required",
                BLOCK_EXPOSURE_LOG_FILE,
            )
        )
    else:
        try:
            fixed["block_exposure_events"] = load_ndjson_no_duplicates(
                exposure_path
            )
        except DuplicateKeyError as exc:
            errors.append(
                _block_error(
                    stage,
                    "DUPLICATE_JSON_KEY",
                    str(exc),
                    BLOCK_EXPOSURE_LOG_FILE,
                    "$.%s" % exc.key,
                )
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(
                _block_error(
                    stage,
                    "INVALID_JSON",
                    str(exc),
                    BLOCK_EXPOSURE_LOG_FILE,
                )
            )

    frame = fixed.get("block_frame")
    if isinstance(frame, Mapping):
        expected_units = frame.get("expected_units")
        if isinstance(expected_units, list):
            for unit in expected_units:
                rel = _string_field(unit, "coordinator_envelope_relative_path")
                if rel:
                    _load_block_json_reference(
                        block_dir,
                        rel,
                        "coordinator_envelope",
                        referenced,
                        errors,
                    )

    manifest = fixed.get("block_location_manifest")
    if isinstance(manifest, Mapping):
        unit_scans = manifest.get("unit_scans")
        if isinstance(unit_scans, list):
            for scan in unit_scans:
                prefix_rel = _string_field(
                    scan, "prefix_commit_log_relative_path"
                )
                stream_rel = _string_field(scan, "stream_ledger_relative_path")
                if prefix_rel:
                    _load_block_json_reference(
                        block_dir,
                        prefix_rel,
                        "prefix_commit",
                        referenced,
                        errors,
                        ndjson=True,
                    )
                if stream_rel:
                    _load_block_json_reference(
                        block_dir,
                        stream_rel,
                        "block_stream_ledger",
                        referenced,
                        errors,
                    )
                    stream = referenced.get(
                        "block_stream_ledger", {}
                    ).get(stream_rel)
                    raw_rel = _string_field(
                        stream, "raw_trajectory_relative_path"
                    )
                    if raw_rel:
                        _load_block_json_reference(
                            block_dir,
                            raw_rel,
                            "block_raw_trajectory",
                            referenced,
                            errors,
                        )
        locations = manifest.get("locations")
        if isinstance(locations, list):
            for location in locations:
                for field, kind in (
                    ("a0_input_relative_path", "a0_input"),
                    (
                        "a0_submissions_relative_path",
                        "block_a0_submissions",
                    ),
                    (
                        "a0_adjudication_container_relative_path",
                        "block_a0_adjudication",
                    ),
                ):
                    rel = _string_field(location, field)
                    if rel:
                        _load_block_json_reference(
                            block_dir, rel, kind, referenced, errors
                        )

    for container in list(
        referenced.get("block_a0_adjudication", {}).values()
    ):
        events = container.get("events") if isinstance(container, Mapping) else None
        if isinstance(events, list):
            for event in events:
                rel = _string_field(event, "a0_label_relative_path")
                if rel:
                    _load_block_json_reference(
                        block_dir, rel, "a0_label", referenced, errors
                    )
                resolution = (
                    event.get("source_resolution")
                    if isinstance(event, Mapping)
                    else None
                )
                search_refs = (
                    resolution.get("search_result_refs")
                    if isinstance(resolution, Mapping)
                    else None
                )
                if isinstance(search_refs, list):
                    for search_ref in search_refs:
                        search_rel = _string_field(
                            search_ref, "relative_path"
                        )
                        if search_rel:
                            _load_block_json_reference(
                                block_dir,
                                search_rel,
                                "source_search_result",
                                referenced,
                                errors,
                            )

    a1_barrier = fixed.get("block_a1_barrier")
    if isinstance(a1_barrier, Mapping):
        event_freezes = a1_barrier.get("event_freezes")
        if isinstance(event_freezes, list):
            for event in event_freezes:
                for field, kind in (
                    ("a1_reveal_relative_path", "a1_reveal"),
                    ("a1_label_relative_path", "a1_label"),
                    (
                        "omission_interval_relative_path",
                        "omission_interval",
                    ),
                ):
                    rel = _string_field(event, field)
                    if rel:
                        _load_block_json_reference(
                            block_dir, rel, kind, referenced, errors
                        )

    if errors:
        return None, errors
    return {
        "schemas": schemas,
        "fixed": fixed,
        "referenced": referenced,
        "block_dir": block_dir,
    }, []


def validate_full_block_instances(
    loaded: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    stage = STAGE_ORDER[2]
    schemas = loaded["schemas"]
    fixed = loaded["fixed"]
    referenced = loaded["referenced"]
    registry = make_registry(schemas)
    errors: List[Dict[str, Any]] = []

    def validate_one(
        value: Any,
        schema_name: str,
        artifact_name: str,
        prefix: str = "$",
    ) -> None:
        validator = Draft202012Validator(
            schemas[schema_name],
            registry=registry,
            format_checker=FormatChecker(),
        )
        for error in sorted(
            validator.iter_errors(value),
            key=lambda item: list(item.absolute_path),
        ):
            suffix = json_path(error.absolute_path)
            errors.append(
                _block_error(
                    stage,
                    "SCHEMA_INSTANCE_INVALID",
                    error.message,
                    artifact_name,
                    prefix + suffix[1:],
                )
            )

    for name, filename in BLOCK_FIXED_FILES.items():
        validate_one(fixed[name], name, filename)
    for index, event in enumerate(fixed["block_exposure_events"]):
        validate_one(
            event,
            "block_exposure_event",
            BLOCK_EXPOSURE_LOG_FILE,
            "$[%d]" % index,
        )
    for kind, by_path in referenced.items():
        schema_name = kind
        for relative_path, value in by_path.items():
            if kind == "prefix_commit":
                for index, entry in enumerate(value):
                    validate_one(
                        entry,
                        "prefix_commit",
                        relative_path,
                        "$[%d]" % index,
                    )
            else:
                validate_one(value, schema_name, relative_path)
    return errors


def _referenced_value(
    loaded: Mapping[str, Any],
    kind: str,
    relative_path: str,
) -> Any:
    return loaded["referenced"][kind][relative_path]


def _artifact_ref_error(
    actual_ref: Mapping[str, Any],
    artifact: Mapping[str, Any],
    artifact_name: str,
    path: str,
) -> Optional[Dict[str, Any]]:
    if actual_ref != artifact_ref(artifact):
        return _block_error(
            STAGE_ORDER[4],
            "HASH_BLOCK_ARTIFACT_REF_MISMATCH",
            "reference does not bind the physical artifact id and canonical bytes",
            artifact_name,
            path,
        )
    return None


def _raw_file_hash_error(
    block_dir: Path,
    relative_path: str,
    expected_sha256: str,
    artifact_name: str,
    path: str,
) -> Optional[Dict[str, Any]]:
    resolved = ensure_within_bundle(block_dir, relative_path)
    if resolved is None or not resolved.is_file():
        return _block_error(
            STAGE_ORDER[4],
            "HASH_BLOCK_RAW_PATH_INVALID",
            "raw bytes must be a physical file inside the block bundle",
            artifact_name,
            path,
        )
    actual = hashlib.sha256(resolved.read_bytes()).hexdigest()
    if actual != expected_sha256:
        return _block_error(
            STAGE_ORDER[4],
            "HASH_BLOCK_RAW_BYTES_MISMATCH",
            "raw bytes do not match their frozen SHA-256",
            artifact_name,
            path,
        )
    return None


def _parse_registered_raw_source(
    source_path: Path,
    parser: Mapping[str, Any],
    block_scope: str,
    artifact_name: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Execute the only currently registered source parser.

    The registered grammar is deliberately synthetic-only.  A real ontology
    Block-A packet therefore fails closed until an adapter that parses the
    immutable published source bytes is added to this executable and schema.
    """

    stage = STAGE_ORDER[4]
    if parser["parser_id"] != RAW_TRAJECTORY_PARSER_ID:
        return None, _block_error(
            stage,
            "HASH_RAW_SOURCE_PARSER_UNREGISTERED",
            "raw source parser id is not registered in this validator",
            artifact_name,
            "$.raw_parser.parser_id",
        )
    if block_scope != "synthetic_test_only":
        return None, _block_error(
            stage,
            "HASH_PRODUCTION_SOURCE_PARSER_UNAVAILABLE",
            "the only registered raw-source parser is synthetic-only; production fails closed",
            artifact_name,
            "$.raw_parser.parser_id",
        )
    try:
        source = json.loads(
            source_path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        return None, _block_error(
            stage,
            "HASH_RAW_SOURCE_PARSE_FAILED",
            "registered raw-source parser rejected source bytes: %s" % exc,
            artifact_name,
            "$.raw_parser",
        )
    required = {
        "source_format",
        "synthetic_test_only",
        "research_evidence",
        "unit_alias",
        "trajectory_id",
        "trajectory_mode",
        "entries",
        "published_at",
    }
    if (
        not isinstance(source, Mapping)
        or set(source) != required
        or source.get("source_format")
        != SYNTHETIC_PUBLISHED_TRAJECTORY_FORMAT
        or source.get("synthetic_test_only") is not True
        or source.get("research_evidence") is not False
        or not isinstance(source.get("unit_alias"), str)
        or not isinstance(source.get("trajectory_id"), str)
        or source.get("trajectory_mode")
        not in {"standard_steps", "batch_tool_model_steps"}
        or not isinstance(source.get("entries"), list)
        or not source["entries"]
        or not isinstance(source.get("published_at"), str)
    ):
        return None, _block_error(
            stage,
            "HASH_RAW_SOURCE_PARSE_FAILED",
            "source bytes do not match the exact registered synthetic grammar",
            artifact_name,
            "$.raw_parser",
        )
    try:
        parse_timestamp(source["published_at"])
        canonical_bytes(source)
    except (TypeError, ValueError) as exc:
        return None, _block_error(
            stage,
            "HASH_RAW_SOURCE_PARSE_FAILED",
            "source bytes violate the registered canonical grammar: %s" % exc,
            artifact_name,
            "$.raw_parser",
        )
    return {
        "raw_format": RAW_TRAJECTORY_FORMAT,
        "unit_alias": source["unit_alias"],
        "trajectory_id": source["trajectory_id"],
        "trajectory_mode": source["trajectory_mode"],
        "entries": source["entries"],
    }, None


def first_full_block_hash_error(
    loaded: Mapping[str, Any],
    expected_frame_sha256: str,
) -> Optional[Dict[str, Any]]:
    stage = STAGE_ORDER[4]
    fixed = loaded["fixed"]
    block_dir = loaded["block_dir"]
    frame = fixed["block_frame"]
    manifest = fixed["block_location_manifest"]
    a0_barrier = fixed["block_barrier"]
    a1_barrier = fixed["block_a1_barrier"]
    stage_b_gate = fixed["stage_b_gate"]
    role_history = fixed["role_history"]

    actual_frame_hash = canonical_sha256(frame)
    if actual_frame_hash != expected_frame_sha256:
        return _block_error(
            stage,
            "HASH_EXTERNAL_FRAME_COMMITMENT_MISMATCH",
            "block frame bytes do not match the external frozen frame commitment",
            BLOCK_FRAME_FILE,
        )
    for actual_ref, artifact, filename, path in (
        (
            manifest["block_frame_ref"],
            frame,
            BLOCK_LOCATION_MANIFEST_FILE,
            "$.block_frame_ref",
        ),
        (
            a0_barrier["block_frame_ref"],
            frame,
            BLOCK_BARRIER_FILE,
            "$.block_frame_ref",
        ),
        (
            a0_barrier["location_manifest_ref"],
            manifest,
            BLOCK_BARRIER_FILE,
            "$.location_manifest_ref",
        ),
        (
            a1_barrier["block_a0_barrier_ref"],
            a0_barrier,
            BLOCK_A1_BARRIER_FILE,
            "$.block_a0_barrier_ref",
        ),
        (
            a1_barrier["location_manifest_ref"],
            manifest,
            BLOCK_A1_BARRIER_FILE,
            "$.location_manifest_ref",
        ),
        (
            stage_b_gate["block_a1_barrier_ref"],
            a1_barrier,
            STAGE_B_GATE_FILE,
            "$.block_a1_barrier_ref",
        ),
        (
            a0_barrier["role_history_ref"],
            role_history,
            BLOCK_BARRIER_FILE,
            "$.role_history_ref",
        ),
    ):
        error = _artifact_ref_error(actual_ref, artifact, filename, path)
        if error:
            return error

    frame_units = {
        item["unit_alias"]: item for item in frame["expected_units"]
    }
    coordinators: Dict[str, Mapping[str, Any]] = {}
    coordinator_source_paths: Dict[str, Path] = {}
    for unit_alias, entry in frame_units.items():
        relative_path = entry["coordinator_envelope_relative_path"]
        coordinator = _referenced_value(
            loaded, "coordinator_envelope", relative_path
        )
        coordinators[unit_alias] = coordinator
        error = _artifact_ref_error(
            entry["coordinator_envelope_ref"],
            coordinator,
            BLOCK_FRAME_FILE,
            "$.expected_units.%s.coordinator_envelope_ref" % unit_alias,
        )
        if error:
            return error
        coordinator_path = ensure_within_bundle(block_dir, relative_path)
        if coordinator_path is None:
            return _block_error(
                stage,
                "HASH_BLOCK_COORDINATOR_PATH_INVALID",
                "coordinator envelope must be a physical file inside the block",
                relative_path,
            )
        source_snapshot = coordinator["source_snapshot"]
        source_path = ensure_within_bundle(
            coordinator_path.parent,
            source_snapshot["raw_response_relative_path"],
        )
        if source_path is None or not source_path.is_file():
            return _block_error(
                stage,
                "HASH_BLOCK_SOURCE_PATH_INVALID",
                "coordinator raw response must be a physical file inside its unit directory",
                relative_path,
                "$.source_snapshot.raw_response_relative_path",
            )
        if (
            hashlib.sha256(source_path.read_bytes()).hexdigest()
            != source_snapshot["raw_response_sha256"]
        ):
            return _block_error(
                stage,
                "HASH_BLOCK_SOURCE_BYTES_MISMATCH",
                "coordinator raw-response bytes do not match their frozen SHA-256",
                relative_path,
                "$.source_snapshot.raw_response_sha256",
            )
        coordinator_source_paths[unit_alias] = source_path
        asset_ids: Set[str] = set()
        asset_paths: Set[str] = set()
        for asset_index, asset in enumerate(coordinator["asset_manifest"]):
            if (
                asset["asset_id"] in asset_ids
                or asset["relative_path"] in asset_paths
            ):
                return _block_error(
                    stage,
                    "HASH_BLOCK_ASSET_DUPLICATE",
                    "coordinator asset ids and paths must be unique",
                    relative_path,
                    "$.asset_manifest[%d]" % asset_index,
                )
            asset_ids.add(asset["asset_id"])
            asset_paths.add(asset["relative_path"])
            asset_path = ensure_within_bundle(
                coordinator_path.parent, asset["relative_path"]
            )
            if asset_path is None or not asset_path.is_file():
                return _block_error(
                    stage,
                    "HASH_BLOCK_ASSET_PATH_INVALID",
                    "coordinator asset must be a physical file inside its unit directory",
                    relative_path,
                    "$.asset_manifest[%d].relative_path" % asset_index,
                )
            if (
                hashlib.sha256(asset_path.read_bytes()).hexdigest()
                != asset["sha256"]
            ):
                return _block_error(
                    stage,
                    "HASH_BLOCK_ASSET_BYTES_MISMATCH",
                    "coordinator asset bytes do not match their frozen SHA-256",
                    relative_path,
                    "$.asset_manifest[%d].sha256" % asset_index,
                )

    schema_hash = schema_bundle_sha256(loaded["schemas"])
    scans = {
        item["unit_alias"]: item for item in manifest["unit_scans"]
    }
    prefix_by_unit: Dict[str, Sequence[Mapping[str, Any]]] = {}
    stream_by_unit: Dict[str, Mapping[str, Any]] = {}
    for unit_alias, scan in scans.items():
        prefix_entries = _referenced_value(
            loaded, "prefix_commit", scan["prefix_commit_log_relative_path"]
        )
        prefix_by_unit[unit_alias] = prefix_entries
        if canonical_sha256(prefix_entries) != scan["prefix_commit_log_sha256"]:
            return _block_error(
                stage,
                "HASH_PREFIX_LOG_MISMATCH",
                "prefix commit log canonical bytes do not match the manifest",
                BLOCK_LOCATION_MANIFEST_FILE,
                "$.unit_scans.%s.prefix_commit_log_sha256" % unit_alias,
            )
        stream = _referenced_value(
            loaded, "block_stream_ledger", scan["stream_ledger_relative_path"]
        )
        stream_by_unit[unit_alias] = stream
        error = _artifact_ref_error(
            scan["stream_ledger_ref"],
            stream,
            BLOCK_LOCATION_MANIFEST_FILE,
            "$.unit_scans.%s.stream_ledger_ref" % unit_alias,
        )
        if error:
            return error
        raw_trajectory = _referenced_value(
            loaded,
            "block_raw_trajectory",
            stream["raw_trajectory_relative_path"],
        )
        error = _artifact_ref_error(
            stream["raw_trajectory_ref"],
            raw_trajectory,
            scan["stream_ledger_relative_path"],
            "$.raw_trajectory_ref",
        )
        if error:
            return error
        parser = stream["raw_parser"]
        if (
            parser["parser_id"] != RAW_TRAJECTORY_PARSER_ID
            or parser["input_format"] != RAW_TRAJECTORY_FORMAT
            or parser["projection_name"] != RAW_TRAJECTORY_PROJECTION
            or parser["executable_sha256"] != validator_file_sha256()
        ):
            return _block_error(
                stage,
                "HASH_RAW_PARSER_IDENTITY_MISMATCH",
                "raw projection requires this exact frozen parser executable",
                scan["stream_ledger_relative_path"],
                "$.raw_parser",
            )
        raw_path = ensure_within_bundle(
            block_dir, stream["raw_trajectory_relative_path"]
        )
        if raw_path is None or not raw_path.is_file():
            return _block_error(
                stage,
                "HASH_RAW_TRAJECTORY_PATH_INVALID",
                "normalized raw trajectory must be a physical file inside the block",
                scan["stream_ledger_relative_path"],
                "$.raw_trajectory_relative_path",
            )
        if raw_path == coordinator_source_paths[unit_alias]:
            return _block_error(
                stage,
                "HASH_RAW_TRAJECTORY_NOT_DERIVED",
                "normalized trajectory must be a separate parser output, not an alias of source bytes",
                scan["stream_ledger_relative_path"],
                "$.raw_trajectory_relative_path",
            )
        parsed_projection, parse_error = _parse_registered_raw_source(
            coordinator_source_paths[unit_alias],
            parser,
            frame["block_scope"],
            scan["stream_ledger_relative_path"],
        )
        if parse_error:
            return parse_error
        assert parsed_projection is not None
        physical_projection = {
            "raw_format": raw_trajectory["raw_format"],
            "unit_alias": raw_trajectory["unit_alias"],
            "trajectory_id": raw_trajectory["trajectory_id"],
            "trajectory_mode": raw_trajectory["trajectory_mode"],
            "entries": raw_trajectory["entries"],
        }
        if physical_projection != parsed_projection:
            return _block_error(
                stage,
                "HASH_RAW_PARSER_PROJECTION_MISMATCH",
                "physical normalized trajectory is not the registered parser output over frozen source bytes",
                stream["raw_trajectory_relative_path"],
            )
        for index, stream_entry in enumerate(stream["entries"]):
            action = stream_entry["current_action"]
            if action["kind"] == "current_action":
                error = _raw_file_hash_error(
                    block_dir,
                    action["action_bytes_relative_path"],
                    action["action_bytes_sha256"],
                    scan["stream_ledger_relative_path"],
                    "$.entries[%d].current_action.action_bytes_sha256"
                    % index,
                )
                if error:
                    return error

    location_objects: Dict[
        Tuple[str, str],
        Tuple[
            Mapping[str, Any],
            Mapping[str, Any],
            Mapping[str, Any],
        ],
    ] = {}
    for location in manifest["locations"]:
        unit_alias = location["unit_alias"]
        boundary_id = location["boundary_location_id"]
        a0_input = _referenced_value(
            loaded, "a0_input", location["a0_input_relative_path"]
        )
        submissions = _referenced_value(
            loaded,
            "block_a0_submissions",
            location["a0_submissions_relative_path"],
        )
        adjudication = _referenced_value(
            loaded,
            "block_a0_adjudication",
            location["a0_adjudication_container_relative_path"],
        )
        location_objects[(unit_alias, boundary_id)] = (
            a0_input,
            submissions,
            adjudication,
        )
        for actual_ref, artifact, field in (
            (location["a0_input_ref"], a0_input, "a0_input_ref"),
            (
                location["a0_submissions_ref"],
                submissions,
                "a0_submissions_ref",
            ),
            (
                location["a0_adjudication_container_ref"],
                adjudication,
                "a0_adjudication_container_ref",
            ),
        ):
            error = _artifact_ref_error(
                actual_ref,
                artifact,
                BLOCK_LOCATION_MANIFEST_FILE,
                "$.locations.%s.%s.%s"
                % (unit_alias, boundary_id, field),
            )
            if error:
                return error
        if submissions["schema_bundle_sha256"] != schema_hash:
            return _block_error(
                stage,
                "HASH_A0_SUBMISSION_SCHEMA_BUNDLE",
                "A0 submission container does not bind the loaded schema bundle",
                location["a0_submissions_relative_path"],
                "$.schema_bundle_sha256",
            )
        raw_ids: Set[str] = set()
        for submission in submissions["submissions"]:
            for raw_label in submission["raw_labels"]:
                expected_id = block_a0_raw_label_id(
                    unit_alias,
                    boundary_id,
                    submissions["schema_bundle_sha256"],
                    submissions["codebook_sha256"],
                    submission["annotator_alias"],
                    raw_label["semantic_payload"],
                )
                if raw_label["a0_raw_label_id"] != expected_id:
                    return _block_error(
                        stage,
                        "HASH_A0_RAW_LABEL_ID",
                        "raw A0 id does not match its complete frozen preimage",
                        location["a0_submissions_relative_path"],
                        "$.submissions.%s.raw_labels"
                        % submission["annotator_alias"],
                    )
                if expected_id in raw_ids:
                    return _block_error(
                        stage,
                        "HASH_A0_RAW_LABEL_DUPLICATE",
                        "duplicate raw A0 identity is prohibited",
                        location["a0_submissions_relative_path"],
                    )
                raw_ids.add(expected_id)
        error = _artifact_ref_error(
            adjudication["a0_input_ref"],
            a0_input,
            location["a0_adjudication_container_relative_path"],
            "$.a0_input_ref",
        )
        if error:
            return error
        error = _artifact_ref_error(
            adjudication["a0_submissions_ref"],
            submissions,
            location["a0_adjudication_container_relative_path"],
            "$.a0_submissions_ref",
        )
        if error:
            return error
        for event in adjudication["events"]:
            label = _referenced_value(
                loaded, "a0_label", event["a0_label_relative_path"]
            )
            error = _artifact_ref_error(
                event["a0_label_ref"],
                label,
                location["a0_adjudication_container_relative_path"],
                "$.events.%s.a0_label_ref"
                % event["adjudicated_event_id"],
            )
            if error:
                return error
            resolution = event["source_resolution"]
            if resolution["status"] == "source_unidentifiable":
                for search_index, search_ref in enumerate(
                    resolution["search_result_refs"]
                ):
                    search_result = _referenced_value(
                        loaded,
                        "source_search_result",
                        search_ref["relative_path"],
                    )
                    error = _artifact_ref_error(
                        search_ref["artifact_ref"],
                        search_result,
                        location[
                            "a0_adjudication_container_relative_path"
                        ],
                        "$.events.%s.source_resolution.search_result_refs[%d]"
                        % (event["adjudicated_event_id"], search_index),
                    )
                    if error:
                        return error
            if adjudicated_event_id(
                label["adjudicated_event_preimage"]
            ) != label["adjudicated_event_id"]:
                return _block_error(
                    stage,
                    "HASH_A0_EVENT_PREIMAGE_MISMATCH",
                    "adjudicated event id does not match its frozen preimage",
                    event["a0_label_relative_path"],
                    "$.adjudicated_event_id",
                )

    a0_barrier_hash = canonical_sha256(a0_barrier)
    for freeze in a1_barrier["event_freezes"]:
        reveal = _referenced_value(
            loaded, "a1_reveal", freeze["a1_reveal_relative_path"]
        )
        label = _referenced_value(
            loaded, "a1_label", freeze["a1_label_relative_path"]
        )
        for actual_ref, artifact, field in (
            (freeze["a1_reveal_ref"], reveal, "a1_reveal_ref"),
            (freeze["a1_label_ref"], label, "a1_label_ref"),
        ):
            error = _artifact_ref_error(
                actual_ref,
                artifact,
                BLOCK_A1_BARRIER_FILE,
                "$.event_freezes.%s.%s"
                % (freeze["adjudicated_event_id"], field),
            )
            if error:
                return error
        if reveal["block_barrier_commitment_sha256"] != a0_barrier_hash:
            return _block_error(
                stage,
                "HASH_A1_A0_BARRIER_LINK",
                "every A1 reveal must bind the complete A0 block barrier",
                freeze["a1_reveal_relative_path"],
                "$.block_barrier_commitment_sha256",
            )
        if "omission_interval_relative_path" in freeze:
            omission = _referenced_value(
                loaded,
                "omission_interval",
                freeze["omission_interval_relative_path"],
            )
            error = _artifact_ref_error(
                freeze["omission_interval_ref"],
                omission,
                BLOCK_A1_BARRIER_FILE,
                "$.event_freezes.%s.omission_interval_ref"
                % freeze["adjudicated_event_id"],
            )
            if error:
                return error

    events = fixed["block_exposure_events"]
    previous = None
    for index, event in enumerate(events):
        if event["previous_entry_sha256"] != previous:
            return _block_error(
                stage,
                "HASH_BLOCK_EXPOSURE_CHAIN_LINK",
                "exposure ledger previous hash does not match",
                BLOCK_EXPOSURE_LOG_FILE,
                "$[%d].previous_entry_sha256" % index,
            )
        expected = block_exposure_entry_sha256(event)
        if event["entry_sha256"] != expected:
            return _block_error(
                stage,
                "HASH_BLOCK_EXPOSURE_ENTRY",
                "exposure ledger entry hash does not match canonical bytes",
                BLOCK_EXPOSURE_LOG_FILE,
                "$[%d].entry_sha256" % index,
            )
        previous = expected
    if previous != stage_b_gate["exposure_chain_tip_sha256"]:
        return _block_error(
            stage,
            "HASH_BLOCK_EXPOSURE_CHAIN_TIP",
            "Stage-B gate does not bind the complete exposure ledger tip",
            STAGE_B_GATE_FILE,
            "$.exposure_chain_tip_sha256",
        )
    return None


def _source_category_or_error(
    loaded: Mapping[str, Any],
    a0_input: Mapping[str, Any],
    a0_label: Mapping[str, Any],
    container_event: Mapping[str, Any],
    artifact_name: str,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    stage = STAGE_ORDER[3]
    evidence = a0_label["update_source_evidence"]
    labels = [item["label"] for item in evidence]
    label_set = set(labels)
    resolution = container_event["source_resolution"]
    if not labels:
        return None, _block_error(
            stage,
            "INVALID_SOURCE_MEASUREMENT",
            "source label set cannot be empty",
            artifact_name,
            "$.update_source_evidence",
        )
    if len(labels) != len(label_set):
        return None, _block_error(
            stage,
            "INVALID_SOURCE_MEASUREMENT",
            "source labels must be unique",
            artifact_name,
            "$.update_source_evidence",
        )
    unknown = "source_unidentifiable" in label_set
    if unknown:
        if label_set != {"source_unidentifiable"}:
            return None, _block_error(
                stage,
                "INVALID_SOURCE_MEASUREMENT",
                "source_unidentifiable is mutually exclusive with factual labels",
                artifact_name,
                "$.update_source_evidence",
            )
        if resolution["status"] != "source_unidentifiable":
            return None, _block_error(
                stage,
                "INVALID_SOURCE_MEASUREMENT",
                "SOURCE_UNKNOWN requires the exclusive frozen search branch",
                artifact_name,
                "$.source_resolution",
            )
        roster = resolution["searched_scope_roster"]
        if canonical_sha256(roster) != resolution["searched_scope_sha256"]:
            return None, _block_error(
                stage,
                "INVALID_SOURCE_MEASUREMENT",
                "searched-scope roster hash mismatch",
                artifact_name,
                "$.source_resolution.searched_scope_sha256",
            )
        search_results = [
            _referenced_value(
                loaded,
                "source_search_result",
                item["relative_path"],
            )
            for item in resolution["search_result_refs"]
        ]
        searched_items = [
            item["searched_scope_item"] for item in search_results
        ]
        expected_status = {
            "NO_CUTOFF_SOURCE_AFTER_FROZEN_SEARCH": "no_source_found",
            "CONFLICTING_CUTOFF_SOURCES_AFTER_FROZEN_SEARCH": "conflicting_sources",
            "SOURCE_BYTES_UNAVAILABLE_AFTER_FROZEN_SEARCH": "source_bytes_unavailable",
        }[resolution["reason_code"]]
        if (
            searched_items != roster
            or any(
                result["unit_alias"] != a0_input["unit_alias"]
                or result["boundary_location_id"]
                != a0_input["boundary_location_id"]
                or artifact_ref(a0_input)
                not in result["checked_artifact_refs"]
                or result["result_status"] != expected_status
                or parse_timestamp(result["frozen_at"])
                > parse_timestamp(a0_label["frozen_at"])
                for result in search_results
            )
        ):
            return None, _block_error(
                stage,
                "INVALID_SOURCE_MEASUREMENT",
                "unknown-source search refs must physically cover the exact frozen scope with event-local audit records",
                artifact_name,
                "$.source_resolution.search_result_refs",
            )
        return "SOURCE_UNKNOWN", None
    if resolution["status"] != "identified":
        return None, _block_error(
            stage,
            "INVALID_SOURCE_MEASUREMENT",
            "factual labels require the identified-source branch",
            artifact_name,
            "$.source_resolution",
        )
    observations = {
        item["observation_ordinal"]: item
        for item in a0_input["prefix_observations"]
    }
    cutoff = a0_input["cutoff_observation_ordinal"]
    for index, item in enumerate(evidence):
        pointer = item["evidence_pointer"]
        ordinal = pointer["observation_ordinal"]
        if (
            pointer["artifact_id"] != a0_input["artifact_id"]
            or pointer["source_kind"] != "observation"
            or ordinal > cutoff
            or ordinal not in observations
            or pointer["content_sha256"]
            != canonical_sha256(observations[ordinal])
        ):
            return None, _block_error(
                stage,
                "INVALID_SOURCE_MEASUREMENT",
                "every factual source label needs a direct cutoff-or-earlier observation pointer",
                artifact_name,
                "$.update_source_evidence[%d].evidence_pointer" % index,
            )
    if "world_truth_changed" in label_set:
        if label_set == {"world_truth_changed"}:
            return "PURE_WORLD", None
        return "MIXED_WORLD", None
    return "NON_WORLD", None


def _first_stream_semantic_error(
    loaded: Mapping[str, Any],
    unit_alias: str,
    scan: Mapping[str, Any],
    coordinator: Mapping[str, Any],
    generator_aliases: Set[str],
) -> Optional[Dict[str, Any]]:
    stage = STAGE_ORDER[3]
    prefix_entries = _referenced_value(
        loaded, "prefix_commit", scan["prefix_commit_log_relative_path"]
    )
    stream = _referenced_value(
        loaded, "block_stream_ledger", scan["stream_ledger_relative_path"]
    )
    raw_trajectory = _referenced_value(
        loaded,
        "block_raw_trajectory",
        stream["raw_trajectory_relative_path"],
    )
    if stream["unit_alias"] != unit_alias:
        return _block_error(
            stage,
            "SEM_STREAM_UNIT_LINK",
            "stream ledger unit alias does not match its scan",
            scan["stream_ledger_relative_path"],
            "$.unit_alias",
        )
    trajectory_mode = coordinator["identity"]["trajectory_mode"]
    if (
        stream["trajectory_mode"] != trajectory_mode
        or raw_trajectory["unit_alias"] != unit_alias
        or raw_trajectory["trajectory_id"]
        != coordinator["identity"]["trajectory_id"]
        or raw_trajectory["trajectory_mode"] != trajectory_mode
        or raw_trajectory["raw_format"] != RAW_TRAJECTORY_FORMAT
    ):
        return _block_error(
            stage,
            "SEM_STREAM_TRAJECTORY_MODE",
            "raw trajectory and stream identity must match the coordinator envelope",
            scan["stream_ledger_relative_path"],
            "$.trajectory_mode",
        )
    raw_entries = raw_trajectory["entries"]
    raw_ordinals = [
        item["observation"]["observation_ordinal"] for item in raw_entries
    ]
    asset_by_id = {
        item["asset_id"]: item for item in coordinator["asset_manifest"]
    }
    for raw_entry in raw_entries:
        observation = raw_entry["observation"]
        ordinal = observation["observation_ordinal"]
        assets = observation["assets"]
        if (
            observation["missingness"] == "none"
            and not assets
        ) or (
            observation["missingness"] != "none"
            and assets
        ):
            return _block_error(
                stage,
                "SEM_RAW_OBSERVATION_ASSET_LINK",
                "raw observation missingness and physical asset refs are inconsistent",
                stream["raw_trajectory_relative_path"],
                "$.entries[%d].observation.assets" % ordinal,
            )
        if any(
            ref["asset_id"] not in asset_by_id
            or asset_by_id[ref["asset_id"]]["observation_ordinal"]
            != ordinal
            or asset_by_id[ref["asset_id"]]["sha256"]
            != ref["sha256"]
            for ref in assets
        ):
            return _block_error(
                stage,
                "SEM_RAW_OBSERVATION_ASSET_LINK",
                "every parsed raw observation asset must bind the coordinator-frozen physical asset for that ordinal",
                stream["raw_trajectory_relative_path"],
                "$.entries[%d].observation.assets" % ordinal,
            )
    expected_ordinals = list(range(len(raw_entries)))
    if (
        raw_ordinals != expected_ordinals
        or scan["observation_count"] != len(raw_entries)
        or scan["ordinal_roster"] != expected_ordinals
    ):
        return _block_error(
            stage,
            "SEM_EXACT_ORDINAL_ROSTER",
            "manifest roster must be rederived from the complete zero-based parsed raw trajectory",
            BLOCK_LOCATION_MANIFEST_FILE,
            "$.unit_scans.%s.ordinal_roster" % unit_alias,
        )
    if len(prefix_entries) != len(expected_ordinals) or len(
        stream["entries"]
    ) != len(expected_ordinals):
        return _block_error(
            stage,
            "SEM_EXACT_ORDINAL_ROSTER",
            "prefix and stream ledgers must cover every frozen ordinal exactly once",
            BLOCK_LOCATION_MANIFEST_FILE,
            "$.unit_scans.%s" % unit_alias,
        )
    previous = None
    boundary_ids: List[str] = []
    for ordinal, (raw_entry, prefix, stream_entry) in enumerate(
        zip(raw_entries, prefix_entries, stream["entries"])
    ):
        raw_observation = raw_entry["observation"]
        if (
            prefix["sequence"] != ordinal
            or prefix["observation_ordinal"] != ordinal
            or stream_entry["observation_ordinal"] != ordinal
            or prefix["unit_alias"] != unit_alias
        ):
            return _block_error(
                stage,
                "SEM_EXACT_ORDINAL_ROSTER",
                "stream and prefix entries cannot be missing, duplicated, or renumbered",
                scan["prefix_commit_log_relative_path"],
                "$[%d]" % ordinal,
            )
        if prefix["previous_entry_sha256"] != previous:
            return _block_error(
                stage,
                "SEM_PREFIX_CHAIN_LINK",
                "prefix chain previous hash mismatch",
                scan["prefix_commit_log_relative_path"],
                "$[%d].previous_entry_sha256" % ordinal,
            )
        expected_entry_hash = chained_entry_sha256(prefix)
        if prefix["entry_sha256"] != expected_entry_hash:
            return _block_error(
                stage,
                "SEM_PREFIX_CHAIN_ENTRY",
                "prefix chain entry hash mismatch",
                scan["prefix_commit_log_relative_path"],
                "$[%d].entry_sha256" % ordinal,
            )
        previous = expected_entry_hash
        expected_location = boundary_location_id(
            prefix["boundary_namespace"],
            unit_alias,
            ordinal,
            prefix["a0_prefix_payload_sha256"],
        )
        if prefix["boundary_location_id"] != expected_location:
            return _block_error(
                stage,
                "SEM_LOCATION_ID_DERIVATION",
                "ordinal boundary id must derive from the outcome-blind prefix commitment",
                scan["prefix_commit_log_relative_path"],
                "$[%d].boundary_location_id" % ordinal,
            )
        boundary_ids.append(expected_location)
        if (
            stream_entry["observation_sha256"]
            != prefix["observation_sha256"]
            or stream_entry["prefix_commit_entry_sha256"]
            != prefix["entry_sha256"]
            or stream_entry["prefix_committed_at"] != prefix["committed_at"]
            or stream_entry["observation_sha256"]
            != canonical_sha256(raw_observation)
            or stream_entry["observed_at"]
            != raw_observation["observed_at"]
        ):
            return _block_error(
                stage,
                "SEM_STREAM_PREFIX_LINK",
                "stream entry must be the parser-derived raw observation and bind its prefix commit",
                scan["stream_ledger_relative_path"],
                "$.entries[%d]" % ordinal,
            )
        observed_at = parse_timestamp(stream_entry["observed_at"])
        committed_at = parse_timestamp(prefix["committed_at"])
        decision_times: List[datetime] = []
        decision_aliases: Set[str] = set()
        for decision in prefix["generator_decisions"]:
            alias = decision["generator_alias"]
            if alias not in generator_aliases or alias in decision_aliases:
                return _block_error(
                    stage,
                    "SEM_GENERATOR_ROLE_OR_INDEPENDENCE",
                    "each prefix needs distinct registered candidate generators",
                    scan["prefix_commit_log_relative_path"],
                    "$[%d].generator_decisions" % ordinal,
                )
            decision_aliases.add(alias)
            if (
                decision["visible_through_observation_ordinal"] != ordinal
                or decision["boundary_location_id"] != expected_location
            ):
                return _block_error(
                    stage,
                    "SEM_GENERATOR_FUTURE_OR_LOCATION_LINK",
                    "generator decision must see exactly o_k and bind that location",
                    scan["prefix_commit_log_relative_path"],
                    "$[%d].generator_decisions" % ordinal,
                )
            decision_times.append(parse_timestamp(decision["decided_at"]))
        if not all(
            observed_at <= decision_time <= committed_at
            for decision_time in decision_times
        ):
            return _block_error(
                stage,
                "SEM_OBSERVATION_COMMIT_ORDER",
                "required order is o_k <= generator decisions <= commit",
                scan["prefix_commit_log_relative_path"],
                "$[%d]" % ordinal,
            )
        action = stream_entry["current_action"]
        if action["kind"] == "terminal_no_action":
            if ordinal != expected_ordinals[-1]:
                return _block_error(
                    stage,
                    "SEM_STREAM_EARLY_TERMINAL",
                    "only the last frozen ordinal may have no current action",
                    scan["stream_ledger_relative_path"],
                    "$.entries[%d].current_action" % ordinal,
                )
            if action != raw_entry["current_action"]:
                return _block_error(
                    stage,
                    "SEM_RAW_STREAM_PROJECTION",
                    "terminal action marker must equal the registered raw-parser projection",
                    scan["stream_ledger_relative_path"],
                    "$.entries[%d].current_action" % ordinal,
                )
            continue
        if ordinal == expected_ordinals[-1]:
            return _block_error(
                stage,
                "SEM_STREAM_NEXT_OBSERVATION_MISSING",
                "a current action requires its next observation",
                scan["stream_ledger_relative_path"],
                "$.entries[%d].current_action" % ordinal,
            )
        next_entry = stream["entries"][ordinal + 1]
        action_reveal = parse_timestamp(action["revealed_at"])
        next_observed = parse_timestamp(action["next_observed_at"])
        if not (
            committed_at < action_reveal < next_observed
            and action["next_observation_ordinal"] == ordinal + 1
            and action["next_observation_sha256"]
            == next_entry["observation_sha256"]
            and action["next_observed_at"] == next_entry["observed_at"]
        ):
            return _block_error(
                stage,
                "SEM_COMMIT_BEFORE_CURRENT_ACTION",
                "required order is commit < current a_k reveal < o_(k+1)",
                scan["stream_ledger_relative_path"],
                "$.entries[%d].current_action" % ordinal,
            )
        subactions = action["subactions"]
        action_ordinals = [item["action_ordinal"] for item in subactions]
        if len(action_ordinals) != len(set(action_ordinals)):
            return _block_error(
                stage,
                "SEM_BATCH_SUBACTION_DUPLICATE",
                "subaction ordinals must be unique",
                scan["stream_ledger_relative_path"],
                "$.entries[%d].current_action.subactions" % ordinal,
            )
        if any(
            parse_timestamp(item["first_observable_at"]) < action_reveal
            or parse_timestamp(item["first_observable_at"]) <= committed_at
            for item in subactions
        ):
            return _block_error(
                stage,
                "SEM_BATCH_SUBACTION_BEFORE_COMMIT",
                "no subaction may become observable before the atomic bundle gate",
                scan["stream_ledger_relative_path"],
                "$.entries[%d].current_action.subactions" % ordinal,
            )
        if trajectory_mode == "batch_tool_model_steps":
            if action["action_unit"] != "batch_bundle":
                return _block_error(
                    stage,
                    "SEM_BATCH_NOT_ATOMIC",
                    "batch-tool actions must be committed and revealed as one bundle",
                    scan["stream_ledger_relative_path"],
                    "$.entries[%d].current_action.action_unit" % ordinal,
                )
        elif action["action_unit"] != "single_action" or len(subactions) != 1:
            return _block_error(
                stage,
                "SEM_STANDARD_ACTION_NOT_SINGLE",
                "standard-step current actions require one atomic action",
                scan["stream_ledger_relative_path"],
                "$.entries[%d].current_action" % ordinal,
            )
        if action != raw_entry["current_action"]:
            return _block_error(
                stage,
                "SEM_RAW_STREAM_PROJECTION",
                "current action bytes, time, subactions, and successor must equal the registered raw-parser projection",
                scan["stream_ledger_relative_path"],
                "$.entries[%d].current_action" % ordinal,
            )
    if previous != scan["prefix_chain_tip_sha256"]:
        return _block_error(
            stage,
            "SEM_PREFIX_CHAIN_TIP",
            "manifest prefix tip does not equal the complete chain tip",
            BLOCK_LOCATION_MANIFEST_FILE,
            "$.unit_scans.%s.prefix_chain_tip_sha256" % unit_alias,
        )
    if scan["ordinal_boundary_location_ids"] != boundary_ids:
        return _block_error(
            stage,
            "SEM_EXACT_LOCATION_ROSTER",
            "manifest location roster must equal every physical ordinal location in order",
            BLOCK_LOCATION_MANIFEST_FILE,
            "$.unit_scans.%s.ordinal_boundary_location_ids" % unit_alias,
        )
    return None


def _production_authority_gap_error(
    frame: Mapping[str, Any],
) -> Optional[Dict[str, Any]]:
    """Fail closed until syntax is anchored to external execution authority."""

    if frame["block_scope"] != "ontology_block_a":
        return None
    return _block_error(
        STAGE_ORDER[3],
        "SEM_PRODUCTION_EXTERNAL_AUTHORITY_UNAVAILABLE",
        (
            "production requires a registered parser over immutable published "
            "source bytes, non-rollback append-only streaming commit receipts "
            "with a trusted clock, and platform-enforced ACL/access logs bound "
            "to external commitments, plus an externally committed complete "
            "append-only role-history checkpoint-to-tip proof and an external "
            "credential authority providing privacy-preserving stable principal "
            "commitments across aliases, roles, and blocks; self-sealed "
            "timestamps, exposure ledgers, alias inequality, and "
            "history_source_ref digests prove syntax only"
        ),
        BLOCK_FRAME_FILE,
        "$.block_scope",
    )


def _first_role_assignment_interval_error(
    loaded: Mapping[str, Any],
    role_by_alias: Mapping[str, str],
) -> Optional[Dict[str, Any]]:
    """Bind every in-bundle role use to an already-effective assignment."""

    stage = STAGE_ORDER[3]
    fixed = loaded["fixed"]
    frame = fixed["block_frame"]
    role_history = fixed["role_history"]
    assignments = {
        item["actor_alias"]: item
        for item in role_history["assignments"]
    }
    first_uses: Dict[str, datetime] = {}
    last_uses: Dict[str, datetime] = {}

    def record_use(alias: str, timestamp: str) -> None:
        occurred = parse_timestamp(timestamp)
        if alias not in first_uses or occurred < first_uses[alias]:
            first_uses[alias] = occurred
        if alias not in last_uses or occurred > last_uses[alias]:
            last_uses[alias] = occurred

    for coordinator in loaded["referenced"].get(
        "coordinator_envelope", {}
    ).values():
        record_use(
            coordinator["provenance"]["generator_alias"],
            coordinator["created_at"],
        )
    for prefix_entries in loaded["referenced"].get(
        "prefix_commit", {}
    ).values():
        for entry in prefix_entries:
            for decision in entry["generator_decisions"]:
                record_use(
                    decision["generator_alias"],
                    decision["decided_at"],
                )
    for submissions in loaded["referenced"].get(
        "block_a0_submissions", {}
    ).values():
        for submission in submissions["submissions"]:
            record_use(
                submission["annotator_alias"],
                submission["frozen_at"],
            )
    for adjudication in loaded["referenced"].get(
        "block_a0_adjudication", {}
    ).values():
        record_use(
            adjudication["adjudicator_alias"],
            adjudication["frozen_at"],
        )
    for label in loaded["referenced"].get("a0_label", {}).values():
        record_use(label["annotator_alias"], label["frozen_at"])
    for label in loaded["referenced"].get("a1_label", {}).values():
        record_use(label["annotator_alias"], label["frozen_at"])

    a0_barrier = fixed["block_barrier"]
    a1_barrier = fixed["block_a1_barrier"]
    stage_b_gate = fixed["stage_b_gate"]
    record_use(a0_barrier["sealed_by"], a0_barrier["sealed_at"])
    record_use(a1_barrier["sealed_by"], a1_barrier["sealed_at"])
    record_use(
        stage_b_gate["authorized_by"],
        stage_b_gate["authorized_at"],
    )
    for event in fixed["block_exposure_events"]:
        record_use(event["actor_alias"], event["occurred_at"])
        for recipient in event["recipient_aliases"]:
            record_use(recipient, event["occurred_at"])

    complete_through = parse_timestamp(
        role_history["complete_through"]
    )
    for alias, role in role_by_alias.items():
        assignment = assignments.get(alias)
        if assignment is None:
            return _block_error(
                stage,
                "SEM_ROLE_ASSIGNMENT_INTERVAL",
                "every registered role must have one permanent assignment",
                ROLE_HISTORY_FILE,
                "$.assignments",
            )
        effective_from = parse_timestamp(assignment["effective_from"])
        if (
            effective_from > complete_through
            or (
                alias in first_uses
                and (
                    effective_from > first_uses[alias]
                    or last_uses[alias] > complete_through
                )
            )
            or (
                frame["block_scope"] == "synthetic_test_only"
                and assignment["first_block_id"] != frame["block_id"]
            )
        ):
            return _block_error(
                stage,
                "SEM_ROLE_ASSIGNMENT_INTERVAL",
                (
                    "artifact authors, sealers, access/delivery actors, and "
                    "recipients must use a role only after effective_from and "
                    "within complete_through; synthetic first_block_id must "
                    "equal the current test block"
                ),
                ROLE_HISTORY_FILE,
                "$.assignments.%s" % alias,
            )
    return None


def first_full_block_semantic_error(
    loaded: Mapping[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Dict[str, str]]:
    stage = STAGE_ORDER[3]
    fixed = loaded["fixed"]
    frame = fixed["block_frame"]
    manifest = fixed["block_location_manifest"]
    a0_barrier = fixed["block_barrier"]
    a1_barrier = fixed["block_a1_barrier"]
    stage_b_gate = fixed["stage_b_gate"]
    role_history = fixed["role_history"]
    source_categories: Dict[str, str] = {}

    block_ids = {
        item["block_id"]
        for item in (frame, manifest, a0_barrier, a1_barrier, stage_b_gate)
    }
    block_scopes = {
        item["block_scope"]
        for item in (frame, manifest, a0_barrier, a1_barrier, stage_b_gate)
    }
    if len(block_ids) != 1 or len(block_scopes) != 1:
        return (
            _block_error(
                stage,
                "SEM_BLOCK_IDENTITY_SPLIT",
                "all full-block artifacts must bind one block id and scope",
            ),
            source_categories,
        )

    frame_units = frame["expected_units"]
    if frame["block_scope"] == "ontology_block_a":
        task_to_configs: Dict[str, Set[str]] = {}
        for item in frame_units:
            task_to_configs.setdefault(item["task_id"], set()).add(
                item["hosted_config_id"]
            )
        if len(frame_units) != 48 or any(
            len(configs) != 6 for configs in task_to_configs.values()
        ):
            return (
                _block_error(
                    stage,
                    "SEM_PRODUCTION_FRAME_CARDINALITY",
                    "frozen ontology Block A is 48 units with exactly six hosted configs per task",
                    BLOCK_FRAME_FILE,
                    "$.expected_units",
                ),
                source_categories,
            )
        authority_error = _production_authority_gap_error(frame)
        if authority_error:
            return authority_error, source_categories
    if frame["expected_unit_count"] != len(frame_units):
        return (
            _block_error(
                stage,
                "SEM_EXTERNAL_FRAME_COUNT",
                "frame count must equal its externally frozen physical roster",
                BLOCK_FRAME_FILE,
                "$.expected_unit_count",
            ),
            source_categories,
        )
    frame_aliases = [item["unit_alias"] for item in frame_units]
    frame_pairs = [
        (item["task_id"], item["hosted_config_id"]) for item in frame_units
    ]
    if len(frame_aliases) != len(set(frame_aliases)) or len(frame_pairs) != len(
        set(frame_pairs)
    ):
        return (
            _block_error(
                stage,
                "SEM_EXTERNAL_FRAME_DUPLICATE",
                "frame unit aliases and task/config pairs must be unique",
                BLOCK_FRAME_FILE,
                "$.expected_units",
            ),
            source_categories,
        )
    frame_by_alias = {item["unit_alias"]: item for item in frame_units}
    scans = manifest["unit_scans"]
    scan_aliases = [item["unit_alias"] for item in scans]
    if (
        len(scan_aliases) != len(set(scan_aliases))
        or set(scan_aliases) != set(frame_aliases)
    ):
        return (
            _block_error(
                stage,
                "SEM_FULL_FRAME_COVERAGE",
                "unit scans must equal the external frame; caller counts cannot shrink it",
                BLOCK_LOCATION_MANIFEST_FILE,
                "$.unit_scans",
            ),
            source_categories,
        )

    registry = a0_barrier["role_registry"]
    role_fields = (
        ("a0_annotator_aliases", "a0_annotator"),
        ("a0_adjudicator_aliases", "a0_adjudicator"),
        ("a1_annotator_aliases", "a1_annotator"),
        ("stage_b_annotator_aliases", "stage_b_annotator"),
        ("coordinator_aliases", "coordinator"),
        ("candidate_generator_aliases", "candidate_generator"),
        ("reference_aliases", "reference"),
    )
    role_by_alias: Dict[str, str] = {}
    for field, role in role_fields:
        for alias in registry[field]:
            if alias in role_by_alias:
                return (
                    _block_error(
                        stage,
                        "SEM_ROLE_POOL_OVERLAP",
                        "all coordinator/generator/reference/A0/A1/Stage-B pools must be pairwise disjoint",
                        BLOCK_BARRIER_FILE,
                        "$.role_registry",
                    ),
                    source_categories,
                )
            role_by_alias[alias] = role
    history_assignments = role_history["assignments"]
    history_aliases = [item["actor_alias"] for item in history_assignments]
    if len(history_aliases) != len(set(history_aliases)):
        return (
            _block_error(
                stage,
                "SEM_ROLE_HISTORY_REASSIGNMENT",
                "append-only permanent history cannot assign one alias twice",
                ROLE_HISTORY_FILE,
                "$.assignments",
            ),
            source_categories,
        )
    history_roles = {
        item["actor_alias"]: item["role"] for item in history_assignments
    }
    if history_roles != role_by_alias:
        return (
            _block_error(
                stage,
                "SEM_ROLE_HISTORY_MISMATCH",
                "current role registry must exactly reconcile with permanent project history",
                ROLE_HISTORY_FILE,
                "$.assignments",
            ),
            source_categories,
        )
    if (
        a0_barrier["sealed_by"] not in registry["coordinator_aliases"]
        or stage_b_gate["authorized_by"]
        not in registry["coordinator_aliases"]
    ):
        return (
            _block_error(
                stage,
                "SEM_COORDINATOR_ROLE",
                "barrier sealing and Stage-B authorization require registered coordinators",
            ),
            source_categories,
        )

    frame_time = parse_timestamp(frame["frozen_at"])
    manifest_time = parse_timestamp(manifest["frozen_at"])
    a0_seal = parse_timestamp(a0_barrier["sealed_at"])
    a1_seal = parse_timestamp(a1_barrier["sealed_at"])
    stage_b_time = parse_timestamp(stage_b_gate["authorized_at"])
    ledger_closed = parse_timestamp(stage_b_gate["ledger_closed_at"])
    if not (
        frame_time < manifest_time < a0_seal < a1_seal < stage_b_time
        <= ledger_closed
    ):
        return (
            _block_error(
                stage,
                "SEM_FULL_BLOCK_BARRIER_ORDER",
                "required order is frame/manifest -> all A0 -> A0 barrier -> all A1 -> A1 barrier -> Stage B",
            ),
            source_categories,
        )
    if parse_timestamp(role_history["complete_through"]) < ledger_closed:
        return (
            _block_error(
                stage,
                "SEM_ROLE_HISTORY_INCOMPLETE",
                "permanent role history must be complete through block ledger close",
                ROLE_HISTORY_FILE,
                "$.complete_through",
            ),
            source_categories,
        )
    role_interval_error = _first_role_assignment_interval_error(
        loaded, role_by_alias
    )
    if role_interval_error:
        return role_interval_error, source_categories

    coordinators: Dict[str, Mapping[str, Any]] = {}
    scans_by_alias = {item["unit_alias"]: item for item in scans}
    for unit_alias, frame_entry in frame_by_alias.items():
        coordinator = _referenced_value(
            loaded,
            "coordinator_envelope",
            frame_entry["coordinator_envelope_relative_path"],
        )
        coordinators[unit_alias] = coordinator
        identity = coordinator["identity"]
        if (
            coordinator["unit_alias"] != unit_alias
            or identity["task_id"] != frame_entry["task_id"]
            or identity["hosted_config_id"]
            != frame_entry["hosted_config_id"]
        ):
            return (
                _block_error(
                    stage,
                    "SEM_FRAME_COORDINATOR_LINK",
                    "external frame unit does not match the physical coordinator envelope",
                    frame_entry["coordinator_envelope_relative_path"],
                ),
                source_categories,
            )
        if (
            coordinator["provenance"]["generator_alias"]
            not in registry["candidate_generator_aliases"]
        ):
            return (
                _block_error(
                    stage,
                    "SEM_GENERATOR_ROLE_OR_INDEPENDENCE",
                    "coordinator provenance generator must be in the permanent generator pool",
                    frame_entry["coordinator_envelope_relative_path"],
                    "$.provenance.generator_alias",
                ),
                source_categories,
            )
        error = _first_stream_semantic_error(
            loaded,
            unit_alias,
            scans_by_alias[unit_alias],
            coordinator,
            set(registry["candidate_generator_aliases"]),
        )
        if error:
            return error, source_categories

    locations = manifest["locations"]
    location_keys = [
        (item["unit_alias"], item["boundary_location_id"])
        for item in locations
    ]
    expected_location_keys: List[Tuple[str, str]] = []
    for scan in scans:
        expected_location_keys.extend(
            (scan["unit_alias"], boundary_id)
            for boundary_id in scan["ordinal_boundary_location_ids"]
        )
    if (
        len(location_keys) != len(set(location_keys))
        or set(location_keys) != set(expected_location_keys)
        or len(location_keys) != len(expected_location_keys)
    ):
        return (
            _block_error(
                stage,
                "SEM_EXACT_LOCATION_ROSTER",
                "manifest must include every and only one location for every physical ordinal",
                BLOCK_LOCATION_MANIFEST_FILE,
                "$.locations",
            ),
            source_categories,
        )
    if a0_barrier["expected_unit_scan_count"] != len(frame_units):
        return (
            _block_error(
                stage,
                "SEM_BARRIER_FRAME_COUNT",
                "A0 barrier count must derive from the external frame",
                BLOCK_BARRIER_FILE,
                "$.expected_unit_scan_count",
            ),
            source_categories,
        )
    if a0_barrier["expected_location_count"] != len(location_keys):
        return (
            _block_error(
                stage,
                "SEM_BARRIER_LOCATION_COUNT",
                "A0 barrier location count must equal the exact manifest set",
                BLOCK_BARRIER_FILE,
                "$.expected_location_count",
            ),
            source_categories,
        )

    freeze_keys = [
        (item["unit_alias"], item["boundary_location_id"])
        for item in a0_barrier["location_freezes"]
    ]
    if (
        len(freeze_keys) != len(set(freeze_keys))
        or set(freeze_keys) != set(location_keys)
    ):
        return (
            _block_error(
                stage,
                "SEM_A0_BARRIER_LOCATION_SET",
                "A0 barrier must freeze the exact location set",
                BLOCK_BARRIER_FILE,
                "$.location_freezes",
            ),
            source_categories,
        )
    freeze_by_key = {
        (item["unit_alias"], item["boundary_location_id"]): item
        for item in a0_barrier["location_freezes"]
    }
    all_event_records: Dict[
        str,
        Tuple[
            Tuple[str, str],
            Mapping[str, Any],
            Mapping[str, Any],
            Mapping[str, Any],
        ],
    ] = {}
    latest_a0 = manifest_time
    for location in locations:
        key = (location["unit_alias"], location["boundary_location_id"])
        unit_alias, boundary_id = key
        scan = scans_by_alias[unit_alias]
        coordinator = coordinators[unit_alias]
        prefix_entries = _referenced_value(
            loaded, "prefix_commit", scan["prefix_commit_log_relative_path"]
        )
        prefix_by_location = {
            item["boundary_location_id"]: item for item in prefix_entries
        }
        prefix = prefix_by_location[boundary_id]
        ordinal = prefix["observation_ordinal"]
        a0_input = _referenced_value(
            loaded, "a0_input", location["a0_input_relative_path"]
        )
        submissions = _referenced_value(
            loaded,
            "block_a0_submissions",
            location["a0_submissions_relative_path"],
        )
        adjudication = _referenced_value(
            loaded,
            "block_a0_adjudication",
            location["a0_adjudication_container_relative_path"],
        )
        if (
            a0_input["unit_alias"] != unit_alias
            or a0_input["coordinator_envelope_commitment_sha256"]
            != canonical_sha256(coordinator)
            or a0_input["boundary_location_id"] != boundary_id
            or a0_input["cutoff_observation_ordinal"] != ordinal
            or a0_input["prefix_chain_tip_sha256"] != prefix["entry_sha256"]
            or a0_input["a0_prefix_payload_sha256"]
            != prefix["a0_prefix_payload_sha256"]
            or a0_prefix_payload_sha256(a0_input, ordinal)
            != prefix["a0_prefix_payload_sha256"]
        ):
            return (
                _block_error(
                    stage,
                    "SEM_LOCATION_A0_PREFIX_LINK",
                    "location A0 input must bind exactly its outcome-blind ordinal prefix",
                    location["a0_input_relative_path"],
                ),
                source_categories,
            )
        if len(a0_input["prefix_observations"]) != ordinal + 1:
            return (
                _block_error(
                    stage,
                    "SEM_LOCATION_A0_PREFIX_LENGTH",
                    "A0 input cannot omit or include observations beyond its location",
                    location["a0_input_relative_path"],
                    "$.prefix_observations",
                ),
                source_categories,
            )
        if any(
            canonical_sha256(observation)
            != prefix_entries[index]["observation_sha256"]
            for index, observation in enumerate(
                a0_input["prefix_observations"]
            )
        ):
            return (
                _block_error(
                    stage,
                    "SEM_LOCATION_A0_OBSERVATION_LINK",
                    "A0 prefix observations do not match the committed ordinal stream",
                    location["a0_input_relative_path"],
                    "$.prefix_observations",
                ),
                source_categories,
            )
        if (
            submissions["unit_alias"] != unit_alias
            or submissions["boundary_location_id"] != boundary_id
            or submissions["a0_input_ref"] != artifact_ref(a0_input)
            or adjudication["unit_alias"] != unit_alias
            or adjudication["boundary_location_id"] != boundary_id
        ):
            return (
                _block_error(
                    stage,
                    "SEM_LOCATION_A0_CONTAINER_LINK",
                    "submissions and adjudication container must bind one physical location",
                    location["a0_adjudication_container_relative_path"],
                ),
                source_categories,
            )
        submission_aliases = [
            item["annotator_alias"] for item in submissions["submissions"]
        ]
        if (
            len(submission_aliases) != 2
            or len(set(submission_aliases)) != 2
            or not set(submission_aliases).issubset(
                set(registry["a0_annotator_aliases"])
            )
        ):
            return (
                _block_error(
                    stage,
                    "SEM_A0_SUBMISSION_INDEPENDENCE",
                    "every location needs exactly two distinct registered A0 submissions, including no-event locations",
                    location["a0_submissions_relative_path"],
                    "$.submissions",
                ),
                source_categories,
            )
        expected_codebook = coordinator["provenance"]["version_hashes"][
            "codebook_sha256"
        ]
        if submissions["codebook_sha256"] != expected_codebook:
            return (
                _block_error(
                    stage,
                    "SEM_A0_SUBMISSION_CODEBOOK",
                    "A0 submissions must use the coordinator-frozen codebook",
                    location["a0_submissions_relative_path"],
                    "$.codebook_sha256",
                ),
                source_categories,
            )
        raw_to_annotator: Dict[str, str] = {}
        raw_by_id: Dict[str, Mapping[str, Any]] = {}
        for submission in submissions["submissions"]:
            for raw in submission["raw_labels"]:
                raw_to_annotator[raw["a0_raw_label_id"]] = submission[
                    "annotator_alias"
                ]
                raw_by_id[raw["a0_raw_label_id"]] = raw
        disposition_ids = [
            item["a0_raw_label_id"]
            for item in adjudication["raw_label_dispositions"]
        ]
        if (
            len(disposition_ids) != len(set(disposition_ids))
            or set(disposition_ids) != set(raw_to_annotator)
        ):
            return (
                _block_error(
                    stage,
                    "SEM_A0_RAW_DISPOSITION_COVERAGE",
                    "the single adjudication container must dispose every raw id exactly once",
                    location["a0_adjudication_container_relative_path"],
                    "$.raw_label_dispositions",
                ),
                source_categories,
            )
        disposition_by_raw = {
            item["a0_raw_label_id"]: item
            for item in adjudication["raw_label_dispositions"]
        }
        case_ids = [
            item["case_id"] for item in adjudication["case_roster"]
        ]
        if len(case_ids) != len(set(case_ids)):
            return (
                _block_error(
                    stage,
                    "SEM_A0_CASE_DUPLICATE",
                    "case roster identities must be unique",
                    location["a0_adjudication_container_relative_path"],
                    "$.case_roster",
                ),
                source_categories,
            )
        cases_by_id = {
            item["case_id"]: item for item in adjudication["case_roster"]
        }
        raw_case_memberships = [
            raw_id
            for case in adjudication["case_roster"]
            for raw_id in case["raw_label_ids"]
        ]
        if (
            len(raw_case_memberships) != len(set(raw_case_memberships))
            or set(raw_case_memberships) != set(raw_to_annotator)
            or any(
                disposition_by_raw[raw_id]["case_id"]
                != block_a0_case_id(
                    unit_alias,
                    boundary_id,
                    case["raw_label_ids"],
                )
                or case["case_id"]
                != block_a0_case_id(
                    unit_alias,
                    boundary_id,
                    case["raw_label_ids"],
                )
                for case in adjudication["case_roster"]
                for raw_id in case["raw_label_ids"]
            )
        ):
            return (
                _block_error(
                    stage,
                    "SEM_A0_RAW_CASE_PARTITION",
                    "every raw label must occur in exactly one derived case denominator",
                    location["a0_adjudication_container_relative_path"],
                    "$.case_roster",
                ),
                source_categories,
            )
        if (
            adjudication["adjudicator_alias"]
            not in registry["a0_adjudicator_aliases"]
        ):
            return (
                _block_error(
                    stage,
                    "SEM_A0_ADJUDICATOR_ROLE",
                    "A0-only adjudication requires the permanent A0 adjudicator pool",
                    location["a0_adjudication_container_relative_path"],
                    "$.adjudicator_alias",
                ),
                source_categories,
            )
        event_ids = [
            item["adjudicated_event_id"] for item in adjudication["events"]
        ]
        if len(event_ids) != len(set(event_ids)):
            return (
                _block_error(
                    stage,
                    "SEM_A0_EVENT_DUPLICATE",
                    "same-location events require distinct adjudicated ids",
                    location["a0_adjudication_container_relative_path"],
                    "$.events",
                ),
                source_categories,
            )
        dispositions_by_event: Dict[str, Set[str]] = {
            event_id: set() for event_id in event_ids
        }
        dispositions_by_unresolved: Dict[str, Set[str]] = {}
        rejected_by_case: Dict[str, Set[str]] = {}
        for disposition in adjudication["raw_label_dispositions"]:
            if disposition["disposition"] == "adjudicated_event":
                event_id = disposition["adjudicated_event_id"]
                if event_id not in dispositions_by_event:
                    return (
                        _block_error(
                            stage,
                            "SEM_A0_DISPOSITION_DANGLING_EVENT",
                            "raw disposition references an event outside the one adjudication container",
                            location[
                                "a0_adjudication_container_relative_path"
                            ],
                        ),
                        source_categories,
                    )
                dispositions_by_event[event_id].add(
                    disposition["a0_raw_label_id"]
                )
                if (
                    disposition.get("decided_by") is not None
                    or disposition.get("decision_rule") is not None
                    or disposition.get("decided_at") is not None
                    or disposition.get("unresolved_record_id") is not None
                    or disposition.get("rejection_reason_code") is not None
                    or disposition.get("rejection_evidence") is not None
                ):
                    return (
                        _block_error(
                            stage,
                            "SEM_A0_RAW_DISPOSITION_TYPED",
                            "event disposition cannot carry rejection or unresolved fields",
                            location[
                                "a0_adjudication_container_relative_path"
                            ],
                            "$.raw_label_dispositions",
                        ),
                        source_categories,
                    )
            elif disposition["disposition"] == "unresolved":
                unresolved_id = disposition.get(
                    "unresolved_record_id"
                )
                if (
                    disposition["adjudication_mode"] != "unresolved"
                    or unresolved_id is None
                    or disposition.get("adjudicated_event_id") is not None
                    or disposition.get("rejection_reason_code") is not None
                    or any(
                        disposition.get(field) is None
                        for field in (
                            "decided_by",
                            "decision_rule",
                            "decided_at",
                        )
                    )
                ):
                    return (
                        _block_error(
                            stage,
                            "SEM_A0_RAW_DISPOSITION_TYPED",
                            "unresolved disposition requires its exact typed unresolved record and decision metadata",
                            location[
                                "a0_adjudication_container_relative_path"
                            ],
                            "$.raw_label_dispositions",
                        ),
                        source_categories,
                    )
                dispositions_by_unresolved.setdefault(
                    unresolved_id, set()
                ).add(disposition["a0_raw_label_id"])
            else:
                if (
                    disposition["adjudication_mode"] != "unresolved"
                    or disposition.get("rejection_reason_code") is None
                    or disposition.get("rejection_evidence") is None
                    or any(
                        disposition.get(field) is None
                        for field in (
                            "decided_by",
                            "decision_rule",
                            "decided_at",
                        )
                    )
                    or disposition.get("adjudicated_event_id") is not None
                    or disposition.get("unresolved_record_id") is not None
                ):
                    return (
                        _block_error(
                            stage,
                            "SEM_A0_REJECTION_EVIDENCE",
                            "typed-invalid rejection needs a closed reason, frozen evidence, adjudicator, rule, and time",
                            location[
                                "a0_adjudication_container_relative_path"
                            ],
                            "$.raw_label_dispositions",
                        ),
                        source_categories,
                    )
                rejected_by_case.setdefault(
                    disposition["case_id"], set()
                ).add(disposition["a0_raw_label_id"])
        groups_by_id = {
            item["path_group_id"]: item
            for item in adjudication["independent_path_groups"]
        }
        unresolved_by_id = {
            item["unresolved_record_id"]: item
            for item in adjudication["unresolved_records"]
        }
        if (
            len(groups_by_id)
            != len(adjudication["independent_path_groups"])
            or len(unresolved_by_id)
            != len(adjudication["unresolved_records"])
        ):
            return (
                _block_error(
                    stage,
                    "SEM_A0_ADJUDICATION_RECORD_DUPLICATE",
                    "path-group and unresolved record identities must be unique",
                    location["a0_adjudication_container_relative_path"],
                ),
                source_categories,
            )
        events_by_id = {
            item["adjudicated_event_id"]: item
            for item in adjudication["events"]
        }
        for case in adjudication["case_roster"]:
            case_id = case["case_id"]
            case_raws = set(case["raw_label_ids"])
            case_events = set(case["event_ids"])
            if (
                case["required_a1_event_ids"] != case["event_ids"]
                or not case_events.issubset(events_by_id)
                or any(
                    events_by_id[event_id]["case_id"] != case_id
                    for event_id in case_events
                )
                or any(
                    disposition_by_raw[raw_id][
                        "adjudication_mode"
                    ]
                    != case["adjudication_mode"]
                    for raw_id in case_raws
                )
            ):
                return (
                    _block_error(
                        stage,
                        "SEM_A0_CASE_ROSTER",
                        "case mode and required A1 path roster must exactly bind its events and raw dispositions",
                        location[
                            "a0_adjudication_container_relative_path"
                        ],
                        "$.case_roster.%s" % case_id,
                    ),
                    source_categories,
                )
            raw_records = [raw_by_id[item] for item in case["raw_label_ids"]]
            derived_agreement = raw_case_agreement_status(raw_records)
            if case["case_status"] == "resolved_event":
                if (
                    case["adjudication_mode"]
                    not in ("consensus", "blinded_human_resolution")
                    or len(case_events) != 1
                    or case_raws
                    != dispositions_by_event[next(iter(case_events))]
                    or case["typed_invalid_raw_label_ids"]
                    or case.get("independent_path_group_id") is not None
                    or case.get("unresolved_record_id") is not None
                    or (
                        case["adjudication_mode"] == "consensus"
                        and derived_agreement != "raw_exact_agreement"
                    )
                    or (
                        case["adjudication_mode"]
                        == "blinded_human_resolution"
                        and derived_agreement
                        != "raw_substantive_disagreement"
                    )
                    or case["agreement_status"] != derived_agreement
                ):
                    return (
                        _block_error(
                            stage,
                            "SEM_A0_CASE_ROSTER",
                            "resolved case must preserve one consensus or blinded-resolution event over its complete raw denominator",
                            location[
                                "a0_adjudication_container_relative_path"
                            ],
                            "$.case_roster.%s" % case_id,
                        ),
                        source_categories,
                    )
            elif case["case_status"] == "independent_unmerged_paths":
                group_id = case.get("independent_path_group_id")
                group = groups_by_id.get(group_id)
                event_support_union = set().union(
                    *(
                        dispositions_by_event[event_id]
                        for event_id in case_events
                    )
                ) if case_events else set()
                if (
                    case["adjudication_mode"] != "independent_paths"
                    or len(case_events) < 2
                    or group is None
                    or group["case_id"] != case_id
                    or set(group["raw_label_ids"]) != case_raws
                    or set(group["event_ids"]) != case_events
                    or event_support_union != case_raws
                    or sum(
                        len(dispositions_by_event[event_id])
                        for event_id in case_events
                    )
                    != len(case_raws)
                    or case["typed_invalid_raw_label_ids"]
                    or case.get("unresolved_record_id") is not None
                    or case["agreement_status"] != derived_agreement
                ):
                    return (
                        _block_error(
                            stage,
                            "SEM_A0_INDEPENDENT_PATH_ROSTER",
                            "independent paths need one explicit group whose disjoint paths preserve the complete raw denominator",
                            location[
                                "a0_adjudication_container_relative_path"
                            ],
                            "$.case_roster.%s" % case_id,
                        ),
                        source_categories,
                    )
            elif case["case_status"] == "unresolved":
                unresolved_id = case.get("unresolved_record_id")
                unresolved = unresolved_by_id.get(unresolved_id)
                if (
                    case["adjudication_mode"] != "unresolved"
                    or case_events
                    or case["required_a1_event_ids"]
                    or unresolved is None
                    or unresolved["case_id"] != case_id
                    or set(unresolved["raw_label_ids"]) != case_raws
                    or dispositions_by_unresolved.get(
                        unresolved_id, set()
                    )
                    != case_raws
                    or case["typed_invalid_raw_label_ids"]
                    or case.get("independent_path_group_id") is not None
                    or case["agreement_status"]
                    != "unresolved_disagreement"
                ):
                    return (
                        _block_error(
                            stage,
                            "SEM_A0_UNRESOLVED_ROSTER",
                            "unresolved case must remain an explicit denominator record with no primary or A1 path",
                            location[
                                "a0_adjudication_container_relative_path"
                            ],
                            "$.case_roster.%s" % case_id,
                        ),
                        source_categories,
                    )
            else:
                if (
                    case["adjudication_mode"] != "unresolved"
                    or case_events
                    or case["required_a1_event_ids"]
                    or set(case["typed_invalid_raw_label_ids"])
                    != case_raws
                    or rejected_by_case.get(case_id, set()) != case_raws
                    or case.get("independent_path_group_id") is not None
                    or case.get("unresolved_record_id") is not None
                    or case["agreement_status"]
                    != "typed_invalid_not_assessed"
                ):
                    return (
                        _block_error(
                            stage,
                            "SEM_A0_TYPED_INVALID_ROSTER",
                            "typed-invalid raw labels remain in the case and missingness denominator",
                            location[
                                "a0_adjudication_container_relative_path"
                            ],
                            "$.case_roster.%s" % case_id,
                        ),
                        source_categories,
                    )
        case_event_memberships = [
            event_id
            for case in adjudication["case_roster"]
            for event_id in case["event_ids"]
        ]
        if (
            len(case_event_memberships)
            != len(set(case_event_memberships))
            or set(case_event_memberships) != set(event_ids)
            or set(groups_by_id)
            != {
                case["independent_path_group_id"]
                for case in adjudication["case_roster"]
                if case["case_status"]
                == "independent_unmerged_paths"
            }
            or set(unresolved_by_id)
            != {
                case["unresolved_record_id"]
                for case in adjudication["case_roster"]
                if case["case_status"] == "unresolved"
            }
        ):
            return (
                _block_error(
                    stage,
                    "SEM_A0_CASE_EVENT_PARTITION",
                    "every event, independent group, and unresolved record belongs to exactly one case",
                    location["a0_adjudication_container_relative_path"],
                    "$.case_roster",
                ),
                source_categories,
            )
        for group in adjudication["independent_path_groups"]:
            group_events = [
                events_by_id[event_id] for event_id in group["event_ids"]
            ]
            expected_path_ids = [
                block_a0_independent_path_id(
                    group["case_id"],
                    event["supporting_a0_raw_label_ids"],
                )
                for event in group_events
            ]
            if (
                group["path_ids"] != expected_path_ids
                or any(
                    event["adjudication_mode"] != "independent_paths"
                    or event.get("independent_path_group_id")
                    != group["path_group_id"]
                    or event.get("independent_path_id")
                    != expected_path_id
                    for event, expected_path_id in zip(
                        group_events, expected_path_ids
                    )
                )
            ):
                return (
                    _block_error(
                        stage,
                        "SEM_A0_INDEPENDENT_PATH_ROSTER",
                        "path group must bind ordered derived path ids and cannot masquerade as unrelated single-support events",
                        location[
                            "a0_adjudication_container_relative_path"
                        ],
                        "$.independent_path_groups.%s"
                        % group["path_group_id"],
                    ),
                    source_categories,
                )
        for unresolved in adjudication["unresolved_records"]:
            unresolved_raws = [
                raw_by_id[raw_id]
                for raw_id in unresolved["raw_label_ids"]
            ]
            raw_projections = {
                raw["a0_raw_label_id"]: a0_raw_semantic_projection(
                    raw["semantic_payload"]
                )
                for raw in unresolved_raws
            }
            differing_fields = [
                field
                for field in A0_RAW_FIELDS
                if len(
                    {
                        canonical_sha256(projection[field])
                        for projection in raw_projections.values()
                    }
                )
                > 1
            ]
            if not differing_fields:
                differing_fields = list(A0_RAW_FIELDS)
            unresolved_fields = unresolved["unresolved_fields"]
            if (
                [item["field"] for item in unresolved_fields]
                != differing_fields
                or any(
                    item["raw_value_hashes"]
                    != [
                        {
                            "a0_raw_label_id": raw_id,
                            "value_sha256": canonical_sha256(
                                raw_projections[raw_id][item["field"]]
                            ),
                        }
                        for raw_id in raw_projections
                    ]
                    for item in unresolved_fields
                )
            ):
                return (
                    _block_error(
                        stage,
                        "SEM_A0_UNRESOLVED_ROSTER",
                        "unresolved record must enumerate every unresolved field and every raw value hash",
                        location[
                            "a0_adjudication_container_relative_path"
                        ],
                        "$.unresolved_records.%s"
                        % unresolved["unresolved_record_id"],
                    ),
                    source_categories,
                )
        label_times: List[datetime] = []
        for container_event in adjudication["events"]:
            event_id = container_event["adjudicated_event_id"]
            case_id = container_event["case_id"]
            mode = container_event["adjudication_mode"]
            supports = set(
                container_event["supporting_a0_raw_label_ids"]
            )
            if (
                supports != dispositions_by_event[event_id]
                or not supports
                or any(
                    disposition_by_raw[item]["case_id"] != case_id
                    or disposition_by_raw[item]["adjudication_mode"]
                    != mode
                    or (
                        mode == "independent_paths"
                        and (
                            disposition_by_raw[item].get(
                                "independent_path_group_id"
                            )
                            != container_event.get(
                                "independent_path_group_id"
                            )
                            or disposition_by_raw[item].get(
                                "independent_path_id"
                            )
                            != container_event.get("independent_path_id")
                        )
                    )
                    for item in supports
                )
                or (
                    mode in ("consensus", "blinded_human_resolution")
                    and len(
                        {
                            raw_to_annotator[item]
                            for item in supports
                        }
                    )
                    < 2
                )
                or (
                    mode != "independent_paths"
                    and (
                        container_event.get(
                            "independent_path_group_id"
                        )
                        is not None
                        or container_event.get("independent_path_id")
                        is not None
                    )
                )
            ):
                return (
                    _block_error(
                        stage,
                        "SEM_A0_EVENT_RAW_SUPPORT",
                        "event support must exactly match one case/path disposition; only consensus or human resolution claims cross-annotator support",
                        location["a0_adjudication_container_relative_path"],
                        "$.events.%s.supporting_a0_raw_label_ids" % event_id,
                    ),
                    source_categories,
                )
            label = _referenced_value(
                loaded,
                "a0_label",
                container_event["a0_label_relative_path"],
            )
            if (
                label["unit_alias"] != unit_alias
                or label["boundary_location_id"] != boundary_id
                or label["case_id"] != case_id
                or label["adjudicated_event_id"] != event_id
                or set(label["supporting_a0_raw_label_ids"]) != supports
                or label["adjudication_mode"] != mode
                or label["grounding_mode"]
                != container_event["grounding_mode"]
                or label["a0_input_ref"] != artifact_ref(a0_input)
                or label["annotator_alias"]
                != adjudication["adjudicator_alias"]
            ):
                return (
                    _block_error(
                        stage,
                        "SEM_A0_EVENT_LINK",
                        "A0 event label, location, raw support, and adjudicator cannot be spliced",
                        container_event["a0_label_relative_path"],
                    ),
                    source_categories,
                )
            if label["grounding_mode"] == "mechanical":
                return (
                    _block_error(
                        stage,
                        "SEM_MECHANICAL_GROUNDING_UNAVAILABLE",
                        "mechanical semantic grounding requires a registered frozen typed-claim verifier; none is available in this implementation",
                        container_event["a0_label_relative_path"],
                        "$.mechanical_grounding_contract",
                    ),
                    source_categories,
                )
            if (
                label["evidence_class"]
                != "HUMAN_ADJUDICATED_EVIDENCE"
                or label["semantic_verification"]
                != "NOT_MECHANICALLY_VERIFIED"
                or label["mechanical_grounding_contract"] is not None
                or any(
                    raw_by_id[item]["semantic_payload"][
                        "grounding_mode"
                    ]
                    != "blinded_human"
                    for item in supports
                )
            ):
                return (
                    _block_error(
                        stage,
                        "SEM_A0_GROUNDING_CLAIM",
                        "current A0 semantic claims are explicit blinded-human evidence and cannot be labeled mechanically verified",
                        container_event["a0_label_relative_path"],
                        "$.grounding_mode",
                    ),
                    source_categories,
                )
            category, error = _source_category_or_error(
                loaded,
                a0_input,
                label,
                container_event,
                container_event["a0_label_relative_path"],
            )
            if error:
                return error, source_categories
            assert category is not None
            source_categories[event_id] = category
            support_raws = [
                raw_by_id[raw_id]
                for raw_id in sorted(
                    supports, key=lambda value: value.encode("utf-8")
                )
            ]
            error = _raw_support_adjudication_error(
                label,
                container_event,
                support_raws,
                raw_to_annotator,
                container_event["a0_label_relative_path"],
            )
            if error:
                return error, source_categories
            label_times.append(parse_timestamp(label["frozen_at"]))
            if event_id in all_event_records:
                return (
                    _block_error(
                        stage,
                        "SEM_GLOBAL_EVENT_ID_DUPLICATE",
                        "adjudicated event ids must be unique across the block",
                        location["a0_adjudication_container_relative_path"],
                    ),
                    source_categories,
                )
            all_event_records[event_id] = (
                key,
                a0_input,
                label,
                container_event,
            )
        submissions_time = parse_timestamp(submissions["frozen_at"])
        adjudication_time = parse_timestamp(adjudication["frozen_at"])
        individual_submission_times = [
            parse_timestamp(item["frozen_at"])
            for item in submissions["submissions"]
        ]
        resolution_times = [
            parse_timestamp(item["decided_at"])
            for item in adjudication["raw_label_dispositions"]
            if item["disposition"] in ("rejected", "unresolved")
        ]
        resolution_times.extend(
            parse_timestamp(item["frozen_at"])
            for item in adjudication["case_roster"]
        )
        resolution_times.extend(
            parse_timestamp(item["frozen_at"])
            for item in adjudication["independent_path_groups"]
        )
        resolution_times.extend(
            parse_timestamp(item["frozen_at"])
            for item in adjudication["unresolved_records"]
        )
        resolution_times.extend(
            parse_timestamp(field["resolved_at"])
            for event in adjudication["events"]
            for field in event["raw_support_adjudication"][
                "field_resolutions"
            ]
        )
        if not (
            manifest_time
            < min(individual_submission_times)
            <= max(individual_submission_times)
            <= submissions_time
            < adjudication_time
            < a0_seal
            and (
                not resolution_times
                or (
                    submissions_time
                    < min(resolution_times)
                    <= max(resolution_times)
                    <= adjudication_time
                )
            )
        ):
            return (
                _block_error(
                    stage,
                    "SEM_A0_ONLY_ADJUDICATION_ORDER",
                    "manifest -> raw submissions -> every case/path/resolution -> adjudication container -> full A0 barrier is required",
                    location["a0_adjudication_container_relative_path"],
                ),
                source_categories,
            )
        if label_times and not (
            submissions_time
            < min(label_times)
            <= max(label_times)
            <= adjudication_time
        ):
            return (
                _block_error(
                    stage,
                    "SEM_A0_CHILD_FREEZE_ORDER",
                    (
                        "every physical A0 event label must freeze after its "
                        "submission container and no later than its "
                        "adjudication container"
                    ),
                    location[
                        "a0_adjudication_container_relative_path"
                    ],
                    "$.events",
                ),
                source_categories,
            )
        latest_a0 = max(
            [latest_a0, submissions_time, adjudication_time]
            + label_times
        )
        freeze = freeze_by_key[key]
        expected_freeze_events = [
            {
                "adjudicated_event_id": item["adjudicated_event_id"],
                "case_id": item["case_id"],
                "supporting_a0_raw_label_ids": item[
                    "supporting_a0_raw_label_ids"
                ],
                "adjudication_mode": item["adjudication_mode"],
                "grounding_mode": item["grounding_mode"],
                "evidence_class": _referenced_value(
                    loaded, "a0_label", item["a0_label_relative_path"]
                )["evidence_class"],
                "raw_support_adjudication_sha256": canonical_sha256(
                    item["raw_support_adjudication"]
                ),
                "frozen_at": _referenced_value(
                    loaded, "a0_label", item["a0_label_relative_path"]
                )["frozen_at"],
            }
            for item in adjudication["events"]
        ]
        flattened_raw_ids = sorted(
            raw_to_annotator, key=lambda value: value.encode("utf-8")
        )
        if (
            freeze["a0_input_ref"] != artifact_ref(a0_input)
            or freeze["a0_submissions_ref"] != artifact_ref(submissions)
            or freeze["a0_adjudication_container_ref"]
            != artifact_ref(adjudication)
            or freeze["a0_raw_label_ids"] != flattened_raw_ids
            or freeze["raw_label_dispositions"]
            != adjudication["raw_label_dispositions"]
            or freeze["case_roster"] != adjudication["case_roster"]
            or freeze["adjudicated_events"] != expected_freeze_events
            or freeze["independent_path_groups"]
            != adjudication["independent_path_groups"]
            or freeze["unresolved_records"]
            != adjudication["unresolved_records"]
            or freeze["prefix_chain_tip_sha256"]
            != a0_input["prefix_chain_tip_sha256"]
            or freeze["a0_submissions_frozen_at"]
            != submissions["frozen_at"]
            or freeze["a0_adjudication_frozen_at"]
            != adjudication["frozen_at"]
        ):
            return (
                _block_error(
                    stage,
                    "SEM_A0_BARRIER_FREEZE_MISMATCH",
                    "A0 barrier must exactly freeze raw dispositions, cases, paths, unresolved records, all 0..N events, and prefix tip",
                    BLOCK_BARRIER_FILE,
                    "$.location_freezes.%s.%s" % key,
                ),
                source_categories,
            )
    if latest_a0 >= a0_seal:
        return (
            _block_error(
                stage,
                "SEM_A0_BARRIER_SEALED_EARLY",
                "A0 barrier must follow the last location adjudication",
                BLOCK_BARRIER_FILE,
                "$.sealed_at",
            ),
            source_categories,
        )
    if (
        a0_barrier["expected_adjudicated_event_count"]
        != len(all_event_records)
    ):
        return (
            _block_error(
                stage,
                "SEM_A0_BARRIER_EVENT_COUNT",
                "A0 barrier event count must derive from the exact 0..N event sets",
                BLOCK_BARRIER_FILE,
                "$.expected_adjudicated_event_count",
            ),
            source_categories,
        )

    a1_freezes = a1_barrier["event_freezes"]
    a1_event_ids = [item["adjudicated_event_id"] for item in a1_freezes]
    if (
        len(a1_event_ids) != len(set(a1_event_ids))
        or set(a1_event_ids) != set(all_event_records)
        or a1_barrier["expected_adjudicated_event_count"]
        != len(all_event_records)
    ):
        return (
            _block_error(
                stage,
                "SEM_A1_EXACT_EVENT_SET",
                "full A1 barrier requires exactly one reveal/label path for every block event",
                BLOCK_A1_BARRIER_FILE,
                "$.event_freezes",
            ),
            source_categories,
        )
    latest_a1 = a0_seal
    seen_a1_reveal_refs: Set[Tuple[str, str]] = set()
    seen_a1_label_refs: Set[Tuple[str, str]] = set()
    seen_a1_paths: Set[str] = set()
    primary_rows_by_case: Dict[str, List[str]] = {}
    for freeze in a1_freezes:
        event_id = freeze["adjudicated_event_id"]
        (unit_alias, boundary_id), a0_input, a0_label, _ = all_event_records[
            event_id
        ]
        if (
            freeze["unit_alias"] != unit_alias
            or freeze["boundary_location_id"] != boundary_id
        ):
            return (
                _block_error(
                    stage,
                    "SEM_A1_EVENT_LOCATION_SPLICE",
                    "A1 event cannot be linked to another unit or location",
                    BLOCK_A1_BARRIER_FILE,
                    "$.event_freezes.%s" % event_id,
                ),
                source_categories,
            )
        reveal = _referenced_value(
            loaded, "a1_reveal", freeze["a1_reveal_relative_path"]
        )
        a1_label = _referenced_value(
            loaded, "a1_label", freeze["a1_label_relative_path"]
        )
        reveal_ref_key = (
            freeze["a1_reveal_ref"]["artifact_id"],
            freeze["a1_reveal_ref"]["sha256"],
        )
        label_ref_key = (
            freeze["a1_label_ref"]["artifact_id"],
            freeze["a1_label_ref"]["sha256"],
        )
        path_names = {
            freeze["a1_reveal_relative_path"],
            freeze["a1_label_relative_path"],
        }
        if (
            reveal_ref_key in seen_a1_reveal_refs
            or label_ref_key in seen_a1_label_refs
            or seen_a1_paths.intersection(path_names)
        ):
            return (
                _block_error(
                    stage,
                    "SEM_A1_PATH_ALIAS",
                    "every required event must have one physically distinct A1 reveal and label path",
                    BLOCK_A1_BARRIER_FILE,
                    "$.event_freezes.%s" % event_id,
                ),
                source_categories,
            )
        seen_a1_reveal_refs.add(reveal_ref_key)
        seen_a1_label_refs.add(label_ref_key)
        seen_a1_paths.update(path_names)
        if (
            reveal["unit_alias"] != unit_alias
            or reveal["adjudicated_event_id"] != event_id
            or reveal["a0_input_ref"] != artifact_ref(a0_input)
            or reveal["a0_label_ref"] != artifact_ref(a0_label)
            or a1_label["unit_alias"] != unit_alias
            or a1_label["adjudicated_event_id"] != event_id
            or a1_label["a0_input_ref"] != artifact_ref(a0_input)
            or a1_label["a0_label_ref"] != artifact_ref(a0_label)
            or a1_label["a1_reveal_ref"] != artifact_ref(reveal)
        ):
            return (
                _block_error(
                    stage,
                    "SEM_A1_EVENT_PATH_SPLICE",
                    "A0 source/obligation/event and A1 phenotype paths must remain event-local",
                    freeze["a1_label_relative_path"],
                ),
                source_categories,
            )
        if a1_label["annotator_alias"] not in registry[
            "a1_annotator_aliases"
        ]:
            return (
                _block_error(
                    stage,
                    "SEM_A1_ANNOTATOR_ROLE",
                    "A1 label requires the permanent A1 pool",
                    freeze["a1_label_relative_path"],
                    "$.annotator_alias",
                ),
                source_categories,
            )
        reveal_time = parse_timestamp(reveal["revealed_at"])
        label_time = parse_timestamp(a1_label["frozen_at"])
        if not (a0_seal < reveal_time < label_time < a1_seal):
            return (
                _block_error(
                    stage,
                    "SEM_WHOLE_BLOCK_A1_EARLY",
                    "no A1 reveal may occur until every A0 container and the full A0 barrier are frozen",
                    freeze["a1_reveal_relative_path"],
                ),
                source_categories,
            )
        if freeze["a1_label_frozen_at"] != a1_label["frozen_at"]:
            return (
                _block_error(
                    stage,
                    "SEM_A1_BARRIER_FREEZE_TIME",
                    "A1 barrier timestamp must equal the physical A1 label",
                    BLOCK_A1_BARRIER_FILE,
                ),
                source_categories,
            )
        latest_a1 = max(latest_a1, label_time)
        if a1_label["primary_uacf_d_positive"]:
            primary_rows_by_case.setdefault(
                a0_label["case_id"], []
            ).append(event_id)
        scan = scans_by_alias[unit_alias]
        prefix_entries = _referenced_value(
            loaded, "prefix_commit", scan["prefix_commit_log_relative_path"]
        )
        prefix_by_location = {
            item["boundary_location_id"]: item for item in prefix_entries
        }
        ordinal = prefix_by_location[boundary_id]["observation_ordinal"]
        stream = _referenced_value(
            loaded, "block_stream_ledger", scan["stream_ledger_relative_path"]
        )
        action = stream["entries"][ordinal]["current_action"]
        atomicity = freeze["reveal_atomicity"]
        if action["kind"] != "current_action":
            return (
                _block_error(
                    stage,
                    "SEM_A1_WITHOUT_CURRENT_ACTION",
                    "an adjudicated behavioral event must bind a current action record",
                    BLOCK_A1_BARRIER_FILE,
                    "$.event_freezes.%s.reveal_atomicity" % event_id,
                ),
                source_categories,
            )
        if (
            atomicity["trajectory_mode"] != stream["trajectory_mode"]
            or atomicity["stream_observation_ordinal"] != ordinal
            or atomicity["stream_action_sha256"]
            != action["action_bytes_sha256"]
            or atomicity["entire_action_unit_revealed_at"]
            != reveal["revealed_at"]
            or (
                action["action_unit"] == "batch_bundle"
                and atomicity["action_unit"] != "batch_bundle"
            )
            or (
                action["action_unit"] == "single_action"
                and atomicity["action_unit"] != "single_action"
            )
        ):
            return (
                _block_error(
                    stage,
                    "SEM_A1_STREAM_ACTION_LINK",
                    "A1 reveal must bind the exact current action or atomic batch",
                    BLOCK_A1_BARRIER_FILE,
                    "$.event_freezes.%s.reveal_atomicity" % event_id,
                ),
                source_categories,
            )
    if any(
        len(event_ids_for_case) > 1
        for event_ids_for_case in primary_rows_by_case.values()
    ):
        return (
            _block_error(
                stage,
                "SEM_A0_CASE_PRIMARY_MULTIPLICITY",
                "one raw-derived case can contribute at most one primary analysis row",
                BLOCK_A1_BARRIER_FILE,
                "$.event_freezes",
            ),
            source_categories,
        )
        if atomicity["action_unit"] == "batch_bundle":
            ordinals = [
                item["action_ordinal"] for item in action["subactions"]
            ]
            if (
                atomicity["bundle_first_action_ordinal"] != min(ordinals)
                or atomicity["bundle_last_action_ordinal"] != max(ordinals)
            ):
                return (
                    _block_error(
                        stage,
                        "SEM_A1_BATCH_RANGE",
                        "A1 batch range must bind every atomic subaction",
                        BLOCK_A1_BARRIER_FILE,
                    ),
                    source_categories,
                )
        event_artifacts: Dict[str, Any] = {
            "coordinator_envelope": coordinators[unit_alias],
            "a0_input": a0_input,
            "a0_label": a0_label,
            "a1_reveal": reveal,
            "a1_label": a1_label,
            "prefix_commits": prefix_entries[: ordinal + 1],
        }
        if "omission_interval_relative_path" in freeze:
            event_artifacts["omission_interval"] = _referenced_value(
                loaded,
                "omission_interval",
                freeze["omission_interval_relative_path"],
            )
        component_error = first_semantic_error(event_artifacts)
        if component_error:
            copied = dict(component_error)
            copied["artifact"] = freeze["a1_label_relative_path"]
            return copied, source_categories
    if latest_a1 >= a1_seal:
        return (
            _block_error(
                stage,
                "SEM_A1_BARRIER_SEALED_EARLY",
                "A1 barrier must follow every A1 label",
                BLOCK_A1_BARRIER_FILE,
                "$.sealed_at",
            ),
            source_categories,
        )
    return None, source_categories


def first_full_block_exposure_error(
    loaded: Mapping[str, Any],
) -> Optional[Dict[str, Any]]:
    stage = STAGE_ORDER[5]
    fixed = loaded["fixed"]
    manifest = fixed["block_location_manifest"]
    a0_barrier = fixed["block_barrier"]
    a1_barrier = fixed["block_a1_barrier"]
    gate = fixed["stage_b_gate"]
    events = fixed["block_exposure_events"]
    registry = a0_barrier["role_registry"]
    role_by_alias: Dict[str, str] = {}
    for field, role in (
        ("a0_annotator_aliases", "a0_annotator"),
        ("a0_adjudicator_aliases", "a0_adjudicator"),
        ("a1_annotator_aliases", "a1_annotator"),
        ("stage_b_annotator_aliases", "stage_b_annotator"),
        ("coordinator_aliases", "coordinator"),
        ("candidate_generator_aliases", "candidate_generator"),
        ("reference_aliases", "reference"),
    ):
        role_by_alias.update({alias: role for alias in registry[field]})
    a0_aliases = set(registry["a0_annotator_aliases"]) | set(
        registry["a0_adjudicator_aliases"]
    )
    a1_aliases = set(registry["a1_annotator_aliases"])
    stage_b_aliases = set(registry["stage_b_annotator_aliases"])
    forbidden_for_a0 = {
        "candidate_action",
        "a1_reveal",
        "a1_label",
        "block_a1_barrier",
        "stage_b_input",
    }
    a0_seal = parse_timestamp(a0_barrier["sealed_at"])
    a1_seal = parse_timestamp(a1_barrier["sealed_at"])
    stage_b_time = parse_timestamp(gate["authorized_at"])
    ledger_closed = parse_timestamp(gate["ledger_closed_at"])
    if (
        gate["exposure_event_count"] != len(events)
        or not events
        or gate["exposure_ledger_id"] != events[0]["exposure_ledger_id"]
    ):
        return _block_error(
            stage,
            "EXPOSURE_LEDGER_COMPLETENESS",
            "Stage-B gate must bind the declared complete delivery/access ledger",
            STAGE_B_GATE_FILE,
        )
    previous_time: Optional[datetime] = None
    seen_types: Set[str] = set()
    visible_refs: Set[Tuple[str, str, str]] = set()
    delivered_refs: Set[Tuple[str, str, str]] = set()
    events_by_type: Dict[str, List[Tuple[int, Mapping[str, Any]]]] = {}
    for index, event in enumerate(events):
        occurred = parse_timestamp(event["occurred_at"])
        if event["sequence"] != index:
            return _block_error(
                stage,
                "EXPOSURE_SEQUENCE",
                "exposure ledger sequence must be complete and contiguous",
                BLOCK_EXPOSURE_LOG_FILE,
                "$[%d].sequence" % index,
            )
        if (
            event["block_id"] != a0_barrier["block_id"]
            or event["exposure_ledger_id"] != gate["exposure_ledger_id"]
            or (previous_time is not None and occurred < previous_time)
            or occurred > ledger_closed
        ):
            return _block_error(
                stage,
                "EXPOSURE_LEDGER_ORDER_OR_SCOPE",
                "all exposure events must be ordered, block-local, and included before ledger close",
                BLOCK_EXPOSURE_LOG_FILE,
                "$[%d]" % index,
            )
        previous_time = occurred
        seen_types.add(event["event_type"])
        events_by_type.setdefault(event["event_type"], []).append(
            (index, event)
        )
        actor = event["actor_alias"]
        if role_by_alias.get(actor) != event["actor_role"]:
            return _block_error(
                stage,
                "EXPOSURE_ACTOR_ROLE_HISTORY",
                "actor role must match the permanent role ledger",
                BLOCK_EXPOSURE_LOG_FILE,
                "$[%d].actor_role" % index,
            )
        recipients = set(event["recipient_aliases"])
        if any(alias not in role_by_alias for alias in recipients):
            return _block_error(
                stage,
                "EXPOSURE_UNKNOWN_RECIPIENT",
                "every recipient must resolve through permanent role history",
                BLOCK_EXPOSURE_LOG_FILE,
                "$[%d].recipient_aliases" % index,
            )
        operation = event["exposure_operation"]
        if (operation == "deliver") != bool(recipients):
            return _block_error(
                stage,
                "EXPOSURE_DELIVERY_SEMANTICS",
                "delivery requires recipients and non-delivery events cannot hide recipients",
                BLOCK_EXPOSURE_LOG_FILE,
                "$[%d]" % index,
            )
        classes = {
            item["artifact_class"] for item in event["visible_artifacts"]
        }
        for visible in event["visible_artifacts"]:
            ref = visible["artifact_ref"]
            key = (
                visible["artifact_class"],
                ref["artifact_id"],
                ref["sha256"],
            )
            visible_refs.add(key)
            if operation == "deliver":
                delivered_refs.add(key)
        a0_access = operation == "access" and actor in a0_aliases
        a0_delivery = operation == "deliver" and bool(
            recipients & a0_aliases
        )
        if (a0_access or a0_delivery) and classes & forbidden_for_a0:
            return _block_error(
                stage,
                "EXPOSURE_WHOLE_BLOCK_A0_LEAK",
                "any action/A1/outcome delivery or access by any A0 role invalidates the entire block",
                BLOCK_EXPOSURE_LOG_FILE,
                "$[%d].visible_artifacts" % index,
            )
        a1_involved = (
            actor in a1_aliases
            or bool(recipients & a1_aliases)
            or bool(classes & {"candidate_action", "a1_reveal", "a1_label"})
        )
        if a1_involved and occurred <= a0_seal:
            return _block_error(
                stage,
                "EXPOSURE_WHOLE_BLOCK_A1_EARLY",
                "no A1 authorization, delivery, access, or reveal may precede the full A0 barrier",
                BLOCK_EXPOSURE_LOG_FILE,
                "$[%d].occurred_at" % index,
            )
        stage_b_involved = (
            actor in stage_b_aliases
            or bool(recipients & stage_b_aliases)
            or "stage_b_input" in classes
        )
        if stage_b_involved and occurred <= stage_b_time:
            return _block_error(
                stage,
                "EXPOSURE_STAGE_B_EARLY",
                "Stage B delivery/access must follow the full A1 barrier and explicit gate",
                BLOCK_EXPOSURE_LOG_FILE,
                "$[%d].occurred_at" % index,
            )
        if event["event_type"] == "block_a0_barrier_frozen" and occurred != a0_seal:
            return _block_error(
                stage,
                "EXPOSURE_A0_BARRIER_TIME",
                "A0 barrier ledger event must equal its physical seal time",
                BLOCK_EXPOSURE_LOG_FILE,
                "$[%d].occurred_at" % index,
            )
        if event["event_type"] == "block_a1_barrier_frozen" and occurred != a1_seal:
            return _block_error(
                stage,
                "EXPOSURE_A1_BARRIER_TIME",
                "A1 barrier ledger event must equal its physical seal time",
                BLOCK_EXPOSURE_LOG_FILE,
                "$[%d].occurred_at" % index,
            )
        if event["event_type"] == "stage_b_authorized" and occurred != stage_b_time:
            return _block_error(
                stage,
                "EXPOSURE_STAGE_B_GATE_TIME",
                "Stage-B authorization event must equal its physical gate time",
                BLOCK_EXPOSURE_LOG_FILE,
                "$[%d].occurred_at" % index,
            )

    def artifact_key(
        artifact_class: str, artifact: Mapping[str, Any]
    ) -> Tuple[str, str, str]:
        return (
            artifact_class,
            artifact["artifact_id"],
            canonical_sha256(artifact),
        )

    def event_visible_set(
        event: Mapping[str, Any],
    ) -> frozenset:
        return frozenset(
            (
                item["artifact_class"],
                item["artifact_ref"]["artifact_id"],
                item["artifact_ref"]["sha256"],
            )
            for item in event["visible_artifacts"]
        )

    def contract_error(
        message: str,
        event_type: str,
        index: Optional[int] = None,
    ) -> Dict[str, Any]:
        return _block_error(
            stage,
            "EXPOSURE_EVENT_CONTRACT",
            message,
            BLOCK_EXPOSURE_LOG_FILE,
            (
                "$.%s" % event_type
                if index is None
                else "$[%d]" % index
            ),
        )

    def verify_contracts(
        event_type: str,
        contracts: Sequence[Mapping[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        actual = events_by_type.get(event_type, [])
        if len(actual) != len(contracts):
            return contract_error(
                "%s multiplicity must equal the physical artifact roster"
                % event_type,
                event_type,
            )
        actual_by_visible: Dict[
            frozenset, List[Tuple[int, Mapping[str, Any]]]
        ] = {}
        for index, event in actual:
            actual_by_visible.setdefault(
                event_visible_set(event), []
            ).append((index, event))
        expected_visible_sets = [
            frozenset(contract["visible"]) for contract in contracts
        ]
        if (
            len(expected_visible_sets) != len(set(expected_visible_sets))
            or set(actual_by_visible) != set(expected_visible_sets)
            or any(len(items) != 1 for items in actual_by_visible.values())
        ):
            return contract_error(
                "%s must bind each exact event-local artifact set once"
                % event_type,
                event_type,
            )
        for contract in contracts:
            visible = frozenset(contract["visible"])
            index, event = actual_by_visible[visible][0]
            recipients = set(event["recipient_aliases"])
            if (
                event["actor_role"] != contract["actor_role"]
                or event["actor_alias"]
                not in contract["actor_aliases"]
                or event["exposure_operation"] != contract["operation"]
                or recipients != contract["recipients"]
            ):
                return contract_error(
                    "%s actor, role, operation, and recipients must match the event-local obligation"
                    % event_type,
                    event_type,
                    index,
                )
            occurred = parse_timestamp(event["occurred_at"])
            exact_time = contract.get("exact_time")
            earliest = contract.get("earliest")
            latest = contract.get("latest")
            if (
                exact_time is not None
                and occurred != exact_time
            ) or (
                earliest is not None
                and occurred < earliest
            ) or (
                latest is not None
                and occurred > latest
            ):
                return contract_error(
                    "%s timestamp must match its physical freeze/reveal interval"
                    % event_type,
                    event_type,
                    index,
                )
        return None

    coordinator_aliases = set(registry["coordinator_aliases"])
    fixed_contract_groups: Sequence[
        Tuple[str, Sequence[Mapping[str, Any]]]
    ] = (
        (
            "block_frame_frozen",
            [
                {
                    "visible": {
                        artifact_key(
                            "block_frame", fixed["block_frame"]
                        )
                    },
                    "actor_role": "coordinator",
                    "actor_aliases": coordinator_aliases,
                    "operation": "freeze",
                    "recipients": set(),
                    "exact_time": parse_timestamp(
                        fixed["block_frame"]["frozen_at"]
                    ),
                }
            ],
        ),
        (
            "location_manifest_frozen",
            [
                {
                    "visible": {
                        artifact_key(
                            "location_manifest", manifest
                        )
                    },
                    "actor_role": "coordinator",
                    "actor_aliases": coordinator_aliases,
                    "operation": "freeze",
                    "recipients": set(),
                    "exact_time": parse_timestamp(
                        manifest["frozen_at"]
                    ),
                }
            ],
        ),
        (
            "block_a0_barrier_frozen",
            [
                {
                    "visible": {
                        artifact_key(
                            "block_a0_barrier", a0_barrier
                        )
                    },
                    "actor_role": "coordinator",
                    "actor_aliases": {a0_barrier["sealed_by"]},
                    "operation": "freeze",
                    "recipients": set(),
                    "exact_time": a0_seal,
                }
            ],
        ),
        (
            "block_a1_barrier_frozen",
            [
                {
                    "visible": {
                        artifact_key(
                            "block_a1_barrier", a1_barrier
                        )
                    },
                    "actor_role": "coordinator",
                    "actor_aliases": {a1_barrier["sealed_by"]},
                    "operation": "freeze",
                    "recipients": set(),
                    "exact_time": a1_seal,
                }
            ],
        ),
        (
            "stage_b_authorized",
            [
                {
                    "visible": {
                        artifact_key(
                            "block_a1_barrier", a1_barrier
                        )
                    },
                    "actor_role": "coordinator",
                    "actor_aliases": {gate["authorized_by"]},
                    "operation": "authorize",
                    "recipients": set(),
                    "exact_time": stage_b_time,
                }
            ],
        ),
    )
    for event_type, contracts in fixed_contract_groups:
        error = verify_contracts(event_type, contracts)
        if error:
            return error

    a0_input_contracts: List[Dict[str, Any]] = []
    a0_raw_contracts: List[Dict[str, Any]] = []
    a0_adjudication_contracts: List[Dict[str, Any]] = []
    for location in manifest["locations"]:
        a0_input = _referenced_value(
            loaded, "a0_input", location["a0_input_relative_path"]
        )
        submissions = _referenced_value(
            loaded,
            "block_a0_submissions",
            location["a0_submissions_relative_path"],
        )
        adjudication = _referenced_value(
            loaded,
            "block_a0_adjudication",
            location["a0_adjudication_container_relative_path"],
        )
        submission_aliases = {
            item["annotator_alias"]
            for item in submissions["submissions"]
        }
        a0_input_contracts.append(
            {
                "visible": {artifact_key("a0_input", a0_input)},
                "actor_role": "coordinator",
                "actor_aliases": coordinator_aliases,
                "operation": "deliver",
                "recipients": submission_aliases,
                "earliest": parse_timestamp(a0_input["frozen_at"]),
                "latest": min(
                    parse_timestamp(item["frozen_at"])
                    for item in submissions["submissions"]
                ),
            }
        )
        a0_raw_contracts.append(
            {
                "visible": {
                    artifact_key("a0_raw_labels", submissions)
                },
                "actor_role": "a0_annotator",
                "actor_aliases": submission_aliases,
                "operation": "freeze",
                "recipients": set(),
                "exact_time": parse_timestamp(
                    submissions["frozen_at"]
                ),
            }
        )
        adjudication_visible = {
            artifact_key("a0_adjudication", adjudication)
        }
        for container_event in adjudication["events"]:
            label = _referenced_value(
                loaded,
                "a0_label",
                container_event["a0_label_relative_path"],
            )
            adjudication_visible.add(
                artifact_key("a0_adjudication", label)
            )
            resolution = container_event["source_resolution"]
            if resolution["status"] == "source_unidentifiable":
                for search_ref in resolution["search_result_refs"]:
                    search_result = _referenced_value(
                        loaded,
                        "source_search_result",
                        search_ref["relative_path"],
                    )
                    adjudication_visible.add(
                        artifact_key(
                            "a0_adjudication", search_result
                        )
                    )
        a0_adjudication_contracts.append(
            {
                "visible": adjudication_visible,
                "actor_role": "a0_adjudicator",
                "actor_aliases": {
                    adjudication["adjudicator_alias"]
                },
                "operation": "freeze",
                "recipients": set(),
                "exact_time": parse_timestamp(
                    adjudication["frozen_at"]
                ),
            }
        )
    for event_type, contracts in (
        ("a0_input_released", a0_input_contracts),
        ("a0_raw_labels_frozen", a0_raw_contracts),
        ("a0_adjudication_frozen", a0_adjudication_contracts),
    ):
        error = verify_contracts(event_type, contracts)
        if error:
            return error

    a1_reveal_contracts: List[Dict[str, Any]] = []
    a1_label_contracts: List[Dict[str, Any]] = []
    for freeze in a1_barrier["event_freezes"]:
        reveal = _referenced_value(
            loaded, "a1_reveal", freeze["a1_reveal_relative_path"]
        )
        label = _referenced_value(
            loaded, "a1_label", freeze["a1_label_relative_path"]
        )
        a1_reveal_contracts.append(
            {
                "visible": {artifact_key("a1_reveal", reveal)},
                "actor_role": "coordinator",
                "actor_aliases": coordinator_aliases,
                "operation": "deliver",
                "recipients": {label["annotator_alias"]},
                "exact_time": parse_timestamp(reveal["revealed_at"]),
            }
        )
        a1_label_contracts.append(
            {
                "visible": {artifact_key("a1_label", label)},
                "actor_role": "a1_annotator",
                "actor_aliases": {label["annotator_alias"]},
                "operation": "freeze",
                "recipients": set(),
                "exact_time": parse_timestamp(label["frozen_at"]),
            }
        )
    for event_type, contracts in (
        ("a1_revealed", a1_reveal_contracts),
        ("a1_label_frozen", a1_label_contracts),
    ):
        error = verify_contracts(event_type, contracts)
        if error:
            return error

    stage_b_records = events_by_type.get("stage_b_input_released", [])
    if len(stage_b_records) != 1:
        return contract_error(
            "stage_b_input_released must occur exactly once",
            "stage_b_input_released",
        )
    stage_b_index, stage_b_event = stage_b_records[0]
    if (
        stage_b_event["actor_alias"] != gate["authorized_by"]
        or stage_b_event["actor_role"] != "coordinator"
        or stage_b_event["exposure_operation"] != "deliver"
        or set(stage_b_event["recipient_aliases"]) != stage_b_aliases
        or len(stage_b_event["visible_artifacts"]) != 1
        or stage_b_event["visible_artifacts"][0]["artifact_class"]
        != "stage_b_input"
    ):
        return contract_error(
            "Stage-B input must be delivered by its coordinator to the exact Stage-B pool",
            "stage_b_input_released",
            stage_b_index,
        )

    required_types = {
        "block_frame_frozen",
        "location_manifest_frozen",
        "block_a0_barrier_frozen",
        "block_a1_barrier_frozen",
        "stage_b_authorized",
        "stage_b_input_released",
    }
    if not required_types.issubset(seen_types):
        return _block_error(
            stage,
            "EXPOSURE_REQUIRED_PHASE_EVENT_MISSING",
            "delivery/access ledger omits a required whole-block phase",
            BLOCK_EXPOSURE_LOG_FILE,
        )

    required_visible: Set[Tuple[str, str, str]] = {
        (
            "block_frame",
            fixed["block_frame"]["artifact_id"],
            canonical_sha256(fixed["block_frame"]),
        ),
        (
            "location_manifest",
            manifest["artifact_id"],
            canonical_sha256(manifest),
        ),
        (
            "block_a0_barrier",
            a0_barrier["artifact_id"],
            canonical_sha256(a0_barrier),
        ),
        (
            "block_a1_barrier",
            a1_barrier["artifact_id"],
            canonical_sha256(a1_barrier),
        ),
    }
    required_deliveries: Set[Tuple[str, str, str]] = set()
    for location in manifest["locations"]:
        a0_input = _referenced_value(
            loaded, "a0_input", location["a0_input_relative_path"]
        )
        submissions = _referenced_value(
            loaded,
            "block_a0_submissions",
            location["a0_submissions_relative_path"],
        )
        adjudication = _referenced_value(
            loaded,
            "block_a0_adjudication",
            location["a0_adjudication_container_relative_path"],
        )
        required_visible.update(
            {
                (
                    "a0_input",
                    a0_input["artifact_id"],
                    canonical_sha256(a0_input),
                ),
                (
                    "a0_raw_labels",
                    submissions["artifact_id"],
                    canonical_sha256(submissions),
                ),
                (
                    "a0_adjudication",
                    adjudication["artifact_id"],
                    canonical_sha256(adjudication),
                ),
            }
        )
        required_deliveries.add(
            (
                "a0_input",
                a0_input["artifact_id"],
                canonical_sha256(a0_input),
            )
        )
        for container_event in adjudication["events"]:
            a0_label = _referenced_value(
                loaded,
                "a0_label",
                container_event["a0_label_relative_path"],
            )
            required_visible.add(
                (
                    "a0_adjudication",
                    a0_label["artifact_id"],
                    canonical_sha256(a0_label),
                )
            )
            resolution = container_event["source_resolution"]
            if resolution["status"] == "source_unidentifiable":
                for search_ref in resolution["search_result_refs"]:
                    search_result = _referenced_value(
                        loaded,
                        "source_search_result",
                        search_ref["relative_path"],
                    )
                    required_visible.add(
                        (
                            "a0_adjudication",
                            search_result["artifact_id"],
                            canonical_sha256(search_result),
                        )
                    )
    for freeze in a1_barrier["event_freezes"]:
        reveal = _referenced_value(
            loaded, "a1_reveal", freeze["a1_reveal_relative_path"]
        )
        label = _referenced_value(
            loaded, "a1_label", freeze["a1_label_relative_path"]
        )
        reveal_key = (
            "a1_reveal",
            reveal["artifact_id"],
            canonical_sha256(reveal),
        )
        required_visible.update(
            {
                reveal_key,
                (
                    "a1_label",
                    label["artifact_id"],
                    canonical_sha256(label),
                ),
            }
        )
        required_deliveries.add(reveal_key)
    if not required_visible.issubset(visible_refs):
        return _block_error(
            stage,
            "EXPOSURE_ARTIFACT_COVERAGE",
            "complete ledger must cover every frame, location, A0, barrier, and A1 artifact",
            BLOCK_EXPOSURE_LOG_FILE,
        )
    if not required_deliveries.issubset(delivered_refs):
        return _block_error(
            stage,
            "EXPOSURE_DELIVERY_COVERAGE",
            "complete ledger must record A0-input and A1-reveal deliveries",
            BLOCK_EXPOSURE_LOG_FILE,
        )

    identity_values: Set[str] = set()
    for coordinator in loaded["referenced"]["coordinator_envelope"].values():
        identity_values.update(
            value
            for value in coordinator["identity"].values()
            if isinstance(value, str)
        )
        identity_values.add(
            coordinator["source_snapshot"]["source_detail_url"]
        )
    public_a0: List[Tuple[str, Mapping[str, Any]]] = []
    for kind in (
        "a0_input",
        "block_a0_submissions",
        "block_a0_adjudication",
        "a0_label",
        "source_search_result",
    ):
        public_a0.extend(loaded["referenced"].get(kind, {}).items())
    for artifact_name, artifact in public_a0:
        for path, obj in walk_objects(artifact):
            forbidden = set(obj) & FORBIDDEN_PUBLIC_KEYS
            if forbidden:
                return _block_error(
                    stage,
                    "EXPOSURE_A0_FORBIDDEN_FIELD",
                    "A0 artifact contains coordinator/action/outcome fields",
                    artifact_name,
                    path,
                )
        for path, text_value in walk_strings(artifact):
            if text_value in identity_values or URL_OR_PATH_RE.search(
                text_value
            ):
                return _block_error(
                    stage,
                    "EXPOSURE_A0_IDENTITY_VALUE_LEAK",
                    "A0 artifact contains identity, URL, or local-path information",
                    artifact_name,
                    path,
                )
    return None


def _full_block_authority_projection(
    loaded: Mapping[str, Any],
    source_categories: Mapping[str, str],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Expose read-only roots and event-local refs for downstream validators."""

    fixed = loaded["fixed"]
    frame = fixed["block_frame"]
    manifest = fixed["block_location_manifest"]
    a0_barrier = fixed["block_barrier"]
    a1_barrier = fixed["block_a1_barrier"]
    stage_b_gate = fixed["stage_b_gate"]
    role_history = fixed["role_history"]
    scans = {
        item["unit_alias"]: item for item in manifest["unit_scans"]
    }
    frame_units = {
        item["unit_alias"]: item for item in frame["expected_units"]
    }
    a1_freezes = {
        item["adjudicated_event_id"]: item
        for item in a1_barrier["event_freezes"]
    }
    unit_stream_roots: List[Dict[str, Any]] = []
    for unit_alias in utf8_sorted(scans):
        scan = scans[unit_alias]
        stream = _referenced_value(
            loaded,
            "block_stream_ledger",
            scan["stream_ledger_relative_path"],
        )
        unit_stream_roots.append(
            {
                "unit_alias": unit_alias,
                "prefix_commit_log_relative_path": scan[
                    "prefix_commit_log_relative_path"
                ],
                "prefix_commit_log_sha256": scan[
                    "prefix_commit_log_sha256"
                ],
                "prefix_chain_tip_sha256": scan[
                    "prefix_chain_tip_sha256"
                ],
                "stream_ledger_relative_path": scan[
                    "stream_ledger_relative_path"
                ],
                "stream_ledger_ref": scan["stream_ledger_ref"],
                "raw_trajectory_relative_path": stream[
                    "raw_trajectory_relative_path"
                ],
                "raw_trajectory_ref": stream["raw_trajectory_ref"],
                "raw_parser": stream["raw_parser"],
            }
        )
    roots = {
        "block_frame": {
            "relative_path": BLOCK_FRAME_FILE,
            "artifact_ref": artifact_ref(frame),
        },
        "location_manifest": {
            "relative_path": BLOCK_LOCATION_MANIFEST_FILE,
            "artifact_ref": artifact_ref(manifest),
        },
        "block_a0_barrier": {
            "relative_path": BLOCK_BARRIER_FILE,
            "artifact_ref": artifact_ref(a0_barrier),
        },
        "block_a1_barrier": {
            "relative_path": BLOCK_A1_BARRIER_FILE,
            "artifact_ref": artifact_ref(a1_barrier),
        },
        "stage_b_gate": {
            "relative_path": STAGE_B_GATE_FILE,
            "artifact_ref": artifact_ref(stage_b_gate),
        },
        "role_history": {
            "relative_path": ROLE_HISTORY_FILE,
            "artifact_ref": artifact_ref(role_history),
        },
        "exposure_ledger": {
            "relative_path": BLOCK_EXPOSURE_LOG_FILE,
            "canonical_sha256": canonical_sha256(
                fixed["block_exposure_events"]
            ),
            "chain_tip_sha256": stage_b_gate[
                "exposure_chain_tip_sha256"
            ],
        },
        "schema_bundle_sha256": schema_bundle_sha256(
            loaded["schemas"]
        ),
        "validator_sha256": validator_file_sha256(),
        "unit_stream_roots": unit_stream_roots,
    }
    events: List[Dict[str, Any]] = []
    for location in manifest["locations"]:
        unit_alias = location["unit_alias"]
        scan = scans[unit_alias]
        prefix_entries = _referenced_value(
            loaded,
            "prefix_commit",
            scan["prefix_commit_log_relative_path"],
        )
        prefix = next(
            item
            for item in prefix_entries
            if item["boundary_location_id"]
            == location["boundary_location_id"]
        )
        stream = _referenced_value(
            loaded,
            "block_stream_ledger",
            scan["stream_ledger_relative_path"],
        )
        action = stream["entries"][prefix["observation_ordinal"]][
            "current_action"
        ]
        adjudication = _referenced_value(
            loaded,
            "block_a0_adjudication",
            location["a0_adjudication_container_relative_path"],
        )
        for container_event in adjudication["events"]:
            event_id = container_event["adjudicated_event_id"]
            freeze = a1_freezes[event_id]
            frame_unit = frame_units[unit_alias]
            key_preimage = [
                frame_unit["task_id"],
                unit_alias,
                location["boundary_location_id"],
                event_id,
            ]
            events.append(
                {
                    "event_key_serialization": "stage0f-canonical-event-key-v1",
                    "event_key_preimage": key_preimage,
                    "event_key_sha256": canonical_sha256(
                        [
                            "stage0f-canonical-event-key-v1",
                            *key_preimage,
                        ]
                    ),
                    "task_id": frame_unit["task_id"],
                    "hosted_config_id": frame_unit[
                        "hosted_config_id"
                    ],
                    "unit_alias": unit_alias,
                    "boundary_location_id": location[
                        "boundary_location_id"
                    ],
                    "adjudicated_event_id": event_id,
                    "observation_ordinal": prefix[
                        "observation_ordinal"
                    ],
                    "stream_ledger_ref": scan["stream_ledger_ref"],
                    "stream_ledger_relative_path": scan[
                        "stream_ledger_relative_path"
                    ],
                    "stream_action_sha256": (
                        action["action_bytes_sha256"]
                        if action["kind"] == "current_action"
                        else None
                    ),
                    "a0_input_ref": location["a0_input_ref"],
                    "a0_input_relative_path": location[
                        "a0_input_relative_path"
                    ],
                    "a0_adjudication_container_ref": location[
                        "a0_adjudication_container_ref"
                    ],
                    "a0_adjudication_container_relative_path": location[
                        "a0_adjudication_container_relative_path"
                    ],
                    "a0_label_ref": container_event[
                        "a0_label_ref"
                    ],
                    "a0_label_relative_path": container_event[
                        "a0_label_relative_path"
                    ],
                    "source_category": source_categories[event_id],
                    "a1_reveal_ref": freeze["a1_reveal_ref"],
                    "a1_reveal_relative_path": freeze[
                        "a1_reveal_relative_path"
                    ],
                    "a1_label_ref": freeze["a1_label_ref"],
                    "a1_label_relative_path": freeze[
                        "a1_label_relative_path"
                    ],
                }
            )
    events.sort(
        key=lambda item: (
            item["task_id"].encode("utf-8"),
            item["hosted_config_id"].encode("utf-8"),
            item["unit_alias"].encode("utf-8"),
            item["observation_ordinal"],
            item["adjudicated_event_id"].encode("utf-8"),
        )
    )
    return roots, events


def _decorate_full_block_result(
    result: Dict[str, Any],
    loaded: Optional[Mapping[str, Any]] = None,
    source_categories: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    result["scope"] = "full_block"
    result["mechanical_claim"] = "STRUCTURAL_VALIDATION_ONLY"
    result["scientific_gate"] = "NOT_EVALUATED"
    result["claim_ceiling"] = "NO_BLOCK_A"
    result["production_authority"] = "UNAVAILABLE_FAIL_CLOSED"
    result["identity_independence"] = "ALIAS_LEVEL_ONLY"
    result["temporal_evidence"] = "SELF_SEALED_SYNTAX_ONLY"
    result["exposure_evidence"] = "SELF_REPORTED_LEDGER_SYNTAX_ONLY"
    result["validator_sha256"] = validator_file_sha256()
    if loaded is None:
        result["frame_sha256"] = None
        result["manifest_sha256"] = None
        result["a0_barrier_sha256"] = None
        result["a1_barrier_sha256"] = None
        result["block_scope"] = None
        result["derived_source_categories"] = {}
        result["authority_roots"] = {}
        result["canonical_adjudicated_events"] = []
        return result
    fixed = loaded["fixed"]
    result["frame_sha256"] = canonical_sha256(fixed["block_frame"])
    result["manifest_sha256"] = canonical_sha256(
        fixed["block_location_manifest"]
    )
    result["a0_barrier_sha256"] = canonical_sha256(
        fixed["block_barrier"]
    )
    result["a1_barrier_sha256"] = canonical_sha256(
        fixed["block_a1_barrier"]
    )
    result["block_scope"] = fixed["block_frame"]["block_scope"]
    result["derived_source_categories"] = (
        dict(source_categories or {}) if result.get("valid") else {}
    )
    if result.get("valid"):
        (
            result["authority_roots"],
            result["canonical_adjudicated_events"],
        ) = _full_block_authority_projection(
            loaded, result["derived_source_categories"]
        )
    else:
        result["authority_roots"] = {}
        result["canonical_adjudicated_events"] = []
    result["bundle_sha256"] = canonical_sha256(
        [
            "stage0f-full-block-bundle-v1",
            result["frame_sha256"],
            result["manifest_sha256"],
            result["a0_barrier_sha256"],
            result["a1_barrier_sha256"],
            canonical_sha256(fixed["stage_b_gate"]),
            fixed["stage_b_gate"]["exposure_chain_tip_sha256"],
            result["validator_sha256"],
        ]
    )
    return result


def validate_full_block(
    block_dir: Path,
    schema_dir: Path,
    expected_frame_sha256: Optional[str],
) -> Dict[str, Any]:
    """The sole full-block entry that can mechanically PASS.

    PASS is structural only: it is not Step-1 GO, does not establish UACF-D
    burden, and does not authorize a real Block-A run.  The real production
    scope currently fails closed on missing external execution authorities.
    """

    if (
        expected_frame_sha256 is None
        or re.fullmatch(r"(?!0{64})[0-9a-f]{64}", expected_frame_sha256)
        is None
    ):
        return _decorate_full_block_result(
            verdict(
                False,
                [
                    _block_error(
                        STAGE_ORDER[3],
                        "FRAME_COMMITMENT_REQUIRED",
                        "full-block validation requires an external nonzero SHA-256 frame commitment",
                        BLOCK_FRAME_FILE,
                    )
                ],
                [],
            )
        )
    loaded, errors = load_full_block(block_dir, schema_dir)
    if errors:
        return _decorate_full_block_result(verdict(False, errors, []))
    assert loaded is not None
    completed = [STAGE_ORDER[0]]
    if JSONSCHEMA_IMPORT_ERROR is not None:
        return _decorate_full_block_result(
            verdict(
                False,
                [
                    _block_error(
                        STAGE_ORDER[1],
                        "DEPENDENCY_JSONSCHEMA_UNAVAILABLE",
                        "Install exact requirements-stage0f.txt; no Draft 2020-12 fallback is permitted: %s"
                        % JSONSCHEMA_IMPORT_ERROR,
                    )
                ],
                completed,
            ),
            loaded,
        )
    errors = validate_schema_meta(loaded["schemas"])
    if errors:
        return _decorate_full_block_result(
            verdict(False, errors, completed), loaded
        )
    completed.append(STAGE_ORDER[1])
    errors = validate_full_block_instances(loaded)
    if errors:
        return _decorate_full_block_result(
            verdict(False, errors, completed), loaded
        )
    completed.append(STAGE_ORDER[2])
    semantic_error, source_categories = first_full_block_semantic_error(
        loaded
    )
    if semantic_error:
        return _decorate_full_block_result(
            verdict(False, [semantic_error], completed),
            loaded,
            source_categories,
        )
    completed.append(STAGE_ORDER[3])
    hash_error = first_full_block_hash_error(
        loaded, expected_frame_sha256
    )
    if hash_error:
        return _decorate_full_block_result(
            verdict(False, [hash_error], completed),
            loaded,
            source_categories,
        )
    completed.append(STAGE_ORDER[4])
    exposure_error = first_full_block_exposure_error(loaded)
    if exposure_error:
        return _decorate_full_block_result(
            verdict(False, [exposure_error], completed),
            loaded,
            source_categories,
        )
    completed.append(STAGE_ORDER[5])
    return _decorate_full_block_result(
        verdict(True, [], completed),
        loaded,
        source_categories,
    )


def validate_block_bundle(
    block_dir: Path,
    schema_dir: Path,
) -> Dict[str, Any]:
    """Legacy block entry: cannot bypass the external-frame API."""

    return verdict(
        False,
        [
            _block_error(
                STAGE_ORDER[3],
                "FULL_BLOCK_REQUIRED",
                "legacy block entry can never PASS; call validate_full_block with the external frame commitment",
                str(block_dir),
            )
        ],
        [],
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
    parser.add_argument(
        "--expected-frame-sha256",
        help="external frozen full-block frame commitment",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    if (args.bundle_dir / BLOCK_BARRIER_FILE).is_file():
        result = validate_full_block(
            args.bundle_dir,
            args.schema_dir,
            args.expected_frame_sha256,
        )
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
