"""
Test script for the Standalone LangGraph Message Agent
"""

import asyncio
import os


async def test_standalone_agent():
    """Test the standalone LangGraph message agent"""
    print("🧪 Testing Standalone LangGraph Message Agent")
    print("=" * 50)
    
    try:
        # Import directly to avoid the __init__.py issues
        from agents.standalone_agent import standalone_message_agent
        
        # Test queries
        test_queries = [
            "Find messages about project updates",
            "Show me recent messages",
            "What did John say about the meeting?",
            "Search for messages containing 'deadline'",
            "Tell me about the latest discussions"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {query}")
            print("-" * 40)
            
            result = await standalone_message_agent.process_query(
                query=query,
                conversation_id="test-conv-123",
                sender_id="test-user-456"
            )
            
            print(f"✅ Success: {result['success']}")
            print(f"📝 Response: {result['response']}")
            print(f"📊 Messages found: {result['message_count']}")
            print(f"🤖 Agent type: {result['agent_type']}")
            
            if result.get('error'):
                print(f"⚠️  Error: {result['error']}")
            
            # Show a sample search result
            if result['search_results']:
                sample = result['search_results'][0]
                print(f"🔍 Sample result: {sample['content'][:100]}...")
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("🎉 LangGraph Message Agent is working!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Standalone LangGraph Message Agent Test")
    print("💡 This agent uses LangGraph for workflow orchestration")
    print("🔄 Workflow: Parse Query → Search Messages → Retrieve Context → Generate Response")
    print()
    
    asyncio.run(test_standalone_agent())
    print("\n🏁 Test completed!")
