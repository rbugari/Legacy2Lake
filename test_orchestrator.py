
import asyncio
import sys
import os

# Adjust path
sys.path.append(os.getcwd())

from apps.api.services.refinement.refinement_orchestrator import RefinementOrchestrator

async def test_init():
    print("Initializing RefinementOrchestrator...")
    try:
        # this triggers __init__ where services are created
        orchestrator = RefinementOrchestrator()
        print("Initialization SUCCESS.")
        
        # We can't easily test start_pipeline without a real DB connection and project ID
        # but we can check if the method exists and if import error is gone.
        print("Checking imports...")
        from apps.api.services.persistence_service import SupabasePersistence
        print("SupabasePersistence import SUCCESS.")
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_init())
