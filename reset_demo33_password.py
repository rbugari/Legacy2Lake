"""
Reset DEMO33 password to known value for testing
"""
import os
import bcrypt
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
NEW_PASSWORD = "Test1234"

# Find DEMO33
users = client.table("utm_users").select("user_id, username").eq(
    "tenant_id", TENANT_ID
).eq("username", "DEMO33").execute()

if not users.data:
    print("❌ DEMO33 not found")
    exit(1)

user_id = users.data[0]["user_id"]
username = users.data[0]["username"]

# Hash password
hashed = bcrypt.hashpw(NEW_PASSWORD.encode('utf-8'), bcrypt.gensalt(rounds=12))

# Update password
client.table("utm_users").update({
    "password_hash": hashed.decode('utf-8')
}).eq("user_id", user_id).execute()

print(f"✅ Password reset for {username}")
print(f"   New password: {NEW_PASSWORD}")
print(f"   User ID: {user_id}")
