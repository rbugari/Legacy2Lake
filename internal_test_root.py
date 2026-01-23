import asyncio
import os
import sys

# Add project root and apps/api to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from dotenv import load_dotenv
load_dotenv(".env")

from apps.api.services.refinement.refinement_orchestrator import RefinementOrchestrator

async def run_internal_test():
    project_name = "base"
    project_uuid = "c522d48a-0329-4264-85ac-58bd0c8c316c"
    
    print(f"--- INTERNAL REFINEMENT TEST (DUAL MODE): {project_name} ---")
    
    # Mocking tenant/client for testing
    orchestrator = RefinementOrchestrator(
        tenant_id="d127a303-fd01-44b3-a7b3-827238d76d1f",
        client_id="27ff46c8-06e9-4220-912a-5d09a3dd1a36"
    )
    
    print("Running Refinement Pipeline...")
    # Passing project_name as start_pipeline currently expects name/id resolvable
    # In main.py it passes project_name after resolution. 
    # But wait, looking at refinement_orchestrator.py, it takes project_id.
    # Ideally should be UUID, but internal services use names as paths.
    # Let's pass "base" (project_name) as the ID, trusting the service resolver uses it as folder name.
    result = await orchestrator.start_pipeline("base")
    
    print("\nResult:")
    import json
    print(json.dumps(result, indent=2))
    
    # Check output directory
    output_dir = os.path.join("solutions", project_name, "Drafting")
    if os.path.exists(output_dir):
        print(f"\nFiles in {output_dir}:")
        for f in os.listdir(output_dir):
            print(f" - {f}")

if __name__ == "__main__":
    asyncio.run(run_internal_test())
