"""
Search Service
Business logic for semantic search operations
"""

import httpx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from core.logging import get_logger

logger = get_logger(__name__)


class SearchResult(BaseModel):
    """Search result model"""

    conversation_id: str
    message_id: str
    content: str
    timestamp: str
    similarity_score: float
    metadata: Dict[str, Any] = {}


class SearchService:
    """Service for semantic search operations"""

    def __init__(self, sync_service_url: str = "http://localhost:3005"):
        self.sync_service_url = sync_service_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_messages(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[SearchResult]:
        """Search for similar messages using semantic search"""
        logger.info(f"🔍 Searching messages: '{query}' (limit: {limit})")

        try:
            # Prepare search request
            search_params = {
                "query": query,
                "limit": limit,
                "similarity_threshold": similarity_threshold,
            }

            if conversation_id:
                search_params["conversation_id"] = conversation_id

            # Call sync service search endpoint
            response = await self.client.get(
                f"{self.sync_service_url}/search/messages", params=search_params
            )
            response.raise_for_status()

            search_data = response.json()

            # Convert to SearchResult objects
            results = []
            for item in search_data.get("results", []):
                result = SearchResult(
                    conversation_id=item.get("conversation_id", ""),
                    message_id=item.get("message_id", ""),
                    content=item.get("content", ""),
                    timestamp=item.get("timestamp", ""),
                    similarity_score=item.get("similarity_score", 0.0),
                    metadata=item.get("metadata", {}),
                )
                results.append(result)

            logger.info(f"✅ Found {len(results)} matching messages")
            return results

        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error searching messages: {e}")
            raise Exception(f"Search service error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error searching messages: {e}")
            raise Exception(f"Search error: {str(e)}")

    async def search_conversations(
        self, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for conversations based on content"""
        logger.info(f"🔍 Searching conversations: '{query}'")

        try:
            # Call sync service to get conversation summaries
            response = await self.client.get(
                f"{self.sync_service_url}/search/conversations",
                params={"query": query, "limit": limit},
            )
            response.raise_for_status()

            data = response.json()
            conversations = data.get("conversations", [])

            logger.info(f"✅ Found {len(conversations)} matching conversations")
            return conversations

        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error searching conversations: {e}")
            raise Exception(f"Search service error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error searching conversations: {e}")
            raise Exception(f"Search error: {str(e)}")

    async def check_sync_service_health(self) -> bool:
        """Check if sync service is available"""
        try:
            response = await self.client.get(f"{self.sync_service_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
