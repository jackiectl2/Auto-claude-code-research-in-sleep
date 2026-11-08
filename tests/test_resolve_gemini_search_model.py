from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
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
        project = Path(temp)
        (project / ".aris").mkdir()
        (project / ".aris" / "installed-skills.txt").write_text("repo_root\t/example\n")
        assert resolve_model(project) == ARGON_MODEL


def test_unrelated_directory_cannot_silently_select_paid_argon() -> None:
    with TemporaryDirectory() as temp:
        try:
            resolve_model(Path(temp))
        except ValueError as exc:
            assert "No ARIS project found" in str(exc)
        else:
            raise AssertionError("An unrelated working directory must fail closed")


def test_explicit_project_root_resolves_switch_from_temporary_working_directory() -> None:
    with TemporaryDirectory() as temp:
        root = Path(temp)
        project = root / "project"
        scratch = root / "scratch"
        (project / ".aris").mkdir(parents=True)
        scratch.mkdir()
        (project / ".aris" / "gemini-search.json").write_text(
            json.dumps({"argon_enabled": False, "argon_paid_authorized": False})
        )
        resolver = Path(__file__).resolve().parents[1] / "tools" / "resolve_gemini_search_model.py"
        result = subprocess.run(
            [sys.executable, str(resolver), "--project-root", str(project)],
            cwd=scratch, capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == UPSTREAM_MODEL
