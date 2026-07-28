#!/usr/bin/env python3
"""Mechanical tests for the fail-closed Stage 0F measurement implementation.

The positive tests below validate only synthetic component mechanics.  The
production entry point is separately required to reject both a lone unit and
the incomplete block-barrier implementation.
"""

from __future__ import annotations

import copy
import ast
import hashlib
import importlib.util
import json
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional
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


class SyntheticFullBlock:
    """Synthetic full-block mechanics only; never research evidence."""

    def __init__(self, root: Path, event_count: int = 2) -> None:
        if event_count not in (0, 2):
            raise ValueError("synthetic builder supports zero or two events")
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.component = root / "component"
        self.unit = SyntheticUnit(self.component)
        self.schemas = self.unit.schemas
        self.unit_alias = self.unit.artifacts["a0_input"]["unit_alias"]
        self.block_id = "BLOCK-SYNTHETIC"
        self.event_count = event_count
        self.fixed: Dict[str, Dict[str, Any]] = {}
        self.location_artifacts: List[Dict[str, Any]] = []
        self.a1_artifacts: List[Dict[str, Any]] = []
        self.source_search_artifacts: List[Dict[str, Any]] = []
        self._build()

    @staticmethod
    def _write_json(path: Path, value: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    def _relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def _a0_input_for_ordinal(
        self,
        base: Mapping[str, Any],
        prefix: Mapping[str, Any],
        ordinal: int,
    ) -> Dict[str, Any]:
        value = copy.deepcopy(base)
        value["artifact_id"] = "a0-input-loc-%d" % ordinal
        value["prefix_observations"] = value["prefix_observations"][
            : ordinal + 1
        ]
        value["cutoff_observation_ordinal"] = ordinal
        value["candidate_locator"]["update_observation_ordinal"] = ordinal
        value["a0_prefix_payload_sha256"] = prefix[
            "a0_prefix_payload_sha256"
        ]
        value["boundary_location_id"] = prefix["boundary_location_id"]
        value["prefix_chain_tip_sha256"] = prefix["entry_sha256"]
        value["frozen_at"] = "2026-07-28T09:01:00+08:00"
        return value

    def _retarget_a0_label(
        self,
        label: Dict[str, Any],
        a0_input: Mapping[str, Any],
        event_index: int,
        supporting_ids: List[str],
    ) -> None:
        label["artifact_id"] = "a0-label-event-%d" % event_index
        label["a0_input_ref"] = V.artifact_ref(a0_input)
        label["boundary_location_id"] = a0_input["boundary_location_id"]
        label["annotator_alias"] = "adjudicator-a0"
        label["frozen_at"] = "2026-07-28T09:02:%02d+08:00" % (
            event_index * 5
        )
        if event_index == 2:
            label["p_new"]["proposition_id"] = "PROP-ANOTHER-NEW-STATE"
            label["p_new"]["statement"] = "Another new state is active."
            label["adjudicated_event_preimage"][
                "p_new_proposition_id"
            ] = "PROP-ANOTHER-NEW-STATE"
        observations = {
            item["observation_ordinal"]: item
            for item in a0_input["prefix_observations"]
        }
        for pointer_holder in (
            label["p_old"],
            label["p_new"],
            *label["update_source_evidence"],
        ):
            pointer = pointer_holder.get("evidence_pointer")
            if pointer is not None:
                pointer["artifact_id"] = a0_input["artifact_id"]
                pointer["content_sha256"] = V.canonical_sha256(
                    observations[pointer["observation_ordinal"]]
                )
        label["supporting_a0_raw_label_ids"] = supporting_ids
        preimage = label["adjudicated_event_preimage"]
        preimage["boundary_location_id"] = a0_input["boundary_location_id"]
        preimage["supporting_a0_raw_label_ids"] = supporting_ids
        label["adjudicated_event_id"] = V.adjudicated_event_id(preimage)

    def attach_source_search_results(
        self,
        artifact: Mapping[str, Any],
        roster: List[str],
        searched_scope_sha256: Optional[str] = None,
    ) -> None:
        location = next(
            item
            for item in self.location_artifacts
            if item["a0_input"]["boundary_location_id"]
            == artifact["boundary_location_id"]
        )
        container_event = next(
            event
            for event in location["adjudication"]["events"]
            if event["adjudicated_event_id"] == artifact["event_id"]
        )
        refs = []
        for index, scope_item in enumerate(roster):
            result = {
                "artifact_type": "source_search_result",
                "schema_version": V.SCHEMA_VERSION,
                "canonicalization": V.CANONICALIZATION,
                "artifact_id": "source-search-%s-%d"
                % (artifact["event_id"][:12], index),
                "unit_alias": artifact["unit_alias"],
                "boundary_location_id": artifact[
                    "boundary_location_id"
                ],
                "searched_scope_item": scope_item,
                "checked_artifact_refs": [
                    V.artifact_ref(location["a0_input"])
                ],
                "result_status": "no_source_found",
                "synthetic_test_only": True,
                "research_evidence": False,
                "frozen_at": "2026-07-28T09:01:55+08:00",
            }
            path = (
                artifact["label_path"].parent
                / ("source-search-%d.json" % index)
            )
            self.source_search_artifacts.append(
                {"artifact": result, "path": path}
            )
            refs.append(
                {
                    "artifact_ref": V.artifact_ref(result),
                    "relative_path": self._relative(path),
                }
            )
        container_event["source_resolution"] = {
            "status": "source_unidentifiable",
            "reason_code": "NO_CUTOFF_SOURCE_AFTER_FROZEN_SEARCH",
            "searched_scope_roster": roster,
            "searched_scope_sha256": (
                V.canonical_sha256(roster)
                if searched_scope_sha256 is None
                else searched_scope_sha256
            ),
            "search_result_refs": refs,
        }

    def _build(self) -> None:
        coordinator = self.unit.artifacts["coordinator_envelope"]
        event_input = copy.deepcopy(self.unit.artifacts["a0_input"])
        prefix_entries = copy.deepcopy(self.unit.prefix_commits)
        observation2_asset_path = self.component / "assets" / "obs2.txt"
        observation2_asset_path.write_text(
            "synthetic observation 2\n", encoding="utf-8"
        )
        observation2_asset = {
            "asset_id": "asset-obs-2",
            "observation_ordinal": 2,
            "relative_path": "assets/obs2.txt",
            "sha256": hashlib.sha256(
                observation2_asset_path.read_bytes()
            ).hexdigest(),
            "media_type": "text/plain",
        }
        coordinator["asset_manifest"].append(observation2_asset)
        observation2 = {
            "observation_ordinal": 2,
            "observed_at": "2026-07-28T09:00:30+08:00",
            "assets": [
                {
                    "asset_id": observation2_asset["asset_id"],
                    "sha256": observation2_asset["sha256"],
                }
            ],
            "agent_visible_text": "Synthetic terminal observation.",
            "normalized_prior_actions": ["batch-action-1"],
            "missingness": "none",
        }
        full_input = copy.deepcopy(event_input)
        full_input["prefix_observations"].append(observation2)
        payload2 = V.a0_prefix_payload_sha256(full_input, 2)
        location2 = V.boundary_location_id(
            full_input["boundary_namespace"],
            self.unit_alias,
            2,
            payload2,
        )
        prefix2 = {
            "artifact_type": "prefix_commit",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "prefix_commit_log_id": full_input["prefix_commit_log_id"],
            "unit_alias": self.unit_alias,
            "sequence": 2,
            "observation_ordinal": 2,
            "observation_sha256": V.canonical_sha256(observation2),
            "boundary_namespace": full_input["boundary_namespace"],
            "a0_prefix_payload_sha256": payload2,
            "boundary_location_id": location2,
            "committed_at": "2026-07-28T09:00:33+08:00",
            "generator_decisions": [
                {
                    "generator_alias": "generator-a",
                    "visible_through_observation_ordinal": 2,
                    "decision": "reject_location",
                    "boundary_location_id": location2,
                    "decided_at": "2026-07-28T09:00:31+08:00",
                },
                {
                    "generator_alias": "generator-b",
                    "visible_through_observation_ordinal": 2,
                    "decision": "reject_location",
                    "boundary_location_id": location2,
                    "decided_at": "2026-07-28T09:00:32+08:00",
                },
            ],
            "previous_entry_sha256": prefix_entries[-1]["entry_sha256"],
            "entry_sha256": digest("prefix-2"),
        }
        prefix2["entry_sha256"] = V.chained_entry_sha256(prefix2)
        prefix_entries.append(prefix2)
        full_input["a0_prefix_payload_sha256"] = payload2
        full_input["boundary_location_id"] = location2
        full_input["prefix_chain_tip_sha256"] = prefix2["entry_sha256"]
        full_input["cutoff_observation_ordinal"] = 2

        raw_dir = self.component / "raw"
        action_paths = []
        for ordinal in (0, 1):
            path = raw_dir / ("action-%d.bin" % ordinal)
            path.write_bytes(
                ("synthetic batch action %d\n" % ordinal).encode("utf-8")
            )
            action_paths.append(path)
        stream_entries = []
        raw_entries = []
        for ordinal, prefix in enumerate(prefix_entries):
            observation = (
                event_input["prefix_observations"][ordinal]
                if ordinal < 2
                else observation2
            )
            entry = {
                "observation_ordinal": ordinal,
                "observation_sha256": prefix["observation_sha256"],
                "observed_at": observation["observed_at"],
                "prefix_commit_entry_sha256": prefix["entry_sha256"],
                "prefix_committed_at": prefix["committed_at"],
                "current_action": {"kind": "terminal_no_action"},
            }
            if ordinal < 2:
                action_path = action_paths[ordinal]
                reveal_second = 15 + ordinal * 10
                next_observation = (
                    event_input["prefix_observations"][ordinal + 1]
                    if ordinal == 0
                    else observation2
                )
                entry["current_action"] = {
                    "kind": "current_action",
                    "action_unit": "batch_bundle",
                    "action_bytes_relative_path": self._relative(action_path),
                    "action_bytes_sha256": hashlib.sha256(
                        action_path.read_bytes()
                    ).hexdigest(),
                    "revealed_at": "2026-07-28T09:00:%02d+08:00"
                    % reveal_second,
                    "subactions": [
                        {
                            "action_ordinal": ordinal * 2 + offset,
                            "subaction_sha256": digest(
                                "subaction-%d-%d" % (ordinal, offset)
                            ),
                            "first_observable_at": "2026-07-28T09:00:%02d+08:00"
                            % reveal_second,
                        }
                        for offset in (0, 1)
                    ],
                    "next_observation_ordinal": ordinal + 1,
                    "next_observation_sha256": V.canonical_sha256(
                        next_observation
                    ),
                    "next_observed_at": next_observation["observed_at"],
                }
            stream_entries.append(entry)
            raw_entries.append(
                {
                    "observation": copy.deepcopy(observation),
                    "current_action": copy.deepcopy(
                        entry["current_action"]
                    ),
                }
            )
        source_path = raw_dir / "published-source-trajectory.json"
        source_response = {
            "source_format": V.SYNTHETIC_PUBLISHED_TRAJECTORY_FORMAT,
            "synthetic_test_only": True,
            "research_evidence": False,
            "unit_alias": self.unit_alias,
            "trajectory_id": coordinator["identity"]["trajectory_id"],
            "trajectory_mode": coordinator["identity"]["trajectory_mode"],
            "entries": raw_entries,
            "published_at": "2026-07-28T08:58:00+08:00",
        }
        self._write_json(source_path, source_response)
        coordinator["source_snapshot"][
            "raw_response_relative_path"
        ] = "raw/published-source-trajectory.json"
        coordinator["source_snapshot"][
            "raw_response_sha256"
        ] = hashlib.sha256(source_path.read_bytes()).hexdigest()
        self._write_json(
            self.component / "coordinator_envelope.json", coordinator
        )
        full_input[
            "coordinator_envelope_commitment_sha256"
        ] = V.canonical_sha256(coordinator)
        trajectory_path = raw_dir / "normalized-trajectory.json"
        raw_trajectory = {
            "artifact_type": "block_raw_trajectory",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "raw-trajectory-001",
            "raw_format": V.RAW_TRAJECTORY_FORMAT,
            "unit_alias": self.unit_alias,
            "trajectory_id": coordinator["identity"]["trajectory_id"],
            "trajectory_mode": coordinator["identity"]["trajectory_mode"],
            "entries": raw_entries,
            "frozen_at": "2026-07-28T09:00:35+08:00",
        }
        self._write_json(trajectory_path, raw_trajectory)
        stream = {
            "artifact_type": "block_stream_ledger",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "stream-ledger-001",
            "unit_alias": self.unit_alias,
            "trajectory_mode": "batch_tool_model_steps",
            "raw_trajectory_ref": V.artifact_ref(raw_trajectory),
            "raw_trajectory_relative_path": self._relative(trajectory_path),
            "raw_parser": {
                "parser_id": V.RAW_TRAJECTORY_PARSER_ID,
                "input_format": V.RAW_TRAJECTORY_FORMAT,
                "projection_name": V.RAW_TRAJECTORY_PROJECTION,
                "executable_sha256": V.validator_file_sha256(),
            },
            "entries": stream_entries,
            "frozen_at": "2026-07-28T09:00:40+08:00",
        }
        prefix_path = self.component / "full-prefix.ndjson"
        prefix_path.write_text(
            "".join(
                json.dumps(item, sort_keys=True, separators=(",", ":"))
                + "\n"
                for item in prefix_entries
            ),
            encoding="utf-8",
        )
        stream_path = self.component / "stream-ledger.json"
        self._write_json(stream_path, stream)
        self.coordinator = coordinator
        self.raw_source_path = source_path
        self.raw_trajectory = raw_trajectory
        self.raw_trajectory_path = trajectory_path
        self.stream = stream
        self.stream_path = stream_path

        frame = {
            "artifact_type": "block_frame",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "block-frame-001",
            "block_id": self.block_id,
            "block_scope": "synthetic_test_only",
            "frame_source_ref": {
                "artifact_id": "synthetic-frame-source",
                "sha256": digest("external-frame-source"),
            },
            "expected_unit_count": 1,
            "expected_units": [
                {
                    "unit_alias": self.unit_alias,
                    "task_id": coordinator["identity"]["task_id"],
                    "hosted_config_id": coordinator["identity"][
                        "hosted_config_id"
                    ],
                    "coordinator_envelope_ref": V.artifact_ref(coordinator),
                    "coordinator_envelope_relative_path": "component/coordinator_envelope.json",
                }
            ],
            "frozen_at": "2026-07-28T08:59:00+08:00",
        }
        self.fixed["block_frame"] = frame
        self.frame_sha256 = V.canonical_sha256(frame)

        locations = []
        location_freezes = []
        all_a1_freezes = []
        event_input_by_ordinal = {
            0: self._a0_input_for_ordinal(
                full_input, prefix_entries[0], 0
            ),
            1: self._a0_input_for_ordinal(
                full_input, prefix_entries[1], 1
            ),
            2: self._a0_input_for_ordinal(
                full_input, prefix_entries[2], 2
            ),
        }
        all_event_count = 0
        for ordinal, prefix in enumerate(prefix_entries):
            location_dir = self.component / "locations" / str(ordinal)
            a0_input = event_input_by_ordinal[ordinal]
            a0_input_path = location_dir / "a0_input.json"
            raw_submissions = {
                "artifact_type": "block_a0_submissions",
                "schema_version": V.SCHEMA_VERSION,
                "canonicalization": V.CANONICALIZATION,
                "artifact_id": "a0-submissions-%d" % ordinal,
                "unit_alias": self.unit_alias,
                "boundary_location_id": prefix["boundary_location_id"],
                "a0_input_ref": V.artifact_ref(a0_input),
                "schema_bundle_sha256": V.schema_bundle_sha256(
                    self.schemas
                ),
                "codebook_sha256": coordinator["provenance"][
                    "version_hashes"
                ]["codebook_sha256"],
                "submissions": [
                    {
                        "annotator_alias": "annotator-a0",
                        "raw_labels": [],
                        "frozen_at": "2026-07-28T09:01:20+08:00",
                    },
                    {
                        "annotator_alias": "annotator-a0b",
                        "raw_labels": [],
                        "frozen_at": "2026-07-28T09:01:30+08:00",
                    },
                ],
                "frozen_at": "2026-07-28T09:01:40+08:00",
            }
            container_events = []
            dispositions = []
            if ordinal == 1 and self.event_count:
                for event_index in range(1, self.event_count + 1):
                    base_label = copy.deepcopy(
                        self.unit.artifacts["a0_label"]
                    )
                    if event_index == 2:
                        base_label["p_new"][
                            "proposition_id"
                        ] = "PROP-ANOTHER-NEW-STATE"
                    raw_payload = {
                        "p_old_proposition_id": base_label["p_old"][
                            "proposition_id"
                        ],
                        "p_new_proposition_id": base_label["p_new"][
                            "proposition_id"
                        ],
                        "update_source_labels": [
                            "world_truth_changed"
                        ],
                        "normative_action_difference": base_label[
                            "normative_action_difference"
                        ],
                        "affected_obligation_ids": base_label[
                            "affected_obligation_ids"
                        ],
                        "boundary_type": base_label[
                            "adjudicated_event_preimage"
                        ]["boundary_type"],
                    }
                    support_ids = []
                    support_raws = []
                    for submission in raw_submissions["submissions"]:
                        raw_id = V.block_a0_raw_label_id(
                            self.unit_alias,
                            prefix["boundary_location_id"],
                            raw_submissions["schema_bundle_sha256"],
                            raw_submissions["codebook_sha256"],
                            submission["annotator_alias"],
                            raw_payload,
                        )
                        raw_record = {
                            "a0_raw_label_id": raw_id,
                            "semantic_payload": copy.deepcopy(
                                raw_payload
                            ),
                        }
                        submission["raw_labels"].append(raw_record)
                        support_raws.append(raw_record)
                        support_ids.append(raw_id)
                    support_ids = V.utf8_sorted(support_ids)
                    label = copy.deepcopy(
                        self.unit.artifacts["a0_label"]
                    )
                    self._retarget_a0_label(
                        label, a0_input, event_index, support_ids
                    )
                    event_id = label["adjudicated_event_id"]
                    label_path = (
                        location_dir
                        / "events"
                        / event_id
                        / "a0_label.json"
                    )
                    container_events.append(
                        {
                            "adjudicated_event_id": event_id,
                            "a0_label_ref": V.artifact_ref(label),
                            "a0_label_relative_path": self._relative(
                                label_path
                            ),
                            "supporting_a0_raw_label_ids": support_ids,
                            "raw_support_adjudication": (
                                V.expected_raw_support_adjudication(
                                    label, support_raws
                                )
                            ),
                            "source_resolution": {
                                "status": "identified"
                            },
                        }
                    )
                    dispositions.extend(
                        {
                            "a0_raw_label_id": raw_id,
                            "disposition": "adjudicated_event",
                            "adjudicated_event_id": event_id,
                        }
                        for raw_id in support_ids
                    )
                    reveal = copy.deepcopy(
                        self.unit.artifacts["a1_reveal"]
                    )
                    reveal["artifact_id"] = "a1-reveal-event-%d" % event_index
                    reveal["unit_alias"] = self.unit_alias
                    reveal["a0_input_ref"] = V.artifact_ref(a0_input)
                    reveal["a0_label_ref"] = V.artifact_ref(label)
                    reveal["adjudicated_event_id"] = event_id
                    reveal["revealed_at"] = (
                        "2026-07-28T09:04:%02d+08:00"
                        % ((event_index - 1) * 10)
                    )
                    reveal["behavior_evidence"][
                        "after_observation_ordinal"
                    ] = 1
                    reveal["behavior_evidence"][
                        "action_ordinal"
                    ] = 2
                    a1_label = copy.deepcopy(
                        self.unit.artifacts["a1_label"]
                    )
                    a1_label["artifact_id"] = (
                        "a1-label-event-%d" % event_index
                    )
                    a1_label["unit_alias"] = self.unit_alias
                    a1_label["a0_input_ref"] = V.artifact_ref(a0_input)
                    a1_label["a0_label_ref"] = V.artifact_ref(label)
                    a1_label["a1_reveal_ref"] = V.artifact_ref(reveal)
                    a1_label["adjudicated_event_id"] = event_id
                    a1_label["annotator_alias"] = "annotator-a1"
                    a1_label["frozen_at"] = (
                        "2026-07-28T09:05:%02d+08:00"
                        % ((event_index - 1) * 10)
                    )
                    evidence = reveal["behavior_evidence"]
                    a1_label["affected_obligation_assessments"][0][
                        "evidence_pointer"
                    ] = {
                        "artifact_id": reveal["artifact_id"],
                        "observation_ordinal": 1,
                        "content_sha256": V.canonical_sha256(evidence),
                        "source_kind": "candidate_action",
                    }
                    reveal_path = (
                        location_dir
                        / "events"
                        / event_id
                        / "a1_reveal.json"
                    )
                    a1_label_path = (
                        location_dir
                        / "events"
                        / event_id
                        / "a1_label.json"
                    )
                    self.a1_artifacts.append(
                        {
                            "event_id": event_id,
                            "label": label,
                            "label_path": label_path,
                            "reveal": reveal,
                            "reveal_path": reveal_path,
                            "a1_label": a1_label,
                            "a1_label_path": a1_label_path,
                            "unit_alias": self.unit_alias,
                            "boundary_location_id": prefix[
                                "boundary_location_id"
                            ],
                        }
                    )
                    all_event_count += 1
            adjudication = {
                "artifact_type": "block_a0_adjudication",
                "schema_version": V.SCHEMA_VERSION,
                "canonicalization": V.CANONICALIZATION,
                "artifact_id": "a0-adjudication-%d" % ordinal,
                "unit_alias": self.unit_alias,
                "boundary_location_id": prefix["boundary_location_id"],
                "a0_input_ref": V.artifact_ref(a0_input),
                "a0_submissions_ref": V.artifact_ref(raw_submissions),
                "raw_label_dispositions": dispositions,
                "events": container_events,
                "adjudicator_alias": "adjudicator-a0",
                "frozen_at": "2026-07-28T09:02:10+08:00",
            }
            submissions_path = location_dir / "a0_submissions.json"
            adjudication_path = location_dir / "a0_adjudication.json"
            locations.append(
                {
                    "unit_alias": self.unit_alias,
                    "boundary_location_id": prefix["boundary_location_id"],
                    "a0_input_ref": V.artifact_ref(a0_input),
                    "a0_input_relative_path": self._relative(
                        a0_input_path
                    ),
                    "a0_submissions_ref": V.artifact_ref(
                        raw_submissions
                    ),
                    "a0_submissions_relative_path": self._relative(
                        submissions_path
                    ),
                    "a0_adjudication_container_ref": V.artifact_ref(
                        adjudication
                    ),
                    "a0_adjudication_container_relative_path": self._relative(
                        adjudication_path
                    ),
                }
            )
            event_freezes = [
                {
                    "adjudicated_event_id": item[
                        "adjudicated_event_id"
                    ],
                    "supporting_a0_raw_label_ids": item[
                        "supporting_a0_raw_label_ids"
                    ],
                    "frozen_at": next(
                        artifact["label"]["frozen_at"]
                        for artifact in self.a1_artifacts
                        if artifact["event_id"]
                        == item["adjudicated_event_id"]
                    ),
                }
                for item in container_events
            ]
            raw_ids = V.utf8_sorted(
                raw["a0_raw_label_id"]
                for submission in raw_submissions["submissions"]
                for raw in submission["raw_labels"]
            )
            location_freezes.append(
                {
                    "unit_alias": self.unit_alias,
                    "boundary_location_id": prefix["boundary_location_id"],
                    "a0_input_ref": V.artifact_ref(a0_input),
                    "a0_submissions_ref": V.artifact_ref(
                        raw_submissions
                    ),
                    "a0_raw_label_ids": raw_ids,
                    "a0_adjudication_container_ref": V.artifact_ref(
                        adjudication
                    ),
                    "adjudicated_events": event_freezes,
                    "prefix_chain_tip_sha256": a0_input[
                        "prefix_chain_tip_sha256"
                    ],
                    "a0_submissions_frozen_at": raw_submissions[
                        "frozen_at"
                    ],
                    "a0_adjudication_frozen_at": adjudication[
                        "frozen_at"
                    ],
                }
            )
            self.location_artifacts.append(
                {
                    "a0_input": a0_input,
                    "a0_input_path": a0_input_path,
                    "submissions": raw_submissions,
                    "submissions_path": submissions_path,
                    "adjudication": adjudication,
                    "adjudication_path": adjudication_path,
                }
            )

        manifest = {
            "artifact_type": "block_location_manifest",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "block-location-manifest-001",
            "block_id": self.block_id,
            "block_scope": "synthetic_test_only",
            "block_frame_ref": V.artifact_ref(frame),
            "unit_scans": [
                {
                    "unit_alias": self.unit_alias,
                    "scan_complete": True,
                    "observation_count": 3,
                    "prefix_commit_log_relative_path": self._relative(
                        prefix_path
                    ),
                    "prefix_commit_log_sha256": V.canonical_sha256(
                        prefix_entries
                    ),
                    "prefix_chain_tip_sha256": prefix_entries[-1][
                        "entry_sha256"
                    ],
                    "stream_ledger_ref": V.artifact_ref(stream),
                    "stream_ledger_relative_path": self._relative(
                        stream_path
                    ),
                    "ordinal_roster": [0, 1, 2],
                    "ordinal_boundary_location_ids": [
                        item["boundary_location_id"]
                        for item in prefix_entries
                    ],
                }
            ],
            "locations": locations,
            "frozen_at": "2026-07-28T09:01:05+08:00",
        }
        self.fixed["block_location_manifest"] = manifest
        registry = {
            "a0_annotator_aliases": [
                "annotator-a0",
                "annotator-a0b",
            ],
            "a0_adjudicator_aliases": ["adjudicator-a0"],
            "a1_annotator_aliases": ["annotator-a1"],
            "stage_b_annotator_aliases": ["annotator-stage-b"],
            "coordinator_aliases": ["coordinator-main"],
            "candidate_generator_aliases": [
                "generator-a",
                "generator-b",
                "generator-synthetic",
            ],
            "reference_aliases": ["reference-a"],
            "separation_is_permanent": True,
        }
        role_history = {
            "artifact_type": "role_history",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "role-history-001",
            "history_source_ref": {
                "artifact_id": "project-role-ledger",
                "sha256": digest("role-ledger-source"),
            },
            "assignments": [
                {
                    "actor_alias": alias,
                    "role": role,
                    "first_block_id": self.block_id,
                    "effective_from": "2026-07-28T08:00:00+08:00",
                    "permanent": True,
                }
                for field, role in (
                    ("a0_annotator_aliases", "a0_annotator"),
                    ("a0_adjudicator_aliases", "a0_adjudicator"),
                    ("a1_annotator_aliases", "a1_annotator"),
                    (
                        "stage_b_annotator_aliases",
                        "stage_b_annotator",
                    ),
                    ("coordinator_aliases", "coordinator"),
                    (
                        "candidate_generator_aliases",
                        "candidate_generator",
                    ),
                    ("reference_aliases", "reference"),
                )
                for alias in registry[field]
            ],
            "complete_through": "2026-07-28T09:06:20+08:00",
            "frozen_at": "2026-07-28T08:58:00+08:00",
        }
        self.fixed["role_history"] = role_history
        a0_barrier = {
            "artifact_type": "block_a0_barrier",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "block-a0-barrier-001",
            "block_id": self.block_id,
            "block_scope": "synthetic_test_only",
            "block_frame_ref": V.artifact_ref(frame),
            "location_manifest_ref": V.artifact_ref(manifest),
            "expected_unit_scan_count": 1,
            "expected_location_count": 3,
            "expected_adjudicated_event_count": all_event_count,
            "location_freezes": location_freezes,
            "role_registry": registry,
            "role_history_ref": V.artifact_ref(role_history),
            "exposure_policy": {
                "classification": "coordinator_secret",
                "allowed_roles": ["coordinator"],
                "public_linkage": "content_hash_only",
            },
            "sealed_by": "coordinator-main",
            "sealed_at": "2026-07-28T09:03:00+08:00",
        }
        self.fixed["block_barrier"] = a0_barrier
        for artifact in self.a1_artifacts:
            artifact["reveal"][
                "block_barrier_commitment_sha256"
            ] = V.canonical_sha256(a0_barrier)
            artifact["a1_label"]["a1_reveal_ref"] = V.artifact_ref(
                artifact["reveal"]
            )
            action = stream_entries[1]["current_action"]
            all_a1_freezes.append(
                {
                    "unit_alias": self.unit_alias,
                    "boundary_location_id": artifact[
                        "boundary_location_id"
                    ],
                    "adjudicated_event_id": artifact["event_id"],
                    "a1_reveal_ref": V.artifact_ref(
                        artifact["reveal"]
                    ),
                    "a1_reveal_relative_path": self._relative(
                        artifact["reveal_path"]
                    ),
                    "a1_label_ref": V.artifact_ref(
                        artifact["a1_label"]
                    ),
                    "a1_label_relative_path": self._relative(
                        artifact["a1_label_path"]
                    ),
                    "reveal_atomicity": {
                        "trajectory_mode": "batch_tool_model_steps",
                        "action_unit": "batch_bundle",
                        "batch_bundle_id": "batch-bundle-one",
                        "bundle_first_action_ordinal": 2,
                        "bundle_last_action_ordinal": 3,
                        "stream_observation_ordinal": 1,
                        "stream_action_sha256": action[
                            "action_bytes_sha256"
                        ],
                        "entire_action_unit_revealed_at": artifact[
                            "reveal"
                        ]["revealed_at"],
                    },
                    "a1_label_frozen_at": artifact["a1_label"][
                        "frozen_at"
                    ],
                }
            )
        a1_barrier = {
            "artifact_type": "block_a1_barrier",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "block-a1-barrier-001",
            "block_id": self.block_id,
            "block_scope": "synthetic_test_only",
            "block_a0_barrier_ref": V.artifact_ref(a0_barrier),
            "location_manifest_ref": V.artifact_ref(manifest),
            "expected_adjudicated_event_count": all_event_count,
            "event_freezes": all_a1_freezes,
            "sealed_by": "coordinator-main",
            "sealed_at": "2026-07-28T09:05:30+08:00",
        }
        self.fixed["block_a1_barrier"] = a1_barrier
        self._build_exposure_and_gate()
        self.write()

    def _build_exposure_and_gate(self) -> None:
        frame = self.fixed["block_frame"]
        manifest = self.fixed["block_location_manifest"]
        a0_barrier = self.fixed["block_barrier"]
        a1_barrier = self.fixed["block_a1_barrier"]
        events: List[Dict[str, Any]] = []
        previous = None

        def add(
            event_type: str,
            occurred_at: str,
            actor_alias: str,
            actor_role: str,
            operation: str,
            recipients: List[str],
            visible: List[tuple],
        ) -> None:
            nonlocal previous
            event = {
                "artifact_type": "block_exposure_event",
                "schema_version": V.SCHEMA_VERSION,
                "canonicalization": V.CANONICALIZATION,
                "exposure_ledger_id": "block-exposure-log-001",
                "block_id": self.block_id,
                "sequence": len(events),
                "event_type": event_type,
                "occurred_at": occurred_at,
                "actor_alias": actor_alias,
                "actor_role": actor_role,
                "exposure_operation": operation,
                "recipient_aliases": recipients,
                "visible_artifacts": [
                    {
                        "artifact_class": artifact_class,
                        "artifact_ref": V.artifact_ref(artifact),
                    }
                    for artifact_class, artifact in visible
                ],
                "previous_entry_sha256": previous,
                "entry_sha256": digest("exposure-placeholder"),
            }
            event["entry_sha256"] = V.block_exposure_entry_sha256(
                event
            )
            previous = event["entry_sha256"]
            events.append(event)

        add(
            "block_frame_frozen",
            frame["frozen_at"],
            "coordinator-main",
            "coordinator",
            "freeze",
            [],
            [("block_frame", frame)],
        )
        add(
            "location_manifest_frozen",
            manifest["frozen_at"],
            "coordinator-main",
            "coordinator",
            "freeze",
            [],
            [("location_manifest", manifest)],
        )
        for item in self.location_artifacts:
            add(
                "a0_input_released",
                "2026-07-28T09:01:10+08:00",
                "coordinator-main",
                "coordinator",
                "deliver",
                ["annotator-a0", "annotator-a0b"],
                [("a0_input", item["a0_input"])],
            )
        for item in self.location_artifacts:
            add(
                "a0_raw_labels_frozen",
                item["submissions"]["frozen_at"],
                "annotator-a0",
                "a0_annotator",
                "freeze",
                [],
                [("a0_raw_labels", item["submissions"])],
            )
        for item in self.location_artifacts:
            visible = [("a0_adjudication", item["adjudication"])]
            visible.extend(
                ("a0_adjudication", artifact["label"])
                for artifact in self.a1_artifacts
                if artifact["boundary_location_id"]
                == item["a0_input"]["boundary_location_id"]
            )
            visible.extend(
                ("a0_adjudication", search["artifact"])
                for search in self.source_search_artifacts
                if search["artifact"]["boundary_location_id"]
                == item["a0_input"]["boundary_location_id"]
            )
            add(
                "a0_adjudication_frozen",
                item["adjudication"]["frozen_at"],
                "adjudicator-a0",
                "a0_adjudicator",
                "freeze",
                [],
                visible,
            )
        add(
            "block_a0_barrier_frozen",
            a0_barrier["sealed_at"],
            "coordinator-main",
            "coordinator",
            "freeze",
            [],
            [("block_a0_barrier", a0_barrier)],
        )
        for artifact in self.a1_artifacts:
            add(
                "a1_revealed",
                artifact["reveal"]["revealed_at"],
                "coordinator-main",
                "coordinator",
                "deliver",
                ["annotator-a1"],
                [("a1_reveal", artifact["reveal"])],
            )
        for artifact in self.a1_artifacts:
            add(
                "a1_label_frozen",
                artifact["a1_label"]["frozen_at"],
                "annotator-a1",
                "a1_annotator",
                "freeze",
                [],
                [("a1_label", artifact["a1_label"])],
            )
        add(
            "block_a1_barrier_frozen",
            a1_barrier["sealed_at"],
            "coordinator-main",
            "coordinator",
            "freeze",
            [],
            [("block_a1_barrier", a1_barrier)],
        )
        add(
            "stage_b_authorized",
            "2026-07-28T09:06:00+08:00",
            "coordinator-main",
            "coordinator",
            "authorize",
            [],
            [("block_a1_barrier", a1_barrier)],
        )
        stage_b_input = {
            "artifact_id": "stage-b-input-synthetic",
            "sha256": digest("stage-b-input"),
        }
        event = {
            "artifact_type": "block_exposure_event",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "exposure_ledger_id": "block-exposure-log-001",
            "block_id": self.block_id,
            "sequence": len(events),
            "event_type": "stage_b_input_released",
            "occurred_at": "2026-07-28T09:06:10+08:00",
            "actor_alias": "coordinator-main",
            "actor_role": "coordinator",
            "exposure_operation": "deliver",
            "recipient_aliases": ["annotator-stage-b"],
            "visible_artifacts": [
                {
                    "artifact_class": "stage_b_input",
                    "artifact_ref": stage_b_input,
                }
            ],
            "previous_entry_sha256": previous,
            "entry_sha256": digest("stage-b-exposure"),
        }
        event["entry_sha256"] = V.block_exposure_entry_sha256(event)
        events.append(event)
        self.exposure_events = events
        self.fixed["stage_b_gate"] = {
            "artifact_type": "stage_b_gate",
            "schema_version": V.SCHEMA_VERSION,
            "canonicalization": V.CANONICALIZATION,
            "artifact_id": "stage-b-gate-001",
            "block_id": self.block_id,
            "block_scope": "synthetic_test_only",
            "block_a1_barrier_ref": V.artifact_ref(a1_barrier),
            "exposure_ledger_id": "block-exposure-log-001",
            "exposure_ledger_complete": True,
            "exposure_event_count": len(events),
            "exposure_chain_tip_sha256": events[-1][
                "entry_sha256"
            ],
            "authorized_by": "coordinator-main",
            "authorized_at": "2026-07-28T09:06:00+08:00",
            "ledger_closed_at": "2026-07-28T09:06:20+08:00",
        }

    def rehash_exposure(self) -> None:
        previous = None
        for sequence, event in enumerate(self.exposure_events):
            event["sequence"] = sequence
            event["previous_entry_sha256"] = previous
            event["entry_sha256"] = V.block_exposure_entry_sha256(event)
            previous = event["entry_sha256"]
        gate = self.fixed["stage_b_gate"]
        gate["exposure_event_count"] = len(self.exposure_events)
        gate["exposure_chain_tip_sha256"] = previous

    def reconcile_event_raw_support(
        self,
        artifact: Dict[str, Any],
    ) -> None:
        """Re-sign one synthetic event after an intentional raw mutation."""

        old_event_id = artifact["event_id"]
        location = next(
            item
            for item in self.location_artifacts
            if item["a0_input"]["boundary_location_id"]
            == artifact["boundary_location_id"]
        )
        container_event = next(
            event
            for event in location["adjudication"]["events"]
            if event["adjudicated_event_id"] == old_event_id
        )
        old_support_ids = set(
            container_event["supporting_a0_raw_label_ids"]
        )
        id_map: Dict[str, str] = {}
        support_raws: List[Dict[str, Any]] = []
        submissions = location["submissions"]
        for submission in submissions["submissions"]:
            for raw in submission["raw_labels"]:
                old_raw_id = raw["a0_raw_label_id"]
                if old_raw_id not in old_support_ids:
                    continue
                new_raw_id = V.block_a0_raw_label_id(
                    self.unit_alias,
                    artifact["boundary_location_id"],
                    submissions["schema_bundle_sha256"],
                    submissions["codebook_sha256"],
                    submission["annotator_alias"],
                    raw["semantic_payload"],
                )
                raw["a0_raw_label_id"] = new_raw_id
                id_map[old_raw_id] = new_raw_id
                support_raws.append(raw)
        if set(id_map) != old_support_ids:
            raise AssertionError("event support roster is incomplete")
        support_ids = V.utf8_sorted(id_map.values())
        label = artifact["label"]
        label["supporting_a0_raw_label_ids"] = support_ids
        label["adjudicated_event_preimage"][
            "supporting_a0_raw_label_ids"
        ] = support_ids
        new_event_id = V.adjudicated_event_id(
            label["adjudicated_event_preimage"]
        )
        label["adjudicated_event_id"] = new_event_id
        container_event["adjudicated_event_id"] = new_event_id
        container_event["supporting_a0_raw_label_ids"] = support_ids
        container_event["raw_support_adjudication"] = (
            V.expected_raw_support_adjudication(label, support_raws)
        )
        for disposition in location["adjudication"][
            "raw_label_dispositions"
        ]:
            raw_id = disposition["a0_raw_label_id"]
            if raw_id in id_map:
                disposition["a0_raw_label_id"] = id_map[raw_id]
            if (
                disposition.get("adjudicated_event_id")
                == old_event_id
            ):
                disposition["adjudicated_event_id"] = new_event_id

        freeze = next(
            item
            for item in self.fixed["block_barrier"][
                "location_freezes"
            ]
            if item["boundary_location_id"]
            == artifact["boundary_location_id"]
        )
        freeze["a0_raw_label_ids"] = V.utf8_sorted(
            raw["a0_raw_label_id"]
            for submission in submissions["submissions"]
            for raw in submission["raw_labels"]
        )
        freeze_event = next(
            item
            for item in freeze["adjudicated_events"]
            if item["adjudicated_event_id"] == old_event_id
        )
        freeze_event["adjudicated_event_id"] = new_event_id
        freeze_event["supporting_a0_raw_label_ids"] = support_ids
        freeze_event["frozen_at"] = label["frozen_at"]
        a1_freeze = next(
            item
            for item in self.fixed["block_a1_barrier"][
                "event_freezes"
            ]
            if item["adjudicated_event_id"] == old_event_id
        )
        a1_freeze["adjudicated_event_id"] = new_event_id
        artifact["event_id"] = new_event_id
        artifact["reveal"]["adjudicated_event_id"] = new_event_id
        artifact["a1_label"]["adjudicated_event_id"] = new_event_id

    def mutate_event_raw_payloads(
        self,
        artifact: Dict[str, Any],
        mutator: Callable[[int, Dict[str, Any]], None],
    ) -> None:
        """Mutate every raw support for one event, then re-sign all links."""

        location = next(
            item
            for item in self.location_artifacts
            if item["a0_input"]["boundary_location_id"]
            == artifact["boundary_location_id"]
        )
        container_event = next(
            event
            for event in location["adjudication"]["events"]
            if event["adjudicated_event_id"] == artifact["event_id"]
        )
        support_ids = set(
            container_event["supporting_a0_raw_label_ids"]
        )
        mutated = 0
        for submission_index, submission in enumerate(
            location["submissions"]["submissions"]
        ):
            for raw in submission["raw_labels"]:
                if raw["a0_raw_label_id"] in support_ids:
                    mutator(
                        submission_index, raw["semantic_payload"]
                    )
                    mutated += 1
        if mutated != len(support_ids):
            raise AssertionError("event support mutation was incomplete")
        self.reconcile_event_raw_support(artifact)

    def set_event_raw_source_labels(
        self,
        artifact: Dict[str, Any],
        labels_by_submission: List[List[str]],
    ) -> None:
        if len(labels_by_submission) != 2:
            raise AssertionError("two source-label submissions required")

        def replace_sources(
            submission_index: int,
            payload: Dict[str, Any],
        ) -> None:
            payload["update_source_labels"] = copy.deepcopy(
                labels_by_submission[submission_index]
            )

        self.mutate_event_raw_payloads(artifact, replace_sources)

    def refresh_full_links(self) -> None:
        manifest = self.fixed["block_location_manifest"]
        barrier = self.fixed["block_barrier"]
        a1_barrier = self.fixed["block_a1_barrier"]
        a1_by_event = {
            item["event_id"]: item for item in self.a1_artifacts
        }
        location_by_key = {
            (
                item["a0_input"]["unit_alias"],
                item["a0_input"]["boundary_location_id"],
            ): item
            for item in self.location_artifacts
        }
        for item in self.location_artifacts:
            item["submissions"]["a0_input_ref"] = V.artifact_ref(
                item["a0_input"]
            )
            item["adjudication"]["a0_input_ref"] = V.artifact_ref(
                item["a0_input"]
            )
            item["adjudication"]["a0_submissions_ref"] = V.artifact_ref(
                item["submissions"]
            )
            for container_event in item["adjudication"]["events"]:
                artifact = a1_by_event[
                    container_event["adjudicated_event_id"]
                ]
                container_event["a0_label_ref"] = V.artifact_ref(
                    artifact["label"]
                )
        for location in manifest["locations"]:
            item = location_by_key[
                (location["unit_alias"], location["boundary_location_id"])
            ]
            location["a0_input_ref"] = V.artifact_ref(item["a0_input"])
            location["a0_submissions_ref"] = V.artifact_ref(
                item["submissions"]
            )
            location["a0_adjudication_container_ref"] = V.artifact_ref(
                item["adjudication"]
            )
        barrier["location_manifest_ref"] = V.artifact_ref(manifest)
        barrier["role_history_ref"] = V.artifact_ref(
            self.fixed["role_history"]
        )
        freeze_by_key = {
            (item["unit_alias"], item["boundary_location_id"]): item
            for item in barrier["location_freezes"]
        }
        for key, item in location_by_key.items():
            freeze = freeze_by_key[key]
            freeze["a0_input_ref"] = V.artifact_ref(item["a0_input"])
            freeze["a0_submissions_ref"] = V.artifact_ref(
                item["submissions"]
            )
            freeze["a0_adjudication_container_ref"] = V.artifact_ref(
                item["adjudication"]
            )
        barrier_hash = V.canonical_sha256(barrier)
        freeze_by_event = {
            item["adjudicated_event_id"]: item
            for item in a1_barrier["event_freezes"]
        }
        for artifact in self.a1_artifacts:
            artifact["reveal"]["a0_input_ref"] = V.artifact_ref(
                location_by_key[
                    (
                        artifact["unit_alias"],
                        artifact["boundary_location_id"],
                    )
                ]["a0_input"]
            )
            artifact["reveal"]["a0_label_ref"] = V.artifact_ref(
                artifact["label"]
            )
            artifact["reveal"][
                "block_barrier_commitment_sha256"
            ] = barrier_hash
            artifact["a1_label"]["a0_input_ref"] = artifact["reveal"][
                "a0_input_ref"
            ]
            artifact["a1_label"]["a0_label_ref"] = V.artifact_ref(
                artifact["label"]
            )
            artifact["a1_label"]["a1_reveal_ref"] = V.artifact_ref(
                artifact["reveal"]
            )
            freeze = freeze_by_event[artifact["event_id"]]
            freeze["a1_reveal_ref"] = V.artifact_ref(
                artifact["reveal"]
            )
            freeze["a1_label_ref"] = V.artifact_ref(
                artifact["a1_label"]
            )
        a1_barrier["block_a0_barrier_ref"] = V.artifact_ref(barrier)
        a1_barrier["location_manifest_ref"] = V.artifact_ref(manifest)
        self._build_exposure_and_gate()

    def write(self) -> None:
        fixed_paths = {
            "block_frame": V.BLOCK_FRAME_FILE,
            "block_location_manifest": V.BLOCK_LOCATION_MANIFEST_FILE,
            "block_barrier": V.BLOCK_BARRIER_FILE,
            "block_a1_barrier": V.BLOCK_A1_BARRIER_FILE,
            "stage_b_gate": V.STAGE_B_GATE_FILE,
            "role_history": V.ROLE_HISTORY_FILE,
        }
        for name, filename in fixed_paths.items():
            self._write_json(self.root / filename, self.fixed[name])
        for item in self.location_artifacts:
            self._write_json(item["a0_input_path"], item["a0_input"])
            self._write_json(
                item["submissions_path"], item["submissions"]
            )
            self._write_json(
                item["adjudication_path"], item["adjudication"]
            )
        for item in self.a1_artifacts:
            self._write_json(item["label_path"], item["label"])
            self._write_json(item["reveal_path"], item["reveal"])
            self._write_json(
                item["a1_label_path"], item["a1_label"]
            )
        for item in self.source_search_artifacts:
            self._write_json(item["path"], item["artifact"])
        (self.root / V.BLOCK_EXPOSURE_LOG_FILE).write_text(
            "".join(
                json.dumps(event, sort_keys=True, separators=(",", ":"))
                + "\n"
                for event in self.exposure_events
            ),
            encoding="utf-8",
        )

    def validate(self) -> Mapping[str, Any]:
        self.write()
        return V.validate_full_block(
            self.root, SCHEMA_DIR, self.frame_sha256
        )


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

    def full_block(self, event_count: int = 2) -> SyntheticFullBlock:
        temp = tempfile.TemporaryDirectory(prefix="stage0f-full-block-")
        self.addCleanup(temp.cleanup)
        return SyntheticFullBlock(Path(temp.name), event_count)

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
        self.assertEqual(result["errors"][0]["code"], "FULL_BLOCK_REQUIRED")

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
        self.assertEqual(result["errors"][0]["code"], "FULL_BLOCK_REQUIRED")

    def test_synthetic_full_block_two_event_mechanics_pass(self) -> None:
        block = self.full_block(2)
        result = block.validate()
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["scope"], "full_block")
        self.assertEqual(
            result["mechanical_claim"], "STRUCTURAL_VALIDATION_ONLY"
        )
        self.assertEqual(result["scientific_gate"], "NOT_EVALUATED")
        self.assertEqual(result["claim_ceiling"], "NO_BLOCK_A")
        self.assertEqual(
            result["production_authority"],
            "UNAVAILABLE_FAIL_CLOSED",
        )
        self.assertEqual(
            result["identity_independence"], "ALIAS_LEVEL_ONLY"
        )
        self.assertEqual(
            set(result["derived_source_categories"].values()),
            {"PURE_WORLD"},
        )
        self.assertEqual(
            result["authority_roots"]["block_frame"]["artifact_ref"][
                "sha256"
            ],
            result["frame_sha256"],
        )
        self.assertEqual(
            len(result["canonical_adjudicated_events"]), 2
        )
        self.assertEqual(
            len(
                {
                    item["event_key_sha256"]
                    for item in result[
                        "canonical_adjudicated_events"
                    ]
                }
            ),
            2,
        )
        for item in result["canonical_adjudicated_events"]:
            self.assertEqual(
                item["event_key_preimage"],
                [
                    item["task_id"],
                    item["unit_alias"],
                    item["boundary_location_id"],
                    item["adjudicated_event_id"],
                ],
            )
            self.assertEqual(
                item["event_key_sha256"],
                V.canonical_sha256(
                    [
                        item["event_key_serialization"],
                        *item["event_key_preimage"],
                    ]
                ),
            )
            self.assertTrue(
                (block.root / item["a0_label_relative_path"]).is_file()
            )
            self.assertTrue(
                (block.root / item["a1_label_relative_path"]).is_file()
            )

    def test_e10_empty_submissions_no_event_location(self) -> None:
        block = self.full_block(0)
        result = block.validate()
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["derived_source_categories"], {})
        block.fixed["block_location_manifest"]["locations"].pop()
        block.write()
        result = block.validate()
        self.assertFalse(result["valid"], result)
        self.assertEqual(
            result["errors"][0]["code"], "SEM_EXACT_LOCATION_ROSTER"
        )

    def test_production_entry_ast_has_no_legacy_pass(self) -> None:
        tree = ast.parse(VALIDATOR_PATH.read_text(encoding="utf-8"))
        functions = [
            node for node in tree.body if isinstance(node, ast.FunctionDef)
        ]
        names = [node.name for node in functions]
        self.assertEqual(names.count("validate_task_bundle"), 1)
        self.assertEqual(names.count("validate_block_bundle"), 1)
        passing_entries = []
        for function in functions:
            if not function.name.startswith("validate"):
                continue
            for call in (
                node
                for node in ast.walk(function)
                if isinstance(node, ast.Call)
            ):
                if (
                    isinstance(call.func, ast.Name)
                    and call.func.id == "verdict"
                    and call.args
                    and isinstance(call.args[0], ast.Constant)
                    and call.args[0].value is True
                ):
                    passing_entries.append(function.name)
        self.assertEqual(passing_entries, ["validate_full_block"])

    def test_full_block_cli_matches_direct_api(self) -> None:
        block = self.full_block(2)
        direct = block.validate()
        completed = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR_PATH),
                str(block.root),
                "--schema-dir",
                str(SCHEMA_DIR),
                "--expected-frame-sha256",
                block.frame_sha256,
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        cli = json.loads(completed.stdout)
        self.assertEqual(cli["valid"], direct["valid"])
        self.assertEqual(cli["bundle_sha256"], direct["bundle_sha256"])

    def test_e01_single_unit_production(self) -> None:
        unit = self.unit()
        self.assert_case(
            "e01_single_unit_production",
            V.validate_bundle(unit.root, SCHEMA_DIR),
        )

    def test_e02_legacy_task_or_block(self) -> None:
        block = self.full_block(2)
        result = V.validate_task_bundle(block.root, SCHEMA_DIR)
        self.assert_case("e02_legacy_task_or_block", result)
        self.assertFalse(
            V.validate_block_bundle(block.root, SCHEMA_DIR)["valid"]
        )

    def test_e03_self_reported_block_a_frame(self) -> None:
        block = self.full_block(0)
        for name in (
            "block_frame",
            "block_location_manifest",
            "block_barrier",
            "block_a1_barrier",
            "stage_b_gate",
        ):
            block.fixed[name]["block_scope"] = "ontology_block_a"
        block.frame_sha256 = V.canonical_sha256(
            block.fixed["block_frame"]
        )
        block.write()
        self.assert_case(
            "e03_self_reported_block_a_frame", block.validate()
        )

    def test_e04_external_frame_mutated(self) -> None:
        block = self.full_block(0)
        block.fixed["block_frame"]["frame_source_ref"][
            "sha256"
        ] = digest("mutated-external-frame")
        block.write()
        self.assert_case("e04_external_frame_mutated", block.validate())

    def test_e05_ordinal_location_deleted(self) -> None:
        block = self.full_block(0)
        block.fixed["block_location_manifest"]["locations"].pop()
        block.write()
        self.assert_case(
            "e05_ordinal_location_deleted", block.validate()
        )

    def test_e06_location_duplicated(self) -> None:
        block = self.full_block(0)
        locations = block.fixed["block_location_manifest"]["locations"]
        locations[-1] = copy.deepcopy(locations[0])
        block.write()
        self.assert_case("e06_location_duplicated", block.validate())

    def test_e07_manifest_bytes_stale(self) -> None:
        block = self.full_block(0)
        block.fixed["block_location_manifest"][
            "frozen_at"
        ] = "2026-07-28T09:01:06+08:00"
        block.write()
        self.assert_case("e07_manifest_bytes_stale", block.validate())

    def test_raw_source_bytes_tamper(self) -> None:
        block = self.full_block(0)
        block.raw_source_path.write_bytes(
            block.raw_source_path.read_bytes() + b" "
        )
        self.assert_case("raw_source_bytes_tamper", block.validate())

    def test_raw_parser_executable_tamper(self) -> None:
        block = self.full_block(0)
        block.stream["raw_parser"]["executable_sha256"] = digest(
            "wrong-parser-executable"
        )
        self.assertNotEqual(
            block.stream["raw_parser"]["executable_sha256"],
            V.validator_file_sha256(),
        )
        block._write_json(block.stream_path, block.stream)
        scan = block.fixed["block_location_manifest"]["unit_scans"][0]
        scan["stream_ledger_ref"] = V.artifact_ref(block.stream)
        block.refresh_full_links()
        block.write()
        self.assert_case(
            "raw_parser_executable_tamper", block.validate()
        )

    def test_raw_parser_projection_tamper(self) -> None:
        block = self.full_block(0)
        tampered_hash = digest("tampered-subaction-projection")
        block.raw_trajectory["entries"][0]["current_action"][
            "subactions"
        ][0]["subaction_sha256"] = tampered_hash
        block.stream["entries"][0]["current_action"]["subactions"][0][
            "subaction_sha256"
        ] = tampered_hash
        block._write_json(
            block.raw_trajectory_path, block.raw_trajectory
        )
        block.stream["raw_trajectory_ref"] = V.artifact_ref(
            block.raw_trajectory
        )
        block._write_json(block.stream_path, block.stream)
        scan = block.fixed["block_location_manifest"]["unit_scans"][0]
        scan["stream_ledger_ref"] = V.artifact_ref(block.stream)
        block.refresh_full_links()
        block.write()
        self.assert_case(
            "raw_parser_projection_tamper", block.validate()
        )

    def test_raw_ordinal_roster_tamper(self) -> None:
        block = self.full_block(0)
        block.raw_trajectory["entries"].pop()
        block._write_json(
            block.raw_trajectory_path, block.raw_trajectory
        )
        block.stream["raw_trajectory_ref"] = V.artifact_ref(
            block.raw_trajectory
        )
        block._write_json(block.stream_path, block.stream)
        self.assert_case("raw_ordinal_roster_tamper", block.validate())

    def test_raw_observation_asset_unbound(self) -> None:
        block = self.full_block(0)
        block.coordinator["asset_manifest"][0][
            "asset_id"
        ] = "asset-replaced"
        block._write_json(
            block.component / "coordinator_envelope.json",
            block.coordinator,
        )
        self.assert_case(
            "raw_observation_asset_unbound", block.validate()
        )

    def test_production_external_authority_is_fail_closed(self) -> None:
        block = self.full_block(0)
        template = copy.deepcopy(
            block.fixed["block_frame"]["expected_units"][0]
        )
        block.fixed["block_frame"]["expected_units"] = [
            {
                **copy.deepcopy(template),
                "unit_alias": "U-%012X" % (task_index * 6 + config_index),
                "task_id": "%03d" % (35 + task_index),
                "hosted_config_id": "hosted-config-%d-%d"
                % (task_index, config_index),
            }
            for task_index in range(8)
            for config_index in range(6)
        ]
        block.fixed["block_frame"]["expected_unit_count"] = 48
        for name in (
            "block_frame",
            "block_location_manifest",
            "block_barrier",
            "block_a1_barrier",
            "stage_b_gate",
        ):
            block.fixed[name]["block_scope"] = "ontology_block_a"
        block.frame_sha256 = V.canonical_sha256(
            block.fixed["block_frame"]
        )
        block.write()
        self.assert_case(
            "production_external_authority_is_fail_closed",
            block.validate(),
        )

    def test_e08_same_a0_annotator(self) -> None:
        block = self.full_block(0)
        block.location_artifacts[0]["submissions"]["submissions"][1][
            "annotator_alias"
        ] = "annotator-a0"
        block.write()
        self.assert_case("e08_same_a0_annotator", block.validate())

    def test_e09_raw_id_duplicate(self) -> None:
        block = self.full_block(2)
        submissions = block.location_artifacts[1]["submissions"][
            "submissions"
        ]
        submissions[1]["raw_labels"][0]["a0_raw_label_id"] = submissions[
            0
        ]["raw_labels"][0]["a0_raw_label_id"]
        block.write()
        self.assert_case("e09_raw_id_duplicate", block.validate())

    def test_e11_same_location_event_missing_or_spliced(self) -> None:
        block = self.full_block(2)
        event_freezes = block.fixed["block_barrier"][
            "location_freezes"
        ][1]["adjudicated_events"]
        event_freezes.pop()
        block.write()
        self.assert_case(
            "e11_same_location_event_missing_or_spliced",
            block.validate(),
        )

        block = self.full_block(2)
        freezes = block.fixed["block_a1_barrier"]["event_freezes"]
        freezes[1]["a1_reveal_relative_path"] = freezes[0][
            "a1_reveal_relative_path"
        ]
        block.write()
        result = block.validate()
        self.assertFalse(result["valid"], result)

    def test_e12_commit_after_current_action(self) -> None:
        block = self.full_block(2)
        manifest = block.fixed["block_location_manifest"]
        scan = manifest["unit_scans"][0]
        prefix_path = block.root / scan[
            "prefix_commit_log_relative_path"
        ]
        prefixes = V.load_ndjson_no_duplicates(prefix_path)
        prefixes[1]["committed_at"] = "2026-07-28T09:00:26+08:00"
        prefixes[1]["entry_sha256"] = V.chained_entry_sha256(
            prefixes[1]
        )
        prefixes[2]["previous_entry_sha256"] = prefixes[1][
            "entry_sha256"
        ]
        prefixes[2]["entry_sha256"] = V.chained_entry_sha256(
            prefixes[2]
        )
        prefix_path.write_text(
            "".join(
                json.dumps(item, sort_keys=True, separators=(",", ":"))
                + "\n"
                for item in prefixes
            ),
            encoding="utf-8",
        )
        stream_path = block.root / scan["stream_ledger_relative_path"]
        stream = V.load_json_no_duplicates(stream_path)
        stream["entries"][1][
            "prefix_committed_at"
        ] = "2026-07-28T09:00:26+08:00"
        stream["entries"][1]["prefix_commit_entry_sha256"] = prefixes[1][
            "entry_sha256"
        ]
        stream["entries"][2]["prefix_commit_entry_sha256"] = prefixes[2][
            "entry_sha256"
        ]
        SyntheticFullBlock._write_json(stream_path, stream)
        scan["prefix_commit_log_sha256"] = V.canonical_sha256(prefixes)
        scan["prefix_chain_tip_sha256"] = prefixes[-1]["entry_sha256"]
        block.write()
        self.assert_case(
            "e12_commit_after_current_action", block.validate()
        )

    def test_e13_batch_subaction_before_commit(self) -> None:
        block = self.full_block(2)
        scan = block.fixed["block_location_manifest"]["unit_scans"][0]
        stream_path = block.root / scan["stream_ledger_relative_path"]
        stream = V.load_json_no_duplicates(stream_path)
        stream["entries"][1]["current_action"]["subactions"][0][
            "first_observable_at"
        ] = "2026-07-28T09:00:22+08:00"
        SyntheticFullBlock._write_json(stream_path, stream)
        self.assert_case(
            "e13_batch_subaction_before_commit", block.validate()
        )

    def test_e14_a1_before_full_a0_barrier(self) -> None:
        block = self.full_block(2)
        artifact = block.a1_artifacts[0]
        artifact["reveal"][
            "revealed_at"
        ] = "2026-07-28T09:02:50+08:00"
        block.fixed["block_a1_barrier"]["event_freezes"][0][
            "reveal_atomicity"
        ][
            "entire_action_unit_revealed_at"
        ] = "2026-07-28T09:02:50+08:00"
        block.refresh_full_links()
        block.write()
        self.assert_case(
            "e14_a1_before_full_a0_barrier", block.validate()
        )

    def test_e15_role_pool_overlap(self) -> None:
        block = self.full_block(0)
        block.fixed["block_barrier"]["role_registry"][
            "a1_annotator_aliases"
        ].append("annotator-a0")
        block.write()
        self.assert_case("e15_role_pool_overlap", block.validate())

    def test_e16_role_history_conflict(self) -> None:
        block = self.full_block(0)
        assignment = next(
            item
            for item in block.fixed["role_history"]["assignments"]
            if item["actor_alias"] == "annotator-a0"
        )
        assignment["role"] = "a1_annotator"
        block.write()
        self.assert_case("e16_role_history_conflict", block.validate())

    def test_x60_future_role_activation(self) -> None:
        block = self.full_block(2)
        assignment = next(
            item
            for item in block.fixed["role_history"]["assignments"]
            if item["actor_alias"] == "coordinator-main"
        )
        assignment["effective_from"] = (
            "2026-07-28T09:06:15+08:00"
        )
        block.refresh_full_links()
        block.write()
        self.assert_case(
            "x60_future_role_activation", block.validate()
        )

    def test_e30_empty_source_labels(self) -> None:
        block = self.full_block(2)
        block.a1_artifacts[0]["label"]["update_source_evidence"] = []
        block.write()
        self.assert_case("e30_empty_source_labels", block.validate())

    def test_e31_unknown_plus_factual(self) -> None:
        block = self.full_block(2)
        label = block.a1_artifacts[0]["label"]
        label["update_source_evidence"].append(
            {
                "label": "source_unidentifiable",
                "evidence_pointer": copy.deepcopy(
                    label["p_new"]["evidence_pointer"]
                ),
            }
        )
        block.refresh_full_links()
        block.write()
        self.assert_case("e31_unknown_plus_factual", block.validate())

    def test_e32_unknown_scope_hash_mismatch(self) -> None:
        block = self.full_block(2)
        artifact = block.a1_artifacts[0]
        label = artifact["label"]
        pointer = copy.deepcopy(label["p_new"]["evidence_pointer"])
        label["update_source_evidence"] = [
            {
                "label": "source_unidentifiable",
                "evidence_pointer": pointer,
            }
        ]
        label["primary_update_source"] = "source_unidentifiable"
        label["environment_primary_eligible"] = False
        block.set_event_raw_source_labels(
            artifact,
            [
                ["source_unidentifiable"],
                ["source_unidentifiable"],
            ],
        )
        block.attach_source_search_results(
            artifact,
            ["visible-observations", "task-schema"],
            searched_scope_sha256=digest("wrong-scope"),
        )
        block.refresh_full_links()
        block.write()
        self.assert_case(
            "e32_unknown_scope_hash_mismatch", block.validate()
        )

    def test_e33_factual_pointer_after_cutoff(self) -> None:
        block = self.full_block(2)
        label = block.a1_artifacts[0]["label"]
        label["update_source_evidence"][0]["evidence_pointer"][
            "observation_ordinal"
        ] = 2
        block.write()
        self.assert_case(
            "e33_factual_pointer_after_cutoff", block.validate()
        )

    def test_x58_raw_support_semantic_laundering(self) -> None:
        block = self.full_block(2)
        artifact = block.a1_artifacts[0]

        def replace_proposition(
            _submission_index: int,
            payload: Dict[str, Any],
        ) -> None:
            payload["p_new_proposition_id"] = (
                "PROP-UNRELATED-STATE"
            )

        block.mutate_event_raw_payloads(
            artifact, replace_proposition
        )
        block.refresh_full_links()
        block.write()
        self.assert_case(
            "x58_raw_support_semantic_laundering",
            block.validate(),
        )

    def test_x59_late_a0_label_freeze(self) -> None:
        block = self.full_block(2)
        artifact = block.a1_artifacts[0]
        artifact["label"]["frozen_at"] = (
            "2026-07-28T09:03:30+08:00"
        )
        freeze = next(
            item
            for location in block.fixed["block_barrier"][
                "location_freezes"
            ]
            for item in location["adjudicated_events"]
            if item["adjudicated_event_id"] == artifact["event_id"]
        )
        freeze["frozen_at"] = artifact["label"]["frozen_at"]
        block.refresh_full_links()
        block.write()
        self.assert_case(
            "x59_late_a0_label_freeze", block.validate()
        )

    def test_e34_world_and_task_goal_mixed(self) -> None:
        block = self.full_block(2)
        artifact = block.a1_artifacts[0]
        label = artifact["label"]
        label["update_source_evidence"].append(
            {
                "label": "task_goal_changed",
                "evidence_pointer": copy.deepcopy(
                    label["p_new"]["evidence_pointer"]
                ),
            }
        )
        label["environment_primary_eligible"] = False
        block.set_event_raw_source_labels(
            artifact,
            [
                ["world_truth_changed"],
                ["task_goal_changed"],
            ],
        )
        container = next(
            event
            for location in block.location_artifacts
            for event in location["adjudication"]["events"]
            if event["adjudicated_event_id"] == artifact["event_id"]
        )
        self.assertEqual(
            len(
                container["raw_support_adjudication"][
                    "disagreements"
                ]
            ),
            1,
        )
        block.refresh_full_links()
        block.write()
        result = block.validate()
        self.assertTrue(result["valid"], result)
        self.assertEqual(
            result["derived_source_categories"][artifact["event_id"]],
            "MIXED_WORLD",
        )

    def test_valid_source_unknown_full_block(self) -> None:
        block = self.full_block(2)
        artifact = block.a1_artifacts[0]
        label = artifact["label"]
        label["update_source_evidence"] = [
            {
                "label": "source_unidentifiable",
                "evidence_pointer": copy.deepcopy(
                    label["p_new"]["evidence_pointer"]
                ),
            }
        ]
        label["primary_update_source"] = "source_unidentifiable"
        label["environment_primary_eligible"] = False
        block.set_event_raw_source_labels(
            artifact,
            [
                ["source_unidentifiable"],
                ["source_unidentifiable"],
            ],
        )
        roster = ["visible-observations", "task-schema"]
        block.attach_source_search_results(artifact, roster)
        block.refresh_full_links()
        block.write()
        result = block.validate()
        self.assertTrue(result["valid"], result)
        self.assertEqual(
            result["derived_source_categories"][artifact["event_id"]],
            "SOURCE_UNKNOWN",
        )

    def test_source_unknown_search_result_stale(self) -> None:
        block = self.full_block(2)
        artifact = block.a1_artifacts[0]
        label = artifact["label"]
        label["update_source_evidence"] = [
            {
                "label": "source_unidentifiable",
                "evidence_pointer": copy.deepcopy(
                    label["p_new"]["evidence_pointer"]
                ),
            }
        ]
        label["primary_update_source"] = "source_unidentifiable"
        label["environment_primary_eligible"] = False
        block.set_event_raw_source_labels(
            artifact,
            [
                ["source_unidentifiable"],
                ["source_unidentifiable"],
            ],
        )
        block.attach_source_search_results(
            artifact, ["visible-observations", "task-schema"]
        )
        block.source_search_artifacts[0]["artifact"][
            "frozen_at"
        ] = "2026-07-28T09:01:54+08:00"
        block.refresh_full_links()
        block.write()
        self.assert_case(
            "source_unknown_search_result_stale", block.validate()
        )

    def test_block_a0_delivery_leak(self) -> None:
        block = self.full_block(2)
        event = next(
            item
            for item in block.exposure_events
            if item["event_type"] == "a0_input_released"
        )
        event["visible_artifacts"].append(
            {
                "artifact_class": "candidate_action",
                "artifact_ref": {
                    "artifact_id": "leaked-candidate-action",
                    "sha256": digest("leaked-action"),
                },
            }
        )
        block.rehash_exposure()
        block.write()
        self.assert_case("block_a0_delivery_leak", block.validate())

    def test_block_a0_access_leak(self) -> None:
        block = self.full_block(2)
        event = next(
            item
            for item in block.exposure_events
            if item["event_type"] == "a0_raw_labels_frozen"
        )
        event["exposure_operation"] = "access"
        event["visible_artifacts"].append(
            {
                "artifact_class": "a1_label",
                "artifact_ref": {
                    "artifact_id": "leaked-a1-label",
                    "sha256": digest("leaked-a1"),
                },
            }
        )
        block.rehash_exposure()
        block.write()
        self.assert_case("block_a0_access_leak", block.validate())

    def test_x51_wrong_role_delivery_laundering(self) -> None:
        block = self.full_block(2)
        for event in block.exposure_events:
            if event["event_type"] in {
                "a0_input_released",
                "a1_revealed",
            }:
                event["recipient_aliases"] = ["coordinator-main"]
        block.rehash_exposure()
        block.write()
        self.assert_case(
            "x51_wrong_role_delivery_laundering",
            block.validate(),
        )

    def test_x52_phase_artifact_swap(self) -> None:
        block = self.full_block(2)
        frame_event = next(
            event
            for event in block.exposure_events
            if event["event_type"] == "block_frame_frozen"
        )
        manifest_event = next(
            event
            for event in block.exposure_events
            if event["event_type"] == "location_manifest_frozen"
        )
        (
            frame_event["visible_artifacts"],
            manifest_event["visible_artifacts"],
        ) = (
            manifest_event["visible_artifacts"],
            frame_event["visible_artifacts"],
        )
        block.rehash_exposure()
        block.write()
        self.assert_case("x52_phase_artifact_swap", block.validate())

    def test_exposure_event_missing_contract(self) -> None:
        block = self.full_block(0)
        block.exposure_events = [
            event
            for event in block.exposure_events
            if event["event_type"] != "block_frame_frozen"
        ]
        block.rehash_exposure()
        block.write()
        self.assert_case(
            "exposure_event_missing_contract", block.validate()
        )

    def test_exposure_event_duplicate_contract(self) -> None:
        block = self.full_block(0)
        frame_event = next(
            event
            for event in block.exposure_events
            if event["event_type"] == "block_frame_frozen"
        )
        block.exposure_events.insert(1, copy.deepcopy(frame_event))
        block.rehash_exposure()
        block.write()
        self.assert_case(
            "exposure_event_duplicate_contract", block.validate()
        )

    def test_exposure_wrong_actor_contract(self) -> None:
        block = self.full_block(0)
        frame_event = next(
            event
            for event in block.exposure_events
            if event["event_type"] == "block_frame_frozen"
        )
        frame_event["actor_alias"] = "generator-a"
        frame_event["actor_role"] = "candidate_generator"
        block.rehash_exposure()
        block.write()
        self.assert_case(
            "exposure_wrong_actor_contract", block.validate()
        )

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
            "synthetic_full_block_two_event_mechanics_pass",
            "e10_empty_submissions_no_event_location",
            "e34_world_and_task_goal_mixed",
            "valid_source_unknown_full_block",
            "production_entry_ast_has_no_legacy_pass",
            "full_block_cli_matches_direct_api",
            "dependency_missing_has_no_fallback",
            "all_object_schemas_closed_and_meta_valid",
            "registry_coverage",
        }
        self.assertEqual(set(self.cases), methods - noncases)


if __name__ == "__main__":
    unittest.main()
