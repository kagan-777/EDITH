from backend.errors import NoDocumentError
from backend.vectorstore import get_all_chunks as _get_all_chunks
from backend.vectorstore import search_chunks


def get_all_chunks(username):
    """Every stored chunk as {'text', 'page', 'unit'} sorted by page."""
    return [
        {"text": chunk["text"], "page": chunk["page"], "unit": chunk["unit"]}
        for chunk in _get_all_chunks(username)
    ]


def search(username, query, k=5):
    """Similarity search -> list of {'text','page','unit'}. Raises if nothing indexed."""
    chunks = search_chunks(username, query, k)
    if not chunks:
        if not _get_all_chunks(username):
            raise NoDocumentError("No document found. Please upload your study material first.")
        return []
    return [
        {
            "text": chunk["text"],
            "page": int(chunk.get("page", 0) or 0),
            "unit": chunk.get("unit", "Page"),
        }
        for chunk in chunks
    ]
