"""
Refinement & Governance Router
Handles Phase 3 (Refinement) and Phase 4 (Governance) operations.
Migrated from main.py for better modularity.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import io
import os
import zipfile
import uuid
import asyncio

from apps.api.routers.dependencies import get_db, get_identity
from apps.api.services.persistence_service import SupabasePersistence, PersistenceService
from apps.api.services.agent_g_service import AgentGService
from apps.api.services.refinement.governance_service import GovernanceService
from apps.api.services.refinement.refinement_orchestrator import RefinementOrchestrator
from apps.api.services.lock_service import LockService, ProcessLockError

router = APIRouter(tags=["Refinement & Governance"])


# --- Models ---

class RefinementRequest(BaseModel):
    project_id: str
    options: Optional[Dict[str, Any]] = None


class DocumentRequest(BaseModel):
    project_name: str
    mesh: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


# --- Refinement Endpoints (Phase 3) ---

# Background task function for refinement
async def _run_refinement_background(
    project_id: str,
    lock_id: str,
    lock_service: LockService,
    tenant_id: str,
    username: str,
    db_config: Dict[str, Any]
):
    """Runs the refinement process in background."""
    db = SupabasePersistence(tenant_id=tenant_id, client_id=db_config.get("client_id"))
    project_uuid = project_id
    
    try:
        # Clear previous execution logs for this phase (fresh start)
        await db.clear_execution_logs(project_uuid, phase="REFINEMENT")
        
        # Update status to REFINING
        await db.update_project_status(project_uuid, "REFINING")
        await db.log_execution(project_uuid, "REFINEMENT", "Starting Refinement Phase...", step="SYSTEM")
        
        # Check for cancellation
        project = await db.get_project_metadata(project_uuid)
        if project and project.get("cancellation_requested"):
            await db.log_execution(project_uuid, "REFINEMENT", "Process cancelled by user.", step="SYSTEM")
            await db.update_project_status(project_uuid, "REFINEMENT")
            return
        
        # 1. Resolve Project Name
        project_name = project_id
        if "-" in project_id:
            n = await db.get_project_name_by_id(project_id)
            if n: 
                project_name = n
        
        await db.log_execution(project_uuid, "REFINEMENT", f"Instantiating RefinementOrchestrator for {project_name}", step="SYSTEM")
        
        # Update stage to REFINEMENT (Stage 3)
        await db.update_project_stage(project_id, "3")
        
        orchestrator = RefinementOrchestrator(
            project_name,
            project_uuid=project_id,
            tenant_id=tenant_id,
            client_id=db_config.get("client_id")
        )
        
        await db.log_execution(project_uuid, "REFINEMENT", "Running refinement (Profiler → Architect → Refactor → Ops)...", step="SYSTEM")
        result = await orchestrator.run()
        
        # Update stage to GOVERNANCE (Stage 4) if successful
        if result.get("success"):
            await db.update_project_stage(project_id, "4")
            await db.update_project_status(project_uuid, "REFINED")
            await db.log_execution(project_uuid, "REFINEMENT", "Refinement complete. Project ready for Governance.", step="SYSTEM")
        else:
            await db.log_execution(project_uuid, "REFINEMENT", f"Refinement failed: {result.get('error', 'Unknown error')}", step="SYSTEM")
            await db.update_project_status(project_uuid, "REFINEMENT")  # Revert on error
        
    except Exception as e:
        await db.log_execution(project_uuid, "REFINEMENT", f"ERROR: {str(e)}", step="SYSTEM")
        await db.update_project_status(project_uuid, "REFINEMENT")  # Revert on error
        raise
    finally:
        # Release lock
        try:
            await lock_service.release_lock(lock_id=lock_id, user_id=tenant_id)
            print(f"[REFINEMENT] Lock {lock_id} released")
        except Exception as e:
            print(f"WARNING: Failed to release lock {lock_id}: {e}")


@router.post("/refine/start")
async def start_refinement_legacy(
    payload: dict, 
    request: Request,
    background_tasks: BackgroundTasks,
    identity: dict = Depends(get_identity),
    db: SupabasePersistence = Depends(get_db)
):
    """Legacy alias for starting refinement (used by RefinementView.tsx)."""
    project_id = payload.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="Missing project_id in payload")
    
    # Delegate to the standard endpoint logic
    return await start_refinement(project_id, payload, request, background_tasks, identity, db)

@router.post("/projects/{project_id}/refinement/start")
async def start_refinement(
    project_id: str, 
    payload: dict, 
    request: Request,
    background_tasks: BackgroundTasks,
    identity: dict = Depends(get_identity),
    db: SupabasePersistence = Depends(get_db)
):
    """Triggers the Refinement Phase (Profiler -> Architect -> Refactor -> Ops) in background."""
    
    # === PROCESS LOCKING ===
    lock_service = LockService(tenant_id=identity.get("tenant_id"), client_id=identity.get("client_id"))
    
    # Get username for lock
    tenant_id = identity.get("tenant_id")
    username = identity.get("username", "Unknown User")
    if not username or username == "Unknown User":
        try:
            tenant = await db.get_tenant_by_id(tenant_id)
            username = tenant.get("username", "Unknown User") if tenant else "Unknown User"
        except:
            username = "Unknown User"
    
    # Generate or get session ID
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Try to acquire lock
    lock_id = None
    try:
        lock = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="refinement",
            user_id=tenant_id,
            username=username,
            session_id=session_id,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.headers.get("x-forwarded-for") or "unknown"
        )
        lock_id = lock['lock_id']
        
    except ProcessLockError as e:
        raise HTTPException(
            status_code=423,
            detail={
                "error": "Process already running",
                "message": e.message,
                "locked_by": e.locked_by
            }
        )
    
    # === MAIN REFINEMENT LOGIC ===
    try:
        # Update status to REFINING and start background task
        await db.update_project_status(project_id, "REFINING")
        
        # Prepare DB config for background task (thread-safe)
        db_config = {
            "client_id": db.client_id,
            "tenant_id": tenant_id
        }
        
        # Start background task
        background_tasks.add_task(
            _run_refinement_background,
            project_id,
            lock_id,
            lock_service,
            tenant_id,
            username,
            db_config
        )
        
        return {
            "status": "RUNNING",
            "message": "Refinement phase started in background. Monitor logs for progress.",
            "project_id": project_id
        }
        
    except Exception as e:
        # === ERROR: Release lock ===
        if lock_id:
            try:
                await lock_service.release_lock(lock_id=lock_id, user_id=tenant_id)
            except:
                pass
        raise e


@router.get("/projects/{project_id}/refinement/state")
async def get_refinement_state(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Returns the persisted state of Phase 3 (logs and profile)."""
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: 
            project_name = n

    state = {
        "log": [],
        "profile": None
    }

    try:
        # 1. Fetch Logs
        log_content = PersistenceService.read_file_content(project_name, "refinement.log")
        if log_content:
            state["log"] = log_content.split("\n")
    except:
        pass

    try:
        # 2. Fetch Profile Metadata
        profile_content = PersistenceService.read_file_content(project_name, "Refined/profile_metadata.json")
        if profile_content:
            state["profile"] = json.loads(profile_content)
    except:
        pass

    return state


# --- Governance Endpoints (Phase 4) ---

@router.get("/projects/{project_id}/status")
async def get_project_status_gov(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Returns the current governance status."""
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: 
            project_uuid = u
        
    status = await db.get_project_status(project_uuid)
    return {"status": status}


@router.get("/projects/{project_id}/governance")
async def get_governance(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Returns the certification report. If cached (from background run), returns instantly. Otherwise generates synchronously."""
    # Try cached report first — set by background task
    settings = await db.get_project_settings(project_id) or {}
    cached = settings.get("governance_report")
    if cached:
        return cached

    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n:
            project_name = n

    service = GovernanceService(tenant_id=db.tenant_id, client_id=db.client_id)
    try:
        report = await service.get_certification_report(project_id)
        return report
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/audit")
async def run_audit_endpoint(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Triggers a fresh audit execution (Alias for /governance)."""
    return await get_governance(project_id, db)


async def _run_governance_background(
    project_id: str,
    lock_id: str,
    lock_service,
    tenant_id: str,
    client_id: str,
):
    """Runs governance certification in background, logging each step."""
    db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
    try:
        await db.clear_execution_logs(project_id, phase="GOVERNANCE")
        await db.update_project_status(project_id, "GOVERNING")
        await db.log_execution(project_id, "GOVERNANCE", "[SYSTEM] Governance pipeline started.", step="SYSTEM")
        await db.log_execution(project_id, "GOVERNANCE", "[AGENT G] Loading refined artifacts and asset inventory...", step="AGENT_G")

        service = GovernanceService(tenant_id=tenant_id, client_id=client_id)

        await db.log_execution(project_id, "GOVERNANCE", "[AGENT G] Running compliance audit (Critic + Governor)...", step="AGENT_G")
        report = await service.get_certification_report(project_id)

        await db.log_execution(project_id, "GOVERNANCE", "[AGENT G] Computing medallion lineage and COP score...", step="AGENT_G")

        # Persist report in project settings for retrieval without re-running Agent G
        settings = await db.get_project_settings(project_id) or {}
        settings["governance_report"] = report
        await db.update_project_settings(project_id, settings)

        await db.update_project_status(project_id, "CERTIFIED")
        score = report.get("score", 0)
        await db.log_execution(project_id, "GOVERNANCE", f"[PROGRESS: 100/100] Governance complete. COP Score: {score}/100", step="SYSTEM")

    except Exception as e:
        import traceback
        traceback.print_exc()
        await db.log_execution(project_id, "GOVERNANCE", f"[ERROR] Governance failed: {str(e)}", step="SYSTEM")
        await db.update_project_status(project_id, "REFINED")  # rollback
    finally:
        try:
            await lock_service.release_lock(lock_id=lock_id, user_id=tenant_id)
        except Exception:
            pass


@router.post("/projects/{project_id}/governance/run")
async def run_governance_background(
    project_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
    identity: dict = Depends(get_identity),
    db: SupabasePersistence = Depends(get_db),
):
    """Starts governance certification in background. Poll /execution-logs?type=governance + project status CERTIFIED."""
    tenant_id = identity.get("tenant_id")
    username = identity.get("username", "Unknown User")
    session_id = request.headers.get("X-Session-ID") or str(uuid.uuid4())

    lock_service = LockService(tenant_id=tenant_id, client_id=identity.get("client_id"))
    lock_id = None
    try:
        lock = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="governance",
            user_id=tenant_id,
            username=username,
            session_id=session_id,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.headers.get("x-forwarded-for") or "unknown",
        )
        lock_id = lock["lock_id"]
    except ProcessLockError as e:
        raise HTTPException(status_code=423, detail={"error": "Process already running", "message": e.message, "locked_by": e.locked_by})

    background_tasks.add_task(
        _run_governance_background,
        project_id,
        lock_id,
        lock_service,
        tenant_id,
        identity.get("client_id"),
    )
    return {"status": "RUNNING", "message": "Governance pipeline started in background. Poll /execution-logs?type=governance for progress."}


@router.post("/governance/document")
async def generate_governance(payload: DocumentRequest):
    """Generates and persists technical/governance documentation."""
    project_name = payload.project_name
    mesh = payload.mesh
    context = payload.context or {}
    
    # 1. Fetch transformations for this project from Supabase
    db = SupabasePersistence()
    asset_id = context.get("asset_id")
    
    transformations = []
    if asset_id:
        res = db.client.table("transformations").select("target_code").eq("asset_id", asset_id).execute()
        transformations = res.data

    # 2. Invoke Agent G
    agent_g = AgentGService()
    doc_content = await agent_g.generate_documentation(project_name, mesh, transformations)
    
    # 3. Save Local
    solution_name = context.get("solution_name", "GovernanceProject")
    local_path = PersistenceService.save_documentation(solution_name, "GOVERNANCE", doc_content)
    
    return {
        "status": "success",
        "documentation": doc_content,
        "saved_at": local_path
    }


@router.get("/projects/{project_id}/export/governance")
async def export_governance(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Streams the project solution as a full governance ZIP bundle."""
    metadata = await db.get_project_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_name = metadata.get("name")
    effective_tenant_id = db.tenant_id or metadata.get("tenant_id")

    service = GovernanceService(tenant_id=effective_tenant_id, client_id=db.client_id)
    try:
        zip_buffer = await service.create_export_bundle(project_id) # Using ID
        filename = f"Legacy2Lake_Solution_{project_name}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        import traceback
        print(f"EXPORT ERROR: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/export/delivery")
async def export_delivery(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Streams the technical deployment-only ZIP bundle (COP)."""
    # 1. Resolve project name and REQUIRED tenant_id
    metadata = await db.get_project_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_name = metadata.get("name")
    effective_tenant_id = db.tenant_id or metadata.get("tenant_id")
    
    # 2. Use PackagingService to create COP structure
    try:
        from apps.api.services.packaging_service import PackagingService
        packager = PackagingService(project_id, tenant_id=effective_tenant_id, client_id=db.client_id)
        # prepares "root_dir" inside "_package_staging"
        package_root = await packager.prepare_bundle()
        
        # 3. ZIP the structured package
        zip_buffer = io.BytesIO()
        base_dir = os.path.dirname(package_root) # .../_package_staging
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(package_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Relpath from _package_staging so the zip has ProjectName/config/...
                    arcname = os.path.relpath(file_path, base_dir)
                    zf.write(file_path, arcname)
                    
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=Legacy2Lake_Delivery_{project_name}.zip"}
        )
        
    except Exception as e:
        import traceback
        print(f"Delivery Export Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to generate package: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# GitHub Push Endpoint
# ─────────────────────────────────────────────────────────────────────────────

class GitHubPushRequest(BaseModel):
    repo_url: str
    token: str
    branch: str = "legacy2lake-migration"
    target_path: str = "modernized/"
    commit_message: str = "Legacy2Lake: Add modernized migration code"
    create_pr: bool = False
    pr_title: str = "[Legacy2Lake] Modernization Artifacts"
    pr_body: str = "Migration artifacts generated automatically by Legacy2Lake UTM v4.0."


@router.post("/projects/{project_id}/github/push")
async def push_to_github(
    project_id: str,
    payload: GitHubPushRequest,
    db: SupabasePersistence = Depends(get_db),
    identity: dict = Depends(get_identity),
):
    """
    Push all generated migration artifacts (drafting + refinement) for a project
    to a GitHub repository and optionally open a Pull Request.
    """
    try:
        from apps.api.services.github_push_service import GitHubPushService

        tenant_id = identity.get("tenant_id")

        # Resolve project name from UUID
        project_meta = await db.get_project_metadata(project_id)
        if not project_meta:
            raise HTTPException(status_code=404, detail="Project not found")

        project_name = project_meta.get("name") or project_meta.get("project_name") or project_id
        storage = PersistenceService.get_storage()
        base_path = PersistenceService.ensure_solution_dir(project_name, tenant_id=tenant_id)

        service = GitHubPushService(tenant_id=tenant_id)
        result = await service.push_artifacts(
            project_id=project_name,
            storage=storage,
            base_path=base_path,
            repo_url=payload.repo_url,
            token=payload.token,
            branch=payload.branch,
            target_path=payload.target_path,
            commit_message=payload.commit_message,
            create_pr=payload.create_pr,
            pr_title=payload.pr_title,
            pr_body=payload.pr_body,
        )

        if not result.get("success"):
            raise HTTPException(status_code=422, detail=result.get("error", "Push failed"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub push failed: {str(e)}")

