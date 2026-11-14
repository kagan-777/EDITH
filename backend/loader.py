"""Read PDF / DOCX / TXT into page-numbered documents.

Every document gets metadata:  page (1-based int), source (file name),
unit ("Page" for PDFs, "Section" for DOCX/TXT which have no real pages).
No Streamlit imports here.
"""
import os
import re
import zipfile
import xml.etree.ElementTree as ET

SECTION_CHARS = 3000
SUPPORTED = (".pdf", ".docx", ".txt")


def _make_document(text, page, source, unit):
    metadata = {"page": int(page), "source": source, "unit": unit}
    try:
        from langchain_core.documents import Document
        return Document(page_content=text, metadata=metadata)
    except ImportError:  # keeps the loader testable without langchain
        from types import SimpleNamespace
        return SimpleNamespace(page_content=text, metadata=metadata)


def _sections(text):
    """Group paragraphs into ~3000 character 'sections' (virtual pages)."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\r\n\s*\r\n", text) if p.strip()]
    sections, current = [], ""
    for p in paragraphs:
        if current and len(current) + len(p) > SECTION_CHARS:
            sections.append(current)
            current = ""
        current = f"{current}\n\n{p}" if current else p
    if current:
        sections.append(current)
    return sections


def _text_docs(text, source):
    return [
        _make_document(sec, i, source, "Section")
        for i, sec in enumerate(_sections(text), start=1)
    ]


def _load_txt(path, source):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return _text_docs(f.read(), source)


def _docx_text(path):
    try:
        import docx
    except ImportError:
        docx = None

    if docx is not None:
        document = docx.Document(path)
        parts = [p.text for p in document.paragraphs]
        for table in document.tables:                      # tables were ignored before
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return "\n\n".join(parts)

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    paragraphs = []
    for p in root.findall(".//w:p", ns):
        t = "".join(n.text or "" for n in p.findall(".//w:t", ns))
        if t.strip():
            paragraphs.append(t)
    return "\n\n".join(paragraphs)


def _load_pdf(path, source):
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ImportError("pypdf is required for PDFs. Install: pip install pypdf") from exc

    docs = []
    for page_number, page in enumerate(PdfReader(path).pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:  # skip blank pages
            docs.append(_make_document(text, page_number, source, "Page"))
    return docs


def load_document(file_path):
    """Return a list of documents, or raise ValueError with a friendly message."""
    ext = os.path.splitext(file_path)[1].lower()
    source = os.path.basename(file_path)

    if ext == ".pdf":
        docs = _load_pdf(file_path, source)
    elif ext == ".txt":
        docs = _load_txt(file_path, source)
    elif ext == ".docx":
        try:
            docs = _text_docs(_docx_text(file_path), source)
        except Exception as exc:  # corrupt / not a real .docx
            raise ValueError("Could not read this DOCX file. It may be corrupt.") from exc
    else:
        raise ValueError(f"Unsupported file type '{ext}'. Use PDF, DOCX or TXT.")

    if not docs:
        raise ValueError(
            "No readable text found. If this is a scanned PDF (images only), "
            "run OCR on it first and upload the result."
        )
    return docs


def full_text(documents) -> str:
    return "\n\n".join(d.page_content for d in documents)
