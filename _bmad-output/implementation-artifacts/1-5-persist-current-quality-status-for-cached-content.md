# Story 1.5: Persist Current Quality Status for Cached Content

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook builder user,
I want quality results saved in a local status file,
so that later generation runs can reuse quality decisions without re-fetching or re-assessing everything manually.

## Acceptance Criteria

1. Given assessed cached lyrics or chords, when quality status is saved, then `data/review/quality_status.json` is created if needed, stores current status by exact song/content identity, and parent directories are created automatically.
2. Given a missing `data/review/quality_status.json`, when quality status is loaded, then the loader returns empty current state and no validation errors.
3. Given malformed quality status JSON or invalid nested entries, when quality status is loaded, then the loader reports recoverable validation errors with file path, field, and reason instead of crashing.
4. Given persisted quality status entries, when the file is read back, then exact `artist`, `title`, `song_key`, `content_type`, `content_hash`, `quality`, `signals`, and `assessed_at` values round-trip without normalization or mutation.
5. Given current architecture, when this story is implemented, then it adds only review-state load/write helpers and focused tests; it does not wire review decisions, generation filtering, or CLI behavior yet.

## Tasks / Subtasks

- [x] Add `app/review_state.py` quality-status persistence helpers (AC: 1, 2, 3, 4, 5)
  - [x] Implement `load_quality_status()` and `save_quality_status()` for the current-state file.
  - [x] Use a top-level JSON object with `version`, `updated_at`, and `entries`, where `entries` is keyed by exact `song_key` and then `content_type`.
  - [x] Persist `app.content_models.build_quality_status()` records unchanged; do not recalculate or normalize identity fields on save.
  - [x] Treat missing files as empty state and malformed content as recoverable validation errors.
  - [x] Create parent directories automatically before writing.
  - [x] Keep the module dependency-free and use standard-library `json` plus `pathlib`/`os` only.
- [x] Add focused unit tests in `tests/test_review_state.py` (AC: 1, 2, 3, 4)
  - [x] Round-trip one and multiple quality-status records.
  - [x] Verify missing file handling returns empty state.
  - [x] Verify malformed JSON, missing required fields, and nested identity mismatches produce structured validation errors.
  - [x] Verify save creates `data/review/` parents automatically.
- [x] Preserve current app boundaries and compatibility (AC: 5)
  - [x] Do not change `main.py`, `app/cache.py`, `app/quality_assessment.py`, or `app/content_models.py`.
  - [x] Do not add review-decision persistence, generation filtering, or report generation in this story.
- [x] Verify from the repository root (AC: 1, 2, 3, 4, 5)
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- `app/content_models.py` already validates `quality_status` records, content hashes, and nested signals. Reuse those builders instead of rebuilding contract validation here.
- Treat `quality_status.json` as current state, not an event log. Save should upsert by exact `song_key` + `content_type` and preserve exact `artist`/`title` cache identity.
- Prefer a recoverable loader that returns structured errors for file-level and field-level problems. Include `file_path`, `field`, and `reason` in validation errors.
- Missing files are empty state. Malformed files should not crash the app; valid entries can be preserved if the implementation can validate them independently.
- Use `Path.mkdir(parents=True, exist_ok=True)` for parent creation and `json.load` / `json.dump` for file I/O.
- This story stops at quality-status persistence. `review_decisions.json`, generation filtering, and reporting are later stories.
- Previous story context: Story 1.4 added deterministic quality assessment helpers and strict contract records. Persist those records unchanged rather than inventing a parallel schema.
- Git context at story creation: recent commits show the 2026 upgrade and BMAD asset updates; no persistence module has been added yet.

### Suggested Record Shape

```python
{
    "version": 1,
    "updated_at": "2026-05-19T14:03:45+01:00",
    "entries": {
        "Artist - Title": {
            "lyrics": { ...quality_status... },
            "chords": { ...quality_status... },
        }
    }
}
```

Validation error example:

```python
{
    "file_path": "data/review/quality_status.json",
    "field": "entries['Artist - Title'].lyrics.quality",
    "reason": "quality must be one of clean, questionable, missing; got 'clean-ish'",
}
```

### Project Structure Notes

- New implementation file: `app/review_state.py`
- New test file: `tests/test_review_state.py`
- Reuse `app/content_models.py` for contract validation and record construction.
- Keep all runtime files under `data/review/`; do not create any other persistence location for this story.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1-5-Persist-Current-Quality-Status-for-Cached-Content]
- [Source: _bmad-output/planning-artifacts/architecture.md#State-Management-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#File-Structure-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement-Guidelines]
- [Source: _bmad-output/implementation-artifacts/1-1-define-quality-data-contracts.md]
- [Source: _bmad-output/implementation-artifacts/1-4-detect-print-hostile-and-low-confidence-content.md]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: https://docs.python.org/3.12/library/json.html]
- [Source: https://docs.python.org/3.12/library/pathlib.html]

## Dev Agent Record

### Agent Model Used

GPT-5.2 (Codex CLI)

### Debug Log References

- `python3 -m unittest tests.test_review_state`
- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created
- Added `app/review_state.py` with current-state quality-status load/save helpers, recoverable validation reporting, exact song-key/content-type indexing, and automatic parent-directory creation.
- Added `tests/test_review_state.py` to cover round-trip persistence, empty-state loading, malformed JSON handling, nested validation errors, and parent-directory creation.
- Resolved review finding: missing `entries` now reports a validation error instead of loading as empty state.
- Resolved review finding: nested `content_type` must match the enclosing entry key before a record is accepted.
- Verified the full `unittest` suite passes from the repository root.
- Revalidated on 2026-05-27: `python3 -m unittest discover -s tests -p 'test_*.py'` (133 tests, OK).
- Senior developer review complete; story marked done.

### File List

- `app/review_state.py`
- `tests/test_review_state.py`
- `_bmad-output/implementation-artifacts/1-5-persist-current-quality-status-for-cached-content.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Senior Developer Review (AI)

Reviewer: Dicky on 2026-06-01

### Scope

- Reviewed story claims vs implementation for: `app/review_state.py`, `tests/test_review_state.py`.
- Docs lookup note: MCP/web search not available in this environment; relied on in-repo docs (`docs/development-guide.md`, `docs/architecture.md`) and the codebase itself.

### Findings

- MEDIUM: `app/review_state.py` has grown beyond the narrow scope of "quality status" persistence and now includes other current-state helpers; story-specific ACs are still satisfied, but the story text no longer reflects the module's full surface area.
- LOW: Loader error messages in shared helpers are quality-status flavored even when used by other current-state files, which can confuse operators during troubleshooting.

### Fixes Applied

- No code changes required for this story; unit coverage for quality-status persistence remains solid.

## Change Log

- 2026-05-19: Implemented quality-status persistence and regression tests for story 1.5.
- 2026-05-19: Addressed code review findings - 2 items resolved (Date: 2026-05-19)
- 2026-05-27: Revalidated test suite and set story status to review.
- 2026-06-01: Senior developer review complete; story marked done.
