#!/usr/bin/env python3
"""Executable red-team tests for standalone identity mechanics L2."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from tools import verify_stage0f_identity_mechanics as I


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


class IdentityMechanicsFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.schemas, self.registry = I.load_schemas()
        self.manifest = I.build_manifest(
            "2026-07-28T16:00:00+08:00",
            self.schemas,
        )
        self.a0_input = self._a0_input()
        self.left_source = self._raw_source(
            p_old="PROP-OLD-L",
            p_new="PROP-NEW-L",
            obligation="O-LEFT",
        )
        self.right_source = self._raw_source(
            p_old="PROP-OLD-R",
            p_new="PROP-NEW-R",
            obligation="O-RIGHT",
        )
        self.left_bytes = I.canonical_bytes(self.left_source)
        self.right_bytes = I.canonical_bytes(self.right_source)
        (self.root / "raw").mkdir(parents=True)
        (self.root / "raw" / "left.json").write_bytes(self.left_bytes)
        (self.root / "raw" / "right.json").write_bytes(self.right_bytes)
        self.left_session = I.build_submission_session(
            self.manifest,
            self.a0_input,
            "left",
            "annotator-left",
            digest("principal-left"),
            "append-channel-left",
            0,
            [("raw/left.json", self.left_bytes)],
            "2026-07-28T16:01:00+08:00",
            "2026-07-28T16:02:00+08:00",
            "2026-07-28T16:03:00+08:00",
            "2026-07-28T16:04:00+08:00",
        )
        self.right_session = I.build_submission_session(
            self.manifest,
            self.a0_input,
            "right",
            "annotator-right",
            digest("principal-right"),
            "append-channel-right",
            0,
            [("raw/right.json", self.right_bytes)],
            "2026-07-28T16:01:00+08:00",
            "2026-07-28T16:02:00+08:00",
            "2026-07-28T16:03:00+08:00",
            "2026-07-28T16:04:00+08:00",
        )
        self.left_envelope = I.build_raw_envelope(
            self.manifest,
            self.a0_input,
            self.left_session,
            0,
            self.left_bytes,
            "2026-07-28T16:05:00+08:00",
            self.registry,
        )
        self.right_envelope = I.build_raw_envelope(
            self.manifest,
            self.a0_input,
            self.right_session,
            0,
            self.right_bytes,
            "2026-07-28T16:05:00+08:00",
            self.registry,
        )
        self.left_receipt = I.verify_raw_envelope(
            self.root,
            self.left_envelope,
            self.left_session,
            self.manifest,
            self.a0_input,
            self.registry,
            "2026-07-28T16:06:00+08:00",
        )
        self.right_receipt = I.verify_raw_envelope(
            self.root,
            self.right_envelope,
            self.right_session,
            self.manifest,
            self.a0_input,
            self.registry,
            "2026-07-28T16:06:00+08:00",
        )
        self.sidecar = I.build_alias_sidecar(
            self.manifest,
            self.a0_input,
            self.left_session,
            self.right_session,
            self.left_envelope,
            self.right_envelope,
            self.left_receipt,
            self.right_receipt,
            digest("alias-key"),
            digest("alias-nonce"),
            digest("reviewer-session-slot"),
        )
        self.packet = I.build_review_packet(
            self.sidecar,
            self.left_envelope,
            self.right_envelope,
            self.a0_input,
        )
        self.redaction_receipt = I.build_redaction_receipt(
            self.manifest,
            self.sidecar,
            self.left_receipt,
            self.right_receipt,
            self.packet,
            self.left_envelope,
            self.right_envelope,
            self.a0_input,
            "2026-07-28T16:07:00+08:00",
        )
        self.write_bundle()

    def _a0_input(self) -> dict:
        instruction = "Use the account state visible before the next action."
        source = "The next action must use the current account state."
        observations = [
            {
                "observation_ordinal": 0,
                "observed_at": "2026-07-28T15:58:00+08:00",
                "assets": [],
                "agent_visible_text": "Account state is OLD.",
                "normalized_prior_actions": [],
                "missingness": "none",
            },
            {
                "observation_ordinal": 1,
                "observed_at": "2026-07-28T15:59:00+08:00",
                "assets": [],
                "agent_visible_text": "Account state changed to NEW.",
                "normalized_prior_actions": ["Open account selector."],
                "missingness": "none",
            },
        ]
        return {
            "artifact_type": "a0_input",
            "schema_version": I.SCHEMA_VERSION,
            "canonicalization": I.CANONICALIZATION,
            "artifact_id": "a0-input-identity-mechanics",
            "source_protocol": (
                "stage0f_osworld2_natural_burden_preregistration.md@v0.6"
            ),
            "unit_alias": "U-ABCDEF012345",
            "coordinator_envelope_commitment_sha256": digest(
                "coordinator-envelope"
            ),
            "prefix_commit_log_id": "prefix-log-identity-mechanics",
            "prefix_chain_tip_sha256": digest("prefix-tip"),
            "boundary_namespace": "stage0f:identity-mechanics",
            "a0_prefix_payload_sha256": digest("prefix-payload"),
            "boundary_location_id": digest("boundary-location"),
            "agent_visible_instruction": {
                "text": instruction,
                "content_sha256": I.text_sha256(instruction),
            },
            "normative_schema": {
                "version": "identity-mechanics-v1",
                "sources": [
                    {
                        "source_ref_id": "source-identity-mechanics",
                        "source_class": "agent_visible_instruction",
                        "content": source,
                        "content_sha256": I.text_sha256(source),
                    }
                ],
                "obligations": [
                    {
                        "obligation_id": "O-USE-CURRENT",
                        "predicate": "Use current account state.",
                        "applicability": "At the next commit.",
                        "deadline_or_commit": "Before current action.",
                        "source_ref_ids": ["source-identity-mechanics"],
                    }
                ],
            },
            "prefix_observations": observations,
            "cutoff_observation_ordinal": 1,
            "candidate_locator": {
                "update_observation_ordinal": 1,
                "selection_rule": "Frozen before any candidate action.",
            },
            "allowed_probes": [],
            "exposure_class": "a0_normative_only",
            "frozen_at": "2026-07-28T16:00:00+08:00",
        }

    def _raw_source(
        self,
        p_old: str,
        p_new: str,
        obligation: str,
    ) -> dict:
        observation = self.a0_input["prefix_observations"][1]
        statement = "The account state changed."
        return {
            "typed_projection": {
                "p_old_proposition_id": p_old,
                "p_new_proposition_id": p_new,
                "update_source_labels": ["world_truth_changed"],
                "normative_action_difference": (
                    "The next action must use NEW."
                ),
                "affected_obligation_ids": [obligation],
                "boundary_type": "action_commit",
                "grounding_mode": "blinded_human",
            },
            "identity_evidence": {
                "evidence_atoms": [
                    {
                        "artifact_id": self.a0_input["artifact_id"],
                        "observation_ordinal": 1,
                        "content_sha256": I.canonical_sha256(observation),
                        "selector": {
                            "selector_type": "text_span",
                            "start": 0,
                            "end": len(
                                observation["agent_visible_text"]
                            ),
                        },
                    }
                ],
                "target_state_variable_claims": [
                    {
                        "claim_id": "STATE-ACCOUNT",
                        "statement": statement,
                        "statement_sha256": I.text_sha256(statement),
                    }
                ],
                "temporal_interval": {
                    "start_observation_ordinal": 1,
                    "end_observation_ordinal": 1,
                },
                "atomicity_claim": "atomic",
                "unanchored_discovery": False,
                "unanchored_reason": None,
            },
        }

    def write_bundle(self) -> None:
        values = {
            "manifest": self.manifest,
            "a0_input": self.a0_input,
            "left_session": self.left_session,
            "right_session": self.right_session,
            "left_envelope": self.left_envelope,
            "right_envelope": self.right_envelope,
            "left_raw_receipt": self.left_receipt,
            "right_raw_receipt": self.right_receipt,
            "sidecar": self.sidecar,
            "packet": self.packet,
            "redaction_receipt": self.redaction_receipt,
        }
        for key, filename in I.BUNDLE_FILES.items():
            write_json(self.root / filename, values[key])


class IdentityMechanicsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fixture = IdentityMechanicsFixture(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def report(self) -> dict:
        return I.verify_bundle(self.root)

    def assert_code(self, expected: str) -> None:
        report = self.report()
        self.assertFalse(report["valid"], report)
        self.assertEqual(report["errors"][0]["code"], expected, report)

    def test_valid_bundle_reaches_l2_only(self) -> None:
        report = self.report()
        self.assertTrue(report["valid"], report)
        self.assertEqual(
            report["mechanics_level"],
            "L2_REDACTION_MECHANICS_PASS",
        )
        self.assertEqual(
            report["pair_universe_authority"],
            "NOT_ESTABLISHED_NO_COMPLETE_PAIR_LEDGER",
        )
        self.assertEqual(
            report["integration_status"],
            "NOT_INTEGRATED_NO_A0_BARRIER",
        )
        self.assertFalse(report["downstream_eligible"])
        self.assertFalse(report["primary_reliability_eligibility"])
        self.assertIn("NO STEP 1 GO", report["claim_ceiling"])

    def test_public_packet_has_no_real_refs_or_projection_hashes(self) -> None:
        packet = self.fixture.packet
        serialized = json.dumps(packet, sort_keys=True)
        forbidden_keys = [
            "raw_envelope_ref",
            "unit_alias",
            "boundary_location_id",
            "input_pair_projection_sha256",
            "output_packet_projection_sha256",
            "typed_projection",
            "target_state_variable_claims",
            "frozen_at",
        ]
        for key in forbidden_keys:
            self.assertNotIn(key, serialized)
        I.assert_no_private_value_visible(
            packet,
            I._private_sensitive_values(
                self.fixture.manifest,
                self.fixture.a0_input,
                [
                    self.fixture.left_session,
                    self.fixture.right_session,
                ],
                [
                    self.fixture.left_envelope,
                    self.fixture.right_envelope,
                ],
            ),
        )

    def test_forbidden_projection_mutation_is_transcript_invariant(
        self,
    ) -> None:
        baseline = I.canonical_bytes(
            I.reviewer_transcript(self.fixture.packet)
        )
        mutated = I._mutate_forbidden_projection(
            self.fixture.left_envelope,
            "test",
        )
        packet = I.build_review_packet(
            self.fixture.sidecar,
            mutated,
            self.fixture.right_envelope,
            self.fixture.a0_input,
        )
        self.assertEqual(
            I.canonical_bytes(I.reviewer_transcript(packet)),
            baseline,
        )

    def test_allowed_projection_mutation_changes_packet(self) -> None:
        mutated = copy.deepcopy(self.fixture.left_envelope)
        mutated["identity_evidence"]["temporal_interval"][
            "start_observation_ordinal"
        ] = 0
        packet = I.build_review_packet(
            self.fixture.sidecar,
            mutated,
            self.fixture.right_envelope,
            self.fixture.a0_input,
        )
        self.assertNotEqual(packet, self.fixture.packet)

    def test_schema_valid_packet_value_tamper_fails_exact_replay(self) -> None:
        packet = copy.deepcopy(self.fixture.packet)
        packet["context_alias"] = digest("malicious-context-alias")
        write_json(self.root / I.BUNDLE_FILES["packet"], packet)
        self.assert_code("SEM_A0_IDENTITY_REDACTION_OUTPUT_MISMATCH")

    def test_raw_byte_tamper_fails_same_buffer_hash(self) -> None:
        (self.root / "raw" / "left.json").write_bytes(
            self.fixture.left_bytes + b" "
        )
        self.assert_code("HASH_A0_RAW_BYTES_HASH_LENGTH")

    def test_raw_source_symlink_is_rejected(self) -> None:
        target = self.root / "raw" / "left-real.json"
        target.write_bytes(self.fixture.left_bytes)
        (self.root / "raw" / "left.json").unlink()
        os.symlink(target.name, self.root / "raw" / "left.json")
        self.assert_code("IO_A0_RAW_SOURCE_SYMLINK")

    def test_raw_duplicate_key_parser_preserves_invalid_status(self) -> None:
        raw = (
            b'{"typed_projection":{},"typed_projection":{},'
            b'"identity_evidence":{}}'
        )
        status, errors, typed, identity = I.parse_raw_identity_bytes(
            raw,
            1,
            self.fixture.registry,
        )
        self.assertEqual(status, "typed_projection_invalid")
        self.assertIsNone(typed)
        self.assertEqual(errors[0]["code"], "RAW_JSON_DUPLICATE_KEY")
        self.assertTrue(identity["unanchored_discovery"])

    def test_reversed_interval_is_rejected_from_raw_source(self) -> None:
        source = copy.deepcopy(self.fixture.left_source)
        source["identity_evidence"]["temporal_interval"] = {
            "start_observation_ordinal": 1,
            "end_observation_ordinal": 0,
        }
        raw = I.canonical_bytes(source)
        (self.root / "raw" / "left.json").write_bytes(raw)
        session = I.build_submission_session(
            self.fixture.manifest,
            self.fixture.a0_input,
            "left",
            "annotator-left",
            digest("principal-left"),
            "append-channel-left",
            0,
            [("raw/left.json", raw)],
            "2026-07-28T16:01:00+08:00",
            "2026-07-28T16:02:00+08:00",
            "2026-07-28T16:03:00+08:00",
            "2026-07-28T16:04:00+08:00",
        )
        envelope = I.build_raw_envelope(
            self.fixture.manifest,
            self.fixture.a0_input,
            session,
            0,
            raw,
            "2026-07-28T16:05:00+08:00",
            self.fixture.registry,
        )
        with self.assertRaises(I.MechanicsError) as caught:
            I.verify_raw_envelope(
                self.root,
                envelope,
                session,
                self.fixture.manifest,
                self.fixture.a0_input,
                self.fixture.registry,
                "2026-07-28T16:06:00+08:00",
            )
        self.assertEqual(
            caught.exception.code,
            "SEM_A0_IDENTITY_REVIEW_INTERVAL_ORDER",
        )

    def test_evidence_after_cutoff_is_rejected(self) -> None:
        envelope = copy.deepcopy(self.fixture.left_envelope)
        envelope["identity_evidence"]["temporal_interval"][
            "end_observation_ordinal"
        ] = 2
        with self.assertRaises(I.MechanicsError) as caught:
            I._validate_and_render_evidence(
                envelope,
                self.fixture.a0_input,
            )
        self.assertEqual(
            caught.exception.code,
            "SEM_A0_IDENTITY_REVIEW_CUTOFF",
        )

    def test_reversed_text_span_is_rejected(self) -> None:
        envelope = copy.deepcopy(self.fixture.left_envelope)
        selector = envelope["identity_evidence"]["evidence_atoms"][0][
            "selector"
        ]
        selector["start"] = 10
        selector["end"] = 2
        with self.assertRaises(I.MechanicsError) as caught:
            I._validate_and_render_evidence(
                envelope,
                self.fixture.a0_input,
            )
        self.assertEqual(
            caught.exception.code,
            "SEM_A0_IDENTITY_REVIEW_SELECTOR_INVALID",
        )

    def test_dom_without_verified_asset_is_rejected(self) -> None:
        envelope = copy.deepcopy(self.fixture.left_envelope)
        envelope["identity_evidence"]["evidence_atoms"][0]["selector"] = {
            "selector_type": "dom_node",
            "node_id": "node-42",
        }
        with self.assertRaises(I.MechanicsError) as caught:
            I._validate_and_render_evidence(
                envelope,
                self.fixture.a0_input,
            )
        self.assertEqual(
            caught.exception.code,
            "SEM_A0_IDENTITY_REVIEW_SELECTOR_UNSUPPORTED",
        )

    def test_statement_hash_is_recomputed(self) -> None:
        envelope = copy.deepcopy(self.fixture.left_envelope)
        envelope["identity_evidence"][
            "target_state_variable_claims"
        ][0]["statement_sha256"] = digest("wrong")
        with self.assertRaises(I.MechanicsError) as caught:
            I._validate_and_render_evidence(
                envelope,
                self.fixture.a0_input,
            )
        self.assertEqual(caught.exception.code, "SEM_A0_RAW_STATEMENT_HASH")

    def test_slot_chain_tamper_is_rejected(self) -> None:
        session = copy.deepcopy(self.fixture.left_session)
        session["slots"][0]["slot_entry_sha256"] = digest("tampered")
        write_json(
            self.root / I.BUNDLE_FILES["left_session"],
            session,
        )
        self.assert_code("SEM_A0_IDENTITY_SLOT_CHAIN")

    def test_alias_collision_is_rejected(self) -> None:
        sidecar = copy.deepcopy(self.fixture.sidecar)
        sidecar["right_binding"]["view_alias"] = sidecar[
            "left_binding"
        ]["view_alias"]
        write_json(self.root / I.BUNDLE_FILES["sidecar"], sidecar)
        self.assert_code("SEM_A0_IDENTITY_REVIEW_ALIAS_COLLISION")

    def test_alias_derivation_tamper_is_rejected(self) -> None:
        sidecar = copy.deepcopy(self.fixture.sidecar)
        sidecar["pair_alias"] = digest("raw-envelope-hash-derived")
        write_json(self.root / I.BUNDLE_FILES["sidecar"], sidecar)
        self.assert_code("SEM_A0_IDENTITY_ALIAS_DERIVATION")

    def test_local_alias_rng_does_not_claim_no_grinding(self) -> None:
        report = self.report()
        self.assertEqual(
            report["alias_randomness"],
            "KEY_GRINDING_AND_ORIGIN_UNATTESTED",
        )
        self.assertEqual(
            self.fixture.redaction_receipt["authority"][
                "alias_randomness"
            ],
            "key_grinding_and_origin_unattested",
        )

    def test_allowed_projection_laundering_stays_partial(self) -> None:
        report = self.report()
        self.assertEqual(
            report["allowed_projection_provenance"],
            "PARTIAL_ANNOTATOR_SELECTED",
        )
        self.assertFalse(report["downstream_eligible"])

    def test_receipt_cannot_upgrade_matcher_or_reliability(self) -> None:
        receipt = self.fixture.redaction_receipt
        self.assertEqual(
            receipt["matcher_authority"],
            "not_established_no_frozen_case_matcher",
        )
        self.assertEqual(
            receipt["agreement_completeness"],
            "not_established_no_frozen_case_matcher",
        )
        self.assertEqual(
            receipt["pair_universe_authority"],
            "not_established_no_complete_pair_ledger",
        )
        self.assertFalse(receipt["primary_reliability_eligibility"])

    def test_identity_schemas_compile_strictly(self) -> None:
        I.validate_schema_set(self.fixture.schemas, self.fixture.registry)


if __name__ == "__main__":
    unittest.main()
