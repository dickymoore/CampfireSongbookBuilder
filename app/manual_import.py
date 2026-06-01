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
    # Preferred: "Artist - Title"
    if " - " in header:
        artist, title = header.split(" - ", 1)
        artist = artist.strip()
        title = title.strip()
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


def _is_chord_line(line: str) -> bool:
    # Heuristic: a line made mostly of chord tokens and separators.
    # This lets us extract lyrics from chord sheets that interleave chords+lyrics.
    stripped = line.strip()
    if stripped == "":
        return False
    if stripped.startswith("[") and stripped.endswith("]"):
        return False
    # Common chord characters: A-G, accidentals, digits, slash, parentheses, plus/minus, sus/add/maj/min, etc.
    allowed = set("ABCDEFGabcdefg0123456789#b/()|:+- .%xX\t")
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
    return chordish / float(len(tokens)) >= 0.8


def _extract_lyrics_from_chords(chords_text: str) -> str:
    lines = _normalize_text(chords_text).splitlines()
    out = []
    for line in lines:
        if _is_chord_line(line):
            continue
        # Drop obvious chord-section-only markers.
        if line.strip().lower() in {"intro", "verse", "chorus", "bridge", "interlude", "instrumental"}:
            continue
        out.append(line)
    return _normalize_text("\n".join(out))


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
        if artist is None or title is None:
            continue
        key = (artist, title)
        bucket = merged.setdefault(key, {})
        normalized_body = _normalize_text(body)
        if _looks_like_chords_header(header):
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


def write_manual_json(path: str | Path, entries: list[ManualSongEntry], field: str) -> None:
    """
    Write a manual JSON dictionary keyed by 'Artist - Title' -> text.
    field: 'lyrics' or 'chords'
    """
    if field not in {"lyrics", "chords"}:
        raise ValueError("field must be 'lyrics' or 'chords'")

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    data: dict[str, str] = {}
    for entry in entries:
        value = getattr(entry, field)
        if isinstance(value, str) and value.strip():
            data[f"{entry.artist} - {entry.title}"] = value.strip() + "\n"

    target.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
