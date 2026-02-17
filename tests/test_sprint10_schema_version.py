"""
Test Suite for Sprint 10: Schema Evolution - SchemaVersionService

Tests schema version tracking, snapshot capture, change detection,
and version history management.

Author: UTM Platform Team
Created: February 11, 2026
Sprint: 10 (Schema Evolution)
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from schema_version_service import (
    SchemaVersionService,
    SchemaSnapshot,
    SchemaColumn,
    SchemaChange
)


class TestSchemaVersionService:
    """Test suite for SchemaVersionService."""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        mock = Mock()
        mock.table = Mock(return_value=mock)
        mock.select = Mock(return_value=mock)
        mock.eq = Mock(return_value=mock)
        mock.order = Mock(return_value=mock)
        mock.limit = Mock(return_value=mock)
        mock.insert = Mock(return_value=mock)
        mock.execute = Mock(return_value=Mock(data=[]))
        return mock
    
    @pytest.fixture
    def service(self, mock_supabase):
        """Create SchemaVersionService instance with mocked Supabase."""
        with patch('schema_version_service.create_client', return_value=mock_supabase):
            return SchemaVersionService(
                tenant_id="tenant-123",
                project_id="project-456"
            )
    
    @pytest.fixture
    def sample_asset_data(self):
        """Sample asset metadata."""
        return {
            "id": "asset-789",
            "name": "customers",
            "metadata": {
                "columns": [
                    {"name": "customer_id", "type": "integer", "nullable": False},
                    {"name": "customer_name", "type": "string", "nullable": True},
                    {"name": "email", "type": "string", "nullable": True},
                    {"name": "created_at", "type": "timestamp", "nullable": False}
                ],
                "primaryKey": ["customer_id"],
                "foreignKeys": []
            }
        }


# ============================================================
# TEST 1: Capture Schema Snapshot (First Version)
# ============================================================
@pytest.mark.asyncio
async def test_capture_schema_snapshot_first_version(mock_supabase, service, sample_asset_data):
    """Test capturing initial schema snapshot (version 1)."""
    
    # Mock utm_objects query
    mock_supabase.execute.return_value = Mock(data=[sample_asset_data])
    
    # Mock version number query (no previous versions)
    version_mock = Mock()
    version_mock.execute.return_value = Mock(data=[])
    
    with patch.object(service, '_get_next_version_number', return_value=1):
        snapshot = await service.capture_schema_snapshot("asset-789")
    
    assert snapshot.asset_id == "asset-789"
    assert snapshot.table_name == "customers"
    assert snapshot.version_number == 1
    assert len(snapshot.columns) == 4
    assert snapshot.columns[0].name == "customer_id"
    assert snapshot.columns[0].primary_key == True


# ============================================================
# TEST 2: Capture Schema Snapshot (Subsequent Version)
# ============================================================
@pytest.mark.asyncio
async def test_capture_schema_snapshot_subsequent_version(mock_supabase, service, sample_asset_data):
    """Test capturing schema snapshot when previous version exists."""
    
    # Modified asset data (added new column)
    modified_data = sample_asset_data.copy()
    modified_data["metadata"]["columns"].append({
        "name": "phone_number",
        "type": "string",
        "nullable": True
    })
    
    mock_supabase.execute.return_value = Mock(data=[modified_data])
    
    with patch.object(service, '_get_next_version_number', return_value=2):
        with patch.object(service, 'get_schema_version') as mock_get_version:
            # Mock previous version
            previous_cols = [
                SchemaColumn("customer_id", "integer", False, True),
                SchemaColumn("customer_name", "string", True),
                SchemaColumn("email", "string", True),
                SchemaColumn("created_at", "timestamp", False)
            ]
            previous_snapshot = SchemaSnapshot(
                asset_id="asset-789",
                table_name="customers",
                columns=previous_cols,
                version_number=1,
                timestamp=datetime.now()
            )
            mock_get_version.return_value = previous_snapshot
            
            snapshot = await service.capture_schema_snapshot("asset-789")
    
    assert snapshot.version_number == 2
    assert len(snapshot.columns) == 5  # Added one column


# ============================================================
# TEST 3: Detect Added Column
# ============================================================
def test_detect_changes_added_column(service):
    """Test detection of added columns."""
    
    old_cols = [
        SchemaColumn("id", "integer", False, True),
        SchemaColumn("name", "string", True)
    ]
    new_cols = [
        SchemaColumn("id", "integer", False, True),
        SchemaColumn("name", "string", True),
        SchemaColumn("email", "string", True)  # Added
    ]
    
    old_snapshot = SchemaSnapshot("asset-1", "users", old_cols, 1, datetime.now())
    new_snapshot = SchemaSnapshot("asset-1", "users", new_cols, 2, datetime.now())
    
    changes = service._detect_changes(old_snapshot, new_snapshot)
    
    added = [c for c in changes if c.change_type == "added"]
    assert len(added) == 1
    assert added[0].column_name == "email"
    assert added[0].is_breaking == False  # Nullable addition is non-breaking


# ============================================================
# TEST 4: Detect Removed Column (Breaking)
# ============================================================
def test_detect_changes_removed_column(service):
    """Test detection of removed columns (breaking change)."""
    
    old_cols = [
        SchemaColumn("id", "integer", False, True),
        SchemaColumn("name", "string", True),
        SchemaColumn("email", "string", True)
    ]
    new_cols = [
        SchemaColumn("id", "integer", False, True),
        SchemaColumn("name", "string", True)
        # email removed
    ]
    
    old_snapshot = SchemaSnapshot("asset-1", "users", old_cols, 1, datetime.now())
    new_snapshot = SchemaSnapshot("asset-1", "users", new_cols, 2, datetime.now())
    
    changes = service._detect_changes(old_snapshot, new_snapshot)
    
    removed = [c for c in changes if c.change_type == "removed"]
    assert len(removed) == 1
    assert removed[0].column_name == "email"
    assert removed[0].is_breaking == True


# ============================================================
# TEST 5: Detect Type Change (Breaking)
# ============================================================
def test_detect_changes_type_modification(service):
    """Test detection of type changes (breaking)."""
    
    old_cols = [
        SchemaColumn("id", "integer", False, True),
        SchemaColumn("age", "integer", True)
    ]
    new_cols = [
        SchemaColumn("id", "integer", False, True),
        SchemaColumn("age", "string", True)  # Type changed
    ]
    
    old_snapshot = SchemaSnapshot("asset-1", "users", old_cols, 1, datetime.now())
    new_snapshot = SchemaSnapshot("asset-1", "users", new_cols, 2, datetime.now())
    
    changes = service._detect_changes(old_snapshot, new_snapshot)
    
    modified = [c for c in changes if c.change_type == "modified"]
    assert len(modified) > 0
    type_change = [c for c in modified if "type" in str(c.old_value)]
    assert len(type_change) == 1
    assert type_change[0].is_breaking == True


# ============================================================
# TEST 6: Detect Nullable Change (Breaking if made NOT NULL)
# ============================================================
def test_detect_changes_nullable_modification(service):
    """Test detection of nullable changes."""
    
    old_cols = [
        SchemaColumn("id", "integer", False, True),
        SchemaColumn("email", "string", True)  # Nullable
    ]
    new_cols = [
        SchemaColumn("id", "integer", False, True),
        SchemaColumn("email", "string", False)  # Made NOT NULL
    ]
    
    old_snapshot = SchemaSnapshot("asset-1", "users", old_cols, 1, datetime.now())
    new_snapshot = SchemaSnapshot("asset-1", "users", new_cols, 2, datetime.now())
    
    changes = service._detect_changes(old_snapshot, new_snapshot)
    
    nullable_changes = [
        c for c in changes 
        if c.change_type == "modified" and "nullable" in str(c.old_value)
    ]
    assert len(nullable_changes) == 1
    assert nullable_changes[0].is_breaking == True  # Making NOT NULL is breaking


# ============================================================
# TEST 7: Get Version History
# ============================================================
@pytest.mark.asyncio
async def test_get_version_history(mock_supabase, service):
    """Test retrieving version history for an asset."""
    
    mock_history = [
        {
            "version_number": 3,
            "created_at": "2026-02-11T10:00:00",
            "breaking_changes": True,
            "changes_from_previous": [{"change_type": "removed", "column_name": "old_field"}]
        },
        {
            "version_number": 2,
            "created_at": "2026-02-10T10:00:00",
            "breaking_changes": False,
            "changes_from_previous": [{"change_type": "added", "column_name": "new_field"}]
        },
        {
            "version_number": 1,
            "created_at": "2026-02-09T10:00:00",
            "breaking_changes": False,
            "changes_from_previous": None
        }
    ]
    
    mock_supabase.execute.return_value = Mock(data=mock_history)
    
    history = await service.get_version_history("asset-789", limit=10)
    
    assert len(history) == 3
    assert history[0]["version_number"] == 3
    assert history[0]["breaking_changes"] == True


# ============================================================
# TEST 8: Compare Versions
# ============================================================
@pytest.mark.asyncio
async def test_compare_versions(service):
    """Test comparing two specific versions."""
    
    old_cols = [
        SchemaColumn("id", "integer", False, True),
        SchemaColumn("name", "string", True)
    ]
    new_cols = [
        SchemaColumn("id", "integer", False, True),
        SchemaColumn("name", "string", True),
        SchemaColumn("email", "string", True)
    ]
    
    old_snapshot = SchemaSnapshot("asset-1", "users", old_cols, 1, datetime.now())
    new_snapshot = SchemaSnapshot("asset-1", "users", new_cols, 2, datetime.now())
    
    with patch.object(service, 'get_schema_version') as mock_get:
        mock_get.side_effect = [old_snapshot, new_snapshot]
        
        changes = await service.compare_versions("asset-1", 1, 2)
    
    assert len(changes) > 0
    assert any(c.change_type == "added" for c in changes)


# ============================================================
# TEST 9: Cache Behavior
# ============================================================
@pytest.mark.asyncio
async def test_cache_behavior(mock_supabase, service):
    """Test that snapshots are cached."""
    
    snapshot_data = {
        "asset_id": "asset-1",
        "table_name": "users",
        "columns": [
            {"name": "id", "data_type": "integer", "nullable": False, "primary_key": True}
        ],
        "version_number": 1,
        "timestamp": datetime.now().isoformat()
    }
    
    mock_supabase.execute.return_value = Mock(data=[{"schema_snapshot": snapshot_data}])
    
    # First call - should query database
    snapshot1 = await service.get_schema_version("asset-1", 1)
    
    # Second call - should use cache (no additional DB query)
    mock_supabase.execute.reset_mock()
    snapshot2 = await service.get_schema_version("asset-1", 1)
    
    assert snapshot1.asset_id == snapshot2.asset_id
    # Should not have called execute again (cache hit)
    mock_supabase.execute.assert_not_called()


# ============================================================
# TEST 10: Error Handling - Asset Not Found
# ============================================================
@pytest.mark.asyncio
async def test_capture_snapshot_asset_not_found(mock_supabase, service):
    """Test error handling when asset doesn't exist."""
    
    mock_supabase.execute.return_value = Mock(data=[])
    
    with pytest.raises(ValueError, match="Asset .* not found"):
        await service.capture_schema_snapshot("nonexistent-asset")


# ============================================================
# TEST 11: Error Handling - Invalid Metadata
# ============================================================
@pytest.mark.asyncio
async def test_capture_snapshot_invalid_metadata(mock_supabase, service):
    """Test error handling for invalid metadata."""
    
    invalid_data = {
        "id": "asset-789",
        "name": "customers",
        "metadata": {}  # Missing columns
    }
    
    mock_supabase.execute.return_value = Mock(data=[invalid_data])
    
    with pytest.raises(ValueError, match="has no column metadata"):
        await service.capture_schema_snapshot("asset-789")


# ============================================================
# Summary
# ============================================================
"""
Test Coverage Summary:
- ✅ TEST 1: Capture first schema snapshot
- ✅ TEST 2: Capture subsequent snapshots with change detection
- ✅ TEST 3: Detect added columns (non-breaking)
- ✅ TEST 4: Detect removed columns (breaking)
- ✅ TEST 5: Detect type changes (breaking)
- ✅ TEST 6: Detect nullable changes (breaking if NOT NULL)
- ✅ TEST 7: Get version history
- ✅ TEST 8: Compare two versions
- ✅ TEST 9: Cache behavior
- ✅ TEST 10: Error - asset not found
- ✅ TEST 11: Error - invalid metadata

Total: 11 tests for SchemaVersionService
"""
