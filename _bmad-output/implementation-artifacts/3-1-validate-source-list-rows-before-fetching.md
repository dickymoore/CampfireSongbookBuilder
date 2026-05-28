# Story 3.1: Validate Source List Rows Before Fetching

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user editing the song CSV,
I want malformed song rows reported before fetching,
so that missing artist/title data does not become confusing cache or quality output.

## Acceptance Criteria

1. Given `data/src/CampfireSongs.csv` contains rows with missing or blank artist/title
   values, when the source list is loaded for fetch or generation workflows, then the
   invalid rows are reported with row context and valid rows still proceed where safe.
2. Given rows are marked with `Skip`, when the source list is loaded, then existing
   skip-filtering behavior is preserved.
3. Given a row is invalid, when it is reported, then the report includes at least the CSV
   row number, the raw artist/title values, and the reason the row is invalid.
4. Given valid rows remain after validation, when fetch/generate workflows continue,
   then those rows are passed through unchanged with exact artist/title values.
5. Given this story is implemented, then it keeps the validation layer local to the
   source-list loading path and does not change cache schemas, quality assessment logic,
   or output generation behavior.

## Tasks / Subtasks

- [x] Add source-list row validation in `app/load_songs.py` or a small adjacent helper
  (AC: 1, 2, 3, 4, 5)
  - [x] Detect missing, blank, or whitespace-only artist/title values after CSV load,
        including `NaN`/missing values from `pandas.read_csv`.
  - [x] Preserve the current case-insensitive `Skip` filter so rows marked `skip` remain
        excluded from processing.
  - [x] Keep valid rows unchanged, including exact `Artist` and `Title` text.
  - [x] Emit row-context details that can be logged or summarized later, rather than
        silently dropping malformed rows.
- [x] Wire the loader into the CLI flow if needed in `main.py` (AC: 1, 2, 3, 4)
  - [x] Surface validation warnings before fetch or generation work begins.
  - [x] Keep repo-root CLI behavior unchanged for all existing modes.
  - [x] If a return-shape change is introduced for validation data, update callers and
        any tests that patch `load_songs` so they match the new contract.
- [x] Add focused tests in `tests/test_load_songs.py` and update impacted CLI tests
      if the loader contract changes (AC: 1, 2, 3, 4, 5)
  - [x] Cover missing artist rows and missing title rows.
  - [x] Cover `Skip` rows still being excluded.
  - [x] Cover valid rows being returned intact.
  - [x] Cover row context using original CSV row numbering.
- [x] Verify from the repository root (AC: 1, 2, 3, 4, 5)
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Current `app/load_songs.py` uses `pandas.read_csv` and only filters rows where `Skip`
  lowercases to `skip`; it does not validate blank artist/title fields. [Source:
  app/load_songs.py]
- `main.py` loads songs at the start of every CLI branch, so validation here affects
  fetch, cache-only, generate-from-cache, lyrics-only, chords-only, and get-song-info
  flows. [Source: main.py]
- Downstream helpers like `app/document_generation.py` and
  `app/document_formatting.py` assume each song row has `Artist` and `Title`; letting
  malformed rows through will cause confusing failures later. [Source:
  app/document_generation.py; app/document_formatting.py]
- The project context requires preserving repo-root execution, absolute `app.*` imports,
  flat helpers, `unittest`, and the existing skip-filtering behavior. [Source:
  _bmad-output/project-context.md]
- Architecture maps FR-8 to `app/load_songs.py`, `main.py`, and reporting tests. This
  story is the source-list validation slice of that feature. [Source:
  _bmad-output/planning-artifacts/architecture.md]
- Previous story context: none. This is the first implementation story in Epic 3.
- `pandas.read_csv` treats empty strings as missing values by default, so the validator
  should not assume blank cells arrive as literal empty strings; check for missing/`NaN`
  values and whitespace-only text. [Source:
  https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html]

### Suggested Validation Record Shape

If the implementation surfaces structured invalid-row data, keep it simple and
machine-readable:

```python
{
    "row_number": 12,
    "artist": None,
    "title": "Trail Song",
    "skip": "",
    "reason": "missing artist",
}
```

Use original CSV row numbering so the user can find the row in the source file quickly.
Keep valid song rows unchanged; validation should only annotate or exclude malformed
rows, not normalize the song identity itself.

### Project Structure Notes

- Likely touch `app/load_songs.py`, maybe `main.py`, and tests under
  `tests/test_load_songs.py`.
- Keep the loader small and flat; do not move this into a new package.
- If the return contract changes, update the existing CLI tests that patch `load_songs`
  so they match the new shape.
- Prefer a backward-compatible loader API if possible; if not, make the validation
  return shape explicit and update all callers together.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3-1-Validate-Source-List-Rows-Before-Fetching]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/prd.md#4-3-Easier-Song-Addition]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping]
- [Source: _bmad-output/planning-artifacts/architecture.md#File-Organization-Patterns]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: app/load_songs.py]
- [Source: main.py]
- [Source: app/document_generation.py]
- [Source: app/document_formatting.py]
- [Source: tests/test_reporting.py]
- [Source: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Implemented row validation and logging in `app/load_songs.py` and exposed structured
  invalid-row records.
- Updated the loader to validate before skip filtering, return structured invalid-row
  records, and surface a CLI summary in `main.py`.
- Added regression coverage in `tests/test_load_songs.py` for invalid rows, malformed
  skipped rows, exact valid row text, and original CSV row numbers.
- Updated impacted CLI tests in `tests/test_reporting.py` for the revised loader
  contract.
- Verified the full test suite from the repository root with
  `python3 -m unittest discover -s tests -p 'test_*.py'`.

### Completion Notes List

- Invalid source rows are now logged with row number, raw CSV values, and a reason.
- Existing case-insensitive `Skip` filtering remains in place.
- Valid rows continue through unchanged, preserving their original `Artist` and
  `Title` values.
- Invalid rows now surface as structured validation records so callers can summarize
  them without scraping logs.

## Senior Developer Review (AI)

- Validation was moved ahead of skip filtering so malformed rows marked `Skip` are
  still reported before being excluded from processing.
- The loader now returns `(songs, invalid_rows)`, and `main.py` logs a summary so the
  new validation layer is visible before generation work starts.
- Regression coverage now proves valid rows remain unchanged, malformed skipped rows
  are reported, and original CSV row numbers are preserved.

### Review Run (2026-05-28)

- Verified AC coverage in `app/load_songs.py` and `main.py`, including row-number
  reporting, skip preservation, and passthrough of valid rows.
- Noted git working tree contains unrelated in-progress changes (separate story); this
  review validated behavior at the current repository state rather than relying on a
  local diff for this story.
- Synced sprint tracking by adding the missing story key
  `3-1-validate-source-list-rows-before-fetching: done` to
  `_bmad-output/implementation-artifacts/sprint-status.yaml`.
- Quieted the E2E story test by capturing stdout so full-suite runs stay clean.

### File List

- app/load_songs.py
- main.py
- tests/test_load_songs.py
- tests/test_reporting.py
- tests/test_e2e_story_3_1_invalid_source_rows_generate_from_cache.py
- _bmad-output/implementation-artifacts/sprint-status.yaml

### Change Log

- 2026-05-19: Added source-list row validation, preserved skip filtering, logged
  malformed rows with row context, added tests, and marked the story ready for review.
- 2026-05-19: Review auto-fix updated validation ordering, returned structured invalid
  rows, surfaced a CLI summary, and expanded regression coverage for skipped malformed
  rows.
- 2026-05-28: Story-automator review verified implementation, synced sprint status,
  and updated the E2E story test to suppress stdout noise.

### Status

done
