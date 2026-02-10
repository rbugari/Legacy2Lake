"""
Test Project Members Management
Requires migration 021 to be applied first.
"""
import requests

API_BASE = "http://localhost:8085"

# Login as DEMO3 (MANAGER)
print("=" * 70)
print("1. LOGIN AS MANAGER (DEMO3)")
print("=" * 70)

login_res = requests.post(f"{API_BASE}/auth/login", json={
    "username": "demo3",
    "password": "demo1234"
})

if not login_res.ok:
    print(f"❌ Login failed: {login_res.status_code}")
    print(login_res.text)
    exit(1)

auth = login_res.json()
print(f"✅ Logged in as {auth['username']}")
print(f"   Tenant ID: {auth['tenant_id']}")
print(f"   User ID: {auth['user_id']}")
print(f"   Role: {auth['role']}")

headers = {
    "x-tenant-id": auth["tenant_id"],
    "x-user-id": auth["user_id"],
    "x-role": auth["role"]
}

# List projects
print("\n" + "=" * 70)
print("2. LIST PROJECTS")
print("=" * 70)

projects_res = requests.get(f"{API_BASE}/projects", headers=headers)

if projects_res.ok:
    projects = projects_res.json().get("projects", [])
    print(f"\n📦 Found {len(projects)} projects:")
    for proj in projects[:5]:  # Show first 5
        print(f"  • {proj.get('name')} ({proj.get('project_id')})")
    
    if len(projects) > 0:
        test_project = projects[0]
        project_id = test_project["project_id"]
        
        # List members of first project
        print("\n" + "=" * 70)
        print(f"3. LIST MEMBERS OF '{test_project['name']}'")
        print("=" * 70)
        
        members_res = requests.get(f"{API_BASE}/projects/{project_id}/members", headers=headers)
        
        if members_res.ok:
            data = members_res.json()
            members = data.get("members", [])
            print(f"\n👥 Current members: {len(members)}")
            
            if members:
                for member in members:
                    print(f"  • {member['username']} - {member['role']}")
            else:
                print("  (No members assigned yet)")
                
                # Try to add DEMO34 (COLLABORATOR) to project
                print("\n" + "=" * 70)
                print(f"4. ADD DEMO34 TO PROJECT")
                print("=" * 70)
                
                # First get DEMO34's user_id
                users_res = requests.get(f"{API_BASE}/auth/users", headers=headers)
                if users_res.ok:
                    users = users_res.json().get("users", [])
                    demo34 = next((u for u in users if u["username"] == "DEMO34"), None)
                    
                    if demo34:
                        add_res = requests.post(
                            f"{API_BASE}/projects/{project_id}/members",
                            headers=headers,
                            json={
                                "user_id": demo34["user_id"],
                                "role": "COLLABORATOR"
                            }
                        )
                        
                        if add_res.ok:
                            print(f"✅ {add_res.json()['message']}")
                            
                            # List members again
                            members_res2 = requests.get(f"{API_BASE}/projects/{project_id}/members", headers=headers)
                            if members_res2.ok:
                                members2 = members_res2.json().get("members", [])
                                print(f"\n👥 Updated members: {len(members2)}")
                                for member in members2:
                                    print(f"  • {member['username']} - {member['role']}")
                        else:
                            error = add_res.json()
                            print(f"❌ Failed to add user: {error.get('detail', 'Unknown error')}")
                    else:
                        print("❌ DEMO34 user not found")
        else:
            error = members_res.json()
            print(f"❌ Failed to list members: {error.get('detail', 'Unknown error')}")
    else:
        print("\n⚠️  No projects found. Create a project first.")
else:
    error = projects_res.json()
    print(f"❌ Failed to list projects: {error.get('detail', 'Unknown error')}")

print("\n" + "=" * 70)
print("✅ TEST COMPLETE")
print("=" * 70)
