# Story 1.3: Detect Junk, Markup, and Duplicate Content

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook builder user,
I want obvious scraper residue, duplicate junk, and unreadable markup flagged,
so that bad source material is reviewable before it pollutes the songbook.

## Acceptance Criteria

1. Given lyrics or chords containing known junk patterns such as HTML residue,
   email/header artifacts, repeated identical blocks, or excessive bracket noise, when
   quality assessment runs, then the result contains one or more warning or error Quality
   Signals explaining the issue.
2. Given ordinary lyrics or chord text without detected junk patterns, when the junk and
   duplication checks run, then no junk-related signal is emitted.
3. Given raw content that can be safely cleaned without losing meaning, when the helper
   assesses it, then the output distinguishes between removable residue and retained
   warning signals instead of silently replacing one with the other.
4. Given content that is effectively unreadable or duplicated enough to undermine the
   song, when the helper runs, then it can mark the quality as `questionable` or `missing`
   and emit at least one warning or error signal.
5. Given a caller passes an invalid `content_type`, the helper fails fast with a clear
   validation error instead of guessing.

## Tasks / Subtasks

- [x] Add pure junk, markup, and duplicate assessment helpers in `app/quality_assessment.py` (AC: 1, 2, 3, 4, 5)
  - [x] Implement a helper that accepts `content_type` plus raw `content` and returns a
        structured result containing `quality`, `signals`, and any lightweight summary
        data needed by later stories.
  - [x] Keep the helper pure: no file writes, no CLI changes, no cache mutations, and no
        calls to `app.text_cleaning` for the decision itself.
  - [x] Use deterministic, local heuristics for junk markup, email/header residue,
        duplicate blocks, and excessive bracket noise.
  - [x] Treat HTML residue and header-like lines as retained warning signals rather than
        cleaning them away inside the assessment step.
  - [x] Emit stable codes that future reports can key on, such as `html_residue`,
        `email_header_artifacts`, `duplicate_block`, `excessive_bracket_noise`, and
        `unreadable_markup`.
  - [x] Use `warning` severity for removable junk and `error` severity when duplication
        or markup makes the content effectively unreadable.
  - [x] Validate `content_type` through the shared contract helpers from Story 1.1 and
        raise on invalid values instead of silently coercing them.
  - [x] Build every Quality Signal through `app.content_models.build_quality_signal()` so
        the signal contract stays consistent.
- [x] Add focused unit tests in `tests/test_quality_assessment.py` (AC: 1, 2, 3, 4, 5)
  - [x] Cover HTML residue, email/header artifacts, duplicate blocks, and bracket noise.
  - [x] Cover valid lyrics and chords that contain no junk signals.
  - [x] Cover mixed input that triggers multiple signals and preserves a stable order.
  - [x] Cover invalid `content_type` handling as a fast failure.
  - [x] Assert the emitted signal shape, code, severity, message, and `content_type`.
  - [x] Confirm the assessment helper does not mutate the input text and does not depend
        on `app.text_cleaning`.
- [x] Preserve current app boundaries and compatibility (AC: 3, 5)
  - [x] Keep the implementation dependency-free and in the existing flat `app/*.py`
        module layout.
  - [x] Do not change `main.py`, `app/cache.py`, `app/text_cleaning.py`, or the existing
        sentinel contract values.
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
  Story 1.1. That module now enforces `sha256:<hex>` hashes, validates nested quality
  signals, and provides the signal builder this story should use. [Source:
  _bmad-output/implementation-artifacts/1-1-define-quality-data-contracts.md]
- Story 1.2 will introduce the same `app/quality_assessment.py` module for missing-content
  detection. Keep the helper names and return shapes compatible so the two stories can
  live in the same pure module without duplicating logic. [Source:
  _bmad-output/implementation-artifacts/1-2-detect-missing-or-unusable-lyrics-and-chords.md]
- Do not route junk detection through `app.text_cleaning.clean_lyrics()` or
  `clean_chords()`. Those helpers normalize away scraps of residue; this story needs to
  see the raw junk so it can emit retained warning signals. [Source: app/text_cleaning.py]
- The architecture explicitly calls out junk markup, duplicate blocks, unreadable
  formatting, and preserved warnings as separate concerns. Keep the helper deterministic
  and local so reports can identify exactly why a song was flagged. [Source:
  _bmad-output/planning-artifacts/architecture.md#API-Communication-Patterns]
- Suggested output pattern:

```python
{
    "quality": "questionable",
    "signals": [
        {
            "code": "html_residue",
            "severity": "warning",
            "message": "HTML residue was detected in the source text.",
            "content_type": "lyrics",
        },
        {
            "code": "duplicate_block",
            "severity": "error",
            "message": "Repeated blocks make the lyrics difficult to trust.",
            "content_type": "lyrics",
        },
    ],
}
```

- Suggested heuristics should stay simple and explainable:
  - HTML-like tags or entities indicate residue.
  - Email/header lines indicate scraped junk.
  - Repeated adjacent lines or repeated blocks indicate duplication.
  - Dense bracket/tag noise indicates unreadable markup.
- Keep the order of emitted signals deterministic so test assertions stay stable.

### Project Structure Notes

- New implementation file: `app/quality_assessment.py`.
- New test file: `tests/test_quality_assessment.py`.
- No existing application files should need modification for this story unless the dev
  agent discovers an import or boundary issue that blocks tests; document any such change
  in the Dev Agent Record.
- Previous story context: Story 1.2 defines the missing-content branch for the same pure
  quality-assessment module. Story 1.3 should extend that module rather than creating a
  separate quality engine.
- Git context at story creation: recent commits include `12da25a Automator upgrade`,
  `4afd01d Merge bug fixes into 2026 upgrade`, and `96f1f71 Add 2026 BMAD upgrade assets`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1-3-Detect-Junk-Markup-and-Duplicate-Content]
- [Source: _bmad-output/planning-artifacts/architecture.md#API-Communication-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Component-Boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#Functional-Requirements-Coverage]
- [Source: _bmad-output/implementation-artifacts/1-1-define-quality-data-contracts.md]
- [Source: _bmad-output/implementation-artifacts/1-2-detect-missing-or-unusable-lyrics-and-chords.md]
- [Source: app/text_cleaning.py]
- [Source: https://docs.python.org/3.12/library/re.html]
- [Source: https://docs.python.org/3.12/library/unittest.html]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `python3 -m unittest tests.test_quality_assessment`
- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created
- Added `app/quality_assessment.py` junk assessment helpers for HTML residue, header
  artifacts, duplicate blocks, and bracket noise with deterministic signal ordering.
- Added `tests/test_quality_assessment.py` to cover stable codes, severities, summary
  fields, invalid `content_type` failures, and no-mutation behavior.
- Verified the full `unittest` suite passes from the repository root.

### File List

- `app/quality_assessment.py`
- `tests/test_quality_assessment.py`

## Change Log

- 2026-05-19: Implemented junk, markup, and duplicate quality assessment plus regression
  tests for story 1.3.

### Review Findings

- [x] [Review][Patch] Ordinary bracketed chord notation is flagged as junk [app/quality_assessment.py:85-88, 131-148] — the current threshold treats common chord markup like `[G] [D] [Em] [C]` as `excessive_bracket_noise`, which can also force `quality: "missing"`. That violates the story's requirement that ordinary lyrics or chords without junk patterns emit no junk-related signal.
- [x] [Review][Patch] Duplicate detection only catches immediately repeated single lines [app/quality_assessment.py:69-82] — repeated identical blocks separated by other lines still pass as clean, so repeated verse/chorus material is not reliably detected.
- [x] [Review][Patch] HTML residue detection misses common numeric entities [app/quality_assessment.py:55] — the residue regex only matches named entities, so scraped text such as `&#39;` or `&#160;` is not flagged.
- [x] [Review][Patch] Missing-content sentinels are accepted for the wrong content type [app/quality_assessment.py:39-43] — `Lyrics not found.` and `Chords not found.` are both accepted regardless of `content_type`, which can label chord sentinels as missing lyrics and vice versa instead of validating the sentinel against the declared type.
