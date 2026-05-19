# Story 3.2: Summarize Newly Added Song Outcomes

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a musician adding a batch of songs,
I want a clear summary of which songs are clean, missing, Questionable, or invalid input,
so that I only spend time reviewing songs that need attention.

## Acceptance Criteria

1. Given a fetch/cache workflow processes songs and invalid rows from the CSV loader, when the run completes, then the CLI summary or report classifies each processed song as clean/found, Questionable, missing, or invalid input, and points to the generated report file.
2. Given clean songs, Questionable songs, and missing songs are all present, when summary output is generated, then clean songs are grouped separately from problem songs, and each problem item includes the primary reason or top quality signal.
3. Given invalid source-list rows were returned by `load_songs`, when summary output is generated, then those rows appear in an invalid-input group with row number and raw artist/title values, and they are not merged into the clean/problem groups.
4. Given the CLI finishes a cache/fetch branch, when the summary is printed, then it remains concise, human-readable, and still includes the machine-readable report path written by `app.reporting`.
5. Given this story is implemented, then it does not change source retry behavior, quality heuristics, review-state persistence, or cache schemas; it only composes and surfaces outcome summaries from existing data.

## Tasks / Subtasks

- [x] Add grouped outcome-summary composition in `app/reporting.py` or a small adjacent helper (AC: 1, 2, 3, 4, 5)
  - [x] Reuse `report_data["entries"]` as the canonical source for clean, Questionable, and missing song outcomes.
  - [x] Thread invalid-row validation records from `load_songs()` into the report data instead of re-parsing logs or CSV files.
  - [x] Keep the existing report JSON shape backward-compatible; any new fields should be additive.
  - [x] Include stable per-item details such as `song_key`, `content_type`, `quality`, `included`, `reason`, and the first quality signal when present.
- [x] Surface the grouped summary through the CLI in `main.py` (AC: 1, 2, 3, 4)
  - [x] Keep the current repo-root command flow unchanged for `--cache-only`, `--generate-from-cache`, `--lyrics-only`, and `--chords-only`.
  - [x] Print a concise human-readable summary after report generation.
  - [x] Preserve the existing report-file pointer so the user can inspect the full machine-readable output.
- [x] Keep fetch/cache behavior and current document generation intact (AC: 5)
  - [x] Do not change source fallback logic, cache writes, or quality assessment rules in this story.
  - [x] Reuse the existing `create_document_from_cache()` report entries rather than adding a second reporting path.
- [x] Add focused regression tests in `tests/test_reporting.py` and, if needed, `tests/test_load_songs.py` or `tests/test_document_creation.py` (AC: 1, 2, 3, 4, 5)
  - [x] Cover grouped clean/questionable/missing output.
  - [x] Cover invalid-input rows appearing as a separate group with row context.
  - [x] Cover the CLI summary still printing the report path and remaining concise.
  - [x] Cover backward compatibility for the existing report summary fields.
- [x] Verify from the repository root (AC: 1, 2, 3, 4, 5)
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- `main.py` already loads songs once per run, receives `(songs, invalid_song_rows)` from `load_songs()`, and calls `_write_generation_report()` after `create_document_from_cache()`. This story should use that hook rather than inventing a parallel output flow.
- `app/reporting.py` already writes the traceable JSON report and prints a one-line count summary. It currently summarizes included, excluded, missing, Questionable, and overridden counts, but not grouped per-song outcomes or invalid CSV rows.
- `app/document_creation.py` already emits per-song entries with `quality`, `included`, `reason`, `signals`, `quality_status`, and `review_decision`. Reuse those records instead of scraping console text or re-running assessment.
- `app/load_songs.py` now returns structured invalid-row records with `row_number`, `raw_artist`, `raw_title`, `skip`, and `reason`. Use that record directly for the invalid-input summary group.
- `app/document_generation.py` still prints separate "Missing Lyrics" / "Missing Chords" summaries during fetch. Keep those messages unless the new run-complete summary provides the same or better information without regressing current feedback.
- Story 3.1 already solved malformed-row detection and skip filtering. This story should not re-validate CSV structure or change row selection rules.
- Preserve absolute `app.*` imports, flat module layout, and unittest-based coverage from the project context.

### Suggested Summary Shape

Keep the summary additive and machine-readable. One workable shape is:

```python
{
    "summary": {
        "counts": {
            "clean": 12,
            "questionable": 3,
            "missing": 2,
            "invalid_input": 1,
        },
        "clean_songs": [
            {
                "song_key": "The Campfire Trio - Trail Song",
                "content_type": "lyrics",
                "quality": "clean",
                "included": True,
                "reason": "Content passed quality checks.",
            }
        ],
        "questionable_songs": [
            {
                "song_key": "The Campfire Trio - Long Song",
                "content_type": "lyrics",
                "quality": "questionable",
                "included": False,
                "reason": "Lyrics are too long and were excluded from the document.",
                "top_signal": {
                    "code": "print_hostile_content",
                    "severity": "warning",
                    "message": "Content is likely too long for comfortable printing.",
                },
            }
        ],
        "missing_songs": [],
        "invalid_input_rows": [
            {
                "row_number": 7,
                "raw_artist": null,
                "raw_title": "Untitled Song",
                "reason": "missing artist",
            }
        ],
    }
}
```

Use the first signal in `signals` as the top signal if the implementation needs a deterministic rule.

### Project Structure Notes

- Likely touch points: `app/reporting.py`, `main.py`, and possibly `app/document_generation.py` if the report payload needs to carry invalid-row records through to the final summary.
- Keep this story local to summary composition and presentation. Do not add new persistence files, new cache formats, or new quality heuristics here.
- If any report fields are extended, keep existing keys stable so Story 2.5 and the current report consumers continue to work.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3-2-Summarize-Newly-Added-Song-Outcomes]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/prd.md#4-3-Easier-Song-Addition]
- [Source: _bmad-output/planning-artifacts/architecture.md#API-And-Communication-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture]
- [Source: _bmad-output/implementation-artifacts/3-1-validate-source-list-rows-before-fetching.md]
- [Source: _bmad-output/implementation-artifacts/2-5-produce-traceable-quality-reports.md]
- [Source: app/load_songs.py]
- [Source: app/document_generation.py]
- [Source: app/document_creation.py]
- [Source: app/reporting.py]
- [Source: main.py]
- [Source: app/source_attempts.py]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Extended `app/reporting.py` to build grouped clean, questionable, missing, and invalid-input summary data from existing report entries.
- Threaded invalid source-row records from `load_songs()` through `main.py` into the final report payload so the summary stays data-driven.
- Updated the CLI summary text to stay concise while still printing the report path and the grouped counts.
- Added regression coverage in `tests/test_reporting.py` for grouped report content, invalid-row handling, backward-compatible summary fields, and CLI output.
- Verified the full unittest suite from the repository root with `python3 -m unittest discover -s tests -p 'test_*.py'`.

### Completion Notes List

- Report summaries now include additive grouped outcome lists for clean, questionable, missing, and invalid-input rows.
- Existing report consumers keep their legacy count fields, so the report shape remains backward-compatible.
- The CLI still prints the generated report path after each cache/fetch branch completes.
- Invalid CSV rows are surfaced in the report summary using the structured validation records from `load_songs()`.

### File List

- app/reporting.py
- main.py
- tests/test_reporting.py
- _bmad-output/implementation-artifacts/3-2-summarize-newly-added-song-outcomes.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- _bmad-output/story-automator/orchestration-1-20260519-165455.md

## Change Log

- 2026-05-19: Added grouped outcome summary composition, threaded invalid loader rows into the report payload, updated the CLI summary, and added regression tests.
- 2026-05-19: Review pass normalized invalid-row values for JSON output, hardened the report writer against missing report data, and updated the file list to reflect the review artifacts.

## Senior Developer Review (AI)

- Normalized invalid row values before report serialization so the machine-readable report stays valid JSON.
- Guarded the report writer against a missing `create_document_from_cache()` result.
- Synced the story status after verification and updated the file list to include the orchestration artifact touched by the workflow.

## Status

done
