import os
import sys
import asyncio
import json

# Add project root to path (so 'apps.api...' works)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Add api explicitly if needed by some relative imports (persistence_service uses relative .storage)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from services.persistence_service import PersistenceService
from services.discovery_service import DiscoveryService
# We might need to mock or setup DB context if services rely on it, 
# but PersistenceService mostly relies on storage now.

PROJECT_ID = "dd13fc92-4091-456a-8ce4-712406ceb831" 
TENANT_ID = "default" # Assuming default tenant if not specified, or we check DB.

async def run_lifecycle_test():
    print(f"--- Starting Lifecycle Test for Project {PROJECT_ID} ---")
    
    # 1. SETUP: Ensure clean state and Upload Asset
    storage = PersistenceService.get_storage()
    project_dir = PersistenceService.ensure_solution_dir(PROJECT_ID, TENANT_ID)
    
    print(f"Target Project Directory (R2 Key): {project_dir}")
    
    # Check if empty (Reset should have cleared it)
    files = storage.list_files(project_dir, recursive=True)
    print(f"Initial File Count: {len(files)}")
    
    # Upload a Dummy Asset (Simulating UI Upload)
    dummy_asset_name = "DimCustomer.dtsx"
    dummy_content = """<?xml version="1.0"?><DTS:Executable xmlns:DTS="www.microsoft.com/SqlServer/Dts"><DTS:Property DTS:Name="PackageFormatVersion">8</DTS:Property></DTS:Executable>"""
    
    # We place it in a Triage or Source folder?
    # Usually uploads go to the root or a 'source' folder before Triage moves them?
    # Looking at projects.py upload logic, it puts zip in temp, generic upload puts in 'Triage' if specified?
    # Let's put it in "Triage" folder directly as if uploaded.
    
    triage_path = f"{project_dir.rstrip('/')}/{PersistenceService.STAGE_TRIAGE}/{dummy_asset_name}"
    print(f"Uploading dummy asset to: {triage_path}")
    storage.save_file(triage_path, dummy_content)
    
    # Verify Upload
    exists = storage.exists(triage_path)
    print(f"Upload Verified: {exists}")
    
    
    # 2. DISCOVERY & TRIAGE EXECUTION
    print(f"\n--- Step 2: Running Discovery Service (Scan) ---")
    try:
        from services.discovery_service import DiscoveryService
        manifest = DiscoveryService.generate_manifest(project_id=PROJECT_ID, tenant_id=TENANT_ID)
        
        file_count = len(manifest.get('file_inventory', []))
        print(f"Discovery Generated Manifest with {file_count} files.")
        
        # Verify our dummy asset is in the inventory
        dummy_found = any(f['name'] == dummy_asset_name for f in manifest['file_inventory'])
        print(f"Dummy Asset Found in Manifest: {dummy_found}")
        
        if file_count > 0:
            print("\n--- Step 3: Running Agent A (Triage Analysis) ---")
            # Load env vars for DB/AAcess
            from dotenv import load_dotenv
            load_dotenv()
            
            try:
                from services.agent_a_service import AgentAService
                agent_a = AgentAService(tenant_id=TENANT_ID)
                
                # Mock LLM response or rely on real one?
                # User asked to execute, so we try real execution.
                # However, this might cost tokens or fail if API keys aren't set in this script's context.
                # The script runs in same env as app, so .env should work.
                
                print("Invoking Agent A (LLM)... this might take a moment...")
                mesh_graph = await agent_a.analyze_manifest(manifest)
                
                print("Agent A Analysis Completed.")
                nodes = mesh_graph.get("mesh_graph", {}).get("nodes", [])
                print(f"Mesh Graph Nodes Generated: {len(nodes)}")
                if nodes:
                    print("Sample Node:", json.dumps(nodes[0], indent=2))
                else:
                    print("Warning: No nodes in output graph (might be expected for dummy content).")
                    
            except Exception as aa_e:
                print(f"Agent A Error: {aa_e}")
                print("(Note: Agent A requires DB access and LLM keys configured in .env)")

    except Exception as e:
        print(f"Discovery/Triage Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_lifecycle_test())
