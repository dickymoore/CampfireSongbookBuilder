import re
from datetime import datetime

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HEADER_COLOR = RGBColor(0xD9, 0x77, 0x06)
PAGE_NUMBER_COLOR = RGBColor(0x9E, 0x2A, 0x2B)

def set_document_margins(document, margin_in_inches):
    """Set the margins of the document."""
    sections = document.sections
    for section in sections:
        section.top_margin = Inches(margin_in_inches)
        section.bottom_margin = Inches(margin_in_inches)
        section.left_margin = Inches(margin_in_inches)
        section.right_margin = Inches(margin_in_inches)


def set_document_mirrored_margins(document, inside_margin_in_inches, outside_margin_in_inches):
    """Set mirrored margins so odd/even pages swap the binding edge automatically."""
    settings = getattr(document, "settings", None)
    settings_element = getattr(settings, "_element", None)
    if settings_element is not None:
        mirror = settings_element.find(qn("w:mirrorMargins"))
        if mirror is None:
            mirror = OxmlElement("w:mirrorMargins")
            settings_element.append(mirror)

    gutter_inches = max(0, inside_margin_in_inches - outside_margin_in_inches)
    for section in document.sections:
        section.left_margin = Inches(outside_margin_in_inches)
        section.right_margin = Inches(outside_margin_in_inches)
        if hasattr(section, "gutter"):
            section.gutter = Inches(gutter_inches)

def set_paragraph_font(paragraph, font_size, font_name=None):
    """Set the font size of a paragraph."""
    for run in paragraph.runs:
        run.font.size = Pt(font_size)
        if font_name:
            run.font.name = font_name


def _set_cell_text(cell, text, font_size, bold=False):
    paragraph = cell.paragraphs[0]
    paragraph.text = ""
    run = paragraph.add_run(text)
    run.font.size = Pt(font_size)
    run.bold = bold
    return paragraph


def _set_cell_no_wrap(cell):
    tc_pr = cell._tc.get_or_add_tcPr()
    no_wrap = tc_pr.find(qn("w:noWrap"))
    if no_wrap is None:
        no_wrap = OxmlElement("w:noWrap")
        tc_pr.append(no_wrap)


def _set_table_fixed_layout(table):
    tbl = getattr(table, "_tbl", None)
    tbl_pr = getattr(tbl, "tblPr", None)
    if tbl_pr is None:
        return
    tbl_layout = tbl_pr.find(qn("w:tblLayout"))
    if tbl_layout is None:
        tbl_layout = OxmlElement("w:tblLayout")
        tbl_pr.append(tbl_layout)
    tbl_layout.set(qn("w:type"), "fixed")


def _set_table_borders(table):
    tbl = getattr(table, "_tbl", None)
    tbl_pr = getattr(tbl, "tblPr", None)
    if tbl_pr is None:
        return
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)

    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = borders.find(qn("w:{}".format(edge)))
        if element is None:
            element = OxmlElement("w:{}".format(edge))
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "8")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "000000")


def _sanitize_bookmark_name(value):
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value or "").strip("_")
    if not slug:
        slug = "song"
    if slug[0].isdigit():
        slug = "song_" + slug
    return slug[:40]


def build_song_bookmark_name(song, index):
    title = song.get("Title") if isinstance(song, dict) else None
    artist = song.get("Artist") if isinstance(song, dict) else None
    return _sanitize_bookmark_name(
        "song_{}_{}_{}".format(index, artist or "unknown", title or "untitled")
    )


def add_bookmark(paragraph, bookmark_name, bookmark_id):
    paragraph_element = getattr(paragraph, "_p", None)
    if paragraph_element is None:
        return

    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(bookmark_id))
    start.set(qn("w:name"), bookmark_name)
    paragraph_element.insert(0, start)

    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(bookmark_id))
    paragraph_element.append(end)


def add_page_ref_field(paragraph, bookmark_name):
    run = paragraph.add_run()
    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "begin")
    run._r.append(fld_char)

    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGEREF {} \\h".format(bookmark_name)
    run._r.append(instr_text)

    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char)


def _append_field_run_properties(run, font_size=None, bold=False, color_rgb=None):
    if font_size is not None:
        run.font.size = Pt(font_size)
    run.font.bold = bool(bold)
    if color_rgb is not None:
        run.font.color.rgb = color_rgb

    r_pr = OxmlElement("w:rPr")
    if bold:
        r_pr.append(OxmlElement("w:b"))
    if font_size is not None:
        size = OxmlElement("w:sz")
        size.set(qn("w:val"), str(int(font_size * 2)))
        r_pr.append(size)
    if color_rgb is not None:
        color = OxmlElement("w:color")
        if isinstance(color_rgb, tuple):
            hex_value = "".join("{:02X}".format(component) for component in color_rgb)
        else:
            hex_value = str(color_rgb)
        color.set(qn("w:val"), hex_value)
        r_pr.append(color)
    run._r.insert(0, r_pr)


def add_page_number_field(paragraph, font_size=12, color_rgb=None, bold=False):
    begin_run = paragraph.add_run()
    _append_field_run_properties(begin_run, font_size=font_size, color_rgb=color_rgb, bold=bold)
    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "begin")
    begin_run._r.append(fld_char)

    instr_run = paragraph.add_run()
    _append_field_run_properties(instr_run, font_size=font_size, color_rgb=color_rgb, bold=bold)
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"
    instr_run._r.append(instr_text)

    separate_run = paragraph.add_run()
    _append_field_run_properties(separate_run, font_size=font_size, color_rgb=color_rgb, bold=bold)
    separate_char = OxmlElement("w:fldChar")
    separate_char.set(qn("w:fldCharType"), "separate")
    separate_run._r.append(separate_char)

    result_run = paragraph.add_run("1")
    _append_field_run_properties(result_run, font_size=font_size, color_rgb=color_rgb, bold=bold)

    end_run = paragraph.add_run()
    _append_field_run_properties(end_run, font_size=font_size, color_rgb=color_rgb, bold=bold)
    end_char = OxmlElement("w:fldChar")
    end_char.set(qn("w:fldCharType"), "end")
    end_run._r.append(end_char)


def _get_or_add_cols(sect_pr):
    cols = sect_pr.xpath('./w:cols')
    if cols:
        return cols[0]
    cols = OxmlElement('w:cols')
    sect_pr.append(cols)
    return cols


def create_two_column_section(target, column_gap_inches=0.5):
    """Configure a document or section to use two columns."""
    sections = getattr(target, "sections", None)
    if sections is not None:
        for section in sections:
            create_two_column_section(section, column_gap_inches=column_gap_inches)
        return

    sectPr = target._sectPr
    cols = _get_or_add_cols(sectPr)
    cols.set(qn('w:num'), '2')
    cols.set(qn('w:space'), str(int(column_gap_inches * 1440)))


def add_contents_page(document, songs, generated_at=None):
    """Add a deterministic title and contents table before the song content."""
    song_count = len(songs or [])
    title_text = "{} Campfire Songs".format(song_count)
    if generated_at:
        try:
            generated_date = datetime.fromisoformat(generated_at).strftime("%Y-%m-%d")
        except ValueError:
            generated_date = str(generated_at)[:10]
        title_text = "{} | {}".format(title_text, generated_date)

    title = document.add_paragraph(title_text)
    set_paragraph_font(title, 14)

    table = document.add_table(rows=1, cols=2)
    table.autofit = False
    table.style = "Table Grid"
    _set_table_fixed_layout(table)
    _set_table_borders(table)
    table.columns[0].width = Inches(6.2)
    table.columns[1].width = Inches(0.8)
    header_song = _set_cell_text(table.rows[0].cells[0], "Song", 9, bold=True)
    header_page = _set_cell_text(table.rows[0].cells[1], "Page", 9, bold=True)
    set_paragraph_font(header_song, 9)
    set_paragraph_font(header_page, 9)
    table.rows[0].cells[0].width = Inches(6.2)
    table.rows[0].cells[1].width = Inches(0.8)
    _set_cell_no_wrap(table.rows[0].cells[0])
    _set_cell_no_wrap(table.rows[0].cells[1])

    for song in songs:
        title = None
        artist = None
        bookmark_name = None
        if isinstance(song, dict):
            title = song.get("Title") or song.get("title")
            artist = song.get("Artist") or song.get("artist")
            bookmark_name = song.get("bookmark_name")
        if not title or not artist or not bookmark_name:
            continue

        row = table.add_row().cells
        row[0].width = Inches(6.2)
        row[1].width = Inches(0.8)
        _set_cell_no_wrap(row[0])
        _set_cell_no_wrap(row[1])
        song_paragraph = _set_cell_text(row[0], "{} - {}".format(title, artist), 9)
        page_paragraph = row[1].paragraphs[0]
        page_paragraph.text = ""
        add_page_ref_field(page_paragraph, bookmark_name)
        set_paragraph_font(song_paragraph, 8)
        set_paragraph_font(page_paragraph, 8)


def add_header_footer(document, header_text="Campfire Songs"):
    """Add a header and footer with page numbers to the document."""
    document.sections[0].different_first_page_header_footer = True

    # Add header
    header = document.sections[0].header
    paragraph = header.paragraphs[0]
    paragraph.text = ""
    run = paragraph.add_run(header_text)
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.color.rgb = HEADER_COLOR

    first_page_header = document.sections[0].first_page_header
    if first_page_header.paragraphs:
        first_page_header.paragraphs[0].text = ""

    # Add footer with page numbers
    footer = document.sections[0].footer
    paragraph = footer.paragraphs[0]
    paragraph.text = ""
    label_run = paragraph.add_run("Page ")
    label_run.font.size = Pt(12)
    label_run.font.bold = True
    label_run.font.color.rgb = PAGE_NUMBER_COLOR
    add_page_number_field(paragraph, font_size=12, color_rgb=PAGE_NUMBER_COLOR, bold=True)

def sort_songs(song_list):
    """Sort songs case-insensitively and ignoring special characters."""
    return sorted(song_list, key=lambda x: re.sub(r'[^a-zA-Z0-9]', '', x['Title']).lower())
