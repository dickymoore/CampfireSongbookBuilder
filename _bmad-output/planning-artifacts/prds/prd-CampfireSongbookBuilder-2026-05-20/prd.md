---
title: CampfireSongbookBuilder Output Quality and Agentic Remediation
status: approved-for-planning
created: 2026-05-20
updated: 2026-05-21
---

# PRD: CampfireSongbookBuilder Output Quality and Agentic Remediation

## 0. Document Purpose

This PRD defines the next internal roadmap slice for CampfireSongbookBuilder after the completion of the quality-upgrade program. It is written for the product owner, future AI agents, architecture workflow owners, and story-generation workflows. It builds on the completed quality-upgrade PRD, the architecture document, and the all-epics retrospective, and focuses on the next problem: making output quality measurable, automatically verifiable, and directly improvable by agents. Assumptions are tagged inline and surfaced again in the Assumptions Index.

## 1. Vision

CampfireSongbookBuilder should not stop at filtering obviously bad content. It should produce songbook outputs that are neat enough to trust at a glance, measurable enough for automated verification, and repairable enough that agents can improve the output before asking Dicky to inspect it.

For this internal slice, “quality” expands beyond missing-content detection. The product should judge whether a generated document is readable, compact, and not wasteful with whitespace; whether each lyrics or chords item is good enough to keep; and whether an agent can safely improve a low-quality item while preserving the original content through a backup path.

The outcome should be a tighter human-in-the-loop workflow: agents score content and documents, run automated checks, attempt bounded fixes when allowed, and only escalate to Dicky when the artifact is already in a substantially reviewable state.

## 2. Target User

### 2.1 Primary Persona

Dicky, acting as an internal operator and reviewer of the songbook-generation workflow. He wants the tool and its agents to do more of the cleanup, verification, and refinement work before he spends attention inspecting outputs manually.

### 2.2 Jobs To Be Done

- Generate songbook documents that are easy to read and do not waste space.
- Know before manual review whether a document is structurally neat enough to inspect.
- See a per-song quality score for lyrics and chords so review effort can focus on the worst items.
- Let agents improve weak content directly, provided the system preserves backups and traceability.

### 2.3 Non-Users (v1)

- End users expecting a polished GUI remediation workflow.
- Users expecting fully autonomous semantic song correction without traceability.
- Users expecting cloud-hosted collaborative review or remote approval flows.

### 2.4 Key User Journeys

- **UJ-1. Dicky generates a compact, readable draft book.** Dicky runs the builder. The system produces Markdown and `.docx` artifacts, evaluates layout quality, and reports whether the document is neat enough for manual inspection. He opens an output that is already readable and not padded with unnecessary whitespace.

- **UJ-2. Dicky sees which songs are weak before reading everything.** Dicky runs a cache-based generation or review pass. The system assigns quality scores to lyrics and chords for each Song, highlights the weakest items first, and gives him a ranked view of what most needs attention.

- **UJ-3. Agents improve low-quality content before escalating.** An agent identifies a low-quality lyrics or chords item, creates a backup, applies a bounded cleanup or restructuring improvement, re-scores the result, and records what changed. Dicky only reviews the post-fix result and its audit trail when needed.

- **UJ-4. Agentic tests gate manual review.** Before Dicky is asked to open a generated document, automated verification checks confirm that output quality thresholds are met or clearly report why they are not. Dicky is not used as the first-line layout checker anymore.

## 3. Glossary

- **Song** — A requested musical item identified by exact `artist` and `title`.
- **Source List** — The canonical input list of Songs in `data/src/CampfireSongs.csv`.
- **Cached Content** — Existing locally stored lyrics or chords/tab records in JSONL cache files.
- **Lyrics Quality Score** — A numeric or ordinal quality score assigned to a Song’s Lyrics.
- **Chords Quality Score** — A numeric or ordinal quality score assigned to a Song’s Chords/Tab.
- **Document Quality Check** — An automated evaluation of generated Markdown or `.docx` output for readability and whitespace efficiency.
- **Neat Document** — A generated document that is readable and avoids unnecessary whitespace. `[ASSUMPTION: This slice should treat “neat” as a measurable layout property rather than a subjective styling preference.]`
- **Agentic Test** — An automated verification step run by an agent or the system before asking Dicky to inspect generated artifacts.
- **Remediation** — A bounded agent-driven improvement to Lyrics, Chords/Tab, or output structure intended to raise quality.
- **Backup Artifact** — A preserved pre-remediation copy or reversible record of content before an agent modifies it.
- **Review Escalation** — The point at which the system asks Dicky to inspect an artifact because automated scoring or remediation could not finish the job safely.

## 4. Features

### 4.1 Document Neatness Evaluation

**Description:** The system evaluates generated songbook outputs for readability and whitespace efficiency so that manual review happens on artifacts that already meet a minimum presentation standard. Realizes UJ-1 and UJ-4.

**Functional Requirements:**

#### FR-1: Evaluate generated documents for neatness

The system can assess generated Markdown and `.docx` outputs for readability and wasted whitespace.

**Consequences (testable):**
- A generation run produces a document-level quality result for each requested output artifact.
- The evaluation checks for excessive whitespace, sparse pages, visually fragmented song layout, or similar print-hostile structure. `[ASSUMPTION: Initial neatness checks can be heuristic rather than page-render-perfect.]`
- The result is stored or reported in a machine-readable form that downstream tests and agents can consume.

#### FR-2: Define neatness thresholds for review readiness

The system can decide whether a generated artifact is ready for human review.

**Consequences (testable):**
- A document that meets the configured threshold is marked review-ready.
- A document that fails is marked not review-ready and includes reasons.
- The threshold logic is configurable or isolated so it can be tuned without rewriting unrelated generation logic.

### 4.2 Agentic Verification Before Manual Review

**Description:** The system adds agent-consumable quality gates so automated checks happen before Dicky is asked to inspect output artifacts. Realizes UJ-4.

**Functional Requirements:**

#### FR-3: Gate manual review behind automated checks

The system can require automated document-quality verification before asking Dicky to inspect output.

**Consequences (testable):**
- A run can fail or warn before human review if document-quality checks do not pass.
- The reporting layer clearly distinguishes automated verification failure from content-quality failure.
- Agentic tests can consume the same machine-readable result without scraping human-facing text.

#### FR-4: Expose agentic verification results in inspectable artifacts

The system can persist agentic verification outcomes in an inspectable local format.

**Consequences (testable):**
- Verification outcomes include pass/fail state, reasons, and artifact identity.
- The results are local-file based and compatible with the current CLI workflow.
- The format is stable enough for AI agents to use in follow-up remediation workflows.

### 4.3 Per-Song Quality Scoring

**Description:** The system assigns quality scores to Lyrics and Chords/Tab for each Song so that review and remediation can be prioritized. Realizes UJ-2 and UJ-3.

**Functional Requirements:**

#### FR-5: Score Lyrics quality per Song

The system can assign a Lyrics Quality Score to each Song.

**Consequences (testable):**
- The score is derived from existing and new quality signals such as missing content, junk markup, confidence, readability, and successful cleanup.
- The score is included in machine-readable outputs and review-facing reports.
- Score calculation is deterministic for the same content snapshot. `[ASSUMPTION: v1 scoring should be deterministic and rule-based, not model-scored.]`

#### FR-6: Score Chords/Tab quality per Song

The system can assign a Chords Quality Score to each Song.

**Consequences (testable):**
- The score reflects existing and new quality signals relevant to playable chord/tab content.
- Chords/Tab scoring can differ from Lyrics scoring when the failure modes differ.
- The score is preserved in a way that agents can use for prioritization and remediation targeting.

#### FR-7: Rank Songs by remediation priority

The system can identify the Songs most in need of improvement.

**Consequences (testable):**
- Reports can sort or group Songs by worst score first.
- The prioritization distinguishes Lyrics and Chords/Tab where needed.
- Clean high-scoring Songs are not surfaced as primary review work unless explicitly requested.

### 4.4 Agentic Content Remediation

**Description:** The system allows agents to improve low-quality content directly, with safety controls, backups, and auditability. Realizes UJ-3.

**Functional Requirements:**

#### FR-8: Permit bounded agent edits to low-quality content

Agents can directly improve low-quality Lyrics or Chords/Tab content within defined safety bounds.

**Consequences (testable):**
- Agents can modify content that falls below configured score thresholds or quality rules.
- Direct remediation is limited to allowed transformation types such as whitespace cleanup, structure normalization, and readability improvements. `[ASSUMPTION: semantic rewrites and musical reinterpretation should remain out of scope for this slice unless explicitly approved later.]`
- The system records that the content was agent-modified and why.

#### FR-9: Preserve backups before remediation

The system can create backups before an agent edits content directly.

**Consequences (testable):**
- A backup artifact or reversible record exists before the modified content becomes current.
- The backup preserves exact pre-remediation content identity.
- Failure during remediation does not destroy the backup or leave the state ambiguous.

#### FR-10: Re-score and re-verify after remediation

The system can re-run quality scoring and verification after an agent improves content.

**Consequences (testable):**
- Post-remediation content gets fresh Lyrics/Chords quality scores.
- Updated document-generation or review workflows can consume the remediated result as the current candidate.
- The system can compare before/after quality state for auditability.

### 4.5 Agent-Friendly Audit and Safety Controls

**Description:** The system keeps remediation and verification inspectable so agents can work autonomously without making the workflow opaque. Realizes UJ-3 and UJ-4.

**Functional Requirements:**

#### FR-11: Record remediation provenance

The system can record what an agent changed and why.

**Consequences (testable):**
- Audit records include Song identity, content type, pre-change reference, post-change reference, and remediation reason.
- Audit data is inspectable through local files rather than hidden internal state.
- Reports can link low-quality content to remediation attempts and results.

#### FR-12: Define escalation boundaries for unresolved quality issues

The system can determine when automated remediation stops and Dicky should be asked to review.

**Consequences (testable):**
- Low-quality content that remains below threshold after remediation is escalated clearly.
- Escalation reasons explain whether the problem is scoring, neatness, remediation failure, or policy restriction.
- Agents are not allowed to silently loop forever on the same bad content. `[ASSUMPTION: v1 should enforce bounded remediation attempts per content item.]`

## 5. Cross-Cutting NFRs

- **NFR-1: Preserve repo-root CLI behavior.** Existing command flows must remain compatible with `python3 main.py` from the repository root.
- **NFR-2: Preserve exact content identity.** Quality scoring, backups, remediation, and reporting must continue to respect exact `artist`, `title`, and `song_key` behavior.
- **NFR-3: Keep outputs and audit files inspectable.** All new state should remain local-file based and human/agent readable.
- **NFR-4: Keep automated verification deterministic where practical.** The same content snapshot and thresholds should produce the same quality outcome.
- **NFR-5: Keep tests agent-operable.** Agentic verification must be runnable without requiring Dicky to manually inspect outputs first.
- **NFR-6: Preserve backup safety.** Direct content edits by agents must never happen without a recoverable pre-edit state.

## 6. Constraints and Guardrails

### Safety

- Agent remediation may edit content directly only if a backup is created first.
- Remediation should favor readability and structure improvement over semantic invention.
- Human escalation remains required for unresolved or policy-blocked content.

### Cost

- This internal slice should prefer local deterministic checks and reuse of existing infrastructure over new paid services. `[ASSUMPTION: no external paid scoring or remediation service is required for v1 of this slice.]`

### Operational Simplicity

- The project should remain a single-process CLI with flat helper modules.
- New behavior should extend the existing review/report/generation pipeline rather than create a parallel product architecture.

## 7. Non-Goals (Explicit)

- Building a GUI remediation dashboard
- Introducing a hosted service, database, or multi-user workflow
- Replacing the current cache identity model
- Adding unconstrained AI rewriting of songs
- Solving perfect pagination or typesetting for every document shape in this slice
- Guaranteeing legal or musicological correctness of agent-edited content

## 8. MVP Scope

### 8.1 In Scope

- Document neatness heuristics and pass/fail review readiness checks
- Machine-readable agentic verification results
- Deterministic per-song Lyrics and Chords/Tab quality scores
- Backup-first direct agent remediation for bounded content improvements
- Before/after scoring and audit trail support
- CLI- and agent-friendly reporting of verification and remediation outcomes

### 8.2 Out of Scope for MVP

- Full WYSIWYG layout optimization
- GUI-based diffing or manual remediation tooling
- Semantic song reconstruction driven purely by generative models
- Cloud review queues or approval routing
- Replacement of the existing document generation stack

## 9. Success Metrics

**Primary**
- **SM-1:** Generated documents intended for review pass automated neatness checks at a materially higher rate than the current baseline. Validates FR-1, FR-2, FR-3.
- **SM-2:** Dicky is no longer asked to inspect documents that have already failed objective layout-quality gates. Validates FR-3, FR-4.
- **SM-3:** Each Song’s Lyrics and Chords/Tab receives a persisted quality score usable for prioritization and reporting. Validates FR-5, FR-6, FR-7.
- **SM-4:** Agents can improve a meaningful subset of low-quality content directly while preserving backups and auditability. Validates FR-8, FR-9, FR-10, FR-11.

**Secondary**
- **SM-5:** Review reports surface the worst Songs first, reducing manual triage effort. Validates FR-7.
- **SM-6:** Escalations to Dicky are more targeted and better explained after automated remediation attempts. Validates FR-12.

**Counter-metrics (do not optimize)**
- **SM-C1:** Do not optimize for aggressive automated rewriting at the expense of content trustworthiness. Counterbalances SM-4.
- **SM-C2:** Do not optimize for whitespace minimization so hard that document readability degrades. Counterbalances SM-1.

## 10. V1 Policy Defaults

### 10.1 Quality Score Scale and Threshold Bands

- Lyrics and Chords/Tab quality scores use a deterministic `0-100` integer scale.
- Threshold bands for v1 are:
  - `85-100`: `clean`
  - `60-84`: `reviewable`
  - `40-59`: `questionable`
  - `0-39`: `poor`
- Default remediation targeting begins below `60`.
- Automatic escalation is required when an item remains below `60` after bounded remediation attempts.

### 10.2 Document Neatness Gate Scope

- Document neatness is an artifact-level review gate.
- The gate may use per-song-block heuristics as contributing signals, but review-ready state is decided at the artifact level rather than by independent per-song document approvals.

### 10.3 Backup and Audit Locations

- Backup artifacts live under `data/review/backups/`.
- Remediation audit and provenance records live under `data/review/audit/`.
- These locations remain local-file based and inspectable by both humans and agents.

### 10.4 Allowed `codex exec` Remediation Operations

- The bounded `codex exec` remediation allowlist for v1 is limited to:
  - whitespace normalization
  - section restructuring without semantic rewrite
  - removal of obvious scraper residue
  - normalization or removal of repeated junk blocks
- Semantic rewriting, musical reinterpretation, lyric invention, and content expansion are not allowed in v1.

### 10.5 Automatic Retry Limit

- The automatic remediation retry limit is `2` attempts per content item before mandatory escalation.

## 10. Open Questions

1. Should score reporting expose only the `0-100` numeric result, or expose both the numeric value and the derived band in all reports?
2. Which exact per-song-block heuristics should contribute to the artifact-level neatness gate in v1?
3. Should remediation update the canonical cache content directly, or create a separate remediated-current-state layer first?
4. Should audit records use one append-only stream per content type or a unified append-only stream under `data/review/audit/`?

## 11. Assumptions Index

- §3 Glossary — “Neat Document” should be treated as a measurable layout property rather than a subjective styling preference.
- §4.1 FR-1 — Initial neatness checks can be heuristic rather than page-render-perfect.
- §4.3 FR-5 — v1 scoring should be deterministic and rule-based, not model-scored.
- §4.4 FR-8 — semantic rewrites and musical reinterpretation should remain out of scope for this slice unless explicitly approved later.
- §4.5 FR-12 — v1 should enforce bounded remediation attempts per content item, with a default retry limit of 2 before escalation.
- §6 Cost — no external paid scoring or remediation service is required for v1 of this slice.
