# Sprint Change Proposal: Move Favourite Membership into Source CSV

Date: 2026-05-20
Project: CampfireSongbookBuilder
Workflow: bmad-correct-course
Mode: Batch
Status: Draft for approval

## 1. Issue Summary

### Change Trigger

- Triggering area: Epic 4, especially Story 4.1 `Load and Validate Favourite Songs`
- Trigger type: Better implementation choice discovered during execution
- Discovery context: While adding songs and marking them as favourites, the current implementation required updating both the source list and a separate favourites file.

### Problem Statement

Favourite membership is currently modeled as separate state in `data/selections/favourites.json`, but in this product it behaves like simple song-list metadata rather than an independent multi-record selection. That creates avoidable duplication and sync risk between the source list and favourites state.

### Evidence

- The source list already acts as the canonical editable catalog in `data/src/CampfireSongs.csv`.
- Favourite membership is currently just a yes/no attribute, not a richer object with extra metadata.
- Named selections still require separate files because a song can belong to many selections, but favourites do not have that same multiplicity problem.
- Current implementation work created `data/selections/favourites.json`, which immediately introduced two places to maintain song identity for the same user intent.

## 2. Impact Analysis

### Epic Impact

- Affected epic: Epic 4 `Favourites, Selections, and Quality-Aware Book Building`
- Epic viability: Still viable without resequencing or replacement
- Required epic-level change: Refine the favourite-storage approach only; no change to the user-facing epic goal

### Story Impact

- Story 4.1 needs substantive revision because it currently assumes `data/selections/favourites.json` is the source of truth.
- Story 4.2 remains valid. Named selections should stay as separate JSON files.
- Story 4.3 remains valid in intent, but its input source for favourite-only generation changes from JSON-backed favourites to CSV-backed favourites.
- Story 4.4 remains valid. No meaningful change beyond wording consistency.

### Artifact Conflicts

- PRD conflict: minor
  - FR-11 says favourite status must be persisted in an inspectable format.
  - This remains true if the inspectable format is a `Favourite` column in the source CSV.
- Architecture conflict: moderate
  - Current architecture repeatedly specifies `data/selections/favourites.json` as a dedicated file contract.
  - Those sections need revision so favourites are treated as source-list metadata while named selections remain under `data/selections/*.json`.
- UX impact: none
  - No GUI artifact exists and no GUI is required for this change.
- Secondary artifact impact: implementation notes, tests, and docs that describe favourite storage

### Technical Impact

- `app/load_songs.py` must recognize an optional `Favourite` column and preserve row compatibility.
- `app/selection_state.py` no longer needs to be the canonical storage path for favourites, though named selections remain in scope there.
- Generation paths that support favourite-only books must filter loaded song rows by a CSV flag rather than loading a separate favourites file.
- Tests for favourite loading/validation need to move from JSON-file validation to CSV-column parsing and favourite-row filtering.
- Migration behavior should be defined for existing `data/selections/favourites.json` users.

## 3. Recommended Approach

### Selected Path

Option 1: Direct Adjustment

### Rationale

- The product goal does not change.
- The data-model change is local and bounded.
- It removes duplicated user intent across two files.
- It matches the actual editing workflow of this repo, where the source CSV is already the primary user-maintained input artifact.
- It preserves separate JSON files only where they are structurally justified: named selections.

### Effort, Risk, Timeline

- Effort: Medium
- Risk: Low to Medium
- Timeline impact: Small

### Why Not Option 2 or 3

- Potential rollback is unnecessary because the existing implementation can be adjusted directly.
- PRD MVP review is unnecessary because the MVP remains fully achievable; only the representation of favourites changes.

## 4. Detailed Change Proposals

### 4.1 Story Changes

Story: 4.1 `Load and Validate Favourite Songs`
Section: Story statement

OLD:

```text
As a camper building a repeat-use songbook,
I want to mark favourite songs in an inspectable local file,
So that I can generate a focused book without editing the master CSV each time.
```

NEW:

```text
As a camper building a repeat-use songbook,
I want to mark favourite songs in the source CSV through a simple Favourite column,
So that favourite membership stays with the main song list and can be edited in one place.
```

Rationale:

- Favourite membership is a per-song boolean attribute, so colocating it with the source row reduces duplication and sync errors.

Story: 4.1 `Load and Validate Favourite Songs`
Section: Acceptance Criteria

OLD:

```text
Given `data/selections/favourites.json` contains favourite song entries
When favourites are loaded
Then valid entries are matched by exact artist/title identity or derived `song_key`
And malformed entries are reported with file path, field, and reason.

Given a favourite song is Questionable
When favourite-only generation is evaluated
Then the song is still subject to default quality exclusion unless explicitly accepted or overridden.
```

NEW:

```text
Given `data/src/CampfireSongs.csv` contains an optional `Favourite` column
When songs are loaded
Then rows marked as favourite are available for favourite-only generation
And missing or unrecognized favourite values are handled predictably without breaking existing CSV compatibility.

Given a favourite song is Questionable
When favourite-only generation is evaluated
Then the song is still subject to default quality exclusion unless explicitly accepted or overridden.
```

Rationale:

- This preserves the favorite-only workflow while moving validation to the natural source of truth.

Story: 4.3 `Generate Quality-Filtered Favourite and Selection Books`
Section: Acceptance Criteria wording

OLD:

```text
Given a favourite-only or named-selection generation request includes clean and Questionable songs
When generation filtering runs
Then clean accepted songs are included and Questionable songs are excluded by default
And the report lists excluded selected songs and reasons.
```

NEW:

```text
Given a favourite-only or named-selection generation request includes clean and Questionable songs
When generation filtering runs
Then clean accepted songs are included and Questionable songs are excluded by default
And favourite-only generation reads favourite membership from the source CSV
And the report lists excluded selected songs and reasons.
```

Rationale:

- Keeps favorite-generation behavior explicit after the storage model change.

### 4.2 PRD Changes

Artifact: PRD
Section: `4.4 Favourites and Selections` / `FR-11: Mark Songs as Favourites`

OLD:

```text
- Favourite status is persisted in an inspectable format.
- The builder can generate output using only Favourite Songs.
- Favourite status is independent from quality status; a Favourite Song may still be excluded when Questionable unless explicitly included.
```

NEW:

```text
- Favourite status is persisted in an inspectable format, with the source CSV as the default canonical store through an optional `Favourite` column.
- The builder can generate output using only Favourite Songs.
- Favourite status is independent from quality status; a Favourite Song may still be excluded when Questionable unless explicitly included.
```

Rationale:

- The PRD intent already allows inspectable persistence; this change narrows the preferred representation.

### 4.3 Architecture Changes

Artifact: Architecture
Section: `Data Architecture` / `Decision: Add separate quality and review state files.`

OLD:

```text
- `data/review/quality_status.json`
- `data/review/review_decisions.json`
- `data/review/source_attempts.jsonl`
- `data/review/reports/*.json`
- `data/selections/favourites.json`
- `data/selections/*.json`
```

NEW:

```text
- `data/review/quality_status.json`
- `data/review/review_decisions.json`
- `data/review/source_attempts.jsonl`
- `data/review/reports/*.json`
- `data/selections/*.json` for named selections
- `data/src/CampfireSongs.csv` as the canonical store for per-song favourite membership via an optional `Favourite` column
```

Rationale:

- This keeps structural state separate only where it must be separate.

Artifact: Architecture
Section: Any path-contract references to `data/selections/favourites.json`

OLD:

```text
`data/selections/favourites.json`
```

NEW:

```text
`data/src/CampfireSongs.csv` with optional `Favourite` column
```

Rationale:

- Repeated path references must be made consistent to avoid future implementation drift.

Artifact: Architecture
Section: Module responsibility for `app/selection_state.py`

OLD:

```text
`app/selection_state.py`: load/write favourites and selections.
```

NEW:

```text
`app/selection_state.py`: load/write named selections.
`app/load_songs.py`: parse optional favourite membership from the source CSV.
```

Rationale:

- The module boundary should match the new canonical data model.

### 4.4 Documentation and Migration Changes

Artifact: README / usage docs

OLD:

```text
No explicit favourite-column guidance.
```

NEW:

```text
Document optional `Favourite` column values and show that favourite-only generation uses the source CSV.
```

Rationale:

- Users need one obvious place to edit favourites.

Artifact: Migration note

NEW:

```text
If `data/selections/favourites.json` exists, provide a one-time migration path or compatibility read that can populate the CSV `Favourite` column without changing song identity semantics.
```

Rationale:

- Avoid stranding any existing favourite state created during the current iteration.

## 5. Checklist Status

### Section 1: Understand the Trigger and Context

- [x] 1.1 Trigger identified: Epic 4 / Story 4.1 favourite storage design
- [x] 1.2 Problem defined: favourite membership modeled as separate state instead of source-row metadata
- [x] 1.3 Evidence gathered: duplicate maintenance, current workflow friction, structural mismatch with named selections

### Section 2: Epic Impact Assessment

- [x] 2.1 Current epic still viable
- [x] 2.2 Epic-level change is a refinement, not replacement
- [x] 2.3 Future epics unaffected
- [x] 2.4 No new epic required
- [x] 2.5 No resequencing required

### Section 3: Artifact Conflict and Impact Analysis

- [x] 3.1 PRD reviewed
- [x] 3.2 Architecture reviewed
- [N/A] 3.3 UX specification reviewed
- [x] 3.4 Other artifacts identified: tests, README, implementation notes

### Section 4: Path Forward Evaluation

- [x] 4.1 Direct adjustment viable
- [N/A] 4.2 Rollback not justified
- [N/A] 4.3 MVP review not needed
- [x] 4.4 Recommended path selected

### Section 5: Sprint Change Proposal Components

- [x] 5.1 Issue summary drafted
- [x] 5.2 Epic and artifact impacts documented
- [x] 5.3 Recommended path justified
- [x] 5.4 MVP impact and action plan defined
- [x] 5.5 Handoff plan defined

### Section 6: Final Review and Handoff

- [x] 6.1 Checklist completed
- [x] 6.2 Proposal reviewed for consistency
- [!] 6.3 User approval pending
- [N/A] 6.4 Sprint status update deferred until approval

## 6. Implementation Handoff

### Scope Classification

Moderate

### Why Moderate

- The change touches planning artifacts, implementation boundaries, and completed Epic 4 assumptions.
- It does not require strategic replanning or a new epic.

### Handoff Recipients

- Product Owner / Developer

### Responsibilities

- Product Owner:
  - Approve the revised canonical storage model for favourites
  - Accept wording updates to Epic 4, PRD FR-11, and architecture references
- Developer:
  - Replace JSON-backed favourite loading with CSV-column-backed favourite loading
  - Preserve named selections as JSON
  - Add migration or compatibility handling for any existing `favourites.json`
  - Update tests and docs

### Success Criteria

- The source CSV supports an optional `Favourite` column without breaking current song loading.
- Favourite-only generation uses the CSV as the source of truth.
- Named selections remain unchanged and continue to support multi-membership.
- Existing quality filtering behavior for favourites is preserved.
- Documentation clearly explains the new editing workflow.

## 7. High-Level Action Plan

1. Update planning artifacts to make the CSV `Favourite` column the canonical favourite store.
2. Refactor implementation so favourite parsing lives with source-list loading.
3. Remove or demote `favourites.json` from the canonical runtime contract.
4. Add migration or compatibility handling for any existing separate favourites file.
5. Update tests and user documentation.

