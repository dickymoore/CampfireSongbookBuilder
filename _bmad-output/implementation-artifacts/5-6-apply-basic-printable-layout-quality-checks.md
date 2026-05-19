# Story 5.6: Apply Basic Printable Layout Quality Checks

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a musician printing a campfire songbook,
I want obvious layout problems flagged before final output,
So that the book avoids unreadable tab wrapping and excessive low-value pages.

## Acceptance Criteria

1. Given accepted content includes very long chord/tab blocks, excessive whitespace, or likely wrapping problems, when printable layout checks run, then the workflow emits print-quality signals or report warnings, and severe print-hostile content can be excluded by default through the same quality filtering path.
2. Given content passes basic print-quality checks, when output artifacts are generated, then no print-quality warning is added for that content.

## Tasks / Subtasks

- [x] Confirm the printable-layout path is already driven by the existing quality assessment helpers.
  - [x] Reuse the centralized print-hostile checks rather than introducing a second layout engine.
  - [x] Preserve default exclusion of severe print-hostile content through the same filtering path used by cached generation.
- [x] Add explicit regression coverage for the layout-warning path.
  - [x] Verify long output content surfaces `print_hostile_content` in the generated report entry.
  - [x] Keep the accepted-content output path unchanged for content that passes the checks.
- [x] Verify from the repository root.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- This story is satisfied by the existing `app.quality_assessment.assess_print_hostile_content()` path and the generation/reporting flow that already carries its signals forward.
- Keep printable-layout checks deterministic and local. The existing line-count, character-count, and longest-line thresholds are the intended basic guardrails.
- Do not add a separate layout optimization or pagination engine for MVP.

### Project Structure Notes

- Primary implementation files: `app/quality_assessment.py`, `app/generation_filtering.py`, `app/document_creation.py`, `app/reporting.py`
- Regression tests: `tests/test_quality_assessment.py`, `tests/test_document_creation.py`, `tests/test_reporting.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5-6-Apply-Basic-Printable-Layout-Quality-Checks]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-5-Offline-Inspectable-Output-Pipeline]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/prd.md#FR-19-Improve-basic-printable-layout-quality]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR-16-through-FR-19-Offline-Inspectable-Output-Pipeline]
- [Source: app/quality_assessment.py]
- [Source: app/generation_filtering.py]
- [Source: app/document_creation.py]
- [Source: app/reporting.py]
- [Source: tests/test_quality_assessment.py]
- [Source: tests/test_document_creation.py]
- [Source: tests/test_reporting.py]

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Confirmed the existing basic printable-layout quality checks were already implemented in the shared quality-assessment helpers and flowed through cache generation and reporting.
- Added explicit regression coverage to prove long content surfaces `print_hostile_content` in the document-generation report entry.
- No additional application code changes were required beyond the regression assertion.

### File List

- `_bmad-output/implementation-artifacts/5-6-apply-basic-printable-layout-quality-checks.md`
- `tests/test_document_creation.py`

## Change Log

- 2026-05-19: Completed basic printable layout quality checks using the existing quality-assessment and reporting pipeline.
