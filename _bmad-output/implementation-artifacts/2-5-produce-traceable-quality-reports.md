# Story 2.5: Produce Traceable Quality Reports

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook builder user,
I want a report explaining included, excluded, missing, and overridden songs,
so that I can quickly review what needs attention before printing.

## Acceptance Criteria

1. Given a generation or quality run evaluates songs, when reporting runs, then a machine-readable report is written under `data/review/reports/`.
2. Given report output is generated, then the report includes included songs, excluded songs, missing content, Questionable signals, source-attempt references where available, and explicit review decisions.
3. Given report output is generated, when the CLI completes, then the user sees a concise summary pointing to the report file.
4. Given a report is written, then no API tokens or private config values are included.
5. Given this story is implemented, then it does not add selection handling, Markdown generation, or output rendering beyond the report and concise summary layer.

## Tasks / Subtasks

- [x] Add report-building helpers in `app/reporting.py` (AC: 1, 2, 4)
  - [x] Accept structured generation/filter results and quality/review state without re-running assessment logic.
  - [x] Emit a machine-readable JSON report under `data/review/reports/` with stable fields for included, excluded, missing, Questionable, source-attempt, and review-decision data.
  - [x] Sanitize report payloads so private config values and API tokens cannot leak into the artifact.
  - [x] Keep helpers pure except for the final write step.
- [x] Add a concise CLI summary path for completed generation or quality runs (AC: 3)
  - [x] Point the user to the report file path and summarize the run outcome in one short message.
  - [x] Preserve existing repo-root CLI behavior and keep the summary non-intrusive.
- [x] Add focused tests in `tests/test_reporting.py` and, if needed, a small CLI integration test (AC: 1, 2, 3, 4, 5)
  - [x] Cover report file creation, required sections, source-attempt references, review-decision inclusion, and redaction of private values.
  - [x] Cover the CLI summary mentions the report path without exposing secrets.
- [x] Preserve current boundaries and compatibility (AC: 1, 2, 3, 4, 5)
  - [x] Do not add selection logic or Markdown generation in this story.
  - [x] Do not change review-state schemas or generation filtering behavior.
  - [x] Keep report format stable enough for later Story 5.x output work to consume.
- [x] Verify from the repository root (AC: 1, 2, 3, 4, 5)
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Story 2.4 already produces include/exclude results with quality status, review decision, and reason metadata. Reuse that shape instead of re-deriving song decisions inside reporting.
- `data/review/reports/` is the required report boundary. Reports are snapshots, not state sources.
- Reports must include traceable reason codes and references where available so users can see why a song was included or excluded.
- Keep the report layer separate from Markdown generation and `.docx` rendering. This story is about traceability, not book output.
- The report must not leak secrets from `data/config/config.json` or any runtime config objects.
- Preserve absolute `app.*` imports and the flat helper-module layout.

### Suggested Report Shape

```python
{
    "generated_at": "2026-05-19T15:14:19+01:00",
    "report_type": "quality_run",
    "source": "generate_from_cache",
    "summary": {
        "included_count": 0,
        "excluded_count": 0,
        "missing_count": 0,
        "questionable_count": 0,
        "overridden_count": 0
    },
    "songs": [
        {
            "song_key": "The Campfire Trio - Trail Song",
            "content_type": "lyrics",
            "quality": "questionable",
            "included": False,
            "decision_source": "default_exclude",
            "reason": "Questionable content excluded by default.",
            "signals": [...],
            "source_attempts": [...],
            "review_decision": {...}
        }
    ]
}
```

Keep the schema stable and additive so later Markdown and `.docx` stories can consume it without reshaping the report layer.

### Project Structure Notes

- Likely implementation files: `app/reporting.py`, `app/document_generation.py`, `main.py`, `tests/test_reporting.py`
- Keep report generation separate from `app/generation_filtering.py`; that module should stay focused on include/exclude decisions.
- Keep Markdown and `.docx` work out of this story; Story 5.x owns the downstream output pipeline.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2-5-Produce-Traceable-Quality-Reports]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision-Impact-Analysis]
- [Source: _bmad-output/planning-artifacts/architecture.md#File-Structure-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Pattern-Enforcement]
- [Source: _bmad-output/implementation-artifacts/2-4-apply-questionable-exclusion-and-override-rules.md]
- [Source: _bmad-output/implementation-artifacts/2-3-persist-review-decisions-with-content-hashes.md]
- [Source: _bmad-output/implementation-artifacts/1-5-persist-current-quality-status-for-cached-content.md]
- [Source: app/document_creation.py]
- [Source: app/generation_filtering.py]
- [Source: app/review_state.py]
- [Source: app/source_attempts.py]
- [Source: main.py]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]

## Dev Agent Record

### Debug Log

- Resolved BMAD workflow config and loaded the story, sprint state, and project context before making changes.
- Updated `app/document_creation.py` so report entries reflect the actual document outcome after the print-length gate.
- Added coverage in `tests/test_document_creation.py` for overlong lyrics exclusion reporting.
- Added coverage in `tests/test_reporting.py` for the CLI summary path on both `--generate-from-cache` and `--lyrics-only`.
- Ran the full unittest suite from the repository root and verified it passed.

### Completion Notes

- Traceability reports are written under `data/review/reports/` as JSON snapshots.
- Reports include included, excluded, missing, questionable, and overridden counts, plus source attempts and review decisions where available.
- Report payloads are sanitized so config-like secrets are not emitted.
- The CLI now prints a single concise line pointing to the generated report file after generation runs.
- Report entries now reflect the actual document output, including lyrics excluded after the print-length gate.

## File List

- `.gitignore`
- `app/content_models.py`
- `app/document_creation.py`
- `app/document_generation.py`
- `app/fetch_data.py`
- `app/generation_filtering.py`
- `app/quality_assessment.py`
- `app/reporting.py`
- `app/review_state.py`
- `app/source_attempts.py`
- `main.py`
- `tests/test_content_models.py`
- `tests/test_document_creation.py`
- `tests/test_generation_filtering.py`
- `tests/test_quality_assessment.py`
- `tests/test_reporting.py`
- `tests/test_review_state.py`
- `tests/test_source_attempts.py`
- `tests/test_source_retry.py`
- `_bmad-output/implementation-artifacts/2-5-produce-traceable-quality-reports.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Change Log

- Added JSON traceability report generation and write helpers.
- Added CLI summary output for completed generation runs.
- Added regression coverage for report content, redaction, summary output, and document-level exclusions.
- Added overlong-lyrics exclusion reporting to keep the report aligned with the actual document output.
- Updated the story artifact and sprint tracker to `done`.
