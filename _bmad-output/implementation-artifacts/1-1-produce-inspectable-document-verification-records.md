# Story 1.1: Produce Inspectable Document Verification Records

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook operator,
I want each generated artifact to produce a machine-readable verification record,
so that agents and reports can inspect document-quality results without scraping console output.

## Acceptance Criteria

1. Given a generation run produces Markdown or `.docx` output, when document verification
   runs, then a local verification record is written with artifact identity, verification
   status, reasons, and timestamp, and the record format is stable and human/agent readable.
2. Given multiple output artifacts are generated in one run, when verification records are
   created, then each artifact receives its own result entry, and the entries remain
   distinguishable by artifact identity and type.

## Tasks / Subtasks

- [x] Add dedicated document-verification state helpers in `app/document_verification.py` (AC: 1, 2)
  - [x] Define a stable record builder and validators for `artifact_path`, `artifact_type`,
        `verification_status`, `verification_reasons`, and `verified_at` using `snake_case`
        keys.
  - [x] Persist state to `data/review/document_quality.json` with a versioned top-level
        document such as `version`, `updated_at`, and `entries`, following the current
        loader/writer pattern already used by `app/review_state.py`.
  - [x] Keep artifact identity stable and explicit so Markdown and `.docx` outputs from
        the same run remain separate records instead of overwriting one another.
  - [x] Reject malformed required fields with focused validation errors that identify the
        file path, field, and bad value.
- [x] Keep document-verification persistence separate from existing content-quality and report state (AC: 1, 2)
  - [x] Do not repurpose `data/cache/*.jsonl`, `data/review/quality_status.json`, or
        `data/review/review_decisions.json` for document verification state.
  - [x] Do not treat the existing traceable quality report output in `app/reporting.py`
        as the source of truth for artifact verification state; keep
        `data/review/document_quality.json` as the dedicated current-state file.
  - [x] Keep this story limited to record construction, validation, and load/save
        behavior; deterministic neatness heuristics and review-ready gate decisions belong
        to Stories `1.2` and `1.3`.
- [x] Add focused unit tests in `tests/test_document_verification.py` (AC: 1, 2)
  - [x] Cover save/load round-trips for multiple artifacts in one run, including at least
        one Markdown record and one `.docx` record.
  - [x] Cover missing-file behavior, malformed JSON, and invalid nested entries while
        preserving valid records when possible.
  - [x] Cover artifact identity collisions or near-collisions so records stay
        distinguishable by path and type.
- [x] Verify from the repository root (AC: 1, 2)
  - [x] Run `python3 -m unittest tests.test_document_verification`.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- Implement this as a new flat helper module under `app/`; keep `main.py` as a thin
  orchestrator and keep `app/reporting.py` as the aggregation layer for machine-readable
  run outputs. [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
  [Source: _bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries]
- Follow the existing persistence style in `app/review_state.py`: a versioned top-level
  JSON document, recoverable validation errors returned to callers, and parent-directory
  creation before save. Reuse that pattern instead of inventing a second state-management
  style. [Source: app/review_state.py]
- Existing generation flow writes Markdown and `.docx` artifacts in
  `app/document_creation.py`, then returns machine-readable run metadata to `main.py`.
  This story should establish the document-verification record contract that later
  generation/reporting stories can call without changing current inclusion, filtering, or
  content-quality behavior. [Source: app/document_creation.py] [Source: main.py]
- Keep document verification state separate from the current traceable quality reports.
  `app/reporting.py` writes run summaries under `data/review/reports`, while the
  architecture reserves `data/review/document_quality.json` for current document
  verification state. Do not collapse those two contracts in this story. [Source:
  app/reporting.py] [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture]
- The architecture leaves artifact identity wording slightly under-specified. For this
  story, use stable file-path identity plus explicit `artifact_type` so outputs such as
  `data/output/Lyrics_Document.md` and `data/output/Lyrics_Document.docx` persist as
  separate records. [Source: _bmad-output/planning-artifacts/architecture.md#Gap-Analysis-Results]
- Preserve current repo-root execution, raw cache immutability, and exact song identity
  semantics. This story is about artifact verification records only; it must not change
  `artist`, `title`, `song_key`, cache readers/writers, or sentinel missing-content
  values. [Source: _bmad-output/project-context.md#Critical-Dont-Miss-Rules]
- No UX specification exists for this slice, and none is needed here; the PRD and
  architecture both define a CLI-first, local-file workflow. [Source:
  _bmad-output/planning-artifacts/epics.md#UX-Design-Requirements] [Source:
  _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#8-1-In-Scope]

### Suggested Record Shape

Verification state document:

```python
{
    "version": 1,
    "updated_at": "2026-05-21T16:00:00+01:00",
    "entries": {
        "data/output/Lyrics_Document.docx": {
            "artifact_path": "data/output/Lyrics_Document.docx",
            "artifact_type": "docx",
            "verification_status": "passed",
            "verification_reasons": [],
            "verified_at": "2026-05-21T16:00:00+01:00",
        },
        "data/output/Lyrics_Document.md": {
            "artifact_path": "data/output/Lyrics_Document.md",
            "artifact_type": "markdown",
            "verification_status": "failed",
            "verification_reasons": [
                "placeholder reason supplied by later neatness checks"
            ],
            "verified_at": "2026-05-21T16:00:00+01:00",
        },
    },
}
```

- Keep the persisted enum surface narrow and explicit. Prefer stable values such as
  `passed` and `failed` for `verification_status` rather than ad hoc prose.
- Save only records produced by an actual verification step; do not use this file as a
  generic artifact inventory.

### Project Structure Notes

- New implementation file: `app/document_verification.py`
- New regression test file: `tests/test_document_verification.py`
- Existing reference files the dev agent should read before coding:
  `app/review_state.py`, `app/document_creation.py`, `app/reporting.py`, and `main.py`
- No required changes to `app/cache.py`, `app/quality_assessment.py`, or current
  report-summary formatting are in scope for this story.

### Latest Technical Notes

- The current official Python standard-library documentation still supports `json.dump()`
  and `json.load()` for UTF-8 text-file persistence, which fits the repo's local JSON
  state pattern without adding a dependency. [Source: https://docs.python.org/3/library/json.html]
- `pathlib.Path.mkdir(parents=True, exist_ok=True)` remains the standard way to create
  nested parent directories before writing review-state files. [Source:
  https://docs.python.org/3/library/pathlib.html]
- Keep the new regression coverage on `unittest` so the file works with the repo's
  existing root-run discovery command. [Source: https://docs.python.org/3/library/unittest.html]

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1-1-Produce-Inspectable-Document-Verification-Records]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-1-Review-Ready-Document-Quality-Gates]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md#4-2-Agentic-Verification-Before-Manual-Review]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements-Mapping]
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Format-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#Gap-Analysis-Results]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: _bmad-output/project-context.md#Critical-Dont-Miss-Rules]
- [Source: app/review_state.py]
- [Source: app/document_creation.py]
- [Source: app/reporting.py]
- [Source: main.py]
- [Source: https://docs.python.org/3/library/json.html]
- [Source: https://docs.python.org/3/library/pathlib.html]
- [Source: https://docs.python.org/3/library/unittest.html]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `create-story workflow`
- `python3 -m unittest tests.test_document_verification` (initial red phase: missing module)
- `python3 -m unittest tests.test_document_verification`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 -m flake8 app/document_verification.py tests/test_document_verification.py` (module unavailable in local environment)

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Regenerated Story `1.1` against the current `2026-05-21` epic and sprint planning
  artifacts instead of the older quality-data-contracts scope.
- Left `_bmad-output/implementation-artifacts/1-1-define-quality-data-contracts.md` in
  place as a historical artifact because older completed story files still reference it;
  this file is the active Story `1.1` artifact for the current sprint.
- Added `app/document_verification.py` with dedicated builders, enum validators,
  recoverable load validation, and versioned save/load helpers for
  `data/review/document_quality.json`.
- Added `tests/test_document_verification.py` to cover multi-artifact round-trips,
  malformed and missing state files, invalid nested entries, and distinct Markdown vs
  `.docx` artifact identity.
- Verified the new test module and the full repository `unittest` suite pass from the
  repository root.
- `flake8` is not installed in the local environment, so style validation was limited to
  keeping the new files compatible with the repo's configured line-length rules by
  inspection.

### File List

- `app/document_verification.py`
- `tests/test_document_verification.py`
- `_bmad-output/implementation-artifacts/1-1-produce-inspectable-document-verification-records.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Change Log

- 2026-05-21: Created the current Story `1.1` implementation guide for document
  verification record persistence and validation.
- 2026-05-21: Implemented document verification state builders/loaders/savers, added
  regression tests, and advanced Story `1.1` to review.
- 2026-05-22: Senior developer review completed with no blocking findings; story
  advanced to done.

## Senior Developer Review (AI)

- Outcome: approved
- Acceptance Criteria:
  - AC1 verified in [app/document_verification.py](/home/dicky/CampfireSongbookBuilder/app/document_verification.py:55) and [app/document_verification.py](/home/dicky/CampfireSongbookBuilder/app/document_verification.py:227) where records are built, validated, loaded, and saved with artifact identity, status, reasons, and timestamps.
  - AC2 verified in [app/document_verification.py](/home/dicky/CampfireSongbookBuilder/app/document_verification.py:311) and [tests/test_document_verification.py](/home/dicky/CampfireSongbookBuilder/tests/test_document_verification.py:25) where multiple Markdown and `.docx` artifacts are persisted as distinct entries.
- File List audit:
  - Claimed source files match the implemented review surface for this story.
  - Additional dirty-worktree files are unrelated legacy changes and were excluded from this review.
- Verification:
  - `python3 -m unittest tests.test_document_verification` passed during review.
  - Full-suite verification remains the passing developer-run baseline recorded above.
- Notes:
  - The spawned Codex review worker failed on an auth refresh error, so this review was executed inline against the same story contract to preserve correctness.
