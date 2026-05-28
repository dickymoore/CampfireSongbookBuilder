# Sprint Change Proposal: Add PDF Output Quality Gates

Date: 2026-05-25
Project: CampfireSongbookBuilder
Requested by: Dicky
Mode: Batch
Recommended Scope: Moderate
Recommended Path: Hybrid leaning Option 1 (direct adjustment via new follow-on epic)

## 1. Issue Summary

### Problem Statement

The project currently supports PDF generation as a conversion step, but PDF is not a first-class artifact in the PRD, epics, architecture acceptance boundaries, or automated review gates. As a result, the system can emit a PDF file without giving agents a deterministic machine-readable answer about whether that PDF is suitable for review.

This creates a contract gap: Markdown and `.docx` artifacts are verified and gated, while PDF is only reported as "generated" or "failed to generate." That is insufficient for an agentic workflow where PDF output also needs review-ready decisions, failure reasons, and escalation boundaries.

### How The Issue Was Identified

The issue surfaced after completion of the current sprint when reviewing whether all output formats were fully covered by the quality pipeline. The user explicitly requested both:

- PDF output as a supported deliverable
- proper agentic quality gates on the PDF

### Evidence

Planning evidence:

- PRD `FR1` only covers generated Markdown and `.docx` outputs.
- Epic 1 is explicitly scoped to "Review-Ready Document Quality Gates" for Markdown and `.docx`.
- Architecture states that existing generation already produces optional PDF, but the verification/governance slice formalized only Markdown and `.docx`.

Code evidence:

- [app/pdf_generation.py](/home/dicky/CampfireSongbookBuilder/app/pdf_generation.py:18) converts `.docx` to PDF if `soffice`, `libreoffice`, or `pandoc` is available.
- [app/document_creation.py](/home/dicky/CampfireSongbookBuilder/app/document_creation.py:303) appends PDF output paths and PDF conversion errors, but does not create a PDF verification record.
- [app/document_verification.py](/home/dicky/CampfireSongbookBuilder/app/document_verification.py:17) restricts `ARTIFACT_TYPES` to `markdown` and `docx`.
- [app/document_creation.py](/home/dicky/CampfireSongbookBuilder/app/document_creation.py:345) computes review gate decisions only from verification records, which currently exclude PDF.
- [app/reporting.py](/home/dicky/CampfireSongbookBuilder/app/reporting.py:331) reports PDF generation counts and errors, but not PDF review readiness as a first-class artifact gate.

## 2. Impact Analysis

### Checklist Status

- [x] 1.1 Trigger story identified: Epic 1 / Stories `1.1` to `1.4` revealed the boundary because they established artifact verification and review gating but stopped at Markdown and `.docx`.
- [x] 1.2 Core problem defined: New requirement plus specification gap in a completed slice.
- [x] 1.3 Evidence gathered: PRD, architecture, epics, and code all confirm PDF exists but is not gated.
- [x] 2.1 Current epic assessed: Epic 1 is complete as originally planned, but its scope is now incomplete relative to the desired product behavior.
- [x] 2.2 Epic-level changes identified: add follow-on epic rather than mutate completed story history.
- [x] 2.3 Remaining epic review completed: Epics 2 and 3 are not invalidated, but Epic 3 remediation/reporting may need small extensions for PDF-related escalation output.
- [x] 2.4 New epic needed: yes.
- [x] 2.5 Epic order review completed: new work should come after Epic 3 as Epic 4.
- [x] 3.1 PRD conflict assessed: PRD needs requirement expansion.
- [x] 3.2 Architecture conflict assessed: architecture needs explicit PDF verification/gating design.
- [x] 3.3 UX conflict assessed: no GUI/UX artifact exists; no direct UX doc changes required.
- [x] 3.4 Secondary artifact impact assessed: tests, reporting contracts, and possibly local review data schemas need updates.
- [x] 4.1 Option 1 evaluated.
- [x] 4.2 Option 2 evaluated.
- [x] 4.3 Option 3 evaluated.
- [x] 4.4 Recommended path selected.
- [x] 5.1 Issue summary created.
- [x] 5.2 Epic and artifact adjustments documented.
- [x] 5.3 Recommended path with rationale documented.
- [x] 5.4 MVP impact and action plan defined.
- [x] 5.5 Handoff plan defined.

### Epic Impact

Epic 1 remains historically valid, but it no longer represents complete artifact-level quality governance for all supported output formats.

Recommended epic change:

- Keep Epics 1 through 3 unchanged as completed history.
- Add `Epic 4: PDF Output Verification and Agentic Quality Gates`.

Reasoning:

- The code already shipped and passed tests for the original scope.
- Rewriting completed Epic 1 would blur what was actually delivered.
- A follow-on epic cleanly captures the newly recognized requirement and preserves auditability.

### Story Impact

No completed stories need rollback.

New stories are required because current stories do not cover:

- deterministic PDF verification records
- PDF-specific review-ready decisions
- PDF-aware reporting and escalation
- PDF quality checks after remediation/re-generation

### PRD Impact

The MVP remains achievable, but the PRD must expand artifact coverage from "Markdown and `.docx`" to "Markdown, `.docx`, and PDF" anywhere artifact-level verification and review gating are defined.

### Architecture Impact

The architecture needs explicit treatment of:

- PDF as a first-class artifact type in verification state
- how PDF content is inspected for deterministic neatness signals
- how PDF review gates are merged with existing artifact review decisions
- how missing PDF converters versus failed PDF quality checks are distinguished
- whether PDF verification uses text extraction, pagination metrics, page-count heuristics, or render-derived layout signals

### Technical Impact

Likely affected modules:

- `app/pdf_generation.py`
- `app/document_verification.py`
- `app/document_creation.py`
- `app/review_gate.py`
- `app/reporting.py`
- `app/remediation.py`
- `app/remediation_state.py`
- `main.py`
- `tests/test_document_verification.py`
- `tests/test_document_creation.py`
- `tests/test_review_gate.py`
- `tests/test_reporting.py`
- `tests/test_remediation.py`

### Secondary Artifact Impact

- local review-state schema in `data/review/document_quality.json`
- generated report schema and summary counts
- sprint backlog artifacts
- retrospective follow-up notes if the team wants to capture the missed PDF boundary explicitly

## 3. Path Forward Evaluation

### Option 1: Direct Adjustment

Assessment:

- Add new stories within a new follow-on epic.
- Extend current artifact verification contracts to include PDF.
- Preserve all completed implementation history.

Effort: Medium
Risk: Medium
Status: Viable

Why it works:

- Most building blocks already exist.
- The current pipeline already generates PDF and already has machine-readable verification/reporting patterns.
- The change is incremental and locally testable.

### Option 2: Potential Rollback

Assessment:

- Reverting Epic 1 or parts of the reporting flow would not simplify the work.
- The gap is not caused by a bad implementation; it is caused by incomplete scope coverage.

Effort: High
Risk: High
Status: Not viable

Why it does not work:

- Rollback throws away stable code without removing the real requirement.
- The team would still need to rebuild nearly the same verification/reporting stack, plus PDF support.

### Option 3: PRD MVP Review

Assessment:

- The PRD could avoid the issue by declaring PDF out of MVP scope.
- That would directly conflict with the user’s clarified requirement.

Effort: Low
Risk: Medium
Status: Not viable

Why it does not work:

- It reduces product value instead of solving the problem.
- It is inconsistent with the existing architecture and code, which already partially support PDF generation.

### Recommended Path

Selected approach: Hybrid, primarily Option 1

Recommendation:

- Add a new Epic 4 for PDF artifact verification and agentic quality gates.
- Update PRD and architecture to make PDF a first-class governed output artifact.
- Keep Epics 1 through 3 unchanged and treat this as a scope extension discovered after sprint completion.

Rationale:

- Lowest disruption to completed work.
- Cleanest audit trail.
- Reuses existing local-file, deterministic, single-process design.
- Preserves momentum while closing a real automation gap.

Timeline impact:

- Moderate. This is additional sprint work, not a patch-only tweak.

Risk assessment:

- Main technical risk is defining deterministic PDF neatness heuristics that are stable across environments and converter implementations.
- Main process risk is under-specifying PDF gate semantics and ending up with "PDF generated" confused with "PDF approved for review."

## 4. Detailed Change Proposals

### Stories

#### Add New Epic

Epic: `Epic 4: PDF Output Verification and Agentic Quality Gates`

Purpose:

The user can generate PDF artifacts, have them deterministically evaluated for layout and readability, and expose machine-readable PDF review gates to agents and reports before manual inspection or downstream remediation decisions.

#### Proposed Story 4.1

Story: `4.1 Produce Inspectable PDF Verification Records`

Section: New Story

OLD:

- No PDF-specific verification story exists.

NEW:

- As a songbook operator,
  I want each generated PDF artifact to produce a machine-readable verification record,
  So that agents can inspect PDF quality status without relying on file existence alone.

Acceptance Criteria:

- Given a generation run produces a PDF artifact
  When PDF verification runs
  Then a local verification record is written with artifact identity, artifact type `pdf`, verification status, reasons, and timestamp.
- Given PDF conversion fails before a file is created
  When reporting runs
  Then the failure is recorded distinctly as a generation/conversion error rather than a verification result.

Rationale:

- This closes the current data-contract gap between PDF existence and PDF quality governance.

#### Proposed Story 4.2

Story: `4.2 Evaluate PDF Neatness with Deterministic Layout Heuristics`

Section: New Story

OLD:

- No PDF neatness heuristics exist.

NEW:

- As a reviewer,
  I want generated PDFs checked for deterministic layout and readability issues,
  So that poor-quality rendered documents are blocked before review.

Acceptance Criteria:

- Given a generated PDF artifact
  When neatness evaluation runs
  Then the system checks deterministic heuristics relevant to rendered output such as excessive page count, sparse pages, text extraction failure, fragment-heavy layout, or other print-hostile structure.
- Given the same PDF bytes and threshold configuration
  When verification is rerun
  Then the same result is produced.

Rationale:

- PDF quality must be assessed on rendered output characteristics, not inferred only from Markdown or `.docx`.

#### Proposed Story 4.3

Story: `4.3 Gate Manual Review on PDF Verification Results`

Section: New Story

OLD:

- Review gates only operate on Markdown and `.docx` verification records.

NEW:

- As a reviewer,
  I want PDF verification to participate in review-ready decisions,
  So that agents and humans see a complete artifact-level gate across all requested deliverables.

Acceptance Criteria:

- Given a run includes Markdown, `.docx`, and PDF artifacts
  When review readiness is computed
  Then each artifact receives its own review-ready decision including PDF.
- Given the PDF fails verification
  When reporting or review gating runs
  Then the PDF is marked blocked from manual review with explicit failure reasons.

Rationale:

- Existing gate logic is blind to PDF and therefore incomplete for multi-artifact runs.

#### Proposed Story 4.4

Story: `4.4 Propagate PDF Gates Through Reporting and Remediation Re-evaluation`

Section: New Story

OLD:

- Reporting includes PDF output counts and conversion errors only.

NEW:

- As a songbook operator,
  I want PDF review results and post-remediation rechecks reflected in machine-readable reports,
  So that agents can escalate or continue based on full artifact-level evidence.

Acceptance Criteria:

- Given a PDF verification result exists
  When the quality report is written
  Then PDF verification and review-gate outcomes are included alongside other artifact results.
- Given remediation regenerates or rechecks underlying artifacts
  When post-remediation verification runs
  Then relevant PDF gate outcomes are refreshed and available for escalation logic.

Rationale:

- Agentic quality gates are not complete unless reporting and retry boundaries can consume them.

### PRD Modifications

Document: `_bmad-output/planning-artifacts/prds/prd-CampfireSongbookBuilder-2026-05-20/prd.md`

Section: Functional Requirements / artifact verification language

OLD:

- The system can assess generated Markdown and `.docx` outputs for readability and wasted whitespace, and produce a machine-readable document-level quality result for each requested artifact.

NEW:

- The system can assess generated Markdown, `.docx`, and PDF outputs for readability, wasted whitespace, and render-level print-hostile structure, and produce a machine-readable document-level quality result for each requested artifact.

Additional proposed PRD additions:

- Add an FR clarifying that PDF conversion failure and PDF verification failure are separate machine-readable outcomes.
- Add an FR or acceptance note that agentic review gating must cover all requested artifact types, including PDF.

Rationale:

- The PRD currently under-specifies a format that the implementation already partially supports.

### Epic Document Modifications

Document: `_bmad-output/planning-artifacts/epics.md`

Section: Functional Requirements / Epic List

OLD:

- `FR1` and Epic 1 refer to Markdown and `.docx` only.

NEW:

- Preserve Epic 1 as historical delivered scope.
- Add a new FR coverage entry and Epic 4 covering PDF verification and gates.

Proposed addition:

- `FR13: The system can verify generated PDF artifacts with deterministic rendered-output heuristics and expose machine-readable review-ready decisions and failure reasons.`

Rationale:

- A new FR avoids muddying the historical meaning of Epic 1 while making the new requirement explicit.

### Architecture Modifications

Document: `_bmad-output/planning-artifacts/architecture.md`

Sections requiring updates:

- Requirements Overview
- Technical Constraints & Dependencies
- Cross-Cutting Concerns
- Data Architecture
- Review/verification flow sections that describe artifact verification

OLD:

- Existing generation already produces Markdown, `.docx`, and optional PDF.
- Verification design is effectively centered on Markdown and `.docx`.

NEW:

- PDF is elevated from optional byproduct to governed artifact.
- Architecture must define deterministic PDF verification mechanics, required dependencies for reading/analyzing PDF, and the rule boundary between conversion failures and quality failures.
- Architecture should document how PDF verification integrates with `document_quality.json`, review gating, remediation rechecks, and machine-readable reports.

Rationale:

- This is the main technical design gap that must be settled before implementation.

### UI/UX Modifications

No UX design document changes required.

Reason:

- The slice remains CLI and report driven, with no GUI in MVP.

## 5. PRD MVP Impact and High-Level Action Plan

### MVP Impact

MVP scope is expanded, not redefined.

Implication:

- MVP now includes governed PDF output rather than optional ungated PDF conversion.

### High-Level Action Plan

1. Update PRD to define PDF as a first-class verified artifact.
2. Update architecture with deterministic PDF verification strategy and dependency assumptions.
3. Add Epic 4 and Story 4.1 through 4.4 to the backlog.
4. Implement PDF verification record support in `app/document_verification.py`.
5. Extend generation flow to evaluate PDF artifacts after successful conversion.
6. Extend review gate computation and reporting to treat PDF like other governed artifacts.
7. Extend remediation re-evaluation and escalation reporting where PDF evidence matters.
8. Add full regression coverage and run the existing `unittest` suite.

### Dependencies and Sequencing

- Architecture clarification should happen before implementation because PDF verification heuristics need explicit definition.
- Story `4.1` should precede `4.2` and `4.3`.
- Story `4.4` should follow once PDF verification records and gates exist.

## 6. Implementation Handoff

### Scope Classification

Moderate

Reason:

- No fundamental replan is required.
- Backlog and planning artifacts need updates before implementation begins.
- Technical design choices around PDF analysis need to be documented to avoid unstable heuristics.

### Handoff Recipients

- Product Owner / Developer
  Responsibility: update PRD and epics backlog to add the new requirement cleanly.
- Architect / Developer
  Responsibility: define PDF verification approach and data contract updates.
- Developer
  Responsibility: implement Epic 4 and regression tests.

### Success Criteria

- A successful run can generate PDF when tooling is available.
- Each generated PDF receives either:
  - a PDF verification record and review-ready decision, or
  - a distinct conversion/generation failure record if no PDF file exists.
- Machine-readable reports include PDF verification and gate results.
- Remediation re-evaluation does not treat PDF as an ungoverned byproduct.
- Full `unittest` suite passes.

## 7. Final Recommendation

Approve a follow-on `Epic 4` for PDF verification and agentic quality gates. Do not reopen or rewrite completed stories. Update PRD and architecture first, then implement PDF verification, review gating, reporting, and re-evaluation as new backlog work.

## 8. Approval Record

Approval status: Approved
Approved by: Dicky
Approved at: 2026-05-25
Scope classification: Moderate

Approved execution path:

- Keep Epics 1 through 3 as completed historical scope.
- Add Epic 4 backlog entries for PDF verification and agentic quality gates.
- Route next work to PRD and architecture updates, then implementation.
