#!/usr/bin/env python3
"""
Apply Sprint 13 Migration
Adds visualization columns to utm_objects table
"""
import os
from supabase import create_client
from pathlib import Path

def apply_migration():
    # Get Supabase credentials from environment
    supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: Supabase credentials not found in environment")
        print("Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        return
    
    # Read migration SQL
    migration_path = Path(__file__).parent / "supabase_migrations" / "sprint_13_visualization_columns.sql"
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"📄 Reading migration: {migration_path.name}")
    print(f"🔗 Connecting to: {supabase_url}")
    
    # Create Supabase client
    supabase = create_client(supabase_url, supabase_key)
    
    # Execute migration
    try:
        print("🔄 Executing migration...")
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()
        print("✅ Migration applied successfully!")
        print(f"   Added columns: object_name, generated_code, tech_id, layer, updated_at,")
        print(f"                  validation_result, optimization_metadata, schema_metadata,")
        print(f"                  row_count, column_count, quality_score, quality_violations")
        return True
    except Exception as e:
        # If exec_sql doesn't exist, try direct execution
        print(f"⚠️  RPC method not available, trying direct execution...")
        try:
            # Split and execute statements individually
            statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
            for i, stmt in enumerate(statements, 1):
                if stmt:
                    print(f"   Executing statement {i}/{len(statements)}...")
                    supabase.postgrest.rpc('exec_sql', {'sql': stmt}).execute()
            print("✅ Migration applied successfully!")
            return True
        except Exception as e2:
            print(f"❌ Migration failed: {e2}")
            print("\n📋 Manual execution required:")
            print(f"   1. Open Supabase SQL Editor")
            print(f"   2. Copy SQL from: {migration_path}")
            print(f"   3. Execute manually")
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("  Sprint 13: Visualization Columns Migration")
    print("=" * 60)
    apply_migration()
