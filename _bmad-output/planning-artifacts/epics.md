---
stepsCompleted: [1, 2, 3, 4]
workflowType: 'epics-and-stories'
status: 'complete'
completedAt: '2026-05-19'
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/addendum.md
  - _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/validation-report.md
  - _bmad-output/planning-artifacts/research/technical-campfiresongbookbuilder-quality-review-architecture-and-content-quality-research-2026-05-19.md
---

# CampfireSongbookBuilder - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for CampfireSongbookBuilder, decomposing the requirements from the PRD, supporting PRD addendum and validation report, technical research, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Detect Songs whose Chords/Tab are missing, empty, sentinel-only, non-string, or otherwise unusable, and mark them with a Quality Signal rather than silently allowing them into default generated books.

FR2: Detect weird markup, email/header artifacts, duplicate junk, scraper residue, and unreadable formatting in Lyrics or Chords/Tab, distinguishing between safely removed artifacts and retained warning signals.

FR3: Detect Lyrics or Chords/Tab likely to create excessive pages or unreadable print output, using configurable or isolated thresholds for length/page heuristics.

FR4: Mark content as low-confidence when source, title/artist matching, or fetched content suggests it may be the wrong song, starting with deterministic heuristics.

FR5: Continue through configured lyric/chord sources when a candidate fails quality assessment, record/report source attempts, and avoid refetching already acceptable cached content unless explicitly requested.

FR6: Persist a Questionable status with quality reasons when all available sources fail to produce acceptable content, and make that status available to later cache-based generation.

FR7: Exclude Questionable Songs from default generated books unless the user explicitly includes them for a one-off generation or through a persisted Review Decision.

FR8: Validate Source List rows before fetching, reporting missing artist/title rows while preserving `Skip` filtering behavior.

FR9: Provide add-song feedback summarizing found, clean, Questionable, and missing statuses and pointing the user to Songs needing review.

FR10: Preserve agent-friendly operation through files and CLI commands, with machine-readable review/report output available for automation.

FR11: Persist Favourite Song status in an inspectable format and support generation from Favourite Songs while still applying quality filtering.

FR12: Support named Selections containing chosen Songs, allow a Song to appear in multiple Selections, and report missing or malformed Selection entries before generation.

FR13: Apply quality filtering when generating from Favourites or named Selections, excluding Questionable Songs by default and reporting reasons.

FR14: Generate selected output from cached content without making external network requests, reporting missing or Questionable cached content.

FR15: Preserve existing JSONL cache data and exact `artist`/`title` cache-key behavior, or provide intentional backward-compatible migration if cache shape changes.

FR16: Produce a Markdown representation of generated books before `.docx` generation, reflecting quality filtering decisions and supporting human/agent inspection.

FR17: Continue producing `.docx` output for accepted content, excluding Questionable Songs by default.

FR18: Support or enable PDF output after `.docx`, with documented local dependency requirements and recoverable failure that does not delete Markdown or `.docx` artifacts.

FR19: Improve basic printable layout quality by avoiding obvious print-hostile output such as bad tab pages, unreadable wrapping, or excessive song length.

### NonFunctional Requirements

NFR1: Preserve the existing repo-root CLI contract, including `python3 main.py`, `--cache-only`, `--generate-from-cache`, `--lyrics-only`, `--chords-only`, `--get-song-info`, and `--test-api`.

NFR2: Preserve cache-first and offline behavior; generation from cache must not perform live network requests, and source retry must not increase external requests when cached acceptable content already exists.

NFR3: Keep source failures isolated so one lyric or chord source failure does not crash the full run when another configured source or cached value can still be used.

NFR4: Keep review state inspectable by storing Quality Status, Review Decisions, Favourites, Selections, and reports in simple local file formats humans and AI agents can inspect and edit.

NFR5: Keep tests independent from external services, Genius credentials, local private config, local cache contents, and generated `.docx` binary comparison.

NFR6: Maintain implementation simplicity by preserving the single-process CLI shape and flat helper-module style unless a future architecture decision justifies changing it.

### Additional Requirements

- Preserve the existing brownfield Python CLI scaffold; do not introduce a new starter template, GUI framework, web server, database, or service layer for MVP.
- Treat Python 3.12 as the verified development runtime for the upgrade, and reconcile existing Python 3.8+ documentation because Python 3.8 is end-of-life.
- Keep `main.py` as thin CLI orchestration; scraper logic, cache mechanics, quality assessment, review state, filtering, reporting, and document rendering belong in helper modules under `app/`.
- Preserve absolute `app.*` imports and repo-root execution.
- Add shared local data contracts for Candidate, Quality Signal, Quality Status, Review Decision, Source Attempt, Favourite, and Selection.
- Normalize source outputs into Candidate records before quality assessment.
- Store raw fetched content in existing JSONL caches; store current quality status and review decisions separately in JSON files under `data/review/`.
- Store source attempts as append-only JSONL under `data/review/source_attempts.jsonl`.
- Store favourites and named selections as JSON files under `data/selections/`.
- Use exact existing `artist` and `title` fields for cache identity; derived `song_key` values use `Artist - Title`.
- Do not globally normalize song titles/artists for cache lookup; normalized variants may only be computed for matching.
- Bind Quality Status and Review Decisions to content hashes using `sha256:<hex>` format to prevent stale approvals after refetch.
- Use data field names in `snake_case`; content type values are `lyrics` and `chords`; quality values are `clean`, `questionable`, and `missing`; review decisions are `accept`, `reject`, and `override`.
- Treat fetched content as untrusted text; clean or escape source content before Markdown or `.docx` rendering and never write API tokens to generated artifacts or reports.
- Keep external metadata enrichment, including MusicBrainz and RapidFuzz-assisted matching, optional and deferred unless deterministic matching proves insufficient.
- If MusicBrainz is added later, use a meaningful User-Agent and respect its documented rate-limit expectations; it must not run during offline generation.
- Generate human-readable and machine-readable reports for included, excluded, missing, Questionable, and explicitly overridden songs.
- Keep Markdown and `.docx` artifacts when optional PDF conversion fails.
- Keep tests under `tests/test_*.py` using `unittest`, `tempfile`, and `unittest.mock`.
- Add focused regression tests for cache compatibility, quality assessment, review-state loading, selection loading, source fallback decisions, filtering, Markdown output, and offline generation.
- Avoid new dependencies for MVP unless a story-specific decision proves they remove more risk than they add.
- Optional future work includes CI, RapidFuzz, jsonschema, packaging modernization, and concrete PDF tooling after the core quality pipeline is stable.

### UX Design Requirements

No UX Design Specification was found or required for v1. The PRD and Architecture explicitly exclude a GUI for MVP. User-facing inspection requirements are covered through CLI summaries, local reports, and Markdown output.

### FR Coverage Map

FR1: Epic 1 - detect missing or unusable Chords/Tab
FR2: Epic 1 - detect junk, markup, duplicate, and unreadable content
FR3: Epic 1 - detect overlong or print-hostile content
FR4: Epic 1 - detect low-confidence candidates
FR5: Epic 2 - retry alternate sources before finalizing bad content
FR6: Epic 2 - persist Questionable status and reasons
FR7: Epic 2 - exclude Questionable songs by default with override path
FR8: Epic 3 - validate source-list rows
FR9: Epic 3 - provide add-song feedback
FR10: Epic 3 - preserve agent-friendly file/CLI operation
FR11: Epic 4 - mark songs as favourites
FR12: Epic 4 - create named selections
FR13: Epic 4 - combine quality filtering with selections
FR14: Epic 5 - generate from cache without network
FR15: Epic 5 - preserve local cache compatibility
FR16: Epic 5 - produce Markdown songbook output
FR17: Epic 5 - produce `.docx` from accepted content
FR18: Epic 5 - support PDF output after `.docx`
FR19: Epic 5 - improve basic printable layout quality

## Epic List

### Epic 1: Trustworthy Content Assessment Foundation
Users can run the tool and get structured quality signals for cached/fetched lyrics and chords, so bad or missing content becomes visible before printing.
**FRs covered:** FR1, FR2, FR3, FR4

### Epic 2: Source Retry, Review State, and Traceability
Users can trust that the tool tries better sources before marking content Questionable, persists review status, and explains source/quality decisions.
**FRs covered:** FR5, FR6, FR7

### Epic 3: Better Song Addition Feedback
Users can add songs through the existing file/CLI workflow and get clear feedback about malformed rows, fetched content quality, missing items, and review needs.
**FRs covered:** FR8, FR9, FR10

### Epic 4: Favourites, Selections, and Quality-Aware Book Building
Users can build books from favourites or named selections while still excluding Questionable songs by default.
**FRs covered:** FR11, FR12, FR13

### Epic 5: Offline, Inspectable Output Pipeline
Users can generate a print-ready book from local reviewed cache content, inspect Markdown before `.docx`, preserve `.docx`, and optionally produce PDF without losing earlier artifacts.
**FRs covered:** FR14, FR15, FR16, FR17, FR18, FR19

## Epic 1: Trustworthy Content Assessment Foundation

Users can run the tool and get structured quality signals for cached/fetched lyrics and chords, so bad or missing content becomes visible before printing.

### Story 1.1: Define Quality Data Contracts

As a songbook builder user,
I want the tool to represent songs, candidates, quality signals, and content hashes consistently,
So that future quality checks and reports describe the same song content without ambiguity.

**Acceptance Criteria:**

**Given** a song with artist, title, content type, source metadata, and content text
**When** the application creates candidate and quality-status records
**Then** the records use `snake_case` fields, preserve exact `artist` and `title`, derive `song_key` as `Artist - Title`, and include a `sha256:<hex>` content hash
**And** invalid content types, quality values, or review decision values are rejected or reported by focused validation helpers.

**Given** existing cache records with exact `artist` and `title` fields
**When** quality data contracts derive matching keys
**Then** existing cache identity remains backward-compatible and no global title/artist normalization is applied.

### Story 1.2: Detect Missing or Unusable Lyrics and Chords

As a musician preparing a songbook,
I want missing or unusable lyrics/chords to be flagged automatically,
So that empty pages or "not found" content do not silently reach a print-ready book.

**Acceptance Criteria:**

**Given** lyrics or chords content that is empty, `None`, non-string, `"Lyrics not found."`, or `"Chords not found."`
**When** quality assessment runs
**Then** the result is marked `missing` or `questionable` with a structured Quality Signal
**And** the signal includes the affected `content_type`, a stable code, a severity, and a human-readable message.

**Given** valid non-empty lyrics or chords content
**When** the missing-content checks run
**Then** no missing-content signal is emitted.

### Story 1.3: Detect Junk, Markup, and Duplicate Content

As a songbook builder user,
I want obvious scraper residue, duplicate junk, and unreadable markup flagged,
So that bad source material is reviewable before it pollutes the songbook.

**Acceptance Criteria:**

**Given** lyrics or chords containing known junk patterns such as HTML residue, email/header artifacts, repeated identical blocks, or excessive bracket noise
**When** quality assessment runs
**Then** the result contains one or more warning or error Quality Signals explaining the issue
**And** safe cleanup remains distinguishable from retained warning signals in the output status.

**Given** ordinary lyrics or chord text without detected junk patterns
**When** the junk and duplication checks run
**Then** no junk-related signal is emitted.

### Story 1.4: Detect Print-Hostile and Low-Confidence Content

As a camper printing a songbook,
I want overlong, unreadable, or likely-wrong song content flagged,
So that I can avoid printing pages that are impractical or unrelated to the requested song.

**Acceptance Criteria:**

**Given** lyrics or chords exceeding initial configured or isolated line/character thresholds
**When** quality assessment runs
**Then** the content receives a print-hostile Quality Signal
**And** the threshold values are centralized so they can be tuned without editing scraper logic.

**Given** a candidate whose source title or artist differs materially from the requested title or artist
**When** deterministic confidence checks run
**Then** the content receives a low-confidence Quality Signal
**And** optional fuzzy matching or MusicBrainz enrichment is not required for this story.

### Story 1.5: Persist Current Quality Status for Cached Content

As a songbook builder user,
I want quality results saved in a local status file,
So that later generation runs can reuse quality decisions without re-fetching or re-assessing everything manually.

**Acceptance Criteria:**

**Given** assessed cached lyrics or chords
**When** quality status is saved
**Then** `data/review/quality_status.json` is created if needed and stores current status by song/content identity
**And** parent directories are created automatically.

**Given** malformed or missing quality status files
**When** the application loads quality status
**Then** it reports recoverable validation errors with file path, field, and reason
**And** absent files are treated as empty state where appropriate.

## Epic 2: Source Retry, Review State, and Traceability

Users can trust that the tool tries better sources before marking content Questionable, persists review status, and explains source/quality decisions.

### Story 2.1: Record Source Attempts During Fetching

As a songbook builder user,
I want each source lookup attempt recorded,
So that I can understand where lyrics or chords came from and why a source failed.

**Acceptance Criteria:**

**Given** an online fetch/cache workflow attempts lyrics or chord sources
**When** a source returns a candidate, not-found result, or error
**Then** a source attempt record is appended to `data/review/source_attempts.jsonl`
**And** the record includes song identity, content type, source name, status, optional error, and retrieval timestamp.

**Given** a source failure occurs while later fallback sources remain
**When** fetching continues
**Then** the failure is logged/reported as recoverable and does not crash the full run.

### Story 2.2: Retry Alternate Sources Before Final Questionable Status

As a musician adding songs,
I want the tool to try alternate sources when one source returns bad content,
So that I get better lyrics or chords without manually chasing websites.

**Acceptance Criteria:**

**Given** a configured source returns content that fails quality assessment
**When** additional configured sources remain available
**Then** the workflow attempts the next source before finalizing the content as Questionable
**And** all failed and successful attempts are reportable.

**Given** acceptable cached content already exists
**When** the fetch workflow runs without an explicit refresh request
**Then** the workflow does not perform unnecessary live source requests for that content.

### Story 2.3: Persist Review Decisions with Content Hashes

As a songbook builder user,
I want my accept/reject/override decisions saved against the exact reviewed content,
So that a stale approval is not silently reused after content changes.

**Acceptance Criteria:**

**Given** a user or agent records a review decision for a song/content type
**When** the decision is saved
**Then** `data/review/review_decisions.json` stores `song_key`, `content_type`, `content_hash`, `decision`, optional reason, and `decided_at`
**And** valid decisions are limited to `accept`, `reject`, and `override`.

**Given** cached content changes after a decision was saved
**When** review decisions are applied
**Then** decisions whose content hash no longer matches are ignored or reported as stale
**And** stale decisions do not allow Questionable content into default output.

### Story 2.4: Apply Questionable Exclusion and Override Rules

As a camper preparing a print-ready book,
I want Questionable songs excluded by default with an explicit override path,
So that known bad content does not reach the printed book unless I deliberately accept it.

**Acceptance Criteria:**

**Given** a song has error-severity quality signals and no matching accept/override decision
**When** generation filtering evaluates the song
**Then** the song is excluded by default
**And** the exclusion reason is available to reports.

**Given** a song has a matching current `accept` or `override` decision
**When** generation filtering evaluates the song
**Then** the song can be included according to the decision
**And** the report identifies that inclusion came from an explicit review decision.

### Story 2.5: Produce Traceable Quality Reports

As a songbook builder user,
I want a report explaining included, excluded, missing, and overridden songs,
So that I can quickly review what needs attention before printing.

**Acceptance Criteria:**

**Given** a generation or quality run evaluates songs
**When** reporting runs
**Then** a machine-readable report is written under `data/review/reports/`
**And** the report includes included songs, excluded songs, missing content, Questionable signals, source-attempt references where available, and explicit review decisions.

**Given** report output is generated
**When** the CLI completes
**Then** the user sees a concise summary pointing to the report file
**And** no API tokens or private config values are included.

## Epic 3: Better Song Addition Feedback

Users can add songs through the existing file/CLI workflow and get clear feedback about malformed rows, fetched content quality, missing items, and review needs.

### Story 3.1: Validate Source List Rows Before Fetching

As a user editing the song CSV,
I want malformed song rows reported before fetching,
So that missing artist/title data does not become confusing cache or quality output.

**Acceptance Criteria:**

**Given** `data/src/CampfireSongs.csv` contains rows with missing artist or title values
**When** the source list is loaded for fetch or generation workflows
**Then** the invalid rows are reported with row context
**And** valid rows still proceed where safe.

**Given** rows are marked with `Skip`
**When** the source list is loaded
**Then** existing skip-filtering behavior is preserved.

### Story 3.2: Summarize Newly Added Song Outcomes

As a musician adding a batch of songs,
I want a clear summary of which songs are clean, missing, or Questionable,
So that I only spend time reviewing songs that need attention.

**Acceptance Criteria:**

**Given** a fetch/cache workflow processes songs
**When** the run completes
**Then** the CLI or report summarizes each processed song as found/clean, Questionable, missing, or invalid input
**And** the summary points to review reports for details.

**Given** newly added songs produce missing or Questionable content
**When** feedback is generated
**Then** those songs are grouped separately from clean songs
**And** each item includes the reason or top quality signal.

### Story 3.3: Keep File and CLI Workflows Agent-Friendly

As a CLI-oriented user,
I want all review and feedback artifacts to be inspectable files,
So that I or an AI agent can review, edit, and regenerate without a GUI.

**Acceptance Criteria:**

**Given** quality, review, selection, or report state is produced
**When** the state is written
**Then** it uses JSON or JSONL in the architecture-approved locations
**And** no workflow requires a GUI or hosted service.

**Given** an AI agent needs to inspect song status
**When** it reads local artifacts
**Then** machine-readable report and review files contain enough structured data to identify next review actions.

## Epic 4: Favourites, Selections, and Quality-Aware Book Building

Users can build books from favourites or named selections while still excluding Questionable songs by default.

### Story 4.1: Load and Validate Favourite Songs

As a camper building a repeat-use songbook,
I want to mark favourite songs in an inspectable local file,
So that I can generate a focused book without editing the master CSV each time.

**Acceptance Criteria:**

**Given** `data/selections/favourites.json` contains favourite song entries
**When** favourites are loaded
**Then** valid entries are matched by exact artist/title identity or derived `song_key`
**And** malformed entries are reported with file path, field, and reason.

**Given** a favourite song is Questionable
**When** favourite-only generation is evaluated
**Then** the song is still subject to default quality exclusion unless explicitly accepted or overridden.

### Story 4.2: Load and Validate Named Selections

As a musician preparing for a specific trip,
I want named selections of songs stored locally,
So that I can generate trip-specific books from the same song library.

**Acceptance Criteria:**

**Given** `data/selections/*.json` contains named selection files
**When** a named selection is loaded
**Then** valid song entries are returned in selection order
**And** missing songs or malformed entries are reported before generation proceeds.

**Given** a song appears in multiple selections
**When** each selection is loaded
**Then** the song is valid in each selection without duplicating raw cache records.

### Story 4.3: Generate Quality-Filtered Favourite and Selection Books

As a camper printing a selected book,
I want favourites and named selections to use the same quality rules as default generation,
So that focused books remain trustworthy.

**Acceptance Criteria:**

**Given** a favourite-only or named-selection generation request includes clean and Questionable songs
**When** generation filtering runs
**Then** clean accepted songs are included and Questionable songs are excluded by default
**And** the report lists excluded selected songs and reasons.

**Given** selected songs have matching current review overrides
**When** generation filtering runs
**Then** overridden songs can be included
**And** the report identifies the override.

### Story 4.4: Report Selection Completeness Before Output

As a songbook builder user,
I want selection problems reported before files are generated,
So that I can fix missing or malformed selection entries without inspecting a broken book.

**Acceptance Criteria:**

**Given** a selection references missing songs, malformed entries, or unavailable content
**When** the selection is prepared for output
**Then** the workflow reports those issues before rendering Markdown or `.docx`
**And** recoverable issues are included in the machine-readable report.

**Given** all selected songs are valid and accepted
**When** generation begins
**Then** no selection-error report blocks output.

## Epic 5: Offline, Inspectable Output Pipeline

Users can generate a print-ready book from local reviewed cache content, inspect Markdown before `.docx`, preserve `.docx`, and optionally produce PDF without losing earlier artifacts.

### Story 5.1: Enforce Network-Free Offline Generation

As a camper generating a book away from internet access,
I want cache-based generation to avoid all network calls,
So that the tool works reliably from reviewed local data.

**Acceptance Criteria:**

**Given** the user runs `--generate-from-cache` or an offline generation path
**When** generation executes
**Then** no source adapter or external metadata lookup is called
**And** missing or Questionable cached content is reported from local state.

**Given** required local cache or review files are absent
**When** offline generation runs
**Then** the workflow reports missing local state clearly
**And** it does not attempt live fetches as a fallback.

### Story 5.2: Preserve Backward-Compatible Cache Reads

As an existing project user,
I want my current JSONL caches to remain usable,
So that upgrading the tool does not discard already fetched songs.

**Acceptance Criteria:**

**Given** existing lyrics and chords JSONL cache records with current fields
**When** upgraded generation or quality workflows read the caches
**Then** records remain readable without migration
**And** exact `artist`/`title` lookup behavior is preserved.

**Given** future cache fields are added
**When** older records are read
**Then** missing new fields are handled by backward-compatible defaults or separate state files.

### Story 5.3: Render Accepted Content to Markdown

As a songbook builder user,
I want a Markdown songbook generated before `.docx`,
So that I or an AI agent can inspect the exact accepted content before document conversion.

**Acceptance Criteria:**

**Given** generation filtering produces accepted songs
**When** Markdown rendering runs
**Then** a `.md` songbook is written under `data/output/`
**And** it includes only accepted content according to quality and review decisions.

**Given** songs were excluded from the output
**When** Markdown output is produced
**Then** excluded content is not included in the book body
**And** exclusions remain available in the report.

### Story 5.4: Generate `.docx` from Accepted Content

As a camper preparing a printable book,
I want `.docx` generation to use the accepted content set,
So that the Word document does not contain known bad songs by default.

**Acceptance Criteria:**

**Given** accepted songs and Markdown/report artifacts exist for a generation run
**When** `.docx` generation runs
**Then** the Word document is generated from accepted content only
**And** existing document formatting responsibilities remain inside document-generation helpers.

**Given** `python-docx` is unavailable in the local environment
**When** `.docx` generation is requested
**Then** the workflow reports the missing dependency clearly
**And** existing Markdown/report artifacts are preserved.

### Story 5.5: Add Recoverable Optional PDF Conversion

As a songbook builder user,
I want an optional PDF output path after Markdown and `.docx`,
So that I can print or share a final artifact when local tooling supports it.

**Acceptance Criteria:**

**Given** Markdown and `.docx` artifacts have been produced
**When** optional PDF conversion is requested and the converter is available
**Then** a PDF is written under `data/output/`
**And** the report records the PDF artifact path.

**Given** PDF conversion is requested but the converter is missing or fails
**When** the failure occurs
**Then** the workflow reports the failure as recoverable
**And** Markdown and `.docx` artifacts are not deleted or modified.

### Story 5.6: Apply Basic Printable Layout Quality Checks

As a musician printing a campfire songbook,
I want obvious layout problems flagged before final output,
So that the book avoids unreadable tab wrapping and excessive low-value pages.

**Acceptance Criteria:**

**Given** accepted content includes very long chord/tab blocks, excessive whitespace, or likely wrapping problems
**When** printable layout checks run
**Then** the workflow emits print-quality signals or report warnings
**And** severe print-hostile content can be excluded by default through the same quality filtering path.

**Given** content passes basic print-quality checks
**When** output artifacts are generated
**Then** no print-quality warning is added for that content.
