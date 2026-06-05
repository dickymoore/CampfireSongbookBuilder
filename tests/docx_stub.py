"""Minimal docx test double used when python-docx is unavailable.

The stub is intentionally small but functional enough for document creation
tests that save and reload generated content through the same interface.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path


class _FakeFont:
    def __init__(self):
        self.size = None
        self.name = None


class _FakeStyle:
    def __init__(self):
        self.font = _FakeFont()
        self.name = "Normal"


class _FakeRun:
    def __init__(self, paragraph):
        self.font = _FakeFont()
        self._paragraph = paragraph
        self._r = []

    def add_break(self):
        self._paragraph._parts.append("\n")


class _FakeParagraph:
    def __init__(self, text=""):
        self._parts = []
        self.runs = []
        self.style = _FakeStyle()
        if text:
            self.text = text

    @property
    def text(self):
        return "".join(self._parts)

    @text.setter
    def text(self, value):
        self._parts = [value]

    def add_run(self, text=""):
        run = _FakeRun(self)
        self.runs.append(run)
        if text:
            self._parts.append(text)
        return run


class _FakeHeaderFooter:
    def __init__(self):
        self.paragraphs = [_FakeParagraph()]


class _FakeSectPr:
    def __init__(self):
        self._cols = [_FakeXmlElement()]

    def xpath(self, _query):
        if _query == './w:cols':
            return self._cols
        return []

    def append(self, element):
        self._cols.append(element)


class _FakeXmlElement:
    def __init__(self):
        self.attrs = {}
        self.children = []

    def set(self, _name, _value):
        self.attrs[_name] = _value
        return None

    def find(self, _name):
        return None

    def append(self, element):
        self.children.append(element)


class _FakeTc:
    def __init__(self):
        self._tc_pr = _FakeXmlElement()

    def get_or_add_tcPr(self):
        return self._tc_pr


class _FakeSection:
    def __init__(self):
        self.header = _FakeHeaderFooter()
        self.footer = _FakeHeaderFooter()
        self._sectPr = _FakeSectPr()
        self.top_margin = None
        self.bottom_margin = None
        self.left_margin = None
        self.right_margin = None


class _FakeCell:
    def __init__(self, text=""):
        self.paragraphs = [_FakeParagraph(text)]
        self.width = None
        self._tc = _FakeTc()

    @property
    def text(self):
        return "\n".join(paragraph.text for paragraph in self.paragraphs)

    @text.setter
    def text(self, value):
        self.paragraphs = [_FakeParagraph(value)]


class _FakeRow:
    def __init__(self, cell_count):
        self.cells = [_FakeCell() for _ in range(cell_count)]


class _FakeTable:
    def __init__(self, rows, cols):
        self.autofit = True
        self.rows = [_FakeRow(cols) for _ in range(rows)]
        self.style = None
        self.columns = [_FakeColumn() for _ in range(cols)]

    def add_row(self):
        row = _FakeRow(len(self.rows[0].cells) if self.rows else len(self.columns))
        self.rows.append(row)
        return row

    def cell(self, row_index, col_index):
        return self.rows[row_index].cells[col_index]


class _FakeColumn:
    def __init__(self):
        self.width = None


class FakeDocument:
    def __init__(self, path=None):
        self.sections = [_FakeSection()]
        self.paragraphs = []
        self.tables = []
        if path is not None:
            self._load(path)

    def _load(self, path):
        target_path = Path(path)
        if not target_path.exists():
            return

        try:
            payload = json.loads(target_path.read_text(encoding="utf-8"))
        except Exception:
            return

        loaded_paragraphs = []
        for item in payload.get("paragraphs", []):
            if isinstance(item, str):
                paragraph = _FakeParagraph(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                paragraph = _FakeParagraph(item["text"])
                style_name = item.get("style_name")
                if isinstance(style_name, str) and style_name:
                    paragraph.style.name = style_name
            else:
                continue
            loaded_paragraphs.append(paragraph)

        self.paragraphs = loaded_paragraphs
        self.tables = []
        for table_payload in payload.get("tables", []):
            table = _FakeTable(0, 0)
            table.autofit = table_payload.get("autofit", True)
            table.style = table_payload.get("style")
            table.rows = []
            for row_payload in table_payload.get("rows", []):
                cells = []
                for cell_payload in row_payload:
                    cell = _FakeCell()
                    cell.paragraphs = [_FakeParagraph(text) for text in cell_payload]
                    if not cell.paragraphs:
                        cell.paragraphs = [_FakeParagraph()]
                    cells.append(cell)
                row = _FakeRow(0)
                row.cells = cells
                table.rows.append(row)
            if table.rows:
                table.columns = [_FakeColumn() for _ in range(len(table.rows[0].cells))]
            self.tables.append(table)

    def add_section(self, *args, **kwargs):  # noqa: ARG002
        section = _FakeSection()
        self.sections.append(section)
        return section

    def add_heading(self, text, level=1):  # noqa: ARG002
        paragraph = _FakeParagraph(text)
        paragraph.style.name = "Heading 1"
        self.paragraphs.append(paragraph)
        return paragraph

    def add_paragraph(self, text=""):
        paragraph = _FakeParagraph(text)
        self.paragraphs.append(paragraph)
        return paragraph

    def add_table(self, rows, cols):
        table = _FakeTable(rows, cols)
        self.tables.append(table)
        return table

    def add_page_break(self):
        paragraph = _FakeParagraph()
        paragraph.style.name = "Page Break"
        self.paragraphs.append(paragraph)
        return paragraph

    def save(self, path):
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "paragraphs": [
                {
                    "text": paragraph.text,
                    "style_name": getattr(paragraph.style, "name", "Normal"),
                }
                for paragraph in self.paragraphs
            ],
            "tables": [
                {
                    "autofit": table.autofit,
                    "style": table.style,
                    "rows": [
                        [cell.text.split("\n") for cell in row.cells]
                        for row in table.rows
                    ],
                }
                for table in self.tables
            ],
        }
        target_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def install_docx_stub():
    if "docx" in sys.modules:
        return

    docx_stub = types.ModuleType("docx")
    docx_stub.Document = FakeDocument

    shared_stub = types.ModuleType("docx.shared")
    shared_stub.Pt = lambda value: value
    shared_stub.Inches = lambda value: value

    enum_stub = types.ModuleType("docx.enum")
    section_stub = types.ModuleType("docx.enum.section")
    section_stub.WD_SECTION = types.SimpleNamespace(NEW_PAGE=1)

    oxml_stub = types.ModuleType("docx.oxml")
    oxml_stub.OxmlElement = lambda *args, **kwargs: _FakeXmlElement()

    ns_stub = types.ModuleType("docx.oxml.ns")
    ns_stub.qn = lambda value: value

    sys.modules["docx"] = docx_stub
    sys.modules["docx.shared"] = shared_stub
    sys.modules["docx.enum"] = enum_stub
    sys.modules["docx.enum.section"] = section_stub
    sys.modules["docx.oxml"] = oxml_stub
    sys.modules["docx.oxml.ns"] = ns_stub
