# Story 4.2: Evaluate PDF Neatness with Deterministic Layout Heuristics

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a reviewer,
I want the system to evaluate generated PDFs for print-hostile structure using deterministic heuristics,
so that PDFs that are clearly not reviewable are blocked before I open them.

## Acceptance Criteria

**Given** a run produces a PDF artifact
**When** PDF neatness evaluation runs
**Then** the system applies deterministic rendered-output heuristics such as excessive page count, sparse pages, or text extraction failure
**And** the resulting reasons are recorded in the PDF verification output.

**Given** the same PDF bytes and verification thresholds
**When** PDF verification is rerun
**Then** the same verification outcome is produced
**And** thresholds remain isolated from unrelated generation logic.

## Tasks / Subtasks

- [x] Implement deterministic PDF neatness evaluation in the verification layer (AC: 1, 2)
  - [x] Extend `app/document_verification.py:evaluate_pdf_artifact_neatness(...)` to evaluate *real* PDF structure, not just existence/size.
  - [x] Use a pure-Python PDF reader (`pypdf`) to avoid external tools and keep the evaluation deterministic and testable.
    - [x] Add a pinned dependency in `requirements.txt` (suggested: `pypdf==6.10.2`, matching the current dev environment).
  - [x] Keep the contract stable: return `{verification_status, verification_reasons}` and let `evaluate_document_artifact(...)` build the governed record.
  - [x] Preserve the Story 4.1 semantics:
    - missing/empty PDF -> `failed` with explicit reason codes (do not throw)
    - PDF conversion failure (no file) remains a generation/conversion outcome (`pdf_errors`) and must not be reclassified as verification state.

- [x] Define PDF-specific reason codes and thresholds (AC: 1, 2)
  - [x] Add stable, `snake_case` PDF reason codes in `app/document_verification.py` (similar to existing `missing_pdf` / `empty_pdf`), for example:
    - `pdf_parse_failed` (unreadable PDF bytes)
    - `excessive_page_count`
    - `sparse_pages` (too many pages with near-empty extracted text)
    - `text_extraction_failed` (exceptions during extraction or no extractable text across pages)
  - [x] Keep all new threshold constants co-located with the existing neatness thresholds in `app/document_verification.py` (do not scatter into generation/reporting).
  - [x] Pick explicit default thresholds and encode them as constants (values can be tuned later, but must be deterministic), for example:
    - `PDF_MAX_PAGE_COUNT = 500` (high enough to avoid false positives on large books, low enough to catch runaway layout)
    - `PDF_MIN_EXTRACTED_TEXT_CHARS_PER_PAGE = 30`
    - `PDF_MAX_SPARSE_PAGE_RATIO = 0.6`
    - `PDF_MAX_TEXT_EXTRACTION_FAILURE_RATIO = 0.2` (or `0.0` if any extraction failure should fail)
  - [x] Ensure reason ordering is deterministic (stable ordering in the returned list).

- [x] Heuristic expectations (deterministic, artifact-only) (AC: 1, 2)
  - [x] Evaluate the PDF from local artifact evidence only (bytes/metadata/text extraction outcomes), not from upstream `.docx` results.
  - [x] Implement at least these deterministic checks:
    - excessive page count above a constant threshold
    - sparse pages ratio above a constant threshold (based on extracted text character count per page)
    - text extraction failure for all pages (or an explicit failure threshold) should yield a failing reason
  - [x] If multiple checks fail, include *all* applicable reasons (not just the first).

- [x] Update regression coverage for PDF verification (AC: 1, 2)
  - [x] Update `tests/test_document_verification.py`:
    - Replace `%PDF-FAKE` “non-empty passes” tests with a *valid* minimal PDF fixture (so parse+extract logic is exercised deterministically).
    - Add failing tests that demonstrate:
      - unreadable PDF bytes -> parse/extraction failure reason(s)
      - sparse pages and/or excessive pages -> corresponding reason(s)
  - [x] Update integration/E2E tests that currently write placeholder PDF bytes:
    - `tests/test_e2e_story_4_1_pdf_verification_records.py` currently writes `"pdf"`; replace with a valid minimal PDF fixture so Story 4.1 remains passing after heuristics tighten.
    - If any other tests create `.pdf` files as plain text, update them similarly.
  - [x] Keep tests network-free and tool-free: do not require `soffice` / `pandoc` during unit tests.

- [x] Verify from repository root (AC: 1, 2)
  - [x] Run `python3 -m unittest tests.test_document_verification`.
  - [x] Run `python3 -m unittest tests.test_document_creation`.
  - [x] Run `python3 -m unittest tests.test_e2e_story_4_1_pdf_verification_records`.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Implement this strictly inside the verification layer (`app/document_verification.py`). Do not move PDF conversion logic out of `app/pdf_generation.py`.
- Prefer adding a single, pinned dependency (`pypdf`) rather than relying on system binaries for parsing/extraction.
  - The repo currently pins runtime deps in `requirements.txt`; keep that convention.
- Keep the evaluation deterministic for the same PDF bytes:
  - no random sampling
  - no time-based behavior
  - no environment-dependent heuristics (e.g., font availability, external tools)
- Keep repo-root CLI behavior unchanged (`python3 main.py ...`) and do not introduce new hardcoded runtime paths.

### Project Structure Notes

- PDF conversion: `app/pdf_generation.py` (already produces `pdf_outputs` or `pdf_errors`)
- PDF verification record emission/persistence: `app/document_creation.py` -> `app/document_verification.py` -> `data/review/document_quality.json`
- PDF neatness heuristics implementation target: `app/document_verification.py:evaluate_pdf_artifact_neatness`
- Tests to update/add:
  - `tests/test_document_verification.py`
  - `tests/test_e2e_story_4_1_pdf_verification_records.py`
  - (potentially) `tests/test_document_creation.py` if any assertions depend on the old “any non-empty bytes pass” behavior

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-4-2-Evaluate-PDF-Neatness-with-Deterministic-Layout-Heuristics]
- [Source: _bmad-output/planning-artifacts/architecture.md ("Document Verification Boundary")]
- [Source: _bmad-output/planning-artifacts/architecture.md ("Decision: Govern PDF artifacts in the same verification state model with distinct failure semantics.")]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: _bmad-output/implementation-artifacts/4-1-produce-inspectable-pdf-verification-records.md]
- [Source: app/document_verification.py]
- [Source: app/document_creation.py]
- [Source: app/pdf_generation.py]
- [Source: tests/test_document_verification.py]
- [Source: tests/test_e2e_story_4_1_pdf_verification_records.py]

## Dev Agent Record

### Agent Model Used

GPT-5.2 (Codex CLI)

### Debug Log References

2026-05-31:
- `python3 -m unittest tests.test_document_verification`
- `python3 -m unittest tests.test_document_creation`
- `python3 -m unittest tests.test_e2e_story_4_1_pdf_verification_records`
- `python3 -m unittest tests.test_e2e_story_4_2_pdf_neatness_heuristics`
- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Added deterministic PDF neatness evaluation using `pypdf` with stable reason codes and thresholds.
- Updated PDF-related tests to use valid minimal PDFs and added regression cases for parse failures and sparse pages.
- Consolidated minimal PDF test fixture generation in `tests/pdf_fixtures.py`.

### File List

- app/document_verification.py
- requirements.txt
- tests/test_document_creation.py
- tests/test_document_verification.py
- tests/test_e2e_story_4_1_pdf_verification_records.py
- tests/test_e2e_story_4_2_pdf_neatness_heuristics.py
- tests/pdf_fixtures.py
- _bmad-output/implementation-artifacts/sprint-status.yaml
- _bmad-output/implementation-artifacts/4-2-evaluate-pdf-neatness-with-deterministic-layout-heuristics.md
- _bmad-output/implementation-artifacts/tests/test-summary.md
- _bmad-output/story-automator/orchestration-1-20260527-163528.md
- _bmad-output/implementation-artifacts/_archive/4-2-load-and-validate-named-selections.md

### Change Log

- 2026-05-31: Implement deterministic PDF neatness heuristics with `pypdf` and update regression coverage.
- 2026-05-31: Senior developer review (AI): refactor PDF fixtures, harden PDF parsing, sync sprint status.

## Senior Developer Review (AI)

Date: 2026-05-31

Outcome: Approved (no remaining critical issues).

Findings (fixed):

- Reduced brittle parsing by using non-strict PDF parsing and treated per-page extraction failures as sparse pages to avoid undercounting sparse ratios.
- Eliminated duplicated PDF fixture-writing helpers across multiple test files by consolidating them into `tests/pdf_fixtures.py`.
- Story Dev Agent Record updated to include the additional E2E coverage (`tests/test_e2e_story_4_2_pdf_neatness_heuristics.py`) and ancillary workflow artifacts produced during the story run.
