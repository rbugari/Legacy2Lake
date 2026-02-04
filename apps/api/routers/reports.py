"""
Reports Router - PRODUCTION READY
Handles PDF report generation for Triage and Final delivery reports.
Using synchronous endpoints via run_in_threadpool for Windows Playwright compatibility.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Dict, Any
import logging

from services.report_service import report_service
from services.persistence_service import SupabasePersistence
from routers.dependencies import get_db
from fastapi.concurrency import run_in_threadpool

router = APIRouter(prefix="/projects", tags=["Reports"])
logger = logging.getLogger("ReportsRouter")

@router.post("/{project_id}/reports/triage")
async def generate_triage_report(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """Generates a PDF Discovery Analysis Report (Post-Triage)."""
    try:
        logger.info(f"Generating Triage Report for project: {project_id}")
        
        # 1. Fetch data
        project = await db.get_project_metadata(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        assets = await db.get_project_assets(project_id)
        logger.info(f"Found {len(assets)} assets for project {project_id}")
        
        # 2. Generate PDF
        pdf_bytes = await run_in_threadpool(report_service.generate_triage_report, project, assets)
        
        if not pdf_bytes:
            logger.error(f"PDF generation returned empty bytes for project {project_id}")
            raise HTTPException(status_code=500, detail="Generated PDF is empty or corrupted")
        
        # 3. Format filename
        raw_name = project.get('name') or project.get('filename') or 'project'
        safe_name = "".join([c if c.isalnum() else "_" for c in raw_name]).lower()
        filename = f"{safe_name}_trieje_report.pdf"
        
        logger.info(f"Successfully generated PDF: {filename} ({len(pdf_bytes)} bytes)")
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Suggested-Filename": filename,
                "Access-Control-Expose-Headers": "Content-Disposition, X-Suggested-Filename"
            }
        )
        
    except HTTPException: raise
    except Exception as e:
        logger.exception(f"Unhandled error in generate_triage_report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/reports/final")
async def generate_final_report(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """Generates a PDF Migration Delivery Report (Final Handover)."""
    try:
        logger.info(f"Generating Final Report for project: {project_id}")
        
        # 1. Fetch data
        project = await db.get_project_metadata(project_id)
        assets = await db.get_project_assets(project_id)
        
        # Mock/derived data
        outputs = _get_generated_outputs(project_id, db.tenant_id)
        timeline = {"phase": "Complete", "delivery": "Final"}
        
        # 2. Generate PDF
        pdf_bytes = await run_in_threadpool(report_service.generate_final_report, project, assets, outputs, timeline)
        
        if not pdf_bytes:
            raise HTTPException(status_code=500, detail="Generated PDF is empty")
            
        # 3. Format filename
        raw_name = project.get('name') or 'project'
        safe_name = "".join([c if c.isalnum() else "_" for c in raw_name]).lower()
        filename = f"{safe_name}_final_report.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Suggested-Filename": filename
            }
        )
        
    except Exception as e:
        logger.exception(f"Error in generate_final_report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_generated_outputs(project_id: str, tenant_id: str) -> list:
    """Helper to collect files for the final report"""
    try:
        from services.persistence_service import PersistenceService
        files = PersistenceService.get_project_files(project_id, tenant_id)
        outputs = []
        def collect(nodes, path=""):
            for n in nodes:
                if n.get("type") == "folder": collect(n.get("children", []), f"{path}/{n['name']}")
                else: outputs.append({"name": n["name"], "path": f"{path}/{n['name']}", "type": "ARTIFACT"})
        collect(files)
        return outputs
    except: return []
