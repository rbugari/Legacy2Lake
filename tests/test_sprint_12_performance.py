"""
Sprint 12: Performance Optimization - Unit Tests

Tests for QueryOptimizer, CacheManager, and ParallelProcessor services.
Total: 18 tests (6 per service)

Author: UTM Platform Team
Version: 3.14 (Sprint 12)
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import time
from datetime import datetime

from apps.api.services.query_optimizer_service import QueryOptimizer, CostEstimate, QueryPlan
from apps.api.services.cache_manager_service import CacheManager, CacheStats
from apps.api.services.parallel_processor_service import ParallelProcessor, ExecutionMode


# ============================================================================
# QUERY OPTIMIZER TESTS (6 tests)
# ============================================================================

class TestQueryOptimizer:
    """Tests for QueryOptimizer service"""
    
    @pytest.fixture
    def optimizer(self):
        return QueryOptimizer(platform="databricks")
    
    @pytest.fixture
    def sample_table_stats(self):
        return {
            'orders': {
                'rows': 1000000,
                'bytes': 100000000,
                'partitions': ['order_date', 'region']
            },
            'customers': {
                'rows': 10000,
                'bytes': 1000000,
                'partitions': []
            }
        }
    
    @pytest.mark.asyncio
    async def test_predicate_pushdown(self, optimizer):
        """Test predicate pushdown optimization"""
        query = """
            SELECT * FROM orders
            WHERE order_date = '2026-02-11'
        """
        
        result = await optimizer.optimize_query(
            query=query,
            query_type="sql",
            table_stats={'orders': {'rows': 1000000, 'bytes': 100000000}}
        )
        
        assert result.is_optimized
        assert 'predicate_pushdown' in result.optimizations_applied
        assert result.estimated_speedup > 1.0
        assert result.cost_after.total_cost < result.cost_before.total_cost
    
    @pytest.mark.asyncio
    async def test_partition_pruning(self, optimizer, sample_table_stats):
        """Test partition pruning optimization"""
        query = """
            SELECT id, customer_id, amount
            FROM orders
            WHERE order_date = '2026-02-11' AND region = 'US'
        """
        
        result = await optimizer.optimize_query(
            query=query,
            query_type="sql",
            table_stats=sample_table_stats
        )
        
        assert result.is_optimized
        assert 'partition_pruning' in result.optimizations_applied
        # Should have 2 filters matching 2 partitions
        plan = await optimizer.analyze_query(query, "sql")
        assert len(plan.filters) == 2
    
    @pytest.mark.asyncio
    async def test_column_projection(self, optimizer):
        """Test column projection optimization (SELECT *)"""
        query_with_star = "SELECT * FROM orders WHERE id = 123"
        
        result = await optimizer.optimize_query(
            query=query_with_star,
            query_type="sql",
            table_stats={'orders': {'rows': 1000000, 'bytes': 100000000}}
        )
        
        assert result.is_optimized
        assert 'column_projection' in result.optimizations_applied
        assert 'SELECT *' in result.metadata.get('recommendations', [])
    
    @pytest.mark.asyncio
    async def test_join_reordering(self, optimizer, sample_table_stats):
        """Test join reordering optimization"""
        query = """
            SELECT o.id, c.name
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE o.order_date = '2026-02-11'
        """
        
        result = await optimizer.optimize_query(
            query=query,
            query_type="sql",
            table_stats=sample_table_stats
        )
        
        assert result.is_optimized
        assert 'join_reordering' in result.optimizations_applied
        # Smaller table (customers: 10k rows) should be broadcast
        assert 'customers' in str(result.metadata.get('join_strategy', ''))
    
    @pytest.mark.asyncio
    async def test_cost_estimation(self, optimizer, sample_table_stats):
        """Test cost estimation accuracy"""
        query = """
            SELECT * FROM orders
            WHERE order_date = '2026-02-11' AND region = 'US'
        """
        
        plan = await optimizer.analyze_query(query, "sql")
        cost = await optimizer.estimate_cost(plan, sample_table_stats)
        
        assert isinstance(cost, CostEstimate)
        assert cost.io_cost > 0
        assert cost.cpu_cost > 0
        assert cost.total_cost == cost.io_cost + cost.cpu_cost
        assert cost.estimated_rows > 0
        assert cost.estimated_bytes > 0
    
    @pytest.mark.asyncio
    async def test_sql_and_pyspark_support(self, optimizer):
        """Test support for both SQL and PySpark"""
        # SQL query
        sql_query = "SELECT * FROM orders WHERE id = 123"
        sql_result = await optimizer.optimize_query(
            query=sql_query,
            query_type="sql",
            table_stats={'orders': {'rows': 1000000, 'bytes': 100000000}}
        )
        assert sql_result.query_type == "sql"
        assert sql_result.is_optimized
        
        # PySpark query
        pyspark_query = """
            df = spark.read.table("orders")
            df = df.filter("order_date = '2026-02-11'")
        """
        pyspark_result = await optimizer.optimize_query(
            query=pyspark_query,
            query_type="pyspark",
            table_stats={'orders': {'rows': 1000000, 'bytes': 100000000}}
        )
        assert pyspark_result.query_type == "pyspark"
        assert pyspark_result.is_optimized


# ============================================================================
# CACHE MANAGER TESTS (6 tests)
# ============================================================================

class TestCacheManager:
    """Tests for CacheManager service"""
    
    @pytest.fixture
    async def cache_manager(self):
        """Create cache manager with in-memory fallback"""
        cache = CacheManager(
            redis_url="redis://localhost:6379",
            default_ttl=300,
            key_prefix="utm:test:"
        )
        
        # Try to connect, fall back to memory if Redis unavailable
        try:
            await cache.connect()
        except:
            pass  # Will use fallback mode
        
        yield cache
        
        # Cleanup
        try:
            await cache.clear_all()
            await cache.disconnect()
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_cache_get_hit(self, cache_manager):
        """Test cache hit scenario"""
        key = "test_hit_key"
        value = {"data": "test_value", "count": 42}
        
        # Set value
        success = await cache_manager.set(key, value, ttl=300)
        assert success
        
        # Get value (should hit)
        result = await cache_manager.get(key)
        assert result == value
        
        # Check stats
        stats = await cache_manager.get_stats()
        assert stats.cache_hits > 0
    
    @pytest.mark.asyncio
    async def test_cache_get_miss(self, cache_manager):
        """Test cache miss scenario"""
        key = "nonexistent_key"
        
        # Get value (should miss)
        result = await cache_manager.get(key)
        assert result is None
        
        # Check stats
        stats = await cache_manager.get_stats()
        assert stats.cache_misses > 0
    
    @pytest.mark.asyncio
    async def test_cache_set_and_ttl(self, cache_manager):
        """Test cache set and TTL management"""
        key = "test_ttl_key"
        value = "test_value"
        ttl = 5  # 5 seconds
        
        # Set with TTL
        await cache_manager.set(key, value, ttl=ttl)
        
        # Should exist immediately
        assert await cache_manager.exists(key)
        
        # Check TTL
        remaining_ttl = await cache_manager.get_ttl(key)
        if remaining_ttl:  # Redis mode
            assert 0 < remaining_ttl <= ttl
        
        # Wait for expiration (if Redis available)
        if cache_manager.client:
            await asyncio.sleep(ttl + 1)
            result = await cache_manager.get(key)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_get_or_set(self, cache_manager):
        """Test cache-aside pattern (get_or_set)"""
        key = "test_get_or_set"
        call_count = 0
        
        async def expensive_operation():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return {"result": "computed_value", "count": call_count}
        
        # First call: should compute and cache
        result1 = await cache_manager.get_or_set(key, expensive_operation, ttl=300)
        assert result1["count"] == 1
        assert call_count == 1
        
        # Second call: should return cached value (no computation)
        result2 = await cache_manager.get_or_set(key, expensive_operation, ttl=300)
        assert result2["count"] == 1  # Same as first call
        assert call_count == 1  # Not incremented
    
    @pytest.mark.asyncio
    async def test_cache_invalidate_pattern(self, cache_manager):
        """Test pattern-based cache invalidation"""
        # Set multiple keys
        keys = ["table:orders:query1", "table:orders:query2", "table:customers:query1"]
        for key in keys:
            await cache_manager.set(key, {"data": key}, ttl=300)
        
        # Verify all exist
        for key in keys:
            assert await cache_manager.exists(key)
        
        # Invalidate orders table
        invalidated = await cache_manager.invalidate("table:orders:*")
        assert invalidated >= 2  # At least 2 keys
        
        # Check results
        assert not await cache_manager.exists("table:orders:query1")
        assert not await cache_manager.exists("table:orders:query2")
        assert await cache_manager.exists("table:customers:query1")  # Should remain
    
    @pytest.mark.asyncio
    async def test_cache_fallback_mode(self):
        """Test fallback to in-memory cache when Redis unavailable"""
        # Create cache with invalid Redis URL
        cache = CacheManager(
            redis_url="redis://invalid_host:9999",
            default_ttl=300,
            key_prefix="utm:test:"
        )
        
        # Should fall back to memory
        try:
            await cache.connect()
        except:
            pass
        
        # Should still work in fallback mode
        key = "fallback_test"
        value = {"data": "fallback_value"}
        
        success = await cache.set(key, value)
        assert success
        
        result = await cache.get(key)
        assert result == value


# ============================================================================
# PARALLEL PROCESSOR TESTS (6 tests)
# ============================================================================

class TestParallelProcessor:
    """Tests for ParallelProcessor service"""
    
    @pytest.fixture
    def processor(self):
        return ParallelProcessor(max_workers=5, mode="auto", timeout_seconds=10)
    
    @pytest.mark.asyncio
    async def test_execute_batch_async(self, processor):
        """Test async parallel execution"""
        async def sample_task(task_id: int):
            await asyncio.sleep(0.1)
            return f"result_{task_id}"
        
        tasks = [lambda i=i: sample_task(i) for i in range(10)]
        
        result = await processor.execute_batch(tasks, mode="async")
        
        assert result.total_tasks == 10
        assert result.succeeded == 10
        assert result.failed == 0
        assert result.execution_mode == "async"
        assert result.speedup_factor > 1.0  # Should be faster than sequential
    
    @pytest.mark.asyncio
    async def test_execute_batch_process(self, processor):
        """Test process pool execution"""
        def cpu_task(n: int) -> int:
            """CPU-bound task"""
            return sum(i * i for i in range(n))
        
        tasks = [lambda n=1000: cpu_task(n) for _ in range(5)]
        
        result = await processor.execute_batch(tasks, mode="process")
        
        assert result.total_tasks == 5
        assert result.succeeded == 5
        assert result.execution_mode == "process"
    
    @pytest.mark.asyncio
    async def test_execute_batch_thread(self, processor):
        """Test thread pool execution"""
        def mixed_task(task_id: int) -> str:
            """Mixed I/O and CPU task"""
            time.sleep(0.05)  # Simulate I/O
            result = sum(i for i in range(1000))  # Simulate CPU
            return f"task_{task_id}_result_{result}"
        
        tasks = [lambda i=i: mixed_task(i) for i in range(10)]
        
        result = await processor.execute_batch(tasks, mode="thread")
        
        assert result.total_tasks == 10
        assert result.succeeded == 10
        assert result.execution_mode == "thread"
    
    @pytest.mark.asyncio
    async def test_batch_quality_evaluation(self, processor):
        """Test batch quality evaluation (integration test)"""
        # Mock the quality engine
        with patch('apps.api.services.quality_rule_engine_service.QualityRuleEngine') as MockEngine:
            mock_instance = MockEngine.return_value
            
            # Mock evaluation result
            mock_result = Mock()
            mock_result.quality_score = 85.0
            mock_result.rules_passed = 17
            mock_result.rules_failed = 3
            mock_instance.evaluate_table = AsyncMock(return_value=mock_result)
            
            # Run batch quality evaluation
            table_names = ["table1", "table2", "table3"]
            
            result = await processor.batch_quality_evaluation(
                table_names=table_names,
                tenant_id="test_tenant",
                project_id="test_project",
                quality_threshold=70.0
            )
            
            assert result.total_tables == 3
            assert result.avg_quality_score == 85.0
            assert len(result.tables_below_threshold) == 0  # All above 70%
            assert result.speedup_factor > 1.0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, processor):
        """Test error handling in parallel execution"""
        async def failing_task(task_id: int):
            if task_id % 2 == 0:
                raise ValueError(f"Task {task_id} failed")
            return f"success_{task_id}"
        
        tasks = [lambda i=i: failing_task(i) for i in range(10)]
        
        result = await processor.execute_batch(tasks, mode="async")
        
        assert result.total_tasks == 10
        assert result.succeeded == 5  # Odd tasks succeed
        assert result.failed == 5  # Even tasks fail
        
        # Check error details
        failed_results = [r for r in result.results if r.status == "error"]
        assert len(failed_results) == 5
        assert all("failed" in r.error for r in failed_results)
    
    @pytest.mark.asyncio
    async def test_resource_limits_and_timeout(self):
        """Test resource limits and timeout handling"""
        processor = ParallelProcessor(max_workers=2, mode="async", timeout_seconds=1)
        
        async def slow_task(task_id: int):
            await asyncio.sleep(2)  # Exceeds timeout
            return f"result_{task_id}"
        
        tasks = [lambda i=i: slow_task(i) for i in range(5)]
        
        result = await processor.execute_batch(tasks, mode="async")
        
        # All tasks should timeout
        assert result.failed == 5
        
        # Check timeout errors
        timeout_results = [r for r in result.results if r.status == "error"]
        assert len(timeout_results) == 5
        assert all("Timeout" in r.error or "timeout" in r.error.lower() for r in timeout_results)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestSpring12Integration:
    """Integration tests for Sprint 12 components working together"""
    
    @pytest.mark.asyncio
    async def test_cache_and_optimizer_integration(self):
        """Test cache and optimizer working together"""
        cache = CacheManager(redis_url="redis://localhost:6379", key_prefix="utm:test:")
        optimizer = QueryOptimizer(platform="databricks")
        
        try:
            await cache.connect()
        except:
            pass  # Fallback mode
        
        # Generate cache key for query
        query = "SELECT * FROM orders WHERE date = '2026-02-11'"
        cache_key = cache.generate_key("query", query=query)
        
        # First call: optimize and cache
        result1 = await optimizer.optimize_query(
            query=query,
            query_type="sql",
            table_stats={'orders': {'rows': 1000000, 'bytes': 100000000}}
        )
        await cache.set(cache_key, result1, ttl=300)
        
        # Second call: retrieve from cache
        cached_result = await cache.get(cache_key)
        assert cached_result is not None
        assert cached_result.original_query == result1.original_query
        assert cached_result.estimated_speedup == result1.estimated_speedup
        
        # Cleanup
        await cache.delete(cache_key)
        try:
            await cache.disconnect()
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_full_optimization_pipeline(self):
        """Test complete optimization pipeline"""
        # Initialize all services
        cache = CacheManager(redis_url="redis://localhost:6379", key_prefix="utm:test:")
        optimizer = QueryOptimizer(platform="databricks")
        processor = ParallelProcessor(max_workers=5, mode="async")
        
        try:
            await cache.connect()
        except:
            pass
        
        # Simulate multiple queries (batch processing)
        queries = [
            f"SELECT * FROM orders WHERE id = {i}" for i in range(10)
        ]
        
        async def process_query(query: str):
            # Check cache first
            cache_key = cache.generate_key("query", query=query)
            cached = await cache.get(cache_key)
            
            if cached:
                return {"source": "cache", "result": cached}
            
            # Optimize query
            result = await optimizer.optimize_query(
                query=query,
                query_type="sql",
                table_stats={'orders': {'rows': 1000000, 'bytes': 100000000}}
            )
            
            # Cache result
            await cache.set(cache_key, result, ttl=300)
            
            return {"source": "optimized", "result": result}
        
        # Process in parallel
        tasks = [lambda q=q: process_query(q) for q in queries]
        batch_result = await processor.execute_batch(tasks, mode="async")
        
        assert batch_result.succeeded == 10
        assert batch_result.speedup_factor > 1.0
        
        # Second run should be mostly from cache
        batch_result2 = await processor.execute_batch(tasks, mode="async")
        assert batch_result2.succeeded == 10
        
        # Cleanup
        for query in queries:
            cache_key = cache.generate_key("query", query=query)
            await cache.delete(cache_key)
        
        try:
            await cache.disconnect()
        except:
            pass


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
