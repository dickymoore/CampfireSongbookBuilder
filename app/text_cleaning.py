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


def _collapse_exact_block_runs(lines, max_block_length=8):
    collapsed = []
    chunk = []

    def _append_chunk(chunk_lines):
        if not chunk_lines:
            return

        i = 0
        while i < len(chunk_lines):
            best_block_length = None
            best_run_count = 1
            max_candidate_length = min(max_block_length, (len(chunk_lines) - i) // 2)

            for block_length in range(1, max_candidate_length + 1):
                block = chunk_lines[i : i + block_length]
                run_count = 1

                while True:
                    start = i + run_count * block_length
                    end = start + block_length
                    if end > len(chunk_lines):
                        break
                    if chunk_lines[start:end] != block:
                        break
                    run_count += 1

                if run_count > 1:
                    span = block_length * run_count
                    if best_block_length is None:
                        best_block_length = block_length
                        best_run_count = run_count
                        best_span = span
                        continue

                    best_span = best_block_length * best_run_count
                    if span > best_span or (span == best_span and block_length > best_block_length):
                        best_block_length = block_length
                        best_run_count = run_count

            if best_block_length is None:
                collapsed.append(chunk_lines[i])
                i += 1
                continue

            block = chunk_lines[i : i + best_block_length]
            collapsed.extend(block)
            if best_run_count > 1 and block:
                collapsed[-1] = "{} x{}".format(collapsed[-1], best_run_count)
            i += best_block_length * best_run_count

    for line in lines:
        stripped = line.strip()
        if not stripped:
            _append_chunk(chunk)
            chunk = []
            collapsed.append(line)
            continue

        chunk.append(line)

    _append_chunk(chunk)
    return collapsed

def clean_lyrics(lyrics):
    """Clean the lyrics by removing deterministic scrape artifacts and promo blocks."""
    if lyrics is None or not isinstance(lyrics, str):
        return ''
    lyrics = remove_scraped_prefix_artifacts(lyrics)
    lyrics = remove_unwanted_phrases(lyrics)
    # Collapse excessive blank lines.
    lyrics = _normalize_line_endings(lyrics)
    lines = [line.rstrip() for line in lyrics.split("\n")]
    lines = _collapse_exact_block_runs(lines)
    lyrics = "\n".join(lines)
    lyrics = re.sub(r"\n{3,}", "\n\n", lyrics).strip() + "\n"
    return lyrics

MARKUP_TAGS = [
    'ch', '/ch', 'tab', '/tab', 'verse', '/verse', 'intro', '/intro',
    'outro', '/outro', 'pre-chorus', '/pre-chorus', 'chorus', '/chorus',
    'bridge', '/bridge', 'solo', '/solo', 'instrumental', '/instrumental',
    'repeat', '/repeat', 'end', '/end', 'coda', '/coda', 'refrain', '/refrain'
]


_CHORD_TOKEN_RE = re.compile(
    r"^[A-Ga-g](?:#|b)?(?:maj|min|m|sus|add|dim|aug)?[0-9]*(?:/[A-Ga-g](?:#|b)?)?$"
)
_TAB_STAFF_RE = re.compile(r"^\s*[eEBGDA]\|")
_CHORD_DIAGRAM_RE = re.compile(r"^\s*\|[-0-9xXhpb/\\~() ]+\|\s*$")
_BEAT_COUNT_RE = re.compile(r"^(?:\s*\[\d+\]\s*\[\+\]\s*){4,}$")
_COMMENTARY_LINE_RE = re.compile(
    r"^\s*(?:"
    r"tab(?:bed)?\s+by\b|"
    r"tab\s+from\b|"
    r"note\b|"
    r"received:\s+from\b|"
    r"this\s+is\s+the\b|"
    r"when\s+playing\b|"
    r"i\s+prefer\b|"
    r"i\s+added\b|"
    r"also,\s+i(?:'|’)m\s+not\s+certain\b|"
    r"sounds\s+like\b|"
    r"chords\s+used\b|"
    r"updated\s+the\s+tab\b"
    r")",
    flags=re.IGNORECASE,
)
_COMMENTARY_BLOCK_START_RE = re.compile(
    r"^\s*(?:"
    r"\(?\s*tab\s+from\b|"
    r"note:|"
    r"this\s+is\s+the\b|"
    r"in\s+the\s+recording\b|"
    r"i\s+prefer\b|"
    r"four\s+chords\s+for\s+the\s+whole\s+song\b|"
    r"david\s+bowie\s+lyrics\s+as\s+written\b|"
    r"the\s+chords\s+repeat\s+themselves\b|"
    r"also,\s+i(?:'|’)m\s+not\s+certain\b|"
    r"when\s+playing\b|"
    r"updated\s+the\s+tab\b"
    r")",
    flags=re.IGNORECASE,
)
_ASTERISK_SEPARATOR_RE = re.compile(r"^\s*\*{8,}\s*$")


def _is_non_musical_chord_line(line):
    stripped = line.strip()
    if not stripped:
        return False
    return bool(
        _TAB_STAFF_RE.match(stripped)
        or _CHORD_DIAGRAM_RE.match(stripped)
        or _BEAT_COUNT_RE.match(stripped)
        or _ASTERISK_SEPARATOR_RE.match(stripped)
        or _COMMENTARY_LINE_RE.match(stripped)
    )


def _strip_commentary_blocks(lines):
    stripped_lines = []
    skipping = False

    for line in lines:
        stripped = line.strip()
        if skipping:
            if (
                not stripped
                or stripped.startswith("[")
                or _is_chord_only_line(line)
                or _CHORD_TOKEN_RE.match(stripped)
            ):
                skipping = False
            else:
                continue

        if _COMMENTARY_BLOCK_START_RE.match(stripped):
            skipping = True
            continue

        stripped_lines.append(line)

    return stripped_lines


def _is_chord_only_line(line):
    stripped = line.strip()
    if not stripped:
        return False
    tokens = [token for token in re.split(r"\s+", stripped) if token]
    if not tokens:
        return False
    if any(token.lower().startswith(("verse", "chorus", "bridge", "intro", "outro", "interlude")) for token in tokens):
        return False
    return all(
        token in {"x", "X", "%", "/"} or bool(_CHORD_TOKEN_RE.match(token))
        for token in tokens
    )


def _collapse_vertical_chord_runs(lines):
    collapsed = []
    run = []

    def flush_run():
        nonlocal run
        if run:
            collapsed.append(" / ".join(item.strip() for item in run))
            run = []

    for line in lines:
        if _is_chord_only_line(line):
            run.append(line)
            continue
        if run and line.strip():
            flush_run()
        elif run and not line.strip():
            flush_run()
        collapsed.append(line)

    flush_run()
    return collapsed

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
    lines = _strip_commentary_blocks(lines)
    lines = [line for line in lines if not _is_non_musical_chord_line(line)]
    lines = _collapse_vertical_chord_runs(lines)
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
