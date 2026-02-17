"""
Find projects with repo_url
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

tenant_id = "daac0ee6-3b28-412d-8acd-43ec51149188"

print("="*70)
print("🔍 Finding Projects with Files")
print("="*70)

# Get all projects for tenant
result = supabase.table("utm_projects").select("project_id, name, repo_url, status, stage").eq("tenant_id", tenant_id).execute()

if result.data:
    print(f"\n📋 Found {len(result.data)} projects:")
    
    for proj in result.data:
        print(f"\n   Project: {proj['name']}")
        print(f"   ID: {proj['project_id']}")
        print(f"   Status: {proj['status']} (Stage {proj['stage']})")
        print(f"   Repo: {proj['repo_url']}")
        
        if proj['repo_url']:
            print(f"   ✅ HAS FILES - Use this project_id")
else:
    print("\n❌ No projects found")

print("\n" + "="*70)
