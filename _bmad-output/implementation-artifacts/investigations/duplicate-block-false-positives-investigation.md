# Investigation: Duplicate-Block False Positives

## Hand-off Brief

1. **What happened.** The lyrics quality checker is flagging several songs as `duplicate_block` because it detects exact repeated line blocks, even when the repetition is a normal chorus or verse reprise.
2. **Where the case stands.** The evidence confirms the detector is working as written, but the current heuristic is too broad for repeated-song structures in otherwise acceptable lyrics.
3. **What's needed next.** Decide whether to narrow the duplicate-block heuristic or whitelist structurally normal repetition for songs that are otherwise clean.

## Case Info

| Field            | Value                                                                      |
| ---------------- | -------------------------------------------------------------------------- |
| Ticket           | N/A                                                                        |
| Date opened      | 2026-06-03                                                                 |
| Status           | Active                                                                     |
| System           | Linux workspace, Python CLI project                                          |
| Evidence sources | `app/quality_assessment.py`, `data/cache/lyrics_cache.jsonl`                |

## Problem Statement

The user reported that some songs were being flagged as questionable even though they looked fine after manual inspection. The investigation focused on `The Smiths - Cemetry Gates`, `The Cure - Close To Me`, and `R.E.M. - Can't Get There from Here`.

## Evidence Inventory

| Source | Status | Notes |
| ------ | ------ | ----- |
| Quality detector | Available | `_has_duplicate_block()` checks exact repeated blocks of lines. |
| Cached lyrics text | Available | The three songs are present in `data/cache/lyrics_cache.jsonl`. |
| Manual inspection | Available | The repeated sections are normal chorus/verse repetition, not obvious scrape duplication. |

## Investigation Backlog

| # | Path to Explore | Priority | Status | Notes |
| - | --------------- | -------- | ------ | ----- |
| 1 | `app/quality_assessment.py` | High | Open | Decide whether repeated choruses should count as duplicate blocks. |
| 2 | `app/text_cleaning.py` | Medium | Open | Ensure cleaning does not reintroduce duplication artifacts. |
| 3 | `data/cache/lyrics_cache.jsonl` | Medium | Open | Check whether other songs have similar normal-repetition false positives. |

## Timeline of Events

| Time | Event | Source | Confidence |
| ---- | ----- | ------ | ---------- |
| 2026-06-03 | The duplicate-block detector was confirmed to scan all exact repeated line blocks up to 200 lines. | `app/quality_assessment.py:81-100` | Confirmed |
| 2026-06-03 | The detector is invoked directly in the lyrics quality pipeline and emits `duplicate_block` as an error signal. | `app/quality_assessment.py:351-359` | Confirmed |
| 2026-06-03 | The three sample songs were shown to contain repeated chorus/verse material that is normal song structure. | `data/cache/lyrics_cache.jsonl` | Confirmed |

## Confirmed Findings

### Finding 1: The detector flags exact repeated line blocks

**Evidence:** `app/quality_assessment.py:81-100`

**Detail:** `_has_duplicate_block()` iterates over all block lengths and returns `True` when the same exact block appears twice with at least one full block of separation.

### Finding 2: The duplicate-block signal is emitted as a quality error

**Evidence:** `app/quality_assessment.py:351-359`

**Detail:** When `_has_duplicate_block(lines)` returns true, the song is marked with `duplicate_block`, which contributes to `questionable`.

### Finding 3: The flagged songs contain normal repetition, not obvious duplication artifacts

**Evidence:** `data/cache/lyrics_cache.jsonl` lyrics text for the songs below.

**Detail:** The repeated sections are the expected chorus/verse repetitions in each song.

## Deduced Conclusions

### Deduction 1: The heuristic is too broad for normal song structure

**Based on:** Findings 1 and 3

**Reasoning:** Exact block repetition is common in songs. A pure repeated-line detector cannot distinguish a repeated chorus from duplicated scrape junk.

**Conclusion:** The current heuristic will keep producing false positives for some legitimate songs unless it is made structure-aware or narrowed.

## Hypothesized Paths

### Hypothesis 1: Normal chorus repetition is causing the false positives

**Status:** Confirmed

**Theory:** The songs are flagged because their choruses repeat verbatim, and the detector treats that as suspicious duplication.

**Supporting indicators:** The repeated spans in the cached lyrics are adjacent to chorus sections, not random duplicated pages or scrape residue.

**Would confirm:** Exact repeated spans in the quoted examples below.

**Would refute:** Evidence of unrelated duplicated blocks or scrape junk outside the chorus structure.

**Resolution:** The cached lyrics show exact repeated chorus/verse material.

## Missing Evidence

| Gap | Impact | How to Obtain |
| --- | ------ | ------------- |
| Chorus-aware detector criteria | Needed to decide how to avoid legitimate repetition without missing real duplication | Define a structure-aware duplicate rule or whitelist normal chorus repeats |

## Source Code Trace

| Element | Detail |
| ------- | ------ |
| Error origin | `app/quality_assessment.py:_has_duplicate_block()` |
| Trigger | Lyrics content with any exact repeated block of lines |
| Condition | The repeated block appears at least twice with one full block of separation |
| Related files | `app/quality_assessment.py`, `data/cache/lyrics_cache.jsonl` |

## Conclusion

**Confidence:** High

The `duplicate_block` flag is not necessarily wrong mechanically, but it is too aggressive for normal song repetition. The three reviewed songs are being flagged because the detector cannot tell a repeated chorus from duplicated junk.

## Recommended Next Steps

### Fix direction

1. Narrow `_has_duplicate_block()` so it ignores expected chorus/verse repeats.
2. Or add a whitelist for known-good repeated sections in the lyrics cache path.
3. Re-run review on the three sample songs to confirm they stop flagging `duplicate_block`.

### Diagnostic

1. Compare the repeated spans against section markers like `[Verse]` and `[Chorus]`.
2. Require repeated blocks to be longer, less structured, or non-adjacent to normal chorus boundaries before flagging.
3. Re-score `Cemetry Gates`, `Close To Me`, and `Can't Get There from Here` after the rule change.

## Reproduction Plan

1. Load the cached lyrics for the three sample songs.
2. Split into lines.
3. Pass the lines to `_has_duplicate_block()`.
4. Observe that the function returns `True` on normal repeated chorus material.

## Side Findings

- `duplicate_block` is the only signal on all three sample songs in the current review state after cache refresh.
- `The Offspring - Come Out And Play (Keep 'Em Separated)` remains questionable for a different reason: `unusable_lyrics`, not duplicate-block repetition.

## Follow-up: 2026-06-03

### New Evidence

- `The Smiths - Cemetry Gates` repeats the opening three lines at lines 1-3 and 4-6.
- `The Cure - Close To Me` repeats the opening chorus lines at lines 1-6 and 18-28.
- `R.E.M. - Can't Get There from Here` repeats `(I've been there I know the way) Can't get there from here` multiple times as the song’s chorus.

### Additional Findings

- The detector is exact-match based, so it cannot distinguish a repeated chorus from duplicated scrape text.

### Updated Hypotheses

- The duplicate-block check should be made chorus-aware or narrowed before it is used as a quality blocker.

### Backlog Changes

- Investigate a structure-aware duplicate heuristic.

### Updated Conclusion

- These are false positives for normal song repetition, not evidence of corrupted text.
