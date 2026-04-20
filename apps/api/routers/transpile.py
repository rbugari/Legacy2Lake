"""
Transpile & Orchestration Router
Handles code generation, transpilation, and migration orchestration.
Migrated from main.py for better modularity.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import uuid
import asyncio

from apps.api.routers.dependencies import get_db, get_identity
from apps.api.services.persistence_service import SupabasePersistence, PersistenceService
from apps.api.services.agent_c_service import AgentCService
from apps.api.services.agent_f_service import AgentFService
from apps.api.services.migration_orchestrator import MigrationOrchestrator
from apps.api.services.lock_service import LockService, ProcessLockError

router = APIRouter(prefix="/transpile", tags=["Transpilation & Orchestration"])


# --- Models ---

class TranspileRequest(BaseModel):
    node_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class TranspileAllRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None


class OptimizeRequest(BaseModel):
    code: str
    optimizations: Optional[List[str]] = []
    context: Optional[Dict[str, Any]] = None


# --- Helper Functions ---

def extract_code_from_result(result: Dict[str, Any]) -> Optional[str]:
    """
    Extracts code from Agent C result, handling multiple possible key formats.
    Tries: code, pyspark_code, sql_code, final_code, generated_code
    Special case: If no standard key found, check if result itself is JSON schema (Salesforce case)
    """
    possible_keys = ["code", "pyspark_code", "sql_code", "dbt_code", "final_code", "generated_code"]
    for key in possible_keys:
        if key in result and result[key]:
            return result[key]
    
    # Special case: Salesforce JSON schemas come as root object without "code" wrapper
    # Detect by presence of schema-like keys: "fields", "name", "sourceObject"
    if isinstance(result, dict) and ("fields" in result or "sourceObject" in result):
        import json
        return json.dumps(result, indent=2)
    
    return None


# --- Single Task Transpilation ---

@router.post("/task")
async def transpile_task(payload: TranspileRequest, db: SupabasePersistence = Depends(get_db)):
    """Chain Agent C (Interpreter) and Agent F (Critic) for a robust result."""
    node_data = payload.node_data
    context = payload.context or {}
    
    # 1. Generate initial code (Agent C)
    agent_c = AgentCService(tenant_id=db.tenant_id, client_id=db.client_id)
    c_result = await agent_c.transpile_task(node_data, context)
    
    if "error" in c_result:
        return c_result

    # Extract code from result (handle multiple key formats)
    generated_code = extract_code_from_result(c_result)
    if not generated_code:
        return {
            "error": "No code generated",
            "detail": "Agent C did not return valid code",
            "result_keys": list(c_result.keys())
        }

    # 2. Audit and Optimize (Agent F)
    agent_f = AgentFService(tenant_id=db.tenant_id, client_id=db.client_id)
    f_result = await agent_f.review_code(node_data, generated_code)
    
    # 3. Persistence (Local & Supabase)
    solution_name = context.get("solution_name", "DefaultProject")
    task_name = node_data.get("name", "UnnamedTask")
    
    # Final code: optimized version if available, otherwise original generated code
    final_code = f_result.get("optimized_code") or generated_code
    
    local_path = PersistenceService.save_transformation(
        solution_name, 
        task_name, 
        final_code
    )
    
    # 4. Persistence (Supabase)
    asset_id = context.get("asset_id")
    if asset_id:
        db = SupabasePersistence()
        await db.save_transformation(
            asset_id,
            node_data.get("description", ""),
            final_code
        )

    return {
        "interpreter": c_result,
        "critic": f_result,
        "final_code": final_code,
        "saved_at": local_path
    }


# --- Batch Transpilation ---

@router.post("/all")
async def transpile_all(payload: TranspileAllRequest, db: SupabasePersistence = Depends(get_db)):
    """Iteratively transpile all nodes in a mesh."""
    nodes = payload.nodes
    context = payload.context or {}
    
    results = []
    agent_c = AgentCService(tenant_id=db.tenant_id, client_id=db.client_id)
    agent_f = AgentFService(tenant_id=db.tenant_id, client_id=db.client_id)
    # db is already passed via Depends(get_db)
    
    solution_name = context.get("solution_name", "BulkProject")
    asset_id = context.get("asset_id")

    # Release 3.7: Fetch Intelligence Context
    project_id = context.get("project_id")
    support_intel = []
    scout_assessment = {}
    if project_id:
        project_meta = await db.get_project_metadata(project_id)
        settings = project_meta.get("settings", {})
        support_intel = settings.get("support_intelligence", [])
        scout_assessment = settings.get("scout_assessment", {})

    for node in nodes:
        node_data = node.get("data", {}).copy() # Use copy to avoid mutating source
        # Inject Intelligence
        node_data["support_intelligence"] = support_intel
        node_data["scout_assessment"] = scout_assessment
        
        # Skip purely decorative or empty nodes
        if not node_data.get("label"):
            continue
            
        # 1. Generate
        c_res = await agent_c.transpile_task(node_data, context)
        if "error" in c_res:
            results.append({"node": node_data.get("label"), "status": "FAILED", "error": c_res["error"]})
            continue
        
        # Extract generated code
        generated_code = extract_code_from_result(c_res)
        if not generated_code:
            results.append({
                "node": node_data.get("label"), 
                "status": "FAILED", 
                "error": "No code generated",
                "result_keys": list(c_res.keys())
            })
            continue
            
        # 2. Audit
        f_res = await agent_f.review_code(node_data, generated_code)
        final_code = f_res.get("optimized_code") or generated_code
        
        # 3. Save Local
        local_path = PersistenceService.save_transformation(
            solution_name,
            node_data.get("name", node_data.get("label")),
            final_code
        )
        
        # 4. Save Supabase
        if asset_id:
            await db.save_transformation(
                asset_id,
                node_data.get("description", ""),
                final_code
            )
        
        results.append({
            "node": node_data.get("label"),
            "status": "SUCCESS",
            "score": f_res.get("score"),
            "path": local_path
        })
        
    return {"summary": results, "solution_path": solution_name}


# --- Optimization ---

@router.post("/optimize")
async def optimize_task_code(payload: OptimizeRequest, db: SupabasePersistence = Depends(get_db)):
    """Re-runs Agent F with specific optimization flags."""
    code = payload.code
    optimizations = payload.optimizations or []
    
    if not code:
        return {"error": "No code provided"}
        
    agent_f = AgentFService(tenant_id=db.tenant_id, client_id=db.client_id)
    result = await agent_f.review_code({"optimizations": optimizations}, code)
    
    return {
        "original": code,
        "optimized": result.get("optimized_code") or code,
        "score": result.get("score"),
        "suggestions": result.get("suggestions", [])
    }


# --- Full Migration Orchestration ---

# Background task function
async def _run_orchestration_background(
    project_id: str,
    limit: int,
    lock_ids: Dict[str, str],
    lock_service: LockService,
    tenant_id: str,
    owner_user_id: str,
    username: str,
    db_config: Dict[str, Any]
):
    """Runs the full orchestration in background."""
    db = SupabasePersistence(tenant_id=tenant_id, client_id=db_config.get("client_id"))
    project_uuid = project_id
    
    try:
        # Clear previous execution logs for this phase (fresh start)
        await db.clear_execution_logs(project_uuid, phase="MIGRATION")
        
        # Log start (but don't change status yet - let run_full_migration validate first)
        await db.log_execution(project_uuid, "MIGRATION", "Starting Migration Orchestrator...", step="SYSTEM")
        
        # Check for cancellation
        project = await db.get_project_metadata(project_uuid)
        if project and project.get("cancellation_requested"):
            await db.log_execution(project_uuid, "MIGRATION", "Process cancelled by user.", step="SYSTEM")
            await db.update_project_status(project_uuid, "DRAFTING")
            return
        
        # 1. Resolve Project Name
        project_name = project_id
        if "-" in project_id:
            n = await db.get_project_name_by_id(project_id)
            if n: 
                project_name = n
        
        await db.log_execution(project_uuid, "MIGRATION", f"Instantiating MigrationOrchestrator for {project_name}", step="SYSTEM")
        
        orchestrator = MigrationOrchestrator(
            project_name, 
            project_uuid=project_id, 
            tenant_id=tenant_id, 
            client_id=db_config.get("client_id")
        )
        
        await db.log_execution(project_uuid, "MIGRATION", "Running full migration (Agents C → F → G)...", step="SYSTEM")
        # Set status to DRAFTING before running so the orchestrator's status check passes
        await db.update_project_status(project_uuid, "DRAFTING")
        result = await orchestrator.run_full_migration(limit=limit)

        if result.get("cancelled"):
            await db.log_execution(project_uuid, "MIGRATION", "Process cancelled by user.", step="SYSTEM")
            await db.update_project_status(project_uuid, "DRAFTING")
            return
        
        await db.log_execution(project_uuid, "MIGRATION", f"Migration complete. Result: {result.get('status', 'success')}", step="SYSTEM")
        
        # Update status to DRAFTED on success
        await db.update_project_status(project_uuid, "DRAFTED")
        
    except Exception as e:
        if "cancelled by user" in str(e).lower():
            await db.log_execution(project_uuid, "MIGRATION", "Process cancelled by user.", step="SYSTEM")
        else:
            await db.log_execution(project_uuid, "MIGRATION", f"ERROR: {str(e)}", step="SYSTEM")
        await db.update_project_status(project_uuid, "DRAFTING")  # Revert on error
        # Do not re-raise from background task; keep API stable and rely on persisted logs/status.
        return
    finally:
        # Release all locks
        for process_type, lock_id in lock_ids.items():
            try:
                await lock_service.release_lock(lock_id=lock_id, user_id=owner_user_id)
                print(f"[ORCHESTRATION] Lock {lock_id} released for {process_type}")
            except Exception as e:
                print(f"WARNING: Failed to release {process_type} lock {lock_id}: {e}")


@router.post("/orchestrate")
async def trigger_orchestration(
    payload: Dict[str, Any], 
    request: Request,
    background_tasks: BackgroundTasks,
    identity: dict = Depends(get_identity),
    db: SupabasePersistence = Depends(get_db)
):
    """Triggers the full Migration Orchestrator (Agents C -> F -> G) in background."""
    print(f"DEBUG: Entering trigger_orchestration with payload: {payload}")
    project_id = payload.get("project_id")
    limit = payload.get("limit", 0)
    
    if not project_id:
        return {"error": "project_id is required"}
    
    # === PROCESS LOCKING ===
    lock_service = LockService(tenant_id=identity.get("tenant_id"), client_id=identity.get("client_id"))
    
    # Get username for lock
    tenant_id = identity.get("tenant_id")
    owner_user_id = identity.get("user_id") or tenant_id
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
        session_id = str(uuid.uuid5(uuid.NAMESPACE_OID, request.headers.get("user-agent", "")))
    
    # Try to acquire lock for all 3 processes (drafting, certification, governance)
    lock_ids = {}
    try:
        for process_type in ["drafting", "certification", "governance"]:
            lock = await lock_service.acquire_lock(
                project_id=project_id,
                process_type=process_type,
                user_id=owner_user_id,
                username=username,
                session_id=session_id,
                user_agent=request.headers.get("user-agent"),
                ip_address=request.headers.get("x-forwarded-for") or "unknown"
            )
            lock_ids[process_type] = lock['lock_id']
        
    except ProcessLockError as e:
        # Release any acquired locks before failing
        for lock_id in lock_ids.values():
            try:
                await lock_service.release_lock(lock_id=lock_id, user_id=owner_user_id)
            except:
                pass
        
        raise HTTPException(
            status_code=423,
            detail={
                "error": "Process already running",
                "message": e.message,
                "locked_by": e.locked_by
            }
        )
    
    # === MAIN ORCHESTRATION LOGIC ===
    # Preserve post_drafting_mode by default so users can continue to Refinement
    # after rerunning Drafting. Allow explicit reset when requested by payload.
    reset_mode_raw = payload.get("reset_post_drafting_mode", False)
    reset_post_drafting_mode = (
        reset_mode_raw is True
        or (isinstance(reset_mode_raw, str) and reset_mode_raw.strip().lower() in {"1", "true", "yes", "on"})
    )
    if reset_post_drafting_mode:
        await db.clear_post_drafting_mode(project_id)

    # Set status to DRAFTING here synchronously so run_full_migration's status check passes
    await db.update_project_status(project_id, "DRAFTING")

    try:
        # Prepare DB config for background task (thread-safe)
        db_config = {
            "client_id": db.client_id,
            "tenant_id": tenant_id
        }
        
        # Start background task
        background_tasks.add_task(
            _run_orchestration_background,
            project_id,
            limit,
            lock_ids,
            lock_service,
            tenant_id,
            owner_user_id,
            username,
            db_config
        )
        
        return {
            "status": "RUNNING",
            "message": "Migration orchestration started in background. Monitor logs for progress.",
            "project_id": project_id
        }
        
    except Exception as e:
        # === ERROR: Release all locks before re-raising ===
        for lock_id in lock_ids.values():
            try:
                await lock_service.release_lock(lock_id=lock_id, user_id=owner_user_id)
            except:
                pass
        raise e

