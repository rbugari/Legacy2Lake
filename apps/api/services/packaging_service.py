import os
import shutil
import yaml
import json
import datetime
from typing import Dict, Any, List
from .persistence_service import PersistenceService, SupabasePersistence

class PackagingService:
    """
    Manages the creation of the Certified Output Package (COP) v3.2.
    Transforms the internal project structure into a vendor-agnostic delivery bundle.
    """
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        # We need to resolve the name for FS paths
        self.persistence = SupabasePersistence()
        
    async def prepare_bundle(self) -> str:
        """
        Orchestrates the packaging process.
        Returns the path to the temporary directory containing the structured package.
        """
        project_name = await self.persistence.get_project_name_by_id(self.project_id)
        if not project_name:
            raise ValueError(f"Project not found: {self.project_id}")

        source_dir = PersistenceService.ensure_solution_dir(project_name)
        
        # Create temp staging area
        staging_dir = os.path.join(source_dir, "_package_staging")
        if os.path.exists(staging_dir):
            PersistenceService.robust_rmtree(staging_dir)
        os.makedirs(staging_dir)
        
        # Root Package Folder
        root_dir = os.path.join(staging_dir, project_name)
        os.makedirs(root_dir)
        
        # 1. Create Directory Structure
        dirs = [
            "config",
            "src/bronze", "src/silver", "src/gold",
            "sql/ddl", "sql/dml",
            "docs/lineage", "docs/data_dictionary",
            "tests"
        ]
        for d in dirs:
            os.makedirs(os.path.join(root_dir, d), exist_ok=True)
            
        # 2. Generate Configuration
        await self._generate_config(root_dir)
        
        # 3. Organize Source Code (Refinement -> src)
        await self._organize_src(source_dir, root_dir)
        
        # 4. Generate Tests
        await self._generate_tests(root_dir)
        
        # 5. Docs & README
        await self._generate_docs(source_dir, root_dir, project_name)
        
        return root_dir

    async def _generate_config(self, root_dir: str):
        """Generates env_config.yaml and schema_mappings.json."""
        registry = await self.persistence.get_design_registry(self.project_id)
        
        # Convert DB rows to Dict
        config_dict = {}
        for row in registry:
            cat = row.get("category", "general")
            key = row.get("key")
            val = row.get("value")
            if cat not in config_dict: config_dict[cat] = {}
            config_dict[cat][key] = val
            
        # env_config.yaml
        env_config = {
            "environment": "PROD",
            "project_settings": config_dict.get("cloud", {}),
            "storage_paths": {
                "bronze": "s3://{bucket}/bronze",
                "silver": "s3://{bucket}/silver",
                "gold": "s3://{bucket}/gold"
            },
            "parameters": config_dict.get("parameters", {})
        }
        
        with open(os.path.join(root_dir, "config", "env_config.yaml"), "w") as f:
            yaml.dump(env_config, f, default_flow_style=False)
            
        # schema_mappings.json (Placeholder for column mapping logic)
        mappings = {"note": "Generated schema mappings will appear here."}
        with open(os.path.join(root_dir, "config", "schema_mappings.json"), "w") as f:
            json.dump(mappings, f, indent=2)

    async def _organize_src(self, source_dir: str, root_dir: str):
        """Moves files from Refinement folders to src/{layer}."""
        # Mapping internal folders to new structure
        # Assuming internal: Refinement/Bronze, Refinement/Silver ...
        
        layer_map = {
            "Bronze": "src/bronze",
            "Silver": "src/silver",
            "Gold": "src/gold"
        }
        
        refinement_dir = os.path.join(source_dir, "Refinement")
        if not os.path.exists(refinement_dir):
            return

        for internal_layer, target_subpath in layer_map.items():
            src_layer_path = os.path.join(refinement_dir, internal_layer)
            if os.path.exists(src_layer_path):
                target_path = os.path.join(root_dir, target_subpath)
                # Copy files
                for f in os.listdir(src_layer_path):
                    if f.endswith(".py") or f.endswith(".sql"):
                        shutil.copy2(os.path.join(src_layer_path, f), target_path)

    async def _generate_tests(self, root_dir: str):
        """Generates unit_tests.py boilerplate and data_quality.sql."""
        
        # Boilerplate Unit Test
        test_py_content = """
import unittest
from pyspark.sql import SparkSession

class TestTransformationLogic(unittest.TestCase):
    def setUp(self):
        self.spark = SparkSession.builder.appName("L2L_UnitTests").master("local[2]").getOrCreate()

    def test_bronze_ingestion(self):
        # TODO: Implement specific test cases based on generated logic
        self.assertTrue(True)

    def tearDown(self):
        self.spark.stop()

if __name__ == '__main__':
    unittest.main()
"""
        with open(os.path.join(root_dir, "tests", "unit_tests.py"), "w") as f:
            f.write(test_py_content.strip())
            
        # Data Quality SQL
        dq_sql_content = """
-- L2L Data Quality Contracts
-- Generated for target platform compliance

-- Example Check
-- SELECT count(*) FROM silver.orders WHERE order_date IS NULL;
"""
        with open(os.path.join(root_dir, "tests", "data_quality.sql"), "w") as f:
            f.write(dq_sql_content.strip())

    async def _generate_docs(self, source_dir: str, root_dir: str, project_name: str):
        """Generates README and copies existing documentation."""
        
        # 1. README.md
        readme_content = f"""# {project_name} - Modernization Project
        
## Certified Output Package (COP) v3.2

This package contains the modernized data engineering logic transpiled from legacy systems.

### Structure
- **config/**: Environment configurations.
- **src/**: PySpark source code organized by Medallion Architecture (Bronze/Silver/Gold).
- **sql/**: Auxiliary SQL scripts.
- **tests/**: Validation suites.
- **docs/**: Lineage and Audit reports.

### Deployment Instructions
1. Upload this folder to your Git repository.
2. Update `config/env_config.yaml` with production credentials.
3. Run `tests/unit_tests.py` to validate logic in CI/CD.
4. deploy using your orchestrator (Airflow/Fabric/etc).

**Generated by Legacy2Lake UTM**
{datetime.datetime.now().isoformat()}
"""
        with open(os.path.join(root_dir, "README.md"), "w") as f:
            f.write(readme_content)
            
        # 2. Copy existing Markdown docs to docs/
        for f in os.listdir(source_dir):
            if f.endswith(".md"):
                shutil.copy2(os.path.join(source_dir, f), os.path.join(root_dir, "docs"))
