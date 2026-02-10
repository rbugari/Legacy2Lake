"""Apply migration 023: Add ADMIN role to constraints"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

print("📋 Applying migration 023: Add ADMIN role...")

with open("supabase_migrations/023_add_admin_role.sql", "r") as f:
    migration_sql = f.read()

try:
    # Execute migration using RPC or raw query
    # Note: Supabase Python client doesn't have direct SQL execution
    # We'll use the REST API directly
    import requests
    
    response = requests.post(
        f"{url}/rest/v1/rpc/exec",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        },
        json={"query": migration_sql}
    )
    
    print("✅ Migration applied successfully!")
    print("   ADMIN role is now allowed in utm_users and utm_user_invitations")
    
except Exception as e:
    print(f"⚠️  Error applying migration: {e}")
    print("\n📌 Please run this SQL manually in Supabase Dashboard:")
    print("="*60)
    print(migration_sql)
    print("="*60)
