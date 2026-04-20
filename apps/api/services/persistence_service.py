import os
import shutil
import ssl
from typing import Dict, Any, Optional, List
from datetime import datetime
from supabase import create_client, Client
from .storage.factory import StorageFactory
import httpx
from apps.api.prompts.catalog import get_prompt_spec
from apps.utm.core.interfaces import EvidenceItem, ProcessHint

# Disable SSL verification globally for development
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Monkey-patch httpx Client to disable SSL verification by default
_original_httpx_client_init = httpx.Client.__init__

def _patched_httpx_client_init(self, *args, **kwargs):
    kwargs.setdefault('verify', False)
    return _original_httpx_client_init(self, *args, **kwargs)

httpx.Client.__init__ = _patched_httpx_client_init

class PersistenceService:
    print("LOADING PersistenceService v3 - WITH StorageProvider Abstraction")
    
    # Deprecated: Consumers should not rely on this.
    # We keep it pointing to local solutions for fallback reference or temp operations.
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "solutions"))

    # Stage-aligned Directory Constants
    STAGE_SOURCE = "source"
    STAGE_TRIAGE = "triage"
    STAGE_DRAFTING = "drafting"
    STAGE_REFINEMENT = "refinement"

    @classmethod
    def get_storage(cls):
        return StorageFactory.get_provider()

    @classmethod
    def get_supabase_persistence(cls, tenant_id: str = None) -> 'SupabasePersistence':
        return SupabasePersistence(tenant_id=tenant_id)

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
                if item["name"].lower() in [cls.STAGE_TRIAGE.lower(), cls.STAGE_SOURCE.lower()]:
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
                source_dir = os.path.join(temp_dir, cls.STAGE_SOURCE)
                os.makedirs(source_dir, exist_ok=True)
                
                if source_type == "zip" and file_path:
                    # file_path is likely local temp path from UploadFile
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(source_dir)
                    print(f"Extracted ZIP for {project_id} in temp.")
                    
                elif source_type == "github" and github_url:
                    subprocess.run(["git", "clone", github_url, source_dir], check=True)
                    # Remove .git to save space/time
                    git_dir = os.path.join(source_dir, ".git")
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
    _supports_understanding_columns: Optional[bool] = None

    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None, user_id: Optional[str] = None, role: Optional[str] = None):
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
        self.user_id = user_id  # [v3.9] Track user_id for multi-user operations
        self.role = role # [v4.2] Track role for visibility rules

    def table(self, table_name: str):
        return self.client.table(table_name)

    def rpc(self, fn_name: str, params: dict = None):
        return self.client.rpc(fn_name, params)

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
        
        # [Security] Ensure we only check current tenant's projects (Admins bypass)
        if self.tenant_id and self.role != "ADMIN":
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
        
        data = {"name": name, "stage": "0", "status": "DISCOVERY", "settings": settings}
        if repo_url:
            data["repo_url"] = repo_url
        
        # [v3.9] Inject tenant_id and user_id for isolation and audit
        if self.tenant_id: 
            data["tenant_id"] = self.tenant_id
        if self.user_id:  
            data["created_by_user_id"] = self.user_id  # Track who created the project
            
        res = self.client.table("utm_projects").insert(data).execute()
        return res.data[0]["project_id"]

    # --- Tenant Management (SaaS Admin) ---
    async def create_tenant(self, name: str) -> str:
        """Creates a new tenant company."""
        res = self.client.table("utm_tenants").insert({"name": name}).execute()
        return res.data[0]["tenant_id"]

    async def list_tenants(self) -> List[Dict[str, Any]]:
        """Lists all tenant companies."""
        res = self.client.table("utm_tenants").select("*").execute()
        return res.data if res.data else []

    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Fetches tenant details including role."""
        res = self.client.table("utm_tenants").select("*").eq("tenant_id", tenant_id).execute()
        return res.data[0] if res.data else None

    async def list_projects(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all projects, with asset counts and calculated progress.
        [v4.2] Role-Based Visibility:
        - ADMIN: All projects
        - MANAGER: All projects in tenant
        - COLLABORATOR / VIEWER: Projects where user is a member
        """
        query = self.client.table("utm_projects").select("*")
        
        # Role-based filtering
        if self.role == "ADMIN":
            # Admin sees all projects from all tenants
            pass
        elif self.role == "MANAGER":
            # Manager sees all projects in their tenant
            if self.tenant_id:
                query = query.eq("tenant_id", self.tenant_id)
        else:
            # COLLABORATOR / VIEWER / others see only explicit memberships
            if self.user_id:
                # Subquery to get projects where user is member
                member_query = self.client.table("utm_project_members").select("project_id").eq("user_id", self.user_id)
                member_res = member_query.execute()
                allowed_ids = [m["project_id"] for m in member_res.data] if member_res.data else []
                
                if allowed_ids:
                    query = query.in_("project_id", allowed_ids)
                else:
                    # No memberships = no projects
                    return []
            else:
                # No identity provided = no projects for non-admins
                return []
            
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
                "0": 5,    # DISCOVERY
                "1": 25,   # TRIAGE
                "2": 50,   # DRAFTING
                "3": 75,   # REFINEMENT
                "4": 90,   # GOVERNANCE
                "5": 100   # HANDOVER
            }
            item["progress"] = stage_map.get(str(item.get("stage", "0")), 0)

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
        
        if self.tenant_id and self.role != "ADMIN":
            query = query.eq("tenant_id", self.tenant_id)
            
        res = query.execute()
        if res.data:
            return res.data[0]["project_id"]
        return None

    async def get_project_name_by_id(self, project_id: str) -> Optional[str]:
        """Resolves a project UUID to its name."""
        try:
            query = self.client.table("utm_projects").select("name").eq("project_id", project_id)
            if self.tenant_id and self.role != "ADMIN":
                query = query.eq("tenant_id", self.tenant_id)
            
            res = query.execute()
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

            select_extended = "project_id, tenant_id, name, repo_url, status, stage, prompt, settings, config, is_active, quick_assessment, readiness_summary, understanding_generated_at, understanding_version, understanding_payload"
            select_legacy = "project_id, tenant_id, name, repo_url, status, stage, prompt, settings, config, is_active, quick_assessment, readiness_summary"

            res = None
            if self._supports_understanding_columns is not False:
                try:
                    query = self.client.table("utm_projects").select(select_extended).eq("project_id", resolved_id)
                    if self.tenant_id and self.role != "ADMIN":
                        query = query.eq("tenant_id", self.tenant_id)
                    res = query.execute()
                    type(self)._supports_understanding_columns = True
                except Exception as exc:
                    message = str(exc).lower()
                    if (
                        "understanding_generated_at" in message
                        or "understanding_version" in message
                        or "understanding_payload" in message
                    ):
                        type(self)._supports_understanding_columns = False
                    else:
                        raise

            if res is None:
                query = self.client.table("utm_projects").select(select_legacy).eq("project_id", resolved_id)
                if self.tenant_id and self.role != "ADMIN":
                    query = query.eq("tenant_id", self.tenant_id)
                res = query.execute()
            if res.data:
                item = res.data[0]
                item["id"] = item["project_id"]
                
                # Enrich with Tech Stack for easy access
                settings = item.get("settings") or {}
                item["source_tech"] = settings.get("source_tech")
                item["target_tech"] = settings.get("target_tech")

                # Backward-compat: expose understanding fields from settings when
                # dedicated columns are not available in the current schema.
                item.setdefault("understanding_generated_at", settings.get("understanding_generated_at"))
                item.setdefault("understanding_version", settings.get("understanding_version"))
                item.setdefault("understanding_payload", settings.get("understanding_payload"))
                
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
        # [v3.9] Only tenant_id for isolation (object ownership tracked via project)
        if self.tenant_id: 
            data["tenant_id"] = self.tenant_id
            
        if source_path:
            data["source_path"] = source_path
            
        res = self.client.table("utm_objects").insert(data).execute()
        return res.data[0]["object_id"]

    async def update_asset_metadata(self, asset_id: str, updates: Dict[str, Any]) -> bool:
        """Updates specific fields of an asset (type, selected, metadata, operational metadata, business metadata)."""
        allowed_fields = [
            "type", "selected", "metadata", 
            "frequency", "load_strategy", "criticality", "is_pii", "masking_rule",
            "business_entity", "target_name",
            # Sprint 8-12: Code generation and visualization fields
            "generated_code", "tech_id", "layer", "object_name",
            "validation_result", "optimization_metadata", "schema_metadata",
            "row_count", "column_count", "quality_score", "quality_violations"
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
        """Upserts multiple assets in a single call. Blocks once the project is post-triage."""
        
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            print(f"Error: batch_save_assets called with invalid project_id: {project_id}")
            return []

        # 1. State Check
        try:
             proj_res = self.client.table("utm_projects").select("status").eq("project_id", resolved_id).execute()
             if proj_res.data:
                 current_status = proj_res.data[0].get("status", "TRIAGE")
                 locked_statuses = {
                     "TRIAGE_APPROVED", "DRAFTING", "ORCHESTRATING", "DRAFTED",
                     "REFINEMENT", "REFINING", "REFINED",
                     "GOVERNANCE", "DOCUMENTING", "GOVERNED", "CERTIFYING",
                     "CERTIFIED", "COMPLETED", "DELIVERED"
                 }
                 if current_status in locked_statuses:
                     raise ValueError(f"Project is in {current_status} mode. Asset Inventory is locked. Unlock Triage first.")
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
                "target_name": asset.get("target_name"),
                # Sprint 14: File classification
                "category": asset.get("category")  # migrable, soporte, documentacion, no_reconocido
            })
            # [v3.9] Only tenant_id for isolation (object ownership tracked via project)
            if self.tenant_id: 
                insert_data[-1]["tenant_id"] = self.tenant_id
            
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

    async def get_asset_by_id(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single asset by its object_id."""
        try:
            res = self.client.table("utm_objects").select("*").eq("object_id", asset_id).execute()
            if res.data and len(res.data) > 0:
                asset = res.data[0]
                # Add compatibility fields
                asset["id"] = asset["object_id"]
                asset["filename"] = asset["source_name"]
                asset["name"] = asset["source_name"]
                return asset
            return None
        except Exception as e:
            print(f"Error fetching asset {asset_id}: {e}")
            return None

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

            # 5. Reset stage to 0 and status to DISCOVERY
            self.client.table("utm_projects").update({
                "stage": "0",
                "status": "DISCOVERY",
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
        if status in {"TRIAGE_APPROVED", "DRAFTING"}:
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

    # [Sprint 2] Post-Drafting Mode Branching
    async def set_post_drafting_mode(self, project_id: str, mode: str) -> bool:
        """
        Sets the post-Drafting mode for a project.
        Valid modes: 'drafting_delivery', 'structured_refinement', 'intelligent_reengineering'
        """
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            return False
        
        valid_modes = {'drafting_delivery', 'structured_refinement', 'intelligent_reengineering'}
        if mode not in valid_modes:
            print(f"Invalid post_drafting_mode: {mode}. Must be one of: {valid_modes}")
            return False
        
        try:
            from datetime import datetime, timezone
            now_iso = datetime.now(timezone.utc).isoformat()
            self.client.table("utm_projects").update({
                "post_drafting_mode": mode,
                "post_drafting_mode_set_at": now_iso
            }).eq("project_id", resolved_id).execute()
            return True
        except Exception as e:
            print(f"Error setting post_drafting_mode for {project_id}: {e}")
            return False

    async def get_post_drafting_mode(self, project_id: str) -> Optional[str]:
        """Retrieves the post-Drafting mode for a project."""
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            return None
        
        try:
            res = self.client.table("utm_projects").select("post_drafting_mode").eq("project_id", resolved_id).execute()
            if res.data:
                return res.data[0].get("post_drafting_mode")
            return None
        except Exception as e:
            print(f"Error getting post_drafting_mode for {project_id}: {e}")
            return None

    async def clear_post_drafting_mode(self, project_id: str) -> bool:
        """Clears the persisted post-Drafting decision so a new Drafting run can ask again."""
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id:
            return False

        try:
            self.client.table("utm_projects").update({
                "post_drafting_mode": None,
                "post_drafting_mode_set_at": None,
            }).eq("project_id", resolved_id).execute()
            return True
        except Exception as e:
            print(f"Error clearing post_drafting_mode for {project_id}: {e}")
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

    async def initialize_design_registry(self, project_id: str, target_tech: str = None) -> bool:
        """Seeds default design standards for a new project."""
        from apps.api.services.knowledge_service import KnowledgeService
        # If target_tech not explicitly provided, read from project settings so the
        # auto-initialized target_stack matches the project's chosen destination.
        if not target_tech:
            try:
                settings = await self.get_project_settings(project_id) or {}
                target_tech = settings.get("target_tech")
            except Exception:
                pass
        defaults = KnowledgeService.get_default_registry_entries(project_id, target_tech=target_tech)
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
        v4.0: Fetching prompt content from DB (GLOBAL prompts only - no tenant_id).
        Prompts are now global across all tenants (v4.0 design decision).
        Falls back to local file with auto-seed if not found in DB.
        """
        try:
            print(f"DEBUG: Fetching prompt '{prompt_id}' from DB (v4.0 Global Prompts)...")
            
            # v4.0: Simple query - no tenant filtering (prompts are global)
            query = self.client.table("utm_prompts").select("content")
            query = query.eq("prompt_id", prompt_id)
            query = query.eq("is_active", True)
                
            res = query.execute()
            
            if res.data and res.data[0].get("content"):
                print(f"DEBUG: ✅ Loaded prompt '{prompt_id}' from DB (Global, {len(res.data[0]['content'])} chars)")
                return res.data[0]["content"]
            
            # Fallback to local file with auto-seed
            print(f"DEBUG: Prompt '{prompt_id}' not found in DB. Attempting auto-seed from local file...")
            return await self._auto_seed_prompt_canonical(prompt_id)
                
        except Exception as e:
            print(f"DEBUG: ❌ Error fetching prompt {prompt_id}: {e}")
            import traceback
            traceback.print_exc()
        return ""

    async def _auto_seed_prompt(self, prompt_id: str) -> str:
        """
        v4.0: Seed a prompt from local markdown file to DB as global prompt.
        No tenant_id - all prompts are global.
        """
        try:
            canonical_spec = get_prompt_spec(prompt_id)
            if canonical_spec:
                content = canonical_spec.read_text()
                data = {
                    "prompt_id": prompt_id,
                    "content": content,
                    "agent_id": canonical_spec.agent_id,
                    "tech_stack": canonical_spec.tech_stack,
                    "pattern_type": canonical_spec.pattern_type,
                    "is_active": True,
                    "metadata": {
                        "auto_seeded": True,
                        "source_file": canonical_spec.relative_source,
                        "category": canonical_spec.category,
                        "seeded_at": datetime.now().isoformat()
                    }
                }
                self.client.table("utm_prompts").insert(data).execute()
                print(f"DEBUG: Successfully auto-seeded '{prompt_id}' from canonical source ({len(content)} chars)")
                return content

            print(f"DEBUG: Prompt source not found for {prompt_id}")
            return ""
            
            if not spec:
                print(f"DEBUG: ❌ Local prompt file not found at {file_path}")
                return ""
                
            content = spec.read_text()
                
            # v4.0: Seed to DB (GLOBAL - no tenant_id)
            data = {
                "prompt_id": prompt_id,
                "content": content,
                "is_active": True,
                "metadata": {
                    "auto_seeded": True,
                    "source_file": f"{prompt_id}.md",
                    "seeded_at": datetime.now().isoformat()
                }
            }
            
            self.client.table("utm_prompts").insert(data).execute()
            print(f"DEBUG: ✅ Successfully auto-seeded '{prompt_id}' to DB ({len(content)} chars)")
            return content
            
        except Exception as e:
            print(f"DEBUG: ❌ Error auto-seeding prompt {prompt_id}: {e}")
            import traceback
            traceback.print_exc()
            return ""

    async def _auto_seed_prompt_canonical(self, prompt_id: str) -> str:
        """
        Canonical prompt auto-seed path for v4.0 prompts managed from disk.
        """
        try:
            canonical_spec = get_prompt_spec(prompt_id)
            if not canonical_spec:
                print(f"DEBUG: Prompt source not found for {prompt_id}")
                return ""

            content = canonical_spec.read_text()
            data = {
                "prompt_id": prompt_id,
                "content": content,
                "agent_id": canonical_spec.agent_id,
                "tech_stack": canonical_spec.tech_stack,
                "pattern_type": canonical_spec.pattern_type,
                "is_active": True,
                "metadata": {
                    "auto_seeded": True,
                    "source_file": canonical_spec.relative_source,
                    "category": canonical_spec.category,
                    "seeded_at": datetime.now().isoformat()
                }
            }
            self.client.table("utm_prompts").insert(data).execute()
            print(f"DEBUG: Successfully auto-seeded '{prompt_id}' from canonical source ({len(content)} chars)")
            return content
        except Exception as e:
            print(f"DEBUG: Canonical auto-seed error for prompt {prompt_id}: {e}")
            import traceback
            traceback.print_exc()
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

    async def save_prompt(
        self, 
        prompt_id: str, 
        content: str,
        agent_id: Optional[str] = None,
        tech_stack: Optional[str] = None,
        pattern_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save or update a prompt in the database (v4.0).
        Prompts are GLOBAL (no tenant_id).
        Trigger automatically saves old version to utm_prompts_history on UPDATE.
        
        Args:
            prompt_id: Unique prompt identifier
            content: Full prompt content
            agent_id: Agent identifier (e.g., 'agent-c')
            tech_stack: Technology stack (e.g., 'databricks')
            pattern_type: Pattern type (e.g., 'direct', 'bronze')
            metadata: Additional metadata
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"DEBUG: Saving prompt '{prompt_id}' length={len(content)}")
            
            # Check if prompt exists (NO tenant filter - prompts are global)
            query = self.client.table("utm_prompts").select("prompt_id").eq("prompt_id", prompt_id)
            res = query.execute()
            
            # Prepare data
            data = {
                "content": content,
                "agent_id": agent_id,
                "tech_stack": tech_stack,
                "pattern_type": pattern_type,
                "metadata": metadata or {},
                "is_active": True
            }
            
            if res.data:
                # Update existing prompt (trigger will save old version to history)
                self.client.table("utm_prompts").update(data).eq("prompt_id", prompt_id).execute()
                print(f"DEBUG: Updated prompt '{prompt_id}'")
            else:
                # Insert new prompt
                data["prompt_id"] = prompt_id
                self.client.table("utm_prompts").insert(data).execute()
                print(f"DEBUG: Inserted new prompt '{prompt_id}'")
            
            return True
        except Exception as e:
            print(f"Error saving prompt {prompt_id}: {e}")
            import traceback
            traceback.print_exc()
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
                 print(f"[log_execution] ERROR: Could not resolve project_id '{project_id}' for log_execution")
                 return

            data = {
                "project_id": resolved_id,
                "phase": phase,
                "step": step or phase,
                "message": message,
                "level": level
            }
            print(f"[log_execution] Writing to DB: project={resolved_id}, phase={phase}, step={step}, message={message[:50]}...")
            result = self.client.table("utm_execution_logs").insert(data).execute()
            print(f"[log_execution] Successfully inserted log entry (count: {len(result.data) if result.data else 0})")
        except Exception as e:
            print(f"[log_execution] ERROR logging to DB: {e}")
            import traceback
            traceback.print_exc()

    async def get_execution_logs(self, project_id: str, phase: str = None) -> List[Dict[str, Any]]:
        """Retrieves execution logs for a project, optionally filtered by phase."""
        try:
            resolved_id = await self._resolve_uuid(project_id)
            if not resolved_id:
                print(f"[get_execution_logs] ERROR: Could not resolve project_id '{project_id}' for get_execution_logs")
                return []

            print(f"[get_execution_logs] Querying logs: project={resolved_id}, phase={phase}")
            query = self.client.table("utm_execution_logs").select("*").eq("project_id", resolved_id)
            if phase:
                query = query.eq("phase", phase)
            
            # Sort by creation time to ensure chronological order
            res = query.order("created_at", desc=False).execute()
            log_count = len(res.data) if res.data else 0
            print(f"[get_execution_logs] Retrieved {log_count} log entries for project={resolved_id}, phase={phase}")
            return res.data if res.data else []
        except Exception as e:
            print(f"[get_execution_logs] ERROR fetching execution logs: {e}")
            import traceback
            traceback.print_exc()
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
        Synchronizes the database file inventory with the physical storage (R2/S3/Local).
        Replaced os.walk with StorageProvider.list_files (v3.5 Cloud Native).
        [Robustness] Tries both project UUID and project Name for the folder path.
        """
        resolved_uuid = await self._resolve_uuid(project_id)
        if not resolved_uuid:
            return False

        tenant_id = self.tenant_id
        storage = PersistenceService.get_storage()
        
        # 1. Resolve folder candidates: UUID and Name
        folder_candidates = [resolved_uuid]
        
        project_name = await self.get_project_name_by_id(resolved_uuid)
        if project_name and project_name != resolved_uuid:
            folder_candidates.append(project_name)

        files_tree = []
        chosen_dir = None
        
        try:
            for folder_name in folder_candidates:
                project_dir = PersistenceService.ensure_solution_dir(folder_name, tenant_id)
                print(f"DEBUG: Trying sync in: {project_dir}")
                
                # List files from storage (recursively)
                candidate_tree = storage.list_files(project_dir, recursive=True)
                
                # Check if we found anything (simple length check on children of root if root is returned, 
                # or if candidate_tree itself has items)
                # list_files returns a list of nodes.
                if candidate_tree:
                    # Filter out the root folder if it's the only item
                    has_content = False
                    for node in candidate_tree:
                        # If node path is not exactly project_dir, or if it has children
                        if node["path"].rstrip('/') != project_dir.rstrip('/') or node.get("children"):
                            has_content = True
                            break
                    
                    if has_content:
                        files_tree = candidate_tree
                        chosen_dir = project_dir
                        print(f"DEBUG: Found files in {project_dir}")
                        break
            
            if not chosen_dir:
                # Default to normalized UUID if nothing found, so we clear older inventory correctly
                chosen_dir = PersistenceService.ensure_solution_dir(resolved_uuid, tenant_id)
                print(f"DEBUG: No files found in any candidate folder for project {project_id}")

            inventory_data = []

            # 2. Flatten tree and prepare batch data
            def _extract_items(nodes):
                for node in nodes:
                    full_key = node["path"]
                    # Relativize path for display (remove chosen_dir prefix)
                    rel_path = full_key[len(chosen_dir):].lstrip('/')
                    
                    if not rel_path: # Skip root folder item itself
                        if node.get("children"):
                            _extract_items(node["children"])
                        continue

                    is_folder = (node["type"] == "folder")
                    
                    inventory_data.append({
                        "project_id": resolved_uuid,
                        "file_path": rel_path,
                        "is_directory": is_folder,
                        "size_bytes": node.get("size", 0),
                        "last_modified": datetime.now().isoformat()
                    })
                    
                    if is_folder and node.get("children"):
                        _extract_items(node["children"])

            _extract_items(files_tree)

            if not inventory_data:
                print(f"DEBUG: No files found in any candidate folder for project {project_id}")
                # Still clear old inventory if no files found
                self.client.table("utm_file_inventory").delete().eq("project_id", resolved_uuid).execute()
                return True

            # 3. Clean existing and batch sync
            self.client.table("utm_file_inventory").delete().eq("project_id", resolved_uuid).execute()
            
            # Batch insert
            try:
                self.client.table("utm_file_inventory").insert(inventory_data).execute()
            except Exception as ex:
                print(f"Batch insert failed, retrying in chunks: {ex}")
                chunk_size = 100
                for i in range(0, len(inventory_data), chunk_size):
                    chunk = inventory_data[i:i + chunk_size]
                    self.client.table("utm_file_inventory").insert(chunk).execute()
            
            print(f"DEBUG: Successfully synced {len(inventory_data)} items to utm_file_inventory")
            return True

        except Exception as e:
            print(f"Error syncing file inventory: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def get_project_files_from_db(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieves and builds the file tree from DB."""
        resolved_uuid = await self._resolve_uuid(project_id)
        if not resolved_uuid:
            return []

        try:
            res = self.client.table("utm_file_inventory").select("*").eq("project_id", resolved_uuid).execute()
            rows = res.data if res.data else []
            
            if not rows and "-" not in project_id:
                 # Lazy sync if name provided and empty
                 await self.sync_file_inventory(project_id)
                 res = self.client.table("utm_file_inventory").select("*").eq("project_id", resolved_uuid).execute()
                 rows = res.data if res.data else []

            # Aligned with WorkspacePage.tsx tree expectations
            return self._build_tree(rows)
        except Exception as e:
            print(f"Error fetching inventory from DB: {e}")
            return []

    def _build_tree(self, inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Converts flat inventory list to nested tree structure."""
        import os
        nodes_by_path = {}
        
        # 1. Create node objects
        for item in inventory:
            path = item["file_path"]
            name = os.path.basename(path)
            node = {
                "name": name,
                "path": path, 
                "type": "folder" if item["is_directory"] else "file",
                "size": item.get("size_bytes", 0),
                "children": [] if item["is_directory"] else None,
                "last_modified": item.get("last_modified")
            }
            nodes_by_path[path] = node

        # 2. Nest them
        root_nodes = []
        sorted_paths = sorted(nodes_by_path.keys())
        
        for path in sorted_paths:
            node = nodes_by_path[path]
            parent_path = os.path.dirname(path).replace("\\", "/")
            
            if parent_path and parent_path != "." and parent_path != "" and parent_path in nodes_by_path:
                nodes_by_path[parent_path]["children"].append(node)
            else:
                root_nodes.append(node)

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

    # --- Sidebar Metrics Helper Methods ---

    async def get_quality_metrics_summary(self, project_id: str) -> Dict[str, Any]:
        """
        Aggregates quality metrics from utm_asset_columns for sidebar display.
        Returns avg quality score, PII count, partitioned table count, etc.
        """
        try:
            resolved_id = await self._resolve_uuid(project_id)
            if not resolved_id:
                return {}
            
            # Get all profiled columns with quality metrics (utm_asset_columns from Sprint 7)
            res = self.client.table("utm_asset_columns").select("*").eq("project_id", resolved_id).execute()
            columns = res.data if res.data else []
            
            if not columns:
                return {"avg_quality_score": 0, "pii_column_count": 0, "partitioned_table_count": 0}
            
            # Calculate averages
            quality_scores = [col.get("quality_score", 0) for col in columns if col.get("quality_score")]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # Count PII columns
            pii_count = sum(1 for col in columns if col.get("has_pii", False))
            
            # Count unique tables with partitioning
            partitioned_tables = set()
            for col in columns:
                if col.get("partition_key") or col.get("is_partition_key"):
                    asset_id = col.get("asset_id")
                    if asset_id:
                        partitioned_tables.add(asset_id)
            
            return {
                "avg_quality_score": round(avg_quality, 1),
                "pii_column_count": pii_count,
                "partitioned_table_count": len(partitioned_tables),
                "total_columns": len(columns)
            }
        except Exception as e:
            print(f"Error getting quality metrics summary: {e}")
            return {}

    async def get_project_tech_stats(self, project_id: str) -> Dict[str, Any]:
        """
        Returns aggregated technology statistics for a project.
        Includes source_tech detection, target_tech, asset counts per tech.
        """
        try:
            resolved_id = await self._resolve_uuid(project_id)
            if not resolved_id:
                return {}
            
            # Get all assets (only source_tech, target is at project level)
            res = self.client.table("utm_objects").select("source_tech").eq("project_id", resolved_id).execute()
            assets = res.data if res.data else []
            
            if not assets:
                return {"source_tech": "Unknown", "target_tech": "Unknown", "asset_count": 0}
            
            # Count source techs (most common)
            source_techs = [a.get("source_tech") for a in assets if a.get("source_tech")]
            most_common_source = max(set(source_techs), key=source_techs.count) if source_techs else "Unknown"
            
            # Get target tech from project metadata
            project = await self.get_project_metadata(project_id)
            target_tech = project.get("target_technology", "Unknown") if project else "Unknown"
            
            return {
                "source_tech": most_common_source,
                "target_tech": target_tech,
                "asset_count": len(assets),
                "source_tech_breakdown": {tech: source_techs.count(tech) for tech in set(source_techs)}
            }
        except Exception as e:
            print(f"Error getting project tech stats: {e}")
            return {}

    async def get_code_validations(self, project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves code validations from utm_code_validations table.
        Returns validation results with is_valid, error_count, etc.
        """
        try:
            resolved_id = await self._resolve_uuid(project_id)
            if not resolved_id:
                return []
            
            res = self.client.table("utm_code_validations").select("*").eq("project_id", resolved_id).order("created_at", desc=True).limit(limit).execute()
            return res.data if res.data else []
        except Exception as e:
            err = str(e)
            # Supabase PostgREST: table missing in schema cache.
            # Treat as feature-not-enabled and keep UI responsive.
            if "PGRST205" in err or "utm_code_validations" in err and "schema cache" in err:
                print("[get_code_validations] utm_code_validations not available yet; returning empty validations")
                return []
            print(f"Error getting code validations: {e}")
            return []

    async def get_governance_files(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves governance documentation files generated by Agent G.
        Looks for files in solution_context with category='documentation' or similar.
        """
        try:
            resolved_id = await self._resolve_uuid(project_id)
            if not resolved_id:
                return []
            
            # Check utm_solution_context for documentation entries
            res = self.client.table("utm_solution_context").select("*").eq("project_id", resolved_id).ilike("context_type", "%documentation%").execute()
            docs = res.data if res.data else []
            
            # Also check design registry for governance category
            res2 = self.client.table("utm_design_registry").select("*").eq("project_id", resolved_id).eq("category", "governance").execute()
            gov_nodes = res2.data if res2.data else []
            
            return docs + gov_nodes
        except Exception as e:
            print(f"Error getting governance files: {e}")
            return []

    # --- V5 Knowledge Model Persistence Methods ---
    
    async def save_evidence_items(self, project_id: str, items: List['EvidenceItem'], asset_id: Optional[str] = None, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Saves a batch of tech-agnostic evidence items to utm_evidence_items."""
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id or not items:
            return []
            
        insert_data = []
        for item in items:
            row = {
                "project_id": resolved_id,
                "asset_id": asset_id,
                "source_path": item.source_path,
                "source_block_type": item.source_block_type,
                "snippet": item.snippet,
                "line_start": item.line_start,
                "line_end": item.line_end,
                "parser_name": item.parser_name,
                "extraction_method": item.extraction_method,
                "confidence": item.confidence,
                "rationale": item.rationale,
                "run_id": run_id
            }
            if self.tenant_id:
                row["tenant_id"] = self.tenant_id
            insert_data.append(row)
            
        try:
            res = self.client.table("utm_evidence_items").insert(insert_data).execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error saving evidence items: {e}")
            return []

    async def save_processes_and_steps(self, project_id: str, processes: List['ProcessHint'], asset_id: Optional[str] = None, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Saves processes, their orchestration steps, and operational constraints."""
        resolved_id = await self._resolve_uuid(project_id)
        if not resolved_id or not processes:
            return []
            
        saved_processes = []
        try:
            for proc in processes:
                # 1. Save Process
                proc_data = {
                    "project_id": resolved_id,
                    "asset_id": asset_id,
                    "name": proc.name,
                    "process_type": proc.process_type,
                    "extraction_method": proc.extraction_method,
                    "confidence": proc.confidence,
                    "run_id": run_id
                }
                if self.tenant_id:
                    proc_data["tenant_id"] = self.tenant_id
                    
                p_res = self.client.table("utm_processes").insert(proc_data).execute()
                if not p_res.data:
                    continue
                    
                process_id = p_res.data[0]["process_id"]
                saved_processes.append(p_res.data[0])
                
                # 2. Save Orchestration Steps
                if proc.orchestration_steps:
                    step_data = []
                    for step in proc.orchestration_steps:
                        s_row = {
                            "process_id": process_id,
                            "project_id": resolved_id,
                            "name": step.name,
                            "step_type": step.step_type,
                            "order_hint": step.order_hint,
                            "branching_hint": step.branching_hint,
                            "extraction_method": step.extraction_method,
                            "confidence": step.confidence,
                            "run_id": run_id
                        }
                        if self.tenant_id:
                            s_row["tenant_id"] = self.tenant_id
                        step_data.append(s_row)
                    self.client.table("utm_orchestration_steps").insert(step_data).execute()
                    
                # 3. Save Operational Constraints
                if proc.operational_constraints:
                    constraint_data = []
                    for const in proc.operational_constraints:
                        c_row = {
                            "process_id": process_id,
                            "project_id": resolved_id,
                            "constraint_type": const.constraint_type,
                            "value_hint": const.value_hint,
                            "severity": const.severity,
                            "extraction_method": const.extraction_method,
                            "confidence": const.confidence,
                            "run_id": run_id
                        }
                        if self.tenant_id:
                            c_row["tenant_id"] = self.tenant_id
                        constraint_data.append(c_row)
                    self.client.table("utm_operational_constraints").insert(constraint_data).execute()
                    
            return saved_processes
        except Exception as e:
            print(f"Error saving processes and steps: {e}")
            return []
