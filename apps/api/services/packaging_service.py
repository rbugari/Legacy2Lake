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
    
    def __init__(self, project_id: str, tenant_id: str = None, client_id: str = None):
        self.project_id = project_id
        self.tenant_id = tenant_id
        # We need to resolve the name for FS paths
        self.persistence = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
        
    async def prepare_bundle(self) -> str:
        """
        Orchestrates the packaging process.
        Returns the path to the temporary directory containing the structured package.
        """
        project_name = await self.persistence.get_project_name_by_id(self.project_id)
        if not project_name:
            raise ValueError(f"Project not found: {self.project_id}")

        # source_dir is now a key prefix in R2 or local path
        source_dir = PersistenceService.ensure_solution_dir(project_name, tenant_id=self.tenant_id)
        
        # Create temp staging area (Local)
        # We need a real local temp dir for the zip building process
        import tempfile
        staging_dir = os.path.join(tempfile.gettempdir(), f"utm_package_{self.project_id}_{datetime.datetime.now().timestamp()}")
        if os.path.exists(staging_dir):
            PersistenceService.robust_rmtree(staging_dir)
        os.makedirs(staging_dir)
        
        # Root Package Folder
        root_dir = os.path.join(staging_dir, project_name)
        os.makedirs(root_dir)
        
        # 1. Create Directory Structure
        dirs = [
            "config",
            "src/bronze", "src/silver", "src/gold", "src/orchestration",
            "sql/ddl", "sql/dml",
            "docs/lineage", "docs/data_dictionary",
            "tests"
        ]
        for d in dirs:
            os.makedirs(os.path.join(root_dir, d), exist_ok=True)
            
        # 2. Generate Configuration
        await self._generate_config(root_dir)
        
        # 3. Organize Source Code (Refinement -> src)
        # We need to DOWNLOAD files from R2/Local Storage to this temp dir
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
        if registry:
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

    async def _organize_src(self, source_prefix: str, root_dir: str):
        """Moves files from Refinement folders to src/{layer} using StorageProvider."""
        storage = PersistenceService.get_storage()
        
        # Refinement prefix
        refinement_prefix = f"{PersistenceService.STAGE_REFINEMENT.capitalize()}" # Support both casing

        layer_map = {
            f"{refinement_prefix}/Bronze": "src/bronze",
            "src/bronze": "src/bronze", # Handle variations
            f"{refinement_prefix}/Silver": "src/silver",
            "src/silver": "src/silver",
            f"{refinement_prefix}/Gold": "src/gold",
            f"{refinement_prefix}/Orchestration": "src/orchestration"
        }
        
        # List all files recursively from source (R2/Local)
        # source_prefix is e.g. "tenant/proj/"
        all_files = storage.list_files(source_prefix, recursive=True)
        
        # We need to flatten the list if list_files returns tree
        # Current implementation of list_files returns tree structure.
        
        def traverse(nodes, parent_path=""):
             for node in nodes:
                if node["type"] == "folder":
                    traverse(node.get("children", []), os.path.join(parent_path, node["name"]))
                else:
                    # Check if file is in one of the layers
                    # node["path"] is full key/path from storage
                    # we need to check if the Relative Path matches our layers
                    
                    # We can use the path logic from node["path"]
                    # If R2, node["path"] is "tenant/proj/Refinement/Bronze/file.py"
                    # We need to match "Refinement/Bronze" subpart
                    
                    # Simpler: check if node["path"] contains mapped folders
                    # Be careful with partial matches
                    
                    for src_layer, target_sub in layer_map.items():
                         # Normalize separators
                         norm_path = node["path"].replace("\\", "/")
                         # Check if path contains the src layer signature
                         # e.g. "/Refinement/Bronze/" or "Refinement/Bronze/"
                         if f"/{src_layer}/" in norm_path or norm_path.startswith(f"{src_layer}/") or norm_path.endswith(f"/{src_layer}") or f"/{src_layer.lower()}/" in norm_path.lower():
                             # Found a match
                             # Read content
                             content = storage.read_file(node["path"], is_binary=True)
                             if content:
                                 target_path = os.path.join(root_dir, target_sub, node["name"])
                                 os.makedirs(os.path.dirname(target_path), exist_ok=True)
                                 with open(target_path, "wb") as f:
                                     f.write(content)
                             break # Handled

        traverse(all_files, "")

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

    async def _generate_docs(self, source_prefix: str, root_dir: str, project_name: str):
        """Generates README and copies existing documentation using StorageProvider."""
        
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
            
        # 2. Copy existing Markdown docs
        # List files from storage
        storage = PersistenceService.get_storage()
        try:
            # We list recursive from root, filtered by .md
            # Or just list top level if that's where docs are?
            # Assuming docs are at project root or in a 'Docs' folder?
            # Existing code looked at source_dir (root).
            
            all_files = storage.list_files(source_prefix, recursive=False) 
            # list_files returns a tree or flat list? 
            # implementation returns recursive tree structure.
            # recursive=False means just top level children. OK.
            
            for node in all_files:
                if node["type"] == "file" and node["name"].endswith(".md"):
                    content = storage.read_file(node["path"], is_binary=True)
                    if content:
                         with open(os.path.join(root_dir, "docs", node["name"]), "wb") as f:
                             f.write(content)
        except Exception as e:
            print(f"Error copying docs: {e}")
