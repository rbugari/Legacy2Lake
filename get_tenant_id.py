"""
Get correct tenant_id from project
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Project ID
project_id = "ec771d1a-4fe4-4499-970d-54e28de4d926"

# Get project with tenant_id
response = client.table("utm_projects").select("*").eq("project_id", project_id).execute()

if response.data:
    project = response.data[0]
    print(f"Project: {project.get('name', 'unknown')}")
    print(f"Project ID: {project_id}")
    print(f"Tenant ID: {project.get('tenant_id')}")
    print(f"Owner ID: {project.get('owner_id')}")
else:
    print("❌ Project not found")
