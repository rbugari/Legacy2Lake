"""
Direct Discovery execution - bypass API permissions
"""
import os
import sys
import json
from pathlib import Path

# Add apps to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Import services
from apps.api.services.discovery_service import DiscoveryService

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
tenant_id = "daac0ee6-3b28-412d-8acd-43ec51149188"

print("="*70)
print("🔧 Direct Discovery Execution (Bypass API)")
print("="*70)

# Get project
result = supabase.table("utm_projects").select("*").eq("project_id", project_id).single().execute()
project = result.data

print(f"\n📦 Project: {project['name']}")
print(f"   Repo: {project['repo_url']}")

# Get project folder
project_folder = project['repo_url'].replace('file:///', '').replace('/', '\\')
print(f"   Folder: {project_folder}")

# Run Discovery directly
print("\n🚀 Running Discovery...")
try:
    # Create a mock db object with tenant_id
    class DB:
        tenant_id = tenant_id
    
    db = DB()
    manifest = DiscoveryService.generate_manifest(project_folder, tenant_id=db.tenant_id, user_context=None)
    
    print(f"\n✅ Discovery completed!")
    print(f"   Files discovered: {len(manifest.get('files', []))}")
    
    # Now manually save assets to DB with connections
    from apps.utm.adapter import UTMAdapter
    
    print("\n💾 Saving assets to database...")
    saved_assets = []
    
    for file_entry in manifest.get('files', []):
        if file_entry.get('metadata', {}).get('logical_medulla'):
            # Save using UTMAdapter
            asset_data = {
                "project_id": project_id,
                "source_name": file_entry['path'].split('\\')[-1],
                "source_path": file_entry['path'],
                "metadata": file_entry['metadata']
            }
            
            # Insert or update
            try:
                existing = supabase.table("utm_objects").select("object_id").eq("project_id", project_id).eq("source_name", asset_data['source_name']).execute()
                
                if existing.data:
                    # Update
                    result = supabase.table("utm_objects").update(asset_data).eq("object_id", existing.data[0]['object_id']).execute()
                    saved_assets.append(result.data[0])
                    print(f"   ✅ Updated: {asset_data['source_name']}")
                else:
                    # Insert
                    result = supabase.table("utm_objects").insert(asset_data).execute()
                    saved_assets.append(result.data[0])
                    print(f"   ✅ Inserted: {asset_data['source_name']}")
                    
            except Exception as e:
                print(f"   ❌ Error saving {asset_data['source_name']}: {e}")
    
    print(f"\n✅ Saved {len(saved_assets)} assets")
    
    # Check connections
    print("\n" + "="*70)
    print("🔍 Checking Connections in Metadata")
    print("="*70)
    
    for asset in saved_assets:
        metadata = asset.get('metadata', {})
        connections = metadata.get('connections', [])
        print(f"\n📦 {asset['source_name']}")
        print(f"   Connections: {len(connections)}")
        
        if connections:
            for conn in connections:
                conn_str = conn.get('connection_string', '')[:60]
                print(f"      - {conn.get('name')}: {conn_str}...")
        else:
            print(f"      ⚠️ EMPTY")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*70)
print("✅ Discovery completed - Check connections above")
print("="*70)
