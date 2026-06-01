import logging
import os
from datetime import datetime
from pathlib import Path

from docx import Document

from app.content_models import derive_song_key
from app.content_scoring import compose_content_score
from app.document_verification import (
    DEFAULT_DOCUMENT_QUALITY_PATH,
    evaluate_document_artifact,
    refresh_document_verification_state,
)
from app.document_formatting import (
    add_header_footer,
    create_two_column_section,
    set_document_margins,
    set_paragraph_font,
    sort_songs,
)
from app.generation_filtering import build_current_content_hashes, evaluate_cached_content
from app.review_state import (
    DEFAULT_CONTENT_SCORES_PATH,
    DEFAULT_QUALITY_STATUS_PATH,
    DEFAULT_REVIEW_DECISIONS_PATH,
    load_content_scores,
    load_quality_status,
    load_review_decisions,
    save_content_scores,
)
from app.pdf_generation import convert_document_to_pdf
from app.review_gate import compute_review_gate_decisions
from app.review_gate_state import refresh_review_gate_state
from app.text_cleaning import clean_chords, clean_lyrics


# Configure logging
logger = logging.getLogger(__name__)

QUALITY_STATUS_PATH = DEFAULT_QUALITY_STATUS_PATH
REVIEW_DECISIONS_PATH = DEFAULT_REVIEW_DECISIONS_PATH
DOCUMENT_QUALITY_PATH = DEFAULT_DOCUMENT_QUALITY_PATH
CONTENT_SCORES_PATH = DEFAULT_CONTENT_SCORES_PATH
DEFAULT_REPORT_SOURCE = "generate_from_cache"


def _song_value(song, preferred_key, fallback_key):
    if isinstance(song, dict):
        if preferred_key in song:
            return song.get(preferred_key)
        return song.get(fallback_key)
    return None


def _song_artist(song):
    return _song_value(song, "Artist", "artist")


def _song_title(song):
    return _song_value(song, "Title", "title")


def _song_key(song):
    return _song_value(song, "song_key", "song_key")


def _build_report_entry(song, content_type, generation_result, included=None, reason=None):
    included_value = generation_result["included"] if included is None else included
    reason_value = generation_result["reason"] if reason is None else reason
    artist = _song_artist(song)
    title = _song_title(song)

    return {
        "artist": artist,
        "title": title,
        "song_key": _song_key(song) or derive_song_key(artist, title),
        "content_type": content_type,
        "content_hash": generation_result["content_hash"],
        "quality": generation_result["quality"],
        "included": included_value,
        "decision_source": generation_result["decision_source"],
        "reason": reason_value,
        "signals": generation_result["signals"],
        "quality_status": generation_result["quality_status"],
        "review_decision": generation_result["review_decision"],
    }


def _markdown_song_block(artist, title, content):
    return [
        "# {} by {}".format(title, artist),
        "",
        "```text",
        content,
        "```",
        "",
    ]


def _write_markdown_document(output_path, lines):
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    logger.info("Markdown document saved as %s.", target_path)


def _save_document_verification_records(records, remove_artifact_paths=None, updated_at=None):
    refresh_document_verification_state(
        DOCUMENT_QUALITY_PATH,
        records,
        remove_artifact_paths=remove_artifact_paths,
        updated_at=updated_at,
    )


def _flatten_content_score_records(state):
    records = []
    for song_entries in state.get("entries", {}).values():
        records.extend(song_entries.values())
    return records


def create_document_from_cache(
    song_list,
    lyrics_cache,
    chords_cache,
    lyrics_output=None,
    chords_output=None,
    selection_records=None,
    report_source=None,
    pdf_output=False,
):
    logger.debug("Running create_document_from_cache function")

    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    current_content_hashes = build_current_content_hashes(lyrics_cache, chords_cache)
    quality_status_state, quality_status_errors = load_quality_status(QUALITY_STATUS_PATH)
    if quality_status_errors:
        logger.warning(
            "Quality status load reported %d recoverable issue(s).",
            len(quality_status_errors),
        )

    review_decision_state, review_decision_errors = load_review_decisions(
        REVIEW_DECISIONS_PATH,
        current_content_hashes=current_content_hashes,
    )
    if review_decision_errors:
        logger.warning(
            "Review decisions load reported %d recoverable issue(s).",
            len(review_decision_errors),
        )

    if lyrics_output:
        logger.debug("Initializing lyrics document")
        lyrics_document = Document()
        set_document_margins(lyrics_document, 0.5)
        create_two_column_section(lyrics_document)
        add_header_footer(lyrics_document)
        lyrics_markdown_lines = []

    if chords_output:
        logger.debug("Initializing chords document")
        chords_document = Document()
        set_document_margins(chords_document, 0.5)
        create_two_column_section(chords_document)
        add_header_footer(chords_document)
        chords_markdown_lines = []

    songs_to_process = selection_records if selection_records is not None else sort_songs(song_list)
    report_entries = []
    selection_issues = []
    pdf_outputs = []
    pdf_errors = []
    document_verification_records = []
    remove_stale_verification_paths = []
    content_score_records = []

    for song in songs_to_process:
        artist = _song_artist(song)
        title = _song_title(song)
        cache_key = _song_key(song) or derive_song_key(artist, title)
        lyrics_quality_status = quality_status_state.get("entries", {}).get(cache_key, {}).get("lyrics")
        lyrics_review_decision = review_decision_state.get("entries", {}).get(cache_key, {}).get("lyrics")
        chords_quality_status = quality_status_state.get("entries", {}).get(cache_key, {}).get("chords")
        chords_review_decision = review_decision_state.get("entries", {}).get(cache_key, {}).get("chords")

        if lyrics_output:
            lyrics = lyrics_cache.get(cache_key) if isinstance(lyrics_cache, dict) else None
            generation_result = evaluate_cached_content(
                artist,
                title,
                "lyrics",
                lyrics,
                quality_status_record=lyrics_quality_status,
                review_decision_record=lyrics_review_decision,
            )
            if generation_result.get("content_hash") is not None:
                try:
                    content_score_records.append(
                        compose_content_score(
                            generation_result.get("quality_status") or {},
                            scored_at=generated_at,
                        )
                    )
                except ValueError as exc:
                    logger.warning("Failed to compute lyrics content score for %s: %s", cache_key, exc)

            report_included = generation_result["included"]
            report_reason = generation_result["reason"]
            if generation_result["included"] and isinstance(lyrics, str) and lyrics != "":
                lyrics = clean_lyrics(lyrics)
                num_characters = len(lyrics)
                logger.debug("Adding lyrics for %s by %s", title, artist)

                if num_characters <= 5000:
                    heading = lyrics_document.add_heading("{} by {}".format(title, artist), level=1)
                    set_paragraph_font(heading, 14)
                    paragraph = lyrics_document.add_paragraph()
                    lines = lyrics.split("\n")
                    for i, line in enumerate(lines):
                        if i > 0:
                            paragraph.add_run().add_break()
                        paragraph.add_run(line)
                    set_paragraph_font(paragraph, 12)
                    lyrics_markdown_lines.extend(_markdown_song_block(artist, title, lyrics))
                else:
                    report_included = False
                    report_reason = "Lyrics are too long and were excluded from the document."
                    logger.debug("Lyrics for %s are too long and have been excluded.", title)
            else:
                logger.debug(
                    "Skipping lyrics for %s by %s: %s",
                    title,
                    artist,
                    report_reason,
                )

            report_entries.append(
                _build_report_entry(
                    song,
                    "lyrics",
                    generation_result,
                    included=report_included,
                    reason=report_reason,
                )
            )
            if selection_records is not None and generation_result["quality"] == "missing":
                selection_issues.append(
                    {
                        "selection_name": None,
                        "issue_type": "missing_content",
                        "artist": artist,
                        "title": title,
                        "song_key": cache_key,
                        "content_type": "lyrics",
                        "reason": report_reason,
                    }
                )

        if chords_output:
            chords = chords_cache.get(cache_key) if isinstance(chords_cache, dict) else None
            generation_result = evaluate_cached_content(
                artist,
                title,
                "chords",
                chords,
                quality_status_record=chords_quality_status,
                review_decision_record=chords_review_decision,
            )
            if generation_result.get("content_hash") is not None:
                try:
                    content_score_records.append(
                        compose_content_score(
                            generation_result.get("quality_status") or {},
                            scored_at=generated_at,
                        )
                    )
                except ValueError as exc:
                    logger.warning("Failed to compute chords content score for %s: %s", cache_key, exc)
            report_entries.append(_build_report_entry(song, "chords", generation_result))
            if selection_records is not None and generation_result["quality"] == "missing":
                selection_issues.append(
                    {
                        "selection_name": None,
                        "issue_type": "missing_content",
                        "artist": artist,
                        "title": title,
                        "song_key": cache_key,
                        "content_type": "chords",
                        "reason": generation_result["reason"],
                    }
                )

            if generation_result["included"] and isinstance(chords, str) and chords != "":
                chords = clean_chords(chords)
                logger.debug("Adding chords for %s by %s", title, artist)
                heading = chords_document.add_heading("{} by {}".format(title, artist), level=1)
                set_paragraph_font(heading, 14)
                paragraph = chords_document.add_paragraph()
                lines = chords.split("\n")
                for i, line in enumerate(lines):
                    if i > 0:
                        paragraph.add_run().add_break()
                    paragraph.add_run(line)
                set_paragraph_font(paragraph, 12)
                chords_markdown_lines.extend(_markdown_song_block(artist, title, chords))
            else:
                logger.debug(
                    "Skipping chords for %s by %s: %s",
                    title,
                    artist,
                    generation_result["reason"],
                )

    if lyrics_output:
        lyrics_markdown_path = Path(lyrics_output).with_suffix(".md")
        _write_markdown_document(lyrics_markdown_path, lyrics_markdown_lines)
        document_verification_records.append(
            evaluate_document_artifact(
                lyrics_markdown_path,
                artifact_type="markdown",
                verified_at=generated_at,
            )
        )
        os.makedirs(os.path.dirname(lyrics_output), exist_ok=True)
        lyrics_document.save(lyrics_output)
        logger.info("Lyrics document saved as %s.", lyrics_output)
        document_verification_records.append(
            evaluate_document_artifact(
                lyrics_output,
                artifact_type="docx",
                verified_at=generated_at,
            )
        )
        if pdf_output:
            lyrics_pdf_path, lyrics_pdf_error = convert_document_to_pdf(lyrics_output)
            if lyrics_pdf_path is not None:
                pdf_outputs.append(str(lyrics_pdf_path))
                document_verification_records.append(
                    evaluate_document_artifact(
                        lyrics_pdf_path,
                        artifact_type="pdf",
                        verified_at=generated_at,
                    )
                )
            if lyrics_pdf_error is not None:
                remove_stale_verification_paths.append(
                    str(Path(lyrics_output).with_suffix(".pdf"))
                )
                pdf_errors.append(
                    {
                        "source": lyrics_output,
                        "target": str(Path(lyrics_output).with_suffix(".pdf")),
                        "reason": lyrics_pdf_error,
                    }
                )

    if chords_output:
        chords_markdown_path = Path(chords_output).with_suffix(".md")
        _write_markdown_document(chords_markdown_path, chords_markdown_lines)
        document_verification_records.append(
            evaluate_document_artifact(
                chords_markdown_path,
                artifact_type="markdown",
                verified_at=generated_at,
            )
        )
        os.makedirs(os.path.dirname(chords_output), exist_ok=True)
        chords_document.save(chords_output)
        logger.info("Chords document saved as %s.", chords_output)
        document_verification_records.append(
            evaluate_document_artifact(
                chords_output,
                artifact_type="docx",
                verified_at=generated_at,
            )
        )
        if pdf_output:
            chords_pdf_path, chords_pdf_error = convert_document_to_pdf(chords_output)
            if chords_pdf_path is not None:
                pdf_outputs.append(str(chords_pdf_path))
                document_verification_records.append(
                    evaluate_document_artifact(
                        chords_pdf_path,
                        artifact_type="pdf",
                        verified_at=generated_at,
                    )
                )
            if chords_pdf_error is not None:
                remove_stale_verification_paths.append(
                    str(Path(chords_output).with_suffix(".pdf"))
                )
                pdf_errors.append(
                    {
                        "source": chords_output,
                        "target": str(Path(chords_output).with_suffix(".pdf")),
                        "reason": chords_pdf_error,
                    }
                )

    if document_verification_records or remove_stale_verification_paths:
        _save_document_verification_records(
            document_verification_records,
            remove_artifact_paths=remove_stale_verification_paths,
            updated_at=generated_at,
        )
    review_gate_decisions = compute_review_gate_decisions(document_verification_records)
    if review_gate_decisions or remove_stale_verification_paths:
        review_gate_state_path = Path(DOCUMENT_QUALITY_PATH).with_name(
            "review_gate_decisions.json"
        )
        refresh_review_gate_state(
            file_path=review_gate_state_path,
            review_gate_decisions=review_gate_decisions,
            remove_artifact_paths=remove_stale_verification_paths,
            updated_at=generated_at,
        )

    if content_score_records:
        score_state, score_errors = load_content_scores(
            CONTENT_SCORES_PATH,
            current_content_hashes=current_content_hashes,
        )
        if score_errors:
            logger.warning(
                "Content scores load reported %d recoverable issue(s).",
                len(score_errors),
            )
        existing_score_records = _flatten_content_score_records(score_state)
        overwrite_keys = {
            (record.get("song_key"), record.get("content_type"))
            for record in content_score_records
        }
        merged_score_records = [
            record
            for record in existing_score_records
            if (record.get("song_key"), record.get("content_type")) not in overwrite_keys
        ]
        merged_score_records.extend(content_score_records)
        save_content_scores(
            CONTENT_SCORES_PATH,
            merged_score_records,
            updated_at=generated_at,
        )

    return {
        "generated_at": generated_at,
        "report_type": "quality_run",
        "source": report_source or DEFAULT_REPORT_SOURCE,
        "entries": report_entries,
        "selection_issues": selection_issues,
        "pdf_outputs": pdf_outputs,
        "pdf_errors": pdf_errors,
        "document_verification": document_verification_records,
        "review_gate_decisions": review_gate_decisions,
        "content_scores": content_score_records,
    }
