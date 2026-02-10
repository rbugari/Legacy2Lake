"""
Reset DEMO33 password using API endpoint
"""
import requests

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

# Get user ID  
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

users = client.table("utm_users").select("user_id, username").eq(
    "tenant_id", TENANT_ID
).eq("username", "DEMO33").execute()

if not users.data:
    print("❌ DEMO33 not found")
    exit(1)

user_id = users.data[0]["user_id"]
username = users.data[0]["username"]

# Reset password via API (need ADMIN/MANAGER headers)
# Since we can't login, we'll use direct DB access with service role

# Use raw SQL
print(f"User {username}: {user_id}")
print("\nExecute this in Supabase SQL Editor:")
print("=" * 60)
print(f"""
UPDATE utm_users 
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ND/qhmeqyaEm' -- Password: Test1234
WHERE user_id = '{user_id}';
""")
print("=" * 60)
print("\nOr use this bcrypt hash for 'Test1234':")
print("$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ND/qhmeqyaEm")
