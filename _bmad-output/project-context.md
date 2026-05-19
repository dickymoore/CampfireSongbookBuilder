---
project_name: 'CampfireSongbookBuilder'
user_name: 'Dicky'
date: '2026-05-17'
sections_completed: ['technology_stack', 'language_rules', 'application_orchestration_rules', 'testing_rules', 'code_quality_style_rules', 'development_workflow_rules', 'critical_dont_miss_rules']
existing_patterns_found: 12
status: 'complete'
rule_count: 61
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- Python CLI application targeting Python 3.8+ per README; current local verification used Python 3.12.3.
- Runtime dependencies are pinned in `requirements.txt`: beautifulsoup4 4.12.3, certifi 2024.6.2, charset-normalizer 3.3.2, lxml 5.2.2, oauthlib 3.2.2, pandas 2.2.2, python-dateutil 2.9.0.post0, python-docx 1.1.2, pytz 2024.1, requests 2.32.3, requests-oauthlib 2.0.0, six 1.16.0, urllib3 2.2.2, lyricsgenius 3.0.1.
- Code quality config is `.flake8` with `max-line-length = 100` and exclusions for `venv`, `__pycache__`, `data`, and `output`.
- Tests use Python `unittest`; current suite contains `tests/test_config.py`.
- There is no active `.github/workflows` CI configuration on this branch.
- Runtime data paths are fixed in code: `data/config/config.json`, `data/src/CampfireSongs.csv`, `data/cache/*.jsonl`, and `data/output/*.docx`.

## Critical Implementation Rules

### Language-Specific Rules

- Use absolute imports from `app.*` because the supported entrypoint is `python3 main.py` from the repository root. Do not change to package-relative imports unless you update the entrypoint, tests, and invocation docs together.
- Preserve the flat `app/` module layout. Add small, single-purpose application helpers as `app/*.py` by default; do not add nested packages without updating imports, entrypoint behavior, and tests.
- Use standard-library `logging` for operational messages. `main.py` owns CLI logging configuration; helper modules should define `logger = logging.getLogger(__name__)` unless the surrounding file already uses `logging.*`. Keep existing intentional user-facing print summaries only where appropriate.
- Respect the current runtime path contract. `main.py` defines fixed runtime paths, while some helpers still reference `data/cache/*.jsonl` directly; path changes must update cache access, fetch flow, document generation, and tests together.
- Do not introduce new hardcoded runtime paths outside `main.py`. Existing hardcoded `data/cache/*.jsonl` paths may only move in a coordinated refactor covering cache, fetch, document generation, and tests.
- Treat scraper/network failures as recoverable unless the caller explicitly requires hard failure. Preserve the existing fallback behavior, sentinel/fallback values, and cache semantics when changing fetch code.
- Cleaning functions must tolerate `None` and non-string lyric/chord inputs, returning `''` instead of raising unless a specific caller requires validation.
- Use `unittest` for tests and keep style compatible with `.flake8` max-line-length `100`. Keep tests executable with the existing `unittest` setup before introducing another test framework.
- Verify import-sensitive changes from the repository root with `python3 main.py` or targeted import tests that preserve `from app...` imports. Do not assume `python -m app...` semantics.
- Preserve JSONL cache semantics under `data/cache`; changes to cache records require reader/writer test updates in the same change.

### Application Orchestration Rules

- This project has no web framework. Treat the application framework as the CLI orchestration, cache-first scraper flow, JSONL persistence, and `python-docx` document generation pipeline.
- Keep `main.py` as a thin CLI orchestration layer. It may parse arguments, load config/song data, select the requested workflow, and call helpers under `app/`; it must not contain scraper parsing, HTTP request logic, JSONL persistence mechanics, or document-layout logic.
- CLI modes must remain behavior-compatible when run from the repository root: `--cache-only`, `--generate-from-cache`, `--lyrics-only`, `--chords-only`, `--get-song-info`, and `--test-api`. Any change touching these paths should include focused test coverage or explicit manual smoke results.
- Keep command outputs and exit behavior stable for automation. Status text, errors, and generated file paths are part of the CLI experience; avoid changing them unless the workflow intentionally changes.
- Preserve cache-first semantics for fetch and reporting paths. Read JSONL caches before network calls, and make any intentional increase in external requests explicit in code or docs.
- Keep JSONL cache handling append-safe and tolerant of missing files. Maintain one record per line, avoid rewriting unrelated cache entries, and treat absent cache files as empty caches.
- Treat cached JSONL records and song input structures as compatibility contracts. Changes to field names, normalization, or record shape should include migration or backward-compatible reading.
- Keep source-specific scraping isolated behind helper functions/modules. New lyric or chord sources should be added as separate source helpers and composed through the existing fallback entry points, unless a broader source registry is introduced deliberately.
- Source failures should be isolated, logged/reported, and should not prevent later configured sources from being attempted.
- Document generation currently uses `python-docx` and writes `.docx` files under `data/output`; ensure output directories exist before saving.
- Keep `python-docx` formatting concerns inside document-generation helpers; callers should pass song/book data and output intent, not manipulate document internals.
- Resolve project data paths consistently from the repository root or a configured data directory; avoid introducing current-working-directory assumptions outside CLI entry points.

### Testing Rules

- Use `unittest` unless the project explicitly migrates test frameworks. Put tests in `tests/` and name files `test_*.py`.
- Run the suite from the repository root with `python3 -m unittest discover -s tests -p 'test_*.py'`. The codebase uses absolute `app.*` imports that assume the repo root is on the Python path.
- Keep test files compatible with `.flake8` max-line-length `100`.
- Prefer focused unit tests for pure helpers and boundary behavior, especially config loading, CSV skip filtering, text cleaning, sorting, JSONL cache semantics, scraper fallback decisions, CLI mode branching, and document-generation decisions.
- Keep fixtures small and local to the test: inline rows/records, `tempfile` paths, `TemporaryDirectory`, and minimal config dictionaries are preferred over large checked-in fixtures.
- Do not make live network calls in unit tests. Mock HTTP, scraper source helpers, source selection, and fallback orchestration with controlled return values.
- For JSONL cache changes, cover missing files, malformed lines when relevant, update-vs-append behavior, and preservation of unrelated records.
- For `python-docx` generation changes, assert observable document structure, expected text, style decisions, or saved output behavior where practical; avoid brittle binary `.docx` comparisons.
- For CLI mode changes, add automated coverage for the affected branch where practical. If manual smoke testing is used, record the exact command and expected result run from the repository root.
- Any change touching cache semantics, config loading, scraper fallback flow, CLI dispatch, or document generation should include at least one regression test that fails on the old behavior or clearly document why manual verification is sufficient.
- Do not add pytest-only fixtures, assertions, markers, or snapshot testing unless the project intentionally adopts pytest or document generation complexity justifies that machinery.

### Code Quality & Style Rules

- Keep changes small and local to the existing helper boundaries. Avoid broad refactors while fixing one scraper, cache, CLI, or document-generation behavior.
- Follow the existing simple Python style: functions over classes, flat modules, explicit helper functions, and straightforward control flow.
- Respect `.flake8` max-line-length `100`; avoid introducing formatting churn in unrelated files.
- Use clear sentinel values consistently: `"Lyrics not found."` and `"Chords not found."` are part of current fetch/cache behavior.
- Prefer structured JSON/CSV handling through `json`, `pandas`, and JSONL helpers rather than ad hoc string parsing.
- Keep comments sparse and useful. Add comments for scraper assumptions, fallback behavior, or non-obvious document formatting, not for obvious assignments.
- Do not mix unrelated cleanup with behavior changes. If modernizing imports, types, paths, or tests, keep that change deliberate and separately reviewable.

### Development Workflow Rules

- Work from the `2026-upgrade` branch for BMAD/context work unless the user chooses another baseline.
- `origin/main` is the remote default branch; `origin/misc_improvements` remains an unmerged broader refactor/CI/test branch and should not be merged casually.
- Keep `.codex/` and `_bmad/*.user.toml` out of commits. They contain local Codex state or personal installer answers.
- Commit BMAD/project-context changes separately from application behavior changes when practical.
- Before committing app changes, run `python3 -m unittest discover -s tests -p 'test_*.py'` from the repository root.
- If a dependency is missing locally, report exactly which verification could not run rather than implying success.
- Prefer branch/commit notes that state the user-visible behavior changed, the cache/data contract affected, and the verification performed.

### Critical Don't-Miss Rules

- Do not commit private/local state: `.codex/`, `data/config/config.json`, generated outputs, and `*.user.toml` files must stay out of version control.
- Do not break repo-root execution. The app is expected to run as `python3 main.py ...` from the repository root.
- Do not change cache key semantics casually. Existing cache lookups depend on exact `artist` and `title` fields plus `"Artist - Title"` mapping keys.
- Do not replace `"Lyrics not found."` or `"Chords not found."` without updating fetch flow, cache readers, reporting, and tests.
- Do not make unit tests depend on live external sites, Genius API credentials, local cache contents, or generated `.docx` files.
- Do not assume `python-docx` is installed in every local environment; if document-generation verification cannot run, report the missing dependency.
- Do not merge `origin/misc_improvements` wholesale without reviewing dependency changes, imports, tests, CI, and document-generation behavior.
- Do not normalize song titles/artists globally unless cache compatibility and scraper query behavior are handled intentionally.

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code.
- Follow all rules exactly as documented.
- When in doubt, prefer the option that preserves current repo-root CLI behavior, cache compatibility, and testability.
- Update this file if new durable project patterns emerge.

**For Humans:**

- Keep this file lean and focused on agent needs.
- Update it when the technology stack, runtime paths, test strategy, or branch baseline changes.
- Remove rules that become obvious or obsolete over time.

Last Updated: 2026-05-17
