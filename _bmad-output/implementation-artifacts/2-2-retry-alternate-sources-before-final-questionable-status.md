# Story 2.2: Retry Alternate Sources Before Final Questionable Status

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a musician adding songs,
I want the tool to keep trying alternate sources when one source returns bad content,
so that I get better lyrics or chords without manually chasing websites.

## Acceptance Criteria

1. Given a configured source returns content that fails deterministic quality assessment, when additional configured sources remain available, then the workflow retries the next source before finalizing the candidate as Questionable, and the retry decision remains visible in tried-log and source-attempt history.
2. Given a later configured source returns clean content, when the retry loop completes, then the clean candidate is returned and cached, and earlier questionable candidates are not treated as the final result.
3. Given all available sources yield only missing or questionable content, when the retry loop exhausts the configured source list, then the final candidate is persisted through the existing quality-status boundary as Questionable with merged signals and content hash, and the run remains recoverable.
4. Given acceptable cached content already exists for a song, when the cache-first fetch workflow runs without an explicit refresh request, then the workflow skips unnecessary live source requests and does not recompute retry decisions for that cached song.
5. Given source attempts are already recorded, when the retry loop runs, then source-attempt records remain append-only, preserve the original song identity, and keep source ordering intact.
6. Given current architecture, when this story is implemented, then it adds only candidate-quality composition, retry orchestration, current-quality persistence, and focused tests; it does not add review-decision application, generation filtering, or report formatting yet.

## Tasks / Subtasks

- [x] Add a combined candidate-quality helper in `app/quality_assessment.py` (AC: 1, 2, 3)
  - [x] Compose the existing pure assessments for missing content, junk/markup, print-hostile content, and low-confidence matching into one deterministic candidate-quality result.
  - [x] Reuse the existing pure helpers and threshold constants; do not invent a second quality policy.
  - [x] Return merged `quality`, `signals`, and `summary` data that downstream fetch/cache code can persist or inspect.
- [x] Make fetch retry quality-aware in `app/fetch_data.py` (AC: 1, 2, 5)
  - [x] Keep the existing source ordering, tried-log behavior, and source-attempt recording from Story 2.1.
  - [x] Continue to later configured sources when a candidate is anything other than clean.
  - [x] Preserve original song identity in all persisted records and do not reintroduce stripped query variants.
- [x] Thread final quality status through cache population in `app/document_generation.py` (AC: 2, 3, 4)
  - [x] Preserve cache-first semantics: if acceptable cached content already exists, skip live requests and reuse the cached value.
  - [x] Use the quality result from the fetch workflow to decide whether the returned candidate is clean or final Questionable.
  - [x] Persist current quality state through the existing `app.review_state` boundary when the final candidate is Questionable, without adding review-decision logic.
  - [x] Keep raw JSONL cache shapes unchanged and avoid changing sentinel values.
- [x] Add focused tests in `tests/test_source_retry.py` (AC: 1, 2, 3, 4, 5)
  - [x] Cover a questionable first candidate that is skipped in favor of a later clean source.
  - [x] Cover exhaustion of all sources into a final Questionable outcome with persisted quality status.
  - [x] Cover acceptable cached content short-circuiting the retry path.
  - [x] Cover preservation of tried-log/source-attempt ordering and original song identity.
  - [x] Use mocks and temporary files only; do not make live network calls.
- [x] Preserve current app boundaries and compatibility (AC: 1, 2, 3, 4, 5, 6)
  - [x] Keep the implementation dependency-free and within the existing flat `app/*.py` module layout.
  - [x] Do not change `main.py`, review-decision application, generation filtering, or report formatting in this story.
  - [x] Do not replace the current raw cache format or the existing quality-status file contract.
- [x] Verify from the repository root (AC: 1, 2, 3, 4, 5, 6)
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Story 2.1 already added append-only source-attempt recording. Preserve that behavior, and keep the original song identity in every attempt record.
- `app/fetch_data.py` currently returns the first usable source result. This story must let later sources win when an earlier candidate is questionable.
- `app/document_generation.py` currently caches fetched content with only raw presence and length checks. Replace that acceptance gate with the quality result from the fetch workflow so the retry path can continue until a clean candidate is found.
- `app/quality_assessment.py` already provides pure helper functions for missing content, junk markup, print-hostile content, and low-confidence matching. Compose those helpers instead of duplicating thresholds or heuristics.
- `app/review_state.py` already owns the current quality-status file boundary and recoverable validation behavior from Story 1.5. Reuse it as the persistence boundary for final Questionable candidates; do not add review-decision logic here.
- Preserve cache-first behavior. If a song already has acceptable cached content, do not issue live requests just to re-evaluate it.
- Keep source failures recoverable and structured. A single bad source should not prevent later configured sources from being attempted.
- Do not write API tokens or private config values into quality status, source attempts, or logs.
- Later stories own review-decision application, Questionable exclusion, explicit overrides, and generation reports. This story stops at retrying sources until a candidate is acceptable or clearly Questionable.
- Previous story context: Story 2.1 fixed source-attempt recording and original song identity. Use that as the traceability baseline for this retry story.

### Suggested Candidate Quality Result Shape

```python
{
    "quality": "questionable",
    "signals": [
        {"code": "print_hostile_content", "severity": "warning", "message": "...", "content_type": "lyrics"}
    ],
    "summary": {
        "line_count": 64,
        "total_characters": 5210,
        "longest_line_length": 182,
        "has_print_hostile_content": True
    },
}
```

### Project Structure Notes

- Likely implementation files: `app/quality_assessment.py`, `app/fetch_data.py`, `app/document_generation.py`
- New test file: `tests/test_source_retry.py`
- Keep source-attempt handling separate from `app/review_state.py`; that module owns current-state review files, not source retry orchestration.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2-2-Retry-Alternate-Sources-Before-Final-Questionable-Status]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision-Impact-Analysis]
- [Source: _bmad-output/planning-artifacts/architecture.md#File-Structure-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Pattern-Enforcement]
- [Source: _bmad-output/implementation-artifacts/2-1-record-source-attempts-during-fetching.md]
- [Source: _bmad-output/implementation-artifacts/1-5-persist-current-quality-status-for-cached-content.md]
- [Source: app/fetch_data.py]
- [Source: app/document_generation.py]
- [Source: app/quality_assessment.py]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]
- [Source: https://docs.python.org/3.12/library/unittest.mock-examples.html]
- [Source: https://docs.python.org/3.12/library/pathlib.html]

## Dev Agent Record

### Agent Model Used

GPT-5.5

### Debug Log References

- 2026-05-19: Implemented candidate-quality composition, retry-aware source loops, and cache/status persistence.
- 2026-05-19: Verified with `python3 -m unittest discover -s tests -p 'test_*.py'` (49 tests).
- 2026-05-19: Applied review fixes so exhausted retries resolve to Questionable and source-attempt history distinguishes real candidate content.

### Completion Notes List

- Added `assess_candidate_quality()` to merge missing, junk, print-hostile, and low-confidence signals into one deterministic result.
- Updated source retry loops to continue past questionable candidates and preserve original song identity in source-attempt records.
- Threaded cache population through `app.review_state` so clean cached content short-circuits live fetches and final questionable runs persist quality state.
- Added focused retry regression tests covering clean handoff, exhausted retries, cache-first short-circuiting, and persistence.

### File List

- `app/quality_assessment.py`
- `app/fetch_data.py`
- `app/document_generation.py`
- `tests/test_quality_assessment.py`
- `tests/test_source_attempts.py`
- `tests/test_source_retry.py`

## Change Log

- 2026-05-19: Created Story 2.2 for quality-aware source retry before final Questionable status.
- 2026-05-19: Implemented Story 2.2 with quality-aware retry, cache-first short-circuiting, and current-quality persistence.
- 2026-05-19: Applied review-driven patch pass for retry exhaustion quality and source-attempt visibility.
