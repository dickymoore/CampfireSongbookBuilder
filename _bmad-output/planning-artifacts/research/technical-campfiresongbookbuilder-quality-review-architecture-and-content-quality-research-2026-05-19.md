---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
workflowType: 'research'
lastStep: 6
research_type: 'technical'
research_topic: 'CampfireSongbookBuilder quality/review architecture and content quality'
research_goals: 'Decide simple local-file architecture for favourites, selections, questionable status, review decisions, quality thresholds, and output pipeline while improving the quality of fetched chords and lyrics.'
user_name: 'Dicky'
date: '2026-05-19'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-05-19
**Author:** Dicky
**Research Type:** technical

---

## Research Overview

This technical research investigates how CampfireSongbookBuilder can improve the real quality of fetched lyrics and chords while keeping the project simple, local, offline-capable, and friendly to AI-agent maintenance. The research focused on local state architecture, source integration, content-quality scoring, review decisions, selections/favourites, cache compatibility, and the Markdown to `.docx` to optional PDF output path.

The strongest conclusion is that this should remain an incremental Python CLI upgrade. The architecture should preserve existing JSONL caches and repo-root commands, then add a normalized candidate contract, a deterministic quality-assessment layer, separate review-state files, generation filtering, and visible inclusion/exclusion reports. This gives the project a concrete way to prove quality: every printed song can be traced to a source candidate, quality signals, a score/status, and any explicit user review decision.

The full synthesis at the end of this document turns the detailed research into architecture defaults, implementation roadmap, risk mitigations, and source-verification notes for the next BMad architecture workflow.

## Technical Research Scope Confirmation

**Research Topic:** CampfireSongbookBuilder quality/review architecture and content quality

**Research Goals:** Decide simple local-file architecture for favourites, selections, questionable status, review decisions, quality thresholds, and output pipeline while improving the quality of fetched chords and lyrics.

**Technical Research Scope:**

- Architecture Analysis - local state design, review workflow, cache compatibility, quality pipeline boundaries
- Implementation Approaches - file formats, validation rules, scoring, source retry, manual override persistence
- Technology Stack - Python CLI-compatible libraries/tools, Markdown, `.docx`, PDF options
- Integration Patterns - scraper/API source fallback, source-attempt records, offline/cache-first behavior
- Content Quality - methods for detecting bad lyrics/chords, low-confidence matches, junk markup, duplicate content, and unusable tab
- Performance Considerations - avoiding unnecessary live requests, preserving offline generation, and testing without live sites

**Research Methodology:**

- Current web data with source verification
- Preference for official documentation and mature project documentation where available
- Confidence levels for uncertain or source-dependent information
- Recommendations constrained by the existing Python CLI, JSONL cache, and `python-docx` document pipeline

**Scope Confirmed:** 2026-05-19

---

<!-- Content will be appended sequentially through research workflow steps -->

## Technology Stack Analysis

### Programming Languages

CampfireSongbookBuilder should stay a Python CLI application for this upgrade. The existing project already uses Python 3.8+ with a flat `app/` helper-module layout, `argparse`, `requests`, `beautifulsoup4`, `pandas`, `lyricsgenius`, and `python-docx`. Re-platforming would add more risk than value because the open PRD is a brownfield quality upgrade, not a product rewrite.

Python remains suitable for the required work: local file parsing, JSONL cache handling, HTML parsing, text normalization, fuzzy matching, document generation, and CLI orchestration. The upgrade should add small helper modules rather than new service or web frameworks.

_Popular Languages:_ Python is the correct primary language because it is already the runtime, has strong standard-library support for JSON/CSV/TOML, and has mature libraries for HTTP, HTML parsing, document creation, and fuzzy matching.

_Emerging Languages:_ No emerging language should be introduced for MVP. Rust-backed Python packages such as RapidFuzz can be used indirectly when they expose a stable Python API, but the application should remain Python-first.

_Language Evolution:_ Python 3.11+ includes `tomllib` for reading TOML, but this project targets Python 3.8+, so relying on standard-library `tomllib` alone would either raise the minimum Python version or require a backport. The Python docs also note that `tomllib` reads TOML but does not write it, which matters for user-editable persisted selections or review decisions.

_Performance Characteristics:_ The expected dataset is a personal song list, so clarity and testability matter more than raw throughput. Fuzzy matching for title/artist confidence can use RapidFuzz if needed because it provides Python APIs with optimized implementations and a pure Python fallback.

_Sources:_ Python `tomllib` documentation: https://docs.python.org/3/library/tomllib.html; Python `json` documentation: https://docs.python.org/3.13/library/json.html; RapidFuzz documentation: https://rapidfuzz.github.io/RapidFuzz/index.html

### Development Frameworks and Libraries

The recommended MVP stack is deliberately conservative:

- Standard-library `json` plus the existing JSONL cache helpers for append-style cache records and machine-readable reports.
- Standard-library `csv` or existing `pandas` usage for the current `data/src/CampfireSongs.csv` source list.
- Optional PyYAML only if the architecture chooses YAML for human-edited selections or review decisions.
- RapidFuzz for deterministic title/artist matching and low-confidence source detection if simpler normalized string comparisons are insufficient.
- Existing `requests` and BeautifulSoup/lxml scraper flow for source retrieval.
- Existing `lyricsgenius` for Genius API-backed lyrics where credentials are configured.
- Existing `python-docx` for `.docx` output.
- Pandoc as an optional external converter candidate for Markdown to `.docx` and PDF paths, if architecture accepts an installed binary dependency.

_Major Frameworks:_ No application framework is needed. The framework is the CLI orchestration plus file-based pipeline.

_Micro-frameworks:_ Small libraries are reasonable where they remove real complexity: RapidFuzz for fuzzy matching, PyYAML for readable config-like files, and requests-cache only if HTTP response caching becomes necessary beyond the existing content cache. Adding any of these should be story-scoped and tested.

_Evolution Trends:_ The safest path is to preserve the current fetch/cache/document boundaries, then insert a quality-assessment layer between fetched/cached content and generated output.

_Ecosystem Maturity:_ `python-docx`, PyYAML, Pandoc, MusicBrainz, lyricsgenius, and RapidFuzz all have public documentation. That makes them acceptable research candidates, but the MVP should prefer existing dependencies before adding new ones.

_Sources:_ python-docx documentation: https://python-docx.readthedocs.io/; PyYAML documentation: https://pyyaml.org/wiki/PyYAMLDocumentation; lyricsgenius API docs: https://lyricsgenius.readthedocs.io/en/master/reference/api.html; Pandoc manual: https://pandoc.org/MANUAL.html

### Database and Storage Technologies

The project should not add a database for MVP. The PRD's priority is local, inspectable, agent-editable state. The current JSONL caches are a good fit for fetched content because JSON Lines stores one valid JSON value per line and is easy to append, inspect, stream, and repair.

For new state, there are three practical choices:

1. JSONL for event-like or append-oriented records such as Source Attempts and quality scan history.
2. JSON for canonical current-state maps such as review decisions keyed by exact artist/title or stable song IDs.
3. YAML for small human-authored files such as named Selections, if readability is more important than dependency minimization.

TOML is less attractive for writable project state because Python's standard `tomllib` reads TOML but does not write it. CSV is useful for source rows and simple favourites columns, but it becomes awkward for nested review reasons, multiple selections, source attempts, and override metadata.

_Relational Databases:_ SQLite is technically viable, but it conflicts with the PRD's inspectable-file preference and is unnecessary for a small personal library.

_NoSQL Databases:_ Document-store concepts map well to JSON files, but an actual database is not needed.

_In-Memory Databases:_ Not relevant for MVP.

_Data Warehousing:_ Not relevant.

_Recommended Storage Direction:_ Keep existing cache JSONL intact. Add a small `data/review/` or `data/state/` area with simple files: JSON for canonical review decisions and quality status, YAML or JSON for selections, and JSONL for source-attempt logs if detailed history is needed.

_Sources:_ JSON Lines documentation: https://jsonlines.org/; Python `json` documentation: https://docs.python.org/3.13/library/json.html; Python `csv` documentation: https://docs.python.org/3.9/library/csv.html; Python `tomllib` documentation: https://docs.python.org/3/library/tomllib.html; PyYAML documentation: https://pyyaml.org/wiki/PyYAMLDocumentation

### Development Tools and Platforms

The existing development platform is sufficient: local Python, `unittest`, `.flake8`, and repo-root CLI execution. The research does not support adding a new test runner, task framework, web app framework, or package manager as part of MVP.

_IDE and Editors:_ No IDE dependency should be introduced. Files should remain simple enough to edit in any editor and by AI agents.

_Version Control:_ Git remains the only required collaboration platform. New generated output and private state must respect existing ignore rules.

_Build Systems:_ No build system is needed. Any optional external converter, such as Pandoc, should be detected at runtime and fail with a clear message.

_Testing Frameworks:_ Continue using `unittest`. Add focused tests for quality scoring, review-decision loading, selection loading, cache compatibility, source fallback, and generation filtering. Do not test against live external sites.

_Static Validation:_ Add pure helper validators for selection/review files so malformed local state can be reported before generation.

_Sources:_ Project context: `_bmad-output/project-context.md`; Python `csv` documentation: https://docs.python.org/3.9/library/csv.html; Python `json` documentation: https://docs.python.org/3.13/library/json.html

### Cloud Infrastructure and Deployment

Cloud infrastructure should stay out of scope. The PRD explicitly prefers offline generation after cache population and does not require hosted services, user accounts, or collaborative libraries.

_Major Cloud Providers:_ Not relevant.

_Container Technologies:_ Not needed for MVP.

_Serverless Platforms:_ Not relevant.

_CDN and Edge Computing:_ Not relevant.

_Operational Implication:_ Because no cloud service is introduced, quality improvement must come from better local validation, better source selection/fallback, better metadata confidence checks, and clear review workflows.

_Sources:_ PRD and validation report in `_bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/`; MusicBrainz API search docs: https://musicbrainz.org/doc/MusicBrainz_API/Search

### Content Quality Technologies

The quality problem is twofold: whether fetched text is clean enough to print, and whether it is the right song.

For lyrics, Genius via `lyricsgenius` can provide an API-backed source, but API results still need post-fetch validation and local cleaning. For song identity, MusicBrainz can provide a metadata cross-check using recording searches with title and artist fields. This should not become a hard dependency for generation, but it can improve confidence scoring when online fetching is already allowed.

For chords, ChordPro is a useful normalization target or validation reference because it represents chords inline with lyrics and preserves chord placement better than fixed-width "chords above lyrics" text after editing. The MVP does not need to convert everything to ChordPro immediately, but ChordPro-like validation can identify whether chords are parseable, whether chord tokens look plausible, and whether chord placement is likely to survive formatting.

Recommended quality signals:

- Missing sentinel values: `"Lyrics not found."`, `"Chords not found."`, empty content, non-string content.
- Source confidence: exact or fuzzy title/artist match, source name, source result metadata, MusicBrainz match where available.
- Structural health: minimum useful line count, maximum length/page estimate, repeated identical blocks, excessive bracket/HTML residue, email/header/footer junk, high ratio of non-lyric markup.
- Chord health: plausible chord-token ratio, invalid chord-token count, lines with tab noise only, ChordPro bracket sanity, repeated tab blocks, excessive whitespace/preformatted residue.
- Review health: whether the user has accepted, rejected, or overridden the current content/version.

_Sources:_ MusicBrainz API search docs: https://musicbrainz.org/doc/MusicBrainz_API/Search; lyricsgenius API docs: https://lyricsgenius.readthedocs.io/en/master/reference/api.html; ChordPro syntax overview: https://songbook-pro.com/docs/manual/chordpro/; ChordPro directives docs: https://chordpro.org/chordpro/directives-define/; RapidFuzz documentation: https://rapidfuzz.github.io/RapidFuzz/index.html

### External Source Operations

This section is intentionally minimal for the project. The architecture should remain local and offline-capable. External services are sources, not infrastructure. They should be optional inputs to the cache population process, with failures isolated and recorded.

_Sources:_ Project PRD: `_bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-19/prd.md`

### Technology Adoption Trends

The stack recommendation follows a conservative brownfield pattern: use existing Python modules and file contracts, then add narrow helper libraries only where they materially improve quality or reduce parsing risk. The major adoption trend relevant here is not cloud or framework migration; it is plain-text, inspectable pipeline design:

- JSON/JSONL for machine-readable local state and appendable cache/history.
- Markdown as an inspectable intermediate artifact.
- ChordPro-style representation or validation for chord placement and print stability.
- Optional external converters for PDF rather than a complex custom PDF engine.
- Deterministic quality scoring before any AI-assisted or semantic enhancement.

_Migration Patterns:_ Introduce review and quality files alongside existing caches before changing cache schema. If cache records later gain quality fields, keep backward-compatible readers.

_Emerging Technologies:_ LLM-based lyric/chord validation could be explored later, but it should not be an MVP dependency because correctness, licensing, and reproducibility are uncertain.

_Legacy Technology:_ The current `.docx` generation via `python-docx` remains valuable. The upgrade should not remove it.

_Community Trends:_ Mature plain-text formats like Markdown, JSONL, and ChordPro are aligned with the project's agent-editable workflow.

_Sources:_ Pandoc manual: https://pandoc.org/MANUAL.html; python-docx documentation: https://python-docx.readthedocs.io/; JSON Lines documentation: https://jsonlines.org/; ChordPro syntax overview: https://songbook-pro.com/docs/manual/chordpro/

## Integration Patterns Analysis

### API Design Patterns

CampfireSongbookBuilder should use a source-adapter pattern rather than a public API, microservice, or plugin platform for MVP. Each lyrics/chords provider should be wrapped behind a small local function or adapter that returns a normalized candidate object. The rest of the pipeline should not depend on source-specific HTML, API fields, exception shapes, or sentinel strings.

Recommended candidate shape:

```json
{
  "artist": "requested artist",
  "title": "requested title",
  "content_type": "lyrics|chords",
  "source": "genius|lyrics_ovh|azlyrics|chordie|ultimate_guitar|...",
  "content": "raw or cleaned candidate text",
  "source_title": "title as returned by source, when available",
  "source_artist": "artist as returned by source, when available",
  "retrieved_at": "ISO-8601 timestamp",
  "status": "candidate|not_found|error",
  "error": null
}
```

This pattern lets source retrieval, quality assessment, review decisions, and document generation evolve independently.

_RESTful APIs:_ MusicBrainz exposes a REST-style HTTP API with XML or JSON responses and search, lookup, and browse requests. It is useful as an optional metadata cross-check for title/artist confidence, not as the canonical song-content source. Genius can be accessed through `lyricsgenius`, which wraps Genius API search methods and higher-level `Genius.search_song()` behavior.

_GraphQL APIs:_ Not relevant for MVP.

_RPC and gRPC:_ Not relevant for a single-process CLI.

_Webhook Patterns:_ Not relevant.

_Source Quality Implication:_ For good-quality chords and lyrics, the integration boundary should preserve source metadata and all Source Attempts. If a later quality report only says "bad content," the user cannot tell whether the problem was source mismatch, parsing residue, missing chords, or print-hostile tab.

_Sources:_ MusicBrainz API docs: https://musicbrainz.org/doc/MusicBrainz_API; MusicBrainz search docs: https://musicbrainz.org/doc/MusicBrainz_API/Search; lyricsgenius API docs: https://lyricsgenius.readthedocs.io/en/master/reference/api.html; lyricsgenius usage docs: https://lyricsgenius.readthedocs.io/en/master/usage.html

### Communication Protocols

The runtime has two communication modes:

1. Local file I/O for source lists, caches, review decisions, selections, reports, Markdown, `.docx`, and optional PDF.
2. HTTP(S) calls during online fetch/enrichment workflows.

The architecture should keep those modes separate. Generation from cache must not call network sources. Online fetch mode may call source adapters and optional metadata checks, but it must record enough Source Attempt data for offline review and later regeneration.

_HTTP/HTTPS Protocols:_ Use `requests` through existing fetch helpers. For MusicBrainz, include a meaningful User-Agent and respect the documented "one call per second" application guidance. That makes MusicBrainz viable only as a low-volume confidence source, not a bulk high-speed dependency.

_WebSocket Protocols:_ Not relevant.

_Message Queue Protocols:_ Not relevant.

_gRPC and Protocol Buffers:_ Not relevant.

_Operational Pattern:_ Treat each external source call as recoverable. Return `not_found` or `error` candidate statuses instead of letting source-specific failures crash the whole run.

_Sources:_ MusicBrainz API docs: https://musicbrainz.org/doc/MusicBrainz_API; MusicBrainz rate limiting docs: https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting; requests-cache user guide for optional HTTP caching concepts: https://requests-cache.readthedocs.io/en/stable/user_guide.html

### Data Formats and Standards

The integration data contracts should be simple and file-native.

_JSON and JSONL:_ JSON should represent current state and machine-readable reports. JSONL should continue to represent append-friendly cache/history records. JSON Lines requires each line to be a valid JSON value, which matches the existing one-record-per-line cache pattern.

_CSV and Flat Files:_ Keep CSV for the current source song list and possibly a simple `Favourite` column if the user prefers editing the existing list. Do not use CSV for nested review decisions, quality reasons, or source-attempt history.

_YAML:_ YAML is acceptable for named selections if readability matters more than minimizing dependencies. Use safe loading and simple schema validation.

_ChordPro:_ ChordPro should be considered a domain standard for chord/lyric alignment. ChordPro places chords inline in square brackets and uses directives on their own lines, which makes it useful as a validation target or optional normalized representation for chords. The MVP can use ChordPro-style parsing checks without forcing all output to become ChordPro.

_Markdown:_ Markdown should be the inspectable generated songbook artifact before `.docx`. Pandoc can convert between Markdown, Word `.docx`, and PDF paths, but PDF output often depends on an external PDF engine. `python-docx` remains the stable direct `.docx` path already used by the project.

_Recommended Data Contracts:_

- `data/cache/lyrics_cache.jsonl` and `data/cache/chords_cache.jsonl`: existing fetched content, backward-compatible.
- `data/review/quality_status.json`: latest quality status per Song/content type.
- `data/review/review_decisions.json`: user accept/reject/override decisions.
- `data/review/source_attempts.jsonl`: optional append-only fetch attempt history.
- `data/selections/*.json` or `data/selections/*.yaml`: named selections.
- `data/output/*.md`: inspectable generated songbook.

_Sources:_ JSON Lines: https://jsonlines.org/; Python JSON docs: https://docs.python.org/3.13/library/json.html; Python CSV docs: https://docs.python.org/3.9/library/csv.html; PyYAML docs: https://pyyaml.org/wiki/PyYAMLDocumentation; ChordPro syntax: https://songbook-pro.com/docs/manual/chordpro/; ChordPro directives: https://chordpro.org/chordpro/directives-define/; Pandoc manual: https://pandoc.org/MANUAL.html; python-docx docs: https://python-docx.readthedocs.io/

### System Interoperability Approaches

The best interoperability pattern is a staged local pipeline:

```text
Source List
  -> Source Adapters
  -> Candidate Records
  -> Quality Assessment
  -> Review State
  -> Selection/Favourite Filter
  -> Markdown Book
  -> .docx
  -> optional PDF
```

Each stage should read and write a stable local contract. This lets architecture and stories evolve one part at a time and gives AI agents durable inspection points.

_Point-to-Point Integration:_ Current scraper functions are effectively point-to-point integrations. Keep them isolated, but normalize their outputs before quality assessment.

_API Gateway Patterns:_ Not relevant as infrastructure, but a local "source registry" function can play the same coordination role by deciding source order and retry behavior.

_Service Mesh:_ Not relevant.

_Enterprise Service Bus:_ Not relevant.

_Quality Pattern:_ Do not decide "good lyrics/chords" inside document generation. Document generation should consume accepted content plus quality/review state. This avoids hiding source-quality decisions in formatting code.

_Sources:_ Project architecture docs: `docs/architecture.md`; MusicBrainz API docs: https://musicbrainz.org/doc/MusicBrainz_API; python-docx docs: https://python-docx.readthedocs.io/

### Microservices Integration Patterns

Microservices are not appropriate for this product. However, several microservice resilience patterns translate well into local function boundaries:

_API Gateway Pattern:_ Implement as a local source-orchestration function that calls source adapters in configured order, records attempts, and returns the best candidate or a Questionable status.

_Service Discovery:_ Not needed. Sources are configured statically in code or config.

_Circuit Breaker Pattern:_ Useful in local form. If a source repeatedly fails during a run, skip further calls to that source for the remainder of the run and report it. This protects the workflow from slow or broken external sites.

_Saga Pattern:_ Not needed. There are no distributed transactions.

_Source Quality Implication:_ A local source orchestrator should score candidates before accepting them. A lower-priority source with clean, high-confidence content should beat a higher-priority source with obvious junk or mismatched metadata.

_Sources:_ MusicBrainz rate limiting docs: https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting; requests-cache docs for optional request persistence and expiration concepts: https://requests-cache.readthedocs.io/en/stable/user_guide.html

### Event-Driven Integration

Full event sourcing is unnecessary, but append-only event-like records are useful for debugging and quality review.

_Publish-Subscribe Patterns:_ Not needed.

_Event Sourcing:_ Do not rebuild application state from events for MVP. Use explicit current-state files for quality status and review decisions.

_Message Broker Patterns:_ Not relevant.

_CQRS Patterns:_ A lightweight separation is useful: write detailed Source Attempts and quality scan records for auditability, but read compact current-state files during generation.

_Recommended Pattern:_

- Append Source Attempts to JSONL when fetching.
- Write latest quality status to JSON for generation.
- Write Review Decisions to JSON for user intent.
- Generate human-readable and machine-readable reports after each run.

This gives traceability without creating a complex event-sourced system.

_Sources:_ JSON Lines: https://jsonlines.org/; Python JSON docs: https://docs.python.org/3.13/library/json.html

### Integration Security and Source Responsibility Patterns

Security is simple but still important because this project touches API tokens and external websites.

_OAuth 2.0 and JWT:_ Only relevant to Genius API credentials as handled by existing config and `lyricsgenius`; do not broaden authentication scope.

_API Key Management:_ Keep `data/config/config.json` private and ignored. Do not write tokens to reports, caches, or Source Attempt logs.

_Mutual TLS:_ Not relevant.

_Data Encryption:_ Not needed for local hobby files unless the user chooses to protect their local config externally.

_External Source Responsibility:_ MusicBrainz requires client identification and rate-limit discipline. Scraped sources should be treated as brittle and optional; failures must be isolated. The architecture should also avoid presenting fetched lyrics/chords as legally redistributable content.

_Sources:_ MusicBrainz API docs: https://musicbrainz.org/doc/MusicBrainz_API; MusicBrainz rate limiting docs: https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting; lyricsgenius docs: https://lyricsgenius.readthedocs.io/en/master/how_it_works.html

### Recommended Integration Decision for Architecture

For the next architecture step, use this decision as the default unless the user overrides it:

1. Keep existing content caches as JSONL and backward-compatible.
2. Add normalized candidate records at the source boundary.
3. Add a quality assessment layer that produces explicit Quality Signals and scores.
4. Persist current quality status and Review Decisions separately from raw fetched content.
5. Persist Source Attempts as optional JSONL audit/history.
6. Generate Markdown from accepted content before `.docx`.
7. Treat PDF as an optional conversion after Markdown/`.docx`, with clear failure reporting.

This pattern directly supports the user's goal: better-quality chords and lyrics become a measurable pipeline output, not just an improvement hoped for inside scrapers.

## Architectural Patterns and Design

### System Architecture Patterns

The correct architecture pattern is an incremental modular monolith, not microservices, not a web app, and not a full rewrite. The application should remain a single-process Python CLI with clearer internal boundaries:

- Source list loading
- Source adapter orchestration
- Candidate normalization
- Quality assessment
- Review-state persistence
- Selection/favourite filtering
- Markdown rendering
- `.docx` rendering
- Optional PDF conversion

This is a brownfield modernization problem. The Strangler Fig pattern is useful as a metaphor: introduce a new quality pipeline around the old fetch/cache/generate flow, route only specific responsibilities through the new pipeline, and keep existing commands working while responsibilities move. Microsoft's Azure Architecture Center describes the Strangler Fig pattern as incremental migration that lets the existing application continue functioning while specific pieces are replaced. Martin Fowler's later writing emphasizes clear components that can be replaced independently. That maps well to this project because replacing the whole CLI would be high risk and unnecessary.

_Recommended Pattern:_ Incremental modular monolith with façade-like orchestration at the CLI boundary. Keep `main.py` thin and route new behavior into helper modules.

_Rejected Patterns:_

- Microservices: no independent deployment, scaling, or team boundary need.
- Event-sourced system: useful audit logs are enough; rebuilding all state from events would add complexity.
- Database-backed app: not needed for a local songbook builder and reduces inspectability.
- GUI-first architecture: explicitly out of v1 scope.

_Sources:_ Microsoft Strangler Fig pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig; Martin Fowler Strangler Fig Application: https://martinfowler.com/bliki/StranglerFigApplication.html; project architecture docs: `docs/architecture.md`

### Design Principles and Best Practices

The architecture should follow a light ports-and-adapters style without importing heavy enterprise ceremony. The core quality logic should depend on plain data structures, not on HTTP, BeautifulSoup, `python-docx`, or live site behavior. This keeps quality scoring testable and lets source adapters remain brittle but isolated.

Recommended boundaries:

- `source adapters` return normalized candidates.
- `quality assessment` consumes candidates and returns deterministic signals.
- `review state` merges quality signals with user decisions.
- `generation filters` decide included/excluded songs.
- `renderers` produce Markdown and `.docx` from accepted content only.

This is close to Clean Architecture's useful idea of keeping business/application rules independent from infrastructure. Microsoft guidance on common web architectures describes Clean Architecture as putting business logic and the application model at the center; for this small CLI, the practical interpretation is simple: quality rules should be central and pure enough to test.

Architecture Decision Records should be used sparingly for the choices that will otherwise be relitigated:

1. Storage format and location for Favourites, Selections, Quality Status, and Review Decisions.
2. Candidate/Quality Signal data contract.
3. Markdown as canonical intermediate versus additional export.
4. Optional PDF conversion strategy.
5. Whether to add RapidFuzz, PyYAML, requests-cache, or other dependencies.

ADR guidance commonly centers on recording context, decision, and consequences for architecturally significant decisions. That is enough for this project.

_Sources:_ Microsoft common architecture guidance: https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures; ADR GitHub organization: https://adr.github.io/; EdgeX ADR format guidance: https://docs.edgexfoundry.org/4.0/design/adr/

### Scalability and Performance Patterns

Human-scale songbook generation does not require distributed scalability. The relevant performance risks are slow/broken external sources, excessive repeated HTTP calls, and expensive repeated quality checks over unchanged cached content.

Recommended patterns:

- Cache-first reads: never fetch when acceptable cached content already exists unless the user requests refresh.
- Source-level circuit breaker within a run: if a source repeatedly fails, skip it for the rest of that run and report it.
- Rate limiting for metadata enrichment: especially for MusicBrainz, which documents a one-call-per-second API rule and requires a meaningful User-Agent.
- Incremental quality recomputation: store enough content/version metadata to avoid rescoring unchanged cached records where practical.
- Small deterministic heuristics before expensive checks: sentinel values, empty content, and obvious markup/junk checks should run before fuzzy matching or metadata API checks.

Microsoft's reliability pattern catalog identifies cache-aside and circuit breaker patterns as common reliability tools. This project should not import a cloud architecture, but those ideas translate directly to local source calls.

_Sources:_ Microsoft reliability design patterns: https://learn.microsoft.com/en-us/azure/well-architected/reliability/design-patterns; MusicBrainz API rate limiting: https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting; requests-cache user guide: https://requests-cache.readthedocs.io/en/stable/user_guide.html

### Integration and Communication Patterns

The architecture should standardize one internal data flow:

```text
requested Song
  -> Source Attempt
  -> Candidate
  -> Quality Signals
  -> Review Status
  -> Accepted/Excluded Song
  -> Rendered output
```

The key architectural decision is to avoid letting source adapters return final content directly to document generation. Direct source-to-document integration is the current weakness: bad tab, junk pages, and wrong-song matches can slip through because there is no durable quality gate.

Recommended communication contracts:

- Source adapters communicate through candidate dictionaries/dataclasses.
- Quality assessment communicates through structured Quality Signals.
- Review state communicates through current-state files.
- Renderers consume accepted content and an exclusion report.

_Sources:_ MusicBrainz API docs: https://musicbrainz.org/doc/MusicBrainz_API; lyricsgenius docs: https://lyricsgenius.readthedocs.io/en/master/reference/api.html; JSON Lines format: https://jsonlines.org/

### Security Architecture Patterns

Security remains modest but non-zero:

- Keep API tokens in private local config.
- Do not write API tokens to logs, caches, source-attempt records, or generated reports.
- Keep generated outputs and private config out of version control.
- Use meaningful User-Agent headers for MusicBrainz and similar APIs.
- Treat scraped source content as untrusted text: clean it, escape or normalize it before Markdown and `.docx` rendering, and do not execute or interpret embedded HTML.

OWASP's secrets guidance is broader than this project needs, but the core principle applies: secrets such as API keys should be managed deliberately and not leak into code or artifacts.

_Sources:_ OWASP Secrets Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html; MusicBrainz rate limiting and User-Agent guidance: https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting

### Data Architecture Patterns

Use separate current-state and history files:

- Existing JSONL caches remain the fetched-content store.
- `quality_status.json` is the current quality state used by generation.
- `review_decisions.json` is the current user override/accept/reject state.
- `source_attempts.jsonl` is historical/audit data for debugging.
- Selection files define user intent for book composition.

This split keeps generation simple. It also avoids polluting raw fetched content with every later review decision. If the architecture later stores quality fields inside cache records for convenience, it should still keep backward-compatible readers and treat review decisions as separate user intent.

Quality status should include a fingerprint of assessed content, such as source, content type, and a stable content hash. That lets the system tell whether a review decision applies to the current content or to an older fetched version.

Recommended minimal status shape:

```json
{
  "song_key": "Artist - Title",
  "artist": "Artist",
  "title": "Title",
  "content_type": "chords",
  "content_hash": "sha256:...",
  "quality": "clean|questionable|missing",
  "score": 0.82,
  "signals": [
    {"code": "low_title_match", "severity": "warning", "message": "..."}
  ],
  "assessed_at": "2026-05-19T10:00:00+01:00"
}
```

_Sources:_ JSON Lines format: https://jsonlines.org/; Python JSON docs: https://docs.python.org/3.13/library/json.html; Python CSV docs: https://docs.python.org/3.9/library/csv.html

### Deployment and Operations Architecture

There is no deployment platform for MVP. Operations means reliable local runs:

- Commands continue to run from repo root.
- Online fetch/cache runs are separate from offline generation runs.
- Optional dependencies such as Pandoc are detected and reported, not assumed.
- Reports are written as local files for human and AI-agent review.
- Unit tests do not depend on live sites or real credentials.

`unittest` remains appropriate because it is in the Python standard library and already used by the project. Pytest can run unittest tests, but adopting pytest is not necessary for this upgrade and would be an unrelated toolchain decision.

`python-docx` remains the direct `.docx` path. Pandoc is a strong optional conversion candidate because its manual documents Markdown, `.docx`, and PDF output support, but PDF output may depend on a third-party PDF engine. Architecture should make PDF optional and non-destructive.

_Sources:_ Python unittest docs: https://docs.python.org/3.9/library/unittest.html; pytest unittest support docs: https://docs.pytest.org/en/stable/unittest.html; python-docx docs: https://python-docx.readthedocs.io/; Pandoc manual: https://pandoc.org/MANUAL.html

### Recommended Architecture Decisions for Next Workflow

The technical research supports these defaults for `bmad-create-architecture`:

1. Adopt an incremental modular monolith architecture.
2. Preserve existing repo-root CLI commands and JSONL cache semantics.
3. Introduce a normalized candidate contract between source fetching and quality assessment.
4. Implement quality assessment as pure/testable helpers.
5. Store review decisions separately from fetched content.
6. Store current quality status separately from source-attempt history.
7. Use Markdown as the inspectable intermediate artifact before `.docx`.
8. Keep PDF optional and recoverable.
9. Record major choices as short ADRs.

This architecture gives the user a concrete way to "show we get good quality chords and lyrics": every included song can be traced to a source candidate, a set of quality signals, a score/status, and any explicit user review decision.

## Implementation Approaches and Technology Adoption

### Technology Adoption Strategies

The implementation should follow incremental adoption, not a rewrite. The PRD is a brownfield quality upgrade, and the current CLI already fetches, caches, cleans, and generates `.docx` output. The safest approach is to introduce new boundaries around the existing flow:

1. Define candidate and quality-status data contracts.
2. Add pure quality assessment helpers.
3. Record quality status and review decisions separately from raw caches.
4. Apply quality filtering during generation.
5. Add Markdown output.
6. Add optional PDF conversion last.

This is consistent with Strangler Fig and Branch by Abstraction approaches: introduce new behavior alongside existing behavior, route a narrow responsibility through the new path, and keep the system working during migration.

_Source:_ Microsoft Strangler Fig pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig; Martin Fowler Branch by Abstraction: https://martinfowler.com/bliki/BranchByAbstraction.html

### Development Workflows and Tooling

Keep the current workflow:

- Repo-root execution with `python3 main.py ...`
- `unittest` tests under `tests/`
- `.flake8` max line length 100
- Small helper modules under `app/`
- Local files under `data/`

Google's engineering practices emphasize small, understandable changes for review. That maps directly to this project: each story should change one behavior surface and include regression tests where possible.

Recommended story shape:

- One story for data contracts and loaders.
- One story for quality assessment helpers.
- One story for source-attempt recording.
- One story for review-decision persistence.
- One story for generation filtering.
- One story for Markdown output.
- One story for optional PDF conversion.

_Source:_ Google Engineering Practices: https://google.github.io/eng-practices/

### Testing and Quality Assurance

Testing should remain `unittest`-based. Use `tempfile.TemporaryDirectory` for local state files and `unittest.mock` for source adapters and network calls. Do not test against live Genius, MusicBrainz, lyric websites, chord websites, local user caches, or generated `.docx` binary equality.

High-value unit tests:

- Candidate normalization from source adapter outputs.
- Missing sentinel detection.
- Empty and non-string content handling.
- Duplicate block detection.
- Junk markup detection.
- Overlong content detection.
- Title/artist confidence scoring.
- Chord-token plausibility checks.
- Review-decision application.
- Selection loading and malformed selection reporting.
- Generation filtering with clean and Questionable songs.
- Offline generation proving no source adapter calls are made.

Use `hashlib.sha256` or equivalent content hashes to bind quality status and review decisions to a specific content version. That prevents a stale "accepted" decision from silently applying after a refetch changes the content.

_Source:_ Python `unittest`: https://docs.python.org/3.9/library/unittest.html; Python `unittest.mock`: https://docs.python.org/3.15/library/unittest.mock.html; Python `tempfile`: https://docs.python.org/3.12/library/tempfile.html; Python `hashlib`: https://docs.python.org/3/library/hashlib.html

### Deployment and Operations Practices

There is no hosted deployment. Operational quality is local-run reliability:

- Source failures are logged and reported, not fatal when fallbacks exist.
- Online fetch/cache flows are separate from offline generation.
- Generated reports identify included, excluded, missing, and Questionable songs.
- Optional external tools such as Pandoc are detected at runtime.
- PDF failure does not delete Markdown or `.docx` artifacts.

Pandoc is a practical optional converter because it documents Markdown input and `.docx`/PDF output, but PDF output depends on the local environment. Keep `python-docx` as the direct `.docx` path until Markdown-to-docx conversion is proven better.

_Source:_ Pandoc getting started: https://pandoc.org/getting-started.html; Pandoc manual: https://pandoc.org/MANUAL.html; python-docx documentation: https://python-docx.readthedocs.io/

### Team Organization and Skills

This is a one-person/project-agent workflow. The needed skill split is architectural clarity rather than team specialization:

- Product owner decides quality thresholds and review behavior.
- Architecture workflow records storage, quality contract, and output-pipeline decisions.
- Story generation splits work into testable slices.
- Dev story execution implements one slice at a time.
- Code review checks cache compatibility, offline behavior, and test coverage.

No new specialized infrastructure or operations role is needed.

_Source:_ Project context: `_bmad-output/project-context.md`; Google Engineering Practices: https://google.github.io/eng-practices/

### Cost Optimization and Resource Management

Cost is mostly developer time, implementation risk, and external-source fragility. The architecture should minimize new dependencies and avoid unnecessary live requests.

Recommended cost controls:

- Use existing dependencies first.
- Add RapidFuzz only if simple normalized string matching is insufficient.
- Add PyYAML only if YAML is chosen for human-authored selections.
- Add requests-cache only if HTTP response caching is needed beyond existing content caches.
- Add jsonschema only if schemas become complex enough that hand validation becomes error-prone.
- Make Pandoc/PDF support optional and non-blocking.

_Source:_ RapidFuzz documentation: https://rapidfuzz.github.io/RapidFuzz/index.html; PyYAML documentation: https://pyyaml.org/wiki/PyYAMLDocumentation; requests-cache user guide: https://requests-cache.readthedocs.io/en/stable/user_guide.html; jsonschema documentation: https://python-jsonschema.readthedocs.io/en/stable/

### Risk Assessment and Mitigation

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Quality scores reject too many usable songs | Frustrating output gaps | Start with warning/reporting, tune thresholds, allow explicit Review Decisions |
| Quality scores accept bad songs | Bad print output | Default exclusion for high-severity signals, report included warnings |
| Review decisions become stale after refetch | Wrong content accepted silently | Store content hashes with quality status and review decisions |
| Cache schema changes break old data | Existing library unusable | Keep raw caches backward-compatible; add separate state files first |
| External sources change markup | Broken fetches or junk content | Isolate source adapters, record Source Attempts, keep fallback behavior |
| PDF tool unavailable | Failed final artifact | Keep Markdown and `.docx`; make PDF optional |
| New dependencies complicate setup | Higher maintenance cost | Add dependencies only after architecture decision and focused tests |

_Source:_ Microsoft reliability design patterns: https://learn.microsoft.com/en-us/azure/well-architected/reliability/design-patterns; project context: `_bmad-output/project-context.md`

## Technical Research Recommendations

### Implementation Roadmap

1. Define local data contracts for Candidate, Quality Signal, Quality Status, Review Decision, Source Attempt, Favourite, and Selection.
2. Add loaders/writers for new state files under a clear local directory such as `data/review/` and `data/selections/`.
3. Implement pure quality assessment helpers for lyrics and chords/tab.
4. Add source-attempt recording around existing source fallback functions.
5. Add title/artist confidence scoring, starting with deterministic normalization and optional RapidFuzz later.
6. Add review-decision application using content hashes.
7. Add generation filtering and reports.
8. Add Markdown output.
9. Preserve `.docx` output.
10. Add optional PDF conversion only after Markdown and `.docx` are stable.

### Technology Stack Recommendations

- Keep Python CLI and flat `app/` modules.
- Keep `unittest`.
- Keep existing JSONL caches.
- Use JSON for current quality/review state by default.
- Use JSON or YAML for selections; choose JSON if dependency minimization wins, YAML if human-editing comfort wins.
- Use `hashlib.sha256` for content fingerprints.
- Consider RapidFuzz for title/artist confidence.
- Consider ChordPro-style validation for chord quality checks.
- Keep `python-docx`; consider Pandoc for optional conversion.

### Skill Development Requirements

Implementation agents need to understand:

- Existing repo-root CLI behavior.
- JSONL cache compatibility.
- Source fallback semantics and sentinel values.
- Unit testing with `unittest`, `tempfile`, and `mock`.
- Basic text normalization and deterministic scoring.
- Markdown and `.docx` generation boundaries.

### Success Metrics and KPIs

Use PRD metrics plus implementation-level checks:

- Every generated book has an inclusion/exclusion report.
- Every Questionable exclusion has at least one structured Quality Signal.
- Offline generation makes zero source-adapter calls.
- Existing cache records remain readable.
- Review decisions include a content hash or equivalent version binding.
- Tests cover clean, missing, junk, duplicate, overlong, low-confidence, and override cases.

---

# Quality-Gated Local Songbook Pipeline: Comprehensive Technical Research

## Executive Summary

CampfireSongbookBuilder does not need a new platform, database, service layer, or GUI to achieve the PRD goal. It needs a quality-gated local pipeline that makes content trust visible before printing. The current Python CLI already has the right foundation: source CSV input, source fetching, JSONL caches, text cleaning, and `.docx` generation. The upgrade should preserve that flow while inserting explicit quality and review stages between fetched content and generated output.

The research supports an incremental modular monolith architecture. Source adapters should produce normalized Candidate records. Pure quality helpers should score lyrics and chords/tab for missing content, junk markup, duplicate blocks, excessive length, title/artist confidence, chord-token plausibility, and print-hostile formatting. Review state should be stored separately from raw fetched caches so user decisions survive regeneration without corrupting source data. Generated books should consume only accepted content, write Markdown first, continue producing `.docx`, and treat PDF as optional.

The key strategic implication is that "good quality chords and lyrics" becomes measurable. A generated book should include a report showing which songs were accepted, excluded, or included by explicit override, with structured reasons. This is stronger than hoping scraper improvements work: it makes quality auditable, testable, and adjustable.

**Key Technical Findings:**

- Keep Python CLI and the existing flat `app/` module style.
- Preserve existing JSONL caches and exact artist/title compatibility.
- Add normalized Candidate, Quality Signal, Quality Status, Review Decision, Source Attempt, Favourite, and Selection contracts.
- Store current quality/review state separately from raw fetched content.
- Use content hashes so review decisions do not silently apply to changed refetched content.
- Use deterministic checks first; consider RapidFuzz and MusicBrainz only as optional confidence enhancers.
- Use ChordPro-style validation ideas for chord quality without requiring full ChordPro conversion in MVP.
- Generate Markdown as an inspectable intermediate before `.docx`.
- Make PDF conversion optional and non-destructive.

**Technical Recommendations:**

1. Adopt an incremental modular monolith architecture.
2. Add the quality pipeline before changing output conversion.
3. Use JSON for current quality/review state by default; use JSONL for source-attempt history.
4. Keep selections as JSON by default unless architecture explicitly chooses YAML for human-editing comfort.
5. Split implementation into small tested stories and keep live network calls out of unit tests.

## Table of Contents

1. Technical Research Introduction and Methodology
2. Technical Landscape and Architecture Analysis
3. Implementation Approaches and Best Practices
4. Technology Stack Evolution and Current Trends
5. Integration and Interoperability Patterns
6. Performance and Scalability Analysis
7. Security and Compliance Considerations
8. Strategic Technical Recommendations
9. Implementation Roadmap and Risk Assessment
10. Future Technical Outlook and Innovation Opportunities
11. Technical Research Methodology and Source Verification
12. Technical Appendices and Reference Materials

## 1. Technical Research Introduction and Methodology

### Technical Research Significance

The core technical problem is not document generation alone. It is content trust. A songbook builder can fetch and print content, but it is not useful before a trip if it prints pages of broken tab, wrong songs, scraper residue, duplicate junk, or missing chords. The architecture therefore needs to treat quality as a first-class pipeline stage.

This is also a local-first problem in practice. The user should be able to fetch/cache content when online, review it, and later generate a book offline. Local-first research emphasizes local ownership and offline capability; that principle fits this project without requiring multi-device sync or distributed conflict resolution.

_Sources:_ Local-first research by Kleppmann et al.: https://martin.kleppmann.com/2019/10/23/local-first-at-onward.html; MusicBrainz rate limiting/User-Agent guidance: https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting

### Technical Research Methodology

- **Technical Scope:** local state design, quality scoring, source integration, cache compatibility, review workflow, and output pipeline.
- **Data Sources:** project PRD/context docs plus official or mature public documentation for Python, JSON Lines, PyYAML, python-docx, Pandoc, MusicBrainz, lyricsgenius, ChordPro, RapidFuzz, requests-cache, jsonschema, and architecture pattern references.
- **Analysis Framework:** prefer incremental brownfield changes, inspectable files, pure/testable helpers, and compatibility with existing CLI behavior.
- **Time Period:** current public documentation checked on 2026-05-19.
- **Technical Depth:** enough to support the next architecture workflow and implementation story breakdown.

### Technical Research Goals and Objectives

**Original Technical Goals:** Decide simple local-file architecture for favourites, selections, questionable status, review decisions, quality thresholds, and output pipeline while improving the quality of fetched chords and lyrics.

**Achieved Technical Objectives:**

- Identified a local pipeline architecture that can prove content quality before print.
- Chose conservative storage defaults that preserve JSONL cache compatibility.
- Identified optional tools for title/artist confidence, chord validation, and PDF conversion.
- Produced an implementation roadmap that starts with quality contracts and tests before output changes.

## 2. Technical Landscape and Architecture Analysis

### Current Technical Architecture Patterns

The current system is a small Python CLI monolith. That is a strength for this project. The right pattern is an incremental modular monolith: keep one process and one local filesystem state model, but create cleaner internal boundaries.

The main architectural evolution is:

```text
Source List
  -> Source Adapters
  -> Candidate Records
  -> Quality Assessment
  -> Review State
  -> Selection/Favourite Filter
  -> Markdown Book
  -> .docx
  -> optional PDF
```

This matches Strangler Fig/Branch by Abstraction thinking: introduce the new quality path alongside existing behavior, then route more generation paths through it as tests and confidence grow.

_Sources:_ Microsoft Strangler Fig pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig; Martin Fowler Branch by Abstraction: https://martinfowler.com/bliki/BranchByAbstraction.html

### System Design Principles and Best Practices

The quality rules should be pure/testable application logic. They should not depend directly on HTTP, BeautifulSoup, `python-docx`, live websites, or local credentials.

Recommended internal boundaries:

- Source adapters normalize source-specific results.
- Quality assessment returns structured signals and scores.
- Review state applies user intent to current content versions.
- Generation filters decide accepted/excluded songs.
- Renderers produce Markdown and `.docx` from accepted content.

Short ADRs should record the few decisions that matter: state file format, data contracts, Markdown/PDF strategy, and any new dependency.

_Sources:_ ADR resources: https://adr.github.io/; EdgeX ADR guidance: https://docs.edgexfoundry.org/4.0/design/adr/

## 3. Implementation Approaches and Best Practices

### Current Implementation Methodologies

Use gradual adoption. Do not rewrite scrapers, cache handling, and document output in one change. Start with data contracts and pure quality helpers, then connect them to source fallback and generation.

Implementation should use small stories with regression tests. Google Engineering Practices emphasize small changes; that aligns with this repo's simple helper-module style.

_Sources:_ Google Engineering Practices: https://google.github.io/eng-practices/

### Implementation Framework and Tooling

Keep the existing toolchain:

- Python CLI
- `unittest`
- `tempfile` for isolated file tests
- `unittest.mock` for network/source isolation
- `hashlib.sha256` for content fingerprints
- `python-docx` for `.docx`
- optional Pandoc for later conversion work

_Sources:_ Python `unittest`: https://docs.python.org/3.9/library/unittest.html; Python `unittest.mock`: https://docs.python.org/3.15/library/unittest.mock.html; Python `tempfile`: https://docs.python.org/3.12/library/tempfile.html; Python `hashlib`: https://docs.python.org/3/library/hashlib.html

## 4. Technology Stack Evolution and Current Trends

### Current Technology Stack Landscape

No major stack migration is recommended. The Python ecosystem is enough for local files, scoring, scraping, Markdown, `.docx`, and optional conversion.

Recommended stack:

- JSON/JSONL for machine-readable state and history.
- JSON or YAML for selections, with JSON as the dependency-minimizing default.
- RapidFuzz as optional if simple normalized matching is not enough.
- ChordPro-style parsing concepts for chord quality validation.
- Pandoc as optional only after Markdown and `.docx` are stable.

_Sources:_ JSON Lines: https://jsonlines.org/; Python JSON docs: https://docs.python.org/3.13/library/json.html; PyYAML docs: https://pyyaml.org/wiki/PyYAMLDocumentation; RapidFuzz docs: https://rapidfuzz.github.io/RapidFuzz/index.html

### Technology Adoption Patterns

Adopt new tools only when they pay for themselves:

- RapidFuzz: useful for title/artist confidence.
- PyYAML: useful only if selections need human-friendly editing beyond JSON.
- requests-cache: useful only if HTTP response caching is needed beyond content caches.
- jsonschema: useful only if hand-rolled validation becomes error-prone.
- Pandoc: useful only if output conversion needs exceed `python-docx`.

_Sources:_ requests-cache docs: https://requests-cache.readthedocs.io/en/stable/user_guide.html; jsonschema docs: https://python-jsonschema.readthedocs.io/en/stable/; Pandoc manual: https://pandoc.org/MANUAL.html

## 5. Integration and Interoperability Patterns

### Current Integration Approaches

External sources should be integrated through adapters that produce normalized Candidate records. Good-quality lyrics/chords require preserving enough source metadata to judge confidence:

- requested title/artist
- source-returned title/artist where available
- source name
- content type
- content
- source status/error
- retrieval timestamp

MusicBrainz can be used as an optional metadata cross-check. Genius via lyricsgenius remains a lyrics source where configured. Scraped chord/lyric sources remain brittle and must be isolated.

_Sources:_ MusicBrainz API: https://musicbrainz.org/doc/MusicBrainz_API; MusicBrainz search docs: https://musicbrainz.org/doc/MusicBrainz_API/Search; lyricsgenius docs: https://lyricsgenius.readthedocs.io/en/master/reference/api.html

### Interoperability Standards and Protocols

The important standards are local data and music text standards:

- JSON and JSONL for state/history.
- CSV for existing source list compatibility.
- Markdown for inspectable output.
- ChordPro concepts for chord placement and chord-token validation.
- `.docx` via python-docx.
- optional PDF through Pandoc or another documented converter.

_Sources:_ ChordPro docs: https://songbook-pro.com/docs/manual/chordpro/; ChordPro directives: https://chordpro.org/chordpro/directives-define/; python-docx docs: https://python-docx.readthedocs.io/

## 6. Performance and Scalability Analysis

### Performance Characteristics and Optimization

The library size is small enough that readability and correctness beat raw speed. The real performance risk is external source latency and repeated calls.

Recommended optimizations:

- Use cache-first behavior.
- Skip source calls during offline generation.
- Rate-limit optional metadata enrichment.
- Short-circuit obvious bad content before fuzzy matching.
- Store content hashes to avoid unnecessary rescoring.

_Sources:_ MusicBrainz rate limiting: https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting; Microsoft reliability patterns: https://learn.microsoft.com/en-us/azure/well-architected/reliability/design-patterns

### Scalability Patterns and Approaches

Do not scale with infrastructure. Scale with clean local contracts:

- current-state files for generation
- append-only JSONL for source-attempt history
- small pure functions for quality checks
- optional dependency boundaries for enrichment/conversion

## 7. Security and Compliance Considerations

### Security Best Practices and Frameworks

Keep secrets local and out of artifacts. Genius API tokens should stay in ignored config files and should never be written to reports, caches, or source-attempt logs.

Treat fetched content as untrusted text. Clean and normalize it before Markdown or `.docx` rendering. Do not execute embedded source content.

_Sources:_ OWASP Secrets Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html

### Compliance and Regulatory Considerations

The PRD correctly avoids promising legal/licensed redistribution of song content. The architecture should continue to frame external lyrics/chords as user-local fetched content and should not add hosted distribution.

MusicBrainz integration, if used, should follow User-Agent and rate-limit expectations.

_Sources:_ MusicBrainz API/rate limiting: https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting

## 8. Strategic Technical Recommendations

### Technical Strategy and Decision Framework

Default decisions for the architecture workflow:

| Decision Area | Recommended Default | Reason |
| --- | --- | --- |
| App shape | Python CLI modular monolith | Preserves working system |
| Raw content cache | Existing JSONL | Backward-compatible |
| Quality status | JSON current-state file | Simple generation reads |
| Review decisions | JSON current-state file with content hash | Prevents stale overrides |
| Source attempts | JSONL history | Append-friendly audit |
| Selections | JSON by default | No new dependency |
| Chord quality | ChordPro-style validation concepts | Better chord evidence |
| Metadata confidence | deterministic matching first, optional RapidFuzz/MusicBrainz | Keeps MVP simple |
| Output | Markdown then `.docx`, optional PDF | Inspectable and recoverable |

### Competitive Technical Advantage

The product advantage is not fetching from more sources blindly. It is confidence: the book can explain why each song was included or excluded. That is the difference between a scraper and a print-ready songbook builder.

## 9. Implementation Roadmap and Risk Assessment

### Technical Implementation Framework

Recommended implementation phases:

1. **Contracts:** Candidate, Quality Signal, Quality Status, Review Decision, Source Attempt, Selection.
2. **Quality Helpers:** missing, junk, duplicate, length, title/artist confidence, chord plausibility.
3. **State Persistence:** load/write quality status and review decisions.
4. **Source Attempts:** record attempts around existing source fallback.
5. **Filtering:** exclude Questionable songs by default and report reasons.
6. **Selections/Favourites:** generate selected subsets with quality filtering.
7. **Markdown:** produce inspectable output.
8. **`.docx`:** preserve current document generation from accepted content.
9. **PDF:** add optional conversion last.

### Technical Risk Management

| Risk | Mitigation |
| --- | --- |
| False positives reject usable songs | Start with report/warn thresholds and allow review overrides |
| False negatives include bad songs | Default-exclude severe signals and surface warnings |
| Stale review decisions | Bind decisions to content hashes |
| Cache incompatibility | Add separate state files before changing cache schema |
| Source fragility | Isolate adapters and record attempts |
| PDF environment failures | Keep Markdown and `.docx`; make PDF optional |
| Dependency creep | Add dependencies only via ADR/story decision |

## 10. Future Technical Outlook and Innovation Opportunities

### Emerging Technology Trends

Near-term opportunities:

- tune deterministic quality heuristics against real cache samples
- add RapidFuzz if title/artist matching needs better confidence
- introduce optional MusicBrainz metadata checks for online fetch mode
- experiment with ChordPro as a future canonical chord representation

Medium-term opportunities:

- richer layout analysis for printable page quality
- source quality ranking based on historical acceptance rates
- interactive review reports
- optional document conversion with Pandoc if it improves consistency

Long-term opportunities:

- AI-assisted review can be explored later, but it should not be an MVP dependency because deterministic tests and reproducibility matter more right now.

## 11. Technical Research Methodology and Source Verification

### Comprehensive Technical Source Documentation

Primary technical sources used:

- Python docs for `json`, `csv`, `tomllib`, `unittest`, `mock`, `tempfile`, and `hashlib`
- JSON Lines documentation
- PyYAML documentation
- RapidFuzz documentation
- requests-cache documentation
- jsonschema documentation
- python-docx documentation
- Pandoc manual/getting started
- MusicBrainz API/search/rate-limit documentation
- lyricsgenius documentation
- ChordPro documentation
- Microsoft Azure Architecture Center patterns
- Martin Fowler architecture/migration writing
- Google Engineering Practices
- OWASP Secrets Management Cheat Sheet

### Technical Research Quality Assurance

Confidence level: **High** for the overall architecture recommendation because it aligns with the existing codebase, PRD constraints, and multiple mature technical references.

Limitations:

- Source-specific scraping quality still requires local cache samples and implementation testing.
- Exact thresholds for "too long," "too much junk," and chord plausibility need empirical tuning.
- PDF conversion choice should be validated locally because available converters differ by machine.

## 12. Technical Appendices and Reference Materials

### Detailed Technical Data Tables

| Artifact | Format | Purpose |
| --- | --- | --- |
| Existing lyrics/chords cache | JSONL | Raw fetched content |
| `quality_status.json` | JSON | Current assessed status per content version |
| `review_decisions.json` | JSON | User decisions bound to content hashes |
| `source_attempts.jsonl` | JSONL | Fetch history/debug audit |
| selections | JSON or YAML | Named book inputs |
| generated book | Markdown | Inspectable output |
| generated document | `.docx` | Printable/editable output |
| generated PDF | PDF | Optional final artifact |

### Technical Resources and References

- JSON Lines: https://jsonlines.org/
- Python JSON: https://docs.python.org/3.13/library/json.html
- Python CSV: https://docs.python.org/3.9/library/csv.html
- Python unittest: https://docs.python.org/3.9/library/unittest.html
- python-docx: https://python-docx.readthedocs.io/
- Pandoc: https://pandoc.org/MANUAL.html
- MusicBrainz API: https://musicbrainz.org/doc/MusicBrainz_API
- lyricsgenius: https://lyricsgenius.readthedocs.io/en/master/reference/api.html
- ChordPro syntax: https://songbook-pro.com/docs/manual/chordpro/
- RapidFuzz: https://rapidfuzz.github.io/RapidFuzz/index.html

---

## Technical Research Conclusion

### Summary of Key Technical Findings

The research supports a local, quality-gated pipeline. Do not rewrite the application. Preserve the CLI and caches, then make quality explicit with normalized candidates, structured quality signals, review decisions, and generation reports.

### Strategic Technical Impact Assessment

This approach gives CampfireSongbookBuilder a credible path from "fetch and generate documents" to "generate a songbook I trust enough to print." It also gives future AI agents stable contracts and tests, which reduces implementation drift.

### Next Steps Technical Recommendations

1. Run `bmad-create-architecture` using this research plus the PRD.
2. Record ADRs for state format, quality contracts, Markdown/PDF strategy, and dependencies.
3. Run `bmad-create-epics-and-stories`.
4. Use implementation stories that each preserve cache compatibility and add focused regression tests.

**Technical Research Completion Date:** 2026-05-19  
**Research Period:** current comprehensive technical analysis  
**Source Verification:** Technical facts cited with current public sources  
**Technical Confidence Level:** High for architecture direction; medium for final quality thresholds until tested against real cache samples
