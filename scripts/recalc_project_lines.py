"""
Recalculate Lines Generated for Existing Projects

This script iterates over all projects in the GOVERNANCE stage (stage 5),
calculates their line counts, and updates the database settings.

Usage:
    python scripts/recalc_project_lines.py
"""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.api.services.persistence_service import SupabasePersistence, PersistenceService
from apps.api.services.refinement.governance_service import GovernanceService


async def recalculate_lines_for_projects():
    """Recalculates and persists line counts for all GOVERNANCE stage projects."""
    db = SupabasePersistence()
    
    # Fetch all projects
    projects = await db.list_projects()
    governance_projects = [p for p in projects if str(p.get("stage")) == "5"]
    
    print(f"Found {len(governance_projects)} projects in GOVERNANCE stage.")
    
    for project in governance_projects:
        project_id = project["project_id"]
        project_name = project["name"]
        
        print(f"\n[{project_name}] Calculating line count...")
        
        try:
            # Use the governance service to calculate stats
            storage = PersistenceService.get_storage()
            project_path = PersistenceService.ensure_solution_dir(project_name)
            refined_dir = f"{project_path.rstrip('/')}/{PersistenceService.STAGE_REFINEMENT}"
            
            # List files
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
            py_files = [f for f in refined_files if f["name"].endswith(".py")]
            
            # Count lines
            total_lines = 0
            for f_node in py_files:
                try:
                    content = storage.read_file(f_node["path"])
                    if content:
                        if isinstance(content, bytes):
                            content = content.decode("utf-8")
                        total_lines += len(content.splitlines())
                except:
                    pass
            
            print(f"[{project_name}] Found {total_lines} lines in {len(py_files)} Python files.")
            
            # Update settings
            current_settings = await db.get_project_settings(project_id)
            if current_settings is None:
                current_settings = {}
            current_settings["lines_generated"] = total_lines
            await db.update_project_settings(project_id, current_settings)
            
            print(f"[{project_name}] ✓ Updated database with {total_lines} lines.")
            
        except Exception as e:
            print(f"[{project_name}] ✗ Error: {e}")
    
    print("\n✓ Recalculation complete!")


if __name__ == "__main__":
    asyncio.run(recalculate_lines_for_projects())
