from docx.shared import Pt, Inches
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re

def set_document_margins(document, margin_in_inches):
    """Set the margins of the document."""
    sections = document.sections
    for section in sections:
        section.top_margin = Inches(margin_in_inches)
        section.bottom_margin = Inches(margin_in_inches)
        section.left_margin = Inches(margin_in_inches)
        section.right_margin = Inches(margin_in_inches)

def set_paragraph_font(paragraph, font_size):
    """Set the font size of a paragraph."""
    for run in paragraph.runs:
        run.font.size = Pt(font_size)

def create_two_column_section(document):
    """Create a new section with two columns."""
    section = document.add_section()
    sectPr = section._sectPr
    cols = sectPr.xpath('./w:cols')[0]
    cols.set(qn('w:num'), '2')

def add_header_footer(document):
    """Add a header and footer with page numbers to the document."""
    # Add header
    header = document.sections[0].header
    paragraph = header.paragraphs[0]
    paragraph.text = "Campfire Songs"
    paragraph.style.font.size = Pt(14)

    # Add footer with page numbers
    footer = document.sections[0].footer
    paragraph = footer.paragraphs[0]
    paragraph.text = "Page "
    paragraph.style.font.size = Pt(12)
    
    # Add the page number field to the footer
    run = paragraph.add_run()
    fldChar = OxmlElement('w:fldChar')
    fldChar.set(qn('w:fldCharType'), 'begin')
    run._r.append(fldChar)
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'PAGE'
    run._r.append(instrText)
    fldChar = OxmlElement('w:fldChar')
    fldChar.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar)

def sort_songs(song_list):
    """Sort songs case-insensitively and ignoring special characters."""
    return sorted(song_list, key=lambda x: re.sub(r'[^a-zA-Z0-9]', '', x['Title']).lower())
