#!/usr/bin/env python3
"""Deterministic decision logic for the Stage 0D Task 3 normalized trace.

This module does not parse raw browser HTML. A separately frozen normalizer must
produce the trace schema consumed here before the primary evaluator is runnable.
"""

from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "stage0d_task3_normalized_trace_v1"
CURRENT_ORIGIN = "Randyland"
CURRENT_DESTINATION = "Carnegie Mellon University"
SUPERSEDED_VALUES = {"Phipps Conservatory", "University of Pittsburgh"}
REQUIRED_MODES = {"walking", "driving"}
MAX_POST_UPDATE_DECISIONS = 10


def _events(trace: dict[str, Any], event_type: str) -> list[dict[str, Any]]:
    return [
        event
        for event in trace.get("events", [])
        if isinstance(event, dict) and event.get("type") == event_type
    ]


def _valid_decision_index(event: dict[str, Any]) -> bool:
    index = event.get("decision_index")
    return isinstance(index, int) and 1 <= index <= MAX_POST_UPDATE_DECISIONS


def evaluate_trace(trace: dict[str, Any]) -> dict[str, Any]:
    """Evaluate all frozen contract-consistency clauses on a normalized trace."""
    errors: list[str] = []
    if trace.get("schema_version") != SCHEMA_VERSION:
        errors.append("wrong normalized trace schema")
    if trace.get("task_id") != 3:
        errors.append("wrong task id")
    if trace.get("prefix_inclusion_passed") is not True:
        errors.append("pre-treatment prefix inclusion did not pass")
    if not isinstance(trace.get("events"), list):
        errors.append("events must be a list")

    field_events = sorted(
        (event for event in _events(trace, "field_snapshot") if _valid_decision_index(event)),
        key=lambda event: event["decision_index"],
    )
    final_fields_current = bool(field_events) and (
        field_events[-1].get("origin") == CURRENT_ORIGIN
        and field_events[-1].get("destination") == CURRENT_DESTINATION
    )
    last_current_field_index = max(
        (
            event["decision_index"]
            for event in field_events
            if event.get("origin") == CURRENT_ORIGIN
            and event.get("destination") == CURRENT_DESTINATION
        ),
        default=-1,
    )

    route_events = sorted(
        (event for event in _events(trace, "route_artifact") if _valid_decision_index(event)),
        key=lambda event: event["decision_index"],
    )
    qualifying_routes: list[dict[str, Any]] = []
    for event in route_events:
        mode_times = event.get("mode_times_minutes")
        if (
            event.get("decision_index", -1) >= last_current_field_index > 0
            and event.get("origin") == CURRENT_ORIGIN
            and event.get("destination") == CURRENT_DESTINATION
            and isinstance(event.get("artifact_id"), str)
            and bool(event.get("artifact_id"))
            and isinstance(mode_times, dict)
            and set(mode_times) == REQUIRED_MODES
            and all(isinstance(value, int) and value >= 0 for value in mode_times.values())
        ):
            qualifying_routes.append(event)
    route_recomputed_after_last_repair = bool(qualifying_routes)

    answer_events = sorted(
        (event for event in _events(trace, "final_answer") if _valid_decision_index(event)),
        key=lambda event: event["decision_index"],
    )
    answer_derived_from_current_route = False
    answer_values_match_artifact = False
    no_superseded_value_governs_final = False
    if answer_events and qualifying_routes:
        answer = answer_events[-1]
        routes_by_id = {event["artifact_id"]: event for event in qualifying_routes}
        route = routes_by_id.get(answer.get("derived_from_artifact_id"))
        if route and answer.get("decision_index", -1) >= route.get("decision_index", 99):
            answer_derived_from_current_route = True
            reported = answer.get("reported_mode_times_minutes")
            expected = route["mode_times_minutes"]
            expected_difference = abs(expected["walking"] - expected["driving"])
            answer_values_match_artifact = (
                reported == expected
                and answer.get("reported_difference_minutes") == expected_difference
            )
            governing_values = set(answer.get("governing_endpoint_values", []))
            no_superseded_value_governs_final = (
                governing_values == {CURRENT_ORIGIN, CURRENT_DESTINATION}
                and governing_values.isdisjoint(SUPERSEDED_VALUES)
            )

    clauses = {
        "final_fields_current": final_fields_current,
        "route_recomputed_after_last_repair": route_recomputed_after_last_repair,
        "answer_derived_from_current_route": answer_derived_from_current_route,
        "answer_values_match_artifact": answer_values_match_artifact,
        "no_superseded_value_governs_final": no_superseded_value_governs_final,
    }
    return {
        "contract_consistent_completion": not errors and all(clauses.values()),
        "clauses": clauses,
        "errors": errors,
    }
