import threading
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.core.logging import logger


class EmbeddingService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(EmbeddingService, cls).__new__(cls)
                    cls._instance._model = None
        return cls._instance

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            with self._lock:
                if self._model is None:
                    logger.info(f"Loading SentenceTransformer model: {settings.EMBEDDING_MODEL_NAME}...")
                    self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                    logger.info("SentenceTransformer model loaded successfully.")
        return self._model

    def encode_text(self, text: str) -> List[float]:
        """Generate normalized vector embedding for a single text query."""
        if not text or not text.strip():
            return [0.0] * settings.EMBEDDING_DIMENSION
        model = self._get_model()
        embedding = model.encode(text.strip(), normalize_embeddings=True)
        return embedding.tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized vector embeddings for a list of text chunks."""
        if not texts:
            return []
        model = self._get_model()
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.tolist()

    def is_loaded(self) -> bool:
        return self._model is not None


embedding_service = EmbeddingService()
