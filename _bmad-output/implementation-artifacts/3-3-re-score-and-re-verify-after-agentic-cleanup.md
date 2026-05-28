# Story 3.3: Re-Score and Re-Verify After Agentic Cleanup

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a reviewer,
I want remediated content to be re-evaluated automatically,
so that post-cleanup quality gains or failures are measurable before further action is taken.

## Acceptance Criteria

1. Given a remediation attempt changes the current-state content, when the attempt
   completes, then the system recomputes the content hash, re-scores the affected
   Lyrics or Chords item, and reruns any relevant document or review verification,
   and before-and-after state is preserved for auditability.
2. Given a remediation attempt does not improve the relevant score or verification
   outcome, when post-remediation evaluation is recorded, then the result clearly
   indicates that the item remains below threshold, and downstream gating can treat
   the item as unresolved.

## Tasks / Subtasks

- [x] Re-score remediated content after successful cleanup (AC: 1, 2)
  - [x] Recompute the remediated content hash from the current-state text saved by
        Story `3.2`.
  - [x] Reuse the deterministic scoring pipeline from Epic 2 to produce updated score
        records for the affected song/content pair.
- [x] Re-run verification and review-state surfaces after successful cleanup (AC: 1, 2)
  - [x] Refresh affected review-state outputs using the remediated content state
        rather than the pre-cleanup content, and optionally refresh artifact
        verification when paths are supplied.
  - [x] Keep before-and-after references visible for auditability and downstream triage
        through append-only audit details.
- [x] Persist measurable unresolved outcomes (AC: 2)
  - [x] Record when remediation succeeded mechanically but did not improve the score
        or verification outcome enough to clear the threshold.
  - [x] Keep unresolved items machine-readable so later stories can enforce retries
        and escalation boundaries.
- [x] Add focused regression coverage
  - [x] Cover successful re-score / re-verify flow after bounded remediation.
  - [x] Cover the unresolved path when cleanup does not improve the outcome enough.
- [x] Verify from the repository root
  - [x] Run focused post-remediation tests.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Story `3.2` now owns bounded remediation execution and writes remediated content plus
  append-only audit history. This story should consume those outputs instead of adding
  another cleanup path. [Source:
  _bmad-output/implementation-artifacts/3-2-run-bounded-agentic-cleanup-through-codex-exec.md]
- Epic 2 already established deterministic score composition and priority ranking.
  Reuse those helpers for post-remediation evaluation rather than inventing a second
  score model. [Source:
  _bmad-output/implementation-artifacts/2-1-persist-deterministic-per-song-lyrics-and-chords-scores.md]
- Architecture and PRD require measurable before/after evaluation so unresolved items
  remain visible to later retry-limit and escalation logic. [Source:
  _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md]

### Project Structure Notes

- Likely implementation files: `app/remediation.py`, `app/remediation_state.py`,
  `app/content_scoring.py`, `app/review_state.py`, `tests/test_remediation.py`
- Do not implement retry-limit or escalation policy here; Story `3.4` owns that
  behavior.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3-3-Re-Score-and-Re-Verify-After-Agentic-Cleanup]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-10-Re-evaluate-after-agent-remediation]
- [Source: _bmad-output/planning-artifacts/architecture.md]
- [Source: _bmad-output/implementation-artifacts/2-1-persist-deterministic-per-song-lyrics-and-chords-scores.md]
- [Source: _bmad-output/implementation-artifacts/2-2-compose-scores-from-existing-quality-signals.md]
- [Source: _bmad-output/implementation-artifacts/3-2-run-bounded-agentic-cleanup-through-codex-exec.md]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `manual create-story fallback for 3.3`
- `python3 -m unittest tests.test_remediation tests.test_remediation_state tests.test_review_state tests.test_content_scoring`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `2026-05-28: python3 -m unittest discover -s tests -p 'test_*.py' (OK)`

### Completion Notes List

- Added immediate post-remediation re-evaluation so successful bounded cleanup now
  persists fresh quality status and content-score state for the remediated current
  candidate.
- Recorded machine-readable `resolved` and `unresolved` post-check outcomes in the
  append-only remediation audit stream, including before/after score and hash details.
- Kept review-workflow compatibility by reusing the existing cached-content evaluation
  path and optional document-verification refresh when artifact paths are supplied.
- Covered both the resolved and still-below-threshold paths with focused remediation
  tests before running the full repository suite.
- 2026-05-28: Re-ran the full `unittest` suite (141 tests) to confirm no regressions.

### File List

- `_bmad-output/implementation-artifacts/3-3-re-score-and-re-verify-after-agentic-cleanup.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/remediation.py`
- `app/remediation_state.py`
- `tests/test_remediation.py`

## Senior Developer Review (AI)

### Review Run (2026-05-28)

- Validated AC 1: post-remediation evaluation recomputes the remediated content hash, re-scores via Epic 2's deterministic score pipeline, optionally refreshes document verification, and preserves before/after details in the append-only remediation audit stream.
- Validated AC 2: unresolved outcomes remain machine-readable via `outcome: unresolved` audit entries plus `unresolved_reasons` / `escalation_category` fields so downstream gating can treat items as still-below-threshold or failing verification.
- Fixed a verification correctness gap: when `artifact_paths` were supplied but none existed, the flow previously treated verification as passing (empty record set). Missing paths are now recorded as `missing_artifact_paths` and force an unresolved post-check outcome.
- Added regression coverage for artifact verification (pass/fail + missing artifact path) in `tests/test_remediation.py` and removed an untracked duplicate E2E test artifact.
- Re-ran `python3 -m unittest discover -s tests -p 'test_*.py'` (144 tests) to confirm the fixes do not introduce regressions.

## Change Log

- 2026-05-23: Created the canonical Story `3.3` artifact and advanced sprint state to
  `ready-for-dev`.
- 2026-05-23: Implemented post-remediation re-score and re-verification persistence,
  added focused regression coverage, and completed Story `3.3`.
- 2026-05-28: Re-ran full regression tests and set story status to `review`.
- 2026-05-28: Story-automator review verified ACs, fixed artifact verification behavior for missing paths, and added regression coverage; set story status to `done`.

## Status

done
