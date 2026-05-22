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
    def xpath(self, _query):
        return [_FakeXmlElement()]


class _FakeXmlElement:
    def set(self, _name, _value):
        return None


class _FakeSection:
    def __init__(self):
        self.header = _FakeHeaderFooter()
        self.footer = _FakeHeaderFooter()
        self._sectPr = _FakeSectPr()
        self.top_margin = None
        self.bottom_margin = None
        self.left_margin = None
        self.right_margin = None


class FakeDocument:
    def __init__(self, path=None):
        self.sections = [_FakeSection()]
        self.paragraphs = []
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

    def add_section(self):
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
            ]
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

    oxml_stub = types.ModuleType("docx.oxml")
    oxml_stub.OxmlElement = lambda *args, **kwargs: _FakeXmlElement()

    ns_stub = types.ModuleType("docx.oxml.ns")
    ns_stub.qn = lambda value: value

    sys.modules["docx"] = docx_stub
    sys.modules["docx.shared"] = shared_stub
    sys.modules["docx.oxml"] = oxml_stub
    sys.modules["docx.oxml.ns"] = ns_stub
