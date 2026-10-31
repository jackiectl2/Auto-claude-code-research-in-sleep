from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.resolve_gemini_search_model import ARGON_MODEL, UPSTREAM_MODEL, resolve_model


def test_project_switch_resolves_from_nested_working_directory() -> None:
    with TemporaryDirectory() as temp:
        project = Path(temp)
        (project / ".aris").mkdir()
        nested = project / "experiments" / "pilot"
        nested.mkdir(parents=True)
        config = project / ".aris" / "gemini-search.json"
        config.write_text(json.dumps({"argon_enabled": False, "argon_paid_authorized": False}))
        assert resolve_model(nested) == UPSTREAM_MODEL
        config.write_text(json.dumps({"argon_enabled": True, "argon_paid_authorized": True}))
        assert resolve_model(nested) == ARGON_MODEL


def test_argon_requires_project_authorization() -> None:
    with TemporaryDirectory() as temp:
        project = Path(temp)
        (project / ".aris").mkdir()
        (project / ".aris" / "gemini-search.json").write_text(
            json.dumps({"argon_enabled": True, "argon_paid_authorized": False})
        )
        try:
            resolve_model(project)
        except ValueError:
            pass
        else:
            raise AssertionError("Argon literature search must require authorization")


def test_legacy_project_preserves_argon_default() -> None:
    with TemporaryDirectory() as temp:
        assert resolve_model(Path(temp)) == ARGON_MODEL
