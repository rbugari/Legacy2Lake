"""
Projects Router
Handles CRUD operations, settings, layout, and lifecycle management for projects.
Migrated from main.py for better modularity.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import hashlib
import os
import io
import json
import zipfile
import time

from apps.api.services.persistence_service import SupabasePersistence, PersistenceService
from apps.api.services.quick_assessment_service import QuickAssessmentService, QuickAssessmentResult
from apps.api.services.table_impact_service import TableImpactService, TableSummary, TableDetail, DependencyDAG
from apps.api.services.knowledge_packet_service import KnowledgePacketService, KnowledgePacket
from apps.api.services.project_cleanup_service import ProjectCleanupService
from apps.api.services.discovery_service import DiscoveryService
from apps.api.services.readiness_service import ReadinessService
from apps.api.services.executive_summary_service import ExecutiveSummaryService
from apps.api.services.understanding_service import UnderstandingService
from apps.api.routers.dependencies import get_db, get_identity
from apps.api.utils.logger import logger

router = APIRouter(prefix="/projects", tags=["Projects"])


def _build_evidence_review_key(record: Dict[str, Any]) -> str:
    basis = "|".join([
        str(record.get("source_path", "")),
        str(record.get("line_start", "")),
        str(record.get("line_end", "")),
        str(record.get("parser_name", "")),
        str(record.get("snippet", ""))[:2000],
    ])
    return hashlib.sha1(basis.encode("utf-8", errors="ignore")).hexdigest()


async def _resolve_project_uuid(db: SupabasePersistence, project_id: str) -> str:
    if "-" in project_id:
        return project_id

    resolved = await db.get_project_id_by_name(project_id)
    return resolved or project_id


def _validate_understanding_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate mandatory contract fields for understanding rebuild responses."""
    if not isinstance(payload, dict):
        raise ValueError("understanding payload must be an object")

    required_top_level = {
        "generated_at",
        "version",
        "project_id",
        "functional_map",
        "operational_map",
        "recommendation_set",
        "rule_candidate_summary",
    }
    missing = sorted(required_top_level.difference(payload.keys()))
    if missing:
        raise ValueError(f"understanding payload missing keys: {', '.join(missing)}")

    if not payload.get("generated_at"):
        raise ValueError("understanding payload generated_at is required")

    section_to_collection = {
        "functional_map": "domains",
        "operational_map": "processes",
        "recommendation_set": "items",
        "rule_candidate_summary": "candidates",
    }
    for section, required_collection in section_to_collection.items():
        section_payload = payload.get(section)
        if not isinstance(section_payload, dict):
            raise ValueError(f"understanding section {section} must be an object")
        if required_collection not in section_payload:
            raise ValueError(
                f"understanding section {section} missing {required_collection}"
            )

    return payload


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


# --- Quick Assessment (Phase A) ---

@router.post("/{project_id}/quick-assessment", response_model=QuickAssessmentResult)
async def run_quick_assessment(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Runs Quick Assessment on project (Phase A).
    
    Performs hybrid evaluation (deterministic + optional LLM opinion):
    - Classifies files by category (migrable, support, documentation, unrecognized)
    - Calculates viability score (0-100)
    - Assigns semaphore (green/yellow/red)
    - Detects technologies
    - Identifies blockers if red
    - Gets optional LLM professional opinion
    
    Returns:
        QuickAssessmentResult with complete evaluation
    """
    try:
        started_at = time.perf_counter()
        logger.info(
            f"[QuickAssessment] START project_id={project_id}, tenant_id={db.tenant_id}",
            "QuickAssessment",
        )

        service = QuickAssessmentService(tenant_id=db.tenant_id, client_id=db.client_id)
        result = await service.assess(project_id)
        
        # Save result to database (updated_at auto-updated by trigger)
        db.client.table("utm_projects").update({
            "quick_assessment": result.dict()
        }).eq("project_id", project_id).execute()

        # Keep readiness in sync with the new assessment signal.
        try:
            readiness_service = ReadinessService(tenant_id=db.tenant_id, client_id=db.client_id)
            await readiness_service.compute_and_persist(project_id)
        except Exception as readiness_error:
            logger.warning(
                f"[Readiness] Auto-recompute after quick assessment failed: {readiness_error}",
                "Readiness"
            )

        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            (
                f"[QuickAssessment] TERMINO OK project_id={project_id}, "
                f"score={result.score}, semaforo={result.semaforo}, elapsed_ms={elapsed_ms}"
            ),
            "QuickAssessment",
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")


@router.get("/{project_id}/quick-assessment")
async def get_quick_assessment(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Retrieves saved Quick Assessment result for project.
    
    Returns:
        Stored QuickAssessmentResult or 404 if not found
    """
    try:
        response = db.client.table("utm_projects").select("quick_assessment").eq("project_id", project_id)
        
        if db.tenant_id:
            response = response.eq("tenant_id", db.tenant_id)
        
        result = response.execute()
        
        if not result.data or not result.data[0].get("quick_assessment"):
            raise HTTPException(
                status_code=404,
                detail="Quick Assessment not found. Run POST /{project_id}/quick-assessment first."
            )
        
        return result.data[0]["quick_assessment"]
    
    except HTTPException:
        raise


# --- Readiness + Confidence Model (Sprint 1) ---

@router.get("/{project_id}/readiness")
async def get_readiness(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Returns the persisted readiness summary for the project.
    If not yet computed, triggers a fresh computation automatically.
    """
    svc = ReadinessService(tenant_id=db.tenant_id, client_id=db.client_id)
    payload = await svc.get_readiness(project_id)
    if payload:
        return payload
    # Auto-compute on first access
    try:
        return await svc.compute_and_persist(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.warning(f"[Readiness] Auto-compute failed: {e}", "Readiness")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/readiness/recompute")
async def recompute_readiness(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Forces a fresh recomputation of the readiness summary and persists the result.
    """
    svc = ReadinessService(tenant_id=db.tenant_id, client_id=db.client_id)
    try:
        return await svc.compute_and_persist(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[Readiness] Recompute failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Executive Summary + Gaps (Sprint 2) ---

@router.get("/{project_id}/executive-summary")
async def get_executive_summary(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Returns a business-facing executive summary derived from all project signals.
    Computed on demand — no DB storage in first pass.
    """
    svc = ExecutiveSummaryService(tenant_id=db.tenant_id, client_id=db.client_id)
    try:
        return await svc.get_executive_summary(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[ExecutiveSummary] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/gaps-summary")
async def get_gaps_summary(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Returns a grouped summary of identified gaps derived from triage, assessment, and validation signals.
    """
    svc = ExecutiveSummaryService(tenant_id=db.tenant_id, client_id=db.client_id)
    try:
        return await svc.get_gaps_summary(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[GapsSummary] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/file-inventory")
async def get_file_inventory(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Returns file inventory from Discovery with SUGGESTED classification.
    This happens BEFORE Triage creates utm_objects.
    
    Purpose: Usuario ve QUÉ hay, sistema SUGIERE cómo tratarlo, usuario AJUSTA.
    
    Returns:
        {
            "success": true,
            "file_count": 50,
            "files": [
                {
                    "name": "Load_Customer.dtsx",
                    "path": "Triage/Load_Customer.dtsx",
                    "size": 45678,
                    "category": "migrable",
                    "detected_tech": "ssis",
                    "suggested_classification": "CORE",  # Sistema sugiere CORE para migrables
                    "include": true  # Default: incluir migrables y soporte
                },
                {
                    "name": "DB_Schema.sql",
                    "category": "soporte",
                    "suggested_classification": "SUPPORT",  # Soporte para contexto
                    "include": true
                },
                {
                    "name": "README.md",
                    "category": "documentacion",
                    "suggested_classification": "IGNORED",  # Docs no aportan a migración
                    "include": false
                }
            ]
        }
    """
    try:
        # Get project name for manifest generation
        project_uuid = project_id
        project_name = project_id
        
        # Try to get project name from database
        try:
            response = db.client.table("utm_projects").select("name").eq("project_id", project_id)
            if db.tenant_id:
                response = response.eq("tenant_id", db.tenant_id)
            result = response.execute()
            if result.data and len(result.data) > 0:
                project_name = result.data[0].get("name", project_id)
        except Exception as e:
            logger.warning(f"Could not fetch project name: {e}")
        
        # Generate manifest (synchronous call)
        manifest = DiscoveryService.generate_manifest(
            project_id=project_name,
            tenant_id=db.tenant_id,
            user_context=None,
            source_folder=PersistenceService.STAGE_SOURCE
        )
        
        if not manifest or "file_inventory" not in manifest:
            raise HTTPException(
                status_code=404,
                detail="No file inventory found. Upload files to Triage folder first."
            )

        project_settings = await db.get_project_settings(project_id) or {}
        saved_pre_classification = project_settings.get("pre_classification", {}) if isinstance(project_settings, dict) else {}
        if not isinstance(saved_pre_classification, dict):
            saved_pre_classification = {}
        
        # Transform file_inventory with SUGGESTED classification
        qa_service = QuickAssessmentService(tenant_id=db.tenant_id, client_id=db.client_id)
        files = []
        
        for item in manifest["file_inventory"]:
            file_category, detected_tech = qa_service._classify_file(item)
            
            # SUGGESTED classification logic:
            # - migrable → CORE (analizar profundo para migrar)
            # - soporte → SUPPORT (consultar para completar datos de CORE)
            # - documentacion → IGNORED (no aporta conocimiento técnico)
            # - no_reconocido → IGNORED (no se puede procesar)
            
            if file_category == "migrable":
                suggested = "CORE"
                include_default = True
            elif file_category == "soporte":
                suggested = "SUPPORT"
                include_default = True
            else:  # documentacion, no_reconocido
                suggested = "IGNORED"
                include_default = False

            override = saved_pre_classification.get(item["path"], {}) if isinstance(saved_pre_classification, dict) else {}
            if not isinstance(override, dict):
                override = {}

            classification = override.get("classification", suggested)
            include = override.get("include", include_default)
            
            files.append({
                "name": item["name"],
                "path": item["path"],
                "size": item.get("size", 0),
                "lines": item.get("lines", 0),
                "category": file_category,  # migrable, soporte, documentacion, no_reconocido
                "detected_tech": detected_tech,
                "suggested_classification": suggested,  # CORE, SUPPORT, IGNORED
                "classification": classification,
                "include": include,
                "has_override": bool(override),
                "classification_source": "manual" if override else "suggested",
                "signatures": item.get("signatures", [])
            })
        
        return {
            "success": True,
            "file_count": len(files),
            "files": files
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file inventory: {str(e)}")


@router.post("/{project_id}/pre-classification")
async def save_pre_classification(
    project_id: str,
    payload: Dict[str, Any],
    db: SupabasePersistence = Depends(get_db)
):
    """
    Guarda la clasificación ajustada por el usuario en Discovery.
    
    Payload:
        {
            "classification": {
                "Triage/Load_Customer.dtsx": {
                    "classification": "CORE",
                    "include": true
                },
                "Triage/README.md": {
                    "classification": "IGNORED",
                    "include": false
                }
            }
        }
    
    Este "mapa" se usará en Triage para optimizar la profundización.
    """
    try:
        classification = payload.get("classification", {})
        
        # Helper: Determine project name to locate files
        project_name = project_id
        try:
            name_resp = db.client.table("utm_projects").select("name").eq("project_id", project_id)
            if db.tenant_id:
                name_resp = name_resp.eq("tenant_id", db.tenant_id)
            result = name_resp.execute()
            if result.data and len(result.data) > 0:
                project_name = result.data[0].get("name", project_id)
        except Exception as e:
            logger.warning(f"Could not fetch project name in pre-classification: {e}")

        # Guardar en project settings (método simple)
        current_settings = await db.get_project_settings(project_id) or {}
        current_settings["pre_classification"] = classification
        current_settings["pre_classification_updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.update_project_settings(project_id, current_settings)

        # Copiar los archivos clasificados como CORE/SUPPORT desde source a triage
        storage = PersistenceService.get_storage()
        project_base = PersistenceService.ensure_solution_dir(project_name, tenant_id=db.tenant_id)
        
        import shutil
        import os

        triage_folder_key = f"{project_base.rstrip('/')}/{PersistenceService.STAGE_TRIAGE}"
        # Rebuild the destination folder on every save so reruns do not keep stale files.
        storage.delete_directory(triage_folder_key)
        storage.ensure_directory(triage_folder_key)

        copied_count = 0
        for file_path, data in classification.items():
            if data.get("include", False) or data.get("classification") in ["CORE", "SUPPORT"]:
                src_fs_path = storage.resolve_absolute_path(file_path)
                if src_fs_path and os.path.exists(src_fs_path):
                    # Extract relative to project_base
                    # file_path is like tenant/project_name/source/file.sql
                    # project_base is like tenant/project_name

                    # We remove project_base prefix
                    if file_path.startswith(project_base):
                        rel_to_project = file_path[len(project_base):].lstrip('/')
                        parts = rel_to_project.split('/')
                        # Force the outer folder to be 'triage' (STAGE_TRIAGE)
                        if len(parts) > 1:
                            parts[0] = PersistenceService.STAGE_TRIAGE
                            new_rel = '/'.join(parts)

                            dst_file_path = f"{project_base.rstrip('/')}/{new_rel}"
                            dst_fs_path = storage.resolve_absolute_path(dst_file_path)

                            if src_fs_path != dst_fs_path:
                                os.makedirs(os.path.dirname(dst_fs_path), exist_ok=True)
                                shutil.copy2(src_fs_path, dst_fs_path)
                                copied_count += 1
        
        logger.info(f"Copied {copied_count} selected files to triage folder.")

        try:
            readiness_service = ReadinessService(tenant_id=db.tenant_id, client_id=db.client_id)
            await readiness_service.compute_and_persist(project_id)
        except Exception as readiness_error:
            logger.warning(
                f"[Readiness] Auto-recompute after pre-classification failed: {readiness_error}",
                "Readiness"
            )

        return {
            "success": True,
            "message": f"Pre-classification saved and {copied_count} files moved to Triage."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save pre-classification: {str(e)}")


@router.get("/{project_id}/evidence")
async def get_project_evidence(
    project_id: str,
    limit: int = 50,
    db: SupabasePersistence = Depends(get_db)
):
    """Returns project evidence items with persisted review state from project settings."""
    try:
        resolved_project_id = await _resolve_project_uuid(db, project_id)
        settings = await db.get_project_settings(project_id) or {}
        review_map = settings.get("evidence_review", {}) if isinstance(settings, dict) else {}
        if not isinstance(review_map, dict):
            review_map = {}

        try:
            query = db.client.table("utm_evidence_items").select("*").eq("project_id", resolved_project_id)
            if db.tenant_id:
                query = query.eq("tenant_id", db.tenant_id)
            result = query.execute()
            rows = result.data or []
        except Exception as query_error:
            logger.warning(
                f"[Evidence] Falling back to empty evidence set for project {project_id}: {query_error}"
            )
            rows = []

        rows = sorted(rows, key=lambda row: row.get("created_at", ""), reverse=True)[:limit]

        items = []
        for row in rows:
            review_key = _build_evidence_review_key(row)
            review_state = review_map.get(review_key, {}) if isinstance(review_map, dict) else {}
            if not isinstance(review_state, dict):
                review_state = {}

            items.append({
                **row,
                "review_key": review_key,
                "review_status": review_state.get("state", "detected"),
                "review_note": review_state.get("note"),
                "review_updated_at": review_state.get("updated_at"),
            })

        summary = {
            "detected": len([item for item in items if item.get("review_status") == "detected"]),
            "reviewed": len([item for item in items if item.get("review_status") == "reviewed"]),
            "pinned": len([item for item in items if item.get("review_status") == "pinned"]),
            "dismissed": len([item for item in items if item.get("review_status") == "dismissed"]),
        }

        return {
            "success": True,
            "count": len(items),
            "items": items,
            "summary": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load evidence: {str(e)}")


@router.patch("/{project_id}/evidence/review")
async def update_project_evidence_review(
    project_id: str,
    payload: Dict[str, Any],
    db: SupabasePersistence = Depends(get_db)
):
    """Persists review state for a single evidence item in project settings."""
    try:
        review_key = payload.get("review_key")
        state = payload.get("state", "reviewed")
        note = payload.get("note")

        if not review_key:
            raise HTTPException(status_code=400, detail="review_key is required")

        current_settings = await db.get_project_settings(project_id) or {}
        evidence_review = current_settings.get("evidence_review", {}) if isinstance(current_settings, dict) else {}
        if not isinstance(evidence_review, dict):
            evidence_review = {}

        evidence_review[review_key] = {
            "state": state,
            "note": note,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        current_settings["evidence_review"] = evidence_review
        await db.update_project_settings(project_id, current_settings)

        return {
            "success": True,
            "review_key": review_key,
            "state": state,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update evidence review: {str(e)}")


# --- Table Impact Analysis (Phase C) ---

@router.post("/{project_id}/table-impacts/analyze")
async def analyze_table_impacts(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Analyzes table impacts for all assets in project (Phase C).
    
    Extracts from each asset:
    - Which tables it reads from (SELECT)
    - Which tables it writes to (INSERT, UPDATE, DELETE, MERGE)
    - Which columns are affected
    - Access patterns (FULL_LOAD, INCREMENTAL, LOOKUP, etc.)
    
    Stores results in utm_table_impacts table.
    
    Returns:
        Analysis summary with stats
    """
    try:
        service = TableImpactService(
            project_id=project_id,
            tenant_id=db.tenant_id,
            client_id=db.client_id
        )
        
        result = await service.analyze_impacts()
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{project_id}/tables/summary", response_model=List[TableSummary])
async def get_tables_summary(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Returns summary of all tables in project with impact counts.
    
    For each table shows:
    - Number of readers (assets that SELECT from it)
    - Number of writers (assets that INSERT/UPDATE/DELETE)
    - Total impacts
    - Operations detected
    
    Sorted by total impact count (descending).
    
    Returns:
        List of TableSummary objects
    """
    try:
        service = TableImpactService(
            project_id=project_id,
            tenant_id=db.tenant_id,
            client_id=db.client_id
        )
        
        return await service.get_table_summary()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/{project_id}/tables/{table_name}/detail", response_model=TableDetail)
async def get_table_detail(
    project_id: str,
    table_name: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Returns detailed impacts on a specific table.
    
    Shows:
    - All readers (assets that SELECT, with SQL and columns)
    - All writers (assets that INSERT/UPDATE/DELETE, with operations and columns)
    - Notes about potential conflicts (e.g., multiple writers on same columns)
    
    Args:
        table_name: Full table name (schema.table or table)
    
    Returns:
        TableDetail with readers and writers lists
    """
    try:
        service = TableImpactService(
            project_id=project_id,
            tenant_id=db.tenant_id,
            client_id=db.client_id
        )
        
        return await service.get_table_detail(table_name)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get detail: {str(e)}")


@router.get("/{project_id}/dependency-dag", response_model=DependencyDAG)
async def get_dependency_dag(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Builds asset dependency DAG based on table impacts.
    
    Logic:
    - If Asset A writes to table X
    - And Asset B reads from table X
    - Then: B depends on A (A must execute before B)
    
    Returns:
        DependencyDAG with:
        - nodes: list of all assets
        - edges: dependency relationships [{from, to, via}, ...]
        - execution_order: [[level0], [level1], ...] topologically sorted
        - cycles: any circular dependencies detected
    """
    try:
        service = TableImpactService(
            project_id=project_id,
            tenant_id=db.tenant_id,
            client_id=db.client_id
        )
        
        return await service.build_dependency_dag()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build DAG: {str(e)}")


# --- Knowledge Packet (Phase B - Librarian) ---

@router.get("/{project_id}/assets/{asset_id}/knowledge", response_model=KnowledgePacket)
async def get_asset_knowledge(
    project_id: str,
    asset_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Returns consolidated knowledge packet for a specific asset (Phase B).
    
    Consolidates data from 6 silos:
    1. utm_objects.metadata (SSIS components)
    2. utm_asset_columns (profiled columns with types)
    3. schema_reference.json (DDL types from Discovery)
    4. utm_origin_analysis_columns (Sprint 8.5 - source intelligence)
    5. utm_column_mappings (explicit source→target mappings)
    6. utm_solution_context (business rules and notes)
    
    Type resolution priority: DDL > profiled > metadata > "STRING"
    
    Key features:
    - SSIS↔DDL cross-linking (matches SSIS table names with DDL schemas)
    - PII detection (from profiling + heuristics)
    - Source intelligence (SqlCommand, transformations, connections)
    - Column-level metadata (types, nullability, PK/FK, cardinality)
    
    Returns:
        KnowledgePacket with complete asset context for code generation
    """
    try:
        service = KnowledgePacketService(
            tenant_id=db.tenant_id,
            project_id=project_id
        )
        
        packet = await service.get_packet(asset_id)
        return packet
    
    except ValueError as e:
        # Asset not found
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build knowledge packet: {str(e)}")


@router.get("/{project_id}/knowledge/scan")
async def scan_project_knowledge(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Scans entire project and returns knowledge consolidation summary.
    
    Used by Triage Pipeline v2 (Phase D) to enrich manifest with:
    - schema_reference.json metadata
    - Asset type coverage (DDL types vs profiled vs fallback)
    - PII detection summary
    - Data quality indicators
    
    This endpoint is called after Discovery phase to provide
    enriched context to Agent A during Triage.
    
    Returns:
        {
            "total_assets": 12,
            "assets_with_ddl_types": 8,
            "assets_with_profiled_types": 10,
            "pii_columns_detected": 15,
            "schema_reference": {...},
            "summary": "8/12 assets have DDL types..."
        }
    """
    try:
        service = KnowledgePacketService(
            tenant_id=db.tenant_id,
            project_id=project_id
        )
        
        scan_result = await service.scan_project(project_id)
        return scan_result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


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
async def reset_project(
    project_id: str, 
    backup: bool = True,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Reset project to initial state (post-upload).
    
    What this does:
    1. Creates ZIP backup of all generated files in drafting/refinement/certification/handover (optional)
    2. Deletes ONLY generated stages (preserves original Triage files)
    3. Clears generated code from database
    4. Resets project to DISCOVERY stage
    
    IMPORTANT: Original uploaded files in Triage folder are PRESERVED.
    
    Args:
        project_id: Project UUID or name
        backup: If True, creates ZIP backup before cleanup (default: True)
    
    Returns:
        Reset results with backup location and detailed cleanup info
    """
    try:
        # Resolve project UUID if name provided
        project_uuid = project_id
        if "-" not in project_id:
            resolved = await db.get_project_id_by_name(project_id)
            if resolved:
                project_uuid = resolved
        
        # Use ProjectCleanupService for complete reset
        cleanup_service = ProjectCleanupService(tenant_id=db.tenant_id, project_id=project_uuid)
        result = await cleanup_service.reset_project(backup=backup)
        
        # Check for errors
        if result.get("errors"):
            logger.warning(f"[Reset] Completed with warnings: {result['errors']}", "Reset")
        
        return {
            "success": True,
            "message": f"Project reset successfully. {len(result['stages_cleaned'])} stages cleaned, "
                      f"{result['files_removed']} files removed. All detected assets deleted. "
                      f"Original uploaded files in Triage folder preserved.",
            "backup_created": result["backup_created"],
            "backup_path": result.get("backup_path"),
            "stages_cleaned": result["stages_cleaned"],
            "files_removed": result["files_removed"],
            "database_reset": result["database_reset"],
            "errors": result.get("errors", [])
        }
    
    except Exception as e:
        logger.error(f"[Reset] Failed: {e}", "Reset")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@router.get("/{project_id}/backups")
async def list_project_backups(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    List all backup ZIP files for a project.
    
    Returns:
        List of backup files with name, size, and created date
    """
    try:
        # Resolve project UUID if name provided
        project_uuid = project_id
        if "-" not in project_id:
            resolved = await db.get_project_id_by_name(project_id)
            if resolved:
                project_uuid = resolved
        
        cleanup_service = ProjectCleanupService(tenant_id=db.tenant_id, project_id=project_uuid)
        backups = await cleanup_service.list_backups()
        
        return {
            "success": True,
            "backups": backups,
            "count": len(backups)
        }
    
    except Exception as e:
        logger.error(f"[Backups] List failed: {e}", "Backups")
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.delete("/{project_id}/backups/{backup_filename}")
async def delete_project_backup(
    project_id: str,
    backup_filename: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Delete a specific backup ZIP file.
    
    Args:
        project_id: Project UUID or name
        backup_filename: Name of the backup file to delete
    
    Returns:
        Success status
    """
    try:
        # Resolve project UUID if name provided
        project_uuid = project_id
        if "-" not in project_id:
            resolved = await db.get_project_id_by_name(project_id)
            if resolved:
                project_uuid = resolved
        
        cleanup_service = ProjectCleanupService(tenant_id=db.tenant_id, project_id=project_uuid)
        result = await cleanup_service.delete_backup(backup_filename)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error", "Backup not found"))
        
        return {
            "success": True,
            "message": f"Backup '{backup_filename}' deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Backups] Delete failed: {e}", "Backups")
        raise HTTPException(status_code=500, detail=f"Failed to delete backup: {str(e)}")


@router.patch("/{project_id}/settings")
async def update_project_settings(project_id: str, settings: Dict[str, Any], db: SupabasePersistence = Depends(get_db)):
    """Updates project-level settings (e.g. Source/Target Tech)."""
    success = await db.update_project_settings(project_id, settings)

    if success and any(key in settings for key in ("source_tech", "target_tech", "discovery_intake")):
        try:
            readiness_service = ReadinessService(tenant_id=db.tenant_id, client_id=db.client_id)
            await readiness_service.compute_and_persist(project_id)
        except Exception as readiness_error:
            logger.warning(
                f"[Readiness] Auto-recompute after settings update failed: {readiness_error}",
                "Readiness"
            )

    return {"success": success}


@router.get("/{project_id}/settings")
async def get_project_settings(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Retrieves project-level settings."""
    return await db.get_project_settings(project_id) or {}


# [Sprint 2] Post-Drafting Mode Decision Gate
@router.post("/{project_id}/set-post-drafting-mode")
async def set_post_drafting_mode(
    project_id: str, 
    payload: Dict[str, str],
    db: SupabasePersistence = Depends(get_db)
):
    """
    Sets the post-Drafting mode for a project.
    Modes: 'drafting_delivery', 'structured_refinement', 'intelligent_reengineering'
    """
    mode = payload.get("mode", "").strip()
    if not mode:
        raise HTTPException(status_code=400, detail="Missing mode in payload")
    
    success = await db.set_post_drafting_mode(project_id, mode)
    if not success:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to set post_drafting_mode. Invalid project or mode: {mode}"
        )
    
    return {
        "success": True, 
        "project_id": project_id, 
        "post_drafting_mode": mode,
        "message": f"Post-Drafting mode set to: {mode}"
    }


@router.get("/{project_id}/get-post-drafting-mode")
async def get_post_drafting_mode(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """Retrieves the post-Drafting mode for a project (if set)."""
    mode = await db.get_post_drafting_mode(project_id)
    return {"post_drafting_mode": mode}


# --- Project Lifecycle ---



@router.post("/{project_id}/approve")
async def approve_triage(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Locks triage scope and opens Drafting without starting orchestration yet."""
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: 
            project_uuid = u

    success_status = await db.update_project_status(project_uuid, "TRIAGE_APPROVED")
    success_stage = await db.update_project_stage(project_uuid, "2")
    return {"success": success_status and success_stage, "status": "TRIAGE_APPROVED", "stage": "2"}


@router.post("/{project_id}/unlock")
async def unlock_triage(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Unlocks the project scope and transitions back to TRIAGE state."""
    project_uuid = project_id
    success_status = await db.update_project_status(project_uuid, "TRIAGE")
    success_stage = await db.update_project_stage(project_uuid, "1")
    return {"success": success_status and success_stage, "status": "TRIAGE"}


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
        "refinement": "REFINEMENT",
        "governance": "GOVERNANCE",
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

@router.get("/{project_id}/source/files")
async def list_source_files(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Lists all files in the project's Source folder for forensic analysis."""
    
    # Resolve project name if UUID provided
    project_folder = project_id
    if "-" in project_id:
        resolved_name = await db.get_project_name_by_id(project_id)
        if resolved_name:
            project_folder = resolved_name
    
    # Get Triage path
    # We use list_files mechanism
    print(f"[DEBUG] list_source_files called for project_id={project_id}, resolved={project_folder}, tenant={db.tenant_id}")
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
        
        # [v4.5] Robust Folder Detection (Align with DiscoveryService)
        # Find candidate folder case-insensitively
        candidate_names = [PersistenceService.STAGE_SOURCE.lower(), PersistenceService.STAGE_TRIAGE.lower(), "source", "triage", "inbound"]
        
        triage_node = None
        for n in all_files:
            if n["type"] == "folder" and n["name"].lower() in candidate_names:
                # If we find "source" or "triage", we use it. 
                # Prefer "source" if both exist (though unlikely)
                if not triage_node or n["name"].lower() == PersistenceService.STAGE_SOURCE.lower():
                    triage_node = n
        
        if not triage_node or (not triage_node.get("children") and triage_node.get("type") == "folder"):
             # Return empty if no triage/source folder or it's empty
             return {
                "success": True,
                "project_id": project_id,
                "source_path": PersistenceService.STAGE_SOURCE.capitalize(),
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
            "source_path": "Source", # Conceptual path
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


@router.post("/{project_id}/source/upload")
async def upload_triage_files(
    project_id: str,
    files: List[UploadFile] = File(...),
    db: SupabasePersistence = Depends(get_db)
):
    """Uploads one or many files to the project's Source directory."""
    # 1. Resolve project folder name (handles UUID or Name)
    project_folder = project_id
    if "-" in project_id:
        resolved_name = await db.get_project_name_by_id(project_id)
        if resolved_name:
            project_folder = resolved_name
            
    # 2. Upload to Storage (STAGE_SOURCE)
    project_base = PersistenceService.ensure_solution_dir(project_folder, db.tenant_id)
    triage_prefix = f"{project_base.rstrip('/')}/{PersistenceService.STAGE_SOURCE}"
    
    storage = PersistenceService.get_storage()
    
    uploaded_files = []
    try:
        for f in files:
            content = await f.read()
            file_key = f"{triage_prefix}/{f.filename}"
            storage.save_file(file_key, content)
            uploaded_files.append({
                "filename": f.filename,
                "size": len(content),
                "path": file_key
            })
            
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

@router.post("/{project_id}/source/promote")
async def promote_source_to_triage(
    project_id: str,
    payload: Dict[str, Any],
    db: SupabasePersistence = Depends(get_db)
):
    """
    Promotes selected files from Source to Triage for actual processing.
    
    Expected payload:
    {
        "classification": {
            "Source/Load_Customer.dtsx": {
                "include": true,
                "classification": "CORE"
            },
            "Source/README.md": {
                "include": false,
                "classification": "IGNORED" 
            }
        }
    }
    """
    project_folder = project_id
    if "-" in project_id:
        resolved_name = await db.get_project_name_by_id(project_id)
        if resolved_name:
            project_folder = resolved_name
            
    project_base = PersistenceService.ensure_solution_dir(project_folder, db.tenant_id)
    storage = PersistenceService.get_storage()
    
    classification = payload.get("classification", {})
    promoted_count = 0
    errors = []
    
    for file_path, data in classification.items():
        if data.get("include", False):
            try:
                # Need to read from source and write to triage
                # file_path is something like "Tenant/Project/source/filename.ext"
                # Extract filename
                filename = file_path.split("/")[-1]
                
                # Construct target path manually
                target_key = f"{project_base.rstrip('/')}/{PersistenceService.STAGE_TRIAGE}/{filename}"
                
                # Read from source
                content = storage.read_file(file_path)
                
                # Write to Triage
                storage.save_file(target_key, content)
                promoted_count += 1
                print(f"[Promotion] Copied {filename} to Triage")
            except Exception as e:
                print(f"[Promotion] Failed to promote {file_path}: {e}")
                errors.append(file_path)
                
    return {
        "success": len(errors) == 0,
        "promoted_count": promoted_count,
        "errors": errors if errors else None
    }

# --- Sidebar Metrics (Stage-Adaptive) ---

@router.get("/{project_id}/sidebar-metrics")
async def get_sidebar_metrics(
    project_id: str,
    stage: Optional[int] = None,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Returns stage-specific metrics for the sidebar navigation.
    Stages: 0=Discovery, 1=Triage, 2=Drafting, 3=Refinement, 4=Governance, 5=Handover
    """
    try:
        # Get project metadata
        project = await db.get_project_metadata(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Use provided stage or detect from project status
        current_stage = stage if stage is not None else _detect_stage_from_status(project.get("status", "DISCOVERY"))
        project_status = (project.get("status") or "DISCOVERY").upper()
        settings = project.get("settings") or {}
        governance_ready_statuses = {"CERTIFIED", "GOVERNED", "COMPLETED", "DELIVERED"}
        bundle_ready_statuses = {"CERTIFIED", "GOVERNED", "COMPLETED", "DELIVERED"}
        
        metrics = {}
        
        # Stage 0: Discovery
        if current_stage == 0:
            files = await db.get_project_files_from_db(project_id)
            metrics["fileCount"] = len(files)
            metrics["uploadStatus"] = project.get("status", "DISCOVERY")
        
        # Stage 1: Triage
        elif current_stage == 1:
            # Quick Assessment
            try:
                qa_service = QuickAssessmentService(tenant_id=db.tenant_id, client_id=db.client_id)
                qa_result = await qa_service.assess(project_id)
                metrics["quickAssessment"] = {
                    "score": qa_result.score,
                    "readability": 0, # Not available in QuickAssessmentResult
                    "complexity": 0,  # Not available in QuickAssessmentResult
                    "risk": qa_result.semaforo
                }
            except Exception as e:
                logger.warning(f"[SidebarMetrics] Quick assessment failed: {e}", "ProjectsRouter")
                metrics["quickAssessment"] = {"score": 0, "readability": 0, "complexity": 0, "risk": "unknown"}
            
            # Assets and Tables
            assets = await db.get_project_assets(project_id)
            metrics["assetCount"] = len(assets)
            
            try:
                impact_service = TableImpactService(project_id=project_id, tenant_id=db.tenant_id, client_id=db.client_id)
                summary = await impact_service.get_table_summary()
                metrics["tableCount"] = len(summary)
            except Exception as e:
                logger.warning(f"[SidebarMetrics] Table impact failed: {e}", "ProjectsRouter")
                metrics["tableCount"] = 0
            
            # Source/Target Tech
            try:
                tech_stats = await db.get_project_tech_stats(project_id)
                metrics["sourceTech"] = tech_stats.get("source_tech", "Unknown")
            except Exception as e:
                logger.warning(f"[SidebarMetrics] Tech stats failed: {e}", "ProjectsRouter")
                metrics["sourceTech"] = "Unknown"
            metrics["targetTech"] = project.get("target_technology", "Unknown")
            
            # Quality Metrics
            try:
                quality_stats = await db.get_quality_metrics_summary(project_id)
                metrics["qualityScore"] = quality_stats.get("avg_quality_score", 0)
                metrics["piiCount"] = quality_stats.get("pii_column_count", 0)
                metrics["partitionRecs"] = quality_stats.get("partitioned_table_count", 0)
            except Exception as e:
                logger.warning(f"[SidebarMetrics] Quality metrics failed: {e}", "ProjectsRouter")
                metrics["qualityScore"] = 0
                metrics["columnsWithPii"] = 0
                metrics["partitionedTables"] = 0
        
        # Stage 2: Drafting
        elif current_stage == 2:
            # Generation Progress
            exec_logs = await db.get_execution_logs(project_id, phase="MIGRATION")
            metrics["generationProgress"] = _calculate_progress_from_logs(exec_logs)
            metrics["currentAgent"] = _extract_current_agent(exec_logs)
            
            # Files Generated
            layout = await db.get_project_layout(project_id)
            nodes = layout.get("nodes", []) if layout else []
            bronze_count = sum(1 for n in nodes if n.get("layer") == "bronze")
            silver_count = sum(1 for n in nodes if n.get("layer") == "silver")
            gold_count = sum(1 for n in nodes if n.get("layer") == "gold")
            
            metrics["filesGenerated"] = len(nodes)
            metrics["bronzeNodes"] = bronze_count
            metrics["silverNodes"] = silver_count
            metrics["goldNodes"] = gold_count
        
        # Stage 3: Refinement
        elif current_stage == 3:
            # Refinement Status
            exec_logs = await db.get_execution_logs(project_id, phase="REFINEMENT")
            metrics["refinementStatus"] = project.get("status", "DRAFTED")
            
            # Code Quality
            try:
                validations = await db.get_code_validations(project_id)
                issue_count = sum(1 for v in validations if not v.get("is_valid", True))
                metrics["issueCount"] = issue_count
                metrics["validationCount"] = len(validations)
            except Exception as e:
                logger.warning(f"[SidebarMetrics] Validations failed: {e}", "ProjectsRouter")
                metrics["issueCount"] = 0
                metrics["validationCount"] = 0
            
            # Quality Delta (compare before/after)
            try:
                quality_stats = await db.get_quality_metrics_summary(project_id)
                metrics["qualityDelta"] = quality_stats.get("quality_delta", 0)
            except Exception as e:
                logger.warning(f"[SidebarMetrics] Quality delta failed: {e}", "ProjectsRouter")
                metrics["qualityDelta"] = 0
        
        # Stage 4: Governance
        elif current_stage == 4:
            # Documentation Status
            docs_generated = bool(settings.get("governance_report"))
            try:
                if not docs_generated:
                    governance_files = await db.get_governance_files(project_id)
                    docs_generated = len(governance_files) > 0
            except Exception as e:
                logger.warning(f"[SidebarMetrics] Governance files failed: {e}", "ProjectsRouter")
            metrics["docsGenerated"] = docs_generated or project_status in governance_ready_statuses
            metrics["bundleReady"] = project_status in bundle_ready_statuses

        # Stage 5: Handover
        elif current_stage == 5:
            docs_generated = bool(settings.get("governance_report"))
            try:
                if not docs_generated:
                    governance_files = await db.get_governance_files(project_id)
                    docs_generated = len(governance_files) > 0
            except Exception as e:
                logger.warning(f"[SidebarMetrics] Handover governance files failed: {e}", "ProjectsRouter")
            metrics["docsGenerated"] = docs_generated or project_status in governance_ready_statuses
            metrics["bundleReady"] = metrics["docsGenerated"] or project_status in bundle_ready_statuses
        
        # Common metrics (all stages)
        metrics["executionStatus"] = project.get("status", "DISCOVERY")
        metrics["lastUpdate"] = project.get("updated_at")
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SidebarMetrics] Failed to fetch metrics: {e}", "ProjectsRouter")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch sidebar metrics: {str(e)}")


def _detect_stage_from_status(status: str) -> int:
    """Map project status to stage number."""
    status_to_stage = {
        "DISCOVERY": 0, "UPLOADING": 0,
        "TRIAGE": 1, "PROCESSING": 1, "TRIAGED": 1,
        "TRIAGE_APPROVED": 2,
        "DRAFTING": 2, "ORCHESTRATING": 2, "DRAFTED": 2,
        "REFINEMENT": 3, "REFINING": 3, "REFINED": 3,
        "GOVERNANCE": 4, "DOCUMENTING": 4, "CERTIFYING": 4, "CERTIFIED": 4, "GOVERNED": 4,
        "COMPLETED": 5, "DELIVERED": 5,
    }
    return status_to_stage.get(status.upper(), 0)


def _calculate_progress_from_logs(logs: List[Dict]) -> int:
    """Estimate progress percentage from execution logs."""
    if not logs:
        return 0
    
    # Count agent mentions (A, C, F, G)
    agent_counts = {"A": 0, "C": 0, "F": 0, "G": 0}
    for log in logs:
        msg = log.get("log_message", "")
        for agent in ["Agent-A", "Agent-C", "Agent-F", "Agent-G"]:
            if agent in msg:
                agent_counts[agent.split("-")[1]] += 1
    
    # Estimate: A=10%, C=50%, F=80%, G=95%
    if agent_counts["G"] > 0:
        return 95
    elif agent_counts["F"] > 0:
        return 80
    elif agent_counts["C"] > 0:
        return 50 + min(agent_counts["C"], 30)
    elif agent_counts["A"] > 0:
        return 10 + min(agent_counts["A"], 20)
    return 5


def _extract_current_agent(logs: List[Dict]) -> Optional[str]:
    """Extract the most recent agent working from logs."""
    if not logs:
        return None
    
    latest = logs[0].get("log_message", "")
    for agent in ["Agent-G", "Agent-F", "Agent-C", "Agent-A"]:
        if agent in latest:
            return agent
    return None


def _classify_file_type(ext: str) -> str:
    """Helper to classify file types for Agent S."""
    if ext == 'dtsx': return 'SSIS_PACKAGE'
    if ext == 'sql': return 'SQL_SCRIPT'
    if ext in ['xml', 'config']: return 'CONFIG'
    if ext in ['json', 'yaml', 'yml']: return 'CONFIG'
    if ext == 'py': return 'PYTHON_SCRIPT'
    if ext in ['txt', 'md', 'doc', 'docx']: return 'DOCUMENTATION'
    return 'OTHER'


# --- Design Registry Endpoints (Sprint 14) ---

@router.get("/{project_id}/registry")
async def get_design_registry(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """Get Design Registry (utm_design_registry) for project."""
    try:
        registry = await db.get_design_registry(project_id)
        
        # Auto-initialize if empty (Sprint 14 - User Experience Fix)
        if not registry or len(registry) == 0:
            logger.info(f"[Registry] No registry found for project {project_id}, initializing defaults", "Registry")
            # Pass None so initialize_design_registry looks up project settings itself
            await db.initialize_design_registry(project_id, target_tech=None)
            registry = await db.get_design_registry(project_id)
        
        return {"registry": registry, "count": len(registry)}
    except Exception as e:
        logger.error(f"[Registry] Error fetching registry: {e}", "Registry")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/registry")
async def update_design_registry(
    project_id: str,
    payload: Dict[str, Any],
    db: SupabasePersistence = Depends(get_db)
):
    """Update a single Design Registry entry."""
    category = payload.get("category")
    key = payload.get("key")
    value = payload.get("value")
    
    if not category or not key:
        raise HTTPException(status_code=400, detail="category and key required")
    
    try:
        success = await db.update_design_registry(project_id, category, key, value)
        if success:
            return {"status": "updated", "category": category, "key": key}
        else:
            raise HTTPException(status_code=500, detail="Update failed")
    except Exception as e:
        logger.error(f"[Registry] Error updating registry: {e}", "Registry")
        raise HTTPException(status_code=500, detail=str(e))


# --- Generation Stats Endpoint (Sprint 14) ---

@router.get("/{project_id}/generation/stats")
async def get_generation_stats(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """Get generation statistics (GenerationStats component)."""
    try:
        # Query utm_objects for generation metrics (only migrable objects - ETL packages)
        query = db.client.table("utm_objects") \
            .select("object_id, generated_code, tech_id, layer, quality_score, validation_result, updated_at, category")
        
        if db.tenant_id:
            query = query.eq("tenant_id", db.tenant_id)
        
        query = query.eq("project_id", project_id).eq("category", "migrable")
        res = query.execute()
        
        objects = res.data if res.data else []
        
        # Calculate stats (only count migrable ETL packages)
        total_objects = len(objects)
        processed = sum(1 for obj in objects if obj.get("generated_code"))
        
        # Successful: has generated code AND quality_score >= 7
        successful = sum(1 for obj in objects 
                        if obj.get("generated_code") 
                        and (obj.get("quality_score") or 0) >= 7)
        
        # Failed: has generated code but quality_score < 7 (rejected by Agent F)
        failed = sum(1 for obj in objects 
                    if obj.get("generated_code") 
                    and (obj.get("quality_score") or 0) < 7)
        
        # Warnings: processed but with validation warnings (quality 7-8)
        warnings = sum(1 for obj in objects 
                      if obj.get("generated_code") 
                      and 7 <= (obj.get("quality_score") or 0) < 9)
        
        # Calculate average generation time (placeholder - would need execution logs)
        avg_time = "N/A"
        
        # Get cartridge used (most common tech_id)
        cartridges = [obj.get("tech_id") for obj in objects if obj.get("tech_id")]
        cartridge_used = max(set(cartridges), key=cartridges.count) if cartridges else "N/A"
        
        # Tokens consumed (placeholder - would need utm_audit_log integration)
        tokens_consumed = 0
        
        stats = {
            "total_objects": total_objects,
            "processed": processed,
            "successful": successful,
            "failed": failed,
            "warnings": warnings,
            "avg_generation_time": avg_time,
            "cartridge_used": cartridge_used,
            "tokens_consumed": tokens_consumed
        }
        
        return {"stats": stats}
        
    except Exception as e:
        logger.error(f"[GenerationStats] Error: {e}", "GenerationStats")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/generation/summary")
async def get_generation_summary(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """Get code generation summary (CodeGenerationSummary component)."""
    try:
        # Query all generated objects (note: no created_at column in utm_objects)
        query = db.client.table("utm_objects") \
            .select("object_id, object_name, source_name, generated_code, tech_id, layer, quality_score, validation_result, updated_at")
        
        if db.tenant_id:
            query = query.eq("tenant_id", db.tenant_id)
        
        query = query.eq("project_id", project_id)
        res = query.execute()
        
        objects = res.data if res.data else []
        
        # Filter only processed objects (with generated code)
        processed = [obj for obj in objects if obj.get("generated_code")]
        
        # Files by type (based on tech_id)
        files_by_type = {}
        for obj in processed:
            tech_id = obj.get("tech_id", "unknown")
            if "python" in tech_id.lower() or "pyspark" in tech_id.lower():
                files_by_type["python"] = files_by_type.get("python", 0) + 1
            elif "sql" in tech_id.lower() or "snowflake" in tech_id.lower():
                files_by_type["sql"] = files_by_type.get("sql", 0) + 1
            elif "yaml" in tech_id.lower():
                files_by_type["yaml"] = files_by_type.get("yaml", 0) + 1
            elif "json" in tech_id.lower():
                files_by_type["json"] = files_by_type.get("json", 0) + 1
            else:
                files_by_type["config"] = files_by_type.get("config", 0) + 1
        
        # Files by category (based on layer)
        files_by_category = {}
        for obj in processed:
            layer = obj.get("layer", "unknown")
            if layer == "bronze":
                files_by_category["staging"] = files_by_category.get("staging", 0) + 1
            elif layer == "silver":
                files_by_category["transformations"] = files_by_category.get("transformations", 0) + 1
            elif layer == "gold":
                files_by_category["dimensions"] = files_by_category.get("dimensions", 0) + 1
            else:
                files_by_category["utilities"] = files_by_category.get("utilities", 0) + 1
        
        # Objects processed status
        objects_processed = []
        for obj in processed:
            quality_score = obj.get("quality_score", 0)
            validation_result = obj.get("validation_result")
            
            # Determine status
            if quality_score >= 8:
                status = "success"
            elif validation_result and "error" in str(validation_result).lower():
                status = "error"
            elif validation_result and "warning" in str(validation_result).lower():
                status = "warning"
            else:
                status = "success"
            
            objects_processed.append({
                "name": obj.get("object_name") or obj.get("source_name", "Unknown"),
                "type": obj.get("layer", "unknown"),
                "file": f"{obj.get('source_name', 'unknown')}.{obj.get('tech_id', 'py')}",
                "status": status
            })
        
        # Structure info (placeholder - would need R2 integration)
        structure = {
            "folders": ["bronze", "silver", "gold", "utilities"],
            "config_files": [
                {"name": "requirements.txt", "size": "1.2 KB", "description": "Python dependencies"},
                {"name": "config.yaml", "size": "856 B", "description": "Project configuration"}
            ]
        }
        
        # Get cartridge used
        cartridges = [obj.get("tech_id") for obj in processed if obj.get("tech_id")]
        cartridge_used = max(set(cartridges), key=cartridges.count) if cartridges else "pyspark"
        
        # Generation timestamp (latest updated_at)
        timestamps = [obj.get("updated_at") for obj in processed if obj.get("updated_at")]
        generation_timestamp = max(timestamps) if timestamps else None
        
        summary = {
            "total_files": len(processed),
            "files_by_type": files_by_type,
            "files_by_category": files_by_category,
            "structure": structure,
            "objects_processed": objects_processed,
            "cartridge_used": cartridge_used,
            "generation_timestamp": generation_timestamp
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"[GenerationSummary] Error: {e}", "GenerationSummary")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Understanding endpoints — Block 3
# ---------------------------------------------------------------------------

@router.get("/{project_id}/understanding/functional-map")
async def get_functional_map(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
):
    """Return the functional map: business domains, capabilities, and datasets."""
    try:
        project_id = await _resolve_project_uuid(db, project_id)
        svc = UnderstandingService(
            project_id=project_id,
            tenant_id=db.tenant_id,
            client_id=db.client_id,
        )
        return await svc.get_functional_map()
    except Exception as exc:
        logger.error(f"[Understanding] functional-map error: {exc}", "Understanding")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{project_id}/understanding/operational-map")
async def get_operational_map(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
):
    """Return the operational map: processes, execution order, and fragility signals."""
    try:
        project_id = await _resolve_project_uuid(db, project_id)
        svc = UnderstandingService(
            project_id=project_id,
            tenant_id=db.tenant_id,
            client_id=db.client_id,
        )
        return await svc.get_operational_map()
    except Exception as exc:
        logger.error(f"[Understanding] operational-map error: {exc}", "Understanding")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{project_id}/understanding/recommendations")
async def get_recommendations(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
):
    """Return prioritized migration recommendations grounded in evidence."""
    try:
        project_id = await _resolve_project_uuid(db, project_id)
        svc = UnderstandingService(
            project_id=project_id,
            tenant_id=db.tenant_id,
            client_id=db.client_id,
        )
        return await svc.get_recommendation_set()
    except Exception as exc:
        logger.error(f"[Understanding] recommendations error: {exc}", "Understanding")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{project_id}/understanding/rule-candidates")
async def get_rule_candidates(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
):
    """Return rule candidate summary: reusable transformation patterns across assets."""
    try:
        project_id = await _resolve_project_uuid(db, project_id)
        svc = UnderstandingService(
            project_id=project_id,
            tenant_id=db.tenant_id,
            client_id=db.client_id,
        )
        return await svc.get_rule_candidates()
    except Exception as exc:
        logger.error(f"[Understanding] rule-candidates error: {exc}", "Understanding")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{project_id}/understanding/rebuild")
async def rebuild_understanding(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
):
    """
    Rebuild all four understanding artifacts and persist to utm_projects.
    Returns the full understanding payload.
    """
    try:
        project_id = await _resolve_project_uuid(db, project_id)
        svc = UnderstandingService(
            project_id=project_id,
            tenant_id=db.tenant_id,
            client_id=db.client_id,
        )
        payload = _validate_understanding_payload(await svc.rebuild())
        return {"status": "rebuilt", "generated_at": payload["generated_at"], "payload": payload}
    except Exception as exc:
        logger.error(f"[Understanding] rebuild error: {exc}", "Understanding")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{project_id}/understanding/refresh")
async def refresh_understanding(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
):
    """Alias endpoint for deterministic understanding refresh."""
    return await rebuild_understanding(project_id=project_id, db=db)


# ==================== EXPORT ENDPOINTS (Block 4 Downstreams) ====================


@router.get("/{project_id}/export/documentation")
async def export_documentation(
    project_id: str,
    format: str = "markdown",
    db: SupabasePersistence = Depends(get_db),
):
    """
    Export complete documentation from understanding snapshot.
    
    Formats: markdown, html, json
    """
    try:
        project_id = await _resolve_project_uuid(db, project_id)
        from apps.api.services.documentation_export_service import (
            DocumentationExportService,
            ExportFormat,
        )
        
        # Validate format
        try:
            export_format = ExportFormat(format.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format '{format}'. Supported: markdown, html, json",
            )
        
        svc = DocumentationExportService(
            tenant_id=db.tenant_id,
            client_id=db.client_id,
        )
        result = await svc.export_full_documentation(project_id, export_format)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result.get("message", "Export failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[Export] documentation error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{project_id}/export/rule-candidates")
async def export_rule_candidates(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
):
    """
    Export rule candidates with implementation tracking and consolidation analysis.
    """
    try:
        project_id = await _resolve_project_uuid(db, project_id)
        from apps.api.services.documentation_export_service import DocumentationExportService
        
        svc = DocumentationExportService(
            tenant_id=db.tenant_id,
            client_id=db.client_id,
        )
        result = await svc.export_rule_candidates_with_tracking(project_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result.get("message", "Export failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[Export] rule-candidates error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{project_id}/export/recommendation-actions")
async def export_recommendation_actions(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
):
    """
    Export recommendation mappings to concrete implementation actions.
    """
    try:
        project_id = await _resolve_project_uuid(db, project_id)
        from apps.api.services.documentation_export_service import DocumentationExportService
        
        svc = DocumentationExportService(
            tenant_id=db.tenant_id,
            client_id=db.client_id,
        )
        result = await svc.export_recommendation_actions(project_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result.get("message", "Export failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[Export] recommendation-actions error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ==================== SNAPSHOT & RULE REFINEMENT (Block 5) ====================


@router.get("/{project_id}/snapshot")
async def get_knowledge_snapshot(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
):
    """
    Retrieve the current knowledge package snapshot for a project.

    Contains: understanding artifacts + refined rules + metadata.
    """
    try:
        project_id = await _resolve_project_uuid(db, project_id)

        record = await db.get_project_metadata(project_id)
        if not record:
            raise HTTPException(status_code=404, detail="Project not found")

        settings = record.get("settings", {})
        snapshot = settings.get("knowledge_package_snapshot")

        if not snapshot:
            return {"error": "No snapshot yet", "message": "Run /refine to generate snapshot"}

        return {
            "snapshot_id": snapshot.get("metadata", {}).get("snapshot_id"),
            "created_at": snapshot.get("metadata", {}).get("created_at"),
            "understanding_artifacts": len(snapshot.get("understanding", {}).keys()),
            "refined_rules_count": len(snapshot.get("refined_rules", [])),
            "package_hash": snapshot.get("package_hash"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[Snapshot] get error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{project_id}/refine")
async def refine_and_snapshot(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
):
    """
    Refine rule candidates and create knowledge package snapshot.

    Scores all rule candidates by:
    - Reusability (across assets/processes)
    - Complexity (effort to implement)
    - Confidence (backing evidence)

    Returns ranked, materialized rules + snapshot ID.
    """
    try:
        project_id = await _resolve_project_uuid(db, project_id)

        record = await db.get_project_metadata(project_id)
        if not record:
            raise HTTPException(status_code=404, detail="Project not found")

        settings = record.get("settings", {})
        understanding = settings.get("understanding_generated") or settings.get("understanding_payload")

        if not understanding:
            return {
                "error": "No understanding yet",
                "message": "Run /understanding/rebuild first",
            }

        rule_candidates = understanding.get("rule_candidates", {}).get("candidates", [])
        if not rule_candidates:
            rule_candidates = understanding.get("rule_candidate_summary", {}).get("rules", [])

        from apps.api.services.rule_refinement_service import RuleRefinementService

        svc = RuleRefinementService(
            tenant_id=db.tenant_id,
            client_id=db.client_id,
        )

        operational_context = understanding.get("operational_map", {})
        project_scope = {
            "object_count": len(settings.get("discovery_results", {}).get("objects", [])),
            "stage": record.get("stage"),
        }

        refined = svc.score_rule_candidates(
            rule_candidates, operational_context, project_scope
        )

        snapshot = svc.create_knowledge_package_snapshot(
            project_id,
            understanding,
            refined,
            metadata={"project_name": record.get("name")},
        )

        updated_settings = settings.copy()
        updated_settings["knowledge_package_snapshot"] = snapshot
        updated_settings["snapshot_refreshed_at"] = datetime.now(timezone.utc).isoformat()

        await db.update_project_settings(project_id, updated_settings)

        logger.info(
            f"Created knowledge snapshot for {project_id}: "
            f"{snapshot['metadata']['snapshot_id']}"
        )

        return {
            "snapshot_id": snapshot["metadata"]["snapshot_id"],
            "created_at": snapshot["metadata"]["created_at"],
            "refined_rules": len(refined),
            "top_3_rules": [
                {
                    "id": r.get("id"),
                    "type": r.get("type"),
                    "composite_score": r.get("composite_score"),
                    "recommendation": r.get("recommendation"),
                }
                for r in refined[:3]
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[Refinement] refine error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{project_id}/refined-rules")
async def get_refined_rules(
    project_id: str,
    top_n: int = 20,
    applicability: Optional[str] = None,
    db: SupabasePersistence = Depends(get_db),
):
    """
    Retrieve refined rules from latest snapshot.

    Query params:
    - top_n: number of top rules to return (default 20)
    - applicability: filter by LOCAL or GLOBAL
    """
    try:
        project_id = await _resolve_project_uuid(db, project_id)

        record = await db.get_project_metadata(project_id)
        if not record:
            raise HTTPException(status_code=404, detail="Project not found")

        settings = record.get("settings", {})
        snapshot = settings.get("knowledge_package_snapshot")

        if not snapshot:
            return {"error": "No snapshot", "message": "Run /refine first"}

        rules = snapshot.get("refined_rules", [])[:top_n]

        if applicability:
            rules = [r for r in rules if r.get("applicability") == applicability.upper()]

        return {
            "snapshot_id": snapshot.get("metadata", {}).get("snapshot_id"),
            "total_rules": len(rules),
            "rules": rules,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[Rules] get-refined error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ==================== GOVERNANCE & VERSIONING (Block 6) ====================


@router.get("/{project_id}/governance/checks")
async def validate_governance(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
):
    """Validate project governance readiness before finalization."""
    try:
        project_id = await _resolve_project_uuid(db, project_id)

        record = await db.get_project_metadata(project_id)
        if not record:
            raise HTTPException(status_code=404, detail="Project not found")

        settings = record.get("settings", {})
        snapshot = settings.get("knowledge_package_snapshot")

        if not snapshot:
            return {"error": "No snapshot", "message": "Run /refine first"}

        from apps.api.services.governance_service import SnapshotVersioningService

        svc = SnapshotVersioningService(
            tenant_id=db.tenant_id,
            client_id=db.client_id,
        )

        return svc.validate_governance_readiness(
            snapshot,
            {
                "stage": record.get("stage"),
                "name": record.get("name"),
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[Governance] validation error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{project_id}/snapshot/diff")
async def get_snapshot_diff(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
):
    """Compare current snapshot against previous version to detect changes."""
    try:
        project_id = await _resolve_project_uuid(db, project_id)

        record = await db.get_project_metadata(project_id)
        if not record:
            raise HTTPException(status_code=404, detail="Project not found")

        settings = record.get("settings", {})
        current_snapshot = settings.get("knowledge_package_snapshot")

        if not current_snapshot:
            return {"error": "No snapshot", "message": "Run /refine first"}

        previous_snapshot = settings.get("knowledge_package_snapshot_previous")

        from apps.api.services.governance_service import SnapshotVersioningService

        svc = SnapshotVersioningService(
            tenant_id=db.tenant_id,
            client_id=db.client_id,
        )

        diff = svc.compute_snapshot_diff(previous_snapshot, current_snapshot)

        return {
            "current_snapshot_id": current_snapshot.get("metadata", {}).get("snapshot_id"),
            "previous_snapshot_id": (
                previous_snapshot.get("metadata", {}).get("snapshot_id")
                if previous_snapshot
                else None
            ),
            "diff": diff,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[Snapshot] diff error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{project_id}/snapshot/history")
async def get_snapshot_history(
    project_id: str,
    limit: int = 10,
    db: SupabasePersistence = Depends(get_db),
):
    """Retrieve snapshot history for the project (versioning audit trail)."""
    try:
        project_id = await _resolve_project_uuid(db, project_id)

        record = await db.get_project_metadata(project_id)
        if not record:
            raise HTTPException(status_code=404, detail="Project not found")

        settings = record.get("settings", {})
        history = []

        current = settings.get("knowledge_package_snapshot")
        if current:
            history.append({
                "version": "current",
                "snapshot_id": current.get("metadata", {}).get("snapshot_id"),
                "created_at": current.get("metadata", {}).get("created_at"),
                "rules_count": len(current.get("refined_rules", [])),
                "package_hash": current.get("package_hash"),
            })

        return {
            "project_id": project_id,
            "history": history[:limit],
            "total_versions": len(history),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[Snapshot] history error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
