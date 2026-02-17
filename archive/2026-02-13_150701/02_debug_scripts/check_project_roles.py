"""
Check project members and their roles
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
tenant_id = "daac0ee6-3b28-412d-8acd-43ec51149188"

print("="*70)
print("🔍 Checking Project Members")
print("="*70)

# Get project members
try:
    result = supabase.table("project_members").select("*").eq("project_id", project_id).execute()
    
    if result.data:
        print(f"\n📋 Project members: {len(result.data)}")
        for member in result.data:
            print(f"\n   User ID: {member.get('user_id')}")
            print(f"   Role: {member.get('role')}")
            print(f"   Active: {member.get('is_active', True)}")
    else:
        print("\n❌ No members found")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

# Get tenant users
print("\n" + "="*70)
print("🔍 Checking Tenant Users")
print("="*70)

try:
    result = supabase.table("users").select("user_id, email, role").eq("tenant_id", tenant_id).execute()
    
    if result.data:
        print(f"\n📋 Tenant users: {len(result.data)}")
        for user in result.data:
            print(f"\n   User ID: {user.get('user_id')}")
            print(f"   Email: {user.get('email')}")
            print(f"   Role: {user.get('role')}")
    else:
        print("\n❌ No users found")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "="*70)
print("💡 Need COLLABORATOR, MANAGER, or ADMIN role to execute Triage")
print("="*70)
