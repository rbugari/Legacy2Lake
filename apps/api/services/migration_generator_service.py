"""
MigrationGeneratorService - Sprint 10: Schema Evolution

Purpose: Generate automatic migration scripts (DDL/SQL) based on schema changes
detected between versions. Supports multiple platforms (PySpark, Snowflake, etc.)
and handles complex scenarios like type conversions and data migrations.

This service enables:
- Automatic ALTER TABLE script generation
- Multi-platform DDL support (Spark SQL, Snowflake, PostgreSQL)
- Rollback script generation
- Data migration scripts for type changes
- Dependency ordering for complex migrations

Author: UTM Platform Team
Created: February 11, 2026
Sprint: 10 (Schema Evolution)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from apps.api.services.schema_version_service import SchemaChange, SchemaSnapshot


class Platform(Enum):
    """Supported data platforms for migration generation."""
    PYSPARK = "pyspark"
    SNOWFLAKE = "snowflake"
    POSTGRESQL = "postgresql"
    DATABRICKS = "databricks"
    MS_FABRIC = "fabric"
    GCP_BIGQUERY = "gcp"
    AWS_REDSHIFT = "aws"


@dataclass
class MigrationScript:
    """Represents a generated migration script."""
    platform: Platform
    forward_sql: str  # Script to apply changes
    rollback_sql: str  # Script to undo changes
    description: str
    breaking: bool
    requires_data_migration: bool = False
    data_migration_sql: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "forward_sql": self.forward_sql,
            "rollback_sql": self.rollback_sql,
            "description": self.description,
            "breaking": self.breaking,
            "requires_data_migration": self.requires_data_migration,
            "data_migration_sql": self.data_migration_sql
        }


class MigrationGeneratorService:
    """
    Service for generating database migration scripts based on schema changes.
    
    This service analyzes SchemaChange objects and generates appropriate DDL
    statements for different data platforms. It handles:
    - Column additions/removals
    - Type modifications with data conversion
    - Constraint changes (PK, FK, nullable)
    - Rollback scripts for safe deployment
    - Platform-specific SQL dialect
    
    Usage:
        generator = MigrationGeneratorService(platform=Platform.PYSPARK)
        
        # Generate migration from changes
        script = generator.generate_migration(
            table_name="customers",
            changes=detected_changes
        )
        
        # Generate multi-version migration
        full_migration = await generator.generate_version_migration(
            asset_id="asset-123",
            from_version=1,
            to_version=3
        )
    """
    
    def __init__(self, platform: Platform = Platform.PYSPARK):
        """
        Initialize MigrationGeneratorService.
        
        Args:
            platform: Target platform for migration scripts
        """
        self.platform = platform
        
        # Platform-specific type mappings
        self._type_mappings = {
            Platform.PYSPARK: {
                "string": "STRING",
                "integer": "INT",
                "long": "BIGINT",
                "double": "DOUBLE",
                "boolean": "BOOLEAN",
                "date": "DATE",
                "timestamp": "TIMESTAMP",
                "decimal": "DECIMAL(18,2)"
            },
            Platform.SNOWFLAKE: {
                "string": "VARCHAR",
                "integer": "NUMBER(10,0)",
                "long": "NUMBER(19,0)",
                "double": "FLOAT",
                "boolean": "BOOLEAN",
                "date": "DATE",
                "timestamp": "TIMESTAMP_NTZ",
                "decimal": "NUMBER(18,2)"
            },
            Platform.POSTGRESQL: {
                "string": "TEXT",
                "integer": "INTEGER",
                "long": "BIGINT",
                "double": "DOUBLE PRECISION",
                "boolean": "BOOLEAN",
                "date": "DATE",
                "timestamp": "TIMESTAMP",
                "decimal": "NUMERIC(18,2)"
            }
        }
    
    def generate_migration(
        self,
        table_name: str,
        changes: List[SchemaChange],
        catalog: str = "main",
        schema: str = "bronze"
    ) -> MigrationScript:
        """
        Generate a complete migration script from a list of changes.
        
        Args:
            table_name: Name of the table to migrate
            changes: List of SchemaChange objects
            catalog: Catalog/database name (default 'main')
            schema: Schema name (default 'bronze')
            
        Returns:
            MigrationScript with forward and rollback SQL
        """
        full_table_name = f"{catalog}.{schema}.{table_name}"
        
        forward_statements = []
        rollback_statements = []
        description_parts = []
        has_breaking = False
        requires_data_migration = False
        data_migration_parts = []
        
        # Sort changes by type for proper ordering
        ordered_changes = self._order_changes(changes)
        
        for change in ordered_changes:
            forward_sql, rollback_sql = self._generate_change_sql(
                full_table_name, change
            )
            
            if forward_sql:
                forward_statements.append(forward_sql)
                description_parts.append(change.description)
            
            if rollback_sql:
                rollback_statements.insert(0, rollback_sql)  # Reverse order
            
            if change.is_breaking:
                has_breaking = True
            
            # Check if data migration needed (type changes)
            if change.change_type == "modified" and "type" in str(change.old_value):
                requires_data_migration = True
                data_migration_sql = self._generate_data_migration_sql(
                    full_table_name, change
                )
                if data_migration_sql:
                    data_migration_parts.append(data_migration_sql)
        
        # Build final script
        forward_sql = ";\n\n".join(forward_statements) + ";"
        rollback_sql = ";\n\n".join(rollback_statements) + ";" if rollback_statements else None
        description = " | ".join(description_parts)
        
        data_migration_full = "\n\n".join(data_migration_parts) if data_migration_parts else None
        
        return MigrationScript(
            platform=self.platform,
            forward_sql=forward_sql,
            rollback_sql=rollback_sql,
            description=description,
            breaking=has_breaking,
            requires_data_migration=requires_data_migration,
            data_migration_sql=data_migration_full
        )
    
    def _generate_change_sql(
        self,
        table_name: str,
        change: SchemaChange
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Generate SQL for a single schema change.
        
        Args:
            table_name: Fully qualified table name
            change: SchemaChange object
            
        Returns:
            Tuple of (forward_sql, rollback_sql)
        """
        if change.change_type == "added":
            return self._generate_add_column_sql(table_name, change)
        elif change.change_type == "removed":
            return self._generate_remove_column_sql(table_name, change)
        elif change.change_type == "modified":
            return self._generate_modify_column_sql(table_name, change)
        else:
            return None, None
    
    def _generate_add_column_sql(
        self,
        table_name: str,
        change: SchemaChange
    ) -> tuple[str, str]:
        """Generate SQL for adding a column."""
        new_col = change.new_value
        col_name = change.column_name
        col_type = self._map_type(new_col.get("data_type", "string"))
        nullable = "NULL" if new_col.get("nullable", True) else "NOT NULL"
        default = f"DEFAULT {new_col['default_value']}" if new_col.get("default_value") else ""
        
        if self.platform == Platform.PYSPARK:
            forward = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} {default}"
            rollback = f"ALTER TABLE {table_name} DROP COLUMN {col_name}"
        elif self.platform == Platform.SNOWFLAKE:
            forward = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} {nullable} {default}"
            rollback = f"ALTER TABLE {table_name} DROP COLUMN {col_name}"
        elif self.platform == Platform.POSTGRESQL:
            forward = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} {nullable} {default}"
            rollback = f"ALTER TABLE {table_name} DROP COLUMN {col_name}"
        else:
            forward = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
            rollback = f"ALTER TABLE {table_name} DROP COLUMN {col_name}"
        
        return forward.strip(), rollback.strip()
    
    def _generate_remove_column_sql(
        self,
        table_name: str,
        change: SchemaChange
    ) -> tuple[str, str]:
        """Generate SQL for removing a column."""
        col_name = change.column_name
        old_col = change.old_value
        col_type = self._map_type(old_col.get("data_type", "string"))
        nullable = "NULL" if old_col.get("nullable", True) else "NOT NULL"
        
        forward = f"ALTER TABLE {table_name} DROP COLUMN {col_name}"
        
        # Rollback: add the column back
        if self.platform == Platform.PYSPARK:
            rollback = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
        else:
            rollback = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} {nullable}"
        
        return forward, rollback
    
    def _generate_modify_column_sql(
        self,
        table_name: str,
        change: SchemaChange
    ) -> tuple[Optional[str], Optional[str]]:
        """Generate SQL for modifying a column."""
        col_name = change.column_name
        old_val = change.old_value
        new_val = change.new_value
        
        # Type change
        if "type" in old_val and "type" in new_val:
            old_type = self._map_type(old_val["type"])
            new_type = self._map_type(new_val["type"])
            
            if self.platform == Platform.PYSPARK:
                # Spark requires ALTER COLUMN ... TYPE
                forward = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} TYPE {new_type}"
                rollback = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} TYPE {old_type}"
            elif self.platform == Platform.SNOWFLAKE:
                forward = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET DATA TYPE {new_type}"
                rollback = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET DATA TYPE {old_type}"
            elif self.platform == Platform.POSTGRESQL:
                forward = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} TYPE {new_type}"
                rollback = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} TYPE {old_type}"
            else:
                forward = f"ALTER TABLE {table_name} MODIFY COLUMN {col_name} {new_type}"
                rollback = f"ALTER TABLE {table_name} MODIFY COLUMN {col_name} {old_type}"
            
            return forward, rollback
        
        # Nullable change
        if "nullable" in old_val and "nullable" in new_val:
            old_nullable = old_val["nullable"]
            new_nullable = new_val["nullable"]
            
            if self.platform == Platform.PYSPARK:
                if new_nullable:
                    forward = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} DROP NOT NULL"
                    rollback = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET NOT NULL"
                else:
                    forward = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET NOT NULL"
                    rollback = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} DROP NOT NULL"
            elif self.platform == Platform.SNOWFLAKE:
                constraint = "NULL" if new_nullable else "NOT NULL"
                rollback_constraint = "NULL" if old_nullable else "NOT NULL"
                forward = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET {constraint}"
                rollback = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET {rollback_constraint}"
            elif self.platform == Platform.POSTGRESQL:
                if new_nullable:
                    forward = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} DROP NOT NULL"
                    rollback = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET NOT NULL"
                else:
                    forward = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET NOT NULL"
                    rollback = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} DROP NOT NULL"
            else:
                return None, None
            
            return forward, rollback
        
        # Primary key change
        if "primary_key" in old_val and "primary_key" in new_val:
            # PK changes are complex and often require recreating the table
            # For now, generate warnings
            forward = f"-- WARNING: Primary key change on {col_name} requires manual intervention"
            rollback = f"-- WARNING: Rollback for primary key change requires manual intervention"
            return forward, rollback
        
        return None, None
    
    def _generate_data_migration_sql(
        self,
        table_name: str,
        change: SchemaChange
    ) -> Optional[str]:
        """
        Generate data migration SQL for type conversions.
        
        When changing column types, data may need to be transformed.
        This generates UPDATE statements to convert existing data.
        
        Args:
            table_name: Fully qualified table name
            change: SchemaChange with type modification
            
        Returns:
            SQL statement for data migration, or None if not needed
        """
        if change.change_type != "modified" or "type" not in str(change.old_value):
            return None
        
        col_name = change.column_name
        old_type = change.old_value.get("type")
        new_type = change.new_value.get("type")
        
        # Generate type-specific conversions
        conversion_map = {
            ("string", "integer"): f"CAST({col_name} AS INT)",
            ("string", "double"): f"CAST({col_name} AS DOUBLE)",
            ("integer", "string"): f"CAST({col_name} AS STRING)",
            ("double", "integer"): f"CAST({col_name} AS INT)",
            ("string", "timestamp"): f"TO_TIMESTAMP({col_name})",
            ("string", "date"): f"TO_DATE({col_name})"
        }
        
        conversion = conversion_map.get((old_type, new_type))
        
        if conversion:
            return f"""-- Data migration for {col_name} type change
UPDATE {table_name}
SET {col_name} = {conversion}
WHERE {col_name} IS NOT NULL"""
        
        return None
    
    def _map_type(self, generic_type: str) -> str:
        """Map generic type to platform-specific type."""
        type_map = self._type_mappings.get(self.platform, {})
        return type_map.get(generic_type, generic_type.upper())
    
    def _order_changes(self, changes: List[SchemaChange]) -> List[SchemaChange]:
        """
        Order changes for safe execution.
        
        Order:
        1. Remove columns (DROP)
        2. Add columns (ADD)
        3. Modify columns (ALTER)
        
        This ensures dependencies are handled correctly.
        """
        remove_changes = [c for c in changes if c.change_type == "removed"]
        add_changes = [c for c in changes if c.change_type == "added"]
        modify_changes = [c for c in changes if c.change_type == "modified"]
        
        return remove_changes + add_changes + modify_changes
    
    def generate_rollback_plan(
        self,
        migration_scripts: List[MigrationScript]
    ) -> str:
        """
        Generate a complete rollback plan for multiple migrations.
        
        Args:
            migration_scripts: List of MigrationScript objects to rollback
            
        Returns:
            Complete rollback SQL script in reverse order
        """
        rollback_parts = []
        
        # Reverse order for rollback
        for script in reversed(migration_scripts):
            if script.rollback_sql:
                rollback_parts.append(f"-- Rollback: {script.description}")
                rollback_parts.append(script.rollback_sql)
                rollback_parts.append("")
        
        return "\n".join(rollback_parts)
    
    def estimate_migration_risk(
        self,
        changes: List[SchemaChange]
    ) -> Dict[str, Any]:
        """
        Estimate risk level for a migration.
        
        Args:
            changes: List of SchemaChange objects
            
        Returns:
            Risk assessment dictionary with score and recommendations
        """
        risk_score = 0
        warnings = []
        
        for change in changes:
            if change.is_breaking:
                risk_score += 10
                warnings.append(f"BREAKING: {change.description}")
            
            if change.change_type == "removed":
                risk_score += 8
                warnings.append(f"HIGH RISK: Column removal - {change.column_name}")
            
            if change.change_type == "modified" and "type" in str(change.old_value):
                risk_score += 7
                warnings.append(f"MEDIUM RISK: Type change - {change.column_name}")
            
            if change.change_type == "modified" and "primary_key" in str(change.old_value):
                risk_score += 15
                warnings.append(f"CRITICAL: Primary key change - {change.column_name}")
        
        # Determine risk level
        if risk_score == 0:
            level = "LOW"
            recommendation = "Safe to deploy automatically"
        elif risk_score < 10:
            level = "MEDIUM"
            recommendation = "Review migration before deployment"
        elif risk_score < 20:
            level = "HIGH"
            recommendation = "Requires manual review and testing"
        else:
            level = "CRITICAL"
            recommendation = "Requires DBA approval and maintenance window"
        
        return {
            "risk_score": risk_score,
            "risk_level": level,
            "recommendation": recommendation,
            "warnings": warnings,
            "breaking_change_count": len([c for c in changes if c.is_breaking]),
            "total_changes": len(changes)
        }
