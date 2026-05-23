# Story 2.2: Compose Scores from Existing Quality Signals

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a maintainer of the review pipeline,
I want score computation to reuse existing quality-assessment signals,
so that the new scoring layer builds on current behavior instead of duplicating or bypassing it.

## Acceptance Criteria

1. Given existing quality signals for missing content, junk markup, confidence,
   readability, or cleanup outcomes, when score computation runs, then the score
   result is derived from those signals plus any new deterministic rules required for
   this slice, and the scoring module remains separate from backup creation, document
   verification, and escalation policy.
2. Given Lyrics and Chords/Tab have different failure modes, when score computation
   runs, then Lyrics and Chords/Tab can produce different scores and reason sets, and
   both remain inspectable in the same local-file state model.

## Tasks / Subtasks

- [x] Add deterministic score-composition helpers to `app/content_scoring.py` (AC: 1, 2)
  - [x] Accept existing `quality_status`-style signals as inputs instead of re-parsing
        raw content or duplicating quality-assessment logic.
  - [x] Produce score records through the Story `2.1` score contract so persisted
        records stay compatible with `content_scores.json`.
  - [x] Keep score derivation separate from reporting, remediation, backup, and
        document-verification logic.
- [x] Compose score outcomes from existing signals and content-type-specific rules (AC: 1, 2)
  - [x] Map missing-content, junk-markup, confidence, readability, and cleanup signals
        into deterministic numeric adjustments or rule outcomes.
  - [x] Allow Lyrics and Chords/Tab to produce different scores and reasons when the
        underlying signals differ.
  - [x] Keep score reasons machine-readable and deterministic for the same signal set.
- [x] Add focused regression coverage (AC: 1, 2)
  - [x] Cover clean, reviewable, questionable, and poor outcomes from signal
        composition.
  - [x] Cover differing Lyrics vs Chords inputs for the same song.
  - [x] Cover deterministic reruns with identical inputs yielding identical scores and
        reasons.
- [x] Preserve current boundaries and compatibility
  - [x] Do not wire prioritization reports, remediation retries, or escalation policy
        into this story.
  - [x] Keep the output inspectable in the same local-file current-state model
        introduced in Story `2.1`.
- [x] Verify from the repository root
  - [x] Run focused scoring tests.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Story `2.1` established the score record contract and `content_scores.json`
  persistence boundary. Reuse that exact record shape instead of introducing a second
  score schema. [Source:
  _bmad-output/implementation-artifacts/2-1-persist-deterministic-per-song-lyrics-and-chords-scores.md]
- Existing signal producers already live in quality-assessment and quality-status
  flows. This story should compose from those signals rather than rescoring from raw
  text in a parallel pipeline. [Source:
  _bmad-output/planning-artifacts/architecture.md]
- The architecture explicitly expects `app/content_scoring.py` to convert signals into
  stable scores and reasons while remaining separate from reporting and remediation.
  [Source: _bmad-output/planning-artifacts/architecture.md]

### Suggested Composition Inputs

- `quality_status.quality`
- `quality_status.signals[]`
- `content_type`
- current `content_hash`
- stable score thresholds from Story `2.1`

### Project Structure Notes

- Likely implementation files: `app/content_scoring.py`, `tests/test_content_scoring.py`
- Possible persistence touchpoints only if needed for integration: `app/review_state.py`
- Do not modify report prioritization yet; Story `2.3` owns that behavior.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2-2-Compose-Scores-from-Existing-Quality-Signals]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-2-Per-Song-Quality-Scoring-and-Prioritization]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-5-Score-Lyrics-quality-per-Song]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-6-Score-ChordsTab-quality-per-Song]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR-Category-Per-Song-LyricsChords-Quality-Scoring---appcontentscoringpy--datareviewcontent_scoresjson]
- [Source: _bmad-output/implementation-artifacts/2-1-persist-deterministic-per-song-lyrics-and-chords-scores.md]
- [Source: app/content_scoring.py]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `manual create-story fallback for 2.2`
- `python3 -m unittest tests.test_content_scoring`
- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Created the canonical Story `2.2` artifact directly from the current epic, PRD, and
  architecture context so the automator could resume against the current score
  composition slice instead of the stale older `2-2` artifact.
- Extended `app/content_scoring.py` with deterministic score composition from existing
  `quality_status` signals instead of rescoring from raw content in parallel.
- Added content-type-specific signal penalties so Lyrics and Chords can diverge where
  the existing pipeline already treats those failure modes differently.
- Kept the score composition logic separate from reporting, remediation, and document
  verification.
- Added focused regression coverage for clean, reviewable, questionable, and poor
  outcomes, plus deterministic reruns and Lyrics-vs-Chords divergence.
- Verified the focused scoring tests and the full repository `unittest` suite pass.

### File List

- `_bmad-output/implementation-artifacts/2-2-compose-scores-from-existing-quality-signals.md`
- `app/content_scoring.py`
- `tests/test_content_scoring.py`

## Change Log

- 2026-05-23: Created the canonical Story `2.2` artifact and advanced sprint state to
  `ready-for-dev`.
- 2026-05-23: Implemented signal-based deterministic score composition and verified the
  full `unittest` suite passes.
