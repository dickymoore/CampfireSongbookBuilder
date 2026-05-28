# Story 2.4: Surface Reasoned Score Outputs for Review

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a reviewer,
I want quality scores to include the reasons why a song is weak,
so that I can decide quickly whether a song needs manual review or remediation.

## Acceptance Criteria

1. Given a Song receives a Lyrics or Chords/Tab quality score, when the score record is produced, then the output includes machine-readable `score_reasons` explaining the main quality signals that drove the result, and the reasons are specific enough to guide remediation targeting.
2. Given a Song has both Lyrics and Chords/Tab state, when review data is inspected, then the reasons for each `content_type` remain separate, and the system does not collapse distinct failure modes into one generic quality label.
3. Given a content item is missing, poor, or questionable, when the score record is read by an agent or human, then the reason set clearly reflects the relevant failure conditions, and the result is usable without reading raw cache content first.

## Tasks / Subtasks

- [x] Define the `score_reasons` contract for v1 scoring outputs (AC: 1-3)
  - [x] Keep `score_reasons` as a list of stable, machine-readable tokens (not prose paragraphs).
  - [x] Confirm deterministic ordering rules (e.g., quality condition first, then signals in a stable order).
  - [x] Ensure reasons are safe for reports (no secrets, no raw scraped content dumps).

- [x] Implement or confirm reason generation in the scoring composer (AC: 1-3)
  - [x] In `app/content_scoring.py`, ensure score composition emits `score_reasons` that reflect the signals used to derive `quality_score`.
  - [x] Emit reasons that are specific enough to guide targeting (e.g., `signal:missing_lyrics`, `signal:duplicate_block`, `signal:html_residue`, `signal:print_hostile_content`, `signal:low_confidence_match`).
  - [x] Ensure missing/unusable content states clearly produce reason signals describing the failure mode without requiring cache inspection.

- [x] Preserve per-`content_type` separation in both state and report outputs (AC: 2)
  - [x] Ensure each content score record remains keyed by (`song_key`, `content_type`) and never merges Lyrics and Chords into a shared reason list.
  - [x] Ensure reporting surfaces the distinct score records independently so Lyrics-vs-Chords divergence remains visible.

- [x] Persist and validate score reasons in the current-state model (AC: 1-3)
  - [x] Ensure `data/review/content_scores.json` records include `score_reasons` for each entry.
  - [x] Ensure loaders/validators treat `score_reasons` as a list of non-empty strings and fail/skip malformed entries without crashing the CLI.

- [x] Add or extend regression tests (AC: 1-3)
  - [x] Unit-test reason generation for representative weak cases (missing, questionable with signals, chords-vs-lyrics divergence).
  - [x] Assert determinism: identical inputs produce identical `quality_score`, `quality_band`, and `score_reasons`.
  - [x] Assert per-`content_type` separation remains intact in persisted/read-back structures.

- [x] Verify from repo root (AC: 1-3)
  - [x] Run focused tests for content scoring and report integration (if touched).
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- This story is about surfacing *reasons* for already-deterministic scores, not introducing model-based scoring or free-form natural-language explanations.
- Keep `score_reasons` machine-readable and stable; prefer a compact token scheme such as:
  - `quality:<quality>` (only when not `clean`)
  - `signal:<signal_code>` for each quality signal that materially contributes to the score outcome
- Avoid embedding the human-readable signal `message` strings inside `score_reasons`; keep reasons as short tokens so current-state files and reports remain compact and diff-friendly.
- Keep the score record contract stable and additive:
  - `build_content_score(...)` should continue returning `artist`, `title`, `song_key`, `content_type`, `content_hash`, `quality_score`, `quality_band`, `score_version`, `score_reasons`, `scored_at`.
  - Persist via `app/review_state.py` under `data/review/content_scores.json` (current-state), keyed by (`song_key`, `content_type`).
- Avoid cross-module duplication: compose reasons from existing quality-signal producers (e.g., `app/quality_assessment.py` and the quality-status pipeline) rather than re-parsing raw text in a second scoring pipeline.
- Preserve boundaries:
  - No remediation execution, no backup creation, and no escalation policy changes in this story (Epic 3 owns those behaviors).
  - Keep raw cache files (`data/cache/*.jsonl`) immutable; scores and reasons live in `data/review/content_scores.json`.

### Project Structure Notes

- Likely implementation files: `app/content_scoring.py`, `app/review_state.py`, `app/reporting.py`
- Likely test files: `tests/test_content_scoring.py`, `tests/test_review_state.py`, `tests/test_reporting.py`
- Keep absolute imports (`from app...`) and repo-root execution (`python3 main.py ...`) intact.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2-4-Surface-Reasoned-Score-Outputs-for-Review]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-5-Score-Lyrics-quality-per-Song]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#FR-6-Score-ChordsTab-quality-per-Song]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR-Category-Per-Song-LyricsChords-Quality-Scoring---appcontentscoringpy--datareviewcontent_scoresjson]
- [Source: _bmad-output/implementation-artifacts/2-1-persist-deterministic-lyrics-and-chords-quality-scores.md]
- [Source: _bmad-output/implementation-artifacts/2-2-compose-scores-from-existing-quality-signals.md]
- [Source: _bmad-output/implementation-artifacts/2-3-rank-songs-for-review-and-remediation-priority.md]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]

## Dev Agent Record

### Agent Model Used

GPT-5.2 (Codex CLI)

### Debug Log References

### Completion Notes List

- Defined `score_reasons` token contract and made ordering deterministic (quality token first, then signals).
- Ensured reasons only include signals that materially contribute to score penalties (no prose or raw content).
- Added regression coverage for deterministic ordering and de-duplication of signal reasons.
- Verified from repo root with `python3 -m unittest discover -s tests -p 'test_*.py'`.

### File List

- app/content_scoring.py
- tests/test_content_scoring.py
- tests/test_remediation.py
- tests/test_e2e_story_2_4_generate_from_cache.py
- _bmad-output/implementation-artifacts/sprint-status.yaml
- _bmad-output/implementation-artifacts/2-4-surface-reasoned-score-outputs-for-review.md

### Change Log

- 2026-05-28: Added deterministic, machine-readable `score_reasons` tokens for scoring outputs; extended tests.
- 2026-05-28: Senior review: fixed remediation test side-effects; aligned token contract; marked story done.

## Senior Developer Review (AI)

Date: 2026-05-28

### Findings

- HIGH: `tests/test_remediation.py` omitted `backups_dir` in multiple `run_bounded_remediation(...)` calls, causing the test suite to write remediation backup files into `data/review/backups` under the repository root.
- MEDIUM: Dev Agent Record → File List was incomplete (missing this story artifact, plus test files impacted during verification).
- LOW: `tests/test_content_scoring.py` used a non-token `score_reasons` value in a `build_content_score(...)` regression test, drifting from the `signal:<code>` contract used elsewhere.

### Fixes Applied

- Routed remediation backups to each test’s temporary workspace via `backups_dir`.
- Updated the content-scoring test to use `signal:missing_structure_signal`.
- Re-ran the full `unittest` suite after fixes.

### Verification

- `python3 -m unittest discover -s tests -p 'test_*.py'`
