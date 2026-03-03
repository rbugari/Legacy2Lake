"""
Reports Router - PRODUCTION READY
Handles PDF report generation for Triage and Final delivery reports.
Using synchronous endpoints via run_in_threadpool for Windows Playwright compatibility.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Dict, Any
import logging

from apps.api.services.report_service import report_service
from apps.api.services.persistence_service import SupabasePersistence
from apps.api.routers.dependencies import get_db
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

        # Ensure source_tech / target_tech are populated (get_project_metadata does not
        # extract them from settings the way list_projects does)
        _s = project.get('settings') or {}
        _c = project.get('config') or {}
        if not project.get('source_tech'):
            project['source_tech'] = (
                _s.get('source_tech') or _c.get('source_tech') or
                _c.get('origin_tech') or _s.get('detected_technology')
            )
        if not project.get('target_tech'):
            project['target_tech'] = (
                _s.get('target_tech') or _c.get('target_tech') or _c.get('dest_tech')
            )
        if not project.get('name'):
            project['name'] = _s.get('name') or project.get('project_name', 'Unknown')

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
        from apps.api.services.persistence_service import PersistenceService
        files = PersistenceService.get_project_files(project_id, tenant_id)
        
        if not files:
            logger.warning(f"No files found for project {project_id}")
            return []
        
        outputs = []
        
        # Files from R2 are already flat list with full paths
        for file in files:
            if isinstance(file, dict):
                # R2 storage returns dicts with 'name', 'path', 'type', etc.
                name = file.get('name', '')
                path = file.get('path', '')
                file_type = file.get('type', 'file')
                
                # Only include actual files, not folders
                if file_type != 'folder' and name:
                    outputs.append({
                        "name": name,
                        "path": path or name,
                        "type": "ARTIFACT"
                    })
            elif isinstance(file, str):
                # If it's just a string path
                outputs.append({
                    "name": file.split('/')[-1],
                    "path": file,
                    "type": "ARTIFACT"
                })
        
        logger.info(f"Found {len(outputs)} artifacts for project {project_id}")
        return outputs
    except Exception as e:
        logger.error(f"Error collecting outputs: {e}", exc_info=True)
        return []
