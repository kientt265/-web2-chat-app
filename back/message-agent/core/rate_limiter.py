"""
Rate limiting utilities for API calls

Helps manage API quotas and rate limits for external services like Gemini.
"""

import time
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds (default: 60 seconds)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: list = []
        
    def can_make_request(self) -> bool:
        """Check if a request can be made without exceeding rate limits"""
        now = time.time()
        
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.time_window]
        
        # Check if we can make another request
        return len(self.requests) < self.max_requests
    
    def record_request(self) -> None:
        """Record a new request"""
        self.requests.append(time.time())
    
    def time_until_next_request(self) -> float:
        """Get time in seconds until next request can be made"""
        if self.can_make_request():
            return 0.0
        
        # Find the oldest request that needs to expire
        now = time.time()
        oldest_request = min(self.requests)
        return max(0.0, self.time_window - (now - oldest_request))
    
    async def wait_if_needed(self) -> None:
        """Wait if necessary before making a request"""
        wait_time = self.time_until_next_request()
        if wait_time > 0:
            logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds...")
            await asyncio.sleep(wait_time)


class GeminiRateLimiter:
    """Specific rate limiter for Gemini API with different quotas"""
    
    def __init__(self):
        # Conservative limits to avoid hitting Gemini quotas
        self.request_limiter = RateLimiter(max_requests=8, time_window=60)  # 8 requests per minute
        self.daily_limiter = RateLimiter(max_requests=1000, time_window=86400)  # 1000 requests per day
        
    async def can_make_request(self) -> tuple[bool, Optional[str]]:
        """
        Check if we can make a Gemini API request
        
        Returns:
            (can_make_request, reason_if_not)
        """
        if not self.daily_limiter.can_make_request():
            return False, "Daily quota exceeded"
        
        if not self.request_limiter.can_make_request():
            wait_time = self.request_limiter.time_until_next_request()
            return False, f"Rate limit exceeded, wait {wait_time:.1f} seconds"
        
        return True, None
    
    async def wait_and_record_request(self) -> bool:
        """
        Wait if needed and record the request
        
        Returns:
            True if request can proceed, False if daily quota exceeded
        """
        # Check daily quota first
        if not self.daily_limiter.can_make_request():
            logger.warning("Gemini daily quota exceeded")
            return False
        
        # Wait for rate limit if needed
        await self.request_limiter.wait_if_needed()
        
        # Record the request
        self.request_limiter.record_request()
        self.daily_limiter.record_request()
        
        return True
    
    def get_status(self) -> Dict[str, any]:
        """Get current rate limiter status"""
        return {
            "requests_this_minute": len(self.request_limiter.requests),
            "max_requests_per_minute": self.request_limiter.max_requests,
            "requests_today": len(self.daily_limiter.requests),
            "max_requests_per_day": self.daily_limiter.max_requests,
            "can_make_request": self.request_limiter.can_make_request(),
            "wait_time_seconds": self.request_limiter.time_until_next_request()
        }


# Global rate limiter instance
gemini_rate_limiter = GeminiRateLimiter()
