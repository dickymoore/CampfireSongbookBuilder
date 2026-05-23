---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md
  - _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/addendum.md
  - _bmad-output/planning-artifacts/architecture.md
workflowType: 'epics-and-stories'
status: 'complete'
completedAt: '2026-05-21'
---

# CampfireSongbookBuilder - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for CampfireSongbookBuilder, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: The system can assess generated Markdown and `.docx` outputs for readability and wasted whitespace, and produce a machine-readable document-level quality result for each requested artifact.
FR2: The system can mark generated artifacts as review-ready or not review-ready using configurable neatness thresholds and clear failure reasons.
FR3: The system can gate manual review behind automated document-quality verification and expose those results to agents without scraping human-facing text.
FR4: The system can persist verification outcomes in an inspectable local format that includes pass/fail state, reasons, and artifact identity.
FR5: The system can assign a deterministic, rule-based Lyrics Quality Score to each Song using quality signals such as missing content, junk markup, confidence, readability, and successful cleanup.
FR6: The system can assign a deterministic Chords/Tab Quality Score to each Song using signals specific to playable chord/tab content.
FR7: The system can rank Songs by remediation priority, including worst-score-first reporting and separate prioritization for Lyrics and Chords/Tab when needed.
FR8: Agents can directly improve low-quality Lyrics or Chords/Tab content within bounded, structure-preserving safety rules such as whitespace cleanup, structure normalization, and removal of obvious scraper residue.
FR9: The system can create a backup artifact or reversible record before any direct agent remediation and preserve exact pre-remediation content identity.
FR10: The system can recompute quality scores and rerun relevant verification after remediation, and make before/after state available for auditability.
FR11: The system can record remediation provenance including Song identity, content type, pre-change reference, post-change reference, and remediation reason in inspectable local files.
FR12: The system can enforce escalation boundaries for unresolved quality issues, including bounded remediation attempts, explicit escalation reasons, and clear stop conditions.

### NonFunctional Requirements

NFR1: Existing command flows must remain compatible with `python3 main.py` from the repository root.
NFR2: Quality scoring, backups, remediation, and reporting must preserve exact `artist`, `title`, and `song_key` identity behavior.
NFR3: All new outputs, verification records, scores, backups, and audit files must remain local-file based and human/agent readable.
NFR4: Automated verification and scoring should remain deterministic where practical for the same content snapshot and thresholds.
NFR5: Agentic verification must be runnable without requiring Dicky to manually inspect outputs first.
NFR6: Direct content edits by agents must never happen without a recoverable pre-edit state.

### Additional Requirements

- Preserve the existing brownfield Python CLI scaffold; no new starter, service layer, hosted workflow, database, or GUI is needed for this slice.
- Continue implementation from the existing repository root and keep `main.py` as a thin orchestrator.
- Preserve flat helper modules under `app/`, with new focused modules for content scoring, document verification, remediation, remediation state, and review gating.
- Preserve raw JSONL caches as immutable fetched-content records.
- Introduce a separate remediated current-state layer above raw caches rather than overwriting canonical fetched content directly.
- Keep current-state review data and append-only history separate.
- Use local machine-readable reports as the primary communication contract for agents and tests.
- Compose score computation with existing `app/quality_assessment.py` signals rather than bypassing current quality logic.
- Store current-state review files under `data/review/`, including `content_scores.json`, `remediated_content.json`, `document_quality.json`, `backups/`, and `audit/remediation_attempts.jsonl`.
- Use a deterministic `0-100` integer quality scoring scale with threshold bands: `85-100 clean`, `60-84 reviewable`, `40-59 questionable`, and `0-39 poor`.
- Treat document neatness as a heuristic but deterministic artifact-level v1 review gate for readability, whitespace efficiency, sparse pages, song fragmentation, or similar print-hostile structure, informed by per-song-block heuristics.
- Define review-ready as a computed machine-readable gate state, not just a summary string.
- Restrict `codex exec` remediation to bounded, structure-preserving operations in v1: whitespace normalization, section restructuring without semantic rewrite, removal of obvious scraper residue, and normalization or removal of repeated junk blocks.
- Persist explicit retry counts and escalation categories so agents do not silently loop on the same content.
- Use an automatic remediation retry limit of `2` attempts per content item before escalation.
- Re-score content and rerun relevant verification after every remediation attempt.
- Preserve exact naming and data contracts: `snake_case` fields, `lyrics` and `chords` content types, explicit score and verification fields, and `sha256:<hex>` content hashes.
- Keep verification, remediation, and reporting compatible with the existing single-process CLI and `unittest` workflow.

### UX Design Requirements

No UX Design Specification was found or required for this slice. The PRD and architecture both explicitly exclude a GUI for MVP.

### FR Coverage Map

FR1: Epic 1 - evaluate generated artifacts for neatness
FR2: Epic 1 - decide review readiness from thresholds
FR3: Epic 1 - gate manual review behind automated checks
FR4: Epic 1 - persist inspectable verification artifacts
FR5: Epic 2 - score Lyrics quality per song
FR6: Epic 2 - score Chords/Tab quality per song
FR7: Epic 2 - rank songs by remediation priority
FR8: Epic 3 - permit bounded agent remediation
FR9: Epic 3 - preserve backups before edits
FR10: Epic 3 - re-score and re-verify after remediation
FR11: Epic 3 - record remediation provenance
FR12: Epic 3 - enforce escalation boundaries and retry limits

## Epic List

### Epic 1: Review-Ready Document Quality Gates
The user can generate Markdown and `.docx` artifacts, have them automatically evaluated for neatness and review readiness, and get machine-readable verification results before manual inspection.
**FRs covered:** FR1, FR2, FR3, FR4

### Epic 2: Per-Song Quality Scoring and Prioritization
The user can see deterministic quality scores for Lyrics and Chords/Tab, understand why a song is weak, and prioritize review or remediation work by worst items first.
**FRs covered:** FR5, FR6, FR7

### Epic 3: Safe Agent Remediation Workflow
Agents can improve low-quality content within bounded rules, create backups first, re-score and re-verify afterward, and keep full provenance for every attempted change.
**FRs covered:** FR8, FR9, FR10, FR11, FR12

<!-- Repeat for each epic in epics_list (N = 1, 2, 3...) -->

## Epic 1: Review-Ready Document Quality Gates

The user can generate Markdown and `.docx` artifacts, have them automatically evaluated for neatness and review readiness, and get machine-readable verification results before manual inspection.

### Story 1.1: Produce Inspectable Document Verification Records

As a songbook operator,
I want each generated artifact to produce a machine-readable verification record,
So that agents and reports can inspect document-quality results without scraping console output.

**Traceability:** FR4

**Acceptance Criteria:**

**Given** a generation run produces Markdown or `.docx` output
**When** document verification runs
**Then** a local verification record is written with artifact identity, verification status, reasons, and timestamp
**And** the record format is stable and human/agent readable.

**Given** multiple output artifacts are generated in one run
**When** verification records are created
**Then** each artifact receives its own result entry
**And** the entries remain distinguishable by artifact identity and type.

### Story 1.2: Evaluate Artifact Neatness with Deterministic Heuristics

As a songbook operator,
I want generated artifacts checked for whitespace waste and print-hostile layout,
So that poor-quality outputs are detected before review.

**Traceability:** FR1

**Acceptance Criteria:**

**Given** a generated Markdown or `.docx` artifact
**When** neatness evaluation runs
**Then** the system checks deterministic heuristics such as excessive whitespace, sparse layout, song fragmentation, or other obvious print-hostile structure at the artifact level using per-song-block heuristics as contributing signals
**And** the resulting reasons are recorded in the verification output.

**Given** threshold or heuristic settings need tuning
**When** verification logic is maintained
**Then** threshold values are isolated from unrelated generation code
**And** tuning does not require changing scraper or cache behavior.

### Story 1.3: Compute Review-Ready Gate Decisions

As a reviewer,
I want the system to decide whether an artifact is ready for manual inspection,
So that I only open outputs that already meet the minimum presentation standard.

**Traceability:** FR2

**Acceptance Criteria:**

**Given** an artifact passes configured neatness thresholds
**When** review readiness is computed
**Then** the artifact is marked review-ready
**And** the decision is persisted in machine-readable form.

**Given** an artifact fails one or more neatness checks
**When** review readiness is computed
**Then** the artifact is marked not review-ready
**And** the persisted result includes explicit failure reasons.

### Story 1.4: Gate Manual Review and Reporting on Verification Results

As a reviewer,
I want automated verification results to drive reporting and review gating,
So that failed artifacts are surfaced before any manual inspection step.

**Traceability:** FR3

**Acceptance Criteria:**

**Given** a run includes artifacts that failed verification
**When** reporting or review gating runs
**Then** those artifacts are clearly identified as blocked from manual review
**And** the output distinguishes document-verification failure from song-content quality issues.

**Given** an agent or automated test consumes verification output
**When** it reads the local verification artifacts
**Then** it can determine pass/fail state and reasons without parsing human-facing summary text
**And** the flow remains compatible with the existing CLI workflow.

## Epic 2: Per-Song Quality Scoring and Prioritization

The user can see deterministic quality scores for Lyrics and Chords/Tab, understand why a song is weak, and prioritize review or remediation work by worst items first.

### Story 2.1: Persist Deterministic Per-Song Lyrics and Chords Scores

As a songbook operator,
I want each Song to receive persisted Lyrics and Chords quality scores,
So that content quality can be measured consistently across runs.

**Traceability:** FR5, FR6

**Acceptance Criteria:**

**Given** a Song with current lyrics or chords content
**When** scoring runs
**Then** the system writes a deterministic score record for each relevant `content_type`
**And** each record preserves exact `artist`, `title`, `song_key`, `content_hash`, `quality_score`, `quality_band`, `score_version`, and `score_reasons`.

**Given** the same content snapshot and threshold configuration
**When** scoring is rerun
**Then** the same score outcome is produced
**And** the score uses the deterministic `0-100` v1 scale with threshold bands `85-100 clean`, `60-84 reviewable`, `40-59 questionable`, and `0-39 poor`.

### Story 2.2: Compose Scores from Existing Quality Signals

As a maintainer of the review pipeline,
I want score computation to reuse existing quality-assessment signals,
So that the new scoring layer builds on current behavior instead of duplicating or bypassing it.

**Traceability:** FR5, FR6

**Acceptance Criteria:**

**Given** existing quality signals for missing content, junk markup, confidence, readability, or cleanup outcomes
**When** score computation runs
**Then** the score result is derived from those signals plus any new deterministic rules required for this slice
**And** the scoring module remains separate from backup creation, document verification, and escalation policy.

**Given** Lyrics and Chords/Tab have different failure modes
**When** score computation runs
**Then** Lyrics and Chords/Tab can produce different scores and reason sets
**And** both remain inspectable in the same local-file state model.

### Story 2.3: Rank Songs for Review and Remediation Priority

As a reviewer,
I want reports to highlight the worst Songs first,
So that I can focus attention on the content most likely to need cleanup or escalation.

**Traceability:** FR7

**Acceptance Criteria:**

**Given** a set of scored Songs
**When** prioritization output is generated
**Then** Songs can be sorted or grouped by worst score first
**And** the output can distinguish Lyrics and Chords/Tab priority when they differ for the same Song.

**Given** high-scoring clean Songs and low-scoring weak Songs
**When** the priority report is viewed by a human or agent
**Then** weak Songs are surfaced as primary remediation targets
**And** clean Songs are not emphasized unless explicitly requested.

## Epic 3: Safe Agent Remediation Workflow

Agents can improve low-quality content within bounded rules, create backups first, re-score and re-verify afterward, and keep full provenance for every attempted change.

### Story 3.1: Create Backup-First Remediation State and Provenance Records

As a songbook operator,
I want every remediation attempt to preserve the pre-edit state and provenance,
So that agentic cleanup remains reversible and auditable.

**Traceability:** FR9, FR11

**Acceptance Criteria:**

**Given** a Song content item is selected for remediation
**When** a remediation attempt begins
**Then** the system creates a backup artifact or reversible record before any edit becomes current
**And** the backup preserves exact Song identity, content type, and pre-remediation content reference under `data/review/backups/`.

**Given** a remediation attempt completes or fails
**When** provenance is recorded
**Then** the audit record includes Song identity, content_type, pre-change reference, post-change reference when present, remediation reason, outcome, and timestamp
**And** current-state records remain separate from append-only remediation history stored under `data/review/audit/`.

### Story 3.2: Run Bounded Agentic Cleanup Through Codex Exec

As an operator delegating cleanup to agents,
I want low-quality content to be remediated through a bounded `codex exec` path,
So that agentic cleanup can improve content automatically without unconstrained rewriting.

**Traceability:** FR8

**Acceptance Criteria:**

**Given** a Song content item falls below the configured remediation threshold and the issue type is allowed for v1 cleanup
**When** remediation is invoked
**Then** the system can launch a `codex exec` remediation step against the backed-up current-state content
**And** the allowed transformation scope is limited to whitespace normalization, section restructuring without semantic rewrite, removal of obvious scraper residue, and normalization or removal of repeated junk blocks.

**Given** a remediation candidate would require semantic rewriting, musical reinterpretation, or changes outside the allowed bounded scope
**When** the `codex exec` path evaluates the candidate
**Then** the system refuses automatic cleanup for that item
**And** the item is marked for escalation or manual review instead of being silently modified.

### Story 3.3: Re-Score and Re-Verify After Agentic Cleanup

As a reviewer,
I want remediated content to be re-evaluated automatically,
So that post-cleanup quality gains or failures are measurable before further action is taken.

**Traceability:** FR10

**Acceptance Criteria:**

**Given** a remediation attempt changes the current-state content
**When** the attempt completes
**Then** the system recomputes the content hash, re-scores the affected Lyrics or Chords item, and reruns any relevant document or review verification
**And** before-and-after state is preserved for auditability.

**Given** a remediation attempt does not improve the relevant score or verification outcome
**When** post-remediation evaluation is recorded
**Then** the result clearly indicates that the item remains below threshold
**And** downstream gating can treat the item as unresolved.

### Story 3.4: Enforce Retry Limits and Escalation Boundaries

As a reviewer,
I want automatic remediation attempts to stop after bounded retries,
So that agents do not loop indefinitely on low-quality content and unresolved items are escalated clearly.

**Traceability:** FR12

**Acceptance Criteria:**

**Given** an item has a persisted remediation-attempt count
**When** another `codex exec` cleanup is considered
**Then** the system checks the configured retry limit of `2` before running a new attempt
**And** items at or beyond the retry limit are escalated without another automatic edit.

**Given** an item is escalated because cleanup is not allowed, not successful, or retry-exhausted
**When** escalation state is recorded
**Then** the output includes an explicit machine-readable escalation category and reason
**And** reports and agents can distinguish `not_allowed_to_fix`, `retry_limit_reached`, and `still_below_threshold` outcomes.
