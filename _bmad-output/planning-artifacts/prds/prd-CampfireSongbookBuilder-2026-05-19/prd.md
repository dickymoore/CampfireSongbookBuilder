---
title: CampfireSongbookBuilder Quality Upgrade
status: draft
created: 2026-05-19
updated: 2026-05-19
---

# PRD: CampfireSongbookBuilder Quality Upgrade

## 0. Document Purpose

This PRD defines the next product direction for CampfireSongbookBuilder: turning the existing CLI songbook builder into a more reliable, quality-aware tool for producing printable camping songbooks. It is written for the product owner, future AI agents, architecture workflow, and story-generation workflow. It builds on `_bmad-output/project-context.md` and generated docs in `docs/`; it does not repeat their technical architecture details.

The PRD is scoped as a brownfield quality upgrade. It should guide architecture and story creation without prescribing exact module names, cache schemas, or document-conversion libraries. Technical choices that affect compatibility, migration, or source-specific parsing belong in architecture or story artifacts.

## 1. Vision

CampfireSongbookBuilder should make it easy to prepare a trustworthy songbook before a camping trip. The user should be able to add songs, run the builder, review questionable content, select favourites or a named setlist, and print a book knowing it will not be full of broken tab, junk pages, missing chords, or unreadable formatting.

The current value is already clear: it can fetch, cache, and generate songbooks. The next step is quality. The product should become opinionated about what “good enough to print” means: complete songs, usable chords/tab, readable layout, sensible page count, and clear warnings when the source material is questionable.

The v1 upgrade should keep the existing CLI/file workflow. A UI is not a priority. The interface can remain friendly to AI agents and power users who are comfortable editing source files or running commands.

## 2. Target User

### 2.1 Primary Persona

Dicky, a musician/camper preparing a printed songbook before a trip. He wants practical, playable songs without spending hours manually cleaning bad tabs, removing junk pages, and checking whether fetched content is usable.

### 2.2 Secondary Persona

Public GitHub user who finds the project useful and wants to generate a personal campfire songbook from their own song list. They are comfortable with a CLI or file-based workflow but need clear guidance and trustworthy output.

### 2.3 Jobs To Be Done

- Prepare a high-quality printable songbook before a camping trip.
- Add songs with less manual cleanup and fewer failed fetches.
- Avoid printing broken, low-quality, duplicated, or junk-filled content.
- Build a book from favourites or a named selection rather than the entire source list.
- Work offline once the needed song data has been fetched and cached.
- Review questionable songs before deciding whether they belong in the final document.

### 2.4 Non-Users (v1)

- Users expecting a polished GUI.
- Users expecting a hosted web app.
- Users expecting guaranteed legal/licensed song content.
- Users expecting fully automatic perfect tab/chord quality with no review step.

### 2.5 Key User Journeys

- **UJ-1. Dicky prints a trusted camping songbook.** Dicky has a camping trip coming up and a source list of songs. He runs the builder against cached/fetched content. The system flags questionable songs and excludes them from the print-ready output unless he chooses otherwise. The generated book is readable, not bloated with junk pages, and ready to print.

- **UJ-2. Dicky adds songs without a cleanup slog.** Dicky adds several desired songs to the source list. The system fetches candidate lyrics/chords/tab, tries alternate sources when content is bad, and records quality status so he can review only the songs needing attention.

- **UJ-3. Dicky builds a favourites or trip-specific book.** Dicky marks songs as favourites and creates a named selection for a trip. The builder generates a book from that selection rather than the entire source library.

- **UJ-4. Dicky works offline after caching.** Dicky has already fetched and reviewed the needed songs. Later, without internet access, he can generate the selected songbook from local cached content.

## 3. Glossary

- **Song** — A requested musical item identified by artist and title.
- **Source List** — The input list of songs, currently represented by `data/src/CampfireSongs.csv`.
- **Cached Content** — Locally stored lyrics or chords/tab content in JSONL cache files.
- **Lyrics** — Words of the song, cleaned for songbook display.
- **Chords/Tab** — Playable chord or tab content for a song. The project currently uses “chords” broadly; this PRD uses **Chords/Tab** for quality requirements.
- **Quality Signal** — A detected indicator that content may be good, missing, broken, duplicated, too long, unreadable, from a low-confidence source, or otherwise unsuitable.
- **Questionable Song** — A Song whose current Cached Content fails one or more quality checks and requires review or exclusion.
- **Favourite** — A Song marked by the user as generally preferred.
- **Selection** — A named set of Songs used to generate a specific book, such as a trip setlist.
- **Printable Book** — The final generated songbook output intended for printing.
- **Review Decision** — A persisted user decision that accepts, rejects, or overrides a Quality Signal for a Song.
- **Source Attempt** — One attempt to fetch Lyrics or Chords/Tab from a configured source, including source name, outcome, and relevant failure reason.

## 4. Features

### 4.1 Song Quality Assessment

**Description:** The system assesses fetched and cached Lyrics and Chords/Tab before they enter a Printable Book. It identifies missing chords, bad tab, weird markup, duplicate junk, too-long content, low-confidence sources, unreadable formatting, suspected wrong songs, and related bad-content signals. Realizes UJ-1 and UJ-2.

**Functional Requirements:**

#### FR-1: Detect missing or unusable Chords/Tab

The system can identify Songs whose Chords/Tab are missing, empty, sentinel-only, or otherwise unusable.

**Consequences:**
- Songs with `"Chords not found."`, empty content, or non-string content are marked with a Quality Signal.
- Songs marked this way do not silently enter a default Printable Book.
- The generated quality report lists the Song, the failing content type, and the reason.

#### FR-2: Detect junk, markup, and unreadable content

The system can detect weird markup, email/header artifacts, duplicate junk, scraper residue, and unreadable formatting in Lyrics or Chords/Tab.

**Consequences:**
- Detected artifacts create one or more Quality Signals.
- Cleaning may remove known safe artifacts, but questionable content remains reviewable rather than silently accepted.
- Removed artifacts and retained warning signals are distinguishable in review output.

#### FR-3: Detect overlong or print-hostile content

The system can identify Lyrics or Chords/Tab likely to create excessive pages or unreadable print output.

**Consequences:**
- Songs exceeding configurable length/page heuristics are marked Questionable.
- The system can report why the Song is Questionable.
- Initial thresholds are configurable or isolated as constants so they can be tuned without rewriting scraper logic.

#### FR-4: Detect low-confidence candidates

The system can mark content as low-confidence when source, title/artist matching, or fetched content suggests it may be the wrong song.

**Consequences:**
- Low-confidence candidates are marked Questionable.
- The reason is preserved for review.
- Wrong-song detection starts with deterministic heuristics such as source match metadata, title/artist mismatch, empty result, or obvious unrelated content. Semantic verification is out of scope for MVP.

### 4.2 Source Retry and Review Workflow

**Description:** When fetched content is bad, the system tries another source before asking the user to decide. If no good source is found, it marks the Song as Questionable and makes that status available to document creation. Realizes UJ-1 and UJ-2.

**Functional Requirements:**

#### FR-5: Try alternate sources before finalizing bad content

The system can continue through configured lyric/chord sources when a candidate fails quality assessment.

**Consequences:**
- A bad candidate from one source does not prevent later sources from being attempted.
- Source attempts are logged or reportable for review.
- The retry flow avoids re-fetching sources that already produced acceptable cached content unless explicitly requested.

#### FR-6: Mark unresolved bad content as Questionable

The system can persist a Questionable status when all available sources fail to produce acceptable content.

**Consequences:**
- The status includes the quality reasons.
- The status is available during document creation.
- Questionable status can survive a later generate-from-cache run.

#### FR-7: Exclude Questionable Songs from generated books by default

The system can generate a Printable Book that excludes Questionable Songs unless the user explicitly includes them. `[ASSUMPTION: Default exclusion is preferred over default inclusion for print confidence.]`

**Consequences:**
- Generated output does not contain known bad-content pages by default.
- A report identifies excluded Songs and reasons.
- The user can explicitly include Questionable Songs for a one-off generation or through a persisted Review Decision.

### 4.3 Easier Song Addition

**Description:** The system reduces the pain of adding new songs by improving validation, fetch feedback, and review output around the existing file-based flow. A UI is not part of v1. Realizes UJ-2.

**Functional Requirements:**

#### FR-8: Validate Source List rows

The system can detect incomplete or malformed Source List rows before fetching.

**Consequences:**
- Missing artist/title rows are reported.
- Rows marked `Skip` continue to be excluded from processing.

#### FR-9: Provide add-song feedback

The system can show or write a summary of what happened for newly added Songs.

**Consequences:**
- Summary includes found/clean/Questionable/missing status.
- Summary points the user to Songs needing review.

#### FR-10: Preserve agent-friendly operation

The system remains operable through files and CLI commands so AI agents can help add, review, and regenerate Songs.

**Consequences:**
- No v1 requirement depends on a GUI.
- Inputs and outputs remain inspectable as files.
- Machine-readable review/report output is available for automation, even if a human-readable summary is also printed.

### 4.4 Favourites and Selections

**Description:** The system supports both broad favourites and named selections/setlists/books so users can generate a book for a specific trip or purpose. Realizes UJ-3.

**Functional Requirements:**

#### FR-11: Mark Songs as Favourites

The user can mark Songs as Favourite.

**Consequences:**
- Favourite status is persisted in an inspectable format.
- The builder can generate output using only Favourite Songs.
- Favourite status is independent from quality status; a Favourite Song may still be excluded when Questionable unless explicitly included.

#### FR-12: Create named Selections

The user can define named Selections, each containing a chosen set of Songs.

**Consequences:**
- The builder can generate a Printable Book from a named Selection.
- A Song can appear in multiple Selections.
- Missing Songs or malformed Selection entries are reported before generation proceeds.

#### FR-13: Combine quality filtering with Selections

The system applies quality filtering when generating from Favourites or a Selection.

**Consequences:**
- Questionable Songs are excluded by default unless explicitly included.
- Excluded items are reported with reasons.

### 4.5 Offline Generation

**Description:** Once content is cached and reviewed, the user can generate books without internet access. Realizes UJ-4.

**Functional Requirements:**

#### FR-14: Generate from cache without network

The system can generate selected output from Cached Content without making external requests.

**Consequences:**
- Offline mode does not attempt live fetches.
- Missing or Questionable cached content is reported.

#### FR-15: Preserve local cache compatibility

The system preserves existing cache data or provides migration/backward-compatible reading when cache shape changes.

**Consequences:**
- Existing JSONL caches remain usable after upgrade or are migrated intentionally.
- Cache schema changes are documented.
- Exact `artist` and `title` cache-key behavior remains backward-compatible unless a migration explicitly preserves lookups for old records.

### 4.6 Output Pipeline and Printable Quality

**Description:** The system should move toward a more inspectable output pipeline: Markdown first, then `.docx`, then PDF. The v1 priority is better print confidence, with intelligent layouts deferred unless needed for basic quality. Realizes UJ-1.

**Functional Requirements:**

#### FR-16: Produce Markdown songbook output

The system can produce a Markdown representation of the generated book before `.docx` generation.

**Consequences:**
- Users and agents can inspect generated content before document conversion.
- Markdown output reflects quality filtering decisions.
- Markdown is treated as an inspectable intermediate artifact in MVP; it may also be offered as a user-visible export.

#### FR-17: Produce `.docx` output from accepted content

The system continues to produce `.docx` output for printing/editing.

**Consequences:**
- Existing document generation remains available.
- `.docx` output excludes Questionable Songs by default.

#### FR-18: Support PDF output after `.docx`

The system can produce or enable PDF output after `.docx`.

**Consequences:**
- PDF generation is documented with local dependency requirements.
- Failure to generate PDF does not destroy Markdown or `.docx` outputs.
- MVP may rely on an installed local converter. Pure Python PDF generation is not required.

#### FR-19: Improve basic printable layout quality

The system can avoid obvious print-hostile output, such as pages full of bad tab, unreadable wrapping, or excessive song length.

**Consequences:**
- Basic layout checks run before final output.
- Intelligent layout optimization is explicitly deferred beyond v1 unless required for basic readability.

## 5. Non-Functional Requirements

### NFR-1: Preserve existing CLI contract

Existing commands remain behavior-compatible from the repository root, especially `python3 main.py`, `--cache-only`, `--generate-from-cache`, `--lyrics-only`, `--chords-only`, `--get-song-info`, and `--test-api`.

### NFR-2: Preserve cache-first and offline behavior

Generation from cache does not perform live network requests. Source retry work must not increase external requests when cached acceptable content already exists.

### NFR-3: Keep source failures isolated

A failure from one lyric or chord source does not crash the full run when another configured source or cached value can still be used.

### NFR-4: Keep review state inspectable

Quality status, Review Decisions, Favourites, and Selections are stored in simple file formats that humans and AI agents can inspect and edit.

### NFR-5: Keep tests independent from external services

Regression tests for quality assessment, cache handling, source fallback decisions, and document-generation decisions do not depend on live websites, Genius credentials, or generated `.docx` binary comparison.

### NFR-6: Maintain implementation simplicity

The v1 upgrade should preserve the single-process CLI shape and flat helper-module style unless architecture identifies a specific compatibility or maintainability reason to change it.

## 6. Non-Goals

- Build a GUI in v1.
- Build a hosted service in v1.
- Guarantee perfect chord/tab accuracy.
- Solve music licensing or public content distribution rights.
- Replace all source-specific scrapers with a full plugin marketplace in v1.
- Build advanced intelligent layout optimization in v1 beyond basic print-quality checks.
- Support collaborative multi-user libraries in v1.
- Guarantee legal rights to redistribute generated song content.

## 7. MVP Scope

### 7.1 In Scope

- Quality assessment for Lyrics and Chords/Tab.
- Alternate-source retry before marking content bad.
- Questionable Song status and reasons.
- Ability to exclude Questionable Songs from generated output.
- Easier file/CLI-based song addition feedback.
- Favourite Songs.
- Named Selections.
- Offline generation from cache.
- Markdown output before `.docx`.
- Continued `.docx` generation.
- Initial PDF path, if feasible without destabilizing the document pipeline.
- Basic machine-readable quality/review reports.
- Regression tests for the upgraded quality and filtering paths.

### 7.2 Out of Scope for MVP

- GUI.
- Hosted web app.
- Advanced automatic semantic wrong-song verification.
- Full intelligent layout engine.
- Cloud sync.
- User accounts.
- Full public package/distribution polish.

## 8. Acceptance Criteria

### AC-1: Print-ready generation excludes known bad content

Given a source list containing at least one clean Song and at least one Questionable Song, when the user generates a default Printable Book, then the clean Song appears, the Questionable Song is excluded, and the report names the exclusion reason.

### AC-2: Alternate-source retry happens before final Questionable status

Given a source returns unusable Chords/Tab and a later configured source returns acceptable Chords/Tab, when fetching the Song, then the acceptable candidate is cached or selected and the failed Source Attempt is reportable.

### AC-3: Offline generation makes no network requests

Given reviewed cached content exists, when the user runs generation from cache or offline mode, then the system uses local data only and reports missing or Questionable cached content without attempting live fetches.

### AC-4: Favourites and Selections respect quality filtering

Given a named Selection contains clean and Questionable Songs, when the user generates from that Selection, then quality filtering still applies by default and the report identifies any excluded Songs.

### AC-5: Markdown, `.docx`, and PDF path preserve artifacts

Given accepted content exists, when the output pipeline runs, then Markdown is produced before `.docx`; `.docx` remains available; and any PDF conversion failure is reported without deleting the Markdown or `.docx` artifacts.

## 9. Success Metrics

**Primary**

- **SM-1:** Trip readiness confidence — before a camping trip, the user can generate and print a selected book without manually removing pages of bad tab. Target: one default generation run produces a report and a printable artifact with zero known Questionable Songs included unless explicitly overridden. Validates FR-1 through FR-7 and FR-13.
- **SM-2:** Song addition pain reduction — adding a batch of new Songs produces a clear found/clean/Questionable/missing summary and requires review only for flagged items. Target: every newly added Song receives one of those statuses in the summary. Validates FR-8 through FR-10.
- **SM-3:** Selection usefulness — the user can generate a book from Favourites or a named Selection. Target: at least one Favourite-only run and one named-Selection run work from local files. Validates FR-11 through FR-13.

**Secondary**

- **SM-4:** Offline reliability — after content is cached, generation works without external network access. Validates FR-14 and FR-15.
- **SM-5:** Output inspectability — Markdown output makes bad content easier to detect before `.docx`/PDF conversion. Validates FR-16 through FR-18.

**Counter-metrics**

- **SM-C1:** Do not optimize for maximum number of included songs if quality drops. Counterbalances SM-1 and SM-3.
- **SM-C2:** Do not increase live external requests unnecessarily. Counterbalances source retry behavior in FR-5.
- **SM-C3:** Do not make the workflow harder for AI agents or CLI users by requiring a GUI. Counterbalances future UI temptation.

## 10. Constraints and Guardrails

- Preserve repo-root CLI operation: `python3 main.py ...`.
- Preserve JSONL cache compatibility or provide an intentional migration.
- Keep private config and generated outputs out of version control.
- Avoid unit tests that depend on live external sites or Genius credentials.
- Treat source failures as recoverable where possible.
- Preserve sentinel compatibility for `"Lyrics not found."` and `"Chords not found."` unless all affected readers, reports, and tests are updated together.

## 11. Architecture and Story Handoff Notes

- Architecture should decide whether quality status lives in cache records, a separate review file, or a hybrid, while preserving backward-compatible reads.
- Architecture should choose the simplest inspectable storage shape for Favourites, Selections, and Review Decisions.
- Story creation should split quality detection, retry behavior, review persistence, generation filtering, and output pipeline changes into separate stories where practical.
- Story creation should include regression tests for each changed cache, fetch, filtering, or generation behavior.
- PDF support should be implemented behind an optional dependency or clearly documented local prerequisite so it does not destabilize Markdown or `.docx` generation.

## 12. Open Questions

1. What exact file format should persist Favourites and Selections: CSV columns, JSON/YAML files, or another simple inspectable format?
2. Should Questionable status live inside cache records, a separate review file, or both?
3. What are the initial quality thresholds for “too long,” “too much junk,” and “low confidence”?
4. Should explicit Review Decisions override quality filtering globally, per Selection, or per generation run?
5. What is the first acceptable PDF generation mechanism?
6. Should Markdown become the canonical intermediate representation after MVP proves the pipeline?

## 13. Assumptions Index

- §4.2 FR-7 — Default exclusion of Questionable Songs is preferred over default inclusion for print confidence.
