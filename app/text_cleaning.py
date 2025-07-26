import re

def remove_contributors_and_embeds(lyrics):
    """Remove the Contributors, Embed sections, and unwanted advertisements from the lyrics."""
    lyrics = re.sub(r'^.*Contributors', '', lyrics, flags=re.DOTALL)
    lyrics = re.sub(r'Embed\s*$', '', lyrics, flags=re.MULTILINE)
    return lyrics

def remove_unwanted_phrases(lyrics):
    """Remove unwanted phrases and advertisements from the lyrics without removing the entire line."""
    patterns_to_remove = [
        r'You might also like.*?',
        r'See .*? LiveGet tickets as low as \$\d+',
        r'.*? Lyrics'
    ]

    # Remove each pattern, but only the matched part, not the entire line
    for pattern in patterns_to_remove:
        lyrics = re.sub(pattern, '', lyrics, flags=re.MULTILINE)

    return lyrics

def clean_lyrics(lyrics):
    """Clean the lyrics by removing contributors, embeds, and unwanted phrases."""
    lyrics = remove_contributors_and_embeds(lyrics)
    lyrics = remove_unwanted_phrases(lyrics)
    return lyrics

MARKUP_TAGS = [
    'ch', '/ch', 'tab', '/tab', 'verse', '/verse', 'intro', '/intro',
    'outro', '/outro', 'pre-chorus', '/pre-chorus', 'chorus', '/chorus',
    'bridge', '/bridge', 'solo', '/solo', 'instrumental', '/instrumental',
    'repeat', '/repeat', 'end', '/end', 'coda', '/coda', 'refrain', '/refrain'
]

def clean_chords(chords):
    """Clean the chords by removing unnecessary introductory lines, email headers, and only markup tags like [ch], [tab], etc. (not chords like [G])."""
    # Remove lines starting with {t:...} and {st:...}
    chords = re.sub(r'{t:.*?}\n', '', chords)
    chords = re.sub(r'{st:.*?}\n', '', chords)

    # Remove email headers
    chords = re.sub(r'^(Received|From|Message-Id|To|Date|Subject|X-.*|MIME-Version|Content-.*):.*\n', '', chords, flags=re.MULTILINE)

    # Remove other unnecessary lines often found in chords
    chords = re.sub(r'^.*To:.*$', '', chords, flags=re.MULTILINE)
    chords = re.sub(r'^.*Email:.*$', '', chords, flags=re.MULTILINE)

    # Remove only known markup tags in brackets (case-insensitive)
    pattern = r'\[(' + '|'.join(re.escape(tag) for tag in MARKUP_TAGS) + r')\]'
    chords = re.sub(pattern, '', chords, flags=re.IGNORECASE)

    # Remove extra newlines and spaces
    chords = re.sub(r'\n\s*\n', '\n', chords)
    chords = re.sub(r'\s+\n', '\n', chords)

    return chords
