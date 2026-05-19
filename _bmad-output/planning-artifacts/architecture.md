---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/prd.md
  - _bmad-output/planning-artifacts/research/technical-campfiresongbookbuilder-quality-review-architecture-and-content-quality-research-2026-05-19.md
  - docs/project-overview.md
  - docs/architecture.md
  - docs/development-guide.md
  - docs/source-tree-analysis.md
  - docs/component-inventory.md
  - _bmad-output/project-context.md
workflowType: 'architecture'
project_name: 'CampfireSongbookBuilder'
user_name: 'Dicky'
date: '2026-05-19'
lastStep: 8
status: 'complete'
completedAt: '2026-05-19'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

The PRD defines 19 functional requirements across six product areas:

- Song quality assessment: detect missing/unusable chords or lyrics, junk markup, duplicate or unreadable content, overlong print-hostile material, and low-confidence song matches.
- Source retry and review workflow: try alternate configured sources before declaring content bad, persist Questionable status with reasons, and exclude Questionable songs from default generated books unless explicitly overridden.
- Easier song addition: validate source-list rows, report what happened for newly added songs, and keep the workflow file/CLI friendly for human and AI-agent assistance.
- Favourites and selections: persist favourite songs and named selections, then apply quality filtering consistently to those subsets.
- Offline generation: generate from local cached/reviewed content without live network access and preserve existing cache compatibility.
- Output pipeline and printable quality: produce inspectable Markdown before `.docx`, preserve `.docx` generation, support an optional PDF path, and prevent obviously bad printable output.

Architecturally, these requirements point to a quality-gated local pipeline rather than a new UI or platform. The key implementation surfaces are source candidate normalization, deterministic quality assessment, persisted quality/review state, selection/favourite filtering, reporting, Markdown rendering, and continued `.docx` output.

**Non-Functional Requirements:**

The driving NFRs are compatibility, offline reliability, inspectability, testability, and implementation simplicity:

- Existing repo-root CLI commands must remain behavior-compatible.
- Cache-first behavior must be preserved, especially for offline generation.
- Existing JSONL caches and exact artist/title cache-key behavior must remain readable.
- External source failures should be isolated and recoverable.
- Review state, quality status, favourites, selections, and reports must use simple local files that are easy for humans and AI agents to inspect.
- Tests must use `unittest` and avoid live websites, Genius credentials, local private config, or brittle `.docx` binary comparisons.
- The project should remain a single-process Python CLI with flat `app/` helper modules unless a specific architectural decision justifies changing that shape.

**Scale & Complexity:**

- Primary domain: local-first Python CLI for content fetching, quality review, and printable document generation.
- Complexity level: medium. The runtime remains small, but quality scoring, source fallback, review-state correctness, and output filtering create meaningful cross-cutting behavior.
- Estimated architectural components: 9 to 11 logical components, mostly implemented as flat helper modules rather than services.

The project has no real-time features, multi-tenancy, hosted deployment, database requirement, collaborative editing, or formal regulatory compliance burden. The main complexity comes from brittle external sources, local file compatibility, quality threshold tuning, stale review decisions after refetching, and ensuring that generation cannot silently include known bad content.

### Technical Constraints & Dependencies

- Python CLI application targeting Python 3.8+.
- Current runtime dependencies include `pandas`, `requests`, `beautifulsoup4`, `lxml`, `lyricsgenius`, and `python-docx`.
- Supported invocation is `python3 main.py ...` from the repository root, with absolute `app.*` imports.
- `main.py` should remain a thin orchestrator; scraper, cache, quality, and document-layout logic belong in helper modules.
- Runtime paths are currently rooted under `data/`: config, source CSV, JSONL caches, and generated outputs.
- Existing sentinel values `"Lyrics not found."` and `"Chords not found."` are compatibility contracts.
- JSONL cache semantics must remain append-safe and tolerant of missing files.
- Generated outputs and private config must stay out of version control.
- There is no active CI workflow on this branch, so local `unittest` verification is the baseline.
- Optional future dependencies such as RapidFuzz, PyYAML, jsonschema, requests-cache, MusicBrainz access, Pandoc, or PDF tools require explicit architecture decisions before adoption.

### Cross-Cutting Concerns Identified

- Cache compatibility: new quality/review behavior must not break existing raw lyrics/chords cache records.
- Content identity and versioning: review decisions should be bound to the content version, likely through content hashes, so stale approvals do not apply silently after refetching.
- Quality signals and thresholds: missing content, junk markup, duplication, length, low-confidence matches, and chord plausibility need deterministic, testable rules.
- Source isolation: source-specific scraping/API logic must stay isolated behind fallback orchestration and normalized candidate records.
- Offline safety: cache-only and generate-from-cache flows must not call network sources.
- Reporting and traceability: generated books should explain included, excluded, missing, and explicitly overridden songs.
- Selection semantics: favourites and named selections must compose cleanly with quality filtering.
- Output pipeline resilience: Markdown and `.docx` artifacts should survive optional PDF conversion failure.
- Testability: quality assessment, state loading, review application, filtering, and CLI branching need focused unit tests with temp files and mocks.
- Agent consistency: architectural decisions must be precise enough that future BMAD story and dev agents preserve the CLI shape, local-file contracts, and quality-first product goal.

## Starter Template Evaluation

### Primary Technology Domain

The primary technology domain is an existing Python CLI application, not a new web, mobile, full-stack, desktop, or service-backed product.

This is a brownfield architecture workflow. The repository already has a working scaffold: `main.py` as the CLI entrypoint, flat helper modules under `app/`, runtime files under `data/`, generated docs under `docs/`, and `unittest` tests under `tests/`. The architecture goal is to preserve that foundation while adding quality-gated songbook behavior.

### Starter Options Considered

**Existing brownfield scaffold**

- Provides the current `argparse` CLI, fixed repo-root execution, flat `app/` module organization, JSONL caches, CSV source list, and `python-docx` output path.
- Best matches project context rules and PRD constraints.
- Avoids replatforming risk and keeps implementation stories small.
- Leaves the product focus on song quality, review state, selections, reports, Markdown, and printable output rather than project bootstrapping.

**Cookiecutter-style Python starters**

- Current Cookiecutter documentation and template directories confirm Cookiecutter remains a general project generator for new projects.
- Rejected for this workflow because generating a fresh scaffold would not preserve this repo's existing CLI contracts, runtime data paths, cache semantics, or helper-module boundaries.

**Typer-based CLI starter**

- Typer remains actively maintained; PyPI listed `typer` 0.24.1 on 2026-02-21 during this review.
- Typer could produce a more modern type-hint-driven CLI, but adopting it now would be a CLI migration rather than a starter decision.
- Rejected for MVP architecture because the current `argparse` CLI is sufficient, and the PRD prioritizes low-intervention quality improvements over CLI ergonomics.

**Click-based CLI starter**

- Click remains actively maintained; PyPI listed `click` 8.3.3 on 2026-04-22 during this review.
- Current Click packaging metadata requires Python >=3.10, while this project targets Python 3.8+.
- Rejected for MVP architecture because it would introduce a dependency and potential Python-version conflict without directly improving songbook quality.

**Modern packaging/project-manager scaffold**

- Python packaging guidance continues to center `pyproject.toml` for build metadata, and Hatch remains a modern Python project manager with project generation, environment, testing, and build features.
- These are useful future packaging options, but packaging is not the first architectural problem.
- Rejected as a starter foundation for MVP because converting the repo to a new package manager/toolchain would broaden the change surface.

### Selected Starter: Existing Brownfield Python CLI Scaffold

**Rationale for Selection:**

The best starter is the repository that already exists. This preserves the working CLI, existing cache files, current source CSV, `python-docx` document generation, and AI-agent rules. It also aligns with the product-owner preference for a high-quality but easy-to-build tool with minimal further intervention.

Using an external starter now would optimize the wrong thing. It would spend architectural energy on scaffolding and migration while the PRD's real risk is content trust: bad chords, bad lyrics, stale review decisions, missing quality gates, and unclear output reports.

**Initialization Command:**

```bash
# No new starter initialization command.
# Continue implementation from the existing repository root.
python3 main.py --generate-from-cache
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**

Python CLI targeting Python 3.8+ with repo-root execution through `python3 main.py ...`.

**Styling Solution:**

No UI styling system. Output quality is document/report formatting, not web or app styling.

**Build Tooling:**

No new build tool. The existing workflow uses direct Python execution and pinned `requirements.txt` dependencies.

**Testing Framework:**

Continue with standard-library `unittest` and run tests from the repository root with:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

**Code Organization:**

Preserve flat helper modules under `app/`. Add new small, single-purpose helpers for quality assessment, state files, selection handling, reports, Markdown rendering, and optional conversion rather than introducing nested packages or a framework.

**Development Experience:**

Prioritize small safe increments, focused regression tests, and inspectable local files. Future packaging modernization can be considered after the quality pipeline is stable, but it is not a prerequisite for the MVP architecture.

**Current-Version Verification Sources:**

- Python Packaging User Guide, `pyproject.toml` specification and guide: https://packaging.python.org/
- Hatch documentation: https://hatch.pypa.io/latest/
- Cookiecutter documentation/template directory: https://www.cookiecutter.io/
- Typer PyPI release history: https://pypi.org/project/typer/
- Click PyPI release metadata: https://pypi.org/project/click/

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**

- Preserve the existing Python CLI brownfield scaffold.
- Add quality-gated local state beside existing caches instead of replacing cache records.
- Store raw fetched content, quality status, review decisions, source attempts, favourites/selections, reports, Markdown, and `.docx` as separate local artifacts.
- Treat Questionable content as excluded from default generated books unless explicitly accepted or overridden.
- Keep online fetch/cache behavior separate from offline generation behavior.
- Bind review decisions to content hashes so stale approvals do not silently apply after refetch.

**Important Decisions (Shape Architecture):**

- Use deterministic quality rules first; optional fuzzy matching or metadata enrichment can be added after baseline quality gates exist.
- Generate Markdown as an inspectable intermediate before `.docx`.
- Keep PDF conversion optional and non-destructive.
- Use small flat helper modules under `app/` rather than introducing a framework, nested package tree, database, or service layer.
- Treat Python 3.12 as the verified development runtime for the upgrade; do not spend effort preserving Python 3.8 behavior because Python 3.8 is end-of-life per the Python Developer's Guide.

**Deferred Decisions (Post-MVP):**

- Full package-manager migration to Hatch, Poetry, uv, or another project manager.
- Typer/Click CLI migration.
- YAML selections, unless JSON proves too awkward for human editing.
- jsonschema validation, unless hand validation becomes brittle.
- RapidFuzz or MusicBrainz enrichment, unless deterministic title/artist matching is insufficient.
- requests-cache, unless external-source traffic becomes a real problem beyond existing content caches.
- Pandoc/PDF pipeline selection, until Markdown and `.docx` output are stable.
- Hosted service, GUI, user accounts, authentication, collaborative editing, and cloud deployment.

### Data Architecture

**Decision: Use local files, not a database.**

The application remains a local-first CLI with file-based state. No SQLite, server database, document database, or hosted persistence is introduced for MVP.

**Rationale:**

The song library is human-scale, local, and agent-editable. A database would reduce inspectability and add migration/testing overhead without solving the main product risk: content quality.

**Decision: Preserve existing JSONL raw caches.**

Existing `data/cache/lyrics_cache.jsonl` and `data/cache/chords_cache.jsonl` remain the raw fetched-content stores. Existing artist/title fields, exact cache-key semantics, sentinel values, and append-safe JSONL behavior are compatibility contracts.

**Decision: Add separate quality and review state files.**

Add current-state files beside, not inside, raw caches:

- `data/review/quality_status.json`
- `data/review/review_decisions.json`
- `data/review/source_attempts.jsonl`
- `data/review/reports/*.json`
- `data/selections/favourites.json`
- `data/selections/*.json`

`source_attempts.jsonl` is append-only audit/history. `quality_status.json` and `review_decisions.json` are current-state files optimized for generation reads.

**Decision: Use content hashes for version binding.**

Quality status and review decisions must include a stable content hash, using `hashlib.sha256` or equivalent. If content changes after refetch, old review decisions no longer apply automatically.

**Decision: Use JSON first for new state.**

JSON is the default for review, status, reports, favourites, and selections because it is standard-library, machine-readable, and easy for AI agents to edit. YAML is deferred unless human-editing comfort becomes more important than dependency minimization.

**Decision: Validate with small explicit loaders first.**

Each new state file gets focused load/validate helpers. jsonschema is deferred until the schemas become large enough that hand validation is riskier than the dependency.

**Verified versions/options:**

- Python Developer's Guide lists Python 3.8 as end-of-life on 2024-10-07.
- `python-docx` remains available on PyPI, with 1.2.0 visible during this review.
- Pandas remains active on PyPI, with 3.0.1 visible during this review, but no pandas upgrade is required for the architecture.
- RapidFuzz remains active on PyPI, with 3.14.5 visible during this review, but adoption is deferred.
- jsonschema remains active on PyPI, with 4.26.0 visible during this review, but adoption is deferred.

### Authentication & Security

**Decision: No authentication or authorization system for MVP.**

This is a local CLI. There are no user accounts, sessions, roles, hosted APIs, or multi-user permissions in scope.

**Decision: Keep secrets local and out of artifacts.**

`data/config/config.json` remains private and ignored. API tokens must not be written to caches, source-attempt logs, quality reports, Markdown, `.docx`, PDF, or console summaries.

**Decision: Treat fetched content as untrusted text.**

Lyrics/chords from external sources must be cleaned or escaped before Markdown or `.docx` rendering. The application must not execute source content or preserve embedded HTML/script-like artifacts as trusted markup.

**Decision: External metadata APIs must identify and rate-limit.**

If MusicBrainz is added later, requests must use a meaningful User-Agent and respect the documented default one-request-per-second IP limit. Metadata enrichment must remain optional and must not run during offline generation.

### API & Communication Patterns

**Decision: No public API layer.**

The architecture uses local function calls and file contracts, not REST, GraphQL, RPC, WebSockets, queues, or background workers.

**Decision: Normalize source outputs before quality assessment.**

Source-specific functions should return or be wrapped into Candidate records with requested artist/title, source name, content type, content, source-returned metadata when available, status, error, and retrieval timestamp.

**Decision: Keep source failures recoverable and structured.**

Source adapters should return `candidate`, `not_found`, or `error` outcomes rather than letting one broken site crash the whole run when fallback sources remain.

**Decision: Reports are the communication surface.**

Each generation run should produce human-readable console/file output and machine-readable report data describing included, excluded, missing, Questionable, and explicitly overridden songs.

### Frontend Architecture

**Decision: No frontend architecture for MVP.**

The PRD explicitly excludes a GUI. There is no component model, routing, client-side state management, responsive design, animation, or web accessibility architecture to decide.

**Decision: Treat Markdown/report output as the user-facing inspection surface.**

Markdown songbooks and review reports are the primary low-intervention way for the user and AI agents to inspect quality before printing.

### Infrastructure & Deployment

**Decision: Local execution only.**

There is no hosting platform, server deployment, container strategy, cloud account, or multi-environment infrastructure in MVP.

**Decision: Keep verification local and `unittest`-based.**

The baseline verification command remains:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Tests must avoid live external websites, Genius credentials, private local config, local cache assumptions, and binary `.docx` comparisons.

**Decision: Use standard-library logging.**

`main.py` owns CLI logging configuration. Helper modules use module loggers and return structured outcomes where practical.

**Decision: CI is useful but not required for architecture MVP.**

GitHub Actions or another CI workflow can be added later as a quality improvement, but it is not required before the quality pipeline stories begin.

### Decision Impact Analysis

**Implementation Sequence:**

1. Reconcile documented Python/runtime expectations with the verified development baseline.
2. Add data contracts and loaders for Candidate, Quality Signal, Quality Status, Review Decision, Source Attempt, Favourite, and Selection.
3. Add pure quality assessment helpers for missing content, junk markup, duplicate blocks, overlong content, low-confidence matches, and chord plausibility.
4. Add source-attempt recording around existing source fallback functions.
5. Add review-decision application with content-hash validation.
6. Add selection/favourite loading and malformed-entry reporting.
7. Add generation filtering that excludes Questionable songs by default.
8. Add machine-readable and human-readable quality reports.
9. Add Markdown songbook output.
10. Preserve `.docx` output from accepted content.
11. Add optional PDF conversion only after Markdown and `.docx` are stable.

**Cross-Component Dependencies:**

- Quality filtering depends on stable content identity, quality status, and review decisions.
- Review decisions depend on content hashing and raw cache compatibility.
- Offline generation depends on strict separation between source adapters and renderers.
- Selections/favourites depend on the same song-key semantics as caches.
- Markdown and `.docx` renderers must consume accepted content rather than making quality decisions.
- Reports depend on quality signals, review decisions, and generation filtering sharing consistent reason codes.
- Any later dependency adoption must preserve simple local execution and focused `unittest` coverage.

**Current-Version Verification Sources:**

- Python Developer's Guide, Status of Python versions: https://devguide.python.org/versions/
- python-docx on PyPI: https://pypi.org/project/python-docx/
- pandas on PyPI: https://pypi.org/project/pandas/
- RapidFuzz on PyPI: https://pypi.org/project/RapidFuzz/
- jsonschema on PyPI: https://pypi.org/project/jsonschema/
- MusicBrainz API and rate limiting docs: https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 12 areas where AI agents could otherwise make incompatible choices:

- Song identity keys
- JSON/JSONL field names
- New state file locations
- Quality signal codes and severities
- Review decision semantics
- Source adapter return shapes
- Offline-vs-online behavior
- Report formats
- Markdown output structure
- `.docx` rendering boundaries
- Error handling/logging
- Test placement and mocking style

### Naming Patterns

**Database Naming Conventions:**

No database is used in MVP. Agents must not introduce table, migration, ORM, or database naming conventions unless a future architecture decision explicitly adds a database.

**API Naming Conventions:**

No public API is used in MVP. Agents must not introduce REST, GraphQL, route, request, response, or status-code conventions for internal behavior. Internal communication uses Python data structures and local files.

**Code Naming Conventions:**

- Python files: lowercase with underscores, e.g. `quality_assessment.py`, `review_state.py`, `selection_state.py`.
- Functions and variables: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Data field names in JSON/JSONL: `snake_case`.
- Song key field: `song_key`.
- Content type values: `lyrics` and `chords`.
- Quality values: `clean`, `questionable`, `missing`.
- Review decision values: `accept`, `reject`, `override`.
- Source outcome values: `candidate`, `not_found`, `error`.

Song identity must preserve exact existing `artist` and `title` cache fields. Derived keys use the existing display form:

```text
Artist - Title
```

Do not globally normalize artist/title values for cache lookup. Normalized variants may be computed for matching, but they must not replace original cache identity.

### Structure Patterns

**Project Organization:**

- Keep `main.py` as CLI orchestration only.
- Keep application code in flat `app/*.py` helper modules.
- Add new behavior as small modules under `app/`, not nested packages.
- Keep tests in `tests/test_*.py`.
- Keep generated BMAD artifacts under `_bmad-output/`.
- Keep runtime input/state/output under `data/`.

Recommended new modules:

- `app/content_models.py`: lightweight constructors/validators for Candidates, Quality Signals, Quality Status, Review Decisions, Source Attempts, and Selections.
- `app/quality_assessment.py`: pure quality checks and scoring.
- `app/review_state.py`: load/write quality status and review decisions.
- `app/selection_state.py`: load/write favourites and selections.
- `app/reporting.py`: generation quality reports.
- `app/markdown_generation.py`: Markdown songbook rendering.
- `app/output_pipeline.py`: orchestration from accepted content to Markdown, `.docx`, and optional PDF.

Agents may adjust exact module names only if they keep the same flat-module shape and document the reason in the story implementation notes.

**File Structure Patterns:**

New runtime files use these locations:

```text
data/review/quality_status.json
data/review/review_decisions.json
data/review/source_attempts.jsonl
data/review/reports/*.json
data/selections/favourites.json
data/selections/*.json
data/output/*.md
data/output/*.docx
data/output/*.pdf
```

Helpers that write these files must create parent directories before saving. Generated reports and outputs must not be assumed to exist.

### Format Patterns

**API Response Formats:**

Not applicable. Internal source adapters should still return structured result dictionaries or dataclass-like dictionaries with these fields where relevant:

```json
{
  "artist": "requested artist",
  "title": "requested title",
  "song_key": "Artist - Title",
  "content_type": "lyrics",
  "source": "genius",
  "content": "candidate text",
  "source_artist": "artist from source",
  "source_title": "title from source",
  "status": "candidate",
  "error": null,
  "retrieved_at": "2026-05-19T10:00:00+01:00"
}
```

**Data Exchange Formats:**

- JSON files use top-level objects, not bare arrays, so schema metadata can be added later.
- JSONL files use one valid JSON object per line.
- Datetimes use ISO-8601 strings with timezone when practical.
- Content hashes use the format `sha256:<hex>`.
- Missing optional string metadata should be `null`, not empty strings, unless the field is existing cache content.
- Existing sentinel content values `"Lyrics not found."` and `"Chords not found."` must remain recognized.

Quality signal shape:

```json
{
  "code": "missing_chords",
  "severity": "error",
  "message": "Chords are missing or unusable.",
  "content_type": "chords"
}
```

Severity values:

- `info`: useful trace information
- `warning`: questionable but potentially usable
- `error`: exclude by default

Review decision shape:

```json
{
  "song_key": "Artist - Title",
  "content_type": "chords",
  "content_hash": "sha256:...",
  "decision": "accept",
  "reason": "Manually reviewed and playable.",
  "decided_at": "2026-05-19T10:00:00+01:00"
}
```

### Communication Patterns

**Event System Patterns:**

No event bus is used. Source attempts provide append-only audit history but must not become event-sourced application state. Generation reads current-state files, not reconstructed event streams.

**State Management Patterns:**

- Raw content state lives in existing JSONL caches.
- Current quality state lives in `quality_status.json`.
- User intent lives in `review_decisions.json`, `favourites.json`, and selection files.
- Source history lives in `source_attempts.jsonl`.
- Generated reports are snapshots of a run and must not be the source of truth for future generation.

### Process Patterns

**Error Handling Patterns:**

- Source/network failures return structured `error` or `not_found` outcomes when fallback can continue.
- File validation errors for user-editable state should be collected and reported with file path, field, and reason.
- Offline generation must fail/report if required local state is missing, but must not call source adapters.
- Optional PDF conversion failure must not delete Markdown or `.docx` artifacts.
- Helper modules log operational details with `logging.getLogger(__name__)`.
- `main.py` remains responsible for CLI-level logging configuration and top-level exits.

**Loading State Patterns:**

There is no UI loading state. CLI progress should be concise and stable. Long-running operations should log source attempts and write reports rather than relying on transient console output.

### Enforcement Guidelines

**All AI Agents MUST:**

- Preserve repo-root execution with `python3 main.py ...`.
- Preserve exact `artist` and `title` cache identity.
- Keep existing JSONL caches backward-compatible.
- Keep network calls out of offline generation.
- Keep source-specific parsing out of `main.py`, quality assessment, review-state loading, and renderers.
- Keep quality assessment pure enough to unit test without network, files, or `python-docx`.
- Bind review decisions to content hashes.
- Use `unittest`, `tempfile`, and `unittest.mock` for regression tests.
- Record any intentional change to runtime paths, cache shape, sentinels, or CLI behavior in the story notes and tests.

**Pattern Enforcement:**

- Run `python3 -m unittest discover -s tests -p 'test_*.py'` after application changes.
- Add focused tests for any changed cache, state, quality, filtering, or generation behavior.
- Treat deviations from this document as architecture changes, not local implementation preferences.
- Update this architecture document or `_bmad-output/project-context.md` when a new durable rule is established.

### Pattern Examples

**Good Examples:**

```python
song_key = f"{artist} - {title}"
```

```json
{
  "song_key": "Oasis - Wonderwall",
  "content_type": "chords",
  "quality": "questionable",
  "signals": [
    {"code": "low_title_match", "severity": "warning", "message": "Source title differs."}
  ]
}
```

```text
tests/test_quality_assessment.py
tests/test_review_state.py
tests/test_generation_filtering.py
```

**Anti-Patterns:**

- Rewriting `artist` or `title` globally to normalized forms.
- Adding a database to store review decisions.
- Making `--generate-from-cache` call source adapters.
- Hiding quality decisions inside `app/document_creation.py`.
- Writing API tokens into source-attempt records.
- Comparing generated `.docx` files as binary blobs in tests.
- Adding pytest-only tests without an explicit test-framework migration.
- Replacing `"Lyrics not found."` or `"Chords not found."` without updating all affected readers, reports, and tests.

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
CampfireSongbookBuilder/
├── README.md
├── LICENSE
├── requirements.txt
├── .flake8
├── .gitignore
├── main.py
├── app/
│   ├── __init__.py
│   ├── cache.py
│   ├── content_models.py              # new: shared local data contracts
│   ├── document_creation.py
│   ├── document_formatting.py
│   ├── document_generation.py
│   ├── fetch_data.py
│   ├── generation_filtering.py        # new: include/exclude accepted content
│   ├── load_config.py
│   ├── load_songs.py
│   ├── markdown_generation.py         # new: inspectable songbook output
│   ├── output_pipeline.py             # new: Markdown -> docx -> optional PDF orchestration
│   ├── quality_assessment.py          # new: pure deterministic content checks
│   ├── reporting.py                   # new: quality/generation reports
│   ├── review_state.py                # new: quality status and review decisions
│   ├── selection_state.py             # new: favourites and named selections
│   ├── song_info.py
│   └── text_cleaning.py
├── data/
│   ├── cache/
│   │   ├── chords_cache.jsonl
│   │   └── lyrics_cache.jsonl
│   ├── config/
│   │   ├── config.example.json
│   │   └── config.json                # ignored local private config
│   ├── output/
│   │   ├── *.md                       # generated Markdown songbooks
│   │   ├── *.docx                     # generated Word songbooks
│   │   └── *.pdf                      # optional generated PDFs
│   ├── review/
│   │   ├── quality_status.json        # generated current quality state
│   │   ├── review_decisions.json      # user-editable decisions
│   │   ├── source_attempts.jsonl      # generated append-only audit history
│   │   └── reports/
│   │       └── *.json                 # generated per-run reports
│   ├── selections/
│   │   ├── favourites.json            # user-editable favourite songs
│   │   └── *.json                     # user-editable named selections
│   └── src/
│       └── CampfireSongs.csv
├── docs/
│   ├── index.md
│   ├── project-overview.md
│   ├── architecture.md
│   ├── development-guide.md
│   ├── source-tree-analysis.md
│   └── component-inventory.md
├── tests/
│   ├── test_config.py
│   ├── test_content_models.py         # new
│   ├── test_generation_filtering.py   # new
│   ├── test_markdown_generation.py    # new
│   ├── test_quality_assessment.py     # new
│   ├── test_reporting.py              # new
│   ├── test_review_state.py           # new
│   └── test_selection_state.py        # new
├── _bmad-output/
│   ├── project-context.md
│   └── planning-artifacts/
│       └── architecture.md
├── clean_chords_cache.py
├── clean_chords_cache_brackets.py
├── fix_mojibake_in_cache.py
└── migrate_cache_to_jsonl.py
```

New files marked `new` are architectural target locations. They should be introduced incrementally by implementation stories when the relevant behavior is built.

### Architectural Boundaries

**API Boundaries:**

There are no public API boundaries. External communication occurs only through source-specific HTTP/API calls in `app/fetch_data.py` or future source adapter helpers. All external source results must be normalized before quality assessment.

**Component Boundaries:**

- `main.py`: parse CLI arguments, load config/song list, select workflow, call orchestration helpers.
- `app/fetch_data.py`: external source calls and scraper-specific parsing.
- `app/document_generation.py`: cache population workflows.
- `app/cache.py`: JSONL cache read/write behavior.
- `app/quality_assessment.py`: pure quality checks; no network, no file writes, no document rendering.
- `app/review_state.py`: load/write quality status and review decisions.
- `app/selection_state.py`: load/write favourites and named selections.
- `app/generation_filtering.py`: combine cached content, quality status, review decisions, and selections into accepted/excluded sets.
- `app/reporting.py`: build machine-readable and human-readable quality/generation reports.
- `app/markdown_generation.py`: render accepted content to Markdown.
- `app/document_creation.py` and `app/document_formatting.py`: preserve `.docx` generation and formatting responsibilities.
- `app/output_pipeline.py`: coordinate Markdown, `.docx`, and optional PDF output once content has already been accepted.

**Service Boundaries:**

No services are introduced. Module boundaries are the architectural boundaries.

**Data Boundaries:**

- Raw source content boundary: `data/cache/*.jsonl`.
- User source-list boundary: `data/src/CampfireSongs.csv`.
- Review/current-state boundary: `data/review/*.json`.
- Audit/history boundary: `data/review/source_attempts.jsonl`.
- Selection boundary: `data/selections/*.json`.
- Generated artifact boundary: `data/output/*`.

### Requirements to Structure Mapping

**Feature Mapping:**

- FR-1 through FR-4, Song Quality Assessment:
  - `app/quality_assessment.py`
  - `app/content_models.py`
  - `tests/test_quality_assessment.py`
  - `tests/test_content_models.py`

- FR-5 through FR-7, Source Retry and Review Workflow:
  - `app/fetch_data.py`
  - `app/document_generation.py`
  - `app/review_state.py`
  - `app/generation_filtering.py`
  - `app/reporting.py`
  - `data/review/quality_status.json`
  - `data/review/review_decisions.json`
  - `data/review/source_attempts.jsonl`
  - `tests/test_review_state.py`
  - `tests/test_generation_filtering.py`

- FR-8 through FR-10, Easier Song Addition:
  - `app/load_songs.py`
  - `app/reporting.py`
  - `main.py` CLI orchestration
  - `tests/test_reporting.py`

- FR-11 through FR-13, Favourites and Selections:
  - `app/selection_state.py`
  - `app/generation_filtering.py`
  - `data/selections/favourites.json`
  - `data/selections/*.json`
  - `tests/test_selection_state.py`
  - `tests/test_generation_filtering.py`

- FR-14 through FR-15, Offline Generation:
  - `main.py`
  - `app/cache.py`
  - `app/generation_filtering.py`
  - `app/output_pipeline.py`
  - tests that assert source adapters are not called in offline modes

- FR-16 through FR-19, Output Pipeline and Printable Quality:
  - `app/markdown_generation.py`
  - `app/output_pipeline.py`
  - `app/document_creation.py`
  - `app/document_formatting.py`
  - `data/output/*.md`
  - `data/output/*.docx`
  - `data/output/*.pdf`
  - `tests/test_markdown_generation.py`

**Cross-Cutting Concerns:**

- Cache compatibility: `app/cache.py`, `app/generation_filtering.py`, cache-related tests.
- Content hashing: `app/content_models.py` or `app/review_state.py`.
- Logging: `main.py` plus module-level loggers.
- Validation: `app/content_models.py`, `app/review_state.py`, `app/selection_state.py`.
- Reports: `app/reporting.py`, `data/review/reports/*.json`.
- CLI compatibility: `main.py` and targeted CLI branch tests where practical.

### Integration Points

**Internal Communication:**

Data flows through plain Python dictionaries/dataclass-like records:

```text
CampfireSongs.csv
  -> load_songs
  -> fetch/cache workflows
  -> Candidate records
  -> quality_assessment
  -> quality_status/review_decisions
  -> selection_state
  -> generation_filtering
  -> reporting
  -> markdown_generation
  -> document_creation/document_formatting
  -> optional PDF conversion
```

**External Integrations:**

- Genius through `lyricsgenius` and private local config.
- Lyrics/chord websites through `requests` and BeautifulSoup/lxml scraping in source-specific helpers.
- Optional MusicBrainz metadata confidence checks after a future architecture/story decision.
- Optional Pandoc or another converter for PDF after Markdown and `.docx` are stable.

**Data Flow:**

Online fetch/cache mode may call external sources and write raw caches, source attempts, quality status, and reports. Offline generation mode reads local caches, quality/review state, and selections, then writes reports and output artifacts without network calls.

### File Organization Patterns

**Configuration Files:**

- `requirements.txt`: pinned runtime dependencies.
- `.flake8`: style constraints.
- `data/config/config.example.json`: tracked config template.
- `data/config/config.json`: ignored private local config.

**Source Organization:**

Application modules remain flat under `app/`. New modules should be small and responsibility-focused. Do not move scraper logic, document formatting, or cache mechanics into `main.py`.

**Test Organization:**

Tests live in `tests/test_*.py` and use `unittest`. Use `tempfile.TemporaryDirectory` for local state and `unittest.mock` for source/network isolation.

**Asset Organization:**

There are no static UI assets. Runtime content and generated artifacts live under `data/`.

### Development Workflow Integration

**Development Server Structure:**

No development server. Run commands from the repository root with `python3 main.py ...`.

**Build Process Structure:**

No build process for MVP. Document generation is the runtime output process.

**Deployment Structure:**

No deployment structure for MVP. The product is a local CLI. Future packaging, CI, or release workflows can be added after the quality pipeline is stable.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**

The decisions are compatible. The selected brownfield Python CLI scaffold supports the local-file data architecture, additive review state, deterministic quality assessment, offline generation, Markdown-first output, and continued `.docx` generation. No selected decision requires a database, web server, frontend framework, hosted infrastructure, authentication system, or major CLI rewrite.

The only deliberate tension is the legacy README/project-context claim of Python 3.8+ support versus the 2026 reality that Python 3.8 is end-of-life. The architecture resolves this by treating Python 3.12 as the verified development runtime and by avoiding new work to preserve 3.8 behavior. This should be reconciled in documentation or project context during implementation.

**Pattern Consistency:**

The naming, structure, data-format, error-handling, logging, and test patterns all support the core decisions. The patterns preserve exact cache identity, isolate source adapters, keep quality checks pure, bind review decisions to content hashes, and prevent offline generation from reaching network code.

**Structure Alignment:**

The proposed structure maps each new responsibility to a flat `app/*.py` helper module while preserving existing module boundaries. Runtime state is placed under `data/` with clear separation between raw caches, review state, source-attempt history, selections, reports, and generated artifacts.

### Requirements Coverage Validation ✅

**Epic/Feature Coverage:**

No epics were loaded. The architecture maps all PRD feature categories directly to modules, state files, and tests.

**Functional Requirements Coverage:**

- FR-1 through FR-4 are covered by `quality_assessment.py`, quality signals, content hashes, and quality status.
- FR-5 through FR-7 are covered by source-attempt recording, source fallback boundaries, review decisions, and generation filtering.
- FR-8 through FR-10 are covered by source-list validation, reports, file/CLI operation, and agent-editable local state.
- FR-11 through FR-13 are covered by favourites/selections state and quality-aware filtering.
- FR-14 through FR-15 are covered by cache-first reads, offline generation boundaries, and cache compatibility rules.
- FR-16 through FR-19 are covered by Markdown output, preserved `.docx` generation, optional PDF conversion, and print-quality signals.

**Non-Functional Requirements Coverage:**

- CLI compatibility is preserved by keeping `main.py` as the entrypoint and avoiding a starter rewrite.
- Offline behavior is protected by separating source adapters from generation.
- Source failures are recoverable through structured outcomes and source attempts.
- Inspectability is addressed with JSON/JSONL state and Markdown output.
- Testability is addressed with pure quality helpers, file loaders, mocks, and `unittest`.
- Implementation simplicity is addressed by preserving the single-process CLI and flat module structure.
- Security is addressed by keeping secrets local, avoiding token leakage, and treating fetched content as untrusted text.

### Implementation Readiness Validation ✅

**Decision Completeness:**

Critical decisions are documented with rationale and current-version checks where technology versions matter. Deferred decisions are explicit and do not block the quality pipeline.

**Structure Completeness:**

The project tree identifies existing files, proposed new modules, proposed runtime state files, test locations, and boundary ownership. It is specific enough for story creation and implementation agents.

**Pattern Completeness:**

The main AI-agent conflict points are addressed: song keys, JSON field naming, state locations, quality signals, review decisions, source outcomes, offline behavior, reports, Markdown rendering, `.docx` boundaries, logging, validation, and tests.

### Gap Analysis Results

**Critical Gaps: None.**

No missing architectural decision blocks implementation.

**Important Gaps:**

- Python baseline documentation needs reconciliation because Python 3.8 is end-of-life while existing docs mention Python 3.8+.
- Initial quality thresholds must be tuned against real cache samples during implementation.
- PDF conversion remains intentionally optional and needs a later concrete converter decision.

**Nice-to-Have Gaps:**

- Add CI after the test suite grows beyond the current minimal baseline.
- Consider RapidFuzz if deterministic title/artist matching is too weak.
- Consider jsonschema if hand validation becomes too scattered.
- Consider packaging modernization after the core quality workflow works.

### Validation Issues Addressed

- Avoided starter/template churn by selecting the existing brownfield scaffold.
- Avoided cache breakage by placing quality/review state beside raw caches.
- Avoided stale manual approvals by requiring content hashes on review decisions.
- Avoided network surprises by making offline generation a hard boundary.
- Avoided over-scoping by deferring GUI, hosted service, auth, database, CLI framework migration, packaging migration, and optional PDF tooling.

### Architecture Completeness Checklist

**Requirements Analysis**

- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**

- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**

- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**

- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**

- Strong alignment with the existing codebase and project context.
- Clear quality-first path without a rewrite.
- Explicit local file contracts for review, quality, selections, and reports.
- Preserves offline generation and existing caches.
- Gives future agents concrete module boundaries and anti-patterns.

**Areas for Future Enhancement:**

- Tune quality thresholds with real song/cache examples.
- Add CI once more regression tests exist.
- Decide optional PDF conversion tooling after Markdown and `.docx` are stable.
- Consider packaging/runtime modernization after MVP quality features are implemented.

### Implementation Handoff

**AI Agent Guidelines:**

- Follow all architectural decisions exactly as documented.
- Use implementation patterns consistently across all components.
- Respect project structure and boundaries.
- Refer to this document for all architectural questions.
- Preserve cache compatibility and offline behavior unless a future architecture change explicitly says otherwise.

**First Implementation Priority:**

Start with the architectural foundation story: reconcile Python/runtime documentation, define shared content/state contracts, add state loaders, and add focused `unittest` coverage before wiring quality filtering into document generation.
