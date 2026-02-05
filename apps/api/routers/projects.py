"""
Projects Router
Handles CRUD operations, settings, layout, and lifecycle management for projects.
Migrated from main.py for better modularity.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List
import os
import io
import zipfile

from services.persistence_service import SupabasePersistence, PersistenceService
from routers.dependencies import get_db, get_identity

router = APIRouter(prefix="/projects", tags=["Projects"])


# --- List & Get Projects ---

@router.get("")
async def list_projects(db: SupabasePersistence = Depends(get_db)):
    """Returns a list of all projects for the current tenant."""
    return await db.list_projects()


@router.get("/{project_id}")
async def get_project(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Returns project details, handling both UUID and Name."""
    # 1. Try to find by UUID or name via resolution
    metadata = await db.get_project_metadata(project_id)
    if metadata:
        if metadata.get("is_active") is False:
            raise HTTPException(status_code=403, detail="Project Access Suspended (Kill-switch Active)")
        return metadata
        
    return {"error": "Project not found"}


# --- Create & Delete Projects ---

@router.post("/create")
async def create_project(
    name: str = Form(...),
    project_id: str = Form(...),
    source_type: str = Form(...),
    github_url: str = Form(None),
    overwrite: bool = Form(False),
    file: UploadFile = File(None),
    origin: str = Form(None),
    destination: str = Form(None),
    db: SupabasePersistence = Depends(get_db)
):
    """Creates a new project and initializes it from source."""
    # 1. Register in Database (Supabase)
    # Force strict normalization for project_id and name
    normalized_id = PersistenceService.normalize_name(project_id)
    normalized_name = PersistenceService.normalize_name(name)
    
    real_id = await db.get_or_create_project(normalized_name, github_url, source_tech=origin, target_tech=destination)
    
    # Use normalized ID for further operations
    project_id = normalized_id
    name = normalized_name
    
    # 2. Handle File Upload (Save temporarily)
    temp_zip_path = None
    if source_type == "zip" and file:
        import tempfile
        # Create a temp file
        fd, temp_zip_path = tempfile.mkstemp(suffix=".zip")
        os.close(fd)
        
        with open(temp_zip_path, "wb") as buffer:
            import shutil
            shutil.copyfileobj(file.file, buffer)
            
    try:
        # 3. Initialize Directory
        success = PersistenceService.initialize_project_from_source(
            project_id=project_id,
            source_type=source_type,
            file_path=temp_zip_path,
            github_url=github_url,
            overwrite=overwrite,
            tenant_id=db.tenant_id  # Pass Tenant ID for isolation
        )
        
        if success:
            return {"success": True, "project_id": project_id}
        else:
            return {"success": False, "error": "Failed to initialize project"}
    finally:
        # Cleanup temp zip if it exists to avoid resource leaks
        if temp_zip_path and os.path.exists(temp_zip_path):
            try:
                os.remove(temp_zip_path)
            except Exception as e:
                print(f"DEBUG: Failed to delete temp zip {temp_zip_path}: {e}")


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Deletes a project from both DB and Filesystem."""
    # 1. Fetch Project Name for Folder Deletion
    project_name = await db.get_project_name_by_id(project_id)
    
    # 2. Delete from DB
    db_success = await db.delete_project(project_id)
    
    # 3. Delete from FS
    fs_success = False
    if project_name:
        fs_success = PersistenceService.delete_project_directory(project_name, db.tenant_id)
    else:
        # Fallback: maybe the ID passed IS the name
        fs_success = PersistenceService.delete_project_directory(project_id, db.tenant_id)
    
    return {
        "success": True, 
        "details": {
            "db_deleted": db_success,
            "fs_deleted": fs_success
        }
    }


# --- Project Assets ---

@router.get("/{project_id}/assets")
async def get_project_assets(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Returns a scanned inventory of project assets."""
    resolved_uuid = project_id
    if "-" not in project_id:  # Heuristic for UUID
        u = await db.get_project_id_by_name(project_id)
        if u: 
            resolved_uuid = u
            
    assets = await db.get_project_assets(resolved_uuid)
    return {"assets": assets}


@router.get("/{project_id}/stats")
async def get_project_stats(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Returns summarized stats (core, ignored, pending) for a project."""
    return await db.get_project_stats(project_id)


# --- Project Files ---

@router.get("/{project_id}/files")
async def list_project_files(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Returns the file tree for the project's output directory."""
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: project_name = n

    # Use direct FS scanning for real-time updates
    # Pass Tenant ID for isolation
    tree = PersistenceService.get_project_files(project_name, db.tenant_id)
    
    return {
        "name": project_name,
        "type": "folder",
        "path": project_name,
        "children": tree
    }


@router.get("/{project_id}/files/content")
async def get_file_content(project_id: str, path: str, db: SupabasePersistence = Depends(get_db)):
    """Returns the content of a specific file."""
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: 
            project_name = n
        
    try:
        content = PersistenceService.read_file_content(project_name, path, db.tenant_id)
        return {"content": content}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}


# --- Project Layout ---

@router.post("/{project_id}/layout")
async def save_layout(project_id: str, layout: Dict[str, Any], db: SupabasePersistence = Depends(get_db)):
    """Saves the graph layout for the project."""
    asset_id = await db.save_project_layout(project_id, layout)
    return {"success": True, "asset_id": asset_id}


@router.get("/{project_id}/layout")
async def get_layout(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Retrieves the graph layout for the project."""
    layout = await db.get_project_layout(project_id)
    return layout or {}


# --- Project Stage & Settings ---

@router.post("/{project_id}/stage")
async def update_stage(project_id: str, payload: Dict[str, str], db: SupabasePersistence = Depends(get_db)):
    """Updates the project stage."""
    success = await db.update_project_stage(project_id, payload.get("stage"))
    if not success:
         raise HTTPException(status_code=400, detail="Failed to update stage. Project not found or invalid ID.")
    return {"success": success}


@router.post("/{project_id}/reset")
async def reset_project(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Clears all assets, FS folders (except Triage), and resets stage/status."""
    success = await db.reset_project_data(project_id)
    return {"success": success}


@router.patch("/{project_id}/settings")
async def update_project_settings(project_id: str, settings: Dict[str, Any], db: SupabasePersistence = Depends(get_db)):
    """Updates project-level settings (e.g. Source/Target Tech)."""
    success = await db.update_project_settings(project_id, settings)
    return {"success": success}


@router.get("/{project_id}/settings")
async def get_project_settings(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Retrieves project-level settings."""
    return await db.get_project_settings(project_id) or {}


# --- Project Lifecycle ---



@router.post("/{project_id}/approve")
async def approve_triage(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Locks the project scope and transitions to DRAFTING state."""
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: 
            project_uuid = u

    success_status = await db.update_project_status(project_uuid, "DRAFTING")
    success_stage = await db.update_project_stage(project_uuid, "2")
    return {"success": success_status and success_stage, "status": "DRAFTING"}


@router.post("/{project_id}/unlock")
async def unlock_triage(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Unlocks the project scope and transitions back to TRIAGE state."""
    project_uuid = project_id
    success = await db.update_project_status(project_uuid, "TRIAGE")
    return {"success": success, "status": "TRIAGE"}


@router.post("/{project_id}/cancel")
async def cancel_project_operation(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Request cancellation for any long-running agentic process on this project."""
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: project_uuid = u
        
    await db.update_project_metadata(project_uuid, {"cancellation_requested": True})
    return {"success": True}


# --- Logs ---

@router.get("/{project_id}/logs")
async def get_project_logs_simple(
    project_id: str, 
    type: str = "migration",  # Added type param with default
    db: SupabasePersistence = Depends(get_db)
):
    """Returns the logs for the project based on type."""
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: 
            project_name = n
        
    if type.lower() == "triage":
        log_file = "triage.log"
    elif type.lower() == "refinement":
        log_file = "refinement.log"
    else:
        log_file = "migration.log"

    try:
        content = PersistenceService.read_file_content(project_name, log_file, db.tenant_id)
        return {"logs": content}
    except Exception:
        return {"logs": ""}


@router.get("/{project_id}/execution-logs")
async def get_project_execution_logs(
    project_id: str, 
    type: str = "Triage", 
    db: SupabasePersistence = Depends(get_db)
):
    """
    Fetches execution logs from the database.
    Release 3.5: Moved to 'utm_execution_logs'.
    """
    phase_map = {
        "triage": "TRIAGE", 
        "migration": "MIGRATION", 
        "refinement": "REFINEMENT"
    }
    phase = phase_map.get(type.lower(), "TRIAGE")
    
    logs = await db.get_execution_logs(project_id, phase)
    
    log_lines = []
    for log in logs:
        timestamp = log.get("created_at", "")
        step = log.get("step", "System")
        msg = log.get("message", "")
        log_lines.append(f"[{timestamp}] [{step}] {msg}")
        
    return {"logs": "\n".join(log_lines)}


# --- Triage Files (for Agent S - Scout) ---

@router.get("/{project_id}/triage/files")
async def list_triage_files(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Lists all files in the project's Triage folder for forensic analysis."""
    
    # Resolve project name if UUID provided
    project_folder = project_id
    if "-" in project_id:
        resolved_name = await db.get_project_name_by_id(project_id)
        if resolved_name:
            project_folder = resolved_name
    
    # Get Triage path
    # We use list_files mechanism
    print(f"[DEBUG] list_triage_files called for project_id={project_id}, resolved={project_folder}, tenant={db.tenant_id}")
    project_base = PersistenceService.ensure_solution_dir(project_folder, db.tenant_id)
    # The ensure_solution_dir return path/key prefix. 
    # But list_files needs the path relative to storage root?
    # get_project_files handles the path construction.
    
    # We want ONLY Triage files.
    # We can scan all files and filter, providing a consistent view.
    try:
        all_files = PersistenceService.get_project_files(project_folder, db.tenant_id)
        
        triage_files = []
        file_types = {}
        
        for node in all_files:
            # We are looking for files starting with "Triage/" or inside Triage folder?
            # List structure is recursive.
            # We need to find the "Triage" folder node.
            
            def find_triage(nodes):
                for n in nodes:
                    if n["name"] == PersistenceService.STAGE_TRIAGE:
                        return n
                    if n.get("children"):
                        found = find_triage(n["children"])
                        if found: return found
                return None
            
            # The structure from list_files might change (it's list of dictionaries).
            # But the root of get_project_files returns the contents of the solution dir.
            # So "Triage" should be a top-level child.
            
            triage_node = next((n for n in all_files if n["name"] == PersistenceService.STAGE_TRIAGE), None)
            
            if not triage_node or not triage_node.get("children"):
                 # Return empty if no triage
                 return {
                    "success": True,
                    "project_id": project_id,
                    "triage_path": "Triage",
                    "file_count": 0,
                    "file_types": {},
                    "files": []
                }
            
            # Now flatten the files inside Triage
            def collect_files(nodes, parent_path=""):
                for n in nodes:
                    if n["type"] == "folder":
                        collect_files(n.get("children", []), os.path.join(parent_path, n["name"]))
                    else:
                        ext = n["name"].split('.')[-1].lower() if '.' in n["name"] else 'no_ext'
                        file_types[ext] = file_types.get(ext, 0) + 1
                        
                        # Fix system file checks (if any)
                        if n["name"] in ['triage.log', 'layout.json', 'migration.log', 'refinement.log', 'manifest.json']:
                            continue

                        triage_files.append({
                            "name": n["name"],
                            "path": n["path"], # This is the full path/key from StorageProvider
                            "full_path": n["path"], 
                            "size": n["size"],
                            "extension": ext,
                            "type": _classify_file_type(ext)
                        })

            collect_files(triage_node.get("children", []), "")
            
            return {
                "success": True,
                "project_id": project_id,
                "triage_path": "Triage", # Conceptual path
                "file_count": len(triage_files),
                "file_types": file_types,
                "files": triage_files
            }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Error scanning Triage: {str(e)}",
            "project_id": project_id,
        }


@router.post("/{project_id}/triage/upload")
async def upload_triage_files(
    project_id: str,
    files: List[UploadFile] = File(...),
    db: SupabasePersistence = Depends(get_db)
):
    """Uploads one or many files to the project's Triage directory."""
    # 1. Resolve project folder name (handles UUID or Name)
    project_folder = project_id
    if "-" in project_id:
        resolved_name = await db.get_project_name_by_id(project_id)
        if resolved_name:
            project_folder = resolved_name
    
    # 2. Get storage provider and ensure directory
    storage = PersistenceService.get_storage()
    project_base = PersistenceService.ensure_solution_dir(project_folder, db.tenant_id)
    triage_prefix = f"{project_base.rstrip('/')}/{PersistenceService.STAGE_TRIAGE}"
    
    uploaded_files = []
    
    try:
        for file in files:
            content = await file.read()
            # Standardize filename and construct key
            # We don't want to nested paths here, just flat in Triage/
            filename = os.path.basename(file.filename)
            dest_key = f"{triage_prefix}/{filename}"
            
            storage.save_file(dest_key, content, is_binary=True)
            uploaded_files.append(filename)
            
        return {
            "success": True,
            "project_id": project_id,
            "uploaded_count": len(uploaded_files),
            "files": uploaded_files
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to upload files: {str(e)}")


def _classify_file_type(ext: str) -> str:
    """Helper to classify file types for Agent S."""
    if ext == 'dtsx': return 'SSIS_PACKAGE'
    if ext == 'sql': return 'SQL_SCRIPT'
    if ext in ['xml', 'config']: return 'CONFIG'
    if ext in ['json', 'yaml', 'yml']: return 'CONFIG'
    if ext == 'py': return 'PYTHON_SCRIPT'
    if ext in ['txt', 'md', 'doc', 'docx']: return 'DOCUMENTATION'
    return 'OTHER'
