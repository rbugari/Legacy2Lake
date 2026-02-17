#!/usr/bin/env python3
"""Quick migration script for Sprint 13"""
import sys
sys.path.insert(0, 'C:/proyectos_dev/UTM')

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read .env manually to ensure we get all vars
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"').strip("'")

supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

print(f"URL: {supabase_url[:30]}..." if supabase_url else "URL: Not found")
print(f"Key: {supabase_key[:20]}..." if supabase_key else "Key: Not found")

if not supabase_url or not supabase_key:
    print("\n❌ Missing credentials - Apply migration manually via Supabase Dashboard SQL Editor")
    sys.exit(1)

from supabase import create_client

# Read migration SQL
migration_path = Path(__file__).parent / "supabase_migrations" / "sprint_13_visualization_columns.sql"
with open(migration_path, 'r', encoding='utf-8') as f:
    sql_content = f.read()

print(f"\n📄 Migration SQL loaded: {len(sql_content)} chars")

# Create client
supabase = create_client(supabase_url, supabase_key)
print("✅ Supabase client created")

# Apply migration via raw SQL
try:
    # Execute via Postgrest (if available)
    print("\n🔄 Applying migration...")
    from postgrest import APIError
    result = supabase.rpc('exec_sql', {'query': sql_content}).execute()
    print("✅ Migration applied via RPC!")
except Exception as e:
    print(f"⚠️  RPC failed: {e}")
    print("\n📋 MANUAL MIGRATION REQUIRED:")
    print("   1. Open Supabase Dashboard → SQL Editor")
    print(f"   2. Copy from: {migration_path}")
    print("   3. Execute SQL manually")
    print("\nAlternatively, run this SQL directly:")
    print("=" * 60)
    print(sql_content[:500] + "..." if len(sql_content) > 500 else sql_content)
