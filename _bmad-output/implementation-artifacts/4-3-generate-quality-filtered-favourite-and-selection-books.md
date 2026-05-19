# Story 4.3: Generate Quality-Filtered Favourite and Selection Books

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a camper printing a selected book,
I want favourites and named selections to use the same quality rules as default generation,
so that focused books remain trustworthy.

## Acceptance Criteria

1. Given a favourite-only or named-selection generation request includes clean and Questionable songs, when generation filtering runs, then clean accepted songs are included and Questionable songs are excluded by default, and the report lists excluded selected songs and reasons.
2. Given selected songs have matching current review overrides, when generation filtering runs, then overridden songs can be included and the report identifies the override.
3. Given selection-state data from Epic 4 loaders, when filtering runs, then the workflow respects exact `song_key` identity and does not mutate selection files or re-normalize selection content.
4. Given a selected song is missing or invalid in the cache pipeline, when generation filtering runs, then selection awareness does not crash the workflow and the report still explains the exclusion.

## Tasks / Subtasks

- [ ] Extend `app/generation_filtering.py` for favourite and named-selection requests.
  - [ ] Reuse current quality and review gating rules instead of inventing a new selection-specific quality model.
  - [ ] Apply the same default exclusion for Questionable songs used by the normal generation path.
  - [ ] Allow explicit current review overrides to include Questionable selected songs where the existing rules permit it.
- [ ] Keep selection loaders separate from filtering logic.
  - [ ] Consume selection-state data from `app.selection_state` without mutating the loaded selection structures.
  - [ ] Keep favourites and named selections as input metadata only.
  - [ ] Do not change the selection file formats in this story.
- [ ] Add focused regression tests.
  - [ ] Cover favourite-only generation with clean and Questionable songs.
  - [ ] Cover named-selection generation with clean and Questionable songs.
  - [ ] Cover override inclusion for selected songs.
  - [ ] Cover report output for excluded selected songs and reasons.
- [ ] Verify from the repository root.
  - [ ] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- This story bridges the selection loaders from 4.1 and 4.2 with the quality rules already used for default generation.
- Preserve the current local-file, CLI-oriented workflow. The implementation should stay inside helper modules under `app/`.
- Respect exact song identity semantics from the cache/review pipeline. Selection-aware filtering must use exact `song_key` matching and must not globally normalize artist/title data.
- Downstream reporting should explain why a selected song was excluded rather than silently dropping it.
- Keep this story scoped to quality-filtered generation only. Completeness reporting belongs to story 4.4.

### Project Structure Notes

- Likely implementation file: `app/generation_filtering.py`
- Possible reporting update: `app/reporting.py`
- New regression tests: `tests/test_generation_filtering.py`
- Possible reporting tests: `tests/test_reporting.py`
- Selection loader input comes from `app/selection_state.py`
- Do not touch `main.py` unless a helper boundary truly requires it.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-4-3-Generate-Quality-Filtered-Favourite-and-Selection-Books]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-4-Favourites-Selections-and-Quality-Aware-Book-Building]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/prd.md#4-4-Favourites-and-Selections]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR-11-through-FR-13-Favourites-and-Selections]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]
- [Source: _bmad-output/project-context.md#Testing-Rules]
- [Source: app/generation_filtering.py]
- [Source: app/reporting.py]
- [Source: app/review_state.py]
- [Source: app/selection_state.py]
- [Source: tests/test_generation_filtering.py]
- [Source: tests/test_reporting.py]

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- Pending implementation.

### Completion Notes List

- Pending implementation.

### File List

- `_bmad-output/implementation-artifacts/4-3-generate-quality-filtered-favourite-and-selection-books.md`

## Change Log

- 2026-05-19: Created story scaffold for selection-aware quality-filtered generation.

