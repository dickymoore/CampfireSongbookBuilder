# Investigation: Questionable Lyrics Repair Queue

## Hand-off Brief

1. **What happened.** The catalogue currently has 61 songs whose lyrics are marked `questionable`; the evidence shows these are mostly repeat-block, bracket-noise, print-hostile, low-confidence, and unusable-lyrics cases.
2. **Where the case stands.** The repair queue is mapped and prioritized, but no cleanup has been applied yet to this batch.
3. **What's needed next.** The queue is mapped, but cleanup is currently paused so higher-priority catalogue work can continue first.

## Case Info

| Field            | Value                                                                      |
| ---------------- | -------------------------------------------------------------------------- |
| Ticket           | N/A                                                                        |
| Date opened      | 2026-06-03                                                                 |
| Status           | Active                                                                     |
| System           | Linux workspace, Python CLI project                                          |
| Evidence sources | `data/review/quality_status.json`, `data/src/CampfireSongs.csv`, source code |

## Problem Statement

The user previously wanted a prioritized repair queue for the 61 catalogue songs whose lyrics were labeled `questionable`. That work has now been deferred because the quality gate is no longer the active priority.

## Evidence Inventory

| Source | Status   | Notes |
| ------ | -------- | ----- |
| Quality state | Available | `data/review/quality_status.json` contains 61 questionable lyrics entries. |
| Source list | Available | `data/src/CampfireSongs.csv` defines the 346-song catalogue baseline. |
| Cleaner code | Available | `app/text_cleaning.py` already contains the deterministic cleanup pipeline. |
| Cache refresh path | Available | `app/document_generation.py` refreshes manual overrides into `data/cache/*.jsonl`. |

## Investigation Backlog

| # | Path to Explore | Priority | Status | Notes |
| - | --------------- | -------- | ------ | ----- |
| 1 | `app/text_cleaning.py` | High | Open | Clear repeat-block / bracket-noise cases in batches. |
| 2 | `app/manual_import.py` | High | Open | Confirm which questionable songs need manual override vs deterministic cleanup. |
| 3 | `data/review/quality_status.json` | High | Open | Track the 61-song queue and re-score after each batch. |

## Confirmed Findings

### Finding 1: The questionable pool is real and bounded

**Evidence:** `data/review/quality_status.json` currently reports 61 lyrics entries with `quality: questionable`.

**Detail:** These are the first target batch because they already have content, but the content still needs cleanup to become `clean`.

### Finding 2: The dominant signal is repeat blocks

**Evidence:** Aggregated signal counts from `data/review/quality_status.json`:

- `duplicate_block`: 61 songs
- `excessive_bracket_noise`: 37 songs
- `print_hostile_content`: 22 songs
- `low_confidence_match`: 16 songs
- `unusable_lyrics`: 12 songs

**Detail:** The same song can have multiple signals; the count above is per-song, deduplicated by signal code.

## Deduced Conclusions

### Deduction 1: One cleaner pass can clear many songs

**Based on:** Finding 2

**Reasoning:** The 61-song pool is not 61 unique failure modes. Most entries cluster around a small number of deterministic artifacts, so a shared cleanup rule can improve several songs at once.

**Conclusion:** Start with deterministic cleanup patterns before using manual overrides.

## Hypothesized Paths

### Hypothesis 1: The first cleanup pass should target repeat-block and bracket-noise artifacts

**Status:** Open

**Theory:** Most questionable lyrics can be moved to `clean` by removing duplicated blocks, promo noise, and scrape residue.

**Supporting indicators:** `duplicate_block` appears on all 61 songs; `excessive_bracket_noise` appears on 37.

**Would confirm:** A cleanup pass that materially reduces the questionable count without manual edits.

**Would refute:** The cleaned output still fails quality checks for the majority of the queue.

**Resolution:** Pending the first cleanup batch.

## Missing Evidence

| Gap | Impact | How to Obtain |
| --- | ------ | ------------- |
| Song-by-song cleaned output diffs | Needed to decide which cases require manual overrides | Run the cleaner on the highest-priority songs and inspect the diff |
| Post-clean quality counts | Needed to confirm the queue is shrinking | Re-run the lyrics cache refresh for the affected songs |

## Source Code Trace

| Element | Detail |
| ------- | ------ |
| Error origin | `app/generation_filtering.py:evaluate_cached_content()` and the quality state stored in `data/review/quality_status.json` |
| Trigger | Song content is loaded for a generation run or cache refresh |
| Condition | Content contains repeat blocks, bracket noise, or other scrape artifacts that keep it in `questionable` |
| Related files | `app/text_cleaning.py`, `app/document_generation.py`, `app/manual_import.py`, `data/review/quality_status.json` |

## Conclusion

**Confidence:** High

The first 61-song batch is a cleanup problem, not a missing-content problem. The evidence points to a small set of recurring artifacts, especially repeat blocks, so the best next move would be mechanical cleanup. That work is now paused by priority, not because the diagnosis changed.

## Recommended Next Steps

### Fix direction

1. Defer cleanup of the deterministic artifact patterns in `app/text_cleaning.py` until the quality gate becomes a priority again.
2. Keep the current cleaner and scorer logic in place so the queue can be resumed later without rework.
3. Continue with catalogue work that is not blocked by the quality gate.

### Diagnostic

1. No further diagnostic work is needed while the queue is paused.
2. Resume the queue later by re-running the priority report and checking whether the same top signals remain.

## Reproduction Plan

1. Load `data/review/quality_status.json`.
2. Filter lyrics entries with `quality == questionable`.
3. Sort the queue by number of distinct signal codes.
4. Apply cleanup to the top batch.
5. Refresh cache and recompute the quality counts.

## Side Findings

- The current lyrics quality-state has 25 clean lyrics entries and 61 questionable lyrics entries.
- The current chords quality-state has 21 clean entries and no questionable entries.

## Follow-up: 2026-06-03

### New Evidence

- `duplicate_block` is the only signal present on all 61 questionable lyrics entries.
- `excessive_bracket_noise`, `print_hostile_content`, `low_confidence_match`, and `unusable_lyrics` cluster on subsets of the queue.

### Additional Findings

- The most urgent batch is not the whole catalogue; it is the 61-questionable lyrics slice.

### Updated Hypotheses

- Deterministic cleanup should clear a meaningful share of the 61 without manual intervention.

### Backlog Changes

- Prioritize the top 10 songs with the most distinct signals.

### Updated Conclusion

- The queue is ready for targeted cleanup.

## Follow-up: 2026-06-03 #3

### New Evidence

- Refreshed quality report: `data/review/reports/quality_run-refresh_quality_state-20260603T164846+0100.json`.
- The report still shows `638` questionable lyrics entries after deterministic normalization.
- The priority queue is dominated by the same three signals:
  - `duplicate_block`
  - `print_hostile_content`
  - `excessive_bracket_noise`
- In the top 100 priority items, the signal distribution is:
  - `duplicate_block`: `100`
  - `print_hostile_content`: `100`
  - `excessive_bracket_noise`: `81`
  - `email_header_artifacts`: `9`
  - `html_residue`: `2`

### Additional Findings

- The highest-priority songs are all lyrics entries with the same 3-signal pattern and quality score `2`.
- The first unique priority items are:
  - `ABC - The Look of Love`
  - `Alex Ebert - Truth`
  - `Ariana Grande - Positions`
  - `Ariana Grande - no tears left to cry`
  - `Aztec Camera - Somewhere in my heart`
  - `Beyonce - Bodyguard`
  - `Blur - Tender`
  - `Britney Spears - Hit Me Baby One More Time`
  - `Britney Spears - Not So Innocent`
  - `Britney Spears - Toxic`

### Updated Hypotheses

- The remaining questionable queue is still dominated by scrape-artifact cleanup rather than missing content.

### Backlog Changes

- Prioritize the top unique songs above for deterministic cleanup or manual override review.
- Inspect the 11-song cluster where the rank-1 signals repeat unchanged.

### Updated Conclusion

- The next useful step is to leave this queue paused and work the higher-priority catalogue tasks first.
