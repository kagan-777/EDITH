"""Build prompt context that COVERS the whole document.

The old code always retrieved the same 5 chunks for "important concepts", so
notes / summary / plan / quiz only ever saw ~5000 characters. Here we pick
chunks evenly spread across the entire document instead.
"""
import random

from backend.errors import NoDocumentError
from backend.retriever import get_all_chunks


def select_spread(chunks, max_chars, offset=0.0):
    """Pick evenly spaced chunks whose combined size is about `max_chars`.
    `offset` (0..1) shifts the picks, giving different samples each time."""
    if not chunks:
        return []
    if sum(len(c["text"]) for c in chunks) <= max_chars:
        return list(chunks)
    avg = sum(len(c["text"]) for c in chunks) / len(chunks)
    n = min(len(chunks), max(1, int(max_chars // max(avg, 1))))
    step = len(chunks) / n
    idx = sorted({min(len(chunks) - 1, int((i + offset) * step)) for i in range(n)})
    return [chunks[i] for i in idx]


def label(chunk):
    return f"{chunk.get('unit', 'Page')} {chunk['page']}"


def format_context(chunks):
    return "\n\n".join(f"[{label(c)}]\n{c['text']}\n-----" for c in chunks)


def build_context(username, max_chars=12000, randomize=False):
    chunks = get_all_chunks(username)
    if not chunks:
        raise NoDocumentError("No document found. Please upload your study material first.")
    offset = random.random() * 0.999 if randomize else 0.0
    picked = select_spread(chunks, max_chars, offset)
    return format_context(picked)


def sources_line(chunks):
    """'Page 3, 5, 9' style string from retrieved chunks."""
    if not chunks:
        return ""
    unit = chunks[0].get("unit", "Page")
    pages = sorted({c["page"] for c in chunks if c["page"]})
    return f"{unit}s " + ", ".join(map(str, pages)) if pages else ""
