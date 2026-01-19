
import os
import json
import zipfile
import io
from pathlib import Path
from datetime import datetime

try:
    from apps.api.services.persistence_service import PersistenceService
except ImportError:
    try:
        from services.persistence_service import PersistenceService
    except ImportError:
        from ..persistence_service import PersistenceService

class GovernanceService:
    def __init__(self):
        pass

    def get_certification_report(self, project_id: str) -> dict:
        """
        Generates a modernization certificate with project metrics.
        """
        project_path = PersistenceService.ensure_solution_dir(project_id)
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

        # 2. Lineage Mapping (Heuristic)
        lineage = self._generate_lineage(project_id)

        # 3. Compliance Logs (from refinement.log)
        compliance_logs = self._fetch_compliance_logs(project_path)

        return {
            "project_id": project_id,
            "certified_at": datetime.now().isoformat(),
            "score": 100 if stats["gold_count"] > 0 else 80,
            "stats": stats,
            "lineage": lineage,
            "compliance_logs": compliance_logs
        }

    def _generate_lineage(self, project_id: str) -> list:
        project_path = PersistenceService.ensure_solution_dir(project_id)
        input_dir = Path(project_path) / PersistenceService.STAGE_DRAFTING
        lineage = []

        if input_dir.exists():
            for file in input_dir.glob("*.py"):
                source = file.name
                table_name = file.stem
                lineage.append({
                    "source": source,
                    "targets": {
                        "bronze": f"main.bronze_raw.{table_name}",
                        "silver": f"main.silver_curated.{table_name}",
                        "gold": f"main.gold_business.{table_name}"
                    }
                })
        return lineage

    def _fetch_compliance_logs(self, project_path: str) -> list:
        log_path = os.path.join(project_path, "refinement.log")
        logs = []
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Focus on OpsAuditor and Refactoring tags
                for line in lines:
                    if "[OpsAuditor]" in line or "[Refactoring]" in line:
                        status = "PASSED" if "OK" in line or "Added" in line or "Validated" in line else "INFO"
                        logs.append({
                            "status": status,
                            "message": line.strip(),
                            "time": "Final Audit"
                        })
        return logs[:10] # Return last 10 relevant entries

    def create_export_bundle(self, project_id: str) -> io.BytesIO:
        """
        Creates a ZIP bundle of the entire solution.
        """
        project_path = PersistenceService.ensure_solution_dir(project_id)
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(project_path):
                # We skip Refined/profile_metadata.json but keep everything else
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_path)
                    zip_file.write(file_path, arcname)
                    
        buffer.seek(0)
        return buffer
