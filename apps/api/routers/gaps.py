"""
Gaps Router - Sprint 3: Gap & Decision Workspace
CRUD operations for utm_project_gaps.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from apps.api.services.gap_service import GapService, GapCreate, GapUpdate, GapResolve
from apps.api.services.persistence_service import SupabasePersistence
from apps.api.routers.dependencies import get_db, get_identity
from apps.api.utils.logger import logger

router = APIRouter(prefix="/projects", tags=["Gaps"])


def _gap_svc(db: SupabasePersistence, identity: dict) -> GapService:
    return GapService(
        tenant_id=db.tenant_id,
        client_id=db.client_id,
        user_id=identity.get("user_id"),
    )


@router.get("/{project_id}/gaps")
async def list_gaps(
    project_id: str,
    status:   Optional[str] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    db: SupabasePersistence = Depends(get_db),
    identity: dict = Depends(get_identity),
):
    """List all gaps for a project, with optional filters."""
    svc = _gap_svc(db, identity)
    return await svc.list_gaps(project_id, status=status, severity=severity, category=category)


@router.post("/{project_id}/gaps", status_code=201)
async def create_gap(
    project_id: str,
    payload: GapCreate,
    db: SupabasePersistence = Depends(get_db),
    identity: dict = Depends(get_identity),
):
    """Create a new gap item for the project."""
    svc = _gap_svc(db, identity)
    return await svc.create_gap(project_id, payload)


@router.patch("/{project_id}/gaps/{gap_id}")
async def update_gap(
    project_id: str,
    gap_id: str,
    payload: GapUpdate,
    db: SupabasePersistence = Depends(get_db),
    identity: dict = Depends(get_identity),
):
    """Update gap metadata or status."""
    svc = _gap_svc(db, identity)
    result = await svc.update_gap(gap_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail="Gap not found")
    return result


@router.post("/{project_id}/gaps/{gap_id}/resolve")
async def resolve_gap(
    project_id: str,
    gap_id: str,
    payload: GapResolve,
    db: SupabasePersistence = Depends(get_db),
    identity: dict = Depends(get_identity),
):
    """Mark a gap as resolved."""
    svc = _gap_svc(db, identity)
    result = await svc.resolve_gap(gap_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail="Gap not found")
    return result


@router.post("/{project_id}/gaps/{gap_id}/reopen")
async def reopen_gap(
    project_id: str,
    gap_id: str,
    db: SupabasePersistence = Depends(get_db),
    identity: dict = Depends(get_identity),
):
    """Reopen a previously resolved gap."""
    svc = _gap_svc(db, identity)
    result = await svc.reopen_gap(gap_id)
    if not result:
        raise HTTPException(status_code=404, detail="Gap not found")
    return result


@router.post("/{project_id}/gaps/import")
async def import_gaps_from_signals(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
    identity: dict = Depends(get_identity),
):
    """
    Auto-import gaps from quick assessment and triage signals.
    Deduplicates by title — safe to call multiple times.
    """
    svc = _gap_svc(db, identity)
    try:
        return await svc.import_from_signals(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[GapsImport] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
