# Router Agent Prompts

This directory contains centralized prompt management for the Router Agent Service. All prompts used by the router agent are organized here for easy management, versioning, and optimization.

## 📁 Directory Structure

```
prompts/
├── __init__.py                 # Package initialization
├── router_prompts.py          # Main router prompts and templates
├── prompt_manager.py          # Prompt versioning and A/B testing
└── README.md                  # This file
```

## 🎯 Core Prompt Classes

### RouterPrompts
Main prompt templates for query routing and analysis:

- **ROUTING_PROMPT_TEMPLATE**: Basic routing prompt with agent descriptions
- **ENHANCED_ROUTING_PROMPT_TEMPLATE**: Advanced prompt with examples and better formatting
- **CONFIDENCE_PROMPT_TEMPLATE**: Prompt for evaluating routing confidence
- **ROUTING_EXPLANATIONS**: Human-readable explanations for routing decisions

### ToolAgentPrompts
Specialized prompts for tool agent operations:

- **TOOL_SELECTION_PROMPT**: Help determine which tools are needed
- **MATH_VALIDATION_PROMPT**: Validate mathematical computation requirements

### HistoryAgentPrompts  
Prompts for message history operations:

- **SEARCH_INTENT_PROMPT**: Analyze search intent for conversation history
- **HISTORY_FORMATTING_PROMPT**: Format search results for better UX

### GeneralAgentPrompts
Prompts for general conversation:

- **CONVERSATION_PROMPT**: General conversation guidelines
- **EXPLANATION_PROMPT**: Structure for educational explanations

## 🔄 Prompt Versioning

The `PromptManager` class provides version management capabilities:

### Available Versions
- **V1_BASIC**: Simple, concise prompts
- **V2_ENHANCED**: Detailed prompts with examples and better formatting  
- **V3_EXPERIMENTAL**: Advanced prompts with context-aware analysis

### Usage Example
```python
from prompts.router_prompts import router_prompts
from prompts.prompt_manager import prompt_manager, PromptVersion

# Get basic routing prompt
prompt = router_prompts.get_routing_prompt("Calculate 5+5", enhanced=False)

# Switch to enhanced version
prompt_manager.set_prompt_version(PromptVersion.V2_ENHANCED)
enhanced_prompt = router_prompts.get_routing_prompt("Calculate 5+5", enhanced=True)

# Get confidence analysis
confidence_prompt = router_prompts.get_confidence_prompt("Calculate 5+5", "TOOL_AGENT")
```

## 📊 Performance Tracking

The prompt manager tracks routing performance metrics:

```python
# Record routing results
prompt_manager.record_routing_result(
    query="Calculate 5+5",
    agent="TOOL_AGENT", 
    confidence=0.9,
    success=True
)

# Get performance statistics
stats = prompt_manager.get_routing_statistics()
```

## 🛠️ Customization

### Adding New Prompts
1. Add prompt templates to the appropriate class in `router_prompts.py`
2. Update the class methods to use new templates
3. Test with different query types

### Creating New Versions
1. Add new version to `PromptVersion` enum in `prompt_manager.py`
2. Add corresponding templates to `PROMPT_TEMPLATES` dictionary
3. Test performance compared to existing versions

### A/B Testing
```python
# Test different versions
for version in PromptVersion:
    prompt_manager.set_prompt_version(version)
    # Run your tests here
    # Compare metrics
```

## 🎯 Best Practices

### Prompt Design
- **Be specific**: Clearly define what each agent handles
- **Use examples**: Show concrete examples of queries for each agent
- **Keep consistent**: Use similar formatting across all prompts
- **Test thoroughly**: Validate with edge cases and ambiguous queries

### Version Management
- **Baseline first**: Establish V1 performance before testing new versions
- **Gradual rollout**: Test new versions with subset of traffic
- **Monitor metrics**: Track accuracy, confidence, and user satisfaction
- **Document changes**: Keep clear records of what changed between versions

### Maintenance
- **Regular review**: Periodically review prompt performance
- **User feedback**: Incorporate feedback from routing errors
- **Performance optimization**: Use metrics to identify improvement areas
- **Keep updated**: Update prompts as new agents or capabilities are added

## 📈 Metrics to Monitor

### Routing Accuracy
- Percentage of correctly routed queries
- Confidence scores for routing decisions
- False positive/negative rates per agent

### Performance Metrics
- Response time impact of different prompt lengths
- LLM token usage for different prompt versions
- User satisfaction with routing results

### A/B Testing Metrics
- Conversion rates between versions
- User engagement with routed responses
- Error rates and fallback usage

## 🚀 Getting Started

1. **Import the prompts**:
   ```python
   from prompts.router_prompts import router_prompts
   ```

2. **Use in your router**:
   ```python
   prompt = router_prompts.get_routing_prompt(user_query, enhanced=True)
   ```

3. **Track performance**:
   ```python
   confidence_info = await router_manager.get_routing_confidence(query, agent_type)
   ```

4. **Monitor and optimize**:
   ```python
   stats = prompt_manager.get_routing_statistics()
   ```

## 🔧 Integration with Router Manager

The router manager automatically uses centralized prompts:

```python
# In router_manager.py
from prompts.router_prompts import router_prompts

def _analyze_query_with_llm(self, user_input: str, enhanced: bool = True):
    routing_content = router_prompts.get_routing_prompt(user_input, enhanced=enhanced)
    # ... rest of the method
```

This ensures all routing decisions use the centrally managed prompts with consistent formatting and versioning.

## 📝 Contributing

When adding new prompts or modifying existing ones:

1. Follow the established patterns and naming conventions
2. Add comprehensive docstrings explaining the prompt's purpose
3. Include example usage in the class or method documentation
4. Test with a variety of query types to ensure robustness
5. Update this README if adding new major functionality

## 🎉 Benefits of Centralized Prompts

- ✅ **Single source of truth** for all prompts
- ✅ **Easy A/B testing** with version management
- ✅ **Performance tracking** and optimization
- ✅ **Consistent formatting** across services
- ✅ **Quick updates** without code changes
- ✅ **Better maintainability** and documentation
