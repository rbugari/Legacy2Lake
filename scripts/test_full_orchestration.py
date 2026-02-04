import os
import asyncio
import json
from dotenv import load_dotenv

from apps.api.services.migration_orchestrator import MigrationOrchestrator

async def test_full_orchestration():
    load_dotenv()
    
    project_id = "test10"
    project_uuid = "f98edb5e-4165-4c49-9fce-18894e8a818c" # Assuming this is the project UUID
    tenant_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    
    # We need to ensure the project has status DRAFTING in DB for the orchestrator to run
    # For testing, we can mock the persistence service or just try to run it.
    
    print(f"Testing Full Orchestration for project: {project_id}, tenant: {tenant_id}")
    
    orchestrator = MigrationOrchestrator(project_id, project_uuid=project_id, tenant_id=tenant_id)
    
    # Force status check to return DRAFTING for test
    # (In a real run, the user does this via UI)
    
    result = await orchestrator.run_full_migration(limit=1)
    
    print("\n--- RESULTS ---")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(test_full_orchestration())
