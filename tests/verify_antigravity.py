
import asyncio
import os
import uuid
from dotenv import load_dotenv

# Ensure we can import from apps
import sys
sys.path.append(os.getcwd())

from apps.api.services.persistence_service import SupabasePersistence

async def test_antigravity():
    print("--- Starting Antigravity (Multi-tenancy) Verification ---")
    
    # 1. Setup IDs
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    client_a = str(uuid.uuid4())
    
    print(f"Tenant A: {tenant_a}")
    print(f"Tenant B: {tenant_b}")
    
    # 2. Create Project for Tenant A
    db_a = SupabasePersistence(tenant_id=tenant_a, client_id=client_a)
    proj_name_a = f"Project_Tenant_A_{str(uuid.uuid4())[:8]}"
    
    try:
        pid_a = await db_a.get_or_create_project(proj_name_a)
        print(f"[Success] Created Project A: {pid_a} for Tenant A")
    except Exception as e:
        print(f"[Error] Failed to create project A: {e}")
        return

    # 3. Verify Isolation: Tenant B should NOT see Project A
    db_b = SupabasePersistence(tenant_id=tenant_b)
    
    # List Check
    projs_b = await db_b.list_projects()
    visible_to_b = any(p["project_id"] == pid_a for p in projs_b)
    
    if visible_to_b:
        print("[FAIL] Tenant B can see Tenant A's project in list_projects()!")
    else:
        print("[PASS] Tenant B cannot see Tenant A's project in list_projects().")
        
    # Metadata Check
    meta_b = await db_b.get_project_metadata(pid_a)
    if meta_b:
        print(f"[FAIL] Tenant B can access metadata for Project A! ({meta_b})")
    else:
        print("[PASS] Tenant B cannot access metadata for Project A (get_project_metadata returned None).")

    # 4. Verify Super Admin (No Tenant ID) should see everything (Legacy Mode)
    # Note: My implementation defaults to "Legacy Mode" if default __init__ is used without args.
    # If I pass NONE, do I see it?
    db_admin = SupabasePersistence(tenant_id=None)
    projs_admin = await db_admin.list_projects()
    visible_to_admin = any(p["project_id"] == pid_a for p in projs_admin)
    
    if visible_to_admin:
        print("[PASS] Super Admin (No Tenant Context) can see Project A.")
    else:
        print("[WARN] Super Admin cannot see Project A. (Assuming 'No Context' = 'All Access')")

    # 5. Cleanup
    await db_admin.delete_project(pid_a)
    print("[Info] Cleaned up test project.")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_antigravity())
