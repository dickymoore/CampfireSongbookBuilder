import re


def _normalize_line_endings(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


def remove_scraped_prefix_artifacts(lyrics):
    """Remove deterministic scraped prefixes like translation lists, contributor counts, and embed counters."""
    lyrics = _normalize_line_endings(lyrics)

    # Common Genius-like prefix noise at the start of scraped lyric pages.
    lyrics = re.sub(r"(?s)^Translations.*?Lyrics", "", lyrics)
    lyrics = re.sub(r"^\s*\d+\s*Contributors?", "", lyrics, flags=re.IGNORECASE)
    lyrics = re.sub(r"\b\d+\s*Embed\b", "", lyrics, flags=re.IGNORECASE)
    lyrics = re.sub(r"\b\d+Embed\b", "", lyrics, flags=re.IGNORECASE)

    return lyrics


def remove_unwanted_phrases(lyrics):
    """Remove common scraped lyric ads / cross-promo blocks."""
    lyrics = _normalize_line_endings(lyrics)
    lyrics = re.sub(r"You might also like(?=\[)", "", lyrics, flags=re.IGNORECASE)
    lyrics = re.sub(r"See .*? LiveGet tickets as low as \$\d+(?=\[)", "", lyrics, flags=re.IGNORECASE)

    lines = lyrics.split("\n")
    out = []
    skip_mode = None

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        # Start of common promo blocks.
        if lower == "you might also like":
            skip_mode = "you_might_also_like"
            continue
        if lower.startswith("see ") and " live" in lower:
            skip_mode = "tickets"
            continue
        if lower.startswith("get tickets as low as"):
            skip_mode = "tickets"
            continue

        # End promo blocks at the next explicit section marker or a blank line run.
        if skip_mode:
            if stripped == "" or (stripped.startswith("[") and stripped.endswith("]")):
                skip_mode = None
                out.append(line if stripped == "" else stripped)
            continue

        # Remove isolated footer-y lines.
        if lower.endswith(" lyrics") and len(stripped.split()) <= 4:
            continue

        out.append(line)

    return "\n".join(out)

def clean_lyrics(lyrics):
    """Clean the lyrics by removing deterministic scrape artifacts and promo blocks."""
    if lyrics is None or not isinstance(lyrics, str):
        return ''
    lyrics = remove_scraped_prefix_artifacts(lyrics)
    lyrics = remove_unwanted_phrases(lyrics)
    # Collapse excessive blank lines.
    lyrics = _normalize_line_endings(lyrics)
    lyrics = re.sub(r"\n{3,}", "\n\n", lyrics).strip() + "\n"
    return lyrics

MARKUP_TAGS = [
    'ch', '/ch', 'tab', '/tab', 'verse', '/verse', 'intro', '/intro',
    'outro', '/outro', 'pre-chorus', '/pre-chorus', 'chorus', '/chorus',
    'bridge', '/bridge', 'solo', '/solo', 'instrumental', '/instrumental',
    'repeat', '/repeat', 'end', '/end', 'coda', '/coda', 'refrain', '/refrain'
]

def clean_chords(chords):
    """Clean the chords by removing unnecessary introductory lines, email headers, and only markup tags like [ch], [tab], etc. (not chords like [G])."""
    if chords is None or not isinstance(chords, str):
        return ''
    chords = _normalize_line_endings(chords)
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

    # Normalize whitespace without destroying chord/lyric separation.
    lines = [line.rstrip() for line in chords.split("\n")]
    out = []
    blank_run = 0
    for line in lines:
        if line.strip() == "":
            blank_run += 1
            if blank_run <= 2:
                out.append("")
            continue
        blank_run = 0
        out.append(line)

    return "\n".join(out).strip() + "\n"
