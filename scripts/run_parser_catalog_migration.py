"""
Parser Catalog Migration Runner

Executes phase_b_parser_catalog.sql against Supabase.
"""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    from supabase import create_client, Client
except ImportError:
    print("❌ Missing dependencies. Install: pip install python-dotenv supabase")
    sys.exit(1)

# Load environment
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
    sys.exit(1)

# Read migration SQL
migration_file = Path(__file__).parent.parent / "migrations" / "phase_b_parser_catalog.sql"

if not migration_file.exists():
    print(f"❌ Migration file not found: {migration_file}")
    sys.exit(1)

with open(migration_file, "r", encoding="utf-8") as f:
    sql_content = f.read()

print(f"📄 Loaded migration: {migration_file.name}")
print(f"   Size: {len(sql_content)} characters")
print(f"   Lines: {sql_content.count(chr(10))} lines")

# Connect to Supabase
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    print(f"✅ Connected to Supabase: {SUPABASE_URL}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# Execute migration
# Note: Supabase Python client doesn't have direct SQL execution via PostgREST
# We need to use the database's REST API or pg connection

print("\n⚠️  MANUAL ACTION REQUIRED:")
print("=" * 60)
print("The Supabase Python client (PostgREST) cannot execute raw SQL.")
print("Please run this migration using one of these methods:")
print()
print("1. Supabase Dashboard:")
print(f"   - Go to: {SUPABASE_URL.replace('supabase.co', 'supabase.com')}/project/_/sql")
print(f"   - Paste contents of: {migration_file}")
print("   - Click 'Run'")
print()
print("2. psql command line:")
print(f"   psql 'postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres' -f {migration_file}")
print()
print("3. Copy SQL to clipboard:")
print("=" * 60)

# Optionally copy to clipboard (Windows)
try:
    import pyperclip
    pyperclip.copy(sql_content)
    print("✅ Migration SQL copied to clipboard!")
except ImportError:
    print("💡 Tip: Install pyperclip to auto-copy SQL")

print("\n📋 Migration Preview (first 1000 chars):")
print("-" * 60)
print(sql_content[:1000])
print("...")
print("-" * 60)

# Show verification queries
print("\n🔍 After running migration, verify with:")
print("SELECT * FROM list_supported_technologies();")
print("SELECT * FROM utm_parser_catalog;")
print("SELECT * FROM resolve_parser_by_tech('SSIS');")
