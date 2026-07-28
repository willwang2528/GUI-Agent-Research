#!/usr/bin/env python3
"""Fail-closed mechanics for the Stage 0F Round-4b finite bounds.

This module is deliberately restricted to synthetic mechanics.  The input
schema fixes ``research_evidence`` and ``confirmatory_outcome_opened`` to
``false``.  A successful run therefore validates the certificate/bounds
machinery only; it cannot be used as a Step-1 result.

The implementation keeps six negative predicates independent at the artifact
layer and applies only the frozen logical implication closure afterward:

    q_B -> q_C and q_env
    q_C and q_env -> q_env_interface
    q_B_deficit[o] -> q_env_deficit[o]

Here an arrow means "a valid negative certificate for the antecedent is also a
valid negative conclusion for the consequent", because the consequent event is
a subset of the antecedent event.  Direct and effective certificates are both
reported so this closure cannot masquerade as a missing independent artifact.
"""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional
from typing import Sequence, Set, Tuple


SCHEMA_VERSION = "stage0f-bounds-v0.6.0-draft"
CANONICALIZATION = "stage0f-bounds-canonical-json-v1"
VALIDATOR_ID = "stage0f-bounds-certificate-validator"
VALIDATOR_VERSION = "0.1.0"
VERIFIER_REGISTRY_RELATIVE_PATH = (
    "schemas/stage0f_bounds_verifier_registry.json"
)
ACTION_SEMANTIC_HELPER_RELATIVE_PATH = (
    "tools/stage0f_action_semantics.py"
)
ACTION_SEMANTIC_HELPER_HASH = (
    "ae5eb06fbf567289e0cec73c07bd48db32758234d2fcd1c3b60c8523c98c90bf"
)
ACTION_SEMANTIC_CONTRACT_RELATIVE_PATH = (
    "schemas/stage0f_bounds_action_semantics.json"
)
ACTION_SEMANTIC_CONTRACT_HASH = (
    "9c5d9c732f4b9edacee6ba474d5e2fa72c2b6f9af9b51fc8646bfde772570258"
)
FROZEN_VERIFIER_REGISTRY_HASH = (
    "47a6c19f6bbf5e455764652b597b715f2ac61a18ce613b376fcec530c401bc18"
)

PREDICATES = (
    "q_B",
    "q_C",
    "q_env",
    "q_env_interface",
    "q_B_deficit",
    "q_env_deficit",
)
NON_DEFICIT_PREDICATES = PREDICATES[:4]
DEFICIT_PREDICATES = PREDICATES[4:]

FROZEN_MODEL_FAMILY_CODEBOOK: Mapping[str, str] = {
    "Config-A": "Anthropic",
    "Config-B": "Anthropic",
    "Config-C": "Anthropic",
    "Config-D": "OpenAI",
    "Config-E": "MiniMax",
    "Config-F": "Qwen",
}
FROZEN_MODEL_FAMILY_CODEBOOK_HASH = (
    "7ff4dde40737650334ecb47740cf3aed350df75e94c60134c3bf43f1234759e2"
)

PROOF_WHITELIST: Mapping[str, Mapping[str, str]] = {
    "FROZEN_TRANSITION_TABLE_NO_OPPORTUNITY_V1": {
        "disposition": "MECHANICALLY_NO_OPPORTUNITY",
        "result_code": "NO_REACHABLE_DECISION_BOUNDARY",
    },
    "DETERMINISTIC_PREDICATE_EVALUATOR_FALSE_V1": {
        "disposition": "MECHANICALLY_PREDICATE_FALSE",
        "result_code": "TARGET_PREDICATE_FALSE",
    },
    "TYPED_EVENT_GRAMMAR_EXCLUSION_V1": {
        "disposition": "MECHANICALLY_PREDICATE_FALSE",
        "result_code": "TARGET_EVENT_TYPE_IMPOSSIBLE",
    },
}

PROOF_REQUIRED_ROLES: Mapping[str, Sequence[str]] = {
    "DETERMINISTIC_PREDICATE_EVALUATOR_FALSE_V1": (
        "predicate_spec",
        "event_ledger",
    ),
    "FROZEN_TRANSITION_TABLE_NO_OPPORTUNITY_V1": (
        "transition_spec",
        "state",
    ),
    "TYPED_EVENT_GRAMMAR_EXCLUSION_V1": (
        "event_grammar",
        "event_record",
    ),
}

FORBIDDEN_PROOF_MODES = {
    "HUMAN_NOT_FOUND",
    "REFERENCE_AGENT_NOT_FOUND",
    "SEARCH_RETURNED_NONE",
}

JOINT_IMPLICATIONS = (
    ("q_C", "q_B"),
    ("q_env", "q_B"),
    ("q_env_interface", "q_C"),
    ("q_env_interface", "q_env"),
    ("q_B_deficit", "q_B"),
    ("q_env_deficit", "q_env"),
    ("q_env_deficit", "q_B_deficit"),
)

CONSTRAINT_SPEC = {
    "serialization": "stage0f-bounds-constraint-set-v1",
    "joint_bits": list(PREDICATES),
    "joint_implications": [list(edge) for edge in JOINT_IMPLICATIONS],
    "task_certificate": "AND_EXACT_SIX_CONFIGS",
    "ordinal_certificate": "AND_EXACT_FROZEN_ROSTER",
    "missingness": "FAIL_CLOSED_TO_ZERO",
    "empty_obligation": {
        "lower": 0,
        "upper": 1,
        "deficit_negative_certificate": 0,
    },
    "prohibited_operations": [
        "MARGINAL_MULTIPLICATION",
        "MARGINAL_ADDITION",
        "CROSS_EVENT_FIELD_STITCHING",
        "CROSS_LOCATION_WITNESS_STITCHING",
    ],
}

PROOF_WHITELIST_SPEC = {
    "serialization": "stage0f-bounds-proof-whitelist-v1",
    "modes": {
        key: {
            **dict(PROOF_WHITELIST[key]),
            "required_projection_roles": list(
                PROOF_REQUIRED_ROLES[key]
            ),
        }
        for key in sorted(PROOF_WHITELIST)
    },
    "explicitly_forbidden": sorted(FORBIDDEN_PROOF_MODES),
    "verifier_registry_sha256": FROZEN_VERIFIER_REGISTRY_HASH,
}

SCHEMA_FILES: Mapping[str, str] = {
    "common": "stage0f_bounds_common.schema.json",
    "certificate": "stage0f_bounds_certificate.schema.json",
    "joint_completion": "stage0f_bounds_joint_completion.schema.json",
    "input": "stage0f_bounds_input.schema.json",
    "output": "stage0f_bounds_output.schema.json",
}


class DuplicateKeyError(ValueError):
    """A duplicate JSON key makes canonical hashes ambiguous."""


class BoundsSchemaDependencyError(RuntimeError):
    """The pinned Draft-2020-12 validator is unavailable."""


def _reject_duplicate_pairs(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    value: Dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise DuplicateKeyError("duplicate JSON key: %s" % key)
        value[key] = child
    return value


def load_json_no_duplicates(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_pairs,
    )


def canonical_bytes(value: Any) -> bytes:
    """Restricted canonical JSON used by every mechanics hash."""

    def normalize(node: Any, path: str = "$") -> Any:
        if isinstance(node, float):
            raise ValueError("%s: floats are forbidden" % path)
        if isinstance(node, Mapping):
            return {
                key: normalize(child, "%s.%s" % (path, key))
                for key, child in node.items()
            }
        if isinstance(node, (list, tuple)):
            return [
                normalize(child, "%s[%d]" % (path, index))
                for index, child in enumerate(node)
            ]
        return node

    normalized = normalize(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


CONSTRAINT_SET_HASH = canonical_sha256(CONSTRAINT_SPEC)
PROOF_WHITELIST_HASH = canonical_sha256(PROOF_WHITELIST_SPEC)

_AUTHORITY_CONSTRUCTION_TOKEN = object()


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                key: _deep_freeze(child)
                for key, child in value.items()
            }
        )
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(child) for child in value)
    if isinstance(value, set):
        return frozenset(_deep_freeze(child) for child in value)
    return value


def _deep_thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _deep_thaw(child)
            for key, child in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_deep_thaw(child) for child in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_deep_thaw(child) for child in value)
    return value


def _authority_runtime_projection(
    authority: "BoundsAuthority",
) -> Mapping[str, Any]:
    evidence_rows = []
    for pointer_id in sorted(authority.evidence_assets):
        asset = authority.evidence_assets[pointer_id]
        content = asset["content_bytes"]
        evidence_rows.append(
            {
                "pointer_id": pointer_id,
                "pointer": _deep_thaw(asset["pointer"]),
                "content_sha256": hashlib.sha256(content).hexdigest(),
                "content_length": len(content),
            }
        )
    projection_rows = []
    for key, pointer_ids in authority.proof_projections.items():
        projection_rows.append(
            {
                "task_id": key[0],
                "config_id": key[1],
                "location_id": key[2],
                "predicate_id": key[3],
                "target_obligation_id": key[4],
                "proof_mode": key[5],
                "ordered_pointer_ids": list(pointer_ids),
            }
        )
    projection_rows.sort(key=canonical_bytes)
    current_event_refs = [
        canonical_sha256(
            ["stage0f-bounds-derived-event-ref-v1", event]
        )
        for event in authority.events
    ]
    return {
        "binding": _deep_thaw(authority.binding),
        "holdout_manifest": _deep_thaw(authority.holdout_manifest),
        "events": _deep_thaw(authority.events),
        "event_refs": current_event_refs,
        "cached_event_refs": list(authority.event_refs),
        "evidence_assets": evidence_rows,
        "proof_projections": projection_rows,
        "structural_mapping": _deep_thaw(
            authority.structural_mapping
        ),
    }


class BoundsAuthority:
    """Read-only authority created only by validated external loaders."""

    __slots__ = (
        "_binding",
        "_holdout_manifest",
        "_events",
        "_event_refs",
        "_evidence_assets",
        "_proof_projections",
        "_structural_mapping",
        "_runtime_commitment_sha256",
        "_sealed",
    )

    def __init__(
        self,
        token: object,
        binding: Mapping[str, Any],
        holdout_manifest: Mapping[str, Any],
        events: Sequence[Mapping[str, Any]],
        evidence_assets: Mapping[str, Mapping[str, Any]],
        proof_projections: Mapping[
            Tuple[str, str, str, str, Optional[str], str],
            Sequence[str],
        ],
        structural_mapping: Optional[Mapping[str, Any]],
    ) -> None:
        if token is not _AUTHORITY_CONSTRUCTION_TOKEN:
            raise ValueError(
                "BoundsAuthority must come from a trusted loader"
            )
        object.__setattr__(
            self, "_binding", _deep_freeze(copy.deepcopy(dict(binding)))
        )
        object.__setattr__(
            self,
            "_holdout_manifest",
            _deep_freeze(copy.deepcopy(dict(holdout_manifest))),
        )
        frozen_events = _deep_freeze(copy.deepcopy(list(events)))
        object.__setattr__(self, "_events", frozen_events)
        event_refs = [
            canonical_sha256(
                ["stage0f-bounds-derived-event-ref-v1", event]
            )
            for event in frozen_events
        ]
        object.__setattr__(
            self, "_event_refs", _deep_freeze(event_refs)
        )
        object.__setattr__(
            self,
            "_evidence_assets",
            _deep_freeze(
                {
                    key: {
                        **copy.deepcopy(dict(value)),
                        "content_bytes": value["content_bytes"],
                    }
                    for key, value in evidence_assets.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "_proof_projections",
            _deep_freeze(
                {
                    key: tuple(value)
                    for key, value in proof_projections.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "_structural_mapping",
            (
                None
                if structural_mapping is None
                else _deep_freeze(
                    copy.deepcopy(dict(structural_mapping))
                )
            ),
        )
        object.__setattr__(
            self,
            "_runtime_commitment_sha256",
            canonical_sha256(
                [
                    "stage0f-bounds-authority-runtime-v1",
                    _authority_runtime_projection(self),
                ]
            ),
        )
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("BoundsAuthority is recursively immutable")

    @property
    def binding(self) -> Mapping[str, Any]:
        return self._binding

    @property
    def holdout_manifest(self) -> Mapping[str, Any]:
        return self._holdout_manifest

    @property
    def events(self) -> Sequence[Mapping[str, Any]]:
        return self._events

    @property
    def event_refs(self) -> Sequence[str]:
        return self._event_refs

    @property
    def evidence_assets(self) -> Mapping[str, Mapping[str, Any]]:
        return self._evidence_assets

    @property
    def proof_projections(
        self,
    ) -> Mapping[
        Tuple[str, str, str, str, Optional[str], str],
        Sequence[str],
    ]:
        return self._proof_projections

    @property
    def structural_mapping(self) -> Optional[Mapping[str, Any]]:
        return self._structural_mapping

    def assert_runtime_integrity(self) -> None:
        actual = canonical_sha256(
            [
                "stage0f-bounds-authority-runtime-v1",
                _authority_runtime_projection(self),
            ]
        )
        if actual != self._runtime_commitment_sha256:
            raise ValueError(
                "AUTHORITY_RUNTIME_COMMITMENT_MISMATCH"
            )


def _safe_authority_file(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    resolved_root = root.resolve()
    if (
        candidate == resolved_root
        or resolved_root not in candidate.parents
    ):
        raise ValueError("authority path escapes root: %s" % relative_path)
    if not candidate.is_file():
        raise ValueError("authority file missing: %s" % relative_path)
    return candidate


def _read_hashed_authority_json(
    root: Path,
    ref: Mapping[str, Any],
) -> Mapping[str, Any]:
    path = _safe_authority_file(root, ref["relative_path"])
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != ref["sha256"]:
        raise ValueError(
            "authority artifact bytes hash mismatch: %s"
            % ref["relative_path"]
        )
    value = json.loads(
        content.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_pairs,
    )
    if not isinstance(value, dict):
        raise ValueError("authority artifact root must be object")
    return value


def _derive_action_phenotype(
    p_old_status: Any,
    action: Any,
) -> Tuple[str, bool]:
    repository_root = Path(__file__).resolve().parents[1]
    helper_path = repository_root / (
        ACTION_SEMANTIC_HELPER_RELATIVE_PATH
    )
    contract_path = repository_root / (
        ACTION_SEMANTIC_CONTRACT_RELATIVE_PATH
    )
    if hashlib.sha256(helper_path.read_bytes()).hexdigest() != (
        ACTION_SEMANTIC_HELPER_HASH
    ):
        raise ValueError("action semantic helper hash mismatch")
    contract_bytes = contract_path.read_bytes()
    if hashlib.sha256(contract_bytes).hexdigest() != (
        ACTION_SEMANTIC_CONTRACT_HASH
    ):
        raise ValueError("action semantic contract hash mismatch")
    contract = json.loads(
        contract_bytes.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_pairs,
    )
    module_name = "_stage0f_bounds_action_semantics"
    semantic_module = sys.modules.get(module_name)
    if semantic_module is None:
        spec = importlib.util.spec_from_file_location(
            module_name, helper_path
        )
        if spec is None or spec.loader is None:
            raise ValueError("action semantic helper unavailable")
        semantic_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(semantic_module)
        sys.modules[module_name] = semantic_module
    try:
        return semantic_module.derive_action_semantics(
            p_old_status, action, contract
        )
    except ValueError as exc:
        raise ValueError(str(exc)) from exc


def _derive_synthetic_event(
    authority_root: Path,
    source: Mapping[str, Any],
) -> Mapping[str, Any]:
    a0 = _read_hashed_authority_json(authority_root, source["a0_ref"])
    a1 = _read_hashed_authority_json(authority_root, source["a1_ref"])
    interface = _read_hashed_authority_json(
        authority_root, source["interface_ref"]
    )
    event_id = source["adjudicated_event_id"]
    location_id = source["location_id"]
    for name, artifact in (
        ("a0", a0),
        ("a1", a1),
        ("interface", interface),
    ):
        if (
            artifact.get("adjudicated_event_id") != event_id
            or artifact.get("boundary_location_id") != location_id
        ):
            raise ValueError(
                "synthetic authority %s event/location splice" % name
            )

    labels = a0.get("source_labels")
    if labels == ["world_truth_changed"]:
        source_status = "PURE_WORLD_CONFIRMED"
    elif isinstance(labels, list) and "world_truth_changed" in labels:
        source_status = "MIXED_WORLD_CONFIRMED"
    elif labels == ["source_unidentifiable"]:
        source_status = "SOURCE_UNKNOWN"
    elif isinstance(labels, list) and labels:
        source_status = "NON_WORLD_CONFIRMED"
    else:
        source_status = "INVALID_SOURCE_MEASUREMENT"

    derived_phenotype, derived_positive = _derive_action_phenotype(
        a0.get("p_old_status"),
        a1.get("action_assessment"),
    )
    if (
        a1.get("phenotype") != derived_phenotype
        or a1.get("primary_uacf_d_positive") is not derived_positive
    ):
        raise ValueError(
            "A1 summary/action semantic divergence"
        )
    if derived_positive:
        b_status = "CONFIRMED_POSITIVE"
    elif (
        a0.get("p_old_status") == "pre_update_frozen"
        and derived_phenotype == "target_negative"
    ):
        b_status = "CONFIRMED_NEGATIVE"
    else:
        b_status = "POSITIVE_COMPATIBLE"

    interface_value = interface.get("qualifying_interface")
    interface_status = {
        "confirmed": "QUALIFYING_CONFIRMED",
        "compatible": "QUALIFYING_COMPATIBLE",
        "absent": "CONFIRMED_ABSENT",
        "unresolved": "UNRESOLVED",
    }.get(interface_value)
    if interface_status is None:
        raise ValueError("invalid synthetic interface derivation")

    assessments = a1.get("affected_obligation_assessments")
    if not isinstance(assessments, list):
        raise ValueError("missing synthetic obligation assessments")
    confirmed_unmet = sorted(
        {
            item["obligation_id"]
            for item in assessments
            if item.get("behavioral_status") == "violated"
        }
    )
    compatible_unmet = sorted(
        {
            item["obligation_id"]
            for item in assessments
            if item.get("behavioral_status") == "unidentifiable"
        }
    )
    event_key_serialization = "stage0f-canonical-event-key-v1"
    event_key_preimage = [
        source["task_id"],
        source["unit_id"],
        location_id,
        event_id,
    ]
    event_key_sha256 = canonical_sha256(
        [event_key_serialization, *event_key_preimage]
    )
    return {
        "event_key": "Event-" + event_key_sha256,
        "event_key_serialization": event_key_serialization,
        "event_key_preimage": event_key_preimage,
        "event_key_sha256": event_key_sha256,
        "task_id": source["task_id"],
        "config_id": source["config_id"],
        "unit_id": source["unit_id"],
        "location_id": location_id,
        "adjudicated_event_id": event_id,
        "b_status": b_status,
        "same_event_interface_status": interface_status,
        "source_status": source_status,
        "b_unmet_obligation_ids_confirmed": confirmed_unmet,
        "b_unmet_obligation_ids_compatible": compatible_unmet,
        "derivation_refs": {
            "a0_sha256": source["a0_ref"]["sha256"],
            "a1_sha256": source["a1_ref"]["sha256"],
            "interface_sha256": source["interface_ref"]["sha256"],
        },
    }


def _derive_synthetic_primitive_event(
    authority_root: Path,
    source: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Rebuild the verifier input from the same frozen source artifacts.

    The event ledger is evidence only if its primitive rows are an exact
    projection of the independently committed A0/A1/interface artifacts.
    Reading a caller-authored ``events`` array from the ledger itself would
    merely move the target assertion one file away.
    """

    a0 = _read_hashed_authority_json(authority_root, source["a0_ref"])
    a1 = _read_hashed_authority_json(authority_root, source["a1_ref"])
    interface = _read_hashed_authority_json(
        authority_root, source["interface_ref"]
    )
    event_id = source["adjudicated_event_id"]
    location_id = source["location_id"]
    for name, artifact in (
        ("a0", a0),
        ("a1", a1),
        ("interface", interface),
    ):
        if (
            artifact.get("adjudicated_event_id") != event_id
            or artifact.get("boundary_location_id") != location_id
        ):
            raise ValueError(
                "synthetic primitive %s event/location splice" % name
            )
    primitive = {
        "adjudicated_event_id": event_id,
        "p_old_status": a0.get("p_old_status"),
        "source_labels": a0.get("source_labels"),
        "action_assessment": a1.get("action_assessment"),
        "candidate_interface_status": {
            "confirmed": "QUALIFYING_CONFIRMED",
            "compatible": "QUALIFYING_COMPATIBLE",
            "absent": "CONFIRMED_ABSENT",
            "unresolved": "UNRESOLVED",
        }.get(interface.get("qualifying_interface")),
        "obligation_assessments": a1.get(
            "affected_obligation_assessments"
        ),
    }
    if (
        primitive["p_old_status"]
        not in {"pre_update_frozen", "old_state_hypothesized"}
        or not isinstance(primitive["source_labels"], list)
        or not isinstance(primitive["action_assessment"], dict)
        or primitive["candidate_interface_status"] is None
        or not isinstance(primitive["obligation_assessments"], list)
    ):
        raise ValueError("synthetic primitive event is incomplete")
    return primitive


def load_synthetic_bounds_authority(
    authority_dir: Path,
    expected_authority_sha256: str,
) -> BoundsAuthority:
    """Load an independently hashed synthetic authority fixture."""

    authority_path = authority_dir / "authority.json"
    authority = load_json_no_duplicates(authority_path)
    if not isinstance(authority, dict):
        raise ValueError("authority root must be object")
    actual_authority_sha256 = canonical_sha256(authority)
    if actual_authority_sha256 != expected_authority_sha256:
        raise ValueError("external synthetic authority hash mismatch")
    if (
        authority.get("artifact_type")
        != "stage0f_bounds_trusted_authority"
        or authority.get("authority_kind")
        != "SYNTHETIC_TRUSTED_FIXTURE"
        or authority.get("schema_version") != SCHEMA_VERSION
    ):
        raise ValueError("unsupported synthetic authority")

    holdout_manifest = authority["holdout_manifest"]
    if holdout_manifest_sha256(holdout_manifest) != holdout_manifest.get(
        "manifest_sha256"
    ):
        raise ValueError("authority holdout manifest hash mismatch")
    event_sources = authority.get("event_sources", [])
    if not isinstance(event_sources, list):
        raise ValueError("synthetic event_sources must be an array")
    events = []
    primitive_events_by_location: Dict[
        Tuple[str, str, str], List[Mapping[str, Any]]
    ] = {}
    seen_source_identities: Set[Tuple[str, str, str, str]] = set()
    for source in event_sources:
        if not isinstance(source, dict):
            raise ValueError("synthetic event source must be an object")
        identity = (
            source.get("task_id"),
            source.get("config_id"),
            source.get("location_id"),
            source.get("adjudicated_event_id"),
        )
        if identity in seen_source_identities:
            raise ValueError("duplicate synthetic event source identity")
        seen_source_identities.add(identity)
        event = _derive_synthetic_event(authority_dir, source)
        primitive = _derive_synthetic_primitive_event(
            authority_dir, source
        )
        events.append(event)
        primitive_events_by_location.setdefault(
            (
                source["task_id"],
                source["config_id"],
                source["location_id"],
            ),
            [],
        ).append(primitive)

    binding_seed = authority["full_block_binding"]
    ledger_authority_binding = {
        key: binding_seed[key]
        for key in (
            "frame_sha256",
            "manifest_sha256",
            "a0_barrier_sha256",
            "a1_barrier_sha256",
            "stream_roots_sha256",
            "full_block_bundle_sha256",
        )
    }

    evidence_assets: Dict[str, Mapping[str, Any]] = {}
    for asset in authority.get("evidence_assets", []):
        pointer = asset["pointer"]
        pointer_id = pointer["pointer_id"]
        if pointer_id in evidence_assets:
            raise ValueError("duplicate authority evidence pointer")
        path = _safe_authority_file(
            authority_dir, asset["relative_path"]
        )
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != pointer["content_sha256"]:
            raise ValueError("authority evidence bytes hash mismatch")
        if pointer.get("projection_role") == "event_ledger":
            try:
                ledger = json.loads(
                    content.decode("utf-8"),
                    object_pairs_hook=_reject_duplicate_pairs,
                )
            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
                DuplicateKeyError,
            ) as exc:
                raise ValueError(
                    "authority event ledger bytes are invalid"
                ) from exc
            if not isinstance(ledger, dict):
                raise ValueError(
                    "authority event ledger root must be object"
                )
            location_key = (
                ledger.get("task_id"),
                ledger.get("config_id"),
                ledger.get("location_id"),
            )
            expected_ledger = {
                "artifact_type": "stage0f_complete_event_ledger",
                "coverage": "EXACT_LOCATION_EVENT_SET",
                "authority_binding": ledger_authority_binding,
                "task_id": location_key[0],
                "config_id": location_key[1],
                "location_id": location_key[2],
                "events": primitive_events_by_location.get(
                    location_key, []
                ),
            }
            if ledger != expected_ledger:
                raise ValueError(
                    "event ledger is not exact projection of frozen "
                    "A0/A1/interface sources"
                )
        evidence_assets[pointer_id] = {
            "pointer": copy.deepcopy(pointer),
            "content_bytes": content,
        }

    projections: Dict[
        Tuple[str, str, str, str, Optional[str], str],
        Sequence[str],
    ] = {}
    for projection in authority.get("proof_projections", []):
        key = (
            projection["task_id"],
            projection["config_id"],
            projection["location_id"],
            projection["predicate_id"],
            projection.get("target_obligation_id"),
            projection["proof_mode"],
        )
        if key in projections:
            raise ValueError("duplicate authority proof projection")
        pointer_ids = projection["ordered_pointer_ids"]
        if any(pointer_id not in evidence_assets for pointer_id in pointer_ids):
            raise ValueError("projection points outside evidence authority")
        projections[key] = tuple(pointer_ids)

    structural_mapping = authority.get("structural_mapping")
    if structural_mapping is not None:
        if not isinstance(structural_mapping, dict):
            raise ValueError(
                "synthetic structural mapping must be an object"
            )
        config_rows = structural_mapping.get(
            "config_mappings", []
        )
        config_mapping = {
            row.get("config_id"): row.get("model_family")
            for row in config_rows
            if isinstance(row, dict)
        }
        if (
            len(config_mapping) != len(config_rows)
            or config_mapping != FROZEN_MODEL_FAMILY_CODEBOOK
            or structural_mapping.get(
                "model_family_codebook_sha256"
            )
            != FROZEN_MODEL_FAMILY_CODEBOOK_HASH
        ):
            raise ValueError(
                "frozen model-family codebook mismatch"
            )
    proof_projection_sha256 = canonical_sha256(
        [
            "stage0f-bounds-proof-projection-v1",
            authority.get("proof_projections", []),
        ]
    )
    structural_mapping_sha256 = canonical_sha256(
        [
            "stage0f-bounds-structural-mapping-v1",
            structural_mapping,
        ]
    )
    binding = {
        "authority_kind": "SYNTHETIC_TRUSTED_FIXTURE",
        "authority_sha256": actual_authority_sha256,
        "frame_sha256": binding_seed["frame_sha256"],
        "manifest_sha256": binding_seed["manifest_sha256"],
        "a0_barrier_sha256": binding_seed["a0_barrier_sha256"],
        "a1_barrier_sha256": binding_seed["a1_barrier_sha256"],
        "stream_roots_sha256": binding_seed["stream_roots_sha256"],
        "full_block_validator_sha256": binding_seed[
            "full_block_validator_sha256"
        ],
        "full_block_bundle_sha256": binding_seed[
            "full_block_bundle_sha256"
        ],
        "proof_projection_sha256": proof_projection_sha256,
        "structural_mapping_sha256": structural_mapping_sha256,
        "verifier_registry_sha256": FROZEN_VERIFIER_REGISTRY_HASH,
    }
    return BoundsAuthority(
        _AUTHORITY_CONSTRUCTION_TOKEN,
        binding,
        holdout_manifest,
        events,
        evidence_assets,
        projections,
        structural_mapping,
    )


def pointer_sort_key(pointer: Mapping[str, Any]) -> bytes:
    return canonical_bytes(pointer)


def roster_projection(config: Mapping[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "observation_ordinal": location["observation_ordinal"],
            "location_id": location["location_id"],
        }
        for location in config["ordinal_locations"]
    ]


def unit_ordinal_roster_sha256(config: Mapping[str, Any]) -> str:
    return canonical_sha256(
        ["stage0f-bounds-unit-ordinal-roster-v1", roster_projection(config)]
    )


def trajectory_hash_chain_root(config: Mapping[str, Any]) -> str:
    previous = "0" * 64
    for location in config["ordinal_locations"]:
        record = [
            "stage0f-bounds-trajectory-chain-node-v1",
            previous,
            config["unit_id"],
            config["config_id"],
            location["observation_ordinal"],
            location["location_id"],
            sorted(location["evidence_pointers"], key=pointer_sort_key),
        ]
        previous = canonical_sha256(record)
    return previous


def config_roster_ids_sha256(config_ids: Sequence[str]) -> str:
    return canonical_sha256(
        ["stage0f-bounds-exact-six-config-roster-v1", list(config_ids)]
    )


def task_manifest_projection(task: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "task_id": task["task_id"],
        "configs": [
            {
                "config_id": config["config_id"],
                "unit_id": config["unit_id"],
                "obligation_status": config["obligation_status"],
                "applicable_obligation_ids": config[
                    "applicable_obligation_ids"
                ],
                "ordinal_locations": config["ordinal_locations"],
                "unit_ordinal_roster_sha256": config[
                    "unit_ordinal_roster_sha256"
                ],
                "trajectory_hash_chain_root": config[
                    "trajectory_hash_chain_root"
                ],
            }
            for config in task["configs"]
        ],
    }


def task_manifest_sha256(task: Mapping[str, Any]) -> str:
    return canonical_sha256(
        [
            "stage0f-bounds-task-manifest-v1",
            task_manifest_projection(task),
        ]
    )


def holdout_manifest_projection(manifest: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "manifest_id": manifest["manifest_id"],
        "task_roster_sha256": manifest["task_roster_sha256"],
        "exact_six_config_ids": manifest["exact_six_config_ids"],
        "exact_six_config_ids_sha256": manifest[
            "exact_six_config_ids_sha256"
        ],
        "tasks": manifest["tasks"],
    }


def holdout_manifest_sha256(manifest: Mapping[str, Any]) -> str:
    return canonical_sha256(
        [
            "stage0f-bounds-holdout-manifest-v1",
            holdout_manifest_projection(manifest),
        ]
    )


def direct_evidence_projection_sha256(
    pointers: Sequence[Mapping[str, Any]],
) -> str:
    return canonical_sha256(
        [
            "stage0f-bounds-direct-evidence-projection-v1",
            list(pointers),
        ]
    )


def verifier_output_hash(output: Mapping[str, Any]) -> str:
    return canonical_sha256(
        ["stage0f-bounds-verifier-output-v1", output]
    )


def certificate_validator_output_hash(
    artifact: Mapping[str, Any],
) -> str:
    projection = {
        key: value
        for key, value in artifact.items()
        if key != "validator_output_hash"
    }
    return canonical_sha256(
        ["stage0f-bounds-validator-output-v1", projection]
    )


def _load_schema_bundle(schema_dir: Path) -> Dict[str, Any]:
    return {
        name: load_json_no_duplicates(schema_dir / filename)
        for name, filename in SCHEMA_FILES.items()
    }


def validate_with_schema(
    instance: Any,
    schema_name: str,
    schema_dir: Path,
) -> List[str]:
    """Validate with the pinned Draft-2020-12 implementation."""

    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
    except ImportError as exc:
        raise BoundsSchemaDependencyError(
            "jsonschema/referencing is required; use requirements-stage0f.txt"
        ) from exc

    schemas = _load_schema_bundle(schema_dir)
    registry = Registry()
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(
            schema["$id"],
            Resource.from_contents(schema),
        )
    validator = Draft202012Validator(
        schemas[schema_name],
        registry=registry,
    )
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    return [
        "%s: %s"
        % (
            "$"
            + "".join(
                "[%d]" % part if isinstance(part, int) else ".%s" % part
                for part in error.absolute_path
            ),
            error.message,
        )
        for error in errors
    ]


def _issue(
    issues: List[Dict[str, str]],
    severity: str,
    code: str,
    path: str,
) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "path": path,
        }
    )


def _fraction_json(value: Fraction) -> Dict[str, Any]:
    scaled = value.numerator * 1000000 // value.denominator
    whole, fractional = divmod(scaled, 1000000)
    decimal = (
        str(whole)
        if fractional == 0
        else ("%d.%06d" % (whole, fractional)).rstrip("0")
    )
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": decimal,
    }


def _validate_manifest(
    packet: Mapping[str, Any],
    issues: List[Dict[str, str]],
) -> Tuple[
    Dict[str, Mapping[str, Any]],
    Dict[Tuple[str, str], Mapping[str, Any]],
    Dict[Tuple[str, str, str], Mapping[str, Any]],
]:
    """Validate the finite task/config/ordinal universe and all its hashes."""

    tasks_by_id: Dict[str, Mapping[str, Any]] = {}
    configs_by_key: Dict[Tuple[str, str], Mapping[str, Any]] = {}
    locations_by_key: Dict[
        Tuple[str, str, str], Mapping[str, Any]
    ] = {}
    manifest = packet.get("holdout_manifest", {})
    config_ids = manifest.get("exact_six_config_ids", [])

    if len(config_ids) != 6 or len(set(config_ids)) != 6:
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "MANIFEST_EXACT_SIX_CONFIGS_REQUIRED",
            "$.holdout_manifest.exact_six_config_ids",
        )
    if config_roster_ids_sha256(config_ids) != manifest.get(
        "exact_six_config_ids_sha256"
    ):
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "MANIFEST_CONFIG_ROSTER_HASH_MISMATCH",
            "$.holdout_manifest.exact_six_config_ids_sha256",
        )

    task_ids = [task.get("task_id") for task in manifest.get("tasks", [])]
    if len(task_ids) != len(set(task_ids)):
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "DUPLICATE_TASK_ID",
            "$.holdout_manifest.tasks",
        )
    expected_task_roster_hash = canonical_sha256(
        ["stage0f-bounds-task-roster-v1", task_ids]
    )
    if expected_task_roster_hash != manifest.get("task_roster_sha256"):
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "TASK_ROSTER_HASH_MISMATCH",
            "$.holdout_manifest.task_roster_sha256",
        )

    for task_index, task in enumerate(manifest.get("tasks", [])):
        task_id = task.get("task_id")
        path = "$.holdout_manifest.tasks[%d]" % task_index
        if not isinstance(task_id, str):
            continue
        tasks_by_id[task_id] = task
        configs = task.get("configs", [])
        actual_config_ids = [
            config.get("config_id") for config in configs
        ]
        if (
            len(configs) != 6
            or len(set(actual_config_ids)) != 6
            or actual_config_ids != config_ids
        ):
            _issue(
                issues,
                "MEASUREMENT_INVALID",
                "TASK_CONFIG_ROSTER_NOT_EXACT_SIX",
                path + ".configs",
            )
        for config_index, config in enumerate(configs):
            config_id = config.get("config_id")
            config_path = "%s.configs[%d]" % (path, config_index)
            if not isinstance(config_id, str):
                continue
            key = (task_id, config_id)
            if key in configs_by_key:
                _issue(
                    issues,
                    "MEASUREMENT_INVALID",
                    "DUPLICATE_TASK_CONFIG",
                    config_path,
                )
            configs_by_key[key] = config

            obligations = config.get("applicable_obligation_ids", [])
            obligation_status = config.get("obligation_status")
            if obligation_status == "FROZEN_NONEMPTY" and not obligations:
                _issue(
                    issues,
                    "MEASUREMENT_INVALID",
                    "FROZEN_OBLIGATION_SET_EMPTY",
                    config_path + ".applicable_obligation_ids",
                )
            if (
                obligation_status == "MISSING_OR_EMPTY"
                and obligations
            ):
                _issue(
                    issues,
                    "MEASUREMENT_INVALID",
                    "MISSING_OBLIGATION_SET_NOT_EMPTY",
                    config_path + ".applicable_obligation_ids",
                )

            ordinal_locations = config.get("ordinal_locations", [])
            ordinals = [
                location.get("observation_ordinal")
                for location in ordinal_locations
            ]
            location_ids = [
                location.get("location_id")
                for location in ordinal_locations
            ]
            if (
                not ordinal_locations
                or len(ordinals) != len(set(ordinals))
                or len(location_ids) != len(set(location_ids))
                or ordinals != sorted(ordinals)
            ):
                _issue(
                    issues,
                    "MEASUREMENT_INVALID",
                    "ORDINAL_ROSTER_NOT_FINITE_UNIQUE_SORTED",
                    config_path + ".ordinal_locations",
                )
            for location in ordinal_locations:
                location_id = location.get("location_id")
                if isinstance(location_id, str):
                    locations_by_key[
                        (task_id, config_id, location_id)
                    ] = location
            if unit_ordinal_roster_sha256(config) != config.get(
                "unit_ordinal_roster_sha256"
            ):
                _issue(
                    issues,
                    "MEASUREMENT_INVALID",
                    "UNIT_ORDINAL_ROSTER_HASH_MISMATCH",
                    config_path + ".unit_ordinal_roster_sha256",
                )
            if trajectory_hash_chain_root(config) != config.get(
                "trajectory_hash_chain_root"
            ):
                _issue(
                    issues,
                    "MEASUREMENT_INVALID",
                    "TRAJECTORY_HASH_CHAIN_ROOT_MISMATCH",
                    config_path + ".trajectory_hash_chain_root",
                )

        try:
            expected_task_hash = task_manifest_sha256(task)
        except (KeyError, TypeError, ValueError):
            expected_task_hash = None
        if expected_task_hash != task.get("task_manifest_sha256"):
            _issue(
                issues,
                "MEASUREMENT_INVALID",
                "TASK_MANIFEST_HASH_MISMATCH",
                path + ".task_manifest_sha256",
            )

    try:
        expected_manifest_hash = holdout_manifest_sha256(manifest)
    except (KeyError, TypeError, ValueError):
        expected_manifest_hash = None
    if expected_manifest_hash != manifest.get("manifest_sha256"):
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "HOLDOUT_MANIFEST_HASH_MISMATCH",
            "$.holdout_manifest.manifest_sha256",
        )

    return tasks_by_id, configs_by_key, locations_by_key


def _validate_events(
    packet: Mapping[str, Any],
    configs_by_key: Mapping[
        Tuple[str, str], Mapping[str, Any]
    ],
    locations_by_key: Mapping[
        Tuple[str, str, str], Mapping[str, Any]
    ],
    issues: List[Dict[str, str]],
) -> List[Mapping[str, Any]]:
    events: List[Mapping[str, Any]] = []
    seen_event_keys: Set[str] = set()
    for index, event in enumerate(packet.get("observed_joint_events", [])):
        path = "$.observed_joint_events[%d]" % index
        event_key = event.get("event_key")
        expected_preimage = [
            event.get("task_id"),
            event.get("unit_id"),
            event.get("location_id"),
            event.get("adjudicated_event_id"),
        ]
        expected_key_sha256 = canonical_sha256(
            ["stage0f-canonical-event-key-v1", *expected_preimage]
        )
        if (
            event.get("event_key_serialization")
            != "stage0f-canonical-event-key-v1"
            or _deep_thaw(event.get("event_key_preimage"))
            != expected_preimage
            or event.get("event_key_sha256")
            != expected_key_sha256
            or event_key != "Event-" + expected_key_sha256
        ):
            _issue(
                issues,
                "MEASUREMENT_INVALID",
                "CANONICAL_EVENT_KEY_DERIVATION_MISMATCH",
                path + ".event_key",
            )
            continue
        if event_key in seen_event_keys:
            _issue(
                issues,
                "MEASUREMENT_INVALID",
                "DUPLICATE_EVENT_KEY",
                path + ".event_key",
            )
        if isinstance(event_key, str):
            seen_event_keys.add(event_key)
        task_id = event.get("task_id")
        config_id = event.get("config_id")
        unit_id = event.get("unit_id")
        location_id = event.get("location_id")
        config = configs_by_key.get((task_id, config_id))
        location = locations_by_key.get(
            (task_id, config_id, location_id)
        )
        if config is None or location is None:
            _issue(
                issues,
                "MEASUREMENT_INVALID",
                "EVENT_OUTSIDE_FROZEN_LOCATION_UNIVERSE",
                path,
            )
            continue
        if unit_id != config.get("unit_id"):
            _issue(
                issues,
                "MEASUREMENT_INVALID",
                "EVENT_UNIT_MISMATCH",
                path + ".unit_id",
            )
            continue
        obligations = set(config.get("applicable_obligation_ids", []))
        event_obligations = set(
            event.get("b_unmet_obligation_ids_confirmed", [])
        ) | set(event.get("b_unmet_obligation_ids_compatible", []))
        if not event_obligations.issubset(obligations):
            _issue(
                issues,
                "MEASUREMENT_INVALID",
                "EVENT_OBLIGATION_OUTSIDE_FROZEN_SET",
                path,
            )
            continue
        events.append(event)
    return events


def _certificate_matrix_template(
    tasks_by_id: Mapping[str, Mapping[str, Any]],
) -> Tuple[
    Dict[Tuple[str, str, str], int],
    Dict[Tuple[str, str, str, str], int],
]:
    direct_non: Dict[Tuple[str, str, str], int] = {}
    direct_def: Dict[Tuple[str, str, str, str], int] = {}
    for task_id, task in tasks_by_id.items():
        for config in task["configs"]:
            config_id = config["config_id"]
            for predicate_id in NON_DEFICIT_PREDICATES:
                direct_non[(task_id, predicate_id, config_id)] = 0
            for predicate_id in DEFICIT_PREDICATES:
                for obligation_id in config[
                    "applicable_obligation_ids"
                ]:
                    direct_def[
                        (
                            task_id,
                            predicate_id,
                            config_id,
                            obligation_id,
                        )
                    ] = 0
    return direct_non, direct_def


def _proof_key(
    proof: Mapping[str, Any],
) -> Tuple[Any, Any, Any]:
    return (
        proof.get("observation_ordinal"),
        proof.get("location_id"),
        proof.get("target_obligation_id"),
    )


def _load_frozen_verifier_registry(
    repository_root: Path,
) -> Tuple[Mapping[str, Any], Path]:
    registry_path = repository_root / VERIFIER_REGISTRY_RELATIVE_PATH
    registry = load_json_no_duplicates(registry_path)
    if canonical_sha256(registry) != FROZEN_VERIFIER_REGISTRY_HASH:
        raise ValueError("frozen verifier registry hash mismatch")
    executable_path = _safe_authority_file(
        repository_root,
        registry["executable_relative_path"],
    )
    executable_hash = hashlib.sha256(
        executable_path.read_bytes()
    ).hexdigest()
    if executable_hash != registry.get("executable_sha256"):
        raise ValueError("frozen verifier executable hash mismatch")
    helper_path = _safe_authority_file(
        repository_root,
        registry["semantic_helper_relative_path"],
    )
    if (
        hashlib.sha256(helper_path.read_bytes()).hexdigest()
        != registry.get("semantic_helper_sha256")
        or registry.get("semantic_helper_relative_path")
        != ACTION_SEMANTIC_HELPER_RELATIVE_PATH
        or registry.get("semantic_helper_sha256")
        != ACTION_SEMANTIC_HELPER_HASH
    ):
        raise ValueError("action semantic helper registry mismatch")
    contract_path = _safe_authority_file(
        repository_root,
        registry["semantic_contract_relative_path"],
    )
    if (
        hashlib.sha256(contract_path.read_bytes()).hexdigest()
        != registry.get("semantic_contract_sha256")
        or registry.get("semantic_contract_relative_path")
        != ACTION_SEMANTIC_CONTRACT_RELATIVE_PATH
        or registry.get("semantic_contract_sha256")
        != ACTION_SEMANTIC_CONTRACT_HASH
    ):
        raise ValueError("action semantic contract registry mismatch")
    if set(registry.get("modes", {})) != set(PROOF_WHITELIST):
        raise ValueError("frozen verifier mode roster mismatch")
    for mode, mode_record in registry["modes"].items():
        projection = {
            key: value
            for key, value in mode_record.items()
            if key != "config_sha256"
        }
        expected_config_hash = canonical_sha256(
            [
                "stage0f-bounds-verifier-mode-config-v1",
                projection,
            ]
        )
        if expected_config_hash != mode_record.get("config_sha256"):
            raise ValueError("verifier mode config hash mismatch")
        if projection["required_projection_roles"] != list(
            PROOF_REQUIRED_ROLES[mode]
        ):
            raise ValueError("verifier mode role projection mismatch")
        if (
            projection["result_code"]
            != PROOF_WHITELIST[mode]["result_code"]
            or projection["disposition"]
            != PROOF_WHITELIST[mode]["disposition"]
        ):
            raise ValueError("verifier mode result mapping mismatch")
    return registry, executable_path


def _run_frozen_verifier(
    proof: Mapping[str, Any],
    predicate_id: str,
    target_obligation_id: Optional[str],
    task_id: str,
    config_id: str,
    authority: BoundsAuthority,
    repository_root: Path,
) -> Tuple[Optional[Mapping[str, Any]], str]:
    proof_mode = proof.get("proof_mode")
    registry, executable_path = _load_frozen_verifier_registry(
        repository_root
    )
    mode_record = registry["modes"].get(proof_mode)
    if mode_record is None:
        return None, "PROOF_MODE_NOT_WHITELISTED"
    if mode_record.get("enabled") is not True:
        return None, "PROOF_MODE_DISABLED_UNSOUND_SEMANTICS"
    projection_key = (
        task_id,
        config_id,
        proof.get("location_id"),
        predicate_id,
        target_obligation_id,
        proof_mode,
    )
    required_pointer_ids = authority.proof_projections.get(
        projection_key
    )
    if required_pointer_ids is None:
        return None, "AUTHORITY_PROOF_PROJECTION_MISSING"
    submitted_pointers = proof.get("direct_evidence_pointers", [])
    submitted_pointer_ids = [
        pointer.get("pointer_id") for pointer in submitted_pointers
    ]
    if submitted_pointer_ids != list(required_pointer_ids):
        return None, "PROOF_POINTER_PROJECTION_NOT_EXACT"
    if [
        pointer.get("projection_role")
        for pointer in submitted_pointers
    ] != mode_record["required_projection_roles"]:
        return None, "PROOF_POINTER_ROLE_ORDER_MISMATCH"
    if [
        pointer.get("sequence_ordinal")
        for pointer in submitted_pointers
    ] != list(range(len(submitted_pointers))):
        return None, "PROOF_POINTER_SEQUENCE_MISMATCH"

    execution_evidence: List[Dict[str, Any]] = []
    for pointer in submitted_pointers:
        asset = authority.evidence_assets.get(pointer["pointer_id"])
        if asset is None or asset["pointer"] != pointer:
            return None, "PROOF_POINTER_NOT_AUTHORITY_EXACT"
        content = asset["content_bytes"]
        if hashlib.sha256(content).hexdigest() != pointer[
            "content_sha256"
        ]:
            return None, "PROOF_EVIDENCE_BYTES_HASH_MISMATCH"
        execution_evidence.append(
            {
                **copy.deepcopy(pointer),
                "content_base64": base64.b64encode(content).decode(
                    "ascii"
                ),
            }
        )
    request = {
        "serialization": "stage0f-bounds-verifier-request-v1",
        "proof_mode": proof_mode,
        "predicate_id": predicate_id,
        "target_obligation_id": target_obligation_id,
        "semantic_contract_sha256": registry[
            "semantic_contract_sha256"
        ],
        "authority_binding": {
            "frame_sha256": authority.binding["frame_sha256"],
            "manifest_sha256": authority.binding["manifest_sha256"],
            "a0_barrier_sha256": authority.binding[
                "a0_barrier_sha256"
            ],
            "a1_barrier_sha256": authority.binding[
                "a1_barrier_sha256"
            ],
            "stream_roots_sha256": authority.binding[
                "stream_roots_sha256"
            ],
            "full_block_bundle_sha256": authority.binding[
                "full_block_bundle_sha256"
            ],
        },
        "evidence": execution_evidence,
    }
    try:
        completed = subprocess.run(
            [sys.executable, str(executable_path)],
            input=canonical_bytes(request),
            capture_output=True,
            check=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return None, "FROZEN_VERIFIER_EXECUTION_TIMEOUT"
    if completed.returncode != 0:
        return None, "FROZEN_VERIFIER_EXECUTION_FAILED"
    try:
        derived = json.loads(
            completed.stdout.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        DuplicateKeyError,
    ):
        return None, "FROZEN_VERIFIER_OUTPUT_INVALID"
    expected_derived = {
        "serialization": "stage0f-bounds-verifier-execution-v1",
        "predicate_id": predicate_id,
        "target_obligation_id": target_obligation_id,
        "result_code": mode_record["result_code"],
        "disposition": mode_record["disposition"],
        "consumed_pointer_ids": submitted_pointer_ids,
        "consumed_content_sha256s": [
            pointer["content_sha256"]
            for pointer in submitted_pointers
        ],
        "execution_status": "EXECUTED_AND_DERIVED",
    }
    if derived != expected_derived:
        return None, "FROZEN_VERIFIER_OUTPUT_SEMANTICS_MISMATCH"
    executable_hash = registry["executable_sha256"]
    config_hash = mode_record["config_sha256"]
    actual_output = {
        "serialization": "stage0f-bounds-proof-output-v1",
        "predicate_id": derived.get("predicate_id"),
        "target_obligation_id": derived.get(
            "target_obligation_id"
        ),
        "result_code": derived.get("result_code"),
        "disposition": derived.get("disposition"),
        "direct_evidence_projection_sha256": (
            direct_evidence_projection_sha256(submitted_pointers)
        ),
        "verifier_executable_sha256": executable_hash,
        "verifier_config_sha256": config_hash,
        "consumed_pointer_ids": derived.get(
            "consumed_pointer_ids"
        ),
        "consumed_content_sha256s": derived.get(
            "consumed_content_sha256s"
        ),
        "execution_status": derived.get("execution_status"),
    }
    if proof.get("verifier_id") != registry["verifier_id"]:
        return None, "VERIFIER_ID_MISMATCH"
    if proof.get("verifier_version") != registry["verifier_version"]:
        return None, "VERIFIER_VERSION_MISMATCH"
    if proof.get("verifier_executable_sha256") != executable_hash:
        return None, "VERIFIER_EXECUTABLE_HASH_MISMATCH"
    if proof.get("verifier_config_sha256") != config_hash:
        return None, "VERIFIER_CONFIG_HASH_MISMATCH"
    return actual_output, "VALID"


def _proof_is_valid(
    proof: Mapping[str, Any],
    predicate_id: str,
    target_obligation_id: Optional[str],
    frozen_location: Mapping[str, Any],
    task_id: str,
    config_id: str,
    authority: BoundsAuthority,
    repository_root: Path,
) -> Tuple[bool, str]:
    proof_mode = proof.get("proof_mode")
    if proof_mode in FORBIDDEN_PROOF_MODES:
        return False, "FORBIDDEN_NOT_FOUND_PROOF_MODE"
    mode_spec = PROOF_WHITELIST.get(proof_mode)
    if mode_spec is None:
        return False, "PROOF_MODE_NOT_WHITELISTED"
    if proof.get("disposition") != mode_spec["disposition"]:
        return False, "PROOF_DISPOSITION_MODE_MISMATCH"
    if proof.get("target_obligation_id") != target_obligation_id:
        return False, "PROOF_TARGET_OBLIGATION_MISMATCH"
    if proof.get("observation_ordinal") != frozen_location.get(
        "observation_ordinal"
    ):
        return False, "PROOF_ORDINAL_MISMATCH"
    if proof.get("location_id") != frozen_location.get("location_id"):
        return False, "PROOF_LOCATION_MISMATCH"

    try:
        actual_output, execution_code = _run_frozen_verifier(
            proof,
            predicate_id,
            target_obligation_id,
            task_id,
            config_id,
            authority,
            repository_root,
        )
    except (OSError, ValueError, KeyError):
        return False, "FROZEN_VERIFIER_REGISTRY_OR_IO_FAILURE"
    if actual_output is None:
        return False, execution_code
    output = proof.get("verifier_output", {})
    if output != actual_output:
        return False, "VERIFIER_OUTPUT_NOT_EXECUTION_DERIVED"
    if proof.get("verifier_output_hash") != verifier_output_hash(
        actual_output
    ):
        return False, "VERIFIER_OUTPUT_HASH_MISMATCH"
    return True, "VALID"


def _validate_certificates(
    packet: Mapping[str, Any],
    tasks_by_id: Mapping[str, Mapping[str, Any]],
    events: Sequence[Mapping[str, Any]],
    schema_dir: Path,
    authority: BoundsAuthority,
    repository_root: Path,
    issues: List[Dict[str, str]],
) -> Tuple[
    Dict[Tuple[str, str, str], int],
    Dict[Tuple[str, str, str, str], int],
    Dict[Tuple[str, str], Dict[str, Any]],
]:
    direct_non, direct_def = _certificate_matrix_template(tasks_by_id)
    audit_state: Dict[Tuple[str, str], Dict[str, Any]] = {
        (task_id, predicate_id): {
            "artifact_present": False,
            "issue_codes": set(),
        }
        for task_id in tasks_by_id
        for predicate_id in PREDICATES
    }
    grouped: Dict[Tuple[str, str], List[Tuple[int, Mapping[str, Any]]]] = {}
    for artifact_index, artifact in enumerate(
        packet.get("negative_certificate_artifacts", [])
    ):
        task_id = artifact.get("task_id")
        predicate_id = artifact.get("predicate_id")
        key = (task_id, predicate_id)
        grouped.setdefault(key, []).append((artifact_index, artifact))
        if key in audit_state:
            audit_state[key]["artifact_present"] = True

    for key, entries in grouped.items():
        task_id, predicate_id = key
        if key not in audit_state:
            for artifact_index, _ in entries:
                _issue(
                    issues,
                    "CERTIFICATE_FAIL_CLOSED",
                    "CERTIFICATE_TARGET_OUTSIDE_MANIFEST",
                    "$.negative_certificate_artifacts[%d]"
                    % artifact_index,
                )
            continue
        state = audit_state[key]
        if len(entries) != 1:
            state["issue_codes"].add("DUPLICATE_CERTIFICATE_ARTIFACT")
            for artifact_index, _ in entries:
                _issue(
                    issues,
                    "CERTIFICATE_FAIL_CLOSED",
                    "DUPLICATE_CERTIFICATE_ARTIFACT",
                    "$.negative_certificate_artifacts[%d]"
                    % artifact_index,
                )
            continue

        artifact_index, artifact = entries[0]
        artifact_path = "$.negative_certificate_artifacts[%d]" % (
            artifact_index
        )
        schema_errors = validate_with_schema(
            artifact,
            "certificate",
            schema_dir,
        )
        if schema_errors:
            state["issue_codes"].add("CERTIFICATE_SCHEMA_INVALID")
            for _ in schema_errors:
                _issue(
                    issues,
                    "CERTIFICATE_FAIL_CLOSED",
                    "CERTIFICATE_SCHEMA_INVALID",
                    artifact_path,
                )
            continue

        task = tasks_by_id[task_id]
        manifest_config_ids = [
            config["config_id"] for config in task["configs"]
        ]
        artifact_invalid = False

        def artifact_check(
            condition: bool,
            code: str,
            suffix: str,
        ) -> None:
            nonlocal artifact_invalid
            if condition:
                return
            artifact_invalid = True
            state["issue_codes"].add(code)
            _issue(
                issues,
                "CERTIFICATE_FAIL_CLOSED",
                code,
                artifact_path + suffix,
            )

        artifact_check(
            artifact.get("artifact_schema_version") == SCHEMA_VERSION,
            "CERTIFICATE_SCHEMA_VERSION_MISMATCH",
            ".artifact_schema_version",
        )
        artifact_check(
            artifact.get("canonicalization") == CANONICALIZATION,
            "CERTIFICATE_CANONICALIZATION_MISMATCH",
            ".canonicalization",
        )
        artifact_check(
            artifact.get("task_manifest_sha256")
            == task.get("task_manifest_sha256"),
            "CERTIFICATE_TASK_MANIFEST_HASH_MISMATCH",
            ".task_manifest_sha256",
        )
        artifact_check(
            artifact.get("exact_six_config_ids")
            == manifest_config_ids,
            "CERTIFICATE_EXACT_SIX_CONFIG_ROSTER_MISMATCH",
            ".exact_six_config_ids",
        )
        artifact_check(
            artifact.get("exact_six_config_ids_sha256")
            == config_roster_ids_sha256(manifest_config_ids),
            "CERTIFICATE_CONFIG_ROSTER_HASH_MISMATCH",
            ".exact_six_config_ids_sha256",
        )
        artifact_check(
            artifact.get("constraint_set_hash") == CONSTRAINT_SET_HASH,
            "CERTIFICATE_CONSTRAINT_SET_HASH_MISMATCH",
            ".constraint_set_hash",
        )
        artifact_check(
            artifact.get("proof_whitelist_hash")
            == PROOF_WHITELIST_HASH,
            "CERTIFICATE_PROOF_WHITELIST_HASH_MISMATCH",
            ".proof_whitelist_hash",
        )
        artifact_check(
            artifact.get("validator_id") == VALIDATOR_ID
            and artifact.get("validator_version") == VALIDATOR_VERSION,
            "CERTIFICATE_VALIDATOR_ID_VERSION_MISMATCH",
            ".validator_id",
        )
        artifact_check(
            artifact.get("validator_output_hash")
            == certificate_validator_output_hash(artifact),
            "CERTIFICATE_VALIDATOR_OUTPUT_HASH_MISMATCH",
            ".validator_output_hash",
        )
        if artifact_invalid:
            continue

        config_records = artifact.get("config_records", [])
        records_by_id: Dict[str, Mapping[str, Any]] = {}
        duplicate_config_record = False
        for record in config_records:
            config_id = record.get("config_id")
            if config_id in records_by_id:
                duplicate_config_record = True
            if isinstance(config_id, str):
                records_by_id[config_id] = record
        if (
            duplicate_config_record
            or set(records_by_id) != set(manifest_config_ids)
            or len(config_records) != 6
        ):
            state["issue_codes"].add(
                "CERTIFICATE_CONFIG_COVERAGE_INCOMPLETE"
            )
            _issue(
                issues,
                "CERTIFICATE_FAIL_CLOSED",
                "CERTIFICATE_CONFIG_COVERAGE_INCOMPLETE",
                artifact_path + ".config_records",
            )

        for config in task["configs"]:
            config_id = config["config_id"]
            record = records_by_id.get(config_id)
            config_path = artifact_path + ".config_records[%s]" % config_id
            if record is None:
                continue
            config_valid = True

            def config_check(
                condition: bool,
                code: str,
                suffix: str,
            ) -> None:
                nonlocal config_valid
                if condition:
                    return
                config_valid = False
                state["issue_codes"].add(code)
                _issue(
                    issues,
                    "CERTIFICATE_FAIL_CLOSED",
                    code,
                    config_path + suffix,
                )

            config_check(
                record.get("unit_id") == config.get("unit_id"),
                "CERTIFICATE_UNIT_ID_MISMATCH",
                ".unit_id",
            )
            config_check(
                record.get("unit_ordinal_roster")
                == roster_projection(config),
                "CERTIFICATE_ORDINAL_ROSTER_MISMATCH",
                ".unit_ordinal_roster",
            )
            config_check(
                record.get("unit_ordinal_roster_sha256")
                == config.get("unit_ordinal_roster_sha256"),
                "CERTIFICATE_ORDINAL_ROSTER_HASH_MISMATCH",
                ".unit_ordinal_roster_sha256",
            )
            config_check(
                record.get("trajectory_hash_chain_root")
                == config.get("trajectory_hash_chain_root"),
                "CERTIFICATE_TRAJECTORY_HASH_CHAIN_MISMATCH",
                ".trajectory_hash_chain_root",
            )
            config_check(
                record.get("applicable_obligation_ids")
                == config.get("applicable_obligation_ids"),
                "CERTIFICATE_OBLIGATION_ROSTER_MISMATCH",
                ".applicable_obligation_ids",
            )
            if not config_valid:
                continue

            locations_by_proof_key: Dict[
                Tuple[Any, Any, Any], Mapping[str, Any]
            ] = {}
            if predicate_id in NON_DEFICIT_PREDICATES:
                for location in config["ordinal_locations"]:
                    locations_by_proof_key[
                        (
                            location["observation_ordinal"],
                            location["location_id"],
                            None,
                        )
                    ] = location
            else:
                if (
                    config.get("obligation_status")
                    != "FROZEN_NONEMPTY"
                    or not config.get("applicable_obligation_ids")
                ):
                    state["issue_codes"].add(
                        "EMPTY_OBLIGATION_FORBIDS_DEFICIT_CERTIFICATE"
                    )
                    _issue(
                        issues,
                        "CERTIFICATE_FAIL_CLOSED",
                        "EMPTY_OBLIGATION_FORBIDS_DEFICIT_CERTIFICATE",
                        config_path,
                    )
                    continue
                for location in config["ordinal_locations"]:
                    for obligation_id in config[
                        "applicable_obligation_ids"
                    ]:
                        locations_by_proof_key[
                            (
                                location["observation_ordinal"],
                                location["location_id"],
                                obligation_id,
                            )
                        ] = location

            proofs_by_key: Dict[
                Tuple[Any, Any, Any], List[Mapping[str, Any]]
            ] = {}
            for proof in record.get("proofs", []):
                proofs_by_key.setdefault(_proof_key(proof), []).append(
                    proof
                )
            extra_keys = set(proofs_by_key) - set(locations_by_proof_key)
            if extra_keys:
                state["issue_codes"].add("CERTIFICATE_EXTRA_PROOF_TARGET")
                _issue(
                    issues,
                    "CERTIFICATE_FAIL_CLOSED",
                    "CERTIFICATE_EXTRA_PROOF_TARGET",
                    config_path + ".proofs",
                )

            validity_by_target: Dict[Optional[str], List[bool]] = {}
            for proof_key, location in locations_by_proof_key.items():
                target_obligation_id = proof_key[2]
                proofs = proofs_by_key.get(proof_key, [])
                if len(proofs) != 1:
                    valid = False
                    code = (
                        "CERTIFICATE_PROOF_MISSING"
                        if not proofs
                        else "CERTIFICATE_DUPLICATE_PROOF"
                    )
                else:
                    valid, code = _proof_is_valid(
                        proofs[0],
                        predicate_id,
                        target_obligation_id,
                        location,
                        task_id,
                        config_id,
                        authority,
                        repository_root,
                    )
                validity_by_target.setdefault(
                    target_obligation_id, []
                ).append(valid)
                if not valid:
                    state["issue_codes"].add(code)
                    _issue(
                        issues,
                        "CERTIFICATE_FAIL_CLOSED",
                        code,
                        config_path + ".proofs",
                    )

            if extra_keys:
                continue
            if predicate_id in NON_DEFICIT_PREDICATES:
                direct_non[(task_id, predicate_id, config_id)] = int(
                    bool(validity_by_target.get(None))
                    and all(validity_by_target[None])
                )
            else:
                for obligation_id in config[
                    "applicable_obligation_ids"
                ]:
                    values = validity_by_target.get(obligation_id, [])
                    direct_def[
                        (
                            task_id,
                            predicate_id,
                            config_id,
                            obligation_id,
                        )
                    ] = int(bool(values) and all(values))

    # A negative proof cannot overwrite confirmed direct positive evidence.
    for event in events:
        if event.get("b_status") != "CONFIRMED_POSITIVE":
            continue
        task_id = event["task_id"]
        config_id = event["config_id"]
        interface_confirmed = (
            event.get("same_event_interface_status")
            == "QUALIFYING_CONFIRMED"
        )
        world_confirmed = (
            event.get("source_status") == "PURE_WORLD_CONFIRMED"
        )
        conflicts = ["q_B"]
        if interface_confirmed:
            conflicts.append("q_C")
        if world_confirmed:
            conflicts.append("q_env")
        if interface_confirmed and world_confirmed:
            conflicts.append("q_env_interface")
        for predicate_id in conflicts:
            matrix_key = (task_id, predicate_id, config_id)
            if direct_non.get(matrix_key):
                direct_non[matrix_key] = 0
                audit_state[(task_id, predicate_id)]["issue_codes"].add(
                    "CONFIRMED_POSITIVE_CERTIFICATE_CONFLICT"
                )
                _issue(
                    issues,
                    "CERTIFICATE_FAIL_CLOSED",
                    "CONFIRMED_POSITIVE_CERTIFICATE_CONFLICT",
                    "$.observed_joint_events",
                )
        for obligation_id in event.get(
            "b_unmet_obligation_ids_confirmed", []
        ):
            b_key = (
                task_id,
                "q_B_deficit",
                config_id,
                obligation_id,
            )
            if direct_def.get(b_key):
                direct_def[b_key] = 0
                audit_state[
                    (task_id, "q_B_deficit")
                ]["issue_codes"].add(
                    "CONFIRMED_POSITIVE_CERTIFICATE_CONFLICT"
                )
            if world_confirmed:
                env_key = (
                    task_id,
                    "q_env_deficit",
                    config_id,
                    obligation_id,
                )
                if direct_def.get(env_key):
                    direct_def[env_key] = 0
                    audit_state[
                        (task_id, "q_env_deficit")
                    ]["issue_codes"].add(
                        "CONFIRMED_POSITIVE_CERTIFICATE_CONFLICT"
                    )

    return direct_non, direct_def, audit_state


def _effective_certificate_closure(
    tasks_by_id: Mapping[str, Mapping[str, Any]],
    direct_non: Mapping[Tuple[str, str, str], int],
    direct_def: Mapping[Tuple[str, str, str, str], int],
) -> Tuple[
    Dict[Tuple[str, str, str], int],
    Dict[Tuple[str, str, str, str], int],
]:
    effective_non = dict(direct_non)
    effective_def = dict(direct_def)
    for task_id, task in tasks_by_id.items():
        for config in task["configs"]:
            config_id = config["config_id"]
            b = effective_non[(task_id, "q_B", config_id)]
            c = max(
                effective_non[(task_id, "q_C", config_id)],
                b,
            )
            env = max(
                effective_non[(task_id, "q_env", config_id)],
                b,
            )
            env_interface = max(
                effective_non[
                    (task_id, "q_env_interface", config_id)
                ],
                c,
                env,
            )
            effective_non[(task_id, "q_C", config_id)] = c
            effective_non[(task_id, "q_env", config_id)] = env
            effective_non[
                (task_id, "q_env_interface", config_id)
            ] = env_interface
            for obligation_id in config[
                "applicable_obligation_ids"
            ]:
                b_deficit = effective_def[
                    (
                        task_id,
                        "q_B_deficit",
                        config_id,
                        obligation_id,
                    )
                ]
                effective_def[
                    (
                        task_id,
                        "q_env_deficit",
                        config_id,
                        obligation_id,
                    )
                ] = max(
                    effective_def[
                        (
                            task_id,
                            "q_env_deficit",
                            config_id,
                            obligation_id,
                        )
                    ],
                    b_deficit,
                )
    return effective_non, effective_def


def _config_certificate(
    task_id: str,
    predicate_id: str,
    config: Mapping[str, Any],
    matrix_non: Mapping[Tuple[str, str, str], int],
    matrix_def: Mapping[Tuple[str, str, str, str], int],
) -> int:
    config_id = config["config_id"]
    if predicate_id in NON_DEFICIT_PREDICATES:
        return matrix_non[(task_id, predicate_id, config_id)]
    obligations = config["applicable_obligation_ids"]
    if (
        config.get("obligation_status") != "FROZEN_NONEMPTY"
        or not obligations
    ):
        return 0
    return int(
        all(
            matrix_def[
                (task_id, predicate_id, config_id, obligation_id)
            ]
            for obligation_id in obligations
        )
    )


def _task_certificate(
    task_id: str,
    predicate_id: str,
    task: Mapping[str, Any],
    matrix_non: Mapping[Tuple[str, str, str], int],
    matrix_def: Mapping[Tuple[str, str, str, str], int],
) -> int:
    configs = task["configs"]
    if len(configs) != 6:
        return 0
    return int(
        all(
            _config_certificate(
                task_id,
                predicate_id,
                config,
                matrix_non,
                matrix_def,
            )
            for config in configs
        )
    )


def _certificate_audit_output(
    tasks_by_id: Mapping[str, Mapping[str, Any]],
    direct_non: Mapping[Tuple[str, str, str], int],
    direct_def: Mapping[Tuple[str, str, str, str], int],
    effective_non: Mapping[Tuple[str, str, str], int],
    effective_def: Mapping[Tuple[str, str, str, str], int],
    audit_state: Mapping[Tuple[str, str], Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for task_id in sorted(tasks_by_id):
        task = tasks_by_id[task_id]
        for predicate_id in PREDICATES:
            config_entries: List[Dict[str, Any]] = []
            for config in task["configs"]:
                config_id = config["config_id"]
                obligation_entries: List[Dict[str, Any]] = []
                if predicate_id in DEFICIT_PREDICATES:
                    for obligation_id in config[
                        "applicable_obligation_ids"
                    ]:
                        obligation_entries.append(
                            {
                                "obligation_id": obligation_id,
                                "direct_certificate": direct_def[
                                    (
                                        task_id,
                                        predicate_id,
                                        config_id,
                                        obligation_id,
                                    )
                                ],
                                "effective_certificate": effective_def[
                                    (
                                        task_id,
                                        predicate_id,
                                        config_id,
                                        obligation_id,
                                    )
                                ],
                            }
                        )
                config_entries.append(
                    {
                        "config_id": config_id,
                        "direct_certificate": _config_certificate(
                            task_id,
                            predicate_id,
                            config,
                            direct_non,
                            direct_def,
                        ),
                        "effective_certificate": _config_certificate(
                            task_id,
                            predicate_id,
                            config,
                            effective_non,
                            effective_def,
                        ),
                        "obligation_certificates": obligation_entries,
                    }
                )
            state = audit_state[(task_id, predicate_id)]
            output.append(
                {
                    "task_id": task_id,
                    "predicate_id": predicate_id,
                    "artifact_present": state["artifact_present"],
                    "direct_task_certificate": _task_certificate(
                        task_id,
                        predicate_id,
                        task,
                        direct_non,
                        direct_def,
                    ),
                    "effective_task_certificate": _task_certificate(
                        task_id,
                        predicate_id,
                        task,
                        effective_non,
                        effective_def,
                    ),
                    "config_certificates": config_entries,
                    "issue_codes": sorted(state["issue_codes"]),
                }
            )
    return output


def _event_compatibility(event: Mapping[str, Any]) -> Dict[str, bool]:
    b_confirmed = event.get("b_status") == "CONFIRMED_POSITIVE"
    b_compatible = event.get("b_status") in {
        "CONFIRMED_POSITIVE",
        "POSITIVE_COMPATIBLE",
    }
    interface_confirmed = (
        event.get("same_event_interface_status")
        == "QUALIFYING_CONFIRMED"
    )
    interface_compatible = event.get(
        "same_event_interface_status"
    ) in {
        "QUALIFYING_CONFIRMED",
        "QUALIFYING_COMPATIBLE",
    }
    world_confirmed = (
        event.get("source_status") == "PURE_WORLD_CONFIRMED"
    )
    world_compatible = event.get("source_status") in {
        "PURE_WORLD_CONFIRMED",
        "PURE_WORLD_COMPATIBLE",
        "SOURCE_UNKNOWN",
        "INVALID_SOURCE_MEASUREMENT",
    }
    return {
        "b_confirmed": b_confirmed,
        "b_compatible": b_compatible,
        "c_confirmed": b_confirmed and interface_confirmed,
        "c_compatible": b_compatible and interface_compatible,
        "env_confirmed": b_confirmed and world_confirmed,
        "env_compatible": b_compatible and world_compatible,
        "env_interface_confirmed": (
            b_confirmed and world_confirmed and interface_confirmed
        ),
        "env_interface_compatible": (
            b_compatible and world_compatible and interface_compatible
        ),
    }


def _compute_bounds(
    tasks_by_id: Mapping[str, Mapping[str, Any]],
    events: Sequence[Mapping[str, Any]],
    effective_non: Mapping[Tuple[str, str, str], int],
    effective_def: Mapping[Tuple[str, str, str, str], int],
) -> Tuple[Dict[str, Any], Dict[str, Set[str]]]:
    events_by_unit: Dict[Tuple[str, str], List[Mapping[str, Any]]] = {}
    for event in events:
        events_by_unit.setdefault(
            (event["task_id"], event["config_id"]), []
        ).append(event)

    lower_sets = {
        "B": set(),
        "C": set(),
        "env": set(),
        "env_interface": set(),
    }
    detected_sets = {
        "B": set(),
        "C": set(),
        "env": set(),
        "env_interface": set(),
    }
    task_negative_sets: Dict[str, Set[str]] = {
        predicate_id: set()
        for predicate_id in NON_DEFICIT_PREDICATES
    }
    b_deficit_lower_total = Fraction(0, 1)
    b_deficit_detected_total = Fraction(0, 1)
    b_deficit_global_total = Fraction(0, 1)
    env_deficit_lower_total = Fraction(0, 1)
    env_deficit_detected_total = Fraction(0, 1)
    env_deficit_global_total = Fraction(0, 1)

    for task_id, task in tasks_by_id.items():
        for predicate_id in NON_DEFICIT_PREDICATES:
            if _task_certificate(
                task_id,
                predicate_id,
                task,
                effective_non,
                effective_def,
            ):
                task_negative_sets[predicate_id].add(task_id)

        task_b_lower = Fraction(0, 1)
        task_b_detected = Fraction(0, 1)
        task_b_global = Fraction(0, 1)
        task_env_lower = Fraction(0, 1)
        task_env_detected = Fraction(0, 1)
        task_env_global = Fraction(0, 1)

        for config in task["configs"]:
            config_id = config["config_id"]
            unit_events = events_by_unit.get((task_id, config_id), [])
            compatibility = [
                (event, _event_compatibility(event))
                for event in unit_events
            ]
            if any(flags["b_confirmed"] for _, flags in compatibility):
                lower_sets["B"].add(task_id)
            if any(flags["c_confirmed"] for _, flags in compatibility):
                lower_sets["C"].add(task_id)
            if any(flags["env_confirmed"] for _, flags in compatibility):
                lower_sets["env"].add(task_id)
            if any(
                flags["env_interface_confirmed"]
                for _, flags in compatibility
            ):
                lower_sets["env_interface"].add(task_id)

            if (
                not effective_non[(task_id, "q_B", config_id)]
                and any(flags["b_compatible"] for _, flags in compatibility)
            ):
                detected_sets["B"].add(task_id)
            if (
                not effective_non[(task_id, "q_C", config_id)]
                and any(flags["c_compatible"] for _, flags in compatibility)
            ):
                detected_sets["C"].add(task_id)
            if (
                not effective_non[(task_id, "q_env", config_id)]
                and any(
                    flags["env_compatible"]
                    for _, flags in compatibility
                )
            ):
                detected_sets["env"].add(task_id)
            if (
                not effective_non[
                    (task_id, "q_env_interface", config_id)
                ]
                and any(
                    flags["env_interface_compatible"]
                    for _, flags in compatibility
                )
            ):
                detected_sets["env_interface"].add(task_id)

            obligations = config["applicable_obligation_ids"]
            if (
                config.get("obligation_status")
                != "FROZEN_NONEMPTY"
                or not obligations
            ):
                b_lower = Fraction(0, 1)
                b_detected = Fraction(1, 1)
                b_global = Fraction(1, 1)
                env_lower = Fraction(0, 1)
                env_detected = Fraction(1, 1)
                env_global = Fraction(1, 1)
            else:
                b_lower_ids: Set[str] = set()
                b_detected_ids: Set[str] = set()
                env_lower_ids: Set[str] = set()
                env_detected_ids: Set[str] = set()
                for event, flags in compatibility:
                    confirmed_ids = set(
                        event["b_unmet_obligation_ids_confirmed"]
                    )
                    compatible_ids = confirmed_ids | set(
                        event["b_unmet_obligation_ids_compatible"]
                    )
                    if flags["b_confirmed"]:
                        b_lower_ids.update(confirmed_ids)
                    if flags["b_compatible"]:
                        for obligation_id in compatible_ids:
                            if not effective_def[
                                (
                                    task_id,
                                    "q_B_deficit",
                                    config_id,
                                    obligation_id,
                                )
                            ]:
                                b_detected_ids.add(obligation_id)
                    if flags["env_confirmed"]:
                        env_lower_ids.update(confirmed_ids)
                    if flags["env_compatible"]:
                        for obligation_id in compatible_ids:
                            if not effective_def[
                                (
                                    task_id,
                                    "q_env_deficit",
                                    config_id,
                                    obligation_id,
                                )
                            ]:
                                env_detected_ids.add(obligation_id)
                b_detected_ids.update(b_lower_ids)
                env_detected_ids.update(env_lower_ids)
                b_global_ids = set(b_lower_ids)
                env_global_ids = set(env_lower_ids)
                for obligation_id in obligations:
                    if not effective_def[
                        (
                            task_id,
                            "q_B_deficit",
                            config_id,
                            obligation_id,
                        )
                    ]:
                        b_global_ids.add(obligation_id)
                    if not effective_def[
                        (
                            task_id,
                            "q_env_deficit",
                            config_id,
                            obligation_id,
                        )
                    ]:
                        env_global_ids.add(obligation_id)
                denominator = len(obligations)
                b_lower = Fraction(len(b_lower_ids), denominator)
                b_detected = Fraction(len(b_detected_ids), denominator)
                b_global = Fraction(len(b_global_ids), denominator)
                env_lower = Fraction(len(env_lower_ids), denominator)
                env_detected = Fraction(
                    len(env_detected_ids), denominator
                )
                env_global = Fraction(len(env_global_ids), denominator)

            task_b_lower += b_lower
            task_b_detected += b_detected
            task_b_global += b_global
            task_env_lower += env_lower
            task_env_detected += env_detected
            task_env_global += env_global

        b_deficit_lower_total += task_b_lower / 6
        b_deficit_detected_total += task_b_detected / 6
        b_deficit_global_total += task_b_global / 6
        env_deficit_lower_total += task_env_lower / 6
        env_deficit_detected_total += task_env_detected / 6
        env_deficit_global_total += task_env_global / 6

    all_tasks = set(tasks_by_id)
    detected_sets["B"].update(lower_sets["B"])
    detected_sets["C"].update(lower_sets["C"])
    detected_sets["env"].update(lower_sets["env"])
    detected_sets["env_interface"].update(
        lower_sets["env_interface"]
    )
    upper_b_global = len(all_tasks - task_negative_sets["q_B"])
    upper_c_global = len(all_tasks - task_negative_sets["q_C"])
    upper_env_global = len(all_tasks - task_negative_sets["q_env"])
    upper_env_interface_global = len(
        all_tasks - task_negative_sets["q_env_interface"]
    )

    bounds = {
        "holdout_task_count": len(tasks_by_id),
        "C0_B": {
            "L_B_tasks": len(lower_sets["B"]),
            "U_B_tasks_detected": len(detected_sets["B"]),
            "U_B_tasks_global": upper_b_global,
            "L_B_deficit": _fraction_json(b_deficit_lower_total),
            "U_B_deficit_detected": _fraction_json(
                b_deficit_detected_total
            ),
            "U_B_deficit_global": _fraction_json(
                b_deficit_global_total
            ),
        },
        "C0_C": {
            "L_C_interface_tasks": len(lower_sets["C"]),
            "U_C_interface_tasks_detected": len(
                detected_sets["C"]
            ),
            "U_C_interface_tasks_global": upper_c_global,
        },
        "C0_E": {
            "L_env_tasks": len(lower_sets["env"]),
            "U_env_tasks_detected": len(detected_sets["env"]),
            "U_env_tasks": upper_env_global,
            "L_env_interface_tasks": len(
                lower_sets["env_interface"]
            ),
            "U_env_interface_tasks_detected": len(
                detected_sets["env_interface"]
            ),
            "U_env_interface_tasks": upper_env_interface_global,
            "L_env_deficit": _fraction_json(env_deficit_lower_total),
            "U_env_deficit_detected": _fraction_json(
                env_deficit_detected_total
            ),
            "U_env_deficit": _fraction_json(
                env_deficit_global_total
            ),
        },
    }
    return bounds, {
        **lower_sets,
        **{"detected_" + key: value for key, value in detected_sets.items()},
        **{
            "negative_" + key: value
            for key, value in task_negative_sets.items()
        },
    }


def _complete_missing_configs(
    tasks_by_id: Mapping[str, Mapping[str, Any]],
    exact_config_ids: Sequence[str],
) -> Dict[str, Mapping[str, Any]]:
    """Insert conservative placeholders without changing a six-config mean.

    This function does not make an incomplete manifest valid.  It only ensures
    that diagnostic bounds emitted alongside ``UNIDENTIFIABLE`` retain the
    frozen denominator instead of silently changing it from six to five.
    """

    completed: Dict[str, Mapping[str, Any]] = {}
    for task_id, task in tasks_by_id.items():
        records = {
            config.get("config_id"): config
            for config in task.get("configs", [])
            if isinstance(config.get("config_id"), str)
        }
        configs: List[Mapping[str, Any]] = []
        for config_id in exact_config_ids:
            if config_id in records:
                configs.append(records[config_id])
            else:
                configs.append(
                    {
                        "config_id": config_id,
                        "unit_id": "MissingUnit-%s-%s"
                        % (task_id, config_id),
                        "obligation_status": "MISSING_OR_EMPTY",
                        "applicable_obligation_ids": [],
                        "ordinal_locations": [],
                        "unit_ordinal_roster_sha256": "0" * 64,
                        "trajectory_hash_chain_root": "0" * 64,
                    }
                )
        completed[task_id] = {
            **task,
            "configs": configs,
        }
    return completed


def _variable_id(
    task_id: str,
    config_id: str,
    location_id: str,
    predicate_id: str,
    obligation_id: Optional[str],
) -> str:
    digest = canonical_sha256(
        [
            "stage0f-bounds-joint-variable-v1",
            task_id,
            config_id,
            location_id,
            predicate_id,
            obligation_id,
        ]
    )
    return "V-" + digest


def _build_joint_completion_ir(
    projection_id: str,
    tasks_by_id: Mapping[str, Mapping[str, Any]],
    events: Sequence[Mapping[str, Any]],
    effective_non: Mapping[Tuple[str, str, str], int],
    effective_def: Mapping[Tuple[str, str, str, str], int],
    issues: List[Dict[str, str]],
) -> Dict[str, Any]:
    if projection_id == "Z_D":
        included_predicates = {
            "q_B",
            "q_C",
            "q_B_deficit",
        }
    elif projection_id == "Z_env_structure":
        included_predicates = set(PREDICATES)
    else:  # pragma: no cover - internal invariant.
        raise ValueError("unknown projection: %s" % projection_id)

    events_by_location: Dict[
        Tuple[str, str, str], List[Mapping[str, Any]]
    ] = {}
    for event in events:
        events_by_location.setdefault(
            (
                event["task_id"],
                event["config_id"],
                event["location_id"],
            ),
            [],
        ).append(event)

    variables: List[Dict[str, Any]] = []
    implications: List[Dict[str, str]] = []
    variables_by_location: Dict[
        Tuple[str, str, str, str, Optional[str]], Dict[str, Any]
    ] = {}

    for task_id in sorted(tasks_by_id):
        task = tasks_by_id[task_id]
        for config in task["configs"]:
            config_id = config["config_id"]
            obligations = config["applicable_obligation_ids"]
            for location in config["ordinal_locations"]:
                location_id = location["location_id"]
                location_events = events_by_location.get(
                    (task_id, config_id, location_id), []
                )
                positive: Dict[Tuple[str, Optional[str]], bool] = {}
                for event in location_events:
                    flags = _event_compatibility(event)
                    positive[("q_B", None)] = (
                        positive.get(("q_B", None), False)
                        or flags["b_confirmed"]
                    )
                    positive[("q_C", None)] = (
                        positive.get(("q_C", None), False)
                        or flags["c_confirmed"]
                    )
                    positive[("q_env", None)] = (
                        positive.get(("q_env", None), False)
                        or flags["env_confirmed"]
                    )
                    positive[("q_env_interface", None)] = (
                        positive.get(
                            ("q_env_interface", None), False
                        )
                        or flags["env_interface_confirmed"]
                    )
                    for obligation_id in event[
                        "b_unmet_obligation_ids_confirmed"
                    ]:
                        positive[("q_B_deficit", obligation_id)] = (
                            positive.get(
                                ("q_B_deficit", obligation_id), False
                            )
                            or flags["b_confirmed"]
                        )
                        positive[("q_env_deficit", obligation_id)] = (
                            positive.get(
                                ("q_env_deficit", obligation_id), False
                            )
                            or flags["env_confirmed"]
                        )

                variable_targets: List[
                    Tuple[str, Optional[str]]
                ] = [
                    (predicate_id, None)
                    for predicate_id in NON_DEFICIT_PREDICATES
                    if predicate_id in included_predicates
                ]
                for obligation_id in obligations:
                    variable_targets.extend(
                        (
                            (predicate_id, obligation_id)
                            for predicate_id in DEFICIT_PREDICATES
                            if predicate_id in included_predicates
                        )
                    )
                for predicate_id, obligation_id in variable_targets:
                    confirmed = positive.get(
                        (predicate_id, obligation_id), False
                    )
                    if predicate_id in NON_DEFICIT_PREDICATES:
                        certified = bool(
                            effective_non[
                                (task_id, predicate_id, config_id)
                            ]
                        )
                    else:
                        certified = bool(
                            effective_def[
                                (
                                    task_id,
                                    predicate_id,
                                    config_id,
                                    obligation_id,
                                )
                            ]
                        )
                    if confirmed and certified:
                        _issue(
                            issues,
                            "MEASUREMENT_INVALID",
                            "JOINT_BIT_CONFIRMED_AND_CERTIFIED_FALSE",
                            "$.%s.%s" % (projection_id, location_id),
                        )
                        domain = []
                        fixed_by = "JOINT_IMPLICATION_PROPAGATION"
                    elif confirmed:
                        domain = [1]
                        fixed_by = "CONFIRMED_DIRECT_EVIDENCE"
                    elif certified:
                        domain = [0]
                        fixed_by = (
                            "EFFECTIVE_MECHANICAL_NEGATIVE_CERTIFICATE"
                        )
                    else:
                        domain = [0, 1]
                        fixed_by = "UNRESOLVED_FINITE_COMPLETION"
                    variable = {
                        "variable_id": _variable_id(
                            task_id,
                            config_id,
                            location_id,
                            predicate_id,
                            obligation_id,
                        ),
                        "task_id": task_id,
                        "config_id": config_id,
                        "unit_id": config["unit_id"],
                        "location_id": location_id,
                        "predicate_id": predicate_id,
                        "obligation_id": obligation_id,
                        "domain": domain,
                        "fixed_by": fixed_by,
                    }
                    variables.append(variable)
                    variables_by_location[
                        (
                            task_id,
                            config_id,
                            location_id,
                            predicate_id,
                            obligation_id,
                        )
                    ] = variable

                for antecedent, consequent in JOINT_IMPLICATIONS:
                    if (
                        antecedent not in included_predicates
                        or consequent not in included_predicates
                    ):
                        continue
                    obligation_values: Sequence[Optional[str]]
                    if antecedent in DEFICIT_PREDICATES:
                        obligation_values = obligations
                    else:
                        obligation_values = [None]
                    for obligation_id in obligation_values:
                        antecedent_key = (
                            task_id,
                            config_id,
                            location_id,
                            antecedent,
                            obligation_id,
                        )
                        consequent_obligation = (
                            obligation_id
                            if consequent in DEFICIT_PREDICATES
                            else None
                        )
                        consequent_key = (
                            task_id,
                            config_id,
                            location_id,
                            consequent,
                            consequent_obligation,
                        )
                        if (
                            antecedent_key not in variables_by_location
                            or consequent_key not in variables_by_location
                        ):
                            continue
                        implications.append(
                            {
                                "antecedent_variable_id": (
                                    variables_by_location[
                                        antecedent_key
                                    ]["variable_id"]
                                ),
                                "consequent_variable_id": (
                                    variables_by_location[
                                        consequent_key
                                    ]["variable_id"]
                                ),
                                "constraint_kind": (
                                    "antecedent_leq_consequent"
                                ),
                            }
                        )

    variable_by_id = {
        variable["variable_id"]: variable for variable in variables
    }
    changed = True
    while changed:
        changed = False
        for implication in implications:
            antecedent = variable_by_id[
                implication["antecedent_variable_id"]
            ]
            consequent = variable_by_id[
                implication["consequent_variable_id"]
            ]
            if antecedent["domain"] == [1] and consequent["domain"] != [1]:
                new_domain = (
                    [1] if 1 in consequent["domain"] else []
                )
                if consequent["domain"] != new_domain:
                    consequent["domain"] = new_domain
                    if new_domain:
                        consequent["fixed_by"] = (
                            "JOINT_IMPLICATION_PROPAGATION"
                        )
                    changed = True
            if consequent["domain"] == [0] and antecedent["domain"] != [0]:
                new_domain = (
                    [0] if 0 in antecedent["domain"] else []
                )
                if antecedent["domain"] != new_domain:
                    antecedent["domain"] = new_domain
                    if new_domain:
                        antecedent["fixed_by"] = (
                            "JOINT_IMPLICATION_PROPAGATION"
                        )
                    changed = True

    finite_nonempty = all(variable["domain"] for variable in variables)
    if not finite_nonempty:
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "JOINT_COMPLETION_EMPTY",
            "$.%s" % projection_id,
        )
    free_count = sum(
        1 for variable in variables if variable["domain"] == [0, 1]
    )
    location_ids = {
        (
            variable["task_id"],
            variable["config_id"],
            variable["location_id"],
        )
        for variable in variables
    }
    ir: Dict[str, Any] = {
        "artifact_type": "stage0f_bounds_joint_completion_ir",
        "schema_version": SCHEMA_VERSION,
        "projection_id": projection_id,
        "joint_semantics": (
            "same-latent-event-or-decision-boundary existential sufficient bits"
        ),
        "finite_location_count": len(location_ids),
        "finite_variable_count": len(variables),
        "free_binary_variable_count": free_count,
        "domain_product_upper_bound_decimal": str(2 ** free_count),
        "finite_nonempty": finite_nonempty,
        "variables": sorted(
            variables, key=lambda variable: variable["variable_id"]
        ),
        "implications": sorted(
            implications,
            key=lambda implication: (
                implication["antecedent_variable_id"],
                implication["consequent_variable_id"],
            ),
        ),
        "prohibited_operations": list(
            CONSTRAINT_SPEC["prohibited_operations"]
        ),
        "constraint_set_hash": CONSTRAINT_SET_HASH,
    }
    ir["completion_ir_sha256"] = canonical_sha256(
        [
            "stage0f-bounds-completion-ir-v1",
            ir,
        ]
    )
    return ir


def enumerate_joint_completions(
    ir: Mapping[str, Any],
    max_free_variables: int = 20,
) -> Iterable[Dict[str, int]]:
    """Enumerate a small synthetic IR for property tests and witnesses."""

    variables = ir["variables"]
    free = [
        variable
        for variable in variables
        if variable["domain"] == [0, 1]
    ]
    if len(free) > max_free_variables:
        raise ValueError(
            "completion enumeration limit exceeded: %d > %d"
            % (len(free), max_free_variables)
        )
    fixed = {
        variable["variable_id"]: variable["domain"][0]
        for variable in variables
        if len(variable["domain"]) == 1
    }
    implications = [
        (
            edge["antecedent_variable_id"],
            edge["consequent_variable_id"],
        )
        for edge in ir["implications"]
    ]
    for mask in range(1 << len(free)):
        assignment = dict(fixed)
        for index, variable in enumerate(free):
            assignment[variable["variable_id"]] = (
                mask >> index
            ) & 1
        if all(
            assignment[antecedent] <= assignment[consequent]
            for antecedent, consequent in implications
        ):
            yield assignment


def find_completion_witness(
    ir: Mapping[str, Any],
    require_predicate_id: str,
    expected_value: int,
    max_free_variables: int = 20,
) -> Optional[Dict[str, int]]:
    """Return a feasible synthetic witness with any target bit at value."""

    target_ids = {
        variable["variable_id"]
        for variable in ir["variables"]
        if variable["predicate_id"] == require_predicate_id
    }
    for assignment in enumerate_joint_completions(
        ir, max_free_variables=max_free_variables
    ):
        if any(
            assignment[variable_id] == expected_value
            for variable_id in target_ids
        ):
            return assignment
    return None


def _structural_statistics(
    assignment: Mapping[str, int],
    ir: Mapping[str, Any],
    tasks_by_id: Mapping[str, Mapping[str, Any]],
    task_mapping: Mapping[str, Mapping[str, str]],
    config_mapping: Mapping[str, str],
    projection_id: str,
) -> Dict[str, Any]:
    positive_predicate = (
        "q_B" if projection_id == "Z_D" else "q_env"
    )
    deficit_predicate = (
        "q_B_deficit"
        if projection_id == "Z_D"
        else "q_env_deficit"
    )
    positive_by_unit: Dict[Tuple[str, str], int] = {}
    deficit_obligations: Dict[Tuple[str, str], Set[str]] = {}
    for variable in ir["variables"]:
        if assignment[variable["variable_id"]] != 1:
            continue
        unit_key = (variable["task_id"], variable["config_id"])
        if variable["predicate_id"] == positive_predicate:
            positive_by_unit[unit_key] = 1
        if variable["predicate_id"] == deficit_predicate:
            obligation_id = variable["obligation_id"]
            if obligation_id is not None:
                deficit_obligations.setdefault(unit_key, set()).add(
                    obligation_id
                )

    positive_tasks = {
        task_id
        for task_id, _ in positive_by_unit
    }
    partitions: Dict[str, Dict[str, Any]] = {}
    for partition_name in (
        "structural_group",
        "site_app_set",
        "model_family",
    ):
        exposures: Dict[str, int] = {}
        positive_mass: Dict[str, Fraction] = {}
        deficit_mass: Dict[str, Fraction] = {}
        if partition_name in {"structural_group", "site_app_set"}:
            for task_id, task in tasks_by_id.items():
                bucket = task_mapping[task_id][partition_name]
                exposures[bucket] = exposures.get(bucket, 0) + 1
                if task_id in positive_tasks:
                    positive_mass[bucket] = (
                        positive_mass.get(bucket, Fraction(0)) + 1
                    )
                task_deficit = Fraction(0)
                for config in task["configs"]:
                    obligations = config[
                        "applicable_obligation_ids"
                    ]
                    if not obligations:
                        raise ValueError(
                            "structural deficit requires nonempty obligations"
                        )
                    unit_key = (task_id, config["config_id"])
                    task_deficit += Fraction(
                        len(deficit_obligations.get(unit_key, set())),
                        len(obligations),
                    )
                task_deficit /= 6
                deficit_mass[bucket] = (
                    deficit_mass.get(bucket, Fraction(0))
                    + task_deficit
                )
        else:
            for task_id, task in tasks_by_id.items():
                for config in task["configs"]:
                    bucket = config_mapping[config["config_id"]]
                    exposures[bucket] = exposures.get(bucket, 0) + 1
                    unit_key = (task_id, config["config_id"])
                    if unit_key in positive_by_unit:
                        positive_mass[bucket] = (
                            positive_mass.get(bucket, Fraction(0)) + 1
                        )
                    obligations = config[
                        "applicable_obligation_ids"
                    ]
                    if not obligations:
                        raise ValueError(
                            "structural deficit requires nonempty obligations"
                        )
                    deficit_mass[bucket] = (
                        deficit_mass.get(bucket, Fraction(0))
                        + Fraction(
                            len(
                                deficit_obligations.get(
                                    unit_key, set()
                                )
                            ),
                            len(obligations),
                        )
                    )

        def normalized_shares(
            mass: Mapping[str, Fraction],
        ) -> Dict[str, Fraction]:
            rates = {
                bucket: mass.get(bucket, Fraction(0))
                / exposure
                for bucket, exposure in exposures.items()
            }
            rate_sum = sum(rates.values(), Fraction(0))
            if rate_sum == 0:
                return {
                    bucket: Fraction(0) for bucket in exposures
                }
            return {
                bucket: rate / rate_sum
                for bucket, rate in rates.items()
            }

        def raw_shares(
            mass: Mapping[str, Fraction],
        ) -> Dict[str, Fraction]:
            total = sum(
                (
                    mass.get(bucket, Fraction(0))
                    for bucket in exposures
                ),
                Fraction(0),
            )
            if total == 0:
                return {
                    bucket: Fraction(0) for bucket in exposures
                }
            return {
                bucket: mass.get(bucket, Fraction(0)) / total
                for bucket in exposures
            }

        positive_shares = normalized_shares(positive_mass)
        deficit_shares = normalized_shares(deficit_mass)
        positive_raw_shares = raw_shares(positive_mass)
        deficit_raw_shares = raw_shares(deficit_mass)
        partitions[partition_name] = {
            "exposures": dict(sorted(exposures.items())),
            "positive_partition_count": sum(
                1
                for bucket in exposures
                if positive_mass.get(bucket, Fraction(0)) > 0
            ),
            "max_positive_share": max(
                positive_shares.values(), default=Fraction(0)
            ),
            "max_deficit_share": max(
                deficit_shares.values(), default=Fraction(0)
            ),
            "bucket_statistics": [
                {
                    "bucket_id": bucket,
                    "exposure": exposures[bucket],
                    "positive_raw_mass": _fraction_json(
                        positive_mass.get(bucket, Fraction(0))
                    ),
                    "deficit_raw_mass": _fraction_json(
                        deficit_mass.get(bucket, Fraction(0))
                    ),
                    "positive_raw_share": _fraction_json(
                        positive_raw_shares[bucket]
                    ),
                    "deficit_raw_share": _fraction_json(
                        deficit_raw_shares[bucket]
                    ),
                    "positive_rate": _fraction_json(
                        positive_mass.get(bucket, Fraction(0))
                        / exposures[bucket]
                    ),
                    "deficit_rate": _fraction_json(
                        deficit_mass.get(bucket, Fraction(0))
                        / exposures[bucket]
                    ),
                    "positive_exposure_normalized_share": (
                        _fraction_json(positive_shares[bucket])
                    ),
                    "deficit_exposure_normalized_share": (
                        _fraction_json(deficit_shares[bucket])
                    ),
                }
                for bucket in sorted(exposures)
            ],
        }

    passed = (
        partitions["structural_group"]["positive_partition_count"] >= 4
        and partitions["site_app_set"]["positive_partition_count"] >= 3
        and partitions["model_family"]["positive_partition_count"] >= 3
        and all(
            partition["max_positive_share"] < Fraction(1, 2)
            and partition["max_deficit_share"] < Fraction(1, 2)
            for partition in partitions.values()
        )
    )
    return {
        "passed_all_3K_and_6_share_gates": passed,
        "K_group": partitions["structural_group"][
            "positive_partition_count"
        ],
        "K_site_or_app_set": partitions["site_app_set"][
            "positive_partition_count"
        ],
        "K_model_family": partitions["model_family"][
            "positive_partition_count"
        ],
        "max_shares": {
            "structural_positive": _fraction_json(
                partitions["structural_group"]["max_positive_share"]
            ),
            "site_app_positive": _fraction_json(
                partitions["site_app_set"]["max_positive_share"]
            ),
            "model_family_positive": _fraction_json(
                partitions["model_family"]["max_positive_share"]
            ),
            "structural_deficit": _fraction_json(
                partitions["structural_group"]["max_deficit_share"]
            ),
            "site_app_deficit": _fraction_json(
                partitions["site_app_set"]["max_deficit_share"]
            ),
            "model_family_deficit": _fraction_json(
                partitions["model_family"]["max_deficit_share"]
            ),
        },
        "exposures": {
            name: value["exposures"]
            for name, value in partitions.items()
        },
        "partition_details": {
            name: value["bucket_statistics"]
            for name, value in partitions.items()
        },
    }


def _structural_witness(
    assignment: Mapping[str, int],
    statistics: Mapping[str, Any],
) -> Dict[str, Any]:
    assignment_rows = [
        {
            "variable_id": variable_id,
            "value": assignment[variable_id],
        }
        for variable_id in sorted(assignment)
    ]
    return {
        "assignment_sha256": canonical_sha256(
            [
                "stage0f-bounds-structural-witness-v1",
                assignment_rows,
            ]
        ),
        "assignment": assignment_rows,
        "statistics": copy.deepcopy(dict(statistics)),
    }


def _evaluate_structural_completion(
    ir: Mapping[str, Any],
    tasks_by_id: Mapping[str, Mapping[str, Any]],
    authority: BoundsAuthority,
) -> Tuple[Dict[str, Any], Optional[str]]:
    mapping = authority.structural_mapping
    base = {
        "projection_id": ir["projection_id"],
        "mapping_sha256": authority.binding[
            "structural_mapping_sha256"
        ],
        "enumeration_complete": False,
        "completion_count": 0,
        "pass_witness": None,
        "fail_witness": None,
    }
    runtime_mapping_sha256 = canonical_sha256(
        [
            "stage0f-bounds-structural-mapping-v1",
            mapping,
        ]
    )
    if runtime_mapping_sha256 != authority.binding[
        "structural_mapping_sha256"
    ]:
        return {
            **base,
            "verdict": "UNIDENTIFIABLE",
        }, "STRUCTURAL_MAPPING_RUNTIME_HASH_MISMATCH"
    if mapping is None:
        return {
            **base,
            "verdict": "UNIDENTIFIABLE",
        }, "STRUCTURAL_MAPPING_AUTHORITY_MISSING"
    task_rows = mapping.get("task_mappings", [])
    config_rows = mapping.get("config_mappings", [])
    task_mapping = {
        row.get("task_id"): row for row in task_rows
    }
    config_mapping = {
        row.get("config_id"): row.get("model_family")
        for row in config_rows
    }
    if (
        len(task_mapping) != len(task_rows)
        or set(task_mapping) != set(tasks_by_id)
        or any(
            row.get("structural_group") in {None, "UNMAPPED"}
            or row.get("site_app_set") in {None, "UNMAPPED"}
            for row in task_rows
        )
    ):
        return {
            **base,
            "verdict": "UNIDENTIFIABLE",
        }, "STRUCTURAL_TASK_MAPPING_INVALID_OR_UNMAPPED"
    expected_configs = {
        config["config_id"]
        for task in tasks_by_id.values()
        for config in task["configs"]
    }
    if (
        len(config_mapping) != len(config_rows)
        or set(config_mapping) != expected_configs
        or config_mapping != FROZEN_MODEL_FAMILY_CODEBOOK
        or mapping.get("model_family_codebook_sha256")
        != FROZEN_MODEL_FAMILY_CODEBOOK_HASH
    ):
        return {
            **base,
            "verdict": "UNIDENTIFIABLE",
        }, "STRUCTURAL_CONFIG_MAPPING_INVALID"
    if any(
        not config["applicable_obligation_ids"]
        for task in tasks_by_id.values()
        for config in task["configs"]
    ):
        return {
            **base,
            "verdict": "UNIDENTIFIABLE",
        }, "STRUCTURAL_EMPTY_OBLIGATION_SET"
    enumeration_limit = mapping.get("enumeration_limit")
    if (
        not isinstance(enumeration_limit, int)
        or enumeration_limit < 0
        or enumeration_limit > 20
        or ir["free_binary_variable_count"] > enumeration_limit
    ):
        return {
            **base,
            "verdict": "UNIDENTIFIABLE",
        }, "STRUCTURAL_SOLVER_CERTIFICATE_REQUIRED"

    pass_witness = None
    fail_witness = None
    completion_count = 0
    all_pass = True
    all_fail = True
    try:
        completions = enumerate_joint_completions(
            ir, max_free_variables=enumeration_limit
        )
        for assignment in completions:
            completion_count += 1
            statistics = _structural_statistics(
                assignment,
                ir,
                tasks_by_id,
                task_mapping,
                config_mapping,
                ir["projection_id"],
            )
            passed = statistics[
                "passed_all_3K_and_6_share_gates"
            ]
            all_pass = all_pass and passed
            all_fail = all_fail and not passed
            if passed and pass_witness is None:
                pass_witness = _structural_witness(
                    assignment, statistics
                )
            if not passed and fail_witness is None:
                fail_witness = _structural_witness(
                    assignment, statistics
                )
    except ValueError:
        return {
            **base,
            "verdict": "UNIDENTIFIABLE",
        }, "STRUCTURAL_COMPLETION_RECOMPUTATION_FAILED"
    if completion_count == 0:
        return {
            **base,
            "verdict": "UNIDENTIFIABLE",
        }, "STRUCTURAL_COMPLETION_SET_EMPTY"
    if all_pass:
        verdict = "SUPPORTED"
    elif all_fail:
        verdict = "CONCENTRATED"
    else:
        verdict = "INCONCLUSIVE"
    return {
        **base,
        "verdict": verdict,
        "enumeration_complete": True,
        "completion_count": completion_count,
        "pass_witness": pass_witness,
        "fail_witness": fail_witness,
    }, None


def _measurement_invalid_structural_evaluation(
    ir: Mapping[str, Any],
    authority: BoundsAuthority,
) -> Dict[str, Any]:
    """Return a non-enumerated structural result after provenance failure."""

    return {
        "projection_id": ir["projection_id"],
        "mapping_sha256": authority.binding[
            "structural_mapping_sha256"
        ],
        "verdict": "UNIDENTIFIABLE",
        "enumeration_complete": False,
        "completion_count": 0,
        "pass_witness": None,
        "fail_witness": None,
    }


def seal_holdout_manifest(manifest: MutableMapping[str, Any]) -> None:
    """Recompute all finite-universe hashes in dependency order."""

    config_ids = manifest["exact_six_config_ids"]
    manifest["exact_six_config_ids_sha256"] = (
        config_roster_ids_sha256(config_ids)
    )
    task_ids: List[str] = []
    for task in manifest["tasks"]:
        task_ids.append(task["task_id"])
        for config in task["configs"]:
            config["unit_ordinal_roster_sha256"] = (
                unit_ordinal_roster_sha256(config)
            )
            config["trajectory_hash_chain_root"] = (
                trajectory_hash_chain_root(config)
            )
        task["task_manifest_sha256"] = task_manifest_sha256(task)
    manifest["task_roster_sha256"] = canonical_sha256(
        ["stage0f-bounds-task-roster-v1", task_ids]
    )
    manifest["manifest_sha256"] = holdout_manifest_sha256(manifest)


def execute_and_seal_proof(
    proof: MutableMapping[str, Any],
    predicate_id: str,
    target_obligation_id: Optional[str],
    task_id: str,
    config_id: str,
    authority: BoundsAuthority,
    repository_root: Optional[Path] = None,
) -> None:
    """Execute the frozen verifier and seal its exact derived output."""

    repository_root = (
        Path(__file__).resolve().parents[1]
        if repository_root is None
        else repository_root
    )
    registry, _ = _load_frozen_verifier_registry(repository_root)
    mode_record = registry["modes"][proof["proof_mode"]]
    proof["verifier_id"] = registry["verifier_id"]
    proof["verifier_version"] = registry["verifier_version"]
    proof["verifier_executable_sha256"] = registry[
        "executable_sha256"
    ]
    proof["verifier_config_sha256"] = mode_record[
        "config_sha256"
    ]
    output, code = _run_frozen_verifier(
        proof,
        predicate_id,
        target_obligation_id,
        task_id,
        config_id,
        authority,
        repository_root,
    )
    if output is None:
        raise ValueError("frozen verifier did not pass: %s" % code)
    proof["verifier_output"] = output
    proof["verifier_output_hash"] = verifier_output_hash(output)


def seal_certificate(artifact: MutableMapping[str, Any]) -> None:
    artifact["validator_output_hash"] = (
        certificate_validator_output_hash(artifact)
    )


def _rational_fraction(value: Mapping[str, Any]) -> Fraction:
    return Fraction(value["numerator"], value["denominator"])


def _validate_bound_ordering(
    bounds: Mapping[str, Any],
    issues: List[Dict[str, str]],
) -> None:
    count = bounds["holdout_task_count"]
    b = bounds["C0_B"]
    c = bounds["C0_C"]
    env = bounds["C0_E"]

    count_chains = [
        (
            0,
            b["L_B_tasks"],
            b["U_B_tasks_detected"],
            b["U_B_tasks_global"],
            count,
        ),
        (
            0,
            c["L_C_interface_tasks"],
            c["U_C_interface_tasks_detected"],
            c["U_C_interface_tasks_global"],
            b["U_B_tasks_global"],
            count,
        ),
        (
            0,
            env["L_env_tasks"],
            env["U_env_tasks_detected"],
            env["U_env_tasks"],
            b["U_B_tasks_global"],
            count,
        ),
        (
            0,
            env["L_env_interface_tasks"],
            env["U_env_interface_tasks_detected"],
            env["U_env_interface_tasks"],
            c["U_C_interface_tasks_global"],
            count,
        ),
    ]
    if any(
        any(left > right for left, right in zip(chain, chain[1:]))
        for chain in count_chains
    ):
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "BOUND_COUNT_ORDERING_VIOLATION",
            "$.bounds",
        )
    if not (
        env["L_env_interface_tasks"] <= env["L_env_tasks"]
        <= b["L_B_tasks"]
    ):
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "BOUND_LOWER_SUBSET_VIOLATION",
            "$.bounds.C0_E",
        )
    if env["L_env_interface_tasks"] > c["L_C_interface_tasks"]:
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "BOUND_INTERFACE_LOWER_SUBSET_VIOLATION",
            "$.bounds.C0_E",
        )

    b_lower = _rational_fraction(b["L_B_deficit"])
    b_detected = _rational_fraction(b["U_B_deficit_detected"])
    b_global = _rational_fraction(b["U_B_deficit_global"])
    env_lower = _rational_fraction(env["L_env_deficit"])
    env_detected = _rational_fraction(
        env["U_env_deficit_detected"]
    )
    env_global = _rational_fraction(env["U_env_deficit"])
    if not (
        Fraction(0, 1)
        <= b_lower
        <= b_detected
        <= b_global
        <= count
    ):
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "BOUND_B_DEFICIT_ORDERING_VIOLATION",
            "$.bounds.C0_B",
        )
    if not (
        Fraction(0, 1)
        <= env_lower
        <= env_detected
        <= env_global
        <= b_global
        <= count
    ):
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "BOUND_ENV_DEFICIT_ORDERING_VIOLATION",
            "$.bounds.C0_E",
        )
    if env_lower > b_lower:
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "BOUND_ENV_DEFICIT_LOWER_SUBSET_VIOLATION",
            "$.bounds.C0_E",
        )


def _verdicts(
    bounds: Mapping[str, Any],
    measurement_valid: bool,
) -> Dict[str, str]:
    if not measurement_valid:
        return {
            "C0_B": "UNIDENTIFIABLE",
            "C0_C": "UNIDENTIFIABLE",
            "C0_E": "UNIDENTIFIABLE",
        }
    b = bounds["C0_B"]
    c = bounds["C0_C"]
    env = bounds["C0_E"]
    b_lower_deficit = _rational_fraction(b["L_B_deficit"])
    b_upper_deficit = _rational_fraction(
        b["U_B_deficit_global"]
    )
    if b["L_B_tasks"] >= 8 and b_lower_deficit >= 1:
        b_verdict = "SUPPORTED"
    elif b["U_B_tasks_global"] < 8 or b_upper_deficit < 1:
        b_verdict = "BELOW_FROZEN_GATE"
    else:
        b_verdict = "INCONCLUSIVE"

    if c["L_C_interface_tasks"] >= 8:
        c_verdict = "PRESENT"
    elif c["U_C_interface_tasks_global"] < 8:
        c_verdict = "ABSENT"
    else:
        c_verdict = "INCONCLUSIVE"

    env_lower_deficit = _rational_fraction(env["L_env_deficit"])
    env_upper_deficit = _rational_fraction(env["U_env_deficit"])
    if (
        env["L_env_tasks"] >= 8
        and env_lower_deficit >= 1
        and env["L_env_interface_tasks"] >= 8
    ):
        env_verdict = "SUPPORTED"
    elif (
        env["U_env_tasks"] < 8
        or env_upper_deficit < 1
        or env["U_env_interface_tasks"] < 8
    ):
        env_verdict = "BELOW_FROZEN_GATE"
    else:
        env_verdict = "INCONCLUSIVE"
    return {
        "C0_B": b_verdict,
        "C0_C": c_verdict,
        "C0_E": env_verdict,
    }


def analyze_packet(
    packet: Mapping[str, Any],
    schema_dir: Optional[Path] = None,
    authority: Optional[BoundsAuthority] = None,
) -> Dict[str, Any]:
    """Validate and derive synthetic certificate/bounds mechanics."""

    if authority is None:
        raise ValueError(
            "BOUNDS_AUTHORITY_REQUIRED: packet hashes cannot self-authorize"
        )
    authority.assert_runtime_integrity()
    schema_dir = (
        schema_dir
        if schema_dir is not None
        else Path(__file__).resolve().parents[1] / "schemas"
    )
    issues: List[Dict[str, str]] = []
    repository_root = Path(__file__).resolve().parents[1]

    # Validate certificate artifacts independently so malformed certificates
    # fail closed without turning the finite holdout itself into a negative.
    schema_projection = copy.deepcopy(packet)
    schema_projection["negative_certificate_artifacts"] = []
    for message in validate_with_schema(
        schema_projection, "input", schema_dir
    ):
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "INPUT_SCHEMA_INVALID",
            message.split(":", 1)[0],
        )
    if packet.get("constraint_set_hash") != CONSTRAINT_SET_HASH:
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "INPUT_CONSTRAINT_SET_HASH_MISMATCH",
            "$.constraint_set_hash",
        )
    if packet.get("proof_whitelist_hash") != PROOF_WHITELIST_HASH:
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "INPUT_PROOF_WHITELIST_HASH_MISMATCH",
            "$.proof_whitelist_hash",
        )
    if packet.get("authority_binding") != _deep_thaw(
        authority.binding
    ):
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "EXTERNAL_AUTHORITY_BINDING_MISMATCH",
            "$.authority_binding",
        )
    if packet.get("holdout_manifest") != _deep_thaw(
        authority.holdout_manifest
    ):
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "HOLDOUT_MANIFEST_NOT_EXTERNAL_AUTHORITY_EXACT",
            "$.holdout_manifest",
        )
    if packet.get("derived_event_refs") != list(authority.event_refs):
        _issue(
            issues,
            "MEASUREMENT_INVALID",
            "DERIVED_EVENT_REFS_NOT_AUTHORITY_EXACT",
            "$.derived_event_refs",
        )

    tasks_by_id, configs_by_key, locations_by_key = _validate_manifest(
        packet, issues
    )
    authority_event_packet = {
        "observed_joint_events": authority.events,
    }
    events = _validate_events(
        authority_event_packet,
        configs_by_key,
        locations_by_key,
        issues,
    )
    exact_config_ids = packet.get("holdout_manifest", {}).get(
        "exact_six_config_ids", []
    )
    analysis_tasks = _complete_missing_configs(
        tasks_by_id, exact_config_ids
    )
    direct_non, direct_def, audit_state = _validate_certificates(
        packet,
        analysis_tasks,
        events,
        schema_dir,
        authority,
        repository_root,
        issues,
    )
    effective_non, effective_def = _effective_certificate_closure(
        analysis_tasks,
        direct_non,
        direct_def,
    )
    certificate_audit = _certificate_audit_output(
        analysis_tasks,
        direct_non,
        direct_def,
        effective_non,
        effective_def,
        audit_state,
    )
    bounds, _ = _compute_bounds(
        analysis_tasks,
        events,
        effective_non,
        effective_def,
    )
    _validate_bound_ordering(bounds, issues)
    z_d = _build_joint_completion_ir(
        "Z_D",
        analysis_tasks,
        events,
        effective_non,
        effective_def,
        issues,
    )
    z_env = _build_joint_completion_ir(
        "Z_env_structure",
        analysis_tasks,
        events,
        effective_non,
        effective_def,
        issues,
    )
    pre_structural_measurement_valid = not any(
        issue["severity"] == "MEASUREMENT_INVALID"
        for issue in issues
    )
    if pre_structural_measurement_valid:
        structural_d, structural_d_error = (
            _evaluate_structural_completion(
                z_d,
                analysis_tasks,
                authority,
            )
        )
        structural_env, structural_env_error = (
            _evaluate_structural_completion(
                z_env,
                analysis_tasks,
                authority,
            )
        )
    else:
        # A structural decision card cannot outlive the authority, manifest,
        # event, or measurement provenance from which its completion space was
        # derived.  In particular, do not enumerate a diagnostically built IR
        # after a measurement-invalid issue has already been raised.
        structural_d = _measurement_invalid_structural_evaluation(
            z_d, authority
        )
        structural_env = _measurement_invalid_structural_evaluation(
            z_env, authority
        )
        structural_d_error = (
            "STRUCTURAL_EVALUATION_BLOCKED_BY_MEASUREMENT_INVALID"
        )
        structural_env_error = (
            "STRUCTURAL_EVALUATION_BLOCKED_BY_MEASUREMENT_INVALID"
        )
    if structural_d_error is not None:
        _issue(
            issues,
            "STRUCTURAL_FAIL_CLOSED",
            structural_d_error,
            "$.Z_D",
        )
    if structural_env_error is not None:
        _issue(
            issues,
            "STRUCTURAL_FAIL_CLOSED",
            structural_env_error,
            "$.Z_env_structure",
        )
    measurement_valid = not any(
        issue["severity"] == "MEASUREMENT_INVALID"
        for issue in issues
    )
    output: Dict[str, Any] = {
        "artifact_type": "stage0f_bounds_output",
        "schema_version": SCHEMA_VERSION,
        "evaluation_mode": "SYNTHETIC_MECHANICS_ONLY",
        "research_evidence": False,
        "confirmatory_outcome_opened": False,
        "measurement_stack_frozen": False,
        "scientific_status": "MECHANICS_TEST_ONLY_NO_STEP1_INFERENCE",
        "input_sha256": canonical_sha256(packet),
        "authority_binding": _deep_thaw(authority.binding),
        "certificate_audit": certificate_audit,
        "bounds": bounds,
        "verdict_inputs": _verdicts(bounds, measurement_valid),
        "structural_verdict_inputs": {
            "C0_D": structural_d,
            "PURE_WORLD_STRUCTURE": structural_env,
        },
        "Z_D": z_d,
        "Z_env_structure": z_env,
        "issues": issues,
    }
    output["output_sha256"] = canonical_sha256(
        ["stage0f-bounds-output-v1", output]
    )
    if measurement_valid:
        output_schema_errors = validate_with_schema(
            output, "output", schema_dir
        )
        if output_schema_errors:
            raise RuntimeError(
                "internal output-schema violation: %s"
                % "; ".join(output_schema_errors)
            )
    return output


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate synthetic Stage 0F Round-4b certificate/bounds mechanics"
        )
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "schemas",
    )
    parser.add_argument(
        "--synthetic-authority-dir",
        type=Path,
        help=(
            "independently frozen synthetic authority fixture directory"
        ),
    )
    parser.add_argument(
        "--expected-authority-sha256",
        help=(
            "external commitment; never read from the bounds packet"
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        if (
            args.synthetic_authority_dir is None
            or args.expected_authority_sha256 is None
        ):
            raise ValueError(
                "external synthetic authority directory and hash are required"
            )
        authority = load_synthetic_bounds_authority(
            args.synthetic_authority_dir,
            args.expected_authority_sha256,
        )
        packet = load_json_no_duplicates(args.input)
        output = analyze_packet(
            packet,
            schema_dir=args.schema_dir,
            authority=authority,
        )
    except (
        BoundsSchemaDependencyError,
        DuplicateKeyError,
        json.JSONDecodeError,
        OSError,
        ValueError,
        RuntimeError,
    ) as exc:
        error = {
            "artifact_type": "stage0f_bounds_error",
            "status": "FAIL",
            "code": type(exc).__name__,
            "message": str(exc),
            "confirmatory_outcome_opened": False,
        }
        sys.stderr.write(
            json.dumps(error, ensure_ascii=False, sort_keys=True) + "\n"
        )
        return 2
    rendered = json.dumps(
        output,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    if args.output is None:
        sys.stdout.write(rendered)
    else:
        args.output.write_text(rendered, encoding="utf-8")
    return (
        2
        if any(
            issue["severity"] == "MEASUREMENT_INVALID"
            for issue in output["issues"]
        )
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
