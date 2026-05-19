# Story 2.1: Record Source Attempts During Fetching

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook builder user,
I want each source lookup attempt recorded,
so that I can understand where lyrics or chords came from and why a source failed.

## Acceptance Criteria

1. Given an online fetch/cache workflow attempts lyrics or chord sources, when a source returns a candidate, not-found result, or error, then a source attempt record is appended to `data/review/source_attempts.jsonl` and the record includes song identity, content type, source name, status, optional error, and retrieval timestamp.
2. Given a source failure occurs while later fallback sources remain, when fetching continues, then the failure is logged or reported as recoverable and does not crash the full run.
3. Given source-attempt records are written, when the file is read back later, then the JSONL lines preserve exact identity fields and append-only ordering without rewriting unrelated records.
4. Given the fetch workflow already exposes tried-log/source-return details, when this story is implemented, then those return shapes and cache semantics are preserved; source-attempt recording is additive, not a replacement.
5. Given current architecture, when this story is implemented, then it adds only source-attempt contract helpers, append/read helpers, fetch integration, and focused tests; it does not change retry policy, review-decision logic, or generation filtering yet.

## Tasks / Subtasks

- [ ] Add source-attempt contract helpers in `app/content_models.py` (AC: 1, 3, 4)
  - [ ] Define the source-attempt record constructor using exact song identity fields plus `content_type`, `source`, `status`, optional `error`, and `retrieved_at`.
  - [ ] Reuse the existing `candidate` / `not_found` / `error` source outcome contract instead of inventing a second status vocabulary.
  - [ ] Keep exact `artist` and `title` values; do not normalize cache identity for source-attempt records.
- [ ] Add append-only source-attempt helpers in `app/source_attempts.py` (AC: 1, 3)
  - [ ] Implement an append helper that writes one JSONL line per attempt to `data/review/source_attempts.jsonl`.
  - [ ] Create parent directories automatically before writing.
  - [ ] Implement a small read helper for inspection and regression tests; missing files should load as empty history.
  - [ ] Keep writes append-only and preserve unrelated records.
  - [ ] Treat write/read failures as recoverable and log them instead of crashing the fetch workflow.
- [ ] Wire source-attempt recording into `app/fetch_data.py` (AC: 1, 2, 4)
  - [ ] Record attempts from the existing lyrics and chords fallback loops, including candidate, not-found, and error outcomes.
  - [ ] Preserve current fetch return shapes, `tried_log` behavior, cache-first semantics, and source ordering.
  - [ ] Do not add new live requests, retries, or policy changes in this story; those belong to Story 2.2.
- [ ] Add focused unit tests in `tests/test_source_attempts.py` (AC: 1, 2, 3, 4)
  - [ ] Cover append and read round-trip behavior for one and multiple attempts.
  - [ ] Cover candidate, not-found, and error statuses with exact identity fields and retrieval timestamps.
  - [ ] Cover missing-file behavior as empty history.
  - [ ] Cover fetch integration with mocked source functions so recording happens without live network calls.
  - [ ] Cover recoverable logging/continuation when source lookup or append recording fails.
- [ ] Preserve current app boundaries and compatibility (AC: 2, 4, 5)
  - [ ] Keep the implementation dependency-free and in the existing flat `app/*.py` module layout.
  - [ ] Do not change `main.py`, cache record shape, or sentinel values `"Lyrics not found."` / `"Chords not found."`.
  - [ ] Do not add review decisions, generation filtering, or reporting in this story.
- [ ] Verify from the repository root (AC: 1, 2, 3, 4, 5)
  - [ ] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- `data/review/source_attempts.jsonl` is append-only audit/history. Treat it as source traceability, not current-state data.
- Architecture already calls out `Source Attempt` as a shared contract and the source-attempt file as a separate artifact from `quality_status.json` and `review_decisions.json`.
- Reuse the existing `candidate` / `not_found` / `error` source outcome vocabulary from Story 1.1. Do not introduce a parallel status enum for source attempts.
- The fetch implementation already has shared fallback loops in `get_lyrics_from_sources()` and `get_chords_from_sources()` inside `app/fetch_data.py`. Hook recording there so the story does not fork the source logic.
- Preserve the existing `tried_log` return values and cache behavior. Source-attempt recording should be additive and must not alter which source wins.
- Source-attempt records should not include API tokens, credentials, or private config values.
- Missing files should behave like empty history. Append failures should be logged and recoverable so a temporary file issue does not take down a fetch run.
- Later stories own retry policy, review-decision application, and generation filtering. This story stops at recording and traceability.
- Previous story context: Story 1.5 established the review-state file boundary and recoverable loader/write pattern for local state. Use that pattern for append-only history, but keep source attempts in their own module and file.
- Git context at story creation: recent commits include `12da25a Automator upgrade`, `4afd01d Merge bug fixes into 2026 upgrade`, and `96f1f71 Add 2026 BMAD upgrade assets`.

### Suggested Record Shape

```python
{
    "artist": "Campfire Band",
    "title": "Trail Song",
    "song_key": "Campfire Band - Trail Song",
    "content_type": "lyrics",
    "source": "Genius",
    "status": "candidate",
    "error": None,
    "retrieved_at": "2026-05-19T14:13:56+01:00",
}
```

Status examples:

- `candidate` - source returned usable content
- `not_found` - source returned no usable content
- `error` - source raised or returned an error condition

### Project Structure Notes

- Likely implementation files: `app/content_models.py`, `app/source_attempts.py`, `app/fetch_data.py`
- New test file: `tests/test_source_attempts.py`
- Keep source-attempt handling separate from `app/review_state.py`; that module owns current-state review files, not append-only source history.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2-1-Record-Source-Attempts-During-Fetching]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision-Impact-Analysis]
- [Source: _bmad-output/planning-artifacts/architecture.md#File-Structure-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Pattern-Enforcement]
- [Source: _bmad-output/implementation-artifacts/1-1-define-quality-data-contracts.md]
- [Source: _bmad-output/implementation-artifacts/1-5-persist-current-quality-status-for-cached-content.md]
- [Source: app/fetch_data.py]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]
- [Source: https://docs.python.org/3.12/library/json.html]
- [Source: https://docs.python.org/3.12/library/pathlib.html]
- [Source: https://docs.python.org/3.12/library/unittest.html]

## Dev Agent Record

### Agent Model Used

GPT-5.5

### Debug Log References

- `python3 -m unittest tests.test_source_attempts`
- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Added `build_source_attempt_record()` to `app/content_models.py` with exact song identity and `candidate` / `not_found` / `error` status validation.
- Added `app/source_attempts.py` for append-only JSONL writes and tolerant reads of `data/review/source_attempts.jsonl`.
- Wired source-attempt recording into `app/fetch_data.py` without changing fetch return shapes or source ordering.
- Added focused coverage in `tests/test_content_models.py` and `tests/test_source_attempts.py`.
- Fixed source-attempt recording to persist the original song identity instead of per-query fallback variants.
- Full repository unittest suite passed with 44 tests.

### File List

- `app/content_models.py`
- `app/source_attempts.py`
- `app/fetch_data.py`
- `tests/test_content_models.py`
- `tests/test_source_attempts.py`

## Change Log

- 2026-05-19: Created Story 2.1 for source-attempt recording and append-only audit history.
- 2026-05-19: Implemented source-attempt recording, append/read helpers, and regression tests; moved story to review.
- 2026-05-19: Fixed source identity persistence in source-attempt records and marked the story done after review.

### Review Findings

- [x] [Review][Patch] Preserve original song identity in source attempts [app/fetch_data.py:155] — fixed by recording the original song identity instead of query variants.
