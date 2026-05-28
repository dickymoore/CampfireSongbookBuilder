# Story 4.1: Produce Inspectable PDF Verification Records

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook operator,
I want a generated PDF to emit a machine-readable verification record,
So that agents and reports can inspect PDF quality state without scraping console output.

## Acceptance Criteria

**Given** a run produces a PDF file successfully
**When** PDF verification runs
**Then** the system writes a local verification record with artifact identity, artifact type `pdf`, verification status, reasons, and timestamp
**And** the record uses the same governed verification state model as other artifact types.

**Given** PDF conversion or generation fails before a file is created
**When** run state is recorded
**Then** the failure is recorded distinctly as a generation/conversion outcome rather than a verification result
**And** downstream agents can distinguish missing-artifact generation failure from failed PDF quality checks.

## Tasks / Subtasks

- [x] Extend the governed document-verification contract to support `pdf` artifacts (AC: 1)
  - [x] Update `app/document_verification.py` to allow `artifact_type="pdf"` (do not invent a parallel state model).
  - [x] Ensure `build_document_verification_record(...)`, load/save validation, and `validate_artifact_type(...)` accept `pdf`.
  - [x] Add a dedicated PDF evaluation entrypoint (even if the initial implementation is intentionally minimal) so later PDF heuristics can be added without reworking the contract.
- [x] Emit and persist PDF verification records only when a PDF file exists (AC: 1, 2)
  - [x] In `app/document_creation.py`, when `pdf_output=True` and `convert_document_to_pdf(...)` returns a real output path, emit a `pdf` verification record and include it in the returned `document_verification` list.
  - [x] Persist the `pdf` verification record into `data/review/document_quality.json` via the existing merge/save flow (same current-state file as Markdown and `.docx`).
  - [x] Do **not** create a verification record when PDF conversion fails to produce a file; that scenario must remain a generation/conversion outcome only.
- [x] Preserve distinct conversion/generation failures as run-state evidence (AC: 2)
  - [x] Keep PDF conversion failures represented in machine-readable run output (the traceable quality report’s `pdf_errors`) rather than misclassifying them as a document verification result.
  - [x] Ensure downstream reporting can distinguish:
    - “No PDF exists because conversion failed” vs
    - “A PDF exists and failed verification”.
- [x] Add focused regression coverage for the PDF verification record lifecycle (AC: 1, 2)
  - [x] Extend `tests/test_document_verification.py` to cover `artifact_type="pdf"` record validation and evaluation entrypoints.
  - [x] Extend `tests/test_document_creation.py` to verify:
    - converter success → `pdf_outputs` includes the file and `document_verification` includes a `pdf` record persisted into `data/review/document_quality.json`
    - converter failure → `pdf_errors` contains a conversion failure record and **no** `pdf` verification record is emitted.
- [x] Verify from the repository root (AC: 1, 2)
  - [x] Run `python3 -m unittest tests.test_document_verification`.
  - [x] Run `python3 -m unittest tests.test_document_creation`.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Reuse the existing verification contract and persistence surface from Stories `1.1` and `1.2`:
  - Current-state verification lives in `data/review/document_quality.json`.
  - Verification records are built via `app/document_verification.py`.
  - Document generation calls into verification from `app/document_creation.py`.
- Keep responsibilities separated:
  - `app/pdf_generation.py` owns conversion and converter selection.
  - `app/document_verification.py` owns verification record creation and (eventually) PDF neatness heuristics.
  - `app/reporting.py` remains the machine-readable run aggregation surface, including conversion failures (`pdf_errors`) and verification outputs (`document_verification`).
- Do **not** change repo-root CLI behavior or introduce new runtime paths in this story. Produce the PDF verification record for the PDF path the system actually generated.
- Avoid adding heavyweight PDF parsing dependencies in this story. The goal is a stable record contract and generation/verification separation; deterministic PDF neatness heuristics are owned by Story `4.2`.

### Project Structure Notes

- PDF conversion: `app/pdf_generation.py`, called from `app/document_creation.py`
- Verification contract & persistence: `app/document_verification.py` → `data/review/document_quality.json`
- Run aggregation: `app/reporting.py` (expects `pdf_outputs`, `pdf_errors`, `document_verification`)
- Gate computation will consume verification records: `app/review_gate.py` (do not expand scope into PDF gate logic here)
- Tests to extend: `tests/test_document_verification.py`, `tests/test_document_creation.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-4-1-Produce-Inspectable-PDF-Verification-Records]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-4-PDF-Output-Verification-and-Agentic-Quality-Gates]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-13-Govern-PDF-as-a-first-class-output-artifact]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#103-Governed-PDF-Artifact-Semantics]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision-Govern-PDF-artifacts-in-the-same-verification-state-model-with-distinct-failure-semantics]
- [Source: _bmad-output/planning-artifacts/architecture.md#Document-Verification-Boundary]
- [Source: _bmad-output/planning-artifacts/architecture.md#Service-and-Data-Integration-Boundaries]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]
- [Source: app/document_creation.py]
- [Source: app/document_verification.py]
- [Source: app/pdf_generation.py]
- [Source: app/reporting.py]
- [Source: app/review_gate.py]
- [Source: tests/test_document_creation.py]
- [Source: tests/test_document_verification.py]

## Dev Agent Record

### Agent Model Used

GPT-5.2 (Codex CLI)

### Debug Log References

- `bmad-create-story story 4.1`
- `python3 -m unittest tests.test_document_verification`
- `python3 -m unittest tests.test_document_creation`
- `python3 -m unittest tests.test_e2e_story_4_1_pdf_verification_records`
- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added `pdf` to governed artifact verification contract and introduced a minimal PDF evaluation entrypoint.
- Emitted/persisted `pdf` verification records only when conversion produces a real PDF, preserving `pdf_errors` as conversion evidence.
- Updated regression coverage for the PDF verification record lifecycle; all tests pass.

### File List

- `_bmad-output/implementation-artifacts/4-1-produce-inspectable-pdf-verification-records.md`
- `_bmad-output/implementation-artifacts/_archive/4-1-load-and-validate-favourite-songs.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/tests/test-summary.md`
- `_bmad-output/story-automator/orchestration-1-20260527-163528.md`
- `app/document_creation.py`
- `app/document_verification.py`
- `tests/test_document_creation.py`
- `tests/test_document_verification.py`
- `tests/test_e2e_story_4_1_pdf_verification_records.py`

## Change Log

- 2026-05-28: Created story file for Epic 4 PDF verification record contract and generation/conversion failure separation.
- 2026-05-28: Implemented PDF verification record emission/persistence and added regression coverage; marked story ready for review.
- 2026-05-28: Senior developer review complete; fixed `.md` artifact-type inference for document verification and updated documentation for full change set.

## Senior Developer Review (AI)

Date: 2026-05-28
Outcome: Approved

### Acceptance Criteria Audit

- AC1 (PDF exists → verification record written with governed model): Implemented via `evaluate_document_artifact(..., artifact_type="pdf")` and persistence through `data/review/document_quality.json`.
- AC2 (PDF conversion failure remains a generation/conversion outcome, not verification): Implemented via `pdf_errors` records only when conversion fails, and no `pdf` verification record is emitted when there is no PDF output path.

### References Consulted

- `_bmad-output/project-context.md`
- `_bmad-output/planning-artifacts/architecture.md` (PDF governance decision + failure semantics)

### Findings (Fixed)

- [HIGH] `evaluate_document_artifact()` rejected `.md` paths when `artifact_type` was omitted (suffix is `md`, governed type is `markdown`), which could break call sites that pass artifact paths without an explicit type. Fixed by mapping `.md` → `markdown` and adding regression coverage.
- [MEDIUM] Dev Agent Record file list and debug logs were missing the E2E test and automation artifacts touched during story orchestration; updated for traceability.

### Verification

- `python3 -m unittest tests.test_document_verification`
- `python3 -m unittest tests.test_document_creation`
- `python3 -m unittest tests.test_e2e_story_4_1_pdf_verification_records`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
