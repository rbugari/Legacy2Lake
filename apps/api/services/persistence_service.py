import os
import shutil
from typing import Dict, Any, Optional, List
from supabase import create_client, Client
from .storage.factory import StorageFactory

class PersistenceService:
    print("LOADING PersistenceService v3 - WITH StorageProvider Abstraction")
    
    # Deprecated: Consumers should not rely on this.
    # We keep it pointing to local solutions for fallback reference or temp operations.
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "solutions"))

    # Stage-aligned Directory Constants
    STAGE_TRIAGE = "triage"
    STAGE_DRAFTING = "drafting"
    STAGE_REFINEMENT = "refinement"

    @classmethod
    def get_storage(cls):
        return StorageFactory.get_provider()

    @staticmethod
    def normalize_name(name: str) -> str:
        """Strict normalization: lowercase and alphanumeric only."""
        if not name: return ""
        import re
        # Lowercase and remove non-alphanumeric
        normalized = re.sub(r'[^a-z0-9]', '', name.lower())
        return normalized

    @classmethod
    def ensure_solution_dir(cls, solution_name: str, tenant_id: str = None) -> str:
        """Ensures the project directory exists. Returns the path/key prefix."""
        # Sanitize name using strict normalization
        folder_name = cls.normalize_name(solution_name)
        
        path = folder_name
        if tenant_id:
             path = f"{tenant_id}/{folder_name}"
             
        return cls.get_storage().ensure_directory(path)

    @classmethod
    def clean_downstream_folders(cls, project_id: str, tenant_id: str = None) -> bool:
        """Wipes all files and subdirectories in the project folder EXCEPT 'Triage'."""
        try:
            folder_name = cls.normalize_name(project_id)
            path = folder_name
            if tenant_id:
                path = f"{tenant_id}/{folder_name}"
            
            storage = cls.get_storage()
            if not storage.exists(path):
                return True

            items = storage.list_files(path, recursive=False)
            for item in items:
                # item['name'] is just the filename/foldername
                if item["name"].lower() == cls.STAGE_TRIAGE.lower():
                    continue
                
                full_item_path = item["path"] # Relative to storage root or absolute key
                if item["type"] == "folder":
                    storage.delete_directory(full_item_path)
                else:
                    storage.delete_file(full_item_path)
            return True
        except Exception as e:
            print(f"Error cleaning downstream folders for {project_id}: {e}")
            return False

    @classmethod
    def delete_project_directory(cls, project_id: str, tenant_id: str = None) -> bool:
        """Deletes the project directory from storage."""
        try:
            folder_name = cls.normalize_name(project_id)
            path = folder_name
            if tenant_id:
               path = f"{tenant_id}/{folder_name}"
            
            return cls.get_storage().delete_directory(path)
        except Exception as e:
            print(f"Error deleting directory {project_id}: {e}")
            return False

    @classmethod
    def save_transformation(cls, solution_name: str, task_name: str, code: str, tenant_id: str = None) -> str:
        """Saves a transpiled PySpark task to the solution directory."""
        dir_path = cls.ensure_solution_dir(solution_name, tenant_id)
        # Sanitize task name for filename
        filename = "".join([c if c.isalnum() else "_" for c in task_name]) + ".py"
        # We need to construct logical path. 
        # ensure_solution_dir returns the prefix (e.g. "tenant/proj/")
        # If dir_path ends with separator, join works.
        import os # Just in case for path.join, but we prefer string concat for cloud safety if mixed separators
        # Actually storage provider usually handles normalized paths.
        
        file_path = f"{dir_path.rstrip('/')}/{filename}"
        
        return cls.get_storage().save_file(file_path, code)

    @classmethod
    def save_documentation(cls, solution_name: str, doc_name: str, content: str, tenant_id: str = None) -> str:
        """Saves governance/technical documentation to the solution directory."""
        dir_path = cls.ensure_solution_dir(solution_name, tenant_id)
        filename = doc_name + ".md"
        file_path = f"{dir_path.rstrip('/')}/{filename}"
        
        return cls.get_storage().save_file(file_path, content)

    @classmethod
    def initialize_project_from_source(cls, project_id: str, source_type: str, file_path: str = None, github_url: str = None, overwrite: bool = False, tenant_id: str = None) -> bool:
        """Initializes a project directory. handles ZIP/Git via temp staging and uploads to Storage."""
        import zipfile
        import subprocess
        import tempfile

        try:
            # 1. Check existence in Storage
            folder_name = cls.normalize_name(project_id)
            target_path = folder_name
            if tenant_id: target_path = f"{tenant_id}/{folder_name}"
            
            storage = cls.get_storage()

            if storage.exists(target_path):
                 # Simple check: if list_files returns anything
                 files = storage.list_files(target_path, recursive=False)
                 if files:
                    if not overwrite:
                        print(f"Error: Project directory {target_path} is not empty and overwrite=False.")
                        return False
                    
                    print(f"Cleaning existing directory for {project_id} (overwrite=True)...")
                    storage.delete_directory(target_path)

            # 2. Local Staging
            with tempfile.TemporaryDirectory() as temp_dir:
                triage_dir = os.path.join(temp_dir, cls.STAGE_TRIAGE)
                os.makedirs(triage_dir, exist_ok=True)
                
                if source_type == "zip" and file_path:
                    # file_path is likely local temp path from UploadFile
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(triage_dir)
                    print(f"Extracted ZIP for {project_id} in temp.")
                    
                elif source_type == "github" and github_url:
                    subprocess.run(["git", "clone", github_url, triage_dir], check=True)
                    # Remove .git to save space/time
                    git_dir = os.path.join(triage_dir, ".git")
                    if os.path.exists(git_dir):
                        cls._robust_local_rmtree(git_dir) 
                    print(f"Cloned GitHub for {project_id} in temp.")
                
                # 3. Upload Staging to Storage
                # We walk the temp dir and upload each file
                print(f"Uploading staged files to {target_path}...")
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        local_f = os.path.join(root, file)
                        # Rel path from temp_dir
                        rel_path = os.path.relpath(local_f, temp_dir) # e.g. "Triage/folder/file.txt"
                        
                        # Dest path
                        dest_key = f"{target_path.rstrip('/')}/{rel_path.replace(os.sep, '/')}"
                        
                        # Read and Upload
                        with open(local_f, 'rb') as f:
                            content = f.read()
                            storage.save_file(dest_key, content, is_binary=True)
                            
            print(f"Project {project_id} initialized successfully in Storage.")
            return True
        except Exception as e:
            print(f"Error initializing project: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def _robust_local_rmtree(path: str):
        """Helper for local temp cleanup (git)"""
        import stat
        def on_error(func, path, exc_info):
            if not os.access(path, os.W_OK):
                os.chmod(path, stat.S_IWUSR)
                func(path)
            else:
                raise
        if os.path.exists(path):
            shutil.rmtree(path, onerror=on_error)

    @classmethod
    def get_project_files(cls, project_id: str, tenant_id: str = None) -> List[Dict[str, Any]]:
        """
        Returns a recursive query of the project's solution directory.
        [Fix] Handles case-sensitivity mismatch (DB=Uppercase, Storage=Lowercase) for R2.
        """
        folder_name = cls.normalize_name(project_id)
        
        # 1. Try exact match (Original logic)
        path = folder_name
        if tenant_id:
            path = f"{tenant_id}/{folder_name}"
        
        files = cls.get_storage().list_files(path, recursive=True)
        
        # 2. If empty, try lowercase path (common issue when migrating from Windows)
        if not files and any(c.isupper() for c in path):
             lower_path = path.lower()
             print(f"DEBUG: No files found at '{path}', trying lowercase '{lower_path}'...")
             files_lower = cls.get_storage().list_files(lower_path, recursive=True)
             if files_lower:
                 return files_lower

        return files

    @classmethod
    def read_file_content(cls, project_id: str, file_path: str, tenant_id: str = None) -> str:
        """Reads the content of a specific file within the project's solution directory."""
        # Security logic handled by providers usually, but we reconstruct key here
        
        folder_name = cls.normalize_name(project_id)
        root_path = folder_name
        if tenant_id:
             root_path = f"{tenant_id}/{folder_name}"
        
        # file_path coming from frontend usually is partial e.g. "Triage/file.txt"
        # or full key e.g. "tenant/proj/Triage/file.txt"
        
        # If the file_path already starts with root_path, use it as is
        # otherwise prepend
        
        clean_file_path = file_path.replace("\\", "/")
        clean_root = root_path.replace("\\", "/")
        
        if clean_file_path.startswith(clean_root):
            full_key = clean_file_path
        else:
            full_key = f"{clean_root}/{clean_file_path.lstrip('/')}"
            
        return cls.get_storage().read_file(full_key)

    @classmethod
    def generate_presigned_url(cls, project_id: str, file_path: str, tenant_id: str = None, expiration: int = 3600) -> Optional[str]:
        """Generates a temporary signed URL for a file."""
        folder_name = cls.normalize_name(project_id)
        root_path = folder_name
        if tenant_id:
             root_path = f"{tenant_id}/{folder_name}"
        
        clean_file_path = file_path.replace("\\", "/")
        clean_root = root_path.replace("\\", "/")
        
        if clean_file_path.startswith(clean_root):
            full_key = clean_file_path
        else:
            full_key = f"{clean_root}/{clean_file_path.lstrip('/')}"
            
        return cls.get_storage().generate_signed_url(full_key, expiration)

class SupabasePersistence:
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        
        if not key:
             print("DEBUG: Service Role Key MISSING. Falling back to ANON.")
             key = os.getenv("SUPABASE_ANON_KEY", "").strip()
        else:
             print(f"DEBUG: Initializing Supabase with Service Role Key (starts with {key[:5]}...)")

        self.client: Client = create_client(url, key)
        
        # [Release 3.6] Sanitize tenant_id: Ensure it's a valid UUID or None
        # This prevents DB syntax errors when non-UUID strings (like usernames) leak into identity headers.
        if tenant_id:
             import re
             uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
             if not uuid_pattern.match(tenant_id):
                 print(f"DEBUG: SupabasePersistence sanitizing non-UUID tenant_id: {tenant_id}")
                 tenant_id = None
                 
        self.tenant_id = tenant_id
        self.client_id = client_id

    async def _resolve_uuid(self, project_id_or_name: str) -> Optional[str]:
        """
        Internal helper to ensure we have a valid project UUID.
        If input contains '-', we assume it's a UUID and validate it (or at least return it).
        If not, we look it up by name.
        """
        if not project_id_or_name or project_id_or_name == "undefined":
            return None

        # Heuristic: UUIDs contain '-' and are 36 chars long. Project names usually don't.
        if "-" in project_id_or_name:
            # We could do a more rigorous UUID validation here if needed
            return project_id_or_name
            
        return await self.get_project_id_by_name(project_id_or_name)

    async def get_or_create_project(self, name: str, repo_url: str = None, source_tech: str = None, target_tech: str = None) -> str:
        """Finds or creates a project by name and returns its UUID. Respects Tenant Isolation."""
        # Force strict normalization for consistency across DB and R2
        name = PersistenceService.normalize_name(name)
        
        query = self.client.table("utm_projects").select("project_id", "settings").eq("name", name)
        
        # [Security] Ensure we only check current tenant's projects
        if self.tenant_id:
             query = query.eq("tenant_id", self.tenant_id)
             
        res = query.execute()
        
        settings = {"source_tech": source_tech, "target_tech": target_tech} if source_tech or target_tech else {}

        if res.data:
            project_id = res.data[0]["project_id"]
            existing_settings = res.data[0].get("settings") or {}
            
            # Update settings and repo_url if provided
            updates = {}
            if repo_url:
                updates["repo_url"] = repo_url
            
            if source_tech or target_tech:
                existing_settings.update(settings)
                updates["settings"] = existing_settings
                
            if updates:
                self.client.table("utm_projects").update(updates).eq("project_id", project_id).execute()
            return project_id
        
        data = {"name": name, "stage": "1", "settings": settings}
        if repo_url:
            data["repo_url"] = repo_url
        
        # Inject Identity
        if self.tenant_id: data["tenant_id"] = self.tenant_id
        if self.client_id: data["client_id"] = self.client_id
            
        res = self.client.table("utm_projects").insert(data).execute()
        return res.data[0]["project_id"]

    # --- Client Management (SaaS Admin) ---
    async def create_client(self, name: str) -> str:
        """Creates a new client company."""
        res = self.client.table("utm_clients").insert({"name": name}).execute()
        return res.data[0]["client_id"]

    async def list_clients(self) -> List[Dict[str, Any]]:
        """Lists all client companies."""
        res = self.client.table("utm_clients").select("*").execute()
        return res.data if res.data else []

    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Fetches tenant details including role."""
        res = self.client.table("utm_tenants").select("*").eq("tenant_id", tenant_id).execute()
        return res.data[0] if res.data else None

    async def list_projects(self) -> List[Dict[str, Any]]:
        """Returns a list of all projects, with asset counts and calculated progress."""
        query = self.client.table("utm_projects").select("*")
        if self.tenant_id:
            query = query.eq("tenant_id", self.tenant_id)
            
        res = query.execute()
        projects = res.data if res.data else []
        
        # Enrich with asset counts and progress
        for item in projects:
            item["id"] = item["project_id"]
            
            # Fetch asset count for this project
            try:
                asset_res = self.client.table("utm_objects").select("object_id", count="exact").eq("project_id", item["project_id"]).execute()
                item["assets_count"] = asset_res.count if asset_res.count is not None else 0
            except:
                item["assets_count"] = 0
                
            # Calculate progress based on stage (Aligned with WorkspacePage.tsx)
            stage_map = {
                "1": 5,    # DISCOVERY
                "2": 25,   # TRIAGE
                "3": 50,   # DRAFTING
                "4": 75,   # REFINEMENT
                "5": 90,   # GOVERNANCE
                "6": 100   # HANDOVER
            }
            item["progress"] = stage_map.get(str(item.get("stage", "1")), 0)

            # Release 3.7: Expose Lines Generated for Dashboard
            project_settings = item.get("settings", {}) or {}
            item["lines_generated"] = project_settings.get("lines_generated", 0)
            
            # Extract source_tech and target_tech from settings or config for dashboard display
            project_config = item.get("config", {}) or {}
            project_settings = item.get("settings", {}) or {}
            
            # Priority: settings (where get_or_create_project saves it) then config
            item["source_tech"] = project_settings.get("source_tech") or project_config.get("source_tech") or project_config.get("origin_tech")
            item["target_tech"] = project_settings.get("target_tech") or project_config.get("target_tech") or project_config.get("dest_tech")
            
        return projects

    async def list_supported_techs(self, role: str = None) -> List[Dict[str, Any]]:
        """Lists supported source or target technologies from the system catalog."""
        try:
            query = self.client.table("utm_supported_techs").select("tech_id, label, description, version, logo_url").eq("is_active", True)
            if role:
                query = query.eq("role", role)
            res = query.execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error listing supported techs: {e}")
            return []

    async def list_agents(self) -> List[Dict[str, Any]]:
        """Lists agents from the utm_agent_catalog."""
        try:
            res = self.client.table("utm_agent_catalog").select("*").eq("is_active", True).execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error listing agents: {e}")
            return []

    async def list_system_catalog(self, tech_type: str = None) -> List[Dict[str, Any]]:
        """Lists technologies from the utm_system_catalog (Metadata)."""
        try:
            query = self.client.table("utm_system_catalog").select("*").eq("is_active", True)
            if tech_type:
                query = query.eq("type", tech_type)
            res = query.execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error listing system catalog: {e}")
            return []

    async def delete_project(self, project_id: str) -> bool:
        """Deletes the project and its assets from the database."""
        try:
            resolved_id = await self._resolve_uuid(project_id)
            if not resolved_id:
                print(f"Error: Could not resolve project ID for deletion: {project_id}")
                return False

            self.client.table("utm_projects").delete().eq("project_id", resolved_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting project {project_id} from DB: {e}")
            return False

    async def get_project_stats(self, project_id: str) -> Dict[str, int]:
        """Returns summarized counts of assets by category for a project."""
        try:
            resolved_id = await self._resolve_uuid(project_id)
            if not resolved_id:
                return {"core": 0, "ignored": 0, "pending": 0}

            res = self.client.table("utm_objects").select("type").eq("project_id", resolved_id).execute()
            assets = res.data or []
            return {
                "core": len([a for a in assets if a.get("type") == "CORE"]),
                "ignored": len([a for a in assets if a.get("type") == "IGNORED"]),
                "pending": len([a for a in assets if a.get("type") not in ["CORE", "IGNORED", "SUPPORT"]])
            }
        except Exception as e:
            print(f"Error fetching stats for {project_id}: {e}")
            return {"core": 0, "ignored": 0, "pending": 0}

    async def get_project_id_by_name(self, name: str) -> Optional[str]:
        """Resolves a project name (slug) to its UUID. Respects Tenant Isolation."""
        query = self.client.table("utm_projects").select("project_id").eq("name", name)
        
        if self.tenant_id:
            query = query.eq("tenant_id", self.tenant_id)
            
        res = query.execute()
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
        """Returns project metadata (name, repo_url, status, stage, prompt, settings, config, is_active)."""
        try:
            resolved_id = await self._resolve_uuid(project_id)
            if not resolved_id:
                return None

            query = self.client.table("utm_projects").select("project_id, tenant_id, name, repo_url, status, stage, prompt, settings, config, is_active").eq("project_id", resolved_id)
            if self.tenant_id:
                query = query.eq("tenant_id", self.tenant_id)
                
            res = query.execute()
            if res.data:
                item = res.data[0]
                item["id"] = item["project_id"]
                
                # Enrich with Tech Stack for easy access
                settings = item.get("settings") or {}
                item["source_tech"] = settings.get("source_tech")
                item["target_tech"] = settings.get("target_tech")
                
                return item
        except Exception:
            pass
        return None

    async def save_asset(self, project_id: str, filename: str, content: str, asset_type: str, file_hash: str, source_path: str = None) -> str:
        """Saves an asset (e.g. .dtsx file) to the database."""
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            raise ValueError(f"Could not resolve project ID for saving asset: {project_id}")

        data = {
            "project_id": resolved_id,
            "source_name": filename,
            "raw_content": content,
            "type": asset_type,
            "hash": file_hash
        }
        if self.tenant_id: data["tenant_id"] = self.tenant_id
        if self.client_id: data["client_id"] = self.client_id
            
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
        
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            print(f"Error: batch_save_assets called with invalid project_id: {project_id}")
            return []

        # 1. State Check
        try:
             proj_res = self.client.table("utm_projects").select("status").eq("project_id", resolved_id).execute()
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
                "project_id": resolved_id,
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
            if self.tenant_id: insert_data[-1]["tenant_id"] = self.tenant_id
            if self.client_id: insert_data[-1]["client_id"] = self.client_id
            
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
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            return []

        try:
            res = self.client.table("utm_objects").select("*").eq("project_id", resolved_id).execute()
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
            resolved_id = await self._resolve_uuid(project_id_or_name)
            if not resolved_id:
                return False

            self.client.table("utm_projects").update({"stage": stage}).eq("project_id", resolved_id).execute()
            return True
        except Exception as e:
            print(f"Error updating stage for {project_id_or_name}: {e}")
            return False

    async def save_project_layout(self, project_id_or_name: str, layout_data: Dict[str, Any]) -> str:
        """Saves the graph layout as a JSON asset. Handles both UUID and Name."""
        import json
        
        resolved_id = await self._resolve_uuid(project_id_or_name)
        if not resolved_id:
            # If it's a new project by name, we might need to create it? 
            # But usually layout is saved for existing projects.
            # Fallback to creating if it looks like a name.
            if "-" not in project_id_or_name:
                resolved_id = await self.get_or_create_project(project_id_or_name)
            else:
                return ""

        content = json.dumps(layout_data)
        res = self.client.table("utm_objects").select("object_id").eq("project_id", resolved_id).eq("type", "LAYOUT").execute()
        
        if res.data:
            asset_id = res.data[0]["object_id"]
            self.client.table("utm_objects").update({"raw_content": content}).eq("object_id", asset_id).execute()
            return asset_id
        else:
            return await self.save_asset(resolved_id, "layout.json", content, "LAYOUT", "v1")

    async def get_project_layout(self, project_id_or_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves the graph layout. Handles both UUID and Name."""
        import json
        resolved_id = await self._resolve_uuid(project_id_or_name)
        if not resolved_id:
            return None

        res = self.client.table("utm_objects").select("raw_content").eq("project_id", resolved_id).eq("type", "LAYOUT").execute()
        if res.data:
            try:
                return json.loads(res.data[0]["raw_content"])
            except:
                return None
        return None

    async def update_project_prompt(self, project_id: str, prompt: str) -> bool:
        """Updates the custom system prompt for a project."""
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            return False

        try:
            self.client.table("utm_projects").update({"prompt": prompt}).eq("project_id", resolved_id).execute()
            return True
        except Exception as e:
            print(f"Error updating prompt for {project_id}: {e}")
            return False

    async def reset_project_data(self, project_id: str) -> bool:
        """Clears all assets and resets stage/status for a project."""
        try:
            resolved_id = await self._resolve_uuid(project_id)
            if not resolved_id:
                return False

            # 1. Get object_ids for this project to handle nested deletions
            obj_res = self.client.table("utm_objects").select("object_id").eq("project_id", resolved_id).execute()
            object_ids = [o["object_id"] for o in obj_res.data]
            
            if object_ids:
                # 2. Delete from dependent tables (satisfy foreign keys)
                # utm_logical_steps -> utm_objects (object_id)
                self.client.table("utm_logical_steps").delete().in_("object_id", object_ids).execute()
                # [Release 4.2] utm_transformations -> utm_objects (asset_id)
                self.client.table("utm_transformations").delete().in_("asset_id", object_ids).execute()
            
            # 2.5 Clean per-asset context overrides
            self.client.table("utm_asset_context").delete().eq("project_id", resolved_id).execute()

            # 3. Delete main assets (utm_objects)
            self.client.table("utm_objects").delete().eq("project_id", resolved_id).execute()
            
            # 4. Clean File Inventory and Logs
            self.client.table("utm_execution_logs").delete().eq("project_id", resolved_id).execute()
            self.client.table("utm_file_inventory").delete().eq("project_id", resolved_id).execute()
            
            # 4.5 Clean File System (except Triage)
            project_name = await self.get_project_name_by_id(resolved_id)
            if project_name:
                PersistenceService.clean_downstream_folders(project_name)

            # 5. Reset stage to 1 and status to TRIAGE
            self.client.table("utm_projects").update({
                "stage": "1",
                "status": "TRIAGE",
                "triage_approved_at": None
            }).eq("project_id", resolved_id).execute()
            
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
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            return False

        data = {"status": status}
        if status == "DRAFTING":
            data["triage_approved_at"] = "now()"
        
        try:
            self.client.table("utm_projects").update(data).eq("project_id", resolved_id).execute()
            return True
        except Exception as e:
            print(f"Error updating status: {e}")
            return False

    async def get_project_status(self, project_id: str) -> str:
         resolved_id = await self._resolve_uuid(project_id)
         if not resolved_id:
             return "TRIAGE"

         try:
             res = self.client.table("utm_projects").select("status").eq("project_id", resolved_id).execute()
             if res.data:
                 return res.data[0].get("status", "TRIAGE")
         except:
             pass
         return "TRIAGE"

    async def update_project_settings(self, project_id: str, settings: Dict[str, Any]) -> bool:
        """Updates the project settings JSONB column."""
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            return False

        try:
            self.client.table("utm_projects").update({"settings": settings}).eq("project_id", resolved_id).execute()
            return True
        except Exception as e:
            print(f"Error updating settings for {project_id}: {e}")
            return False

    async def update_project_metadata(self, project_id: str, metadata: Dict[str, Any]) -> bool:
        """Updates arbitrary metadata on the project record."""
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id: return False
        try:
            self.client.table("utm_projects").update(metadata).eq("project_id", resolved_id).execute()
            return True
        except Exception as e:
            print(f"Error updating metadata for {project_id}: {e}")
            return False

    async def check_cancellation(self, project_id: str) -> bool:
        """Checks if cancellation has been requested for a project."""
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id: return False
        try:
            res = self.client.table("utm_projects").select("cancellation_requested").eq("project_id", resolved_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0].get("cancellation_requested", False)
            return False
        except Exception:
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
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            return []

        try:
            # [Release 3.5] Table Renamed: 'asset_context' -> 'utm_asset_context'
            res = self.client.table("utm_asset_context").select("*").eq("project_id", resolved_id).execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error fetching project context: {e}")
            return []

    # Release 1.3 Knowledge Registry Methods
    async def get_design_registry(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieves all global design rules for a project."""
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            return []

        try:
            # [Release 3.5] Table Renamed: 'design_registry' -> 'utm_design_registry'
            res = self.client.table("utm_design_registry").select("*").eq("project_id", resolved_id).execute()
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

    # Release 3.5 Phase 3: Universal Persistence (Prompts & Catalogs)
    # ----------------------------------------------------------------

    async def get_prompt(self, prompt_id: str, version: Optional[int] = None) -> str:
        """
        Fetching prompt content from DB with local file fallback and versioning support.
        Supports Tenant-Priority: Fetches tenant-specific prompt if exists, otherwise global (tenant_id is NULL).
        """
        try:
            print(f"DEBUG: Fetching prompt '{prompt_id}' (Tenant: {self.tenant_id or 'GLOBAL'}) from DB...")
            
            query = self.client.table("utm_prompts").select("content, version_number, tenant_id")
            query = query.eq("prompt_id", prompt_id)
            
            if self.tenant_id:
                # [Release 3.6] Support Global Fallback: Query matches my tenant OR is null
                # We sort by tenant_id DESC to ensure specific UUID comes before NULL
                query = query.or_(f"tenant_id.eq.{self.tenant_id},tenant_id.is.null")
                query = query.order("tenant_id", desc=True)
            else:
                # Strictly global
                query = query.is_("tenant_id", "null")
            
            if version:
                query = query.eq("version_number", version)
            else:
                query = query.eq("is_active", True)
                
            res = query.execute()
            
            if res.data and res.data[0].get("content"):
                print(f"DEBUG: Loaded prompt {prompt_id} v{res.data[0].get('version_number')} from DB " + 
                      f"({'Tenant' if res.data[0].get('tenant_id') else 'Global'})")
                return res.data[0]["content"]
            
            # Fallback to local file with auto-seed
            print(f"DEBUG: Prompt '{prompt_id}' not found in DB. Attempting auto-seed from local file...")
            return await self._auto_seed_prompt(prompt_id)
                
        except Exception as e:
            print(f"Error fetching prompt {prompt_id}: {e}")
        return ""

    async def _auto_seed_prompt(self, prompt_id: str) -> str:
        """Seed a prompt from local markdown file to DB as v1 Active."""
        try:
            prompt_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompts"))
            file_path = os.path.join(prompt_dir, f"{prompt_id}.md")
            
            if not os.path.exists(file_path):
                print(f"DEBUG: Local prompt file not found at {file_path}")
                return ""
                
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Seed to DB
            data = {
                "tenant_id": self.tenant_id,
                "prompt_id": prompt_id,
                "version_number": 1,
                "content": content,
                "is_active": True,
                "changelog": "Initial auto-seed from local .md file"
            }
            
            self.client.table("utm_prompts").insert(data).execute()
            print(f"DEBUG: Successfully auto-seeded {prompt_id} v1 to DB")
            return content
            
        except Exception as e:
            print(f"DEBUG: Error auto-seeding prompt {prompt_id}: {e}")
            return ""

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List all prompts with content."""
        try:
            res = self.client.table("utm_prompts").select("*").execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error listing prompts: {e}")
            return []

    async def list_supported_techs(self) -> List[Dict[str, Any]]:
        """Returns valid source/target technologies from the unified catalog."""
        try:
            res = self.client.table("utm_system_catalog").select("*").eq("is_active", True).execute()
            # Map for backward compatibility if any frontend still expects 'role'
            for item in res.data:
                if "role" not in item:
                    item["role"] = "SOURCE" if item["type"] == "origin" else "TARGET"
                if "label" not in item:
                    item["label"] = item["name"]
            return res.data if res.data else []
        except Exception as e:
            print(f"Error listing techs: {e}")
            return []

    async def save_prompt(self, prompt_id: str, content: str) -> bool:
        """
        Updates the ACTIVE prompt version in the DB.
        DEPRECATED: Use PromptLabService for versioned imports.
        """
        try:
            print(f"DEBUG: Saving (updating active) prompt '{prompt_id}' length={len(content)}")
            
            # Find current active version
            query = self.client.table("utm_prompts").select("version_number").eq("prompt_id", prompt_id).eq("is_active", True)
            if self.tenant_id:
                query = query.eq("tenant_id", self.tenant_id)
            
            res = query.execute()
            
            if res.data:
                v = res.data[0]["version_number"]
                self.client.table("utm_prompts").update({
                    "content": content
                }).eq("prompt_id", prompt_id).eq("version_number", v).execute()
            else:
                # If no active version exists, create v1 active
                await self._auto_seed_prompt(prompt_id)
                # Then update it just in case content differs from file
                self.client.table("utm_prompts").update({
                    "content": content
                }).eq("prompt_id", prompt_id).eq("version_number", 1).execute()
            
            return True
        except Exception as e:
            print(f"Error saving prompt {prompt_id}: {e}")
            return False

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Returns the list of available LLM models.
        Tenant-Aware: 
        1. Returns models where (tenant_id = current_tenant OR is_public = True)
        2. Filters out models if the tenant DOES NOT have the provider configured in their Vault.
        """
        try:
            # 1. Fetch Candidates (Public or Tenant-Specific)
            query = self.client.table("utm_model_catalog").select("*")
            
            if self.tenant_id:
                # STRICT ISOLATION: User sees ONLY models they defined.
                # We do NOT show 'is_public' system models (No Suggestions).
                query = query.eq("tenant_id", self.tenant_id)
            else:
                # Admin (no tenant context) sees everything? Or just public?
                # Let's show everything for now if no tenant, or just public if no specific admin view logic.
                pass 

            res = query.execute()
            candidates = res.data if res.data else []
            
            if not self.tenant_id:
                return candidates

            # 2. Fetch Active Providers from Vault
            # If I'm a tenant, I only want to see models I can actually USE.
            vault_res = self.client.table("utm_provider_vault").select("provider_name").eq("tenant_id", self.tenant_id).eq("is_active", True).execute()
            active_providers = {v["provider_name"].strip().lower() for v in vault_res.data}
            
            print(f"[DEBUG] Active Providers for Tenant {self.tenant_id}: {active_providers}")

            # 3. Filter
            final_list = []
            for m in candidates:
                p = m.get("provider", "").strip().lower()
                if p in active_providers:
                    final_list.append(m)
                else:
                    print(f"[DEBUG] Model {m.get('model_id')} ORPHAN REVEALED. Provider '{p}' not in active list {active_providers}")
                    # EXPOSE ORPHAN: Allow it to be seen so it can be fixed/deleted.
                    final_list.append(m)

            return final_list

        except Exception as e:
            print(f"Error listing models: {e}")
            return []

    async def resolve_agent_model(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Resolves the configured model for a specific agent for the current tenant.
        Strictly requires DB configuration; no ENV fallbacks.
        """
        try:
            # 1. Get Agent Config (Global mapping of agent -> model)
            query = self.client.table("utm_agent_matrix").select("*").eq("agent_id", agent_id).eq("is_active", True)
            
            # [Fix] Filter by tenant if provided
            if self.tenant_id:
                query = query.eq("tenant_id", self.tenant_id)
            
            res = query.execute()
            if not res.data:
                return None
            
            agent_config = res.data[0]
            model_id = agent_config["model_id"]
            
            # 2. Get Model Details from Catalog
            model_res = self.client.table("utm_model_catalog").select("*").eq("model_id", model_id).execute()
            if not model_res.data:
                return None
                
            model = model_res.data[0]
            provider = model.get("provider", "azure").lower()
            
            # 3. Get Credentials from Vault (STRICTLY Tenant-Specific)
            if not self.tenant_id:
                # Security: Operations without tenant ID cannot use LLM if multi-tenancy is active
                return None
                
            vault_res = self.client.table("utm_provider_vault")\
                .select("api_key, base_url")\
                .eq("tenant_id", self.tenant_id)\
                .ilike("provider_name", provider)\
                .execute()
            
            if not vault_res.data or not vault_res.data[0].get("api_key"):
                # No credentials for this tenant/provider
                return None

            api_key = vault_res.data[0].get("api_key")
            vault_url = vault_res.data[0].get("base_url")

            # [Refactor] Prioritize Provider URL (Vault) over Model URL
            # If the provider has a base_url, we use that. 
            # If not, we fall back to the model's api_url (legacy support).
            final_url = vault_url
            if not final_url:
                 final_url = model.get("api_url")
                 if final_url:
                     print(f"[MATRIX] Warning: Using Legacy Model URL for {agent_id}. Please migrate URL to Provider Vault.")

            print(f"[MATRIX] Resolved {agent_id} -> {provider} ({model_id}) for tenant {self.tenant_id}")

            # [Fix] O1/O3 models require default temperature (1)
            temp_val = agent_config.get("temperature", 0.0)
            m_id = str(model.get("model_id") or "").lower()
            if m_id.startswith("o1") or m_id.startswith("o3"):
                temp_val = 1.0

            deployment_name = model.get("deployment_id") or model.get("model_id")
            print(f"[MATRIX] Resolved Deployment: '{deployment_name}' for Agent {agent_id}")

            return {
                "provider": provider,
                "deployment": deployment_name,
                "api_version": model.get("api_version"),
                "endpoint": final_url,
                "api_key": api_key,
                "temperature": temp_val
            }
        except Exception as e:
            print(f"Error resolving agent model {agent_id}: {e}")
            return None

    async def list_agents(self) -> List[Dict[str, Any]]:
        """Returns the agent catalog."""
        try:
            res = self.client.table("utm_agent_catalog").select("*").eq("is_active", True).execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error listing agents: {e}")
            return []

    async def list_stages(self) -> List[Dict[str, Any]]:
        """Returns the configured project stages."""
        try:
            res = self.client.table("utm_stages").select("*").eq("is_active", True).order("stage_id").execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error listing stages: {e}")
            return []

    # Release 3.5: Execution Logs & File Inventory
    # --------------------------------------------
    
    async def log_execution(self, project_id: str, phase: str, message: str, step: str = None, level: str = "INFO"):
        """Persists a log entry to the database."""
        try:
            # Resolve UUID if project_id is a name
            resolved_id = await self._resolve_uuid(project_id)
            if not resolved_id:
                 print(f"DEBUG: Could not resolve project_id {project_id} for log_execution")
                 return

            data = {
                "project_id": resolved_id,
                "phase": phase,
                "step": step or phase,
                "message": message,
                "level": level
            }
            self.client.table("utm_execution_logs").insert(data).execute()
        except Exception as e:
            print(f"Error logging to DB: {e}")

    async def get_execution_logs(self, project_id: str, phase: str = None) -> List[Dict[str, Any]]:
        """Retrieves execution logs for a project, optionally filtered by phase."""
        try:
            resolved_id = await self._resolve_uuid(project_id)
            if not resolved_id:
                print(f"DEBUG: Could not resolve project_id {project_id} for get_execution_logs")
                return []

            query = self.client.table("utm_execution_logs").select("*").eq("project_id", resolved_id)
            if phase:
                query = query.eq("phase", phase)
            
            # Sort by creation time to ensure chronological order
            res = query.order("created_at", desc=False).execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error fetching execution logs: {e}")
            return []

    async def clear_execution_logs(self, project_id: str, phase: str = None) -> bool:
        """Clears execution logs for a project, optionally filtered by phase."""
        try:
            resolved_id = await self._resolve_uuid(project_id)
            if not resolved_id:
                print(f"DEBUG: Could not resolve project_id {project_id} for clear_execution_logs")
                return False

            query = self.client.table("utm_execution_logs").delete().eq("project_id", resolved_id)
            if phase:
                query = query.eq("phase", phase)
            query.execute()
            return True
        except Exception as e:
            print(f"Error clearing execution logs: {e}")
            return False

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

    # --- Project Settings (v1.5) ---
    async def get_project_settings(self, project_id: str) -> Dict[str, Any]:
        """Retrieves settings for a specific project."""
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            return {}

        try:
            res = self.client.table("utm_projects").select("settings").eq("project_id", resolved_id).execute()
            if res.data:
                return res.data[0].get("settings") or {}
            return {}
        except Exception as e:
            print(f"Error fetching settings for project {project_id}: {e}")
            return {}

    async def update_project_settings(self, project_id: str, settings: Dict[str, Any]) -> bool:
        """Updates (merges) settings for a specific project."""
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            return False

        try:
            # First get current to merge
            current = await self.get_project_settings(resolved_id)
            updated = {**current, **settings}
            
            self.client.table("utm_projects").update({
                "settings": updated
            }).eq("project_id", resolved_id).execute()
            return True
        except Exception as e:
            print(f"Error updating settings for project {project_id}: {e}")
            return False

    async def resolve_llm_for_agent(self, agent_id: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Dynamically resolves LLM configuration for a specific agent.
        Logic: 
        1. Query matrix to find assigned model_id.
        2. Query model_catalog for technical specs.
        3. Query vault for provider credentials.
        """
        try:
            # 1. Get Model Assignment from Matrix
            query = self.client.table("utm_agent_matrix").select("model_id").eq("agent_id", agent_id)
            if self.tenant_id:
                query = query.eq("tenant_id", self.tenant_id)
            
            matrix_res = query.execute()

            # Release 3.7: Fallback to Global Helper if no specific assignment
            if not matrix_res.data and agent_id != "agent-helper":
                print(f"[AUTH] Agent {agent_id} has no explicit assignment for tenant {self.tenant_id}. Falling back to helper.")
                query_h = self.client.table("utm_agent_matrix").select("model_id").eq("agent_id", "agent-helper")
                if self.tenant_id:
                    query_h = query_h.eq("tenant_id", self.tenant_id)
                matrix_res = query_h.execute()
            
            if not matrix_res.data:
                return {"error": f"No model assigned to {agent_id} in matrix and no helper found."}
            
            model_id = matrix_res.data[0]["model_id"]

            # 2. Get Technical Specs from Catalog
            catalog_res = self.client.table("utm_model_catalog").select("*").eq("model_id", model_id).execute()
            if not catalog_res.data:
                return {"error": f"Model {model_id} not found in catalog"}
            
            model = catalog_res.data[0]
            provider_type = model.get("provider", "openai").lower()

            # 3. Get Credentials from Vault (Context Aware)
            vault_query = self.client.table("utm_provider_vault").select("*").ilike("provider_name", provider_type)
            if self.tenant_id:
                vault_query = vault_query.eq("tenant_id", self.tenant_id)
            
            vault_res = vault_query.execute()
            creds = vault_res.data[0] if vault_res.data else {}

            # 4. Build Standardized Config
            # [Refactor] Prioritize Vault Base URL
            final_url = creds.get("base_url")
            if not final_url:
                 final_url = model.get("api_url")

            # [Fix] O1/O3 models require default temperature (1)
            temp_val = 0
            m_id = str(model.get("model_id") or "").lower()
            if m_id.startswith("o1") or m_id.startswith("o3"):
                temp_val = 1

            config = {
                "provider": provider_type,
                "model_name": model.get("model_id"), # e.g. "gpt-4"
                "deployment_id": model.get("deployment_id"),
                "api_version": model.get("api_version"),
                "api_url": final_url,
                "api_key": creds.get("api_key"),
                "temperature": temp_val
            }

            return config
            
        except Exception as e:
            print(f"Error resolving LLM for {agent_id}: {e}")

    # --- System Catalog & Multi-Tenancy (v3.7) ---

    async def list_system_catalog(self) -> List[Dict[str, Any]]:
        """Returns all supported technologies from the unified catalog."""
        try:
            res = self.client.table("utm_system_catalog").select("*").order("name").execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error listing system catalog: {e}")
            return []

    async def list_models(self) -> List[Dict[str, Any]]:
        """Returns all models from the global catalog, filtered by tenant if applicable."""
        try:
            query = self.client.table("utm_model_catalog").select("*")
            if self.tenant_id:
                # [Refactor] Consider showing both global and tenant-specific
                # For now, just all available
                pass
            res = query.order("label").execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error listing models: {e}")
            return []

    async def list_supported_techs(self, role: str = None) -> List[Dict[str, Any]]:
        """Alias for backward compatibility with some legacy routers."""
        data = await self.list_system_catalog()
        if not role:
            return data
        
        # Filter by role
        filtered = []
        for tech in data:
            tech_role = "SOURCE" if tech.get("type") == "origin" else "TARGET"
            if tech_role == role.upper():
                filtered.append(tech)
        return filtered


