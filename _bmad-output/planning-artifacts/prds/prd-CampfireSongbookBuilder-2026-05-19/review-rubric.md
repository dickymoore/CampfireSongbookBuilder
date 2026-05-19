# PRD Quality Review — CampfireSongbookBuilder Quality Upgrade

## Overall verdict

The PRD is decision-ready for a hobby/public brownfield quality upgrade. It has a clear thesis: keep the existing CLI/file workflow, but make generated songbooks trustworthy by assessing content quality, retrying bad sources, filtering questionable songs, and preserving offline generation.

The main residual risk is not product direction; it is implementation readiness. Architecture still needs to decide where review state lives, how thresholds are configured, and how manual overrides behave across refetching and named selections.

## Decision-readiness — adequate

The PRD makes the core choices explicit: no GUI in v1, preserve CLI operation, exclude Questionable Songs by default, add Favourites and Selections, and move toward Markdown to `.docx` to PDF. The Open Questions are real product/architecture decisions rather than template residue.

### Findings
- **medium** Persistence choices remain open (§12) — Favourites, Selections, Questionable status, and Review Decisions are intentionally unresolved. That is acceptable for architecture handoff, but story creation will need these decisions before implementation starts. *Fix:* Resolve §12 questions 1, 2, and 4 during architecture.

## Substance over theater — strong

The sections are earned by the product problem. Personas are light and useful; user journeys drive the features; non-goals remove likely distractions; and NFRs are specific to this repo's CLI/cache/scraper/document-generation shape.

### Findings
- No substantive findings.

## Strategic coherence — strong

The PRD has a coherent quality thesis rather than a loose backlog. Song quality assessment, source retry, review status, selection generation, offline generation, and inspectable output all support the same outcome: printable confidence before a trip.

### Findings
- No substantive findings.

## Done-ness clarity — adequate

Most FRs have testable consequences, and the added Acceptance Criteria give downstream story creation a usable spine. Some thresholds remain open by design, especially "too long," "too much junk," and "low confidence."

### Findings
- **medium** Quality thresholds are not yet concrete (§4.1, §12) — FR-3 and FR-4 are directionally clear but cannot be fully tested until initial thresholds and heuristics are chosen. *Fix:* During architecture or the first quality-assessment story, define initial configurable defaults and regression examples.

## Scope honesty — strong

The document is clear about non-goals and deferrals: GUI, hosted service, semantic wrong-song verification, intelligent layout, cloud sync, and public distribution polish are out. The single remaining `[ASSUMPTION]` is indexed and visible.

### Findings
- No substantive findings.

## Downstream usability — adequate

The glossary, FR IDs, NFR IDs, ACs, metrics, and handoff notes make the PRD usable for architecture and story generation. The document avoids implementation design while still naming brownfield constraints that architecture must honor.

### Findings
- **low** User journeys name "Dicky" rather than the exact section label "Primary Persona" (§2.5) — the linkage is understandable, but downstream extractors may prefer exact persona labels. *Fix:* Optionally revise each UJ opener to "Primary Persona Dicky..."

## Shape fit — strong

The shape fits a small brownfield CLI product. It avoids overbuilding personas or UX ceremony, while still including user journeys because the problem is an experience quality problem: the user needs trust in printable output.

### Findings
- No substantive findings.

## Mechanical notes

- FR IDs are contiguous from FR-1 through FR-19.
- NFR IDs are contiguous from NFR-1 through NFR-6.
- AC IDs are contiguous from AC-1 through AC-5.
- UJ IDs are contiguous from UJ-1 through UJ-4.
- The single inline `[ASSUMPTION]` in FR-7 is present in the Assumptions Index.
- No broken cross-references were found.
