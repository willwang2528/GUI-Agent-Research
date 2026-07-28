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
        identity_view = {
            "view_alias": "1" * 64,
            "evidence_presentations": [
                {
                    "evidence_alias": "2" * 64,
                    "source_observation_ordinal": 1,
                    "rendition": {
                        "rendition_type": "utf8_text",
                        "text": "Account state changed.",
                    },
                }
            ],
            "temporal_interval": {
                "start_observation_ordinal": 0,
                "end_observation_ordinal": 1,
            },
            "atomicity_question_id": (
                "stage0f-independent-atomicity-question-v1"
            ),
        }
        packet = {
            "artifact_type": "pairwise_identity_review_packet",
            "schema_version": "stage0f-measurement-v0.6.0-draft",
            "canonicalization": "stage0f-canonical-json-v1",
            "artifact_id": "identity-packet-" + "3" * 64,
            "packet_alias": "3" * 64,
            "pair_alias": "4" * 64,
            "context_alias": "5" * 64,
            "review_protocol_id": (
                "stage0f-isolated-pairwise-identity-review-v1"
            ),
            "redaction_policy_id": (
                "stage0f-conditional-identity-redaction-v2"
            ),
            "left_identity_view": identity_view,
            "right_identity_view": copy.deepcopy(identity_view),
        }
        packet["right_identity_view"]["view_alias"] = "6" * 64
        packet["right_identity_view"]["evidence_presentations"][0][
            "evidence_alias"
        ] = "7" * 64
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

    def test_secret_bearing_raw_envelope_hash_is_rejected(self) -> None:
        packet = self.valid_packet()
        packet["left_identity_view"]["raw_envelope_ref"] = {
            "artifact_id": "raw-envelope-left",
            "sha256": "8" * 64,
        }
        with self.assertRaises(jsonschema.ValidationError):
            self.validate(packet)

    def test_public_input_projection_hash_is_rejected(self) -> None:
        packet = self.valid_packet()
        packet["input_pair_projection_sha256"] = "9" * 64
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
