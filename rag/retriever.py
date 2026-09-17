"""Vector retriever adapter for backward compatibility."""

from app.services.embedding import embedding_service
from app.services.retriever import retriever_service


def get_embedding_model():
    """Load the embedding model only when retrieval is first requested."""
    return embedding_service._get_model()


def retrieve_chunks(question: str, top_k: int = 2, similarity_threshold: float = 0.5):
    """Retrieve top-k chunks matching the question with similarity >= threshold."""
    return retriever_service.retrieve(
        query=question,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
    )
