# Story 1.1: Define Quality Data Contracts

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a songbook builder user,
I want the tool to represent songs, candidates, quality signals, and content hashes consistently,
so that future quality checks and reports describe the same song content without ambiguity.

## Acceptance Criteria

1. Given a song with artist, title, content type, source metadata, and content text, when
   candidate and quality-status records are created, then the records use `snake_case`
   fields, preserve exact `artist` and `title`, derive `song_key` as `Artist - Title`,
   and include a content hash in `sha256:<hex>` format.
2. Given invalid content types, quality values, review decision values, severity values,
   or source outcome values, when validation helpers are called, then invalid values are
   rejected with focused errors that name the field and value.
3. Given existing cache records with exact `artist` and `title` fields, when quality data
   contracts derive matching keys, then existing cache identity remains backward-compatible
   and no global title/artist normalization is applied.
4. Given optional source metadata is missing, when candidate records are created, then
   missing optional string metadata is represented as `None`/JSON `null`, not an empty
   string.
5. Given current architecture conventions, when this story is implemented, then it adds
   only shared data-contract helpers and focused tests; it does not wire quality filtering
   into fetching, cache persistence, review state files, or document generation.

## Tasks / Subtasks

- [x] Add shared content contract helpers in `app/content_models.py` (AC: 1, 2, 3, 4)
  - [x] Define constants for allowed `content_type`, `quality`, `decision`,
        `severity`, and `source outcome` values.
  - [x] Implement `derive_song_key(artist, title)` using exact input values and the
        display format `Artist - Title`; do not trim, lowercase, slugify, or otherwise
        normalize cache identity.
  - [x] Implement `compute_content_hash(content)` using UTF-8 text bytes and
        `hashlib.sha256(...).hexdigest()`, returning `sha256:<hex>`.
  - [x] Implement focused validation helpers that raise `ValueError` with the bad field
        and value when an enum-like contract value is invalid.
  - [x] Implement dictionary constructors for candidate, quality signal, quality status,
        and review decision records using `snake_case` keys and architecture field names.
- [x] Preserve current app boundaries and compatibility (AC: 3, 5)
  - [x] Keep the implementation dependency-free and in the existing flat `app/*.py`
        module layout.
  - [x] Do not change `main.py`, `app/cache.py`, existing JSONL cache field names, or
        existing sentinel values `"Lyrics not found."` / `"Chords not found."`.
  - [x] Do not create or write `data/review/*.json` in this story; persistence belongs
        to later review-state stories.
- [x] Add focused unit tests in `tests/test_content_models.py` (AC: 1, 2, 3, 4, 5)
  - [x] Cover exact `song_key` derivation, including inputs whose capitalization and
        spacing must be preserved.
  - [x] Cover deterministic `sha256:<64 hex chars>` content hashes for known text.
  - [x] Cover valid candidate, quality signal, quality status, and review decision
        constructor output shapes.
  - [x] Cover invalid content type, quality value, review decision, severity, and source
        outcome validation failures.
  - [x] Cover optional source metadata remaining `None`.
  - [x] Cover compatibility with existing cache-style records containing exact `artist`
        and `title` values.
- [x] Verify from the repository root (AC: 5)
  - [x] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.
  - [x] If available in the local environment, run the repo's style check; otherwise
        keep new lines compatible with `.flake8` `max-line-length = 100` by inspection.

### Review Findings

- [x] [Review][Patch] Validate nested quality-signal payloads before storing them [app/content_models.py:130]
- [x] [Review][Patch] Enforce `sha256:<hex>` for stored content hashes [app/content_models.py:126]

## Dev Notes

- Implement this as a pure helper module. No network calls, file writes, document
  rendering, or CLI behavior changes are in scope. [Source:
  _bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries]
- The project favors simple functions, flat modules, absolute `app.*` imports, and
  `unittest`; follow the existing style in `app/cache.py`, `app/text_cleaning.py`, and
  `tests/test_config.py`. [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- Current cache identity depends on exact `artist` and `title` equality and derived
  `"Artist - Title"` display keys. `app/cache.py` already uses exact fields for JSONL
  lookup and the same derived display key in `jsonl_load_all`; this story must not
  change that behavior. [Source: app/cache.py]
- Architecture requires JSON/JSONL field names in `snake_case`, content types `lyrics`
  and `chords`, quality values `clean`, `questionable`, and `missing`, review decisions
  `accept`, `reject`, and `override`, source outcomes `candidate`, `not_found`, and
  `error`, plus severity values `info`, `warning`, and `error`. [Source:
  _bmad-output/planning-artifacts/architecture.md#Format-Patterns]
- Missing optional string metadata should be represented as `None` in Python so it
  serializes as JSON `null` later; do not coerce optional source artist/title/error
  fields to empty strings. [Source: _bmad-output/planning-artifacts/architecture.md#Format-Patterns]
- Existing sentinel content values `"Lyrics not found."` and `"Chords not found."` stay
  recognized by later quality stories; this story should only define contracts and hash
  whatever content value it is given. [Source: _bmad-output/project-context.md#Critical-Dont-Miss-Rules]

### Suggested Record Shapes

Candidate fields:

```python
{
    "artist": artist,
    "title": title,
    "song_key": derive_song_key(artist, title),
    "content_type": content_type,
    "source": source,
    "content": content,
    "content_hash": compute_content_hash(content),
    "source_artist": source_artist,
    "source_title": source_title,
    "status": status,
    "error": error,
    "retrieved_at": retrieved_at,
}
```

Quality signal fields:

```python
{
    "code": code,
    "severity": severity,
    "message": message,
    "content_type": content_type,
}
```

Quality status fields:

```python
{
    "artist": artist,
    "title": title,
    "song_key": derive_song_key(artist, title),
    "content_type": content_type,
    "content_hash": content_hash,
    "quality": quality,
    "signals": signals,
    "assessed_at": assessed_at,
}
```

Review decision fields:

```python
{
    "song_key": song_key,
    "content_type": content_type,
    "content_hash": content_hash,
    "decision": decision,
    "reason": reason,
    "decided_at": decided_at,
}
```

### Latest Technical Notes

- Python 3.12 standard `hashlib` guarantees a `sha256()` constructor, and `hexdigest()`
  returns hexadecimal text suitable for non-binary exchange; use that rather than adding
  a dependency. [Source: https://docs.python.org/3.12/library/hashlib.html]
- Python `datetime` supports `datetime.isoformat()` for timestamp strings with timezone
  data when the datetime is timezone-aware. Constructors should accept a caller-supplied
  timestamp string or generate one through a small helper only if needed. [Source:
  https://docs.python.org/3.12/library/datetime.html]
- Keep tests on `unittest` discovery because that is the existing project standard and
  Python's supported standard-library test framework. [Source:
  https://docs.python.org/3.12/library/unittest.html]

### Project Structure Notes

- New implementation file: `app/content_models.py`.
- New test file: `tests/test_content_models.py`.
- No existing application files should need modification for this story unless the dev
  agent discovers an import/style issue that blocks tests; document any such change in
  the Dev Agent Record.
- Previous story context: none. This is the first implementation story in Epic 1.
- Git context at story creation: recent commits include `12da25a Automator upgrade`,
  `4afd01d Merge bug fixes into 2026 upgrade`, and `96f1f71 Add 2026 BMAD upgrade assets`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1-1-Define-Quality-Data-Contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Format-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: app/cache.py]
- [Source: tests/test_config.py]
- [Source: https://docs.python.org/3.12/library/hashlib.html]
- [Source: https://docs.python.org/3.12/library/datetime.html]
- [Source: https://docs.python.org/3.12/library/unittest.html]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `python3 -m unittest tests.test_content_models`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 -m unittest tests.test_content_models` after contract validation fix
- `python3 -m unittest discover -s tests -p 'test_*.py'` after contract validation fix

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created
- Added `app/content_models.py` with exact-key song contracts, SHA-256 content hashing,
  enum validation helpers, and constructors for candidate, quality signal, quality status,
  and review decision records.
- Added `tests/test_content_models.py` to cover exact `song_key` derivation, hash
  format, constructor output shapes, optional `None` metadata, and invalid-value
  rejection.
- Verified the full `unittest` suite passes from the repository root.
- Hardened nested quality-signal validation and strict `sha256:<hex>` enforcement for
  quality status and review decision hashes after code review.

### File List

- `app/content_models.py`
- `tests/test_content_models.py`

## Change Log

- 2026-05-19: Implemented the quality data contract helpers and regression tests for
  story 1.1.
- 2026-05-19: Addressed review findings for nested quality-signal validation and strict
  content-hash enforcement.
