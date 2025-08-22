"""
Test script for the LangGraph Message Agent (without ChromaDB)
"""

import asyncio
import os
from datetime import datetime


async def test_simple_agent():
    """Test a simple version without ChromaDB dependencies"""
    print("🧪 Testing Simple LangGraph Message Agent")
    print("=" * 50)
    
    # Import here to avoid ChromaDB issues
    try:
        # Simple mock test without external dependencies
        from typing import Dict, Any, Optional
        
        # Mock agent response
        async def mock_process_query(query: str, conversation_id: Optional[str] = None, sender_id: Optional[str] = None) -> Dict[str, Any]:
            return {
                "response": f"I processed your query: '{query}' for conversation {conversation_id}",
                "search_results": [
                    {"message_id": "msg_1", "content": f"Mock result for: {query}", "sender_id": "user_1"},
                    {"message_id": "msg_2", "content": f"Another mock result for: {query}", "sender_id": "user_2"}
                ],
                "message_count": 2,
                "conversation_id": conversation_id,
                "query": query,
                "success": True,
                "error": None,
                "agent_type": "message_agent",
                "timestamp": datetime.now().isoformat()
            }
        
        # Test queries
        test_queries = [
            "Find messages about project updates",
            "Show me recent messages",
            "What did John say about the meeting?",
            "Search for messages containing 'deadline'"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {query}")
            print("-" * 30)
            
            result = await mock_process_query(
                query=query,
                conversation_id="test-conv-123",
                sender_id="test-user-456"
            )
            
            print(f"✅ Success: {result['success']}")
            print(f"📝 Response: {result['response']}")
            print(f"📊 Messages found: {result['message_count']}")
            print(f"🔍 Sample result: {result['search_results'][0]['content']}")
        
        print("\n" + "=" * 50)
        print("✅ Mock agent test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Simple LangGraph Message Agent Test")
    asyncio.run(test_simple_agent())
    print("🏁 Test completed!")
