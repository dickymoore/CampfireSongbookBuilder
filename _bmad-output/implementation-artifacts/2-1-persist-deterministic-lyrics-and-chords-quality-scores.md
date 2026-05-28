# Story 2.1: Persist Deterministic Lyrics and Chords Quality Scores

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

### Story 2.1: Persist Deterministic Lyrics and Chords Quality Scores

As a songbook operator,
I want each Song to receive persisted Lyrics and Chords quality scores,
So that content quality can be measured consistently across runs.

**Acceptance Criteria:**

**Given** a Song with current lyrics or chords content
**When** scoring runs
**Then** the system writes a deterministic score record for each relevant `content_type`
**And** each record preserves exact `artist`, `title`, `song_key`, `content_hash`, `quality_score`, `quality_band`, `score_version`, and `score_reasons`.

**Given** the same content snapshot and threshold configuration
**When** scoring is rerun
**Then** the same score outcome is produced
**And** the score uses the deterministic `0-100` v1 scale with threshold bands `85-100 clean`, `60-84 reviewable`, `40-59 questionable`, and `0-39 poor`.

**Given** score state is stored for generation and reporting
**When** downstream workflows read the current-state files
**Then** the score records remain human/agent readable
**And** they do not require scraping prose reports.

## Tasks / Subtasks

- [x] Implement deterministic score record persistence for lyrics and chords (AC: 1)
  - [x] Add/confirm load/save helpers for content scores under data/review/content_scores.json (current-state)
  - [x] Ensure record fields include identity + hash + band + reasons and remain machine-readable

- [x] Ensure determinism and identity binding (AC: 2)
  - [x] Verify same content snapshot yields same score output
  - [x] Ensure scores are tied to content_hash and stale scores are distinguishable

- [x] Add focused tests (AC: 1-2)
  - [x] Round-trip save/load for lyrics + chords entries
  - [x] Determinism test (same inputs -> same outputs)

- [x] Verify from repo root
  - [x] Run focused tests
  - [x] Run python3 -m unittest discover -s tests -p 'test_*.py'

## Dev Notes

- Reuse the existing current-state persistence patterns under data/review/ (see prior score work in this repo).
- Keep raw JSONL caches immutable; do not store scores in cache files.
- Keep changes small and test-backed.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2-1-Persist-Deterministic-Lyrics-and-Chords-Quality-Scores]
- [Source: _bmad-output/planning-artifacts/architecture.md]
- [Source: _bmad-output/project-context.md]

## Dev Agent Record

### Agent Model Used

GPT-5.2 (Codex CLI)

### Debug Log References

- Focused tests:
  - `python3 -m unittest tests.test_document_creation.TestDocumentCreation.test_create_document_from_cache_persists_content_scores_for_lyrics_and_chords`
  - `python3 -m unittest tests.test_source_retry`
  - `python3 -m unittest tests.test_review_state.TestReviewState.test_load_content_scores_reports_stale_hash_and_ignores_entry`
- Full suite:
  - `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Persist `data/review/content_scores.json` updates during both caching (`cache_lyrics` / `cache_chords`) and document creation (`create_document_from_cache`).
- Add optional stale filtering for `load_content_scores(..., current_content_hashes=...)` so stale scores can be detected/ignored using content hashes.
- Include `content_scores` in traceability report generation input when present.
- Add unit tests covering content-score persistence and stale filtering; full `unittest` suite passes.

### File List

- `_bmad-output/implementation-artifacts/2-1-persist-deterministic-lyrics-and-chords-quality-scores.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/review_state.py`
- `app/document_generation.py`
- `app/document_creation.py`
- `main.py`
- `tests/test_source_retry.py`
- `tests/test_document_creation.py`
- `tests/test_review_state.py`

## Change Log

- 2026-05-27: Persist deterministic lyrics/chords content scores, add stale filtering support, and add tests; ran full `unittest` suite.
- 2026-05-28: Senior developer review completed; hardened current-state persistence (stale filtering + line-ending normalization) and revalidated full `unittest` suite; status moved to `done`.

## Senior Developer Review (AI)

- Outcome: approved
- Git vs story discrepancies: the working tree includes unrelated diffs outside this story’s File List (notably under `.agents/skills/bmad-story-automator/` and other `_bmad-output/implementation-artifacts/*` files). Review scope here is limited to validating Story 2.1 requirements against the application source changes in the File List.
- Acceptance Criteria:
  - AC1 verified via current-state persistence in `app/review_state.py` (/home/dicky/CampfireSongbookBuilder/app/review_state.py:1191) and generation/caching integration in `app/document_generation.py` (/home/dicky/CampfireSongbookBuilder/app/document_generation.py:90) plus `app/document_creation.py` (/home/dicky/CampfireSongbookBuilder/app/document_creation.py:379).
  - AC2 verified via deterministic scoring scale + band thresholds in `app/content_scoring.py` (/home/dicky/CampfireSongbookBuilder/app/content_scoring.py:84) and deterministic compose behavior in `tests/test_content_scoring.py` (see `test_compose_content_scores_is_deterministic_for_identical_inputs`).
  - AC3 verified via machine-readable JSON state and downstream report plumbing in `main.py` (/home/dicky/CampfireSongbookBuilder/main.py:43).
- Findings addressed during review:
  - Normalized mixed CRLF/LF line endings in `app/document_generation.py` to keep diffs stable and avoid cross-platform tooling issues.
  - Ensured `content_scores.json` load uses `current_content_hashes` when merging updates so stale score records are automatically ignored during generation runs (`app/document_creation.py` (/home/dicky/CampfireSongbookBuilder/app/document_creation.py:379) and `app/document_generation.py` (/home/dicky/CampfireSongbookBuilder/app/document_generation.py:90)).
- Verification:
  - `python3 -m unittest tests.test_document_creation.TestDocumentCreation.test_create_document_from_cache_persists_content_scores_for_lyrics_and_chords`
  - `python3 -m unittest tests.test_source_retry`
  - `python3 -m unittest tests.test_review_state.TestReviewState.test_load_content_scores_reports_stale_hash_and_ignores_entry`
  - `python3 -m unittest discover -s tests -p 'test_*.py'`
- Notes:
  - External documentation search was not required for this story review; validation was performed via local architecture/context docs and the existing unit test suite.
