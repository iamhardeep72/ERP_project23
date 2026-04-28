# ============================================================
# extractor.py — Text Extraction from PDF / Images
# ============================================================
# Uses:
#   • PyMuPDF  (fitz)       → PDF text extraction (fast, no OCR needed for digital PDFs)
#   • Pytesseract + Pillow  → OCR for image files and scanned PDFs
# ============================================================

import io
import logging

log = logging.getLogger(__name__)


def extract_text(file_bytes: bytes, content_type: str) -> str:
    """
    Extract text from a PDF or image file.

    Args:
        file_bytes:   Raw bytes of the uploaded file.
        content_type: MIME type (e.g. 'application/pdf', 'image/png').

    Returns:
        A single string containing all extracted text.
    """
    if content_type == "application/pdf":
        return _extract_from_pdf(file_bytes)
    else:
        # image/png, image/jpeg, image/webp
        return _extract_from_image(file_bytes)


# ── PDF Extraction ────────────────────────────────────────────

def _extract_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF using PyMuPDF.
    If a page has no selectable text (scanned page), fall back to OCR.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PyMuPDF is not installed. Run: pip install PyMuPDF"
        )

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_text = []

    for page_num, page in enumerate(doc):
        text = page.get_text("text").strip()

        if text:
            # Digital PDF — text layer available
            log.info(f"Page {page_num + 1}: extracted {len(text)} chars via text layer.")
            pages_text.append(text)
        else:
            # Scanned page — render to image and OCR
            log.info(f"Page {page_num + 1}: no text layer found, falling back to OCR.")
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            ocr_text = _extract_from_image(img_bytes)
            pages_text.append(ocr_text)

    doc.close()
    return "\n\n".join(pages_text)


# ── Image OCR ─────────────────────────────────────────────────

def _extract_from_image(file_bytes: bytes) -> str:
    """
    Run OCR on an image using Pytesseract.
    Pre-processes the image for better accuracy.
    """
    try:
        import pytesseract
        from PIL import Image, ImageFilter, ImageOps
    except ImportError:
        raise ImportError(
            "Pillow or pytesseract is not installed. "
            "Run: pip install Pillow pytesseract  (and install Tesseract binary)"
        )

    # Open image
    image = Image.open(io.BytesIO(file_bytes))

    # ── Pre-processing for better OCR accuracy ──
    # 1. Convert to grayscale
    image = image.convert("L")

    # 2. Upscale if small (Tesseract works best at 300+ DPI)
    min_dim = 1500
    w, h = image.size
    if w < min_dim or h < min_dim:
        scale = min_dim / min(w, h)
        image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # 3. Sharpen slightly
    image = image.filter(ImageFilter.SHARPEN)

    # Run Tesseract OCR (PSM 6 = assume a single uniform block of text)
    custom_config = r"--oem 3 --psm 6"
    text = pytesseract.image_to_string(image, config=custom_config)

    log.info(f"OCR extracted {len(text)} characters from image.")
    return text
