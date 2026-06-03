import re

from app.content_models import build_quality_signal, validate_content_type


def _content_label(content_type):
    if content_type == "lyrics":
        return "Lyrics"
    return "Chords"


def _build_missing_signal(content_type):
    return build_quality_signal(
        "missing_{}".format(content_type),
        "error",
        "{} are missing or unusable.".format(_content_label(content_type)),
        content_type,
    )


def _build_unusable_signal(content_type):
    return build_quality_signal(
        "unusable_{}".format(content_type),
        "warning",
        "{} were not found.".format(_content_label(content_type)),
        content_type,
    )


def assess_missing_content(content_type, content):
    content_type_value = validate_content_type(content_type)
    sentinel_map = {
        "lyrics": "Lyrics not found.",
        "chords": "Chords not found.",
    }

    if not isinstance(content, str) or content.strip() == "":
        return {
            "quality": "missing",
            "signals": [_build_missing_signal(content_type_value)],
        }

    if content == sentinel_map[content_type_value]:
        return {
            "quality": "questionable",
            "signals": [_build_unusable_signal(content_type_value)],
        }

    return {
        "quality": "clean",
        "signals": [],
    }


HEADER_LINE_PATTERN = re.compile(
    r"^(Received|From|Message-Id|To|Date|Subject|X-.*|MIME-Version|Content-.*):",
    re.IGNORECASE,
)
HTML_RESIDUE_PATTERN = re.compile(r"<[^>]+>|&(?:#\d+|#x[0-9A-Fa-f]+|[A-Za-z]+);")
BRACKET_NOISE_PATTERN = re.compile(r"\[(?:/?[A-Za-z0-9_-]+)\]")
CHORD_BRACKET_PATTERN = re.compile(
    r"^\[(?:[A-G](?:#|b)?(?:maj|min|m|dim|aug|sus|add\d+)?(?:/[A-G](?:#|b)?)?|N.C.)\]$",
    re.IGNORECASE,
)


def _content_value(content):
    if isinstance(content, str):
        return content
    return ""


def _meaningful_lines(content_text):
    return [line.strip() for line in content_text.splitlines() if line.strip()]


def _all_lines(content_text):
    return content_text.splitlines()


def _has_duplicate_block(lines):
    line_count = len(lines)

    # Duplicate-block detection is intentionally bounded so already huge inputs
    # do not trigger a pathological search. Long content is handled by the
    # print-hostile checks instead.
    if line_count > 200:
        return False

    for block_length in range(1, (line_count // 2) + 1):
        seen = {}
        for start in range(0, line_count - block_length + 1):
            block = tuple(lines[start : start + block_length])
            previous_start = seen.get(block)
            if previous_start is not None and start - previous_start >= block_length:
                return True
            if previous_start is None:
                seen[block] = start

    return False


def _bracket_noise_counts(content_text):
    bracket_tags = BRACKET_NOISE_PATTERN.findall(content_text)
    bracket_chars = content_text.count("[") + content_text.count("]")
    bracket_noise_tags = [tag for tag in bracket_tags if not CHORD_BRACKET_PATTERN.match(tag)]
    return len(bracket_noise_tags), bracket_chars


def _build_signal(code, severity, message, content_type):
    return build_quality_signal(code, severity, message, content_type)


PRINT_HOSTILE_LINE_COUNT_LIMIT = 60
PRINT_HOSTILE_TOTAL_CHARACTER_LIMIT = 4000
PRINT_HOSTILE_LONGEST_LINE_LIMIT = 160


def _normalize_match_text(value):
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.split()).casefold()
    if normalized == "":
        return None
    return normalized


def _candidate_text(candidate, field_name, required=False):
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a dictionary; got {!r}".format(candidate))

    value = candidate.get(field_name)
    if value is None:
        if required:
            raise ValueError("{} must be a non-empty string; got {!r}".format(field_name, value))
        return None

    if not isinstance(value, str):
        if required:
            raise ValueError("{} must be a non-empty string; got {!r}".format(field_name, value))
        return None

    stripped = value.strip()
    if stripped == "":
        if required:
            raise ValueError("{} must be a non-empty string; got {!r}".format(field_name, value))
        return None
    return value


def _build_print_hostile_signal(content_type, reason):
    return _build_signal(
        "print_hostile_content",
        "warning",
        reason,
        content_type,
    )


def _build_low_confidence_signal(content_type, reason):
    return _build_signal(
        "low_confidence_match",
        "warning",
        reason,
        content_type,
    )


def assess_print_hostile_content(content_type, content):
    content_type_value = validate_content_type(content_type)
    content_text = _content_value(content)
    lines = _all_lines(content_text)
    total_characters = len(content_text)
    longest_line_length = max((len(line) for line in lines), default=0)
    signals = []

    if (
        len(lines) > PRINT_HOSTILE_LINE_COUNT_LIMIT
        or total_characters > PRINT_HOSTILE_TOTAL_CHARACTER_LIMIT
        or longest_line_length > PRINT_HOSTILE_LONGEST_LINE_LIMIT
    ):
        signals.append(
            _build_print_hostile_signal(
                content_type_value,
                "Content is likely too long for comfortable printing.",
            )
        )

    summary = {
        "line_count": len(lines),
        "total_characters": total_characters,
        "longest_line_length": longest_line_length,
        "has_print_hostile_content": bool(signals),
    }

    if signals:
        return {
            "quality": "questionable",
            "signals": signals,
            "summary": summary,
        }

    return {
        "quality": "clean",
        "signals": [],
        "summary": summary,
    }


def assess_low_confidence_candidate(candidate):
    content_type_value = validate_content_type(_candidate_text(candidate, "content_type", True))
    requested_artist = _candidate_text(candidate, "artist", True)
    requested_title = _candidate_text(candidate, "title", True)
    source_artist = _candidate_text(candidate, "source_artist")
    source_title = _candidate_text(candidate, "source_title")
    signals = []
    artist_mismatch = False
    title_mismatch = False

    normalized_requested_artist = _normalize_match_text(requested_artist)
    normalized_requested_title = _normalize_match_text(requested_title)
    normalized_source_artist = _normalize_match_text(source_artist)
    normalized_source_title = _normalize_match_text(source_title)

    if normalized_source_artist is not None and normalized_requested_artist is not None:
        artist_mismatch = normalized_source_artist != normalized_requested_artist

    if normalized_source_title is not None and normalized_requested_title is not None:
        title_mismatch = normalized_source_title != normalized_requested_title

    if artist_mismatch or title_mismatch:
        if artist_mismatch and title_mismatch:
            message = "Source artist and title do not match the requested song."
        elif artist_mismatch:
            message = "Source artist does not match the requested song."
        else:
            message = "Source title does not match the requested song."

        signals.append(_build_low_confidence_signal(content_type_value, message))

    summary = {
        "has_low_confidence_match": bool(signals),
        "source_artist_present": normalized_source_artist is not None,
        "source_title_present": normalized_source_title is not None,
        "artist_mismatch": artist_mismatch,
        "title_mismatch": title_mismatch,
    }

    if signals:
        return {
            "quality": "questionable",
            "signals": signals,
            "summary": summary,
        }

    return {
        "quality": "clean",
        "signals": [],
        "summary": summary,
    }


def assess_print_hostile_and_low_confidence(candidate):
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a dictionary; got {!r}".format(candidate))

    content_type_value = validate_content_type(_candidate_text(candidate, "content_type", True))
    content_result = assess_print_hostile_content(content_type_value, candidate.get("content"))
    confidence_result = assess_low_confidence_candidate(candidate)
    signals = content_result["signals"] + confidence_result["signals"]
    quality = "questionable" if signals else "clean"

    summary = dict(content_result["summary"])
    summary.update(confidence_result["summary"])

    return {
        "quality": quality,
        "signals": signals,
        "summary": summary,
    }


def assess_candidate_quality(candidate):
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a dictionary; got {!r}".format(candidate))

    content_type_value = validate_content_type(_candidate_text(candidate, "content_type", True))
    content_value = candidate.get("content")

    missing_result = assess_missing_content(content_type_value, content_value)
    junk_result = assess_junk_content(content_type_value, content_value)
    print_hostile_result = assess_print_hostile_content(content_type_value, content_value)
    low_confidence_result = assess_low_confidence_candidate(candidate)

    results = [
        missing_result,
        junk_result,
        print_hostile_result,
        low_confidence_result,
    ]
    signals = []
    summary = {}

    for result in results:
        signals.extend(result["signals"])
        summary.update(result.get("summary", {}))

    if any(result["quality"] == "missing" for result in results):
        quality = "missing"
    elif signals:
        quality = "questionable"
    else:
        quality = "clean"

    summary["has_quality_signals"] = bool(signals)
    summary["signal_count"] = len(signals)

    return {
        "quality": quality,
        "signals": signals,
        "summary": summary,
    }


def assess_junk_content(content_type, content):
    content_type_value = validate_content_type(content_type)
    content_text = _content_value(content)
    lines = _meaningful_lines(content_text)
    signals = []

    if HTML_RESIDUE_PATTERN.search(content_text):
        signals.append(
            _build_signal(
                "html_residue",
                "warning",
                "HTML residue was detected in the source text.",
                content_type_value,
            )
        )

    if any(HEADER_LINE_PATTERN.match(line) for line in lines):
        signals.append(
            _build_signal(
                "email_header_artifacts",
                "warning",
                "Email or header artifacts were detected in the source text.",
                content_type_value,
            )
        )

    if _has_duplicate_block(lines):
        signals.append(
            _build_signal(
                "duplicate_block",
                "warning",
                "Repeated blocks make the content difficult to trust.",
                content_type_value,
            )
        )

    bracket_tags, bracket_chars = _bracket_noise_counts(content_text)
    if bracket_tags >= 3 or bracket_chars >= 12:
        signals.append(
            _build_signal(
                "excessive_bracket_noise",
                "warning",
                "Bracket noise makes the content hard to read.",
                content_type_value,
            )
        )

    if signals:
        quality = "questionable"
        summary = {
            "line_count": len(lines),
            "bracket_tag_count": bracket_tags,
            "bracket_char_count": bracket_chars,
            "has_html_residue": any(signal["code"] == "html_residue" for signal in signals),
            "has_email_header_artifacts": any(
                signal["code"] == "email_header_artifacts" for signal in signals
            ),
            "has_duplicate_block": any(signal["code"] == "duplicate_block" for signal in signals),
            "has_excessive_bracket_noise": any(
                signal["code"] == "excessive_bracket_noise" for signal in signals
            ),
        }
        if any(signal["code"] == "duplicate_block" for signal in signals) and not summary[
            "has_html_residue"
        ]:
            summary["duplicate_block_count"] = 1
        return {
            "quality": quality,
            "signals": signals,
            "summary": summary,
        }

    return {
        "quality": "clean",
        "signals": [],
        "summary": {
            "line_count": len(lines),
            "bracket_tag_count": bracket_tags,
            "bracket_char_count": bracket_chars,
            "has_html_residue": False,
            "has_email_header_artifacts": False,
            "has_duplicate_block": False,
            "has_excessive_bracket_noise": False,
        },
    }
