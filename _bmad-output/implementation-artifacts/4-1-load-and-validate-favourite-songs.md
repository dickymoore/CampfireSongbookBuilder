# Story 4.1: Load and Validate Favourite Songs

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a camper building a repeat-use songbook,
I want to mark favourite songs in an inspectable local file,
so that I can generate a focused book without editing the master CSV each time.

## Acceptance Criteria

1. Given `data/selections/favourites.json` contains favourite song entries, when favourites are loaded, then valid entries are returned as canonical favourites keyed by exact `song_key`, exact `artist` and `title` are preserved, and any entry that only stores artist/title derives the same `song_key`.
2. Given the favourites file contains malformed JSON, a non-object top level, or entries with missing or mismatched identity fields, when favourites are loaded, then the loader reports recoverable validation errors with `file_path`, `field`, and `reason`, while preserving any valid entries it can validate.
3. Given the favourites file is missing, when favourites are loaded, then the loader returns empty current state and no errors; when favourites are saved, parent directories under `data/selections/` are created automatically.
4. Given a favourite song is Questionable, when downstream favourite-only generation later consumes the loaded favourites, then favourite status alone does not override quality/review rules. This story only loads and validates the favourite-state file.

## Tasks / Subtasks

- [x] Add `app/selection_state.py` as the favourite state helper module (AC: 1, 2, 3, 4)
  - [x] Define a JSON current-state shape with top-level `version`, `updated_at`, and `entries`.
  - [x] Key `entries` by exact `song_key` so lookups stay stable and duplicate favourites do not require extra normalization.
  - [x] Validate each favourite entry against exact `artist`, `title`, and derived `song_key` identity rules.
  - [x] Treat missing files as empty state and malformed content as recoverable validation errors.
  - [x] Create parent directories automatically before saving `data/selections/favourites.json`.
  - [x] Keep the module flat and dependency-light; prefer stdlib `json`, `pathlib`, and existing app helpers.
- [x] Reuse existing contract helpers instead of inventing a second identity model (AC: 1, 2, 4)
  - [x] Reuse `app.content_models.derive_song_key` and the existing exact `artist`/`title` contract.
  - [x] If a small favourite-record validator is needed, add it in `app/content_models.py` so selection and future named-selection code share the same rules.
  - [x] Do not globally normalize artist/title strings, trim identity fields, or infer alternate song identities.
- [x] Add focused tests in `tests/test_selection_state.py` and, if needed, `tests/test_content_models.py` (AC: 1, 2, 3)
  - [x] Round-trip a valid favourites file and verify exact identity preservation.
  - [x] Verify missing-file loading returns empty state without errors.
  - [x] Verify malformed JSON, top-level shape errors, and nested identity errors report `file_path`, `field`, and `reason`.
  - [x] Verify save creates parent directories automatically.
  - [x] Verify a mismatched `song_key` or missing `artist`/`title` is rejected, not silently repaired.
- [x] Preserve downstream quality semantics while loading favourites (AC: 4)
  - [x] Do not wire favourite status into generation filtering yet; story 4.3 owns that behavior.
  - [x] Keep favourites as metadata only so current quality/review rules still govern inclusion.
  - [x] Ensure this story does not change `app/generation_filtering.py`, `main.py`, or output rendering paths.
- [x] Verify from the repository root (AC: 1, 2, 3, 4)
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- This story is the first half of Epic 4. It should establish the favourites state contract without implementing named selections yet.
- The architecture expects favourites and selections to live in flat helper modules under `app/`, with JSON as the default inspectable format.
- Use exact song identity semantics from the existing cache/review pipeline: preserve `artist`, `title`, and derived `song_key` exactly as provided. Do not lower-case, strip, or globally normalize identity fields.
- Prefer a top-level JSON object over a bare array so the file can carry `version` and `updated_at` without changing the shape later.
- Validation should follow the same recoverable pattern as `app/review_state.py`: return structured errors instead of raising for file-level and field-level problems when possible.
- Keep the loader permissive enough to preserve valid entries even if one entry is malformed.
- Favourites are current-state metadata, not review decisions. A favourite does not imply `accept` or `override`, and downstream filtering still depends on Epic 2 review state.
- Named selection files under `data/selections/*.json` are out of scope for this story; story 4.2 owns that loader and its ordering rules.

### Suggested Favourite File Shape

```json
{
  "version": 1,
  "updated_at": "2026-05-19T19:11:13+01:00",
  "entries": {
    "The Campfire Trio - Trail Song": {
      "artist": "The Campfire Trio",
      "title": "Trail Song",
      "song_key": "The Campfire Trio - Trail Song"
    }
  }
}
```

### Project Structure Notes

- Likely new implementation file: `app/selection_state.py`
- Possible shared contract update: `app/content_models.py`
- New regression tests: `tests/test_selection_state.py`
- Possible contract test extension: `tests/test_content_models.py`
- Runtime file boundary: `data/selections/favourites.json`
- Do not touch `main.py` or `app/generation_filtering.py` unless a helper boundary truly requires it.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-4-1-Load-and-Validate-Favourite-Songs]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-4-Favourites-Selections-and-Quality-Aware-Book-Building]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/prd.md#4-4-Favourites-and-Selections]
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#File-Structure-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR-11-through-FR-13-Favourites-and-Selections]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]
- [Source: _bmad-output/project-context.md#Testing-Rules]
- [Source: app/content_models.py]
- [Source: app/review_state.py]
- [Source: app/generation_filtering.py]
- [Source: tests/test_content_models.py]
- [Source: tests/test_review_state.py]
- [Source: tests/test_generation_filtering.py]

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Added `app/selection_state.py` with recoverable JSON load/save helpers for `data/selections/favourites.json`.
- Added `build_favourite_record()` to `app/content_models.py` so favourites and future named selections share the same exact song identity contract.
- Added regression tests covering round-trip persistence, missing files, malformed JSON, top-level shape errors, nested identity validation, and parent-directory creation on save.
- Kept downstream filtering untouched; favourites remain metadata only in this story.
- Verified the focused favourite-state and content-model tests, plus the full repository test suite, all passing.

### File List

- `app/content_models.py`
- `app/selection_state.py`
- `tests/test_content_models.py`
- `tests/test_selection_state.py`
- `_bmad-output/implementation-artifacts/4-1-load-and-validate-favourite-songs.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Change Log

- 2026-05-19: Implemented favourite-state load/save helpers and shared favourite-record validation.
- 2026-05-19: Added regression coverage for exact identity preservation, recoverable validation errors, and directory creation on save.
- 2026-05-19: Updated story tracking metadata to `done` after successful test verification.
