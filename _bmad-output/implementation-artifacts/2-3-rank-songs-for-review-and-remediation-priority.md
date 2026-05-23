# Story 2.3: Rank Songs for Review and Remediation Priority

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a reviewer,
I want reports to highlight the worst Songs first,
so that I can focus attention on the content most likely to need cleanup or escalation.

## Acceptance Criteria

1. Given a set of scored Songs, when prioritization output is generated, then Songs can
   be sorted or grouped by worst score first, and the output can distinguish Lyrics and
   Chords/Tab priority when they differ for the same Song.
2. Given high-scoring clean Songs and low-scoring weak Songs, when the priority report
   is viewed by a human or agent, then weak Songs are surfaced as primary remediation
   targets, and clean Songs are not emphasized unless explicitly requested.

## Tasks / Subtasks

- [x] Add deterministic prioritization helpers for scored content (AC: 1, 2)
  - [x] Accept persisted content-score records from Story `2.1` / Story `2.2`.
  - [x] Sort or group by worst score first without losing exact `song_key`,
        `content_type`, or `content_hash` identity.
  - [x] Keep prioritization logic separate from remediation execution and review
        overrides.
- [x] Distinguish Lyrics and Chords/Tab priorities for the same song (AC: 1)
  - [x] Allow a song to appear with different priorities for different `content_type`
        records.
  - [x] Preserve machine-readable fields needed for downstream agents to select targets.
- [x] Keep weak content prominent and clean content de-emphasized (AC: 2)
  - [x] Surface `poor` and `questionable` items before `reviewable` and `clean`.
  - [x] Keep clean content available but not highlighted by default.
- [x] Add focused regression coverage
  - [x] Cover mixed score sets sorting by worst-first.
  - [x] Cover same-song Lyrics/Chords divergence.
  - [x] Cover clean content de-emphasis unless explicitly requested.
- [x] Verify from the repository root
  - [x] Run focused prioritization tests.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Stories `2.1` and `2.2` established the score record shape and signal-based score
  composition. This story should consume those score records, not recompute scores or
  re-parse quality signals from scratch. [Source:
  _bmad-output/implementation-artifacts/2-1-persist-deterministic-per-song-lyrics-and-chords-scores.md]
  [Source:
  _bmad-output/implementation-artifacts/2-2-compose-scores-from-existing-quality-signals.md]
- FR-7 is a prioritization/reporting slice, not a remediation slice. Keep ranking
  separate from backup creation, bounded edits, or escalation decisions. [Source:
  _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md]
- Machine-readable priority output should stay exact-identity based so later
  remediation stories can target content safely. [Source:
  _bmad-output/planning-artifacts/architecture.md]

### Suggested Prioritization Fields

- `song_key`
- `artist`
- `title`
- `content_type`
- `content_hash`
- `quality_score`
- `quality_band`
- `score_reasons`
- `priority_rank`

### Project Structure Notes

- Likely implementation files: `app/content_scoring.py`, `app/reporting.py`,
  `tests/test_content_scoring.py`, `tests/test_reporting.py`
- Do not add cleanup execution or escalation behavior here; Epic 3 owns that work.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2-3-Rank-Songs-for-Review-and-Remediation-Priority]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-2-Per-Song-Quality-Scoring-and-Prioritization]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-7-Rank-Songs-by-remediation-priority]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR-Category-Per-Song-LyricsChords-Quality-Scoring---appcontentscoringpy--datareviewcontent_scoresjson]
- [Source: _bmad-output/implementation-artifacts/2-1-persist-deterministic-per-song-lyrics-and-chords-scores.md]
- [Source: _bmad-output/implementation-artifacts/2-2-compose-scores-from-existing-quality-signals.md]
- [Source: app/content_scoring.py]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `manual create-story fallback for 2.3`
- `python3 -m unittest tests.test_content_scoring tests.test_reporting`
- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Created the canonical Story `2.3` artifact directly from the current epic, PRD, and
  architecture context so the automator could resume against the current prioritization
  slice instead of the stale older `2-3` artifact.
- Added deterministic worst-first prioritization helpers to `app/content_scoring.py`
  that preserve exact identity and keep Lyrics and Chords priorities separate.
- Extended the reporting contract with a machine-readable `priority_report` section so
  weak content is surfaced first without entangling prioritization with remediation.
- Kept clean content de-emphasized by default while still allowing inclusion when
  explicitly requested.
- Added focused regression coverage for worst-first ordering, same-song content-type
  divergence, and optional inclusion of clean items.
- Verified the focused scoring/reporting tests and the full repository `unittest` suite
  pass.

### File List

- `_bmad-output/implementation-artifacts/2-3-rank-songs-for-review-and-remediation-priority.md`
- `app/content_scoring.py`
- `app/reporting.py`
- `tests/test_content_scoring.py`
- `tests/test_reporting.py`

## Change Log

- 2026-05-23: Created the canonical Story `2.3` artifact and advanced sprint state to
  `ready-for-dev`.
- 2026-05-23: Implemented worst-first prioritization output and verified the full
  `unittest` suite passes.
