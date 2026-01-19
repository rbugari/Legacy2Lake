
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
    def __init__(self):
        pass

    def audit_project(self, project_id: str, architect_output: dict, log: list = None) -> dict:
        """
        Validates the refined project and generates operational artifacts.
        """
        if log is None: log = []
        log.append("[OpsAuditor] Starting Operational Audit...")

        refined_files = architect_output.get("refined_files", {})
        project_path = PersistenceService.ensure_solution_dir(project_id)
        refined_dir = os.path.join(project_path, PersistenceService.STAGE_REFINEMENT)

        # 1. Validation Engine
        validation_results = self._perform_validation(refined_files, log)

        # 2. Artifact Generation
        log.append("[OpsAuditor] Generating Infrastructure-as-Code (IaC) manifests...")
        iac_path = self._generate_iac_manifest(project_id, refined_files, refined_dir)
        
        log.append("[OpsAuditor] Generating Operational Handbook (README_DEVOPS.md)...")
        handbook_path = self._generate_handbook(project_id, refined_files, refined_dir)

        log.append("[OpsAuditor] Audit Complete.")
        
        return {
            "status": "COMPLETED",
            "validation": validation_results,
            "artifacts": {
                "iac_manifest": iac_path,
                "devops_handbook": handbook_path
            }
        }

    def _perform_validation(self, refined_files: dict, log: list) -> dict:
        results = {"passed": True, "issues": []}

        # Check Medallion Layers
        for layer in ["bronze", "silver", "gold"]:
            files = refined_files.get(layer, [])
            if not files:
                msg = f"MISSING LAYER: {layer.upper()} has no files."
                log.append(f"[OpsAuditor] ERROR: {msg}")
                results["issues"].append(msg)
                results["passed"] = False
            else:
                log.append(f"[OpsAuditor] OK: {layer.upper()} layer contains {len(files)} files.")

        # Check for config/utils
        if not refined_files.get("config"):
            msg = "MISSING ARTIFACT: config.py not found."
            log.append(f"[OpsAuditor] ERROR: {msg}")
            results["issues"].append(msg)
            results["passed"] = False
        
        # Semantic Check (SCD2/Stable Keys / Dynamic PK) - Heuristic
        silver_files = refined_files.get("silver", [])
        for sf in silver_files:
            try:
                filename = os.path.basename(sf).replace("_silver.py", ".py")
                # Look for PK in profile metadata
                project_dir = os.path.dirname(os.path.dirname(os.path.dirname(sf)))
                profile_path = os.path.join(project_dir, PersistenceService.STAGE_REFINEMENT, "profile_metadata.json")
                
                pk_expected = "id"
                if os.path.exists(profile_path):
                    with open(profile_path, "r") as pf:
                        meta = json.load(pf)
                        pk_expected = meta.get("primary_keys", {}).get(filename, ["id"])
                        if isinstance(pk_expected, str): pk_expected = [pk_expected]

                with open(sf, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                    # Build expected merge condition: "target.k1 = source.k1 AND target.k2 = source.k2"
                    merge_cond = " AND ".join([f"target.{k} = source.{k}" for k in pk_expected])
                    
                    if ".merge(" in content and merge_cond in content:
                        log.append(f"[OpsAuditor] OK: {os.path.basename(sf)} uses PK '{pk_expected}' for MERGE.")
                    elif ".merge(" in content:
                        msg = f"COMPLIANCE WARNING: {os.path.basename(sf)} has MERGE logic but might use wrong keys. Expected: {merge_cond}"
                        log.append(f"[OpsAuditor] WARNING: {msg}")
                        results["issues"].append(msg)
                    else:
                        msg = f"COMPLIANCE WARNING: {os.path.basename(sf)} missing explicit MERGE logic."
                        log.append(f"[OpsAuditor] WARNING: {msg}")
                        # We don't fail for warnings, but we log them
            except Exception as e: 
                log.append(f"[OpsAuditor] Error validating {sf}: {e}")

        return results

    def _generate_iac_manifest(self, project_id: str, refined_files: dict, target_dir: str) -> str:
        # Generate a Databricks Job Manifest (Simplified)
        bundle = {
            "bundle": {
                "name": f"shift_t_{project_id}"
            },
            "resources": {
                "jobs": {
                    "medallion_pipeline": {
                        "name": f"Shift-T: {project_id} Pipeline",
                        "tasks": []
                    }
                }
            }
        }

        # Add tasks for each layer
        # For simplicity, we create groups. In production, we'd add individual notebooks.
        for layer in ["bronze", "silver", "gold"]:
            files = refined_files.get(layer, [])
            if not files: continue
            
            task = {
                "task_key": f"process_{layer}",
                "description": f"Executes all {layer.upper()} layer transformations.",
                "existing_cluster_id": "0000-000000-cluster1",
                "notebook_task": {
                    "notebook_path": f"/Repos/Shift-T/{project_id}/Refined/{layer.capitalize()}/Master_{layer.capitalize()}"
                }
            }
            if layer == "silver": task["depends_on"] = [{"task_key": "process_bronze"}]
            if layer == "gold": task["depends_on"] = [{"task_key": "process_silver"}]
            
            bundle["resources"]["jobs"]["medallion_pipeline"]["tasks"].append(task)

        manifest_path = os.path.join(target_dir, "workflows.yaml")
        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(bundle, f, default_flow_style=False)
            
        return manifest_path

    def _generate_handbook(self, project_id: str, refined_files: dict, target_dir: str) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""# Operational Handbook: {project_id}
Generated by Shift-T Ops Auditor - {timestamp}

## Architecture Overview
This project follows a **Medallion Architecture** (Bronze, Silver, Gold).

### 1. Execution Order
1. **Bronze**: Ingest raw data from source systems.
2. **Silver**: Clean, deduplicate, and apply SCD Type 2 logic.
3. **Gold**: Final business aggregations and semantic views.

## Component Registry
- **Bronze Files**: {len(refined_files.get('bronze', []))} files
- **Silver Files**: {len(refined_files.get('silver', []))} files
- **Gold Files**: {len(refined_files.get('gold', []))} files

## Deployment Notes
- **Infrastructure**: Use the provided `workflows.yaml` for Databricks Job configuration.
- **Environment**: Ensure Spark 3.x+ and Delta Lake 2.x+ are available.
- **Secrets**: Credentials should be managed via Databricks Secret Scopes using the names defined in `config.py`.

## Troubleshooting
- **Merge Failures**: Check that the Primary Keys (PK) used in Silver merges match the source system business keys.
- **Schema Evolution**: Delta Lake is configured with `mergeSchema=True` in the Bronze layer.
"""
        handbook_path = os.path.join(target_dir, "README_DEVOPS.md")
        with open(handbook_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return handbook_path
