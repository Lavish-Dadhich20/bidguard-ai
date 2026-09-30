"""
Document-type-agnostic PDF text extraction with OCR fallback.

Flow:
    PDF -> embedded text layer
        -> if unusable -> Poppler renders page(s) to images
        -> Tesseract OCR
        -> plain text for the document-specific extractor

OCR is configured automatically on Windows. It first checks PATH, then
common Tesseract locations and the WinGet Poppler installation location.
No per-user absolute path is required in the project.
"""

from dataclasses import dataclass, field
from pathlib import Path
import shutil
import tempfile

import pdfplumber


WATERMARK_FONT_SIZE_THRESHOLD = 20.0
MIN_USABLE_TEXT_CHARS = 60
LINE_GROUPING_TOLERANCE = 3.0
OCR_DPI = 300


@dataclass
class ExtractionResult:
    text: str
    method: str  # "PDF_TEXT" or "OCR"
    ocr_used: bool
    pages_processed: int
    warnings: list = field(default_factory=list)


def _clean_page_text(page) -> str:
    """Extract readable text while ignoring large decorative text."""
    words = page.extract_words(extra_attrs=["size"])
    content_words = [
        w for w in words if w.get("size", 0) <= WATERMARK_FONT_SIZE_THRESHOLD
    ]

    if not content_words:
        return ""

    content_words.sort(key=lambda w: (w["top"], w["x0"]))

    lines = []
    current_line = [content_words[0]]
    current_top = content_words[0]["top"]

    for word in content_words[1:]:
        if abs(word["top"] - current_top) <= LINE_GROUPING_TOLERANCE:
            current_line.append(word)
        else:
            lines.append(current_line)
            current_line = [word]
            current_top = word["top"]

    lines.append(current_line)

    return "\n".join(
        " ".join(w["text"] for w in sorted(line, key=lambda w: w["x0"]))
        for line in lines
    )


def _extract_pdf_text_layer(pdf_path: str) -> tuple[str, int]:
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        pages_processed = len(pdf.pages)
        for page in pdf.pages:
            all_text.append(_clean_page_text(page))
    return "\n".join(all_text).strip(), pages_processed


def _is_text_usable(text: str) -> bool:
    alnum_chars = sum(1 for char in text if char.isalnum())
    return alnum_chars >= MIN_USABLE_TEXT_CHARS


def _find_tesseract() -> str | None:
    """Find tesseract.exe without requiring the user to edit PATH."""
    found = shutil.which("tesseract")
    if found:
        return found

    candidates = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)

    return None


def _find_poppler() -> str | None:
    """Find the directory containing pdftoppm/pdfinfo."""
    # PATH first.
    if shutil.which("pdftoppm") and shutil.which("pdfinfo"):
        return None  # pdf2image can use PATH directly.

    local_app_data = Path.home() / "AppData" / "Local"
    winget_packages = local_app_data / "Microsoft" / "WinGet" / "Packages"

    if winget_packages.is_dir():
        # This covers the standard oschwartz10612.Poppler WinGet install.
        for pdftoppm in winget_packages.rglob("pdftoppm.exe"):
            bin_dir = pdftoppm.parent
            if (bin_dir / "pdfinfo.exe").is_file():
                return str(bin_dir)

    common_dirs = [
        Path(r"C:\Program Files\poppler\Library\bin"),
        Path(r"C:\Program Files\poppler\bin"),
        Path(r"C:\poppler\Library\bin"),
        Path(r"C:\poppler\bin"),
    ]

    for directory in common_dirs:
        if (directory / "pdftoppm.exe").is_file() and (directory / "pdfinfo.exe").is_file():
            return str(directory)

    return None


def _preprocess_for_ocr(image):
    """Return a few OCR-friendly versions of a page.

    PAN cards and similar Indian government cards often have blue backgrounds.
    The blue colour channel can produce substantially cleaner text than a
    normal grayscale conversion, so it is tried first.
    """
    from PIL import ImageEnhance, ImageOps

    rgb = image.convert("RGB")

    versions = []

    # Blue channel: particularly useful for blue PAN-card backgrounds.
    blue = rgb.getchannel("B")
    blue = ImageOps.autocontrast(blue)
    blue = blue.resize((blue.width * 2, blue.height * 2))
    blue = ImageEnhance.Contrast(blue).enhance(1.8)
    versions.append(blue)

    # Standard grayscale fallback.
    gray = ImageOps.grayscale(rgb)
    gray = ImageOps.autocontrast(gray)
    gray = gray.resize((gray.width * 2, gray.height * 2))
    gray = ImageEnhance.Contrast(gray).enhance(1.5)
    versions.append(gray)

    return versions


def _extract_via_ocr(pdf_path: str) -> tuple[str, int, list[str]]:
    """Render PDF pages with Poppler and OCR them with Tesseract."""
    import pytesseract
    from pdf2image import convert_from_path

    warnings = []

    tesseract_cmd = _find_tesseract()
    if not tesseract_cmd:
        raise RuntimeError(
            "Tesseract was not found. Install Tesseract OCR or add "
            "tesseract.exe to PATH."
        )
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    poppler_path = _find_poppler()
    if not poppler_path and not shutil.which("pdftoppm"):
        raise RuntimeError(
            "Poppler was not found. Install Poppler or add its Library\\bin "
            "directory containing pdftoppm.exe and pdfinfo.exe to PATH."
        )

    convert_kwargs = {
        "dpi": OCR_DPI,
        "fmt": "png",
        "thread_count": 1,
    }
    if poppler_path:
        convert_kwargs["poppler_path"] = poppler_path

    images = convert_from_path(pdf_path, **convert_kwargs)
    page_texts = []

    for image in images:
        candidates = []
        for processed in _preprocess_for_ocr(image):
            for psm in (6,):
                text = pytesseract.image_to_string(
                    processed,
                    lang="eng",
                    config=f"--psm {psm}",
                ).strip()
                if text:
                    candidates.append(text)

        # Pick the OCR pass with the most useful alphanumeric content.
        best = max(
            candidates,
            key=lambda value: sum(char.isalnum() for char in value),
            default="",
        )
        page_texts.append(best)

    return "\n".join(page_texts).strip(), len(images), warnings


def get_document_text(pdf_path: str) -> ExtractionResult:
    """Extract PDF text, falling back to OCR when the text layer is unusable."""
    warnings = []

    text, pages_processed = _extract_pdf_text_layer(pdf_path)

    if _is_text_usable(text):
        return ExtractionResult(
            text=text,
            method="PDF_TEXT",
            ocr_used=False,
            pages_processed=pages_processed,
            warnings=warnings,
        )

    warnings.append(
        "Embedded PDF text layer produced insufficient text; falling back to OCR."
    )

    try:
        ocr_text, ocr_pages, ocr_warnings = _extract_via_ocr(pdf_path)
        warnings.extend(ocr_warnings)
    except Exception as exc:
        warnings.append(f"OCR extraction failed: {exc}")
        return ExtractionResult(
            text=text,
            method="PDF_TEXT",
            ocr_used=False,
            pages_processed=pages_processed,
            warnings=warnings,
        )

    if not _is_text_usable(ocr_text):
        warnings.append("OCR completed but produced very little usable text.")

    return ExtractionResult(
        text=ocr_text,
        method="OCR",
        ocr_used=True,
        pages_processed=ocr_pages,
        warnings=warnings,
    )
