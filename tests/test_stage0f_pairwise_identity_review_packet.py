#!/usr/bin/env python3
"""Schema mechanics for the estimand-blind identity review packet."""

from __future__ import annotations

import copy
import json
import subprocess
import unittest
from pathlib import Path

import jsonschema
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILES = [
    "stage0f_common.schema.json",
    "stage0f_raw_event_identity_envelope.schema.json",
    "stage0f_pairwise_identity_review_packet.schema.json",
]


class PairwiseIdentityReviewPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {
            name: json.loads(
                (ROOT / "schemas" / name).read_text(encoding="utf-8")
            )
            for name in SCHEMA_FILES
        }
        cls.schema = cls.schemas[
            "stage0f_pairwise_identity_review_packet.schema.json"
        ]
        cls.registry = Registry().with_resources(
            [
                (schema["$id"], Resource.from_contents(schema))
                for schema in cls.schemas.values()
            ]
        )

    def valid_packet(self) -> dict:
        forbidden = [
            "affected_obligation_ids",
            "boundary_type",
            "candidate_action",
            "normative_action_difference",
            "outcome",
            "p_new_proposition_id",
            "p_old_proposition_id",
            "raw_source",
            "target_state_variable_claims",
            "typed_projection",
            "update_source_labels",
        ]
        identity_view = {
            "raw_envelope_ref": {
                "artifact_id": "raw-envelope-left",
                "sha256": "1" * 64,
            },
            "evidence_atoms": [
                {
                    "artifact_id": "observation-001",
                    "observation_ordinal": 1,
                    "content_sha256": "2" * 64,
                    "selector": {
                        "selector_type": "dom_node",
                        "node_id": "node-42",
                    },
                }
            ],
            "temporal_interval": {
                "start_observation_ordinal": 0,
                "end_observation_ordinal": 1,
            },
            "atomicity_evidence_refs": [],
        }
        packet = {
            "artifact_type": "pairwise_identity_review_packet",
            "schema_version": "stage0f-measurement-v0.6.0-draft",
            "canonicalization": "stage0f-canonical-json-v1",
            "artifact_id": "identity-review-packet-001",
            "pair_id": "3" * 64,
            "unit_alias": "U-ABCDEF012345",
            "boundary_location_id": "4" * 64,
            "reviewer_visible_a0_input_ref": {
                "artifact_id": "a0-review-input-001",
                "sha256": "5" * 64,
            },
            "left_identity_view": identity_view,
            "right_identity_view": copy.deepcopy(identity_view),
            "redaction_contract": {
                "policy_id": (
                    "stage0f-estimand-blind-identity-redaction-v1"
                ),
                "policy_sha256": "6" * 64,
                "executable_sha256": "7" * 64,
                "input_pair_projection_sha256": "8" * 64,
                "output_packet_projection_sha256": "9" * 64,
                "forbidden_field_names": forbidden,
            },
            "frozen_at": "2026-07-28T15:00:00+08:00",
        }
        packet["right_identity_view"]["raw_envelope_ref"] = {
            "artifact_id": "raw-envelope-right",
            "sha256": "a" * 64,
        }
        return packet

    def validate(self, packet: dict) -> None:
        jsonschema.Draft202012Validator(
            self.schema,
            registry=self.registry,
        ).validate(packet)

    def test_valid_estimand_blind_packet_shape(self) -> None:
        self.validate(self.valid_packet())

    def test_substantive_projection_is_rejected(self) -> None:
        packet = self.valid_packet()
        packet["left_identity_view"]["typed_projection"] = {
            "p_new_proposition_id": "PROP-LEAK"
        }
        with self.assertRaises(jsonschema.ValidationError):
            self.validate(packet)

    def test_raw_source_is_rejected(self) -> None:
        packet = self.valid_packet()
        packet["right_identity_view"]["raw_source"] = {
            "relative_path": "raw/label.json"
        }
        with self.assertRaises(jsonschema.ValidationError):
            self.validate(packet)

    def test_forbidden_field_roster_cannot_be_shortened(self) -> None:
        packet = self.valid_packet()
        packet["redaction_contract"]["forbidden_field_names"].pop()
        with self.assertRaises(jsonschema.ValidationError):
            self.validate(packet)

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
const names = [
  "stage0f_common.schema.json",
  "stage0f_raw_event_identity_envelope.schema.json",
  "stage0f_pairwise_identity_review_packet.schema.json"
];
const schemas = names.map((name) => JSON.parse(
  fs.readFileSync("schemas/" + name, "utf8")
));
const ajv = new Ajv2020({strict: true, allErrors: true});
for (const schema of schemas) {
  ajv.addSchema(schema);
}
const target = schemas[2];
if (typeof ajv.getSchema(target.$id) !== "function") {
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
