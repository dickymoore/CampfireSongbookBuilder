# Campfire Songbook Builder Plan

## Baseline

- Total rows in catalogue: 345
- Unique song keys in refreshed report: 338
- Missing both lyrics and chords: 15
- Missing lyrics: 0
- Missing chords: 2
- Questionable both: 311
- Questionable lyrics: 316
- Questionable chords: 318

Current assessed state:

- Songs with clean lyrics only: 7
- Songs with clean chords only: 3
- Songs with both sides clean: 0

## Target

Primary target:

- Reduce questionable lyrics to 0.

Secondary target:

- Fill chords for songs that already have lyrics.

Tertiary target:

- Backfill songs missing both lyrics and chords.

## Working Order

1. Clean up the 316 questionable lyrics entries until they become clean.
2. Add chords for the 7 songs that already have clean lyrics.
3. Backfill the remaining missing songs and normalize the borderline entries.
4. Regenerate the favourites PDFs after each useful batch.
5. Recheck the same six counts after every pass.

## Success Criteria

- Questionable lyrics reaches 0.
- Missing chords drops materially below 318.
- Missing both drops steadily instead of staying flat.
- Favourites generation stays complete after each refresh.
