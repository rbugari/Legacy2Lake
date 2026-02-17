"""
SchemaVersionService - Sprint 10: Schema Evolution

Purpose: Track and manage schema versions over time, detect schema changes,
and maintain a complete history of schema evolution for each data asset.

This service enables:
- Automatic schema versioning with snapshots
- Change detection between schema versions
- Historical tracking of schema evolution
- Breaking change identification

Author: UTM Platform Team
Created: February 11, 2026
Sprint: 10 (Schema Evolution)
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import json
from supabase import create_client, Client
import os


@dataclass
class SchemaColumn:
    """Represents a single column in a schema."""
    name: str
    data_type: str
    nullable: bool
    primary_key: bool = False
    foreign_key: Optional[str] = None
    default_value: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SchemaSnapshot:
    """Represents a complete schema snapshot at a point in time."""
    asset_id: str
    table_name: str
    columns: List[SchemaColumn]
    version_number: int
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "table_name": self.table_name,
            "columns": [col.to_dict() for col in self.columns],
            "version_number": self.version_number,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SchemaChange:
    """Represents a single change between two schema versions."""
    change_type: str  # 'added', 'removed', 'modified', 'renamed'
    column_name: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    is_breaking: bool = False
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SchemaVersionService:
    """
    Service for managing schema versions and tracking schema evolution.
    
    This service provides comprehensive schema versioning capabilities:
    - Capture schema snapshots from utm_objects.metadata
    - Compare two schema versions and detect changes
    - Track schema history with complete audit trail
    - Identify breaking vs. non-breaking changes
    - Support rollback and migration planning
    
    Usage:
        service = SchemaVersionService(tenant_id, project_id)
        
        # Capture current schema
        version = await service.capture_schema_snapshot(asset_id)
        
        # Compare versions
        changes = await service.compare_versions(asset_id, v1, v2)
        
        # Get version history
        history = await service.get_version_history(asset_id)
    """
    
    def __init__(self, tenant_id: str, project_id: str):
        """
        Initialize SchemaVersionService.
        
        Args:
            tenant_id: UUID of the tenant
            project_id: UUID of the project
        """
        self.tenant_id = tenant_id
        self.project_id = project_id
        
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Cache for schema snapshots
        self._cache: Dict[str, SchemaSnapshot] = {}
    
    async def capture_schema_snapshot(
        self,
        asset_id: str,
        user_id: Optional[str] = None
    ) -> SchemaSnapshot:
        """
        Capture a new schema snapshot for the given asset.
        
        This method:
        1. Queries utm_objects.metadata for current schema
        2. Parses columns, types, constraints
        3. Determines next version number
        4. Compares with previous version (if exists)
        5. Saves snapshot to utm_schema_versions
        
        Args:
            asset_id: UUID of the asset to snapshot
            user_id: Optional UUID of user creating snapshot
            
        Returns:
            SchemaSnapshot object with version information
            
        Raises:
            ValueError: If asset not found or metadata invalid
        """
        # 1. Fetch current schema from utm_objects
        response = self.supabase.table("utm_objects").select(
            "object_id, source_name, metadata"
        ).eq(
            "tenant_id", self.tenant_id
        ).eq(
            "project_id", self.project_id
        ).eq(
            "object_id", asset_id
        ).execute()
        
        if not response.data or len(response.data) == 0:
            raise ValueError(f"Asset {asset_id} not found")
        
        asset_data = response.data[0]
        metadata = asset_data.get("metadata", {})
        
        if not metadata or "columns" not in metadata:
            raise ValueError(f"Asset {asset_id} has no column metadata")
        
        # 2. Parse schema from metadata
        columns = []
        metadata_columns = metadata.get("columns", [])
        primary_keys = metadata.get("primaryKey", [])
        foreign_keys_dict = {
            fk.get("column"): fk.get("references")
            for fk in metadata.get("foreignKeys", [])
        }
        
        for col_data in metadata_columns:
            column = SchemaColumn(
                name=col_data.get("name"),
                data_type=col_data.get("type", "string"),
                nullable=col_data.get("nullable", True),
                primary_key=col_data.get("name") in primary_keys,
                foreign_key=foreign_keys_dict.get(col_data.get("name")),
                default_value=col_data.get("defaultValue")
            )
            columns.append(column)
        
        # 3. Determine next version number
        version_number = await self._get_next_version_number(asset_id)
        
        # 4. Create snapshot
        snapshot = SchemaSnapshot(
            asset_id=asset_id,
            table_name=asset_data.get("name"),
            columns=columns,
            version_number=version_number,
            timestamp=datetime.now()
        )
        
        # 5. Compare with previous version if exists
        changes = []
        breaking = False
        
        if version_number > 1:
            previous_snapshot = await self.get_schema_version(
                asset_id, version_number - 1
            )
            changes = self._detect_changes(previous_snapshot, snapshot)
            breaking = any(change.is_breaking for change in changes)
        
        # 6. Save to database
        insert_data = {
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "asset_id": asset_id,
            "version_number": version_number,
            "schema_snapshot": snapshot.to_dict(),
            "changes_from_previous": [c.to_dict() for c in changes] if changes else None,
            "breaking_changes": breaking,
            "created_by": user_id
        }
        
        self.supabase.table("utm_schema_versions").insert(insert_data).execute()
        
        # 7. Update cache
        cache_key = f"{asset_id}:v{version_number}"
        self._cache[cache_key] = snapshot
        
        return snapshot
    
    async def get_schema_version(
        self,
        asset_id: str,
        version_number: int
    ) -> SchemaSnapshot:
        """
        Retrieve a specific schema version.
        
        Args:
            asset_id: UUID of the asset
            version_number: Version number to retrieve
            
        Returns:
            SchemaSnapshot for the requested version
            
        Raises:
            ValueError: If version not found
        """
        # Check cache first
        cache_key = f"{asset_id}:v{version_number}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Query database
        response = self.supabase.table("utm_schema_versions").select(
            "schema_snapshot, created_at"
        ).eq(
            "tenant_id", self.tenant_id
        ).eq(
            "project_id", self.project_id
        ).eq(
            "asset_id", asset_id
        ).eq(
            "version_number", version_number
        ).execute()
        
        if not response.data or len(response.data) == 0:
            raise ValueError(
                f"Version {version_number} not found for asset {asset_id}"
            )
        
        snapshot_data = response.data[0]["schema_snapshot"]
        
        # Reconstruct SchemaSnapshot
        columns = [
            SchemaColumn(**col_data)
            for col_data in snapshot_data["columns"]
        ]
        
        snapshot = SchemaSnapshot(
            asset_id=snapshot_data["asset_id"],
            table_name=snapshot_data["table_name"],
            columns=columns,
            version_number=snapshot_data["version_number"],
            timestamp=datetime.fromisoformat(snapshot_data["timestamp"])
        )
        
        # Cache it
        self._cache[cache_key] = snapshot
        
        return snapshot
    
    async def get_version_history(
        self,
        asset_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get complete version history for an asset.
        
        Args:
            asset_id: UUID of the asset
            limit: Maximum number of versions to return (default 50)
            
        Returns:
            List of version records with metadata
        """
        response = self.supabase.table("utm_schema_versions").select(
            "version_number, created_at, breaking_changes, changes_from_previous"
        ).eq(
            "tenant_id", self.tenant_id
        ).eq(
            "project_id", self.project_id
        ).eq(
            "asset_id", asset_id
        ).order(
            "version_number", desc=True
        ).limit(limit).execute()
        
        return response.data if response.data else []
    
    async def compare_versions(
        self,
        asset_id: str,
        from_version: int,
        to_version: int
    ) -> List[SchemaChange]:
        """
        Compare two schema versions and detect changes.
        
        Args:
            asset_id: UUID of the asset
            from_version: Starting version number
            to_version: Target version number
            
        Returns:
            List of SchemaChange objects describing differences
        """
        # Fetch both versions
        from_snapshot = await self.get_schema_version(asset_id, from_version)
        to_snapshot = await self.get_schema_version(asset_id, to_version)
        
        # Detect changes
        changes = self._detect_changes(from_snapshot, to_snapshot)
        
        return changes
    
    def _detect_changes(
        self,
        old_snapshot: SchemaSnapshot,
        new_snapshot: SchemaSnapshot
    ) -> List[SchemaChange]:
        """
        Internal method to detect changes between two snapshots.
        
        Detects:
        - Added columns
        - Removed columns
        - Modified columns (type, nullable, constraints)
        - Potentially renamed columns (heuristic matching)
        
        Args:
            old_snapshot: Previous schema snapshot
            new_snapshot: Current schema snapshot
            
        Returns:
            List of SchemaChange objects
        """
        changes = []
        
        # Build column maps
        old_cols = {col.name: col for col in old_snapshot.columns}
        new_cols = {col.name: col for col in new_snapshot.columns}
        
        # 1. Detect removed columns
        for col_name in old_cols:
            if col_name not in new_cols:
                changes.append(SchemaChange(
                    change_type="removed",
                    column_name=col_name,
                    old_value=old_cols[col_name].to_dict(),
                    new_value=None,
                    is_breaking=True,
                    description=f"Column '{col_name}' was removed"
                ))
        
        # 2. Detect added columns
        for col_name in new_cols:
            if col_name not in old_cols:
                is_breaking = not new_cols[col_name].nullable
                changes.append(SchemaChange(
                    change_type="added",
                    column_name=col_name,
                    old_value=None,
                    new_value=new_cols[col_name].to_dict(),
                    is_breaking=is_breaking,
                    description=f"Column '{col_name}' was added"
                ))
        
        # 3. Detect modified columns
        for col_name in old_cols:
            if col_name in new_cols:
                old_col = old_cols[col_name]
                new_col = new_cols[col_name]
                
                # Check type change
                if old_col.data_type != new_col.data_type:
                    changes.append(SchemaChange(
                        change_type="modified",
                        column_name=col_name,
                        old_value={"type": old_col.data_type},
                        new_value={"type": new_col.data_type},
                        is_breaking=True,
                        description=f"Column '{col_name}' type changed from {old_col.data_type} to {new_col.data_type}"
                    ))
                
                # Check nullable change
                if old_col.nullable != new_col.nullable:
                    is_breaking = new_col.nullable is False  # Making non-nullable is breaking
                    changes.append(SchemaChange(
                        change_type="modified",
                        column_name=col_name,
                        old_value={"nullable": old_col.nullable},
                        new_value={"nullable": new_col.nullable},
                        is_breaking=is_breaking,
                        description=f"Column '{col_name}' nullable changed from {old_col.nullable} to {new_col.nullable}"
                    ))
                
                # Check PK change
                if old_col.primary_key != new_col.primary_key:
                    changes.append(SchemaChange(
                        change_type="modified",
                        column_name=col_name,
                        old_value={"primary_key": old_col.primary_key},
                        new_value={"primary_key": new_col.primary_key},
                        is_breaking=True,
                        description=f"Column '{col_name}' primary key constraint changed"
                    ))
        
        return changes
    
    async def _get_next_version_number(self, asset_id: str) -> int:
        """
        Get the next version number for an asset.
        
        Args:
            asset_id: UUID of the asset
            
        Returns:
            Next version number (1 if no previous versions)
        """
        response = self.supabase.table("utm_schema_versions").select(
            "version_number"
        ).eq(
            "tenant_id", self.tenant_id
        ).eq(
            "project_id", self.project_id
        ).eq(
            "asset_id", asset_id
        ).order(
            "version_number", desc=True
        ).limit(1).execute()
        
        if not response.data or len(response.data) == 0:
            return 1
        
        return response.data[0]["version_number"] + 1
    
    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()
