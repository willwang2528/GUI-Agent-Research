#!/usr/bin/env python3
"""Deterministic evidence verifier used by Stage 0F bounds certificates.

The parent validator verifies this file's exact SHA-256 before execution.
Requests and responses are canonical JSON on stdin/stdout.  This executable
does not accept a caller-supplied boolean result: it parses every required
evidence byte string and derives the result from the frozen mode semantics.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from stage0f_action_semantics import (
    ActionSemanticError,
    derive_action_semantics,
)


MODE_CONFIG: Mapping[str, Mapping[str, Any]] = {
    "DETERMINISTIC_PREDICATE_EVALUATOR_FALSE_V1": {
        "required_roles": ["predicate_spec", "event_ledger"],
        "result_code": "TARGET_PREDICATE_FALSE",
        "disposition": "MECHANICALLY_PREDICATE_FALSE",
        "enabled": True
    },
    "FROZEN_TRANSITION_TABLE_NO_OPPORTUNITY_V1": {
        "required_roles": ["transition_spec", "state"],
        "result_code": "NO_REACHABLE_DECISION_BOUNDARY",
        "disposition": "MECHANICALLY_NO_OPPORTUNITY",
        "enabled": False
    },
    "TYPED_EVENT_GRAMMAR_EXCLUSION_V1": {
        "required_roles": ["event_grammar", "event_record"],
        "result_code": "TARGET_EVENT_TYPE_IMPOSSIBLE",
        "disposition": "MECHANICALLY_PREDICATE_FALSE",
        "enabled": False
    },
}


class VerificationFailure(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def target_key(
    predicate_id: str,
    obligation_id: Any,
) -> str:
    return (
        predicate_id
        if obligation_id is None
        else "%s[%s]" % (predicate_id, obligation_id)
    )


def parse_evidence(
    evidence: Sequence[Mapping[str, Any]],
    expected_roles: Sequence[str],
) -> Dict[str, Tuple[Mapping[str, Any], Mapping[str, Any]]]:
    roles = [item.get("projection_role") for item in evidence]
    ordinals = [item.get("sequence_ordinal") for item in evidence]
    if roles != list(expected_roles):
        raise VerificationFailure("evidence roles/order mismatch")
    if ordinals != list(range(len(expected_roles))):
        raise VerificationFailure("evidence sequence is not exact")
    parsed: Dict[str, Tuple[Mapping[str, Any], Mapping[str, Any]]] = {}
    for item in evidence:
        try:
            raw = base64.b64decode(
                item["content_base64"], validate=True
            )
            value = json.loads(raw.decode("utf-8"))
        except (KeyError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise VerificationFailure("invalid evidence bytes") from exc
        if not isinstance(value, dict):
            raise VerificationFailure("evidence root must be an object")
        parsed[item["projection_role"]] = (item, value)
    return parsed


def verify(request: Mapping[str, Any]) -> Dict[str, Any]:
    mode = request.get("proof_mode")
    mode_config = MODE_CONFIG.get(mode)
    if mode_config is None:
        raise VerificationFailure("unknown proof mode")
    if mode_config.get("enabled") is not True:
        raise VerificationFailure(
            "proof mode disabled pending sound raw-evidence semantics"
        )
    predicate_id = request.get("predicate_id")
    obligation_id = request.get("target_obligation_id")
    key = target_key(predicate_id, obligation_id)
    evidence = request.get("evidence")
    if not isinstance(evidence, list):
        raise VerificationFailure("evidence must be an array")
    parsed = parse_evidence(
        evidence, mode_config["required_roles"]
    )

    if mode == "DETERMINISTIC_PREDICATE_EVALUATOR_FALSE_V1":
        contract_path = (
            Path(__file__).resolve().parents[1]
            / "schemas"
            / "stage0f_bounds_action_semantics.json"
        )
        contract_bytes = contract_path.read_bytes()
        contract_sha256 = hashlib.sha256(
            contract_bytes
        ).hexdigest()
        if (
            request.get("semantic_contract_sha256")
            != contract_sha256
        ):
            raise VerificationFailure(
                "action semantic contract hash mismatch"
            )
        contract = json.loads(contract_bytes.decode("utf-8"))
        spec = parsed["predicate_spec"][1]
        ledger = parsed["event_ledger"][1]
        if (
            spec
            != {
                "artifact_type": "stage0f_predicate_spec",
                "evaluator": "complete_event_ledger_v1",
                "predicate_id": predicate_id,
                "target_obligation_id": obligation_id,
            }
        ):
            raise VerificationFailure("predicate spec mismatch")
        if (
            ledger.get("artifact_type")
            != "stage0f_complete_event_ledger"
            or ledger.get("coverage") != "EXACT_LOCATION_EVENT_SET"
            or ledger.get("authority_binding")
            != request.get("authority_binding")
            or not isinstance(ledger.get("events"), list)
        ):
            raise VerificationFailure(
                "event ledger is not an exact complete event set"
            )

        def event_positive(
            event: Mapping[str, Any],
        ) -> Any:
            try:
                phenotype, confirmed_positive = (
                    derive_action_semantics(
                        event.get("p_old_status"),
                        event.get("action_assessment"),
                        contract,
                    )
                )
            except ActionSemanticError as exc:
                raise VerificationFailure(
                    "malformed primitive event"
                ) from exc
            if (
                event.get("p_old_status")
                != contract["confirmed_p_old_status"]
            ):
                return None
            if phenotype == "unidentifiable":
                return None
            return confirmed_positive

        def logical_and(*values: Any) -> Any:
            if any(value is False for value in values):
                return False
            if all(value is True for value in values):
                return True
            return None

        def matches(event: Mapping[str, Any]) -> Any:
            positive = event_positive(event)
            source_labels = event.get("source_labels")
            if source_labels == ["world_truth_changed"]:
                pure_world: Any = True
            elif (
                isinstance(source_labels, list)
                and source_labels
                and "source_unidentifiable" not in source_labels
            ):
                pure_world = False
            else:
                pure_world = None
            interface_status = event.get(
                "candidate_interface_status"
            )
            if interface_status == "QUALIFYING_CONFIRMED":
                interface: Any = True
            elif interface_status == "CONFIRMED_ABSENT":
                interface = False
            elif interface_status in {
                "QUALIFYING_COMPATIBLE",
                "UNRESOLVED",
            }:
                interface = None
            else:
                raise VerificationFailure(
                    "malformed primitive interface status"
                )
            assessments = event.get("obligation_assessments")
            if not isinstance(assessments, list):
                raise VerificationFailure(
                    "malformed primitive obligation assessments"
                )
            target_rows = [
                item
                for item in assessments
                if item.get("obligation_id") == obligation_id
            ]
            if len(target_rows) > 1:
                raise VerificationFailure(
                    "duplicate target obligation assessment"
                )
            if not target_rows:
                violated: Any = None
            else:
                behavioral = target_rows[0].get(
                    "behavioral_status"
                )
                if behavioral == "violated":
                    violated = True
                elif behavioral in {
                    "met",
                    "satisfied",
                    "not_violated",
                }:
                    violated = False
                elif behavioral == "unidentifiable":
                    violated = None
                else:
                    raise VerificationFailure(
                        "unknown obligation behavioral status"
                    )
            if predicate_id == "q_B":
                return positive
            if predicate_id == "q_C":
                return logical_and(positive, interface)
            if predicate_id == "q_env":
                return logical_and(positive, pure_world)
            if predicate_id == "q_env_interface":
                return logical_and(
                    positive, pure_world, interface
                )
            if predicate_id == "q_B_deficit":
                return logical_and(positive, violated)
            if predicate_id == "q_env_deficit":
                return logical_and(
                    positive, pure_world, violated
                )
            raise VerificationFailure("unknown predicate")

        for event in ledger["events"]:
            result = matches(event)
            if result is True:
                raise VerificationFailure(
                    "complete raw event ledger contains target witness"
                )
            if result is None:
                raise VerificationFailure(
                    "complete raw event ledger leaves target unresolved"
                )

    return {
        "serialization": "stage0f-bounds-verifier-execution-v1",
        "predicate_id": predicate_id,
        "target_obligation_id": obligation_id,
        "result_code": mode_config["result_code"],
        "disposition": mode_config["disposition"],
        "consumed_pointer_ids": [
            item["pointer_id"] for item in evidence
        ],
        "consumed_content_sha256s": [
            item["content_sha256"] for item in evidence
        ],
        "execution_status": "EXECUTED_AND_DERIVED",
    }


def main() -> int:
    try:
        request = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        if not isinstance(request, dict):
            raise VerificationFailure("request root must be an object")
        result = verify(request)
    except (
        VerificationFailure,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        sys.stderr.write(
            json.dumps(
                {
                    "status": "FAIL",
                    "error": str(exc),
                },
                sort_keys=True,
            )
            + "\n"
        )
        return 2
    sys.stdout.buffer.write(canonical_bytes(result) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
