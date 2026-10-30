from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools import idea_lens_argon


TASK = {
    "shard_id": "lens:contradiction",
    "assigned_unit_ids": ["contradiction"],
    "lens_instructions": "Find conflicting empirical results.",
    "research_context": "Study retrieval under distribution shift.",
}
CANDIDATE = {
    "summary": "Compare adaptive and static retrieval.",
    "hypothesis": "Adaptive retrieval helps only after a shift.",
    "mve": "Run both policies before and after a controlled shift.",
    "contribution_type": "empirical finding",
    "risk": "medium",
    "effort": "days",
    "dedup_key": "adaptive-retrieval-shift",
}


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, *_args):
        return json.dumps({
            "status": "completed",
            "steps": [{"type": "model_output", "content": [
                {"type": "text", "text": json.dumps({"candidates": [CANDIDATE]})}
            ]}]
        }).encode()


def test_argon_lens_pins_model_and_preserves_shard_identity() -> None:
    with patch.object(idea_lens_argon.request, "urlopen", return_value=FakeResponse()) as call:
        result = idea_lens_argon.generate(TASK, "test-key")
    sent = json.loads(call.call_args.args[0].data)
    assert sent["model"] == "gemini-4-argon"
    assert sent["response_format"]["mime_type"] == "application/json"
    assert call.call_args.kwargs["timeout"] == 900
    assert result == {
        "shard_id": TASK["shard_id"],
        "assigned_unit_ids": TASK["assigned_unit_ids"],
        "covered_unit_ids": TASK["assigned_unit_ids"],
        "status": "completed",
        "candidates": [CANDIDATE],
        "errors": [],
    }


def test_argon_lens_rejects_incomplete_output() -> None:
    try:
        idea_lens_argon.validate_candidates({"candidates": [{"summary": "incomplete"}]})
    except ValueError:
        pass
    else:
        raise AssertionError("Incomplete candidates must not enter the jury")


def test_argon_lens_rejects_unfinished_interaction() -> None:
    response = {"status": "in_progress", "steps": [
        {"type": "model_output", "content": [
            {"type": "text", "text": json.dumps({"candidates": [CANDIDATE]})}
        ]}
    ]}
    try:
        idea_lens_argon.extract_output(response)
    except ValueError:
        pass
    else:
        raise AssertionError("An unfinished interaction must not enter the jury")


def test_argon_lens_requires_project_switch_and_paid_authorization() -> None:
    with TemporaryDirectory() as temp:
        root = Path(temp)
        config_dir = root / ".aris"
        config_dir.mkdir()
        config_file = config_dir / "idea-creator.json"
        for config in (
            {"lens_generator": "native", "argon_paid_authorized": False},
            {"lens_generator": "gemini-4-argon", "argon_paid_authorized": False},
        ):
            config_file.write_text(json.dumps(config))
            try:
                idea_lens_argon.require_project_switch(root)
            except ValueError:
                pass
            else:
                raise AssertionError("Paid Argon call must require the project switch and authorization")
        config_file.write_text(json.dumps({
            "lens_generator": "gemini-4-argon", "argon_paid_authorized": True,
        }))
        idea_lens_argon.require_project_switch(root)
