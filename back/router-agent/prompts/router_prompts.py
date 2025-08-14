"""
Centralized prompts for Router Agent Service.

This module contains all prompts used by the router agent for query analysis
and routing decisions. Centralizing prompts makes them easier to manage,
update, and maintain consistency across the application.
"""


class RouterPrompts:
    """Centralized prompts for router agent operations."""

    # System prompt for the router LLM
    SYSTEM_PROMPT = "You are a smart query router that analyzes user queries and determines the best specialized agent to handle them."

    # Main routing prompt template
    ROUTING_PROMPT_TEMPLATE = """
You are a smart router that analyzes user queries and determines which specialized agent should handle them.

Available agents:
1. TOOL_AGENT - Handles queries requiring external tools like:
   - Mathematical calculations (e.g., "calculate 15*8+24", "solve x²+5x-6=0")
   - Web scraping (e.g., "scrape data from website", "get content from URL")
   - Data processing and transformations
   - External API calls
   - Computational tasks
   - File operations and conversions

2. MESSAGE_HISTORY_AGENT - Handles queries about conversation history like:
   - "Show me previous messages"
   - "Find messages about machine learning"
   - "What did we discuss yesterday?"
   - "Search my conversation history for 'project'"
   - Message retrieval and search
   - Conversation analysis
   - Historical context requests

3. GENERAL_AGENT - Handles general conversation and queries that don't require tools or history search:
   - General questions and answers
   - Casual conversation
   - Information requests
   - Explanations and discussions
   - Knowledge-based queries
   - Default fallback for unclear queries

Instructions:
- Analyze the user query carefully
- Consider the intent and context
- Choose the most appropriate agent
- Respond with ONLY the agent type: TOOL_AGENT, MESSAGE_HISTORY_AGENT, or GENERAL_AGENT

User query: {query}
"""

    # Enhanced routing prompt with examples
    ENHANCED_ROUTING_PROMPT_TEMPLATE = """
You are an intelligent query router. Analyze the user query and determine which specialized agent should handle it.

AGENT TYPES AND CAPABILITIES:

🔧 TOOL_AGENT - For queries requiring external tools or computations:
   Mathematical Operations:
   - "Calculate 15*8+24" → TOOL_AGENT
   - "What is √144?" → TOOL_AGENT
   - "Solve x²+5x-6=0" → TOOL_AGENT
   
   Web/Data Operations:
   - "Scrape data from website" → TOOL_AGENT
   - "Fetch content from URL" → TOOL_AGENT
   - "Convert CSV to JSON" → TOOL_AGENT
   
   External Services:
   - "Use calculator tool" → TOOL_AGENT
   - "Process this data" → TOOL_AGENT

📚 MESSAGE_HISTORY_AGENT - For conversation history and message search:
   History Retrieval:
   - "Show me previous messages" → MESSAGE_HISTORY_AGENT
   - "What did we discuss yesterday?" → MESSAGE_HISTORY_AGENT
   - "Find our conversation about AI" → MESSAGE_HISTORY_AGENT
   
   Message Search:
   - "Search messages for 'project'" → MESSAGE_HISTORY_AGENT
   - "Find messages containing 'docker'" → MESSAGE_HISTORY_AGENT
   - "Show conversation history" → MESSAGE_HISTORY_AGENT

💬 GENERAL_AGENT - For general conversation and information:
   Knowledge Queries:
   - "What is machine learning?" → GENERAL_AGENT
   - "Explain microservices" → GENERAL_AGENT
   - "How does Docker work?" → GENERAL_AGENT
   
   Conversation:
   - "Hello, how are you?" → GENERAL_AGENT
   - "Tell me a joke" → GENERAL_AGENT
   - "Can you help me understand..." → GENERAL_AGENT

ROUTING DECISION:
Analyze this query: "{query}"

Respond with ONLY one of: TOOL_AGENT, MESSAGE_HISTORY_AGENT, or GENERAL_AGENT
"""

    # Confidence scoring prompt
    CONFIDENCE_PROMPT_TEMPLATE = """
Analyze this routing decision and provide a confidence score.

Query: "{query}"
Recommended Agent: {agent_type}

Rate your confidence in this routing decision from 0.0 to 1.0:
- 1.0 = Very confident, clear match
- 0.8 = Confident, good match
- 0.6 = Moderately confident
- 0.4 = Uncertain, could go either way
- 0.2 = Low confidence
- 0.0 = No confidence

Provide reasoning for your confidence score.

Format your response as:
CONFIDENCE: [0.0-1.0]
REASONING: [Brief explanation]
"""

    # Fallback routing explanations
    ROUTING_EXPLANATIONS = {
        "TOOL_AGENT": "Query requires computational tools, mathematical calculations, or external services",
        "MESSAGE_HISTORY_AGENT": "Query involves searching, retrieving, or analyzing conversation history",
        "GENERAL_AGENT": "Query is conversational, informational, or doesn't require specialized tools",
    }

    @classmethod
    def get_routing_prompt(cls, query: str, enhanced: bool = False) -> str:
        """
        Get the routing prompt with the user query inserted.

        Args:
            query: The user's query to be analyzed
            enhanced: Whether to use the enhanced prompt with examples

        Returns:
            Formatted prompt string
        """
        if enhanced:
            return cls.ENHANCED_ROUTING_PROMPT_TEMPLATE.format(query=query)
        return cls.ROUTING_PROMPT_TEMPLATE.format(query=query)

    @classmethod
    def get_confidence_prompt(cls, query: str, agent_type: str) -> str:
        """
        Get the confidence scoring prompt.

        Args:
            query: The user's query
            agent_type: The recommended agent type

        Returns:
            Formatted confidence prompt
        """
        return cls.CONFIDENCE_PROMPT_TEMPLATE.format(query=query, agent_type=agent_type)

    @classmethod
    def get_routing_explanation(cls, agent_type: str) -> str:
        """
        Get explanation for why a specific agent was chosen.

        Args:
            agent_type: The selected agent type

        Returns:
            Explanation string
        """
        return cls.ROUTING_EXPLANATIONS.get(
            agent_type, "Agent selected based on query analysis"
        )


class ToolAgentPrompts:
    """Prompts specific to tool agent interactions."""

    TOOL_SELECTION_PROMPT = """
Based on the user query, determine which tools might be needed:

Available tool categories:
- Calculator: Mathematical operations and computations
- Web Scraper: Extracting data from websites
- File Processor: File operations and conversions
- API Client: External API interactions

Query: "{query}"

Suggest the most appropriate tools and explain why.
"""

    MATH_VALIDATION_PROMPT = """
Validate if this query requires mathematical computation:

Query: "{query}"

Respond with:
- MATH: true/false
- CONFIDENCE: 0.0-1.0
- OPERATIONS: [list of operations needed]
"""


class HistoryAgentPrompts:
    """Prompts specific to message history agent interactions."""

    SEARCH_INTENT_PROMPT = """
Analyze the search intent for conversation history:

Query: "{query}"

Determine:
- SEARCH_TYPE: [keyword, semantic, temporal, user-specific]
- KEYWORDS: [relevant search terms]
- TIME_FILTER: [recent, yesterday, last_week, all_time]
- CONFIDENCE: 0.0-1.0
"""

    HISTORY_FORMATTING_PROMPT = """
Format the search results for better user experience:

Found {count} messages.
Format them in a clear, readable way with:
- Message content preview
- Sender information
- Timestamp
- Relevance indicators
"""


class GeneralAgentPrompts:
    """Prompts specific to general agent interactions."""

    CONVERSATION_PROMPT = """
You are a helpful AI assistant engaged in natural conversation.

Guidelines:
- Be friendly and helpful
- Provide accurate information
- Ask clarifying questions when needed
- Keep responses concise but informative

User: {query}
"""

    EXPLANATION_PROMPT = """
Provide a clear, educational explanation for this topic:

Topic: {topic}

Structure your response with:
- Brief overview
- Key concepts
- Practical examples
- Additional resources if relevant
"""


# Global prompt instance for easy access
router_prompts = RouterPrompts()
tool_prompts = ToolAgentPrompts()
history_prompts = HistoryAgentPrompts()
general_prompts = GeneralAgentPrompts()
