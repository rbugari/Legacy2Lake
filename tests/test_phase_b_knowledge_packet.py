"""
Unit tests for Knowledge Packet Service (Phase B - v4.0)

Tests:
- get_packet() consolidation
- Type resolution priority (DDL > profiled > metadata > fallback)
- SQL table name extraction
- PII detection and masking rules
- Source intelligence extraction
- Project scanning
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from apps.api.services.knowledge_packet_service import (
    KnowledgePacketService,
    KnowledgePacket,
    ColumnKnowledge,
    ColumnMapping,
    TransformationStep,
    SourceConnection,
    TableImpactInfo
)


@pytest.fixture
def knowledge_service():
    """
    Create KnowledgePacketService instance with mocked DB client.
    
    Includes mock for resolve_parser_by_tech RPC (Zero-Hardcode v4.0).
    """
    from unittest.mock import Mock
    
    service = KnowledgePacketService(
        tenant_id="test-tenant-id",
        project_id="test-project-id"
    )
    
    # Mock Supabase client
    mock_client = Mock()
    
    # Mock RPC calls (for parser resolution)
    def mock_rpc(function_name, params=None):
        mock_response = Mock()
        
        if function_name == "resolve_parser_by_tech":
            source_tech = params.get("p_source_tech", "UNKNOWN").upper() if params else "UNKNOWN"
            
            # SSIS parser config
            if source_tech in ["SSIS", "SQL SERVER"]:
                mock_response.data = [{
                    "parser_id": "parser-ssis",
                    "medulla_config": {
                        "main_key": "data_flow_logic",
                        "sql_keys": ["SqlCommand", "OpenRowset", "TableOrViewName"],
                        "transformation_types": ["DerivedColumn", "Lookup", "Sort", "UnionAll", "ConditionalSplit"],
                        "complexity_weights": {
                            "oledbsource": 1,
                            "derivedcolumn": 2,
                            "lookup": 3,
                            "conditionalsplit": 4,
                            "script": 8
                        }
                    }
                }]
            else:
                # Generic fallback
                mock_response.data = [{
                    "parser_id": "parser-generic",
                    "medulla_config": {
                        "main_key": "components",
                        "sql_keys": ["sql_query", "query"],
                        "transformation_types": [],
                        "complexity_weights": {"default": 2}
                    }
                }]
            
            mock_response.execute = Mock(return_value=mock_response)
            return mock_response
        
        # Default empty response
        mock_response.data = []
        mock_response.execute = Mock(return_value=mock_response)
        return mock_response
    
    mock_client.rpc = mock_rpc
    
    # Mock table queries
    mock_execute = Mock()
    mock_execute.data = []
    mock_client.table = Mock(return_value=Mock(
        select=Mock(return_value=Mock(
            eq=Mock(return_value=Mock(
                execute=Mock(return_value=mock_execute)
            ))
        ))
    ))
    
    service.db.client = mock_client
    
    return service


@pytest.fixture
def sample_asset():
    """Sample asset from utm_objects."""
    return {
        "object_id": "asset-123",
        "project_id": "project-456",
        "name": "LoadCustomers.dtsx",
        "source_tech": "SSIS",
        "metadata": {
            "source_tech": "SSIS",  # Also in metadata for _extract_source_intelligence
            "logical_medulla": {
                "connections": [
                    {
                        "name": "SourceDB",
                        "server": "sql-server-01",
                        "database": "AdventureWorks",
                        "type": "OLEDB"
                    }
                ],
                "data_flow_logic": [
                    {
                        "type": "OleDbSource",
                        "name": "Extract Customers",
                        "raw_properties": {
                            "SqlCommand": "SELECT CustomerID, FirstName, LastName, Email FROM dbo.Customers WHERE ModifiedDate > @LastRunDate"
                        },
                        "columns": [
                            {"name": "CustomerID", "type": "INT"},
                            {"name": "FirstName", "type": "STRING"},
                            {"name": "LastName", "type": "STRING"},
                            {"name": "Email", "type": "STRING"}
                        ]
                    },
                    {
                        "type": "DerivedColumn",
                        "name": "Add Load Date",
                        "raw_properties": {
                            "Expression": "GETDATE()"
                        }
                    },
                    {
                        "type": "Lookup",
                        "name": "Lookup Region",
                        "raw_properties": {
                            "TableOrViewName": "dbo.DimRegion"
                        }
                    }
                ],
                "columns": [
                    {"name": "CustomerID", "type": "INT"},
                    {"name": "FirstName", "type": "STRING"},
                    {"name": "LastName", "type": "STRING"},
                    {"name": "Email", "type": "STRING"}
                ]
            }
        }
    }


@pytest.fixture
def sample_profiled_columns():
    """Sample profiled columns from utm_asset_columns."""
    return [
        {
            "column_name": "CustomerID",
            "inferred_type": "int",
            "nullable_flag": False,
            "is_pii": False,
            "cardinality_ratio": 1.0,
            "sample_values": ["1", "2", "3"]
        },
        {
            "column_name": "Email",
            "inferred_type": "varchar",
            "nullable_flag": True,
            "is_pii": True,
            "pii_category": "email",
            "cardinality_ratio": 0.95,
            "sample_values": ["john@example.com", "jane@example.com"]
        }
    ]


@pytest.fixture
def sample_schema_reference():
    """Sample schema_reference.json from DDL."""
    return {
        "tables": {
            "Customers": {
                "schema": "dbo",
                "columns": [
                    {
                        "name": "CustomerID",
                        "data_type": "INT",
                        "is_primary_key": True,
                        "is_nullable": False
                    },
                    {
                        "name": "FirstName",
                        "data_type": "VARCHAR(50)",
                        "is_primary_key": False,
                        "is_nullable": False
                    },
                    {
                        "name": "LastName",
                        "data_type": "VARCHAR(50)",
                        "is_primary_key": False,
                        "is_nullable": False
                    },
                    {
                        "name": "Email",
                        "data_type": "VARCHAR(100)",
                        "is_primary_key": False,
                        "is_nullable": True
                    }
                ]
            }
        }
    }


# ============================================
# Test: Table Name Extraction
# ============================================

def test_extract_table_names_simple_select(knowledge_service):
    """Test extraction from simple SELECT."""
    sql = "SELECT * FROM dbo.Customers"
    tables = knowledge_service._extract_table_names_from_query(sql)
    
    assert "dbo.Customers" in tables


def test_extract_table_names_with_brackets(knowledge_service):
    """Test extraction with SQL Server brackets."""
    sql = "SELECT * FROM [dbo].[Customers]"
    tables = knowledge_service._extract_table_names_from_query(sql)
    
    assert "dbo.Customers" in tables


def test_extract_table_names_with_joins(knowledge_service):
    """Test extraction with JOIN syntax."""
    sql = """
    SELECT c.*, o.OrderID
    FROM dbo.Customers c
    INNER JOIN dbo.Orders o ON c.CustomerID = o.CustomerID
    LEFT JOIN dbo.OrderDetails od ON o.OrderID = od.OrderID
    """
    tables = knowledge_service._extract_table_names_from_query(sql)
    
    assert "dbo.Customers" in tables
    assert "dbo.Orders" in tables
    assert "dbo.OrderDetails" in tables


def test_extract_table_names_insert(knowledge_service):
    """Test extraction from INSERT statement."""
    sql = "INSERT INTO dw.DimCustomer (CustomerKey, Name) VALUES (@p1, @p2)"
    tables = knowledge_service._extract_table_names_from_query(sql)
    
    assert "dw.DimCustomer" in tables


def test_extract_table_names_update(knowledge_service):
    """Test extraction from UPDATE statement."""
    sql = "UPDATE dbo.Customers SET Email = @p1 WHERE CustomerID = @p2"
    tables = knowledge_service._extract_table_names_from_query(sql)
    
    assert "dbo.Customers" in tables


def test_extract_table_names_empty(knowledge_service):
    """Test with empty SQL."""
    tables = knowledge_service._extract_table_names_from_query(None)
    assert tables == []
    
    tables = knowledge_service._extract_table_names_from_query("")
    assert tables == []


# ============================================
# Test: Metadata Column Extraction
# ============================================

def test_extract_metadata_columns(knowledge_service, sample_asset):
    """Test extraction of columns from metadata."""
    metadata = sample_asset["metadata"]
    columns = knowledge_service._extract_metadata_columns(metadata)
    
    assert len(columns) == 4
    assert any(col["name"] == "CustomerID" for col in columns)
    assert any(col["name"] == "Email" for col in columns)


def test_extract_metadata_columns_deduplication(knowledge_service):
    """Test that duplicate columns are deduplicated."""
    metadata = {
        "logical_medulla": {
            "data_flow_logic": [
                {"columns": [{"name": "Col1", "type": "INT"}]},
                {"columns": [{"name": "Col1", "type": "INT"}]}  # Duplicate
            ]
        }
    }
    
    columns = knowledge_service._extract_metadata_columns(metadata)
    assert len(columns) == 1


# ============================================
# Test: DDL Column Map Building
# ============================================

def test_build_ddl_column_map(knowledge_service, sample_schema_reference):
    """Test building DDL column map from schema_reference."""
    referenced_tables = ["dbo.Customers"]
    ddl_map = knowledge_service._build_ddl_column_map(sample_schema_reference, referenced_tables)
    
    assert "customerid" in ddl_map
    assert ddl_map["customerid"]["data_type"] == "INT"
    assert ddl_map["customerid"]["is_primary_key"] is True
    
    assert "email" in ddl_map
    assert ddl_map["email"]["data_type"] == "VARCHAR(100)"


def test_build_ddl_column_map_no_match(knowledge_service, sample_schema_reference):
    """Test with table not in schema_reference."""
    referenced_tables = ["dbo.NonExistent"]
    ddl_map = knowledge_service._build_ddl_column_map(sample_schema_reference, referenced_tables)
    
    assert len(ddl_map) == 0


# ============================================
# Test: Type Resolution Priority
# ============================================

@pytest.mark.asyncio
async def test_resolve_column_types_ddl_priority(knowledge_service, sample_asset, sample_profiled_columns, sample_schema_reference):
    """Test that DDL types have highest priority."""
    metadata = sample_asset["metadata"]
    source_intelligence = {
        "source_query": "SELECT * FROM dbo.Customers"
    }
    
    resolved = await knowledge_service._resolve_column_types(
        metadata, sample_profiled_columns, sample_schema_reference, source_intelligence
    )
    
    # CustomerID should use DDL type (INT from schema_reference)
    customer_id = next((col for col in resolved if col.name == "CustomerID"), None)
    assert customer_id is not None
    assert customer_id.source_type == "INT"
    assert customer_id.is_pk is True
    assert customer_id.resolution_source == "ddl"
    
    # FirstName should use DDL type
    first_name = next((col for col in resolved if col.name == "FirstName"), None)
    assert first_name is not None
    assert first_name.source_type == "VARCHAR(50)"
    assert first_name.resolution_source == "ddl"


@pytest.mark.asyncio
async def test_resolve_column_types_profiled_fallback(knowledge_service, sample_asset, sample_profiled_columns):
    """Test fallback to profiled types when DDL not available."""
    metadata = sample_asset["metadata"]
    source_intelligence = {"source_query": None}
    schema_ref = {}  # No DDL
    
    resolved = await knowledge_service._resolve_column_types(
        metadata, sample_profiled_columns, schema_ref, source_intelligence
    )
    
    # Email should use profiled type
    email = next((col for col in resolved if col.name == "Email"), None)
    assert email is not None
    assert email.source_type == "varchar"
    assert email.is_pii is True
    assert email.pii_category == "email"
    assert email.resolution_source == "profiled"


@pytest.mark.asyncio
async def test_resolve_column_types_metadata_fallback(knowledge_service, sample_asset):
    """Test fallback to metadata types when DDL and profiled not available."""
    metadata = sample_asset["metadata"]
    source_intelligence = {"source_query": None}
    schema_ref = {}
    profiled = []
    
    resolved = await knowledge_service._resolve_column_types(
        metadata, profiled, schema_ref, source_intelligence
    )
    
    # Should use metadata types (INT from SSIS parser)
    customer_id = next((col for col in resolved if col.name == "CustomerID"), None)
    assert customer_id is not None
    assert customer_id.source_type == "INT"
    assert customer_id.resolution_source == "metadata"


@pytest.mark.asyncio
async def test_resolve_column_types_string_fallback(knowledge_service):
    """Test fallback to STRING when no type information available."""
    metadata = {
        "logical_medulla": {
            "columns": [{"name": "UnknownCol"}]  # No type
        }
    }
    source_intelligence = {"source_query": None}
    
    resolved = await knowledge_service._resolve_column_types(
        metadata, [], {}, source_intelligence
    )
    
    unknown = next((col for col in resolved if col.name == "UnknownCol"), None)
    assert unknown is not None
    assert unknown.source_type == "STRING"
    assert unknown.resolution_source == "fallback"


# ============================================
# Test: PII Detection
# ============================================

def test_identify_pii_from_profiling(knowledge_service, sample_profiled_columns):
    """Test PII identification from profiled data."""
    columns = [
        ColumnKnowledge(name="Email", source_type="varchar", is_pii=True, pii_category="email")
    ]
    
    pii_cols, masking_rules = knowledge_service._identify_pii(columns, sample_profiled_columns)
    
    assert "Email" in pii_cols
    assert masking_rules is not None
    assert "email_mask" in masking_rules["Email"]


def test_identify_pii_heuristic_ssn(knowledge_service):
    """Test heuristic PII detection for SSN."""
    columns = [
        ColumnKnowledge(name="SSN", source_type="varchar", is_pii=False)
    ]
    
    pii_cols, masking_rules = knowledge_service._identify_pii(columns, [])
    
    assert "SSN" in pii_cols
    assert masking_rules["SSN"] == "sha256"


def test_identify_pii_heuristic_phone(knowledge_service):
    """Test heuristic PII detection for phone."""
    columns = [
        ColumnKnowledge(name="PhoneNumber", source_type="varchar", is_pii=False)
    ]
    
    pii_cols, masking_rules = knowledge_service._identify_pii(columns, [])
    
    assert "PhoneNumber" in pii_cols
    assert masking_rules["PhoneNumber"] == "phone_mask"


def test_identify_pii_heuristic_credit_card(knowledge_service):
    """Test heuristic PII detection for credit card."""
    columns = [
        ColumnKnowledge(name="CreditCardNumber", source_type="varchar", is_pii=False)
    ]
    
    pii_cols, masking_rules = knowledge_service._identify_pii(columns, [])
    
    assert "CreditCardNumber" in pii_cols
    assert masking_rules["CreditCardNumber"] == "cc_mask"


def test_identify_pii_no_pii(knowledge_service):
    """Test with no PII columns."""
    columns = [
        ColumnKnowledge(name="ProductID", source_type="int", is_pii=False)
    ]
    
    pii_cols, masking_rules = knowledge_service._identify_pii(columns, [])
    
    assert len(pii_cols) == 0
    assert masking_rules is None


# ============================================
# Test: Source Intelligence Extraction
# ============================================

@pytest.mark.asyncio
async def test_extract_source_intelligence(knowledge_service, sample_asset):
    """Test extraction of source intelligence from metadata (Zero-Hardcode v4.0)."""
    metadata = sample_asset["metadata"]
    intelligence = await knowledge_service._extract_source_intelligence(metadata)
    
    # Should extract source query
    assert intelligence["source_query"] is not None
    assert "SELECT" in intelligence["source_query"]
    assert "dbo.Customers" in intelligence["source_query"]
    
    # Should extract connections
    assert len(intelligence["connections"]) == 1
    assert intelligence["connections"][0].connection_name == "SourceDB"
    assert intelligence["connections"][0].server == "sql-server-01"
    
    # Should extract transformations
    assert len(intelligence["transformations"]) == 2
    assert any(t.type == "DERIVEDCOLUMN" for t in intelligence["transformations"])
    assert any(t.type == "LOOKUP" for t in intelligence["transformations"])
    
    # Should calculate complexity
    assert intelligence["complexity_score"] > 0


def test_extract_intelligence_dynamic(knowledge_service):
    """
    Test data-driven intelligence extraction (Zero-Hardcode architecture).
    
    This method replaces all tech-specific _extract_{tech}_intelligence() methods.
    """
    medulla = {
        "data_flow_logic": [
            {
                "type": "OleDbSource",
                "name": "Source",
                "raw_properties": {"SqlCommand": "SELECT * FROM dbo.Customers"}
            },
            {
                "type": "DerivedColumn",
                "name": "AddFullName",
                "raw_properties": {"Expression": "FirstName + ' ' + LastName"}
            },
            {
                "type": "Lookup",
                "name": "LookupCustomerType",
                "raw_properties": {}
            }
        ]
    }
    
    config = {
        "main_key": "data_flow_logic",
        "sql_keys": ["SqlCommand", "OpenRowset"],
        "transformation_types": ["DerivedColumn", "Lookup"],
        "complexity_weights": {
            "oledbsource": 1,
            "derivedcolumn": 2,
            "lookup": 3
        }
    }
    
    # Extract intelligence using config
    source_query, transformations, complexity = knowledge_service._extract_intelligence_dynamic(medulla, config)
    
    # Verify SQL extraction
    assert source_query == "SELECT * FROM dbo.Customers"
    
    # Verify transformations
    assert len(transformations) == 2
    assert any(t.type == "DERIVEDCOLUMN" for t in transformations)
    assert any(t.type == "LOOKUP" for t in transformations)
    
    # Verify complexity calculation (1 + 2 + 3 = 6)
    assert complexity == 6


def test_extract_intelligence_dynamic_generic(knowledge_service):
    """Test generic extraction with unknown tech config."""
    medulla = {
        "components": [
            {"type": "Source", "name": "GenericSource", "sql_query": "SELECT 1"},
            {"type": "Transform", "name": "GenericTransform"}
        ]
    }
    
    config = {
        "main_key": "components",
        "sql_keys": ["sql_query", "query"],
        "transformation_types": [],
        "complexity_weights": {"default": 2}
    }
    
    source_query, transformations, complexity = knowledge_service._extract_intelligence_dynamic(medulla, config)
    
    assert source_query == "SELECT 1"
    assert complexity == 4  # 2 components * weight 2


# ============================================
# Test: End-to-End get_packet()
# ============================================

@pytest.mark.asyncio
async def test_get_packet_full_flow(knowledge_service, sample_asset, sample_profiled_columns, sample_schema_reference):
    """Test complete get_packet() flow with all data sources."""
    
    # Mock all data fetchers
    with patch.object(knowledge_service, '_get_asset', return_value=sample_asset):
        with patch.object(knowledge_service, '_get_profiled_columns', return_value=sample_profiled_columns):
            with patch.object(knowledge_service, '_get_column_mappings', return_value=[]):
                with patch.object(knowledge_service, '_get_business_context', return_value="Customer dimension table"):
                    with patch.object(knowledge_service, '_load_schema_reference', return_value=sample_schema_reference):
                        with patch.object(knowledge_service, '_get_table_impacts', return_value=[]):
                            
                            packet = await knowledge_service.get_packet("asset-123")
                            
                            # Verify packet structure
                            assert packet.object_id == "asset-123"
                            assert packet.source_name == "LoadCustomers.dtsx"
                            assert packet.source_tech == "SSIS"
                            
                            # Verify columns resolved
                            assert len(packet.columns) > 0
                            
                            # Verify source intelligence
                            assert packet.source_query is not None
                            assert len(packet.transformations) == 2
                            assert len(packet.source_connections) == 1
                            assert packet.complexity_score > 0
                            
                            # Verify business context
                            assert packet.business_context == "Customer dimension table"
                            
                            # Verify PII detection
                            assert "Email" in packet.pii_columns
                            assert packet.masking_rules is not None


@pytest.mark.asyncio
async def test_get_packet_asset_not_found(knowledge_service):
    """Test get_packet() with non-existent asset."""
    
    with patch.object(knowledge_service, '_get_asset', return_value=None):
        with pytest.raises(ValueError, match="Asset not found"):
            await knowledge_service.get_packet("nonexistent")


# ============================================
# Test: Project Scanning
# ============================================

@pytest.mark.asyncio
async def test_scan_project(knowledge_service, sample_schema_reference):
    """Test project-level scanning."""
    
    # Mock data
    assets = [
        {"object_id": "asset-1", "name": "Asset1.dtsx", "source_tech": "SSIS"},
        {"object_id": "asset-2", "name": "Asset2.dtsx", "source_tech": "SSIS"},
        {"object_id": "asset-3", "name": "Asset3.dtsx", "source_tech": "SSIS"}
    ]
    
    profiled_1 = [{"column_name": "Col1", "is_pii": True}]
    profiled_2 = [{"column_name": "Col2", "is_pii": False}]
    
    with patch.object(knowledge_service, '_load_schema_reference', return_value=sample_schema_reference):
        with patch.object(knowledge_service.db.client, 'table') as mock_table:
            mock_query = MagicMock()
            mock_query.select.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.execute.return_value.data = assets
            mock_table.return_value = mock_query
            
            with patch.object(knowledge_service, '_get_profiled_columns', side_effect=[profiled_1, profiled_2, []]):
                
                result = await knowledge_service.scan_project("project-123")
                
                assert result["total_assets"] == 3
                assert result["assets_with_ddl_types"] == 3  # All have DDL (schema_reference exists)
                assert result["assets_with_profiled_types"] == 2
                assert result["pii_columns_detected"] == 1
                assert "summary" in result


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
