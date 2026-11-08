#!/usr/bin/env python3
"""Resolve a project's Gemini literature model without changing global settings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


UPSTREAM_MODEL = "auto-gemini-3"
ARGON_MODEL = "gemini-4-argon"


def resolve_model(start: Path) -> str:
    for directory in (start.resolve(), *start.resolve().parents):
        config_path = directory / ".aris" / "gemini-search.json"
        if config_path.is_file():
            config = json.loads(config_path.read_text(encoding="utf-8"))
            if not isinstance(config, dict) or type(config.get("argon_enabled")) is not bool:
                raise ValueError(f"Invalid Gemini literature switch: {config_path}")
            if config["argon_enabled"]:
                if config.get("argon_paid_authorized") is not True:
                    raise ValueError(f"Argon literature use is not authorized: {config_path}")
                return ARGON_MODEL
            return UPSTREAM_MODEL
        # Projects initialized before the switch still use this branch's old default.
        if (directory / ".aris" / "installed-skills.txt").is_file() or (
            directory / ".aris" / "installed-skills-codex.txt"
        ).is_file():
            return ARGON_MODEL
    raise ValueError(f"No ARIS project found from {start.resolve()}; run from the project or pass --project-root")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, help="Actual ARIS project root, even when called from a temporary directory")
    args = parser.parse_args()
    try:
        print(resolve_model(args.project_root or Path.cwd()))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Gemini literature model resolution failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
