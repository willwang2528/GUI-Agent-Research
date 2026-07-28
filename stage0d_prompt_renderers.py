#!/usr/bin/env python3
"""Deterministic prompt renderers for the Stage 0D Task 3 pilot."""

from __future__ import annotations

import hashlib
import json
from typing import Any


RENDERER_VERSION = "task3_prompt_renderer_v1"
ATOM_KEYS = ("id", "predicate", "value", "status", "source", "relation")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_atom(atom: dict[str, Any]) -> dict[str, Any]:
    if set(atom) != set(ATOM_KEYS):
        raise ValueError(f"Atom {atom.get('id')} must have exactly {ATOM_KEYS}")
    return {key: atom[key] for key in ATOM_KEYS}


def render_flat(atoms: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for atom in atoms:
        item = canonical_atom(atom)
        rows.append(
            "ATOM "
            + "; ".join(
                [
                    f"id={item['id']}",
                    f"predicate={item['predicate']}",
                    f"value={canonical_json(item['value'])}",
                    f"status={item['status']}",
                    f"source={item['source']}",
                    f"relation={canonical_json(item['relation'])}",
                ]
            )
            + "."
        )
    return "\n".join(rows)


def render_structured(atoms: list[dict[str, Any]]) -> str:
    return "STATE=" + canonical_json([canonical_atom(atom) for atom in atoms])


def render_history_repeat(initial_instruction: str, updates: list[str]) -> str:
    lines = [f"INITIAL_INSTRUCTION={initial_instruction}"]
    lines.extend(f"UPDATE_{index}={update}" for index, update in enumerate(updates, 1))
    return "\n".join(lines)


def render_arm(
    *,
    state_text: str,
    planning_text: str,
    delimiter: str,
    state_first: bool,
) -> str:
    parts = [part for part in (state_text, planning_text) if part]
    if not state_first:
        parts.reverse()
    return delimiter.join(parts)


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
