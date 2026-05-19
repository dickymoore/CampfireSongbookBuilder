# Story 5.5: Add Recoverable Optional PDF Conversion

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook builder user,
I want an optional PDF output path after Markdown and `.docx`,
so that I can print or share a final artifact when local tooling supports it.

## Acceptance Criteria

1. Given Markdown and `.docx` artifacts have been produced, when optional PDF conversion is requested and the converter is available, then a PDF is written under `data/output/` and the report records the PDF artifact path.
2. Given PDF conversion is requested but the converter is missing or fails, when the failure occurs, then the workflow reports the failure as recoverable and Markdown and `.docx` artifacts are not deleted or modified.
3. Given PDF conversion is requested for both lyrics and chords outputs, when conversion succeeds, then each requested output may produce its own local PDF artifact and the report records the successful artifact paths.

## Tasks / Subtasks

- [x] Add optional PDF conversion alongside the accepted-content output path.
  - [x] Convert after Markdown and `.docx` generation has completed.
  - [x] Keep Markdown and `.docx` artifacts intact when conversion fails.
  - [x] Support local converter tooling in a recoverable way.
- [x] Thread PDF artifact details into the traceable report.
  - [x] Record successful PDF artifact paths in the returned report payload.
  - [x] Record recoverable PDF failures without deleting earlier artifacts.
- [x] Add focused regression coverage.
  - [x] Cover PDF success and failure in document generation.
  - [x] Cover PDF artifact recording in the traceable report.
- [x] Verify from the repository root.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- This story layers PDF conversion onto the existing Markdown and `.docx` pipeline rather than replacing it.
- Keep the PDF conversion optional and recoverable. The absence of local converter tooling should not break earlier output artifacts.
- The report should preserve the PDF path or failure reason alongside the other local artifact details.

### Project Structure Notes

- Likely implementation files: `app/document_creation.py`, `app/pdf_generation.py`, `app/reporting.py`
- New or updated regression tests: `tests/test_document_creation.py`, `tests/test_reporting.py`
- Output files remain under `data/output/`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5-5-Add-Recoverable-Optional-PDF-Conversion]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-5-Offline-Inspectable-Output-Pipeline]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]
- [Source: _bmad-output/project-context.md#Testing-Rules]
- [Source: app/document_creation.py]
- [Source: app/pdf_generation.py]
- [Source: app/reporting.py]
- [Source: tests/test_document_creation.py]
- [Source: tests/test_reporting.py]

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Added an optional PDF conversion helper and wired it into the document-generation pipeline.
- Kept Markdown and `.docx` artifacts intact when PDF conversion is missing or fails.
- Recorded PDF artifact paths and recoverable PDF failures in the traceable report.
- Verified the full repository test suite, all passing.

### File List

- `_bmad-output/implementation-artifacts/5-5-add-recoverable-optional-pdf-conversion.md`
- `app/document_creation.py`
- `app/pdf_generation.py`
- `app/reporting.py`
- `main.py`
- `tests/test_document_creation.py`
- `tests/test_reporting.py`

## Change Log

- 2026-05-19: Completed optional PDF conversion and recovery handling.

