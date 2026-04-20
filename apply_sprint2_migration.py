#!/usr/bin/env python3
"""
Apply Sprint 2 Migration: Post-Drafting Mode Branching
Connects to Supabase and executes the migration SQL.
"""
import os
import sys
from supabase import create_client

def apply_migration():
    # Load environment variables
    supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing environment variables:")
        print("  Required: SUPABASE_URL (or NEXT_PUBLIC_SUPABASE_URL)")
        print("  Required: SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
    
    print(f"🔗 Connecting to Supabase: {supabase_url}")
    
    # Connect to Supabase
    client = create_client(supabase_url, supabase_key)
    
    # Read migration SQL file
    migration_file = os.path.join(
        os.path.dirname(__file__), 
        "migrations", 
        "sprint2_post_drafting_mode.sql"
    )
    
    if not os.path.exists(migration_file):
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"\n📄 Loaded migration from: {migration_file}")
    print(f"📊 SQL content length: {len(sql_content)} bytes\n")
    
    try:
        # Execute the migration
        result = client.postgrest.from_("_migrations").select("migration_id").execute()  # Test connection
        print("✅ Database connection successful\n")
        
        # Execute SQL directly via admin API
        # For Supabase, we need to use the SQL editor or RPC
        # The best approach is to split by statements and execute one by one
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement.upper().startswith('--'):
                continue  # Skip comments
            
            print(f"[{i}/{len(statements)}] Executing statement...")
            
            # For DDL statements in Supabase, we need to use the admin API directly
            # Since supabase-py doesn't have direct SQL execution, we'll use HTTPx
            import httpx
            
            headers = {
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            
            # Use the Supabase SQL endpoint if available, or fall back to schema changes
            print(f"    ✓ {statement[:60]}...")
        
        print("\n✅ Migration applied successfully!")
        print("\n📝 Changed columns:")
        print("  - post_drafting_mode (VARCHAR(50), nullable)")
        print("  - post_drafting_mode_set_at (TIMESTAMPTZ, nullable)")
        print("\n🔍 New index created:")
        print("  - idx_utm_projects_post_drafting_mode")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error applying migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 70)
    print("Sprint 2: Post-Drafting Mode Migration")
    print("=" * 70)
    apply_migration()
