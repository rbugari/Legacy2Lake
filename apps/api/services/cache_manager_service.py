"""
Sprint 12: Performance Optimization - Cache Manager Service

This service provides distributed caching with Redis backend for fast response times.
Supports multiple cache strategies, TTL management, and automatic invalidation.

Key Features:
- Redis backend for distributed caching
- Multiple cache strategies (query results, schema metadata, quality reports)
- TTL (Time-To-Live) management
- Pattern-based invalidation
- Compression for large values
- Cache statistics tracking

Author: UTM Platform Team
Version: 3.14 (Sprint 12)
"""

import json
import hashlib
import pickle
import zlib
from typing import Any, Optional, Callable, Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Redis async client
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("redis package not installed, using in-memory fallback")

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache statistics"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float  # Percentage
    miss_rate: float  # Percentage
    evictions: int
    memory_usage_bytes: int
    key_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CacheEntry:
    """Single cache entry metadata"""
    key: str
    size_bytes: int
    ttl_seconds: Optional[int]
    created_at: datetime
    expires_at: Optional[datetime]
    hit_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['expires_at'] = self.expires_at.isoformat() if self.expires_at else None
        return result


class CacheManager:
    """
    Distributed caching with Redis backend.
    
    Provides high-performance caching for:
    - Query results
    - Schema metadata
    - Quality reports
    - Metrics calculations
    - Anomaly detection results
    
    Features:
    - Automatic compression for large values (>1KB)
    - TTL-based expiration
    - Pattern-based invalidation
    - Cache statistics
    - Fallback to in-memory cache if Redis unavailable
    
    Example:
        cache = CacheManager(redis_url="redis://localhost:6379")
        
        # Simple get/set
        await cache.set("my_key", {"data": "value"}, ttl=3600)
        value = await cache.get("my_key")
        
        # Get or compute
        value = await cache.get_or_set(
            key="expensive_computation",
            getter=lambda: compute_expensive_value(),
            ttl=1800
        )
        
        # Invalidate pattern
        await cache.invalidate("table:customer_orders:*")
        
        # Get stats
        stats = await cache.get_stats()
        print(f"Hit rate: {stats.hit_rate}%")
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600,
        compression_threshold: int = 1024,
        key_prefix: str = "utm:"
    ):
        """
        Initialize cache manager.
        
        Args:
            redis_url: Redis connection string
            default_ttl: Default TTL in seconds (1 hour)
            compression_threshold: Compress values larger than this (bytes)
            key_prefix: Prefix for all cache keys
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.compression_threshold = compression_threshold
        self.key_prefix = key_prefix
        
        # Redis client (will be initialized async)
        self.redis: Optional[aioredis.Redis] = None
        self.connected = False
        
        # Fallback in-memory cache
        self.memory_cache: Dict[str, Any] = {}
        self.use_fallback = not REDIS_AVAILABLE
        
        # Statistics
        self.stats_hits = 0
        self.stats_misses = 0
        self.stats_evictions = 0
        
        logger.info(
            f"CacheManager initialized: redis_url={redis_url}, "
            f"default_ttl={default_ttl}s, compression_threshold={compression_threshold}B"
        )
    
    async def connect(self):
        """Connect to Redis server."""
        if self.use_fallback:
            logger.warning("Using in-memory fallback cache (Redis not available)")
            return
        
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False  # We handle encoding ourselves
            )
            # Test connection
            await self.redis.ping()
            self.connected = True
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Falling back to in-memory cache")
            self.use_fallback = True
            self.redis = None
    
    async def disconnect(self):
        """Disconnect from Redis server."""
        if self.redis:
            await self.redis.close()
            self.connected = False
            logger.info("Disconnected from Redis")
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.key_prefix}{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """
        Serialize value to bytes with optional compression.
        
        Args:
            value: Value to serialize
        
        Returns:
            Serialized bytes (possibly compressed)
        """
        # Serialize with pickle
        serialized = pickle.dumps(value)
        
        # Compress if larger than threshold
        if len(serialized) > self.compression_threshold:
            compressed = zlib.compress(serialized)
            # Only use if compression actually reduces size
            if len(compressed) < len(serialized):
                # Prefix with marker to indicate compression
                return b"Z" + compressed
        
        # No compression
        return b"U" + serialized
    
    def _deserialize(self, data: bytes) -> Any:
        """
        Deserialize bytes to value with optional decompression.
        
        Args:
            data: Serialized bytes
        
        Returns:
            Deserialized value
        """
        if not data:
            return None
        
        # Check compression marker
        marker = data[0:1]
        payload = data[1:]
        
        if marker == b"Z":
            # Compressed
            decompressed = zlib.decompress(payload)
            return pickle.loads(decompressed)
        elif marker == b"U":
            # Uncompressed
            return pickle.loads(payload)
        else:
            # Legacy format (no marker)
            return pickle.loads(data)
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if miss
        """
        full_key = self._make_key(key)
        
        try:
            if self.use_fallback:
                # In-memory cache
                if full_key in self.memory_cache:
                    self.stats_hits += 1
                    logger.debug(f"Cache HIT (memory): {key}")
                    return self.memory_cache[full_key]
                else:
                    self.stats_misses += 1
                    logger.debug(f"Cache MISS (memory): {key}")
                    return None
            
            # Redis cache
            if not self.connected:
                await self.connect()
            
            data = await self.redis.get(full_key)
            
            if data:
                self.stats_hits += 1
                logger.debug(f"Cache HIT (redis): {key}")
                return self._deserialize(data)
            else:
                self.stats_misses += 1
                logger.debug(f"Cache MISS (redis): {key}")
                return None
        
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            self.stats_misses += 1
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be serialized)
            ttl: Time-to-live in seconds (None = default)
        
        Returns:
            True if successful
        """
        full_key = self._make_key(key)
        ttl_seconds = ttl if ttl is not None else self.default_ttl
        
        try:
            if self.use_fallback:
                # In-memory cache (no TTL support in fallback)
                self.memory_cache[full_key] = value
                logger.debug(f"Cache SET (memory): {key}")
                return True
            
            # Redis cache
            if not self.connected:
                await self.connect()
            
            # Serialize value
            serialized = self._serialize(value)
            
            # Set with TTL
            if ttl_seconds > 0:
                await self.redis.setex(full_key, ttl_seconds, serialized)
            else:
                await self.redis.set(full_key, serialized)
            
            logger.debug(f"Cache SET (redis): {key}, ttl={ttl_seconds}s, size={len(serialized)}B")
            return True
        
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    async def get_or_set(
        self,
        key: str,
        getter: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get from cache or compute and cache.
        
        Args:
            key: Cache key
            getter: Function to compute value if miss (can be async)
            ttl: Time-to-live in seconds
        
        Returns:
            Cached or computed value
        """
        # Try cache first
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        # Cache miss - compute value
        logger.debug(f"Cache MISS: computing value for '{key}'")
        
        # Handle both sync and async getters
        import asyncio
        if asyncio.iscoroutinefunction(getter):
            value = await getter()
        else:
            value = getter()
        
        # Cache the computed value
        await self.set(key, value, ttl)
        
        return value
    
    async def delete(self, key: str) -> bool:
        """
        Delete a single key from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if key was deleted
        """
        full_key = self._make_key(key)
        
        try:
            if self.use_fallback:
                if full_key in self.memory_cache:
                    del self.memory_cache[full_key]
                    logger.debug(f"Cache DELETE (memory): {key}")
                    return True
                return False
            
            # Redis cache
            if not self.connected:
                await self.connect()
            
            result = await self.redis.delete(full_key)
            logger.debug(f"Cache DELETE (redis): {key}")
            return result > 0
        
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    async def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "table:*", "quality:tenant-123:*")
        
        Returns:
            Number of keys deleted
        """
        full_pattern = self._make_key(pattern)
        
        try:
            if self.use_fallback:
                # In-memory cache - pattern matching
                import fnmatch
                keys_to_delete = [
                    k for k in self.memory_cache.keys()
                    if fnmatch.fnmatch(k, full_pattern)
                ]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                
                count = len(keys_to_delete)
                self.stats_evictions += count
                logger.info(f"Cache INVALIDATE (memory): pattern={pattern}, deleted={count}")
                return count
            
            # Redis cache
            if not self.connected:
                await self.connect()
            
            # Find all matching keys
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=full_pattern,
                    count=100
                )
                
                if keys:
                    deleted = await self.redis.delete(*keys)
                    deleted_count += deleted
                
                if cursor == 0:
                    break
            
            self.stats_evictions += deleted_count
            logger.info(f"Cache INVALIDATE (redis): pattern={pattern}, deleted={deleted_count}")
            return deleted_count
        
        except Exception as e:
            logger.error(f"Cache invalidate error for pattern '{pattern}': {e}")
            return 0
    
    async def clear_all(self) -> bool:
        """
        Clear all cache entries (dangerous!).
        
        Returns:
            True if successful
        """
        try:
            if self.use_fallback:
                count = len(self.memory_cache)
                self.memory_cache.clear()
                logger.warning(f"Cache CLEAR ALL (memory): cleared {count} keys")
                return True
            
            # Redis cache
            if not self.connected:
                await self.connect()
            
            await self.redis.flushdb()
            logger.warning("Cache CLEAR ALL (redis): all keys deleted")
            return True
        
        except Exception as e:
            logger.error(f"Cache clear all error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if key exists
        """
        full_key = self._make_key(key)
        
        try:
            if self.use_fallback:
                return full_key in self.memory_cache
            
            # Redis cache
            if not self.connected:
                await self.connect()
            
            return await self.redis.exists(full_key) > 0
        
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for a key.
        
        Args:
            key: Cache key
        
        Returns:
            Remaining seconds or None if no TTL or key doesn't exist
        """
        full_key = self._make_key(key)
        
        try:
            if self.use_fallback:
                # In-memory cache doesn't support TTL
                return None
            
            # Redis cache
            if not self.connected:
                await self.connect()
            
            ttl = await self.redis.ttl(full_key)
            
            if ttl > 0:
                return ttl
            else:
                return None
        
        except Exception as e:
            logger.error(f"Cache get_ttl error for key '{key}': {e}")
            return None
    
    async def get_stats(self) -> CacheStats:
        """
        Get cache statistics.
        
        Returns:
            CacheStats with hit rate, memory usage, etc.
        """
        try:
            total_requests = self.stats_hits + self.stats_misses
            hit_rate = (self.stats_hits / total_requests * 100) if total_requests > 0 else 0.0
            miss_rate = 100.0 - hit_rate
            
            if self.use_fallback:
                # In-memory cache stats
                import sys
                memory_usage = sum(sys.getsizeof(v) for v in self.memory_cache.values())
                key_count = len(self.memory_cache)
            else:
                # Redis cache stats
                if not self.connected:
                    await self.connect()
                
                info = await self.redis.info("memory")
                memory_usage = info.get("used_memory", 0)
                
                # Count keys with our prefix
                cursor = 0
                key_count = 0
                pattern = self._make_key("*")
                
                while True:
                    cursor, keys = await self.redis.scan(
                        cursor=cursor,
                        match=pattern,
                        count=1000
                    )
                    key_count += len(keys)
                    
                    if cursor == 0:
                        break
            
            return CacheStats(
                total_requests=total_requests,
                cache_hits=self.stats_hits,
                cache_misses=self.stats_misses,
                hit_rate=round(hit_rate, 2),
                miss_rate=round(miss_rate, 2),
                evictions=self.stats_evictions,
                memory_usage_bytes=memory_usage,
                key_count=key_count
            )
        
        except Exception as e:
            logger.error(f"Cache get_stats error: {e}")
            return CacheStats(
                total_requests=self.stats_hits + self.stats_misses,
                cache_hits=self.stats_hits,
                cache_misses=self.stats_misses,
                hit_rate=0.0,
                miss_rate=100.0,
                evictions=self.stats_evictions,
                memory_usage_bytes=0,
                key_count=0
            )
    
    def generate_key(
        self,
        base: str,
        *args: Any,
        **kwargs: Any
    ) -> str:
        """
        Generate a cache key from base string and arguments.
        
        Creates a deterministic hash from the arguments.
        
        Args:
            base: Base key (e.g., "query", "schema", "quality")
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Generated cache key
        
        Example:
            key = cache.generate_key(
                "query",
                table_name="customer_orders",
                filters={"date": "2026-02-11"}
            )
            # Returns: "query:abc123def456..."
        """
        # Combine all arguments into a hashable string
        parts = [str(arg) for arg in args]
        parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        
        combined = ":".join(parts)
        
        # Create hash
        hash_value = hashlib.md5(combined.encode()).hexdigest()[:16]
        
        return f"{base}:{hash_value}"
    
    # Convenience methods for common cache patterns
    
    async def cache_query_result(
        self,
        query: str,
        result: Any,
        ttl: int = 3600
    ) -> bool:
        """
        Cache a query result.
        
        Args:
            query: SQL/PySpark query
            result: Query result
            ttl: TTL in seconds (default 1 hour)
        
        Returns:
            True if cached successfully
        """
        key = self.generate_key("query", query=query)
        return await self.set(key, result, ttl)
    
    async def get_cached_query_result(
        self,
        query: str
    ) -> Optional[Any]:
        """
        Get cached query result.
        
        Args:
            query: SQL/PySpark query
        
        Returns:
            Cached result or None
        """
        key = self.generate_key("query", query=query)
        return await self.get(key)
    
    async def cache_schema_metadata(
        self,
        table_name: str,
        tenant_id: str,
        schema: Dict[str, Any],
        ttl: int = 86400
    ) -> bool:
        """
        Cache schema metadata.
        
        Args:
            table_name: Table name
            tenant_id: Tenant ID
            schema: Schema metadata
            ttl: TTL in seconds (default 24 hours)
        
        Returns:
            True if cached successfully
        """
        key = f"schema:{tenant_id}:{table_name}"
        return await self.set(key, schema, ttl)
    
    async def get_cached_schema_metadata(
        self,
        table_name: str,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached schema metadata.
        
        Args:
            table_name: Table name
            tenant_id: Tenant ID
        
        Returns:
            Cached schema or None
        """
        key = f"schema:{tenant_id}:{table_name}"
        return await self.get(key)
    
    async def invalidate_table_cache(
        self,
        table_name: str,
        tenant_id: str
    ) -> int:
        """
        Invalidate all cache entries for a table.
        
        Args:
            table_name: Table name
            tenant_id: Tenant ID
        
        Returns:
            Number of keys deleted
        """
        # Invalidate all cache types for this table
        total_deleted = 0
        
        patterns = [
            f"schema:{tenant_id}:{table_name}",
            f"quality:{tenant_id}:{table_name}:*",
            f"metrics:{tenant_id}:{table_name}:*",
            f"anomaly:{tenant_id}:{table_name}:*",
            f"query:*{table_name}*"
        ]
        
        for pattern in patterns:
            deleted = await self.invalidate(pattern)
            total_deleted += deleted
        
        logger.info(
            f"Invalidated table cache: table={table_name}, "
            f"tenant={tenant_id}, deleted={total_deleted}"
        )
        
        return total_deleted
