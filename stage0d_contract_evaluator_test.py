#!/usr/bin/env python3
"""Unit tests for the normalized Stage 0D contract evaluator."""

from __future__ import annotations

import copy
import unittest

from stage0d_contract_evaluator import SCHEMA_VERSION, evaluate_trace


def successful_trace() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": 3,
        "prefix_inclusion_passed": True,
        "events": [
            {
                "decision_index": 1,
                "type": "field_snapshot",
                "origin": "Randyland",
                "destination": "Carnegie Mellon University",
            },
            {
                "decision_index": 2,
                "type": "route_artifact",
                "artifact_id": "route-current",
                "origin": "Randyland",
                "destination": "Carnegie Mellon University",
                "mode_times_minutes": {"walking": 42, "driving": 9},
            },
            {
                "decision_index": 3,
                "type": "final_answer",
                "derived_from_artifact_id": "route-current",
                "reported_mode_times_minutes": {"walking": 42, "driving": 9},
                "reported_difference_minutes": 33,
                "governing_endpoint_values": [
                    "Randyland",
                    "Carnegie Mellon University",
                ],
            },
        ],
    }


class ContractEvaluatorTest(unittest.TestCase):
    def test_success(self) -> None:
        self.assertTrue(evaluate_trace(successful_trace())["contract_consistent_completion"])

    def test_stale_destination_fails(self) -> None:
        trace = successful_trace()
        trace["events"][0]["destination"] = "University of Pittsburgh"
        self.assertFalse(evaluate_trace(trace)["contract_consistent_completion"])

    def test_no_post_repair_route_fails(self) -> None:
        trace = successful_trace()
        trace["events"][1]["origin"] = "Phipps Conservatory"
        self.assertFalse(evaluate_trace(trace)["contract_consistent_completion"])

    def test_answer_from_old_artifact_fails(self) -> None:
        trace = successful_trace()
        trace["events"][2]["derived_from_artifact_id"] = "route-old"
        self.assertFalse(evaluate_trace(trace)["contract_consistent_completion"])

    def test_wrong_reported_difference_fails(self) -> None:
        trace = successful_trace()
        trace["events"][2]["reported_difference_minutes"] = 34
        self.assertFalse(evaluate_trace(trace)["contract_consistent_completion"])

    def test_superseded_governing_value_fails(self) -> None:
        trace = successful_trace()
        trace["events"][2]["governing_endpoint_values"] = [
            "Phipps Conservatory",
            "Carnegie Mellon University",
        ]
        self.assertFalse(evaluate_trace(trace)["contract_consistent_completion"])

    def test_missing_prefix_evidence_fails(self) -> None:
        trace = successful_trace()
        trace["prefix_inclusion_passed"] = False
        self.assertFalse(evaluate_trace(trace)["contract_consistent_completion"])

    def test_event_after_window_fails(self) -> None:
        trace = copy.deepcopy(successful_trace())
        trace["events"][2]["decision_index"] = 11
        self.assertFalse(evaluate_trace(trace)["contract_consistent_completion"])


if __name__ == "__main__":
    unittest.main()
