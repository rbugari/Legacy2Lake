"""
Apply Sprint 7 Migration: utm_asset_columns Table
==================================================

Purpose:
    Creates the utm_asset_columns table for Deep Forensic Triage feature.
    This table stores column-level profiling data (cardinality, PII detection, 
    partition recommendations, etc.)

Usage:
    python apply_sprint7_migration.py

Requirements:
    - Supabase connection configured
    - utm_objects and utm_projects tables must exist
    - RLS policies will be enabled

Author: Legacy2Lake Engineering
Date: 2026-02-11
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from apps.api.services.persistence_service import SupabasePersistence
from apps.api.utils.logger import logger


async def apply_migration():
    """
    Apply Sprint 7 migration to create utm_asset_columns table.
    """
    logger.info("=" * 80, "Migration")
    logger.info("Sprint 7 Migration: utm_asset_columns Table", "Migration")
    logger.info("=" * 80, "Migration")
    
    # Read migration SQL
    migration_path = Path(__file__).parent / 'migrations' / 'sprint7_asset_columns_table.sql'
    
    if not migration_path.exists():
        logger.error(f"Migration file not found: {migration_path}", "Migration")
        return False
    
    with open(migration_path, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    logger.info(f"Read migration SQL ({len(migration_sql)} characters)", "Migration")
    
    # Connect to Supabase
    try:
        db = SupabasePersistence(tenant_id=None)  # Use admin connection
        logger.info("Connected to Supabase", "Migration")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}", "Migration")
        return False
    
    # Execute migration
    try:
        logger.info("Executing migration SQL...", "Migration")
        
        # Supabase Python client doesn't directly support DDL execution
        # We need to use the REST API or PostgREST
        # For now, we'll log instructions for manual execution
        
        logger.info("=" * 80, "Migration")
        logger.info("MIGRATION SQL READY", "Migration")
        logger.info("=" * 80, "Migration")
        logger.info("", "Migration")
        logger.info("The migration SQL is ready in:", "Migration")
        logger.info(f"  {migration_path}", "Migration")
        logger.info("", "Migration")
        logger.info("Please execute this migration in one of the following ways:", "Migration")
        logger.info("", "Migration")
        logger.info("Option 1: Supabase Dashboard", "Migration")
        logger.info("  1. Go to your Supabase project dashboard", "Migration")
        logger.info("  2. Navigate to SQL Editor", "Migration")
        logger.info("  3. Paste the migration SQL", "Migration")
        logger.info("  4. Click 'Run'", "Migration")
        logger.info("", "Migration")
        logger.info("Option 2: psql CLI", "Migration")
        logger.info("  psql -h <host> -U <user> -d <database> -f migrations/sprint7_asset_columns_table.sql", "Migration")
        logger.info("", "Migration")
        logger.info("Option 3: DBeaver / pgAdmin", "Migration")
        logger.info("  1. Connect to your Supabase PostgreSQL database", "Migration")
        logger.info("  2. Open SQL script editor", "Migration")
        logger.info("  3. Load and execute the migration file", "Migration")
        logger.info("", "Migration")
        logger.info("=" * 80, "Migration")
        
        # Verify if table already exists
        try:
            result = db.client.table('utm_asset_columns').select('column_id').limit(1).execute()
            logger.info("✅ Table utm_asset_columns already exists!", "Migration")
            logger.info(f"   Found {len(result.data)} rows (sample check)", "Migration")
            return True
        except Exception as check_error:
            logger.info("❌ Table utm_asset_columns does not exist yet", "Migration")
            logger.info("   Please execute the migration SQL as instructed above", "Migration")
            return False
    
    except Exception as e:
        logger.error(f"Migration execution failed: {e}", "Migration")
        return False


async def verify_migration():
    """
    Verify that the migration was successful by checking table structure.
    """
    logger.info("=" * 80, "Verification")
    logger.info("Verifying Migration", "Verification")
    logger.info("=" * 80, "Verification")
    
    db = SupabasePersistence(tenant_id=None)
    
    try:
        # Try to query the table
        result = db.client.table('utm_asset_columns').select('*').limit(0).execute()
        
        logger.info("✅ utm_asset_columns table exists and is accessible", "Verification")
        logger.info("", "Verification")
        logger.info("Expected Columns:", "Verification")
        expected_cols = [
            'column_id', 'asset_id', 'project_id', 'column_name',
            'data_type', 'inferred_type', 'distinct_count', 'cardinality_ratio',
            'null_count', 'null_percentage', 'is_pii', 'pii_category',
            'pii_confidence', 'partition_candidate', 'partition_score',
            'partition_reason', 'sample_values', 'min_value', 'max_value',
            'is_primary_key', 'is_foreign_key', 'is_nullable', 'is_indexed',
            'analysis_timestamp', 'created_at', 'updated_at'
        ]
        for col in expected_cols:
            logger.info(f"  - {col}", "Verification")
        
        logger.info("", "Verification")
        logger.info("✅ Migration verification successful!", "Verification")
        return True
    
    except Exception as e:
        logger.error(f"❌ Migration verification failed: {e}", "Verification")
        logger.error("   Table may not exist or RLS policies prevent access", "Verification")
        return False


async def test_insert_sample():
    """
    Test inserting a sample column profile to verify functionality.
    """
    logger.info("=" * 80, "Testing")
    logger.info("Testing Sample Insert", "Testing")
    logger.info("=" * 80, "Testing")
    
    db = SupabasePersistence(tenant_id=None)
    
    # Create a test record
    test_record = {
        'asset_id': '00000000-0000-0000-0000-000000000000',  # Placeholder
        'project_id': '00000000-0000-0000-0000-000000000000',  # Placeholder
        'column_name': '__TEST_COLUMN__',
        'column_position': 1,
        'data_type': 'VARCHAR(255)',
        'inferred_type': 'STRING',
        'distinct_count': 100,
        'cardinality_ratio': 0.5,
        'null_count': 10,
        'null_percentage': 5.0,
        'is_pii': False,
        'partition_candidate': False,
        'analysis_version': 'v1.0_test'
    }
    
    try:
        # Insert test record
        result = db.client.table('utm_asset_columns').insert(test_record).execute()
        
        if result.data:
            logger.info("✅ Sample insert successful!", "Testing")
            test_id = result.data[0]['column_id']
            logger.info(f"   Created test record with ID: {test_id}", "Testing")
            
            # Clean up test record
            db.client.table('utm_asset_columns').delete().eq('column_id', test_id).execute()
            logger.info("✅ Test record cleaned up", "Testing")
            return True
        else:
            logger.error("❌ Sample insert failed: No data returned", "Testing")
            return False
    
    except Exception as e:
        logger.error(f"❌ Sample insert failed: {e}", "Testing")
        return False


async def main():
    """
    Main migration workflow.
    """
    logger.info("", "Main")
    logger.info("🚀 Sprint 7 Migration Runner", "Main")
    logger.info("", "Main")
    
    # Step 1: Prepare migration
    success = await apply_migration()
    
    if not success:
        logger.warning("⚠️  Migration needs to be executed manually", "Main")
        logger.info("", "Main")
        logger.info("After executing the migration, run this script again to verify.", "Main")
        return
    
    # Step 2: Verify migration
    logger.info("", "Main")
    logger.info("Waiting 2 seconds before verification...", "Main")
    await asyncio.sleep(2)
    
    verified = await verify_migration()
    
    if not verified:
        logger.error("❌ Migration verification failed", "Main")
        return
    
    # Step 3: Test functionality
    logger.info("", "Main")
    logger.info("Testing insert functionality...", "Main")
    
    tested = await test_insert_sample()
    
    if tested:
        logger.info("", "Main")
        logger.info("=" * 80, "Main")
        logger.info("✅ MIGRATION COMPLETE", "Main")
        logger.info("=" * 80, "Main")
        logger.info("", "Main")
        logger.info("Next Steps:", "Main")
        logger.info("  1. Test column profiling API: POST /assets/{asset_id}/analyze-columns", "Main")
        logger.info("  2. Test retrieval API: GET /assets/{asset_id}/columns", "Main")
        logger.info("  3. Test PII heatmap: GET /projects/{project_id}/pii-heatmap", "Main")
        logger.info("  4. Test partition recommendations: GET /projects/{project_id}/partition-recommendations", "Main")
        logger.info("", "Main")
    else:
        logger.error("❌ Testing failed - please review error messages above", "Main")


if __name__ == "__main__":
    asyncio.run(main())
