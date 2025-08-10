"""
Embedding service for text vectorization
"""

from typing import List
from sentence_transformers import SentenceTransformer

from core.logging import get_logger
from config.settings import settings

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings"""

    def __init__(self):
        self.model: SentenceTransformer = None
        self.model_name = settings.embedding_model_name

    async def initialize(self) -> bool:
        """Initialize embedding model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"✅ Embedding model loaded: {self.model_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            return False

    def encode(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")

        try:
            embedding = self.model.encode([text])[0]
            return embedding.tolist()

        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            raise

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")

        try:
            embeddings = self.model.encode(texts)
            return [emb.tolist() for emb in embeddings]

        except Exception as e:
            logger.error(f"❌ Failed to generate batch embeddings: {e}")
            raise


# Global service instance
embedding_service = EmbeddingService()
