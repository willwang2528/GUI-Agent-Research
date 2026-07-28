#!/usr/bin/env python3
"""Schema mechanics for the draft raw event identity envelope."""

from __future__ import annotations

import copy
import json
import subprocess
import unittest
from pathlib import Path

import jsonschema
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    ROOT / "schemas" / "stage0f_raw_event_identity_envelope.schema.json"
)
COMMON_PATH = ROOT / "schemas" / "stage0f_common.schema.json"


class RawEventIdentityEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.common = json.loads(COMMON_PATH.read_text(encoding="utf-8"))
        cls.registry = Registry().with_resources(
            [
                (
                    cls.common["$id"],
                    Resource.from_contents(cls.common),
                ),
                (
                    cls.schema["$id"],
                    Resource.from_contents(cls.schema),
                ),
            ]
        )

    def valid_envelope(self) -> dict:
        return {
            "artifact_type": "raw_event_identity_envelope",
            "schema_version": "stage0f-measurement-v0.6.0-draft",
            "canonicalization": "stage0f-canonical-json-v1",
            "artifact_id": "raw-envelope-001",
            "identity_stack_manifest_ref": {
                "artifact_id": "identity-stack-001",
                "sha256": "a" * 64,
            },
            "unit_alias": "U-ABCDEF012345",
            "boundary_location_id": "1" * 64,
            "a0_input_ref": {
                "artifact_id": "a0-input-001",
                "sha256": "2" * 64,
            },
            "submission_session_ref": {
                "artifact_id": "identity-submission-session-001",
                "sha256": "3" * 64,
            },
            "submission_slot_id": "c" * 64,
            "annotator_alias": "annotator-a0",
            "annotator_principal_commitment_sha256": "4" * 64,
            "raw_envelope_id": "5" * 64,
            "raw_source": {
                "relative_path": "raw/a0-label-001.json",
                "content_sha256": "6" * 64,
                "media_type": "application/json",
                "byte_length": 128,
            },
            "parser_contract": {
                "parser_id": "stage0f-raw-identity-json-parser-v1",
                "parser_executable_sha256": "d" * 64,
                "projection_id": (
                    "typed-projection-plus-identity-evidence-v1"
                ),
            },
            "parse_status": "typed_projection_valid",
            "parse_errors": [],
            "typed_projection": {
                "p_old_proposition_id": "PROP-OLD",
                "p_new_proposition_id": "PROP-NEW",
                "update_source_labels": ["world_truth_changed"],
                "normative_action_difference": (
                    "The next commit must use the new state."
                ),
                "affected_obligation_ids": ["O-KEEP-NEW"],
                "boundary_type": "action_commit",
                "grounding_mode": "blinded_human",
            },
            "identity_evidence": {
                "evidence_atoms": [],
                "target_state_variable_claims": [],
                "temporal_interval": {
                    "start_observation_ordinal": 0,
                    "end_observation_ordinal": 1,
                },
                "atomicity_claim": "unknown",
                "unanchored_discovery": True,
                "unanchored_reason": (
                    "No pre-frozen fine-grained selector is available."
                ),
            },
            "version_hashes": {
                "schema_bundle_sha256": "7" * 64,
                "codebook_sha256": "8" * 64,
                "matcher_spec_sha256": "9" * 64,
            },
            "frozen_at": "2026-07-28T14:30:00+08:00",
        }

    def validate(self, instance: dict) -> None:
        jsonschema.Draft202012Validator(
            self.schema,
            registry=self.registry,
        ).validate(instance)

    def make_anchored(self, envelope: dict) -> None:
        envelope["identity_evidence"]["evidence_atoms"] = [
            {
                "artifact_id": "observation-001",
                "observation_ordinal": 1,
                "content_sha256": "a" * 64,
                "selector": {
                    "selector_type": "dom_node",
                    "node_id": "node-42",
                },
            }
        ]
        envelope["identity_evidence"][
            "target_state_variable_claims"
        ] = [
            {
                "claim_id": "STATE-ACCOUNT",
                "statement": "The selected account state.",
                "statement_sha256": "b" * 64,
            }
        ]
        envelope["identity_evidence"]["atomicity_claim"] = "atomic"
        envelope["identity_evidence"]["unanchored_discovery"] = False
        envelope["identity_evidence"]["unanchored_reason"] = None

    def test_valid_unanchored_typed_projection(self) -> None:
        self.validate(self.valid_envelope())

    def test_invalid_projection_retains_raw_envelope_and_parse_errors(
        self,
    ) -> None:
        envelope = self.valid_envelope()
        envelope["parse_status"] = "typed_projection_invalid"
        envelope["typed_projection"] = None
        envelope["parse_errors"] = [
            {
                "code": "MISSING_P_NEW",
                "json_pointer": "/p_new_proposition_id",
            }
        ]
        self.validate(envelope)

    def test_invalid_projection_cannot_carry_typed_projection(self) -> None:
        envelope = self.valid_envelope()
        envelope["parse_status"] = "typed_projection_invalid"
        envelope["parse_errors"] = [
            {
                "code": "MISSING_P_NEW",
                "json_pointer": "/p_new_proposition_id",
            }
        ]
        with self.assertRaises(jsonschema.ValidationError):
            self.validate(envelope)

    def test_unanchored_discovery_requires_reason(self) -> None:
        envelope = self.valid_envelope()
        envelope["identity_evidence"]["unanchored_reason"] = None
        with self.assertRaises(jsonschema.ValidationError):
            self.validate(envelope)

    def test_anchored_discovery_forbids_unanchored_reason(self) -> None:
        envelope = self.valid_envelope()
        self.make_anchored(envelope)
        envelope["identity_evidence"]["unanchored_reason"] = (
            "This reason must be null for an anchored envelope."
        )
        with self.assertRaises(jsonschema.ValidationError):
            self.validate(envelope)

    def test_anchored_discovery_requires_identity_evidence(self) -> None:
        envelope = self.valid_envelope()
        envelope["identity_evidence"]["unanchored_discovery"] = False
        envelope["identity_evidence"]["unanchored_reason"] = None
        envelope["identity_evidence"]["atomicity_claim"] = "atomic"
        with self.assertRaises(jsonschema.ValidationError):
            self.validate(envelope)

    def test_valid_anchored_identity_shape(self) -> None:
        envelope = self.valid_envelope()
        self.make_anchored(envelope)
        self.validate(envelope)

    def test_additional_property_is_rejected(self) -> None:
        envelope = copy.deepcopy(self.valid_envelope())
        envelope["identity_evidence"]["outcome"] = "success"
        with self.assertRaises(jsonschema.ValidationError):
            self.validate(envelope)

    def test_schema_compiles_with_ajv2020_strict(self) -> None:
        script = r"""
const fs = require("fs");
let Ajv2020;
try {
  Ajv2020 = require("ajv/dist/2020").default;
} catch (firstError) {
  Ajv2020 = require(
    "/opt/homebrew/lib/node_modules/openclaw/node_modules/ajv/dist/2020"
  ).default;
}
const common = JSON.parse(
  fs.readFileSync("schemas/stage0f_common.schema.json", "utf8")
);
const schema = JSON.parse(
  fs.readFileSync(
    "schemas/stage0f_raw_event_identity_envelope.schema.json",
    "utf8"
  )
);
const ajv = new Ajv2020({strict: true, allErrors: true});
ajv.addSchema(common);
ajv.addSchema(schema);
if (typeof ajv.getSchema(schema.$id) !== "function") {
  throw new Error("strict compile did not produce a validator");
}
process.stdout.write("AJV2020_STRICT_PASS\n");
"""
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=str(ROOT),
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "AJV2020_STRICT_PASS")


if __name__ == "__main__":
    unittest.main()
