
import asyncio
import os
from dotenv import load_dotenv
import json

# Add apps/api to path
import sys
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from services.persistence_service import SupabasePersistence

load_dotenv()

async def debug_persistence():
    tenant_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    project_id = "dd13fc92-4091-456a-8ce4-712406ceb831" # TEST9
    
    db = SupabasePersistence(tenant_id=tenant_id)
    
    print(f"Checking assets for project {project_id}...")
    assets = await db.get_project_assets(project_id)
    print(f"Existing assets count: {len(assets)}")
    
    # Simulate batch save with a test asset
    sample_assets = [
        {
            "filename": "test_persistence.dtsx",
            "type": "CORE",
            "source_path": f"{tenant_id}/test9/Triage/test_persistence.dtsx",
            "metadata": {"size": 1234},
            "selected": True
        }
    ]
    
    print("Testing batch_save_assets...")
    try:
        saved = await db.batch_save_assets(project_id, sample_assets)
        print(f"Saved assets count: {len(saved)}")
        if saved:
            print(f"Result ID: {saved[0].get('object_id')}")
            print(f"Result Path: {saved[0].get('source_path')}")
        else:
            print("WARNING: batch_save_assets returned EMPTY LIST!")
    except Exception as e:
        print(f"batch_save_assets FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_persistence())
