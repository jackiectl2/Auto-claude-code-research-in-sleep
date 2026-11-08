"""Standard-library tests for Claude reviewer effort routing."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.reviewer_route import resolve_route


class ClaudeReviewerRouteTests(unittest.TestCase):
    def test_supported_efforts_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for effort in ("low", "medium", "high", "xhigh", "max"):
                with self.subTest(effort=effort):
                    route = resolve_route(
                        directory,
                        "codex",
                        reviewer="claude-code",
                        model="opus5.5",
                        effort=effort,
                    )
                    self.assertEqual(route["model"], "opus5.5")
                    self.assertEqual(route["effort"], effort)

    def test_unsupported_efforts_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for effort in ("ultra", "unknown"):
                with self.subTest(effort=effort), self.assertRaisesRegex(
                    ValueError, "Claude reviewer effort"
                ):
                    resolve_route(
                        directory,
                        "codex",
                        reviewer="claude-code",
                        effort=effort,
                    )

    def test_project_selected_effort_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            config_dir = project / ".aris"
            config_dir.mkdir()
            (config_dir / "reviewer.json").write_text(
                json.dumps(
                    {
                        "backend": "claude-code",
                        "model": "opus5.5",
                        "effort": "high",
                    }
                ),
                encoding="utf-8",
            )
            route = resolve_route(project, "codex")
            self.assertEqual(route["backend"], "claude-code")
            self.assertEqual(route["model"], "opus5.5")
            self.assertEqual(route["effort"], "high")


if __name__ == "__main__":
    unittest.main()
