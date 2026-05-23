# Story 1.4: Gate Manual Review and Reporting on Verification Results

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a reviewer,
I want automated verification results to drive reporting and review gating,
so that failed artifacts are surfaced before any manual inspection step.

## Acceptance Criteria

1. Given a run includes artifacts that failed verification, when reporting or review
   gating runs, then those artifacts are clearly identified as blocked from manual
   review, and the output distinguishes document-verification failure from song-content
   quality issues.
2. Given an agent or automated test consumes verification output, when it reads the
   local verification artifacts, then it can determine pass/fail state and reasons
   without parsing human-facing summary text, and the flow remains compatible with the
   existing CLI workflow.

## Tasks / Subtasks

- [x] Extend the machine-readable reporting contract with explicit manual-review gate data (AC: 1, 2)
  - [x] Build a deterministic artifact-level `manual_review_gate` section in `app/reporting.py`.
  - [x] Preserve the existing `document_verification` and `review_gate_decisions` surfaces for backward compatibility.
  - [x] Mark blocked artifacts explicitly with a machine-readable boolean and blocking stage.
- [x] Distinguish artifact verification failures from song-content quality issues (AC: 1)
  - [x] Keep artifact-level review gating separate from song-level `clean`/`questionable`/`missing` summaries.
  - [x] Carry document-verification reasons through to blocked manual-review artifacts without collapsing them into prose.
- [x] Add focused regression coverage for report consumers (AC: 1, 2)
  - [x] Verify ready vs blocked artifact counts and entries in `tests/test_reporting.py`.
  - [x] Verify song-quality summaries remain distinct from manual-review blocks in the same report payload.
- [x] Verify from the repository root (AC: 1, 2)
  - [x] Run `python3 -m unittest tests.test_reporting`.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Story `1.3` introduced deterministic `review_gate_decisions` derived from document
  verification. This story should build on that contract rather than inventing a
  separate review-state channel. [Source:
  _bmad-output/implementation-artifacts/1-3-compute-review-ready-gate-decisions.md]
- FR-3 requires failed artifacts to be surfaced before manual inspection and to stay
  distinguishable from song-content quality issues. That means the artifact gate must
  stay separate from song summaries in the reporting layer. [Source:
  _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md]
- Keep the result local-file based and compatible with the existing CLI/report flow.
  Avoid new services, daemons, or parser-dependent human prose. [Source:
  _bmad-output/planning-artifacts/architecture.md]

### Suggested Report Contract Additions

- `manual_review_gate.ready_count`
- `manual_review_gate.blocked_count`
- `manual_review_gate.ready_artifacts[]`
- `manual_review_gate.blocked_artifacts[]`
- `blocked_artifacts[].blocked_from_manual_review`
- `blocked_artifacts[].blocking_stage`
- `blocked_artifacts[].verification_reasons`

### Project Structure Notes

- Existing reporting surface: `app/reporting.py`
- Existing gate inputs: `document_verification`, `review_gate_decisions`
- Existing tests to extend: `tests/test_reporting.py`
- Keep CLI integration unchanged apart from surfacing richer machine-readable report
  content through the existing `build_traceable_quality_report()` path.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1-4-Gate-Manual-Review-and-Reporting-on-Verification-Results]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-1-Review-Ready-Document-Quality-Gates]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-3-Gate-manual-review-behind-automated-verification]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-4-Expose-agentic-verification-results-in-inspectable-artifacts]
- [Source: app/reporting.py]
- [Source: tests/test_reporting.py]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `python3 -m unittest tests.test_reporting`
- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Added a deterministic `manual_review_gate` section to the reporting contract so
  consumers can read ready vs blocked artifacts directly from machine-readable output.
- Preserved compatibility with the existing `document_verification` and
  `review_gate_decisions` fields while making manual-review blocks explicit.
- Kept document-verification failures separate from song-content quality summaries so a
  report can show both kinds of issues without conflating them.
- Added focused regression coverage for blocked artifact reporting and the separation
  between artifact gating and song-quality reporting.
- Verified the focused reporting tests and the full repository `unittest` suite pass.

### File List

- `_bmad-output/implementation-artifacts/1-4-gate-manual-review-and-reporting-on-verification-results.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/reporting.py`
- `tests/test_reporting.py`

## Change Log

- 2026-05-23: Added explicit manual-review gate reporting, preserved existing gate
  inputs for compatibility, and verified the full `unittest` suite passes.
