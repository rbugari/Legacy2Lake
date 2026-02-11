"""
Test Suite for Sprint 2 Orchestration Components
Tests workflow state, context management, retry logic, and pipeline optimization
"""
import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

# Import Sprint 2 components
from apps.api.services.orchestration.workflow_state_manager import (
    WorkflowStateManager,
    WorkflowStatus,
    PackageStatus
)
from apps.api.services.orchestration.context_manager import (
    SharedContext,
    ContextCache
)
from apps.api.services.orchestration.retry_manager import (
    RetryManager,
    ErrorCategory
)
from apps.api.services.orchestration.pipeline_optimizer import (
    PipelineOptimizer,
    ValidationResult
)


class TestContextCache:
    """Test ContextCache functionality"""
    
    def test_cache_set_get(self):
        cache = ContextCache(ttl_seconds=10)
        
        # Set value
        cache.set("test_key", {"data": "test_value"})
        
        # Get value
        result = cache.get("test_key")
        assert result is not None
        assert result["data"] == "test_value"
    
    def test_cache_miss(self):
        cache = ContextCache(ttl_seconds=10)
        
        # Get non-existent key
        result = cache.get("missing_key")
        assert result is None
    
    def test_cache_expiration(self):
        cache = ContextCache(ttl_seconds=0)  # Immediate expiration
        
        cache.set("expire_key", "value")
        
        # Wait a moment
        import time
        time.sleep(0.1)
        
        # Should be expired
        result = cache.get("expire_key")
        assert result is None
    
    def test_cache_clear(self):
        cache = ContextCache(ttl_seconds=10)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestSharedContext:
    """Test SharedContext functionality"""
    
    def test_schema_context(self):
        context = SharedContext("test-project-uuid")
        
        schema = {"tables": ["table1", "table2"]}
        context.set_schema_context(schema)
        
        result = context.get_schema_context()
        assert result is not None
        assert len(result["tables"]) == 2
    
    def test_package_metadata(self):
        context = SharedContext("test-project-uuid")
        
        metadata = {
            "package_name": "test_pkg",
            "inputs": ["input1"],
            "outputs": ["output1"]
        }
        
        context.add_package_metadata("test_pkg", metadata)
        
        result = context.get_package_metadata("test_pkg")
        assert result is not None
        assert result["package_name"] == "test_pkg"
        assert len(result["inputs"]) == 1
    
    def test_cache_hits(self):
        context = SharedContext("test-project-uuid")
        
        schema = {"tables": ["table1"]}
        context.set_schema_context(schema)
        
        # First get (cache miss)
        context.get_schema_context()
        assert context.cache_misses == 1
        
        # Second get (cache hit)
        context.get_schema_context()
        assert context.cache_hits == 1
    
    def test_build_agent_context(self):
        context = SharedContext("test-project-uuid")
        
        # Setup contexts
        context.set_schema_context({"tables": ["t1"]})
        context.set_topology_context({"phases": []})
        context.add_package_metadata("pkg1", {"name": "pkg1"})
        context.set_intelligence_context({
            "support_intel": ["tip1"],
            "scout_assessment": {"gaps": []}
        })
        
        # Build agent context
        agent_ctx = context.build_agent_context("pkg1")
        
        assert "project_uuid" in agent_ctx
        assert "package" in agent_ctx
        assert "schema" in agent_ctx
        assert "topology" in agent_ctx
        assert "support_intelligence" in agent_ctx


class TestRetryManager:
    """Test RetryManager functionality"""
    
    def test_error_categorization(self):
        manager = RetryManager()
        
        # Test rate limit detection
        rate_error = Exception("HTTP 429: Rate limit exceeded")
        category = manager.categorize_error(rate_error)
        assert category == ErrorCategory.RATE_LIMIT
        
        # Test timeout detection
        timeout_error = Exception("Request timed out")
        category = manager.categorize_error(timeout_error)
        assert category == ErrorCategory.TIMEOUT
        
        # Test server error detection
        server_error = Exception("HTTP 500: Internal server error")
        category = manager.categorize_error(server_error)
        assert category == ErrorCategory.SERVER_ERROR
        
        # Test validation error detection
        validation_error = Exception("HTTP 400: Bad request")
        category = manager.categorize_error(validation_error)
        assert category == ErrorCategory.VALIDATION_ERROR
    
    def test_should_retry(self):
        manager = RetryManager()
        
        # Rate limit should retry multiple times
        assert manager.should_retry(ErrorCategory.RATE_LIMIT, 0) == True
        assert manager.should_retry(ErrorCategory.RATE_LIMIT, 3) == True
        assert manager.should_retry(ErrorCategory.RATE_LIMIT, 5) == False
        
        # Validation error should not retry
        assert manager.should_retry(ErrorCategory.VALIDATION_ERROR, 0) == True
        assert manager.should_retry(ErrorCategory.VALIDATION_ERROR, 1) == False
    
 @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        manager = RetryManager()
        
        # Create mock function that succeeds
        mock_func = AsyncMock(return_value={"result": "success"})
        
        success, result, error = await manager.execute_with_retry(
            mock_func,
            context_name="test_operation"
        )
        
        assert success == True
        assert result["result"] == "success"
        assert error is None
        assert mock_func.call_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_failure(self):
        manager = RetryManager()
        
        # Create mock function that always fails
        mock_func = AsyncMock(side_effect=Exception("Test error"))
        
        success, result, error = await manager.execute_with_retry(
            mock_func,
            context_name="test_operation"
        )
        
        assert success == False
        assert result is None
        assert "Test error" in error
        # Should retry based on UNKNOWN category (max 2 attempts)
        assert mock_func.call_count >= 2


class TestPipelineOptimizer:
    """Test PipelineOptimizer functionality"""
    
    def test_code_extraction(self):
        optimizer = PipelineOptimizer()
        
        # Test various key formats
        result1 = optimizer._extract_code({"code": "test_code"})
        assert result1 == "test_code"
        
        result2 = optimizer._extract_code({"pyspark_code": "spark_code"})
        assert result2 == "spark_code"
        
        result3 = optimizer._extract_code({"sql_code": "sql_code"})
        assert result3 == "sql_code"
        
        result4 = optimizer._extract_code({"other_key": "value"})
        assert result4 is None
    
    def test_pre_validation_valid_code(self):
        optimizer = PipelineOptimizer()
        
        valid_code = """
        # L2L MODERNIZATION TRACE
        from pyspark.sql import SparkSession
        
        def execute_task(spark, config):
            df = spark.read.table("source")
            df.write.saveAsTable("target")
        """
        
        task_def = {"tech_id": "pyspark"}
        validation = optimizer._pre_validate_code(valid_code, task_def)
        
        assert validation.valid == True
        assert len(validation.issues) == 0
    
    def test_pre_validation_invalid_code(self):
        optimizer = PipelineOptimizer()
        
        invalid_code = "# Too short"
        
        task_def = {"tech_id": "pyspark"}
        validation = optimizer._pre_validate_code(invalid_code, task_def)
        
        assert validation.valid == False
        assert len(validation.issues) > 0
    
    def test_pre_validation_warnings(self):
        optimizer = PipelineOptimizer()
        
        code_with_warnings = """
        def execute_task(spark, config):
            df = spark.read.table("source")
            df.write.saveAsTable("target")
        """
        
        task_def = {"tech_id": "pyspark"}
        validation = optimizer._pre_validate_code(code_with_warnings, task_def)
        
        # Should have warnings but be valid
        assert validation.valid == True
        assert len(validation.warnings) > 0


# Integration test
@pytest.mark.asyncio
async def test_pipeline_integration():
    """Test pipeline with mocked agents"""
    
    # Mock agent responses
    mock_agent_c_result = {
        "code": """
        # L2L MODERNIZATION TRACE
        from pyspark.sql import SparkSession
        
        def execute_task(spark, config):
            df = spark.read.table("source")
            df.write.saveAsTable("target")
            return "SUCCESS"
        """
    }
    
    mock_agent_f_result = {
        "status": "APPROVED",
        "score": 9.5,
        "critique": "Excellent code quality"
    }
    
    with patch("apps.api.services.agent_c_service.AgentCService.transpile_task", new_callable=AsyncMock, return_value=mock_agent_c_result):
        with patch("apps.api.services.agent_f_service.AgentFService.review_code", new_callable=AsyncMock, return_value=mock_agent_f_result):
            
            optimizer = PipelineOptimizer(tenant_id="test-tenant")
            
            task_def = {
                "package_name": "test_package",
                "tech_id": "pyspark"
            }
            
            success, result = await optimizer.execute_pipeline(
                package_name="test_package",
                task_definition=task_def
            )
            
            assert success == True
            assert result["status"] == "APPROVED"
            assert result["score"] == 9.5
            assert result["final_code"] is not None


def run_tests():
    """Run all tests"""
    print("="*80)
    print("🧪 SPRINT 2 ORCHESTRATION TESTS")
    print("="*80)
    
    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
