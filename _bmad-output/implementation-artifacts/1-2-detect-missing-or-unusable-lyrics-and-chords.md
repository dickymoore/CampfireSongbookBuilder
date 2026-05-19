# Story 1.2: Detect Missing or Unusable Lyrics and Chords

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a musician preparing a songbook,
I want missing or unusable lyrics/chords to be flagged automatically,
so that empty pages or "not found" content do not silently reach a print-ready book.

## Acceptance Criteria

1. Given lyrics or chords content that is empty, `None`, non-string, `"Lyrics not found."`,
   or `"Chords not found."`, when quality assessment runs, then the result is marked
   `missing` or `questionable` with a structured Quality Signal.
2. Given that structured Quality Signal, then it includes the affected `content_type`, a
   stable code, a severity, and a human-readable message.
3. Given valid non-empty lyrics or chords content, when the missing-content checks run,
   then no missing-content signal is emitted.
4. Given `content_type` values outside the accepted contract, when quality assessment is
   called, then the helper fails fast with a clear validation error instead of silently
   guessing.
5. Given the existing sentinel values `"Lyrics not found."` and `"Chords not found."`,
   when this story is implemented, then those values remain recognized exactly as written
   and are not normalized away or replaced.

## Tasks / Subtasks

- [x] Add pure missing-content assessment helpers in `app/quality_assessment.py` (AC: 1, 2, 3, 4, 5)
  - [x] Implement a helper that accepts `content_type` plus raw `content` and returns a
        structured result containing a `quality` value and a list of Quality Signal
        dictionaries.
  - [x] Treat `None`, non-string values, and strings that are empty after trimming
        whitespace as `missing`.
  - [x] Treat the exact sentinel values `"Lyrics not found."` and `"Chords not found."`
        as `questionable`, not clean.
  - [x] Build all signals through `app.content_models.build_quality_signal()` so the
        returned shape stays consistent with the contract story.
  - [x] Use stable, content-type-specific codes and messages:
        `missing_lyrics`, `missing_chords`, `unusable_lyrics`, `unusable_chords`.
  - [x] Use `error` severity for missing content and `warning` severity for explicit
        not-found sentinels.
  - [x] Validate `content_type` through the shared contract helpers and raise on invalid
        values instead of silently coercing them.
  - [x] Keep the helper pure: no file writes, no CLI changes, no cache mutations, and no
        text-cleaning side effects.
- [x] Add focused unit tests in `tests/test_quality_assessment.py` (AC: 1, 2, 3, 4, 5)
  - [x] Cover empty string, whitespace-only string, `None`, and non-string inputs for
        both lyrics and chords.
  - [x] Cover the exact `"Lyrics not found."` and `"Chords not found."` sentinel cases.
  - [x] Cover valid non-empty lyrics and chords producing no missing-content signal.
  - [x] Cover invalid `content_type` handling as a fast failure.
  - [x] Assert the emitted signal shape, code, severity, message, and `content_type`.
- [x] Preserve current app boundaries and compatibility (AC: 4, 5)
  - [x] Keep the implementation dependency-free and in the existing flat `app/*.py`
        module layout.
  - [x] Do not change `main.py`, `app/cache.py`, `app/text_cleaning.py`, or the
        existing sentinel contract values.
  - [x] Do not add file I/O or persistence logic; later stories own status files and
        generation orchestration.
- [x] Verify from the repository root (AC: 1, 2, 3, 4, 5)
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.
  - [x] Keep new lines compatible with `.flake8` `max-line-length = 100` by inspection
        if no style tool is available locally.

## Dev Notes

- Implement this as a pure helper module in `app/quality_assessment.py`. It should only
  inspect raw content and return structured results; it must not write files, call the
  network, or mutate caches. [Source:
  _bmad-output/planning-artifacts/architecture.md#Component-Boundaries]
- Reuse the shared constructors and validators from `app/content_models.py` created in
  Story 1.1. That module now enforces `sha256:<hex>` hashes and validates nested quality
  signals, so this story should build on those contracts instead of duplicating them.
  [Source: _bmad-output/implementation-artifacts/1-1-define-quality-data-contracts.md]
- The current `app/text_cleaning.py` helper collapses non-string inputs to empty strings
  and strips other scraper residue. Do not route missing-content checks through that
  module; this story must evaluate the raw content value directly so `None`, non-string,
  empty, and sentinel inputs stay distinguishable. [Source: app/text_cleaning.py]
- Existing cache identity and sentinel values remain compatibility contracts. Exact
  `"Lyrics not found."` and `"Chords not found."` strings must continue to be recognized
  literally, and no global normalization of `artist` or `title` should be introduced in
  this story. [Source:
  _bmad-output/planning-artifacts/architecture.md#Format-Patterns]
- Expected signal pattern for missing content:

```json
{
  "code": "missing_lyrics",
  "severity": "error",
  "message": "Lyrics are missing or unusable.",
  "content_type": "lyrics"
}
```

- Expected signal pattern for explicit not-found content:

```json
{
  "code": "unusable_chords",
  "severity": "warning",
  "message": "Chords were not found.",
  "content_type": "chords"
}
```

- The return shape should be simple and predictable, for example:

```python
{
    "quality": "missing",
    "signals": [
        {
            "code": "missing_lyrics",
            "severity": "error",
            "message": "Lyrics are missing or unusable.",
            "content_type": "lyrics",
        }
    ],
}
```

### Project Structure Notes

- New implementation file: `app/quality_assessment.py`.
- New test file: `tests/test_quality_assessment.py`.
- No existing application files should need modification for this story unless the dev
  agent discovers an import or boundary issue that blocks tests; document any such change
  in the Dev Agent Record.
- Previous story context: Story 1.1 created the shared content contracts and contract
  validators in `app/content_models.py`. Reuse those helpers rather than inventing a
  parallel shape.
- Git context at story creation: recent commits include `12da25a Automator upgrade`,
  `4afd01d Merge bug fixes into 2026 upgrade`, and `96f1f71 Add 2026 BMAD upgrade assets`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1-2-Detect-Missing-or-Unusable-Lyrics-and-Chords]
- [Source: _bmad-output/planning-artifacts/architecture.md#Component-Boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#Format-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Functional-Requirements-Coverage]
- [Source: _bmad-output/implementation-artifacts/1-1-define-quality-data-contracts.md]
- [Source: app/text_cleaning.py]
- [Source: https://docs.python.org/3.12/library/unittest.html]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `python3 -m unittest tests.test_quality_assessment`
- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created
- Added `app/quality_assessment.py` with a pure missing-content assessor that marks
  empty/`None`/non-string inputs as `missing`, exact sentinel strings as
  `questionable`, and valid content as `clean`.
- Added `tests/test_quality_assessment.py` to cover both content types, exact sentinel
  handling, invalid `content_type` failures, and stable signal shape.
- Verified the full `unittest` suite passes from the repository root.

### File List

- `app/quality_assessment.py`
- `tests/test_quality_assessment.py`

## Change Log

- 2026-05-19: Implemented missing-content quality assessment and regression tests for
  story 1.2.
