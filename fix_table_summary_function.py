"""
Execute SQL to fix get_table_summary function
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL to update function
sql = """
CREATE OR REPLACE FUNCTION get_table_summary(p_project_id UUID)
RETURNS TABLE (
    table_name TEXT,
    reader_count BIGINT,
    writer_count BIGINT,
    total_impacts BIGINT,
    operations TEXT[]
)
LANGUAGE sql
STABLE
AS $$
    SELECT 
        full_name as table_name,
        COUNT(*) FILTER (WHERE is_source = true) as reader_count,
        COUNT(*) FILTER (WHERE is_target = true) as writer_count,
        COUNT(*) as total_impacts,
        ARRAY_AGG(DISTINCT operation ORDER BY operation) as operations
    FROM utm_table_impacts
    WHERE project_id = p_project_id
    GROUP BY full_name
    ORDER BY total_impacts DESC, full_name;
$$;
"""

print("=" * 80)
print("Updating get_table_summary function...")
print("=" * 80)

try:
    # Use postgrest to execute - wrap in transaction
    from postgrest import APIError
    
    # Try to execute using raw SQL query
    # Note: Supabase client doesn't support DDL directly
    # We need to use the Management API or execute via psql
    
    print("\n⚠️ Direct SQL execution not supported via Supabase client")
    print("\n📝 ACTION REQUIRED:")
    print("Please execute the following SQL in Supabase Dashboard > SQL Editor:")
    print("\n" + "-" * 80)
    print(sql)
    print("-" * 80)
    print("\nOR copy from: migrations/fix_table_summary_field_names.sql")
    
    print("\n✅ After executing SQL, restart the backend with: .\\restart.ps1")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
