#!/usr/bin/env python3
"""Mechanical tests for the fail-closed Stage 0F measurement implementation.

The positive tests below validate only synthetic component mechanics.  The
production entry point is separately required to reject both a lone unit and
the incomplete block-barrier implementation.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "tools" / "validate_stage0f_stage_a_packet.py"
SCHEMA_DIR = ROOT / "schemas"
CASE_PATH = ROOT / "tests" / "fixtures" / "stage0f_negative_cases.json"

SPEC = importlib.util.spec_from_file_location("stage0f_validator", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


def digest(text: str) -> str:
    return hashlib.sha256(("synthetic:" + text).encode("utf-8")).hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SyntheticUnit:
    """Synthetic-only unit; never a source of scientific evidence."""

    def __init__(
        self,
        root: Path,
        source_labels: Optional[List[str]] = None,
        p_old_status: str = "pre_update_frozen",
    ) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        (root / "raw").mkdir()
        (root / "assets").mkdir()
        (root / "raw" / "source.json").write_bytes(
            b'{"synthetic":true,"research_evidence":false}\n'
        )
        for index in range(2):
            (root / "assets" / ("obs%d.txt" % index)).write_text(
                "synthetic observation %d\n" % index,
                encoding="utf-8",
            )
        self.schemas = {
            name: V.load_json_no_duplicates(SCHEMA_DIR / filename)
            for name, filename in V.SCHEMA_FILES.items()
        }
        versions = {
            "prompt_sha256": digest("prompt"),
            "codebook_sha256": digest("codebook"),
            "code_sha256": digest("code"),
            "schema_bundle_sha256": V.schema_bundle_sha256(self.schemas),
            "validator_sha256": V.validator_file_sha256(),
            "matching_sha256": digest("matching"),
            "adjudication_sha256": digest("adjudication"),
            "normative_canonicalization_sha256": digest("normative"),
        }
        self.artifacts: Dict[str, Dict[str, Any]] = {}
        self.artifacts["coordinator_envelope"] = {
            "artifact_type": "coordinator_envelope",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "coord-envelope-001",
            "unit_alias": "U-ABCDEF012345",
            "identity": {
                "task_id": "035",
                "hosted_config_id": "hosted-config-alpha",
                "model_family_id": "model-family-alpha",
                "trajectory_id": "trajectory-alpha",
                "trajectory_mode": "batch_tool_model_steps",
            },
            "source_snapshot": {
                "source_detail_url": "https://example.invalid/result/alpha",
                "raw_response_relative_path": "raw/source.json",
                "raw_response_sha256": hashlib.sha256(
                    (root / "raw" / "source.json").read_bytes()
                ).hexdigest(),
                "replay_availability": "available",
            },
            "asset_manifest": [
                {
                    "asset_id": "asset-obs-%d" % index,
                    "observation_ordinal": index,
                    "relative_path": "assets/obs%d.txt" % index,
                    "sha256": hashlib.sha256(
                        (root / "assets" / ("obs%d.txt" % index)).read_bytes()
                    ).hexdigest(),
                    "media_type": "text/plain",
                }
                for index in range(2)
            ],
            "provenance": {
                "release_tag": "synthetic-test-only",
                "release_commit": "1" * 40,
                "generator_alias": "generator-synthetic",
                "version_hashes": versions,
            },
            "exposure_policy": {
                "classification": "coordinator_secret",
                "allowed_roles": ["coordinator"],
                "public_linkage": "content_hash_only",
            },
            "created_at": "2026-07-28T09:00:00+08:00",
        }
        instruction = "Synthetic instruction; never research evidence."
        normative = "Synthetic outcome-blind normative source."
        observations = [
            {
                "observation_ordinal": index,
                "observed_at": "2026-07-28T09:00:%02d+08:00" % (10 + 10 * index),
                "assets": [
                    {
                        "asset_id": "asset-obs-%d" % index,
                        "sha256": self.artifacts["coordinator_envelope"][
                            "asset_manifest"
                        ][index]["sha256"],
                    }
                ],
                "agent_visible_text": (
                    "Old state is active."
                    if index == 0
                    else "World truth changed to the new state."
                ),
                "normalized_prior_actions": [] if index == 0 else ["observe"],
                "missingness": "none",
            }
            for index in range(2)
        ]
        self.artifacts["a0_input"] = {
            "artifact_type": "a0_input",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "a0-input-001",
            "source_protocol": "stage0f_osworld2_natural_burden_preregistration.md@v0.5",
            "unit_alias": "U-ABCDEF012345",
            "coordinator_envelope_commitment_sha256": V.canonical_sha256(
                self.artifacts["coordinator_envelope"]
            ),
            "prefix_commit_log_id": "prefix-log-001",
            "prefix_chain_tip_sha256": digest("placeholder-prefix-tip"),
            "boundary_namespace": "stage0f:synthetic",
            "a0_prefix_payload_sha256": digest("placeholder-prefix-payload"),
            "boundary_location_id": digest("placeholder-boundary"),
            "agent_visible_instruction": {
                "text": instruction,
                "content_sha256": sha_text(instruction),
            },
            "normative_schema": {
                "version": "synthetic-v1",
                "sources": [
                    {
                        "source_ref_id": "norm-source-001",
                        "source_class": "release_tagged_task_schema",
                        "content": normative,
                        "content_sha256": sha_text(normative),
                    }
                ],
                "obligations": [
                    {
                        "obligation_id": "O-KEEP-NEW",
                        "predicate": "Commit uses the new state.",
                        "applicability": "Changed evidence is visible.",
                        "deadline_or_commit": "Before next commit.",
                        "source_ref_ids": ["norm-source-001"],
                    },
                    {
                        "obligation_id": "O-SECONDARY",
                        "predicate": "Unrelated obligation.",
                        "applicability": "Always.",
                        "deadline_or_commit": "At task end.",
                        "source_ref_ids": ["norm-source-001"],
                    },
                ],
            },
            "prefix_observations": observations,
            "cutoff_observation_ordinal": 1,
            "candidate_locator": {
                "update_observation_ordinal": 1,
                "selection_rule": "Synthetic fixed locator.",
            },
            "allowed_probes": [
                {
                    "probe_id": "probe-synthetic",
                    "description": "Read visible state.",
                    "safety": "safe",
                    "cost_budget": "one observation",
                }
            ],
            "exposure_class": "a0_normative_only",
            "frozen_at": "2026-07-28T09:01:00+08:00",
        }
        self.prefix_commits: List[Dict[str, Any]] = []
        self.rebuild_prefix_commits()

        labels = source_labels or ["world_truth_changed"]
        primary_source = next(
            label for label in V.SOURCE_PRECEDENCE if label in labels
        )
        p_old_pointer = (
            self.pointer_to_observation(0)
            if p_old_status == "pre_update_frozen"
            else None
        )
        p_new_pointer = self.pointer_to_observation(1)
        supporting_ids = sorted(
            [digest("raw-label-a"), digest("raw-label-b")],
            key=lambda value: value.encode("utf-8"),
        )
        normative_difference = "The commit must use the new state."
        preimage = {
            "serialization": V.ADJUDICATED_EVENT_SERIALIZATION,
            "boundary_location_id": self.artifacts["a0_input"][
                "boundary_location_id"
            ],
            "p_old_proposition_id": "PROP-OLD-STATE",
            "p_new_proposition_id": "PROP-NEW-STATE",
            "normative_action_difference_sha256": sha_text(
                normative_difference
            ),
            "sorted_obligation_ids": ["O-KEEP-NEW"],
            "boundary_type": "action_commit",
            "schema_bundle_sha256": versions["schema_bundle_sha256"],
            "codebook_sha256": versions["codebook_sha256"],
            "supporting_a0_raw_label_ids": supporting_ids,
        }
        primary = p_old_status == "pre_update_frozen"
        self.artifacts["a0_label"] = {
            "artifact_type": "a0_label",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "a0-label-001",
            "unit_alias": "U-ABCDEF012345",
            "a0_input_ref": V.artifact_ref(self.artifacts["a0_input"]),
            "p_old": {
                "proposition_id": "PROP-OLD-STATE",
                "statement": "Old state remains active.",
                "status": p_old_status,
                "evidence_pointer": p_old_pointer,
            },
            "p_new": {
                "proposition_id": "PROP-NEW-STATE",
                "statement": "New state is active.",
                "evidence_pointer": p_new_pointer,
            },
            "update_source_evidence": [
                {
                    "label": label,
                    "evidence_pointer": copy.deepcopy(p_new_pointer),
                }
                for label in labels
            ],
            "primary_update_source": primary_source,
            "normative_action_difference": normative_difference,
            "eligible_decision_point": {
                "observation_ordinal": 1,
                "rule": "Before next commit.",
            },
            "obligation_assessments": [
                {
                    "obligation_id": "O-KEEP-NEW",
                    "affected": True,
                    "rationale": "Changed proposition controls it.",
                },
                {
                    "obligation_id": "O-SECONDARY",
                    "affected": False,
                    "rationale": "Changed proposition does not control it.",
                },
            ],
            "affected_obligation_ids": ["O-KEEP-NEW"],
            "affected_external_object_ids": ["artifact-synthetic"],
            "competing_causes": ["E", "O", "G", "R", "P", "S", "A", "V"],
            "boundary_location_id": self.artifacts["a0_input"][
                "boundary_location_id"
            ],
            "supporting_a0_raw_label_ids": supporting_ids,
            "required_action_spec": None,
            "adjudicated_event_preimage": preimage,
            "adjudicated_event_id": V.adjudicated_event_id(preimage),
            "primary_analysis_eligible": primary,
            "environment_primary_eligible": (
                primary and labels == ["world_truth_changed"]
            ),
            "annotator_alias": "annotator-a0",
            "frozen_at": "2026-07-28T09:02:00+08:00",
        }
        self.artifacts["a1_reveal"] = {
            "artifact_type": "a1_reveal",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "a1-reveal-001",
            "unit_alias": "U-ABCDEF012345",
            "a0_input_ref": V.artifact_ref(self.artifacts["a0_input"]),
            "a0_label_ref": V.artifact_ref(self.artifacts["a0_label"]),
            "adjudicated_event_id": self.artifacts["a0_label"][
                "adjudicated_event_id"
            ],
            "block_barrier_commitment_sha256": digest("synthetic-block"),
            "reveal_kind": "observed_action",
            "behavior_evidence": {
                "kind": "observed_action",
                "action_ordinal": 1,
                "after_observation_ordinal": 1,
                "semantic_action_type": "write",
                "semantic_action": "Commit using the old state.",
                "target_object_ids": ["artifact-synthetic"],
            },
            "exposure_class": "a1_behavioral_reveal",
            "revealed_at": "2026-07-28T09:04:00+08:00",
        }
        self.artifacts["a1_label"] = {
            "artifact_type": "a1_label",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "a1-label-001",
            "unit_alias": "U-ABCDEF012345",
            "a0_input_ref": V.artifact_ref(self.artifacts["a0_input"]),
            "a0_label_ref": V.artifact_ref(self.artifacts["a0_label"]),
            "a1_reveal_ref": V.artifact_ref(self.artifacts["a1_reveal"]),
            "adjudicated_event_id": self.artifacts["a0_label"][
                "adjudicated_event_id"
            ],
            "action_assessment": {
                "candidate_action_executed": True,
                "compatible_with_p_old": "yes",
                "compatible_with_p_new": "no",
                "required_action_omission": False,
                "deadline_or_commit_reached": True,
                "phenotype": "target_positive",
            },
            "affected_obligation_assessments": [
                {
                    "obligation_id": "O-KEEP-NEW",
                    "behavioral_status": "violated",
                    "evidence_pointer": self.action_evidence_pointer(),
                }
            ],
            "primary_uacf_d_positive": primary,
            "annotator_alias": "annotator-a1",
            "frozen_at": "2026-07-28T09:05:00+08:00",
        }
        self.events = self.build_audit_events()
        self.write()

    def pointer_to_observation(self, ordinal: int) -> Dict[str, Any]:
        observation = self.artifacts["a0_input"]["prefix_observations"][ordinal]
        return {
            "artifact_id": self.artifacts["a0_input"]["artifact_id"],
            "observation_ordinal": ordinal,
            "content_sha256": V.canonical_sha256(observation),
            "source_kind": "observation",
        }

    def action_evidence_pointer(self) -> Dict[str, Any]:
        evidence = self.artifacts["a1_reveal"]["behavior_evidence"]
        return {
            "artifact_id": self.artifacts["a1_reveal"]["artifact_id"],
            "observation_ordinal": evidence["after_observation_ordinal"],
            "content_sha256": V.canonical_sha256(evidence),
            "source_kind": "candidate_action",
        }

    def rebuild_prefix_commits(self) -> None:
        a0_input = self.artifacts["a0_input"]
        commits: List[Dict[str, Any]] = []
        previous = None
        for ordinal, observation in enumerate(a0_input["prefix_observations"]):
            payload_hash = V.a0_prefix_payload_sha256(a0_input, ordinal)
            location = V.boundary_location_id(
                a0_input["boundary_namespace"],
                a0_input["unit_alias"],
                ordinal,
                payload_hash,
            )
            entry = {
                "artifact_type": "prefix_commit",
                "schema_version": V.SCHEMA_VERSION,
                "canonicalization": V.CANONICALIZATION,
                "prefix_commit_log_id": a0_input["prefix_commit_log_id"],
                "unit_alias": a0_input["unit_alias"],
                "sequence": ordinal,
                "observation_ordinal": ordinal,
                "observation_sha256": V.canonical_sha256(observation),
                "boundary_namespace": a0_input["boundary_namespace"],
                "a0_prefix_payload_sha256": payload_hash,
                "boundary_location_id": location,
                "committed_at": "2026-07-28T09:00:%02d+08:00" % (13 + ordinal * 10),
                "generator_decisions": [
                    {
                        "generator_alias": "generator-a",
                        "visible_through_observation_ordinal": ordinal,
                        "decision": (
                            "propose_location"
                            if ordinal == len(a0_input["prefix_observations"]) - 1
                            else "reject_location"
                        ),
                        "boundary_location_id": location,
                        "decided_at": "2026-07-28T09:00:%02d+08:00" % (11 + ordinal * 10),
                    },
                    {
                        "generator_alias": "generator-b",
                        "visible_through_observation_ordinal": ordinal,
                        "decision": "reject_location",
                        "boundary_location_id": location,
                        "decided_at": "2026-07-28T09:00:%02d+08:00" % (12 + ordinal * 10),
                    },
                ],
                "previous_entry_sha256": previous,
                "entry_sha256": digest("placeholder-entry"),
            }
            entry["entry_sha256"] = V.chained_entry_sha256(entry)
            previous = entry["entry_sha256"]
            commits.append(entry)
        self.prefix_commits = commits
        a0_input["a0_prefix_payload_sha256"] = commits[-1][
            "a0_prefix_payload_sha256"
        ]
        a0_input["boundary_location_id"] = commits[-1]["boundary_location_id"]
        a0_input["prefix_chain_tip_sha256"] = commits[-1]["entry_sha256"]

    def build_audit_events(self) -> List[Dict[str, Any]]:
        omission = "omission_interval" in self.artifacts
        definitions = [
            ("coordinator_envelope_created", "09:00:00", "coordinator-main", "coordinator", "coordinator_envelope", ["coordinator"], ["coordinator_envelope"]),
            ("a0_input_frozen", "09:01:00", "coordinator-main", "coordinator", "a0_input", ["a0_annotator"], ["a0_input"]),
            ("a0_label_frozen", "09:02:00", "annotator-a0", "a0_annotator", "a0_label", ["coordinator"], ["a0_label"]),
        ]
        if omission:
            definitions.append(("omission_interval_frozen", "09:02:50", "coordinator-main", "coordinator", "omission_interval", ["coordinator"], ["omission_interval"]))
        definitions.extend([
            ("a1_reveal_authorized", "09:03:00", "coordinator-main", "coordinator", "a1_reveal", ["coordinator"], ["a1_reveal"]),
            ("a1_revealed", "09:04:00", "coordinator-main", "coordinator", "a1_reveal", ["a1_annotator"], ["a0_input", "a0_label"] + (["omission_interval"] if omission else []) + ["a1_reveal"]),
            ("a1_label_frozen", "09:05:00", "annotator-a1", "a1_annotator", "a1_label", ["coordinator"], ["a1_label"]),
        ])
        versions = self.artifacts["coordinator_envelope"]["provenance"]["version_hashes"]
        events = []
        previous = None
        for sequence, item in enumerate(definitions):
            kind, clock, actor, role, artifact_name, recipients, visible = item
            event = {
                "artifact_type": "audit_event",
                "schema_version": V.SCHEMA_VERSION,
                "canonicalization": V.CANONICALIZATION,
                "audit_log_id": "audit-log-001",
                "sequence": sequence,
                "event_type": kind,
                "occurred_at": "2026-07-28T%s+08:00" % clock,
                "actor": {"actor_alias": actor, "role": role},
                "artifact_ref": V.artifact_ref(self.artifacts[artifact_name]),
                "previous_entry_sha256": previous,
                "exposure": {
                    "recipient_roles": recipients,
                    "visible_artifacts": [
                        V.artifact_ref(self.artifacts[name]) for name in visible
                    ],
                },
                "version_hashes": copy.deepcopy(versions),
                "entry_sha256": digest("placeholder-audit"),
            }
            event["entry_sha256"] = V.audit_entry_sha256(event)
            previous = event["entry_sha256"]
            events.append(event)
        return events

    def refresh_links(self) -> None:
        a0_input = self.artifacts["a0_input"]
        a0_label = self.artifacts["a0_label"]
        reveal = self.artifacts["a1_reveal"]
        label = self.artifacts["a1_label"]
        a0_input["coordinator_envelope_commitment_sha256"] = V.canonical_sha256(
            self.artifacts["coordinator_envelope"]
        )
        a0_label["a0_input_ref"] = V.artifact_ref(a0_input)
        reveal["a0_input_ref"] = V.artifact_ref(a0_input)
        reveal["a0_label_ref"] = V.artifact_ref(a0_label)
        label["a0_input_ref"] = V.artifact_ref(a0_input)
        label["a0_label_ref"] = V.artifact_ref(a0_label)
        label["a1_reveal_ref"] = V.artifact_ref(reveal)
        self.events = self.build_audit_events()

    def recompute_id_chain(self) -> None:
        instruction = self.artifacts["a0_input"]["agent_visible_instruction"]
        instruction["content_sha256"] = sha_text(instruction["text"])
        self.rebuild_prefix_commits()
        a0_label = self.artifacts["a0_label"]
        a0_label["boundary_location_id"] = self.artifacts["a0_input"][
            "boundary_location_id"
        ]
        preimage = a0_label["adjudicated_event_preimage"]
        preimage["boundary_location_id"] = a0_label["boundary_location_id"]
        preimage["normative_action_difference_sha256"] = sha_text(
            a0_label["normative_action_difference"]
        )
        a0_label["adjudicated_event_id"] = V.adjudicated_event_id(preimage)
        self.artifacts["a1_reveal"]["adjudicated_event_id"] = a0_label[
            "adjudicated_event_id"
        ]
        self.artifacts["a1_label"]["adjudicated_event_id"] = a0_label[
            "adjudicated_event_id"
        ]
        if self.artifacts["a1_reveal"]["reveal_kind"] == "observed_action":
            self.artifacts["a1_label"]["affected_obligation_assessments"][0][
                "evidence_pointer"
            ] = self.action_evidence_pointer()
        self.refresh_links()

    def convert_to_omission(self) -> None:
        a0_label = self.artifacts["a0_label"]
        required = {
            "action_signature": "ACT-REQUIRED",
            "semantic_description": "Perform required repair.",
            "deadline_or_commit_rule": "Before observation 3 commit.",
            "obligation_ids": ["O-KEEP-NEW"],
        }
        a0_label["required_action_spec"] = required
        a0_label["adjudicated_event_preimage"]["boundary_type"] = (
            "required_action_omission"
        )
        a0_label["adjudicated_event_id"] = V.adjudicated_event_id(
            a0_label["adjudicated_event_preimage"]
        )
        entries = []
        previous = None
        for sequence, ordinal in enumerate((2, 3)):
            entry = {
                "sequence": sequence,
                "observation_ordinal": ordinal,
                "observed_at": "2026-07-28T09:02:%02d+08:00" % (35 + sequence * 10),
                "agent_visible_text": "Synthetic interval %d" % ordinal,
                "normalized_actions": (
                    [
                        {
                            "action_ordinal": 2,
                            "action_signature": "ACT-OTHER",
                            "semantic_description": "Unrelated action.",
                            "matches_required_action": False,
                        }
                    ]
                    if sequence == 0
                    else []
                ),
                "previous_entry_sha256": previous,
                "entry_sha256": digest("placeholder-interval"),
            }
            entry["entry_sha256"] = V.chained_entry_sha256(entry)
            previous = entry["entry_sha256"]
            entries.append(entry)
        omission = {
            "artifact_type": "omission_interval",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "omission-interval-001",
            "unit_alias": "U-ABCDEF012345",
            "adjudicated_event_id": a0_label["adjudicated_event_id"],
            "required_action_spec_sha256": V.canonical_sha256(required),
            "decision_observation_ordinal": 1,
            "deadline_observation_ordinal": 3,
            "deadline_evidence": {
                "observation_ordinal": 3,
                "content_sha256": V.canonical_sha256(entries[-1]),
                "deadline_or_commit_reached": True,
            },
            "source_snapshot_sha256": self.artifacts["coordinator_envelope"][
                "source_snapshot"
            ]["raw_response_sha256"],
            "complete_through_deadline": True,
            "entries": entries,
            "chain_tip_sha256": entries[-1]["entry_sha256"],
            "frozen_at": "2026-07-28T09:02:50+08:00",
        }
        self.artifacts["omission_interval"] = omission
        reveal = self.artifacts["a1_reveal"]
        reveal["adjudicated_event_id"] = a0_label["adjudicated_event_id"]
        reveal["reveal_kind"] = "omission_interval"
        reveal["behavior_evidence"] = {
            "kind": "omission_interval",
            "omission_interval_ref": V.artifact_ref(omission),
        }
        label = self.artifacts["a1_label"]
        label["adjudicated_event_id"] = a0_label["adjudicated_event_id"]
        label["action_assessment"] = {
            "candidate_action_executed": False,
            "compatible_with_p_old": "yes",
            "compatible_with_p_new": "no",
            "required_action_omission": True,
            "deadline_or_commit_reached": True,
            "phenotype": "target_positive",
        }
        label["affected_obligation_assessments"][0]["evidence_pointer"] = {
            "artifact_id": omission["artifact_id"],
            "observation_ordinal": 3,
            "content_sha256": V.canonical_sha256(entries[-1]),
            "source_kind": "omission_interval",
        }
        self.refresh_links()

    def write(self) -> None:
        for name, filename in V.ARTIFACT_FILES.items():
            (self.root / filename).write_text(
                json.dumps(self.artifacts[name], sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
        (self.root / V.PREFIX_COMMIT_LOG_FILE).write_text(
            "".join(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n" for item in self.prefix_commits),
            encoding="utf-8",
        )
        (self.root / V.AUDIT_LOG_FILE).write_text(
            "".join(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n" for item in self.events),
            encoding="utf-8",
        )
        omission_path = self.root / V.OMISSION_INTERVAL_FILE
        if "omission_interval" in self.artifacts:
            omission_path.write_text(
                json.dumps(self.artifacts["omission_interval"], sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
        elif omission_path.exists():
            omission_path.unlink()

    def mechanical_result(self) -> Mapping[str, Any]:
        self.write()
        loaded, errors = V.load_bundle_and_schemas(self.root, SCHEMA_DIR)
        if errors:
            return V.verdict(False, errors, [])
        assert loaded is not None
        artifacts = loaded["artifacts"]
        schemas = loaded["schemas"]
        completed = [V.STAGE_ORDER[0]]
        errors = V.validate_schema_meta(schemas)
        if errors:
            return V.verdict(False, errors, completed, artifacts)
        completed.append(V.STAGE_ORDER[1])
        errors = V.validate_instances(artifacts, schemas)
        if errors:
            return V.verdict(False, errors, completed, artifacts)
        completed.append(V.STAGE_ORDER[2])
        error = V.first_semantic_error(artifacts)
        if error:
            return V.verdict(False, [error], completed, artifacts)
        completed.append(V.STAGE_ORDER[3])
        error = V.first_content_hash_error(artifacts, schemas, self.root)
        if error:
            return V.verdict(False, [error], completed, artifacts)
        completed.append(V.STAGE_ORDER[4])
        error = V.first_chain_exposure_error(artifacts)
        if error:
            return V.verdict(False, [error], completed, artifacts)
        completed.append(V.STAGE_ORDER[5])
        return V.verdict(True, [], completed, artifacts)


class ValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = {
            item["case_id"]: item
            for item in json.loads(CASE_PATH.read_text(encoding="utf-8"))
        }

    def unit(
        self,
        source_labels: Optional[List[str]] = None,
        p_old_status: str = "pre_update_frozen",
    ) -> SyntheticUnit:
        temp = tempfile.TemporaryDirectory(prefix="stage0f-unit-")
        self.addCleanup(temp.cleanup)
        return SyntheticUnit(Path(temp.name), source_labels, p_old_status)

    def assert_case(self, case_id: str, result: Mapping[str, Any]) -> None:
        expected = self.cases[case_id]
        self.assertFalse(result["valid"], result)
        self.assertEqual(len(result["errors"]), 1, result)
        self.assertEqual(result["errors"][0]["stage"], expected["expected_stage"])
        self.assertEqual(result["errors"][0]["code"], expected["expected_code"])

    def test_synthetic_component_mechanics_pass(self) -> None:
        result = self.unit().mechanical_result()
        self.assertTrue(result["valid"], result)
        self.assertTrue(all(item["status"] == "PASS" for item in result["stages"]))

    def test_complete_omission_component_mechanics_pass(self) -> None:
        unit = self.unit()
        unit.convert_to_omission()
        result = unit.mechanical_result()
        self.assertTrue(result["valid"], result)

    def test_production_single_unit_is_fail_closed(self) -> None:
        unit = self.unit()
        result = V.validate_bundle(unit.root, SCHEMA_DIR)
        self.assertEqual(result["errors"][0]["code"], "SEM_BLOCK_BARRIER_CONTEXT_REQUIRED")

    def test_block_entry_is_fail_closed_not_ready(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="stage0f-block-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        unit = self.unit()
        barrier = {
            "artifact_type": "block_a0_barrier",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "block-barrier-001",
            "block_id": "BLOCK-SYNTHETIC",
            "block_scope": "synthetic_test_only",
            "expected_unit_scan_count": 1,
            "location_manifest_sha256": digest("location-manifest"),
            "location_freezes": [{
                "unit_alias": "U-ABCDEF012345",
                "boundary_location_id": unit.artifacts["a0_input"]["boundary_location_id"],
                "task_id": "035",
                "hosted_config_id": "hosted-config-alpha",
                "coordinator_envelope_ref": V.artifact_ref(unit.artifacts["coordinator_envelope"]),
                "a0_input_ref": V.artifact_ref(unit.artifacts["a0_input"]),
                "a0_raw_labels_ref": {"artifact_id":"a0-raw-labels-001","sha256":digest("raw-label-set")},
                "a0_adjudication_ref": V.artifact_ref(unit.artifacts["a0_label"]),
                "adjudicated_event_ids": [unit.artifacts["a0_label"]["adjudicated_event_id"]],
                "prefix_chain_tip_sha256": unit.artifacts["a0_input"]["prefix_chain_tip_sha256"],
                "a0_label_frozen_at": unit.artifacts["a0_label"]["frozen_at"]
            }],
            "role_registry": {
                "a0_annotator_aliases": ["annotator-a0","annotator-a0b"],
                "a0_adjudicator_aliases": ["adjudicator-a0"],
                "a1_annotator_aliases": ["annotator-a1"],
                "stage_b_annotator_aliases": ["annotator-stage-b"],
                "separation_is_permanent": True
            },
            "exposure_policy": {
                "classification":"coordinator_secret",
                "allowed_roles":["coordinator"],
                "public_linkage":"content_hash_only"
            },
            "sealed_by":"coordinator-main",
            "sealed_at":"2026-07-28T09:02:30+08:00"
        }
        (root / V.BLOCK_BARRIER_FILE).write_text(json.dumps(barrier), encoding="utf-8")
        result = V.validate_block_bundle(root, SCHEMA_DIR)
        self.assertEqual(result["errors"][0]["code"], "SEM_BLOCK_BARRIER_LEDGER_NOT_IMPLEMENTED")

    def test_same_location_supports_multiple_semantic_event_ids(self) -> None:
        unit = self.unit()
        first = copy.deepcopy(unit.artifacts["a0_label"]["adjudicated_event_preimage"])
        second = copy.deepcopy(first)
        second["p_new_proposition_id"] = "PROP-ANOTHER-NEW-STATE"
        self.assertEqual(first["boundary_location_id"], second["boundary_location_id"])
        self.assertNotEqual(V.adjudicated_event_id(first), V.adjudicated_event_id(second))

    def test_dependency_missing_has_no_fallback(self) -> None:
        unit = self.unit()
        with mock.patch.object(V, "JSONSCHEMA_IMPORT_ERROR", ImportError("missing")):
            result = V.validate_bundle(unit.root, SCHEMA_DIR)
        self.assertEqual(result["errors"][0]["code"], "DEPENDENCY_JSONSCHEMA_UNAVAILABLE")

    def test_all_object_schemas_closed_and_meta_valid(self) -> None:
        schemas = {
            name: V.load_json_no_duplicates(SCHEMA_DIR / filename)
            for name, filename in V.SCHEMA_FILES.items()
        }
        self.assertEqual(V.validate_schema_meta(schemas), [])

    def test_duplicate_json_key(self) -> None:
        unit = self.unit()
        path = unit.root / "a0_input.json"
        raw = path.read_text()
        path.write_text(raw.replace('"artifact_type":"a0_input"', '"artifact_type":"a0_input","artifact_type":"a0_input"', 1))
        self.assert_case("duplicate_json_key", V.validate_bundle(unit.root, SCHEMA_DIR))

    def test_nested_extra_key(self) -> None:
        unit = self.unit()
        unit.artifacts["a0_input"]["normative_schema"]["sources"][0]["debug"] = True
        self.assert_case("nested_extra_key", unit.mechanical_result())

    def test_generator_semantic_anchor_field(self) -> None:
        unit = self.unit()
        unit.prefix_commits[-1]["generator_decisions"][0]["proposition_id"] = "PROP-LEAK"
        self.assert_case("generator_semantic_anchor_field", unit.mechanical_result())

    def test_batch_observation_gap(self) -> None:
        unit = self.unit()
        unit.artifacts["a0_input"]["prefix_observations"][1]["observation_ordinal"] = 2
        unit.artifacts["a0_input"]["cutoff_observation_ordinal"] = 2
        unit.refresh_links()
        self.assert_case("batch_observation_gap", unit.mechanical_result())

    def test_future_p_new(self) -> None:
        unit = self.unit()
        unit.artifacts["a0_label"]["p_new"]["evidence_pointer"]["observation_ordinal"] = 2
        unit.refresh_links()
        self.assert_case("future_p_new", unit.mechanical_result())

    def test_late_p_old(self) -> None:
        unit = self.unit()
        unit.artifacts["a0_label"]["p_old"]["evidence_pointer"]["observation_ordinal"] = 1
        unit.refresh_links()
        self.assert_case("late_p_old", unit.mechanical_result())

    def test_source_nonexclusive(self) -> None:
        unit = self.unit()
        unit.artifacts["a0_label"]["update_source_evidence"].append({
            "label":"source_unidentifiable",
            "evidence_pointer":copy.deepcopy(unit.artifacts["a0_label"]["p_new"]["evidence_pointer"])
        })
        unit.refresh_links()
        self.assert_case("source_nonexclusive", unit.mechanical_result())

    def test_unidentifiable_environment_true(self) -> None:
        unit = self.unit(["source_unidentifiable"])
        unit.artifacts["a0_label"]["environment_primary_eligible"] = True
        unit.refresh_links()
        self.assert_case("unidentifiable_environment_true", unit.mechanical_result())

    def test_hypothesized_old_primary_true(self) -> None:
        unit = self.unit(p_old_status="old_state_hypothesized")
        unit.artifacts["a0_label"]["primary_analysis_eligible"] = True
        unit.refresh_links()
        self.assert_case("hypothesized_old_primary_true", unit.mechanical_result())

    def test_obligation_coverage_missing(self) -> None:
        unit = self.unit()
        unit.artifacts["a0_label"]["obligation_assessments"].pop()
        unit.refresh_links()
        self.assert_case("obligation_coverage_missing", unit.mechanical_result())

    def test_dangling_obligation(self) -> None:
        unit = self.unit()
        unit.artifacts["a0_label"]["affected_obligation_ids"][0] = "O-MISSING"
        unit.refresh_links()
        self.assert_case("dangling_obligation", unit.mechanical_result())

    def test_semantic_location_hash(self) -> None:
        unit = self.unit()
        fake = V.adjudicated_event_id(unit.artifacts["a0_label"]["adjudicated_event_preimage"])
        unit.prefix_commits[-1]["boundary_location_id"] = fake
        unit.prefix_commits[-1]["generator_decisions"][0]["boundary_location_id"] = fake
        unit.prefix_commits[-1]["generator_decisions"][1]["boundary_location_id"] = fake
        unit.artifacts["a0_input"]["boundary_location_id"] = fake
        unit.refresh_links()
        self.assert_case("semantic_location_hash", unit.mechanical_result())

    def test_rolling_prefix_late(self) -> None:
        unit = self.unit()
        unit.prefix_commits[0]["committed_at"] = "2026-07-28T09:00:20+08:00"
        unit.prefix_commits[0]["entry_sha256"] = V.chained_entry_sha256(unit.prefix_commits[0])
        unit.refresh_links()
        self.assert_case("rolling_prefix_late", unit.mechanical_result())

    def test_rolling_prefix_future_exposure(self) -> None:
        unit = self.unit()
        unit.prefix_commits[0]["generator_decisions"][0]["visible_through_observation_ordinal"] = 1
        unit.refresh_links()
        self.assert_case("rolling_prefix_future_exposure", unit.mechanical_result())

    def test_a1_revealed_early(self) -> None:
        unit = self.unit()
        unit.artifacts["a1_reveal"]["revealed_at"] = "2026-07-28T09:01:30+08:00"
        unit.refresh_links()
        self.assert_case("a1_revealed_early", unit.mechanical_result())

    def test_single_action_omission(self) -> None:
        unit = self.unit()
        label = unit.artifacts["a0_label"]
        label["required_action_spec"] = {
            "action_signature":"ACT-REQUIRED",
            "semantic_description":"Repair.",
            "deadline_or_commit_rule":"Before deadline.",
            "obligation_ids":["O-KEEP-NEW"]
        }
        label["adjudicated_event_preimage"]["boundary_type"] = "required_action_omission"
        label["adjudicated_event_id"] = V.adjudicated_event_id(label["adjudicated_event_preimage"])
        unit.artifacts["a1_reveal"]["adjudicated_event_id"] = label["adjudicated_event_id"]
        unit.artifacts["a1_label"]["adjudicated_event_id"] = label["adjudicated_event_id"]
        unit.refresh_links()
        self.assert_case("single_action_omission", unit.mechanical_result())

    def test_omission_interval_gap(self) -> None:
        unit = self.unit()
        unit.convert_to_omission()
        unit.artifacts["omission_interval"]["entries"].pop(0)
        unit.refresh_links()
        self.assert_case("omission_interval_gap", unit.mechanical_result())

    def test_omission_required_action_present(self) -> None:
        unit = self.unit()
        unit.convert_to_omission()
        action = unit.artifacts["omission_interval"]["entries"][0]["normalized_actions"][0]
        action["action_signature"] = "ACT-REQUIRED"
        action["matches_required_action"] = True
        unit.refresh_links()
        self.assert_case("omission_required_action_present", unit.mechanical_result())

    def test_source_file_path_missing(self) -> None:
        unit = self.unit()
        unit.artifacts["coordinator_envelope"]["source_snapshot"]["raw_response_relative_path"] = "raw/missing.json"
        unit.refresh_links()
        self.assert_case("source_file_path_missing", unit.mechanical_result())

    def test_asset_hash_mismatch(self) -> None:
        unit = self.unit()
        unit.artifacts["coordinator_envelope"]["asset_manifest"][0]["sha256"] = digest("wrong")
        unit.refresh_links()
        self.assert_case("asset_hash_mismatch", unit.mechanical_result())

    def test_adjudicated_event_tamper(self) -> None:
        unit = self.unit()
        tampered = digest("tampered-event")
        unit.artifacts["a0_label"]["adjudicated_event_id"] = tampered
        unit.artifacts["a1_reveal"]["adjudicated_event_id"] = tampered
        unit.artifacts["a1_label"]["adjudicated_event_id"] = tampered
        unit.refresh_links()
        self.assert_case("adjudicated_event_tamper", unit.mechanical_result())

    def test_a0_label_ref_mismatch(self) -> None:
        unit = self.unit()
        unit.artifacts["a1_reveal"]["a0_label_ref"]["sha256"] = digest("wrong-ref")
        self.assert_case("a0_label_ref_mismatch", unit.mechanical_result())

    def test_evidence_content_mismatch(self) -> None:
        unit = self.unit()
        unit.artifacts["a0_label"]["p_new"]["evidence_pointer"]["content_sha256"] = digest("wrong-evidence")
        unit.refresh_links()
        self.assert_case("evidence_content_mismatch", unit.mechanical_result())

    def test_audit_entry_tamper(self) -> None:
        unit = self.unit()
        unit.events[0]["entry_sha256"] = digest("wrong-entry")
        self.assert_case("audit_entry_tamper", unit.mechanical_result())

    def test_audit_delete(self) -> None:
        unit = self.unit()
        unit.events.pop(3)
        self.assert_case("audit_delete", unit.mechanical_result())

    def test_audit_reorder(self) -> None:
        unit = self.unit()
        unit.events[1], unit.events[2] = unit.events[2], unit.events[1]
        self.assert_case("audit_reorder", unit.mechanical_result())

    def test_audit_fork(self) -> None:
        unit = self.unit()
        unit.events.append(copy.deepcopy(unit.events[2]))
        self.assert_case("audit_fork", unit.mechanical_result())

    def test_identity_leak(self) -> None:
        unit = self.unit()
        unit.artifacts["a0_input"]["agent_visible_instruction"]["text"] = "model-family-alpha"
        unit.recompute_id_chain()
        self.assert_case("identity_leak", unit.mechanical_result())

    def test_result_url_leak(self) -> None:
        unit = self.unit()
        unit.artifacts["a0_input"]["agent_visible_instruction"]["text"] = "https://example.invalid/result/alpha"
        unit.recompute_id_chain()
        self.assert_case("result_url_leak", unit.mechanical_result())

    def test_registry_coverage(self) -> None:
        methods = {
            name.removeprefix("test_")
            for name in dir(self)
            if name.startswith("test_")
        }
        noncases = {
            "synthetic_component_mechanics_pass",
            "complete_omission_component_mechanics_pass",
            "production_single_unit_is_fail_closed",
            "block_entry_is_fail_closed_not_ready",
            "same_location_supports_multiple_semantic_event_ids",
            "dependency_missing_has_no_fallback",
            "all_object_schemas_closed_and_meta_valid",
            "registry_coverage",
        }
        self.assertEqual(set(self.cases), methods - noncases)


if __name__ == "__main__":
    unittest.main()
