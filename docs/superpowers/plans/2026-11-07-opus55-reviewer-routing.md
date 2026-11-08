# Opus 5.5 Reviewer Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the shared Claude review bridge accept the ARIS project alias `opus5.5` and invoke Claude Code with `claude-opus-5-5` across all projects.

**Architecture:** Add one explicit model-alias resolver at the CLI boundary in the shared bridge. Preserve the caller's requested alias in result metadata while using only Claude Code's returned metadata as evidence of the actual model.

**Tech Stack:** Python 3, `unittest`, Claude Code CLI, Codex MCP.

**Spec:** `docs/superpowers/specs/2026-11-07-opus55-reviewer-routing.md`

## Global Constraints

- `opus5.5` must resolve to `claude-opus-5-5`.
- No automatic fallback to a different model is permitted.
- Unrelated model identifiers must pass through unchanged.
- Existing synchronous, reply, and asynchronous review interfaces must remain compatible.
- The bridge must continue distinguishing requested model configuration from actual CLI-reported model evidence.

---

### Task 1: Pin the model-alias contract

**Files:**
- Modify: `tests/test_claude_review_artifact_tools.py`

**Interfaces:**
- Consumes: `build_command(prompt, model=...) -> list[str]`
- Produces: Regression coverage for explicit and default model alias routing.

- [x] **Step 1: Write failing command-construction tests**

Add tests asserting that `model="opus5.5"` and `DEFAULT_MODEL="opus5.5"` place
`claude-opus-5-5` after `--model`, while an unrelated identifier remains
unchanged.

- [x] **Step 2: Run the focused tests and confirm failure**

Run: `python3 -m unittest tests.test_claude_review_artifact_tools.BridgeDefaultTests -v`

Expected: the two alias cases fail because the bridge currently passes
`opus5.5` through unchanged.

### Task 2: Implement the shared alias resolver

**Files:**
- Modify: `mcp-servers/claude-review/server.py`
- Modify: `tests/test_claude_review_parse.py`

**Interfaces:**
- Consumes: Caller model string or `CLAUDE_REVIEW_MODEL`.
- Produces: `resolve_cli_model(model: str) -> str`, used only at command construction.

- [x] **Step 1: Add the minimal resolver**

Define an immutable alias mapping containing only
`{"opus5.5": "claude-opus-5-5"}` and resolve the selected model immediately
before adding the CLI `--model` argument.

- [x] **Step 2: Preserve request-versus-evidence semantics**

Add a mocked CLI result test asserting `requestedModel == "opus5.5"`,
`model == "claude-opus-5-5"`, and `modelSource == "cli_model_usage"`.

- [x] **Step 3: Run the focused bridge tests**

Run: `python3 -m unittest tests.test_claude_review_artifact_tools tests.test_claude_review_parse -v`

Expected: all tests pass.

### Task 3: Document and validate global behavior

**Files:**
- Modify: `mcp-servers/claude-review/README.md`

**Interfaces:**
- Consumes: The alias resolver behavior implemented in Task 2.
- Produces: Installation-independent documentation and live validation evidence.

- [x] **Step 1: Document the compatibility alias**

Document that ARIS projects may keep `opus5.5`, that the bridge resolves it to
`claude-opus-5-5`, and that results still report requested and actual models
separately.

- [x] **Step 2: Run relevant test suites**

Run: `python3 -m unittest tests.test_claude_review_artifact_tools tests.test_claude_review_parse -v`

Expected: all tests pass.

- [x] **Step 3: Run a live no-tools review through the patched module**

Invoke `run_claude_review` with `model="opus5.5"` and assert the returned
actual model is `claude-opus-5-5`.

- [x] **Step 4: Record the repair in the active project**

Update `ICDE_2/NEEDS-YOU.md` and `ICDE_2/PROJECT-STATUS.md` with an
America/Detroit timestamp, removing the reviewer-routing blocker only after
the live model evidence passes.

- [x] **Step 5: Commit only the shared bridge repair**

Stage the spec, plan, bridge, tests, and bridge README. Do not stage unrelated
files or push a remote.
