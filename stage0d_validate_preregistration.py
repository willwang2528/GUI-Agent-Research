#!/usr/bin/env python3
"""Validate the Stage 0D Task 3 revision-pilot analysis plan.

This script separates three claims:

1. the analysis plan is structurally coherent;
2. the execution manifest is fully frozen and runnable;
3. a Memory experiment is eligible.

The current protocol is intentionally ineligible for claim 3.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import pathlib
import sys
from types import ModuleType
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_PROTOCOL = ROOT / "stage0d_task3_preregistration.json"
UNRESOLVED = "UNRESOLVED"

EXPECTED_FORBIDDEN_CLAIMS = {
    "memory_causal",
    "natural_failure_root_cause",
    "planner_internal_mechanism",
    "long_horizon_end_to_end_improvement",
    "production_prevalence",
    "stale_memory_replacement_generalization",
}
EXPECTED_ARM_MATRIX = {
    "B": ("NONE", "NONE", "original_prompt_behavior"),
    "B_P0": (
        "NONE",
        "P0_ACTIVE_CONTROL",
        "generic_four_step_active_control_prompt_injection_effect",
    ),
    "U_REPEAT_P0": (
        "HISTORY_REPEAT",
        "P0_ACTIVE_CONTROL",
        "labeled_history_recap_and_salience_effect",
    ),
    "F_P0": (
        "FLAT_STATE",
        "P0_ACTIVE_CONTROL",
        "externally_supplied_canonical_state_context_effect",
    ),
    "S_P0": (
        "STRUCTURED_STATE",
        "P0_ACTIVE_CONTROL",
        "row_dsl_vs_json_serialization_effect",
    ),
    "F_P1": (
        "FLAT_STATE",
        "P1_TASK_VALUE_FREE",
        "task_value_free_update_repair_prompt_bundle_effect",
    ),
    "S_P1": (
        "STRUCTURED_STATE",
        "P1_TASK_VALUE_FREE",
        "serialization_by_update_repair_prompt_bundle_interaction",
    ),
}
EXPECTED_ESTIMANDS = {
    "active_control_prompt_injection": {"B_P0": 1, "B": -1},
    "labeled_history_recap": {"U_REPEAT_P0": 1, "B_P0": -1},
    "external_state_canonicalization": {"F_P0": 1, "U_REPEAT_P0": -1},
    "serialization": {"S_P0": 1, "F_P0": -1},
    "repair_prompt_flat": {"F_P1": 1, "F_P0": -1},
    "repair_prompt_structured": {"S_P1": 1, "S_P0": -1},
    "encoding_by_repair_interaction": {
        "S_P1": 1,
        "S_P0": -1,
        "F_P1": -1,
        "F_P0": 1,
    },
}
EXPECTED_ORACLES = {
    "E_STAR",
    "G_STAR",
    "R_STAR",
    "P_GENERIC",
    "P_ORACLE",
    "V_SELECT_STAR",
    "A_STAR",
}
REQUIRED_TASK3_BLOCKERS = {
    "renderer_hashes",
    "map_webarena",
    "baseline_trajectory_3_modification",
    "prefix_inclusion_and_equivalence",
    "frozen_model_and_seed_support",
    "token_and_deliberation_match",
    "deterministic_primary_evaluator",
    "manual_prompt_leakage_audit",
}
EXPECTED_ALL_BLOCKERS = REQUIRED_TASK3_BLOCKERS | {"cross_task_confirmatory_families"}
EXPECTED_RESEARCH_QUESTION = (
    "After an explicit two-value task revision and a verified pre-update route artifact, "
    "does a canonical state synthesis or a task-value-free repair prompt change "
    "contract-consistent completion under a frozen policy?"
)
EXPECTED_PRE_EXECUTION_CLAIM_CEILING = "prompt_context_pilot_design_only"
EXPECTED_INITIAL_INSTRUCTION = (
    "Compare the difference in time for walking and driving route from Phipps "
    "Conservatory to University of Pittsburgh"
)
EXPECTED_UPDATES = [
    "Correction: the starting point should be Randyland, not Phipps Conservatory",
    "And the destination is Carnegie Mellon University, not University of Pittsburgh",
]
EXPECTED_ATOMS = [
    {
        "id": "origin_old",
        "predicate": "task.origin",
        "value": "Phipps Conservatory",
        "status": "superseded",
        "source": "initial_instruction",
        "relation": {"superseded_by": "update_1"},
    },
    {
        "id": "origin_current",
        "predicate": "task.origin",
        "value": "Randyland",
        "status": "current",
        "source": "update_1",
        "relation": {"supersedes": "origin_old"},
    },
    {
        "id": "destination_old",
        "predicate": "task.destination",
        "value": "University of Pittsburgh",
        "status": "superseded",
        "source": "initial_instruction",
        "relation": {"superseded_by": "update_2"},
    },
    {
        "id": "destination_current",
        "predicate": "task.destination",
        "value": "Carnegie Mellon University",
        "status": "current",
        "source": "update_2",
        "relation": {"supersedes": "destination_old"},
    },
    {
        "id": "travel_modes",
        "predicate": "task.travel_modes",
        "value": ["walking", "driving"],
        "status": "current",
        "source": "initial_instruction",
        "relation": None,
    },
    {
        "id": "requested_output",
        "predicate": "task.requested_output",
        "value": "compare_route_times",
        "status": "current",
        "source": "initial_instruction",
        "relation": None,
    },
]
EXPECTED_PLANNING_LIBRARY = {
    "NONE": {
        "text": "",
        "claim_label": "no_additional_prompt",
    },
    "P0_ACTIVE_CONTROL": {
        "text": (
            "Follow four ordinary control steps. First, review the available instruction. "
            "Second, organize the visible interface information. Third, choose one allowed "
            "next action. Fourth, use the normal response format and continue without adding "
            "assumptions."
        ),
        "claim_label": "generic_four_step_active_control",
    },
    "P1_TASK_VALUE_FREE": {
        "text": (
            "Follow four update-repair steps. First, identify prior decisions or external "
            "artifacts invalidated by the update. Second, identify their dependent results. "
            "Third, undo or compensate affected state and recompute. Fourth, verify the current "
            "source before committing without inferring missing values."
        ),
        "claim_label": "task_value_free_repair_prompt",
    },
}
EXPECTED_ESTIMAND_METADATA = {
    "active_control_prompt_injection": (
        "nuisance_control",
        "generic_four_step_active_control_prompt_injection_effect",
    ),
    "labeled_history_recap": (
        "key_secondary",
        "labeled_history_recap_and_salience_effect",
    ),
    "external_state_canonicalization": (
        "primary",
        "externally_supplied_canonical_state_context_effect",
    ),
    "serialization": ("key_secondary", "row_dsl_vs_json_serialization_effect"),
    "repair_prompt_flat": (
        "key_secondary",
        "task_value_free_update_repair_prompt_bundle_effect",
    ),
    "repair_prompt_structured": (
        "key_secondary",
        "task_value_free_update_repair_prompt_bundle_effect",
    ),
    "encoding_by_repair_interaction": (
        "exploratory",
        "serialization_by_update_repair_prompt_bundle_interaction",
    ),
}
EXPECTED_PRIMARY_DEFINITION = (
    "Current origin and destination are reflected in final Map fields; a route computation "
    "occurs after their last repair; the final answer is derived from the post-update route "
    "artifact; no superseded origin or destination governs the final result."
)
EXPECTED_DECISION_RULES = {
    "memory_topic_status": "ineligible_not_tested",
    "external_state_canonicalization_progression_signal": {
        "estimand_id": "external_state_canonicalization",
        "outcome_id": "contract_consistent_completion",
        "minimum_effect_pp": 20,
        "allowed_label": "candidate_signal_on_this_frozen_task_prefix",
        "required_reporting": "paired_effect_exact_interval_and_all_discordant_pairs",
        "confirmatory_support_claim_allowed": False,
    },
    "repair_prompt_support": {
        "estimand_id": "repair_prompt_flat",
        "outcome_id": "contract_consistent_completion",
        "minimum_effect_pp": 20,
        "allowed_label": "candidate_task_value_free_update_repair_prompt_bundle_signal",
        "required_reporting": "paired_effect_exact_interval_and_all_discordant_pairs",
        "confirmatory_support_claim_allowed": False,
    },
    "root_cause_decision_allowed": False,
    "topic_rename_decision_allowed_from_task3_alone": False,
}


def reject_duplicate_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys instead of silently keeping the last value."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: pathlib.Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_object_pairs,
    )


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def verify_evidence_record(
    errors: list[str], blocker_id: str, record: Any
) -> bool:
    """Verify a resolved blocker is backed by a frozen local evidence artifact."""
    if not isinstance(record, dict):
        errors.append(f"resolved blocker lacks evidence record: {blocker_id}")
        return False
    path_value = record.get("path")
    expected_hash = record.get("sha256")
    if not isinstance(path_value, str) or not path_value:
        errors.append(f"evidence path missing: {blocker_id}")
        return False
    if not is_sha256(expected_hash):
        errors.append(f"evidence hash invalid: {blocker_id}")
        return False
    path = ROOT / path_value
    if not path.is_file():
        errors.append(f"evidence file missing: {blocker_id}: {path}")
        return False
    if sha256_file(path) != expected_hash:
        errors.append(f"evidence hash mismatch: {blocker_id}")
        return False
    try:
        payload = load_json(path)
    except (ValueError, json.JSONDecodeError) as exc:
        errors.append(f"evidence JSON invalid: {blocker_id}: {exc}")
        return False
    if not isinstance(payload, dict):
        errors.append(f"evidence payload must be an object: {blocker_id}")
        return False
    if (
        payload.get("blocker_id") != blocker_id
        or payload.get("protocol_version") != "0.3.0"
        or payload.get("status") != "passed"
        or not isinstance(payload.get("checks"), list)
        or not payload.get("checks")
    ):
        errors.append(f"evidence payload schema failed: {blocker_id}")
        return False
    return True


def validate_seed_map_payload(
    payload: Any,
    *,
    screening_seeds: list[int],
    confirmation_seeds: list[int],
    arm_ids: set[str],
) -> list[str]:
    """Validate complete paired-arm coverage and balanced Latin-cycle ordering."""
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["seed-map payload must be an object"]
    if payload.get("assignment_algorithm") != "balanced_latin_cycle_v1":
        failures.append("seed-map assignment algorithm changed")
    if not isinstance(payload.get("randomization_seed"), int):
        failures.append("seed-map randomization seed missing")
    base_order = payload.get("base_arm_order")
    if not isinstance(base_order, list) or len(base_order) != len(arm_ids) or set(base_order) != arm_ids:
        failures.append("seed-map base arm order is not a complete permutation")
        return failures

    combined_records: list[dict[str, Any]] = []
    for phase, expected_seeds in (
        ("screening", screening_seeds),
        ("confirmation", confirmation_seeds),
    ):
        records = payload.get(phase)
        if not isinstance(records, list):
            failures.append(f"seed-map {phase} records missing")
            continue
        if any(not isinstance(record, dict) for record in records):
            failures.append(f"seed-map {phase} record is not an object")
            continue
        seeds = [record.get("seed") for record in records]
        if seeds != expected_seeds or len(set(seeds)) != len(expected_seeds):
            failures.append(f"seed-map {phase} seeds are incomplete, reordered or duplicated")
        for record in records:
            order = record.get("arm_order")
            if not isinstance(order, list) or len(order) != len(arm_ids) or set(order) != arm_ids:
                failures.append(f"seed-map seed {record.get('seed')} lacks one complete arm permutation")
        combined_records.extend(records)

    if len(combined_records) == len(screening_seeds) + len(confirmation_seeds):
        for index, record in enumerate(combined_records):
            offset = index % len(base_order)
            expected_order = base_order[offset:] + base_order[:offset]
            if record.get("arm_order") != expected_order:
                failures.append(
                    f"seed-map seed {record.get('seed')} violates the balanced Latin cycle"
                )
    return failures


def verify_seed_map_record(
    errors: list[str],
    record: Any,
    *,
    screening_seeds: list[int],
    confirmation_seeds: list[int],
    arm_ids: set[str],
) -> bool:
    if not verify_evidence_record(errors, "seed_to_arm_mapping", record):
        return False
    path = ROOT / record["path"]
    payload = load_json(path)
    failures = validate_seed_map_payload(
        payload,
        screening_seeds=screening_seeds,
        confirmation_seeds=confirmation_seeds,
        arm_ids=arm_ids,
    )
    errors.extend(failures)
    return not failures


def load_renderer(path: pathlib.Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("stage0d_frozen_renderer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load renderer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def unique_ids(items: list[dict[str, Any]], label: str, errors: list[str]) -> list[str]:
    ids = [str(item.get("id", "")) for item in items]
    require(errors, all(ids), f"{label} contains a blank id")
    require(errors, len(ids) == len(set(ids)), f"{label} ids must be unique")
    return ids


def task_item(items: list[dict[str, Any]], task_id: int) -> dict[str, Any] | None:
    return next((item for item in items if item.get("task_id") == task_id), None)


def generated_leakage_lexicon(atoms: list[dict[str, Any]]) -> set[str]:
    lexicon = {
        "origin",
        "starting point",
        "start location",
        "destination",
        "route",
        "map",
        "directions",
        "from field",
        "to field",
        "recalculate directions",
    }
    for atom in atoms:
        value = atom.get("value")
        values = value if isinstance(value, list) else [value]
        lexicon.update(str(item).lower().replace("_", " ") for item in values)
        lexicon.update(str(atom.get("predicate", "")).lower().split("."))
    lexicon.discard("task")
    return {item for item in lexicon if item}


def render_inputs(
    protocol: dict[str, Any], renderer: ModuleType
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    diagnostic = protocol["diagnostic_variant"]
    atoms = protocol["semantic_atoms"]
    state_texts = {
        "NONE": "",
        "HISTORY_REPEAT": renderer.render_history_repeat(
            diagnostic["initial_instruction"], diagnostic["updates"]
        ),
        "FLAT_STATE": renderer.render_flat(atoms),
        "STRUCTURED_STATE": renderer.render_structured(atoms),
    }
    planning_texts = {
        key: item["text"] for key, item in protocol["planning_library"].items()
    }
    state_first = protocol["renderer"].get("order") == [
        "state_input",
        "planning_input",
    ]
    arm_texts: dict[str, str] = {}
    for arm in protocol["arms"]:
        state_id = arm["state_input_id"]
        planning_id = arm["planning_input_id"]
        arm_texts[arm["id"]] = renderer.render_arm(
            state_text=state_texts[state_id],
            planning_text=planning_texts[planning_id],
            delimiter=protocol["renderer"]["delimiter"],
            state_first=state_first,
        )
    return state_texts, planning_texts, arm_texts


def validate(protocol: dict[str, Any], *, verify_assets: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    require(errors, protocol.get("protocol_version") == "0.3.0", "wrong protocol version")
    require(
        errors,
        protocol.get("analysis_plan_status") == "frozen",
        "analysis plan must be frozen",
    )
    require(
        errors,
        protocol.get("execution_manifest_status") in {"pending", "frozen"},
        "execution manifest status must be pending or frozen",
    )
    require(
        errors,
        protocol.get("research_question") == EXPECTED_RESEARCH_QUESTION,
        "research question changed or exceeds the frozen prompt-pilot scope",
    )
    require(
        errors,
        protocol.get("pre_execution_claim_ceiling")
        == EXPECTED_PRE_EXECUTION_CLAIM_CEILING,
        "pre-execution claim ceiling changed",
    )
    require(
        errors,
        set(protocol.get("forbidden_claims_before_cross_task_execution", []))
        == EXPECTED_FORBIDDEN_CLAIMS,
        "forbidden pre-cross-task claims must match the complete frozen set",
    )
    require(
        errors,
        protocol.get("experiment_class") == "single_task_causal_prompt_diagnostic_pilot",
        "Task 3 must remain labeled as a single-task causal prompt diagnostic pilot",
    )

    anchor = protocol.get("case_anchor_not_experimental", {})
    require(errors, anchor.get("variant") == "1update", "case anchor must be 1update")
    require(
        errors,
        "supersession_handling" in anchor.get("forbidden_claims", []),
        "addition anchor must forbid supersession claims",
    )

    diagnostic = protocol.get("diagnostic_variant", {})
    semantics = diagnostic.get("update_semantics", {})
    require(errors, diagnostic.get("name") == "2modification", "diagnostic must use 2modification")
    require(errors, diagnostic.get("task_id") == 3, "diagnostic task id must be 3")
    require(
        errors,
        diagnostic.get("initial_instruction") == EXPECTED_INITIAL_INSTRUCTION
        and diagnostic.get("updates") == EXPECTED_UPDATES,
        "diagnostic instruction or revision text changed",
    )
    require(
        errors,
        semantics.get("type") == "two_value_revision"
        and semantics.get("creates_supersession") is True
        and semantics.get("old_values_explicit") is True
        and semantics.get("new_values_explicit") is True
        and semantics.get("requires_pre_update_artifact_for_inclusion") is True,
        "diagnostic semantics must require explicit supersession and a pre-update artifact",
    )
    require(
        errors,
        diagnostic.get("strict_checkpoint_equivalence_claimed") is False,
        "action-prefix replay must not claim strict checkpoint equivalence",
    )

    asset_keys = ("base_task", "transformed_task", "raw_update", "interrupt_spec")
    if verify_assets:
        for key in asset_keys:
            record = diagnostic.get(key, {})
            path = ROOT / str(record.get("path", ""))
            require(errors, path.is_file(), f"missing asset {key}: {path}")
            if path.is_file():
                require(
                    errors,
                    sha256_file(path) == record.get("sha256"),
                    f"asset hash mismatch: {key}",
                )

        raw_path = ROOT / str(diagnostic.get("raw_update", {}).get("path", ""))
        spec_path = ROOT / str(diagnostic.get("interrupt_spec", {}).get("path", ""))
        transformed_path = ROOT / str(diagnostic.get("transformed_task", {}).get("path", ""))
        if raw_path.is_file() and spec_path.is_file() and transformed_path.is_file():
            raw = load_json(raw_path)
            spec = load_json(spec_path)
            transformed = load_json(transformed_path)
            require(errors, len(raw) == 165, "raw revision file must contain 165 tasks")
            require(
                errors,
                {item.get("task_id") for item in raw} == set(range(165)),
                "raw revision task ids must cover 0 through 164",
            )
            raw3 = task_item(raw, 3)
            spec3 = spec.get("tasks", {}).get("3")
            require(errors, raw3 is not None and spec3 is not None, "task 3 raw/spec entry missing")
            if raw3 and spec3:
                require(
                    errors,
                    raw3.get("transformed_initial_intent") == diagnostic.get("initial_instruction")
                    == transformed.get("intent"),
                    "diagnostic initial instruction differs across raw/config/manifest",
                )
                require(
                    errors,
                    raw3.get("updates") == diagnostic.get("updates"),
                    "diagnostic updates differ from official raw data",
                )
                require(
                    errors,
                    spec3.get("update_intent") == "\n".join(diagnostic.get("updates", [])),
                    "interrupt spec update differs from official raw updates",
                )
                require(
                    errors,
                    spec3.get("interrupt_at_pct") == "60%"
                    and spec3.get("update_mode") == "append"
                    and spec3.get("extra_steps") == 0,
                    "task 3 diagnostic interrupt parameters changed",
                )

    prefix = protocol.get("prefix_eligibility_before_raw_update", {})
    required_pre_update_prefix = {
        "old_origin_entered_or_used_in_route_query",
        "old_destination_entered_or_used_in_route_query",
        "route_artifact_computed_from_old_values",
        "no_stop_or_termination_before_k",
        "same_page_url_after_replay",
        "same_normalized_accessibility_tree_hash_after_replay",
        "same_task_relevant_field_values_after_replay",
        "same_prefix_action_hash",
    }
    require(
        errors,
        prefix.get("evaluated_before_update_and_before_arm_assignment") is True
        and set(prefix.get("all_required", [])) == required_pre_update_prefix
        and prefix.get("post_treatment_variables_may_filter_population") is False,
        "pre-treatment prefix inclusion rule is incomplete or post-treatment dependent",
    )
    checkpoint = protocol.get("common_post_update_pre_assignment_artifact_checkpoint", {})
    require(
        errors,
        checkpoint.get("evaluated_after_raw_update_before_arm_assignment") is True
        and checkpoint.get("all_required")
        == ["old_route_artifact_persists_after_raw_update_before_arm_injection"]
        and checkpoint.get("arm_dependent_selection") is False,
        "common post-update artifact checkpoint is missing or arm dependent",
    )
    expected_fingerprint_schema = {
        "required_fields": [
            "from_field_normalized_value",
            "to_field_normalized_value",
            "route_result_dom_sha256",
            "route_mode",
            "route_computation_action_index",
            "old_route_artifact_id",
        ],
        "dependency_edges": [
            "old_route_artifact<-origin_old",
            "old_route_artifact<-destination_old",
        ],
        "measurement_time": "after_raw_update_before_arm_assignment",
    }
    require(
        errors,
        checkpoint.get("artifact_fingerprint_schema") == expected_fingerprint_schema,
        "old-route artifact fingerprint schema changed",
    )
    expected_assignment_core = {
        "assignment_time": "after_both_common_eligibility_gates_pass",
        "fresh_agent_browser_session_per_arm": True,
        "same_verified_prefix_replayed_per_arm": True,
        "cross_arm_cache_or_store_reuse": False,
        "arm_order": "randomized_or_counterbalanced_from_frozen_seed_to_arm_map",
    }
    assignment = protocol.get("assignment_and_isolation", {})
    require(
        errors,
        {key: assignment.get(key) for key in expected_assignment_core}
        == expected_assignment_core
        and set(assignment)
        == set(expected_assignment_core) | {"seed_to_arm_mapping_artifact"},
        "arm assignment, session isolation or seed-map plan changed",
    )
    window = protocol.get("analysis_window", {})
    require(
        errors,
        window.get("end")
        == "task_termination_or_10_post_update_agent_decisions_whichever_occurs_first",
        "analysis window must avoid first-commit differential censoring",
    )

    atoms = protocol.get("semantic_atoms", [])
    atom_ids = unique_ids(atoms, "semantic atoms", errors)
    require(errors, len(atoms) == 6, "diagnostic state must contain six frozen atoms")
    require(
        errors,
        atoms == EXPECTED_ATOMS,
        "semantic atoms do not exactly match the official Task 3 revision contract",
    )
    for atom in atoms:
        require(
            errors,
            set(atom) == {"id", "predicate", "value", "status", "source", "relation"},
            f"atom {atom.get('id')} has an invalid schema",
        )
    current = [atom for atom in atoms if atom.get("status") == "current"]
    superseded = [atom for atom in atoms if atom.get("status") == "superseded"]
    require(errors, len(current) == 4 and len(superseded) == 2, "current/superseded atom counts changed")
    require(
        errors,
        {atom.get("predicate") for atom in superseded}
        == {"task.origin", "task.destination"},
        "revision must supersede both origin and destination",
    )
    for old in superseded:
        relation = old.get("relation") or {}
        require(errors, "superseded_by" in relation, f"{old.get('id')} lacks superseded_by")
    for new in [atom for atom in current if atom.get("predicate") in {"task.origin", "task.destination"}]:
        relation = new.get("relation") or {}
        require(
            errors,
            relation.get("supersedes") in atom_ids,
            f"{new.get('id')} does not bind to a frozen old atom",
        )

    renderer_manifest = protocol.get("renderer", {})
    renderer_path = ROOT / str(renderer_manifest.get("implementation_path", ""))
    require(errors, renderer_path.is_file(), "renderer implementation is missing")
    renderer: ModuleType | None = None
    if renderer_path.is_file():
        require(
            errors,
            sha256_file(renderer_path) == renderer_manifest.get("implementation_sha256"),
            "renderer implementation hash changed",
        )
        renderer = load_renderer(renderer_path)
        require(
            errors,
            getattr(renderer, "RENDERER_VERSION", None) == renderer_manifest.get("version"),
            "renderer version changed",
        )
    require(
        errors,
        renderer_manifest.get("message_role") == "user"
        and renderer_manifest.get("insertion_point")
        == "immediately_after_raw_update_before_first_post_update_model_call"
        and renderer_manifest.get("frequency") == "once"
        and renderer_manifest.get("order") == ["state_input", "planning_input"],
        "prompt render role, position, frequency or order changed",
    )

    states = protocol.get("input_library", {})
    plans = protocol.get("planning_library", {})
    require(
        errors,
        set(states) == {"NONE", "HISTORY_REPEAT", "FLAT_STATE", "STRUCTURED_STATE"},
        "state input library changed",
    )
    require(
        errors,
        set(plans) == {"NONE", "P0_ACTIVE_CONTROL", "P1_TASK_VALUE_FREE"},
        "planning input library changed",
    )
    for plan_id, expected in EXPECTED_PLANNING_LIBRARY.items():
        require(
            errors,
            plans.get(plan_id, {}).get("text") == expected["text"]
            and plans.get(plan_id, {}).get("claim_label") == expected["claim_label"],
            f"planning prompt or claim label changed: {plan_id}",
        )
    full_atom_ids = atom_ids
    for state_id in ("HISTORY_REPEAT", "FLAT_STATE", "STRUCTURED_STATE"):
        require(
            errors,
            states.get(state_id, {}).get("semantic_atom_ids") == full_atom_ids,
            f"{state_id} must contain the complete ordered atom set",
        )

    arm_ids = unique_ids(protocol.get("arms", []), "arms", errors)
    require(errors, set(arm_ids) == set(EXPECTED_ARM_MATRIX), "arm ids changed")
    arms_by_id = {arm["id"]: arm for arm in protocol.get("arms", []) if arm.get("id")}
    for arm_id, expected in EXPECTED_ARM_MATRIX.items():
        arm = arms_by_id.get(arm_id, {})
        actual = (
            arm.get("state_input_id"),
            arm.get("planning_input_id"),
            arm.get("claim_ceiling"),
        )
        require(errors, actual == expected, f"arm mapping changed: {arm_id}")
        require(errors, actual[0] in states, f"arm {arm_id} references undefined state input")
        require(errors, actual[1] in plans, f"arm {arm_id} references undefined planning input")

    if renderer is not None and set(arm_ids) == set(EXPECTED_ARM_MATRIX):
        try:
            rendered_states, rendered_plans, rendered_arms = render_inputs(protocol, renderer)
        except Exception as exc:
            errors.append(f"rendering failed: {type(exc).__name__}: {exc}")
        else:
            for state_id, text in rendered_states.items():
                require(
                    errors,
                    renderer.text_sha256(text) == states[state_id].get("rendered_sha256"),
                    f"frozen state rendering changed: {state_id}",
                )
            for plan_id, text in rendered_plans.items():
                require(
                    errors,
                    renderer.text_sha256(text) == plans[plan_id].get("rendered_sha256"),
                    f"frozen planning rendering changed: {plan_id}",
                )
            for arm_id, text in rendered_arms.items():
                require(
                    errors,
                    renderer.text_sha256(text) == arms_by_id[arm_id].get("rendered_sha256"),
                    f"frozen arm rendering changed: {arm_id}",
                )

    p1 = plans.get("P1_TASK_VALUE_FREE", {})
    p1_text = str(p1.get("text", "")).lower()
    leaked = sorted(term for term in generated_leakage_lexicon(atoms) if term in p1_text)
    require(errors, not leaked, f"P1 contains task-specific terms: {leaked}")
    require(
        errors,
        p1.get("claim_label") == "task_value_free_repair_prompt",
        "Task 3 P1 must not be labeled generic planning",
    )

    estimands = protocol.get("estimands", [])
    estimand_ids = unique_ids(estimands, "estimands", errors)
    require(errors, set(estimand_ids) == set(EXPECTED_ESTIMANDS), "estimand ids changed")
    primary_estimands = [item for item in estimands if item.get("role") == "primary"]
    require(
        errors,
        [item.get("id") for item in primary_estimands]
        == ["external_state_canonicalization"],
        "there must be one frozen primary estimand: external_state_canonicalization",
    )
    for item in estimands:
        terms = item.get("terms", [])
        term_ids = unique_ids(
            [{"id": term.get("arm_id")} for term in terms],
            f"estimand {item.get('id')} terms",
            errors,
        )
        coefficients = {term.get("arm_id"): term.get("coefficient") for term in terms}
        require(
            errors,
            coefficients == EXPECTED_ESTIMANDS.get(item.get("id")),
            f"estimand algebra changed: {item.get('id')}",
        )
        require(errors, set(term_ids).issubset(set(arm_ids)), f"estimand {item.get('id')} references unknown arm")
        require(
            errors,
            all(isinstance(value, (int, float)) for value in coefficients.values())
            and sum(coefficients.values()) == 0,
            f"estimand {item.get('id')} coefficients are invalid",
        )
        require(
            errors,
            item.get("outcome_id") == "contract_consistent_completion"
            and item.get("scale") == "risk_difference_pp"
            and item.get("population") == "prefix_inclusion_passed_runs"
            and item.get("window") == "frozen_analysis_window",
            f"estimand scope changed: {item.get('id')}",
        )
        expected_metadata = EXPECTED_ESTIMAND_METADATA.get(item.get("id"))
        require(
            errors,
            expected_metadata is not None
            and (item.get("role"), item.get("causal_label")) == expected_metadata,
            f"estimand role or causal label changed: {item.get('id')}",
        )

    outcomes = protocol.get("outcomes", {})
    primary = outcomes.get("unique_primary", {})
    require(
        errors,
        primary.get("id") == "contract_consistent_completion"
        and primary.get("type") == "binary"
        and primary.get("definition") == EXPECTED_PRIMARY_DEFINITION
        and primary.get("evaluator_scope") == "normalized_trace_decision_logic_only"
        and primary.get("measurement_source")
        == "full_html_trace_plus_action_log_plus_final_answer"
        and primary.get("missing_policy") == "failure_if_trace_missing_after_valid_prefix",
        "unique primary outcome changed",
    )
    require(
        errors,
        primary.get("blind_to_arm") is True
        and primary.get("may_condition_primary_analysis") is False
        and outcomes.get("post_treatment_variables_may_filter_or_adjust_primary") is False
        and outcomes.get("formal_mediation_claim_allowed") is False,
        "post-treatment outcomes may not filter, adjust or mediate the primary analysis",
    )

    stats = protocol.get("statistics", {})
    screening = stats.get("screening_seeds", [])
    confirmation = stats.get("confirmation_seeds", [])
    require(
        errors,
        len(screening) == 5
        and len(confirmation) == 10
        and not set(screening).intersection(confirmation)
        and stats.get("seed_sets_overlap") is False,
        "screening and confirmation seeds must be disjoint and frozen",
    )
    require(errors, stats.get("screening_candidate_arm") == "F_P0", "screening candidate arm changed")
    require(
        errors,
        stats.get("primary_estimand_id") == "external_state_canonicalization",
        "primary estimand changed",
    )
    require(
        errors,
        stats.get("confirmation_test") == "two_sided_exact_mcnemar"
        and stats.get("alpha") == 0.05
        and stats.get("multiplicity") == "holm_for_primary_and_key_secondary_estimands",
        "test, alpha or multiplicity rule changed",
    )
    require(
        errors,
        stats.get("single_task_generalization_claim_allowed") is False
        and stats.get("power_claim_allowed_at_n10") is False
        and stats.get("equivalence_claim_allowed_at_n10") is False
        and stats.get("negative_transfer_claim_allowed_without_unaffected_tasks") is False,
        "single-task pilot overclaims generalization, power, equivalence or negative transfer",
    )

    memory = protocol.get("memory_topic_gate", {})
    require(
        errors,
        memory.get("status") == "ineligible_not_tested"
        and memory.get("unlocking_by_editing_this_protocol_allowed") is False,
        "prompt pilot must remain ineligible for a Memory conclusion",
    )
    require(
        errors,
        "persistent_store_protocol" in str(memory.get("required_next_protocol", "")),
        "Memory eligibility must require a separate persistent-store protocol",
    )

    oracle = protocol.get("functional_oracle_catalog", {})
    require(
        errors,
        oracle.get("status") == "catalog_only_not_part_of_task3_prompt_experiment"
        and oracle.get("decision_rules_may_reference_catalog") is False,
        "oracle catalog must remain non-executable in this prompt pilot",
    )
    oracle_items = oracle.get("items", [])
    oracle_ids = unique_ids(oracle_items, "oracle catalog", errors)
    require(errors, set(oracle_ids) == EXPECTED_ORACLES, "oracle catalog ids changed")
    for item in oracle_items:
        for key in ("interface", "allowed", "forbidden", "control"):
            require(errors, bool(item.get(key)), f"oracle {item.get('id')} has empty {key}")

    decisions = protocol.get("decision_rules", {})
    require(
        errors,
        decisions == EXPECTED_DECISION_RULES,
        "Task 3 decision rules changed or exceed the prompt-pilot claim ceiling",
    )

    budget = protocol.get("budget_manifest", {})
    unresolved_budget = sorted(key for key, value in budget.items() if value == UNRESOLVED)
    if unresolved_budget:
        warnings.append("unresolved execution budget fields: " + ", ".join(unresolved_budget))
    budget_valid = not unresolved_budget
    if budget_valid:
        nonempty_text_fields = ("model_id", "model_build", "tokenizer")
        budget_valid = all(
            isinstance(budget.get(key), str)
            and len(budget[key].strip()) >= 3
            and budget[key].strip().lower() not in {"dummy", "fake", "unknown"}
            for key in nonempty_text_fields
        )
        budget_valid = budget_valid and budget.get("provider_seed_supported") is True
        budget_valid = budget_valid and budget.get("temperature") == 0
        budget_valid = budget_valid and budget.get("top_p") == 1
        budget_valid = budget_valid and budget.get("max_output_tokens") == 2048
        budget_valid = budget_valid and budget.get("max_post_update_agent_decisions") == 10
        budget_valid = budget_valid and isinstance(budget.get("max_total_tool_calls"), int)
        budget_valid = budget_valid and budget.get("max_total_tool_calls", 0) > 0
        budget_valid = budget_valid and isinstance(budget.get("wall_clock_seconds"), int)
        budget_valid = budget_valid and budget.get("wall_clock_seconds", 0) > 0
        budget_valid = budget_valid and is_sha256(budget.get("tool_schema_sha256"))
        token_counts = budget.get("token_count_by_arm")
        budget_valid = budget_valid and isinstance(token_counts, dict)
        if isinstance(token_counts, dict):
            budget_valid = budget_valid and set(token_counts) == set(EXPECTED_ARM_MATRIX)
            budget_valid = budget_valid and all(
                isinstance(value, int) and value >= 0 for value in token_counts.values()
            )
        budget_valid = budget_valid and budget.get("padding_policy") in {
            "task_value_free_token_matched_padding",
            "no_padding_with_frozen_token_count_adjustment",
        }
        budget_valid = budget_valid and isinstance(
            budget.get("deliberation_match_audit"), str
        )
        budget_valid = budget_valid and bool(
            str(budget.get("deliberation_match_audit", "")).strip()
        )
        require(errors, budget_valid, "resolved execution budget fields fail schema or range checks")

    seed_map_value = assignment.get("seed_to_arm_mapping_artifact")
    assignment_ready = False
    if seed_map_value != UNRESOLVED:
        assignment_ready = verify_seed_map_record(
            errors,
            seed_map_value,
            screening_seeds=screening,
            confirmation_seeds=confirmation,
            arm_ids=set(arm_ids),
        )

    blockers = protocol.get("execution_blockers", [])
    blocker_ids = unique_ids(blockers, "execution blockers", errors)
    require(errors, set(blocker_ids) == EXPECTED_ALL_BLOCKERS, "execution blocker set changed")
    blocker_map = {item["id"]: item.get("resolved") is True for item in blockers if item.get("id")}
    renderer_error_prefixes = (
        "renderer implementation",
        "renderer version",
        "prompt render",
        "rendering failed",
        "frozen state rendering",
        "frozen planning rendering",
        "frozen arm rendering",
    )
    hashes_valid = not any(error.startswith(renderer_error_prefixes) for error in errors)
    require(
        errors,
        blocker_map.get("renderer_hashes") == hashes_valid,
        "renderer_hashes blocker does not match actual render/hash validation",
    )
    evidence_records = protocol.get("execution_evidence", {})
    require(errors, isinstance(evidence_records, dict), "execution evidence must be an object")
    evidence_valid: dict[str, bool] = {"renderer_hashes": hashes_valid}
    if isinstance(evidence_records, dict):
        for blocker_id, resolved in blocker_map.items():
            if resolved and blocker_id != "renderer_hashes":
                evidence_valid[blocker_id] = verify_evidence_record(
                    errors, blocker_id, evidence_records.get(blocker_id)
                )
            elif blocker_id != "renderer_hashes":
                evidence_valid[blocker_id] = False
    unresolved_task3_blockers = sorted(
        blocker
        for blocker in REQUIRED_TASK3_BLOCKERS
        if not blocker_map.get(blocker, False) or not evidence_valid.get(blocker, False)
    )
    cross_task_ready = blocker_map.get("cross_task_confirmatory_families", False) and evidence_valid.get(
        "cross_task_confirmatory_families", False
    )
    evaluator_path_value = primary.get("evaluator_implementation_path")
    evaluator_hash_value = primary.get("evaluator_implementation_sha256")
    evaluator_path = ROOT / str(evaluator_path_value)
    evaluator_logic_resolved = (
        isinstance(evaluator_path_value, str)
        and evaluator_path_value != UNRESOLVED
        and is_sha256(evaluator_hash_value)
        and evaluator_path.is_file()
        and sha256_file(evaluator_path) == evaluator_hash_value
    )
    normalizer_path_value = primary.get("normalizer_implementation_path")
    normalizer_hash_value = primary.get("normalizer_implementation_sha256")
    normalizer_path = ROOT / str(normalizer_path_value)
    normalizer_resolved = (
        isinstance(normalizer_path_value, str)
        and normalizer_path_value != UNRESOLVED
        and is_sha256(normalizer_hash_value)
        and normalizer_path.is_file()
        and sha256_file(normalizer_path) == normalizer_hash_value
    )
    evaluator_resolved = evaluator_logic_resolved and normalizer_resolved
    if (
        protocol.get("execution_manifest_status") == "frozen"
        and not evaluator_resolved
    ):
        errors.append("frozen execution manifest lacks a real hash-matched primary evaluator")
    execution_manifest_frozen = (
        protocol.get("execution_manifest_status") == "frozen"
        and budget_valid
        and evaluator_resolved
        and assignment_ready
        and not unresolved_task3_blockers
    )

    analysis_plan_valid = not errors
    return {
        "analysis_plan_valid": analysis_plan_valid,
        "execution_manifest_frozen": execution_manifest_frozen,
        "causal_prompt_pilot_ready": analysis_plan_valid and execution_manifest_frozen,
        "cross_task_confirmation_ready": False,
        "memory_experiment_eligible": False,
        "claim_ceiling": "prompt_context_pilot_design_only" if analysis_plan_valid else "none",
        "errors": errors,
        "warnings": warnings,
        "unresolved_task3_blockers": unresolved_task3_blockers,
        "cross_task_confirmatory_families_resolved": cross_task_ready,
        "checked_assets": verify_assets,
    }


def refreeze_planning_mutation(protocol: dict[str, Any], text: str) -> dict[str, Any]:
    mutated = copy.deepcopy(protocol)
    renderer_path = ROOT / mutated["renderer"]["implementation_path"]
    renderer = load_renderer(renderer_path)
    mutated["planning_library"]["P1_TASK_VALUE_FREE"]["text"] = text
    mutated["planning_library"]["P1_TASK_VALUE_FREE"]["rendered_sha256"] = renderer.text_sha256(text)
    states, plans, arms = render_inputs(mutated, renderer)
    del states, plans
    for arm in mutated["arms"]:
        arm["rendered_sha256"] = renderer.text_sha256(arms[arm["id"]])
    return mutated


def refreeze_prompt_hashes(mutated: dict[str, Any]) -> dict[str, Any]:
    """Recompute prompt hashes so semantic mutation tests cannot fail on stale hashes alone."""
    renderer_path = ROOT / mutated["renderer"]["implementation_path"]
    renderer = load_renderer(renderer_path)
    states, plans, arms = render_inputs(mutated, renderer)
    for state_id, text in states.items():
        mutated["input_library"][state_id]["rendered_sha256"] = renderer.text_sha256(text)
    for plan_id, text in plans.items():
        mutated["planning_library"][plan_id]["rendered_sha256"] = renderer.text_sha256(text)
    for arm in mutated["arms"]:
        arm["rendered_sha256"] = renderer.text_sha256(arms[arm["id"]])
    return mutated


def run_self_tests(protocol: dict[str, Any]) -> dict[str, bool]:
    cases: dict[str, tuple[dict[str, Any], str]] = {}

    undefined_input = copy.deepcopy(protocol)
    next(arm for arm in undefined_input["arms"] if arm["id"] == "U_REPEAT_P0")[
        "state_input_id"
    ] = "ARBITRARY_UNDEFINED"
    cases["undefined_arm_input"] = (undefined_input, "invalid")

    bogus_estimand = copy.deepcopy(protocol)
    next(
        item
        for item in bogus_estimand["estimands"]
        if item["id"] == "external_state_canonicalization"
    )["terms"][0]["arm_id"] = "NOT_AN_ARM"
    cases["bogus_estimand_arm"] = (bogus_estimand, "invalid")

    empty_oracle = copy.deepcopy(protocol)
    empty_oracle["functional_oracle_catalog"]["items"][0]["control"] = ""
    cases["empty_oracle_control"] = (empty_oracle, "invalid")

    ready_unresolved_budget = copy.deepcopy(protocol)
    ready_unresolved_budget["execution_manifest_status"] = "frozen"
    for item in ready_unresolved_budget["execution_blockers"]:
        if item["id"] in REQUIRED_TASK3_BLOCKERS:
            item["resolved"] = True
    cases["ready_with_unresolved_budget"] = (ready_unresolved_budget, "not_ready")

    synonym_leakage = refreeze_planning_mutation(
        protocol,
        "Change the origin input, recompute the route comparison, and verify the map result.",
    )
    cases["task_specific_synonym_leakage"] = (synonym_leakage, "invalid")

    memory_unlock = copy.deepcopy(protocol)
    memory_unlock["memory_topic_gate"]["status"] = "eligible"
    memory_unlock["decision_rules"]["memory_topic_status"] = "eligible"
    cases["memory_unlock_without_store_protocol"] = (memory_unlock, "invalid")

    missing_forbidden = copy.deepcopy(protocol)
    missing_forbidden["forbidden_claims_before_cross_task_execution"].pop()
    cases["missing_forbidden_claim"] = (missing_forbidden, "invalid")

    dangerous_decision = copy.deepcopy(protocol)
    dangerous_decision["decision_rules"]["root_cause_decision_allowed"] = True
    cases["task3_root_cause_decision"] = (dangerous_decision, "invalid")

    wrong_truth = copy.deepcopy(protocol)
    next(atom for atom in wrong_truth["semantic_atoms"] if atom["id"] == "origin_current")[
        "value"
    ] = "Wrongville"
    cases["refrozen_wrong_current_truth"] = (
        refreeze_prompt_hashes(wrong_truth),
        "invalid",
    )

    crossed_relations = copy.deepcopy(protocol)
    next(
        atom for atom in crossed_relations["semantic_atoms"] if atom["id"] == "origin_current"
    )["relation"] = {"supersedes": "destination_old"}
    next(
        atom
        for atom in crossed_relations["semantic_atoms"]
        if atom["id"] == "destination_current"
    )["relation"] = {"supersedes": "origin_old"}
    cases["cross_predicate_supersession"] = (
        refreeze_prompt_hashes(crossed_relations),
        "invalid",
    )

    overclaim_estimand = copy.deepcopy(protocol)
    next(
        item
        for item in overclaim_estimand["estimands"]
        if item["id"] == "external_state_canonicalization"
    )["causal_label"] = "memory_causal"
    cases["estimand_memory_overclaim"] = (overclaim_estimand, "invalid")

    permissive_decision = copy.deepcopy(protocol)
    rule = permissive_decision["decision_rules"][
        "external_state_canonicalization_progression_signal"
    ]
    rule["minimum_effect_pp"] = -999
    rule["outcome_id"] = "always_true"
    cases["permissive_decision_rule"] = (permissive_decision, "invalid")

    trivial_outcome = copy.deepcopy(protocol)
    trivial_outcome["outcomes"]["unique_primary"]["definition"] = "Always return success."
    cases["trivial_primary_outcome"] = (trivial_outcome, "invalid")

    top_level_overclaim = copy.deepcopy(protocol)
    top_level_overclaim["research_question"] = "Prompt formatting proves Memory causal."
    top_level_overclaim["pre_execution_claim_ceiling"] = "memory_causal"
    cases["top_level_memory_overclaim"] = (top_level_overclaim, "invalid")

    implicit_revision = copy.deepcopy(protocol)
    implicit_revision["diagnostic_variant"]["update_semantics"]["old_values_explicit"] = False
    cases["nonexplicit_old_value"] = (implicit_revision, "invalid")

    fake_ready = copy.deepcopy(protocol)
    fake_ready["execution_manifest_status"] = "frozen"
    fake_ready["assignment_and_isolation"]["seed_to_arm_mapping_artifact"] = "fake-map.json"
    fake_ready["budget_manifest"].update(
        {
            "model_id": "dummy-model",
            "model_build": "dummy-build",
            "provider_seed_supported": True,
            "tokenizer": "dummy-tokenizer",
            "max_total_tool_calls": 20,
            "wall_clock_seconds": 600,
            "tool_schema_sha256": "0" * 64,
            "token_count_by_arm": {arm_id: 100 for arm_id in EXPECTED_ARM_MATRIX},
            "padding_policy": "task_value_free_token_matched_padding",
            "deliberation_match_audit": "fake-audit.json",
        }
    )
    fake_ready["outcomes"]["unique_primary"]["evaluator_implementation_path"] = (
        "stage0d_prompt_renderers.py"
    )
    fake_ready["outcomes"]["unique_primary"]["evaluator_implementation_sha256"] = sha256_file(
        ROOT / "stage0d_prompt_renderers.py"
    )
    for item in fake_ready["execution_blockers"]:
        item["resolved"] = True
    cases["fake_ready_without_evidence"] = (fake_ready, "invalid")

    results: dict[str, bool] = {}
    for name, (mutated, expected) in cases.items():
        result = validate(mutated, verify_assets=False)
        if expected == "invalid":
            results[name] = result["analysis_plan_valid"] is False
        else:
            results[name] = result["causal_prompt_pilot_ready"] is False
    try:
        json.loads(
            '{"id":"first","id":"second"}',
            object_pairs_hook=reject_duplicate_object_pairs,
        )
    except ValueError:
        results["duplicate_json_key"] = True
    else:
        results["duplicate_json_key"] = False
    arm_order = list(EXPECTED_ARM_MATRIX)
    bad_seed_map = {
        "assignment_algorithm": "balanced_latin_cycle_v1",
        "randomization_seed": 123,
        "base_arm_order": arm_order,
        "screening": [
            {"seed": seed, "arm_order": arm_order}
            for seed in protocol["statistics"]["screening_seeds"]
        ],
        "confirmation": [
            {"seed": seed, "arm_order": arm_order}
            for seed in protocol["statistics"]["confirmation_seeds"]
        ],
    }
    results["noncounterbalanced_seed_map"] = bool(
        validate_seed_map_payload(
            bad_seed_map,
            screening_seeds=protocol["statistics"]["screening_seeds"],
            confirmation_seeds=protocol["statistics"]["confirmation_seeds"],
            arm_ids=set(EXPECTED_ARM_MATRIX),
        )
    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("protocol", nargs="?", type=pathlib.Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    protocol = load_json(args.protocol.resolve())
    result = validate(protocol, verify_assets=True)
    if args.self_test:
        tests = run_self_tests(protocol)
        result["self_tests"] = tests
        result["self_tests_passed"] = all(tests.values())
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result["analysis_plan_valid"]:
        return 1
    if args.self_test and not result.get("self_tests_passed"):
        return 1
    if args.require_ready and not result["causal_prompt_pilot_ready"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
