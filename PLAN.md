# Campfire Songbook Builder Plan

## Baseline

- Total rows in catalogue: 345
- Unique song keys in refreshed report: 338
- Refreshed content records: 654
- Missing both lyrics and chords: 32
- Missing lyrics: 32
- Missing chords: 32
- Questionable both: 638
- Questionable lyrics: 638
- Questionable chords: 638

Current assessed state:

- Songs with clean lyrics only: 0
- Songs with clean chords only: 0
- Songs with both sides clean: 16

## Target

Current priority:

- Pause quality-gate cleanup work until it becomes a top-priority.

Secondary target:

- Fill chords for songs that already have clean lyrics.

Tertiary target:

- Backfill songs missing both lyrics and chords.

## Working Order

1. Add chords for the songs that already have clean lyrics.
2. Backfill the remaining missing songs and normalize the borderline entries.
3. Regenerate the favourites PDFs after each useful batch.
4. Recheck the same six counts after every pass.
5. Revisit the quality-gate queue only after the higher-priority catalogue work is done.

## Success Criteria

- Favourites generation stays complete after each refresh.
- Missing chords drops materially below 32.
- Missing both drops steadily instead of staying flat.
- Quality-gate cleanup remains deferred without blocking catalogue work.
