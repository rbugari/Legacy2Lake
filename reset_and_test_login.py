"""
Reset DEMO34 password to Test1234 using API
"""
import requests
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

# Get DEMO33 user_id
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

demo33 = client.table("utm_users").select("user_id").eq(
    "tenant_id", TENANT_ID
).eq("username", "DEMO33").execute()

demo34 = client.table("utm_users").select("user_id").eq(
    "tenant_id", TENANT_ID
).eq("username", "DEMO34").execute()

if not demo33.data or not demo34.data:
    print("❌ Users not found")
    exit(1)

manager_id = demo33.data[0]["user_id"]
target_id = demo34.data[0]["user_id"]

print(f"Manager: {manager_id}")
print(f"Target: {target_id}")
print("\nResetting password...")

# Reset password
response = requests.post(
    f"{API_BASE}/auth/users/{target_id}/reset-password",
    headers={
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": manager_id,
        "X-Role": "MANAGER"
    },
    json={"new_password": "Test1234"}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 200:
    print("\n✅ Password reset successful!")
    print("\nNow trying login...")
    
    login_response = requests.post(
        f"{API_BASE}/auth/login",
        json={
            "username": "DEMO34",
            "password": "Test1234"
        }
    )
    
    print(f"Login Status: {login_response.status_code}")
    print(f"Login Response: {login_response.json()}")
