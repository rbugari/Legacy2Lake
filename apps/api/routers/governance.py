"""
Refinement & Governance Router
Handles Phase 3 (Refinement) and Phase 4 (Governance) operations.
Migrated from main.py for better modularity.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json

from routers.dependencies import get_db
from services.persistence_service import SupabasePersistence, PersistenceService
from services.agent_g_service import AgentGService
from services.refinement.governance_service import GovernanceService
from services.refinement.refinement_orchestrator import RefinementOrchestrator

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

@router.post("/projects/{project_id}/refinement/start")
async def start_refinement(project_id: str, payload: dict, db: SupabasePersistence = Depends(get_db)):
    """Triggers the Refinement Phase (Profiler -> Architect -> Refactor -> Ops)."""
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: 
            project_name = n

    try:
        # Update stage to REFINEMENT (Stage 3)
        await db.update_project_stage(project_id, "3")
        
        orchestrator = RefinementOrchestrator(
            project_name,
            project_uuid=project_id,
            tenant_id=db.tenant_id,
            client_id=db.client_id
        )
        
        result = await orchestrator.run()
        
        # Update stage to GOVERNANCE (Stage 4) if successful
        if result.get("success"):
            await db.update_project_stage(project_id, "4")
            
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


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
    """Returns the certification report and lineage for the project."""
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: 
            project_name = n

    service = GovernanceService()
    try:
        report = service.get_certification_report(project_name)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@router.get("/projects/{project_id}/export")
async def export_project_bundle(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Streams the project solution as a full governance ZIP bundle."""
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: 
            project_name = n

    service = GovernanceService()
    try:
        zip_buffer = service.create_export_bundle(project_name)
        filename = f"ShiftT_Solution_{project_name}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/x-zip-compressed",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
