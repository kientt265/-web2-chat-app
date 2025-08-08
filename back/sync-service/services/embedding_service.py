"""
Embedding service for text vectorization
"""
from typing import List
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from core.logging import get_logger
from config.settings import settings

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using ChromaDB default function"""
    
    def __init__(self):
        self.embedding_function: DefaultEmbeddingFunction = None
        
    async def initialize(self) -> bool:
        """Initialize ChromaDB default embedding function"""
        try:
            self.embedding_function = DefaultEmbeddingFunction()
            logger.info(f"✅ ChromaDB default embedding function initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize embedding function: {e}")
            return False
    
    def encode(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not self.embedding_function:
            raise RuntimeError("Embedding function not initialized")
        
        try:
            # ChromaDB's DefaultEmbeddingFunction expects a list of texts
            embeddings = self.embedding_function([text])
            # Convert numpy array to list
            return embeddings[0].tolist()  # Return the first (and only) embedding as list
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            raise
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.embedding_function:
            raise RuntimeError("Embedding function not initialized")
        
        try:
            embeddings = self.embedding_function(texts)
            # Convert numpy arrays to lists
            return [embedding.tolist() for embedding in embeddings]
            
        except Exception as e:
            logger.error(f"❌ Failed to generate batch embeddings: {e}")
            raise


# Global service instance
embedding_service = EmbeddingService()
