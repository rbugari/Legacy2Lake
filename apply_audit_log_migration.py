"""
Sprint 6: Apply Audit Log Migration
Creates utm_audit_log table in Supabase
"""
import os
from supabase import create_client
from pathlib import Path

# Supabase credentials
SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

def main():
    """Execute audit log table migration"""
    
    print("=" * 80)
    print("SPRINT 6: AUDIT LOG TABLE MIGRATION")
    print("=" * 80)
    
    # Initialize Supabase client
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Read SQL migration file
    sql_file = Path("migrations/sprint6_audit_log_table.sql")
    
    if not sql_file.exists():
        print(f"\n❌ ERROR: Migration file not found: {sql_file}")
        return
    
    print(f"\n[1/3] Reading migration file: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"      ✅ Migration file loaded ({len(sql_content)} bytes)")
    
    # Note: Supabase Python client doesn't directly support arbitrary SQL execution
    # This needs to be run via Supabase SQL Editor
    
    print("\n[2/3] Executing migration...")
    print("      ⚠️  NOTE: Supabase Python client cannot execute DDL statements")
    print("      Manual SQL execution required in Supabase SQL Editor")
    print("")
    print("      Steps to complete migration:")
    print("      1. Go to: https://qdsdfityyxmalyipqbfm.supabase.co")
    print("      2. Navigate to: SQL Editor")
    print("      3. Copy the SQL from: migrations/sprint6_audit_log_table.sql")
    print("      4. Paste and execute in SQL Editor")
    print("")
    
    # Check if table exists (will be used after manual execution)
    print("[3/3] Verifying table structure (will work after manual execution)...")
    try:
        # Try to query the table
        response = client.table("utm_audit_log").select("id").limit(1).execute()
        
        print("      ✅ utm_audit_log table exists and is accessible")
        print(f"      Rows in table: {len(response.data)}")
        
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg or "relation" in error_msg:
            print("      ⚠️  utm_audit_log table not found - execute SQL migration first")
        else:
            print(f"      ⚠️  Error checking table: {error_msg}")
    
    print("\n" + "=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)
    print("✅ Migration file ready: migrations/sprint6_audit_log_table.sql")
    print("⚠️  Manual execution required in Supabase SQL Editor")
    print("")
    print("After executing SQL:")
    print("- utm_audit_log table will be created")
    print("- 5 indexes for performance")
    print("- Row Level Security (RLS) enabled")
    print("- 3 RLS policies (service_role, tenant_isolation, admin_access)")
    print("=" * 80)


if __name__ == "__main__":
    main()
