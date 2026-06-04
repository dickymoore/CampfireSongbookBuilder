import difflib
import re
from datetime import datetime
from pathlib import Path

from app.content_models import derive_song_key


def normalize_duplicate_text(value):
    if not isinstance(value, str):
        return ""
    normalized = value.lower().strip()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _song_record(song, index):
    artist = song.get("Artist") if isinstance(song, dict) else None
    title = song.get("Title") if isinstance(song, dict) else None
    return {
        "index": index,
        "artist": artist,
        "title": title,
        "song_key": derive_song_key(artist, title),
        "normalized_artist": normalize_duplicate_text(artist),
        "normalized_title": normalize_duplicate_text(title),
    }


def find_song_duplicates(song_list, threshold=0.92):
    records = [_song_record(song, index + 1) for index, song in enumerate(song_list or [])]

    exact_map = {}
    for record in records:
        exact_map.setdefault(
            (record["normalized_artist"], record["normalized_title"]),
            [],
        ).append(record)

    exact_duplicates = [
        group
        for group in exact_map.values()
        if len(group) > 1 and group[0]["normalized_artist"] and group[0]["normalized_title"]
    ]

    fuzzy_candidates = []
    for left_index, left in enumerate(records):
        if not left["normalized_artist"] or not left["normalized_title"]:
            continue

        for right in records[left_index + 1 :]:
            if not right["normalized_artist"] or not right["normalized_title"]:
                continue

            if (
                left["normalized_artist"] == right["normalized_artist"]
                and left["normalized_title"] == right["normalized_title"]
            ):
                continue

            same_artist = left["normalized_artist"] == right["normalized_artist"]
            same_title = left["normalized_title"] == right["normalized_title"]
            if not (same_artist or same_title):
                continue

            artist_similarity = difflib.SequenceMatcher(
                None,
                left["normalized_artist"],
                right["normalized_artist"],
            ).ratio()
            title_similarity = difflib.SequenceMatcher(
                None,
                left["normalized_title"],
                right["normalized_title"],
            ).ratio()
            if same_artist:
                similarity = title_similarity
            elif same_title:
                similarity = artist_similarity
            else:
                similarity = max(artist_similarity, title_similarity)

            if similarity < threshold:
                continue

            fuzzy_candidates.append(
                {
                    "left": left,
                    "right": right,
                    "similarity": round(similarity, 3),
                    "artist_similarity": round(artist_similarity, 3),
                    "title_similarity": round(title_similarity, 3),
                    "same_artist": same_artist,
                    "same_title": same_title,
                }
            )

    fuzzy_candidates.sort(
        key=lambda item: (
            -item["similarity"],
            item["left"]["artist"] or "",
            item["left"]["title"] or "",
            item["right"]["artist"] or "",
            item["right"]["title"] or "",
        )
    )

    return {
        "total_songs": len(records),
        "exact_duplicate_groups": exact_duplicates,
        "exact_duplicate_count": sum(len(group) for group in exact_duplicates),
        "fuzzy_candidates": fuzzy_candidates,
        "fuzzy_candidate_count": len(fuzzy_candidates),
        "threshold": threshold,
    }


def write_duplicate_report(analysis, output_dir=Path("data/review/reports")):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    report_path = output_dir / f"song_duplicate_report-{timestamp}.md"

    lines = [
        "# Song Duplicate Report",
        "",
        f"- Total songs: `{analysis['total_songs']}`",
        f"- Exact duplicate groups: `{len(analysis['exact_duplicate_groups'])}`",
        f"- Fuzzy candidate pairs: `{analysis['fuzzy_candidate_count']}`",
        f"- Fuzzy threshold: `{analysis['threshold']}`",
        "",
        "## Exact Duplicates",
        "",
    ]

    if analysis["exact_duplicate_groups"]:
        for group in analysis["exact_duplicate_groups"]:
            lines.append(
                "- "
                + "; ".join(
                    f"{record['artist']} - {record['title']} (row {record['index']})"
                    for record in group
                )
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Fuzzy Candidates", ""])
    if analysis["fuzzy_candidates"]:
        for candidate in analysis["fuzzy_candidates"]:
            left = candidate["left"]
            right = candidate["right"]
            lines.append(
                "- "
                f"{left['artist']} - {left['title']} (row {left['index']}) "
                f"<-> {right['artist']} - {right['title']} (row {right['index']}) "
                f"[similarity {candidate['similarity']}]"
            )
    else:
        lines.append("- None")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path
