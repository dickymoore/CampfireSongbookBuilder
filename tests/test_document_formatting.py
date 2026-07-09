import unittest

from docx.oxml.ns import qn

from tests.docx_stub import install_docx_stub

install_docx_stub()

from docx import Document  # noqa: E402

from app.document_formatting import add_contents_page, create_two_column_section  # noqa: E402


class TestDocumentFormatting(unittest.TestCase):
    def test_create_two_column_section_reuses_existing_section(self):
        document = Document()

        self.assertEqual(len(document.sections), 1)

        create_two_column_section(document)

        self.assertEqual(len(document.sections), 1)
        cols = document.sections[0]._sectPr.xpath('./w:cols')[0]
        attrs = getattr(cols, 'attrs', None)
        if attrs is not None:
            self.assertEqual(attrs.get('w:num'), '2')
            self.assertEqual(attrs.get('w:space'), '720')
        else:
            self.assertEqual(cols.get(qn('w:num')), '2')
            self.assertEqual(cols.get(qn('w:space')), '720')

    def test_add_contents_page_builds_a_table_with_page_references(self):
        document = Document()

        add_contents_page(
            document,
            [
                {
                    "Artist": "The Campfire Trio",
                    "Title": "River Song",
                    "bookmark_name": "song_1_the_campfire_trio_river_song",
                },
                {
                    "Artist": "The Campfire Trio",
                    "Title": "Trail Song",
                    "bookmark_name": "song_2_the_campfire_trio_trail_song",
                },
            ],
            generated_at="2026-07-09T17:50:45+01:00",
        )

        self.assertEqual(document.paragraphs[0].text, "2 Campfire Songs | 2026-07-09")
        self.assertEqual(len(document.tables), 1)
        table = document.tables[0]
        self.assertEqual(table.cell(0, 0).text, "Song")
        self.assertEqual(table.cell(0, 1).text, "Page")
        self.assertEqual(table.cell(1, 0).text, "River Song - The Campfire Trio")
        self.assertEqual(table.cell(2, 0).text, "Trail Song - The Campfire Trio")
        self.assertIn("PAGEREF song_1_the_campfire_trio_river_song", table.cell(1, 1).paragraphs[0]._p.xml)
        self.assertIn("PAGEREF song_2_the_campfire_trio_trail_song", table.cell(2, 1).paragraphs[0]._p.xml)
        self.assertIn("tblBorders", table._tbl.xml)
        self.assertIn("tblLayout", table._tbl.xml)
        self.assertIn("noWrap", table.cell(0, 0)._tc.xml)
