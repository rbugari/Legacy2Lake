import os
import shutil
from typing import Dict, Any, Optional, List
from supabase import create_client, Client

class PersistenceService:
    print("LOADING PersistenceService v2 - WITH initialize_project_from_source")
    # Base directory for local file storage (Solutions)
    # Calculated relative to this file to be robust against CWD changes
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "solutions"))

    # Stage-aligned Directory Constants
    STAGE_TRIAGE = "Triage"     # Was Input/Source
    STAGE_DRAFTING = "Drafting"   # Was Output
    STAGE_REFINEMENT = "Refinement" # Was Refined

    @classmethod
    def ensure_solution_dir(cls, solution_name: str) -> str:
        """Creates a directory for the specific solution if it doesn't exist."""
        # Sanitize name
        folder_name = "".join([c if c.isalnum() else "_" for c in solution_name])
        path = os.path.join(cls.BASE_DIR, folder_name)
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def robust_rmtree(cls, path: str):
        """Robustly deletes a directory tree, handling read-only files (Windows .git issue)."""
        import stat

        def on_error(func, path, exc_info):
            # Check if it's a permission error (Access denied)
            if not os.access(path, os.W_OK):
                # Change to writable and retry
                os.chmod(path, stat.S_IWUSR)
                func(path)
            else:
                raise # Re-raise if it's not a permission issue

        if os.path.exists(path):
            shutil.rmtree(path, onerror=on_error)

    @classmethod
    def delete_project_directory(cls, project_id: str) -> bool:
        """Deletes the project directory from the filesystem."""
        try:
            # We assume project_id maps to folder name. If not, we might need a lookup, 
            # but for this app we enforce project_id ~ folder_name (sanitized)
            # However, ensure_solution_dir sanitizes. We should probably replicate that logic or assume robust_rmtree handles it.
            # Best effort: try to look for the folder
            
            # Simple approach: Re-sanitize just in case, or list dirs to find match. 
            # Given ensure_solution_dir implementation:
            folder_name = "".join([c if c.isalnum() else "_" for c in project_id])
            path = os.path.join(cls.BASE_DIR, folder_name)
            
            if os.path.exists(path):
                print(f"Deleting directory: {path}")
                cls.robust_rmtree(path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting directory {project_id}: {e}")
            return False

    @classmethod
    def save_transformation(cls, solution_name: str, task_name: str, code: str) -> str:
        """Saves a transpiled PySpark task to the solution directory."""
        dir_path = cls.ensure_solution_dir(solution_name)
        # Sanitize task name for filename
        filename = "".join([c if c.isalnum() else "_" for c in task_name]) + ".py"
        file_path = os.path.join(dir_path, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        return file_path

    @classmethod
    def save_documentation(cls, solution_name: str, doc_name: str, content: str) -> str:
        """Saves governance/technical documentation to the solution directory."""
        dir_path = cls.ensure_solution_dir(solution_name)
        filename = doc_name + ".md"
        file_path = os.path.join(dir_path, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return file_path

    @classmethod
    def initialize_project_from_source(cls, project_id: str, source_type: str, file_path: str = None, github_url: str = None, overwrite: bool = False) -> bool:
        """Initializes a project directory from a ZIP file or GitHub Repo. Handles overwrite logic."""
        import zipfile
        import subprocess

        try:
            project_dir = cls.ensure_solution_dir(project_id)
            
            # Check if exists and handle overwrite
            if any(os.scandir(project_dir)):
                if not overwrite:
                    print(f"Error: Project directory {project_dir} is not empty and overwrite=False.")
                    return False
                
                print(f"Cleaning existing directory for {project_id} (overwrite=True)...")
                cls.robust_rmtree(project_dir)
                # Re-create the empty dir
                project_dir = cls.ensure_solution_dir(project_id)

            # Ensure Triage directory exists for source files
            triage_dir = os.path.join(project_dir, cls.STAGE_TRIAGE)
            os.makedirs(triage_dir, exist_ok=True)

            if source_type == "zip" and file_path:
                # Extract ZIP into Triage
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(triage_dir)
                # Cleanup temporary ZIP
                if os.path.exists(file_path):
                    os.remove(file_path)
                print(f"Project {project_id} initialized from ZIP into {cls.STAGE_TRIAGE}.")
                
            elif source_type == "github" and github_url:
                # Git Clone into Triage
                subprocess.run(["git", "clone", github_url, triage_dir], check=True)
                print(f"Project {project_id} initialized from GitHub into {cls.STAGE_TRIAGE}.")
                
            return True
        except Exception as e:
            print(f"Error initializing project: {e}")
            return False

    @classmethod
    def get_project_files(cls, project_id: str) -> List[Dict[str, Any]]:
        """Returns a recursive query of the project's solution directory."""
        # Clean ID just in case
        folder_name = "".join([c if c.isalnum() else "_" for c in project_id])
        solution_path = os.path.join(cls.BASE_DIR, folder_name)
        
        if not os.path.exists(solution_path):
            return []

        def _scan_dir(path: str) -> List[Dict[str, Any]]:
            children = []
            try:
                with os.scandir(path) as it:
                    for entry in it:
                        # Skip hidden files and common junk
                        if entry.name.startswith('.'): continue
                        if entry.name == "__pycache__": continue
                        
                        node = {
                            "name": entry.name,
                            "path": entry.path, # Absolute path, maybe dangerous to expose but needed for read
                            "type": "folder" if entry.is_dir() else "file",
                            "last_modified": entry.stat().st_mtime
                        }
                        if entry.is_dir():
                            node["children"] = _scan_dir(entry.path)
                            # Sort: folders first, then files
                            node["children"].sort(key=lambda x: (x["type"] != "folder", x["name"]))
                            
                        children.append(node)
            except Exception as e:
                print(f"Error scanning {path}: {e}")
                
            # Sort: folders first, then files
            children.sort(key=lambda x: (x["type"] != "folder", x["name"]))
            return children

        return _scan_dir(solution_path)

    @classmethod
    def read_file_content(cls, project_id: str, file_path: str) -> str:
        """Reads the content of a specific file within the project's solution directory."""
        # Security check: Ensure file is inside project dir
        folder_name = "".join([c if c.isalnum() else "_" for c in project_id])
        project_root = os.path.join(cls.BASE_DIR, folder_name)
        
        # Resolve absolute path
        # Fix: If file_path is relative, assume it is inside project_root
        if not os.path.isabs(file_path):
            file_path = os.path.join(project_root, file_path)
            
        abs_path = os.path.abspath(file_path)
        abs_root = os.path.abspath(project_root)
        
        if not abs_path.startswith(abs_root):
            # Debug info in case of error
            # print(f"[Security] Denied access to {abs_path} (limit: {abs_root})")
            raise ValueError("Access Denied: File is outside project directory")
            
        if not os.path.exists(abs_path):
            return ""

        with open(abs_path, 'r', encoding='utf-8') as f:
            return f.read()

class SupabasePersistence:
    def __init__(self):
        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        self.client: Client = create_client(url, key)

    async def get_or_create_project(self, name: str, repo_url: str = None) -> str:
        """Finds or creates a project by name and returns its UUID."""
        res = self.client.table("utm_projects").select("project_id").eq("name", name).execute()
        if res.data:
            project_id = res.data[0]["project_id"]
            if repo_url:
                self.client.table("utm_projects").update({"repo_url": repo_url}).eq("project_id", project_id).execute()
            return project_id
        
        data = {"name": name, "stage": "1"}
        if repo_url:
            data["repo_url"] = repo_url
            
        res = self.client.table("utm_projects").insert(data).execute()
        return res.data[0]["project_id"]

    async def list_projects(self) -> List[Dict[str, Any]]:
        """Returns a list of all projects."""
        res = self.client.table("utm_projects").select("*").execute()
        if res.data:
            for item in res.data:
                item["id"] = item["project_id"]
        return res.data if res.data else []

    async def delete_project(self, project_id: str) -> bool:
        """Deletes the project and its assets from the database."""
        try:
            # Supabase should handle cascade if configured, but let's be explicit if needed.
            # Assuming 'projects' deletion deletes related 'assets' via FK cascade.
            self.client.table("utm_projects").delete().eq("project_id", project_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting project {project_id} from DB: {e}")
            return False

    async def get_project_id_by_name(self, name: str) -> Optional[str]:
        """Resolves a project name (slug) to its UUID."""
        res = self.client.table("utm_projects").select("project_id").eq("name", name).execute()
        if res.data:
            return res.data[0]["project_id"]
        return None

    async def get_project_name_by_id(self, project_id: str) -> Optional[str]:
        """Resolves a project UUID to its name."""
        try:
            res = self.client.table("utm_projects").select("name").eq("project_id", project_id).execute()
            if res.data:
                return res.data[0]["name"]
        except Exception:
            pass
        return None

    async def get_project_metadata(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Returns project metadata (name, repo_url, status, stage, prompt, settings, config)."""
        try:
            res = self.client.table("utm_projects").select("project_id, name, repo_url, status, stage, prompt, settings, config").eq("project_id", project_id).execute()
            if res.data:
                item = res.data[0]
                item["id"] = item["project_id"]
                return item
        except Exception:
            pass
        return None

    async def save_asset(self, project_id: str, filename: str, content: str, asset_type: str, file_hash: str, source_path: str = None) -> str:
        """Saves an asset (e.g. .dtsx file) to the database."""
        data = {
            "project_id": project_id,
            "source_name": filename,
            "raw_content": content,
            "type": asset_type,
            "hash": file_hash
        }
        if source_path:
            data["source_path"] = source_path
            
        res = self.client.table("utm_objects").insert(data).execute()
        return res.data[0]["object_id"]

    async def update_asset_metadata(self, asset_id: str, updates: Dict[str, Any]) -> bool:
        """Updates specific fields of an asset (type, selected, metadata, operational metadata, business metadata)."""
        allowed_fields = [
            "type", "selected", "metadata", 
            "frequency", "load_strategy", "criticality", "is_pii", "masking_rule",
            "business_entity", "target_name"
        ]
        safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not safe_updates:
            return False
            
        try:
            self.client.table("utm_objects").update(safe_updates).eq("object_id", asset_id).execute()
            return True
        except Exception as e:
            print(f"Error updating asset {asset_id}: {e}")
            return False

    async def batch_save_assets(self, project_id: str, assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Upserts multiple assets in a single call. Blocks if project is in DRAFTING mode."""
        
        if not project_id or project_id == "undefined":
            print(f"Error: batch_save_assets called with invalid project_id: {project_id}")
            return []

        # 1. State Check
        try:
             proj_res = self.client.table("utm_projects").select("status").eq("project_id", project_id).execute()
             if proj_res.data:
                 current_status = proj_res.data[0].get("status", "TRIAGE")
                 if current_status == "DRAFTING":
                     raise ValueError("Project is in DRAFTING mode. Asset Inventory is locked. Unlock Triege first.")
        except Exception as e:
             print(f"Error checking status for {project_id}: {e}")
             return []

        if not assets:
            return []
            
        insert_data = []
        for asset in assets:
            insert_data.append({
                "project_id": project_id,
                "source_name": asset["filename"],
                "raw_content": asset.get("content"),
                "type": asset.get("type", "OTHER"),
                "hash": asset.get("hash", "v1"),
                "source_path": asset.get("source_path") or asset.get("path"),
                "metadata": asset.get("metadata", {}),
                "selected": asset.get("selected", False),
                # Release 1.2 Fields
                "frequency": asset.get("frequency", "DAILY"),
                "load_strategy": asset.get("load_strategy", "FULL_OVERWRITE"),
                "criticality": asset.get("criticality", "P3"),
                "is_pii": asset.get("is_pii", False),
                "masking_rule": asset.get("masking_rule"),
                "business_entity": asset.get("business_entity"),
                "target_name": asset.get("target_name")
            })
            
        try:
            res = self.client.table("utm_objects").upsert(insert_data, on_conflict="project_id, source_path").execute()
            if res.data:
                for item in res.data:
                    item["id"] = item["object_id"]
                    item["filename"] = item["source_name"]
            return res.data 
        except Exception as e:
            print(f"Error in batch_save_assets: {e}")
            return []

    async def get_project_assets(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieves all assets for a given project from the database."""
        try:
            res = self.client.table("utm_objects").select("*").eq("project_id", project_id).execute()
            # Map source_name back to filename for frontend compatibility if needed, 
            # though it's better to keep it consistent.
            if res.data:
                for item in res.data:
                    item["id"] = item["object_id"]
                    item["filename"] = item["source_name"]
                    item["name"] = item["source_name"] # Compatibility
            return res.data if res.data else []
        except Exception as e:
            print(f"Error fetching assets for {project_id}: {e}")
            return []

    async def save_transformation(self, asset_id: str, source_code: str, target_code: str, status: str = "completed") -> str:
        """Saves a transformation record."""
        data = {
            "asset_id": asset_id,
            "source_code": source_code,
            "target_code": target_code,
            "status": status
        }
        # [Release 3.5] Table Renamed: 'transformations' -> 'utm_transformations'
        res = self.client.table("utm_transformations").insert(data).execute()
        return res.data[0]["id"]

    async def update_project_stage(self, project_id_or_name: str, stage: str) -> bool:
        """Updates the stage of a project. Handles both UUID and Name."""
        try:
            project_uuid = project_id_or_name
            if "-" not in project_id_or_name:
                resolved = await self.get_project_id_by_name(project_id_or_name)
                if resolved:
                    project_uuid = resolved

            self.client.table("utm_projects").update({"stage": stage}).eq("project_id", project_uuid).execute()
            return True
        except Exception as e:
            print(f"Error updating stage for {project_id_or_name}: {e}")
            return False

    async def save_project_layout(self, project_id_or_name: str, layout_data: Dict[str, Any]) -> str:
        """Saves the graph layout as a JSON asset. Handles both UUID and Name."""
        import json
        
        project_uuid = project_id_or_name
        if "-" not in project_id_or_name: 
            resolved = await self.get_project_id_by_name(project_id_or_name)
            if resolved:
                project_uuid = resolved
            else:
                project_uuid = await self.get_or_create_project(project_id_or_name)

        content = json.dumps(layout_data)
        res = self.client.table("utm_objects").select("object_id").eq("project_id", project_uuid).eq("type", "LAYOUT").execute()
        
        if res.data:
            asset_id = res.data[0]["object_id"]
            self.client.table("utm_objects").update({"raw_content": content}).eq("object_id", asset_id).execute()
            return asset_id
        else:
            return await self.save_asset(project_uuid, "layout.json", content, "LAYOUT", "v1")

    async def get_project_layout(self, project_id_or_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves the graph layout. Handles both UUID and Name."""
        import json
        project_uuid = project_id_or_name
        if "-" not in project_id_or_name:
            resolved = await self.get_project_id_by_name(project_id_or_name)
            if resolved:
                project_uuid = resolved
            else:
                return None

        res = self.client.table("utm_objects").select("raw_content").eq("project_id", project_uuid).eq("type", "LAYOUT").execute()
        if res.data:
            try:
                return json.loads(res.data[0]["raw_content"])
            except:
                return None
        return None

    async def update_project_prompt(self, project_id: str, prompt: str) -> bool:
        """Updates the custom system prompt for a project."""
        project_uuid = project_id
        if "-" not in project_id:
            resolved = await self.get_project_id_by_name(project_id)
            if resolved:
                project_uuid = resolved

        try:
            self.client.table("utm_projects").update({"prompt": prompt}).eq("project_id", project_uuid).execute()
            return True
        except Exception as e:
            print(f"Error updating prompt for {project_id}: {e}")
            return False

    async def reset_project_data(self, project_id: str) -> bool:
        """Clears all assets and resets stage/status for a project."""
        try:
            # 1. Get object_ids for this project to handle nested deletions
            obj_res = self.client.table("utm_objects").select("object_id").eq("project_id", project_id).execute()
            object_ids = [o["object_id"] for o in obj_res.data]
            
            if object_ids:
                # 2. Delete from dependent tables (satisfy foreign keys)
                # utm_logical_steps -> utm_objects (object_id)
                self.client.table("utm_logical_steps").delete().in_("object_id", object_ids).execute()
                # [Release 4.2] utm_transformations -> utm_objects (asset_id)
                self.client.table("utm_transformations").delete().in_("asset_id", object_ids).execute()
            
            # 2.5 Clean per-asset context overrides
            self.client.table("utm_asset_context").delete().eq("project_id", project_id).execute()

            # 3. Delete main assets (utm_objects)
            self.client.table("utm_objects").delete().eq("project_id", project_id).execute()
            
            # 4. Clean File Inventory and Logs
            self.client.table("utm_execution_logs").delete().eq("project_id", project_id).execute()
            self.client.table("utm_file_inventory").delete().eq("project_id", project_id).execute()
            
            # 5. Reset stage to 1 and status to TRIAGE
            self.client.table("utm_projects").update({
                "stage": "1",
                "status": "TRIAGE",
                "triage_approved_at": None
            }).eq("project_id", project_id).execute()
            
            return True
        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            with open("reset_error.log", "w", encoding="utf-8") as f:
                f.write(f"ERROR resetting project {project_id}:\n{err_msg}\n")
            print(f"ERROR resetting project {project_id}: {err_msg}")
            return False

    async def update_project_status(self, project_id: str, status: str) -> bool:
        """Updates the project status (TRIAGE <-> DRAFTING)."""
        project_uuid = project_id
        if "-" not in project_id:
             resolved = await self.get_project_id_by_name(project_id)
             if resolved:
                 project_uuid = resolved

        data = {"status": status}
        if status == "DRAFTING":
            data["triage_approved_at"] = "now()"
        
        try:
            self.client.table("utm_projects").update(data).eq("project_id", project_uuid).execute()
            return True
        except Exception as e:
            print(f"Error updating status: {e}")
            return False

    async def get_project_status(self, project_id: str) -> str:
         project_uuid = project_id
         if "-" not in project_id:
             resolved = await self.get_project_id_by_name(project_id)
             if resolved:
                 project_uuid = resolved

         try:
             res = self.client.table("utm_projects").select("status").eq("project_id", project_uuid).execute()
             if res.data:
                 return res.data[0].get("status", "TRIAGE")
         except:
             pass
         return "TRIAGE"

    async def update_project_settings(self, project_id: str, settings: Dict[str, Any]) -> bool:
        """Updates the project settings JSONB column."""
        project_uuid = project_id
        if "-" not in project_id:
            resolved = await self.get_project_id_by_name(project_id)
            if resolved:
                project_uuid = resolved

        try:
            self.client.table("utm_projects").update({"settings": settings}).eq("project_id", project_uuid).execute()
            return True
        except Exception as e:
            print(f"Error updating settings for {project_id}: {e}")
            return False

    async def save_asset_context(self, project_id: str, source_path: str, notes: str, rules: Dict[str, Any] = None) -> bool:
        """Saves or updates human context for a specific asset."""
        data = {
            "project_id": project_id,
            "source_path": source_path,
            "notes": notes,
            "rules": rules or {}
        }
        try:
            # [Release 3.5] Table Renamed: 'asset_context' -> 'utm_asset_context'
            self.client.table("utm_asset_context").upsert(data, on_conflict="project_id, source_path").execute()
            return True
        except Exception as e:
            print(f"Error saving asset context: {e}")
            return False

    async def get_project_context(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieves all human context entries for a project."""
        try:
            # [Release 3.5] Table Renamed: 'asset_context' -> 'utm_asset_context'
            res = self.client.table("utm_asset_context").select("*").eq("project_id", project_id).execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error fetching project context: {e}")
            return []

    # Release 1.3 Knowledge Registry Methods
    async def get_design_registry(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieves all global design rules for a project."""
        project_uuid = project_id
        if "-" not in project_id:
            resolved = await self.get_project_id_by_name(project_id)
            if resolved:
                project_uuid = resolved

        try:
            # [Release 3.5] Table Renamed: 'design_registry' -> 'utm_design_registry'
            res = self.client.table("utm_design_registry").select("*").eq("project_id", project_uuid).execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error fetching design registry: {e}")
            return []

    async def update_design_registry(self, project_id: str, category: str, key: str, value: Any) -> bool:
        """Upserts a specific design rule."""
        data = {
            "project_id": project_id,
            "category": category,
            "key": key,
            "value": value,
            "updated_at": "now()"
        }
        try:
            # [Release 3.5] Table Renamed: 'design_registry' -> 'utm_design_registry'
            self.client.table("utm_design_registry").upsert(data, on_conflict="project_id, category, key").execute()
            return True
        except Exception as e:
            print(f"Error updating design registry: {e}")
            return False

    async def initialize_design_registry(self, project_id: str) -> bool:
        """Seeds default design standards for a new project."""
        from apps.api.services.knowledge_service import KnowledgeService
        defaults = KnowledgeService.get_default_registry_entries(project_id)
        try:
            # [Release 3.5] Table Renamed: 'design_registry' -> 'utm_design_registry'
            self.client.table("utm_design_registry").upsert(defaults, on_conflict="project_id, category, key").execute()
            return True
        except Exception as e:
            print(f"Error initializing design registry: {e}")
            return False

    # Release 3.5: Execution Logs & File Inventory
    # --------------------------------------------
    
    async def log_execution(self, project_id: str, phase: str, message: str, step: str = None, level: str = "INFO"):
        """Persists a log entry to the database."""
        try:
            # Resolve UUID if project_id is a name
            resolved_id = project_id
            if "-" not in project_id:
                uuid = await self.get_project_id_by_name(project_id)
                if uuid: resolved_id = uuid
            
            data = {
                "project_id": resolved_id,
                "phase": phase,
                "step": step,
                "message": message,
                "level": level
            }
            self.client.table("utm_execution_logs").insert(data).execute()
        except Exception as e:
            print(f"Error logging to DB: {e}")

    async def sync_file_inventory(self, project_id: str) -> bool:
        """
        Scans the project's solution directory and updates 'utm_file_inventory'.
        Replaces file-system scanning for read operations.
        """
        import os
        from .persistence_service import PersistenceService
        
        project_uuid = project_id
        folder_key = project_id

        if "-" not in project_id:
             resolved = await self.get_project_id_by_name(project_id)
             if resolved: project_uuid = resolved
             folder_key = project_id
        else:
             # Input is UUID, find name for folder lookup
             name = await self.get_project_name_by_id(project_id)
             if name: folder_key = name
        
        try:
            # 1. Get real path
            project_dir = PersistenceService.ensure_solution_dir(folder_key)
            import datetime
            if not os.path.exists(project_dir):
                return False

            # 2. Walk and Collect
            inventory = []
            # now = "now()" # In SQL, or use python datetime
            
            for root, dirs, files in os.walk(project_dir):
                rel_root = os.path.relpath(root, project_dir)
                if rel_root == ".": rel_root = ""
                
                # Add Directories
                for d in dirs:
                    if d.startswith(".") or d == "__pycache__": continue
                    d_path = os.path.join(rel_root, d).replace("\\", "/")
                    inventory.append({
                        "project_id": project_uuid,
                        "file_path": d_path,
                        "is_directory": True,
                        "file_path": d_path,
                        "is_directory": True,
                        "last_modified": None
                    })

                # Add Files
                for f in files:
                    if f.startswith(".") or f == "__pycache__": continue
                    if f.endswith(".pyc"): continue
                    
                    full_path = os.path.join(root, f)
                    rel_path = os.path.join(rel_root, f).replace("\\", "/")
                    
                    size = os.path.getsize(full_path)
                    
                    mtime = os.path.getmtime(full_path)
                    mtime_iso = datetime.datetime.fromtimestamp(mtime).isoformat()
                    
                    inventory.append({
                        "project_id": project_uuid,
                        "file_path": rel_path,
                        "is_directory": False,
                        "size_bytes": size,
                        "last_modified": mtime_iso
                    })
            
            # 3. Simple Refresh: Delete all and re-insert
            # (In future, intelligent diffing would be better)
            self.client.table("utm_file_inventory").delete().eq("project_id", project_uuid).execute()
            
            if inventory:
                # Batch insert? Supabase might limit request size. 
                # Let's chunk if necessary, but thousands of files might be fine.
                # Just catch error if too big.
                try:
                    self.client.table("utm_file_inventory").insert(inventory).execute()
                except Exception as ex:
                    print(f"Batch insert failed, retrying in chunks: {ex}")
                    # Naive chunking
                    chunk_size = 100
                    for i in range(0, len(inventory), chunk_size):
                        chunk = inventory[i:i + chunk_size]
                        self.client.table("utm_file_inventory").insert(chunk).execute()

            return True
        except Exception as e:
            print(f"Error syncing file inventory: {e}")
            return False

    async def get_project_files_from_db(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieves and builds the file tree from DB."""
        project_uuid = project_id
        if "-" not in project_id:
             resolved = await self.get_project_id_by_name(project_id)
             if resolved: project_uuid = resolved

        try:
            res = self.client.table("utm_file_inventory").select("*").eq("project_id", project_uuid).execute()
            rows = res.data if res.data else []
            
            if not rows:
                # Lazy Sync if empty
                await self.sync_file_inventory(project_id)
                res = self.client.table("utm_file_inventory").select("*").eq("project_id", project_uuid).execute()
                rows = res.data if res.data else []

            # Build Tree
            return self._build_tree(rows)
        except Exception as e:
            print(f"Error fetching inventory from DB: {e}")
            return []

    def _build_tree(self, inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Converts flat inventory list to nested tree structure."""
        tree = []
        # sort by path len to ensure parents processed before children?
        # Actually easier to build a map.
        
        # Structure: path -> node
        # But frontend expects recursive logic.
        
        # Let's just create a quick map of nodes
        # This is a bit complex to do generic hierarchy from paths in one pass.
        # Let's verify what frontend expects: 
        # { name: "foo", type: "folder", children: [...] }
        
        # 1. Create all nodes
        nodes_by_path = {}
        
        # First pass: Create node objects
        for item in inventory:
            path = item["file_path"]
            name = os.path.basename(path)
            node = {
                "name": name,
                "path": path, # This is usually absolute in old helper, here relative?
                              # Frontend uses this path for 'read_file_content'.
                              # 'read_file_content' in persistence_service (lines 175+) handles relative paths!
                              # So returning relative path is actually safer/better.
                "type": "folder" if item["is_directory"] else "file",
                "type": "folder" if item["is_directory"] else "file",
                "children": [] if item["is_directory"] else None,
                "last_modified": item.get("last_modified")
            }
            nodes_by_path[path] = node

        # 2. Nest them
        root_nodes = []
        
        # Sort keys to ensure deterministic order (though map keys are insertion ordered in modern python)
        sorted_paths = sorted(nodes_by_path.keys())
        
        for path in sorted_paths:
            node = nodes_by_path[path]
            parent_path = os.path.dirname(path).replace("\\", "/")
            
            if parent_path and parent_path != "." and parent_path in nodes_by_path:
                nodes_by_path[parent_path]["children"].append(node)
            else:
                # It's a top level node (relative to project root)
                root_nodes.append(node)

        # 3. Sort children? 
        # The frontend likely expects folders first.
        # We can do a recursive sort if needed, but 'sorted_paths' helps.
        
        return root_nodes

    # Release 3.5 Phase 2: Global Configuration
    async def get_global_config(self, key: str) -> Dict[str, Any]:
        """Retrieves a global configuration object."""
        try:
            res = self.client.table("utm_global_config").select("value").eq("key", key).execute()
            if res.data:
                return res.data[0]["value"]
            return {}
        except Exception as e:
            print(f"Error fetching global config {key}: {e}")
            return {}

    async def set_global_config(self, key: str, value: Dict[str, Any]) -> bool:
        """Upserts a global configuration object."""
        try:
            self.client.table("utm_global_config").upsert({
                "key": key,
                "value": value,
                "updated_at": "now()"
            }).execute()
            return True
        except Exception as e:
            print(f"Error saving global config {key}: {e}")
            return False


