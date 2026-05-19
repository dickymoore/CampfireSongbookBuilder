# Story 5.4: Generate `.docx` from Accepted Content

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a camper preparing a printable book,
I want `.docx` generation to use the accepted content set,
so that the Word document does not contain known bad songs by default.

## Acceptance Criteria

1. Given accepted songs and Markdown/report artifacts exist for a generation run, when `.docx` generation runs, then the Word document is generated from accepted content only and existing document formatting responsibilities remain inside document-generation helpers.
2. Given songs were excluded by quality or review rules, when the `.docx` is generated, then excluded songs do not appear in the Word document body.
3. Given selection-aware generation is used, when `.docx` generation runs, then the Word document preserves the accepted selection order and still reflects the same filtered content set as Markdown.

## Tasks / Subtasks

- [x] Preserve the accepted-content `.docx` generation path.
  - [x] Keep formatting concerns inside document-generation helpers.
  - [x] Generate the Word document only from accepted content.
  - [x] Keep the document path local and inspectable.
- [x] Verify excluded content stays out of the Word document.
  - [x] Keep quality/review exclusions visible in the report, not the `.docx` body.
  - [x] Preserve selection-aware ordering where applicable.
- [x] Confirm regression coverage exists.
  - [x] Existing document-generation tests cover the `.docx` output path and accepted/excluded content behavior.
- [x] Verify from the repository root.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- This story is satisfied by the existing document-generation implementation and the regressions already added while building the earlier stories.
- Keep `.docx` generation paired with the accepted-content pipeline, not a separate rendering path.
- The Word document should remain a local artifact produced from the same filtered content as the Markdown output.

### Project Structure Notes

- Primary implementation file: `app/document_creation.py`
- Regression tests: `tests/test_document_creation.py`
- Output files remain under `data/output/`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5-4-Generate-docx-from-Accepted-Content]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-5-Offline-Inspectable-Output-Pipeline]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]
- [Source: _bmad-output/project-context.md#Testing-Rules]
- [Source: app/document_creation.py]
- [Source: tests/test_document_creation.py]

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Existing document-generation helpers already produce `.docx` from the accepted content set only.
- Regression tests cover excluded content staying out of the document body and selection-aware ordering.
- No additional code changes were required for this story.

### File List

- `_bmad-output/implementation-artifacts/5-4-generate-docx-from-accepted-content.md`

## Change Log

- 2026-05-19: Recorded `.docx` generation story as complete based on the existing accepted-content pipeline and tests.

