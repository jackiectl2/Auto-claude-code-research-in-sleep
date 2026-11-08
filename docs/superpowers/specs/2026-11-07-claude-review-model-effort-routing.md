# General Claude Reviewer Model and Effort Routing Specification

## Requirement

The shared `claude-review` route must support current and future versioned
Claude family aliases without one hard-coded entry per release, and must pass
an explicit reviewer effort through ARIS to Claude Code.

## Model contract

- Convert compact versioned aliases for `opus`, `sonnet`, and `haiku` to the
  current Claude Code canonical form. Examples: `opus5.5` becomes
  `claude-opus-5-5`; `opus5.6` becomes `claude-opus-5-6`; and
  `sonnet4.6[1m]` becomes `claude-sonnet-4-6[1m]`.
- Preserve already canonical identifiers and every unrecognized identifier.
- Preserve the caller's original value in `requestedModel`.
- Continue deriving `model` only from Claude Code result metadata.
- Never fall back to another model.
- Future compatibility is limited to the documented family/version naming
  convention; a vendor naming change still requires a bridge update.

## Effort contract

- Accept `effort` on synchronous, reply, asynchronous, and asynchronous reply
  calls, plus `CLAUDE_REVIEW_EFFORT` as the default.
- Accept only Claude Code's documented levels: `low`, `medium`, `high`,
  `xhigh`, and `max`.
- Pass the selected value as `claude --effort <level>` on every invocation,
  including resumed calls and background workers.
- Preserve the caller's value as `requestedEffort`.
- Return actual effort as unknown because Claude Code 2.1.319 result JSON does
  not report it; never copy the request into an actual-effort field.
- Allow `.aris/reviewer.json` and invocation overrides to select Claude effort
  through `tools/reviewer_route.py`.

## Deployment contract

- The central bridge and reviewer contract are the source of truth for new
  projects.
- Existing projects under `ARIS-Auto-Research` must not remain pinned to a
  route that rejects Claude effort; synchronize only the affected shared route
  files in each manifest-selected checkout and record that targeted override.
- No project research content, experiment configuration, or result is changed.

## Validation

- Unit tests cover compact future aliases, canonical pass-through, context
  suffixes, effort validation, explicit/default/reply/async propagation, tool
  schema forwarding, and request-versus-evidence fields.
- Route tests cover accepted and rejected Claude effort levels.
- Live fresh-process MCP calls verify `opus5.5` and explicit `high` effort.
- An independent Opus 5.5 review must approve the completed shared change.
