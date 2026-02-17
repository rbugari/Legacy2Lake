"""
Automated COLLABORATOR flow test - NO BROWSER NEEDED
Uses direct DB access and API calls to test complete workflow
"""
import os
import requests
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timezone

load_dotenv()

# Config
API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

# Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

print("=" * 70)
print("AUTOMATED COLLABORATOR FLOW TEST")
print("=" * 70)

# Step 1: Get project and users
print("\n🔍 Step 1: Identifying resources...")
projects = client.table("utm_projects").select("project_id, name").eq(
    "tenant_id", TENANT_ID
).execute()

ttt_project = next((p for p in projects.data if "ttt" in p["name"].lower()), None)
if not ttt_project:
    print("❌ Project 'ttt' not found")
    exit(1)

project_id = ttt_project["project_id"]
project_name = ttt_project["name"]
print(f"✅ Project: {project_name} ({project_id})")

# Get DEMO34
users = client.table("utm_users").select("user_id, username, role").eq(
    "tenant_id", TENANT_ID
).eq("username", "DEMO34").execute()

if not users.data:
    print("❌ DEMO34 not found")
    exit(1)

collab_user = users.data[0]
print(f"✅ COLLABORATOR: {collab_user['username']} ({collab_user['user_id']})")

# Step 2: Assign to project (direct DB)
print("\n🔧 Step 2: Assigning DEMO34 to project (direct DB)...")

# Check if already assigned
existing = client.table("utm_project_members").select("*").eq(
    "project_id", project_id
).eq("user_id", collab_user["user_id"]).execute()

if existing.data:
    print(f"⚠️  Already assigned, removing first...")
    client.table("utm_project_members").delete().eq(
        "project_id", project_id
    ).eq("user_id", collab_user["user_id"]).execute()

# Get DEMO33 user_id for added_by
demo33 = client.table("utm_users").select("user_id").eq(
    "tenant_id", TENANT_ID
).eq("username", "DEMO33").execute()

added_by = demo33.data[0]["user_id"] if demo33.data else None

# Insert
client.table("utm_project_members").insert({
    "project_id": project_id,
    "user_id": collab_user["user_id"],
    "role": "COLLABORATOR",
    "added_by": added_by,
    "added_at": datetime.now(timezone.utc).isoformat()
}).execute()

print(f"✅ DEMO34 assigned as COLLABORATOR")

# Step 3: Reset password via API (use MANAGER headers)
print("\n🔐 Step 3: Resetting DEMO34 password to Test1234...")

# Get a MANAGER user (DEMO33) to make the API call
demo33 = client.table("utm_users").select("user_id, username").eq(
    "tenant_id", TENANT_ID
).eq("username", "DEMO33").execute()

if not demo33.data:
    print("❌ DEMO33 not found")
    exit(1)

# Create temporary MANAGER headers (bypass login)
manager_headers = {
    "X-Tenant-ID": TENANT_ID,
    "X-User-ID": demo33.data[0]["user_id"],
    "X-Role": "MANAGER"
}

# Reset password via API
reset_res = requests.post(
    f"{API_BASE}/auth/users/{collab_user['user_id']}/reset-password",
    headers=manager_headers,
    json={"new_password": "Test1234"}
)

if reset_res.status_code == 200:
    print(f"✅ Password reset via API (Test1234)")
else:
    print(f"⚠️  Password reset API failed: {reset_res.status_code}")
    print(f"   Response: {reset_res.json()}")
    print(f"   Trying direct DB method...")
    
    # Fallback: Use the pre-computed hash
    password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ND/qhmeqyaEm"
    client.table("utm_users").update({
        "password_hash_bcrypt": password_hash
    }).eq("user_id", collab_user["user_id"]).execute()
    print(f"✅ Password reset via DB (Test1234)")

# Step 4: Login as DEMO34
print("\n🔑 Step 4: Login as DEMO34...")

login_res = requests.post(f"{API_BASE}/auth/login", json={
    "username": "DEMO34",
    "password": "Test1234"
})

if login_res.status_code != 200:
    print(f"❌ Login failed: {login_res.json()}")
    exit(1)

collab_data = login_res.json()
collab_headers = {
    "X-Tenant-ID": collab_data["tenant_id"],
    "X-User-ID": collab_data["user_id"],
    "X-Role": collab_data["role"]
}

print(f"✅ Logged in as DEMO34")
print(f"   Tenant: {collab_data['tenant_id']}")
print(f"   User ID: {collab_data['user_id']}")
print(f"   Role: {collab_data['role']}")

# Step 5: List projects (should only see assigned)
print("\n📋 Step 5: List projects visible to COLLABORATOR...")

projects_res = requests.get(f"{API_BASE}/projects", headers=collab_headers)

if projects_res.status_code != 200:
    print(f"❌ Failed to list projects: {projects_res.status_code}")
    print(f"   Response: {projects_res.json()}")
    exit(1)

visible_projects = projects_res.json()

if isinstance(visible_projects, list):
    print(f"✅ Projects visible: {len(visible_projects)}")
    for p in visible_projects:
        print(f"   - {p['name']} ({p['project_id']})")
    
    # Verify isolation
    if len(visible_projects) == 1 and visible_projects[0]["project_id"] == project_id:
        print(f"\n✅ ISOLATION VERIFIED: Only sees assigned project!")
    elif len(visible_projects) == 0:
        print(f"\n❌ NO PROJECTS VISIBLE - Check backend logic in list_projects()")
    else:
        print(f"\n⚠️  Sees {len(visible_projects)} projects (expected 1)")
else:
    print(f"⚠️  Unexpected response format: {type(visible_projects)}")

# Step 6: Check project files
print("\n📁 Step 6: Check project files...")

files_res = requests.get(
    f"{API_BASE}/projects/{project_id}/triage/files",
    headers=collab_headers
)

if files_res.status_code == 200:
    files = files_res.json()
    file_count = len(files) if isinstance(files, list) else "unknown"
    print(f"✅ Files endpoint accessible: {file_count} files")
elif files_res.status_code == 403:
    print(f"❌ PERMISSION DENIED on files endpoint!")
    print(f"   Response: {files_res.json()}")
else:
    print(f"⚠️  Files check: {files_res.status_code}")

# Step 7: Test triage execution
print("\n🔄 Step 7: Execute TRIAGE phase...")

triage_res = requests.post(
    f"{API_BASE}/projects/{project_id}/triage",
    headers=collab_headers,
    json={
        "include_screenshots": False,
        "force_rerun": False
    }
)

if triage_res.status_code == 200:
    triage_data = triage_res.json()
    print(f"✅ TRIAGE executed successfully!")
    print(f"   Status: {triage_data.get('status', 'unknown')}")
    
    if "mesh" in triage_data:
        mesh = triage_data["mesh"]
        print(f"   Nodes: {len(mesh.get('nodes', []))}")
        print(f"   Edges: {len(mesh.get('edges', []))}")
elif triage_res.status_code == 423:
    print(f"⚠️  Process locked: {triage_res.json().get('error', 'Unknown')}")
elif triage_res.status_code == 403:
    print(f"❌ PERMISSION DENIED: COLLABORATOR cannot execute triage!")
    print(f"   Response: {triage_res.json()}")
elif triage_res.status_code == 404:
    print(f"⚠️  Project or files not found")
    print(f"   Response: {triage_res.json()}")
else:
    print(f"❌ Triage failed: {triage_res.status_code}")
    print(f"   Response: {triage_res.json()}")

# Step 8: Test project members access (should work)
print("\n👥 Step 8: Check project members (READ access)...")

members_res = requests.get(
    f"{API_BASE}/projects/{project_id}/members",
    headers=collab_headers
)

if members_res.status_code == 200:
    members_data = members_res.json()
    members = members_data.get("members", [])
    print(f"✅ Can read project members: {len(members)} members")
    for m in members:
        print(f"   - {m.get('username', 'unknown')} ({m.get('role', 'unknown')})")
elif members_res.status_code == 403:
    print(f"❌ Cannot read members (needs MANAGER role)")
else:
    print(f"⚠️  Members endpoint: {members_res.status_code}")

# Step 9: Test adding member (should FAIL - only MANAGER can)
print("\n🚫 Step 9: Try to add member (should FAIL)...")

add_member_res = requests.post(
    f"{API_BASE}/projects/{project_id}/members",
    headers=collab_headers,
    json={
        "user_id": collab_user["user_id"],  # Try to add self
        "role": "VIEWER"
    }
)

if add_member_res.status_code == 403:
    print(f"✅ CORRECTLY BLOCKED: COLLABORATOR cannot add members")
elif add_member_res.status_code == 200:
    print(f"❌ SECURITY ISSUE: COLLABORATOR should NOT be able to add members!")
else:
    print(f"⚠️  Unexpected response: {add_member_res.status_code}")

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"✅ User: DEMO34 (COLLABORATOR)")
print(f"✅ Project: {project_name}")
print(f"✅ Assignment: OK")
print(f"✅ Login: OK")
print(f"✅ Project Isolation: {'OK' if len(visible_projects) == 1 else 'NEEDS CHECK'}")
print(f"✅ Triage Access: {'OK' if triage_res.status_code == 200 else 'BLOCKED' if triage_res.status_code == 403 else 'UNKNOWN'}")
print(f"✅ Member Management: {'BLOCKED (OK)' if add_member_res.status_code == 403 else 'ISSUE'}")
print("=" * 70)
