"""
utils/helpers.py
=================
PDF text extraction, page counting, and utility helpers.
"""

import io
import base64
import re
from typing import Optional


def extract_pdf_text(file_bytes: bytes) -> str:
    """
    Extract text from a PDF byte string.
    Tries pdfplumber first, falls back to PyPDF2, then pymupdf.
    """
    text = ""

    # ── Attempt 1: pdfplumber (best for structured text) ─────────────────────
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages_text = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                pages_text.append(page_text)
            text = "\n\n".join(pages_text)
        if text.strip():
            return _clean_text(text)
    except Exception:
        pass

    # ── Attempt 2: PyPDF2 ─────────────────────────────────────────────────────
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages:
            pages_text.append(page.extract_text() or "")
        text = "\n\n".join(pages_text)
        if text.strip():
            return _clean_text(text)
    except Exception:
        pass

    # ── Attempt 3: pymupdf (fitz) ─────────────────────────────────────────────
    try:
        import fitz  # pymupdf
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_text = []
        for page in doc:
            pages_text.append(page.get_text())
        text = "\n\n".join(pages_text)
        if text.strip():
            return _clean_text(text)
    except Exception:
        pass

    return ""


def get_page_count(file_bytes: bytes) -> int:
    """Return the number of pages in the PDF."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            return len(pdf.pages)
    except Exception:
        pass
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        return len(reader.pages)
    except Exception:
        pass
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        return len(doc)
    except Exception:
        return 0


def pdf_to_base64_preview(file_bytes: bytes) -> Optional[str]:
    """Return a base64-encoded data URI for embedding the PDF (first page)."""
    try:
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        return f"data:application/pdf;base64,{b64}"
    except Exception:
        return None


def _clean_text(text: str) -> str:
    """
    Light cleanup of raw PDF text:
    - Remove excessive whitespace / blank lines
    - Normalize unicode dashes and quotes
    """
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Normalize common unicode chars
    replacements = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "--",
        "\u00a0": " ",
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    return text.strip()


def truncate_snippet(text: str, keyword: str, window: int = 250) -> str:
    """
    Extract a snippet of `window` characters around the first occurrence of `keyword`.
    Returns empty string if keyword is not found.
    """
    if not text or not keyword:
        return ""
    idx = text.lower().find(keyword.lower())
    if idx == -1:
        return ""
    start = max(0, idx - window // 2)
    end = min(len(text), idx + window // 2)
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet


def find_all_snippets(text: str, keywords: list, window: int = 200) -> list:
    """Find all clause snippets matching any of the given keywords."""
    snippets = []
    seen_positions = set()
    for kw in keywords:
        idx = 0
        while True:
            pos = text.lower().find(kw.lower(), idx)
            if pos == -1:
                break
            # Avoid duplicate nearby snippets
            if not any(abs(pos - s) < 100 for s in seen_positions):
                seen_positions.add(pos)
                start = max(0, pos - window // 2)
                end = min(len(text), pos + window // 2)
                snippets.append(text[start:end].strip())
            idx = pos + 1
    return snippets[:5]  # Cap at 5


def word_count(text: str) -> int:
    return len(text.split()) if text else 0


def char_count(text: str) -> int:
    return len(text) if text else 0
