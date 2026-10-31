#!/usr/bin/env python3
"""Resolve a project's Gemini literature model without changing global settings."""

from __future__ import annotations

import json
from pathlib import Path
import sys


UPSTREAM_MODEL = "auto-gemini-3"
ARGON_MODEL = "gemini-4-argon"


def resolve_model(start: Path) -> str:
    for directory in (start.resolve(), *start.resolve().parents):
        config_path = directory / ".aris" / "gemini-search.json"
        if not config_path.is_file():
            continue
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(config, dict) or type(config.get("argon_enabled")) is not bool:
            raise ValueError(f"Invalid Gemini literature switch: {config_path}")
        if config["argon_enabled"]:
            if config.get("argon_paid_authorized") is not True:
                raise ValueError(f"Argon literature use is not authorized: {config_path}")
            return ARGON_MODEL
        return UPSTREAM_MODEL
    # Preserve the custom branch's existing behavior for older projects with no switch.
    return ARGON_MODEL


if __name__ == "__main__":
    try:
        print(resolve_model(Path.cwd()))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Gemini literature model resolution failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
