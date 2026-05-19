# Story 2.4: Apply Questionable Exclusion and Override Rules

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a camper preparing a print-ready book,
I want Questionable songs excluded by default with an explicit override path,
so that known bad content does not reach the printed book unless I deliberately accept it.

## Acceptance Criteria

1. Given cached content is clean and has no current reject decision, when generation filtering runs, then the song is included and the result records that it passed quality and review checks.
2. Given cached content is Questionable and has no matching current `accept` or `override` decision, when generation filtering runs, then the song is excluded by default and the exclusion reason reflects the quality status and signals.
3. Given cached content is Questionable and has a matching current `accept` or `override` decision, when generation filtering runs, then the song is included and the result identifies the explicit review decision that allowed it.
4. Given a current `reject` decision or a stale decision hash, when generation filtering runs, then the song is excluded and stale decisions are ignored rather than being treated as active.
5. Given the cache-to-document path renders a book, when generation filtering excludes a song, then the song does not appear in the generated `.docx`, while existing document formatting and the current lyrics length guard remain unchanged.
6. Given this story is implemented, then it does not add report formatting, selection handling, Markdown output, or selection-specific override logic yet.

## Tasks / Subtasks

- [x] Add generation filtering helpers in `app/generation_filtering.py` (AC: 1, 2, 3, 4)
  - [x] Load or consume current quality status and review decisions from `app.review_state`.
  - [x] Use `load_review_decisions(current_content_hashes=...)` so stale decisions are ignored before filtering.
  - [x] Return structured include/exclude decisions with machine-readable reasons and decision-source metadata.
  - [x] Keep helpers pure: no network, no file writes, and no document rendering.
- [x] Wire filtering into the cache-to-document flow in `app/document_creation.py` (AC: 1, 2, 3, 4, 5)
  - [x] Preserve repo-root CLI behavior and existing formatting/cleaning logic.
  - [x] Keep the existing lyric length cutoff and `clean_lyrics` / `clean_chords` behavior intact.
  - [x] Skip rendering excluded songs, but leave included song rendering unchanged.
- [x] Add focused tests in `tests/test_generation_filtering.py` and, if needed, `tests/test_document_creation.py` (AC: 1, 2, 3, 4, 5)
  - [x] Cover clean include, Questionable default exclusion, `accept` / `override` inclusion, `reject` exclusion, and stale-decision ignore behavior.
  - [x] Cover the generated document omits excluded songs without breaking included content.
- [x] Preserve current boundaries and compatibility (AC: 1, 2, 3, 4, 5, 6)
  - [x] Do not change review-state file schemas from Story 2.3.
  - [x] Do not add report formatting or selection logic in this story.
  - [x] Do not change `main.py` unless the document builder signature truly requires it.
- [x] Verify from the repository root (AC: 1, 2, 3, 4, 5, 6)
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Story 2.3 already persisted review decisions as current-state data with content hashes. Reuse `load_review_decisions()` instead of revalidating decision files here.
- `app/document_creation.py` currently renders every non-empty cached song and only applies a lyric length cutoff. Add filtering before rendering, not a renderer rewrite.
- `app/review_state.py` already ignores stale review decisions when given current hashes. Use that path so stale approvals do not become active by accident.
- Questionable content is the default exclusion state. Explicit `accept` or `override` decisions are the only allow path for Questionable content.
- Keep `reject` as a hard exclusion even if the content is otherwise clean.
- Preserve absolute `app.*` imports and the existing flat module layout.
- `python-docx` is optional in local environments; docx-level integration tests should skip cleanly when the dependency is unavailable.

### Suggested Generation Filter Result Shape

```python
{
    "song_key": "Artist - Title",
    "content_type": "lyrics",
    "content_hash": "sha256:...",
    "quality": "questionable",
    "included": False,
    "decision_source": "default_exclude",
    "reason": "Questionable content excluded by default.",
    "signals": [...],
    "quality_status": {...},
    "review_decision": None
}
```

Keep this shape stable enough for Story 2.5 to consume when report formatting is added.

### Project Structure Notes

- Likely implementation files: `app/generation_filtering.py`, `app/document_creation.py`, `tests/test_generation_filtering.py`, `tests/test_document_creation.py`
- Keep filtering separate from `app/review_state.py`; that module should stay focused on current-state persistence and stale-hash validation.
- Keep report formatting out of this story; Story 2.5 owns the report layer.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2-4-Apply-Questionable-Exclusion-and-Override-Rules]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision-Impact-Analysis]
- [Source: _bmad-output/planning-artifacts/architecture.md#File-Structure-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Pattern-Enforcement]
- [Source: _bmad-output/implementation-artifacts/2-3-persist-review-decisions-with-content-hashes.md]
- [Source: _bmad-output/implementation-artifacts/2-2-retry-alternate-sources-before-final-questionable-status.md]
- [Source: _bmad-output/implementation-artifacts/1-5-persist-current-quality-status-for-cached-content.md]
- [Source: app/content_models.py]
- [Source: app/document_creation.py]
- [Source: app/review_state.py]
- [Source: app/quality_assessment.py]
- [Source: main.py]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]

## Dev Agent Record

### Agent Model Used

GPT-5.5

### Debug Log References

- 2026-05-19: Added pure generation-filter helpers for current quality status and review-decision evaluation.
- 2026-05-19: Wired cache-to-document rendering to exclude Questionable content by default and respect explicit override/reject decisions.
- 2026-05-19: Added regression coverage for generation filtering and document creation; full unittest suite passed with docx-dependent integration tests skipped because `python-docx` is unavailable in this environment.
- 2026-05-19: Code review completed cleanly; Story 2.4 approved for completion.

### Completion Notes List

- Implemented `app/generation_filtering.py` with current content hash tracking and include/exclude decision metadata.
- Updated `app/document_creation.py` to load quality status and review decisions once per run, then skip excluded songs before rendering.
- Added tests for clean inclusion, default Questionable exclusion, override inclusion, reject exclusion, stale-decision ignore behavior, and document output filtering.
- Verified with `python3 -m unittest discover -s tests -p 'test_*.py'` from the repository root; 61 tests ran, 2 skipped due missing `python-docx`.

### File List

- `app/generation_filtering.py`
- `app/document_creation.py`
- `tests/test_generation_filtering.py`
- `tests/test_document_creation.py`
- `_bmad-output/implementation-artifacts/2-4-apply-questionable-exclusion-and-override-rules.md`

### Change Log

- 2026-05-19: Created Story 2.4 for Questionable exclusion and explicit review override rules.
- 2026-05-19: Implemented Story 2.4 with pure generation filtering, cache-to-document filtering, and regression tests.
- 2026-05-19: Marked Story 2.4 done after clean code review.
