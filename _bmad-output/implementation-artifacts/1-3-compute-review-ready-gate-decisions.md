# Story 1.3: Compute Review-Ready Gate Decisions

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a reviewer,
I want the system to decide whether an artifact is ready for manual inspection,
so that I only open outputs that already meet the minimum presentation standard.

## Acceptance Criteria

1. Given an artifact passes configured neatness thresholds, when review readiness is
   computed, then the artifact is marked review-ready, and the decision is persisted
   in machine-readable form.
2. Given an artifact fails one or more neatness checks, when review readiness is
   computed, then the artifact is marked not review-ready, and the persisted result
   includes explicit failure reasons.

## Tasks / Subtasks

- [x] Add a deterministic review-ready gate module and machine-readable decision contract (AC: 1, 2)
  - [x] Implement gate computation in `app/review_gate.py`, not inside scraper, cache, or CLI orchestration code.
  - [x] Reuse the existing document verification contract from Story `1.1` and neatness results from Story `1.2` as the gate inputs.
  - [x] Keep threshold and gate logic isolated so tuning review-readiness does not require rewriting unrelated generation or reporting modules.
  - [x] Emit stable machine-readable fields for at least:
        artifact identity,
        review-ready boolean/state,
        explicit failure reasons,
        and computed timestamp.
- [x] Compute review-ready decisions from current artifact verification outputs (AC: 1, 2)
  - [x] Mark an artifact review-ready when its deterministic document verification state satisfies configured neatness thresholds.
  - [x] Mark an artifact not review-ready when verification shows one or more blocking neatness failures.
  - [x] Preserve explicit failure reasons from verification input rather than collapsing them into a single summary string.
  - [x] Keep this story limited to computing and persisting the gate state; Story `1.4` owns downstream review blocking and presentation behavior.
- [x] Persist the gate decision in the machine-readable reporting surface (AC: 1, 2)
  - [x] Extend the existing report contract in `app/reporting.py` so downstream tests and agents can consume review-ready state without parsing prose.
  - [x] Keep persistence local and inspectable using the existing report-writing flow rather than introducing a service or daemon.
  - [x] Preserve compatibility with the current CLI/report pipeline and avoid changing raw cache semantics.
- [x] Add focused regression coverage for gate computation and report persistence (AC: 1, 2)
  - [x] Add or extend tests for the gate module, likely in `tests/test_review_gate.py` or a closely related focused test file.
  - [x] Extend `tests/test_reporting.py` to verify machine-readable review-ready state is preserved in persisted report output.
  - [x] Cover both a passing artifact and a failing artifact with explicit carried-through reasons.
- [x] Verify from the repository root (AC: 1, 2)
  - [x] Run the focused gate/report tests.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Story `1.1` established the artifact verification persistence contract in
  `app/document_verification.py` and `data/review/document_quality.json`. This story
  must consume that state rather than defining a parallel verification format. [Source:
  _bmad-output/implementation-artifacts/1-1-produce-inspectable-document-verification-records.md]
- Story `1.2` added deterministic neatness heuristics and explicit machine-readable
  reasons. Treat those reasons as direct review-gate inputs rather than recomputing
  neatness inside the new gate module. [Source:
  _bmad-output/implementation-artifacts/1-2-evaluate-artifact-neatness-with-deterministic-heuristics.md]
- The architecture explicitly separates document verification from review-ready gate
  computation. `app/document_verification.py` emits inputs; `app/review_gate.py`
  computes machine-readable readiness state before manual inspection. [Source:
  _bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries]
  [Source: _bmad-output/planning-artifacts/architecture.md#Service-and-Data-Integration-Boundaries]
- The architecture also treats review-ready as a machine-readable gate state, not just
  a human summary line. Avoid burying the gate result only in console output or prose.
  [Source: _bmad-output/planning-artifacts/architecture.md#Decision-Priority-Analysis]
- PRD FR-2 requires a document that meets threshold to be marked review-ready, and a
  failing document to be marked not review-ready with reasons. The threshold logic
  must remain isolated from unrelated generation code. [Source:
  _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-2-Define-neatness-thresholds-for-review-readiness]
- The reporting layer is already the machine-readable aggregation surface for run
  output. Persist the gate decision there so later stories and tests can consume it
  without inventing a side channel. [Source: app/reporting.py]
  [Source: tests/test_reporting.py]
- Preserve repo-root execution and exact `artist`, `title`, and `song_key` identity
  semantics. This story must not alter cache immutability, content-score ownership, or
  remediation boundaries. [Source: _bmad-output/project-context.md#Critical-Dont-Miss-Rules]

### Suggested Gate Contract

Define a stable artifact-level gate result that can be carried through reports and
tests. Candidate fields for v1:

- `artifact_path`
- `artifact_type`
- `review_ready` or equivalent explicit state
- `failure_reasons`
- `computed_at`

If the artifact passes, keep the result explicit rather than omitting it. Avoid hidden
meaning like "no reasons means ready".

### Project Structure Notes

- Existing verification state module: `app/document_verification.py`
- New gate module target: `app/review_gate.py`
- Existing report aggregation surface: `app/reporting.py`
- Existing generation/report producer to preserve: `app/document_creation.py`
- Existing reporting tests to extend: `tests/test_reporting.py`
- Existing verification tests and story context to reference: `tests/test_document_verification.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1-3-Compute-Review-Ready-Gate-Decisions]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-1-Review-Ready-Document-Quality-Gates]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision-Priority-Analysis]
- [Source: _bmad-output/planning-artifacts/architecture.md#Policy-Defaults-Resolved-for-V1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#Service-and-Data-Integration-Boundaries]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-2-Define-neatness-thresholds-for-review-readiness]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#102-Document-Neatness-Gate-Scope]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: _bmad-output/project-context.md#Critical-Dont-Miss-Rules]
- [Source: _bmad-output/implementation-artifacts/1-1-produce-inspectable-document-verification-records.md]
- [Source: _bmad-output/implementation-artifacts/1-2-evaluate-artifact-neatness-with-deterministic-heuristics.md]
- [Source: app/document_verification.py]
- [Source: app/reporting.py]
- [Source: tests/test_reporting.py]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `story-automator create-story retries for 1.3`
- `manual controller-side story generation`
- `python3 -m unittest tests.test_review_gate`
- `python3 -m unittest tests.test_reporting`
- `python3 -m unittest tests.test_document_creation`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 -m flake8 app tests main.py` (fails locally: `No module named flake8`)

### Completion Notes List

- Created the canonical Story `1.3` artifact directly because autonomous create-story
  workers repeatedly drifted into an interactive improvement path instead of writing
  the story file.
- Kept scope aligned to FR-2 while preserving the architecture split between
  `app/document_verification.py` and the new `app/review_gate.py`.
- Pointed persistence toward the existing machine-readable report contract instead of
  inventing a separate service or daemon-backed gate path.
- Added `app/review_gate.py` to compute deterministic artifact-level review-ready
  decisions from persisted document verification results with explicit failure reasons.
- Extended `app/document_creation.py`, `app/reporting.py`, and `main.py` so review-gate
  decisions flow through the existing machine-readable report path beside document
  verification output.
- Added regression coverage in `tests/test_review_gate.py`, `tests/test_reporting.py`,
  and `tests/test_document_creation.py`, then verified the full `unittest` suite
  passes from the repository root.
- `flake8` is referenced by project config but is not installed in the local
  environment, so style verification was limited to line-length inspection.

### File List

- `_bmad-output/implementation-artifacts/1-3-compute-review-ready-gate-decisions.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/document_creation.py`
- `app/reporting.py`
- `app/review_gate.py`
- `main.py`
- `tests/test_document_creation.py`
- `tests/test_reporting.py`
- `tests/test_review_gate.py`

## Change Log

- 2026-05-22: Created the canonical Story `1.3` implementation guide manually after
  autonomous create-story retries failed to cross the file-write boundary.
- 2026-05-22: Implemented deterministic review-ready gate decisions, threaded them
  through the existing report contract, added regression coverage, and moved the story
  to `review`.
