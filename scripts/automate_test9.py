import os
import asyncio
import sys
from dotenv import load_dotenv

# Path Setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from apps.api.services.persistence_service import SupabasePersistence, PersistenceService
from apps.api.services.migration_orchestrator import MigrationOrchestrator

ZIP_FILE = r"C:\proyectos_dev\UTM\Dim_Customers_test.zip"

async def run_test():
    load_dotenv()
    print("--- Starting TEST9 Automation for DEMO2 & DEMO3 ---")

    # 1. Admin Persistence to fetch Tenants
    admin_db = SupabasePersistence(tenant_id=None)
    
    if os.path.exists(ZIP_FILE):
        print(f"DEBUG: Zip file found at {ZIP_FILE}")
    else:
        print(f"ERROR: Zip file NOT FOUND at {ZIP_FILE}")
        # List dir to see what's there
        print(f"Dir contents of {os.path.dirname(ZIP_FILE)}:")
        print(os.listdir(os.path.dirname(ZIP_FILE)))
        return

    # Get Tenant IDs and Client IDs
    res = admin_db.client.table("utm_tenants").select("tenant_id, username, client_id").in_("username", ["DEMO3"]).execute()
    tenants = res.data
    
    if not tenants:
        print("ERROR: DEMO3 not found")
        return

    print(f"Found Tenants: {tenants}")

    for t in tenants:
        t_name = t["username"]
        t_id = t["tenant_id"]
        c_id = t.get("client_id")  # Direct fetch
        print(f"\nProcessing Tenant: {t_name} ({t_id})")
        
        # 2. Impersonate Tenant
        print(f"  > Using Client ID: {c_id}")
        
        # Initialize Services doing impersonation
        db = SupabasePersistence(tenant_id=t_id, client_id=c_id)
        
        project_name = "TEST9"
        
        # 3. Cleanup Existing (if any)
        # Check if exists
        p_res = db.client.table("utm_projects").select("project_id").eq("name", project_name).eq("tenant_id", t_id).execute()
        if p_res.data:
            p_id = p_res.data[0]["project_id"]
            print(f"  > Deleting existing project {p_id}...")
            # Delete DB
            db.client.table("utm_projects").delete().eq("project_id", p_id).execute()
            # Delete FS
            PersistenceService.delete_project_directory(project_name, tenant_id=t_id)

        # 4. Create Project
        print(f"  > Creating Project {project_name}...")
        project_id = await db.get_or_create_project(project_name)
        print(f"  > Created Project UUID: {project_id}")
        
        # 5. Initialize from ZIP
        print(f"  > Initializing from ZIP: {ZIP_FILE}")
        success = PersistenceService.initialize_project_from_source(
            project_id=project_name, # Use name for folder
            source_type="zip",
            file_path=ZIP_FILE,
            overwrite=True,
            tenant_id=t_id,
            source_tech="Microsoft SSIS",
            target_tech="Databricks (PySpark)"
        )
        
        if not success:
            print("  > ERROR: Failed to unzip file.")
            continue
            
        # 6. Execute Migration
        print(f"  > Starting Orchestrator for {t_name}...")
        orchestrator = MigrationOrchestrator(
            project_id=project_name, 
            project_uuid=project_id, 
            tenant_id=t_id, 
            client_id=c_id
        )
        
        results = await orchestrator.run_full_migration(limit=0)
        print(f"  > Migration Finished. Succeeded: {len(results['succeeded'])}, Failed: {len(results['failed'])}")

    print("\n--- Automation Complete ---")

if __name__ == "__main__":
    asyncio.run(run_test())
