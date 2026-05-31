# Story 4.4: Propagate PDF Gate Outcomes Through Reporting and Re-Evaluation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook operator,
I want PDF verification and review-ready outcomes to propagate into reporting and post-change re-evaluation,
so that agents can reason about PDF readiness and refresh it after regeneration or remediation.

## Acceptance Criteria

1. **Given** a run includes a PDF generation/conversion failure  
   **When** reporting runs  
   **Then** the output distinguishes generation failure from PDF verification failure  
   **And** the run state remains machine-readable and inspectable.

2. **Given** a run includes a PDF that failed verification or is not review-ready  
   **When** reporting or review gating runs  
   **Then** the PDF is clearly identified as blocked from manual review  
   **And** the output distinguishes PDF gate failures from song-content quality issues.

3. **Given** a regeneration or remediation changes downstream artifacts including PDF  
   **When** post-change verification runs  
   **Then** relevant PDF verification and review-ready outcomes are refreshed before escalation or final review decisions  
   **And** stale PDF gate state is not left in place.

## Tasks / Subtasks

- [x] Propagate PDF generation/conversion failures into the same report-level “manual review” surface (AC: 1)
  - [x] Keep the semantic separation intact:
    - conversion/generation failures remain represented as `pdf_errors` (machine-readable)
    - PDF verification failures remain represented as governed `document_verification` + `review_gate_decisions`
  - [x] Update `app/reporting.py` to surface PDF conversion failures as *manual-review blockers* without pretending they are verification outcomes.
    - Recommended: extend `manual_review_gate` with a dedicated list (e.g., `generation_failures`) or extend `blocked_artifacts` entries with `blocking_stage="pdf_generation"` for `pdf_errors`.
    - Ensure the representation is machine-readable and does not require parsing the human summary string.
  - [x] Ensure output can distinguish:
    - “PDF missing because conversion failed” (from `pdf_errors`) vs
    - “PDF exists and failed neatness verification” (from `document_verification`/`review_gate_decisions`).
  - [x] Keep ordering deterministic (stable ordering for any derived PDF generation-failure gate entries).

- [x] Ensure PDF verification + review gate outcomes remain visible (and not conflated with song quality) (AC: 2)
  - [x] Preserve the existing contract where PDF verification records (when a PDF exists) flow through:
    - `app/document_creation.py` → `document_verification` records
    - `app/review_gate.py` → `review_gate_decisions`
    - `app/reporting.py` → `manual_review_gate` blocked/ready artifacts
  - [x] Confirm PDF artifacts appear in `manual_review_gate.blocked_artifacts` when verification fails (PDF exists, `verification_status="failed"`).
  - [x] Ensure any new generation-failure surface does not change how song-quality counts are computed (keep PDF gate failures separate from `missing/questionable/clean` song classification).

- [x] Refresh PDF outcomes after regeneration/remediation (AC: 3)
  - [x] Regeneration path: when a run requests PDF output, ensure the report-level surfaces always reflect the *current run’s* PDF evidence (success, conversion failure, verification result) and do not “inherit” a stale PDF-ready impression from prior state.
  - [x] Stale-state hazard to address explicitly: `app/document_creation.py` currently merges verification records into `data/review/document_quality.json` only for artifacts that produce a verification record in the current run. If a previous run produced a PDF verification record but the current run requests PDF output and conversion fails (no PDF verification record), the persisted verification entry can remain and mislead downstream consumers. Ensure the refreshed current-state model does not leave an old “PDF passed/failed” verification entry standing in for a run where PDF generation failed.
    - One acceptable approach: when `pdf_output=True` and conversion fails for a specific `target` PDF path, remove any existing verification entry for that PDF path from `data/review/document_quality.json` (while still recording the conversion failure via `pdf_errors`).
  - [x] Remediation re-evaluation path: if post-remediation evaluation verifies downstream artifacts, ensure PDF artifacts are handled consistently with FR-13 semantics:
    - if a PDF exists, verify it and compute its review gate decision
    - if PDF conversion failed, record that as a generation/conversion outcome (not a verification record) and ensure downstream escalation/reporting can distinguish it from verification failure
  - [x] Keep `app/review_gate.py` focused on converting governed verification records into decisions; do not push generation/conversion semantics into `app/review_gate.py`.

- [x] Add/extend regression coverage (AC: 1–3)
  - [x] Unit: extend `tests/test_reporting.py` to assert the PDF conversion failure surface is present and clearly distinct from verification failures.
  - [x] E2E: add `tests/test_e2e_story_4_4_pdf_gate_propagation.py` (pattern matches existing Story 4.x E2Es) that exercises:
    - converter failure (`pdf_errors` present, no PDF verification record)
    - converter success + failing PDF verification (PDF exists, PDF appears in `manual_review_gate.blocked_artifacts`)
    - converter success + passing PDF verification (PDF appears in `manual_review_gate.ready_artifacts`)
  - [x] If remediation re-evaluation is updated for PDF generation failure distinction, extend `tests/test_remediation.py` with a focused case.

## Dev Notes

- This epic already has working foundations from Stories 4.1–4.3:
  - PDF conversion result capture: `app/document_creation.py` (`pdf_outputs`, `pdf_errors`)
  - PDF neatness verification: `app/document_verification.py` (`artifact_type="pdf"`, deterministic reason codes)
  - PDF review gate decisions: `app/review_gate.py` (derives `review_ready` from governed verification records)
  - Traceability reporting: `app/reporting.py` (includes `pdf_outputs`, `pdf_errors`, `document_verification`, `review_gate_decisions`, `manual_review_gate`)
- The main gap for Story 4.4 is ensuring that *run-level reporting and post-change evaluation* consistently surface PDF readiness/failure states with explicit “generation vs verification” distinction, and without leaving downstream consumers with stale PDF gate assumptions.
- Keep repo-root execution and import rules (`python3 main.py`, `from app...`) intact.
- Do not reclassify conversion failure into a fake PDF verification record (Story 4.1 explicitly separated these concerns).

### Project Structure Notes

- Generation + conversion evidence: `app/document_creation.py`, `app/pdf_generation.py`
- Verification + persistence: `app/document_verification.py` → `data/review/document_quality.json`
- Gate decisions: `app/review_gate.py`
- Report aggregation and manual-review surface: `app/reporting.py`
- Post-change re-evaluation (if touched): `app/remediation.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-4-4-Propagate-PDF-Gate-Outcomes-Through-Reporting-and-Re-Evaluation]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-13-Govern-PDF-as-a-first-class-output-artifact]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#10-3-Governed-PDF-Artifact-Semantics]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR-Category-Document-Neatness-Evaluation-app-document_verification-py-data-review-document_quality-json]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR-Category-Agentic-Verification-Before-Manual-Review-app-review_gate-py-app-reporting-py]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]
- [Source: _bmad-output/project-context.md#Testing-Rules]
- [Source: _bmad-output/implementation-artifacts/4-1-produce-inspectable-pdf-verification-records.md]
- [Source: _bmad-output/implementation-artifacts/4-2-evaluate-pdf-neatness-with-deterministic-layout-heuristics.md]
- [Source: _bmad-output/implementation-artifacts/4-3-gate-manual-review-on-pdf-verification-results.md]
- [Source: app/document_creation.py]
- [Source: app/pdf_generation.py]
- [Source: app/document_verification.py]
- [Source: app/review_gate.py]
- [Source: app/reporting.py]
- [Source: app/remediation.py]
- [Source: tests/test_reporting.py]
- [Source: tests/test_document_creation.py]
- [Source: tests/test_e2e_story_4_1_pdf_verification_records.py]
- [Source: tests/test_e2e_story_4_2_pdf_neatness_heuristics.py]
- [Source: tests/test_e2e_story_4_3_pdf_review_gate.py]

## Dev Agent Record

### Agent Model Used

GPT-5.2 (Codex CLI)

### Debug Log References

- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- `app/reporting.py`: surface PDF generation/conversion failures as machine-readable manual-review blockers via `manual_review_gate.generation_failures` (keeps semantic separation from governed verification).
- `app/document_creation.py`: remove stale persisted PDF verification entries from `data/review/document_quality.json` when a run requests PDF output but conversion fails (prevents stale PDF gate state).
- Added regression coverage for generation-vs-verification distinction, plus stale-state cleanup.

### File List

- `app/reporting.py`
- `app/document_creation.py`
- `tests/test_reporting.py`
- `tests/test_document_creation.py`
- `tests/test_e2e_story_4_4_pdf_gate_propagation.py`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/tests/test-summary.md`
- `_bmad-output/implementation-artifacts/4-4-propagate-pdf-gate-outcomes-through-reporting-and-reevaluation.md`
- `_bmad-output/story-automator/orchestration-1-20260527-163528.md`

## Change Log

- Add `manual_review_gate.generation_failures` to report PDF conversion failures as manual-review blockers without creating fake verification records.
- Drop stale persisted PDF verification entries when conversion fails so downstream consumers cannot infer outdated PDF readiness.
- Add Story 4.4 regression tests covering generation failure surface and PDF gate propagation.
- 2026-05-31: Senior developer review completed; hardened PDF error path normalization and stale-verification cleanup; story marked done.

## Senior Developer Review (AI)

Reviewer: Dicky  
Date: 2026-05-31  
Outcome: Approved (with fixes applied)

### Context Loaded

- Project standards: `_bmad-output/project-context.md`
- Epic reference: `_bmad-output/planning-artifacts/epics.md` (Epic 4 / Story 4.4)
- Epic tech spec: `_bmad-output/planning-artifacts/architecture.md` + PRD references in story Dev Notes
- External/MCP doc search: not required for this change (local code + tests only)

### Acceptance Criteria Validation

- AC1 (generation failure vs verification failure is distinguishable and inspectable): Implemented via `pdf_errors` + `manual_review_gate.generation_failures` in `app/reporting.py`; verified by `tests/test_reporting.py` + `tests/test_e2e_story_4_4_pdf_gate_propagation.py`.
- AC2 (verification failures block manual review without conflating song quality): Verified that governed `document_verification` records flow to `review_gate_decisions` and appear in `manual_review_gate.blocked_artifacts` (PDF failures stay separate from per-song quality counts); verified by E2E + existing report contract tests.
- AC3 (post-change refresh avoids stale PDF gate state): Implemented stale-entry removal when `pdf_output=True` but conversion fails, so persisted `data/review/document_quality.json` cannot retain an old PDF verification result for a run with generation failure; verified by `tests/test_document_creation.py`.

### Findings

MEDIUM
- Report contract hardening: `build_traceable_quality_report()` previously passed through non-string `pdf_errors[*].source/target` values and used raw `artifact_type` keys, which can break JSON serialization and cause duplicate/manual gate entries when path-like inputs or non-normalized artifact types are supplied. Fixed by normalizing `pdf_errors` path values to strings and lowercasing artifact keys in `app/reporting.py`.
- Defensive stale-state cleanup: conversion-failure cleanup was only applied when there were new verification records. Fixed by persisting removal requests even if the verification-record list is empty in `app/document_creation.py`.

LOW
- Git/story drift: additional modified artifacts were present in the working tree outside the story’s original File List (e.g., story-automator tooling). Updated the story File List for the tracked story-automation artifacts; remaining `.agents/` modifications are outside the story scope and are blocked by workspace permissions in this environment.

### Verification

- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Security Notes

- No new dependencies or network calls introduced.
- Changes are limited to report shaping and persistence cleanup logic; tests use `unittest` and temp directories.
