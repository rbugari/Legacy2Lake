"""
Traceability Router - v4.5
Endpoints for legacy-to-target column/table traceability maps.

GET  /projects/{project_id}/traceability            → list all cached asset statuses
GET  /projects/{project_id}/traceability/{asset_id} → build (or rebuild) traceability for one asset
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

try:
    from apps.api.utils.logger import logger
    from apps.api.services.traceability_service import TraceabilityService
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.routers.dependencies import get_db
except ImportError:
    try:
        from utils.logger import logger
        from services.traceability_service import TraceabilityService
        from services.persistence_service import SupabasePersistence
        from routers.dependencies import get_db
    except ImportError:
        from ..utils.logger import logger
        from ..services.traceability_service import TraceabilityService
        from ..services.persistence_service import SupabasePersistence
        from .dependencies import get_db

router = APIRouter(tags=["Traceability"])


def _get_svc(project_id: str, db: SupabasePersistence) -> TraceabilityService:
    tenant_id = db.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return TraceabilityService(tenant_id=tenant_id, project_id=project_id)


@router.get("/projects/{project_id}/traceability")
async def list_traceability(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List cached traceability summaries for all assets in this project."""
    svc = _get_svc(project_id, db)
    return svc.list_for_project()


@router.get("/projects/{project_id}/traceability/{asset_id}")
async def get_asset_traceability(
    project_id: str,
    asset_id: str,
    db: SupabasePersistence = Depends(get_db),
) -> Dict[str, Any]:
    """
    Build (or rebuild) the traceability map for one asset.
    Always recomputes from current data; the result is also cached in utm_asset_traceability.
    """
    svc = _get_svc(project_id, db)
    result = svc.build(asset_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
