"""
Unit Tests for Sprint 9 - Parameter Extractor Service
======================================================

Tests:
    - Parameter extraction from utm_design_registry
    - Path extraction (bronze_path, silver_path, gold_path)
    - Schema name extraction (bronze_schema, silver_schema, gold_schema)
    - Naming convention extraction (prefixes, suffixes)
    - Target tech stack extraction
    - Source tech stack extraction
    - Table mapping extraction
    - Table name resolution with layer prefixes/suffixes
    - Full table path building (catalog.schema.table)
    - File path building (/mnt/datalake/layer/table)
    - Default values when registry is empty
    - Cache functionality

Coverage Areas:
    - ParameterExtractor.extract_parameters()
    - ParameterExtractor.resolve_table_name()
    - ParameterExtractor.get_full_table_path()
    - ParameterExtractor.get_file_path()
    - ParameterExtractor.to_dict()

Author: Legacy2Lake Engineering
Date: 2026-02-11 (Sprint 9)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import services
from apps.api.services.parameter_extractor_service import (
    ParameterExtractor,
    ProjectParameters
)


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def mock_knowledge_service():
    """Mock KnowledgeService.flatten_knowledge()"""
    with patch('apps.api.services.parameter_extractor_service.KnowledgeService') as mock_ks:
        # Sample flattened registry
        mock_ks.flatten_knowledge.return_value = {
            'paths': {
                'bronze_path': '/mnt/datalake/bronze',
                'silver_path': '/mnt/datalake/silver',
                'gold_path': '/mnt/datalake/gold',
                'target_stack': 'pyspark'
            },
            'naming': {
                'bronze_prefix': 'raw_',
                'silver_prefix': 'stg_',
                'gold_prefix': 'dim_',
                'bronze_suffix': '',
                'silver_suffix': '',
                'gold_suffix': ''
            },
            'target': {
                'tech_stack': 'pyspark',
                'dialect': 'spark_sql',
                'catalog_name': 'main',
                'database_name': 'datalake'
            },
            'source': {
                'tech_stack': 'mssql',
                'dialect': 'tsql'
            },
            'table_mappings': {
                'Customers': 'customers',
                'Orders': 'orders'
            }
        }
        yield mock_ks


@pytest.fixture
def mock_persistence():
    """Mock SupabasePersistence"""
    with patch('apps.api.services.parameter_extractor_service.SupabasePersistence') as mock_db:
        # Mock get_design_registry response
        mock_db.return_value.get_design_registry = AsyncMock(return_value=[
            {
                'key': 'paths',
                'value': {
                    'bronze_path': '/mnt/datalake/bronze',
                    'silver_path': '/mnt/datalake/silver',
                    'gold_path': '/mnt/datalake/gold'
                }
            },
            {
                'key': 'naming',
                'value': {
                    'bronze_prefix': 'raw_',
                    'silver_prefix': 'stg_',
                    'gold_prefix': 'dim_'
                }
            }
        ])
        yield mock_db


# ================================================================
# TEST: ParameterExtractor Initialization
# ================================================================

def test_parameter_extractor_init():
    """Test parameter extractor initialization"""
    extractor = ParameterExtractor(tenant_id="tenant-1", project_id="project-1")
    
    assert extractor is not None
    assert extractor.tenant_id == "tenant-1"
    assert extractor.project_id == "project-1"
    assert extractor._cache is None


# ================================================================
# TEST: Extract Parameters
# ================================================================

@pytest.mark.asyncio
async def test_extract_parameters(mock_persistence, mock_knowledge_service):
    """Test extracting parameters from utm_design_registry"""
    extractor = ParameterExtractor(tenant_id="tenant-1", project_id="project-1")
    params = await extractor.extract_parameters()
    
    assert params is not None
    assert isinstance(params, ProjectParameters)
    
    # Verify paths
    assert params.bronze_path == '/mnt/datalake/bronze'
    assert params.silver_path == '/mnt/datalake/silver'
    assert params.gold_path == '/mnt/datalake/gold'
    
    # Verify schemas would use defaults if not in registry
    # (In this mock, they're not provided, so defaults apply)
    
    # Verify naming
    assert params.bronze_prefix == 'raw_'
    assert params.silver_prefix == 'stg_'
    assert params.gold_prefix == 'dim_'
    
    # Verify target
    assert params.target_tech_stack == 'pyspark'
    assert params.catalog_name == 'main'


@pytest.mark.asyncio
async def test_extract_parameters_with_schemas(mock_persistence, mock_knowledge_service):
    """Test extracting parameters with explicit schemas"""
    # Add schema names to mock
    mock_knowledge_service.flatten_knowledge.return_value['schemas'] = {
        'bronze_schema': 'raw_staging',
        'silver_schema': 'curated_silver',
        'gold_schema': 'business_gold'
    }
    
    extractor = ParameterExtractor(tenant_id="tenant-1", project_id="project-1")
    params = await extractor.extract_parameters()
    
    assert params.bronze_schema == 'raw_staging'
    assert params.silver_schema == 'curated_silver'
    assert params.gold_schema == 'business_gold'


@pytest.mark.asyncio
async def test_extract_parameters_cache(mock_persistence, mock_knowledge_service):
    """Test parameter caching"""
    extractor = ParameterExtractor(tenant_id="tenant-1", project_id="project-1")
    
    # First call
    params1 = await extractor.extract_parameters()
    
    # Second call (should hit cache)
    params2 = await extractor.extract_parameters()
    
    assert params1 is params2  # Same object
    assert extractor._cache is not None


# ================================================================
# TEST: Resolve Table Name
# ================================================================

def test_resolve_table_name_bronze():
    """Test resolving table name for bronze layer"""
    params = ProjectParameters(
        bronze_prefix='raw_',
        bronze_suffix='',
        silver_prefix='stg_',
        silver_suffix='',
        gold_prefix='dim_',
        gold_suffix='',
        bronze_path='/bronze',
        silver_path='/silver',
        gold_path='/gold',
        bronze_schema='raw',
        silver_schema='curated',
        gold_schema='business',
        catalog_name='main',
        database_name='datalake',
        target_tech_stack='pyspark',
        target_dialect='spark_sql',
        source_tech_stack='mssql',
        source_dialect='tsql',
        table_mappings={}
    )
    
    extractor = ParameterExtractor()
    extractor._cache = params
    
    table_name = extractor.resolve_table_name('Customers', 'bronze', params)
    
    # Should apply bronze_prefix
    assert table_name == 'raw_Customers' or table_name == 'raw_customers'


def test_resolve_table_name_silver():
    """Test resolving table name for silver layer"""
    params = ProjectParameters(
        bronze_prefix='raw_',
        silver_prefix='stg_',
        gold_prefix='dim_',
        bronze_suffix='',
        silver_suffix='',
        gold_suffix='',
        bronze_path='/bronze',
        silver_path='/silver',
        gold_path='/gold',
        bronze_schema='raw',
        silver_schema='curated',
        gold_schema='business',
        catalog_name='main',
        database_name='datalake',
        target_tech_stack='pyspark',
        target_dialect='spark_sql',
        source_tech_stack='mssql',
        source_dialect='tsql',
        table_mappings={'Customers': 'customers'}
    )
    
    extractor = ParameterExtractor()
    extractor._cache = params
    
    table_name = extractor.resolve_table_name('Customers', 'silver', params)
    
    # Should apply silver_prefix + table mapping
    assert 'stg_' in table_name.lower()
    assert 'customers' in table_name.lower()


def test_resolve_table_name_gold():
    """Test resolving table name for gold layer"""
    params = ProjectParameters(
        bronze_prefix='raw_',
        silver_prefix='stg_',
        gold_prefix='dim_',
        bronze_suffix='',
        silver_suffix='',
        gold_suffix='',
        bronze_path='/bronze',
        silver_path='/silver',
        gold_path='/gold',
        bronze_schema='raw',
        silver_schema='curated',
        gold_schema='business',
        catalog_name='main',
        database_name='datalake',
        target_tech_stack='pyspark',
        target_dialect='spark_sql',
        source_tech_stack='mssql',
        source_dialect='tsql',
        table_mappings={}
    )
    
    extractor = ParameterExtractor()
    extractor._cache = params
    
    table_name = extractor.resolve_table_name('Customers', 'gold', params)
    
    # Should apply gold_prefix (dimension prefix)
    assert 'dim_' in table_name.lower()


def test_resolve_table_name_with_suffix():
    """Test resolving table name with suffix"""
    params = ProjectParameters(
        bronze_prefix='raw_',
        silver_prefix='stg_',
        gold_prefix='dim_',
        bronze_suffix='_src',
        silver_suffix='_clean',
        gold_suffix='',
        bronze_path='/bronze',
        silver_path='/silver',
        gold_path='/gold',
        bronze_schema='raw',
        silver_schema='curated',
        gold_schema='business',
        catalog_name='main',
        database_name='datalake',
        target_tech_stack='pyspark',
        target_dialect='spark_sql',
        source_tech_stack='mssql',
        source_dialect='tsql',
        table_mappings={}
    )
    
    extractor = ParameterExtractor()
    extractor._cache = params
    
    table_name = extractor.resolve_table_name('Customers', 'bronze', params)
    
    # Should have both prefix and suffix
    assert table_name.startswith('raw_')
    assert table_name.endswith('_src')


# ================================================================
# TEST: Get Full Table Path
# ================================================================

def test_get_full_table_path_bronze():
    """Test building full table path for bronze layer"""
    params = ProjectParameters(
        bronze_prefix='raw_',
        silver_prefix='stg_',
        gold_prefix='dim_',
        bronze_suffix='',
        silver_suffix='',
        gold_suffix='',
        bronze_path='/bronze',
        silver_path='/silver',
        gold_path='/gold',
        bronze_schema='raw_staging',
        silver_schema='curated_silver',
        gold_schema='business_gold',
        catalog_name='main',
        database_name='datalake',
        target_tech_stack='pyspark',
        target_dialect='spark_sql',
        source_tech_stack='mssql',
        source_dialect='tsql',
        table_mappings={}
    )
    
    extractor = ParameterExtractor()
    extractor._cache = params
    
    full_path = extractor.get_full_table_path('raw_customers', 'bronze', params)
    
    # Should be catalog.schema.table
    assert full_path == 'main.raw_staging.raw_customers'


def test_get_full_table_path_silver():
    """Test building full table path for silver layer"""
    params = ProjectParameters(
        bronze_prefix='raw_',
        silver_prefix='stg_',
        gold_prefix='dim_',
        bronze_suffix='',
        silver_suffix='',
        gold_suffix='',
        bronze_path='/bronze',
        silver_path='/silver',
        gold_path='/gold',
        bronze_schema='raw_staging',
        silver_schema='curated_silver',
        gold_schema='business_gold',
        catalog_name='main',
        database_name='datalake',
        target_tech_stack='pyspark',
        target_dialect='spark_sql',
        source_tech_stack='mssql',
        source_dialect='tsql',
        table_mappings={}
    )
    
    extractor = ParameterExtractor()
    extractor._cache = params
    
    full_path = extractor.get_full_table_path('stg_customers', 'silver', params)
    
    assert full_path == 'main.curated_silver.stg_customers'


# ================================================================
# TEST: Get File Path
# ================================================================

def test_get_file_path_bronze():
    """Test building file path for bronze layer"""
    params = ProjectParameters(
        bronze_prefix='raw_',
        silver_prefix='stg_',
        gold_prefix='dim_',
        bronze_suffix='',
        silver_suffix='',
        gold_suffix='',
        bronze_path='/mnt/datalake/bronze',
        silver_path='/mnt/datalake/silver',
        gold_path='/mnt/datalake/gold',
        bronze_schema='raw_staging',
        silver_schema='curated_silver',
        gold_schema='business_gold',
        catalog_name='main',
        database_name='datalake',
        target_tech_stack='pyspark',
        target_dialect='spark_sql',
        source_tech_stack='mssql',
        source_dialect='tsql',
        table_mappings={}
    )
    
    extractor = ParameterExtractor()
    extractor._cache = params
    
    file_path = extractor.get_file_path('raw_customers', 'bronze', params)
    
    assert file_path == '/mnt/datalake/bronze/raw_customers'


def test_get_file_path_silver():
    """Test building file path for silver layer"""
    params = ProjectParameters(
        bronze_prefix='raw_',
        silver_prefix='stg_',
        gold_prefix='dim_',
        bronze_suffix='',
        silver_suffix='',
        gold_suffix='',
        bronze_path='/mnt/datalake/bronze',
        silver_path='/mnt/datalake/silver',
        gold_path='/mnt/datalake/gold',
        bronze_schema='raw_staging',
        silver_schema='curated_silver',
        gold_schema='business_gold',
        catalog_name='main',
        database_name='datalake',
        target_tech_stack='pyspark',
        target_dialect='spark_sql',
        source_tech_stack='mssql',
        source_dialect='tsql',
        table_mappings={}
    )
    
    extractor = ParameterExtractor()
    extractor._cache = params
    
    file_path = extractor.get_file_path('stg_customers', 'silver', params)
    
    assert file_path == '/mnt/datalake/silver/stg_customers'


# ================================================================
# TEST: To Dict
# ================================================================

def test_to_dict():
    """Test converting ProjectParameters to dictionary"""
    params = ProjectParameters(
        bronze_prefix='raw_',
        silver_prefix='stg_',
        gold_prefix='dim_',
        bronze_suffix='',
        silver_suffix='',
        gold_suffix='',
        bronze_path='/bronze',
        silver_path='/silver',
        gold_path='/gold',
        bronze_schema='raw',
        silver_schema='curated',
        gold_schema='business',
        catalog_name='main',
        database_name='datalake',
        target_tech_stack='pyspark',
        target_dialect='spark_sql',
        source_tech_stack='mssql',
        source_dialect='tsql',
        table_mappings={'Customers': 'customers'}
    )
    
    extractor = ParameterExtractor()
    param_dict = extractor.to_dict(params)
    
    assert isinstance(param_dict, dict)
    assert param_dict['bronze_prefix'] == 'raw_'
    assert param_dict['catalog_name'] == 'main'
    assert param_dict['target_tech_stack'] == 'pyspark'
    assert param_dict['table_mappings'] == {'Customers': 'customers'}


# ================================================================
# TEST: Default Values
# ================================================================

@pytest.mark.asyncio
async def test_extract_parameters_defaults():
    """Test that defaults are used when registry is empty"""
    # Mock empty registry
    with patch('apps.api.services.parameter_extractor_service.SupabasePersistence') as mock_db:
        mock_db.return_value.get_design_registry = AsyncMock(return_value=[])
        
        with patch('apps.api.services.parameter_extractor_service.KnowledgeService') as mock_ks:
            mock_ks.flatten_knowledge.return_value = {}
            
            extractor = ParameterExtractor(tenant_id="tenant-1", project_id="project-1")
            params = await extractor.extract_parameters()
            
            # Should have default values
            assert params is not None
            assert params.bronze_schema == 'bronze'  # Default
            assert params.silver_schema == 'silver'  # Default
            assert params.gold_schema == 'gold'  # Default
            assert params.catalog_name == 'main'  # Default


# ================================================================
# TEST: Table Mappings
# ================================================================

@pytest.mark.asyncio
async def test_extract_table_mappings(mock_persistence, mock_knowledge_service):
    """Test extracting table name mappings"""
    extractor = ParameterExtractor(tenant_id="tenant-1", project_id="project-1")
    params = await extractor.extract_parameters()
    
    assert params.table_mappings is not None
    assert params.table_mappings.get('Customers') == 'customers'
    assert params.table_mappings.get('Orders') == 'orders'


def test_resolve_table_name_with_mapping():
    """Test table name resolution uses mapping"""
    params = ProjectParameters(
        bronze_prefix='raw_',
        silver_prefix='stg_',
        gold_prefix='dim_',
        bronze_suffix='',
        silver_suffix='',
        gold_suffix='',
        bronze_path='/bronze',
        silver_path='/silver',
        gold_path='/gold',
        bronze_schema='raw',
        silver_schema='curated',
        gold_schema='business',
        catalog_name='main',
        database_name='datalake',
        target_tech_stack='pyspark',
        target_dialect='spark_sql',
        source_tech_stack='mssql',
        source_dialect='tsql',
        table_mappings={'Customers': 'customers'}
    )
    
    extractor = ParameterExtractor()
    extractor._cache = params
    
    table_name = extractor.resolve_table_name('Customers', 'silver', params)
    
    # Should use mapping (Customers -> customers) + prefix
    assert 'stg_customers' in table_name.lower()


# ================================================================
# TEST: Clear Cache
# ================================================================

@pytest.mark.asyncio
async def test_clear_cache(mock_persistence, mock_knowledge_service):
    """Test clearing the parameter cache"""
    extractor = ParameterExtractor(tenant_id="tenant-1", project_id="project-1")
    
    # Load parameters (populates cache)
    params = await extractor.extract_parameters()
    assert extractor._cache is not None
    
    # Clear cache
    extractor.clear_cache()
    assert extractor._cache is None


# ================================================================
# TEST: Error Handling
# ================================================================

@pytest.mark.asyncio
async def test_extract_parameters_db_error():
    """Test handling database errors gracefully"""
    with patch('apps.api.services.parameter_extractor_service.SupabasePersistence') as mock_db:
        # Mock database error
        mock_db.return_value.get_design_registry = AsyncMock(side_effect=Exception("DB connection failed"))
        
        extractor = ParameterExtractor(tenant_id="tenant-1", project_id="project-1")
        params = await extractor.extract_parameters()
        
        # Should fall back to defaults
        assert params is not None
        assert params.catalog_name == 'main'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
