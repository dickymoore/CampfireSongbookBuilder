# Story 1.5: Refresh Artifact Gates After Regeneration or Re-Verification

Status: ready-for-dev

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

- [ ] Define what "artifact identity" means for refresh semantics (AC: 1, 3)
  - [ ] Confirm the identity keys used by the verification record contract from Story 1.1 (e.g. `artifact_path` + `artifact_type`) and use those as the stable replacement key.
  - [ ] Ensure refresh semantics do not accidentally merge distinct artifacts from the same run (e.g. markdown vs docx vs pdf).

- [ ] Implement "refresh" behavior for document verification current-state persistence (AC: 1, 3)
  - [ ] When saving verification results, replace existing entry for the same artifact identity instead of appending duplicates.
  - [ ] Update `updated_at` / `verified_at` fields consistently so downstream agents can tell "new evidence" exists.
  - [ ] Keep behavior deterministic given the same inputs (stable ordering, stable identity mapping).

- [ ] Implement "refresh" behavior for review-gate decisions (AC: 1, 3)
  - [ ] Ensure review-ready decisions are recomputed from the latest verification/neatness evidence, not cached stale values.
  - [ ] When persisting review-gate results, replace prior decision records for the same artifact identity.

- [ ] Ensure refresh is invoked in the pipeline paths that can produce stale evidence (AC: 1)
  - [ ] Identify the code path(s) that re-run verification after regeneration/re-verification and ensure they call the same persistence helpers (no parallel formats).
  - [ ] Verify reporting reads the current-state files and does not keep its own shadow copy.

- [ ] PDF-aware refresh semantics (AC: 2)
  - [ ] Ensure that when PDF is part of the run, the refresh behavior covers PDF verification + gate results using the same identity semantics.
  - [ ] Ensure PDF generation/conversion failure remains distinct from PDF verification failure in the persisted state model.

- [ ] Add regression tests (AC: 1-3)
  - [ ] Test "replace not append": saving a second result for the same artifact identity overwrites (or replaces) the existing record and does not create duplicates.
  - [ ] Test determinism: same input snapshot produces same persisted outcome.
  - [ ] If PDF is in-scope in code, add at least one focused test that proves PDF refresh does not collide with docx/markdown identity.

- [ ] Verify from repo root (AC: 1-3)
  - [ ] Run focused tests added/updated for this story.
  - [ ] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

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

TBD

### Debug Log References

### Completion Notes List

### File List

