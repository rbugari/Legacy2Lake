import os
from supabase import create_client, Client
from typing import List, Dict, Any
from apps.utm.core.interfaces import MetadataObject, LogicalStep
from dotenv import load_dotenv

load_dotenv()

class UTMPersistence:
    """
    Handles persistence of UTM artifacts to Supabase.
    """
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        # Prefer Service Role Key for backend ops, fallback to Anon if needed
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            print("[WARN] Supabase credentials not found. Persistence disabled.")
            self.client = None
        else:
            self.client: Client = create_client(url, key)

    def get_or_create_project(self, name: str) -> str:
        """Gets existing project ID or creates a new one."""
        if not self.client: return "mock_project_id"

        try:
            # Check existing
            res = self.client.table("utm_projects").select("project_id").eq("name", name).execute()
            if res.data:
                return res.data[0]["project_id"]
            
            # Create new
            res = self.client.table("utm_projects").insert({
                "name": name,
                "description": "Auto-created by UTM Pipeline"
            }).execute()
            
            if res.data:
                return res.data[0]["project_id"]
        except Exception as e:
            print(f"[WARN] Supabase Persistence Failed: {e}")
            self.client = None # Disable for subsequent calls
            return "mock_project_id_fallback"
            
        return "error_project_id"

    def save_object(self, project_id: str, metadata: MetadataObject) -> str:
        """Saves the ingested metadata to UTM_Object."""
        if not self.client: return "mock_object_id"
        
        try:
            payload = {
                "project_id": project_id,
                "source_name": metadata.source_name,
                "source_tech": metadata.source_tech,
                "raw_content": metadata.raw_content
            }
            
            res = self.client.table("utm_objects").insert(payload).execute()
            if res.data:
                return res.data[0]["object_id"]
        except Exception as e:
            print(f"[WARN] Failed to save object: {e}")
            
        return "mock_object_id_fallback"

    def save_logical_steps(self, object_id: str, steps: List[LogicalStep]):
        """Saves the normalized IR steps to UTM_Logical_Step."""
        if not self.client: return
        
        try:
            rows = []
            for step in steps:
                rows.append({
                    "object_id": object_id,
                    "step_order": step.step_order,
                    "step_type": step.step_type,
                    "ir_payload": step.ir_payload,
                    "status": "VALIDATED"
                })
                
            if rows:
                self.client.table("utm_logical_steps").insert(rows).execute()
        except Exception as e:
            print(f"[WARN] Failed to save logical steps: {e}")
