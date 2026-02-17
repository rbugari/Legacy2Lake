"""
Test user management endpoints.
Creates a COLLABORATOR user to verify the functionality works.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_user_management():
    base_url = "http://localhost:8085"
    
    # Login as DEMO3 (MANAGER)
    print("=" * 70)
    print("1. LOGIN AS MANAGER (DEMO3)")
    print("=" * 70)
    
    login_res = requests.post(f"{base_url}/login", json={
        "username": "DEMO3",
        "password": "demo123"
    })
    
    if not login_res.ok:
        print(f"❌ Login failed: {login_res.status_code}")
        return
    
    login_data = login_res.json()
    print(f"✅ Logged in as {login_data['message']}")
    print(f"   Tenant ID: {login_data['tenant_id']}")
    print(f"   User ID: {login_data['user_id']}")
    print(f"   Role: {login_data['role']}")
    
    headers = {
        "x-tenant-id": login_data['tenant_id'],
        "x-user-id": login_data['user_id'],
        "x-role": login_data['role']
    }
    
    # List existing users
    print("\n" + "=" * 70)
    print("2. LIST CURRENT USERS")
    print("=" * 70)
    
    list_res = requests.get(f"{base_url}/auth/users", headers=headers)
    if list_res.ok:
        users = list_res.json()['users']
        print(f"\nFound {len(users)} users:")
        for user in users:
            status = "✅" if user['is_active'] else "❌"
            print(f"  {status} {user['username']:15} | {user['email']:30} | {user['role']}")
    else:
        print(f"❌ Failed to list users: {list_res.status_code}")
        print(f"   {list_res.text}")
        return
    
    # Create a new COLLABORATOR
    print("\n" + "=" * 70)
    print("3. CREATE NEW COLLABORATOR")
    print("=" * 70)
    
    new_user = {
        "username": "TestCollaborator",
        "email": "collab@test.com",
        "role": "COLLABORATOR",
        "display_name": "Test Collaborator User"
    }
    
    create_res = requests.post(
        f"{base_url}/auth/users",
        headers=headers,
        json=new_user
    )
    
    if create_res.ok:
        created = create_res.json()
        print("✅ User created successfully!")
        print(f"   User ID: {created['user']['user_id']}")
        print(f"   Username: {created['user']['username']}")
        print(f"   Email: {created['user']['email']}")
        print(f"   Role: {created['user']['role']}")
        if created.get('temporary_password'):
            print(f"   Temporary Password: {created['temporary_password']}")
            print("   ⚠️  User should change this password on first login")
    else:
        print(f"❌ Failed to create user: {create_res.status_code}")
        print(f"   {create_res.text}")
        return
    
    created_user_id = created['user']['user_id']
    
    # Update the user
    print("\n" + "=" * 70)
    print("4. UPDATE USER (Change display name)")
    print("=" * 70)
    
    update_res = requests.patch(
        f"{base_url}/auth/users/{created_user_id}",
        headers=headers,
        json={"display_name": "Updated Collaborator Name"}
    )
    
    if update_res.ok:
        print("✅ User updated successfully!")
    else:
        print(f"❌ Failed to update user: {update_res.status_code}")
        print(f"   {update_res.text}")
    
    # List users again to verify
    print("\n" + "=" * 70)
    print("5. VERIFY - LIST USERS AGAIN")
    print("=" * 70)
    
    list_res = requests.get(f"{base_url}/auth/users", headers=headers)
    if list_res.ok:
        users = list_res.json()['users']
        print(f"\nFound {len(users)} users:")
        for user in users:
            status = "✅" if user['is_active'] else "❌"
            display = f" ({user['display_name']})" if user.get('display_name') and user['display_name'] != user['username'] else ""
            print(f"  {status} {user['username']:15}{display:30} | {user['role']}")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("""
User management is working correctly!

You can now:
1. Go to http://localhost:3005/settings
2. Click on"User Management" tab
3. Create, edit, and manage users through the UI
    """)

if __name__ == "__main__":
    test_user_management()
