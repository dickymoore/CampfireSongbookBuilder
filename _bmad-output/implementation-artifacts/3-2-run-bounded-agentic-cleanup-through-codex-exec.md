# Story 3.2: Run Bounded Agentic Cleanup Through Codex Exec

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an operator delegating cleanup to agents,
I want low-quality content to be remediated through a bounded `codex exec` path,
so that agentic cleanup can improve content automatically without unconstrained rewriting.

## Acceptance Criteria

1. Given a Song content item falls below the configured remediation threshold and the
   issue type is allowed for v1 cleanup, when remediation is invoked, then the system
   can launch a `codex exec` remediation step against the backed-up current-state
   content, and the allowed transformation scope is limited to whitespace
   normalization, section restructuring without semantic rewrite, removal of obvious
   scraper residue, and normalization or removal of repeated junk blocks.
2. Given a remediation candidate would require semantic rewriting, musical
   reinterpretation, or changes outside the allowed bounded scope, when the `codex
   exec` path evaluates the candidate, then the system refuses automatic cleanup for
   that item, and the item is marked for escalation or manual review instead of being
   silently modified.

## Tasks / Subtasks

- [x] Add bounded remediation orchestration for `codex exec` (AC: 1, 2)
  - [x] Introduce `app/remediation.py` to own the non-interactive `codex exec`
        launch path and reuse Story `3.1` backup/provenance helpers.
  - [x] Define an explicit bounded prompt and allowlist contract for approved v1
        cleanup operations only.
  - [x] Keep raw caches immutable and operate against backup-protected current-state
        content.
- [x] Enforce the allowed transformation scope (AC: 1, 2)
  - [x] Allow whitespace normalization, section restructuring without semantic rewrite,
        scraper-residue removal, and repeated junk-block cleanup for approved issue
        signals only.
  - [x] Refuse semantic rewrites, musical reinterpretation, and other out-of-scope
        transformations with a machine-readable refusal outcome.
- [x] Persist cleanup outcomes through existing remediation-state surfaces
  - [x] Reuse backup references and append-only audit history from Story `3.1`.
  - [x] Record whether remediation was allowed, attempted, refused, failed, or
        completed successfully.
- [x] Add focused regression coverage
  - [x] Cover allowed remediation candidate routing.
  - [x] Cover refusal for out-of-scope remediation candidates.
  - [x] Cover audit/provenance recording around `codex exec` invocation decisions.
- [x] Verify from the repository root
  - [x] Run focused remediation tests.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Story `3.1` established backup-first remediation state and append-only provenance.
  This story should consume that state rather than inventing another edit workflow.
  [Source:
  _bmad-output/implementation-artifacts/3-1-create-backup-first-remediation-state-and-provenance-records.md]
- FR-8 is explicitly bounded. The allowlist is narrow and semantic rewriting stays out
  of scope for v1. Keep the refusal path explicit and machine-readable. [Source:
  _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md]
- Architecture assigns backup-first remediation orchestration to a dedicated
  remediation module while preserving raw cache immutability and exact identity.
  [Source: _bmad-output/planning-artifacts/architecture.md]

### Allowed `codex exec` Operations

- whitespace normalization
- section restructuring without semantic rewrite
- removal of obvious scraper residue
- normalization or removal of repeated junk blocks

### Project Structure Notes

- Likely implementation files: `app/remediation.py`, `app/remediation_state.py`,
  `tests/test_remediation.py`
- Do not add retry-limit policy or post-remediation rescoring in this story; Stories
  `3.3` and `3.4` own those behaviors.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3-2-Run-Bounded-Agentic-Cleanup-Through-Codex-Exec]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-8-Permit-bounded-agent-edits-to-low-quality-content]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#104-Allowed-codex-exec-Remediation-Operations]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR-Category-Backup-First-Agent-Remediation---appremediationpy--appremediation_statepy--datareviewbackups--datareviewremediated_contentjson]
- [Source: _bmad-output/implementation-artifacts/3-1-create-backup-first-remediation-state-and-provenance-records.md]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `manual create-story fallback for 3.2`
- `python3 -m unittest tests.test_remediation tests.test_remediation_state`
- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Implemented bounded remediation orchestration in `app/remediation.py` using the
  installed local `codex exec` CLI surface with injected runner support for tests.
- Added explicit allowlist evaluation so only approved cleanup signals can launch
  automatic remediation while semantic-rewrite candidates are refused for manual
  review.
- Extended remediation audit outcomes to capture `allowed`, `attempted`, and
  `refused` states in addition to `success` and `failed`.
- Verified backup-first remediation persistence and append-only audit behavior through
  focused and full `unittest` coverage.

### File List

- `_bmad-output/implementation-artifacts/3-2-run-bounded-agentic-cleanup-through-codex-exec.md`
- `app/remediation.py`
- `app/remediation_state.py`
- `tests/test_remediation.py`

## Change Log

- 2026-05-23: Created the canonical Story `3.2` artifact and advanced sprint state to
  `ready-for-dev`.
- 2026-05-23: Implemented bounded `codex exec` remediation, added focused regression
  coverage, and completed Story `3.2`.

## Status

done
