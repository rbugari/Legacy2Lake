"""
Create a real VIEWER user for testing
"""
from supabase import create_client
import os
from dotenv import load_dotenv
import requests

load_dotenv()

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

# Get DEMO33 credentials to create user
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

demo33 = client.table("utm_users").select("user_id").eq(
    "tenant_id", TENANT_ID
).eq("username", "DEMO33").execute()

if not demo33.data:
    print("❌ DEMO33 not found")
    exit(1)

manager_headers = {
    "X-Tenant-ID": TENANT_ID,
    "X-User-ID": demo33.data[0]["user_id"],
    "X-Role": "MANAGER"
}

# Create VIEWER user
print("Creating ViewerTest user...")

create_res = requests.post(
    f"{API_BASE}/auth/users",
    headers=manager_headers,
    json={
        "username": "ViewerTest",
        "email": "viewer@test.com",
        "password": "Test1234",
        "role": "VIEWER",
        "display_name": "Viewer Test User"
    }
)

if create_res.status_code == 200:
    user_data = create_res.json()
    print(f"✅ Created: {user_data}")
    print(f"\nUser ID: {user_data.get('user_id')}")
    print(f"Username: ViewerTest")
    print(f"Password: Test1234")
    print(f"Role: VIEWER")
else:
    print(f"❌ Failed: {create_res.status_code}")
    print(f"Response: {create_res.json()}")
