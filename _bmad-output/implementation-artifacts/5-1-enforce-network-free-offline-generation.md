# Story 5.1: Enforce Network-Free Offline Generation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a camper generating a book away from internet access,
I want cache-based generation to avoid all network calls,
so that the tool works reliably from reviewed local data.

## Acceptance Criteria

1. Given the user runs `--generate-from-cache` or another offline generation path, when generation executes, then no source adapter or external metadata lookup is called, and missing or Questionable cached content is reported from local state.
2. Given required local cache or review files are absent, when offline generation runs, then the workflow reports missing local state clearly and it does not attempt live fetches as a fallback.
3. Given offline generation succeeds, when the report is written, then the output remains inspectable and local-only.

## Tasks / Subtasks

- [x] Keep offline generation isolated from live source fetching.
  - [x] Make Genius client initialization lazy so cache-only generation does not create source adapters unnecessarily.
  - [x] Preserve the existing cache-first generation path for the repo-root CLI.
  - [x] Keep `--generate-from-cache` from falling back to any live fetch path.
- [x] Preserve local-state reporting.
  - [x] Continue loading quality and review state from local files only.
  - [x] Surface missing cached content through the traceable report rather than hidden network retries.
- [x] Add focused regression coverage.
  - [x] Verify the offline generation branch does not initialize the Genius client.
  - [x] Verify the report path still runs and remains inspectable.
- [x] Verify from the repository root.
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- This story locks down the offline generation contract for the cache-only path.
- Keep the implementation local and inspectable. The existing JSONL caches, review state, and traceable report should be the only inputs for offline generation.
- Do not reintroduce source fetching in the cache-only branch as a convenience fallback.

### Project Structure Notes

- Likely implementation files: `main.py`, `app/document_creation.py`
- Possible reporting update: `app/reporting.py`
- New regression tests: `tests/test_reporting.py`
- Cache and review state remain local-file inputs only

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5-1-Enforce-Network-Free-Offline-Generation]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-5-Offline-Inspectable-Output-Pipeline]
- [Source: _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/prd.md#4-5-Offline-Generation]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture]
- [Source: _bmad-output/project-context.md#Application-Orchestration-Rules]
- [Source: _bmad-output/project-context.md#Testing-Rules]
- [Source: main.py]
- [Source: app/document_creation.py]
- [Source: app/reporting.py]
- [Source: tests/test_reporting.py]

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- `python3 -m unittest discover -s tests -p 'test_*.py'`

### Completion Notes List

- Made Genius client creation lazy so `--generate-from-cache` no longer instantiates a source adapter unless a live-fetch branch actually needs one.
- Added a regression test that confirms the offline generation branch does not initialize the Genius client.
- Kept the existing cache-only report generation path intact and fully local.

### File List

- `_bmad-output/implementation-artifacts/5-1-enforce-network-free-offline-generation.md`
- `main.py`
- `tests/test_reporting.py`

## Change Log

- 2026-05-19: Completed offline-generation network isolation and verification.

