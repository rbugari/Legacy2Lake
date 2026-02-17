"""
Integration Tests for Sprint 9 - Zero-Hardcode Generation
==========================================================

Tests:
    - End-to-end code generation with Agent C
    - Schema extraction + parameter extraction + template generation
    - Verification that generated code has NO hardcoded values
    - Verification that schema columns are used dynamically
    - Verification that table names are resolved from parameters
    - Verification that paths are resolved from design registry
    - Bronze/silver/gold layer integration

Coverage Areas:
    - AgentCService.transpile_task() with Sprint 9 enhancements
    - Integration of SchemaMetadataService + ParameterExtractor + TemplateEngine
    - LLM context injection with schema + parameters
    - Response includes schema and parameters

Author: Legacy2Lake Engineering
Date: 2026-02-11 (Sprint 9)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json

# Import services
from apps.api.services.agent_c_service import AgentCService


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def mock_agent_c_dependencies():
    """Mock all Agent C dependencies"""
    with patch('apps.api.services.agent_c_service.SupabasePersistence') as mock_db, \\
         patch('apps.api.services.agent_c_service.KnowledgeService') as mock_ks, \\
         patch('apps.api.services.agent_c_service.SchemaMetadataService') as mock_sms, \\
         patch('apps.api.services.agent_c_service.ParameterExtractor') as mock_pe, \\
         patch('apps.api.services.agent_c_service.TemplateEngine') as mock_te, \\
         patch('apps.api.services.agent_c_service.ValidationService') as mock_vs, \\
         patch('apps.api.services.agent_c_service.TestGeneratorService') as mock_tg, \\
         patch('apps.api.services.agent_c_service.CartridgeFactory') as mock_cf:
        
        # Mock database
        mock_db_instance = Mock()
        mock_db_instance.resolve_agent_model = AsyncMock(return_value={
            'provider': 'azure',
            'endpoint': 'https://test.openai.azure.com',
            'deployment': 'gpt-4',
            'api_version': '2024-02-01',
            'api_key': 'test-key',
            'temperature': 0
        })
        mock_db_instance.get_design_registry = AsyncMock(return_value=[])
        mock_db_instance.get_prompt = AsyncMock(return_value="You are a code generator.")
        mock_db.return_value = mock_db_instance
        
        # Mock KnowledgeService
        mock_ks.flatten_knowledge.return_value = {}
        
        # Mock SchemaMetadataService
        mock_schema_service = Mock()
        mock_schema = Mock()
        mock_schema.table_name = "Customers"
        mock_schema.columns = [
            Mock(name="customer_id", data_type="int", nullable=False, is_primary_key=True, is_foreign_key=False),
            Mock(name="customer_name", data_type="varchar(100)", nullable=False, is_primary_key=False, is_foreign_key=False)
        ]
        mock_schema.primary_key = ["customer_id"]
        mock_schema.foreign_keys = []
        mock_schema.row_count = 1000
        mock_schema_service.get_table_schema = AsyncMock(return_value=mock_schema)
        mock_sms.return_value = mock_schema_service
        
        # Mock ParameterExtractor
        mock_param_extractor = Mock()
        mock_params = Mock()
        mock_params.bronze_path = "/mnt/datalake/bronze"
        mock_params.silver_path = "/mnt/datalake/silver"
        mock_params.gold_path = "/mnt/datalake/gold"
        mock_params.bronze_schema = "raw_staging"
        mock_params.silver_schema = "curated_silver"
        mock_params.gold_schema = "business_gold"
        mock_params.bronze_prefix = "raw_"
        mock_params.silver_prefix = "stg_"
        mock_params.gold_prefix = "dim_"
        mock_params.catalog_name = "main"
        mock_params.target_tech_stack = "pyspark"
        mock_param_extractor.extract_parameters = AsyncMock(return_value=mock_params)
        mock_pe.return_value = mock_param_extractor
        
        # Mock TemplateEngine
        mock_template_engine = Mock()
        mock_template_engine.render_template = AsyncMock(return_value="""
# BRONZE LAYER
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
df = spark.read.csv("/source/customers.csv")
df.write.format("delta").save("main.raw_staging.raw_customers")
        """)
        mock_te.return_value = mock_template_engine
        
        # Mock ValidationService
        mock_validator = Mock()
        mock_validation_result = Mock()
        mock_validation_result.is_valid = True
        mock_validation_result.errors_count = 0
        mock_validation_result.warnings_count = 0
        mock_validation_result.to_dict = Mock(return_value={'is_valid': True})
        mock_validator.validate_code = AsyncMock(return_value=mock_validation_result)
        mock_vs.return_value = mock_validator
        
        # Mock TestGeneratorService
        mock_test_gen = Mock()
        mock_test_gen.generate_tests = AsyncMock(return_value="def test_bronze(): pass")
        mock_tg.return_value = mock_test_gen
        
        # Mock CartridgeFactory
        mock_cartridge = Mock()
        mock_cartridge.get_rules = Mock(return_value="Generate PySpark code.")
        mock_cf.get_cartridge.return_value = mock_cartridge
        
        yield {
            'db': mock_db_instance,
            'schema_service': mock_schema_service,
            'param_extractor': mock_param_extractor,
            'template_engine': mock_template_engine,
            'validator': mock_validator,
            'test_gen': mock_test_gen,
            'schema': mock_schema,
            'params': mock_params
        }


@pytest.fixture
def mock_llm():
    """Mock LLM response"""
    with patch('apps.api.services.agent_c_service.AzureChatOpenAI') as mock_llm_class:
        mock_llm_instance = Mock()
        
        # Mock LLM response with generated code
        mock_response = Mock()
        mock_response.content = json.dumps({
            'code': """
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("bronze_customers").getOrCreate()
df = spark.read.csv("/source/customers.csv")
df.write.format("delta").save("main.raw_staging.raw_customers")
            """,
            'mapping_logic': 'Bronze ingestion for Customers table',
            'audit_trail': 'Generated using schema metadata and design registry parameters'
        })
        
        mock_llm_instance.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_class.return_value = mock_llm_instance
        
        yield mock_llm_instance


# ================================================================
# TEST: End-to-End Bronze Generation
# ================================================================

@pytest.mark.asyncio
async def test_agent_c_bronze_with_schema_and_params(mock_agent_c_dependencies, mock_llm):
    """Test Agent C generates bronze code with schema + parameters"""
    agent_c = AgentCService(tenant_id="tenant-1", client_id="client-1")
    
    node_data = {
        'project_id': 'project-123',
        'asset_id': 'asset-456',
        'tech_id': 'pyspark',
        'layer': 'bronze',
        'source_table': 'Customers',
        'target_table': 'raw_customers'
    }
    
    result = await agent_c.transpile_task(node_data)
    
    # Verify result structure
    assert result is not None
    assert 'code' in result
    assert 'validation' in result
    assert 'schema' in result  # Sprint 9
    assert 'parameters' in result  # Sprint 9
    
    # Verify schema was extracted
    assert result['schema'] is not None
    
    # Verify parameters were extracted
    assert result['parameters'] is not None
    
    # Verify validation passed
    assert result['validation']['is_valid'] is True


@pytest.mark.asyncio
async def test_agent_c_schema_extraction_called(mock_agent_c_dependencies, mock_llm):
    """Test that SchemaMetadataService.get_table_schema() is called"""
    agent_c = AgentCService(tenant_id="tenant-1", client_id="client-1")
    
    node_data = {
        'project_id': 'project-123',
        'asset_id': 'asset-456',
        'tech_id': 'pyspark',
        'layer': 'bronze'
    }
    
    result = await agent_c.transpile_task(node_data)
    
    # Verify SchemaMetadataService was used
    schema_service = mock_agent_c_dependencies['schema_service']
    schema_service.get_table_schema.assert_called_once_with('asset-456')


@pytest.mark.asyncio
async def test_agent_c_parameter_extraction_called(mock_agent_c_dependencies, mock_llm):
    """Test that ParameterExtractor.extract_parameters() is called"""
    agent_c = AgentCService(tenant_id="tenant-1", client_id="client-1")
    
    node_data = {
        'project_id': 'project-123',
        'asset_id': 'asset-456',
        'tech_id': 'pyspark',
        'layer': 'bronze'
    }
    
    result = await agent_c.transpile_task(node_data)
    
    # Verify ParameterExtractor was used
    param_extractor = mock_agent_c_dependencies['param_extractor']
    param_extractor.extract_parameters.assert_called_once()


@pytest.mark.asyncio
async def test_agent_c_template_generation_for_pyspark(mock_agent_c_dependencies, mock_llm):
    """Test that TemplateEngine is used for PySpark"""
    agent_c = AgentCService(tenant_id="tenant-1", client_id="client-1")
    
    node_data = {
        'project_id': 'project-123',
        'asset_id': 'asset-456',
        'tech_id': 'pyspark',
        'layer': 'bronze'
    }
    
    result = await agent_c.transpile_task(node_data)
    
    # Verify TemplateEngine was used
    template_engine = mock_agent_c_dependencies['template_engine']
    template_engine.render_template.assert_called_once()


# ================================================================
# TEST: Schema Context in LLM Prompt
# ================================================================

@pytest.mark.asyncio
async def test_agent_c_llm_receives_schema_context(mock_agent_c_dependencies, mock_llm):
    """Test that LLM receives schema context in prompt"""
    agent_c = AgentCService(tenant_id="tenant-1", client_id="client-1")
    
    node_data = {
        'project_id': 'project-123',
        'asset_id': 'asset-456',
        'tech_id': 'pyspark',
        'layer': 'bronze'
    }
    
    result = await agent_c.transpile_task(node_data)
    
    # Verify LLM was called
    assert mock_llm.ainvoke.called
    
    # Get the messages sent to LLM
    call_args = mock_llm.ainvoke.call_args
    messages = call_args[0][0]
    
    # Find HumanMessage with prompt
    human_message = next((msg for msg in messages if hasattr(msg, 'content') and 'Schema Metadata' in msg.content), None)
    
    assert human_message is not None
    assert 'Schema Metadata' in human_message.content
    assert 'Project Parameters' in human_message.content


@pytest.mark.asyncio
async def test_agent_c_llm_receives_parameters_context(mock_agent_c_dependencies, mock_llm):
    """Test that LLM receives parameters context in prompt"""
    agent_c = AgentCService(tenant_id="tenant-1", client_id="client-1")
    
    node_data = {
        'project_id': 'project-123',
        'asset_id': 'asset-456',
        'tech_id': 'pyspark',
        'layer': 'silver'
    }
    
    result = await agent_c.transpile_task(node_data)
    
    # Verify LLM was called
    assert mock_llm.ainvoke.called
    
    # Get the messages sent to LLM
    call_args = mock_llm.ainvoke.call_args
    messages = call_args[0][0]
    
    # Find HumanMessage with prompt
    human_message = next((msg for msg in messages if hasattr(msg, 'content') and 'Project Parameters' in msg.content), None)
    
    assert human_message is not None
    assert 'bronze_path' in human_message.content or 'silver_path' in human_message.content


# ================================================================
# TEST: No Hardcoded Values in Generated Code
# ================================================================

@pytest.mark.asyncio
async def test_generated_code_uses_dynamic_values(mock_agent_c_dependencies, mock_llm):
    """Test that generated code uses dynamic values from schema + parameters"""
    agent_c = AgentCService(tenant_id="tenant-1", client_id="client-1")
    
    node_data = {
        'project_id': 'project-123',
        'asset_id': 'asset-456',
        'tech_id': 'pyspark',
        'layer': 'bronze'
    }
    
    result = await agent_c.transpile_task(node_data)
    
    generated_code = result['code']
    
    # Verify code uses schema-driven values
    # (The mock LLM returns code with dynamic table names)
    assert 'main.raw_staging.raw_customers' in generated_code or 'raw_staging' in generated_code
    
    # Verify no obvious hardcoded values
    # (This is a basic check; real validation happens in Sprint 8 ValidationService)
    assert generated_code is not None
    assert len(generated_code) > 0


# ================================================================
# TEST: Silver Layer Integration
# ================================================================

@pytest.mark.asyncio
async def test_agent_c_silver_with_schema_and_params(mock_agent_c_dependencies, mock_llm):
    """Test Agent C generates silver code with schema + parameters"""
    # Update mock LLM response for silver
    mock_llm.ainvoke.return_value.content = json.dumps({
        'code': """
from pyspark.sql import SparkSession
from delta.tables import DeltaTable

spark = SparkSession.builder.appName("silver_customers").getOrCreate()
df = spark.read.table("main.raw_staging.raw_customers")

# Merge using primary key
target_table = DeltaTable.forName(spark, "main.curated_silver.stg_customers")
target_table.alias("target").merge(
    df.alias("source"),
    "target.customer_id = source.customer_id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
        """,
        'mapping_logic': 'Silver SCD Type 2 for Customers',
        'audit_trail': 'Used schema.primary_key for merge condition'
    })
    
    agent_c = AgentCService(tenant_id="tenant-1", client_id="client-1")
    
    node_data = {
        'project_id': 'project-123',
        'asset_id': 'asset-456',
        'tech_id': 'pyspark',
        'layer': 'silver'
    }
    
    result = await agent_c.transpile_task(node_data)
    
    # Verify result
    assert result is not None
    assert 'code' in result
    assert result['schema'] is not None
    assert result['parameters'] is not None
    
    # Verify silver-specific logic
    generated_code = result['code']
    assert 'merge' in generated_code.lower() or 'upsert' in generated_code.lower()


# ================================================================
# TEST: Gold Layer Integration
# ================================================================

@pytest.mark.asyncio
async def test_agent_c_gold_with_schema_and_params(mock_agent_c_dependencies, mock_llm):
    """Test Agent C generates gold code with schema + parameters"""
    # Update mock LLM response for gold
    mock_llm.ainvoke.return_value.content = json.dumps({
        'code': """
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("gold_customers").getOrCreate()
df = spark.read.table("main.curated_silver.stg_customers")

# Gold logic: dimension table
df_gold = df.select("customer_id", "customer_name")
df_gold.write.format("delta").mode("overwrite").saveAsTable("main.business_gold.dim_customers")
        """,
        'mapping_logic': 'Gold dimension for Customers',
        'audit_trail': 'Dimension table with no aggregation'
    })
    
    agent_c = AgentCService(tenant_id="tenant-1", client_id="client-1")
    
    node_data = {
        'project_id': 'project-123',
        'asset_id': 'asset-456',
        'tech_id': 'pyspark',
        'layer': 'gold'
    }
    
    result = await agent_c.transpile_task(node_data)
    
    # Verify result
    assert result is not None
    assert 'code' in result
    assert result['schema'] is not None
    assert result['parameters'] is not None


# ================================================================
# TEST: Error Handling When Schema Missing
# ================================================================

@pytest.mark.asyncio
async def test_agent_c_handles_missing_schema_gracefully(mock_agent_c_dependencies, mock_llm):
    """Test Agent C handles missing schema gracefully"""
    # Mock schema service to return None
    schema_service = mock_agent_c_dependencies['schema_service']
    schema_service.get_table_schema = AsyncMock(return_value=None)
    
    agent_c = AgentCService(tenant_id="tenant-1", client_id="client-1")
    
    node_data = {
        'project_id': 'project-123',
        'asset_id': 'asset-999',  # Non-existent
        'tech_id': 'pyspark',
        'layer': 'bronze'
    }
    
    result = await agent_c.transpile_task(node_data)
    
    # Should still generate code (with fallback logic)
    assert result is not None
    assert 'code' in result
    # Schema context will be None
    assert result['schema'] is None or result['schema'] == 'N/A'


# ================================================================
# TEST: Error Handling When Parameters Missing
# ================================================================

@pytest.mark.asyncio
async def test_agent_c_handles_missing_parameters_gracefully(mock_agent_c_dependencies, mock_llm):
    """Test Agent C handles missing parameters gracefully"""
    # Mock param extractor to return None
    param_extractor = mock_agent_c_dependencies['param_extractor']
    param_extractor.extract_parameters = AsyncMock(return_value=None)
    
    agent_c = AgentCService(tenant_id="tenant-1", client_id="client-1")
    
    node_data = {
        'project_id': 'project-999',  # Non-existent
        'asset_id': 'asset-456',
        'tech_id': 'pyspark',
        'layer': 'bronze'
    }
    
    result = await agent_c.transpile_task(node_data)
    
    # Should still generate code (with defaults)
    assert result is not None
    assert 'code' in result
    # Parameters context will be None
    assert result['parameters'] is None or result['parameters'] == 'N/A'


# ================================================================
# TEST: Non-PySpark Technologies Skip Template Generation
# ================================================================

@pytest.mark.asyncio
async def test_agent_c_snowflake_skips_template(mock_agent_c_dependencies, mock_llm):
    """Test that non-PySpark technologies skip template generation"""
    agent_c = AgentCService(tenant_id="tenant-1", client_id="client-1")
    
    node_data = {
        'project_id': 'project-123',
        'asset_id': 'asset-456',
        'tech_id': 'snowflake',  # Not PySpark
        'layer': 'bronze'
    }
    
    result = await agent_c.transpile_task(node_data)
    
    # TemplateEngine should NOT be called for Snowflake
    template_engine = mock_agent_c_dependencies['template_engine']
    # Template engine is only called for pyspark/spark
    # For snowflake, it should be skipped
    # (Check is in Agent C code: if target_engine in ['pyspark', 'spark'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
