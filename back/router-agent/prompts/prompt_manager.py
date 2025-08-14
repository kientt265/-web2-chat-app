"""
Prompt configuration and management for Router Agent Service.

This module provides utilities for managing prompts, including
versioning, A/B testing, and dynamic prompt updates.
"""

from typing import Dict
from enum import Enum
import json
import os


class PromptVersion(Enum):
    """Available prompt versions for A/B testing."""

    V1_BASIC = "v1_basic"
    V2_ENHANCED = "v2_enhanced"
    V3_EXPERIMENTAL = "v3_experimental"


class PromptManager:
    """Manages prompt versions and configurations."""

    def __init__(self):
        self.current_version = PromptVersion.V2_ENHANCED
        self.prompt_metrics = {}

    def get_active_prompt_version(self) -> PromptVersion:
        """Get the currently active prompt version."""
        return self.current_version

    def set_prompt_version(self, version: PromptVersion):
        """Set the active prompt version."""
        self.current_version = version
        print(f"✅ Switched to prompt version: {version.value}")

    def should_use_enhanced_prompts(self) -> bool:
        """Determine if enhanced prompts should be used."""
        return self.current_version in [
            PromptVersion.V2_ENHANCED,
            PromptVersion.V3_EXPERIMENTAL,
        ]

    def record_routing_result(
        self, query: str, agent: str, confidence: float, success: bool
    ):
        """Record routing results for prompt optimization."""
        key = f"{self.current_version.value}_{agent}"
        if key not in self.prompt_metrics:
            self.prompt_metrics[key] = {
                "total_routes": 0,
                "successful_routes": 0,
                "avg_confidence": 0.0,
                "confidence_sum": 0.0,
            }

        metrics = self.prompt_metrics[key]
        metrics["total_routes"] += 1
        metrics["confidence_sum"] += confidence
        metrics["avg_confidence"] = metrics["confidence_sum"] / metrics["total_routes"]

        if success:
            metrics["successful_routes"] += 1

    def get_routing_statistics(self) -> Dict:
        """Get routing performance statistics."""
        stats = {}
        for key, metrics in self.prompt_metrics.items():
            version, agent = key.split("_", 1)
            if version not in stats:
                stats[version] = {}

            success_rate = (
                metrics["successful_routes"] / metrics["total_routes"]
            ) * 100
            stats[version][agent] = {
                "success_rate": round(success_rate, 2),
                "avg_confidence": round(metrics["avg_confidence"], 3),
                "total_routes": metrics["total_routes"],
            }

        return stats


# Prompt templates for different versions
PROMPT_TEMPLATES = {
    PromptVersion.V1_BASIC: {
        "routing": """
Analyze this query and choose the best agent:

Query: {query}

Agents:
- TOOL_AGENT: Mathematical calculations, web scraping, external tools
- MESSAGE_HISTORY_AGENT: Conversation history, message search
- GENERAL_AGENT: General conversation, information

Response: TOOL_AGENT, MESSAGE_HISTORY_AGENT, or GENERAL_AGENT
""",
        "system": "You are a query router.",
    },
    PromptVersion.V2_ENHANCED: {
        "routing": """
You are an intelligent query router. Analyze the user query and determine which specialized agent should handle it.

🔧 TOOL_AGENT - For queries requiring external tools or computations:
   - Mathematical calculations, equations, formulas
   - Web scraping, data extraction, API calls
   - File processing, data transformations
   
📚 MESSAGE_HISTORY_AGENT - For conversation history and message search:
   - Previous message retrieval
   - Conversation search and analysis
   - Historical context requests
   
💬 GENERAL_AGENT - For general conversation and information:
   - Knowledge queries, explanations
   - Casual conversation, general help
   - Default for unclear queries

Query: "{query}"

Respond with ONLY: TOOL_AGENT, MESSAGE_HISTORY_AGENT, or GENERAL_AGENT
""",
        "system": "You are a smart query router that analyzes user intent and selects the most appropriate specialized agent.",
    },
    PromptVersion.V3_EXPERIMENTAL: {
        "routing": """
Advanced Query Router - Context-Aware Analysis

MISSION: Route queries to optimal agents based on deep intent analysis.

AGENT CAPABILITIES:
🔧 TOOL_AGENT → External operations requiring computation or data processing
📚 MESSAGE_HISTORY_AGENT → Conversational memory and historical analysis  
💬 GENERAL_AGENT → Knowledge sharing and natural conversation

ANALYSIS FRAMEWORK:
1. Intent Classification: [computational | retrieval | conversational]
2. Context Requirements: [tools | history | knowledge]
3. Output Expectations: [data | information | interaction]

QUERY: "{query}"

ROUTING DECISION: [Single agent type only]
""",
        "system": "You are an advanced AI router with deep understanding of query intent and agent capabilities.",
    },
}


def get_prompt_template(version: PromptVersion, template_type: str = "routing") -> str:
    """Get a prompt template for a specific version."""
    return PROMPT_TEMPLATES.get(version, {}).get(template_type, "")


def load_custom_prompts(file_path: str) -> Dict:
    """Load custom prompts from a JSON file."""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Failed to load custom prompts: {e}")
    return {}


def save_prompt_metrics(metrics: Dict, file_path: str):
    """Save prompt performance metrics to file."""
    try:
        with open(file_path, "w") as f:
            json.dump(metrics, f, indent=2)
    except Exception as e:
        print(f"Failed to save prompt metrics: {e}")


# Global prompt manager instance
prompt_manager = PromptManager()
