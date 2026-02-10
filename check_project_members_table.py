"""
Check if utm_project_members table exists and show current data
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 70)
print("CHECKING utm_project_members TABLE")
print("=" * 70)

try:
    # Try to query the table
    result = supabase.table("utm_project_members").select("*").execute()
    
    print(f"\n✅ Table exists!")
    print(f"\n📊 Current members: {len(result.data)}")
    
    if result.data:
        print("\n" + "=" * 70)
        print("CURRENT PROJECT MEMBERS")
        print("=" * 70)
        for member in result.data:
            print(f"\n  Project: {member.get('project_id')}")
            print(f"  User: {member.get('user_id')}")
            print(f"  Role: {member.get('role')}")
            print(f"  Added: {member.get('added_at')}")
    else:
        print("\n⚠️  No members assigned yet")
        
except Exception as e:
    error_msg = str(e)
    if "does not exist" in error_msg or "not found" in error_msg.lower():
        print("\n❌ Table utm_project_members does NOT exist")
        print("\n📝 You need to apply migration 021:")
        print("   supabase_migrations/021_v3.9_project_members_table.sql")
    else:
        print(f"\n❌ Error: {error_msg}")

# Also check projects
print("\n" + "=" * 70)
print("PROJECTS IN SYSTEM")
print("=" * 70)

try:
    projects = supabase.table("utm_projects").select(
        "project_id, project_name, tenant_id, created_at"
    ).execute()
    
    print(f"\n📦 Total projects: {len(projects.data)}")
    
    if projects.data:
        for proj in projects.data[:5]:  # Show first 5
            print(f"\n  • {proj.get('project_name')}")
            print(f"    ID: {proj.get('project_id')}")
            print(f"    Tenant: {proj.get('tenant_id')}")
except Exception as e:
    print(f"❌ Error fetching projects: {e}")
