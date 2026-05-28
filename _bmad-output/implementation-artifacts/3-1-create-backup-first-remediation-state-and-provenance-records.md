# Story 3.1: Create Backup-First Remediation State and Provenance Records

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook operator,
I want every remediation attempt to preserve the pre-edit state and provenance,
so that agentic cleanup remains reversible and auditable.

## Acceptance Criteria

1. Given a Song content item is selected for remediation, when a remediation attempt
   begins, then the system creates a backup artifact or reversible record before any
   edit becomes current, and the backup preserves exact Song identity, content type,
   and pre-remediation content reference under `data/review/backups/`.
2. Given a remediation attempt completes or fails, when provenance is recorded, then
   the audit record includes Song identity, `content_type`, pre-change reference,
   post-change reference when present, remediation reason, outcome, and timestamp, and
   current-state records remain separate from append-only remediation history stored
   under `data/review/audit/`.

## Tasks / Subtasks

- [x] Add remediation-state persistence for backup-first workflows (AC: 1, 2)
  - [x] Introduce a remediation-state module, likely `app/remediation_state.py`, for
        current-state remediated content and append-only audit helpers.
- [x] Define local-file paths for `data/review/remediated_content.json`,
        `data/review/backups/`, and `data/review/audit/remediation_attempts.jsonl`.
  - [x] Preserve exact `song_key`, `content_type`, and content-hash identity across all
        backup and provenance records.
- [x] Create backup records before any direct edit path (AC: 1)
  - [x] Capture a reversible pre-change reference before remediation writes current
        remediated state.
  - [x] Keep raw cache immutability intact; backup-first safety must not overwrite
        fetched JSONL caches.
- [x] Record append-only provenance entries for remediation outcomes (AC: 2)
  - [x] Persist machine-readable audit rows with song identity, content type,
        pre-change reference, post-change reference when present, remediation reason,
        outcome, and timestamp.
  - [x] Keep append-only audit history separate from current-state remediated content.
- [x] Add focused regression coverage
  - [x] Cover backup creation and exact-identity round trips.
  - [x] Cover append-only provenance writes for success and failure outcomes.
  - [x] Cover missing parent directories being created automatically.
- [x] Verify from the repository root
  - [x] Run focused remediation-state tests.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Architecture assigns backup-first remediation orchestration to a new remediation
  module family, with current-state remediated content separate from raw caches and
  separate append-only audit history. [Source:
  _bmad-output/planning-artifacts/architecture.md]
- FR-9 and FR-11 are state and provenance slices, not the actual `codex exec`
  remediation run yet. This story should establish safe storage and audit boundaries
  before automated cleanup is wired in. [Source:
  _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md]
- Exact identity and backup safety are critical. Do not overwrite raw fetched cache
  content or blur pre-change vs post-change references. [Source:
  _bmad-output/project-context.md]

### Suggested State Surfaces

- `data/review/remediated_content.json`
- `data/review/backups/`
- `data/review/audit/remediation_attempts.jsonl`

### Suggested Audit Fields

- `song_key`
- `artist`
- `title`
- `content_type`
- `pre_change_reference`
- `post_change_reference`
- `remediation_reason`
- `outcome`
- `timestamp`

### Project Structure Notes

- Likely implementation files: `app/remediation_state.py`, `tests/test_remediation_state.py`
- Keep backup/provenance helpers separate from `app/content_scoring.py`,
  `app/reporting.py`, and document-verification logic in this story.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3-1-Create-Backup-First-Remediation-State-and-Provenance-Records]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-9-Preserve-backups-before-remediation]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-11-Record-remediation-provenance]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR-Category-Backup-First-Agent-Remediation---appremediationpy--appremediation_statepy--datareviewbackups--datareviewremediated_contentjson]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR-Category-Audit-and-Escalation-Controls---appremediation_statepy--datareviewauditremediation_attemptsjsonl--appreportingpy]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `manual create-story fallback for 3.1`
- `python3 -m unittest tests.test_remediation_state`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `2026-05-28: python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Created the canonical Story `3.1` artifact directly from the current Epic 3, PRD,
  and architecture context so the automator could resume against the current
  remediation-state slice instead of the stale older `3-1` artifact.
- Added `app/remediation_state.py` with current-state remediated-content persistence,
  backup snapshot creation, and append-only remediation audit helpers.
- Preserved exact song/content identity and raw-cache immutability while establishing
  backup-first state boundaries for later agentic cleanup stories.
- Added focused regression coverage for backup creation, remediated-content round
  trips, append-only remediation audit writes, malformed audit lines, and parent
  directory creation.
- Verified the focused remediation-state tests and the full repository `unittest`
  suite pass.
- Re-ran the full `unittest` suite on 2026-05-28 and advanced story status to `review`.

### File List

- `_bmad-output/implementation-artifacts/3-1-create-backup-first-remediation-state-and-provenance-records.md`
- `app/remediation_state.py`
- `tests/test_remediation_state.py`
- `tests/test_remediation.py`

## Senior Developer Review (AI)

### Review Run (2026-05-28)

- Validated AC 1: `app.remediation.run_bounded_remediation` creates a backup via
  `app.remediation_state.create_backup_record` before persisting any current-state
  remediated content under `data/review/remediated_content.json`.
- Validated AC 2: remediation audit entries are append-only under
  `data/review/audit/remediation_attempts.jsonl` and include identity, references,
  reason/outcome, and timestamps via `app.remediation_state.record_remediation_audit`.
- Fixed a backup-safety gap: back-to-back backups for the same song/content within the
  same second could overwrite due to timestamp-only filenames; backups now include a
  content-hash prefix and fall back to a numeric suffix to stay unique.
- Added regression coverage for backup-path uniqueness and strengthened the end-to-end
  remediation tests to assert the backup reference is persisted and referenced by all
  audit entries in the success path.

## Change Log

- 2026-05-23: Created the canonical Story `3.1` artifact and advanced sprint state to
  `ready-for-dev`.
- 2026-05-23: Implemented backup-first remediation state and provenance helpers and
  verified the full `unittest` suite passes.
- 2026-05-28: Re-validated the full `unittest` suite and set Story status to `review`.
- 2026-05-28: Story-automator review verified ACs and fixed backup filename
  collision/overwrite risk; added regression coverage.
