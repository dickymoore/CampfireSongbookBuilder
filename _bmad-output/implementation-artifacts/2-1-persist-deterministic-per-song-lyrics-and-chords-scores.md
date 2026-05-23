# Story 2.1: Persist Deterministic Per-Song Lyrics and Chords Scores

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook operator,
I want each Song to receive persisted Lyrics and Chords quality scores,
so that content quality can be measured consistently across runs.

## Acceptance Criteria

1. Given a Song with current lyrics or chords content, when scoring runs, then the
   system writes a deterministic score record for each relevant `content_type`, and
   each record preserves exact `artist`, `title`, `song_key`, `content_hash`,
   `quality_score`, `quality_band`, `score_version`, and `score_reasons`.
2. Given the same content snapshot and threshold configuration, when scoring is rerun,
   then the same score outcome is produced, and the score uses the deterministic
   `0-100` v1 scale with threshold bands `85-100 clean`, `60-84 reviewable`,
   `40-59 questionable`, and `0-39 poor`.

## Tasks / Subtasks

- [x] Add deterministic score persistence helpers for current score state (AC: 1, 2)
  - [x] Introduce a score-focused module, likely `app/content_scoring.py`, that owns
        score record construction and deterministic band derivation only.
  - [x] Add load/save helpers for `data/review/content_scores.json` using the same
        current-state persistence pattern already used for `quality_status.json` and
        `review_decisions.json`.
  - [x] Preserve exact `artist`, `title`, `song_key`, `content_type`, and
        `content_hash` identity without normalization during save/load.
- [x] Define the deterministic v1 score contract and thresholds (AC: 1, 2)
  - [x] Emit integer `quality_score` values in `0-100`.
  - [x] Emit deterministic `quality_band` derived from the configured thresholds:
        `clean`, `reviewable`, `questionable`, `poor`.
  - [x] Emit stable `score_version` and machine-readable `score_reasons`.
- [x] Add focused regression coverage (AC: 1, 2)
  - [x] Cover save/load round trips for lyrics and chords score records.
  - [x] Cover threshold boundary behavior for band assignment.
  - [x] Cover missing or malformed score-state files returning recoverable validation
        errors rather than crashing.
- [x] Preserve current boundaries and compatibility
  - [x] Do not fold score computation into report formatting, remediation, or document
        verification in this story.
  - [x] Keep the scoring state local-file based and compatible with repo-root CLI runs.
- [x] Verify from the repository root
  - [x] Run focused score-state tests.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- The repo already has current-state persistence patterns for `quality_status.json` and
  `review_decisions.json` in `app/review_state.py`. Reuse that storage shape and
  validation style rather than inventing a separate persistence model. [Source:
  _bmad-output/implementation-artifacts/1-5-persist-current-quality-status-for-cached-content.md]
  [Source: _bmad-output/implementation-artifacts/2-3-persist-review-decisions-with-content-hashes.md]
- Architecture allocates score ownership to a separate score module and a dedicated
  current-state file at `data/review/content_scores.json`. Keep score derivation and
  score persistence separate from reporting and remediation concerns. [Source:
  _bmad-output/planning-artifacts/architecture.md]
- The score contract must stay exact-identity based and tied to current content hashes.
  Later prioritization and remediation stories depend on that stability. [Source:
  _bmad-output/planning-artifacts/architecture.md]
  [Source: _bmad-output/project-context.md]

### Suggested Score State Shape

```python
{
    "version": 1,
    "updated_at": "2026-05-23T19:00:00+01:00",
    "entries": {
        "The Campfire Trio - Trail Song": {
            "lyrics": {
                "artist": "The Campfire Trio",
                "title": "Trail Song",
                "song_key": "The Campfire Trio - Trail Song",
                "content_type": "lyrics",
                "content_hash": "sha256:...",
                "quality_score": 82,
                "quality_band": "reviewable",
                "score_version": "v1",
                "score_reasons": ["missing_structure_signal"],
                "scored_at": "2026-05-23T19:00:00+01:00"
            }
        }
    }
}
```

### Project Structure Notes

- Likely implementation files: `app/content_scoring.py`, `app/review_state.py`,
  `tests/test_content_scoring.py`, and/or `tests/test_review_state.py`
- Preserve the existing flat `app/*.py` module layout.
- Do not wire prioritization or remediation behavior here; Story `2.2` and later own
  score composition and downstream use.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2-1-Persist-Deterministic-Per-Song-Lyrics-and-Chords-Scores]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-2-Per-Song-Quality-Scoring-and-Prioritization]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-5-Score-Lyrics-quality-per-Song]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-6-Score-ChordsTab-quality-per-Song]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR-Category-Per-Song-LyricsChords-Quality-Scoring---appcontentscoringpy--datareviewcontent_scoresjson]
- [Source: _bmad-output/implementation-artifacts/1-5-persist-current-quality-status-for-cached-content.md]
- [Source: _bmad-output/implementation-artifacts/2-3-persist-review-decisions-with-content-hashes.md]
- [Source: app/review_state.py]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `manual create-story fallback for 2.1`
- `python3 -m unittest tests.test_content_scoring tests.test_review_state`
- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Created the canonical Story `2.1` artifact directly from the current epic/PRD/
  architecture context so orchestration could resume against the current scoring plan
  instead of the stale older Epic 2 artifact set.
- Added `app/content_scoring.py` to own the deterministic v1 score contract, including
  `0-100` integer validation, stable quality-band derivation, and score record
  construction.
- Extended `app/review_state.py` with `content_scores.json` current-state persistence
  helpers that mirror the existing quality-status and review-decision patterns.
- Added regression coverage for score-band thresholds, score-state round trips,
  malformed score-state handling, and automatic parent-directory creation.
- Verified the focused score/review-state tests and the full repository `unittest`
  suite pass from the repository root.

### File List

- `_bmad-output/implementation-artifacts/2-1-persist-deterministic-per-song-lyrics-and-chords-scores.md`
- `app/content_scoring.py`
- `app/review_state.py`
- `tests/test_content_scoring.py`
- `tests/test_review_state.py`

## Change Log

- 2026-05-23: Created the canonical Story `2.1` artifact for deterministic per-song
  score persistence and advanced sprint state to `ready-for-dev`.
- 2026-05-23: Implemented deterministic score record construction and
  `content_scores.json` persistence, then verified the full `unittest` suite passes.
