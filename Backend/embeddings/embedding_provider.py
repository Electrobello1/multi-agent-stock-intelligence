from functools import lru_cache

from Backend.embeddings.embedding_service import (
    EmbeddingService
)


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """
    Return one shared EmbeddingService instance
    for the lifetime of this Python process.

    The embedding model is therefore loaded once
    instead of once per request.
    """

    return EmbeddingService()