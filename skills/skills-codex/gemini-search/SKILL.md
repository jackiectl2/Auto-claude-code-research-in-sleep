---
name: gemini-search
description: Search research papers via Gemini for broad literature discovery. Use when user says "gemini search", "gemini papers", "search with gemini", or wants AI-powered literature discovery beyond arXiv/Semantic Scholar indexes.
argument-hint: "[search-query]"
allowed-tools: Bash(*), Read, Write
---

# Gemini Literature Search

Search query: $ARGUMENTS

## Role & Positioning

This skill uses Gemini as a **broad literature discovery** source:

| Skill | Source | Best for |
|-------|--------|----------|
| `/arxiv` | arXiv API | Latest preprints, cutting-edge unrefereed work |
| `/semantic-scholar` | Semantic Scholar API | Published venue papers (IEEE, ACM, Springer) with citation counts |
| `/deepxiv` | DeepXiv CLI | Layered reading: search, brief, section map, section reads |
| `/exa-search` | Exa API | Broad web search: blogs, docs, news, companies, research papers |
| `/gemini-search` | Gemini CLI | **AI-powered broad literature discovery** — searches across multiple angles, aliases, and sub-problems |

Use Gemini when you want AI-driven discovery that goes beyond keyword matching — Gemini decomposes topics into sub-problems, explores naming variants, and surfaces papers that traditional API searches may miss.

## Constants

- **MAX_RESULTS = 15** — Target number of papers Gemini should find.
- **MIN_YEAR = 2022** — Default minimum publication year. Override with `— year: 2020-`.
- **DEFAULT_MODEL = project switch** — Resolve the project's model before each search. An explicit `— model: <model-id>` request may override it after any required paid-use authorization.

Read the project's `.aris/gemini-search.json` through `tools/resolve_gemini_search_model.py` in the installed ARIS repo. Resolve that repo from `.aris/installed-skills-codex.txt` (`repo_root`); do not use the machine-wide ARIS pointer for a project. Set `PROJECT_ROOT` to the actual project root before calling Gemini. When working from a temporary directory, set `ARIS_PROJECT_ROOT` to that root explicitly; never infer a project or paid model from the temporary directory. Use the resolved `GEMINI_LITERATURE_MODEL` for the CLI call. Stop if resolution fails. `argon_enabled: false` selects upstream `auto-gemini-3`; `true` selects `gemini-4-argon` with project authorization. Projects created before this switch retain the prior Argon default until migrated.

```bash
PROJECT_ROOT=${ARIS_PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null)}
test -f "$PROJECT_ROOT/.aris/installed-skills-codex.txt" || { echo "Set ARIS_PROJECT_ROOT to the actual project root" >&2; exit 2; }
ARIS_REPO=$(awk -F '\t' '$1=="repo_root" {print $2; exit}' "$PROJECT_ROOT/.aris/installed-skills-codex.txt")
test -f "$ARIS_REPO/tools/resolve_gemini_search_model.py" || { echo "Installed ARIS model resolver is missing" >&2; exit 2; }
GEMINI_LITERATURE_MODEL=$(python3 "$ARIS_REPO/tools/resolve_gemini_search_model.py" --project-root "$PROJECT_ROOT") || exit 2
```

> Overrides (append to arguments):
> - `/gemini-search "topic" — max: 20` — request up to 20 papers
> - `/gemini-search "topic" — year: 2020-` — papers from 2020 onward
> - `/gemini-search "topic" — code-only` — only papers with open-source code
> - `/gemini-search "topic" — venues: NeurIPS,ICML,ICLR` — focus on specific venues
> - `/gemini-search "topic" — model: gemini-3-flash-preview` — explicitly use a different model

## Environment & Setup

### Prerequisites

1. **Node.js** v16.0.0+
2. **Google Gemini CLI** — installed and authenticated
   ```bash
   npm install -g @google/gemini-cli
   gemini auth
   ```
The third-party `gemini-mcp-tool` is not required or installed by this workflow. Its current default backend can ignore model selection, while its Gemini CLI backend can retry quota failures with Flash. Neither behavior is acceptable for a project-selected literature model.

### Authentication

Gemini CLI uses your Google account or an API key. Reuse an existing Google account login, or set an API key in the same shell **before starting Codex** so its tool shell inherits it:

```bash
export GEMINI_API_KEY='your-key-here'
codex
```

A separate tool-shell `export` does not update an already running host. If you keep credentials in an environment file, load it explicitly before starting the host rather than relying on automatic `.env` loading.

- Free key from [Google AI Studio](https://aistudio.google.com/apikey)
- Flash model (`gemini-2.5-flash`) has a generous free tier (500 req/min)

### Verify Setup

```bash
gemini --version
```

## Workflow

### Step 1: Parse Arguments

Parse `$ARGUMENTS` for:
- **query**: The research topic (required)
- **max**: Override MAX_RESULTS
- **year**: Minimum publication year (e.g., `2020-`)
- **code-only**: Only include papers with open-source code
- **venues**: Comma-separated venue filter
- **model**: Override DEFAULT_MODEL

### Step 2: Execute Search (Gemini CLI)

Build the search prompt below, substituting the query, year, and result count. Store the complete prompt in `GEMINI_SEARCH_PROMPT`:

```
You are a research literature scout. Search comprehensively for papers on: "QUERY"

IMPORTANT CONSTRAINTS:
1. Search from MULTIPLE angles — do not just use the exact query. Decompose the topic into sub-problems, aliases, neighboring tasks, and common benchmark/settings variants.
2. Prefer papers that are genuinely relevant, not merely keyword-adjacent.
3. Include top venues, journals, surveys, recent preprints, and papers with code when available.
4. Focus on papers from MIN_YEAR onward unless older foundational work is necessary.

For EACH paper found, provide ALL of the following in this exact format:
- Title: [exact title]
- Authors: [full author list]
- Year: [publication year]
- Venue: [exact conference/journal name + year, or "arXiv preprint" if not published]
- arXiv ID: [format 2401.12345, or "N/A"]
- DOI: [if available, or "N/A"]
- Code URL: [GitHub/GitLab link if available, or "No code"]
- Summary: [one-sentence core contribution]

Find at least MAX_RESULTS papers with good coverage across:
- strong recent papers from top venues
- surveys/reviews if they exist
- papers with open-source code
- closely related variants of the topic

Format as a numbered list with all fields for each paper.
```

Run the CLI from the project root with the selected model. Substitute an explicitly requested `— model:` value only after any required paid-use authorization:

```bash
(cd "$PROJECT_ROOT" && gemini -m "$GEMINI_LITERATURE_MODEL" -p "$GEMINI_SEARCH_PROMPT")
```

- **Timeout**: 120 seconds
- **Failure handling**: Keep stderr and check the exit status. On failure, report the error and stop this Gemini source; do not treat empty output as search results. If Gemini CLI reports an untrusted workspace, review and trust this project explicitly. Do not add `--skip-trust` or change global trust settings automatically.

Do not route this project-selected model through the current third-party `gemini-mcp-tool`: its default backend can ignore `model`, and its Gemini backend can silently retry with Flash after a quota error.

### Step 3: Parse Results

Extract structured paper information from Gemini's response. For each paper, normalize to:

```
{
  title, authors, year, venue,
  arxiv_id,    // "N/A" if not available
  doi,         // "N/A" if not available
  code_url,    // "No code" if not available
  summary      // one-sentence contribution
}
```

If Gemini returns fewer papers than requested, note this but do not re-query.

### Step 4: Present Results

Format results as a structured table:

```
| # | Title | Venue | Year | Code | Summary |
|---|-------|-------|------|------|---------|
| 1 | ... | NeurIPS 2024 | 2024 | [GitHub](url) | ... |
| 2 | ... | IEEE TWC | 2023 | No | ... |
```

For each paper, also show:
- **arXiv ID**: if available (for cross-reference with `/arxiv`)
- **DOI**: if available (canonical link for published papers)
- **Code**: GitHub/GitLab link or "No"

### Step 5: Offer Follow-up

After presenting results, suggest:

```text
/semantic-scholar "topic"    — search published venue papers with citation counts
/arxiv "arXiv:XXXX.XXXXX"   — fetch specific preprint details
/research-lit "topic" — sources: gemini, semantic-scholar  — combined multi-source review
/novelty-check "idea"       — verify novelty against literature
```

## Key Rules

- **Use the selected CLI model.** Pass `-m <selected-model>` and check the command result; do not treat another model's output as the selected model's output.
- **Gemini is a discovery source, not a database.** Its results may include papers it "knows about" from training data. Always cross-verify critical details (exact titles, venues, years) via `/semantic-scholar` or `/arxiv` when precision matters.
- **Do not use Gemini for citation counts.** It may hallucinate citation numbers. Use Semantic Scholar for authoritative citation data.
- **Preserve stderr and exit status** so authentication, trust, quota, and model errors remain visible.
- **Timeout generously in CLI mode** — Gemini's thorough search can take 30-60 seconds. Set timeout to 120s.
- If Gemini CLI is unreachable, suggest using `/semantic-scholar`, `/arxiv`, or `/research-lit "topic" — sources: web` as alternatives.
