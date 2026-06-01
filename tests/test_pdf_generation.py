import tempfile
import unittest
from pathlib import Path

from app.pdf_generation import convert_document_to_pdf


class TestPdfGeneration(unittest.TestCase):
    def test_pandoc_falls_back_to_tectonic_when_default_pdf_engine_missing(self):
        calls = []

        def fake_which(name):
            if name == "pandoc":
                return "/usr/local/bin/pandoc"
            if name == "tectonic":
                return "/usr/local/bin/tectonic"
            return None

        def fake_runner(cmd, check, capture_output, text):
            calls.append(cmd)
            # First call is pandoc docx->pdf which we simulate as failing.
            if cmd[:2] == ["pandoc", str(docx_path)] and cmd[-2] == "-o":
                raise RuntimeError("pdflatex not found")
            # Second call is pandoc -s docx -> tex.
            if cmd[:2] == ["pandoc", "-s"] and cmd[-2] == "-o":
                Path(cmd[-1]).write_text("\\\\documentclass{article}\\\\begin{document}x\\\\end{document}\\n")
                return
            # Third call is tectonic tex -> pdf.
            if cmd[0] == "tectonic":
                outdir = Path(cmd[cmd.index("--outdir") + 1])
                pdf = outdir / Path(cmd[1]).with_suffix(".pdf").name
                pdf.write_bytes(b"%PDF-1.4\\n%fake\\n")
                return
            raise AssertionError(f"Unexpected command: {cmd}")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            docx_path = tmp_dir / "songbook.docx"
            docx_path.write_bytes(b"fake docx")
            pdf_path = tmp_dir / "songbook.pdf"

            out_path, err = convert_document_to_pdf(
                docx_path,
                pdf_path=pdf_path,
                runner=fake_runner,
                which=fake_which,
            )

            self.assertIsNone(err)
            self.assertEqual(out_path, pdf_path)
            self.assertTrue(pdf_path.exists())
            self.assertGreater(len(calls), 0)

