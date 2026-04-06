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
from apps.api.services.reports_catalog_service import ReportsCatalogService
from datetime import datetime

router = APIRouter(prefix="/projects", tags=["Reports"])
logger = logging.getLogger("ReportsRouter")

@router.get("/reports/catalog")
async def list_reports_catalog(
    stage: int | None = None,
    category: str | None = None,
    product_line: str | None = None,
    audience: str | None = None,
    report_type: str | None = None,
):
    """List all available reports with optional filtering."""
    try:
        reports = ReportsCatalogService.get_all_reports(
            stage=stage,
            category=category,
            product_line=product_line,
            audience=audience,
            report_type=report_type
        )
        return {
            "reports": reports,
            "count": len(reports),
            "filters_applied": {
                "stage": stage,
                "category": category,
                "product_line": product_line,
                "audience": audience,
                "report_type": report_type,
            }
        }
    except Exception as e:
        logger.exception(f"Error listing reports catalog: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/catalog/{report_id}")
async def get_report_metadata(report_id: str):
    """Get metadata for a specific report."""
    try:
        report = ReportsCatalogService.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found in catalog")
        return {"report": report}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving report metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/catalog-summary")
async def get_catalog_summary():
    """Get overall catalog statistics and schema."""
    try:
        summary = ReportsCatalogService.get_catalog_summary()
        return {"summary": summary}
    except Exception as e:
        logger.exception(f"Error getting catalog summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@router.get("/{project_id}/reports/schema-intelligence")
async def get_schema_intelligence_report(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """Returns schema intelligence data (PK/FK detection, column profiling, PII flags)."""
    try:
        assets = await db.get_project_assets(project_id)
        if not assets:
            return {
                "project_id": project_id,
                "generated_at": str(datetime.now()),
                "asset_count": 0,
                "schema_stats": {
                    "pk_count": 0, "fk_count": 0, "detection_rate": 0,
                    "total_columns": 0, "assets_with_schema": 0, "column_profiles": []
                }
            }
        schema_stats = await run_in_threadpool(report_service._calculate_schema_stats, assets)
        return {
            "project_id": project_id,
            "generated_at": str(datetime.now()),
            "asset_count": len(assets),
            "schema_stats": schema_stats,
        }
    except Exception as e:
        logger.exception(f"Error fetching schema intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/reports/forensic-assessment")
async def get_forensic_assessment_report(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """Returns forensic assessment from quick_assessment or scout_assessment."""
    try:
        project = await db.get_project_metadata(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        settings = project.get('settings') or {}
        scout_data = settings.get('scout_assessment') or {}
        if scout_data and (scout_data.get('completeness_score') or scout_data.get('assessment_summary')):
            return {"project_id": project_id, "source": "scout_assessment",
                    "generated_at": str(datetime.now()), "assessment": scout_data}

        qa = project.get('quick_assessment') or {}
        if not qa:
            return {"project_id": project_id, "generated_at": str(datetime.now()),
                    "assessment": None,
                    "message": "No forensic assessment yet. Run Discovery Forensic Scan first."}

        blockers = qa.get('blockers') or []
        gaps = [{"category": "Blocker", "gap_description": b, "impact": "HIGH", "suggested_file": None}
                for b in blockers if isinstance(b, str) and b.strip()]
        techs = qa.get('detected_techs') or []
        return {
            "project_id": project_id,
            "generated_at": str(datetime.now()),
            "source": "quick_assessment",
            "assessment": {
                "completeness_score": qa.get('score', 0),
                "detected_technology": ', '.join(techs) if techs else None,
                "assessment_summary": (
                    qa.get('llm_opinion') or
                    f"Quick Assessment: viability {qa.get('score', 0)}/100 ({qa.get('semaforo', 'yellow')}). "
                    f"{len(qa.get('file_details') or [])} files analyzed."
                ),
                "detected_gaps": gaps,
                "blockers_count": len(blockers),
                "file_breakdown": qa.get('file_breakdown') or {},
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching forensic assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))
