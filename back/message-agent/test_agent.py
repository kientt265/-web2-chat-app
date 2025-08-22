"""
Test script for the LangGraph Message Agent
"""

import asyncio
import os
from agents.message_agent import message_agent
from managers.agent_manager import agent_manager


async def test_message_agent():
    """Test the LangGraph message agent"""
    print("🧪 Testing LangGraph Message Agent")
    print("=" * 50)
    
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
        
        try:
            result = await agent_manager.process_message_query(
                query=query,
                conversation_id="test-conv-123",
                sender_id="test-user-456"
            )
            
            print(f"✅ Success: {result['success']}")
            print(f"📝 Response: {result['response']}")
            print(f"📊 Messages found: {result['message_count']}")
            
            if result.get('error'):
                print(f"⚠️  Error: {result['error']}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🔧 Agent Status:")
    status = agent_manager.get_agent_status()
    for key, value in status.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    # Set environment variables for testing (optional)
    # os.environ["OPENAI_API_KEY"] = "your-api-key-here"
    
    print("🚀 Starting LangGraph Message Agent Test")
    asyncio.run(test_message_agent())
    print("🏁 Test completed!")
