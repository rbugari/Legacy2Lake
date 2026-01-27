"""
Projects Router
Handles CRUD operations, settings, layout, and lifecycle management for projects.
Migrated from main.py for better modularity.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
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
    # 1. Try to find by UUID first
    metadata = await db.get_project_metadata(project_id)
    if metadata:
        if metadata.get("is_active") is False:
            raise HTTPException(status_code=403, detail="Project Access Suspended (Kill-switch Active)")
        return metadata
    
    # 2. Fallback: maybe the string passed is the project Name?
    uuid = await db.get_project_id_by_name(project_id)
    if uuid:
        metadata = await db.get_project_metadata(uuid)
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
    db: SupabasePersistence = Depends(get_db)
):
    """Creates a new project and initializes it from source."""
    # 1. Register in Database (Supabase)
    real_id = await db.get_or_create_project(name, github_url)
    
    # 2. Handle File Upload (Save temporarily)
    temp_zip_path = None
    if source_type == "zip" and file:
        temp_zip_path = os.path.join(PersistenceService.BASE_DIR, f"{project_id}_temp.zip")
        with open(temp_zip_path, "wb") as buffer:
            import shutil
            shutil.copyfileobj(file.file, buffer)
            
    # 3. Initialize Directory
    success = PersistenceService.initialize_project_from_source(
        project_id=project_id,
        source_type=source_type,
        file_path=temp_zip_path,
        github_url=github_url,
        overwrite=overwrite
    )
    
    if success:
        return {"success": True, "project_id": project_id}
    else:
        return {"success": False, "error": "Failed to initialize project"}


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
        fs_success = PersistenceService.delete_project_directory(project_name)
    else:
        # Fallback: maybe the ID passed IS the name
        fs_success = PersistenceService.delete_project_directory(project_id)
    
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
        if n: 
            project_name = n

    # Use direct FS scanning for real-time updates
    tree = PersistenceService.get_project_files(project_name)
    
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
        content = PersistenceService.read_file_content(project_name, path)
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
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: 
            project_uuid = u

    success = await db.update_project_status(project_uuid, "TRIAGE")
    return {"success": success, "status": "TRIAGE"}


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
        
    log_file = "migration.log"
    if type.lower() == "triage":
        log_file = "triage.log"
    elif type.lower() == "refinement":
        log_file = "migration.log"

    try:
        content = PersistenceService.read_file_content(project_name, log_file)
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
    project_base = PersistenceService.ensure_solution_dir(project_folder)
    triage_path = os.path.join(project_base, PersistenceService.STAGE_TRIAGE)
    
    if not os.path.exists(triage_path):
        return {
            "success": False,
            "message": "Triage folder not found. Upload files first.",
            "project_id": project_id,
            "triage_path": triage_path,
            "file_count": 0,
            "files": []
        }
    
    files = []
    file_types = {}
    
    for root, dirs, filenames in os.walk(triage_path):
        # Exclude system folders
        if '.git' in dirs: dirs.remove('.git')
        if '__pycache__' in dirs: dirs.remove('__pycache__')
        
        for filename in filenames:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, triage_path).replace("\\", "/")
            ext = filename.split('.')[-1].lower() if '.' in filename else 'no_ext'
            
            # Count file types
            file_types[ext] = file_types.get(ext, 0) + 1
            
            files.append({
                "name": filename,
                "path": rel_path,
                "full_path": full_path,
                "size": os.path.getsize(full_path),
                "extension": ext,
                "type": _classify_file_type(ext)
            })
    
    return {
        "success": True,
        "project_id": project_id,
        "triage_path": triage_path,
        "file_count": len(files),
        "file_types": file_types,
        "files": files
    }


def _classify_file_type(ext: str) -> str:
    """Helper to classify file types for Agent S."""
    if ext == 'dtsx': return 'SSIS_PACKAGE'
    if ext == 'sql': return 'SQL_SCRIPT'
    if ext in ['xml', 'config']: return 'CONFIG'
    if ext in ['json', 'yaml', 'yml']: return 'CONFIG'
    if ext == 'py': return 'PYTHON_SCRIPT'
    if ext in ['txt', 'md', 'doc', 'docx']: return 'DOCUMENTATION'
    return 'OTHER'


# --- Export ---

@router.get("/{project_id}/export")
async def export_project(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Streams the project solution as a ZIP bundle."""
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: 
            project_name = n
    
    # 1. Use PackagingService to create COP structure
    try:
        from services.packaging_service import PackagingService
        packager = PackagingService(project_id)
        # prepares "root_dir" inside "_package_staging"
        package_root = await packager.prepare_bundle()
        
        # 2. ZIP the structured package
        zip_buffer = io.BytesIO()
        # package_root is .../_package_staging/ProjectName
        # We want the ZIP to contain ProjectName/...
        
        base_dir = os.path.dirname(package_root) # .../_package_staging
        root_folder_name = os.path.basename(package_root) # ProjectName
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(package_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Relpath from _package_staging so the zip has ProjectName/config/...
                    arcname = os.path.relpath(file_path, base_dir)
                    zf.write(file_path, arcname)
                    
        # Cleanup staging is tricky if we want async stream, but for now we rely on overwrite next time
        # or we could schedule a cleanup task. 
        # PersistenceService.robust_rmtree(os.path.dirname(package_root)) # Optional cleanup
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=Legacy2Lake_{project_name}.zip"}
        )
        
    except Exception as e:
        print(f"Export Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate package: {str(e)}")
