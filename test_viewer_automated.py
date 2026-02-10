"""
Automated VIEWER flow test - Testing read-only access
VIEWER should have the most restrictive permissions:
- Can view assigned projects
- Can view project files
- CANNOT execute triage/analyze/transform
- CANNOT modify anything
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
print("AUTOMATED VIEWER FLOW TEST")
print("=" * 70)

# Step 1: Get project and TestCollaborator user
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

# Get ViewerTest user
users = client.table("utm_users").select("user_id, username, role").eq(
    "tenant_id", TENANT_ID
).eq("username", "ViewerTest").execute()

if not users.data:
    print("❌ ViewerTest not found - run create_viewer_user.py first")
    exit(1)

viewer_user = users.data[0]
print(f"✅ VIEWER: {viewer_user['username']} ({viewer_user['user_id']})")
print(f"   Role in utm_users: {viewer_user['role']}")

# Step 2: Assign to project as VIEWER
print("\n🔧 Step 2: Assigning ViewerTest to project as VIEWER...")

# Remove existing assignment
existing = client.table("utm_project_members").select("*").eq(
    "project_id", project_id
).eq("user_id", viewer_user["user_id"]).execute()

if existing.data:
    print(f"⚠️  Already assigned, removing first...")
    client.table("utm_project_members").delete().eq(
        "project_id", project_id
    ).eq("user_id", viewer_user["user_id"]).execute()

# Get DEMO33 for added_by
demo33 = client.table("utm_users").select("user_id").eq(
    "tenant_id", TENANT_ID
).eq("username", "DEMO33").execute()

added_by = demo33.data[0]["user_id"] if demo33.data else None

# Insert as VIEWER
client.table("utm_project_members").insert({
    "project_id": project_id,
    "user_id": viewer_user["user_id"],
    "role": "VIEWER",
    "added_by": added_by,
    "added_at": datetime.now(timezone.utc).isoformat()
}).execute()

print(f"✅ ViewerTest assigned as VIEWER")

# Step 3: Reset password
print("\n🔐 Step 3: Resetting password to Test1234...")

manager_headers = {
    "X-Tenant-ID": TENANT_ID,
    "X-User-ID": demo33.data[0]["user_id"],
    "X-Role": "MANAGER"
}

reset_res = requests.post(
    f"{API_BASE}/auth/users/{viewer_user['user_id']}/reset-password",
    headers=manager_headers,
    json={"new_password": "Test1234"}
)

if reset_res.status_code == 200:
    print(f"✅ Password reset")
else:
    print(f"⚠️  Password reset failed: {reset_res.status_code}")

# Step 4: Login as VIEWER
print("\n🔑 Step 4: Login as ViewerTest (VIEWER role)...")

login_res = requests.post(f"{API_BASE}/auth/login", json={
    "username": "ViewerTest",
    "password": "Test1234"
})

if login_res.status_code != 200:
    print(f"❌ Login failed: {login_res.json()}")
    exit(1)

viewer_data = login_res.json()
viewer_headers = {
    "X-Tenant-ID": viewer_data["tenant_id"],
    "X-User-ID": viewer_data["user_id"],
    "X-Role": viewer_data["role"]
}

print(f"✅ Logged in as {viewer_user['username']}")
print(f"   Role: {viewer_data['role']}")

# Step 5: List projects (should only see assigned)
print("\n📋 Step 5: List projects visible to VIEWER...")

projects_res = requests.get(f"{API_BASE}/projects", headers=viewer_headers)

if projects_res.status_code != 200:
    print(f"❌ Failed: {projects_res.status_code}")
    exit(1)

visible_projects = projects_res.json()

if isinstance(visible_projects, list):
    print(f"✅ Projects visible: {len(visible_projects)}")
    for p in visible_projects:
        print(f"   - {p['name']}")
    
    if len(visible_projects) == 1 and visible_projects[0]["project_id"] == project_id:
        print(f"\n✅ ISOLATION VERIFIED: Only sees assigned project!")
    else:
        print(f"\n⚠️  Sees {len(visible_projects)} projects (expected 1)")

# Step 6: View project files (should work - read only)
print("\n📁 Step 6: View project files (READ access)...")

files_res = requests.get(
    f"{API_BASE}/projects/{project_id}/triage/files",
    headers=viewer_headers
)

if files_res.status_code == 200:
    print(f"✅ Can view files (read-only)")
elif files_res.status_code == 403:
    print(f"❌ BLOCKED from viewing files (should be allowed for VIEWER)")
else:
    print(f"⚠️  Files: {files_res.status_code}")

# Step 7: Try to execute triage (should FAIL)
print("\n🚫 Step 7: Try to execute TRIAGE (should FAIL)...")

triage_res = requests.post(
    f"{API_BASE}/projects/{project_id}/triage",
    headers=viewer_headers,
    json={
        "include_screenshots": False,
        "force_rerun": False
    }
)

if triage_res.status_code == 403:
    print(f"✅ CORRECTLY BLOCKED: VIEWER cannot execute triage")
elif triage_res.status_code == 200:
    print(f"❌ SECURITY ISSUE: VIEWER should NOT execute triage!")
else:
    print(f"⚠️  Unexpected: {triage_res.status_code} - {triage_res.json()}")

# Step 8: Try to add member (should FAIL)
print("\n🚫 Step 8: Try to add project member (should FAIL)...")

add_member_res = requests.post(
    f"{API_BASE}/projects/{project_id}/members",
    headers=viewer_headers,
    json={
        "user_id": viewer_user["user_id"],
        "role": "VIEWER"
    }
)

if add_member_res.status_code == 403:
    print(f"✅ CORRECTLY BLOCKED: VIEWER cannot manage members")
elif add_member_res.status_code == 200:
    print(f"❌ SECURITY ISSUE: VIEWER should NOT manage members!")
else:
    print(f"⚠️  Unexpected: {add_member_res.status_code}")

# Step 9: Try to upload files (should FAIL if endpoint exists)
print("\n🚫 Step 9: Try to upload files (should FAIL)...")

# Check if upload endpoint blocks VIEWER
# Note: This would need actual file upload logic
print(f"⚠️  File upload not tested (needs multipart/form-data)")

# Step 10: Compare with COLLABORATOR permissions
print("\n📊 Step 10: Permission comparison...")

print("\nVIEWER permissions:")
print("  ✅ View assigned projects")
print("  ✅ View project files")
print("  ❌ Execute triage/phases")
print("  ❌ Manage members")
print("  ❌ Upload files")

print("\nCOLLABORATOR permissions:")
print("  ✅ View assigned projects")
print("  ✅ View project files")
print("  ✅ Execute triage/phases")
print("  ❌ Manage members")
print("  ✅ Upload files")

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"✅ User: {viewer_user['username']} (VIEWER)")
print(f"✅ Project: {project_name}")
print(f"✅ Assignment: OK")
print(f"✅ Login: OK")
print(f"✅ Project Isolation: {'OK' if len(visible_projects) == 1 else 'NEEDS CHECK'}")
print(f"✅ File Viewing: {'OK' if files_res.status_code == 200 else 'BLOCKED'}")
print(f"✅ Triage Blocked: {'OK' if triage_res.status_code == 403 else 'ISSUE'}")
print(f"✅ Member Management Blocked: {'OK' if add_member_res.status_code == 403 else 'ISSUE'}")
print("=" * 70)
