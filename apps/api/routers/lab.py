from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import FileResponse
import os
from typing import Dict, Any, List, Optional
from apps.api.routers.dependencies import get_db
from apps.api.services.persistence_service import SupabasePersistence
from apps.api.services.prompt_lab_service import PromptLabService

router = APIRouter(prefix="/lab", tags=["Lab"])

@router.post("/export")
async def export_prompts(db: SupabasePersistence = Depends(get_db)):
    lab = PromptLabService(tenant_id=db.tenant_id, client_id=db.client_id)
    return await lab.export_to_lab()

@router.post("/import")
async def import_prompt(prompt_id: str, lab_path: str, db: SupabasePersistence = Depends(get_db)):
    # Note: frontend seems to pass these as query params based on admin/page.tsx:152
    lab = PromptLabService(tenant_id=db.tenant_id, client_id=db.client_id)
    return await lab.import_from_lab(prompt_id, lab_path)

@router.post("/activate")
async def activate_prompt_v(prompt_id: str, version: int, db: SupabasePersistence = Depends(get_db)):
    # Note: frontend passes as query params admin/page.tsx:141
    lab = PromptLabService(tenant_id=db.tenant_id, client_id=db.client_id)
    return await lab.activate_version(prompt_id, version)

@router.get("/versions/{prompt_id}")
async def list_prompt_versions(prompt_id: str, db: SupabasePersistence = Depends(get_db)):
    lab = PromptLabService(tenant_id=db.tenant_id, client_id=db.client_id)
    versions = await lab.list_versions(prompt_id)
    return {"versions": versions}

@router.get("/download")
async def download_lab_zip():
    zip_path = os.path.abspath("./prompt_lab_export.zip")
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Export ZIP not found. Run export first.")
    
    return FileResponse(
        zip_path, 
        media_type="application/zip", 
        filename="prompt_lab_export.zip"
    )

@router.get("/prompts/enriched")
async def get_enriched_prompt(
    agent_id: str,
    origin_tech: Optional[str] = None,
    dest_tech: Optional[str] = None,
    db: SupabasePersistence = Depends(get_db)
):
    """Returns an enriched prompt for a specific agent and technology stack."""
    lab = PromptLabService(tenant_id=db.tenant_id, client_id=db.client_id)
    prompt = lab.get_enriched_prompt(
        agent_name=agent_id,
        origin_tech=origin_tech,
        dest_tech=dest_tech
    )
    return prompt
