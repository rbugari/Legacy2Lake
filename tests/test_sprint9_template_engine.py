"""
Unit Tests for Sprint 9 - Template Engine Service
==================================================

Tests:
    - Template rendering with Jinja2
    - Dynamic context building (schema + parameters)
    - PySpark bronze/silver/gold templates
    - Column references from schema
    - Table name resolution from parameters
    - Path resolution from parameters
    - Primary key handling
    - Foreign key handling

Coverage Areas:
    - TemplateEngine.render_template()
    - TemplateEngine._build_context()
    - Template syntax validation
    - Error handling for missing templates

Author: Legacy2Lake Engineering
Date: 2026-02-11 (Sprint 9)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

# Import services
from apps.api.services.template_engine_service import TemplateEngine
from apps.api.services.schema_metadata_service import TableSchema, ColumnMetadata, ForeignKeyMetadata
from apps.api.services.parameter_extractor_service import ProjectParameters


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def sample_schema():
    """Sample table schema for testing"""
    return TableSchema(
        asset_id="asset-123",
        table_name="Customers",
        columns=[
            ColumnMetadata(
                name="customer_id",
                data_type="int",
                nullable=False,
                is_primary_key=True,
                is_foreign_key=False
            ),
            ColumnMetadata(
                name="customer_name",
                data_type="varchar(100)",
                nullable=False,
                is_primary_key=False,
                is_foreign_key=False
            ),
            ColumnMetadata(
                name="email",
                data_type="varchar(255)",
                nullable=True,
                is_primary_key=False,
                is_foreign_key=False
            ),
            ColumnMetadata(
                name="_ingestion_timestamp",
                data_type="timestamp",
                nullable=False,
                is_primary_key=False,
                is_foreign_key=False
            )
        ],
        primary_key=["customer_id"],
        foreign_keys=[],
        row_count=1000000,
        sample_data=[
            {"customer_id": 1, "customer_name": "Alice", "email": "alice@example.com"},
            {"customer_id": 2, "customer_name": "Bob", "email": "bob@example.com"}
        ]
    )


@pytest.fixture
def sample_parameters():
    """Sample project parameters for testing"""
    return ProjectParameters(
        bronze_path="/mnt/datalake/bronze",
        silver_path="/mnt/datalake/silver",
        gold_path="/mnt/datalake/gold",
        bronze_schema="raw_staging",
        silver_schema="curated_silver",
        gold_schema="business_gold",
        bronze_prefix="raw_",
        silver_prefix="stg_",
        gold_prefix="dim_",
        bronze_suffix="",
        silver_suffix="",
        gold_suffix="",
        catalog_name="main",
        database_name="datalake",
        target_tech_stack="pyspark",
        target_dialect="spark_sql",
        source_tech_stack="mssql",
        source_dialect="tsql",
        table_mappings={
            "Customers": "customers",
            "Orders": "orders"
        }
    )


@pytest.fixture
def template_engine():
    """Template engine instance"""
    return TemplateEngine()


# ================================================================
# TEST: TemplateEngine Initialization
# ================================================================

def test_template_engine_init(template_engine):
    """Test template engine initialization"""
    assert template_engine is not None
    assert template_engine.env is not None
    assert 'pyspark_bronze' in template_engine.TEMPLATES
    assert 'pyspark_silver' in template_engine.TEMPLATES
    assert 'pyspark_gold' in template_engine.TEMPLATES


def test_template_engine_has_filters(template_engine):
    """Test template engine has custom filters"""
    assert 'snake_case' in template_engine.env.filters
    assert 'camel_case' in template_engine.env.filters


# ================================================================
# TEST: Template Rendering - Bronze Layer
# ================================================================

@pytest.mark.asyncio
async def test_render_bronze_template(template_engine, sample_schema, sample_parameters):
    """Test rendering bronze layer template"""
    code = await template_engine.render_template(
        template_name='pyspark_bronze',
        schema=sample_schema,
        params=sample_parameters,
        layer='bronze'
    )
    
    assert code is not None
    assert len(code) > 0
    
    # Verify dynamic values are injected (no hardcoded)
    assert 'BRONZE_SCHEMA = "raw_staging"' in code
    assert 'TARGET_TABLE = "raw_customers"' in code or 'TARGET_TABLE = "raw_Customers"' in code
    assert 'CATALOG = "main"' in code
    
    # Verify columns are dynamic
    assert '"customer_id"' in code
    assert '"customer_name"' in code
    assert '"email"' in code
    
    # Verify audit columns
    assert '_ingestion_timestamp' in code
    assert 'current_timestamp()' in code


@pytest.mark.asyncio
async def test_bronze_template_column_loop(template_engine, sample_schema, sample_parameters):
    """Test bronze template generates column list dynamically"""
    code = await template_engine.render_template(
        template_name='pyspark_bronze',
        schema=sample_schema,
        params=sample_parameters,
        layer='bronze'
    )
    
    # All business columns should be in source_columns list
    for col in sample_schema.columns:
        if not col.name.startswith('_'):
            assert f'"{col.name}"' in code


# ================================================================
# TEST: Template Rendering - Silver Layer
# ================================================================

@pytest.mark.asyncio
async def test_render_silver_template(template_engine, sample_schema, sample_parameters):
    """Test rendering silver layer template"""
    code = await template_engine.render_template(
        template_name='pyspark_silver',
        schema=sample_schema,
        params=sample_parameters,
        layer='silver'
    )
    
    assert code is not None
    assert len(code) > 0
    
    # Verify dynamic values
    assert 'SILVER_SCHEMA = "curated_silver"' in code
    assert 'BRONZE_SCHEMA = "raw_staging"' in code
    
    # Verify primary key in merge condition
    assert 'customer_id' in code
    assert 'dropDuplicates' in code
    
    # Verify SCD Type 2 (upsert)
    assert 'merge' in code.lower()
    assert 'whenMatchedUpdateAll' in code
    assert 'whenNotMatchedInsertAll' in code


@pytest.mark.asyncio
async def test_silver_template_primary_key_filter(template_engine, sample_schema, sample_parameters):
    """Test silver template filters null primary keys"""
    code = await template_engine.render_template(
        template_name='pyspark_silver',
        schema=sample_schema,
        params=sample_parameters,
        layer='silver'
    )
    
    # Should filter nulls in PK columns
    for pk in sample_schema.primary_key:
        assert f'col("{pk}").isNotNull()' in code


# ================================================================
# TEST: Template Rendering - Gold Layer
# ================================================================

@pytest.mark.asyncio
async def test_render_gold_template(template_engine, sample_schema, sample_parameters):
    """Test rendering gold layer template"""
    code = await template_engine.render_template(
        template_name='pyspark_gold',
        schema=sample_schema,
        params=sample_parameters,
        layer='gold',
        table_type='DIMENSION'
    )
    
    assert code is not None
    assert len(code) > 0
    
    # Verify dynamic values
    assert 'GOLD_SCHEMA = "business_gold"' in code
    assert 'SILVER_SCHEMA = "curated_silver"' in code
    
    # Verify dimension logic
    assert 'DIMENSION' in code


@pytest.mark.asyncio
async def test_gold_template_fact_table(template_engine, sample_schema, sample_parameters):
    """Test gold template with FACT table type"""
    code = await template_engine.render_template(
        template_name='pyspark_gold',
        schema=sample_schema,
        params=sample_parameters,
        layer='gold',
        table_type='FACT'
    )
    
    assert code is not None
    assert 'FACT' in code


# ================================================================
# TEST: Context Building
# ================================================================

def test_build_context_bronze(template_engine, sample_schema, sample_parameters):
    """Test context building for bronze layer"""
    context = template_engine._build_context(
        schema=sample_schema,
        params=sample_parameters,
        layer='bronze'
    )
    
    assert context is not None
    assert context['schema'] == sample_schema
    assert context['params'] == sample_parameters
    assert context['layer'] == 'bronze'
    assert context['source_table_name'] == 'Customers'
    
    # Bronze has no source (reads from external)
    assert context['source_table_full'] is None
    
    # Target should be resolved
    assert 'target_table_name' in context
    assert 'target_table_full' in context
    assert 'raw_' in context['target_table_name'].lower() or 'customers' in context['target_table_name'].lower()


def test_build_context_silver(template_engine, sample_schema, sample_parameters):
    """Test context building for silver layer"""
    context = template_engine._build_context(
        schema=sample_schema,
        params=sample_parameters,
        layer='silver'
    )
    
    assert context is not None
    assert context['layer'] == 'silver'
    
    # Silver reads from bronze
    assert context['source_table_full'] is not None
    assert 'raw_staging' in context['source_table_full'].lower()
    
    # Target is silver
    assert context['target_table_full'] is not None
    assert 'curated_silver' in context['target_table_full'].lower()


def test_build_context_gold(template_engine, sample_schema, sample_parameters):
    """Test context building for gold layer"""
    context = template_engine._build_context(
        schema=sample_schema,
        params=sample_parameters,
        layer='gold'
    )
    
    assert context is not None
    assert context['layer'] == 'gold'
    
    # Gold reads from silver
    assert context['source_table_full'] is not None
    assert 'curated_silver' in context['source_table_full'].lower()
    
    # Target is gold
    assert context['target_table_full'] is not None
    assert 'business_gold' in context['target_table_full'].lower()


# ================================================================
# TEST: Custom Filters
# ================================================================

def test_snake_case_filter(template_engine):
    """Test snake_case filter"""
    assert template_engine._snake_case("CustomerOrder") == "customer_order"
    assert template_engine._snake_case("customer_order") == "customer_order"
    assert template_engine._snake_case("CUSTOMER_ORDER") == "customer_order"
    assert template_engine._snake_case("CustomerOrderItem") == "customer_order_item"


def test_camel_case_filter(template_engine):
    """Test camel_case filter"""
    assert template_engine._camel_case("customer_order") == "CustomerOrder"
    assert template_engine._camel_case("customer-order") == "CustomerOrder"
    assert template_engine._camel_case("customer order") == "CustomerOrder"


# ================================================================
# TEST: Error Handling
# ================================================================

@pytest.mark.asyncio
async def test_render_invalid_template(template_engine, sample_schema, sample_parameters):
    """Test rendering with invalid template name"""
    from jinja2 import TemplateNotFound
    
    with pytest.raises(TemplateNotFound):
        await template_engine.render_template(
            template_name='invalid_template',
            schema=sample_schema,
            params=sample_parameters,
            layer='bronze'
        )


@pytest.mark.asyncio
async def test_render_with_extra_context(template_engine, sample_schema, sample_parameters):
    """Test rendering with extra context variables"""
    code = await template_engine.render_template(
        template_name='pyspark_bronze',
        schema=sample_schema,
        params=sample_parameters,
        layer='bronze',
        source_path='/custom/path/source.csv'
    )
    
    assert code is not None
    # Extra context should be merged
    # (Template uses source_path variable)


# ================================================================
# TEST: Schema with No Primary Key
# ================================================================

@pytest.mark.asyncio
async def test_silver_template_no_primary_key(template_engine, sample_parameters):
    """Test silver template with table that has no primary key"""
    schema_no_pk = TableSchema(
        asset_id="asset-456",
        table_name="Logs",
        columns=[
            ColumnMetadata(name="log_id", data_type="int", nullable=False, is_primary_key=False, is_foreign_key=False),
            ColumnMetadata(name="message", data_type="varchar(500)", nullable=True, is_primary_key=False, is_foreign_key=False)
        ],
        primary_key=[],  # No PK
        foreign_keys=[],
        row_count=5000000,
        sample_data=[]
    )
    
    code = await template_engine.render_template(
        template_name='pyspark_silver',
        schema=schema_no_pk,
        params=sample_parameters,
        layer='silver'
    )
    
    assert code is not None
    # Should still generate code, but with different logic


# ================================================================
# TEST: Schema with Foreign Keys
# ================================================================

@pytest.mark.asyncio
async def test_gold_template_with_foreign_keys(template_engine, sample_parameters):
    """Test gold template with foreign keys"""
    schema_with_fk = TableSchema(
        asset_id="asset-789",
        table_name="Orders",
        columns=[
            ColumnMetadata(name="order_id", data_type="int", nullable=False, is_primary_key=True, is_foreign_key=False),
            ColumnMetadata(name="customer_id", data_type="int", nullable=False, is_primary_key=False, is_foreign_key=True),
            ColumnMetadata(name="order_date", data_type="date", nullable=False, is_primary_key=False, is_foreign_key=False),
            ColumnMetadata(name="total_amount", data_type="decimal(10,2)", nullable=False, is_primary_key=False, is_foreign_key=False)
        ],
        primary_key=["order_id"],
        foreign_keys=[
            ForeignKeyMetadata(
                column="customer_id",
                ref_table="Customers",
                ref_column="customer_id",
                constraint_name="fk_orders_customers"
            )
        ],
        row_count=5000000,
        sample_data=[]
    )
    
    code = await template_engine.render_template(
        template_name='pyspark_gold',
        schema=schema_with_fk,
        params=sample_parameters,
        layer='gold',
        table_type='FACT'
    )
    
    assert code is not None
    # Should handle foreign keys appropriately


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
