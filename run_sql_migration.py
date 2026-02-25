"""
Execute SQL migration to fix get_table_summary field names
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Read SQL file
with open("migrations/fix_table_summary_field_names.sql", "r") as f:
    sql = f.read()

print("Executing SQL migration...")
print("=" * 80)

try:
    # Execute SQL using postgrest (split by semicolon and execute each statement)
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    for i, stmt in enumerate(statements):
        if stmt:
            print(f"\nStatement {i+1}:")
            print(stmt[:100] + "..." if len(stmt) > 100 else stmt)
            try:
                result = client.rpc('exec_sql', {'sql': stmt}).execute()
                print("✅ Success")
            except Exception as e:
                # Try direct execution
                print(f"⚠️ Using service role direct query")
                # We can't execute DDL via RPC, need to use supabase SQL editor
                print("NOTE: Please execute this SQL manually in Supabase SQL Editor")
    
    print("\n" + "=" * 80)
    print("Migration preparation complete!")
    print("\n📝 ACTION REQUIRED:")
    print("Please execute the SQL in: migrations/fix_table_summary_field_names.sql")
    print("via Supabase Dashboard > SQL Editor")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n📝 FALLBACK ACTION:")
    print("Execute the SQL manually in Supabase Dashboard > SQL Editor")
