
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
        """
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        project_name = await db.get_project_name_by_id(project_id) or project_id
        
        # 1. Fetch Context for Agent G
        assets = await db.get_project_assets(project_id)
        # Filter for transformations
        transformations = []
        for asset in assets:
            # Fetch transformation logic from DB or Files
            # For simplicity, we'll summarize the assets and their inferred metadata
            transformations.append({
                "asset_id": asset.get("object_id"),
                "name": asset.get("source_name"),
                "metadata": asset.get("metadata", {}),
                "is_pii": asset.get("is_pii", False),
                "target_name": asset.get("target_name")
            })

        # 2. Get AI Audit from Agent G
        governance_data = await self.agent_g.generate_governance(
            project_name=project_name,
            mesh={}, # Layout data could go here
            transformations=transformations,
            metadata={"project_id": project_id} # Global metadata 
        )

        project_path = PersistenceService.ensure_solution_dir(project_name)
        refined_dir = Path(project_path) / PersistenceService.STAGE_REFINEMENT
        
        # 1. Calculate Stats
        stats = {
            "bronze_count": len(list((refined_dir / "Bronze").glob("*.py"))) if (refined_dir / "Bronze").exists() else 0,
            "silver_count": len(list((refined_dir / "Silver").glob("*.py"))) if (refined_dir / "Silver").exists() else 0,
            "gold_count": len(list((refined_dir / "Gold").glob("*.py"))) if (refined_dir / "Gold").exists() else 0,
            "total_files": 0,
            "total_lines": 0
        }
        
        # Count lines of code in Refined
        for root, _, files in os.walk(refined_dir):
            for file in files:
                if file.endswith(".py"):
                    stats["total_files"] += 1
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        stats["total_lines"] += len(f.readlines())

        # 2. Lineage Mapping (SSIS -> Bronze -> Silver -> Gold)
        lineage = self._generate_lineage(project_id)

        # 3. Compliance Logs
        compliance_logs = self._fetch_compliance_logs(project_path)

        # 4. Dynamic Score (Merge Heuristic with AI)
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

    def _generate_lineage(self, project_id: str) -> list:
        """Determines traceability from legacy source to medallion targets."""
        project_path = PersistenceService.ensure_solution_dir(project_id)
        refined_dir = Path(project_path) / PersistenceService.STAGE_REFINEMENT
        lineage = []

        # We look into the Bronze layer as the anchor for source-to-target mapping
        bronze_dir = refined_dir / "Bronze"
        if bronze_dir.exists():
            for file in bronze_dir.glob("*.py"):
                # SSIS Package name is usually part of the generated filename or metadata
                # Heuristic: file_bronze.py -> file.dtsx
                source_name = file.stem.replace("_bronze", "") + ".dtsx"
                table_name = file.stem.replace("_bronze", "")
                
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
            drafting_dir = Path(project_path) / PersistenceService.STAGE_DRAFTING
            if drafting_dir.exists():
                for file in drafting_dir.glob("*.py"):
                    table_name = file.stem
                    lineage.append({
                        "source": f"{table_name}.dtsx",
                        "targets": {
                            "bronze": f"main.bronze_raw.{table_name}",
                            "silver": f"main.silver_curated.{table_name}",
                            "gold": f"main.gold_business.{table_name}"
                        }
                    })
                    
        return lineage[:10] # Cap for UI performance

    def _fetch_compliance_logs(self, project_path: str) -> list:
        # Check both refinement.log and refinement_verbose.log
        logs = []
        for log_name in ["refinement.log", "refinement_verbose.log", "triage.log"]:
            log_path = os.path.join(project_path, log_name)
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f.readlines()[-20:]: # Last 20 lines
                        if any(tag in line for tag in ["[OpsAuditor]", "[Refactorer]", "[Architect]", "[Agent G]"]):
                            status = "PASSED" if any(kw in line for kw in ["OK", "Complete", "Success", "Saved"]) else "INFO"
                            logs.append({
                                "status": status,
                                "message": line.strip(),
                                "time": datetime.now().strftime("%H:%M") # placeholder time
                            })
        return logs[-15:] # Return 15 most recent entries

    async def create_export_bundle(self, project_id: str) -> io.BytesIO:
        """
        Creates a ZIP bundle of the entire solution, including the AI Runbook.
        """
        # 1. Get real report to extract runbook
        report = await self.get_certification_report(project_id)
        runbook = report.get("runbook", "# Modernization Runbook")

        # 2. Fetch Project Variables
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        settings = await db.get_project_settings(project_id) or {}
        variables = settings.get("variables", {})

        project_path = PersistenceService.ensure_solution_dir(project_id)
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add Runbook explicitly
            zip_file.writestr("Modernization_Runbook.md", runbook)
            # Add Variables Manifest
            zip_file.writestr("variables_manifest.json", json.dumps(variables, indent=2))

            # 3. Generate Data Quality Contracts (Optional)
            assets = await db.get_project_assets(project_id)
            if assets:
                zip_file.writestr("quality_contracts/", "") # ensure folder exists
                for asset in assets:
                    # Fetch real column mappings
                    mappings = await db.get_asset_mappings(asset.get("object_id"))
                    if not mappings: continue
                    
                    # Generate GX and Soda
                    gx_suite = self.quality.generate_great_expectations_json(asset["source_name"], mappings)
                    soda_check = self.quality.generate_soda_yaml(asset["source_name"], mappings)
                    
                    if gx_suite:
                        zip_file.writestr(
                            f"quality_contracts/gx/great_expectations_{asset['source_name']}.json", 
                            json.dumps(gx_suite, indent=2)
                        )
                    if soda_check:
                         zip_file.writestr(
                            f"quality_contracts/soda/checks_{asset['source_name']}.yaml", 
                            soda_check
                        )

            for root, _, files in os.walk(project_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_path)
                    zip_file.write(file_path, arcname)
                    
        buffer.seek(0)
        return buffer
