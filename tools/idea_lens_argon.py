#!/usr/bin/env python3
"""Generate one bounded idea lens with the Gemini 4 Argon Interactions API."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from urllib import request


MODEL = "gemini-4-argon"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
FIELDS = ("summary", "hypothesis", "mve", "contribution_type", "risk", "effort", "dedup_key")
CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {field: {"type": "string"} for field in FIELDS},
    "required": list(FIELDS),
}
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {"candidates": {"type": "array", "items": CANDIDATE_SCHEMA}},
    "required": ["candidates"],
}


def load_task(path: Path) -> dict[str, object]:
    task = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(task, dict):
        raise ValueError("Input must be a JSON object")
    for field in ("shard_id", "lens_instructions", "research_context"):
        if not isinstance(task.get(field), str) or not task[field].strip():
            raise ValueError(f"Missing nonempty {field}")
    units = task.get("assigned_unit_ids")
    if not isinstance(units, list) or not units or any(not isinstance(unit, str) or not unit for unit in units):
        raise ValueError("assigned_unit_ids must be a nonempty string array")
    return task


def require_project_switch(project_root: Path) -> None:
    config_path = project_root / ".aris" / "idea-creator.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("lens_generator") != MODEL:
        raise ValueError("Project has not selected Gemini 4 Argon for idea lenses")
    if config.get("argon_paid_authorized") is not True:
        raise ValueError("Project has not authorized paid Argon idea-lens calls")


def build_payload(task: dict[str, object]) -> dict[str, object]:
    prompt = (
        "You are generating research idea candidates for exactly one analytical lens. "
        "Do not rank, score, accept, reject, or review ideas. Do not invent paper titles or citations. "
        "Generate distinct, testable candidates for the assigned lens only. "
        "Each candidate needs a concise summary, falsifiable hypothesis, minimum viable experiment "
        "(mve), contribution_type, risk, effort, and dedup_key. Return JSON only.\n\n"
        f"Lens: {task['shard_id']}\n"
        f"Assigned units: {json.dumps(task['assigned_unit_ids'], ensure_ascii=False)}\n"
        f"Lens instructions: {task['lens_instructions']}\n"
        f"Research context and project constraints:\n{task['research_context']}"
    )
    return {
        "model": MODEL,
        "input": prompt,
        "generation_config": {"thinking_level": "medium"},
        "response_format": {"type": "text", "mime_type": "application/json", "schema": OUTPUT_SCHEMA},
    }


def extract_output(response: dict[str, object]) -> dict[str, object]:
    if response.get("status") != "completed":
        raise ValueError("Gemini interaction did not complete")
    for step in reversed(response.get("steps", [])):
        if not isinstance(step, dict) or step.get("type") != "model_output":
            continue
        for part in step.get("content", []):
            if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                result = json.loads(part["text"])
                if isinstance(result, dict):
                    return result
    raise ValueError("Gemini returned no JSON model output")


def validate_candidates(result: dict[str, object]) -> list[dict[str, str]]:
    candidates = result.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Gemini returned no candidates")
    for candidate in candidates:
        if not isinstance(candidate, dict) or any(
            not isinstance(candidate.get(field), str) or not candidate[field].strip() for field in FIELDS
        ):
            raise ValueError("Gemini returned an incomplete candidate")
    return [{field: candidate[field].strip() for field in FIELDS} for candidate in candidates]


def generate(task: dict[str, object], api_key: str) -> dict[str, object]:
    payload = json.dumps(build_payload(task)).encode("utf-8")
    req = request.Request(
        ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    with request.urlopen(req, timeout=900) as response:
        data = json.load(response)
    candidates = validate_candidates(extract_output(data))
    return {
        "shard_id": task["shard_id"],
        "assigned_unit_ids": task["assigned_unit_ids"],
        "covered_unit_ids": task["assigned_unit_ids"],
        "status": "completed",
        "candidates": candidates,
        "errors": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="One lens task JSON file")
    parser.add_argument("--project-root", type=Path, required=True, help="Project with the idea-creator switch")
    args = parser.parse_args()
    try:
        require_project_switch(args.project_root)
        task = load_task(args.input)
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is required")
        print(json.dumps(generate(task, api_key), ensure_ascii=False))
        return 0
    except Exception as exc:
        # Do not print API responses, request bodies, or environment values.
        print(f"Argon idea lens failed: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
