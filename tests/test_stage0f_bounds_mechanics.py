#!/usr/bin/env python3
"""Round-4b synthetic tests for fail-closed bounds mechanics.

Every fixture is synthetic and carries no scientific evidentiary weight.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, MutableMapping, Optional


ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "tools" / "stage0f_bounds_mechanics.py"
SCHEMA_DIR = ROOT / "schemas"
CASE_PATH = (
    ROOT / "tests" / "fixtures" / "stage0f_bounds_negative_cases.json"
)

SPEC = importlib.util.spec_from_file_location(
    "stage0f_bounds_mechanics", TOOL_PATH
)
assert SPEC is not None and SPEC.loader is not None
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def digest(label: str) -> str:
    return hashlib.sha256(
        ("stage0f-bounds-synthetic:" + label).encode("utf-8")
    ).hexdigest()


class SyntheticBoundsPacket:
    CONFIG_IDS = ["Config-%s" % letter for letter in "ABCDEF"]

    def __init__(
        self,
        task_count: int = 1,
        ordinal_count: int = 2,
    ) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.authority_dir = Path(self._temporary.name)
        tasks: List[Dict[str, Any]] = []
        for task_index in range(task_count):
            task_id = "Task-%03d" % task_index
            configs: List[Dict[str, Any]] = []
            for config_index, config_id in enumerate(self.CONFIG_IDS):
                unit_id = "Unit-%03d-%s" % (
                    task_index,
                    chr(ord("A") + config_index),
                )
                locations = []
                for ordinal in range(ordinal_count):
                    pointer = {
                        "pointer_id": "Pointer-%03d-%s-%02d"
                        % (task_index, chr(ord("A") + config_index), ordinal),
                        "artifact_id": "Artifact-%03d-%s"
                        % (task_index, chr(ord("A") + config_index)),
                        "observation_ordinal": ordinal,
                        "content_sha256": digest(
                            "%s:%s:%d" % (task_id, config_id, ordinal)
                        ),
                        "projection_role": "observation",
                        "sequence_ordinal": 0,
                    }
                    locations.append(
                        {
                            "observation_ordinal": ordinal,
                            "location_id": "Location-%03d-%s-%02d"
                            % (
                                task_index,
                                chr(ord("A") + config_index),
                                ordinal,
                            ),
                            "evidence_pointers": [pointer],
                        }
                    )
                configs.append(
                    {
                        "config_id": config_id,
                        "unit_id": unit_id,
                        "obligation_status": "FROZEN_NONEMPTY",
                        "applicable_obligation_ids": ["O-PRIMARY"],
                        "ordinal_locations": locations,
                        "unit_ordinal_roster_sha256": digest(
                            "placeholder-roster"
                        ),
                        "trajectory_hash_chain_root": digest(
                            "placeholder-chain"
                        ),
                    }
                )
            tasks.append(
                {
                    "task_id": task_id,
                    "configs": configs,
                    "task_manifest_sha256": digest(
                        "placeholder-task"
                    ),
                }
            )
        manifest: Dict[str, Any] = {
            "manifest_id": "Manifest-Synthetic",
            "task_roster_sha256": digest("placeholder-task-roster"),
            "exact_six_config_ids": list(self.CONFIG_IDS),
            "exact_six_config_ids_sha256": digest(
                "placeholder-config-roster"
            ),
            "tasks": tasks,
            "manifest_sha256": digest("placeholder-manifest"),
        }
        M.seal_holdout_manifest(manifest)
        config_families = {
            "Config-A": "Anthropic",
            "Config-B": "Anthropic",
            "Config-C": "Anthropic",
            "Config-D": "OpenAI",
            "Config-E": "MiniMax",
            "Config-F": "Qwen",
        }
        self.authority_document: Dict[str, Any] = {
            "artifact_type": "stage0f_bounds_trusted_authority",
            "authority_kind": "SYNTHETIC_TRUSTED_FIXTURE",
            "schema_version": M.SCHEMA_VERSION,
            "full_block_binding": {
                "frame_sha256": digest("authority-frame"),
                "manifest_sha256": digest("authority-manifest"),
                "a0_barrier_sha256": digest("authority-a0-barrier"),
                "a1_barrier_sha256": digest("authority-a1-barrier"),
                "stream_roots_sha256": digest("authority-stream-roots"),
                "full_block_validator_sha256": digest(
                    "authority-full-block-validator"
                ),
                "full_block_bundle_sha256": digest(
                    "authority-full-block-bundle"
                ),
            },
            "holdout_manifest": copy.deepcopy(manifest),
            "event_sources": [],
            "evidence_assets": [],
            "proof_projections": [],
            "structural_mapping": {
                "mapping_version": "synthetic-structural-v1",
                "enumeration_limit": 20,
                "model_family_codebook_sha256": (
                    M.FROZEN_MODEL_FAMILY_CODEBOOK_HASH
                ),
                "task_mappings": [
                    {
                        "task_id": "Task-%03d" % task_index,
                        "structural_group": "Group-%03d"
                        % task_index,
                        "site_app_set": "Site-%d"
                        % (task_index % 3),
                    }
                    for task_index in range(task_count)
                ],
                "config_mappings": [
                    {
                        "config_id": config_id,
                        "model_family": config_families[config_id],
                    }
                    for config_id in self.CONFIG_IDS
                ],
            },
        }
        self.packet: Dict[str, Any] = {
            "artifact_type": "stage0f_bounds_input",
            "schema_version": M.SCHEMA_VERSION,
            "canonicalization": M.CANONICALIZATION,
            "evaluation_mode": "SYNTHETIC_MECHANICS_ONLY",
            "research_evidence": False,
            "confirmatory_outcome_opened": False,
            "measurement_stack_frozen": False,
            "constraint_set_hash": M.CONSTRAINT_SET_HASH,
            "proof_whitelist_hash": M.PROOF_WHITELIST_HASH,
            "authority_binding": {},
            "holdout_manifest": copy.deepcopy(manifest),
            "derived_event_refs": [],
            "negative_certificate_artifacts": [],
        }
        self._primitive_events_by_location: Dict[
            tuple, List[Dict[str, Any]]
        ] = {}
        self._sync_authority()

    def _write_json_asset(
        self,
        relative_path: str,
        value: Dict[str, Any],
    ) -> Dict[str, str]:
        path = self.authority_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        content = M.canonical_bytes(value)
        path.write_bytes(content)
        return {
            "relative_path": relative_path,
            "sha256": hashlib.sha256(content).hexdigest(),
        }

    def _sync_authority(self) -> None:
        authority_path = self.authority_dir / "authority.json"
        authority_path.write_bytes(
            M.canonical_bytes(self.authority_document)
        )
        self.expected_authority_sha256 = M.canonical_sha256(
            self.authority_document
        )
        self.authority = M.load_synthetic_bounds_authority(
            self.authority_dir,
            self.expected_authority_sha256,
        )
        self.packet["authority_binding"] = M._deep_thaw(
            self.authority.binding
        )
        self.packet["holdout_manifest"] = M._deep_thaw(
            self.authority.holdout_manifest
        )
        self.packet["derived_event_refs"] = list(
            self.authority.event_refs
        )

    def set_events(self, events: List[Dict[str, Any]]) -> None:
        event_sources = []
        primitive_by_location: Dict[tuple, List[Dict[str, Any]]] = {}
        for index, event in enumerate(events):
            event_id = digest(
                "authority-event:%s:%d" % (event["event_key"], index)
            )
            location_id = event["location_id"]
            source_status = event["source_status"]
            source_labels = {
                "PURE_WORLD_CONFIRMED": ["world_truth_changed"],
                "PURE_WORLD_COMPATIBLE": ["world_truth_changed"],
                "MIXED_WORLD_CONFIRMED": [
                    "world_truth_changed",
                    "task_goal_changed",
                ],
                "NON_WORLD_CONFIRMED": ["task_goal_changed"],
                "SOURCE_UNKNOWN": ["source_unidentifiable"],
                "INVALID_SOURCE_MEASUREMENT": [],
            }[source_status]
            b_status = event["b_status"]
            if b_status == "CONFIRMED_POSITIVE":
                positive = True
                phenotype = "target_positive"
            elif b_status == "CONFIRMED_NEGATIVE":
                positive = False
                phenotype = "target_negative"
            else:
                positive = False
                phenotype = "unidentifiable"
            interface_value = {
                "QUALIFYING_CONFIRMED": "confirmed",
                "QUALIFYING_COMPATIBLE": "compatible",
                "CONFIRMED_ABSENT": "absent",
                "UNRESOLVED": "unresolved",
            }[event["same_event_interface_status"]]
            confirmed = set(
                event["b_unmet_obligation_ids_confirmed"]
            )
            compatible = set(
                event["b_unmet_obligation_ids_compatible"]
            )
            all_obligations = sorted(confirmed | compatible)
            assessments = [
                {
                    "obligation_id": obligation_id,
                    "behavioral_status": (
                        "violated"
                        if obligation_id in confirmed
                        else "unidentifiable"
                    ),
                }
                for obligation_id in all_obligations
            ]
            if b_status == "CONFIRMED_POSITIVE":
                action_assessment = {
                    "candidate_action_executed": True,
                    "compatible_with_p_old": "yes",
                    "compatible_with_p_new": "no",
                    "required_action_omission": False,
                    "deadline_or_commit_reached": True,
                }
                p_old_status = "pre_update_frozen"
            elif b_status == "CONFIRMED_NEGATIVE":
                action_assessment = {
                    "candidate_action_executed": True,
                    "compatible_with_p_old": "no",
                    "compatible_with_p_new": "yes",
                    "required_action_omission": False,
                    "deadline_or_commit_reached": True,
                }
                p_old_status = "pre_update_frozen"
            else:
                action_assessment = {
                    "candidate_action_executed": True,
                    "compatible_with_p_old": "unidentifiable",
                    "compatible_with_p_new": "unidentifiable",
                    "required_action_omission": False,
                    "deadline_or_commit_reached": True,
                }
                p_old_status = "old_state_hypothesized"
            primitive_by_location.setdefault(
                (
                    event["task_id"],
                    event["config_id"],
                    location_id,
                ),
                [],
            ).append(
                {
                    "adjudicated_event_id": event_id,
                    "p_old_status": p_old_status,
                    "source_labels": source_labels,
                    "action_assessment": action_assessment,
                    "candidate_interface_status": event[
                        "same_event_interface_status"
                    ],
                    "obligation_assessments": assessments,
                }
            )
            base = "events/event-%03d" % index
            a0_ref = self._write_json_asset(
                base + "-a0.json",
                {
                    "artifact_type": "synthetic_verified_a0",
                    "adjudicated_event_id": event_id,
                    "boundary_location_id": location_id,
                    "p_old_status": p_old_status,
                    "source_labels": source_labels,
                },
            )
            a1_ref = self._write_json_asset(
                base + "-a1.json",
                {
                    "artifact_type": "synthetic_verified_a1",
                    "adjudicated_event_id": event_id,
                    "boundary_location_id": location_id,
                    "primary_uacf_d_positive": positive,
                    "phenotype": phenotype,
                    "action_assessment": action_assessment,
                    "affected_obligation_assessments": assessments,
                },
            )
            interface_ref = self._write_json_asset(
                base + "-interface.json",
                {
                    "artifact_type": (
                        "synthetic_frozen_candidate_interface"
                    ),
                    "adjudicated_event_id": event_id,
                    "boundary_location_id": location_id,
                    "qualifying_interface": interface_value,
                },
            )
            event_sources.append(
                {
                    "task_id": event["task_id"],
                    "config_id": event["config_id"],
                    "unit_id": event["unit_id"],
                    "location_id": location_id,
                    "adjudicated_event_id": event_id,
                    "a0_ref": a0_ref,
                    "a1_ref": a1_ref,
                    "interface_ref": interface_ref,
                }
            )
        self.authority_document["event_sources"] = event_sources
        self._primitive_events_by_location = primitive_by_location
        # Event ledgers already frozen for a certificate must track the
        # authoritative source projection.  Their external pointer hashes are
        # updated, while any previously issued certificate remains stale and
        # therefore fails closed.
        for asset in self.authority_document["evidence_assets"]:
            pointer = asset["pointer"]
            if pointer["projection_role"] != "event_ledger":
                continue
            ledger_path = self.authority_dir / asset["relative_path"]
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            location_key = (
                ledger["task_id"],
                ledger["config_id"],
                ledger["location_id"],
            )
            ledger["events"] = copy.deepcopy(
                primitive_by_location.get(location_key, [])
            )
            content = M.canonical_bytes(ledger)
            ledger_path.write_bytes(content)
            pointer["content_sha256"] = hashlib.sha256(
                content
            ).hexdigest()
        self._sync_authority()

    def set_all_obligations_empty(self) -> None:
        manifest = self.authority_document["holdout_manifest"]
        for task in manifest["tasks"]:
            for config in task["configs"]:
                config["obligation_status"] = "MISSING_OR_EMPTY"
                config["applicable_obligation_ids"] = []
        M.seal_holdout_manifest(manifest)
        self._sync_authority()

    def analyze(self) -> Dict[str, Any]:
        return M.analyze_packet(
            self.packet,
            SCHEMA_DIR,
            authority=self.authority,
        )

    def event(
        self,
        task_index: int = 0,
        config_index: int = 0,
        ordinal: int = 0,
        event_suffix: str = "A",
        b_status: str = "CONFIRMED_POSITIVE",
        interface_status: str = "CONFIRMED_ABSENT",
        source_status: str = "NON_WORLD_CONFIRMED",
        confirmed_unmet: Optional[List[str]] = None,
        compatible_unmet: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        task = self.packet["holdout_manifest"]["tasks"][task_index]
        config = task["configs"][config_index]
        location = config["ordinal_locations"][ordinal]
        return {
            "event_key": "Event-%03d-%s-%02d-%s"
            % (
                task_index,
                chr(ord("A") + config_index),
                ordinal,
                event_suffix,
            ),
            "task_id": task["task_id"],
            "config_id": config["config_id"],
            "unit_id": config["unit_id"],
            "location_id": location["location_id"],
            "b_status": b_status,
            "same_event_interface_status": interface_status,
            "source_status": source_status,
            "b_unmet_obligation_ids_confirmed": (
                confirmed_unmet or []
            ),
            "b_unmet_obligation_ids_compatible": (
                compatible_unmet or []
            ),
        }

    def certificate(
        self,
        predicate_id: str,
        task_index: int = 0,
    ) -> Dict[str, Any]:
        task = self.packet["holdout_manifest"]["tasks"][task_index]
        deficit = predicate_id in M.DEFICIT_PREDICATES
        mode = "DETERMINISTIC_PREDICATE_EVALUATOR_FALSE_V1"
        existing_projection_keys = {
            (
                item["task_id"],
                item["config_id"],
                item["location_id"],
                item["predicate_id"],
                item.get("target_obligation_id"),
                item["proof_mode"],
            )
            for item in self.authority_document["proof_projections"]
        }
        for config in task["configs"]:
            targets: List[Optional[str]] = (
                list(config["applicable_obligation_ids"])
                if deficit
                else [None]
            )
            for location in config["ordinal_locations"]:
                for obligation_id in targets:
                    projection_key = (
                        task["task_id"],
                        config["config_id"],
                        location["location_id"],
                        predicate_id,
                        obligation_id,
                        mode,
                    )
                    if projection_key in existing_projection_keys:
                        continue
                    stem = "proof/%s/%s/%s/%s" % (
                        task["task_id"],
                        config["config_id"],
                        location["location_id"],
                        predicate_id,
                    )
                    if obligation_id is not None:
                        stem += "-" + obligation_id
                    spec_value = {
                        "artifact_type": "stage0f_predicate_spec",
                        "evaluator": "complete_event_ledger_v1",
                        "predicate_id": predicate_id,
                        "target_obligation_id": obligation_id,
                    }
                    ledger_value = {
                        "artifact_type": (
                            "stage0f_complete_event_ledger"
                        ),
                        "coverage": "EXACT_LOCATION_EVENT_SET",
                        "authority_binding": {
                            key: self.authority.binding[key]
                            for key in (
                                "frame_sha256",
                                "manifest_sha256",
                                "a0_barrier_sha256",
                                "a1_barrier_sha256",
                                "stream_roots_sha256",
                                "full_block_bundle_sha256",
                            )
                        },
                        "task_id": task["task_id"],
                        "config_id": config["config_id"],
                        "location_id": location["location_id"],
                        "events": copy.deepcopy(
                            self._primitive_events_by_location.get(
                                (
                                    task["task_id"],
                                    config["config_id"],
                                    location["location_id"],
                                ),
                                [],
                            )
                        ),
                    }
                    pointer_ids = []
                    for sequence, (
                        role,
                        value,
                        suffix,
                    ) in enumerate(
                        (
                            (
                                "predicate_spec",
                                spec_value,
                                "spec",
                            ),
                            (
                                "event_ledger",
                                ledger_value,
                                "ledger",
                            ),
                        )
                    ):
                        relative_path = stem + "-" + suffix + ".json"
                        ref = self._write_json_asset(
                            relative_path, value
                        )
                        pointer = {
                            "pointer_id": "ProofPointer-%s"
                            % digest(relative_path)[:24],
                            "artifact_id": "ProofArtifact-%s"
                            % digest(relative_path + ":artifact")[:24],
                            "observation_ordinal": location[
                                "observation_ordinal"
                            ],
                            "content_sha256": ref["sha256"],
                            "projection_role": role,
                            "sequence_ordinal": sequence,
                        }
                        self.authority_document[
                            "evidence_assets"
                        ].append(
                            {
                                "pointer": pointer,
                                "relative_path": relative_path,
                            }
                        )
                        pointer_ids.append(pointer["pointer_id"])
                    self.authority_document[
                        "proof_projections"
                    ].append(
                        {
                            "task_id": task["task_id"],
                            "config_id": config["config_id"],
                            "location_id": location["location_id"],
                            "predicate_id": predicate_id,
                            "target_obligation_id": obligation_id,
                            "proof_mode": mode,
                            "ordered_pointer_ids": pointer_ids,
                        }
                    )
                    existing_projection_keys.add(projection_key)
        self._sync_authority()

        records = []
        for config in task["configs"]:
            proofs = []
            targets: List[Optional[str]] = (
                list(config["applicable_obligation_ids"])
                if deficit
                else [None]
            )
            for location in config["ordinal_locations"]:
                for obligation_id in targets:
                    projection_key = (
                        task["task_id"],
                        config["config_id"],
                        location["location_id"],
                        predicate_id,
                        obligation_id,
                        mode,
                    )
                    pointers = [
                        M._deep_thaw(
                            self.authority.evidence_assets[pointer_id][
                                "pointer"
                            ]
                        )
                        for pointer_id in self.authority.proof_projections[
                            projection_key
                        ]
                    ]
                    proof = {
                        "observation_ordinal": location[
                            "observation_ordinal"
                        ],
                        "location_id": location["location_id"],
                        "target_obligation_id": obligation_id,
                        "disposition": (
                            "MECHANICALLY_PREDICATE_FALSE"
                        ),
                        "direct_evidence_pointers": pointers,
                        "proof_mode": (
                            "DETERMINISTIC_PREDICATE_EVALUATOR_FALSE_V1"
                        ),
                        "verifier_id": M.VALIDATOR_ID,
                        "verifier_version": M.VALIDATOR_VERSION,
                        "verifier_executable_sha256": digest(
                            "placeholder-executable"
                        ),
                        "verifier_config_sha256": digest(
                            "placeholder-config"
                        ),
                        "verifier_output": {},
                        "verifier_output_hash": digest(
                            "placeholder-verifier-output"
                        ),
                    }
                    M.execute_and_seal_proof(
                        proof,
                        predicate_id,
                        obligation_id,
                        task["task_id"],
                        config["config_id"],
                        self.authority,
                        ROOT,
                    )
                    proofs.append(proof)
            records.append(
                {
                    "config_id": config["config_id"],
                    "unit_id": config["unit_id"],
                    "unit_ordinal_roster": M.roster_projection(config),
                    "unit_ordinal_roster_sha256": config[
                        "unit_ordinal_roster_sha256"
                    ],
                    "trajectory_hash_chain_root": config[
                        "trajectory_hash_chain_root"
                    ],
                    "applicable_obligation_ids": list(
                        config["applicable_obligation_ids"]
                    ),
                    "proofs": proofs,
                }
            )
        artifact = {
            "artifact_type": "stage0f_bounds_negative_certificate",
            "artifact_schema_version": M.SCHEMA_VERSION,
            "canonicalization": M.CANONICALIZATION,
            "artifact_id": "Certificate-%03d-%s"
            % (task_index, predicate_id.replace("_", "-")),
            "predicate_id": predicate_id,
            "task_id": task["task_id"],
            "task_manifest_sha256": task["task_manifest_sha256"],
            "exact_six_config_ids": list(self.CONFIG_IDS),
            "exact_six_config_ids_sha256": (
                M.config_roster_ids_sha256(self.CONFIG_IDS)
            ),
            "config_records": records,
            "constraint_set_hash": M.CONSTRAINT_SET_HASH,
            "proof_whitelist_hash": M.PROOF_WHITELIST_HASH,
            "validator_id": M.VALIDATOR_ID,
            "validator_version": M.VALIDATOR_VERSION,
            "validator_output_hash": digest(
                "placeholder-validator-output"
            ),
        }
        M.seal_certificate(artifact)
        return artifact


def audit_entry(
    output: Dict[str, Any],
    task_id: str,
    predicate_id: str,
) -> Dict[str, Any]:
    return next(
        entry
        for entry in output["certificate_audit"]
        if entry["task_id"] == task_id
        and entry["predicate_id"] == predicate_id
    )


def rational(value: Dict[str, Any]) -> Fraction:
    return Fraction(value["numerator"], value["denominator"])


class Stage0FBoundsMechanicsTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.case_roster = json.loads(
            CASE_PATH.read_text(encoding="utf-8")
        )

    def test_schemas_compile_and_valid_packet_output_validates(self) -> None:
        fixture = SyntheticBoundsPacket()
        self.assertEqual(
            M.validate_with_schema(fixture.packet, "input", SCHEMA_DIR),
            [],
        )
        output = fixture.analyze()
        self.assertEqual(
            M.validate_with_schema(output, "output", SCHEMA_DIR),
            [],
        )
        self.assertFalse(output["research_evidence"])
        self.assertFalse(output["confirmatory_outcome_opened"])
        self.assertFalse(output["measurement_stack_frozen"])

    def test_ajv2020_strict_compiles_all_bounds_schemas(self) -> None:
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
const ajv = new Ajv2020({strict: true, allErrors: true});
const files = fs.readdirSync("schemas")
  .filter((name) =>
    name.startsWith("stage0f_bounds_") &&
    name.endsWith(".schema.json")
  )
  .sort();
const schemas = files.map((name) => {
  const schema = JSON.parse(
    fs.readFileSync("schemas/" + name, "utf8")
  );
  ajv.addSchema(schema);
  return [name, schema.$id];
});
for (const [name, id] of schemas) {
  if (typeof ajv.getSchema(id) !== "function") {
    throw new Error("strict compile did not produce validator: " + name);
  }
}
process.stdout.write("STRICT_COMPILED_COUNT=" + schemas.length + "\n");
"""
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=str(ROOT),
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout.strip(), "STRICT_COMPILED_COUNT=5"
        )

    def test_valid_complete_certificates_and_monotonic_closure(self) -> None:
        fixture = SyntheticBoundsPacket()
        fixture.packet["negative_certificate_artifacts"] = [
            fixture.certificate(predicate_id)
            for predicate_id in M.PREDICATES
        ]
        output = fixture.analyze()
        task_id = "Task-000"
        for predicate_id in M.PREDICATES:
            entry = audit_entry(output, task_id, predicate_id)
            self.assertEqual(entry["direct_task_certificate"], 1)
            self.assertEqual(entry["effective_task_certificate"], 1)
        self.assertEqual(
            output["bounds"]["C0_B"]["U_B_tasks_global"], 0
        )
        self.assertEqual(
            output["bounds"]["C0_C"][
                "U_C_interface_tasks_global"
            ],
            0,
        )
        self.assertEqual(output["bounds"]["C0_E"]["U_env_tasks"], 0)

    def test_x36_frozen_executable_and_evidence_bytes_are_enforced(
        self,
    ) -> None:
        # Positive control: a complete certificate was created by actually
        # executing the registry-pinned verifier over the authoritative bytes.
        fixture = SyntheticBoundsPacket()
        artifact = fixture.certificate("q_B")
        fixture.packet["negative_certificate_artifacts"] = [artifact]
        clean = fixture.analyze()
        self.assertEqual(
            audit_entry(clean, "Task-000", "q_B")[
                "direct_task_certificate"
            ],
            1,
        )
        proof = artifact["config_records"][0]["proofs"][0]
        executable = ROOT / (
            "tools/stage0f_bounds_frozen_verifier.py"
        )
        self.assertEqual(
            proof["verifier_executable_sha256"],
            hashlib.sha256(executable.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            proof["verifier_output"]["execution_status"],
            "EXECUTED_AND_DERIVED",
        )

        # A caller cannot replace the subprocess result and merely reseal the
        # public hashes.
        forged_fixture = SyntheticBoundsPacket()
        forged = forged_fixture.certificate("q_B")
        forged_proof = forged["config_records"][0]["proofs"][0]
        forged_proof["verifier_output"][
            "direct_evidence_projection_sha256"
        ] = digest(
            "caller-forged-projection"
        )
        forged_proof["verifier_output_hash"] = M.verifier_output_hash(
            forged_proof["verifier_output"]
        )
        M.seal_certificate(forged)
        forged_fixture.packet[
            "negative_certificate_artifacts"
        ] = [forged]
        forged_output = forged_fixture.analyze()
        forged_audit = audit_entry(
            forged_output, "Task-000", "q_B"
        )
        self.assertEqual(
            forged_audit["direct_task_certificate"], 0
        )
        self.assertIn(
            "VERIFIER_OUTPUT_NOT_EXECUTION_DERIVED",
            forged_audit["issue_codes"],
        )

        # A single-byte change on disk cannot be loaded under the frozen
        # evidence pointer/content commitment.
        damaged_fixture = SyntheticBoundsPacket()
        damaged_fixture.certificate("q_B")
        damaged_asset = damaged_fixture.authority_document[
            "evidence_assets"
        ][0]
        damaged_path = (
            damaged_fixture.authority_dir
            / damaged_asset["relative_path"]
        )
        damaged_path.write_bytes(damaged_path.read_bytes() + b"\x20")
        with self.assertRaisesRegex(
            ValueError, "authority evidence bytes hash mismatch"
        ):
            M.load_synthetic_bounds_authority(
                damaged_fixture.authority_dir,
                damaged_fixture.expected_authority_sha256,
            )

    def test_x37_packet_cannot_reseal_or_reassign_external_universe(
        self,
    ) -> None:
        no_authority = SyntheticBoundsPacket()
        with self.assertRaisesRegex(
            ValueError, "BOUNDS_AUTHORITY_REQUIRED"
        ):
            M.analyze_packet(no_authority.packet, SCHEMA_DIR)

        truncated = SyntheticBoundsPacket()
        manifest = truncated.packet["holdout_manifest"]
        manifest["tasks"][0]["configs"][0][
            "ordinal_locations"
        ].pop()
        M.seal_holdout_manifest(manifest)
        truncated_output = truncated.analyze()
        self.assertEqual(
            truncated_output["verdict_inputs"]["C0_B"],
            "UNIDENTIFIABLE",
        )
        self.assertTrue(
            any(
                issue["code"]
                == "HOLDOUT_MANIFEST_NOT_EXTERNAL_AUTHORITY_EXACT"
                for issue in truncated_output["issues"]
            )
        )

        reassigned = SyntheticBoundsPacket()
        reassigned_manifest = reassigned.packet["holdout_manifest"]
        configs = reassigned_manifest["tasks"][0]["configs"]
        configs[0]["unit_id"], configs[1]["unit_id"] = (
            configs[1]["unit_id"],
            configs[0]["unit_id"],
        )
        M.seal_holdout_manifest(reassigned_manifest)
        reassigned_output = reassigned.analyze()
        self.assertEqual(
            reassigned_output["verdict_inputs"]["C0_B"],
            "UNIDENTIFIABLE",
        )
        self.assertTrue(
            any(
                issue["code"]
                == "HOLDOUT_MANIFEST_NOT_EXTERNAL_AUTHORITY_EXACT"
                for issue in reassigned_output["issues"]
            )
        )

    def test_x38_bare_prestitch_row_is_never_an_event_authority(
        self,
    ) -> None:
        fixture = SyntheticBoundsPacket()
        forged = fixture.event(
            interface_status="QUALIFYING_CONFIRMED",
            source_status="PURE_WORLD_CONFIRMED",
            confirmed_unmet=["O-PRIMARY"],
        )
        fixture.packet["observed_joint_events"] = [forged]
        output = fixture.analyze()
        self.assertEqual(output["bounds"]["C0_B"]["L_B_tasks"], 0)
        self.assertEqual(
            output["bounds"]["C0_E"]["L_env_interface_tasks"],
            0,
        )
        self.assertEqual(
            output["verdict_inputs"]["C0_B"], "UNIDENTIFIABLE"
        )
        self.assertTrue(
            any(
                issue["code"] == "INPUT_SCHEMA_INVALID"
                for issue in output["issues"]
            )
        )

        derived_fixture = SyntheticBoundsPacket()
        derived_fixture.set_events([derived_fixture.event()])
        derived = derived_fixture.authority.events[0]
        expected_preimage = (
            derived["task_id"],
            derived["unit_id"],
            derived["location_id"],
            derived["adjudicated_event_id"],
        )
        self.assertEqual(
            derived["event_key_sha256"],
            M.canonical_sha256(
                [
                    "stage0f-canonical-event-key-v1",
                    *expected_preimage,
                ]
            ),
        )
        self.assertEqual(
            derived["event_key_preimage"], expected_preimage
        )

    def test_x39_exact_proof_projection_delete_replace_reorder_stale(
        self,
    ) -> None:
        for mutation in ("delete", "replace", "reorder", "stale_bytes"):
            with self.subTest(mutation=mutation):
                fixture = SyntheticBoundsPacket()
                artifact = fixture.certificate("q_B")
                proof = artifact["config_records"][0]["proofs"][0]
                if mutation == "delete":
                    proof["direct_evidence_pointers"].pop()
                elif mutation == "replace":
                    replacement = artifact["config_records"][0][
                        "proofs"
                    ][1]["direct_evidence_pointers"][0]
                    proof["direct_evidence_pointers"][0] = (
                        copy.deepcopy(replacement)
                    )
                elif mutation == "reorder":
                    proof["direct_evidence_pointers"].reverse()
                else:
                    proof["direct_evidence_pointers"][1][
                        "content_sha256"
                    ] = digest("stale-proof-evidence-bytes")
                M.seal_certificate(artifact)
                fixture.packet[
                    "negative_certificate_artifacts"
                ] = [artifact]
                output = fixture.analyze()
                entry = audit_entry(output, "Task-000", "q_B")
                self.assertEqual(
                    entry["direct_task_certificate"], 0
                )
                self.assertEqual(
                    output["bounds"]["C0_B"][
                        "U_B_tasks_global"
                    ],
                    1,
                )

    def test_x40_structural_completion_recomputes_pass_and_fail(
        self,
    ) -> None:
        fixture = SyntheticBoundsPacket(
            task_count=4, ordinal_count=1
        )
        selected_configs = [0, 3, 4, 5]
        events = []
        for task_index, config_index in enumerate(selected_configs):
            if task_index < 2:
                events.append(
                    fixture.event(
                        task_index=task_index,
                        config_index=config_index,
                        event_suffix="STRUCTURAL",
                        confirmed_unmet=["O-PRIMARY"],
                    )
                )
            else:
                events.append(
                    fixture.event(
                        task_index=task_index,
                        config_index=config_index,
                        event_suffix="STRUCTURAL",
                        compatible_unmet=["O-PRIMARY"],
                    )
                )
        fixture.set_events(events)
        issues: List[Dict[str, str]] = []
        tasks, configs, locations = M._validate_manifest(
            fixture.packet, issues
        )
        derived_events = M._validate_events(
            {"observed_joint_events": fixture.authority.events},
            configs,
            locations,
            issues,
        )
        direct_non, direct_def = M._certificate_matrix_template(
            tasks
        )
        for task_index, (task_id, task) in enumerate(tasks.items()):
            selected_config_id = SyntheticBoundsPacket.CONFIG_IDS[
                selected_configs[task_index]
            ]
            for config in task["configs"]:
                config_id = config["config_id"]
                # The derived events have no qualifying interface, so q_C can
                # be independently fixed to zero at every location.
                direct_non[(task_id, "q_C", config_id)] = 1
                if config_id == selected_config_id:
                    continue
                direct_non[(task_id, "q_B", config_id)] = 1
                direct_def[
                    (
                        task_id,
                        "q_B_deficit",
                        config_id,
                        "O-PRIMARY",
                    )
                ] = 1
        effective_non, effective_def = (
            M._effective_certificate_closure(
                tasks, direct_non, direct_def
            )
        )
        ir = M._build_joint_completion_ir(
            "Z_D",
            tasks,
            derived_events,
            effective_non,
            effective_def,
            issues,
        )
        self.assertEqual(ir["free_binary_variable_count"], 2)
        evaluation, error = M._evaluate_structural_completion(
            ir, tasks, fixture.authority
        )
        self.assertIsNone(error)
        self.assertEqual(evaluation["verdict"], "INCONCLUSIVE")
        self.assertTrue(evaluation["enumeration_complete"])
        self.assertIsNotNone(evaluation["pass_witness"])
        self.assertIsNotNone(evaluation["fail_witness"])
        pass_stats = evaluation["pass_witness"]["statistics"]
        fail_stats = evaluation["fail_witness"]["statistics"]
        self.assertTrue(
            pass_stats["passed_all_3K_and_6_share_gates"]
        )
        self.assertFalse(
            fail_stats["passed_all_3K_and_6_share_gates"]
        )
        self.assertEqual(
            pass_stats["exposures"]["structural_group"],
            {
                "Group-000": 1,
                "Group-001": 1,
                "Group-002": 1,
                "Group-003": 1,
            },
        )
        self.assertEqual(
            pass_stats["exposures"]["model_family"],
            {
                "Anthropic": 12,
                "MiniMax": 4,
                "OpenAI": 4,
                "Qwen": 4,
            },
        )
        for partition_name, max_key in (
            ("structural_group", "structural_positive"),
            ("site_app_set", "site_app_positive"),
            ("model_family", "model_family_positive"),
        ):
            rows = pass_stats["partition_details"][
                partition_name
            ]
            self.assertEqual(
                max(
                    rational(
                        row[
                            "positive_exposure_normalized_share"
                        ]
                    )
                    for row in rows
                ),
                rational(pass_stats["max_shares"][max_key]),
            )
            self.assertEqual(
                sum(
                    (
                        rational(
                            row[
                                "positive_exposure_normalized_share"
                            ]
                        )
                        for row in rows
                    ),
                    Fraction(0),
                ),
                Fraction(1),
            )

    def test_x40_large_or_unmapped_structure_fails_closed(
        self,
    ) -> None:
        large = SyntheticBoundsPacket()
        large_output = large.analyze()
        self.assertEqual(
            large_output["structural_verdict_inputs"]["C0_D"][
                "verdict"
            ],
            "UNIDENTIFIABLE",
        )
        self.assertTrue(
            any(
                issue["code"]
                == "STRUCTURAL_SOLVER_CERTIFICATE_REQUIRED"
                for issue in large_output["issues"]
            )
        )

        unmapped = SyntheticBoundsPacket(ordinal_count=1)
        unmapped.authority_document["structural_mapping"][
            "task_mappings"
        ][0][
            "structural_group"
        ] = "UNMAPPED"
        unmapped._sync_authority()
        unmapped_output = unmapped.analyze()
        self.assertEqual(
            unmapped_output["structural_verdict_inputs"]["C0_D"][
                "verdict"
            ],
            "UNIDENTIFIABLE",
        )
        self.assertTrue(
            any(
                issue["code"]
                == "STRUCTURAL_TASK_MAPPING_INVALID_OR_UNMAPPED"
                for issue in unmapped_output["issues"]
            )
        )

    def test_x61_measurement_invalid_blocks_structural_enumeration(
        self,
    ) -> None:
        fixture = SyntheticBoundsPacket(ordinal_count=1)
        fixture.packet["authority_binding"]["frame_sha256"] = digest(
            "wrong-but-valid-frame"
        )

        output = fixture.analyze()

        self.assertEqual(
            [
                issue["code"]
                for issue in output["issues"]
                if issue["severity"] == "MEASUREMENT_INVALID"
            ],
            ["EXTERNAL_AUTHORITY_BINDING_MISMATCH"],
        )
        for verdict_key in ("C0_B", "C0_C", "C0_E"):
            self.assertEqual(
                output["verdict_inputs"][verdict_key],
                "UNIDENTIFIABLE",
            )
        for projection_key in ("C0_D", "PURE_WORLD_STRUCTURE"):
            structural = output["structural_verdict_inputs"][
                projection_key
            ]
            self.assertEqual(
                structural["verdict"], "UNIDENTIFIABLE"
            )
            self.assertFalse(structural["enumeration_complete"])
            self.assertEqual(structural["completion_count"], 0)
            self.assertIsNone(structural["pass_witness"])
            self.assertIsNone(structural["fail_witness"])
        self.assertEqual(
            {
                issue["path"]
                for issue in output["issues"]
                if issue["code"]
                == (
                    "STRUCTURAL_EVALUATION_BLOCKED_BY_"
                    "MEASUREMENT_INVALID"
                )
            },
            {"$.Z_D", "$.Z_env_structure"},
        )

    def test_x42_target_boolean_is_not_sound_evidence(self) -> None:
        fixture = SyntheticBoundsPacket()
        fixture.certificate("q_B")
        ledger_asset = next(
            asset
            for asset in fixture.authority_document[
                "evidence_assets"
            ]
            if asset["pointer"]["projection_role"]
            == "event_ledger"
        )
        ledger_path = fixture.authority_dir / ledger_asset[
            "relative_path"
        ]
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        ledger["predicate_values"] = {"q_B": False}
        ledger_bytes = M.canonical_bytes(ledger)
        ledger_path.write_bytes(ledger_bytes)
        ledger_asset["pointer"]["content_sha256"] = hashlib.sha256(
            ledger_bytes
        ).hexdigest()
        authority_path = fixture.authority_dir / "authority.json"
        authority_path.write_bytes(
            M.canonical_bytes(fixture.authority_document)
        )
        laundered_authority_hash = M.canonical_sha256(
            fixture.authority_document
        )
        with self.assertRaisesRegex(
            ValueError,
            "event ledger is not exact projection",
        ):
            M.load_synthetic_bounds_authority(
                fixture.authority_dir,
                laundered_authority_hash,
            )

        positive = SyntheticBoundsPacket()
        positive.set_events(
            [positive.event(confirmed_unmet=["O-PRIMARY"])]
        )
        with self.assertRaisesRegex(
            ValueError, "frozen verifier did not pass"
        ):
            positive.certificate("q_B")

        registry = json.loads(
            (
                SCHEMA_DIR
                / "stage0f_bounds_verifier_registry.json"
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(
            registry["modes"][
                "FROZEN_TRANSITION_TABLE_NO_OPPORTUNITY_V1"
            ]["enabled"]
        )
        self.assertFalse(
            registry["modes"][
                "TYPED_EVENT_GRAMMAR_EXCLUSION_V1"
            ]["enabled"]
        )
        disabled_fixture = SyntheticBoundsPacket()
        disabled_artifact = disabled_fixture.certificate("q_B")
        disabled_proof = disabled_artifact["config_records"][0][
            "proofs"
        ][0]
        disabled_proof["proof_mode"] = (
            "FROZEN_TRANSITION_TABLE_NO_OPPORTUNITY_V1"
        )
        disabled_proof["disposition"] = (
            "MECHANICALLY_NO_OPPORTUNITY"
        )
        M.seal_certificate(disabled_artifact)
        disabled_fixture.packet[
            "negative_certificate_artifacts"
        ] = [disabled_artifact]
        disabled_output = disabled_fixture.analyze()
        disabled_audit = audit_entry(
            disabled_output, "Task-000", "q_B"
        )
        self.assertEqual(
            disabled_audit["direct_task_certificate"], 0
        )
        self.assertIn(
            "PROOF_MODE_DISABLED_UNSOUND_SEMANTICS",
            disabled_audit["issue_codes"],
        )

    def test_x44_obligation_denominator_cannot_reseal_external_authority(
        self,
    ) -> None:
        fixture = SyntheticBoundsPacket()
        manifest = fixture.packet["holdout_manifest"]
        config = manifest["tasks"][0]["configs"][0]
        config["applicable_obligation_ids"] = ["O-FAKE"]
        M.seal_holdout_manifest(manifest)
        output = fixture.analyze()
        self.assertEqual(
            output["verdict_inputs"]["C0_B"], "UNIDENTIFIABLE"
        )
        self.assertTrue(
            any(
                issue["code"]
                == "HOLDOUT_MANIFEST_NOT_EXTERNAL_AUTHORITY_EXACT"
                for issue in output["issues"]
            )
        )
        self.assertEqual(
            fixture.authority.holdout_manifest["tasks"][0][
                "configs"
            ][0]["applicable_obligation_ids"],
            ("O-PRIMARY",),
        )

    def test_x45_unit_task_reassignment_cannot_reseal_external_authority(
        self,
    ) -> None:
        fixture = SyntheticBoundsPacket(task_count=2)
        manifest = fixture.packet["holdout_manifest"]
        first = manifest["tasks"][0]["configs"][0]
        second = manifest["tasks"][1]["configs"][0]
        first["unit_id"], second["unit_id"] = (
            second["unit_id"],
            first["unit_id"],
        )
        M.seal_holdout_manifest(manifest)
        output = fixture.analyze()
        self.assertEqual(
            output["verdict_inputs"]["C0_B"], "UNIDENTIFIABLE"
        )
        self.assertTrue(
            any(
                issue["code"]
                == "HOLDOUT_MANIFEST_NOT_EXTERNAL_AUTHORITY_EXACT"
                for issue in output["issues"]
            )
        )
        self.assertEqual(
            fixture.authority.holdout_manifest["tasks"][0][
                "configs"
            ][0]["unit_id"],
            "Unit-000-A",
        )
        self.assertEqual(
            fixture.authority.holdout_manifest["tasks"][1][
                "configs"
            ][0]["unit_id"],
            "Unit-001-A",
        )

    def test_x49_external_structural_mapping_commitment_rejects_rewrite(
        self,
    ) -> None:
        fixture = SyntheticBoundsPacket(task_count=4)
        # Runtime mutation is detected against the binding captured by the
        # trusted loader; no caller can retain the old mapping hash and use a
        # newly convenient partition.
        with self.assertRaises(TypeError):
            fixture.authority.structural_mapping[
                "task_mappings"
            ][0]["structural_group"] = "Group-Outcome-Dependent"

        # Rewriting the fixture on disk also fails under the independently
        # retained expected authority commitment.
        fixture = SyntheticBoundsPacket(task_count=4)
        original_expected_hash = fixture.expected_authority_sha256
        fixture.authority_document["structural_mapping"][
            "task_mappings"
        ][0]["structural_group"] = "Group-Outcome-Dependent"
        fixture.authority_document["structural_mapping"][
            "task_mappings"
        ][0]["site_app_set"] = "Site-Outcome-Dependent"
        (fixture.authority_dir / "authority.json").write_bytes(
            M.canonical_bytes(fixture.authority_document)
        )
        with self.assertRaisesRegex(
            ValueError, "external synthetic authority hash mismatch"
        ):
            M.load_synthetic_bounds_authority(
                fixture.authority_dir,
                original_expected_hash,
            )

    def test_x53_runtime_authority_is_immutable_and_recommitted(
        self,
    ) -> None:
        fixture = SyntheticBoundsPacket()
        fixture.set_events(
            [
                fixture.event(
                    b_status="CONFIRMED_NEGATIVE",
                    event_suffix="NEGATIVE",
                )
            ]
        )
        baseline = fixture.analyze()
        self.assertEqual(
            baseline["bounds"]["C0_B"]["L_B_tasks"], 0
        )

        with self.assertRaises(TypeError):
            fixture.authority.events[0][
                "b_status"
            ] = "CONFIRMED_POSITIVE"
        with self.assertRaises(TypeError):
            fixture.authority.holdout_manifest["tasks"][0][
                "configs"
            ][0]["applicable_obligation_ids"] = ("O-FAKE",)
        with self.assertRaises(TypeError):
            fixture.authority.evidence_assets["missing"] = {}
        with self.assertRaises(TypeError):
            fixture.authority.proof_projections["missing"] = ()

        unchanged = fixture.analyze()
        self.assertEqual(
            unchanged["bounds"]["C0_B"]["L_B_tasks"], 0
        )

        # Even reflective replacement of a private frozen snapshot is caught
        # by the per-analysis runtime commitment before any bound is derived.
        tampered_events = M._deep_thaw(fixture.authority.events)
        tampered_events[0]["b_status"] = "CONFIRMED_POSITIVE"
        object.__setattr__(
            fixture.authority,
            "_events",
            M._deep_freeze(tampered_events),
        )
        with self.assertRaisesRegex(
            ValueError, "AUTHORITY_RUNTIME_COMMITMENT_MISMATCH"
        ):
            fixture.analyze()

    def test_x54_a1_summary_must_equal_primitive_action_semantics(
        self,
    ) -> None:
        fixture = SyntheticBoundsPacket()
        fixture.set_events(
            [
                fixture.event(
                    b_status="CONFIRMED_NEGATIVE",
                    event_suffix="NEGATIVE",
                )
            ]
        )
        self.assertEqual(
            fixture.authority.events[0]["b_status"],
            "CONFIRMED_NEGATIVE",
        )
        source = fixture.authority_document["event_sources"][0]
        a1_path = (
            fixture.authority_dir
            / source["a1_ref"]["relative_path"]
        )
        a1 = json.loads(a1_path.read_text(encoding="utf-8"))
        self.assertEqual(
            a1["action_assessment"]["compatible_with_p_old"],
            "no",
        )
        a1["primary_uacf_d_positive"] = True
        a1["phenotype"] = "target_positive"
        a1_bytes = M.canonical_bytes(a1)
        a1_path.write_bytes(a1_bytes)
        source["a1_ref"]["sha256"] = hashlib.sha256(
            a1_bytes
        ).hexdigest()
        (fixture.authority_dir / "authority.json").write_bytes(
            M.canonical_bytes(fixture.authority_document)
        )
        divergent_hash = M.canonical_sha256(
            fixture.authority_document
        )
        with self.assertRaisesRegex(
            ValueError, "A1 summary/action semantic divergence"
        ):
            M.load_synthetic_bounds_authority(
                fixture.authority_dir,
                divergent_hash,
            )

    def test_x55_model_family_codebook_is_exact_not_enum_only(
        self,
    ) -> None:
        fixture = SyntheticBoundsPacket(task_count=4)
        rows = fixture.authority_document["structural_mapping"][
            "config_mappings"
        ]
        by_config = {row["config_id"]: row for row in rows}
        by_config["Config-A"]["model_family"] = "OpenAI"
        by_config["Config-D"]["model_family"] = "Anthropic"
        forged_mapping = {
            row["config_id"]: row["model_family"] for row in rows
        }
        fixture.authority_document["structural_mapping"][
            "model_family_codebook_sha256"
        ] = M.canonical_sha256(
            [
                "stage0f-bounds-model-family-codebook-v1",
                forged_mapping,
            ]
        )
        (fixture.authority_dir / "authority.json").write_bytes(
            M.canonical_bytes(fixture.authority_document)
        )
        rewritten_hash = M.canonical_sha256(
            fixture.authority_document
        )
        with self.assertRaisesRegex(
            ValueError, "frozen model-family codebook mismatch"
        ):
            M.load_synthetic_bounds_authority(
                fixture.authority_dir,
                rewritten_hash,
            )

    def test_x56_malformed_action_cannot_become_negative(
        self,
    ) -> None:
        for malformed_action in (
            {},
            {
                "candidate_action_executed": True,
                "compatible_with_p_old": "banana",
                "compatible_with_p_new": "pear",
                "required_action_omission": False,
                "deadline_or_commit_reached": True,
            },
        ):
            with self.subTest(malformed_action=malformed_action):
                fixture = SyntheticBoundsPacket()
                fixture.set_events(
                    [
                        fixture.event(
                            b_status="CONFIRMED_NEGATIVE",
                            event_suffix="NEGATIVE",
                        )
                    ]
                )
                source = fixture.authority_document[
                    "event_sources"
                ][0]
                a1_path = (
                    fixture.authority_dir
                    / source["a1_ref"]["relative_path"]
                )
                a1 = json.loads(
                    a1_path.read_text(encoding="utf-8")
                )
                a1["action_assessment"] = malformed_action
                a1["primary_uacf_d_positive"] = False
                a1["phenotype"] = "target_negative"
                a1_bytes = M.canonical_bytes(a1)
                a1_path.write_bytes(a1_bytes)
                source["a1_ref"]["sha256"] = hashlib.sha256(
                    a1_bytes
                ).hexdigest()
                (
                    fixture.authority_dir / "authority.json"
                ).write_bytes(
                    M.canonical_bytes(fixture.authority_document)
                )
                malformed_hash = M.canonical_sha256(
                    fixture.authority_document
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "malformed primitive action assessment",
                ):
                    M.load_synthetic_bounds_authority(
                        fixture.authority_dir,
                        malformed_hash,
                    )

    def test_x57_omission_semantics_match_stage_a_contract(
        self,
    ) -> None:
        # Align with the upstream Stage-A contract: a required omission may
        # legitimately retain old=yes/new=no and is positive once the deadline
        # or commit boundary has been reached.
        omission = SyntheticBoundsPacket()
        omission.set_events([omission.event()])
        source = omission.authority_document["event_sources"][0]
        a1_path = (
            omission.authority_dir
            / source["a1_ref"]["relative_path"]
        )
        a1 = json.loads(a1_path.read_text(encoding="utf-8"))
        a1["action_assessment"] = {
            "candidate_action_executed": False,
            "compatible_with_p_old": "yes",
            "compatible_with_p_new": "no",
            "required_action_omission": True,
            "deadline_or_commit_reached": True,
        }
        a1["primary_uacf_d_positive"] = True
        a1["phenotype"] = "target_positive"
        a1_bytes = M.canonical_bytes(a1)
        a1_path.write_bytes(a1_bytes)
        source["a1_ref"]["sha256"] = hashlib.sha256(
            a1_bytes
        ).hexdigest()
        (omission.authority_dir / "authority.json").write_bytes(
            M.canonical_bytes(omission.authority_document)
        )
        omission_hash = M.canonical_sha256(
            omission.authority_document
        )
        omission_authority = M.load_synthetic_bounds_authority(
            omission.authority_dir,
            omission_hash,
        )
        self.assertEqual(
            omission_authority.events[0]["b_status"],
            "CONFIRMED_POSITIVE",
        )

    def test_action_semantic_contract_cross_layer_truth_table(
        self,
    ) -> None:
        contract_path = (
            ROOT
            / M.ACTION_SEMANTIC_CONTRACT_RELATIVE_PATH
        )
        self.assertEqual(
            hashlib.sha256(contract_path.read_bytes()).hexdigest(),
            M.ACTION_SEMANTIC_CONTRACT_HASH,
        )
        executed_positive = {
            "candidate_action_executed": True,
            "compatible_with_p_old": "yes",
            "compatible_with_p_new": "no",
            "required_action_omission": False,
            "deadline_or_commit_reached": True,
        }
        executed_negative = {
            **executed_positive,
            "compatible_with_p_old": "no",
            "compatible_with_p_new": "yes",
        }
        executed_unresolved = {
            **executed_positive,
            "compatible_with_p_old": "unidentifiable",
            "compatible_with_p_new": "unidentifiable",
        }
        self.assertEqual(
            M._derive_action_phenotype(
                "pre_update_frozen", executed_positive
            ),
            ("target_positive", True),
        )
        self.assertEqual(
            M._derive_action_phenotype(
                "pre_update_frozen", executed_negative
            ),
            ("target_negative", False),
        )
        self.assertEqual(
            M._derive_action_phenotype(
                "pre_update_frozen", executed_unresolved
            ),
            ("unidentifiable", False),
        )

        negative = SyntheticBoundsPacket()
        negative.set_events(
            [
                negative.event(
                    b_status="CONFIRMED_NEGATIVE",
                    event_suffix="NEGATIVE",
                )
            ]
        )
        negative.packet["negative_certificate_artifacts"] = [
            negative.certificate("q_B")
        ]
        negative_output = negative.analyze()
        self.assertEqual(
            audit_entry(negative_output, "Task-000", "q_B")[
                "direct_task_certificate"
            ],
            1,
        )

        unresolved = SyntheticBoundsPacket()
        unresolved.set_events(
            [
                unresolved.event(
                    b_status="POSITIVE_COMPATIBLE",
                    event_suffix="UNRESOLVED",
                )
            ]
        )
        with self.assertRaisesRegex(
            ValueError, "frozen verifier did not pass"
        ):
            unresolved.certificate("q_B")

    def test_independent_predicate_slot_and_logical_closure(self) -> None:
        fixture = SyntheticBoundsPacket()
        fixture.packet["negative_certificate_artifacts"] = [
            fixture.certificate("q_C")
        ]
        output = fixture.analyze()
        b = audit_entry(output, "Task-000", "q_B")
        c = audit_entry(output, "Task-000", "q_C")
        self.assertEqual(b["direct_task_certificate"], 0)
        self.assertEqual(b["effective_task_certificate"], 0)
        self.assertEqual(c["direct_task_certificate"], 1)
        self.assertEqual(c["effective_task_certificate"], 1)
        self.assertEqual(
            output["bounds"]["C0_B"]["U_B_tasks_global"], 1
        )
        self.assertEqual(
            output["bounds"]["C0_C"][
                "U_C_interface_tasks_global"
            ],
            0,
        )

    def test_joint_completion_monotonicity_and_two_witnesses(self) -> None:
        fixture = SyntheticBoundsPacket(ordinal_count=1)
        # Fix five configs to zero while leaving one finite six-bit location
        # free; this keeps exhaustive witness enumeration intentionally small.
        partial_certificates = []
        for predicate_id in ("q_B", "q_B_deficit"):
            artifact = fixture.certificate(predicate_id)
            artifact["config_records"].pop()
            artifact["validator_output_hash"] = (
                M.certificate_validator_output_hash(artifact)
            )
            partial_certificates.append(artifact)
        fixture.packet[
            "negative_certificate_artifacts"
        ] = partial_certificates
        output = fixture.analyze()
        ir = output["Z_env_structure"]
        completions = list(M.enumerate_joint_completions(ir))
        self.assertGreater(len(completions), 1)
        edges = [
            (
                edge["antecedent_variable_id"],
                edge["consequent_variable_id"],
            )
            for edge in ir["implications"]
        ]
        for completion in completions:
            self.assertTrue(
                all(
                    completion[antecedent]
                    <= completion[consequent]
                    for antecedent, consequent in edges
                )
            )
        self.assertIsNotNone(
            M.find_completion_witness(ir, "q_env_interface", 0)
        )
        self.assertIsNotNone(
            M.find_completion_witness(ir, "q_env_interface", 1)
        )

    def test_empty_obligation_is_lower_zero_upper_one_and_no_cert(
        self,
    ) -> None:
        fixture = SyntheticBoundsPacket()
        fixture.set_all_obligations_empty()
        certificate = fixture.certificate("q_B_deficit")
        fixture.packet["negative_certificate_artifacts"] = [certificate]
        output = fixture.analyze()
        entry = audit_entry(output, "Task-000", "q_B_deficit")
        self.assertEqual(entry["effective_task_certificate"], 0)
        self.assertEqual(
            rational(output["bounds"]["C0_B"]["L_B_deficit"]),
            Fraction(0, 1),
        )
        self.assertEqual(
            rational(
                output["bounds"]["C0_B"]["U_B_deficit_global"]
            ),
            Fraction(1, 1),
        )

    def test_confirmed_positive_invalidates_certificate_not_lower(
        self,
    ) -> None:
        fixture = SyntheticBoundsPacket()
        fixture.packet["negative_certificate_artifacts"] = [
            fixture.certificate("q_B")
        ]
        fixture.set_events(
            [fixture.event(confirmed_unmet=["O-PRIMARY"])]
        )
        output = fixture.analyze()
        entry = audit_entry(output, "Task-000", "q_B")
        self.assertEqual(entry["effective_task_certificate"], 0)
        self.assertIn(
            # Updating the authoritative event set refreshes the exact ledger
            # pointer.  The pre-existing negative proof is therefore stale
            # before it could overwrite the confirmed positive.
            "PROOF_POINTER_NOT_AUTHORITY_EXACT",
            entry["issue_codes"],
        )
        self.assertEqual(output["bounds"]["C0_B"]["L_B_tasks"], 1)
        self.assertEqual(
            rational(output["bounds"]["C0_B"]["L_B_deficit"]),
            Fraction(1, 6),
        )

    def test_same_event_and_location_no_stitching_counterexamples(
        self,
    ) -> None:
        # E23: e1 has B, e2 has WORLD+interface but not B.
        e23 = SyntheticBoundsPacket(ordinal_count=1)
        e23.set_events([
            e23.event(
                event_suffix="B-NONWORLD",
                interface_status="CONFIRMED_ABSENT",
                source_status="NON_WORLD_CONFIRMED",
            ),
            e23.event(
                event_suffix="WORLD-I-NOT-B",
                b_status="CONFIRMED_NEGATIVE",
                interface_status="QUALIFYING_CONFIRMED",
                source_status="PURE_WORLD_CONFIRMED",
            ),
        ])
        out23 = e23.analyze()
        self.assertEqual(
            out23["bounds"]["C0_E"]["L_env_interface_tasks"], 0
        )
        env_i_vars = [
            variable
            for variable in out23["Z_env_structure"]["variables"]
            if variable["predicate_id"] == "q_env_interface"
        ]
        self.assertEqual(env_i_vars[0]["domain"], [0, 1])

        # E24: B at location 0 and interface-only at location 1.
        e24 = SyntheticBoundsPacket(ordinal_count=2)
        e24.set_events([
            e24.event(
                ordinal=0,
                event_suffix="B-ONLY",
                interface_status="CONFIRMED_ABSENT",
            ),
            e24.event(
                ordinal=1,
                event_suffix="I-ONLY",
                b_status="CONFIRMED_NEGATIVE",
                interface_status="QUALIFYING_CONFIRMED",
            ),
        ])
        out24 = e24.analyze()
        self.assertEqual(
            out24["bounds"]["C0_C"]["L_C_interface_tasks"], 0
        )

        # E25: WORLD+B has met(o); NON_WORLD+B has unmet(o).
        e25 = SyntheticBoundsPacket(ordinal_count=1)
        e25.set_events([
            e25.event(
                event_suffix="WORLD-MET",
                source_status="PURE_WORLD_CONFIRMED",
            ),
            e25.event(
                event_suffix="NONWORLD-UNMET",
                source_status="NON_WORLD_CONFIRMED",
                confirmed_unmet=["O-PRIMARY"],
            ),
        ])
        out25 = e25.analyze()
        self.assertEqual(
            rational(out25["bounds"]["C0_B"]["L_B_deficit"]),
            Fraction(1, 6),
        )
        self.assertEqual(
            rational(out25["bounds"]["C0_E"]["L_env_deficit"]),
            Fraction(0, 1),
        )

    def test_missing_config_never_changes_six_config_denominator(
        self,
    ) -> None:
        fixture = SyntheticBoundsPacket()
        missing_config_events = []
        for config_index in range(5):
            missing_config_events.append(
                fixture.event(
                    config_index=config_index,
                    event_suffix="UNMET",
                    confirmed_unmet=["O-PRIMARY"],
                )
            )
        fixture.set_events(missing_config_events)
        fixture.packet["holdout_manifest"]["tasks"][0][
            "configs"
        ].pop()
        M.seal_holdout_manifest(fixture.packet["holdout_manifest"])
        output = fixture.analyze()
        self.assertEqual(
            output["verdict_inputs"]["C0_B"], "UNIDENTIFIABLE"
        )
        self.assertEqual(
            rational(output["bounds"]["C0_B"]["L_B_deficit"]),
            Fraction(5, 6),
        )
        self.assertEqual(
            rational(
                output["bounds"]["C0_B"]["U_B_deficit_global"]
            ),
            Fraction(1, 1),
        )

    def test_no_detection_no_certificate_retains_global_82(
        self,
    ) -> None:
        fixture = SyntheticBoundsPacket(
            task_count=82, ordinal_count=1
        )
        output = fixture.analyze()
        b = output["bounds"]["C0_B"]
        self.assertEqual(b["U_B_tasks_detected"], 0)
        self.assertEqual(b["U_B_tasks_global"], 82)
        self.assertEqual(
            output["verdict_inputs"]["C0_B"], "INCONCLUSIVE"
        )

    def test_c_lower_seven_global_82_is_inconclusive(self) -> None:
        fixture = SyntheticBoundsPacket(
            task_count=82, ordinal_count=1
        )
        c_events = []
        for task_index in range(7):
            c_events.append(
                fixture.event(
                    task_index=task_index,
                    event_suffix="C",
                    interface_status="QUALIFYING_CONFIRMED",
                )
            )
        fixture.set_events(c_events)
        output = fixture.analyze()
        c = output["bounds"]["C0_C"]
        self.assertEqual(c["L_C_interface_tasks"], 7)
        self.assertEqual(c["U_C_interface_tasks_global"], 82)
        self.assertEqual(
            output["verdict_inputs"]["C0_C"], "INCONCLUSIVE"
        )

    def test_unknown_and_invalid_source_retain_environment_global(
        self,
    ) -> None:
        for source_status in (
            "SOURCE_UNKNOWN",
            "INVALID_SOURCE_MEASUREMENT",
        ):
            with self.subTest(source_status=source_status):
                fixture = SyntheticBoundsPacket()
                fixture.set_events([
                    fixture.event(
                        b_status="POSITIVE_COMPATIBLE",
                        source_status=source_status,
                    )
                ])
                output = fixture.analyze()
                env = output["bounds"]["C0_E"]
                self.assertEqual(env["L_env_tasks"], 0)
                self.assertEqual(env["U_env_tasks_detected"], 1)
                self.assertEqual(env["U_env_tasks"], 1)

    def test_certificate_one_damage_roster_e17_to_e20(self) -> None:
        covered = set()
        certificate_cases = [
            case
            for case in self.case_roster["cases"]
            if case["case_id"].split("-", 1)[0]
            in {"E17", "E18", "E19", "E20"}
        ]
        self.assertGreaterEqual(len(certificate_cases), 13)
        for case in certificate_cases:
            with self.subTest(case_id=case["case_id"]):
                fixture = SyntheticBoundsPacket()
                artifact = fixture.certificate("q_B")
                mutation = case["mutation"]
                record = artifact["config_records"][0]
                proof = record["proofs"][0]
                if mutation == "certificate_drop_config":
                    artifact["config_records"].pop()
                elif mutation == "certificate_duplicate_config":
                    artifact["config_records"][-1] = copy.deepcopy(
                        artifact["config_records"][0]
                    )
                elif mutation == "certificate_drop_ordinal_proof":
                    record["proofs"].pop()
                elif mutation == "certificate_renumber_ordinal":
                    proof["observation_ordinal"] = 99
                elif mutation == "certificate_stale_roster_hash":
                    record["unit_ordinal_roster_sha256"] = digest(
                        "stale-roster"
                    )
                elif mutation == "certificate_stale_chain_root":
                    record["trajectory_hash_chain_root"] = digest(
                        "stale-chain"
                    )
                elif mutation.startswith("proof_mode_"):
                    proof["proof_mode"] = {
                        "proof_mode_human_not_found": "HUMAN_NOT_FOUND",
                        "proof_mode_reference_not_found": (
                            "REFERENCE_AGENT_NOT_FOUND"
                        ),
                        "proof_mode_search_returned_none": (
                            "SEARCH_RETURNED_NONE"
                        ),
                    }[mutation]
                elif mutation == "proof_drop_verifier_output":
                    proof.pop("verifier_output")
                elif mutation == "proof_stale_verifier_output_hash":
                    proof["verifier_output_hash"] = digest(
                        "stale-verifier-output"
                    )
                elif mutation == "proof_stale_direct_pointer":
                    proof["direct_evidence_pointers"][0][
                        "content_sha256"
                    ] = digest("stale-pointer")
                elif mutation == "proof_drop_direct_pointer":
                    proof["direct_evidence_pointers"] = []
                else:
                    self.fail("unhandled mutation: %s" % mutation)
                artifact["validator_output_hash"] = (
                    M.certificate_validator_output_hash(artifact)
                )
                fixture.packet[
                    "negative_certificate_artifacts"
                ] = [artifact]
                output = fixture.analyze()
                entry = audit_entry(output, "Task-000", "q_B")
                self.assertEqual(entry["direct_task_certificate"], 0)
                self.assertEqual(
                    output["bounds"]["C0_B"]["U_B_tasks_global"],
                    1,
                )
                covered.add(case["case_id"])
        self.assertEqual(
            covered,
            {case["case_id"] for case in certificate_cases},
        )

    def test_case_roster_maps_all_delegated_redteam_cases(self) -> None:
        case_ids = {case["case_id"] for case in self.case_roster["cases"]}
        for required in (
            "E17",
            "E18",
            "E19",
            "E20",
            "E21",
            "E22",
            "E23",
            "E24",
            "E25",
            "E26",
            "E27",
            "E28",
            "E29",
            "E35",
            "X36",
            "X37",
            "X38",
            "X39",
            "X40",
            "X42",
            "X44",
            "X45",
            "X49",
            "X53",
            "X54",
            "X55",
            "X56",
            "X57",
        ):
            self.assertTrue(
                any(case_id.startswith(required + "-") for case_id in case_ids),
                required,
            )
        self.assertGreaterEqual(len(case_ids), 24)

    def test_verdict_grid_is_total_and_straddles_are_inconclusive(
        self,
    ) -> None:
        outcomes = set()
        fixture = SyntheticBoundsPacket()
        base_output = fixture.analyze()
        bounds = base_output["bounds"]
        for lower_tasks in range(10):
            for upper_tasks in range(lower_tasks, 10):
                for lower_deficit in (Fraction(0), Fraction(1)):
                    for upper_deficit in (
                        lower_deficit,
                        Fraction(1),
                    ):
                        candidate = copy.deepcopy(bounds)
                        candidate["C0_B"]["L_B_tasks"] = lower_tasks
                        candidate["C0_B"][
                            "U_B_tasks_global"
                        ] = upper_tasks
                        candidate["C0_B"]["L_B_deficit"] = (
                            M._fraction_json(lower_deficit)
                        )
                        candidate["C0_B"][
                            "U_B_deficit_global"
                        ] = M._fraction_json(upper_deficit)
                        verdict = M._verdicts(candidate, True)["C0_B"]
                        self.assertIn(
                            verdict,
                            {
                                "SUPPORTED",
                                "BELOW_FROZEN_GATE",
                                "INCONCLUSIVE",
                            },
                        )
                        outcomes.add(verdict)
                        if (
                            lower_tasks < 8 <= upper_tasks
                            and lower_deficit < 1 <= upper_deficit
                        ):
                            self.assertEqual(verdict, "INCONCLUSIVE")
        self.assertEqual(
            outcomes,
            {
                "SUPPORTED",
                "BELOW_FROZEN_GATE",
                "INCONCLUSIVE",
            },
        )

    def test_clean_cli_matches_direct_api(self) -> None:
        fixture = SyntheticBoundsPacket()
        expected = fixture.analyze()
        with tempfile.TemporaryDirectory() as temporary:
            input_path = Path(temporary) / "input.json"
            output_path = Path(temporary) / "output.json"
            input_path.write_text(
                json.dumps(fixture.packet, ensure_ascii=False),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    str(Path(sys.executable)),
                    str(TOOL_PATH),
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--schema-dir",
                    str(SCHEMA_DIR),
                    "--synthetic-authority-dir",
                    str(fixture.authority_dir),
                    "--expected-authority-sha256",
                    fixture.expected_authority_sha256,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            actual = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
