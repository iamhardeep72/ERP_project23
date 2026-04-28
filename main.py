# ============================================================
# main.py — MediScan FastAPI Backend
# ============================================================
# Endpoints:
#   GET  /          → health check
#   POST /analyze   → upload file, extract text, run AI analysis
# ============================================================

import os
import io
import json
import logging

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from extractor import extract_text          # OCR / PDF text extraction
from analyzer import analyze_report         # AI analysis via Claude API

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")
log = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title="MediScan API",
    description="AI-powered medical report analyzer",
    version="1.0.0",
)

# ── CORS ─────────────────────────────────────────────────────
# Allows the frontend (any origin during development) to call this API.
# In production, replace "*" with your actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Allowed file types ────────────────────────────────────────
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}
MAX_FILE_SIZE_MB = 10  # reject files larger than this


# ── Routes ───────────────────────────────────────────────────

@app.get("/")
async def health_check():
    """Simple health-check endpoint."""
    return {"status": "ok", "service": "MediScan API"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """
    Accept a PDF or image file, extract text via OCR/PDF parsing,
    then send the text to Claude AI for structured medical analysis.

    Returns:
        {
          "high_values":   [...],
          "low_values":    [...],
          "normal_values": [...]
        }
    """

    # 1. Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. "
                   "Please upload a PDF, PNG, JPEG, or WEBP file.",
        )

    # 2. Read file bytes
    raw_bytes = await file.read()

    # 3. Validate file size
    size_mb = len(raw_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed is {MAX_FILE_SIZE_MB} MB.",
        )

    log.info(f"Received file: {file.filename!r} ({size_mb:.2f} MB, {file.content_type})")

    # 4. Extract text from the file
    try:
        extracted_text = extract_text(raw_bytes, file.content_type)
    except Exception as exc:
        log.exception("Text extraction failed")
        raise HTTPException(status_code=422, detail=f"Could not extract text: {exc}")

    if not extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text found in the file. "
                   "Make sure the document contains actual text or a clear scan.",
        )

    log.info(f"Extracted {len(extracted_text)} characters of text.")

    # 5. AI analysis
    try:
        analysis = analyze_report(extracted_text)
    except Exception as exc:
        log.exception("AI analysis failed")
        raise HTTPException(status_code=502, detail=f"AI analysis error: {exc}")

    log.info(
        f"Analysis complete — high: {len(analysis.get('high_values', []))}, "
        f"low: {len(analysis.get('low_values', []))}, "
        f"normal: {len(analysis.get('normal_values', []))}"
    )

    return JSONResponse(content=analysis)
