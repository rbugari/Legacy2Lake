import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

from apps.api.services.persistence_service import SupabasePersistence, PersistenceService
from apps.api.services.discovery_service import DiscoveryService
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

TENANT_ID = "f98edb5e-4165-4c49-9fce-18894e8a818c"
PROJECT_UUID = "dd13fc92-4091-456a-8ce4-712406ceb831"

async def debug_triage():
    print(f"DEBUG: Tenant ID: {TENANT_ID}")
    print(f"DEBUG: Project UUID: {PROJECT_UUID}")
    
    db = SupabasePersistence(tenant_id=TENANT_ID)
    
    # 1. Resolve Name
    project_name = await db.get_project_name_by_id(PROJECT_UUID)
    print(f"DEBUG: Resolved Project Name: '{project_name}'")
    
    if not project_name:
        print("ERROR: Could not resolve project name. Using UUID as folder?")
        project_folder = PROJECT_UUID
    else:
        project_folder = project_name
        
    # 2. Check Directory Physical Path
    solution_dir = PersistenceService.ensure_solution_dir(project_folder, tenant_id=TENANT_ID)
    print(f"DEBUG: Physical Solution Dir: {solution_dir}")
    print(f"DEBUG: Exists? {os.path.exists(solution_dir)}")
    
    triage_path = os.path.join(solution_dir, "Triage")
    print(f"DEBUG: Triage Path: {triage_path}")
    print(f"DEBUG: Exists? {os.path.exists(triage_path)}")
    
    if os.path.exists(triage_path):
        print("DEBUG: Listing Triage Folder Contents:")
        for f in os.listdir(triage_path):
            print(f"  - {f}")
    
    # 3. specific file check (test case sensitivity)
    # The user directory list showed 'test9' (lowercase) but project name might be 'TEST9'
    # Windows is case insensitive but python path logic implies exact string handling for some libs
    
    # 4. Generate Manifest
    print("-" * 50)
    print("Running DiscoveryService.generate_manifest...")
    try:
        manifest = DiscoveryService.generate_manifest(project_folder, tenant_id=TENANT_ID)
        print(f"Manifest Project ID: {manifest.get('project_id')}")
        print(f"Manifest Root Path: {manifest.get('root_path')}")
        inventory = manifest.get('file_inventory', [])
        print(f"Inventory Count: {len(inventory)}")
        for item in inventory:
            print(f"  > Found: {item['name']} ({item['type']})")
    except Exception as e:
        print(f"ERROR Generating Manifest: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_triage())
