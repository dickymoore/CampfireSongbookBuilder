import logging
import os
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION

from app.content_models import derive_song_key
from app.content_scoring import compose_content_score
from app.document_verification import (
    DEFAULT_DOCUMENT_QUALITY_PATH,
    evaluate_document_artifact,
    refresh_document_verification_state,
)
from app.document_formatting import (
    add_contents_page,
    add_bookmark,
    add_header_footer,
    build_song_bookmark_name,
    create_two_column_section,
    set_document_margins,
    set_document_mirrored_margins,
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
CHORDS_MONOSPACE_FONT = "Courier New"
CHORDS_BODY_FONT_SIZE = 10
CHORDS_MIN_BODY_FONT_SIZE = 8
CHORDS_COLUMN_COUNT = 2
CHORDS_COLUMN_GAP_INCHES = 0.3
PAGE_WIDTH_INCHES = 8.5
DEFAULT_MARGIN_INCHES = 0.5
CHORDS_MARGIN_INCHES = 0.4
DEFAULT_INSIDE_MARGIN_INCHES = 0.99
DEFAULT_OUTSIDE_MARGIN_INCHES = 0.1
CHORDS_INSIDE_MARGIN_INCHES = 0.89
CHORDS_OUTSIDE_MARGIN_INCHES = 0.1
MONOSPACE_CHAR_WIDTH_FACTOR = 0.55


def _has_missing_or_unusable_signal(generation_result):
    signal_codes = {
        signal.get("code")
        for signal in generation_result.get("signals", [])
        if isinstance(signal, dict)
    }
    return bool(
        {
            "missing_lyrics",
            "unusable_lyrics",
            "missing_chords",
            "unusable_chords",
        }
        & signal_codes
    )


def _xml_safe_text(value):
    if not isinstance(value, str):
        return value
    return "".join(
        ch
        for ch in value
        if ch in ("\n", "\r", "\t") or ord(ch) >= 32
    )


def _max_safe_chords_line_length(font_size=None):
    effective_font_size = font_size or CHORDS_BODY_FONT_SIZE
    usable_width = PAGE_WIDTH_INCHES - (
        CHORDS_INSIDE_MARGIN_INCHES + CHORDS_OUTSIDE_MARGIN_INCHES
    )
    total_gap = CHORDS_COLUMN_GAP_INCHES * (CHORDS_COLUMN_COUNT - 1)
    column_width_points = ((usable_width - total_gap) / CHORDS_COLUMN_COUNT) * 72
    monospace_char_width_points = effective_font_size * MONOSPACE_CHAR_WIDTH_FACTOR
    return max(1, int(column_width_points // monospace_char_width_points))


def _audit_chords_wrapping(artist, title, content):
    safe_content = _xml_safe_text(content) or ""
    lines = safe_content.split("\n")

    chosen_font_size = CHORDS_BODY_FONT_SIZE
    overlong_lines = []
    max_chars = _max_safe_chords_line_length(chosen_font_size)

    for font_size in range(CHORDS_BODY_FONT_SIZE, CHORDS_MIN_BODY_FONT_SIZE - 1, -1):
        max_chars = _max_safe_chords_line_length(font_size)
        candidate_overlong_lines = []
        for line_number, line in enumerate(lines, start=1):
            line_length = len(line)
            if line_length > max_chars:
                candidate_overlong_lines.append(
                    {
                        "line_number": line_number,
                        "line_length": line_length,
                        "max_safe_length": max_chars,
                        "preview": line[:120],
                    }
                )
        chosen_font_size = font_size
        overlong_lines = candidate_overlong_lines
        if not overlong_lines:
            break

    return {
        "artist": artist,
        "title": title,
        "song_key": derive_song_key(artist, title),
        "font_name": CHORDS_MONOSPACE_FONT,
        "font_size": chosen_font_size,
        "max_safe_length": max_chars,
        "has_overlong_lines": bool(overlong_lines),
        "overlong_line_count": len(overlong_lines),
        "overlong_lines": overlong_lines,
    }


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
    safe_content = _xml_safe_text(content)
    return [
        "# {} by {}".format(title, artist),
        "",
        "```text",
        safe_content,
        "```",
        "",
    ]


def _document_title(song_items):
    return "{} Campfire Songs".format(len(song_items or []))


def _render_song_item(
    document,
    song_item,
    heading_font_size,
    body_font_size,
    bookmark_id,
    body_font_name=None,
):
    artist = song_item["artist"]
    title = song_item["title"]
    content = _xml_safe_text(song_item["content"])
    bookmark_name = song_item["bookmark_name"]

    heading = document.add_heading("{} by {}".format(title, artist), level=1)
    set_paragraph_font(heading, heading_font_size)
    add_bookmark(heading, bookmark_name, bookmark_id)

    paragraph = document.add_paragraph()
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if i > 0:
            paragraph.add_run().add_break()
        paragraph.add_run(line)
    set_paragraph_font(paragraph, body_font_size, font_name=body_font_name)


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
    report_all_content=False,
    include_questionable=False,
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

    songs_to_process = selection_records if selection_records is not None else sort_songs(song_list)

    if lyrics_output:
        logger.debug("Initializing lyrics document")
        lyrics_document = Document()
        set_document_margins(lyrics_document, DEFAULT_MARGIN_INCHES)
        set_document_mirrored_margins(
            lyrics_document,
            DEFAULT_INSIDE_MARGIN_INCHES,
            DEFAULT_OUTSIDE_MARGIN_INCHES,
        )
        lyrics_markdown_lines = []
        lyrics_render_items = []

    if chords_output:
        logger.debug("Initializing chords document")
        chords_document = Document()
        set_document_margins(chords_document, CHORDS_MARGIN_INCHES)
        set_document_mirrored_margins(
            chords_document,
            CHORDS_INSIDE_MARGIN_INCHES,
            CHORDS_OUTSIDE_MARGIN_INCHES,
        )
        chords_markdown_lines = []
        chords_render_items = []
    report_entries = []
    selection_issues = []
    pdf_outputs = []
    pdf_errors = []
    document_verification_records = []
    remove_stale_verification_paths = []
    content_score_records = []
    chords_layout_audit = []

    for song in songs_to_process:
        artist = _song_artist(song)
        title = _song_title(song)
        cache_key = _song_key(song) or derive_song_key(artist, title)
        pending_lyrics_render_item = None
        pending_lyrics_markdown_lines = None
        pending_chords_render_item = None
        pending_chords_markdown_lines = None
        lyrics_quality_status = quality_status_state.get("entries", {}).get(cache_key, {}).get("lyrics")
        lyrics_review_decision = review_decision_state.get("entries", {}).get(cache_key, {}).get("lyrics")
        chords_quality_status = quality_status_state.get("entries", {}).get(cache_key, {}).get("chords")
        chords_review_decision = review_decision_state.get("entries", {}).get(cache_key, {}).get("chords")

        lyrics = lyrics_cache.get(cache_key) if isinstance(lyrics_cache, dict) else None
        lyrics_generation_result = evaluate_cached_content(
            artist,
            title,
            "lyrics",
            lyrics,
            quality_status_record=lyrics_quality_status,
            review_decision_record=lyrics_review_decision,
        )
        if lyrics_generation_result.get("content_hash") is not None:
            try:
                content_score_records.append(
                    compose_content_score(
                        lyrics_generation_result.get("quality_status") or {},
                        scored_at=generated_at,
                    )
                )
            except ValueError as exc:
                logger.warning("Failed to compute lyrics content score for %s: %s", cache_key, exc)

        if (
            include_questionable
            and lyrics_generation_result["quality"] == "questionable"
            and not _has_missing_or_unusable_signal(lyrics_generation_result)
        ):
            lyrics_generation_result = dict(lyrics_generation_result)
            lyrics_generation_result["included"] = True
            lyrics_generation_result["decision_source"] = "include_questionable_mode"
            lyrics_generation_result["reason"] = (
                "Questionable content included by generation mode."
            )

        report_included = lyrics_generation_result["included"]
        report_reason = lyrics_generation_result["reason"]
        if lyrics_output and lyrics_generation_result["included"] and isinstance(lyrics, str) and lyrics != "":
            lyrics = clean_lyrics(lyrics)
            num_characters = len(lyrics)
            logger.debug("Adding lyrics for %s by %s", title, artist)

            if num_characters <= 5000:
                pending_lyrics_render_item = {
                    "artist": artist,
                    "title": title,
                    "content": lyrics,
                }
                pending_lyrics_markdown_lines = _markdown_song_block(artist, title, lyrics)
            else:
                report_included = False
                report_reason = "Lyrics are too long and were excluded from the document."
                logger.debug("Lyrics for %s are too long and have been excluded.", title)
        elif lyrics_output:
            logger.debug(
                "Skipping lyrics for %s by %s: %s",
                title,
                artist,
                report_reason,
            )
        else:
            pending_lyrics_render_item = None
            pending_lyrics_markdown_lines = None

        if (
            selection_records is not None
            and lyrics_generation_result["quality"] == "missing"
            and (report_all_content or lyrics_output)
        ):
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

        chords = chords_cache.get(cache_key) if isinstance(chords_cache, dict) else None
        chords_generation_result = evaluate_cached_content(
            artist,
            title,
            "chords",
            chords,
            quality_status_record=chords_quality_status,
            review_decision_record=chords_review_decision,
        )
        if chords_generation_result.get("content_hash") is not None:
            try:
                content_score_records.append(
                    compose_content_score(
                        chords_generation_result.get("quality_status") or {},
                        scored_at=generated_at,
                    )
                )
            except ValueError as exc:
                logger.warning("Failed to compute chords content score for %s: %s", cache_key, exc)

        if (
            include_questionable
            and chords_generation_result["quality"] == "questionable"
            and not _has_missing_or_unusable_signal(chords_generation_result)
        ):
            chords_generation_result = dict(chords_generation_result)
            chords_generation_result["included"] = True
            chords_generation_result["decision_source"] = "include_questionable_mode"
            chords_generation_result["reason"] = (
                "Questionable content included by generation mode."
            )

        # Exclude songs missing either side from both books so the generated sets
        # stay aligned.
        lyrics_signal_codes = {
            signal.get("code")
            for signal in lyrics_generation_result.get("signals", [])
            if isinstance(signal, dict)
        }
        chords_signal_codes = {
            signal.get("code")
            for signal in chords_generation_result.get("signals", [])
            if isinstance(signal, dict)
        }
        song_has_missing_side = (
            lyrics_output
            and chords_output
            and (
                lyrics_generation_result["quality"] == "missing"
                or chords_generation_result["quality"] == "missing"
                or "missing_lyrics" in lyrics_signal_codes
                or "unusable_lyrics" in lyrics_signal_codes
                or "missing_chords" in chords_signal_codes
                or "unusable_chords" in chords_signal_codes
            )
        )
        if song_has_missing_side:
            missing_reason = "Song is missing lyrics or chords and is excluded from both documents."
            report_included = False
            report_reason = missing_reason
            lyrics_generation_result = dict(lyrics_generation_result)
            lyrics_generation_result["included"] = False
            lyrics_generation_result["reason"] = missing_reason
            chords_generation_result = dict(chords_generation_result)
            chords_generation_result["included"] = False
            chords_generation_result["reason"] = missing_reason

        if report_all_content or lyrics_output:
            report_entries.append(
                _build_report_entry(
                    song,
                    "lyrics",
                    lyrics_generation_result,
                    included=report_included,
                    reason=report_reason,
                )
            )
        if report_all_content or chords_output:
            report_entries.append(_build_report_entry(song, "chords", chords_generation_result))
        if (
            selection_records is not None
            and chords_generation_result["quality"] == "missing"
            and (report_all_content or chords_output)
        ):
            selection_issues.append(
                {
                    "selection_name": None,
                    "issue_type": "missing_content",
                    "artist": artist,
                    "title": title,
                    "song_key": cache_key,
                    "content_type": "chords",
                    "reason": chords_generation_result["reason"],
                }
            )

        if chords_output and chords_generation_result["included"] and isinstance(chords, str) and chords != "":
            logger.debug("Adding chords for %s by %s", title, artist)
            chords_audit = _audit_chords_wrapping(artist, title, chords)
            chords_layout_audit.append(chords_audit)
            pending_chords_render_item = {
                "artist": artist,
                "title": title,
                "content": chords,
                "body_font_size": chords_audit["font_size"],
            }
            pending_chords_markdown_lines = _markdown_song_block(artist, title, chords)
        elif chords_output:
            logger.debug(
                "Skipping chords for %s by %s: %s",
                title,
                artist,
                chords_generation_result["reason"],
            )
        else:
            pending_chords_render_item = None
            pending_chords_markdown_lines = None

        if (
            lyrics_output
            and report_included
            and pending_lyrics_render_item is not None
        ):
            pending_lyrics_render_item["bookmark_name"] = build_song_bookmark_name(
                song,
                len(lyrics_render_items) + 1,
            )
            lyrics_render_items.append(pending_lyrics_render_item)
            lyrics_markdown_lines.extend(pending_lyrics_markdown_lines)

        if (
            chords_output
            and chords_generation_result["included"]
            and pending_chords_render_item is not None
        ):
            pending_chords_render_item["bookmark_name"] = build_song_bookmark_name(
                song,
                len(chords_render_items) + 1,
            )
            chords_render_items.append(pending_chords_render_item)
            chords_markdown_lines.extend(pending_chords_markdown_lines)

    if lyrics_output:
        add_header_footer(lyrics_document, _document_title(lyrics_render_items))
        add_contents_page(lyrics_document, lyrics_render_items, generated_at=generated_at)
        create_two_column_section(
            lyrics_document.add_section(WD_SECTION.NEW_PAGE),
            column_gap_inches=0.5,
        )
        for index, song_item in enumerate(lyrics_render_items, start=1):
            _render_song_item(lyrics_document, song_item, 13, 11, index)
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
        add_header_footer(chords_document, _document_title(chords_render_items))
        add_contents_page(chords_document, chords_render_items, generated_at=generated_at)
        create_two_column_section(
            chords_document.add_section(WD_SECTION.NEW_PAGE),
            column_gap_inches=CHORDS_COLUMN_GAP_INCHES,
        )
        for index, song_item in enumerate(chords_render_items, start=1):
            _render_song_item(
                chords_document,
                song_item,
                13,
                song_item.get("body_font_size", CHORDS_BODY_FONT_SIZE),
                index,
                body_font_name=CHORDS_MONOSPACE_FONT,
            )
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
        "chords_layout_audit": chords_layout_audit,
    }
