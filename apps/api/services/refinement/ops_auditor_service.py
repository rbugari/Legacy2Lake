
import os
import yaml
import json
from pathlib import Path
from datetime import datetime

try:
    from apps.api.services.persistence_service import PersistenceService
except ImportError:
    try:
        from services.persistence_service import PersistenceService
    except ImportError:
        from ..persistence_service import PersistenceService

class OpsAuditorService:
    def __init__(self, tenant_id: str = None, client_id: str = None):
        self.tenant_id = tenant_id
        self.client_id = client_id

    def _log(self, log: list, msg: str, level: str = "OpsAuditor", model: str = "Compliance Auditor"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.append(f"[{timestamp}] [{level}] [{model}] {msg}")

    async def audit_project(self, project_id: str, architect_output: dict, log: list = None, project_name: str = None) -> dict:
        """
        Validates the refined project and generates operational artifacts via R2.
        """
        if log is None: log = []
        self._log(log, "Starting Operational Audit...")

        storage = PersistenceService.get_storage()
        refined_files = architect_output.get("refined_files", {})
        
        # [Fix] Use project_name for R2 paths if provided
        folder_id = project_name or project_id
        base_path = PersistenceService.ensure_solution_dir(folder_id, tenant_id=self.tenant_id)
        refined_prefix = f"{base_path.rstrip('/')}/{PersistenceService.STAGE_REFINEMENT}"

        # 1. Validation Engine
        execution_mode = architect_output.get("execution_mode", "structured_refinement")
        validation_results = await self._perform_validation(refined_files, log, base_path, execution_mode)

        # 2. Artifact Generation
        self._log(log, "Generating Infrastructure-as-Code (IaC) manifests...")
        iac_path = await self._generate_iac_manifest(project_id, refined_files, refined_prefix, execution_mode)
        
        self._log(log, "Generating Operational Handbook (README_DEVOPS.md)...")
        handbook_path = await self._generate_handbook(project_id, refined_files, refined_prefix, execution_mode)

        self._log(log, "Audit Complete.")
        
        return {
            "status": "COMPLETED",
            "validation": validation_results,
            "artifacts": {
                "iac_manifest": iac_path,
                "devops_handbook": handbook_path
            }
        }

    async def _perform_validation(self, refined_files: dict, log: list, base_path: str, execution_mode: str) -> dict:
        results = {"passed": True, "issues": []}
        storage = PersistenceService.get_storage()

        # Check Medallion Layers
        for layer in ["bronze", "silver", "gold"]:
            files = refined_files.get(layer, [])
            if not files:
                msg = f"MISSING LAYER: {layer.upper()} has no files."
                self._log(log, f"ERROR: {msg}", model="System")
                results["issues"].append(msg)
                results["passed"] = False
            else:
                self._log(log, f"OK: {layer.upper()} layer contains {len(files)} files.")

        # Check for config/utils
        if not refined_files.get("config"):
            msg = "MISSING ARTIFACT: config shared scaffolding not found."
            self._log(log, f"ERROR: {msg}", model="System")
            results["issues"].append(msg)
            results["passed"] = False

        if execution_mode == "intelligent_reengineering" and not refined_files.get("manifest"):
            msg = "MISSING ARTIFACT: reengineering manifest not found."
            self._log(log, f"ERROR: {msg}", model="System")
            results["issues"].append(msg)
            results["passed"] = False
        
        # Semantic Check
        silver_files = refined_files.get("silver", [])
        profile_path = f"{base_path.rstrip('/')}/{PersistenceService.STAGE_REFINEMENT}/profile_metadata.json"
        
        try:
            profile_bytes = storage.read_file(profile_path)
            meta = json.loads(profile_bytes) if profile_bytes else {}
        except:
            meta = {}

        for sf_key in silver_files:
            try:
                filename_only = sf_key.split("/")[-1]
                unit_name = filename_only.replace("_silver.py", "").replace("_silver.sql", "").replace("_silver.dtsx", "")
                # Guess original name
                source_guess = filename_only.replace("_silver.py", ".py").replace("_silver.dtsx", ".dtsx")
                
                pk_expected = meta.get("unit_primary_keys", {}).get(unit_name) or meta.get("primary_keys", {}).get(source_guess, ["id"])
                if isinstance(pk_expected, str): pk_expected = [pk_expected]

                content = storage.read_file(sf_key)
                if not content: continue
                if isinstance(content, bytes): content = content.decode("utf-8")
                
                # Build expected merge condition
                merge_cond = " AND ".join([f"target.{k} = source.{k}" for k in pk_expected])
                
                if ".merge(" in content and merge_cond in content:
                    self._log(log, f"OK: {filename_only} uses PK '{pk_expected}' for MERGE.")
                elif ".merge(" in content:
                    msg = f"COMPLIANCE WARNING: {filename_only} has MERGE logic but might use wrong keys. Expected: {merge_cond}"
                    self._log(log, f"WARNING: {msg}")
                    results["issues"].append(msg)
                else:
                    msg = f"COMPLIANCE WARNING: {filename_only} missing explicit MERGE logic."
                    self._log(log, f"WARNING: {msg}")
            except Exception as e: 
                self._log(log, f"Error validating {sf_key}: {e}", model="System")

        return results

    async def _generate_iac_manifest(self, project_id: str, refined_files: dict, target_prefix: str, execution_mode: str) -> str:
        storage = PersistenceService.get_storage()
        bundle = {
            "bundle": {"name": f"legacy2lake_{project_id}"},
            "resources": {
                "jobs": {
                    "medallion_pipeline": {
                        "name": f"Legacy2Lake: {project_id} Pipeline",
                        "tasks": []
                    }
                }
            }
        }

        layer_order = ["bronze", "silver", "gold"]

        for layer in layer_order:
            files = refined_files.get(layer, [])
            if not files: continue
            
            task = {
                "task_key": f"process_{layer}",
                "description": f"Executes all {layer.upper()} layer transformations.",
                "existing_cluster_id": "0000-000000-cluster1",
                "notebook_task": {
                    "notebook_path": f"/Repos/Legacy2Lake/{project_id}/Refined/{layer.capitalize()}/Master_{layer.capitalize()}"
                }
            }
            if layer == "silver": task["depends_on"] = [{"task_key": "process_bronze"}]
            if layer == "gold": task["depends_on"] = [{"task_key": "process_silver"}]
            
            bundle["resources"]["jobs"]["medallion_pipeline"]["tasks"].append(task)

        manifest_key = f"{target_prefix.rstrip('/')}/workflows.yaml"
        storage.save_file(manifest_key, yaml.dump(bundle, default_flow_style=False))
        return manifest_key

    async def _generate_handbook(self, project_id: str, refined_files: dict, target_prefix: str, execution_mode: str) -> str:
        storage = PersistenceService.get_storage()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        architecture_overview = "This project follows a **Medallion Architecture** (Bronze, Silver, Gold)."
        execution_order = """1. **Bronze**: Ingest raw data from source systems.
    2. **Silver**: Clean, deduplicate, and apply SCD Type 2 logic.
    3. **Gold**: Final business aggregations and semantic views."""
        registry_block = f"""- **Bronze Files**: {len(refined_files.get('bronze', []))} files
    - **Silver Files**: {len(refined_files.get('silver', []))} files
    - **Gold Files**: {len(refined_files.get('gold', []))} files"""

        if execution_mode == "intelligent_reengineering":
            architecture_overview = "This project follows a **Medallion Architecture with Intelligent Reengineering Consolidation** (Bronze, Silver, Gold)."
            execution_order = """1. **Bronze**: Consolidated ingestion for shared source objects.
    2. **Silver**: Consolidated cleansing and merge logic across shared objects.
    3. **Gold**: Consolidated publish outputs with traceability."""

        content = f"""# Operational Handbook: {project_id}
Generated by Legacy2Lake Ops Auditor - {timestamp}

## Architecture Overview
{architecture_overview}

### 1. Execution Order
{execution_order}

## Component Registry
{registry_block}

## Deployment Notes
- **Infrastructure**: Use the provided `workflows.yaml` for Databricks Job configuration.
- **Environment**: Ensure Spark 3.x+ and Delta Lake 2.x+ are available.
- **Secrets**: Credentials should be managed via Databricks Secret Scopes using the names defined in `config.py`.

## Troubleshooting
- **Merge Failures**: Check that the Primary Keys (PK) used in Silver merges match the source system business keys.
- **Schema Evolution**: Delta Lake is configured with `mergeSchema=True` in the Bronze layer.
"""
        handbook_key = f"{target_prefix.rstrip('/')}/README_DEVOPS.md"
        storage.save_file(handbook_key, content)
        return handbook_key
