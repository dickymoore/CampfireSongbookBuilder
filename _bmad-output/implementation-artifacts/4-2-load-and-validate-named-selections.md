# Story 4.2: Load and Validate Named Selections

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a musician preparing for a specific trip,
I want named selections of songs stored locally,
so that I can generate trip-specific books from the same song library.

## Acceptance Criteria

1. Given `data/selections/*.json` contains named selection files, when a named selection is loaded, then valid song entries are returned in selection order and the loader preserves exact `artist`, `title`, and `song_key` identity.
2. Given a named selection contains malformed entries, missing songs, or mismatched identity fields, when the selection is loaded, then the loader reports recoverable validation errors with `file_path`, `field`, and `reason`, while preserving any valid entries it can validate.
3. Given the same song appears in multiple named selections, when each selection is loaded, then the song remains valid in each selection without duplicating or normalizing raw cache records.
4. Given a named selection file is missing, when it is loaded, then the loader returns empty current state and no errors; when a selection is saved, parent directories under `data/selections/` are created automatically.
5. Given named selections are loaded for later generation, then this story only loads and validates selection-state files and does not apply quality filtering yet.

## Tasks / Subtasks

- [ ] Add `app/selection_state.py` support for named selections while keeping favourites behavior intact.
  - [ ] Define a selection JSON current-state shape that can preserve ordered song keys and file metadata.
  - [ ] Keep selection ordering stable and exact, without lower-casing, trimming, or inferring alternate identities.
  - [ ] Validate selection entries with recoverable field-level errors and preserve valid entries when possible.
  - [ ] Reuse shared identity helpers from `app.content_models` so named selections and favourites follow the same exact song contract.
- [ ] Preserve the existing favourites loader contract while extending the module.
  - [ ] Keep `load_favourites` and `save_favourites` backward compatible.
  - [ ] Do not wire named selections into generation filtering or report rendering in this story.
  - [ ] Keep the module flat and dependency-light, using stdlib `json`, `pathlib`, and existing app helpers.
- [ ] Add focused tests in `tests/test_selection_state.py` and, if needed, `tests/test_content_models.py`.
  - [ ] Round-trip a valid named selection file and verify order preservation.
  - [ ] Verify missing-file loading returns empty state without errors.
  - [ ] Verify malformed JSON, top-level shape errors, and nested identity errors report `file_path`, `field`, and `reason`.
  - [ ] Verify save creates parent directories automatically.
  - [ ] Verify duplicate song presence across selections does not mutate the underlying record contract.
- [ ] Preserve downstream quality semantics while loading selections.
  - [ ] Do not change `app/generation_filtering.py`, `main.py`, or output rendering paths in this story.
  - [ ] Keep selections as metadata only so current quality/review rules still govern inclusion.
- [ ] Verify from the repository root.
  - [ ] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- This story is the second half of Epic 4. It extends the favourites work into named selections without changing quality rules yet.
- The architecture expects selections to live in flat helper modules under `app/`, with JSON as the default inspectable format.
- Preserve exact song identity semantics from the existing cache/review pipeline: keep `artist`, `title`, and derived `song_key` exactly as provided.
- Prefer a top-level JSON object so the file can carry version and update metadata without changing the shape later.
- Validation should follow the same recoverable pattern as `app/review_state.py`: return structured errors instead of raising for file-level and field-level problems when possible.
- Named selection files are out of scope for quality filtering and printable book generation. Story 4.3 owns that behavior.
- If the implementation reuses or extends `app/selection_state.py`, keep the favourites file contract stable and make the new selection helpers additive.

### Project Structure Notes

- Likely implementation file: `app/selection_state.py`
- Possible shared contract update: `app/content_models.py`
- New regression tests: `tests/test_selection_state.py`
- Possible contract test extension: `tests/test_content_models.py`
- Runtime file boundary: `data/selections/*.json`
- Do not touch `main.py` or `app/generation_filtering.py` unless a helper boundary truly requires it.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-4-2-Load-and-Validate-Named-Selections]
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

- Pending implementation.

### Completion Notes List

- Pending implementation.

### File List

- `_bmad-output/implementation-artifacts/4-2-load-and-validate-named-selections.md`

## Change Log

- 2026-05-19: Created story scaffold for named selection loading and validation.

