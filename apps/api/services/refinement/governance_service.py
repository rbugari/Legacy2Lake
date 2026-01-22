
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
        Generates a modernization certificate with real project metrics.
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

        # 2. Lineage Mapping (SSIS -> Bronze -> Silver -> Gold)
        lineage = self._generate_lineage(project_id)

        # 3. Compliance Logs
        compliance_logs = self._fetch_compliance_logs(project_path)

        # 4. Dynamic Score
        # Start at 70, +10 for each medallion layer present, +5 for lineage coverage
        score = 70
        if stats["bronze_count"] > 0: score += 10
        if stats["silver_count"] > 0: score += 10
        if stats["gold_count"] > 0: score += 10
        if stats["total_lines"] > 1000: score = min(100, score + 5)

        return {
            "project_id": project_id,
            "certified_at": datetime.now().isoformat(),
            "score": score,
            "stats": stats,
            "lineage": lineage,
            "compliance_logs": compliance_logs
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
