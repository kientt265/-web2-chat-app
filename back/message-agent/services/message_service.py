from services.chromadb_service import chromadb_service


class MessageService:
    def __init__(self):
        self.chromadb_service = chromadb_service

    async def search_messages(
        self,
        query_texts: str,
        conversation_id: str | None,
        sender_id: str | None,
        limit: int = 10,
    ):
        """
        Search messages in the database using the provided query and agent type.
        """
        try:
            # Check if ChromaDB is initialized
            if not self.chromadb_service or not self.chromadb_service.collection:
                raise RuntimeError("ChromaDB not initialized")

            results = await self.chromadb_service.search_similar(
                query_texts=query_texts,  # Pass as string, not list
                conversation_id=conversation_id,
                sender_id=sender_id,
                limit=limit,
            )
            return results
        except Exception as e:
            raise Exception(f"Error searching messages: {str(e)}")


message_service = MessageService()
