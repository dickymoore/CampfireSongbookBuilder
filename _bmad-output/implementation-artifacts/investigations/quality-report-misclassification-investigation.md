# Investigation: quality-report-misclassification

## Hand-off Brief

1. **What happened.** The quality report is labeling cached songs as `missing` even when lyrics and chords exist in `data/cache/*.jsonl`; confirmed on `Feargal Sharkey - A Good Heart`.
2. **Where the case stands.** Root cause is confirmed in the quality classifier: error-severity junk signals are mapped to `quality: "missing"`, and `evaluate_cached_content()` reports that as `quality_missing`.
3. **What's needed next.** Decide whether `missing` should remain the hard-fail bucket for duplicate blocks / bracket noise, or whether those signals should be downgraded to `questionable`.

## Case Info

| Field            | Value                                                                      |
| ---------------- | -------------------------------------------------------------------------- |
| Ticket           | N/A                                                                        |
| Date opened      | 2026-06-03                                                                 |
| Status           | Active                                                                     |
| System           | Linux workstation, repository root `/home/dicky/CampfireSongbookBuilder`   |
| Evidence sources | cache JSONL, review report JSON, source code                                |

## Problem Statement

The report `data/review/reports/quality_run-generate_from_cache-20260603T141329+0100.json` says some songs are `missing` even though cached lyrics/chords exist.

## Evidence Inventory

| Source | Status   | Notes |
| ------ | -------- | ----- |
| Cache JSONL | Available | `Feargal Sharkey - A Good Heart` has cached lyrics and chords. |
| Quality report JSON | Available | First entries classify `Feargal Sharkey - A Good Heart` as `missing`. |
| Source code | Available | `app/quality_assessment.py`, `app/generation_filtering.py`, `app/document_creation.py`. |

## Investigation Backlog

| # | Path to Explore | Priority | Status | Notes |
| - | --------------- | -------- | ------ | ----- |
| 1 | `app/quality_assessment.py` missing/junk classification | High | Done | Error-severity junk signals map to `missing`. |
| 2 | `app/generation_filtering.py` decision mapping | High | Done | `quality == "missing"` becomes `decision_source = "quality_missing"`. |
| 3 | Report generation path | Medium | Done | Report is derived from current cached content + quality state. |

## Confirmed Findings

### Finding 1: Cached content exists for the song that was reported missing

**Evidence:** `data/cache/lyrics_cache.jsonl` and `data/cache/chords_cache.jsonl` entries for `Feargal Sharkey - A Good Heart`; lyrics start with `A Good Heart Lyrics...`, chords are present.

**Detail:** The song is not absent from cache. The missing label is not caused by no cached row.

### Finding 2: Error-severity junk signals force `quality: "missing"`

**Evidence:** `app/quality_assessment.py:264-291` and `app/quality_assessment.py:299-303` (in `assess_junk_content()`); `app/quality_assessment.py:314-332` (in `assess_candidate_quality()`).

**Detail:** `duplicate_block` and `excessive_bracket_noise` are created as error-severity signals. `assess_candidate_quality()` sets `quality = "missing"` if any sub-result is missing or if junk signals include an error.

### Finding 3: The report follows the quality result verbatim

**Evidence:** `app/generation_filtering.py:93-130`.

**Detail:** `evaluate_cached_content()` maps `quality == "missing"` to `decision_source = "quality_missing"` and excludes the song by default.

## Deduced Conclusions

### Deduction 1: The report is internally consistent, but the label is semantically misleading

**Based on:** Confirmed Findings 1-3

**Reasoning:** The report is not claiming the cache row is absent. It is claiming the song failed the quality classifier strongly enough to land in the `missing` bucket.

**Conclusion:** The bug is a classification-policy problem, not a cache-loss problem.

## Hypothesized Paths

### Hypothesis 1: Downgrade duplicate-block / bracket-noise error signals to `questionable`

**Status:** Open

**Theory:** Songs with repeated choruses or normal repeated sections are being over-penalized by `duplicate_block`, and the report would be more useful if those cases stayed visible as `questionable`.

**Supporting indicators:** Earlier investigation already identified repeated choruses in several songs as false positives.

**Would confirm:** Reclassifying those signals changes the report from `missing` to `questionable` for the affected songs.

**Would refute:** A different classification rule is already intended and documented for `missing`.

**Resolution:** Pending policy decision.

## Missing Evidence

| Gap | Impact | How to Obtain |
| --- | ------ | ------------- |
| Expected semantics for `missing` vs `questionable` | Needed to decide whether the classifier or the report wording should change | User policy decision |

## Source Code Trace

| Element | Detail |
| ------- | ------ |
| Error origin | `app/quality_assessment.py:264-291`, `app/quality_assessment.py:314-332` |
| Trigger | Cached content contains repeated blocks or excessive bracket noise |
| Condition | `assess_candidate_quality()` sees any sub-result with `quality == "missing"` |
| Related files | `app/generation_filtering.py`, `app/document_creation.py` |

## Conclusion

**Confidence:** High

The quality report is not wrong about the classifier’s current decision, but it is misleading if interpreted as “no cached content exists.” The cached lyrics/chords are present; the classifier is marking them `missing` because junk heuristics currently escalate some content-quality problems to the hard-fail bucket.

## Recommended Next Steps

### Fix direction

Either keep the current policy and document `missing` as “present but unusable,” or downgrade duplicate-block / bracket-noise-only failures to `questionable` so the report distinguishes absent content from noisy content.

### Diagnostic

Add a regression test for a song with cached content and a repeated chorus to verify the expected quality bucket.

## Reproduction Plan

1. Load `Feargal Sharkey - A Good Heart` from cache.
2. Run `assess_candidate_quality()` on the cached lyrics/chords.
3. Observe `quality: "missing"` when duplicate-block or bracket-noise errors are present.

## Side Findings

- `Sea Urchins - Time Is All I've Seen` exists in cache, but no quality-status record is present for it yet.
