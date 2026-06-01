# Story 1.5: Refresh Artifact Gates After Regeneration or Re-Verification

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook operator,
I want artifact gate outcomes refreshed after regeneration or follow-up verification,
so that escalation and downstream workflows use current evidence rather than stale state.

## Acceptance Criteria

1. Given a regeneration or follow-up verification pass updates one or more artifacts, when artifact verification reruns, then the latest verification and review-ready results replace stale current-state outcomes, and artifact identity remains explicit.
2. Given remediation or regeneration affects a PDF-producing run, when post-change verification completes, then relevant PDF gate outcomes are refreshed before escalation or review decisions are finalized, and PDF is not treated as an ungoverned byproduct.
3. Given unchanged artifacts are rechecked, when the same thresholds and artifact bytes are used, then the verification outcome remains deterministic.

## Tasks / Subtasks

- [x] Define what "artifact identity" means for refresh semantics (AC: 1, 3)
  - [x] Confirm the identity keys used by the verification record contract from Story 1.1 (e.g. `artifact_path` + `artifact_type`) and use those as the stable replacement key.
  - [x] Ensure refresh semantics do not accidentally merge distinct artifacts from the same run (e.g. markdown vs docx vs pdf).

- [x] Implement "refresh" behavior for document verification current-state persistence (AC: 1, 3)
  - [x] When saving verification results, replace existing entry for the same artifact identity instead of appending duplicates.
  - [x] Update `updated_at` / `verified_at` fields consistently so downstream agents can tell "new evidence" exists.
  - [x] Keep behavior deterministic given the same inputs (stable ordering, stable identity mapping).

- [x] Implement "refresh" behavior for review-gate decisions (AC: 1, 3)
  - [x] Ensure review-ready decisions are recomputed from the latest verification/neatness evidence, not cached stale values.
  - [x] When persisting review-gate results, replace prior decision records for the same artifact identity.

- [x] Ensure refresh is invoked in the pipeline paths that can produce stale evidence (AC: 1)
  - [x] Identify the code path(s) that re-run verification after regeneration/re-verification and ensure they call the same persistence helpers (no parallel formats).
  - [x] Verify reporting reads the current-state files and does not keep its own shadow copy.

- [x] PDF-aware refresh semantics (AC: 2)
  - [x] Ensure that when PDF is part of the run, the refresh behavior covers PDF verification + gate results using the same identity semantics.
  - [x] Ensure PDF generation/conversion failure remains distinct from PDF verification failure in the persisted state model.

- [x] Add regression tests (AC: 1-3)
  - [x] Test "replace not append": saving a second result for the same artifact identity overwrites (or replaces) the existing record and does not create duplicates.
  - [x] Test determinism: same input snapshot produces same persisted outcome.
  - [x] If PDF is in-scope in code, add at least one focused test that proves PDF refresh does not collide with docx/markdown identity.

- [x] Verify from repo root (AC: 1-3)
  - [x] Run focused tests added/updated for this story.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- This story is intentionally about "current-state correctness" and should avoid broad refactors.
- Reuse and extend existing persistence contracts and helper modules created by Stories 1.1-1.4; do not introduce a parallel state format.
- Avoid changing raw cache semantics (`data/cache/*.jsonl`). This is artifact verification/gating state only.
- Keep changes compatible with repo-root execution (`python3 main.py ...`).

### Project Structure Notes

- Persist artifact verification state under `data/review/` (current-state) and keep it machine-readable and inspectable.
- Keep `main.py` thin; implement refresh behavior in focused helpers under `app/`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1-5-Refresh-Artifact-Gates-After-Regeneration-or-Re-Verification]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-1-Evaluate-generated-documents-for-neatness]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-13-Govern-PDF-as-a-first-class-output-artifact]
- [Source: _bmad-output/planning-artifacts/architecture.md#State-Management-Patterns]
- [Source: _bmad-output/implementation-artifacts/1-1-produce-inspectable-document-verification-records.md]
- [Source: _bmad-output/implementation-artifacts/1-2-evaluate-artifact-neatness-with-deterministic-heuristics.md]
- [Source: _bmad-output/implementation-artifacts/1-3-compute-review-ready-gate-decisions.md]
- [Source: _bmad-output/implementation-artifacts/1-4-gate-manual-review-and-reporting-on-verification-results.md]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]

## Dev Agent Record

### Agent Model Used

GPT-5.2 (Codex CLI)

### Debug Log References

- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Added `refresh_document_verification_state()` so artifact verification current-state upserts by `(artifact_path, artifact_type)` and can remove stale paths.
- Added `app/review_gate_state.py` to persist current-state artifact review-gate decisions and refresh them alongside verification.
- Updated generation + remediation pipelines to use the shared refresh helpers (including removing stale PDF gate state on conversion failure).
- Added regression tests for replace-not-append, removals, and PDF identity separation.
- Senior developer review follow-up: standardized refresh timestamps and added refresh non-collision regression coverage for multi-type review-gate state.

### File List

- `app/document_creation.py`
- `app/document_verification.py`
- `app/remediation.py`
- `app/review_gate_state.py`
- `tests/test_document_verification.py`
- `tests/test_review_gate_state.py`
- `_bmad-output/implementation-artifacts/1-5-refresh-artifact-gates-after-regeneration-or-reverification.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Senior Developer Review (AI)

Reviewer: Dicky on 2026-06-01

### Scope

- Reviewed story claims vs implementation for: `app/document_creation.py`, `app/document_verification.py`, `app/remediation.py`, `app/review_gate_state.py`, `tests/test_document_verification.py`, `tests/test_review_gate_state.py`.
- Git discrepancy noted: `_bmad-output/story-automator/orchestration-1-20260527-163528.md` changed but is non-source; excluded from code review per workflow rules.
- Docs lookup note: MCP/web search not available in this environment; relied on in-repo docs (`docs/development-guide.md`, `docs/architecture.md`) and the codebase itself.

### Findings

- CRITICAL: Refresh path did not guarantee consistent timestamping across verification + gate refresh in remediation, making "freshness" harder to reason about downstream.
- HIGH: Generation verification `verified_at` timestamps were per-call rather than aligned to the run timestamp, increasing needless churn and weakening determinism when callers supply explicit timestamps.
- MEDIUM: Review-gate state had coverage for multi-type identity separation on save/load, but lacked a refresh-specific regression proving a refresh of one type does not remove another.

### Fixes Applied

- Standardized `verified_at` for document verification records during a single generation run (`app/document_creation.py`).
- Standardized `updated_at` and `verified_at` markers during remediation refresh (`app/remediation.py`).
- Added refresh non-collision regression coverage for multi-type review-gate decisions (`tests/test_review_gate_state.py`).

## Change Log

- 2026-05-31: Implemented refresh semantics for artifact verification + review-gate current-state and added regression tests.
- 2026-05-31: Updated sprint-status tracking for Story 1.5 to `review`.
- 2026-06-01: Senior developer review complete; story marked done (standardized refresh timestamps; added refresh non-collision regression coverage).
