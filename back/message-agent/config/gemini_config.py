"""
Configuration for Gemini API rate limiting

Adjust these values based on your API quota and usage patterns.
"""

# Gemini API Rate Limits (conservative values to avoid hitting quotas)
GEMINI_RATE_LIMITS = {
    # Requests per minute - keep this lower than your actual quota
    "requests_per_minute": 8,  # Gemini free tier allows 15/min, so we use 8 for safety
    # Daily request limit
    "requests_per_day": 1000,  # Adjust based on your quota
    # Token limits (if applicable)
    "tokens_per_minute": 100000,
    # Retry configuration
    "max_retries": 3,
    "base_delay": 2.0,  # seconds
    "max_delay": 60.0,  # seconds
    # Timeout settings
    "request_timeout": 30.0,  # seconds
}

# Fallback behavior configuration
FALLBACK_CONFIG = {
    "use_fallback_on_rate_limit": True,
    "use_fallback_on_error": True,
    "log_api_usage": True,
}

# Model configuration
GEMINI_MODEL_CONFIG = {
    "model": "gemini-1.5-flash",  # Fastest model
    "temperature": 0.1,
    "max_output_tokens": 1000,  # Limit response length
}


def get_rate_limit_config():
    """Get the current rate limiting configuration"""
    return GEMINI_RATE_LIMITS.copy()


def get_fallback_config():
    """Get the fallback behavior configuration"""
    return FALLBACK_CONFIG.copy()


def get_model_config():
    """Get the Gemini model configuration"""
    return GEMINI_MODEL_CONFIG.copy()
