import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

from apps.api.services.discovery_service import DiscoveryService
from apps.api.services.persistence_service import SupabasePersistence, PersistenceService

# Tenant and Project from failure case
TENANT_ID = "f98edb5e-4165-4c49-9fce-18894e8a818c"
PROJECT_ID = "dd13fc92-4091-456a-8ce4-712406ceb831" # TEST9

async def debug_agent_a():
    print(f"--- Debugging Agent A Manifest for Project {PROJECT_ID} ---")
    print(f"Tenant: {TENANT_ID}")
    
    # 1. Resolve Project Name
    db = SupabasePersistence(tenant_id=TENANT_ID)
    meta = await db.get_project_metadata(PROJECT_ID)
    if not meta:
        print("❌ Project metadata not found!")
        return
        
    project_name = meta.get("name")
    print(f"Resolved Project Name: {project_name}")
    
    # 2. Call DiscoveryService (simulating Triage Router)
    print("\n[Step 1] Generating Manifest via DiscoveryService...")
    try:
        manifest = DiscoveryService.generate_manifest(project_name, tenant_id=TENANT_ID)
        
        file_count = len(manifest.get("file_inventory", []))
        print(f"Manifest generated. File Count: {file_count}")
        
        if file_count == 0:
            print("❌ FAILURE: No files detected in manifest.")
            # Check what path it looked at
            print(f"Root Path checked: {manifest.get('root_path')}")
        else:
            print("✅ SUCCESS: Files detected.")
            for f in manifest.get("file_inventory")[:5]:
                print(f" - {f['path']}")
                
    except Exception as e:
        print(f"❌ Error during manifest generation: {e}")

if __name__ == "__main__":
    asyncio.run(debug_agent_a())
