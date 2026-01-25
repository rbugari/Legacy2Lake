"""
Authentication Router
Handles login, session management, and authentication utilities.
Migrated from main.py with security improvements (bcrypt support).
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import hashlib
import bcrypt
from typing import Optional, List
from datetime import datetime

from services.persistence_service import SupabasePersistence

router = APIRouter(prefix="/auth", tags=["Authentication"])


# --- Models ---
class LoginPayload(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    tenant_id: str
    client_id: str
    role: Optional[str] = None
    message: str


class TenantCreate(BaseModel):
    username: str
    password: str
    client_id: str
    role: str = "USER"


class TenantUpdate(BaseModel):
    role: Optional[str] = None
    client_id: Optional[str] = None
    password: Optional[str] = None


# --- Password Utilities ---
def verify_password_sha256(plain_password: str, hashed_password: str) -> bool:
    """Legacy SHA256 verification (for migration compatibility)."""
    input_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return input_hash == hashed_password


def verify_password_bcrypt(plain_password: str, hashed_password: str) -> bool:
    """Secure bcrypt verification."""
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except Exception:
        return False


def hash_password_bcrypt(password: str) -> str:
    """Generate secure bcrypt hash."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


async def migrate_password_to_bcrypt(db: SupabasePersistence, user_id: str, password: str):
    """Migrates a user's password from SHA256 to bcrypt."""
    new_hash = hash_password_bcrypt(password)
    try:
        db.client.table("utm_tenants").update({
            "password_hash_bcrypt": new_hash
        }).eq("tenant_id", user_id).execute()
        print(f"[AUTH] Migrated password to bcrypt for tenant: {user_id}")
    except Exception as e:
        print(f"[AUTH] Failed to migrate password: {e}")


# --- Endpoints ---
@router.get("/ping-antigravity")
async def ping_antigravity():
    """Health check endpoint for Antigravity."""
    return {"message": "pong-antigravity"}


@router.post("/login", response_model=LoginResponse)
async def login(request: Request):
    """
    Simple Login for MVP Antigravity. 
    Supports JSON or Form data.
    Includes automatic password migration from SHA256 to bcrypt.
    """
    # 1. Parse Body based on Content-Type
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()
            username = data.get("username")
            password = data.get("password")
        elif "form" in content_type:  # urlencoded or multipart
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported Content-Type. Use 'application/json'."
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Request Body")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and Password required")
    
    db = SupabasePersistence(tenant_id=None)  # Admin Mode
    
    # 2. Fetch Tenant
    res = db.client.table("utm_tenants").select(
        "tenant_id, client_id, password_hash, password_hash_bcrypt, role"
    ).eq("username", username).execute()
    
    if not res.data:
        print(f"[AUTH] User {username} not found")
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    
    user = res.data[0]
    
    # 3. Verify Password (with migration support)
    password_valid = False
    needs_migration = False
    
    # Try bcrypt first (preferred)
    if user.get("password_hash_bcrypt"):
        password_valid = verify_password_bcrypt(password, user["password_hash_bcrypt"])
    
    # Fall back to SHA256 if bcrypt not set or failed
    if not password_valid and user.get("password_hash"):
        password_valid = verify_password_sha256(password, user["password_hash"])
        if password_valid:
            needs_migration = True  # Valid SHA256, migrate to bcrypt
    
    if not password_valid:
        print(f"[AUTH] Password verification failed for user: {username}")
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    
    # 4. Migrate password to bcrypt if needed (async, non-blocking)
    if needs_migration:
        await migrate_password_to_bcrypt(db, user["tenant_id"], password)
    
    # 5. Return Identity (Frontend should store in X-Tenant-ID headers)
    return LoginResponse(
        success=True,
        tenant_id=user["tenant_id"],
        client_id=user["client_id"],
        role=user.get("role"),
        message=f"Welcome {username}"
    )


# --- Admin Management Endpoints ---

@router.get("/tenants", response_model=List[dict])
async def list_tenants(request: Request):
    """List all tenants (Admin only)."""
    # Authorization check (In a real app, use a dependency)
    role = request.headers.get("X-Role")
    if role != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    
    db = SupabasePersistence(tenant_id=None)
    res = db.client.table("utm_tenants").select(
        "tenant_id, client_id, username, role, created_at"
    ).execute()
    return res.data


@router.post("/tenants")
async def create_tenant(payload: TenantCreate, request: Request):
    """Create a new tenant (Admin only)."""
    role = request.headers.get("X-Role")
    if role != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    db = SupabasePersistence(tenant_id=None)
    
    # Check if exists
    existing = db.client.table("utm_tenants").select("tenant_id").eq("username", payload.username).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_tenant = {
        "username": payload.username,
        "password_hash": hashlib.sha256(payload.password.encode()).hexdigest(), # Legacy compatibility
        "password_hash_bcrypt": hash_password_bcrypt(payload.password),
        "client_id": payload.client_id,
        "role": payload.role,
        "tenant_id": f"t-{payload.username}-{datetime.now().strftime('%y%m%d%H%M')}"
    }
    
    db.client.table("utm_tenants").insert(new_tenant).execute()
    return {"success": True, "tenant_id": new_tenant["tenant_id"]}


@router.patch("/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, payload: TenantUpdate, request: Request):
    """Update tenant details (Admin only)."""
    role = request.headers.get("X-Role")
    if role != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    db = SupabasePersistence(tenant_id=None)
    update_data = {}
    if payload.role: update_data["role"] = payload.role
    if payload.client_id: update_data["client_id"] = payload.client_id
    if payload.password:
        update_data["password_hash_bcrypt"] = hash_password_bcrypt(payload.password)
    
    if not update_data:
        return {"success": True, "message": "No changes applied"}
        
    db.client.table("utm_tenants").update(update_data).eq("tenant_id", tenant_id).execute()
    return {"success": True}


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, request: Request):
    """Remove a tenant (Admin only)."""
    role = request.headers.get("X-Role")
    if role != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    db = SupabasePersistence(tenant_id=None)
    db.client.table("utm_tenants").delete().eq("tenant_id", tenant_id).execute()
    return {"success": True}
