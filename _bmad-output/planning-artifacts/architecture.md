---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md
  - _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/addendum.md
  - _bmad-output/implementation-artifacts/all-epics-retro-2026-05-20.md
  - _bmad-output/project-context.md
  - docs/index.md
workflowType: 'architecture'
project_name: 'CampfireSongbookBuilder'
user_name: 'Dicky'
date: '2026-05-20'
lastStep: 8
status: 'complete'
completedAt: '2026-05-20'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

The new roadmap slice defines 12 functional requirements across five product areas:

- document neatness evaluation for Markdown and `.docx` outputs
- agentic verification before manual review
- per-song Lyrics and Chords/Tab quality scoring
- backup-first direct agent remediation
- remediation provenance and escalation controls

Architecturally, these requirements move the project from passive quality filtering into an active verification-and-remediation pipeline. The system must now evaluate content, evaluate generated artifacts, decide whether automation is allowed to act, preserve pre-edit state, and expose the whole chain in local inspectable artifacts.

**Non-Functional Requirements:**

The main architectural drivers are:

- preserve repo-root CLI behavior
- preserve exact content identity
- keep verification deterministic where practical
- keep outputs, backups, and audit files inspectable
- keep tests agent-operable
- preserve backup safety before direct edits

These requirements strongly constrain the solution toward local deterministic workflows rather than hosted or opaque automation.

**Scale & Complexity:**

- Primary domain: brownfield Python CLI / local content-processing and verification pipeline
- Complexity level: medium
- Estimated architectural components: 11 to 14

The complexity comes less from scale and more from state correctness: scores, backups, provenance, remediation attempts, escalation boundaries, and output verification all need to stay aligned with exact content identity.

### Technical Constraints & Dependencies

- The existing runtime is a single-process Python CLI invoked as `python3 main.py` from the repository root.
- Existing JSONL cache semantics and exact `artist` / `title` identity are compatibility constraints.
- The project should remain flat-module and local-file based.
- Existing document generation already produces Markdown, `.docx`, and optional PDF.
- The next slice should prefer deterministic local rules and existing infrastructure over new paid or hosted services.
- Agent remediation is allowed only with backup-first safety.
- The slice resolves the state-management fork in favor of a remediated current-state layer above raw caches; canonical raw caches remain immutable fetched snapshots.

### Cross-Cutting Concerns Identified

- content identity and content-hash versioning
- deterministic score computation
- artifact-level neatness verification
- backup and rollback safety
- remediation provenance
- bounded retry / escalation control
- integration of scoring with existing Quality Signals
- compatibility with offline generation and current reporting flows
- automated testability of agentic verification and remediation behavior

## Starter Template Evaluation

### Primary Technology Domain

Brownfield Python CLI / local content-processing and verification pipeline based on project requirements analysis.

### Starter Options Considered

**Existing brownfield Python CLI scaffold**

- Matches the current repo-root execution model: `python3 main.py`
- Preserves flat `app/*.py` helper boundaries
- Preserves JSONL cache semantics, local file state, and current output pipeline
- Best fits the new PRD because the work is an extension of the current quality/review pipeline, not a platform rewrite

**Typer-based CLI modernization**

- Current PyPI release verified: `typer 0.24.1`
- Would provide a more modern typed CLI experience
- Rejected as the starter foundation for this slice because it changes CLI ergonomics without directly solving scoring, verification, backup, or remediation architecture

**Hatch / modern packaging scaffold**

- Current PyPI release verified: `hatch 1.16.5`
- Current packaging guidance continues to center `pyproject.toml`
- Useful for future packaging/project-management modernization
- Rejected as the starter foundation for this slice because it broadens the change surface without addressing the core runtime architecture problem

### Selected Starter: Existing Brownfield Python CLI Scaffold

**Rationale for Selection:**

The current repository is the right architectural foundation. This roadmap slice extends an already working local-first CLI system with new verification, scoring, remediation, and audit capabilities. Replacing the starter would optimize packaging or CLI aesthetics instead of the actual product risk.

**Initialization Command:**

```bash
# No new starter initialization command.
# Continue implementation from the existing repository root.
python3 main.py --generate-from-cache
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
Python CLI with repo-root execution via `python3 main.py`.

**Styling Solution:**
No UI styling system. Presentation concerns remain document-format and output-layout concerns, not web styling concerns.

**Build Tooling:**
No new build foundation required for this slice. Existing `requirements.txt` and direct Python execution remain sufficient.

**Testing Framework:**
Continue with `unittest` and repo-root test execution:
`python3 -m unittest discover -s tests -p 'test_*.py'`

**Code Organization:**
Preserve flat helper modules under `app/`. New work should likely land as focused modules for:
- document verification
- score computation
- remediation backup/provenance
- remediation orchestration

**Development Experience:**
The current scaffold already supports incremental, test-first brownfield extension. Future packaging modernization remains possible, but is not required for this architecture slice.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**

- Preserve raw JSONL caches as immutable fetched-content records
- Add a separate remediated current-state layer instead of overwriting raw caches directly
- Add separate current-state score storage for per-song Lyrics and Chords/Tab quality
- Add separate document-verification result storage for generated artifacts
- Add append-only remediation-attempt history plus explicit backup references
- Enforce bounded remediation attempts before human escalation

**Important Decisions (Shape Architecture):**

- Treat document neatness as heuristic and deterministic in v1
- Compose scores from existing Quality Signals plus new verification/remediation signals
- Keep verification and remediation local-file based, not service-based
- Keep remediation orchestration inside the CLI/helper pipeline rather than introducing a queue or daemon
- Treat review-ready as a machine-readable gate state, not just a human summary line

### Policy Defaults Resolved for V1

- Use a deterministic `0-100` integer quality score scale for Lyrics and Chords/Tab.
- Use threshold bands:
  - `85-100` = `clean`
  - `60-84` = `reviewable`
  - `40-59` = `questionable`
  - `0-39` = `poor`
- Target automatic remediation for content scoring below `60`.
- Treat document neatness as an artifact-level review gate informed by per-song-block heuristics.
- Store backup artifacts under `data/review/backups/`.
- Store remediation audit and provenance records under `data/review/audit/`.
- Freeze the `codex exec` remediation allowlist to:
  - whitespace normalization
  - section restructuring without semantic rewrite
  - removal of obvious scraper residue
  - normalization or removal of repeated junk blocks
- Set the automatic remediation retry limit to `2` attempts per content item before escalation.

**Deferred Decisions (Post-MVP):**

- Semantic or model-driven rewrite strategies
- GUI review/remediation tooling
- Cloud or multi-user workflow
- Packaging/toolchain modernization such as Hatch migration
- Schema-framework adoption unless explicit validation burden justifies it

### Data Architecture

**Decision: Preserve raw caches as immutable fetched-content records.**

Rationale:

- Existing JSONL caches are compatibility contracts.
- Raw fetched content is useful as the authoritative pre-remediation snapshot.
- Overwriting raw caches would blur provenance and weaken rollback safety.

**Decision: Add a remediated current-state layer above raw caches.**

Rationale:

- Backup-first safety is stronger if remediated content is not stored in the same files as fetched content.
- A separate layer makes before/after comparison straightforward.
- It reduces the risk of agents silently mutating canonical fetched data.

**Proposed current-state files:**

- `data/review/content_scores.json`
- `data/review/remediated_content.json`
- `data/review/document_quality.json`
- `data/review/backups/` for preserved pre-remediation artifacts or content snapshots
- `data/review/audit/remediation_attempts.jsonl` for append-only remediation audit and provenance history

**Decision: Keep current-state and history separate.**

Rationale:

- Current-state files support fast generation and reporting reads.
- Append-only history supports auditability and debugging.
- This matches the successful pattern already used for review decisions and source attempts.

### Authentication & Security

**Decision: No user authentication layer for this slice.**

Rationale:

- This remains an internal local CLI workflow.
- The relevant safety issue is not access control; it is controlled automated mutation.

**Decision: Use policy-based remediation safety rather than auth-based safety.**

Rationale:

- The key guardrails are:
  - backup required before write
  - bounded retry count
  - explicit remediation reason
  - escalation when thresholds are not met
- These controls fit the actual product risk better than adding auth infrastructure.

### API & Communication Patterns

**Decision: No new network API boundary for MVP.**

Rationale:

- This slice is an internal extension of the local pipeline.
- Adding REST or GraphQL would add architectural surface without solving the core problem.

**Decision: Machine-readable local reports are the main communication contract.**

Rationale:

- Agentic tests and remediation workflows need stable, local, inspectable contracts.
- JSON outputs fit the current architecture and the existing review/reporting style.

**Decision: Verification and remediation should plug into existing report flow.**

Rationale:

- Duplicating report pathways would create drift.
- The reporting layer should unify:
  - content-quality state
  - score state
  - document neatness state
  - remediation attempts
  - escalation reasons

### Frontend Architecture

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
12 areas where AI agents could make incompatible choices if not explicitly constrained

### Naming Patterns

**Data File Naming Conventions:**
- Current-state JSON files use `snake_case` names under `data/review/`
- Append-only history files use `*.jsonl`
- Backup directories use noun-based paths, for example `data/review/backups/`
- Remediated current-state files must distinguish content type and role by field, not by ad hoc filename variants

**Identity Naming Conventions:**
- Song identity remains exact:
  - `artist`
  - `title`
  - `song_key`
- Content domains remain exact:
  - `lyrics`
  - `chords`
- Score fields use explicit names:
  - `quality_score`
  - `score_version`
  - `score_reasons`
- Verification fields use explicit names:
  - `review_ready`
  - `verification_status`
  - `verification_reasons`

**Code Naming Conventions:**
- New helper modules remain flat under `app/`
- Function names remain straightforward and descriptive
- State loaders/savers use explicit verbs:
  - `load_*`
  - `save_*`
  - `build_*`
  - `evaluate_*`
  - `apply_*`
- Do not introduce parallel synonyms for the same concept:
  - use `remediation`, not alternating between `repair`, `fixup`, and `cleanup` as top-level state terms

### Structure Patterns

**Project Organization:**
- Raw fetched content stays in existing JSONL cache files
- Current-state review and verification data stays under `data/review/`
- Named selections remain under `data/selections/`
- Favourite membership remains in `data/src/CampfireSongs.csv`
- Tests remain in `tests/test_*.py`

**State Layering Rules:**
- Raw cache = immutable fetched snapshot
- Remediated content = separate current-state layer
- Scores = separate current-state layer
- Verification results = separate current-state layer
- Remediation attempts = append-only history
- Backups = explicit preserved pre-edit state

**Module Ownership Pattern:**
- `app/cache.py` owns raw cache read/write semantics
- `app/quality_assessment.py` owns deterministic signal generation
- new score module should own score derivation only
- new verification module should own document neatness evaluation only
- new remediation module should own backup-first transformation orchestration
- `app/reporting.py` remains the aggregation layer for machine-readable run outputs

### Format Patterns

**Data Exchange Formats:**
- Use `snake_case` in all new JSON and JSONL structures
- Preserve exact `song_key` derivation rules from current architecture
- Use `sha256:<hex>` content-hash format for version binding
- Use explicit status enums rather than free-form prose where a field is machine-consumed

**Current-State Record Pattern:**
Each new current-state record should follow this shape discipline:
- identity fields first
- state/result fields second
- reasons/signals next
- metadata timestamps last

Example pattern:
- `song_key`
- `content_type`
- `content_hash`
- `quality_score`
- `quality_band`
- `review_ready`
- `score_reasons`
- `updated_at`

**History Record Pattern:**
Append-only remediation history records should include:
- identity
- pre-change reference
- post-change reference
- remediation action
- outcome
- escalation flag
- retry_count
- timestamp

### Communication Patterns

**Reporting Contract:**
- Human-readable summaries must be derived from machine-readable report state, not the other way around
- Verification failures, score failures, remediation failures, and escalation outcomes must remain distinct in the report
- Reports must not collapse document-level and content-level failures into one generic `quality issue`

**Escalation Contract:**
- Escalation reasons must be encoded as stable machine-readable categories
- Human-facing explanations may elaborate, but the category must remain explicit
- Agents must not silently treat `not fixable` and `not allowed to fix` as the same state

### Process Patterns

**Remediation Process Pattern:**
1. Load current content state
2. Create backup reference before modification
3. Apply bounded remediation
4. Recompute content hash
5. Re-score content
6. Re-run relevant verification
7. Record remediation attempt
8. Escalate if thresholds still fail or retry bound is reached

**Verification Process Pattern:**
- Verification runs after generation and after remediation where relevant
- Document verification evaluates generated artifacts, not just source content
- Review-ready state is computed, not hand-set
- Agentic tests consume the same verification outputs used by reports

**Retry and Escalation Pattern:**
- Remediation attempts must be bounded per content item
- Retry count must be explicit and persisted
- Once the retry bound is reached, the item must escalate
- Escalated items must remain inspectable and not be silently suppressed

### Enforcement Guidelines

**All AI Agents MUST:**
- preserve raw cache immutability
- create backup state before direct content edits
- preserve exact `artist` / `title` / `song_key` identity semantics
- use `snake_case` in all new machine-readable records
- keep current-state and append-only history separate
- write new behavior into focused helper modules rather than broadening `main.py`

**Pattern Enforcement:**
- Enforce through focused `unittest` coverage on loaders, writers, scoring, verification, remediation, and escalation
- Treat report shape as a compatibility contract
- Document pattern violations in story review findings and correct them before expanding the surface area

### Pattern Examples

**Good Examples:**
- raw cache unchanged, remediated content stored separately
- score recalculated after remediation and tied to current content hash
- document verification stored with explicit artifact identity and pass/fail reasons
- remediation attempt recorded in append-only history with before/after references

**Anti-Patterns:**
- overwriting raw fetched cache content without preserved backup
- storing scores only in prose reports
- mixing current-state records and history in the same file
- using ad hoc field names for the same concept across modules
- silently retrying remediation without persisted attempt tracking

## Project Structure & Boundaries

### Requirements Mapping

**FR Category: Document Neatness Evaluation -> `app/document_verification.py` + `data/review/document_quality.json`**

- Evaluates Markdown and `.docx` outputs for readability and wasted whitespace
- Uses per-song-block heuristics only as contributing signals to an artifact-level review gate
- Produces deterministic artifact-level verification results
- Feeds review-ready gate and report aggregation

**FR Category: Agentic Verification Before Manual Review -> `app/review_gate.py` + `app/reporting.py`**

- Computes whether a run is review-ready before asking for human inspection
- Unifies score results, neatness verification, remediation outcomes, and escalation state
- Exposes machine-readable gate decisions to tests and reports

**FR Category: Per-Song Lyrics/Chords Quality Scoring -> `app/content_scoring.py` + `data/review/content_scores.json`**

- Computes deterministic quality scores per song and content type
- Composes with existing `app/quality_assessment.py` signals
- Tracks score version, reasons, and current content hash

**FR Category: Backup-First Agent Remediation -> `app/remediation.py` + `app/remediation_state.py` + `data/review/backups/` + `data/review/remediated_content.json`**

- Creates explicit backup state before direct edits
- Stores remediated current-state content separately from raw cache content
- Records bounded remediation attempts and resulting state transitions

**FR Category: Audit and Escalation Controls -> `app/remediation_state.py` + `data/review/audit/remediation_attempts.jsonl` + `app/reporting.py`**

- Persists append-only remediation history
- Encodes escalation reasons and retry exhaustion
- Keeps audit state available for tests, reports, and manual inspection

### Complete Project Directory Structure

```text
CampfireSongbookBuilder/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── .flake8
├── main.py
├── clean_chords_cache.py
├── clean_chords_cache_brackets.py
├── fix_mojibake_in_cache.py
├── migrate_cache_to_jsonl.py
├── app/
│   ├── __init__.py
│   ├── cache.py
│   ├── content_models.py
│   ├── document_creation.py
│   ├── document_formatting.py
│   ├── document_generation.py
│   ├── fetch_data.py
│   ├── generation_filtering.py
│   ├── load_config.py
│   ├── load_songs.py
│   ├── pdf_generation.py
│   ├── quality_assessment.py
│   ├── reporting.py
│   ├── review_state.py
│   ├── selection_state.py
│   ├── song_info.py
│   ├── source_attempts.py
│   ├── text_cleaning.py
│   ├── content_scoring.py
│   ├── document_verification.py
│   ├── remediation.py
│   ├── remediation_state.py
│   └── review_gate.py
├── data/
│   ├── src/
│   │   └── CampfireSongs.csv
│   ├── config/
│   │   ├── config.json
│   │   └── config.example.json
│   ├── cache/
│   │   ├── lyrics_cache.jsonl
│   │   └── chords_cache.jsonl
│   ├── selections/
│   │   └── *.json
│   ├── output/
│   │   ├── Lyrics_Document.docx
│   │   ├── Chords_Document.docx
│   │   ├── Lyrics_Document.md
│   │   ├── Chords_Document.md
│   │   └── pdf/
│   ├── reports/
│   │   ├── quality/
│   │   └── verification/
│   └── review/
│       ├── content_scores.json
│       ├── remediated_content.json
│       ├── document_quality.json
│       ├── audit/
│       │   └── remediation_attempts.jsonl
│       └── backups/
│           ├── content/
│           └── artifacts/
├── tests/
│   ├── docx_stub.py
│   ├── test_cache.py
│   ├── test_config.py
│   ├── test_content_models.py
│   ├── test_document_creation.py
│   ├── test_generation_filtering.py
│   ├── test_load_songs.py
│   ├── test_main.py
│   ├── test_quality_assessment.py
│   ├── test_reporting.py
│   ├── test_review_state.py
│   ├── test_selection_state.py
│   ├── test_source_attempts.py
│   ├── test_source_retry.py
│   ├── test_content_scoring.py
│   ├── test_document_verification.py
│   ├── test_remediation.py
│   ├── test_remediation_state.py
│   └── test_review_gate.py
├── docs/
│   ├── index.md
│   ├── architecture.md
│   ├── component-inventory.md
│   ├── development-guide.md
│   ├── project-overview.md
│   ├── project-scan-report.json
│   └── source-tree-analysis.md
├── _bmad/
└── _bmad-output/
```

### Architectural Boundaries

**Entry Point Boundary:**
- `main.py` remains a thin orchestrator
- CLI parsing, run-mode selection, and top-level error handling stay here
- Business logic must remain in `app/*.py` helpers

**Raw Content Boundary:**
- `app/cache.py` owns read/write access to `data/cache/*.jsonl`
- Raw cache files are immutable fetched snapshots from the perspective of this slice
- No remediation logic writes back into raw cache files

**Current-State Review Boundary:**
- `app/remediation_state.py` owns `data/review/` loaders and writers
- `data/review/remediated_content.json` is the highest-priority current-state content layer for generation and scoring
- `data/review/content_scores.json` stores current deterministic score state
- `data/review/document_quality.json` stores artifact verification state
- `data/review/audit/remediation_attempts.jsonl` stores append-only audit history

**Scoring Boundary:**
- `app/quality_assessment.py` continues to derive low-level content signals
- `app/content_scoring.py` converts those signals into stable quality scores and reasons
- Scoring must not own backup creation, document inspection, or escalation policy

**Document Verification Boundary:**
- `app/document_verification.py` evaluates generated artifacts only
- It does not edit source content
- It emits deterministic neatness findings and review-ready inputs

**Remediation Boundary:**
- `app/remediation.py` owns backup-first transformation orchestration
- It may modify remediated current-state content directly after backup creation
- It must not mutate raw caches
- It must re-score and re-verify after every attempted change

**Review Gate Boundary:**
- `app/review_gate.py` computes machine-readable readiness state
- It combines score thresholds, document neatness, remediation exhaustion, and escalation flags
- It does not generate documents or fetch content

**Reporting Boundary:**
- `app/reporting.py` remains the single aggregation layer for run outputs
- Human-readable summaries derive from machine-readable report state
- Report shape is a compatibility contract for agentic tests

### Service and Data Integration Boundaries

**Generation Flow:**
1. `main.py`
2. `app/load_songs.py` and optional `app/selection_state.py`
3. `app/cache.py` and existing fetch/generation modules
4. `app/remediation_state.py` current-state overlay resolution
5. `app/content_scoring.py`
6. document generation modules
7. `app/document_verification.py`
8. `app/review_gate.py`
9. `app/reporting.py`

**Remediation Flow:**
1. load raw or current remediated content
2. create backup in `data/review/backups/`
3. apply bounded remediation in `app/remediation.py`
4. persist updated current-state content in `data/review/remediated_content.json`
5. recompute score in `data/review/content_scores.json`
6. rerun artifact verification where relevant
7. append remediation history in `data/review/audit/remediation_attempts.jsonl`
8. compute escalation or review-ready state

### Requirement-to-Structure Mapping

**Neat Documents**
- Runtime: `app/document_verification.py`
- State: `data/review/document_quality.json`
- Tests: `tests/test_document_verification.py`

**Agentic Verification Before Manual Review**
- Runtime: `app/review_gate.py`, `app/reporting.py`
- State: `data/reports/verification/`, `data/review/document_quality.json`, `data/review/content_scores.json`
- Tests: `tests/test_review_gate.py`, `tests/test_reporting.py`, `tests/test_main.py`

**Per-Song Quality Scores**
- Runtime: `app/content_scoring.py`, `app/quality_assessment.py`
- State: `data/review/content_scores.json`
- Tests: `tests/test_content_scoring.py`, `tests/test_quality_assessment.py`

**Agentic Improvement with Backups**
- Runtime: `app/remediation.py`, `app/remediation_state.py`
- State: `data/review/remediated_content.json`, `data/review/backups/`, `data/review/audit/remediation_attempts.jsonl`
- Tests: `tests/test_remediation.py`, `tests/test_remediation_state.py`

**Audit Trail and Escalation**
- Runtime: `app/remediation_state.py`, `app/review_gate.py`, `app/reporting.py`
- State: `data/review/audit/remediation_attempts.jsonl`, `data/reports/quality/`
- Tests: `tests/test_remediation_state.py`, `tests/test_review_gate.py`, `tests/test_reporting.py`

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
The architectural decisions are compatible. Raw cache immutability, remediated current-state overlays, backup-first remediation, append-only audit history, and machine-readable reporting work together without contradiction.

**Pattern Consistency:**
Implementation patterns support the decisions well. Naming, layering, retry, escalation, and reporting contracts are aligned with the selected local-file Python CLI architecture.

**Structure Alignment:**
The project structure supports the architecture. The proposed `app/` modules and `data/review/` state layer cleanly map to the new scoring, verification, remediation, and audit responsibilities.

### Requirements Coverage Validation ✅

**Feature Coverage:**
All five feature areas are architecturally supported:
- document neatness evaluation
- agentic verification before manual review
- per-song quality scoring
- backup-first direct remediation
- audit and escalation controls

**Functional Requirements Coverage:**
All functional requirement categories identified in project context are covered by specific modules, state files, and integration flows.

**Non-Functional Requirements Coverage:**
The architecture supports repo-root CLI preservation, exact identity preservation, deterministic verification, inspectable outputs/state, agent-operable tests, and backup safety.

### Implementation Readiness Validation ✅

**Decision Completeness:**
Critical decisions are documented clearly enough to guide implementation agents consistently.

**Structure Completeness:**
The project structure is concrete and specific enough for implementation planning.

**Pattern Completeness:**
The implementation patterns are sufficiently explicit to prevent common agent conflicts around naming, layering, and audit semantics.

### Gap Analysis Results

**Critical Gaps**
- None identified

**Important Gaps**
- Artifact identity rules for document verification records should be specified explicitly

**Nice-to-Have Gaps**
- Add schema appendix for new `data/review/` files
- Add enum appendix for verification and escalation status values

### Validation Issues Addressed

No blocking architectural issues were found. Remaining issues are policy-detail refinements that do not require structural redesign.

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [ ] Performance considerations addressed

**Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

Status: Implementation-ready with one remaining documentation gap.

The architecture is sufficiently complete to guide AI agents through consistent implementation. Remaining gaps are limited to document-verification artifact identity wording rather than unresolved policy defaults.

Not applicable for this slice.

Rationale:

- No GUI is planned.
- Neatness is a document/output concern, not an application UI concern.

### Infrastructure & Deployment

**Decision: Keep local single-process execution as the operating model.**

Rationale:

- The current architecture is already aligned with the PRD.
- Verification and remediation can be implemented as additional orchestration steps and helper modules.

**Decision: Expand automated verification through `unittest` and agent-consumable report checks.**

Rationale:

- This directly serves the requirement that agentic tests verify quality before manual inspection.
- It preserves the current developer workflow and repo-root execution model.

### Decision Impact Analysis

**Implementation Sequence:**

1. Define score and remediation data contracts
2. Define remediated current-state and backup model
3. Define document-quality verification contract
4. Implement score computation
5. Implement document neatness verification
6. Implement remediation orchestration with bounded retries
7. Integrate verification/remediation results into reporting and generation gates

**Cross-Component Dependencies:**

- Score computation depends on existing Quality Signals and current content identity
- Remediation depends on backup creation and remediated current-state storage
- Document neatness verification depends on generated artifact identity and output pipeline hooks
- Escalation logic depends on scores, neatness checks, remediation history, and retry bounds
- Reporting depends on all of the above staying aligned under exact `song_key` / hash semantics

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
12 areas where AI agents could make incompatible choices if not explicitly constrained

### Naming Patterns

**Data File Naming Conventions:**

- Current-state JSON files use `snake_case` names under `data/review/`
- Append-only history files use `*.jsonl`
- Backup directories use noun-based paths, for example `data/review/backups/`
- Remediated current-state files must distinguish content type and role by field, not by ad hoc filename variants

**Identity Naming Conventions:**

- Song identity remains exact:
  - `artist`
  - `title`
  - `song_key`
- Content domains remain exact:
  - `lyrics`
  - `chords`
- Score fields use explicit names:
  - `quality_score`
  - `score_version`
  - `score_reasons`
- Verification fields use explicit names:
  - `review_ready`
  - `verification_status`
  - `verification_reasons`

**Code Naming Conventions:**

- New helper modules remain flat under `app/`
- Function names remain straightforward and descriptive
- State loaders/savers use explicit verbs:
  - `load_*`
  - `save_*`
  - `build_*`
  - `evaluate_*`
  - `apply_*`
- Do not introduce parallel synonyms for the same concept:
  - use `remediation`, not alternating between `repair`, `fixup`, and `cleanup` as top-level state terms

### Structure Patterns

**Project Organization:**

- Raw fetched content stays in existing JSONL cache files
- Current-state review and verification data stays under `data/review/`
- Named selections remain under `data/selections/`
- Favourite membership remains in `data/src/CampfireSongs.csv`
- Tests remain in `tests/test_*.py`

**State Layering Rules:**

- Raw cache = immutable fetched snapshot
- Remediated content = separate current-state layer
- Scores = separate current-state layer
- Verification results = separate current-state layer
- Remediation attempts = append-only history
- Backups = explicit preserved pre-edit state

**Module Ownership Pattern:**

- `app/cache.py` owns raw cache read/write semantics
- `app/quality_assessment.py` owns deterministic signal generation
- a new score module should own score derivation only
- a new verification module should own document neatness evaluation only
- a new remediation module should own backup-first transformation orchestration
- `app/reporting.py` remains the aggregation layer for machine-readable run outputs

### Format Patterns

**Data Exchange Formats:**

- Use `snake_case` in all new JSON and JSONL structures
- Preserve exact `song_key` derivation rules from current architecture
- Use `sha256:<hex>` content-hash format for version binding
- Use explicit status enums rather than free-form prose where a field is machine-consumed

**Current-State Record Pattern:**

Each new current-state record should follow this shape discipline:

- identity fields first
- state/result fields second
- reasons/signals next
- metadata timestamps last

Example pattern:

- `song_key`
- `content_type`
- `content_hash`
- `quality_score`
- `review_ready`
- `score_reasons`
- `updated_at`

**History Record Pattern:**

Append-only remediation history records should include:

- identity
- pre-change reference
- post-change reference
- remediation action
- outcome
- escalation flag
- timestamp

### Communication Patterns

**Reporting Contract:**

- Human-readable summaries must be derived from machine-readable report state, not the other way around
- Verification failures, score failures, remediation failures, and escalation outcomes must remain distinct in the report
- Reports must not collapse document-level and content-level failures into one generic quality issue

**Escalation Contract:**

- Escalation reasons must be encoded as stable machine-readable categories
- Human-facing explanations may elaborate, but the category must remain explicit
- Agents must not silently treat “not fixable” and “not allowed to fix” as the same state

### Process Patterns

**Remediation Process Pattern:**

1. Load current content state
2. Create backup reference before modification
3. Apply bounded remediation
4. Recompute content hash
5. Re-score content
6. Re-run relevant verification
7. Record remediation attempt
8. Escalate if thresholds still fail or retry bound is reached

**Verification Process Pattern:**

- Verification runs after generation and after remediation where relevant
- Document verification evaluates generated artifacts, not just source content
- Review-ready state is computed, not hand-set
- Agentic tests consume the same verification outputs used by reports

**Retry and Escalation Pattern:**

- Remediation attempts must be bounded per content item
- Retry count must be explicit and persisted
- Once the retry bound is reached, the item must escalate
- Escalated items must remain inspectable and not be silently suppressed

### Enforcement Guidelines

**All AI Agents MUST:**

- preserve raw cache immutability
- create backup state before direct content edits
- preserve exact `artist` / `title` / `song_key` identity semantics
- use `snake_case` in all new machine-readable records
- keep current-state and append-only history separate
- write new behavior into focused helper modules rather than broadening `main.py`

**Pattern Enforcement:**

- Enforce through focused `unittest` coverage on loaders, writers, scoring, verification, remediation, and escalation
- Treat report shape as a compatibility contract
- Document pattern violations in story review findings and correct them before expanding the surface area

### Pattern Examples

**Good Examples:**

- raw cache unchanged, remediated content stored separately
- score recalculated after remediation and tied to current content hash
- document verification stored with explicit artifact identity and pass/fail reasons
- remediation attempt recorded in append-only history with before/after references

**Anti-Patterns:**

- overwriting raw fetched cache content without preserved backup
- storing scores only in prose reports
- mixing current-state records and history in the same file
- using ad hoc field names for the same concept across modules
- silently retrying remediation without persisted attempt tracking
