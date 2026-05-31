import io
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def write_minimal_pdf(pdf_path, page_texts):
    if isinstance(page_texts, str):
        page_texts = [page_texts]

    writer = PdfWriter()
    font_object = writer._add_object(  # noqa: SLF001
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
    )

    for text in page_texts:
        page = writer.add_blank_page(width=200, height=200)
        if not text:
            continue

        escaped_text = (
            str(text)
            .replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )
        content = "BT /F1 12 Tf 10 100 Td ({}) Tj ET\n".format(escaped_text)
        stream = DecodedStreamObject()
        stream.set_data(content.encode("utf-8"))
        page[NameObject("/Contents")] = stream

        resources = page.get("/Resources") or DictionaryObject()
        fonts = resources.get("/Font") or DictionaryObject()
        fonts.update({NameObject("/F1"): font_object})
        resources[NameObject("/Font")] = fonts
        page[NameObject("/Resources")] = resources

    buffer = io.BytesIO()
    writer.write(buffer)
    Path(pdf_path).write_bytes(buffer.getvalue())

