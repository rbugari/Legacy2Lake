"""
Apply migration 021: utm_project_members table
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

print("=" * 70)
print("APPLYING MIGRATION 021: utm_project_members")
print("=" * 70)

# Read migration file
migration_path = "supabase_migrations/021_v3.9_project_members_table.sql"

with open(migration_path, "r", encoding="utf-8") as f:
    migration_sql = f.read()

print(f"\n📄 Migration file: {migration_path}")
print(f"📝 SQL length: {len(migration_sql)} characters")

# Execute migration via Supabase RPC
# Note: For complex migrations with multiple statements, we need to execute via direct SQL
# Supabase's Python client doesn't support multi-statement SQL directly

print("\n⚠️  NOTE: This migration must be applied manually via Supabase Dashboard.")
print("\nSTEPS:")
print("1. Go to: https://supabase.com/dashboard")
print("2. Select your project")
print("3. Go to SQL Editor")
print("4. Paste the following SQL and execute:\n")
print("=" * 70)
print(migration_sql)
print("=" * 70)

print("\n✅ After executing, run check_project_members_table.py to verify")
