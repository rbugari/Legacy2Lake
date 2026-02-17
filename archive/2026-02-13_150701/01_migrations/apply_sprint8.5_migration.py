"""
Sprint 8.5: Apply Origin Analysis Schema Migration
Adds columns to utm_objects for SSIS origin analysis storage.
"""
import os
import sys
from pathlib import Path
from supabase import create_client, Client

# Supabase credentials  
SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def apply_migration():
    """Apply Sprint 8.5 migration to add origin analysis columns."""
    print("🚀 Applying Sprint 8.5 Origin Analysis Migration...\n")
    
    # Read migration SQL
    migration_file = Path(__file__).parent / "migrations" / "sprint8.5_origin_analysis_columns.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, "r", encoding="utf-8") as f:
        sql = f.read()
    
    # Remove comments and verification query section
    sql_lines = []
    skip_section = False
    for line in sql.split("\n"):
        if "-- Verification query" in line:
            skip_section = True
        if not skip_section and line.strip() and not line.strip().startswith("--"):
            sql_lines.append(line)
    
    sql_clean = "\n".join(sql_lines)
    
    print("📝 Migration SQL:")
    print("-" * 80)
    print(sql_clean)
    print("-" * 80)
    print()
    
    try:
        # Execute migration via RPC or direct SQL
        # Note: Supabase Python client doesn't have direct SQL execution
        # We'll need to use psycopg2 or execute via Supabase SQL Editor
        
        print("⚠️  MANUAL STEP REQUIRED:")
        print("   Copy the SQL above and execute it in Supabase SQL Editor:")
        print("   https://supabase.com/dashboard/project/qdsdfityyxmalyipqbfm/sql/new")
        print()
        print("   OR use the SQL file directly:")
        print(f"   {migration_file}")
        print()
        
        # Verify columns exist after manual execution
        result = supabase.table("utm_objects") \
            .select("source_connection, source_type, transformations, complexity_score, data_flow_analysis") \
            .limit(1) \
            .execute()
        
        print("✅ Verification: Columns exist in utm_objects")
        print(f"   Columns: source_connection, source_type, transformations, complexity_score, data_flow_analysis")
        return True
        
    except Exception as e:
        if "column" in str(e).lower() and "does not exist" in str(e).lower():
            print("❌ Migration not applied yet. Please execute SQL manually.")
            print(f"   Error: {e}")
            return False
        else:
            print(f"❌ Error verifying migration: {e}")
            return False

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
