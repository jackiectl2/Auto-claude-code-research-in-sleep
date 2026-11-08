# General Claude Reviewer Model and Effort Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generalize the shared Claude reviewer route across versioned Claude model families and explicit Claude Code effort settings.

**Architecture:** Normalize only recognized compact Claude family/version aliases at the CLI boundary, while preserving requested and reported identity separately. Add effort as a first-class bridge option, then allow the ARIS route resolver and shared contract to forward it without fabricating actual-effort evidence.

**Tech Stack:** Python 3 standard library, Claude Code CLI, Codex MCP, ARIS reviewer route.

**Spec:** `docs/superpowers/specs/2026-11-07-claude-review-model-effort-routing.md`

## Global Constraints

- No automatic model fallback.
- Unknown model identifiers pass through unchanged.
- Valid Claude efforts are exactly `low`, `medium`, `high`, `xhigh`, and `max`.
- Requested settings remain distinct from CLI-reported evidence.
- Existing sync, reply, async, cwd, tools, and permission contracts remain compatible.
- Existing project research artifacts remain untouched.

---

### Task 1: Pin general model and effort behavior

**Files:**
- Modify: `tests/test_claude_review_artifact_tools.py`
- Modify: `tests/test_claude_review_parse.py`
- Create: `tests/test_claude_reviewer_route_unittest.py`

**Interfaces:**
- Consumes: `build_command`, `run_claude_review`, async job helpers, `handle_request`, and `resolve_route`.
- Produces: Failing regression tests for model patterns and effort propagation.

- [x] **Step 1: Add model-pattern tests**

Assert conversions for `opus5.6`, `sonnet4.6[1m]`, and `haiku4.5`, while
asserting canonical and unrelated identifiers remain unchanged.

- [x] **Step 2: Add effort command and schema tests**

Assert explicit/default/reply calls add `--effort`, invalid values fail, and
all four MCP review tools expose and forward `effort`.

- [x] **Step 3: Add result and async tests**

Assert `requestedEffort` is preserved, actual effort fields remain unknown,
and async state/worker/status retain the request.

- [x] **Step 4: Add standard-library reviewer-route tests**

Assert Claude accepts `low` through `max`, rejects `ultra` and unknown values,
and preserves a project-selected effort.

- [x] **Step 5: Run the tests and confirm the new assertions fail**

Run: `python3 -m unittest tests.test_claude_review_artifact_tools tests.test_claude_review_parse tests.test_claude_reviewer_route_unittest -v`

Expected: failures show missing general alias conversion, effort arguments,
schema forwarding, result fields, and route acceptance.

### Task 2: Implement bridge and route support

**Files:**
- Modify: `mcp-servers/claude-review/server.py`
- Modify: `tools/reviewer_route.py`

**Interfaces:**
- Consumes: model and effort from explicit MCP arguments, environment defaults, and `.aris/reviewer.json`.
- Produces: canonical CLI model, validated CLI effort, and request metadata.

- [x] **Step 1: Replace the exact alias map with family/version parsing**

Use one anchored regular expression for `opus`, `sonnet`, and `haiku`, preserve
optional context suffixes, and leave nonmatching values untouched.

- [x] **Step 2: Add effort validation and command construction**

Add `DEFAULT_EFFORT`, validate against the five Claude Code levels, and append
`--effort <level>` for explicit and default values.

- [x] **Step 3: Propagate effort through every bridge path**

Extend sync, reply, async state, worker, status serialization, tool schemas,
and tool dispatch. Return `requestedEffort`; return actual effort as null with
no source because CLI result JSON has no such metadata.

- [x] **Step 4: Permit Claude effort in reviewer_route.py**

Validate Claude effort against the same five-level contract instead of
rejecting all non-null values.

- [x] **Step 5: Run the focused tests**

Run: `python3 -m unittest tests.test_claude_review_artifact_tools tests.test_claude_review_parse tests.test_claude_reviewer_route_unittest -v`

Expected: all tests pass.

### Task 3: Update contracts, deploy, and verify

**Files:**
- Modify: `mcp-servers/claude-review/README.md`
- Modify: `skills/shared-references/reviewer-backends.md`
- Modify: manifest-selected checkout copies of `tools/reviewer_route.py` and `skills/shared-references/reviewer-backends.md` only when needed.
- Modify: `ICDE_2/.aris/reviewer.json`
- Modify: `ICDE_2/NEEDS-YOU.md`
- Modify: `ICDE_2/PROJECT-STATUS.md`

**Interfaces:**
- Consumes: completed bridge and route behavior.
- Produces: accurate operator guidance and active-project configuration.

- [x] **Step 1: Document model-pattern and effort semantics**

Document supported aliases, effort levels, reply behavior, environment default,
and the absence of provider-returned actual-effort metadata.

- [x] **Step 2: Inventory manifest-selected checkouts**

List unique `repo_root` values from project manifests without reading sibling
research content, then apply only the route/contract compatibility patch where
the old rejection remains.

- [x] **Step 3: Set ICDE_2 reviewer effort explicitly**

Add top-level `"effort": "high"` to `.aris/reviewer.json` and verify the
project route resolves `opus5.5` plus `high`.

- [x] **Step 4: Run live fresh-process MCP validation**

Call the shared MCP protocol with `model="opus5.5"` and `effort="high"` and
verify the actual model is `claude-opus-5-5`, the requested effort is `high`,
and actual effort remains unknown rather than fabricated.

- [x] **Step 5: Obtain independent Opus 5.5 approval**

Use the canonical identifier `claude-opus-5-5` to review the shared diff with
read-only tools and resolve all concrete findings.

- [x] **Step 6: Update active-project records**

Record the global repair and exact new-session next steps with an
America/Detroit timestamp.

- [x] **Step 7: Commit shared changes without pushing**

Stage only the shared bridge, resolver, contract, tests, spec, and plan. Keep
unrelated untracked files out of the commit.
