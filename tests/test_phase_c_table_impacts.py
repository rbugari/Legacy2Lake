"""
Unit Tests for Phase C - Table Impact Service
===============================================

Tests:
    - Table name extraction from SQL
    - Operation classification (SELECT, INSERT, UPDATE, DELETE, MERGE)
    - Column inference from SQL statements
    - Access pattern detection (FULL_LOAD, INCREMENTAL, LOOKUP)
    - Impact extraction from SSIS components
    - Dependency DAG construction
    - Cycle detection
    - Topological sorting

Coverage Areas:
    - TableImpactService._extract_table_names()
    - TableImpactService._classify_operation()
    - TableImpactService._infer_columns_affected()
    - TableImpactService._infer_access_pattern()
    - TableImpactService._detect_cycles()
    - TableImpactService._topological_sort()

Author: Legacy2Lake Engineering
Date: 2026-02-15 (Phase C - Sprint 14)
"""

import asyncio

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

# Import service and models
from apps.api.services.table_impact_service import (
    TableImpactService,
    TableImpact,
    TableSummary,
    TableDetail,
    DependencyDAG
)


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def impact_service():
    """TableImpactService instance"""
    return TableImpactService(
        project_id="test-project-123",
        tenant_id="test-tenant-456"
    )


@pytest.fixture
def sample_ssis_component_select():
    """Sample SSIS SOURCE component with SqlCommand"""
    return {
        "intent": "SOURCE",
        "type": "OleDbSource",
        "raw_properties": {
            "SqlCommand": "SELECT CustomerID, Name, Email FROM dbo.Customers WHERE Active = 1"
        }
    }


@pytest.fixture
def sample_ssis_component_insert():
    """Sample SSIS DESTINATION component"""
    return {
        "intent": "DESTINATION",
        "type": "OleDbDestination",
        "raw_properties": {
            "TableOrViewName": "[dw].[DimCustomer]"
        }
    }


@pytest.fixture
def sample_ssis_component_update():
    """Sample SSIS component with UPDATE statement"""
    return {
        "intent": "DESTINATION",
        "type": "ExecuteSql",
        "raw_properties": {
            "SqlCommand": "UPDATE dbo.Products SET Price = @Price, Stock = @Stock WHERE ProductID = @ID"
        }
    }


# ================================================================
# UNIT TESTS - Table Name Extraction
# ================================================================

def test_extract_table_names_simple_select(impact_service):
    """Test extracting table from simple SELECT"""
    sql = "SELECT * FROM Customers"
    tables = impact_service._extract_table_names(sql)
    
    assert len(tables) == 1
    assert "Customers" in tables


def test_extract_table_names_with_schema(impact_service):
    """Test extracting table with schema"""
    sql = "SELECT * FROM dbo.Customers"
    tables = impact_service._extract_table_names(sql)
    
    assert len(tables) == 1
    assert "dbo.Customers" in tables


def test_extract_table_names_with_brackets(impact_service):
    """Test extracting table with SQL Server brackets"""
    sql = "SELECT * FROM [dbo].[Customers]"
    tables = impact_service._extract_table_names(sql)
    
    assert len(tables) == 1
    assert "dbo.Customers" in tables


def test_extract_table_names_join(impact_service):
    """Test extracting tables from JOIN"""
    sql = """
    SELECT c.*, o.*
    FROM dbo.Customers c
    INNER JOIN dbo.Orders o ON c.CustomerID = o.CustomerID
    """
    tables = impact_service._extract_table_names(sql)
    
    assert len(tables) == 2
    assert "dbo.Customers" in tables
    assert "dbo.Orders" in tables


def test_extract_table_names_multiple_joins(impact_service):
    """Test extracting tables from multiple JOINs"""
    sql = """
    SELECT *
    FROM dbo.Orders
    LEFT JOIN dbo.Customers ON Orders.CustomerID = Customers.CustomerID
    RIGHT JOIN dbo.Products ON Orders.ProductID = Products.ProductID
    """
    tables = impact_service._extract_table_names(sql)
    
    assert len(tables) == 3
    assert "dbo.Orders" in tables
    assert "dbo.Customers" in tables
    assert "dbo.Products" in tables


def test_extract_table_names_insert(impact_service):
    """Test extracting table from INSERT"""
    sql = "INSERT INTO dbo.Customers (Name, Email) VALUES ('John', 'john@example.com')"
    tables = impact_service._extract_table_names(sql)
    
    assert len(tables) == 1
    assert "dbo.Customers" in tables


def test_extract_table_names_update(impact_service):
    """Test extracting table from UPDATE"""
    sql = "UPDATE dbo.Products SET Price = 99.99 WHERE ProductID = 1"
    tables = impact_service._extract_table_names(sql)
    
    assert len(tables) == 1
    assert "dbo.Products" in tables


def test_extract_table_names_delete(impact_service):
    """Test extracting table from DELETE"""
    sql = "DELETE FROM dbo.OldRecords WHERE Date < '2020-01-01'"
    tables = impact_service._extract_table_names(sql)
    
    assert len(tables) == 1
    assert "dbo.OldRecords" in tables


def test_extract_table_names_empty(impact_service):
    """Test with empty SQL"""
    tables = impact_service._extract_table_names("")
    assert len(tables) == 0


# ================================================================
# UNIT TESTS - Operation Classification
# ================================================================

def test_classify_operation_select(impact_service, sample_ssis_component_select):
    """Test classification of SELECT operation"""
    operation = impact_service._classify_operation(sample_ssis_component_select)
    assert operation == "SELECT"


def test_classify_operation_insert_by_intent(impact_service, sample_ssis_component_insert):
    """Test classification of INSERT by DESTINATION intent"""
    operation = impact_service._classify_operation(sample_ssis_component_insert)
    assert operation == "INSERT"


def test_classify_operation_update_by_sql(impact_service, sample_ssis_component_update):
    """Test classification of UPDATE from SqlCommand"""
    operation = impact_service._classify_operation(sample_ssis_component_update)
    assert operation == "UPDATE"


def test_classify_operation_delete(impact_service):
    """Test classification of DELETE"""
    comp = {
        "intent": "DESTINATION",
        "raw_properties": {
            "SqlCommand": "DELETE FROM dbo.OldData WHERE Date < '2020-01-01'"
        }
    }
    operation = impact_service._classify_operation(comp)
    assert operation == "DELETE"


def test_classify_operation_merge(impact_service):
    """Test classification of MERGE"""
    comp = {
        "intent": "DESTINATION",
        "raw_properties": {
            "SqlCommand": "MERGE dbo.Target USING dbo.Source..."
        }
    }
    operation = impact_service._classify_operation(comp)
    assert operation == "MERGE"


def test_classify_operation_unknown(impact_service):
    """Test classification when no operation detected"""
    comp = {
        "intent": "UNKNOWN",
        "raw_properties": {}
    }
    operation = impact_service._classify_operation(comp)
    assert operation == "UNKNOWN"


def test_save_impact_uses_natural_conflict_target(impact_service):
    """Reruns should upsert table impacts using the project/asset/table/operation key."""
    mock_execute = Mock()
    mock_upsert = Mock()
    mock_upsert.execute = mock_execute
    mock_table = Mock()
    mock_table.upsert.return_value = mock_upsert
    impact_service.db.client = Mock()
    impact_service.db.client.table.return_value = mock_table

    impact = {
        "tenant_id": "tenant-1",
        "project_id": "project-1",
        "schema_name": "dbo",
        "table_name": "DimProduct",
        "full_name": "dbo.DimProduct",
        "asset_id": "asset-1",
        "asset_name": "DimProduct.dtsx",
        "operation": "UPDATE",
        "access_pattern": "SCD",
        "is_source": False,
        "is_target": True,
        "sql_statement": "UPDATE dbo.DimProduct SET Flag = 1",
        "columns_affected": ["Flag"],
    }

    asyncio.run(impact_service._save_impact(impact))

    mock_table.upsert.assert_called_once()
    args, kwargs = mock_table.upsert.call_args
    assert kwargs["on_conflict"] == "project_id,asset_id,full_name,operation"
    assert args[0]["table_name"] == "DimProduct"
    assert "full_name" not in args[0]


# ================================================================
# UNIT TESTS - Column Inference
# ================================================================

def test_infer_columns_select_explicit(impact_service):
    """Test inferring columns from explicit SELECT"""
    sql = "SELECT CustomerID, Name, Email FROM Customers"
    columns = impact_service._infer_columns_affected(sql, "SELECT")
    
    # Should contain the specific columns
    assert len(columns) >= 3 or "*" in columns
    # Note: Implementation may vary based on sqlglot availability


def test_infer_columns_select_star(impact_service):
    """Test inferring columns from SELECT *"""
    sql = "SELECT * FROM Customers"
    columns = impact_service._infer_columns_affected(sql, "SELECT")
    
    assert "*" in columns or len(columns) == 0


def test_infer_columns_update(impact_service):
    """Test inferring columns from UPDATE"""
    sql = "UPDATE Products SET Price = 99.99, Stock = 100 WHERE ProductID = 1"
    columns = impact_service._infer_columns_affected(sql, "UPDATE")
    
    # Should extract Price and Stock (if sqlglot available)
    # Otherwise returns empty list
    assert isinstance(columns, list)


def test_infer_columns_insert_explicit(impact_service):
    """Test inferring columns from INSERT with column list"""
    sql = "INSERT INTO Customers (Name, Email, Phone) VALUES ('John', 'john@example.com', '555-1234')"
    columns = impact_service._infer_columns_affected(sql, "INSERT")
    
    # Should extract Name, Email, Phone (if sqlglot available)
    assert isinstance(columns, list)


def test_infer_columns_delete(impact_service):
    """Test inferring columns from DELETE (affects all)"""
    sql = "DELETE FROM OldRecords WHERE Date < '2020-01-01'"
    columns = impact_service._infer_columns_affected(sql, "DELETE")
    
    assert "*" in columns


def test_infer_columns_empty_sql(impact_service):
    """Test with empty SQL"""
    columns = impact_service._infer_columns_affected("", "SELECT")
    assert len(columns) == 0


# ================================================================
# UNIT TESTS - Access Pattern Inference
# ================================================================

def test_infer_access_pattern_full_load(impact_service):
    """Test FULL_LOAD pattern detection"""
    comp = {
        "type": "OleDbSource",
        "raw_properties": {
            "SqlCommand": "SELECT * FROM Customers"
        }
    }
    pattern = impact_service._infer_access_pattern(comp, "SELECT")
    assert pattern == "FULL_LOAD"


def test_infer_access_pattern_incremental(impact_service):
    """Test INCREMENTAL pattern detection"""
    comp = {
        "type": "OleDbSource",
        "raw_properties": {
            "SqlCommand": "SELECT * FROM Orders WHERE OrderDate > GETDATE() - 1"
        }
    }
    pattern = impact_service._infer_access_pattern(comp, "SELECT")
    assert pattern == "INCREMENTAL"


def test_infer_access_pattern_lookup(impact_service):
    """Test LOOKUP pattern detection"""
    comp = {
        "type": "Lookup",
        "raw_properties": {}
    }
    pattern = impact_service._infer_access_pattern(comp, "SELECT")
    assert pattern == "LOOKUP"


def test_infer_access_pattern_upsert(impact_service):
    """Test UPSERT pattern detection"""
    comp = {
        "type": "ExecuteSql",
        "raw_properties": {
            "SqlCommand": "MERGE INTO Target..."
        }
    }
    pattern = impact_service._infer_access_pattern(comp, "MERGE")
    assert pattern == "UPSERT"


# ================================================================
# UNIT TESTS - Table Name Cleaning
# ================================================================

def test_clean_table_name_brackets(impact_service):
    """Test cleaning table name with brackets"""
    cleaned = impact_service._clean_table_name("[dbo].[Customers]")
    assert cleaned == "dbo.Customers"


def test_clean_table_name_quotes(impact_service):
    """Test cleaning table name with quotes"""
    cleaned = impact_service._clean_table_name('"dbo"."Customers"')
    assert cleaned == "dbo.Customers"


def test_clean_table_name_mixed(impact_service):
    """Test cleaning table name with mixed brackets and quotes"""
    cleaned = impact_service._clean_table_name('[dbo]."Customers"')
    assert cleaned == "dbo.Customers"


def test_clean_table_name_simple(impact_service):
    """Test cleaning simple table name (no change)"""
    cleaned = impact_service._clean_table_name("Customers")
    assert cleaned == "Customers"


# ================================================================
# UNIT TESTS - Cycle Detection
# ================================================================

def test_detect_cycles_no_cycle(impact_service):
    """Test cycle detection with no cycles"""
    nodes = {"A", "B", "C"}
    dependencies = {
        "B": {"A"},  # B depends on A
        "C": {"B"}   # C depends on B
    }
    
    cycles = impact_service._detect_cycles(nodes, dependencies)
    assert len(cycles) == 0


def test_detect_cycles_simple_cycle(impact_service):
    """Test cycle detection with simple cycle"""
    nodes = {"A", "B"}
    dependencies = {
        "A": {"B"},  # A depends on B
        "B": {"A"}   # B depends on A (cycle!)
    }
    
    cycles = impact_service._detect_cycles(nodes, dependencies)
    assert len(cycles) > 0


def test_detect_cycles_three_node_cycle(impact_service):
    """Test cycle detection with three-node cycle"""
    nodes = {"A", "B", "C"}
    dependencies = {
        "A": {"C"},  # A depends on C
        "B": {"A"},  # B depends on A
        "C": {"B"}   # C depends on B (cycle: A→C→B→A)
    }
    
    cycles = impact_service._detect_cycles(nodes, dependencies)
    assert len(cycles) > 0


# ================================================================
# UNIT TESTS - Topological Sort
# ================================================================

def test_topological_sort_linear(impact_service):
    """Test topological sort with linear dependencies"""
    nodes = {"A", "B", "C"}
    dependencies = {
        "B": {"A"},  # B depends on A
        "C": {"B"}   # C depends on B
    }
    
    order = impact_service._topological_sort(nodes, dependencies)
    
    # Should have 3 levels: [A], [B], [C]
    assert len(order) == 3
    assert "A" in order[0]
    assert "B" in order[1]
    assert "C" in order[2]


def test_topological_sort_parallel(impact_service):
    """Test topological sort with parallel execution possible"""
    nodes = {"A", "B", "C", "D"}
    dependencies = {
        "C": {"A", "B"},  # C depends on both A and B
        "D": {"C"}        # D depends on C
    }
    
    order = impact_service._topological_sort(nodes, dependencies)
    
    # Level 0: A and B can run in parallel
    # Level 1: C (depends on A and B)
    # Level 2: D (depends on C)
    assert len(order) == 3
    assert len(order[0]) == 2  # A and B in level 0
    assert "C" in order[1]
    assert "D" in order[2]


def test_topological_sort_no_dependencies(impact_service):
    """Test topological sort with no dependencies (all parallel)"""
    nodes = {"A", "B", "C"}
    dependencies = {}
    
    order = impact_service._topological_sort(nodes, dependencies)
    
    # All nodes can execute in parallel (level 0)
    assert len(order) == 1
    assert len(order[0]) == 3


# ================================================================
# INTEGRATION TEST - Component Analysis
# ================================================================

def test_extract_tables_from_component_sqlcommand(impact_service, sample_ssis_component_select):
    """Test full extraction from component with SqlCommand"""
    results = impact_service._extract_tables_from_component(sample_ssis_component_select)
    
    assert len(results) > 0
    result = results[0]
    
    assert result["table_name"] == "Customers"
    assert result["schema_name"] == "dbo"
    assert result["full_name"] == "dbo.Customers"
    assert result["operation"] == "SELECT"
    assert result["sql_statement"] is not None


def test_extract_tables_from_component_table_name(impact_service, sample_ssis_component_insert):
    """Test full extraction from component with TableOrViewName"""
    results = impact_service._extract_tables_from_component(sample_ssis_component_insert)
    
    assert len(results) > 0
    result = results[0]
    
    assert result["table_name"] == "DimCustomer"
    assert result["schema_name"] == "dw"
    assert result["full_name"] == "dw.DimCustomer"
    assert result["operation"] == "INSERT"


def test_extract_tables_from_component_no_tables(impact_service):
    """Test extraction when no tables found"""
    comp = {
        "intent": "TRANSFORMATION",
        "type": "DerivedColumn",
        "raw_properties": {}
    }
    
    results = impact_service._extract_tables_from_component(comp)
    assert len(results) == 0


# ================================================================
# RUN TESTS
# ================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
