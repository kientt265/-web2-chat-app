#!/usr/bin/env python3
"""
Test script for the Gemini-powered Message Agent

This script demonstrates how to use the MessageAgent with Google's Gemini AI model.
"""

import asyncio
import os
from agents.message_agent import MessageAgent


async def test_gemini_agent():
    """Test the Message Agent with Gemini"""
    
    print("🧪 Testing Message Agent with Gemini")
    print("=" * 50)
    
    # Initialize agent (will use fallback mode without API key)
    agent = MessageAgent()
    
    # Test queries
    test_queries = [
        "Find messages about project updates",
        "Show me recent messages",
        "What did John say about the meeting?",
        "Search for messages containing 'deadline'",
        "Tell me about the latest discussions"
    ]
    
    print(f"\n🚀 Running {len(test_queries)} test queries...")
    print("-" * 50)
    
    success_count = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        
        try:
            result = await agent.process_query(
                query=query,
                conversation_id="test-conversation",
                sender_id="test-user"
            )
            
            if result["success"]:
                print(f"✅ Success: {result['message_count']} messages found")
                print(f"🤖 Response: {result['response'][:100]}...")
                success_count += 1
            else:
                print(f"❌ Failed: {result['error']}")
                
        except Exception as e:
            print(f"💥 Exception: {e}")
    
    print(f"\n📊 Test Results: {success_count}/{len(test_queries)} queries successful")
    
    # Show Gemini setup instructions
    print("\n" + "=" * 50)
    print("🔧 To use Gemini AI instead of fallback responses:")
    print("1. Get a Gemini API key from https://makersuite.google.com/app/apikey")
    print("2. Set the environment variable: export GOOGLE_API_KEY='your-api-key'")
    print("3. Or pass it directly: MessageAgent(gemini_api_key='your-api-key')")
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  No GOOGLE_API_KEY found - using fallback responses")
    else:
        print("✅ GOOGLE_API_KEY detected - using Gemini AI")


if __name__ == "__main__":
    asyncio.run(test_gemini_agent())
