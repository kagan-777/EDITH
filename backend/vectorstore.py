"""Per-user JSON document index with semantic search and a BM25 fallback."""
import json
import logging
import math
import re

from backend import user_db
from backend.embeddings import get_embedding_model

logger = logging.getLogger(__name__)
INDEX_FILE = "document_index.json"
TOKEN_RE = re.compile(r"\w+", re.UNICODE)
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "for",
    "from", "how", "i", "in", "is", "it", "of", "on", "or", "that", "the",
    "this", "to", "was", "what", "when", "where", "which", "who", "why",
    "with", "you",
}
MIN_SEMANTIC_SIMILARITY = 0.3


def _index_path(username):
    return user_db.user_dir(username) / INDEX_FILE


def _read_index(username):
    path = _index_path(username)
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Document index for {username} is not valid JSON.") from exc
    if (
        not isinstance(data, dict)
        or data.get("version") != 1
        or not isinstance(data.get("chunks"), list)
    ):
        raise ValueError(f"Document index for {username} has an unsupported format.")
    return data["chunks"]


def _document_text(chunk):
    return chunk.page_content


def _metadata(chunk):
    return dict(chunk.metadata or {})


def reset_vector_store(username):
    """Remove only the user's search index."""
    path = _index_path(username)
    if path.exists():
        path.unlink()


def create_vector_store(chunks, username):
    if not chunks:
        raise ValueError("Nothing to index: the document produced no text chunks.")

    records = []
    for chunk in chunks:
        metadata = _metadata(chunk)
        records.append({
            "text": _document_text(chunk),
            "page": int(metadata.get("page", 0) or 0),
            "unit": metadata.get("unit", "Page"),
            "source": metadata.get("source", ""),
            "embedding": None,
        })

    try:
        model = get_embedding_model()
        vectors = model.embed_documents([record["text"] for record in records])
        if len(vectors) != len(records):
            raise ValueError("Embedding model returned an unexpected number of vectors.")
        embeddings = [[float(value) for value in vector] for vector in vectors]
        for record, embedding in zip(records, embeddings):
            record["embedding"] = embedding
    except Exception:
        logger.exception("Embedding model unavailable; indexing with BM25 keyword search.")

    user_db.atomic_write_json(_index_path(username), {
        "version": 1,
        "chunks": records,
    })
    return records


def get_all_chunks(username):
    """Return all indexed chunks sorted by page."""
    chunks = _read_index(username)
    chunks.sort(key=lambda chunk: int(chunk.get("page", 0) or 0))
    return chunks


def _cosine_similarity(left, right):
    if len(left) != len(right):
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def _tokens(text):
    return [
        token for token in TOKEN_RE.findall(text.casefold())
        if token not in STOP_WORDS
    ]


def _bm25_search(chunks, query, k):
    query_terms = set(_tokens(query))
    if not query_terms:
        return []

    documents = [_tokens(chunk["text"]) for chunk in chunks]
    doc_freq = {}
    for tokens in documents:
        for term in query_terms.intersection(tokens):
            doc_freq[term] = doc_freq.get(term, 0) + 1

    count = len(documents)
    average_length = sum(map(len, documents)) / count if count else 0
    scored = []
    for index, (chunk, tokens) in enumerate(zip(chunks, documents)):
        frequencies = {}
        for term in tokens:
            if term in query_terms:
                frequencies[term] = frequencies.get(term, 0) + 1
        score = 0.0
        for term, frequency in frequencies.items():
            inverse_frequency = math.log(
                1 + (count - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5)
            )
            length_norm = (
                frequency + 1.5 * (1 - 0.75 + 0.75 * len(tokens) / average_length)
                if average_length
                else frequency + 1.5
            )
            score += inverse_frequency * frequency * 2.5 / length_norm
        scored.append((score, index, chunk))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [chunk for score, _, chunk in scored[:k] if score > 0]


def search_chunks(username, query, k=5):
    """Return the most relevant chunks, using BM25 if semantic search fails."""
    chunks = _read_index(username)
    if not chunks:
        return []

    k = max(1, int(k))
    vectors = [chunk.get("embedding") for chunk in chunks]
    if all(vector is not None for vector in vectors):
        try:
            query_vector = get_embedding_model().embed_query(query)
            scored = [
                (_cosine_similarity(query_vector, vector), index, chunk)
                for index, (chunk, vector) in enumerate(zip(chunks, vectors))
            ]
            scored.sort(key=lambda item: (-item[0], item[1]))
            if scored[0][0] >= MIN_SEMANTIC_SIMILARITY:
                return [chunk for _, _, chunk in scored[:k]]
        except Exception:
            logger.exception("Semantic search failed; falling back to BM25 keyword search.")

    return _bm25_search(chunks, query, k)


def delete_document(username):
    """Remove the search index and stored document files for this user."""
    reset_vector_store(username)
    user_db.clear_user_files(username)
