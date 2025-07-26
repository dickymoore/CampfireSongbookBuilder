"""Utilities for cleaning lyrics and chord text.

The cleaning functions remove contributor sections, embedded adverts and
unwanted markup tags to produce cleaner songbooks.  See individual
functions for details.
"""

import re

def remove_contributors_and_embeds(lyrics: str) -> str:
    """Remove the Contributors, Embed sections, and advertisements from lyrics."""
    lyrics = re.sub(r'^.*Contributors', '', lyrics, flags=re.DOTALL)
    lyrics = re.sub(r'Embed\s*$', '', lyrics, flags=re.MULTILINE)
    return lyrics

def remove_unwanted_phrases(lyrics: str) -> str:
    """Remove unwanted phrases and advertisements from the lyrics without removing the entire line."""
    patterns_to_remove = [
        r'You might also like.*?',
        r'See .*? LiveGet tickets as low as \$\d+',
        r'.*? Lyrics'
    ]
    for pattern in patterns_to_remove:
        lyrics = re.sub(pattern, '', lyrics, flags=re.MULTILINE)
    return lyrics

def clean_lyrics(lyrics: str) -> str:
    """Clean lyrics by removing contributors, embeds and unwanted phrases."""
    lyrics = remove_contributors_and_embeds(lyrics)
    lyrics = remove_unwanted_phrases(lyrics)
    return lyrics

MARKUP_TAGS = [
    'ch', '/ch', 'tab', '/tab', 'verse', '/verse', 'intro', '/intro',
    'outro', '/outro', 'pre-chorus', '/pre-chorus', 'chorus', '/chorus',
    'bridge', '/bridge', 'solo', '/solo', 'instrumental', '/instrumental',
    'repeat', '/repeat', 'end', '/end', 'coda', '/coda', 'refrain', '/refrain'
]

def clean_chords(chords: str) -> str:
    """Clean chord charts by removing unnecessary introductory lines and markup tags.

    This function removes email headers and bracketed markup tags (e.g. ``[ch]``)
    without stripping actual chord symbols like ``[G]``.
    """
    chords = re.sub(r'{t:.*?}\n', '', chords)
    chords = re.sub(r'{st:.*?}\n', '', chords)
    chords = re.sub(r'^(Received|From|Message-Id|To|Date|Subject|X-.*|MIME-Version|Content-.*):.*\n', '', chords, flags=re.MULTILINE)
    chords = re.sub(r'^.*To:.*$', '', chords, flags=re.MULTILINE)
    chords = re.sub(r'^.*Email:.*$', '', chords, flags=re.MULTILINE)
    pattern = r'\[(' + '|'.join(re.escape(tag) for tag in MARKUP_TAGS) + r')\]'
    chords = re.sub(pattern, '', chords, flags=re.IGNORECASE)
    chords = re.sub(r'\n\s*\n', '\n', chords)
    chords = re.sub(r'\s+\n', '\n', chords)
    return chords