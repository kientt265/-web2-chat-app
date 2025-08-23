# Message Agent with Google Gemini AI

This document explains how the Message Agent has been updated to use Google's Gemini AI model instead of OpenAI's GPT models.

## 🚀 What Changed

### Dependencies Updated
- ✅ Replaced `langchain-openai` with `langchain-google-genai`
- ✅ Added `google-generativeai` package
- ✅ Updated `requirements.txt`

### Code Changes
- ✅ Replaced `ChatOpenAI` with `ChatGoogleGenerativeAI`
- ✅ Updated initialization to use `GOOGLE_API_KEY` instead of `OPENAI_API_KEY`
- ✅ Modified prompt template for Gemini compatibility
- ✅ Added `convert_system_message_to_human=True` for Gemini's requirements

## 🔧 Setup Instructions

### 1. Get a Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### 2. Set Environment Variable
```bash
# Option 1: Set for current session
export GOOGLE_API_KEY="your-gemini-api-key-here"

# Option 2: Add to your shell profile (~/.bashrc, ~/.zshrc)
echo 'export GOOGLE_API_KEY="your-gemini-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### 3. Or Pass API Key Directly
```python
from agents.message_agent import MessageAgent

# Initialize with API key
agent = MessageAgent(gemini_api_key="your-gemini-api-key-here")
```

## 🧪 Testing

### Run the Test Script
```bash
cd /path/to/message-agent
python test_gemini_agent.py
```

### Expected Output
- ✅ Without API key: Uses fallback responses
- ✅ With API key: Uses Gemini AI for intelligent responses

## 💡 Model Configuration

### Current Settings
```python
self.llm = ChatGoogleGenerativeAI(
    google_api_key=self.gemini_api_key,
    model="gemini-1.5-flash",  # Fast and efficient model
    temperature=0.1,           # Low temperature for consistent responses
    convert_system_message_to_human=True  # Required for Gemini
)
```

### Available Models
- `gemini-1.5-pro`: Most capable model (higher cost)
- `gemini-1.5-flash`: Fast and efficient (recommended)
- `gemini-1.0-pro`: Original model (legacy)

## 🔄 Fallback Behavior

The agent gracefully handles missing API keys:
1. **With API Key**: Uses Gemini AI for intelligent, context-aware responses
2. **Without API Key**: Uses predefined fallback responses
3. **Service Error**: Automatically falls back to mock data and simple responses

## 📊 Comparison: OpenAI vs Gemini

| Feature | OpenAI GPT-4 | Google Gemini |
|---------|--------------|---------------|
| **Speed** | Good | Excellent (Flash) |
| **Cost** | Higher | Lower |
| **Context** | 128k tokens | 1M tokens |
| **Languages** | Excellent | Excellent |
| **API Key** | OPENAI_API_KEY | GOOGLE_API_KEY |
| **Setup** | Pay-per-use | Free tier available |

## 🚨 Important Notes

### Prompt Template Changes
- **Before**: Separate system and human messages
- **After**: Combined into single human message (Gemini requirement)

### API Key Environment Variable
- **Before**: `OPENAI_API_KEY`
- **After**: `GOOGLE_API_KEY`

### Error Handling
The agent maintains the same error handling and fallback behavior, ensuring reliability regardless of API availability.

## 🎯 Usage Examples

### Basic Usage
```python
import asyncio
from agents.message_agent import MessageAgent

async def main():
    # Initialize agent
    agent = MessageAgent()
    
    # Process query
    result = await agent.process_query(
        query="Find messages about project updates",
        conversation_id="conv-123",
        sender_id="user-456"
    )
    
    print(f"Response: {result['response']}")
    print(f"Found {result['message_count']} messages")

# Run
asyncio.run(main())
```

### With API Key
```python
# Set environment variable first
import os
os.environ['GOOGLE_API_KEY'] = 'your-api-key'

# Or pass directly
agent = MessageAgent(gemini_api_key='your-api-key')
```

## 🔍 Troubleshooting

### Common Issues

1. **"No Gemini API key provided"**
   - Set `GOOGLE_API_KEY` environment variable
   - Or pass `gemini_api_key` parameter

2. **Import errors**
   - Run: `pip install langchain-google-genai google-generativeai`

3. **Slow responses**
   - Switch to `gemini-1.5-flash` model for faster responses

4. **API quota exceeded**
   - Check your Google AI Studio quotas and billing

### Debugging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.INFO)

# Test API connection
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(google_api_key="your-key")
response = llm.invoke("Hello!")
print(response.content)
```

## 🎉 Benefits of Gemini Integration

1. **Cost Effective**: Lower API costs compared to GPT-4
2. **Large Context**: 1M token context window
3. **Speed**: Gemini Flash is very fast
4. **Free Tier**: Generous free usage limits
5. **Google Integration**: Works well with Google services

The Message Agent now provides the same intelligent conversation analysis capabilities using Google's Gemini AI, with improved performance and cost efficiency!
