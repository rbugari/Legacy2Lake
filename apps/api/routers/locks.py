"""
Process Locks Router
Manages process locking to prevent concurrent execution.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import Dict, Any, Optional
from pydantic import BaseModel
import uuid

from apps.api.services.lock_service import LockService, ProcessLockError
from apps.api.services.persistence_service import SupabasePersistence
from apps.api.routers.dependencies import get_db, get_identity, require_admin

router = APIRouter(prefix="/locks", tags=["Process Locks"])


# --- Pydantic Models ---

class AcquireLockRequest(BaseModel):
    project_id: str
    process_type: str  # 'triage', 'drafting', 'refinement', 'certification', 'governance'


class ReleaseLockRequest(BaseModel):
    lock_id: Optional[str] = None
    project_id: Optional[str] = None
    process_type: Optional[str] = None


class CheckLockRequest(BaseModel):
    project_id: str
    process_type: str


class ForceReleaseRequest(BaseModel):
    project_id: str
    process_type: str


class LockResponse(BaseModel):
    lock_id: str
    project_id: str
    process_type: str
    locked_by_username: str
    locked_at: str
    expires_at: str
    status: str


class LockStatusResponse(BaseModel):
    is_locked: bool
    lock_info: Optional[Dict[str, Any]] = None


# --- Helper Functions ---

async def get_username(tenant_id: str, db: SupabasePersistence) -> str:
    """Fetch username from tenant_id."""
    try:
        tenant = await db.get_tenant_by_id(tenant_id)
        return tenant.get("username", "Unknown User") if tenant else "Unknown User"
    except Exception:
        return "Unknown User"


async def get_session_id(request: Request) -> str:
    """
    Generate or retrieve session ID from request.
    In production, this could come from a session cookie or JWT.
    For now, we'll use a combination of user agent and a request-scoped ID.
    """
    # Try to get from custom header
    session_id = request.headers.get("X-Session-ID")
    if session_id:
        return session_id
    
    # Generate a pseudo-session ID (in production, use proper session management)
    user_agent = request.headers.get("user-agent", "")
    return str(uuid.uuid5(uuid.NAMESPACE_OID, user_agent))


# --- Endpoints ---

@router.post("/acquire", response_model=LockResponse)
async def acquire_lock(
    request: Request,
    lock_request: AcquireLockRequest,
    identity: dict = Depends(get_identity),
    db: SupabasePersistence = Depends(get_db)
):
    """
    Acquire a lock for a process on a project.
    Returns lock information if successful.
    Raises 423 Locked if the process is already locked by another user/session.
    """
    tenant_id = identity.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get username for display
    username = await get_username(tenant_id, db)
    
    # Get session ID
    session_id = await get_session_id(request)
    
    # Get client info
    user_agent = request.headers.get("user-agent")
    # In production, use request.client.host for IP
    ip_address = request.headers.get("x-forwarded-for") or "unknown"
    
    # Create lock service
    lock_service = LockService(tenant_id=tenant_id, client_id=identity.get("client_id"))
    
    try:
        lock = await lock_service.acquire_lock(
            project_id=lock_request.project_id,
            process_type=lock_request.process_type,
            user_id=tenant_id,
            username=username,
            session_id=session_id,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        return LockResponse(
            lock_id=lock['lock_id'],
            project_id=lock['project_id'],
            process_type=lock['process_type'],
            locked_by_username=lock['locked_by_username'],
            locked_at=lock['locked_at'],
            expires_at=lock['expires_at'],
            status=lock['status']
        )
        
    except ProcessLockError as e:
        raise HTTPException(
            status_code=423,  # 423 Locked status code
            detail={
                "message": e.message,
                "locked_by": e.locked_by
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acquire lock: {str(e)}")


@router.post("/release")
async def release_lock(
    lock_request: ReleaseLockRequest,
    identity: dict = Depends(get_identity)
):
    """
    Release a process lock.
    Can release by lock_id or by project_id + process_type.
    """
    tenant_id = identity.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    lock_service = LockService(tenant_id=tenant_id, client_id=identity.get("client_id"))
    
    success = await lock_service.release_lock(
        lock_id=lock_request.lock_id,
        project_id=lock_request.project_id,
        process_type=lock_request.process_type,
        user_id=tenant_id
    )
    
    if success:
        return {"message": "Lock released successfully"}
    else:
        raise HTTPException(status_code=404, detail="No active lock found to release")


@router.post("/check", response_model=LockStatusResponse)
async def check_lock(
    lock_request: CheckLockRequest,
    identity: dict = Depends(get_identity)
):
    """
    Check if a process is locked on a project.
    Returns lock status and information if locked.
    """
    tenant_id = identity.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    lock_service = LockService(tenant_id=tenant_id, client_id=identity.get("client_id"))
    
    lock = await lock_service.check_lock(
        project_id=lock_request.project_id,
        process_type=lock_request.process_type
    )
    
    if lock:
        return LockStatusResponse(
            is_locked=True,
            lock_info={
                "lock_id": lock['lock_id'],
                "locked_by_username": lock['locked_by_username'],
                "locked_at": lock['locked_at'],
                "expires_at": lock['expires_at']
            }
        )
    else:
        return LockStatusResponse(is_locked=False)


@router.post("/force-release")
async def force_release_lock(
    force_request: ForceReleaseRequest,
    identity: dict = Depends(require_admin)
):
    """
    Admin-only: Force release a lock.
    Use with caution - can cause data inconsistency if process is still running.
    """
    admin_id = identity.get("tenant_id")
    
    lock_service = LockService(tenant_id=identity.get("tenant_id"), client_id=identity.get("client_id"))
    
    success = await lock_service.force_release_lock(
        project_id=force_request.project_id,
        process_type=force_request.process_type,
        admin_user_id=admin_id
    )
    
    if success:
        return {"message": "Lock force-released successfully"}
    else:
        raise HTTPException(status_code=404, detail="No active lock found")


@router.get("/project/{project_id}")
async def get_project_locks(
    project_id: str,
    identity: dict = Depends(get_identity)
):
    """
    Get all locks (active and historical) for a project.
    Useful for debugging and audit trail.
    """
    tenant_id = identity.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    lock_service = LockService(tenant_id=tenant_id, client_id=identity.get("client_id"))
    
    locks = await lock_service.get_project_locks(project_id)
    
    return {
        "project_id": project_id,
        "locks": locks
    }


@router.get("/all")
async def get_all_active_locks(
    identity: dict = Depends(get_identity),
    admin_check: dict = Depends(require_admin),
    db: SupabasePersistence = Depends(get_db)
):
    """
    Admin Only: Get all active locks across all projects.
    Used for system administration and debugging stuck locks.
    """
    try:
        # Query all active locks
        result = db.client.table('utm_process_locks')\
            .select('*')\
            .eq('status', 'active')\
            .order('expires_at', desc=False)\
            .execute()
        
        locks = result.data if result.data else []
        
        return {
            "success": True,
            "count": len(locks),
            "locks": locks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch locks: {str(e)}")


@router.post("/{lock_id}/force-release")
async def force_release_lock_by_id(
    lock_id: str,
    identity: dict = Depends(get_identity),
    admin_check: dict = Depends(require_admin),
    db: SupabasePersistence = Depends(get_db)
):
    """
    Admin Only: Force-release a specific lock by lock_id.
    This bypasses ownership checks and forcefully sets the lock to 'released' status.
    """
    tenant_id = identity.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Update lock status to released
        result = db.client.table('utm_process_locks')\
            .update({'status': 'released'})\
            .eq('lock_id', lock_id)\
            .eq('status', 'active')\
            .execute()
        
        if result.data:
            return {
                "success": True,
                "message": f"Lock {lock_id} released successfully",
                "lock_id": lock_id
            }
        else:
            raise HTTPException(status_code=404, detail="Lock not found or already released")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to release lock: {str(e)}")

