"""
Unit Tests for Technology Cartridges

Test suite for validating cartridge code generation.
Run with: pytest test_cartridges.py
"""

import pytest
from pathlib import Path
from typing import Dict, Any

# Import cartridges
from .base_cartridge import Cartridge
from .pyspark_cartridge import PySparkCartridge
from .snowflake_cartridge import SnowflakeCartridge
from .dbt_cartridge import DbtCartridge
from .ms_fabric_cartridge import MSFabricCartridge


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_table_metadata() -> Dict[str, Any]:
    """Standard table metadata for tests"""
    return {
        "source_path": "customers.py",
        "output_table_name": "dim_customer",
        "pk_columns": ["customer_id"],
        "table_type": "DIMENSION",
        "original_code": "df = spark.read.csv('customers.csv')"
    }


@pytest.fixture
def composite_pk_metadata() -> Dict[str, Any]:
    """Table metadata with composite primary key"""
    return {
        "source_path": "orders.py",
        "output_table_name": "fact_orders",
        "pk_columns": ["order_id", "line_number"],
        "table_type": "FACT"
    }


@pytest.fixture
def sample_registry() -> Dict[str, Any]:
    """Standard design registry for tests"""
    return {
        "naming": {
            "bronze_schema": "bronze_raw",
            "silver_schema": "silver_curated",
            "gold_schema": "gold_business"
        }
    }


# ============================================================================
# Base Cartridge Tests
# ============================================================================

class TestBaseCartridge:
    """Tests for BaseCartridge helper methods"""
    
    def test_pk_validation_none(self):
        """Test PK validation with None input"""
        cartridge = PySparkCartridge("test", {})
        result = cartridge._validate_and_normalize_pk(None)
        assert result == ["id"], "None should default to ['id']"
    
    def test_pk_validation_empty_list(self):
        """Test PK validation with empty list"""
        cartridge = PySparkCartridge("test", {})
        result = cartridge._validate_and_normalize_pk([])
        assert result == ["id"], "Empty list should default to ['id']"
    
    def test_pk_validation_string(self):
        """Test PK validation with string input"""
        cartridge = PySparkCartridge("test", {})
        result = cartridge._validate_and_normalize_pk("customer_id")
        assert result == ["customer_id"], "String should be wrapped in list"
    
    def test_pk_validation_list(self):
        """Test PK validation with valid list"""
        cartridge = PySparkCartridge("test", {})
        result = cartridge._validate_and_normalize_pk(["col_a", "col_b"])
        assert result == ["col_a", "col_b"], "Valid list should pass through"


# ============================================================================
# PySpark Cartridge Tests
# ============================================================================

class TestPySparkCartridge:
    """Tests for PySparkCartridge code generation"""
    
    def test_scaffolding_generation(self, sample_registry):
        """Test scaffolding file generation"""
        cartridge = PySparkCartridge("test_project", sample_registry)
        scaffold = cartridge.generate_scaffolding()
        
        assert "config.py" in scaffold
        assert "utils.py" in scaffold
        assert len(scaffold["config.py"]) > 0
        assert "add_ingestion_metadata" in scaffold["utils.py"]
    
    def test_bronze_generation(self, sample_table_metadata, sample_registry):
        """Test Bronze layer code generation"""
        cartridge = PySparkCartridge("test_project", sample_registry)
        bronze_code = cartridge.generate_bronze(sample_table_metadata)
        
        assert "BRONZE LAYER" in bronze_code
        assert "add_ingestion_metadata" in bronze_code
        assert ".write.format(\"delta\")" in bronze_code
        assert "mergeSchema" in bronze_code  # P1 improvement
    
    def test_silver_generation_single_pk(self, sample_table_metadata, sample_registry):
        """Test Silver layer with single PK"""
        cartridge = PySparkCartridge("test_project", sample_registry)
        silver_code = cartridge.generate_silver(sample_table_metadata)
        
        assert "SILVER LAYER" in silver_code
        assert "customer_id" in silver_code
        assert "MERGE" in silver_code or "merge" in silver_code
    
    def test_silver_generation_composite_pk(self, composite_pk_metadata, sample_registry):
        """Test Silver layer with composite PK"""
        cartridge = PySparkCartridge("test_project", sample_registry)
        silver_code = cartridge.generate_silver(composite_pk_metadata)
        
        assert "order_id" in silver_code
        assert "line_number" in silver_code
        # Should include both PKs in merge condition
    
    def test_gold_generation(self, sample_table_metadata, sample_registry):
        """Test Gold layer code generation"""
        cartridge = PySparkCartridge("test_project", sample_registry)
        gold_code = cartridge.generate_gold(sample_table_metadata)
        
        assert "GOLD LAYER" in gold_code
        assert "DIMENSION" in gold_code


# ============================================================================
# Snowflake Cartridge Tests
# ============================================================================

class TestSnowflakeCartridge:
    """Tests for SnowflakeCartridge code generation"""
    
    def test_scaffolding_generation(self, sample_registry):
        """Test Snowflake scaffolding"""
        cartridge = SnowflakeCartridge("test_project", sample_registry)
        scaffold = cartridge.generate_scaffolding()
        
        assert "config.py" in scaffold
        assert "utils.py" in scaffold
        assert "snowpark" in scaffold["config.py"].lower()
    
    def test_composite_pk_merge(self, composite_pk_metadata, sample_registry):
        """Test composite PK handling (P0 fix)"""
        cartridge = SnowflakeCartridge("test_project", sample_registry)
        silver_code = cartridge.generate_silver(composite_pk_metadata)
        
        # Should build composite merge condition
        assert "merge_conditions" in silver_code or ("order_id" in silver_code and "line_number" in silver_code)
    
    def test_bronze_sql_file_format(self, sample_table_metadata, sample_registry):
        """Test file format detection (P2 improvement)"""
        cartridge = SnowflakeCartridge("test_project", sample_registry)
        
        # Test CSV
        metadata_csv = {**sample_table_metadata, "source_path": "data.csv"}
        sql = cartridge.generate_bronze_sql(metadata_csv)
        assert "CSV" in sql
        
        # TODO: Test other formats when P2 improvement is applied
        # metadata_json = {**sample_table_metadata, "source_path": "data.json"}
        # sql = cartridge.generate_bronze_sql(metadata_json)
        # assert "JSON" in sql


# ============================================================================
# dbt Cartridge Tests
# ============================================================================

class TestDbtCartridge:
    """Tests for DbtCartridge code generation"""
    
    def test_scaffolding_generation(self, sample_registry):
        """Test dbt project scaffolding"""
        cartridge = DbtCartridge("test_project", sample_registry)
        scaffold = cartridge.generate_scaffolding()
        
        assert "dbt_project.yml" in scaffold
        assert "Bronze/sources.yml" in scaffold
    
    def test_silver_deduplication(self, sample_table_metadata, sample_registry):
        """Test improved deduplication (P1 improvement)"""
        cartridge = DbtCartridge("test_project", sample_registry)
        silver_code = cartridge.generate_silver(sample_table_metadata)
         
        # Should use window function, not DISTINCT
        assert "row_number()" in silver_code
        assert "partition by" in silver_code.lower()
        assert "_rn = 1" in silver_code


# ============================================================================
# MS Fabric Cartridge Tests
# ============================================================================

class TestMSFabricCartridge:
    """Tests for MSFabricCartridge code generation"""
    
    def test_scaffolding_generation(self, sample_registry):
        """Test Fabric scaffolding"""
        cartridge = MSFabricCartridge("test_project", sample_registry)
        scaffold = cartridge.generate_scaffolding()
        
        assert "fabric_config.py" in scaffold
        assert "fabric_utils.py" in scaffold
        assert "LAKEHOUSE" in scaffold["fabric_config.py"]
    
    def test_semantic_model_generation(self, sample_table_metadata, sample_registry):
        """Test TMDL semantic model generation"""
        cartridge = MSFabricCartridge("test_project", sample_registry)
        tmdl = cartridge.generate_semantic_model(sample_table_metadata)
        
        assert "table" in tmdl.lower()
        assert "measure" in tmdl.lower()
        assert "Total Records" in tmdl


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests across multiple cartridges"""
    
    def test_all_cartridges_with_same_metadata(self, sample_table_metadata, sample_registry):
        """Test all cartridges process same metadata successfully"""
        cartridges = [
            PySparkCartridge("test", sample_registry),
            SnowflakeCartridge("test", sample_registry),
            DbtCartridge("test", sample_registry),
            MSFabricCartridge("test", sample_registry)
        ]
        
        for cartridge in cartridges:
            # All should generate without errors
            bronze = cartridge.generate_bronze(sample_table_metadata)
            silver = cartridge.generate_silver(sample_table_metadata)
            gold = cartridge.generate_gold(sample_table_metadata)
            
            assert len(bronze) > 0
            assert len(silver) > 0
            assert len(gold) > 0
    
    def test_pk_validation_consistency(self):
        """Test PK validation works consistently across all cartridges"""
        cartridges = [
            PySparkCartridge("test", {}),
            SnowflakeCartridge("test", {}),
            DbtCartridge("test", {}),
            MSFabricCartridge("test", {})
        ]
        
        for cartridge in cartridges:
            # All should normalize None to ["id"]
            assert cartridge._validate_and_normalize_pk(None) == ["id"]
            # All should normalize string to list
            assert cartridge._validate_and_normalize_pk("col_a") == ["col_a"]


# ============================================================================
# TODO: Add more tests
# ============================================================================

"""
Additional test cases to implement:

1. Error handling tests:
   - Invalid metadata structure
   - Missing required fields
   - Invalid PK types (numbers, dicts, etc.)

2. Code validation tests:
   - Generated Python code compiles
   - Generated SQL is syntactically valid
   - Generated YAML parses correctly

3. Orchestration tests:
   - Multiple table dependencies
   - Task ordering correctness

4. Performance tests:
   - Large metadata inputs
   - Many tables batch processing

5. Edge case tests:
   - Unicode characters in table names
   - Very long column lists
   - Nested data structures
"""

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
