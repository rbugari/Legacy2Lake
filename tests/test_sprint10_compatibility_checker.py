"""
Test Suite for Sprint 10: Schema Evolution - CompatibilityChecker

Tests backward compatibility checking, breaking change detection,
column rename detection, compatibility scoring, and migration strategies.

Author: UTM Platform Team
Created: February 11, 2026
Sprint: 10 (Schema Evolution)
"""

import pytest
from datetime import datetime
from compatibility_checker_service import (
    CompatibilityChecker,
    CompatibilityResult
)
from schema_version_service import (
    SchemaSnapshot,
    SchemaColumn,
    SchemaChange
)


class TestCompatibilityChecker:
    """Test suite for CompatibilityChecker."""
    
    @pytest.fixture
    def checker(self):
        """Create CompatibilityChecker instance."""
        return CompatibilityChecker(similarity_threshold=0.7)
    
    @pytest.fixture
    def old_snapshot_simple(self):
        """Simple old schema snapshot."""
        columns = [
            SchemaColumn("id", "integer", False, True),
            SchemaColumn("name", "string", True),
            SchemaColumn("email", "string", True)
        ]
        return SchemaSnapshot("asset-1", "users", columns, 1, datetime.now())
    
    @pytest.fixture
    def new_snapshot_compatible(self):
        """Compatible new schema (added nullable column)."""
        columns = [
            SchemaColumn("id", "integer", False, True),
            SchemaColumn("name", "string", True),
            SchemaColumn("email", "string", True),
            SchemaColumn("phone", "string", True)  # Added nullable
        ]
        return SchemaSnapshot("asset-1", "users", columns, 2, datetime.now())
    
    @pytest.fixture
    def new_snapshot_incompatible(self):
        """Incompatible new schema (removed column)."""
        columns = [
            SchemaColumn("id", "integer", False, True),
            SchemaColumn("name", "string", True)
            # email removed (BREAKING)
        ]
        return SchemaSnapshot("asset-1", "users", columns, 2, datetime.now())


# ============================================================
# TEST 1: Compatible Changes (Added Nullable Column)
# ============================================================
def test_compatible_changes_added_nullable(checker, old_snapshot_simple, new_snapshot_compatible):
    """Test that adding nullable columns is compatible."""
    
    result = checker.check_compatibility(old_snapshot_simple, new_snapshot_compatible)
    
    assert result.compatible == True
    assert result.compatibility_score >= 90
    assert len(result.breaking_changes) == 0
    assert len(result.non_breaking_changes) > 0


# ============================================================
# TEST 2: Incompatible Changes (Removed Column)
# ============================================================
def test_incompatible_changes_removed_column(checker, old_snapshot_simple, new_snapshot_incompatible):
    """Test that removing columns is incompatible."""
    
    result = checker.check_compatibility(old_snapshot_simple, new_snapshot_incompatible)
    
    assert result.compatible == False
    assert result.compatibility_score < 100
    assert len(result.breaking_changes) > 0
    
    # Verify the breaking change is for email removal
    email_removal = [c for c in result.breaking_changes if c.column_name == "email"]
    assert len(email_removal) == 1


# ============================================================
# TEST 3: Detect Column Rename (High Similarity)
# ============================================================
def test_detect_column_rename(checker):
    """Test detection of column renames using similarity matching."""
    
    old_cols = [
        SchemaColumn("customer_email", "string", True),
        SchemaColumn("customer_name", "string", True)
    ]
    new_cols = [
        SchemaColumn("cust_email", "string", True),  # Similar to customer_email
        SchemaColumn("customer_name", "string", True)
    ]
    
    old_snapshot = SchemaSnapshot("asset-1", "users", old_cols, 1, datetime.now())
    new_snapshot = SchemaSnapshot("asset-1", "users", new_cols, 2, datetime.now())
    
    result = checker.check_compatibility(old_snapshot, new_snapshot, detect_renames=True)
    
    # Should suggest customer_email -> cust_email mapping
    assert len(result.suggested_column_mappings) > 0
    assert "customer_email" in result.suggested_column_mappings


# ============================================================
# TEST 4: Name Similarity Calculation
# ============================================================
def test_name_similarity_calculation(checker):
    """Test column name similarity scoring."""
    
    # High similarity
    assert checker._calculate_name_similarity("customer_email", "cust_email") > 0.7
    assert checker._calculate_name_similarity("CustomerName", "customer_name") > 0.8
    
    # Low similarity
    assert checker._calculate_name_similarity("email", "phone") < 0.5
    assert checker._calculate_name_similarity("id", "name") < 0.5


# ============================================================
# TEST 5: Compatibility Scoring
# ============================================================
def test_compatibility_scoring(checker):
    """Test compatibility score calculation."""
    
    # No changes = 100%
    score = checker._calculate_compatibility_score(0, 0, 0)
    assert score == 100.0
    
    # 1 breaking change = 80%
    score = checker._calculate_compatibility_score(1, 0, 0)
    assert score == 80.0
    
    # 2 breaking + 3 non-breaking = 60% - 15% = 45%
    score = checker._calculate_compatibility_score(2, 3, 0)
    assert score == 45.0


# ============================================================
# TEST 6: Safety Score Calculation
# ============================================================
def test_safety_score_calculation(checker):
    """Test migration safety scoring."""
    
    # Safe change (nullable addition)
    safe_changes = [
        SchemaChange("added", "email", None, {"data_type": "string", "nullable": True}, False, "Added")
    ]
    score = checker._calculate_safety_score(safe_changes)
    assert score >= 90
    
    # Risky change (column removal)
    risky_changes = [
        SchemaChange("removed", "email", {"data_type": "string"}, None, True, "Removed")
    ]
    score = checker._calculate_safety_score(risky_changes)
    assert score <= 75


# ============================================================
# TEST 7: Validate Column Mapping
# ============================================================
def test_validate_column_mapping(checker, old_snapshot_simple):
    """Test validation of proposed column mappings."""
    
    new_cols = [
        SchemaColumn("id", "integer", False, True),
        SchemaColumn("full_name", "string", True),  # Renamed from 'name'
        SchemaColumn("contact_email", "string", True)  # Renamed from 'email'
    ]
    new_snapshot = SchemaSnapshot("asset-1", "users", new_cols, 2, datetime.now())
    
    # Valid mapping
    valid_mapping = {
        "name": "full_name",
        "email": "contact_email"
    }
    
    result = checker.validate_column_mapping(old_snapshot_simple, new_snapshot, valid_mapping)
    
    assert result["valid"] == True
    assert len(result["errors"]) == 0
    assert result["mapping_count"] == 2


# ============================================================
# TEST 8: Invalid Column Mapping (Nonexistent Column)
# ============================================================
def test_validate_column_mapping_invalid(checker, old_snapshot_simple, new_snapshot_compatible):
    """Test validation of invalid column mappings."""
    
    # Invalid mapping (old column doesn't exist)
    invalid_mapping = {
        "nonexistent_col": "phone"
    }
    
    result = checker.validate_column_mapping(old_snapshot_simple, new_snapshot_compatible, invalid_mapping)
    
    assert result["valid"] == False
    assert len(result["errors"]) > 0


# ============================================================
# TEST 9: Migration Strategy - Simple Deploy
# ============================================================
def test_suggest_migration_strategy_simple(checker, old_snapshot_simple, new_snapshot_compatible):
    """Test migration strategy suggestion for simple changes."""
    
    compat_result = checker.check_compatibility(old_snapshot_simple, new_snapshot_compatible)
    strategy = checker.suggest_migration_strategy(compat_result)
    
    assert strategy["strategy"] == "SIMPLE_DEPLOY"
    assert strategy["risk_level"] == "LOW"
    assert strategy["requires_dba_approval"] == False


# ============================================================
# TEST 10: Migration Strategy - Manual Migration
# ============================================================
def test_suggest_migration_strategy_manual(checker, old_snapshot_simple, new_snapshot_incompatible):
    """Test migration strategy for complex/breaking changes."""
    
    compat_result = checker.check_compatibility(old_snapshot_simple, new_snapshot_incompatible)
    strategy = checker.suggest_migration_strategy(compat_result)
    
    # Breaking changes should require higher-risk strategy
    assert strategy["risk_level"] in ["MEDIUM", "HIGH", "CRITICAL"]
    
    if strategy["risk_level"] in ["HIGH", "CRITICAL"]:
        assert strategy["requires_dba_approval"] == True


# ============================================================
# TEST 11: Warning Generation
# ============================================================
def test_generate_warnings(checker, old_snapshot_simple, new_snapshot_incompatible):
    """Test generation of human-readable warnings."""
    
    result = checker.check_compatibility(old_snapshot_simple, new_snapshot_incompatible)
    
    assert len(result.warnings) > 0
    
    # Should warn about email removal
    email_warnings = [w for w in result.warnings if "email" in w.lower()]
    assert len(email_warnings) > 0


# ============================================================
# TEST 12: Estimate Downtime
# ============================================================
def test_estimate_downtime(checker, old_snapshot_simple, new_snapshot_compatible):
    """Test downtime estimation for migrations."""
    
    compat_result = checker.check_compatibility(old_snapshot_simple, new_snapshot_compatible)
    downtime = checker._estimate_downtime(compat_result)
    
    # Simple addition should have minimal downtime
    assert downtime >= 5  # Base downtime
    assert downtime < 30  # Should be quick for non-breaking changes


# ============================================================
# Summary
# ============================================================
"""
Test Coverage Summary:
- ✅ TEST 1: Compatible changes (added nullable column)
- ✅ TEST 2: Incompatible changes (removed column)
- ✅ TEST 3: Detect column rename (similarity matching)
- ✅ TEST 4: Name similarity calculation
- ✅ TEST 5: Compatibility scoring
- ✅ TEST 6: Safety score calculation
- ✅ TEST 7: Validate column mapping (valid)
- ✅ TEST 8: Validate column mapping (invalid)
- ✅ TEST 9: Migration strategy (simple deploy)
- ✅ TEST 10: Migration strategy (manual migration)
- ✅ TEST 11: Warning generation
- ✅ TEST 12: Estimate downtime

Total: 12 tests for CompatibilityChecker

OVERALL SPRINT 10 TEST SUMMARY:
- SchemaVersionService: 11 tests
- MigrationGeneratorService: 12 tests
- CompatibilityChecker: 12 tests
TOTAL: 35 tests (exceeds 30 test target ✅)
"""
