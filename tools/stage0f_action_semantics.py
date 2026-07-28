#!/usr/bin/env python3
"""Shared interpreter for the frozen Stage-0F action semantic contract."""

from __future__ import annotations

from typing import Any, Mapping, Tuple


class ActionSemanticError(ValueError):
    pass


def derive_action_semantics(
    p_old_status: Any,
    action: Any,
    contract: Mapping[str, Any],
) -> Tuple[str, bool]:
    """Validate a primitive action and derive phenotype/confirmed-positive."""

    if contract.get("artifact_type") != (
        "stage0f_bounds_action_semantic_contract"
    ) or contract.get("contract_version") != (
        "stage0f-action-semantics-v1"
    ):
        raise ActionSemanticError("unsupported action semantic contract")
    required_keys = contract.get("required_action_keys")
    boolean_fields = contract.get("boolean_fields")
    compatibility_fields = contract.get("compatibility_fields")
    compatibility_enum = contract.get("compatibility_enum")
    if (
        not isinstance(action, dict)
        or not isinstance(required_keys, list)
        or set(action) != set(required_keys)
        or p_old_status not in contract.get("p_old_status_enum", [])
        or not isinstance(boolean_fields, list)
        or any(type(action.get(field)) is not bool for field in boolean_fields)
        or not isinstance(compatibility_fields, list)
        or any(
            action.get(field) not in compatibility_enum
            for field in compatibility_fields
        )
        or contract.get("constraints")
        != [
            "candidate_action_and_required_omission_mutually_exclusive",
            "required_omission_requires_candidate_false",
        ]
    ):
        raise ActionSemanticError(
            "malformed primitive action assessment"
        )

    executed = action["candidate_action_executed"]
    omission = action["required_action_omission"]
    if executed and omission:
        raise ActionSemanticError(
            "malformed primitive action assessment"
        )
    if omission and executed is not False:
        raise ActionSemanticError(
            "malformed primitive action assessment"
        )

    compatibility_key = "%s|%s" % (
        action["compatible_with_p_old"],
        action["compatible_with_p_new"],
    )
    if executed:
        table = contract.get(
            "executed_compatibility_truth_table", {}
        )
        phenotype = table.get(compatibility_key)
    elif omission:
        table = contract.get(
            "omission_deadline_truth_table", {}
        )
        phenotype = table.get(
            "true"
            if action["deadline_or_commit_reached"]
            else "false"
        )
    else:
        table = contract.get(
            "no_action_compatibility_truth_table", {}
        )
        phenotype = table.get(compatibility_key)
    if phenotype not in {
        "target_positive",
        "target_negative",
        "unidentifiable",
    }:
        raise ActionSemanticError(
            "incomplete action semantic truth table"
        )
    positive = (
        p_old_status == contract.get("confirmed_p_old_status")
        and phenotype == "target_positive"
    )
    return phenotype, positive
