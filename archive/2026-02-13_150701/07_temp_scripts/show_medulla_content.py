"""Show actual medulla content"""
import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

result = supabase.table("utm_objects").select("source_name, metadata").eq("project_id", project_id).eq("source_name", "DimCustomers.dtsx").single().execute()

if result.data:
    metadata = result.data.get("metadata", {})
    medulla = metadata.get("logical_medulla", {})
    connections = metadata.get("connections", [])
    
    print("="*70)
    print("📄 DimCustomers.dtsx - Medulla Content")
    print("="*70)
    print("\n🔗 Connections:")
    print(json.dumps(connections, indent=2))
    print("\n🧠 Logical Medulla:")
    print(json.dumps(medulla, indent=2))
    print("\n" + "="*70)
else:
    print("❌ Asset not found")
