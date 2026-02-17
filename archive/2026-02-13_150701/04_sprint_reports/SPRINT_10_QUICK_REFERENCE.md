# Sprint 10: Schema Evolution - Quick Reference

**Version:** v3.12  
**Status:** ✅ Production Ready

---

## 🚀 Quick Start (3 minutes)

### 1. Install Database Migration

```bash
# Run Sprint 10 migration
psql -U postgres -d utm_db -f migrations/sprint_10_schema_versions.sql
```

### 2. Capture Initial Schema Snapshot

```python
from apps.api.services.schema_version_service import SchemaVersionService

# Create service instance
service = SchemaVersionService(
    tenant_id="your-tenant-id",
    project_id="your-project-id"
)

# Capture snapshot
snapshot = await service.capture_schema_snapshot("asset-id-here")

print(f"✅ Version {snapshot.version_number} captured")
print(f"📊 Columns: {len(snapshot.columns)}")
```

### 3. Agent C Automatically Tracks Changes

```python
from apps.api.services.agent_c_service import AgentCService

agent_c = AgentCService(tenant_id="...", client_id="...")

# Agent C now returns schema evolution data automatically
response = await agent_c.transpile_task(node_data)

# Access schema version info
if response.get('schema_version'):
    print(f"Version: {response['schema_version']['version_number']}")
    print(f"Breaking: {response['schema_version']['is_breaking']}")
```

---

## 📖 Common Use Cases

### Use Case 1: Check if Schema Changed

```python
service = SchemaVersionService(tenant_id, project_id)

# Get version history
history = await service.get_version_history("asset-123")

if len(history) > 1:
    print(f"✅ Schema has {len(history)} versions")
    
    # Check latest for breaking changes
    latest = history[0]
    if latest['breaking_changes']:
        print("⚠️ Latest version has breaking changes!")
else:
    print("ℹ️ This is the first schema version")
```

### Use Case 2: Generate Migration Script

```python
from apps.api.services.migration_generator_service import (
    MigrationGeneratorService, 
    Platform
)

# Compare two versions
changes = await service.compare_versions("asset-123", 1, 2)

if changes:
    # Generate migration for PySpark
    generator = MigrationGeneratorService(platform=Platform.PYSPARK)
    
    migration = generator.generate_migration(
        table_name="customers",
        changes=changes,
        catalog="main",
        schema="bronze"
    )
    
    print("Forward SQL:")
    print(migration.forward_sql)
    print("\nRollback SQL:")
    print(migration.rollback_sql)
    
    # Check risk
    risk = generator.estimate_migration_risk(changes)
    print(f"\nRisk Level: {risk['risk_level']}")
```

### Use Case 3: Check Compatibility

```python
from apps.api.services.compatibility_checker_service import CompatibilityChecker

# Get two snapshots
old_snapshot = await service.get_schema_version("asset-123", 1)
new_snapshot = await service.get_schema_version("asset-123", 2)

# Check compatibility
checker = CompatibilityChecker()
result = checker.check_compatibility(old_snapshot, new_snapshot)

print(f"Compatible: {result.compatible}")
print(f"Score: {result.compatibility_score}%")

if result.breaking_changes:
    print("\n⚠️ Breaking Changes:")
    for change in result.breaking_changes:
        print(f"  - {change.description}")

if result.suggested_column_mappings:
    print("\n💡 Suggested Renames:")
    for old, new in result.suggested_column_mappings.items():
        print(f"  {old} → {new}")
```

### Use Case 4: Get Migration Strategy

```python
# Suggest migration strategy based on compatibility
strategy = checker.suggest_migration_strategy(result)

print(f"Strategy: {strategy['strategy']}")
print(f"Risk Level: {strategy['risk_level']}")
print(f"DBA Approval Required: {strategy['requires_dba_approval']}")
print(f"Estimated Downtime: {strategy['estimated_downtime_minutes']} minutes")

print("\nRecommended Steps:")
for step in strategy['recommended_steps']:
    print(f"  {step}")
```

---

## 🎯 Agent C Response Structure

When Agent C detects schema changes, the response includes:

```python
response = {
    "code": "...",  # Generated code
    "validation": {...},  # Sprint 8
    "test_code": "...",  # Sprint 8
    "schema": {...},  # Sprint 9
    "parameters": {...},  # Sprint 9
    
    # Sprint 10: Schema Evolution
    "schema_version": {
        "version_number": 2,
        "timestamp": "2026-02-11T10:00:00",
        "is_breaking": True,
        "changes_detected": 3
    },
    
    "migration_scripts": {
        "forward_sql": "ALTER TABLE ...",
        "rollback_sql": "ALTER TABLE ...",
        "description": "Column 'email' type changed from string to integer",
        "breaking": True,
        "requires_data_migration": True,
        "data_migration_sql": "UPDATE ... SET email = CAST(email AS INT)",
        "risk_assessment": {
            "risk_score": 22,
            "risk_level": "HIGH",
            "recommendation": "Requires manual review and testing",
            "warnings": ["TYPE CHANGE: Data migration required"],
            "breaking_change_count": 2,
            "total_changes": 3
        },
        "migration_strategy": {
            "strategy": "BLUE_GREEN_DEPLOY",
            "risk_level": "HIGH",
            "recommended_steps": [...],
            "requires_dba_approval": True,
            "requires_maintenance_window": False,
            "estimated_downtime_minutes": 35
        }
    },
    
    "compatibility": {
        "compatible": False,
        "compatibility_score": 65.0,
        "breaking_changes": [...],
        "non_breaking_changes": [...],
        "suggested_column_mappings": {"old_name": "new_name"},
        "warnings": [
            "⚠️ Column 'email' type changed from string to integer. Data migration required."
        ],
        "safety_score": 45.0
    }
}
```

---

## 🔤 Supported Platforms

| Platform | Enum Value | Example DDL |
|----------|-----------|-------------|
| PySpark | `Platform.PYSPARK` | `ALTER TABLE main.bronze.customers ADD COLUMN email STRING` |
| Snowflake | `Platform.SNOWFLAKE` | `ALTER TABLE customers ADD COLUMN email VARCHAR NULL` |
| PostgreSQL | `Platform.POSTGRESQL` | `ALTER TABLE customers ADD COLUMN email TEXT NULL` |
| Databricks | `Platform.DATABRICKS` | Same as PySpark |
| MS Fabric | `Platform.MS_FABRIC` | Fabric-specific syntax |
| GCP BigQuery | `Platform.GCP_BIGQUERY` | BigQuery-specific syntax |
| AWS Redshift | `Platform.AWS_REDSHIFT` | Redshift-specific syntax |

---

## ⚙️ Configuration

### Similarity Threshold (Column Rename Detection)

```python
# Default: 0.7 (70% similarity)
checker = CompatibilityChecker(similarity_threshold=0.7)

# More restrictive (fewer false positives)
checker = CompatibilityChecker(similarity_threshold=0.85)

# More permissive (more rename suggestions)
checker = CompatibilityChecker(similarity_threshold=0.6)
```

### Cache Management

```python
# Clear cache to force DB re-query
service.clear_cache()

# Cache is automatically managed per instance
# Each asset+version is cached independently
```

---

## 🛡️ Risk Levels

| Risk Level | Score Range | Description | Approval Required |
|-----------|-------------|-------------|-------------------|
| **LOW** | 0-9 | Safe changes (nullable additions) | No |
| **MEDIUM** | 10-19 | Review recommended (non-nullable additions) | No |
| **HIGH** | 20-39 | Manual review + testing required | Yes (DBA) |
| **CRITICAL** | 40+ | Maintenance window required | Yes (DBA + CTO) |

---

## 📊 Change Types

### Non-Breaking Changes ✅

```python
# Adding nullable column
SchemaChange("added", "email", None, {"nullable": True}, False, "...")

# Making column nullable
SchemaChange("modified", "age", {"nullable": False}, {"nullable": True}, False, "...")
```

### Breaking Changes ⚠️

```python
# Removing column
SchemaChange("removed", "old_field", {...}, None, True, "...")

# Changing type
SchemaChange("modified", "age", {"type": "string"}, {"type": "integer"}, True, "...")

# Making NOT NULL
SchemaChange("modified", "email", {"nullable": True}, {"nullable": False}, True, "...")
```

---

## 🧪 Testing

### Run Sprint 10 Tests

```bash
# All Sprint 10 tests
pytest tests/test_sprint10_*.py -v

# Individual test suites
pytest tests/test_sprint10_schema_version.py -v        # 11 tests
pytest tests/test_sprint10_migration_generator.py -v   # 12 tests
pytest tests/test_sprint10_compatibility_checker.py -v # 12 tests
```

### Mock Data for Testing

```python
from schema_version_service import SchemaSnapshot, SchemaColumn
from datetime import datetime

# Create mock snapshot
columns = [
    SchemaColumn("id", "integer", False, True),
    SchemaColumn("name", "string", True),
    SchemaColumn("email", "string", True)
]

snapshot = SchemaSnapshot(
    asset_id="asset-123",
    table_name="customers",
    columns=columns,
    version_number=1,
    timestamp=datetime.now()
)
```

---

## 🔍 Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Service logs will show:
# [AgentC Sprint10] Tracking schema evolution for asset_id=...
# [AgentC Sprint10] ✅ Schema snapshot captured: v2
# [AgentC Sprint10] 📊 Schema changes detected: 3 changes
# [AgentC Sprint10] ✅ Migration scripts generated: breaking=True
```

### Check Database State

```sql
-- View all schema versions
SELECT 
    asset_id,
    version_number,
    breaking_changes,
    created_at
FROM utm_schema_versions
ORDER BY created_at DESC
LIMIT 20;

-- Count versions per asset
SELECT 
    asset_id,
    COUNT(*) as version_count,
    MAX(version_number) as latest_version
FROM utm_schema_versions
GROUP BY asset_id;

-- Breaking changes only
SELECT *
FROM utm_schema_versions
WHERE breaking_changes = TRUE
ORDER BY created_at DESC;
```

---

## 🚨 Common Issues

### Issue: "Asset not found"

```python
# Verify asset exists in utm_objects
response = supabase.table("utm_objects").select("id, name").eq("id", asset_id).execute()

if not response.data:
    print(f"❌ Asset {asset_id} not found in utm_objects")
```

### Issue: "No column metadata"

```python
# Check utm_objects.metadata structure
response = supabase.table("utm_objects").select("metadata").eq("id", asset_id).execute()

metadata = response.data[0]['metadata']

if 'columns' not in metadata:
    print("❌ Metadata missing 'columns' field")
    print("Required structure:")
    print({
        "columns": [
            {"name": "id", "type": "integer", "nullable": False},
            ...
        ],
        "primaryKey": ["id"]
    })
```

### Issue: "Version number mismatch"

```python
# Check latest version
history = await service.get_version_history(asset_id, limit=1)

if history:
    latest_version = history[0]['version_number']
    print(f"Latest version: {latest_version}")
else:
    print("No versions exist yet")
```

---

## 🎯 Best Practices

### 1. Always Capture Snapshots Before Code Generation

```python
# GOOD ✅
snapshot = await service.capture_schema_snapshot(asset_id)
response = await agent_c.transpile_task(node_data)

# BAD ❌ (Agent C does this automatically, but manual capture is useful for auditing)
response = await agent_c.transpile_task(node_data)  # No explicit snapshot
```

### 2. Review Breaking Changes Before Deployment

```python
if response.get('migration_scripts', {}).get('breaking'):
    print("⚠️ BREAKING CHANGES - REVIEW REQUIRED")
    
    # Get migration strategy
    strategy = response['migration_scripts']['migration_strategy']
    
    if strategy['requires_dba_approval']:
        print("❌ Cannot deploy without DBA approval")
        # Send notification, create ticket, etc.
    else:
        print("✅ Safe to proceed with caution")
```

### 3. Use Column Mappings for Renames

```python
# If rename detected
if result.suggested_column_mappings:
    # Validate mapping before using
    validation = checker.validate_column_mapping(
        old_snapshot, 
        new_snapshot, 
        result.suggested_column_mappings
    )
    
    if validation['valid']:
        print("✅ Column mapping is valid")
        # Use ALTER + UPDATE instead of DROP + ADD
    else:
        print(f"❌ Invalid mapping: {validation['errors']}")
```

### 4. Always Generate Rollback Scripts

```python
# Generate migration
migration = generator.generate_migration(table_name, changes)

# Save both forward and rollback
save_migration_script(migration.forward_sql, "forward.sql")
save_migration_script(migration.rollback_sql, "rollback.sql")

# Test rollback in staging first
```

---

## 📚 Additional Resources

- [Full Implementation Report](./SPRINT_10_SCHEMA_EVOLUTION_REPORT.md)
- [Test Suite](./tests/test_sprint10_*.py)
- [Database Migration](./migrations/sprint_10_schema_versions.sql)
- [Agent C Integration Example](./apps/api/services/agent_c_service.py#L164-L265)

---

**Sprint 10:** ✅ Complete  
**Next Sprint:** Sprint 11 - Data Quality Framework  
**Questions?** See full report or check test examples
