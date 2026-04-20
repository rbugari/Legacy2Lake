import asyncio
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

try:
    from apps.api.routers.dependencies import get_db, get_identity
    from apps.api.services.lock_service import LockService, ProcessLockError
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.services.target_matrix_service import (
        DEFAULT_BASE_URL,
        build_default_matrix_config,
        list_matrix_runs,
        load_matrix_run,
        TargetMatrixRunner,
    )
    from apps.api.utils.logger import logger
except ImportError:
    from .dependencies import get_db, get_identity
    from ..services.lock_service import LockService, ProcessLockError
    from ..services.persistence_service import SupabasePersistence
    from ..services.target_matrix_service import (
        DEFAULT_BASE_URL,
        build_default_matrix_config,
        list_matrix_runs,
        load_matrix_run,
        TargetMatrixRunner,
    )
    from ..utils.logger import logger


router = APIRouter(prefix="/projects/{project_id}/matrix-tests", tags=["Matrix Tests"])


class MatrixRunRequest(BaseModel):
    config: Dict[str, Any] = Field(..., description="Matriz declarativa target + modo")
    base_url: Optional[str] = Field(default=None, description="Base URL de la API a usar para la corrida")
    request_timeout_seconds: int = Field(default=120, ge=10, le=600)


async def _run_matrix_test_background(
    project_id: str,
    tenant_id: str,
    db_config: Dict[str, Any],
    run_request: Dict[str, Any],
    lock_id: str,
    lock_service: LockService,
    owner_user_id: str,
) -> None:
    db = SupabasePersistence(tenant_id=tenant_id, client_id=db_config.get("client_id"))
    try:
        await db.log_execution(project_id, "MIGRATION", "Starting autonomous target matrix run...", step="MATRIX_TEST")

        runner = TargetMatrixRunner(
            base_url=(run_request.get("base_url") or DEFAULT_BASE_URL).rstrip("/"),
            tenant_id=tenant_id,
            request_timeout_seconds=int(run_request.get("request_timeout_seconds") or 120),
        )

        result = await asyncio.to_thread(
            runner.run_config,
            project_id,
            run_request["config"],
            None,
        )
        await db.log_execution(
            project_id,
            "MIGRATION",
            f"Matrix run finished with status {result.get('status')} and {len(result.get('failures', []))} failures.",
            step="MATRIX_TEST",
        )
    except Exception as exc:
        logger.error(f"[MatrixTests] Background run failed: {exc}", "MatrixTests")
        await db.log_execution(project_id, "MIGRATION", f"Matrix run failed: {exc}", step="MATRIX_TEST", level="ERROR")
    finally:
        try:
            await lock_service.release_lock(lock_id=lock_id, user_id=owner_user_id)
        except Exception as exc:
            logger.warning(f"[MatrixTests] Failed to release lock {lock_id}: {exc}", "MatrixTests")


@router.get("/template")
async def get_matrix_test_template(project_id: str, db: SupabasePersistence = Depends(get_db)):
    try:
        catalog = await db.list_supported_techs()
        config = build_default_matrix_config(catalog)
        config["project_id"] = project_id
        return {
            "project_id": project_id,
            "config": config,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to build matrix template: {exc}")


@router.post("/runs")
async def start_matrix_test_run(
    project_id: str,
    payload: MatrixRunRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    identity: dict = Depends(get_identity),
    db: SupabasePersistence = Depends(get_db),
):
    lock_service = LockService(tenant_id=identity.get("tenant_id"), client_id=identity.get("client_id"))
    tenant_id = identity.get("tenant_id")
    owner_user_id = identity.get("user_id") or tenant_id
    username = identity.get("username", "Unknown User")
    if not username or username == "Unknown User":
        try:
            tenant = await db.get_tenant_by_id(tenant_id)
            username = tenant.get("username", "Unknown User") if tenant else "Unknown User"
        except Exception:
            username = "Unknown User"

    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        session_id = f"matrix-{project_id}"

    try:
        lock = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="matrix_test",
            user_id=owner_user_id,
            username=username,
            session_id=session_id,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.headers.get("x-forwarded-for") or "unknown",
        )
    except ProcessLockError as exc:
        raise HTTPException(
            status_code=423,
            detail={
                "error": "Matrix test already running",
                "message": exc.message,
                "locked_by": exc.locked_by,
            },
        )

    db_config = {
        "client_id": db.client_id,
        "tenant_id": tenant_id,
    }
    request_payload = payload.model_dump()
    background_tasks.add_task(
        _run_matrix_test_background,
        project_id,
        tenant_id,
        db_config,
        request_payload,
        lock["lock_id"],
        lock_service,
        owner_user_id,
    )

    return {
        "status": "RUNNING",
        "message": "Autonomous matrix test started in background.",
        "project_id": project_id,
        "lock_id": lock["lock_id"],
    }


@router.get("/runs")
async def get_matrix_test_runs(project_id: str):
    return {
        "project_id": project_id,
        "runs": list_matrix_runs(project_id),
    }


@router.get("/runs/{run_id}")
async def get_matrix_test_run(project_id: str, run_id: str):
    try:
        return load_matrix_run(project_id, run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/runs/{run_id}/download")
async def download_matrix_test_run_bundle(project_id: str, run_id: str):
    try:
        payload = load_matrix_run(project_id, run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    bundle_path = payload.get("bundle_path")
    if not bundle_path:
        raise HTTPException(status_code=409, detail="Run bundle is not available yet")
    if not os.path.exists(bundle_path):
        raise HTTPException(status_code=404, detail="Run bundle file not found on disk")

    return FileResponse(
        path=bundle_path,
        media_type="application/zip",
        filename=os.path.basename(bundle_path),
    )