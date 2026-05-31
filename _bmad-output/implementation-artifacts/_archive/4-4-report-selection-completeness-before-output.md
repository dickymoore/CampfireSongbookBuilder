# Story 4.4: Report Selection Completeness Before Output

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook builder user,
I want selection problems reported before files are generated,
so that I can fix missing or malformed selection entries without inspecting a broken book.

## Acceptance Criteria

1. Given a selection references missing songs, malformed entries, or unavailable content, when the selection is prepared for output, then the workflow reports those issues before rendering Markdown or `.docx`, and recoverable issues are included in the machine-readable report.
2. Given all selected songs are valid and accepted, when generation begins, then no selection-error report blocks output.
3. Given selection-aware generation runs after the Epic 4 loaders, then the completeness check preserves selection order and exact identity and does not mutate selection files.

## Tasks / Subtasks

- [x] Extend document generation to surface selection-completeness issues before output.
  - [x] Collect missing-content selection issues while selection-aware generation is building report entries.
  - [x] Preserve the existing quality and review rules for included and excluded songs.
  - [x] Keep the completeness check inside helper modules rather than the CLI entrypoint.
- [x] Thread selection completeness into the machine-readable report.
  - [x] Add selection-issue data to the returned report payload.
  - [x] Extend traceable quality reporting to include selection-issue counts and details.
  - [x] Keep the report additive and backward-compatible with the existing JSON structure.
- [x] Add focused regression tests.
  - [x] Cover selection-aware document generation with missing content.
  - [x] Cover selection-completeness issues in the report payload.
  - [x] Confirm the full test suite still passes.
- [x] Verify from the repository root.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- This story completes Epic 4 by reporting selection completeness before output is written.
- The completeness data should stay local, inspectable, and additive to the current traceability report.
- Keep the selection-aware generation path using exact `song_key` identity and preserve the existing quality/review semantics from stories 4.1 through 4.3.
- Do not change the file-based CLI behavior unless a helper boundary truly requires it.

### Project Structure Notes

- Likely implementation files: `app/document_creation.py`, `app/reporting.py`
- Possible CLI plumbing update: `main.py`
- New regression tests: `tests/test_document_creation.py`, `tests/test_reporting.py`
- Selection loader input comes from `app.selection_state`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-4-4-Report-Selection-Completeness-Before-Output]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-4-Favourites-Selections-and-Quality-Aware-Book-Building]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/prd.md#4-4-Favourites-and-Selections]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR-11-through-FR-13-Favourites-and-Selections]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]
- [Source: _bmad-output/project-context.md#Testing-Rules]
- [Source: app/document_creation.py]
- [Source: app/reporting.py]
- [Source: app/selection_state.py]
- [Source: main.py]
- [Source: tests/test_document_creation.py]
- [Source: tests/test_reporting.py]

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Added selection-completeness issue tracking to selection-aware document generation.
- Threaded selection-issue data into the traceable quality report and CLI summary path.
- Added regression tests for missing selection content and report payload inclusion.
- Verified the full repository test suite, all passing.

### File List

- `_bmad-output/implementation-artifacts/4-4-report-selection-completeness-before-output.md`
- `app/document_creation.py`
- `app/reporting.py`
- `main.py`
- `tests/test_document_creation.py`
- `tests/test_reporting.py`

## Change Log

- 2026-05-19: Created and completed selection-completeness reporting story.

