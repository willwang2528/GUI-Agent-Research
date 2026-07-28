#!/usr/bin/env python3
"""Frozen packet generator for Stage 0F conditional identity redaction.

This file intentionally does not import the standalone verifier.  The verifier
reimplements the projection and alias checks so a shared helper cannot make an
incorrect packet self-certifying.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Dict, Mapping, Sequence, Tuple


SCHEMA_VERSION = "stage0f-measurement-v0.6.0-draft"
CANONICALIZATION = "stage0f-canonical-json-v1"
POLICY_ID = "stage0f-conditional-identity-redaction-v2"
ALIAS_SERIALIZATION = "stage0f-packet-alias-v1"
ATOMICITY_QUESTION_ID = "stage0f-independent-atomicity-question-v1"


class RedactionError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    def reject_float(node: Any, path: str = "$") -> None:
        if isinstance(node, float):
            raise RedactionError("%s: float is not canonical" % path)
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


def _selector_sort_key(atom: Mapping[str, Any]) -> Tuple[int, bytes]:
    return (
        int(atom["observation_ordinal"]),
        canonical_bytes(atom["selector"]),
    )


def _render(
    envelope: Mapping[str, Any],
    a0_input: Mapping[str, Any],
) -> Sequence[Dict[str, Any]]:
    observations = {
        item["observation_ordinal"]: item
        for item in a0_input["prefix_observations"]
    }
    output = []
    for atom in sorted(
        envelope["identity_evidence"]["evidence_atoms"],
        key=_selector_sort_key,
    ):
        ordinal = atom["observation_ordinal"]
        if ordinal not in observations:
            raise RedactionError("evidence ordinal is absent")
        observation = observations[ordinal]
        if atom["artifact_id"] != a0_input["artifact_id"]:
            raise RedactionError("evidence artifact mismatch")
        if atom["content_sha256"] != canonical_sha256(observation):
            raise RedactionError("evidence content mismatch")
        selector = atom["selector"]
        text = observation["agent_visible_text"]
        if selector["selector_type"] == "whole_observation":
            rendition = (
                {"rendition_type": "utf8_text", "text": text}
                if isinstance(text, str) and text
                else {
                    "rendition_type": "unavailable",
                    "reason": "agent_visible_text_missing",
                }
            )
        elif selector["selector_type"] == "text_span":
            if not isinstance(text, str):
                raise RedactionError("text selector lacks text")
            start = selector["start"]
            end = selector["end"]
            if not (0 <= start < end <= len(text)):
                raise RedactionError("text selector is invalid")
            rendition = {
                "rendition_type": "utf8_text",
                "text": text[start:end],
            }
        else:
            raise RedactionError("selector requires unsupported asset")
        output.append(
            {
                "source_observation_ordinal": ordinal,
                "rendition": rendition,
            }
        )
    return output


def _verify_side_aliases(
    side: str,
    sidecar: Mapping[str, Any],
    evidence_count: int,
) -> None:
    binding = sidecar["%s_binding" % side]
    expected_view = derive_alias(
        sidecar["alias_key_hex"],
        sidecar["alias_nonce_hex"],
        sidecar["session_slot_id"],
        "view-%s" % side,
        0,
    )
    if binding["view_alias"] != expected_view:
        raise RedactionError("view alias derivation mismatch")
    if len(binding["evidence_aliases"]) != evidence_count:
        raise RedactionError("evidence alias coverage mismatch")
    for index, item in enumerate(binding["evidence_aliases"]):
        expected = derive_alias(
            sidecar["alias_key_hex"],
            sidecar["alias_nonce_hex"],
            sidecar["session_slot_id"],
            "evidence-%s" % side,
            index,
        )
        if (
            item["evidence_index"] != index
            or item["evidence_alias"] != expected
        ):
            raise RedactionError("evidence alias derivation mismatch")


def build_review_packet(
    sidecar: Mapping[str, Any],
    left_envelope: Mapping[str, Any],
    right_envelope: Mapping[str, Any],
    a0_input: Mapping[str, Any],
) -> Dict[str, Any]:
    expected_aliases = {
        "pair_alias": derive_alias(
            sidecar["alias_key_hex"],
            sidecar["alias_nonce_hex"],
            sidecar["session_slot_id"],
            "pair",
            0,
        ),
        "packet_alias": derive_alias(
            sidecar["alias_key_hex"],
            sidecar["alias_nonce_hex"],
            sidecar["session_slot_id"],
            "packet",
            0,
        ),
        "context_alias": derive_alias(
            sidecar["alias_key_hex"],
            sidecar["alias_nonce_hex"],
            sidecar["session_slot_id"],
            "context",
            0,
        ),
    }
    for key, expected in expected_aliases.items():
        if sidecar[key] != expected:
            raise RedactionError("%s derivation mismatch" % key)

    def view(
        side: str,
        envelope: Mapping[str, Any],
    ) -> Dict[str, Any]:
        rendered = list(_render(envelope, a0_input))
        _verify_side_aliases(side, sidecar, len(rendered))
        binding = sidecar["%s_binding" % side]
        return {
            "view_alias": binding["view_alias"],
            "evidence_presentations": [
                {
                    "evidence_alias": binding["evidence_aliases"][index][
                        "evidence_alias"
                    ],
                    "source_observation_ordinal": item[
                        "source_observation_ordinal"
                    ],
                    "rendition": item["rendition"],
                }
                for index, item in enumerate(rendered)
            ],
            "temporal_interval": dict(
                envelope["identity_evidence"]["temporal_interval"]
            ),
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
