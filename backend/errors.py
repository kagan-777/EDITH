class LLMError(RuntimeError):
    """The AI model call failed or returned unusable output."""


class NoDocumentError(RuntimeError):
    """The user has not uploaded / indexed a document yet."""
