import asyncio
import sys
import os

# Add parent directory to path so 'services' and 'utils' can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from typing import Any, Dict
from services.agent_c_service import AgentCService

# Mock Persistence to avoid DB connection and force Snowflake config
class MockPersistence:
    async def get_global_config(self, key: str) -> Dict[str, Any]:
        if key == "generators":
            return {"default": "snowflake"}
        return {}

    async def get_design_registry(self, project_id: str):
        # Mock Registry with Snowflake Target
        return [
            {"category": "paths", "key": "target_stack", "value": "snowflake"},
            {"category": "naming", "key": "bronze_schema", "value": "BRONZE_TEST"},
            {"category": "naming", "key": "silver_schema", "value": "SILVER_TEST"},
            {"category": "naming", "key": "gold_schema", "value": "GOLD_TEST"},
            {"category": "style", "key": "indentation", "value": "4 spaces"}
        ]

    async def log_execution(self, *args, **kwargs):
        pass
        
    @staticmethod
    def ensure_solution_dir(project_id):
        # Create a temp dir for simulation
        path = os.path.abspath(f"temp_sim_{project_id}")
        os.makedirs(os.path.join(path, "Drafting"), exist_ok=True)
        return path

    @staticmethod
    def get_persistence():
        return MockPersistence()
        
    STAGE_DRAFTING = "Drafting"
    STAGE_REFINEMENT = "Refinement"

# Monkeypatching
import sys
from unittest.mock import MagicMock

# Patch the module globally so local imports get the mock
mock_persistence_module = MagicMock()
mock_persistence_module.SupabasePersistence = MockPersistence
mock_persistence_module.PersistenceService = MockPersistence
sys.modules["apps.api.services.persistence_service"] = mock_persistence_module

import services.agent_c_service
import services.refinement.architect_service
import services.refinement.refactoring_service
import services.refinement.refinement_orchestrator
import services.persistence_service

services.agent_c_service.SupabasePersistence = MockPersistence
services.refinement.architect_service.SupabasePersistence = MockPersistence
services.refinement.architect_service.PersistenceService = MockPersistence
services.refinement.refactoring_service.PersistenceService = MockPersistence

# Mock LLM
class MockLLM:
    async def ainvoke(self, messages):
        sys_msg = messages[0].content
        if "TARGET DIALECT: SNOWFLAKE" in sys_msg:
            print("[SUCCESS] Agent C: System Prompt contains Snowflake instructions.")
        else:
            print("[ERROR] Agent C: System Prompt missing Snowflake instructions!")
        
        class Response:
            content = """```json
{
"final_code": "import snowflake.snowpark as snowpark..."
}
```"""
        return Response()

services.agent_c_service.AzureChatOpenAI = lambda **kwargs: MockLLM()


async def run_simulation():
    print("--- Simulating Agent C (Drafting) with Snowflake Target ---")
    service = AgentCService()
    
    node_data = {
        "name": "Clean Daily Sales",
        "type": "ExecuteSQL",
        "description": "Delete rows where amount is null.",
        "project_id": "test_proj_snow"
    }
    
    # 1. Test Agent C
    result = await service.transpile_task(node_data)
    
    print("\n--- Simulating Agent A & R (Refinement) ---")
    from services.refinement.architect_service import ArchitectService
    from services.refinement.refactoring_service import RefactoringService
    
    # Create dummy source file
    base_path = MockPersistence.ensure_solution_dir(node_data["project_id"])
    draft_dir = os.path.join(base_path, "Drafting")
    with open(os.path.join(draft_dir, "test_source.py"), "w") as f:
        f.write("# Original PyScript\ndf = spark.read.csv('file')\ndf.write.save('out')")
        
    profile_meta = {
        "total_files": 1,
        "analyzed_files": ["test_source.py"],
        "primary_keys": {"test_source.py": ["id"]},
        "table_metadata": {"test_source.py": {"type": "DIMENSION"}}
    }
    
    architect = ArchitectService()
    arch_out = await architect.refine_project(node_data["project_id"], profile_meta)
    
    # Verify Architect Output (Snowflake Cartridge)
    bronze_file = arch_out["refined_files"]["bronze"][0]
    with open(bronze_file, "r") as f:
        content = f.read()
        if "SNOWFLAKE" in content and "snowflake.snowpark" in content:
            print(f"[SUCCESS] Architect: Generated Snowflake Bronze layer (Python): {os.path.basename(bronze_file)}")
        else:
            print(f"[ERROR] Architect: Generated code does NOT look like Snowflake: {content[:100]}")
            
    # Verify SQL Output
    sql_file = bronze_file.replace(".py", ".sql")
    if os.path.exists(sql_file):
        with open(sql_file, "r") as f:
            content = f.read()
            if "COPY INTO" in content:
                print(f"[SUCCESS] Architect: Generated Snowflake Bronze layer (SQL): {os.path.basename(sql_file)}")
    else:
        print(f"[WARN] Architect: SQL file missing: {sql_file}")
            
    # Verify Refactoring Output
    refactor = RefactoringService()
    ref_out = await refactor.refactor_project(node_data["project_id"], arch_out)
    
    with open(bronze_file, "r") as f:
        content = f.read()
        if "CLUSTER BY" in content or "Config.get_session()" in content:
             print(f"[SUCCESS] Refactoring: Applied Snowflake optimizations.")
        else:
             print(f"[ERROR] Refactoring: Missing Snowflake optimizations.")
             
    # Cleanup
    import shutil
    shutil.rmtree(base_path)

if __name__ == "__main__":
    asyncio.run(run_simulation())
