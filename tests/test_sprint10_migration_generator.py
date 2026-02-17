"""
Test Suite for Sprint 10: Schema Evolution - MigrationGeneratorService

Tests SQL/DDL migration script generation for multiple platforms,
rollback script generation, data migration scripts, and risk assessment.

Author: UTM Platform Team
Created: February 11, 2026
Sprint: 10 (Schema Evolution)
"""

import pytest
from migration_generator_service import (
    MigrationGeneratorService,
    Platform,
    MigrationScript
)
from schema_version_service import SchemaChange


class TestMigrationGeneratorService:
    """Test suite for MigrationGeneratorService."""
    
    @pytest.fixture
    def service_pyspark(self):
        """PySpark migration generator."""
        return MigrationGeneratorService(platform=Platform.PYSPARK)
    
    @pytest.fixture
    def service_snowflake(self):
        """Snowflake migration generator."""
        return MigrationGeneratorService(platform=Platform.SNOWFLAKE)
    
    @pytest.fixture
    def service_postgresql(self):
        """PostgreSQL migration generator."""
        return MigrationGeneratorService(platform=Platform.POSTGRESQL)
    
    @pytest.fixture
    def sample_add_column_change(self):
        """Sample schema change: add column."""
        return SchemaChange(
            change_type="added",
            column_name="email",
            old_value=None,
            new_value={
                "data_type": "string",
                "nullable": True,
                "default_value": None
            },
            is_breaking=False,
            description="Column 'email' was added"
        )
    
    @pytest.fixture
    def sample_remove_column_change(self):
        """Sample schema change: remove column."""
        return SchemaChange(
            change_type="removed",
            column_name="old_field",
            old_value={
                "data_type": "string",
                "nullable": True
            },
            new_value=None,
            is_breaking=True,
            description="Column 'old_field' was removed"
        )
    
    @pytest.fixture
    def sample_type_change(self):
        """Sample schema change: type modification."""
        return SchemaChange(
            change_type="modified",
            column_name="age",
            old_value={"type": "string"},
            new_value={"type": "integer"},
            is_breaking=True,
            description="Column 'age' type changed from string to integer"
        )


# ============================================================
# TEST 1: Generate ADD COLUMN (PySpark)
# ============================================================
def test_generate_add_column_pyspark(service_pyspark, sample_add_column_change):
    """Test generating ADD COLUMN for PySpark."""
    
    migration = service_pyspark.generate_migration(
        table_name="customers",
        changes=[sample_add_column_change],
        catalog="main",
        schema="bronze"
    )
    
    assert "ALTER TABLE main.bronze.customers" in migration.forward_sql
    assert "ADD COLUMN email STRING" in migration.forward_sql
    assert "DROP COLUMN email" in migration.rollback_sql
    assert migration.breaking == False


# ============================================================
# TEST 2: Generate ADD COLUMN (Snowflake)
# ============================================================
def test_generate_add_column_snowflake(service_snowflake, sample_add_column_change):
    """Test generating ADD COLUMN for Snowflake."""
    
    migration = service_snowflake.generate_migration(
        table_name="customers",
        changes=[sample_add_column_change]
    )
    
    assert "ALTER TABLE" in migration.forward_sql
    assert "ADD COLUMN email VARCHAR" in migration.forward_sql
    assert "NULL" in migration.forward_sql  # Nullable specified in Snowflake
    assert migration.breaking == False


# ============================================================
# TEST 3: Generate DROP COLUMN (Breaking)
# ============================================================
def test_generate_drop_column(service_pyspark, sample_remove_column_change):
    """Test generating DROP COLUMN (breaking change)."""
    
    migration = service_pyspark.generate_migration(
        table_name="customers",
        changes=[sample_remove_column_change]
    )
    
    assert "DROP COLUMN old_field" in migration.forward_sql
    assert "ADD COLUMN old_field" in migration.rollback_sql  # Rollback re-adds
    assert migration.breaking == True


# ============================================================
# TEST 4: Generate ALTER COLUMN TYPE (PySpark)
# ============================================================
def test_generate_alter_type_pyspark(service_pyspark, sample_type_change):
    """Test generating type change for PySpark."""
    
    migration = service_pyspark.generate_migration(
        table_name="users",
        changes=[sample_type_change]
    )
    
    assert "ALTER COLUMN age TYPE INT" in migration.forward_sql
    assert "ALTER COLUMN age TYPE STRING" in migration.rollback_sql
    assert migration.breaking == True
    assert migration.requires_data_migration == True


# ============================================================
# TEST 5: Generate ALTER COLUMN TYPE (Snowflake)
# ============================================================
def test_generate_alter_type_snowflake(service_snowflake, sample_type_change):
    """Test generating type change for Snowflake."""
    
    migration = service_snowflake.generate_migration(
        table_name="users",
        changes=[sample_type_change]
    )
    
    assert "ALTER COLUMN age SET DATA TYPE" in migration.forward_sql
    assert "NUMBER" in migration.forward_sql  # Snowflake uses NUMBER for integers


# ============================================================
# TEST 6: Generate Nullable Change (NOT NULL)
# ============================================================
def test_generate_nullable_change(service_pyspark):
    """Test generating nullable constraint change."""
    
    nullable_change = SchemaChange(
        change_type="modified",
        column_name="email",
        old_value={"nullable": True},
        new_value={"nullable": False},
        is_breaking=True,
        description="Column 'email' now NOT NULL"
    )
    
    migration = service_pyspark.generate_migration(
        table_name="users",
        changes=[nullable_change]
    )
    
    assert "SET NOT NULL" in migration.forward_sql
    assert "DROP NOT NULL" in migration.rollback_sql


# ============================================================
# TEST 7: Multiple Changes (Correct Ordering)
# ============================================================
def test_multiple_changes_ordering(service_pyspark):
    """Test that changes are ordered correctly (DROP → ADD → ALTER)."""
    
    changes = [
        SchemaChange("added", "new_col", None, {"data_type": "string", "nullable": True}, False, "Added new_col"),
        SchemaChange("removed", "old_col", {"data_type": "string"}, None, True, "Removed old_col"),
        SchemaChange("modified", "age", {"type": "string"}, {"type": "integer"}, True, "Type changed")
    ]
    
    migration = service_pyspark.generate_migration(
        table_name="users",
        changes=changes
    )
    
    # Verify order: DROP first, then ADD, then ALTER
    sql_parts = migration.forward_sql.split(";\n\n")
    
    # First statement should be DROP
    assert "DROP COLUMN old_col" in sql_parts[0]
    
    # Second should be ADD
    assert "ADD COLUMN new_col" in sql_parts[1]
    
    # Third should be ALTER
    assert "ALTER COLUMN age" in sql_parts[2]


# ============================================================
# TEST 8: Data Migration SQL Generation
# ============================================================
def test_data_migration_sql_generation(service_pyspark):
    """Test data migration SQL for type conversions."""
    
    type_change = SchemaChange(
        change_type="modified",
        column_name="age",
        old_value={"type": "string"},
        new_value={"type": "integer"},
        is_breaking=True,
        description="Type change"
    )
    
    migration = service_pyspark.generate_migration(
        table_name="users",
        changes=[type_change]
    )
    
    assert migration.requires_data_migration == True
    assert migration.data_migration_sql is not None
    assert "UPDATE" in migration.data_migration_sql
    assert "CAST(age AS INT)" in migration.data_migration_sql


# ============================================================
# TEST 9: Risk Assessment - Low Risk
# ============================================================
def test_risk_assessment_low(service_pyspark):
    """Test risk assessment for low-risk changes."""
    
    low_risk_changes = [
        SchemaChange("added", "email", None, {"data_type": "string", "nullable": True}, False, "Added email")
    ]
    
    risk = service_pyspark.estimate_migration_risk(low_risk_changes)
    
    assert risk["risk_level"] == "LOW"
    assert risk["risk_score"] < 10
    assert "Safe to deploy" in risk["recommendation"]


# ============================================================
# TEST 10: Risk Assessment - High Risk
# ============================================================
def test_risk_assessment_high(service_pyspark):
    """Test risk assessment for high-risk changes."""
    
    high_risk_changes = [
        SchemaChange("removed", "email", {"data_type": "string"}, None, True, "Removed email"),
        SchemaChange("modified", "age", {"type": "string"}, {"type": "integer"}, True, "Type changed")
    ]
    
    risk = service_pyspark.estimate_migration_risk(high_risk_changes)
    
    assert risk["risk_level"] in ["HIGH", "CRITICAL"]
    assert risk["risk_score"] >= 20
    assert len(risk["warnings"]) > 0


# ============================================================
# TEST 11: Rollback Plan Generation
# ============================================================
def test_rollback_plan_generation(service_pyspark):
    """Test generating complete rollback plan."""
    
    migration1 = MigrationScript(
        platform=Platform.PYSPARK,
        forward_sql="ALTER TABLE users ADD COLUMN email STRING",
        rollback_sql="ALTER TABLE users DROP COLUMN email",
        description="Add email column",
        breaking=False
    )
    
    migration2 = MigrationScript(
        platform=Platform.PYSPARK,
        forward_sql="ALTER TABLE users ALTER COLUMN age TYPE INT",
        rollback_sql="ALTER TABLE users ALTER COLUMN age TYPE STRING",
        description="Change age type",
        breaking=True
    )
    
    rollback_plan = service_pyspark.generate_rollback_plan([migration1, migration2])
    
    # Rollback should be in reverse order
    assert "age TYPE STRING" in rollback_plan  # migration2 rollback first
    assert "DROP COLUMN email" in rollback_plan  # migration1 rollback second
    
    # Check order
    age_pos = rollback_plan.find("age TYPE STRING")
    email_pos = rollback_plan.find("DROP COLUMN email")
    assert age_pos < email_pos  # Age rollback appears before email


# ============================================================
# TEST 12: Platform-Specific Type Mapping
# ============================================================
def test_platform_type_mapping(service_pyspark, service_snowflake, service_postgresql):
    """Test that each platform maps types correctly."""
    
    # PySpark
    assert service_pyspark._map_type("string") == "STRING"
    assert service_pyspark._map_type("integer") == "INT"
    
    # Snowflake
    assert service_snowflake._map_type("string") == "VARCHAR"
    assert service_snowflake._map_type("integer") == "NUMBER(10,0)"
    
    # PostgreSQL
    assert service_postgresql._map_type("string") == "TEXT"
    assert service_postgresql._map_type("integer") == "INTEGER"


# ============================================================
# Summary
# ============================================================
"""
Test Coverage Summary:
- ✅ TEST 1: ADD COLUMN (PySpark)
- ✅ TEST 2: ADD COLUMN (Snowflake)
- ✅ TEST 3: DROP COLUMN (breaking)
- ✅ TEST 4: ALTER TYPE (PySpark)
- ✅ TEST 5: ALTER TYPE (Snowflake)
- ✅ TEST 6: Nullable change
- ✅ TEST 7: Multiple changes with correct ordering
- ✅ TEST 8: Data migration SQL generation
- ✅ TEST 9: Risk assessment (low risk)
- ✅ TEST 10: Risk assessment (high risk)
- ✅ TEST 11: Rollback plan generation
- ✅ TEST 12: Platform-specific type mapping

Total: 12 tests for MigrationGeneratorService
"""
