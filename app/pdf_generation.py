import logging
import shutil
import subprocess
from pathlib import Path


logger = logging.getLogger(__name__)


def _resolve_converter(which):
    for candidate in ("soffice", "libreoffice", "pandoc"):
        converter = which(candidate)
        if converter:
            return candidate
    return None


def convert_document_to_pdf(docx_path, pdf_path=None, runner=subprocess.run, which=shutil.which):
    source_path = Path(docx_path)
    target_path = Path(pdf_path) if pdf_path is not None else source_path.with_suffix(".pdf")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    converter = _resolve_converter(which)
    if converter is None:
        return None, "No PDF converter available"

    expected_generated_path = target_path
    command = None

    if converter in {"soffice", "libreoffice"}:
        expected_generated_path = target_path.parent / (source_path.stem + ".pdf")
        command = [
            converter,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(target_path.parent),
            str(source_path),
        ]
    elif converter == "pandoc":
        command = [
            converter,
            str(source_path),
            "-o",
            str(target_path),
        ]

    try:
        runner(command, check=True, capture_output=True, text=True)
    except Exception as exc:
        logger.warning("PDF conversion failed for %s: %s", source_path, exc)
        return None, str(exc)

    if expected_generated_path.exists() and expected_generated_path != target_path:
        if target_path.exists():
            target_path.unlink()
        expected_generated_path.replace(target_path)

    if not target_path.exists():
        return None, "PDF converter did not create output"

    logger.info("PDF document saved as %s.", target_path)
    return target_path, None
