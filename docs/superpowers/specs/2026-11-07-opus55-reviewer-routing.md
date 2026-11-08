# Opus 5.5 Reviewer Routing Specification

## Requirement

Every Codex project that uses the shared `claude-review` MCP bridge must be
able to request the project-level model alias `opus5.5`. The bridge must pass
Claude Code's accepted canonical identifier, `claude-opus-5-5`, to the CLI.

## Compatibility contract

- Preserve `requestedModel` as the caller-provided value (`opus5.5`).
- Continue deriving `model` only from Claude Code result metadata.
- Apply the mapping to explicit tool arguments and `CLAUDE_REVIEW_MODEL`.
- Leave every other model identifier unchanged.
- Apply the same behavior to synchronous, resumed, and asynchronous reviews.
- Do not add fallback to another model when Opus 5.5 is unavailable.

## Validation

- Unit tests prove command construction maps `opus5.5` and preserves unrelated
  model identifiers.
- Contract tests prove the response retains the requested alias while reporting
  the actual `claude-opus-5-5` model.
- A live no-tools review requested with `opus5.5` must return actual model
  `claude-opus-5-5`.
