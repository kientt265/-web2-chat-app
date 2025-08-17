"""
Embedding service for semantic search
"""

from typing import List
from sentence_transformers import SentenceTransformer

from core.logging import get_logger
from config.settings import settings

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings"""

    def __init__(self):
        self.model = None
        self.model_name = settings.embedding_model_name

    async def initialize(self) -> bool:
        """Initialize the embedding model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("✅ Embedding model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            return False

    def encode(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")

        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            raise


# Global service instance
embedding_service = EmbeddingService()
