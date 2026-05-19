# Story 5.2: Preserve Backward-Compatible Cache Reads

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an existing project user,
I want my current JSONL caches to remain usable,
so that upgrading the tool does not discard already fetched songs.

## Acceptance Criteria

1. Given existing lyrics and chords JSONL cache records with current fields, when upgraded generation or quality workflows read the caches, then records remain readable without migration and exact `artist`/`title` lookup behavior is preserved.
2. Given future cache fields are added, when older records are read, then missing new fields are handled by backward-compatible defaults or separate state files.
3. Given mixed cache files include legacy and augmented records, when the cache helpers read them, then load operations remain deterministic and inspectable.

## Tasks / Subtasks

- [ ] Keep JSONL cache reads backward compatible.
  - [ ] Preserve exact `artist`/`title` lookup behavior in the cache helpers.
  - [ ] Keep missing or additional fields from breaking cache reads.
  - [ ] Avoid migration requirements for existing cache files.
- [ ] Add focused regression coverage.
  - [ ] Cover loading cache lines with additional future fields.
  - [ ] Cover exact lookup behavior for existing song keys.
  - [ ] Cover legacy lines that remain readable alongside newer shapes.
- [ ] Verify from the repository root.
  - [ ] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Dev Notes

- This story hardens the existing JSONL cache helpers rather than replacing them.
- Keep the cache semantics append-safe and local-file based.
- Do not change song identity normalization; exact `artist` and `title` lookups remain the contract.

### Project Structure Notes

- Likely implementation file: `app/cache.py`
- New regression tests: `tests/test_cache.py`
- Cache files remain under `data/cache/*.jsonl`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5-2-Preserve-Backward-Compatible-Cache-Reads]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-5-Offline-Inspectable-Output-Pipeline]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture]
- [Source: _bmad-output/project-context.md#JSONL-cache-semantics]
- [Source: app/cache.py]
- [Source: tests/test_source_retry.py]

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- `python3 -m pytest tests/test_cache.py tests/test_reporting.py tests/test_document_creation.py tests/test_selection_state.py tests/test_generation_filtering.py`

### Completion Notes List

- Confirmed the JSONL cache helpers remain backward compatible with both legacy and augmented records.
- Added regression coverage for exact artist/title lookup plus mixed legacy and future-shaped cache lines.
- Kept the cache read helpers local, append-safe, and migration-free.

### File List

- `_bmad-output/implementation-artifacts/5-2-preserve-backward-compatible-cache-reads.md`
- `app/cache.py`
- `tests/test_cache.py`

## Change Log

- 2026-05-19: Created story scaffold for cache-read compatibility.
- 2026-05-19: Added cache compatibility regression coverage and marked the story done.
