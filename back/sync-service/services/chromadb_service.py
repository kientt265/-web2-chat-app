"""
ChromaDB service for vector database operations
"""

import chromadb
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.logging import get_logger
from config.settings import settings
from models.cdc import MessageData
from models.api import SearchResult

logger = get_logger(__name__)


class ChromaDBService:
    """ChromaDB service for managing chat message embeddings"""

    def __init__(self):
        self.client: Optional[chromadb.Client] = None
        self.collection = None
        self.host = settings.chromadb_host
        self.port = settings.chromadb_port
        self.collection_name = settings.chromadb_collection_name

    async def initialize(self) -> bool:
        """Initialize ChromaDB client and collection"""
        try:
            self.client = chromadb.HttpClient(host=self.host, port=self.port)

            # Test connection
            heartbeat = self.client.heartbeat()
            logger.info(f"ChromaDB heartbeat: {heartbeat}")

            # Create or get collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "Chat messages with semantic embeddings",
                    "created_at": datetime.now().isoformat(),
                },
            )

            logger.info(f"✅ ChromaDB initialized: {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"❌ ChromaDB initialization failed: {e}")
            return False

    async def upsert_message(
        self, message: MessageData, embedding: List[float]
    ) -> bool:
        """Insert or update message with embedding"""
        if not self.collection:
            raise RuntimeError("ChromaDB not initialized")

        try:
            metadata = {
                "conversation_id": message.conversation_id,
                "sender_id": message.sender_id,
                "sent_at": message.sent_at.isoformat(),
                "operation": message.operation,
                "indexed_at": datetime.now().isoformat(),
            }

            self.collection.upsert(
                ids=[message.message_id],
                embeddings=[embedding],
                documents=[message.content],
                metadatas=[metadata],
            )

            logger.debug(f"✅ Upserted message: {message.message_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to upsert message {message.message_id}: {e}")
            return False

    async def delete_message(self, message_id: str) -> bool:
        """Delete message from ChromaDB"""
        if not self.collection:
            raise RuntimeError("ChromaDB not initialized")

        try:
            self.collection.delete(ids=[message_id])
            logger.debug(f"✅ Deleted message: {message_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete message {message_id}: {e}")
            return False

    async def search_similar(
        self,
        query_embedding: List[float],
        conversation_id: Optional[str] = None,
        sender_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[SearchResult]:
        """Search for similar messages"""
        if not self.collection:
            raise RuntimeError("ChromaDB not initialized")

        try:
            # Build where clause
            where_clause = {}
            if conversation_id:
                where_clause["conversation_id"] = conversation_id
            if sender_id:
                where_clause["sender_id"] = sender_id

            # Perform search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause if where_clause else None,
                include=["metadatas", "documents", "distances"],
            )

            # Parse results
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    message_id = results["ids"][0][i]
                    metadata = results["metadatas"][0][i]
                    content = results["documents"][0][i]
                    distance = results["distances"][0][i]

                    similarity_score = max(0, 1 - distance)

                    search_result = SearchResult(
                        message_id=message_id,
                        conversation_id=metadata["conversation_id"],
                        sender_id=metadata["sender_id"],
                        content=content,
                        sent_at=datetime.fromisoformat(metadata["sent_at"]),
                        similarity_score=similarity_score,
                    )
                    search_results.append(search_result)

            return search_results

        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        if not self.collection:
            raise RuntimeError("ChromaDB not initialized")

        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "status": "healthy",
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {"status": "error", "error": str(e)}


# Global service instance
chromadb_service = ChromaDBService()
