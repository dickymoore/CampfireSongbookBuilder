---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md
  - _bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/addendum.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/research/technical-campfiresongbookbuilder-quality-review-architecture-and-content-quality-research-2026-05-19.md
  - docs/index.md
workflowType: 'epics-and-stories'
lastStep: 4
status: 'complete'
updatedAt: '2026-05-25'
---

# CampfireSongbookBuilder - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for CampfireSongbookBuilder, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: The system can assess generated Markdown, `.docx`, and PDF outputs for readability, wasted whitespace, and artifact-specific print-hostile structure, and produce a machine-readable document-level quality result for each requested artifact.
FR2: The system can mark generated artifacts as review-ready or not review-ready using configurable neatness thresholds and clear failure reasons.
FR3: The system can gate manual review behind automated document-quality verification and expose those results to agents without scraping human-facing text.
FR4: The system can persist verification outcomes in an inspectable local format that includes pass/fail state, reasons, and artifact identity.
FR5: The system can assign a deterministic, rule-based Lyrics Quality Score to each Song using quality signals such as missing content, junk markup, confidence, readability, and successful cleanup.
FR6: The system can assign a deterministic Chords/Tab Quality Score to each Song using signals specific to playable chord/tab content.
FR7: The system can rank Songs by remediation priority, including worst-score-first reporting and separate prioritization for Lyrics and Chords/Tab when needed.
FR8: Agents can directly improve low-quality Lyrics or Chords/Tab content within bounded, structure-preserving safety rules such as whitespace cleanup, structure normalization, and readability improvements.
FR9: The system can create a backup artifact or reversible record before any direct agent remediation and preserve exact pre-remediation content identity.
FR10: The system can re-run quality scoring and verification after an agent improves content, including before/after state comparison for auditability and downstream reuse.
FR11: The system can record remediation provenance including Song identity, content type, pre-change reference, post-change reference, and remediation reason in inspectable local files.
FR12: The system can enforce escalation boundaries for unresolved quality issues, including bounded remediation attempts, explicit escalation reasons, and clear stop conditions.
FR13: The system can treat PDF as a first-class governed artifact with deterministic verification, separate conversion-versus-verification outcomes, propagated review-ready decisions, and refreshed post-remediation gate results.

### NonFunctional Requirements

NFR1: Existing command flows must remain compatible with `python3 main.py` from the repository root.
NFR2: Quality scoring, backups, remediation, and reporting must preserve exact `artist`, `title`, and `song_key` identity behavior.
NFR3: All new outputs, verification records, scores, backups, and audit files must remain local-file based and human/agent readable.
NFR4: Automated verification and scoring should remain deterministic where practical for the same content snapshot and thresholds.
NFR5: Agentic verification must be runnable without requiring Dicky to manually inspect outputs first.
NFR6: Direct content edits by agents must never happen without a recoverable pre-edit state.
NFR7: Artifact-governance outputs must distinguish generation/conversion failures from verification failures rather than collapsing them into one failure mode.

### Additional Requirements

- Preserve the existing brownfield Python CLI scaffold; no new starter, service layer, hosted workflow, database, or GUI is needed for this slice.
- Continue implementation from the existing repository root and keep `main.py` as a thin orchestrator.
- Preserve flat helper modules under `app/`, with focused ownership across `content_scoring`, `document_verification`, `remediation`, `remediation_state`, `review_gate`, `reporting`, and `pdf_generation`.
- Preserve raw JSONL caches as immutable fetched-content records and keep remediation state separate from raw cache data.
- Store current-state review files under `data/review/`, including `content_scores.json`, `remediated_content.json`, `document_quality.json`, `backups/`, and `audit/remediation_attempts.jsonl`.
- Keep current-state records and append-only history separate so generation/reporting read stable current state while audit trails remain inspectable.
- Use local machine-readable reports as the primary communication contract for agents and tests.
- Compose score computation with existing `app/quality_assessment.py` signals rather than bypassing current quality logic.
- Use a deterministic `0-100` integer quality scale with threshold bands `85-100 clean`, `60-84 reviewable`, `40-59 questionable`, and `0-39 poor`.
- Treat document neatness as a heuristic but deterministic artifact-level review gate, with PDF evaluated through deterministic rendered-output heuristics rather than inherited `.docx` results.
- Treat PDF as a governed artifact type that must produce either a verification result and review-ready decision or a distinct conversion/generation failure outcome.
- Restrict `codex exec` remediation in v1 to bounded, structure-preserving operations such as whitespace normalization, section restructuring without semantic rewrite, removal of obvious scraper residue, and normalization/removal of repeated junk blocks.
- Use an automatic remediation retry limit of `2` attempts per content item before escalation, with persisted retry counts and explicit machine-readable escalation categories.
- Re-score content and rerun relevant verification after every remediation attempt, including PDF gate refresh when regenerated artifacts are in scope.
- Preserve exact naming and data contracts using `snake_case` fields, `lyrics` and `chords` content types, and `sha256:<hex>` content hashes.
- Keep verification, remediation, and reporting compatible with the existing single-process CLI and `unittest` workflow.
- Keep generated outputs and verification/reporting flows aligned with the staged local pipeline: source data, current-state content, generated artifacts, artifact verification, review gating, and reporting.

### UX Design Requirements

No UX Design Specification was found or required for this slice. MVP remains CLI- and report-driven with no GUI in scope.

### FR Coverage Map

FR1: Epic 1 - evaluate generated artifacts for neatness (Markdown and .docx)
FR2: Epic 1 - compute review-ready decisions from thresholds (Markdown and .docx)
FR3: Epic 1 - gate manual review behind automated verification (Markdown and .docx)
FR4: Epic 1 - persist inspectable verification artifacts (Markdown and .docx)
FR5: Epic 2 - score Lyrics quality per song
FR6: Epic 2 - score Chords/Tab quality per song
FR7: Epic 2 - rank songs for review and remediation priority
FR8: Epic 3 - permit bounded agent remediation
FR9: Epic 3 - preserve backups before edits
FR10: Epic 3 - re-score and re-verify after remediation
FR11: Epic 3 - record remediation provenance
FR12: Epic 3 - enforce escalation boundaries and retry limits
FR13: Epic 4 - govern PDF verification and review gates

## Epic List

### Epic 1: Governed Artifact Verification and Review Gates
The user can generate Markdown and `.docx` artifacts, have each requested artifact evaluated for review readiness, and receive machine-readable verification and gate outcomes before manual inspection.
**FRs covered:** FR1, FR2, FR3, FR4

### Epic 2: Per-Song Quality Scoring and Prioritized Review
The user can see deterministic Lyrics and Chords/Tab quality scores, understand why a song is weak, and prioritize review or remediation work by the worst items first.
**FRs covered:** FR5, FR6, FR7

### Epic 3: Safe Agent Remediation and Re-Evaluation
Agents can improve low-quality content within bounded rules, preserve backups and provenance, re-score and re-verify outcomes, and escalate unresolved issues with explicit stop conditions.
**FRs covered:** FR8, FR9, FR10, FR11, FR12

### Epic 4: PDF Output Verification and Agentic Quality Gates
PDF becomes a first-class governed artifact with its own verification records, neatness heuristics, review-ready decisions, reporting propagation, and post-regeneration refresh behavior.
**FRs covered:** FR13 (plus FR1-FR4 as applied to PDF)

## Epic 1: Governed Artifact Verification and Review Gates

The user can generate Markdown and `.docx` artifacts, have each requested artifact evaluated for review readiness, and receive machine-readable verification and gate outcomes before manual inspection.

### Story 1.1: Produce Inspectable Document Verification Records

As a songbook operator,
I want each generated artifact to emit a machine-readable verification record,
So that agents and reports can inspect artifact quality state without scraping console output.

**Acceptance Criteria:**

**Given** a generation run produces Markdown or `.docx` output
**When** document verification runs
**Then** a local verification record is written with artifact identity, artifact type, verification status, reasons, and timestamp
**And** the record format is stable and human/agent readable.

**Given** a generation run produces a Markdown or `.docx` artifact
**When** document verification runs
**Then** a local verification record is written with artifact identity, artifact type, verification status, reasons, and timestamp
**And** the record format is stable and human/agent readable.

### Story 1.2: Evaluate Artifact Neatness with Deterministic Heuristics

As a songbook operator,
I want generated artifacts checked for whitespace waste and print-hostile layout,
So that poor-quality outputs are detected before review.

**Acceptance Criteria:**

**Given** a generated Markdown or `.docx` artifact
**When** neatness evaluation runs
**Then** the system checks deterministic heuristics such as excessive whitespace, sparse layout, song fragmentation, or other obvious print-hostile structure
**And** the resulting reasons are recorded in the verification output.

**Given** the same artifact bytes and threshold configuration
**When** verification is rerun
**Then** the same result is produced
**And** threshold values remain isolated from unrelated generation logic.

### Story 1.3: Compute Review Ready Gate Decisions

As a reviewer,
I want the system to decide whether each artifact is ready for manual inspection,
So that I only open outputs that already meet the minimum presentation standard.

**Acceptance Criteria:**

**Given** an artifact passes configured neatness thresholds
**When** review readiness is computed
**Then** the artifact is marked review-ready
**And** the decision is persisted in machine-readable form.

**Given** an artifact fails one or more neatness checks
**When** review readiness is computed
**Then** the artifact is marked not review-ready
**And** the persisted result includes explicit failure reasons.

**Given** a run includes Markdown and `.docx` artifacts
**When** review readiness is computed
**Then** each artifact receives its own review-ready decision
**And** `.docx` is not inferred solely from Markdown.

### Story 1.4: Gate Manual Review and Reporting on Verification Results

As a reviewer,
I want automated verification results to drive reporting and review gating,
So that failed artifacts are surfaced before any manual inspection step.

**Acceptance Criteria:**

**Given** a run includes artifacts that failed verification
**When** reporting or review gating runs
**Then** those artifacts are clearly identified as blocked from manual review
**And** the output distinguishes document-verification failure from song-content quality issues.

**Given** an agent or automated test consumes verification output
**When** it reads the local verification artifacts and related run-state files
**Then** it can determine pass/fail state, review-ready state, and failure category without parsing human-facing summary text.

### Story 1.5: Refresh Artifact Gates After Regeneration or Re-Verification

As a songbook operator,
I want artifact gate outcomes refreshed after regeneration or follow-up verification,
So that escalation and downstream workflows use current evidence rather than stale state.

**Acceptance Criteria:**

**Given** a regeneration or follow-up verification pass updates one or more artifacts
**When** artifact verification reruns
**Then** the latest verification and review-ready results replace stale current-state outcomes
**And** artifact identity remains explicit.

**Given** unchanged artifacts are rechecked
**When** the same thresholds and artifact bytes are used
**Then** the verification outcome remains deterministic.

## Epic 2: Per-Song Quality Scoring and Prioritized Review

The user can see deterministic Lyrics and Chords/Tab quality scores, understand why a song is weak, and prioritize review or remediation work by the worst items first.

### Story 2.1: Persist Deterministic Lyrics and Chords Quality Scores

As a songbook operator,
I want each Song to receive persisted Lyrics and Chords quality scores,
So that content quality can be measured consistently across runs.

**Acceptance Criteria:**

**Given** a Song with current lyrics or chords content
**When** scoring runs
**Then** the system writes a deterministic score record for each relevant `content_type`
**And** each record preserves exact `artist`, `title`, `song_key`, `content_hash`, `quality_score`, `quality_band`, `score_version`, and `score_reasons`.

**Given** the same content snapshot and threshold configuration
**When** scoring is rerun
**Then** the same score outcome is produced
**And** the score uses the deterministic `0-100` v1 scale with threshold bands `85-100 clean`, `60-84 reviewable`, `40-59 questionable`, and `0-39 poor`.

**Given** score state is stored for generation and reporting
**When** downstream workflows read the current-state files
**Then** the score records remain human/agent readable
**And** they do not require scraping prose reports.

### Story 2.2: Compose Scores from Existing Quality Signals

As a maintainer of the review pipeline,
I want score computation to reuse existing quality-assessment signals,
So that the new scoring layer builds on current behavior instead of duplicating or bypassing it.

**Acceptance Criteria:**

**Given** existing quality signals for missing content, junk markup, confidence, readability, or cleanup outcomes
**When** score computation runs
**Then** the score result is derived from those signals plus any new deterministic rules required for this slice
**And** the scoring module remains separate from backup creation, document verification, and escalation policy.

**Given** Lyrics and Chords/Tab have different failure modes
**When** score computation runs
**Then** Lyrics and Chords/Tab can produce different scores and reason sets
**And** both remain inspectable in the same local-file state model.

**Given** a content item contains exact identity fields and current content hash
**When** score output is written
**Then** the score remains bound to the correct content snapshot
**And** stale scores can be distinguished from current ones.

### Story 2.3: Rank Songs for Review and Remediation Priority

As a reviewer,
I want reports to highlight the worst Songs first,
So that I can focus attention on the content most likely to need cleanup or escalation.

**Acceptance Criteria:**

**Given** a set of scored Songs
**When** prioritization output is generated
**Then** Songs can be sorted or grouped by worst score first
**And** the output can distinguish Lyrics and Chords/Tab priority when they differ for the same Song.

**Given** high-scoring clean Songs and low-scoring weak Songs
**When** the priority report is viewed by a human or agent
**Then** weak Songs are surfaced as primary remediation targets
**And** clean Songs are not emphasized unless explicitly requested.

### Story 2.4: Surface Reasoned Score Outputs for Review

As a reviewer,
I want quality scores to include the reasons why a song is weak,
So that I can decide quickly whether a song needs manual review or remediation.

**Acceptance Criteria:**

**Given** a Song receives a Lyrics or Chords/Tab quality score
**When** the score record is produced
**Then** the output includes machine-readable `score_reasons` explaining the main quality signals that drove the result
**And** the reasons are specific enough to guide remediation targeting.

**Given** a Song has both Lyrics and Chords/Tab state
**When** review data is inspected
**Then** the reasons for each `content_type` remain separate
**And** the system does not collapse distinct failure modes into one generic quality label.

**Given** a content item is missing, poor, or questionable
**When** the score record is read by an agent or human
**Then** the reason set clearly reflects the relevant failure conditions
**And** the result is usable without reading raw cache content first.

## Epic 3: Safe Agent Remediation and Re-Evaluation

Agents can improve low-quality content within bounded rules, preserve backups and provenance, re-score and re-verify outcomes, and escalate unresolved issues with explicit stop conditions.

### Story 3.1: Create Backup-First Remediation State and Provenance Records

As a songbook operator,
I want every remediation attempt to preserve the pre-edit state and provenance,
So that agentic cleanup remains reversible and auditable.

**Acceptance Criteria:**

**Given** a Song content item is selected for remediation
**When** a remediation attempt begins
**Then** the system creates a backup artifact or reversible record before any edit becomes current
**And** the backup preserves exact Song identity, content type, and pre-remediation content reference under `data/review/backups/`.

**Given** a remediation attempt completes or fails
**When** provenance is recorded
**Then** the audit record includes Song identity, `content_type`, pre-change reference, post-change reference when present, remediation reason, outcome, and timestamp
**And** current-state records remain separate from append-only remediation history stored under `data/review/audit/`.

**Given** a failure occurs during remediation
**When** state is inspected afterward
**Then** the pre-edit backup remains recoverable
**And** the current-state result does not become ambiguous.

### Story 3.2: Run Bounded Agentic Cleanup Through Codex Exec

As an operator delegating cleanup to agents,
I want low-quality content to be remediated through a bounded `codex exec` path,
So that agentic cleanup can improve content automatically without unconstrained rewriting.

**Acceptance Criteria:**

**Given** a Song content item falls below the configured remediation threshold and the issue type is allowed for v1 cleanup
**When** remediation is invoked
**Then** the system can launch a `codex exec` remediation step against the backed-up current-state content
**And** the allowed transformation scope is limited to whitespace normalization, section restructuring without semantic rewrite, removal of obvious scraper residue, and normalization or removal of repeated junk blocks.

**Given** a remediation candidate would require semantic rewriting, musical reinterpretation, or changes outside the allowed bounded scope
**When** the `codex exec` path evaluates the candidate
**Then** the system refuses automatic cleanup for that item
**And** the item is marked for escalation or manual review instead of being silently modified.

**Given** remediation is allowed and executed
**When** the attempt is recorded
**Then** the system marks that the content was agent-modified
**And** the recorded reason explains why the attempt was made.

### Story 3.3: Re-Score and Re-Verify After Agentic Cleanup

As a reviewer,
I want remediated content to be re-evaluated automatically,
So that post-cleanup quality gains or failures are measurable before further action is taken.

**Acceptance Criteria:**

**Given** a remediation attempt changes the current-state content
**When** the attempt completes
**Then** the system recomputes the content hash, re-scores the affected Lyrics or Chords item, and reruns any relevant document or review verification
**And** before-and-after state is preserved for auditability.

**Given** remediation affects a run that produces downstream artifacts including PDF
**When** post-remediation verification runs
**Then** relevant artifact gate outcomes are refreshed using current evidence
**And** stale verification results are not left in place.

**Given** a remediation attempt does not improve the relevant score or verification outcome
**When** post-remediation evaluation is recorded
**Then** the result clearly indicates that the item remains below threshold
**And** downstream gating can treat the item as unresolved.

### Story 3.4: Enforce Retry Limits and Escalation Boundaries

As a reviewer,
I want automatic remediation attempts to stop after bounded retries,
So that agents do not loop indefinitely on low-quality content and unresolved items are escalated clearly.

**Acceptance Criteria:**

**Given** an item has a persisted remediation-attempt count
**When** another `codex exec` cleanup is considered
**Then** the system checks the configured retry limit of `2` before running a new attempt
**And** items at or beyond the retry limit are escalated without another automatic edit.

**Given** an item is escalated because cleanup is not allowed, not successful, or retry-exhausted
**When** escalation state is recorded
**Then** the output includes an explicit machine-readable escalation category and reason
**And** reports and agents can distinguish `not_allowed_to_fix`, `retry_limit_reached`, and `still_below_threshold` outcomes.

**Given** remediation remains unresolved after post-attempt evaluation
**When** review or reporting workflows inspect the item
**Then** the escalation state is visible in the same local-file workflow
**And** unresolved items are not silently suppressed.

## Epic 4: PDF Output Verification and Agentic Quality Gates

PDF becomes a first-class governed artifact with its own verification records, neatness heuristics, review-ready decisions, reporting propagation, and post-regeneration refresh behavior.

### Story 4.1: Produce Inspectable PDF Verification Records

As a songbook operator,
I want a generated PDF to emit a machine-readable verification record,
So that agents and reports can inspect PDF quality state without scraping console output.

**Acceptance Criteria:**

**Given** a run produces a PDF file successfully
**When** PDF verification runs
**Then** the system writes a local verification record with artifact identity, artifact type `pdf`, verification status, reasons, and timestamp
**And** the record uses the same governed verification state model as other artifact types.

**Given** PDF conversion or generation fails before a file is created
**When** run state is recorded
**Then** the failure is recorded distinctly as a generation/conversion outcome rather than a verification result
**And** downstream agents can distinguish missing-artifact generation failure from failed PDF quality checks.

### Story 4.2: Evaluate PDF Neatness with Deterministic Layout Heuristics

As a reviewer,
I want the system to evaluate generated PDFs for print-hostile structure using deterministic heuristics,
So that PDFs that are clearly not reviewable are blocked before I open them.

**Acceptance Criteria:**

**Given** a run produces a PDF artifact
**When** PDF neatness evaluation runs
**Then** the system applies deterministic rendered-output heuristics such as excessive page count, sparse pages, or text extraction failure
**And** the resulting reasons are recorded in the PDF verification output.

**Given** the same PDF bytes and verification thresholds
**When** PDF verification is rerun
**Then** the same verification outcome is produced
**And** thresholds remain isolated from unrelated generation logic.

### Story 4.3: Gate Manual Review on PDF Verification Results

As a reviewer,
I want the system to compute a review-ready decision for PDF artifacts from their verification results,
So that I only open PDFs that already meet the minimum review threshold.

**Acceptance Criteria:**

**Given** a PDF artifact passes configured PDF neatness thresholds
**When** PDF review readiness is computed
**Then** the PDF is marked review-ready
**And** the decision is persisted in machine-readable form alongside other artifact gate outcomes.

**Given** a PDF artifact fails one or more PDF neatness checks
**When** PDF review readiness is computed
**Then** the PDF is marked not review-ready
**And** the decision includes explicit failure reasons.

### Story 4.4: Propagate PDF Gate Outcomes Through Reporting and Re-Evaluation

As a songbook operator,
I want PDF verification and review-ready outcomes to propagate into reporting and post-change re-evaluation,
So that agents can reason about PDF readiness and refresh it after regeneration or remediation.

**Acceptance Criteria:**

**Given** a run includes a PDF generation/conversion failure
**When** reporting runs
**Then** the output distinguishes generation failure from PDF verification failure
**And** the run state remains machine-readable and inspectable.

**Given** a run includes a PDF that failed verification or is not review-ready
**When** reporting or review gating runs
**Then** the PDF is clearly identified as blocked from manual review
**And** the output distinguishes PDF gate failures from song-content quality issues.

**Given** a regeneration or remediation changes downstream artifacts including PDF
**When** post-change verification runs
**Then** relevant PDF verification and review-ready outcomes are refreshed before escalation or final review decisions
**And** stale PDF gate state is not left in place.
