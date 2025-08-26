"""
ChromaDB service for message retrieval
"""

import chromadb
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.logging import get_logger
from config.settings import settings
from models.api import MessageResult

logger = get_logger(__name__)


class ChromaDBService:
    """ChromaDB service for retrieving chat messages"""

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

            # Get existing collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(
                    f"✅ Connected to existing collection: {self.collection_name}"
                )
            except Exception as e:
                logger.warning(f"Collection {self.collection_name} not found: {e}")
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "Chat messages with semantic embeddings",
                        "created_at": datetime.now().isoformat(),
                    },
                )
                logger.info(f"✅ Created new collection: {self.collection_name}")

            logger.info(f"✅ ChromaDB initialized: {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"❌ ChromaDB initialization failed: {e}")
            return False

    async def get_messages(
        self,
        conversation_id: Optional[str] = None,
        sender_id: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[MessageResult]:
        """Retrieve messages with filters"""
        if not self.collection:
            raise RuntimeError("ChromaDB not initialized")

        try:
            # Build where clause with proper ChromaDB syntax
            where_clause = None
            if conversation_id and sender_id:
                # Use $and operator for multiple conditions
                where_clause = {
                    "$and": [
                        {"conversation_id": {"$eq": conversation_id}},
                        {"sender_id": {"$eq": sender_id}},
                    ]
                }
            elif conversation_id:
                where_clause = {"conversation_id": {"$eq": conversation_id}}
            elif sender_id:
                where_clause = {"sender_id": {"$eq": sender_id}}

            # Get all matching documents
            results = self.collection.get(
                where=where_clause,
                include=["metadatas", "documents"],
            )

            # Convert to MessageResult objects
            messages = []
            if results["ids"]:
                # Sort by sent_at (assuming metadata contains sent_at)
                indexed_results = list(
                    zip(
                        results["ids"],
                        results["metadatas"] or [],
                        results["documents"] or [],
                    )
                )

                # Sort by sent_at descending
                try:
                    indexed_results.sort(
                        key=lambda x: datetime.fromisoformat(
                            x[1].get("sent_at", "1970-01-01")
                        ),
                        reverse=True,
                    )
                except Exception as e:
                    logger.warning(f"Could not sort by sent_at: {e}")

                # Apply pagination
                start_idx = offset
                end_idx = offset + limit
                paginated_results = indexed_results[start_idx:end_idx]

                for message_id, metadata, content in paginated_results:
                    try:
                        message = MessageResult(
                            message_id=message_id,
                            conversation_id=metadata.get("conversation_id", ""),
                            sender_id=metadata.get("sender_id", ""),
                            content=content,
                            sent_at=datetime.fromisoformat(
                                metadata.get("sent_at", datetime.now().isoformat())
                            ),
                        )
                        messages.append(message)
                    except Exception as e:
                        logger.error(f"Error processing message {message_id}: {e}")
                        continue

            return messages

        except Exception as e:
            logger.error(f"❌ Failed to retrieve messages: {e}")
            return []

    async def search_similar(
        self,
        query_texts: str,
        conversation_id: Optional[str] = None,
        sender_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[MessageResult]:
        """Search for similar messages using semantic similarity"""
        if not self.collection:
            raise RuntimeError("ChromaDB not initialized")

        try:
            # Build where clause with proper ChromaDB syntax
            where_clause = None
            if conversation_id and sender_id:
                # Use $and operator for multiple conditions
                where_clause = {
                    "$and": [
                        {"conversation_id": {"$eq": conversation_id}},
                        {"sender_id": {"$eq": sender_id}},
                    ]
                }
            elif conversation_id:
                where_clause = {"conversation_id": {"$eq": conversation_id}}
            elif sender_id:
                where_clause = {"sender_id": {"$eq": sender_id}}

            # Perform semantic search
            results = self.collection.query(
                query_texts=[query_texts],
                n_results=limit,
                where=where_clause,
                include=["metadatas", "documents", "distances"],
            )

            # Parse results
            messages = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    message_id = results["ids"][0][i]
                    metadata = results["metadatas"][0][i]
                    content = results["documents"][0][i]
                    distance = results["distances"][0][i]

                    # Calculate similarity score (1 - distance)
                    similarity_score = max(0, 1 - distance)

                    message = MessageResult(
                        message_id=message_id,
                        conversation_id=metadata.get("conversation_id", ""),
                        sender_id=metadata.get("sender_id", ""),
                        content=content,
                        sent_at=datetime.fromisoformat(
                            metadata.get("sent_at", datetime.now().isoformat())
                        ),
                        similarity_score=similarity_score,
                    )
                    messages.append(message)

            return messages

        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
            return []

    async def get_recent_messages(
        self,
        conversation_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[MessageResult]:
        """Get most recent messages"""
        return await self.get_messages(
            conversation_id=conversation_id, limit=limit, offset=0
        )

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
