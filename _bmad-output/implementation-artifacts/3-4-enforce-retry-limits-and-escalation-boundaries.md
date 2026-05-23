# Story 3.4: Enforce Retry Limits and Escalation Boundaries

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a reviewer,
I want automatic remediation attempts to stop after bounded retries,
so that agents do not loop indefinitely on low-quality content and unresolved items are escalated clearly.

## Acceptance Criteria

1. Given an item has a persisted remediation-attempt count, when another `codex exec`
   cleanup is considered, then the system checks the configured retry limit of `2`
   before running a new attempt, and items at or beyond the retry limit are escalated
   without another automatic edit.
2. Given an item is escalated because cleanup is not allowed, not successful, or
   retry-exhausted, when escalation state is recorded, then the output includes an
   explicit machine-readable escalation category and reason, and reports and agents can
   distinguish `not_allowed_to_fix`, `retry_limit_reached`, and
   `still_below_threshold` outcomes.

## Tasks / Subtasks

- [x] Enforce persisted retry limits before bounded remediation runs (AC: 1)
  - [x] Count prior remediation attempts for the song/content item from the existing
        append-only audit history.
  - [x] Refuse additional automatic remediation once the configured retry ceiling of
        `2` attempts has been reached.
- [x] Record machine-readable escalation outcomes (AC: 1, 2)
  - [x] Persist explicit escalation categories for policy-blocked, failed, and
        retry-exhausted items.
  - [x] Keep escalation state inspectable through the existing local-file audit/report
        surfaces.
- [x] Surface escalation outcomes to downstream reporting and agent flows (AC: 2)
  - [x] Make the stored outcome clear enough for later reports and agents to
        distinguish `not_allowed_to_fix`, `retry_limit_reached`, and
        `still_below_threshold`.
- [x] Add focused regression coverage
  - [x] Cover the retry-limit refusal path.
  - [x] Cover explicit escalation-category persistence for blocked or unresolved items.
- [x] Verify from the repository root
  - [x] Run focused retry/escalation tests.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Story `3.2` introduced bounded remediation execution and append-only audit history.
  Story `3.3` now adds machine-readable `resolved` and `unresolved` post-check outcomes
  with before/after score details. This story should build on that audit history rather
  than creating a separate retry tracker. [Source:
  _bmad-output/implementation-artifacts/3-3-re-score-and-re-verify-after-agentic-cleanup.md]
- PRD policy default sets the automatic remediation retry limit to `2` attempts per
  content item before mandatory escalation. [Source:
  _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md]
- Keep escalation state local-file based and inspectable for later reporting. [Source:
  _bmad-output/planning-artifacts/architecture.md]

### Project Structure Notes

- Likely implementation files: `app/remediation.py`, `app/remediation_state.py`,
  `app/reporting.py`, `tests/test_remediation.py`
- Reuse the existing remediation audit JSONL stream instead of inventing a database or
  hidden retry counter.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3-4-Enforce-Retry-Limits-and-Escalation-Boundaries]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-12-Define-escalation-boundaries-for-unresolved-quality-issues]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#105-Automatic-Retry-Limit]
- [Source: _bmad-output/planning-artifacts/architecture.md]
- [Source: _bmad-output/implementation-artifacts/3-2-run-bounded-agentic-cleanup-through-codex-exec.md]
- [Source: _bmad-output/implementation-artifacts/3-3-re-score-and-re-verify-after-agentic-cleanup.md]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `manual create-story fallback for 3.4`
- `python3 -m unittest tests.test_remediation tests.test_remediation_state`
- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Added retry-limit enforcement ahead of `codex exec` launches by counting persisted
  `attempted` audit entries for each song/content item.
- Added explicit escalation categories to remediation outcomes so agents and reports can
  distinguish policy-blocked, retry-exhausted, remediation-failed, and
  still-below-threshold cases.
- Covered the retry-limit refusal path and the machine-readable escalation-category
  contract with focused remediation tests before running the full repository suite.

### File List

- `_bmad-output/implementation-artifacts/3-4-enforce-retry-limits-and-escalation-boundaries.md`
- `app/remediation.py`
- `tests/test_remediation.py`

## Change Log

- 2026-05-23: Created the canonical Story `3.4` artifact and advanced sprint state to
  `ready-for-dev`.
- 2026-05-23: Implemented retry-limit enforcement, explicit escalation categories, and
  completed Story `3.4`.

## Status

done
