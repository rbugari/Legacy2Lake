"""
Schema Metadata Service - Sprint 9
===================================

Purpose:
    Retrieves schema metadata from utm_objects table.
    Provides column names, data types, foreign keys, primary keys,
    and sample data for zero-hardcode code generation.

Features:
    - Query utm_objects.metadata (JSONB)
    - Extract columns list with types
    - Identify primary keys
    - Identify foreign keys
    - Get sample data from metadata
    - Cache results for performance

Usage:
    schema_service = SchemaMetadataService(tenant_id, project_id)
    
    # Get table schema
    schema = await schema_service.get_table_schema(asset_id)
    
    # Access schema properties
    columns = schema['columns']  # [{'name': 'customer_id', 'type': 'int', 'nullable': False}, ...]
    pk = schema['primary_key']  # ['customer_id']
    fks = schema['foreign_keys']  # [{'column': 'order_id', 'ref_table': 'orders', 'ref_column': 'id'}]

Integration:
    - Used by Agent C for schema-aware code generation
    - Used by Parameter Extractor for table resolution
    - Used by Template Engine for dynamic column references

Author: Legacy2Lake Engineering
Date: 2026-02-11 (Sprint 9)
Version: v1.0
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

try:
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.utils.logger import logger
except ImportError:
    from services.persistence_service import SupabasePersistence
    from utils.logger import logger


# ================================================================
# DATA CLASSES
# ================================================================

@dataclass
class ColumnMetadata:
    """Column metadata"""
    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_ref: Optional[Dict[str, str]] = None  # {'table': 'orders', 'column': 'id'}
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    default_value: Optional[str] = None


@dataclass
class ForeignKeyMetadata:
    """Foreign key metadata"""
    column: str
    ref_table: str
    ref_column: str
    constraint_name: Optional[str] = None


@dataclass
class TableSchema:
    """Complete table schema"""
    asset_id: str
    table_name: str
    source_name: str
    source_type: str  # 'SSIS', 'SQL_PROC', 'INFORMATICA', etc.
    columns: List[ColumnMetadata] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    foreign_keys: List[ForeignKeyMetadata] = field(default_factory=list)
    row_count: Optional[int] = None
    sample_data: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ================================================================
# SCHEMA METADATA SERVICE
# ================================================================

class SchemaMetadataService:
    """
    Service for retrieving schema metadata from utm_objects.
    Provides schema information for zero-hardcode code generation.
    """
    
    def __init__(self, tenant_id: Optional[str] = None, project_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.project_id = project_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=None)
        self._cache: Dict[str, TableSchema] = {}
    
    
    async def get_table_schema(self, asset_id: str, use_cache: bool = True) -> TableSchema:
        """
        Get table schema from utm_objects.
        
        Args:
            asset_id: UUID of asset in utm_objects
            use_cache: If True, use cached schema if available
        
        Returns:
            TableSchema with columns, primary key, foreign keys, etc.
        """
        # Check cache
        if use_cache and asset_id in self._cache:
            logger.info(f"[SchemaMetadata] Using cached schema for asset_id={asset_id}", "SchemaMetadata")
            return self._cache[asset_id]
        
        logger.info(f"[SchemaMetadata] Fetching schema for asset_id={asset_id}", "SchemaMetadata")
        
        # Query utm_objects
        response = self.db.client.table("utm_objects") \
            .select("object_id, source_name, source_tech, type, metadata") \
            .eq("object_id", asset_id) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise ValueError(f"Asset not found: {asset_id}")
        
        asset_data = response.data[0]
        
        # Parse metadata
        metadata = asset_data.get("metadata", {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        
        # Extract schema
        schema = self._parse_metadata(
            asset_id=asset_data["object_id"],
            source_name=asset_data["source_name"],
            source_type=asset_data.get("source_tech", "UNKNOWN"),
            metadata=metadata
        )
        
        # Cache
        self._cache[asset_id] = schema
        
        logger.info(
            f"[SchemaMetadata] Schema loaded: {schema.table_name}, "
            f"{len(schema.columns)} columns, PK={schema.primary_key}",
            "SchemaMetadata"
        )
        
        return schema
    
    
    async def get_project_tables(self, project_id: Optional[str] = None) -> List[TableSchema]:
        """
        Get all table schemas for a project.
        
        Args:
            project_id: Project ID (defaults to self.project_id)
        
        Returns:
            List of TableSchema objects
        """
        project_id = project_id or self.project_id
        
        if not project_id:
            raise ValueError("project_id required")
        
        logger.info(f"[SchemaMetadata] Fetching project tables: project_id={project_id}", "SchemaMetadata")
        
        # Query all assets for project
        response = self.db.client.table("utm_objects") \
            .select("object_id, source_name, source_tech, type, metadata") \
            .eq("project_id", project_id) \
            .execute()
        
        if not response.data:
            logger.warning(f"[SchemaMetadata] No tables found for project: {project_id}", "SchemaMetadata")
            return []
        
        # Parse all schemas
        schemas = []
        for asset_data in response.data:
            metadata = asset_data.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            
            schema = self._parse_metadata(
                asset_id=asset_data["object_id"],
                source_name=asset_data["source_name"],
                source_type=asset_data.get("source_tech", "UNKNOWN"),
                metadata=metadata
            )
            
            schemas.append(schema)
            self._cache[asset_data["object_id"]] = schema
        
        logger.info(f"[SchemaMetadata] Loaded {len(schemas)} table schemas", "SchemaMetadata")
        
        return schemas
    
    
    def _parse_metadata(
        self,
        asset_id: str,
        source_name: str,
        source_type: str,
        metadata: Dict[str, Any]
    ) -> TableSchema:
        """
        Parse utm_objects.metadata JSONB into TableSchema.
        
        Metadata structure (from Agent A forensic triage):
        {
            "columns": [
                {
                    "name": "customer_id",
                    "type": "int",
                    "nullable": false,
                    "maxLength": null,
                    "precision": null,
                    "scale": null
                }
            ],
            "primaryKey": ["customer_id"],
            "foreignKeys": [
                {"name": "fk_order_customer", "column": "customer_id", "refTable": "Customers", "refColumn": "customer_id"}
            ],
            "rowCount": 1000000,
            "sampleData": [
                {"customer_id": 1, "name": "Alice"},
                {"customer_id": 2, "name": "Bob"}
            ]
        }
        """
        # Extract columns
        columns_raw = metadata.get("columns", [])
        columns = []
        
        for col_data in columns_raw:
            column = ColumnMetadata(
                name=col_data.get("name", "unknown_column"),
                data_type=col_data.get("type", "string"),
                nullable=col_data.get("nullable", True),
                max_length=col_data.get("maxLength"),
                precision=col_data.get("precision"),
                scale=col_data.get("scale"),
                default_value=col_data.get("defaultValue")
            )
            columns.append(column)
        
        # Extract primary key
        primary_key = metadata.get("primaryKey", [])
        if isinstance(primary_key, str):
            primary_key = [primary_key]
        
        # Mark PK columns
        for pk_col in primary_key:
            for col in columns:
                if col.name == pk_col:
                    col.is_primary_key = True
        
        # Extract foreign keys
        foreign_keys_raw = metadata.get("foreignKeys", [])
        foreign_keys = []
        
        for fk_data in foreign_keys_raw:
            fk = ForeignKeyMetadata(
                column=fk_data.get("column", ""),
                ref_table=fk_data.get("refTable", ""),
                ref_column=fk_data.get("refColumn", ""),
                constraint_name=fk_data.get("name")
            )
            foreign_keys.append(fk)
            
            # Mark FK columns
            for col in columns:
                if col.name == fk.column:
                    col.is_foreign_key = True
                    col.foreign_key_ref = {
                        'table': fk.ref_table,
                        'column': fk.ref_column
                    }
        
        # Extract row count
        row_count = metadata.get("rowCount")
        
        # Extract sample data
        sample_data = metadata.get("sampleData", [])
        
        # Build TableSchema
        schema = TableSchema(
            asset_id=asset_id,
            table_name=source_name,
            source_name=source_name,
            source_type=source_type,
            columns=columns,
            primary_key=primary_key,
            foreign_keys=foreign_keys,
            row_count=row_count,
            sample_data=sample_data,
            metadata=metadata
        )
        
        return schema
    
    
    def get_column_names(self, schema: TableSchema, exclude_audit: bool = True) -> List[str]:
        """
        Get list of column names from schema.
        
        Args:
            schema: TableSchema object
            exclude_audit: If True, exclude audit columns (_ingestion_*, _source_*, etc.)
        
        Returns:
            List of column names
        """
        column_names = [col.name for col in schema.columns]
        
        if exclude_audit:
            audit_prefixes = ['_ingestion_', '_source_', '_audit_', '_delta_']
            column_names = [
                name for name in column_names
                if not any(name.startswith(prefix) for prefix in audit_prefixes)
            ]
        
        return column_names
    
    
    def get_column_types_map(self, schema: TableSchema) -> Dict[str, str]:
        """
        Get dictionary mapping column names to data types.
        
        Args:
            schema: TableSchema object
        
        Returns:
            Dict like {'customer_id': 'int', 'name': 'string', ...}
        """
        return {col.name: col.data_type for col in schema.columns}
    
    
    def infer_join_conditions(
        self,
        left_schema: TableSchema,
        right_schema: TableSchema
    ) -> Optional[Dict[str, Any]]:
        """
        Infer join conditions between two tables based on foreign keys.
        
        Args:
            left_schema: Left table schema
            right_schema: Right table schema
        
        Returns:
            Dict with join information or None if no FK relationship found
            {
                'left_column': 'customer_id',
                'right_column': 'id',
                'join_type': 'LEFT'
            }
        """
        # Check if left has FK to right
        for fk in left_schema.foreign_keys:
            if fk.ref_table.lower() == right_schema.table_name.lower():
                return {
                    'left_column': fk.column,
                    'right_column': fk.ref_column,
                    'join_type': 'LEFT',
                    'constraint_name': fk.constraint_name
                }
        
        # Check if right has FK to left
        for fk in right_schema.foreign_keys:
            if fk.ref_table.lower() == left_schema.table_name.lower():
                return {
                    'left_column': fk.ref_column,
                    'right_column': fk.column,
                    'join_type': 'LEFT',
                    'constraint_name': fk.constraint_name
                }
        
        # No FK relationship found
        return None
    
    
    def clear_cache(self):
        """Clear schema cache"""
        self._cache.clear()
        logger.info("[SchemaMetadata] Cache cleared", "SchemaMetadata")
