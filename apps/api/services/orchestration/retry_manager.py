"""
Retry Manager - Sprint 2 Enhancement
Intelligent retry logic with exponential backoff and error categorization
"""
import asyncio
import random
from typing import Dict, Any, Optional, Callable, Tuple
from enum import Enum
from datetime import datetime

try:
    from apps.api.utils.logger import logger
except ImportError:
    from utils.logger import logger


class ErrorCategory(str, Enum):
    """Error categorization for intelligent retry strategies"""
    RATE_LIMIT = "RATE_LIMIT"          # 429, retry with backoff
    TIMEOUT = "TIMEOUT"                 # Connection timeout, retry immediately
    SERVER_ERROR = "SERVER_ERROR"       # 500-599, retry with backoff
    VALIDATION_ERROR = "VALIDATION_ERROR"  # 400-499 (non-429), don't retry
    NETWORK_ERROR = "NETWORK_ERROR"     # Connection issues, retry with backoff
    CONTENT_ERROR = "CONTENT_ERROR"     # LLM returned invalid content, retry
    UNKNOWN = "UNKNOWN"                 # Unknown error, retry with caution


class RetryStrategy:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.base_delay * (self.exponential_base ** attempt)
        
        # Cap at max_delay
        delay = min(delay, self.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay


class RetryManager:
    """
    Manages retry logic for agent executions with intelligent backoff.
    Categorizes errors and applies appropriate retry strategies.
    """
    
    # Default strategies per error category
    DEFAULT_STRATEGIES = {
        ErrorCategory.RATE_LIMIT: RetryStrategy(max_attempts=5, base_delay=2.0, max_delay=120.0),
        ErrorCategory.TIMEOUT: RetryStrategy(max_attempts=3, base_delay=0.5, max_delay=10.0),
        ErrorCategory.SERVER_ERROR: RetryStrategy(max_attempts=3, base_delay=1.0, max_delay=30.0),
        ErrorCategory.NETWORK_ERROR: RetryStrategy(max_attempts=4, base_delay=1.0, max_delay=60.0),
        ErrorCategory.CONTENT_ERROR: RetryStrategy(max_attempts=2, base_delay=0.5, max_delay=5.0),
        ErrorCategory.UNKNOWN: RetryStrategy(max_attempts=2, base_delay=1.0, max_delay=10.0),
        ErrorCategory.VALIDATION_ERROR: RetryStrategy(max_attempts=1, base_delay=0, max_delay=0)  # Don't retry
    }
    
    def __init__(self):
        self.retry_stats: Dict[str, Dict[str, int]] = {}
        self.total_retries = 0
        self.successful_retries = 0
    
    def categorize_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorCategory:
        """Categorize error for appropriate retry strategy"""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Check for rate limiting
        if "429" in error_str or "rate limit" in error_str or "quota" in error_str:
            return ErrorCategory.RATE_LIMIT
        
        # Check for timeouts
        if "timeout" in error_str or "timed out" in error_str or error_type in ["TimeoutError", "asyncio.TimeoutError"]:
            return ErrorCategory.TIMEOUT
        
        # Check for server errors
        if any(code in error_str for code in ["500", "502", "503", "504"]) or "server error" in error_str:
            return ErrorCategory.SERVER_ERROR
        
        # Check for network errors
        if "connection" in error_str or "network" in error_str or error_type in ["ConnectionError", "NetworkError"]:
            return ErrorCategory.NETWORK_ERROR
        
        # Check for validation errors (don't retry)
        if any(code in error_str for code in ["400", "401", "403", "404"]) or "invalid" in error_str:
            return ErrorCategory.VALIDATION_ERROR
        
        # Check for content errors (LLM returned bad content)
        if "json" in error_str or "parse" in error_str or "schema" in error_str:
            return ErrorCategory.CONTENT_ERROR
        
        return ErrorCategory.UNKNOWN
    
    def should_retry(self, category: ErrorCategory, attempt: int) -> bool:
        """Determine if retry should be attempted"""
        strategy = self.DEFAULT_STRATEGIES.get(category)
        if not strategy:
            return False
        
        return attempt < strategy.max_attempts
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        context_name: str = "operation",
        **kwargs
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute function with retry logic.
        
        Returns:
            (success: bool, result: Any, error: Optional[str])
        """
        attempt = 0
        last_error = None
        error_category = None
        
        while True:
            try:
                # Execute function
                logger.debug(f"Executing {context_name} (attempt {attempt + 1})", "RetryManager")
                result = await func(*args, **kwargs)
                
                # Success
                if attempt > 0:
                    self.successful_retries += 1
                    logger.info(
                        f"✅ {context_name} succeeded after {attempt + 1} attempts",
                        "RetryManager"
                    )
                
                self._record_attempt(context_name, error_category, attempt, success=True)
                return (True, result, None)
            
            except Exception as e:
                last_error = e
                error_category = self.categorize_error(e)
                attempt += 1
                self.total_retries += 1
                
                logger.warning(
                    f"❌ {context_name} failed (attempt {attempt}): {error_category.value} - {str(e)}",
                    "RetryManager"
                )
                
                # Check if should retry
                if not self.should_retry(error_category, attempt):
                    logger.error(
                        f"🛑 {context_name} failed permanently after {attempt} attempts",
                        "RetryManager"
                    )
                    self._record_attempt(context_name, error_category, attempt, success=False)
                    return (False, None, str(e))
                
                # Calculate and wait for backoff delay
                strategy = self.DEFAULT_STRATEGIES[error_category]
                delay = strategy.calculate_delay(attempt - 1)
                
                logger.info(
                    f"⏳ Retrying {context_name} in {delay:.2f}s... (category: {error_category.value})",
                    "RetryManager"
                )
                await asyncio.sleep(delay)
    
    def _record_attempt(
        self,
        context_name: str,
        category: Optional[ErrorCategory],
        attempts: int,
        success: bool
    ):
        """Record retry attempt statistics"""
        if context_name not in self.retry_stats:
            self.retry_stats[context_name] = {
                "total_attempts": 0,
                "total_retries": 0,
                "successes": 0,
                "failures": 0,
                "by_category": {}
            }
        
        stats = self.retry_stats[context_name]
        stats["total_attempts"] += attempts + 1
        stats["total_retries"] += attempts
        
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1
        
        if category:
            cat_key = category.value
            if cat_key not in stats["by_category"]:
                stats["by_category"][cat_key] = 0
            stats["by_category"][cat_key] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry statistics"""
        return {
            "total_retries": self.total_retries,
            "successful_retries": self.successful_retries,
            "retry_success_rate": (
                self.successful_retries / self.total_retries
                if self.total_retries > 0
                else 0
            ),
            "operation_stats": self.retry_stats
        }
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        stats = self.get_stats()
        return (
            f"Retry Stats: {stats['total_retries']} retries, "
            f"{stats['successful_retries']} succeeded "
            f"({stats['retry_success_rate']:.1%} success rate)"
        )


# Singleton instance for global access
retry_manager = RetryManager()


# Convenience decorator for retry logic
def with_retry(context_name: str = "operation"):
    """
    Decorator to add retry logic to async functions.
    
    Usage:
        @with_retry(context_name="Agent C Generation")
        async def generate_code(...):
            # Your code here
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            success, result, error = await retry_manager.execute_with_retry(
                func, *args, context_name=context_name, **kwargs
            )
            if not success:
                raise Exception(f"Operation failed after retries: {error}")
            return result
        return wrapper
    return decorator
