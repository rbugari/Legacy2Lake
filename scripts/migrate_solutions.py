import os
import shutil
import asyncio
from dotenv import load_dotenv

# Add project root to path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.api.services.persistence_service import SupabasePersistence, PersistenceService

async def migrate():
    load_dotenv()
    print("--- Starting Migration of Solution Folders ---")
    
    # 1. Admin Persistence (no tenant filter)
    db = SupabasePersistence(tenant_id=None)
    
    # 2. Fetch all projects with tenant_id
    try:
        res = db.client.table("utm_projects").select("project_id, name, tenant_id").not_.is_("tenant_id", "null").execute()
        projects = res.data
        print(f"Found {len(projects)} projects with tenant assignment.")
    except Exception as e:
        print(f"Error fetching projects: {e}")
        return

    base_dir = PersistenceService.BASE_DIR
    print(f"Solutions Base Dir: {base_dir}")
    
    moved_count = 0
    
    # 3. Move Folders
    for p in projects:
        p_name = p.get("name")
        tenant_id = p.get("tenant_id")
        
        # Sanitize matches PersistenceService logic
        folder_name = "".join([c if c.isalnum() else "_" for c in p_name])
        
        old_path = os.path.join(base_dir, folder_name)
        new_dir = os.path.join(base_dir, tenant_id)
        new_path = os.path.join(new_dir, folder_name)
        
        if os.path.exists(old_path):
            if os.path.exists(new_path):
                print(f"SKIP: Target {new_path} already exists. Leaving {old_path} for cleanup.")
            else:
                print(f"MOVING: {old_path} -> {new_path}")
                os.makedirs(new_dir, exist_ok=True)
                shutil.move(old_path, new_path)
                moved_count += 1
        
    print(f"Moved {moved_count} project folders.")
    
    # 4. Cleanup Orphans
    print("\n--- Cleaning up Orphaned/Legacy Folders ---")
    known_folders = set()
    
    # Re-scan to see what is currently valid (including what we just moved)
    # Actually, we know valid structure is solutions/<tenant_id>/<project> OR solutions/<project> (admin)
    # But user said "delete the rest".
    
    # Get all tenant IDs to avoid deleting tenant folders
    tenant_res = db.client.table("utm_tenants").select("tenant_id").execute()
    valid_tenants = {t["tenant_id"] for t in tenant_res.data}
    
    if os.path.exists(base_dir):
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            
            if not os.path.isdir(item_path):
                continue
                
            # If item is a Tenant ID, it is valid (keep it)
            if item in valid_tenants:
                continue
                
            # If item was a project folder and we moved it, it should be gone.
            # If it is still here, it means it's an orphan or an Admin project (no tenant_id).
            
            # Check if it belongs to a project without tenant_id
            is_admin_project = False
            # We need to query projects without tenant_id or check if name matches
            # Let's be safe: query all checks again
            
            # We already queried projects with tenant_id. Now query those WITHOUT.
            # But the user said "delete the rest". "Los que tienen dueño (owner)".
            # So if it doesn't have an owner (tenant_id), we delete.
            
            print(f"DELETING Orphan/Legacy: {item_path}")
            try:
                PersistenceService.robust_rmtree(item_path)
            except Exception as e:
                print(f"Failed to delete {item}: {e}")

    print("\nMigration Complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
