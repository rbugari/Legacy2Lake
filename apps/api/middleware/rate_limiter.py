"""
Sprint 6: Rate Limiting Middleware
Protects API from abuse and brute force attacks
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import time
import hashlib

class RateLimiter:
    """
    Token bucket rate limiter with separate limits for IP and tenant.
    
    Features:
    - IP-based rate limiting (protects against DDoS)
    - Tenant-based rate limiting (fair usage per tenant)
    - Sliding window algorithm
    - Automatic cleanup of old entries
    - Configurable limits per endpoint category
    """
    
    def __init__(self):
        # Storage: {key: [(timestamp1, count1), (timestamp2, count2), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.last_cleanup = time.time()
        
        # Rate limits (requests per minute)
        self.limits = {
            "default": {"requests": 60, "window": 60},      # 60 req/min default
            "auth": {"requests": 5, "window": 60},          # 5 req/min for auth (slow brute force)
            "heavy": {"requests": 10, "window": 60},        # 10 req/min for heavy operations
            "tenant_default": {"requests": 1000, "window": 60},  # 1000 req/min per tenant
        }
    
    def _get_key(self, identifier: str, category: str) -> str:
        """Generate cache key for rate limiting"""
        return f"{category}:{hashlib.md5(identifier.encode()).hexdigest()}"
    
    def _cleanup_old_entries(self):
        """Remove entries older than 5 minutes to prevent memory bloat"""
        now = time.time()
        
        # Cleanup every 60 seconds
        if now - self.last_cleanup < 60:
            return
        
        cutoff = now - 300  # 5 minutes ago
        
        for key in list(self.requests.keys()):
            self.requests[key] = [
                (ts, count) for ts, count in self.requests[key]
                if ts > cutoff
            ]
            
            # Remove empty entries
            if not self.requests[key]:
                del self.requests[key]
        
        self.last_cleanup = now
    
    def check_limit(self, identifier: str, category: str = "default") -> Tuple[bool, Dict]:
        """
        Check if request is within rate limit.
        
        Returns:
            (allowed: bool, info: dict)
            
        info contains:
            - limit: max requests allowed
            - remaining: requests remaining in window
            - reset: seconds until window resets
            - retry_after: seconds to wait if blocked
        """
        self._cleanup_old_entries()
        
        # Get limits for category
        limit_config = self.limits.get(category, self.limits["default"])
        max_requests = limit_config["requests"]
        window_seconds = limit_config["window"]
        
        key = self._get_key(identifier, category)
        now = time.time()
        cutoff = now - window_seconds
        
        # Get recent requests within window
        recent = [(ts, count) for ts, count in self.requests[key] if ts > cutoff]
        total_requests = sum(count for _, count in recent)
        
        # Calculate remaining and reset time
        oldest_in_window = recent[0][0] if recent else now
        reset_seconds = int(window_seconds - (now - oldest_in_window))
        remaining = max(0, max_requests - total_requests)
        
        info = {
            "limit": max_requests,
            "remaining": remaining,
            "reset": reset_seconds,
            "window": window_seconds
        }
        
        # Check if limit exceeded
        if total_requests >= max_requests:
            info["retry_after"] = reset_seconds
            return False, info
        
        # Add new request
        recent.append((now, 1))
        self.requests[key] = recent
        
        return True, info


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    
    Applies different limits based on:
    - Client IP address (prevents DDoS)
    - Tenant ID (fair usage per tenant)
    - Endpoint category (stricter for auth)
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        
        # Determine rate limit category
        category = self._get_category(request.url.path)
        
        # Check IP-based rate limit
        ip_allowed, ip_info = rate_limiter.check_limit(client_ip, category)
        
        if not ip_allowed:
            return self._rate_limit_response(
                "IP rate limit exceeded",
                ip_info,
                client_ip
            )
        
        # Check tenant-based rate limit (if tenant header present)
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            # Only check if it's a valid UUID (skip rate limit for invalid IDs - they'll be rejected by auth)
            import re
            uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
            
            if uuid_pattern.match(tenant_id):
                tenant_allowed, tenant_info = rate_limiter.check_limit(
                    tenant_id, 
                    "tenant_default"
                )
                
                if not tenant_allowed:
                    return self._rate_limit_response(
                        "Tenant rate limit exceeded",
                        tenant_info,
                        tenant_id
                    )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(ip_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(ip_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(ip_info["reset"])
        
        return response
    
    def _get_category(self, path: str) -> str:
        """Determine rate limit category based on endpoint path"""
        if "/auth/" in path or "/login" in path or "/token" in path:
            return "auth"
        elif "/transpile" in path or "/orchestrate" in path:
            return "heavy"
        else:
            return "default"
    
    def _rate_limit_response(self, message: str, info: Dict, identifier: str):
        """Generate 429 Too Many Requests response"""
        from fastapi.responses import JSONResponse
        
        print(f"[RATE LIMIT] {message} - Identifier: {identifier[:30]}...")
        
        return JSONResponse(
            status_code=429,
            headers={
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(info["reset"]),
                "Retry-After": str(info.get("retry_after", info["reset"]))
            },
            content={
                "detail": message,
                "limit": info["limit"],
                "window_seconds": info["window"],
                "retry_after_seconds": info.get("retry_after", info["reset"])
            }
        )


def get_rate_limiter() -> RateLimiter:
    """Dependency injection for rate limiter"""
    return rate_limiter
