
import os
import json
import zipfile
import io
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from apps.api.services.persistence_service import PersistenceService, SupabasePersistence
    from apps.api.services.agent_g_service import AgentGService
    from apps.api.services.refinement.quality_service import QualityService
except ImportError:
    try:
        from services.persistence_service import PersistenceService, SupabasePersistence
        from services.agent_g_service import AgentGService
        from services.refinement.quality_service import QualityService
    except ImportError:
        from ..persistence_service import PersistenceService, SupabasePersistence
        from ..agent_g_service import AgentGService
        from .quality_service import QualityService

class GovernanceService:
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.agent_g = AgentGService(tenant_id=tenant_id, client_id=client_id)
        self.quality = QualityService()

    async def get_certification_report(self, project_id: str) -> dict:
        """
        Generates a modernization certificate with AI-driven compliance checks.
        Optimized with parallel processing.
        """
        import asyncio
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        project_name = await db.get_project_name_by_id(project_id) or project_id
        
        # 1. Fetch Assets and Start AI Audit in parallel
        assets_task = db.get_project_assets(project_id)
        prompt_task = db.resolve_agent_model("agent-g")
        
        assets, llm_config = await asyncio.gather(assets_task, prompt_task)
        
        transformations = []
        for asset in assets:
            transformations.append({
                "asset_id": asset.get("object_id"),
                "name": asset.get("source_name"),
                "metadata": asset.get("metadata", {}),
                "is_pii": asset.get("is_pii", False),
                "target_name": asset.get("target_name")
            })

        if llm_config:
            provider = llm_config.get('provider', 'UNKNOWN').upper()
            model = llm_config.get('deployment') or llm_config.get('model_name', 'UNKNOWN')
            print(f"[GOVERNANCE] Initiating Agent G (Auditor) via {provider} using model {model}")

        # Start G async
        g_task = asyncio.create_task(self.agent_g.generate_governance(
            project_name=project_name,
            mesh={}, 
            transformations=transformations,
            metadata={"project_id": project_id}
        ))

        storage = PersistenceService.get_storage()
        project_path = PersistenceService.ensure_solution_dir(project_name, tenant_id=self.tenant_id)
        refined_dir = f"{project_path.rstrip('/')}/{PersistenceService.STAGE_REFINEMENT}"
        
        # 2. Parallel File Listing and Stats
        items = storage.list_files(project_path, recursive=True)
        
        def flatten_nodes(nodes):
            files = []
            for n in nodes:
                if n["type"] == "folder":
                    files.extend(flatten_nodes(n.get("children", [])))
                else:
                    files.append(n)
            return files
        
        all_files = flatten_nodes(items)
        refined_files = [f for f in all_files if f["path"].replace("\\", "/").lower().startswith(refined_dir.lower())]
        
        # 3. Parallel LoC Counting for .py files
        py_files = [f for f in refined_files if f["name"].endswith(".py")]
        
        stats = {
            "bronze_count": 0,
            "silver_count": 0,
            "gold_count": 0,
            "total_files": len(py_files),
            "total_lines": 0
        }

        async def count_lines(f_node):
            try:
                content = storage.read_file(f_node["path"])
                if content:
                    if isinstance(content, bytes): content = content.decode("utf-8")
                    return len(content.splitlines())
            except:
                pass
            return 0

        # Heuristic for layer coloring
        for f_node in py_files:
            norm_path = f_node["path"].replace("\\", "/").lower()
            if "/bronze/" in norm_path: stats["bronze_count"] += 1
            if "/silver/" in norm_path: stats["silver_count"] += 1
            if "/gold/" in norm_path: stats["gold_count"] += 1

        results = await asyncio.gather(*[count_lines(f) for f in py_files])
        stats["total_lines"] = sum(results)

        # Persist total_lines to project settings for dashboard display
        current_settings = await db.get_project_settings(project_id)
        if current_settings is None:
            current_settings = {}
        current_settings["lines_generated"] = stats["total_lines"]
        await db.update_project_settings(project_id, current_settings)

        # 4. Wait for G and remaining parts
        governance_data = await g_task
        lineage = self._generate_lineage(project_name, refined_files)
        compliance_logs = self._fetch_compliance_logs(project_path)

        ai_audit = governance_data.get("audit_json", {})
        score = ai_audit.get("score", 70)
        
        return {
            "project_id": project_id,
            "certified_at": datetime.now().isoformat(),
            "score": score,
            "stats": stats,
            "lineage": lineage,
            "compliance_logs": compliance_logs,
            "audit_details": ai_audit,
            "runbook": governance_data.get("runbook_markdown", "")
        }

    def _generate_lineage(self, project_id: str, all_refined_files: list = None) -> list:
        """Determines traceability from legacy source to medallion targets via storage."""
        if all_refined_files is None:
            storage = PersistenceService.get_storage()
            project_path = PersistenceService.ensure_solution_dir(project_id, tenant_id=self.tenant_id)
            refined_dir = f"{project_path.rstrip('/')}/{PersistenceService.STAGE_REFINEMENT}"
            items = storage.list_files(refined_dir, recursive=True)
            def get_all_files(nodes):
                files = []
                for n in nodes:
                    if n["type"] == "folder" and n.get("children"):
                        files.extend(get_all_files(n["children"]))
                    elif n["type"] == "file":
                        files.append(n)
                return files
            all_refined_files = get_all_files(items)

        lineage = []

        # We look into the Bronze layer as the anchor for source-to-target mapping
        bronze_files = [f for f in all_refined_files if "/Bronze/" in f["path"].replace("\\", "/") and f["name"].endswith(".py")]
        
        for f_node in bronze_files:
            stem = f_node["name"].replace(".py", "").replace("_bronze", "")
            source_name = stem + ".dtsx"
            table_name = stem
            
            lineage.append({
                "source": source_name,
                "targets": {
                    "bronze": f"main.bronze_raw.{table_name}",
                    "silver": f"main.silver_curated.{table_name}",
                    "gold": f"main.gold_business.{table_name}"
                }
            })
        
        # Fallback if no Bronze files but we have Drafting files
        if not lineage:
            # Re-list for Drafting if needed? Or just skip for now.
            pass
                    
        return lineage[:10] # Cap for UI performance

    def _fetch_compliance_logs(self, project_path: str) -> list:
        # Check logs directly from R2
        storage = PersistenceService.get_storage()
        logs = []
        for log_name in ["refinement.log", "refinement_verbose.log", "triage.log", "migration.log"]:
            log_key = f"{project_path.rstrip('/')}/{log_name}"
            try:
                log_content = storage.read_file(log_key)
                if log_content:
                    if isinstance(log_content, bytes): log_content = log_content.decode("utf-8")
                    lines = log_content.splitlines()
                    for line in lines[-20:]: # Last 20 lines
                        if any(tag in line for tag in ["[OpsAuditor]", "[Refactorer]", "[Architect]", "[Agent G]", "[DEVELOPER]", "[COMPLIANCE]"]):
                            status = "PASSED" if any(kw in line for kw in ["OK", "Complete", "Success", "Saved"]) else "INFO"
                            logs.append({
                                "status": status,
                                "message": line.strip(),
                                "time": datetime.now().strftime("%H:%M") # placeholder time
                            })
            except:
                continue
        return logs[-15:] # Return 15 most recent entries

    async def create_export_bundle(self, project_id: str) -> io.BytesIO:
        """
        Creates a ZIP bundle of the entire solution, including the AI Runbook.
        Optimized version with parallel R2 reads and batched zipping.
        """
        import asyncio
        
        # 1. Start AI Certification Report in background
        report_task = asyncio.create_task(self.get_certification_report(project_id))

        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        project_name = await db.get_project_name_by_id(project_id) or project_id
        
        storage = PersistenceService.get_storage()
        project_path = PersistenceService.ensure_solution_dir(project_name, tenant_id=self.tenant_id)
        
        # 2. Parallel Fetch Assets and Column Mappings
        assets = await db.get_project_assets(project_id)
        
        async def fetch_mappings(asset):
            try:
                res = db.client.table("utm_column_mappings").select("*").eq("asset_id", asset.get("object_id")).execute()
                return asset, res.data if res.data else []
            except:
                return asset, []

        mapping_results_task = asyncio.gather(*[fetch_mappings(a) for a in assets]) if assets else asyncio.sleep(0, [])
        settings_task = db.get_project_settings(project_id)
        
        # 3. List files and fetch data in parallel
        items = storage.list_files(project_path, recursive=True)
        
        def flatten_nodes(nodes):
            files = []
            for n in nodes:
                if n["type"] == "folder":
                    files.extend(flatten_nodes(n.get("children", [])))
                else:
                    files.append(n)
            return files
        all_files = flatten_nodes(items)

        # Wait for metadata
        # Handle the case where assets is empty or mapping_results_task is None
        mapping_results_raw = await mapping_results_task
        mapping_results = mapping_results_raw if mapping_results_raw else []
        settings = await settings_task
        
        # 4. Prepare ZIP buffer
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # wait for AI report for runbook
            try:
                report = await report_task
                runbook = report.get("runbook", "# Modernization Runbook")
                zip_file.writestr("Modernization_Runbook.md", runbook)
            except Exception as e:
                zip_file.writestr("Modernization_Runbook.md", "# Modernization Runbook\n(Generation failed or timed out)")

            # Add Variables Manifest
            variables = settings.get("variables", {}) if settings else {}
            zip_file.writestr("variables_manifest.json", json.dumps(variables, indent=2))

            # Add Data Quality Contracts
            if mapping_results:
                for asset, mappings in mapping_results:
                    if not mappings: continue
                    gx_suite = self.quality.generate_great_expectations_json(asset["source_name"], mappings)
                    soda_check = self.quality.generate_soda_yaml(asset["source_name"], mappings)
                    if gx_suite:
                        zip_file.writestr(f"quality_contracts/gx/great_expectations_{asset['source_name']}.json", json.dumps(gx_suite, indent=2))
                    if soda_check:
                        zip_file.writestr(f"quality_contracts/soda/checks_{asset['source_name']}.yaml", soda_check)

            # 5. Parallel R2 Reads (Batched for stability)
            norm_base = project_path.replace("\\", "/").rstrip("/") + "/"
            BATCH_SIZE = 15
            for i in range(0, len(all_files), BATCH_SIZE):
                batch = all_files[i : i + BATCH_SIZE]
                async def fetch_one(node):
                    try:
                        f_bytes = storage.read_file(node["path"], is_binary=True)
                        return node, f_bytes
                    except:
                        return node, None
                
                batch_results = await asyncio.gather(*[fetch_one(n) for n in batch])
                for node, f_bytes in batch_results:
                    if f_bytes:
                        full_key = node["path"].replace("\\", "/")
                        arcname = full_key[len(norm_base):].lstrip("/") if full_key.startswith(norm_base) else node["name"]
                        zip_file.writestr(arcname, f_bytes)
                    
        buffer.seek(0)
        return buffer
