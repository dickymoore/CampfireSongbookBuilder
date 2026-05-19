# Story 1.4: Detect Print-Hostile and Low-Confidence Content

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a camper printing a songbook,
I want overlong, unreadable, or likely-wrong song content flagged,
so that I can avoid printing pages that are impractical or unrelated to the requested song.

## Acceptance Criteria

1. Given lyrics or chords that exceed the story's isolated line-count, total-character, or longest-line thresholds, when quality assessment runs, then the result contains a `print_hostile_content` Quality Signal and the threshold values are centralized in one place.
2. Given a candidate whose `source_artist` or `source_title` differs materially from the requested `artist` or `title`, when deterministic confidence checks run, then the result contains a `low_confidence_match` Quality Signal that explains the mismatch.
3. Given ordinary lyrics or chord text that stays within the print-hostile thresholds and a candidate whose source metadata matches the requested song, when the checks run, then no print-hostile or low-confidence signal is emitted.
4. Given content that triggers both print-hostile and low-confidence checks, when the helper runs, then the emitted signals stay in a deterministic order and the returned quality is still a valid contract value.
5. Given an invalid `content_type`, the helper fails fast with the shared validation error instead of guessing.

## Tasks / Subtasks

- [x] Add pure print-hostile and low-confidence helpers in `app/quality_assessment.py` (AC: 1, 2, 3, 4, 5)
  - [x] Implement a helper for print-hostile assessment that accepts `content_type` plus raw `content` and returns structured output with `quality`, `signals`, and lightweight summary data.
  - [x] Use module-level threshold constants for line count, total character count, and longest-line length; keep them in one place so they can be tuned later without touching call sites.
  - [x] Implement a low-confidence helper that works from the Story 1.1 candidate contract and compares `artist`/`title` against `source_artist`/`source_title` without fuzzy matching or external enrichment.
  - [x] Keep both helpers pure: no file writes, no CLI changes, no cache mutations, and no calls to MusicBrainz, RapidFuzz, or other optional matching services.
  - [x] Build every Quality Signal through `app.content_models.build_quality_signal()` so the signal contract stays consistent with Stories 1.1 to 1.3.
  - [x] Preserve the existing missing-content and junk-content helpers unchanged except for any internal reuse that keeps the module deterministic.
- [x] Add focused unit tests in `tests/test_quality_assessment.py` (AC: 1, 2, 3, 4, 5)
  - [x] Cover threshold boundary cases so ordinary verse/chord sheets do not trip print-hostile detection.
  - [x] Cover mismatched and matching source metadata for the low-confidence helper.
  - [x] Cover combined print-hostile and low-confidence inputs and assert the signal order is stable.
  - [x] Cover invalid `content_type` handling as a fast failure.
  - [x] Assert the emitted signal shape, code, severity, message, and `content_type`.
  - [x] Confirm the helper does not mutate input text and does not depend on `app.text_cleaning`.
- [x] Preserve current app boundaries and compatibility (AC: 3, 5)
  - [x] Keep the implementation dependency-free and in the existing flat `app/*.py` module layout.
  - [x] Do not change `main.py`, `app/cache.py`, `app/text_cleaning.py`, or the existing sentinel contract values.
  - [x] Do not add file I/O, persistence logic, review-state wiring, or document-generation logic; later stories own those boundaries.
- [x] Verify from the repository root (AC: 1, 2, 3, 4, 5)
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.
  - [x] Keep new lines compatible with `.flake8` `max-line-length = 100` by inspection if no style tool is available locally.

### Review Findings

- [x] [Review][Patch] Whitespace-heavy content can evade print-hostile detection [app/quality_assessment.py:159-184] — `_meaningful_lines()` drops blank lines before the line-count check, so content padded with many empty lines is reported as clean even when it would create excessive pages. The summary line count is also underreported for that case.

## Dev Notes

- Implement this as a pure helper extension inside `app/quality_assessment.py`. It should only inspect raw content and candidate metadata and return structured results; it must not write files, call the network, or mutate caches. [Source: _bmad-output/planning-artifacts/architecture.md#Architecture-Decision-Document]
- Reuse the shared constructors and validators from `app/content_models.py` created in Story 1.1. That module already enforces `sha256:<hex>` hashes, validates nested quality signals, and provides the signal builder this story should use. [Source: _bmad-output/implementation-artifacts/1-1-define-quality-data-contracts.md]
- Story 1.2 and Story 1.3 already established the same `app/quality_assessment.py` module for missing-content and junk-content checks. Keep the helper names, return shapes, and deterministic signal ordering compatible so this story extends the same pure module rather than creating a second quality engine. [Source: _bmad-output/implementation-artifacts/1-2-detect-missing-or-unusable-lyrics-and-chords.md]
- Do not route print-hostile detection through `app.text_cleaning.clean_lyrics()` or `clean_chords()`. Those helpers normalize content for display; this story needs to inspect the raw text and flag print-hostile input rather than silently fixing it. [Source: app/text_cleaning.py]
- The architecture explicitly calls out print-hostile output and low-confidence song matches as separate concerns. Keep them deterministic and local so later report and filtering stories can identify exactly why a song was flagged. [Source: _bmad-output/planning-artifacts/architecture.md#Architecture-Decision-Document]
- Use the existing candidate contract from Story 1.1 for low-confidence checks: `artist`, `title`, `content_type`, `source`, `content`, `source_artist`, `source_title`, `status`, `error`, and `retrieved_at`. Compare requested song metadata against source metadata; do not add fuzzy matching or external enrichment in this story. [Source: _bmad-output/implementation-artifacts/1-1-define-quality-data-contracts.md]
- Keep threshold constants conservative and isolated. Ordinary chord sheets such as `[G] [D] [Em] [C]` should remain clean; print-hostile checks are about scale and readability, not bracketed chord notation or junk cleanup. [Source: _bmad-output/implementation-artifacts/1-3-detect-junk-markup-and-duplicate-content.md]
- Suggested output pattern:

```python
{
    "quality": "questionable",
    "signals": [
        {
            "code": "print_hostile_content",
            "severity": "warning",
            "message": "Lyrics are likely too long for comfortable printing.",
            "content_type": "lyrics",
        },
        {
            "code": "low_confidence_match",
            "severity": "warning",
            "message": "Source metadata does not match the requested song.",
            "content_type": "lyrics",
        },
    ],
    "summary": {
        "line_count": 84,
        "total_characters": 4620,
        "longest_line_length": 182,
        "has_print_hostile_content": True,
        "has_low_confidence_match": True,
    },
}
```

- Suggested heuristics should stay simple and explainable:
  - Long content, too many lines, or a single extremely long line indicate print-hostile input.
  - Source artist/title mismatches indicate low-confidence input.
  - Missing source metadata alone should not create a low-confidence flag.
  - Keep the order of emitted signals deterministic so test assertions stay stable.

### Project Structure Notes

- New implementation file: `app/quality_assessment.py`.
- New test file: `tests/test_quality_assessment.py`.
- No existing application files should need modification for this story unless the dev agent discovers an import or boundary issue that blocks tests; document any such change in the Dev Agent Record.
- Previous story context: Story 1.3 established junk and duplicate detection in the same pure quality-assessment module. Story 1.4 should extend that module rather than creating a separate quality engine.
- Git context at story creation: recent commits include `12da25a Automator upgrade`, `4afd01d Merge bug fixes into 2026 upgrade`, and `96f1f71 Add 2026 BMAD upgrade assets`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1-4-Detect-Print-Hostile-and-Low-Confidence-Content]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-1-Trustworthy-Content-Assessment-Foundation]
- [Source: _bmad-output/planning-artifacts/architecture.md#Architecture-Decision-Document]
- [Source: _bmad-output/planning-artifacts/architecture.md#Format-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure-Patterns]
- [Source: _bmad-output/implementation-artifacts/1-1-define-quality-data-contracts.md]
- [Source: _bmad-output/implementation-artifacts/1-3-detect-junk-markup-and-duplicate-content.md]
- [Source: app/text_cleaning.py]
- [Source: https://docs.python.org/3.12/library/re.html]
- [Source: https://docs.python.org/3.12/library/unittest.html]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 -m unittest discover -s tests -p 'test_*.py'` after resolving the review finding

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created
- Added `assess_print_hostile_content()`, `assess_low_confidence_candidate()`, and `assess_print_hostile_and_low_confidence()` to `app/quality_assessment.py` with centralized thresholds and deterministic signal ordering.
- Covered threshold boundaries, source metadata mismatch detection, combined signal ordering, and invalid content-type handling in `tests/test_quality_assessment.py`.
- Verified the full `unittest` suite passes from the repository root.
- Resolved the review finding for whitespace-heavy content by counting all lines for print-hostile detection and adding regression coverage for blank-line padding.

### File List

- `app/quality_assessment.py`
- `tests/test_quality_assessment.py`
- `_bmad-output/implementation-artifacts/1-4-detect-print-hostile-and-low-confidence-content.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

### Change Log

- 2026-05-19: Implemented print-hostile and low-confidence assessment helpers plus regression tests for story 1.4.
- 2026-05-19: Addressed code review finding - 1 item resolved (Date: 2026-05-19)
