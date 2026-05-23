# All Epics Retrospective: CampfireSongbookBuilder Quality Upgrade

Status: done
Date: 2026-05-20
Scope: Epics 1 through 5

## Portfolio Summary

The program delivered the full quality-upgrade roadmap defined in the PRD:

- Epic 1: quality contracts and deterministic assessment foundation
- Epic 2: source retry, review state, and traceability
- Epic 3: better song-addition feedback and input validation
- Epic 4: favourites, selections, and quality-aware subset generation
- Epic 5: offline inspectable output with Markdown, `.docx`, optional PDF, and printable checks

Sprint tracking currently records:

- Epics complete: 5/5
- Stories complete: 23/23
- Retrospectives complete in sprint status: Epic 1 only

Post-epic work completed after the tracked stories:

- Favourites were simplified from a separate JSON file to a `Favourite` column in `data/src/CampfireSongs.csv`
- `--favourites-only` CLI support was added
- `--selection <name>` CLI support was added
- Regression coverage was added for both new CLI paths

## What Went Well

### 1. Contract-First Foundation Held Up

The early decision to build explicit content contracts, exact identity handling, and deterministic validators gave the rest of the program a stable base. This avoided a lot of hidden ambiguity later in review state, reporting, and filtered generation.

### 2. Boundaries Stayed Mostly Clean

The project kept the intended architecture:

- thin `main.py`
- flat `app/*.py` modules
- file-based state
- deterministic helper functions
- `unittest` regression coverage

That discipline made later stories additive instead of destabilizing.

### 3. Quality and Traceability Became Real Product Features

The tool now does more than fetch and print. It can explain:

- why content was excluded
- what source attempts happened
- what review decisions are current
- what selection issues exist
- what output artifacts were produced

That is a meaningful product upgrade, not just a refactor.

### 4. Test Coverage Supported Fast Iteration

The implementation stories repeatedly closed with a passing suite, and the recent post-story CLI changes were also covered with targeted tests. That kept the project safe while still moving quickly.

### 5. Course Correction Was Handled Properly

The favourite-storage change was a good correction:

- the original JSON-based plan was internally consistent
- actual usage showed that favourite membership behaves like row metadata, not independent state
- the correction simplified the runtime model without weakening named selections

That is a healthy example of planning adapting to reality.

## What Was Hard

### 1. State Modeling Was the Main Source of Complexity

The difficult parts were not fetching or rendering by themselves. The hard parts were:

- exact song identity
- stale review decisions
- separation of current state vs. append-only history
- keeping selection semantics clean
- preserving backward compatibility with the cache

### 2. Planning Drift Appeared After Delivery

The biggest cross-epic process issue is that the recent favourite/selection CLI work happened after the epic stories were already marked done. The code and docs were corrected, but sprint tracking still reflects the earlier epic-complete state rather than the follow-up implementation cycle.

### 3. Some Architecture Decisions Were Correct but Too Abstract

The original “inspectable file” direction for favourites was reasonable, but it did not distinguish between:

- simple per-row metadata
- truly separate user-managed collections

That distinction only became obvious during hands-on usage.

### 4. Retrospective Discipline Was Incomplete

Only Epic 1 has an epic-specific retrospective artifact. The program completed all five epics, but the learning loop was not maintained consistently across Epics 2 through 5.

## Cross-Epic Lessons

### Lesson 1: Exact Identity Is a Core Domain Constraint

This project depends on preserving exact `artist`, `title`, and derived `song_key` semantics. That constraint shaped cache compatibility, review state, filtering, selections, and reporting. Any future work that weakens identity discipline will create subtle regressions.

### Lesson 2: Separate File-Based State Only When the Data Model Truly Requires It

The project benefited from separate files for:

- review decisions
- quality status
- source attempt history
- named selections

But favourite membership did not justify its own canonical file. The more general rule is:

- separate state for many-to-many or versioned user intent
- keep simple boolean row attributes with the source row

### Lesson 3: Deterministic, Local Rules Were the Right MVP Choice

The current product direction succeeded because it stayed with:

- deterministic heuristics
- local files
- no new service layer
- no database
- no heavy dependency expansion

That kept implementation effort focused on product value rather than infrastructure churn.

### Lesson 4: Reports Matter as Much as Filtering

Quality gating without explanation would have made the product feel arbitrary. The machine-readable and human-readable reporting work is a core part of trust, not a secondary convenience.

### Lesson 5: Brownfield CLI Changes Need Story Tracking Too

Small follow-up changes can still be product-significant. The recent favourite-column and selection CLI work proved that “post-epic cleanup” can actually be roadmap-relevant functionality and should be tracked as such.

## Successes to Preserve

- Contract-first implementation order
- Pure helper modules for assessment logic
- Explicit loader validation with recoverable errors
- Full-suite verification after behavior changes
- Human-editable runtime state
- Thin CLI orchestration
- Pragmatic course correction when real usage exposed a better model

## Risks and Gaps

### 1. Sprint Tracking Is Now Slightly Stale

The current `sprint-status.yaml` does not reflect the recent post-epic implementation work. It is not wrong about the five delivered epics, but it no longer tells the full story of the codebase’s latest behavior.

### 2. No Formal Next Roadmap Slice Exists Yet

The existing roadmap was completed. There is no next epic defined, so the project now needs either:

- a new planning slice
- a maintenance/cleanup slice
- or a deliberate stop condition

### 3. README and Generated Project Docs Need Ongoing Normalization

The core docs were updated during the favourite-model correction, but documentation drift is likely to reappear unless it becomes a habit to close code changes with doc and sprint-state updates together.

## Action Items

### Process

1. Start a new tracked implementation slice for post-roadmap enhancements instead of letting them accumulate as untracked “aftercare”.
2. Treat retrospective completion as mandatory at major delivery boundaries, even if the epic itself is already marked done.
3. Update sprint tracking whenever behaviorally meaningful follow-up work lands after an epic is marked complete.

### Product / Planning

1. Decide whether the next phase is maintenance, roadmap extension, or packaging/release preparation.
2. If roadmap extension is chosen, create a fresh PRD or addendum for the next feature slice rather than stretching the completed epic set.

### Technical

1. Keep the CSV-as-canonical-source rule for favourite membership.
2. Keep named selections as separate JSON files.
3. Continue adding focused CLI regression tests whenever command-line behavior changes.

## Readiness Assessment

The current codebase looks ready for a next planning cycle, not another emergency correction cycle.

Reasons:

- tests are passing
- architecture direction is coherent
- runtime model is simpler than before
- the core roadmap is complete

The main thing missing is not implementation readiness. It is roadmap clarity.

## Recommended Next Move

Use a fresh planning cycle for whatever comes next.

If the goal is to extend the product:

- update or create planning artifacts first
- then create the next story slice

If the goal is to package or stabilize:

- define a maintenance epic or release-preparation slice explicitly

## Closing Notes

This was a successful program increment. The work did not just add features; it made the application more trustworthy, inspectable, and operable. The strongest pattern across all epics was disciplined simplification: local state, explicit contracts, deterministic rules, and incremental tests.

The main improvement needed now is process closure: track follow-up work with the same rigor used for the original epics.
