from functools import lru_cache

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    """Loaded ONCE per process (the old code reloaded it on every question)."""
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError as exc:
        raise ImportError(
            "langchain-huggingface is required. Install: pip install langchain-huggingface"
        ) from exc
    return HuggingFaceEmbeddings(model_name=MODEL_NAME)
