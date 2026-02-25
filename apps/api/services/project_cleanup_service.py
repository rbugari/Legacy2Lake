"""
Project Cleanup Service - Sprint 14
====================================

Purpose:
    Provides project reset/cleanup functionality to:
    1. Remove generated artifacts (code, diagrams, logs)
    2. Preserve original uploaded files (triage folder)
    3. Optionally ZIP generated files before deletion
    4. Reset project stage to Discovery

Features:
    - Smart cleanup (keeps originals, removes generated)
    - ZIP backup option
    - Database state reset
    - Multi-tenant safe

Usage:
    cleanup_service = ProjectCleanupService(tenant_id, project_id)
    
    # Soft reset (ZIP + delete generated)
    result = await cleanup_service.reset_project(backup=True)
    
    # Hard reset (delete all generated, no backup)
    result = await cleanup_service.reset_project(backup=False)
    
    # Clean specific stage
    result = await cleanup_service.clean_stage("drafting")

Author: Legacy2Lake Engineering
Date: 2026-02-16 (Sprint 14)
"""

import os
import json
import zipfile
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Multi-context imports
try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence, PersistenceService
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence, PersistenceService
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence, PersistenceService


class ProjectCleanupService:
    """Service for cleaning/resetting project artifacts."""
    
    # Stages que contienen archivos generados
    GENERATED_STAGES = ["drafting", "refinement", "certification", "handover"]
    
    # Stages que contienen archivos originales (NO tocar)
    ORIGINAL_STAGES = ["triage"]
    
    def __init__(self, tenant_id: Optional[str] = None, project_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.project_id = project_id
        self.db = SupabasePersistence(tenant_id=tenant_id)
        self.storage = PersistenceService.get_storage()
    
    async def reset_project(self, backup: bool = True) -> Dict[str, Any]:
        """
        Reset project to initial state (after upload).
        
        Args:
            backup: If True, ZIP generated files before deletion
        
        Returns:
            Dict with cleanup results and backup location
        """
        logger.info(f"[Cleanup] Starting project reset: project_id={self.project_id}, backup={backup}", "Cleanup")
        
        # Resolve project name
        project_name = await self._resolve_project_name()
        if not project_name:
            raise ValueError(f"Project not found: {self.project_id}")
        
        base_path = PersistenceService.ensure_solution_dir(project_name, self.tenant_id)
        
        result = {
            "project_id": self.project_id,
            "project_name": project_name,
            "backup_created": False,
            "backup_path": None,
            "stages_cleaned": [],
            "files_removed": 0,
            "database_reset": False,
            "errors": []
        }
        
        try:
            # Step 1: Create backup ZIP if requested
            if backup:
                backup_info = await self._create_backup(base_path, project_name)
                result["backup_created"] = backup_info["success"]
                result["backup_path"] = backup_info.get("backup_path")
                if not backup_info["success"]:
                    result["errors"].append(f"Backup failed: {backup_info.get('error')}")
            
            # Step 2: Clean generated stages
            for stage in self.GENERATED_STAGES:
                stage_result = await self._clean_stage(base_path, stage)
                if stage_result["success"]:
                    result["stages_cleaned"].append(stage)
                    result["files_removed"] += stage_result["files_removed"]
                else:
                    result["errors"].append(f"Stage {stage}: {stage_result.get('error')}")
            
            # Step 3: Reset database state
            db_result = await self._reset_database_state()
            result["database_reset"] = db_result["success"]
            if not db_result["success"]:
                result["errors"].append(f"Database reset failed: {db_result.get('error')}")
            
            logger.info(
                f"[Cleanup] Project reset complete: stages={len(result['stages_cleaned'])}, "
                f"files={result['files_removed']}, backup={result['backup_created']}", 
                "Cleanup"
            )
            
        except Exception as e:
            logger.error(f"[Cleanup] Project reset failed: {e}", "Cleanup")
            result["errors"].append(str(e))
        
        return result
    
    async def clean_stage(self, stage: str) -> Dict[str, Any]:
        """
        Clean specific stage folder.
        
        Args:
            stage: Stage name (drafting, refinement, certification, handover)
        
        Returns:
            Dict with cleanup results
        """
        if stage not in self.GENERATED_STAGES:
            return {
                "success": False,
                "error": f"Invalid stage: {stage}. Must be one of {self.GENERATED_STAGES}"
            }
        
        project_name = await self._resolve_project_name()
        base_path = PersistenceService.ensure_solution_dir(project_name, self.tenant_id)
        
        return await self._clean_stage(base_path, stage)
    
    async def _create_backup(self, base_path: str, project_name: str) -> Dict[str, Any]:
        """Create ZIP backup of generated files."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{project_name}_backup_{timestamp}.zip"
            backup_key = f"{base_path.rstrip('/')}/{backup_filename}"
            
            logger.info(f"[Cleanup] Creating backup ZIP: {backup_filename}", "Cleanup")
            
            # Crear ZIP en memoria
            import io
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for stage in self.GENERATED_STAGES:
                    stage_path = f"{base_path.rstrip('/')}/{stage}"
                    
                    try:
                        # List all files in stage
                        items = self.storage.list_files(stage_path, recursive=True)
                        files = self._flatten_files(items)
                        
                        for file_info in files:
                            file_key = file_info["path"]
                            relative_path = file_key.replace(f"{base_path.rstrip('/')}/", "")
                            
                            try:
                                content = self.storage.read_file(file_key)
                                zipf.writestr(relative_path, content)
                            except Exception as e:
                                logger.warning(f"[Cleanup] Skipped file in backup: {file_key}, error: {e}", "Cleanup")
                    
                    except Exception as e:
                        logger.warning(f"[Cleanup] Stage {stage} not found or empty: {e}", "Cleanup")
            
            # Save ZIP to storage
            zip_buffer.seek(0)
            self.storage.save_file(backup_key, zip_buffer.read())
            
            logger.info(f"[Cleanup] Backup created successfully: {backup_key}", "Cleanup")
            
            return {
                "success": True,
                "backup_path": backup_key,
                "backup_filename": backup_filename
            }
        
        except Exception as e:
            logger.error(f"[Cleanup] Backup creation failed: {e}", "Cleanup")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _clean_stage(self, base_path: str, stage: str) -> Dict[str, Any]:
        """Clean all files in a stage folder."""
        try:
            stage_path = f"{base_path.rstrip('/')}/{stage}"
            logger.info(f"[Cleanup] Cleaning stage: {stage}", "Cleanup")
            
            # List all files in stage
            items = self.storage.list_files(stage_path, recursive=True)
            files = self._flatten_files(items)
            
            files_removed = 0
            for file_info in files:
                try:
                    self.storage.delete_file(file_info["path"])
                    files_removed += 1
                except Exception as e:
                    logger.warning(f"[Cleanup] Failed to delete file: {file_info['path']}, error: {e}", "Cleanup")
            
            logger.info(f"[Cleanup] Stage {stage} cleaned: {files_removed} files removed", "Cleanup")
            
            return {
                "success": True,
                "stage": stage,
                "files_removed": files_removed
            }
        
        except Exception as e:
            logger.error(f"[Cleanup] Failed to clean stage {stage}: {e}", "Cleanup")
            return {
                "success": False,
                "stage": stage,
                "error": str(e),
                "files_removed": 0
            }
    
    async def _reset_database_state(self) -> Dict[str, Any]:
        """
        Reset project database state to initial (post-upload).
        
        Cleans:
        - Dependent tables (utm_logical_steps, utm_transformations, utm_asset_context)
        - Execution logs and file inventory
        - ALL utm_objects (detected assets deleted completely)
        - Design registry
        - Resets project stage to 0 (DISCOVERY)
        
        NOTE: This is a HARD reset - all detected assets are deleted.
        TODO v4.1: Add 'preserve_metadata' parameter for soft reset (only clear generated fields)
        """
        try:
            # Get object_ids for dependent table cleanup
            obj_res = self.db.client.table("utm_objects").select("object_id").eq("project_id", self.project_id).execute()
            object_ids = [o["object_id"] for o in obj_res.data]
            
            if object_ids:
                # Delete dependent tables (satisfy foreign keys)
                try:
                    self.db.client.table("utm_logical_steps").delete().in_("object_id", object_ids).execute()
                except Exception as e:
                    logger.warning(f"[Cleanup] Could not delete utm_logical_steps: {e}", "Cleanup")
                
                try:
                    self.db.client.table("utm_transformations").delete().in_("asset_id", object_ids).execute()
                except Exception as e:
                    logger.warning(f"[Cleanup] Could not delete utm_transformations: {e}", "Cleanup")
            
            # Clean per-asset context overrides
            try:
                self.db.client.table("utm_asset_context").delete().eq("project_id", self.project_id).execute()
            except Exception as e:
                logger.warning(f"[Cleanup] Could not delete utm_asset_context: {e}", "Cleanup")
            
            # DELETE all utm_objects (hard reset - removes all detected assets)
            # This is the original behavior - user must re-run Triage to detect assets again
            self.db.client.table("utm_objects").delete().eq("project_id", self.project_id).execute()
            
            # Delete execution logs
            try:
                self.db.client.table("utm_execution_logs").delete().eq("project_id", self.project_id).execute()
            except Exception as e:
                logger.warning(f"[Cleanup] Could not delete utm_execution_logs: {e}", "Cleanup")
            
            # Delete file inventory
            try:
                self.db.client.table("utm_file_inventory").delete().eq("project_id", self.project_id).execute()
            except Exception as e:
                logger.warning(f"[Cleanup] Could not delete utm_file_inventory: {e}", "Cleanup")
            
            # Delete design registry nodes
            try:
                self.db.client.table("utm_design_registry").delete().eq("project_id", self.project_id).execute()
            except Exception as e:
                logger.warning(f"[Cleanup] Could not delete utm_design_registry: {e}", "Cleanup")
            
            # Reset project stage to 0 (DISCOVERY) and status
            self.db.client.table("utm_projects").update({
                "stage": "0",
                "status": "DISCOVERY",
                "triage_approved_at": None
            }).eq("project_id", self.project_id).execute()
            
            logger.info(f"[Cleanup] Database state reset complete: project_id={self.project_id}", "Cleanup")
            
            return {"success": True}
        
        except Exception as e:
            logger.error(f"[Cleanup] Database reset failed: {e}", "Cleanup")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _resolve_project_name(self) -> Optional[str]:
        """Resolve project name from project_id."""
        try:
            result = self.db.client.table("utm_projects").select("name").eq("project_id", self.project_id).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]["name"]
            return None
        except Exception as e:
            logger.error(f"[Cleanup] Failed to resolve project name: {e}", "Cleanup")
            return None
    
    def _flatten_files(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Flatten recursive file tree."""
        files = []
        for node in nodes:
            if node["type"] == "folder" and node.get("children"):
                files.extend(self._flatten_files(node["children"]))
            elif node["type"] == "file":
                files.append(node)
        return files
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all backup ZIP files for this project.
        
        Returns:
            List of backup info dicts with: filename, size, created_at, path
        """
        try:
            project_name = await self._resolve_project_name()
            if not project_name:
                return []
            
            base_path = PersistenceService.ensure_solution_dir(project_name, self.tenant_id)
            
            # List all files in project root
            items = self.storage.list_files(base_path, recursive=False)
            
            # Filter only backup ZIP files
            backups = []
            for item in items:
                if item["type"] == "file" and "_backup_" in item["name"] and item["name"].endswith(".zip"):
                    # Extract timestamp from filename: projectname_backup_YYYYMMDD_HHMMSS.zip
                    try:
                        parts = item["name"].replace(".zip", "").split("_backup_")
                        if len(parts) == 2:
                            timestamp_str = parts[1]  # YYYYMMDD_HHMMSS
                            # Parse timestamp
                            created_at = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S").isoformat()
                        else:
                            created_at = None
                    except:
                        created_at = None
                    
                    backups.append({
                        "filename": item["name"],
                        "size": item.get("size", 0),
                        "size_mb": round(item.get("size", 0) / (1024 * 1024), 2) if item.get("size") else 0,
                        "created_at": created_at,
                        "path": item["path"]
                    })
            
            # Sort by created_at descending (newest first)
            backups.sort(key=lambda x: x["created_at"] or "", reverse=True)
            
            logger.info(f"[Cleanup] Listed {len(backups)} backups for project {self.project_id}", "Cleanup")
            return backups
        
        except Exception as e:
            logger.error(f"[Cleanup] Failed to list backups: {e}", "Cleanup")
            return []
    
    async def delete_backup(self, backup_filename: str) -> Dict[str, Any]:
        """
        Delete a specific backup ZIP file.
        
        Args:
            backup_filename: Name of the backup file to delete
        
        Returns:
            Dict with success status
        """
        try:
            project_name = await self._resolve_project_name()
            if not project_name:
                return {"success": False, "error": "Project not found"}
            
            base_path = PersistenceService.ensure_solution_dir(project_name, self.tenant_id)
            backup_path = f"{base_path.rstrip('/')}/{backup_filename}"
            
            # Verify file exists
            if not self.storage.exists(backup_path):
                return {"success": False, "error": f"Backup file not found: {backup_filename}"}
            
            # Delete the file
            self.storage.delete_file(backup_path)
            
            logger.info(f"[Cleanup] Deleted backup: {backup_filename}", "Cleanup")
            return {"success": True}
        
        except Exception as e:
            logger.error(f"[Cleanup] Failed to delete backup {backup_filename}: {e}", "Cleanup")
            return {"success": False, "error": str(e)}
