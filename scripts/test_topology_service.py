import os
import asyncio
import json
from dotenv import load_dotenv

from apps.api.services.persistence_service import PersistenceService
from apps.api.services.topology_service import TopologyService

async def test_topology_service():
    load_dotenv()
    
    project_id = "test10"
    tenant_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    
    print(f"Testing TopologyService for project: {project_id}, tenant: {tenant_id}")
    
    topology = TopologyService(project_id, tenant_id=tenant_id)
    result = topology.build_orchestration_plan()
    
    print("\n--- RESULTS ---")
    print(json.dumps(result["orchestration"], indent=2))
    print(f"\nMetadata entries: {len(result['package_metadatas'])}")

if __name__ == "__main__":
    asyncio.run(test_topology_service())
