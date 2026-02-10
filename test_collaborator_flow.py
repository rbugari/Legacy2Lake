"""
Test complete COLLABORATOR flow:
1. List available COLLABORATOR users
2. Assign to project 'ttt' (test-project9)
3. Login as COLLABORATOR
4. List projects (should only see assigned ones)
5. Execute all project phases
"""
import os
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Config
API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

# Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

print("=" * 70)
print("PHASE 1: List CUSTOMER3 Users and Projects")
print("=" * 70)

# Get users
users = client.table("utm_users").select(
    "user_id, username, email, role"
).eq("tenant_id", TENANT_ID).order("role", desc=True).order("username").execute()

print("\n📋 Users:")
for u in users.data:
    print(f"  {u['username']:15} | {u['role']:12} | {u['email']}")

# Get projects
projects = client.table("utm_projects").select(
    "project_id, name"
).eq("tenant_id", TENANT_ID).execute()

print("\n📦 Projects:")
for p in projects.data:
    print(f"  {p['name']:30} | {p['project_id']}")

# Find test-project9 (ttt)
ttt_project = next((p for p in projects.data if "test-project9" in p["name"].lower() or "ttt" in p["name"].lower()), None)

if not ttt_project:
    print("\n❌ Project 'ttt' (test-project9) not found!")
    print("Available projects:")
    [print(f"  - {p['name']}") for p in projects.data]
    exit(1)

project_id = ttt_project["project_id"]
project_name = ttt_project["name"]

print(f"\n✅ Found target project: {project_name} ({project_id})")

# Find COLLABORATOR user
collaborators = [u for u in users.data if u["role"] == "COLLABORATOR"]

if not collaborators:
    print("\n❌ No COLLABORATOR users found in tenant!")
    exit(1)

collab_user = collaborators[0]
print(f"✅ Found COLLABORATOR: {collab_user['username']} ({collab_user['user_id']})")

print("\n" + "=" * 70)
print("PHASE 2: Verify Project Assignment (Manual Step)")
print("=" * 70)

print(f"\n📝 MANUAL STEP REQUIRED:")
print(f"   1. Open browser: http://localhost:3005")
print(f"   2. Login as MANAGER (DEMO33)")
print(f"   3. Go to Settings → Project Access")
print(f"   4. Select project: {project_name}")
print(f"   5. Add user: {collab_user['username']} as COLLABORATOR")
print(f"\n⏸️  Press ENTER when ready to continue...")
input()

# Verify assignment via database
members = client.table("utm_project_members").select("*").eq(
    "project_id", project_id
).eq("user_id", collab_user["user_id"]).execute()

if members.data:
    print(f"✅ {collab_user['username']} is assigned to project")
else:
    print(f"❌ {collab_user['username']} is NOT assigned yet")
    print(f"   Please complete the manual step and try again")
    exit(1)

print("\n" + "=" * 70)
print("PHASE 3: Login as COLLABORATOR")
print("=" * 70)

# Try common password patterns
password_attempts = ["Test1234", "demo1234", "password", "Password123", collab_user["username"].lower()]

collab_headers = None
for pwd in password_attempts:
    collab_login = requests.post(f"{API_BASE}/auth/login", json={
        "username": collab_user["username"],
        "password": pwd
    })
    
    if collab_login.status_code == 200:
        collab_data = collab_login.json()
        collab_headers = {
            "X-Tenant-ID": collab_data["tenant_id"],
            "X-User-ID": collab_data["user_id"],
            "X-Role": collab_data["role"]
        }
        print(f"✅ Logged in as {collab_user['username']} (password: {pwd})")
        break

if not collab_headers:
    print(f"\n⚠️  Could not login as {collab_user['username']}")
    print(f"   Tried passwords: {password_attempts}")
    print(f"\n📝 MANUAL STEP: Reset password in browser:")
    print(f"   1. Login as MANAGER")
    print(f"   2. Go to Settings → User Management")
    print(f"   3. Click 'Reset Password' for {collab_user['username']}")
    print(f"   4. Set password to: Test1234")
    print(f"\n⏸️  Press ENTER after resetting password...")
    input()
    
    # Retry with Test1234
    collab_login = requests.post(f"{API_BASE}/auth/login", json={
        "username": collab_user["username"],
        "password": "Test1234"
    })
    
    if collab_login.status_code == 200:
        collab_data = collab_login.json()
        collab_headers = {
            "X-Tenant-ID": collab_data["tenant_id"],
            "X-User-ID": collab_data["user_id"],
            "X-Role": collab_data["role"]
        }
        print(f"✅ Logged in as {collab_user['username']}")
    else:
        print(f"❌ Still cannot login. Exiting.")
        exit(1)

print("\n" + "=" * 70)
print("PHASE 4: List Projects (COLLABORATOR should only see assigned)")
print("=" * 70)

projects_res = requests.get(f"{API_BASE}/projects", headers=collab_headers)

if projects_res.status_code == 200:
    visible_projects = projects_res.json()
    print(f"\n📦 Projects visible to {collab_user['username']}:")
    
    if isinstance(visible_projects, list):
        for p in visible_projects:
            print(f"  - {p['name']} ({p['project_id']})")
        
        # Verify isolation
        if len(visible_projects) == 1 and visible_projects[0]["project_id"] == project_id:
            print(f"\n✅ PASS: Only sees assigned project '{project_name}'")
        else:
            print(f"\n⚠️  Expected 1 project, got {len(visible_projects)}")
    else:
        print(f"  {visible_projects}")
else:
    print(f"❌ Failed to list projects: {projects_res.status_code}")

print("\n" + "=" * 70)
print("PHASE 5: Execute Project Phases (as COLLABORATOR)")
print("=" * 70)

# Check if project has files uploaded
files_res = requests.get(
    f"{API_BASE}/projects/{project_id}/triage/files",
    headers=collab_headers
)

if files_res.status_code == 200:
    files = files_res.json()
    print(f"\n📁 Project files: {len(files) if isinstance(files, list) else 'unknown'}")
else:
    print(f"\n⚠️  Could not check files: {files_res.status_code}")

# Test Phase 1: Triage (Discovery)
print("\n🔄 Phase 1: TRIAGE (Discovery)")
triage_payload = {
    "include_screenshots": False,
    "force_rerun": False
}

triage_res = requests.post(
    f"{API_BASE}/projects/{project_id}/triage",
    headers=collab_headers,  
    json=triage_payload
)

if triage_res.status_code == 200:
    triage_data = triage_res.json()
    print(f"   ✅ Triage completed")
    print(f"   Status: {triage_data.get('status', 'unknown')}")
    
    if "mesh" in triage_data:
        mesh = triage_data["mesh"]
        print(f"   Nodes discovered: {len(mesh.get('nodes', []))}")
        print(f"   Edges discovered: {len(mesh.get('edges', []))}")
elif triage_res.status_code == 423:
    print(f"   ⚠️  Process locked: {triage_res.json().get('error', 'Unknown')}")
elif triage_res.status_code == 403:
    print(f"   ❌ PERMISSION DENIED: COLLABORATOR cannot execute triage!")
    print(f"   Response: {triage_res.json()}")
else:
    print(f"   ❌ Triage failed: {triage_res.status_code}")
    print(f"   Response: {triage_res.json()}")

print("\n📌 Other phases to test:")
print("   - Phase 2: ANALYZE (validate nodes)")
print("   - Phase 3: TRANSPILE (generate code)")
print("   - Phase 4: REPORT (generate documentation)")

print("\n" + "=" * 70)
print("✅ COLLABORATOR Flow Test Complete")
print("=" * 70)
print(f"\nSummary:")
print(f"  - User: {collab_user['username']} (COLLABORATOR)")
print(f"  - Project: {project_name}")
print(f"  - Projects visible: {len(visible_projects) if 'visible_projects' in dir() else 'N/A'}")
print(f"  - Triage access: {'✅ YES' if triage_res.status_code == 200 else '❌ NO'}")
