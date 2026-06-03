# Investigation: Questionable Lyrics Repair Queue

## Hand-off Brief

1. **What happened.** The catalogue currently has 61 songs whose lyrics are marked `questionable`; the evidence shows these are mostly repeat-block, bracket-noise, print-hostile, low-confidence, and unusable-lyrics cases.
2. **Where the case stands.** The repair queue is mapped and prioritized, but no cleanup has been applied yet to this batch.
3. **What's needed next.** Start with deterministic cleanup for the repeated artifact patterns, then refresh the affected lyrics cache and re-run the quality counts.

## Case Info

| Field            | Value                                                                      |
| ---------------- | -------------------------------------------------------------------------- |
| Ticket           | N/A                                                                        |
| Date opened      | 2026-06-03                                                                 |
| Status           | Active                                                                     |
| System           | Linux workspace, Python CLI project                                          |
| Evidence sources | `data/review/quality_status.json`, `data/src/CampfireSongs.csv`, source code |

## Problem Statement

The user wants a prioritized repair queue for the 61 catalogue songs whose lyrics are currently labeled `questionable`, so the catalogue quality counts can be improved in a targeted way.

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

The first 61-song batch is a cleanup problem, not a missing-content problem. The evidence points to a small set of recurring artifacts, especially repeat blocks, so the best next move is to fix those mechanically and only fall back to manual overrides for the stubborn cases.

## Recommended Next Steps

### Fix direction

1. Clean the deterministic artifact patterns in `app/text_cleaning.py`.
2. Refresh the affected lyrics cache entries from manual overrides or the cleaned source text.
3. Re-run the quality-state counts and compare the new questionable total to 61.

### Diagnostic

1. Pick the top 10 songs with the most distinct signals.
2. Clean them and verify that the `questionable` label drops to `clean`.
3. If a song still fails, inspect whether the remaining issue is source noise or a true manual override case.

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
