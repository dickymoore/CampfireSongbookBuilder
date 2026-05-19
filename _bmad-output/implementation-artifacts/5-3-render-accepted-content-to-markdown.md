# Story 5.3: Render Accepted Content to Markdown

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook builder user,
I want a Markdown songbook generated before `.docx`,
so that I or an AI agent can inspect the exact accepted content before document conversion.

## Acceptance Criteria

1. Given generation filtering produces accepted songs, when Markdown rendering runs, then a `.md` songbook is written under `data/output/` and it includes only accepted content according to quality and review decisions.
2. Given songs were excluded from the output, when Markdown output is produced, then excluded content is not included in the book body and exclusions remain available in the report.
3. Given selection-aware generation runs, when Markdown is written, then the Markdown artifact reflects the same accepted content set as the `.docx` output and preserves selection order.

## Tasks / Subtasks

- [x] Add Markdown output alongside the existing document-generation path.
  - [x] Render accepted lyrics/chords content into inspectable `.md` files before saving `.docx`.
  - [x] Keep the Markdown file local, additive, and generated from the same accepted-content set as the Word document.
  - [x] Preserve the existing document-generation responsibilities inside helper modules.
- [x] Keep exclusions visible in the traceable report.
  - [x] Ensure excluded content remains represented in the machine-readable report.
  - [x] Keep the Markdown body focused on accepted content only.
- [x] Add focused regression coverage.
  - [x] Verify Markdown files are written alongside document output.
  - [x] Verify excluded songs stay out of the Markdown body.
- [x] Verify from the repository root.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- This story adds the Markdown inspection step without changing the accepted-content rules.
- Keep the Markdown output aligned with the same selection-aware and quality-aware content that feeds the `.docx` generator.
- The Markdown file should be produced locally and inspectably before the Word document save happens.

### Project Structure Notes

- Likely implementation file: `app/document_creation.py`
- New or updated regression tests: `tests/test_document_creation.py`
- Output files remain under `data/output/`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5-3-Render-Accepted-Content-to-Markdown]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-5-Offline-Inspectable-Output-Pipeline]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/prd.md#4-5-Offline-Generation]
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

- Added Markdown rendering to the document-generation path so accepted content is written to `.md` before `.docx`.
- Kept excluded songs out of the Markdown body while preserving them in the report payload.
- Added regression coverage for Markdown file creation and content exclusion.
- Verified the full repository test suite, all passing.

### File List

- `_bmad-output/implementation-artifacts/5-3-render-accepted-content-to-markdown.md`
- `app/document_creation.py`
- `tests/test_document_creation.py`

## Change Log

- 2026-05-19: Completed Markdown rendering and verification.

