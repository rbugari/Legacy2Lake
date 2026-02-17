"""
Unit Tests for Sprint 9 - Schema Metadata Service
==================================================

Tests:
    - Table schema extraction from utm_objects.metadata
    - Column metadata parsing (name, type, nullable, PK, FK)
    - Primary key identification
    - Foreign key relationship parsing
    - Sample data extraction
    - Project-wide table schema retrieval
    - Column name extraction
    - Column type mapping
    - Join condition inference from foreign keys
    - Cache functionality

Coverage Areas:
    - SchemaMetadataService.get_table_schema()
    - SchemaMetadataService.get_project_tables()
    - SchemaMetadataService.get_column_names()
    - SchemaMetadataService.get_column_types_map()
    - SchemaMetadataService.infer_join_conditions()

Author: Legacy2Lake Engineering
Date: 2026-02-11 (Sprint 9)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

# Import services
from apps.api.services.schema_metadata_service import (
    SchemaMetadataService,
    TableSchema,
    ColumnMetadata,
    ForeignKeyMetadata
)


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    client = Mock()
    
    # Mock utm_objects query response
    mock_response = Mock()
    mock_response.data = [{
        'object_id': 'asset-123',
        'source_name': 'Customers',
        'source_tech': 'SSIS',
        'metadata': {
            'columns': [
                {
                    'name': 'customer_id',
                    'type': 'int',
                    'nullable': False,
                    'maxLength': None,
                    'precision': None,
                    'scale': None
                },
                {
                    'name': 'customer_name',
                    'type': 'varchar',
                    'nullable': False,
                    'maxLength': 100,
                    'precision': None,
                    'scale': None
                },
                {
                    'name': 'email',
                    'type': 'varchar',
                    'nullable': True,
                    'maxLength': 255,
                    'precision': None,
                    'scale': None
                },
                {
                    'name': '_ingestion_timestamp',
                    'type': 'timestamp',
                    'nullable': False,
                    'maxLength': None,
                    'precision': None,
                    'scale': None
                }
            ],
            'primaryKey': ['customer_id'],
            'foreignKeys': [],
            'rowCount': 1000000,
            'sampleData': [
                {'customer_id': 1, 'customer_name': 'Alice', 'email': 'alice@example.com'},
                {'customer_id': 2, 'customer_name': 'Bob', 'email': 'bob@example.com'}
            ]
        }
    }]
    
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
    
    return client


@pytest.fixture
def mock_supabase_client_with_fk():
    """Mock Supabase client with foreign keys"""
    client = Mock()
    
    mock_response = Mock()
    mock_response.data = [{
        'object_id': 'asset-456',
        'source_name': 'Orders',
        'source_tech': 'SQL_PROC',
        'metadata': {
            'columns': [
                {'name': 'order_id', 'type': 'int', 'nullable': False, 'maxLength': None, 'precision': None, 'scale': None},
                {'name': 'customer_id', 'type': 'int', 'nullable': False, 'maxLength': None, 'precision': None, 'scale': None},
                {'name': 'order_date', 'type': 'date', 'nullable': False, 'maxLength': None, 'precision': None, 'scale': None},
                {'name': 'total_amount', 'type': 'decimal', 'nullable': False, 'maxLength': None, 'precision': 10, 'scale': 2}
            ],
            'primaryKey': ['order_id'],
            'foreignKeys': [
                {
                    'name': 'fk_orders_customers',
                    'column': 'customer_id',
                    'refTable': 'Customers',
                    'refColumn': 'customer_id'
                }
            ],
            'rowCount': 5000000,
            'sampleData': []
        }
    }]
    
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
    
    return client


@pytest.fixture
def mock_persistence():
    """Mock SupabasePersistence"""
    with patch('apps.api.services.schema_metadata_service.SupabasePersistence') as mock_db:
        yield mock_db


# ================================================================
# TEST: SchemaMetadataService Initialization
# ================================================================

def test_schema_service_init():
    """Test schema service initialization"""
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    
    assert service is not None
    assert service.tenant_id == "tenant-1"
    assert service.project_id == "project-1"
    assert service._cache == {}


# ================================================================
# TEST: Get Table Schema
# ================================================================

@pytest.mark.asyncio
async def test_get_table_schema(mock_persistence, mock_supabase_client):
    """Test getting table schema from utm_objects"""
    # Setup mock
    mock_persistence.return_value.client = mock_supabase_client
    
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    schema = await service.get_table_schema("asset-123")
    
    assert schema is not None
    assert schema.asset_id == "asset-123"
    assert schema.table_name == "Customers"
    assert len(schema.columns) == 4
    assert schema.primary_key == ["customer_id"]
    assert schema.row_count == 1000000


@pytest.mark.asyncio
async def test_get_table_schema_columns(mock_persistence, mock_supabase_client):
    """Test column metadata in table schema"""
    mock_persistence.return_value.client = mock_supabase_client
    
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    schema = await service.get_table_schema("asset-123")
    
    # Find customer_id column
    customer_id_col = next((col for col in schema.columns if col.name == "customer_id"), None)
    
    assert customer_id_col is not None
    assert customer_id_col.data_type == "int"
    assert customer_id_col.nullable is False
    assert customer_id_col.is_primary_key is True
    assert customer_id_col.is_foreign_key is False


@pytest.mark.asyncio
async def test_get_table_schema_with_foreign_keys(mock_persistence, mock_supabase_client_with_fk):
    """Test table schema with foreign keys"""
    mock_persistence.return_value.client = mock_supabase_client_with_fk
    
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    schema = await service.get_table_schema("asset-456")
    
    assert schema is not None
    assert schema.table_name == "Orders"
    assert len(schema.foreign_keys) == 1
    
    fk = schema.foreign_keys[0]
    assert fk.column == "customer_id"
    assert fk.ref_table == "Customers"
    assert fk.ref_column == "customer_id"
    assert fk.constraint_name == "fk_orders_customers"


@pytest.mark.asyncio
async def test_get_table_schema_cache(mock_persistence, mock_supabase_client):
    """Test schema caching"""
    mock_persistence.return_value.client = mock_supabase_client
    
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    
    # First call
    schema1 = await service.get_table_schema("asset-123")
    
    # Second call (should hit cache)
    schema2 = await service.get_table_schema("asset-123")
    
    assert schema1 is schema2  # Same object
    assert "asset-123" in service._cache


# ================================================================
# TEST: Get Project Tables
# ================================================================

@pytest.mark.asyncio
async def test_get_project_tables(mock_persistence):
    """Test getting all table schemas for a project"""
    # Setup mock for multiple tables
    client = Mock()
    mock_response = Mock()
    mock_response.data = [
        {
            'object_id': 'asset-1',
            'source_name': 'Customers',
            'metadata': {
                'columns': [{'name': 'customer_id', 'type': 'int', 'nullable': False}],
                'primaryKey': ['customer_id'],
                'foreignKeys': [],
                'rowCount': 1000,
                'sampleData': []
            }
        },
        {
            'object_id': 'asset-2',
            'source_name': 'Orders',
            'metadata': {
                'columns': [{'name': 'order_id', 'type': 'int', 'nullable': False}],
                'primaryKey': ['order_id'],
                'foreignKeys': [],
                'rowCount': 5000,
                'sampleData': []
            }
        }
    ]
    
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
    mock_persistence.return_value.client = client
    
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    tables = await service.get_project_tables()
    
    assert len(tables) == 2
    assert tables[0].table_name == "Customers"
    assert tables[1].table_name == "Orders"


# ================================================================
# TEST: Get Column Names
# ================================================================

def test_get_column_names():
    """Test extracting column names from schema"""
    schema = TableSchema(
        asset_id="asset-123",
        table_name="Customers",
        columns=[
            ColumnMetadata(name="customer_id", data_type="int", nullable=False, is_primary_key=True, is_foreign_key=False),
            ColumnMetadata(name="customer_name", data_type="varchar", nullable=False, is_primary_key=False, is_foreign_key=False),
            ColumnMetadata(name="_ingestion_timestamp", data_type="timestamp", nullable=False, is_primary_key=False, is_foreign_key=False)
        ],
        primary_key=["customer_id"],
        foreign_keys=[],
        row_count=1000,
        sample_data=[]
    )
    
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    
    # Exclude audit columns
    columns = service.get_column_names(schema, exclude_audit=True)
    assert len(columns) == 2
    assert "customer_id" in columns
    assert "customer_name" in columns
    assert "_ingestion_timestamp" not in columns


def test_get_column_names_include_audit():
    """Test extracting column names including audit columns"""
    schema = TableSchema(
        asset_id="asset-123",
        table_name="Customers",
        columns=[
            ColumnMetadata(name="customer_id", data_type="int", nullable=False, is_primary_key=True, is_foreign_key=False),
            ColumnMetadata(name="_ingestion_timestamp", data_type="timestamp", nullable=False, is_primary_key=False, is_foreign_key=False)
        ],
        primary_key=["customer_id"],
        foreign_keys=[],
        row_count=1000,
        sample_data=[]
    )
    
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    
    # Include audit columns
    columns = service.get_column_names(schema, exclude_audit=False)
    assert len(columns) == 2
    assert "_ingestion_timestamp" in columns


# ================================================================
# TEST: Get Column Types Map
# ================================================================

def test_get_column_types_map():
    """Test creating column name -> type mapping"""
    schema = TableSchema(
        asset_id="asset-123",
        table_name="Customers",
        columns=[
            ColumnMetadata(name="customer_id", data_type="int", nullable=False, is_primary_key=True, is_foreign_key=False),
            ColumnMetadata(name="customer_name", data_type="varchar(100)", nullable=False, is_primary_key=False, is_foreign_key=False),
            ColumnMetadata(name="balance", data_type="decimal(10,2)", nullable=True, is_primary_key=False, is_foreign_key=False)
        ],
        primary_key=["customer_id"],
        foreign_keys=[],
        row_count=1000,
        sample_data=[]
    )
    
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    types_map = service.get_column_types_map(schema)
    
    assert types_map is not None
    assert types_map["customer_id"] == "int"
    assert types_map["customer_name"] == "varchar(100)"
    assert types_map["balance"] == "decimal(10,2)"


# ================================================================
# TEST: Infer Join Conditions
# ================================================================

def test_infer_join_conditions():
    """Test inferring join conditions from foreign keys"""
    # Left table (Orders) with FK to Customers
    left_schema = TableSchema(
        asset_id="asset-456",
        table_name="Orders",
        columns=[
            ColumnMetadata(name="order_id", data_type="int", nullable=False, is_primary_key=True, is_foreign_key=False),
            ColumnMetadata(name="customer_id", data_type="int", nullable=False, is_primary_key=False, is_foreign_key=True)
        ],
        primary_key=["order_id"],
        foreign_keys=[
            ForeignKeyMetadata(column="customer_id", ref_table="Customers", ref_column="customer_id", constraint_name="fk_orders_customers")
        ],
        row_count=5000,
        sample_data=[]
    )
    
    # Right table (Customers)
    right_schema = TableSchema(
        asset_id="asset-123",
        table_name="Customers",
        columns=[
            ColumnMetadata(name="customer_id", data_type="int", nullable=False, is_primary_key=True, is_foreign_key=False),
            ColumnMetadata(name="customer_name", data_type="varchar", nullable=False, is_primary_key=False, is_foreign_key=False)
        ],
        primary_key=["customer_id"],
        foreign_keys=[],
        row_count=1000,
        sample_data=[]
    )
    
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    join_info = service.infer_join_conditions(left_schema, right_schema)
    
    assert join_info is not None
    assert join_info['left_table'] == "Orders"
    assert join_info['right_table'] == "Customers"
    assert join_info['left_column'] == "customer_id"
    assert join_info['right_column'] == "customer_id"
    assert join_info['constraint_name'] == "fk_orders_customers"


def test_infer_join_conditions_no_fk():
    """Test inferring join conditions when no foreign key exists"""
    # Tables with no FK relationship
    left_schema = TableSchema(
        asset_id="asset-1",
        table_name="Logs",
        columns=[ColumnMetadata(name="log_id", data_type="int", nullable=False, is_primary_key=True, is_foreign_key=False)],
        primary_key=["log_id"],
        foreign_keys=[],
        row_count=1000,
        sample_data=[]
    )
    
    right_schema = TableSchema(
        asset_id="asset-2",
        table_name="Events",
        columns=[ColumnMetadata(name="event_id", data_type="int", nullable=False, is_primary_key=True, is_foreign_key=False)],
        primary_key=["event_id"],
        foreign_keys=[],
        row_count=1000,
        sample_data=[]
    )
    
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    join_info = service.infer_join_conditions(left_schema, right_schema)
    
    assert join_info is None


# ================================================================
# TEST: Clear Cache
# ================================================================

@pytest.mark.asyncio
async def test_clear_cache(mock_persistence, mock_supabase_client):
    """Test clearing the schema cache"""
    mock_persistence.return_value.client = mock_supabase_client
    
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    
    # Load schema (populates cache)
    schema = await service.get_table_schema("asset-123")
    assert "asset-123" in service._cache
    
    # Clear cache
    service.clear_cache()
    assert service._cache == {}


# ================================================================
# TEST: Error Handling
# ================================================================

@pytest.mark.asyncio
async def test_get_table_schema_not_found(mock_persistence):
    """Test getting schema for non-existent asset"""
    # Setup mock with empty response
    client = Mock()
    mock_response = Mock()
    mock_response.data = []
    
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
    mock_persistence.return_value.client = client
    
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    schema = await service.get_table_schema("asset-999")
    
    assert schema is None


@pytest.mark.asyncio
async def test_get_table_schema_no_metadata(mock_persistence):
    """Test handling utm_objects row with no metadata"""
    # Setup mock with null metadata
    client = Mock()
    mock_response = Mock()
    mock_response.data = [{
        'object_id': 'asset-999',
        'source_name': 'EmptyTable',
        'metadata': None
    }]
    
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
    mock_persistence.return_value.client = client
    
    service = SchemaMetadataService(tenant_id="tenant-1", project_id="project-1")
    schema = await service.get_table_schema("asset-999")
    
    assert schema is None or len(schema.columns) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
