import os
import sys
import asyncio
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from services.persistence_service import PersistenceService
from services.agent_s_service import AgentSService
from routers.projects import list_triage_files

# Check if tenant_id arg is needed in list_triage_files? 
# The router function signature is: async def list_triage_files(project_id: str, db: SupabasePersistence = Depends(get_db)):
# We cannot call router directly easily because of Dependency Injection.
# We will simulate the logic inside the script.

PROJECT_ID = "dd13fc92-4091-456a-8ce4-712406ceb831" # TEST9
TENANT_ID = None

async def debug_agent_s_flow():
    print("\n[Step 0] Resolving Project Details...")
    try:
        # Use SupabasePersistence for DB access
        from services.persistence_service import SupabasePersistence
        db = SupabasePersistence()
        
        # 1. Get Project Metadata (Tenant ID + Name)
        project_meta = await db.get_project_metadata(PROJECT_ID)
        
        if project_meta:
             global TENANT_ID
             TENANT_ID = project_meta.get("tenant_id")
             if TENANT_ID == "default": TENANT_ID = None
             PROJECT_NAME = project_meta.get("name")
             print(f"Resolved Project: {PROJECT_NAME} (Tenant: {TENANT_ID})")
        else:
             print("Project not found in DB!")
             return

    except Exception as e:
        print(f"Error resolving project: {e}")
        return

    # 1. Simulate GET /projects/{id}/triage/files
    print("\n[Step 1] Listing Triage Files via PersistenceService...")
    try:
        # PersistenceService expects folder name (usually project name)
        # Pass tenant_id if it exists to support 'tenant/project' structure
        all_files = PersistenceService.get_project_files(PROJECT_NAME, TENANT_ID)
        print(f"PersistenceService returned {len(all_files)} root items.")
        print(f"PersistenceService returned {len(all_files)} root items.")
        
        # Logic from router to find Triage
        triage_node = next((n for n in all_files if n["name"] == PersistenceService.STAGE_TRIAGE), None)
        
        if not triage_node:
            print("WARNING: 'Triage' folder not found in project root.")
            # print(json.dumps(all_files, indent=2)) # Reduce noise
            triage_files = []
        else:
            print(f"✅ Found Triage folder with {len(triage_node.get('children', []))} items.")
            # Flatten
            triage_files = []
            def collect_files(nodes):
                for n in nodes:
                    if n["type"] == "folder":
                        collect_files(n.get("children", []))
                    else:
                        triage_files.append(n["path"]) # Router uses 'path' key
            
            collect_files(triage_node.get("children", []))
            print(f"Collected {len(triage_files)} files in Triage.")
            print("Files:", triage_files)
            
            # 2. Simulate POST /system/scout/assess
            if len(triage_files) > 0:
                print("\n[Step 2] invoking Agent S Service...")
                # Load env for LLM
                from dotenv import load_dotenv
                load_dotenv()
                
                agent_s = AgentSService(tenant_id=TENANT_ID)
                try:
                    # Note: Agent S might need API Keys. If this fails on keys, it's config issue.
                    # But if it fails on code error, we catch it.
                    result = await agent_s.assess_repository(triage_files)
                    print("Agent S Result:", json.dumps(result, indent=2))
                except Exception as e:
                    print(f"Agent S Failed: {e}")
                    import traceback
                    traceback.print_exc()

    except Exception as e:
        print(f"Error in Step 1: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_agent_s_flow())
