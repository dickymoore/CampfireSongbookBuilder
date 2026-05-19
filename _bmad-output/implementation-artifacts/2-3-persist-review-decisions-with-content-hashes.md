# Story 2.3: Persist Review Decisions with Content Hashes

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook builder user,
I want my accept/reject/override decisions saved against the exact reviewed content,
so that a stale approval is not silently reused after content changes.

## Acceptance Criteria

1. Given a user or agent records a review decision for a song/content type, when the decision is saved, then `data/review/review_decisions.json` stores `song_key`, `content_type`, `content_hash`, `decision`, optional `reason`, and `decided_at`, and valid decisions are limited to `accept`, `reject`, and `override`.
2. Given cached content changes after a decision was saved, when review decisions are loaded against the current content hash, then decisions whose stored hash no longer matches are reported as stale or ignored, and stale decisions do not become active automatically.
3. Given missing or malformed review-decision files, when the application loads review decisions, then it reports recoverable validation errors with file path, field, and reason, while absent files are treated as empty state where appropriate.
4. Given current architecture, when this story is implemented, then it adds only review-decision persistence and hash-bound validation/helpers; it does not add generation filtering, review-based inclusion/exclusion, or report formatting yet.

## Tasks / Subtasks

- [x] Add review-decision current-state helpers in `app/review_state.py` (AC: 1, 2, 3)
  - [x] Add load/save helpers for `data/review/review_decisions.json` using the same current-state pattern as `quality_status.json`.
  - [x] Reuse `build_review_decision()` from `app/content_models.py` instead of duplicating decision or hash validation.
  - [x] Validate stale hash mismatches when the caller provides current content-hash context, and report them without turning the helper into generation filtering.
  - [x] Preserve recoverable validation behavior for malformed files and nested entries.
- [x] Add focused tests in `tests/test_review_state.py` (AC: 1, 2, 3)
  - [x] Cover save/load round-trip for review decisions with exact `song_key`, `content_type`, `content_hash`, `decision`, `reason`, and `decided_at`.
  - [x] Cover missing and malformed files returning empty state or recoverable validation errors.
  - [x] Cover stale-hash detection when stored decisions no longer match the current content hash.
  - [x] Cover invalid decision values and invalid hashes through the existing contract helpers.
- [x] Preserve current boundaries and compatibility (AC: 1, 2, 3, 4)
  - [x] Keep `quality_status.json` behavior unchanged.
  - [x] Do not wire review decisions into generation filtering, inclusion/exclusion logic, or report rendering in this story.
  - [x] Do not change `main.py` or the raw JSONL cache contracts.
- [x] Verify from the repository root (AC: 1, 2, 3, 4)
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Story 2.2 already established the retry path and current Questionable persistence. Keep that behavior intact; this story starts at review-decision persistence, not source retry.
- `app/review_state.py` currently owns the current quality-status file boundary. Extend that same module with review-decision persistence and stale-hash validation, rather than introducing a new state layer.
- `app/content_models.py` already validates review decisions and content hashes through `build_review_decision()`. Reuse those contracts so decision values remain limited to `accept`, `reject`, and `override`.
- Review decisions must be bound to exact content via `sha256:<hex>` hashes. If the reviewed content changes later, the saved decision must no longer look current.
- Keep review decisions as current-state JSON under `data/review/review_decisions.json`, not append-only history. Source attempts remain the append-only audit trail.
- Do not add generation filtering, Questionable exclusion, explicit override application, or report formatting here. Story 2.4 owns the inclusion/exclusion rules.
- Keep loader failures recoverable and structured, matching the validation style already used for quality-status files in Story 1.5.
- Preserve repo-root execution, absolute `app.*` imports, and the existing flat helper-module layout.

### Suggested Review Decision State Shape

```python
{
    "version": 1,
    "updated_at": "2026-05-19T15:00:00+01:00",
    "entries": {
        "The Campfire Trio - Trail Song": {
            "lyrics": {
                "artist": "The Campfire Trio",
                "title": "Trail Song",
                "song_key": "The Campfire Trio - Trail Song",
                "content_type": "lyrics",
                "content_hash": "sha256:...",
                "decision": "accept",
                "reason": "Manually reviewed and playable.",
                "decided_at": "2026-05-19T15:00:00+01:00"
            }
        }
    }
}
```

### Project Structure Notes

- Likely implementation files: `app/review_state.py`, `tests/test_review_state.py`
- Keep review-decision handling separate from `app/generation_filtering.py`; that module should only appear in the later exclusion story.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2-3-Persist-Review-Decisions-with-Content-Hashes]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision-Impact-Analysis]
- [Source: _bmad-output/planning-artifacts/architecture.md#File-Structure-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Pattern-Enforcement]
- [Source: _bmad-output/implementation-artifacts/2-2-retry-alternate-sources-before-final-questionable-status.md]
- [Source: _bmad-output/implementation-artifacts/1-5-persist-current-quality-status-for-cached-content.md]
- [Source: app/content_models.py]
- [Source: app/review_state.py]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]
- [Source: https://docs.python.org/3.12/library/hashlib.html]
- [Source: https://docs.python.org/3.12/library/pathlib.html]
- [Source: https://docs.python.org/3.12/library/unittest.mock-examples.html]

## Dev Agent Record

### Agent Model Used

GPT-5.5

### Debug Log References

- 2026-05-19: Added hash-bound review decision persistence and stale decision detection to `app/review_state.py`.
- 2026-05-19: Added focused review-state tests for round-trip persistence, malformed files, and stale-hash handling.
- 2026-05-19: Fixed nested review-decision content-type validation to keep loaded records in the correct bucket.
- 2026-05-19: Verified with `python3 -m unittest discover -s tests -p 'test_*.py'` (53 tests).

### Completion Notes List

- Added `load_review_decisions()` and `save_review_decisions()` with the same current-state file pattern used for quality status.
- Review decisions are validated against `sha256:<hex>` content hashes and stale decisions are reported then ignored during load.
- Nested review-decision records now must match their enclosing `content_type` bucket, preventing schema drift on load.
- Added regression coverage for review-decision round trips, missing/malformed files, and stale hash detection.

### File List

- `app/review_state.py`
- `tests/test_review_state.py`

## Change Log

- 2026-05-19: Created Story 2.3 for hash-bound review-decision persistence.
- 2026-05-19: Implemented Story 2.3 with review-decision persistence, stale-hash validation, and regression tests.
- 2026-05-19: Resolved review feedback on nested `content_type` mismatch handling.
