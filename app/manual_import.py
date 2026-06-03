import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ManualSongEntry:
    artist: str
    title: str
    lyrics: str | None = None
    chords: str | None = None


_HEADER_RE = re.compile(r"^\s*#\s*(?P<header>.+?)\s*$")


def _normalize_text(text: str) -> str:
    # Normalize line endings, strip trailing spaces, and cap blank-line runs.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]

    normalized = []
    blank_run = 0
    for line in lines:
        if line.strip() == "":
            blank_run += 1
            if blank_run <= 2:
                normalized.append("")
            continue
        blank_run = 0
        normalized.append(line)
    return "\n".join(normalized).strip() + "\n"


def _looks_like_chords_header(header: str) -> bool:
    header_lower = header.lower()
    return "chord" in header_lower


def _parse_artist_title(header: str) -> tuple[str | None, str | None]:
    header = header.strip()
    # Drop trailing parenthetical notes like "(add this to favourites too please)".
    header = re.sub(r"\s*\([^)]*\)\s*$", "", header).strip()

    # Preferred: "Artist - Title"
    if " - " in header:
        artist, title = header.split(" - ", 1)
        artist = artist.strip()
        title = title.strip()
        title = re.sub(r"\s+(lyrics|chords)\s*$", "", title, flags=re.IGNORECASE).strip()
        if artist and title:
            return artist, title

    # Fallback: if header ends with "lyrics"/"chords", strip and retry.
    header = re.sub(r"\s+(lyrics|chords)\s*$", "", header, flags=re.IGNORECASE).strip()
    if " - " in header:
        artist, title = header.split(" - ", 1)
        artist = artist.strip()
        title = title.strip()
        if artist and title:
            return artist, title

    # Alternative: "Title by Artist"
    if " by " in header.lower():
        # split on last ' by ' to avoid titles that contain 'by'
        parts = re.split(r"\s+by\s+", header, flags=re.IGNORECASE)
        if len(parts) >= 2:
            title = parts[0].strip()
            artist = parts[1].strip()
            title = re.sub(r"\s+(lyrics|chords)\s*$", "", title, flags=re.IGNORECASE).strip()
            if artist and title:
                return artist, title

    return None, None


def _normalize_title(title: str) -> str:
    title = title.strip().lower()
    title = re.sub(r"\s+", " ", title)
    # Drop punctuation for fuzzy matching.
    title = re.sub(r"[^a-z0-9 ]", "", title)
    return title.strip()


def _infer_artist_title(header: str, known_songs: dict[str, tuple[str, str]]) -> tuple[str | None, str | None]:
    """
    Infer (artist, title) from a header that only contains a title, using a map of
    normalized_title -> (artist, title).
    """
    header = re.sub(r"\s+(lyrics|chords)\s*$", "", header, flags=re.IGNORECASE).strip()
    normalized = _normalize_title(header)
    return known_songs.get(normalized, (None, None))


def _canonicalize_artist_title(
    artist: str | None,
    title: str | None,
    known_songs: dict[str, tuple[str, str]] | None,
) -> tuple[str | None, str | None]:
    if artist is None or title is None or not known_songs:
        return artist, title
    return known_songs.get(_normalize_title(title), (artist, title))


def _is_chord_line(line: str) -> bool:
    # Heuristic: a line made mostly of chord tokens and separators.
    # This lets us extract lyrics from chord sheets that interleave chords+lyrics.
    stripped = line.strip()
    if stripped == "":
        return False
    if stripped.startswith("[") and stripped.endswith("]"):
        return False
    # Common chord characters: A-G, accidentals, digits, slash, parentheses, plus/minus, sus/add/maj/min, etc.
    # Allow chord modifiers (maj/min/sus/add/dim/aug, etc). We keep this fairly
    # permissive, then rely on token-level chord matching below to avoid treating
    # lyric sentences as chord lines.
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789#b/()|:+-_.%xX\t ")
    if any(ch not in allowed for ch in stripped):
        return False
    tokens = [t for t in re.split(r"\s+", stripped) if t and t != "|"]
    if not tokens:
        return False
    chordish = 0
    for tok in tokens:
        if tok in {"x", "X", "%"}:
            chordish += 1
            continue
        if re.match(r"^[A-Ga-g](?:#|b)?[0-9]?(?:maj|min|m|sus|add|dim|aug)?[0-9]*(?:/[A-Ga-g](?:#|b)?)?$", tok):
            chordish += 1
            continue
        if re.match(r"^[A-Ga-g](?:#|b)?(?:maj|min|m|sus|add|dim|aug)[0-9]*(?:/[A-Ga-g](?:#|b)?)?$", tok):
            chordish += 1
            continue
    if chordish == 0:
        return False
    return chordish / float(len(tokens)) >= 0.8


def _extract_lyrics_from_chords(chords_text: str) -> str:
    section_only_re = re.compile(
        r"^(intro|verse|chorus|bridge|interlude|instrumental|outro|pre-chorus|solo)(\s+\d+)?$",
        flags=re.IGNORECASE,
    )
    bracketed_section_re = re.compile(
        r"^\[(intro|instrumental|outro|solo)\]$",
        flags=re.IGNORECASE,
    )

    def _is_chord_token(tok: str) -> bool:
        if tok in {"x", "X", "%"} or re.match(r"^(?:[xX]\d+|\d+[xX])$", tok):
            return True
        if re.match(
            r"^[A-Ga-g](?:#|b)?[0-9]?(?:maj|min|m|sus|add|dim|aug)?[0-9]*(?:/[A-Ga-g](?:#|b)?)?$",
            tok,
        ):
            return True
        if re.match(
            r"^[A-Ga-g](?:#|b)?(?:maj|min|m|sus|add|dim|aug)[0-9]*(?:/[A-Ga-g](?:#|b)?)?$",
            tok,
        ):
            return True
        return False

    def _strip_leading_chords(line: str) -> str:
        # Remove leading chord tokens from a line like: "Em Bm A So sweet"
        tokens = [t for t in re.split(r"\s+", line.strip()) if t]
        kept = []
        stripping = True
        removed = 0
        for tok in tokens:
            if stripping and _is_chord_token(tok):
                removed += 1
                continue
            stripping = False
            kept.append(tok)
        return (" ".join(kept).strip(), removed)

    lines = _normalize_text(chords_text).splitlines()
    out = []
    for line in lines:
        remainder, removed = _strip_leading_chords(line)
        if removed >= 2:
            # Inline chords like "Em Bm A So sweet" -> keep just the lyric part.
            if remainder:
                out.append(remainder)
            continue
        if _is_chord_line(line):
            # Pure chord line: drop it.
            continue
        # Drop obvious chord-section-only markers.
        stripped = line.strip()
        if section_only_re.match(stripped):
            continue
        if bracketed_section_re.match(stripped):
            continue
        if re.match(r"^(no capo|capo\b.*|key:.*|bpm:.*)$", stripped, flags=re.IGNORECASE):
            continue
        if re.match(r"^(?:[xX]\d+|\d+[xX])$", stripped):
            continue
        out.append(line)
    return _normalize_text("\n".join(out))


def _chord_line_stats(text: str) -> tuple[int, int, float]:
    lines = _normalize_text(text).splitlines()
    if not lines:
        return 0, 0, 0.0
    considered = 0
    chordish = 0
    for line in lines:
        if line.strip() == "":
            continue
        considered += 1
        if _is_chord_line(line):
            chordish += 1
    if considered == 0:
        return 0, chordish, 0.0
    return considered, chordish, chordish / float(considered)


def parse_manual_import(text: str, known_songs: dict[str, tuple[str, str]] | None = None) -> list[ManualSongEntry]:
    """
    Parse a human-pasted manual import blob.

    Expected format:
      # Artist - Title lyrics
      <lyrics...>
      # Artist - Title chords
      <chords...>

    If a chords section contains lyrics inline, the caller can extract lyrics with
    _extract_lyrics_from_chords().
    """
    text = _normalize_text(text)
    lines = text.splitlines(keepends=True)

    sections: list[tuple[str, str]] = []
    current_header = None
    current_body: list[str] = []

    for line in lines:
        m = _HEADER_RE.match(line.rstrip("\n"))
        if m:
            if current_header is not None:
                sections.append((current_header, "".join(current_body)))
            current_header = m.group("header")
            current_body = []
            continue
        current_body.append(line)

    if current_header is not None:
        sections.append((current_header, "".join(current_body)))

    merged: dict[tuple[str, str], dict[str, str]] = {}
    for header, body in sections:
        artist, title = _parse_artist_title(header)
        if (artist is None or title is None) and known_songs:
            artist, title = _infer_artist_title(header, known_songs)
        artist, title = _canonicalize_artist_title(artist, title, known_songs)
        if artist is None or title is None:
            continue
        key = (artist, title)
        bucket = merged.setdefault(key, {})
        normalized_body = _normalize_text(body)
        if _looks_like_chords_header(header):
            bucket["chords"] = normalized_body
            continue

        # If the section looks like a chord sheet (lots of chord-only lines),
        # treat it as chords; we'll extract lyrics from it later.
        considered, chordish, fraction = _chord_line_stats(normalized_body)
        # More permissive chord detection for real-world copy/pastes where
        # chord headers and lyric lines are interleaved.
        if chordish >= 3 and fraction >= 0.08:
            bucket["chords"] = normalized_body
        else:
            bucket["lyrics"] = normalized_body

    entries: list[ManualSongEntry] = []
    for (artist, title), bucket in sorted(merged.items()):
        lyrics = bucket.get("lyrics")
        chords = bucket.get("chords")
        # If lyrics missing but chords exist, attempt extraction.
        if (lyrics is None or lyrics.strip() == "") and chords:
            extracted = _extract_lyrics_from_chords(chords)
            if extracted.strip():
                lyrics = extracted
        entries.append(ManualSongEntry(artist=artist, title=title, lyrics=lyrics, chords=chords))

    return entries


def _load_manual_json(path: str | Path) -> dict[str, str]:
    target = Path(path)
    if not target.exists():
        return {}
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        str(key): value
        for key, value in payload.items()
        if isinstance(key, str) and isinstance(value, str) and value.strip()
    }


def write_manual_json(
    path: str | Path,
    entries: list[ManualSongEntry],
    field: str,
    merge_existing: bool = True,
) -> None:
    """
    Write a manual JSON dictionary keyed by 'Artist - Title' -> text.
    field: 'lyrics' or 'chords'
    """
    if field not in {"lyrics", "chords"}:
        raise ValueError("field must be 'lyrics' or 'chords'")

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    data: dict[str, str] = _load_manual_json(target) if merge_existing else {}
    for entry in entries:
        value = getattr(entry, field)
        if isinstance(value, str) and value.strip():
            data[f"{entry.artist} - {entry.title}"] = value.strip() + "\n"

    target.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
