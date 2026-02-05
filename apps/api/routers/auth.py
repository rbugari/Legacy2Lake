from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
import hashlib
import bcrypt
from typing import Optional, List
from datetime import datetime

from services.persistence_service import SupabasePersistence
from services.email_service import EmailService
from routers.dependencies import require_admin, get_identity
import secrets
import string

router = APIRouter(tags=["Authentication"])


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
    password: Optional[str] = None
    email: Optional[str] = None
    client_id: str
    role: str = "USER"


class TenantInvite(BaseModel):
    username: str
    email: str
    client_id: Optional[str] = None # Optional now as we auto-create
    role: str = "USER"


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class TenantUpdate(BaseModel):
    role: Optional[str] = None
    client_id: Optional[str] = None
    password: Optional[str] = None


class ClientCreate(BaseModel):
    name: str


class ClientResponse(BaseModel):
    client_id: str
    name: str
    created_at: str


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
async def list_tenants(admin: dict = Depends(require_admin)):
    """List all tenants (Admin only)."""
    db = SupabasePersistence(tenant_id=None)
    res = db.client.table("utm_tenants").select(
        "tenant_id, client_id, username, role, created_at"
    ).execute()
    return res.data


@router.post("/tenants")
async def create_tenant(payload: TenantCreate, admin: dict = Depends(require_admin)):
    """Create a new tenant (Admin only)."""
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
        "role": payload.role
    }
    
    res = db.client.table("utm_tenants").insert(new_tenant).execute()
    return {"success": True, "tenant_id": res.data[0]["tenant_id"]}


@router.patch("/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, payload: TenantUpdate, admin: dict = Depends(require_admin)):
    """Update tenant details (Admin only)."""
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
async def delete_tenant(tenant_id: str, admin: dict = Depends(require_admin)):
    """Remove a tenant (Admin only)."""
    db = SupabasePersistence(tenant_id=None)
    db.client.table("utm_tenants").delete().eq("tenant_id", tenant_id).execute()
    return {"success": True}


# --- Client Management Endpoints ---

@router.get("/clients", response_model=List[ClientResponse])
async def list_clients(admin: dict = Depends(require_admin)):
    """List all clients (Admin only)."""
    db = SupabasePersistence(tenant_id=None)
    return await db.list_clients()


@router.post("/clients")
async def create_client(payload: ClientCreate, admin: dict = Depends(require_admin)):
    """Create a new client (Admin only)."""
    db = SupabasePersistence(tenant_id=None)
    
    # Check if exists
    existing = db.client.table("utm_clients").select("client_id").eq("name", payload.name).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Client name already exists")
    
    client_id = await db.create_client(payload.name)
    return {"success": True, "client_id": client_id}


# --- User Self-Service ---

@router.post("/change-password")
async def change_password(payload: PasswordChange, identity: dict = Depends(get_identity)):
    """User changes their own password."""
    tenant_id = identity.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid Session")

    db = SupabasePersistence(tenant_id=None)
    
    # 1. Fetch current user
    res = db.client.table("utm_tenants").select(
        "password_hash, password_hash_bcrypt"
    ).eq("tenant_id", tenant_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")
        
    user = res.data[0]
    
    # 2. Verify current password
    password_valid = False
    if user.get("password_hash_bcrypt"):
        password_valid = verify_password_bcrypt(payload.current_password, user["password_hash_bcrypt"])
    elif user.get("password_hash"):
        password_valid = verify_password_sha256(payload.current_password, user["password_hash"])
        
    if not password_valid:
        raise HTTPException(status_code=400, detail="Current password incorrect")
        
    # 3. Update to new bcrypt hash
    new_hash = hash_password_bcrypt(payload.new_password)
    db.client.table("utm_tenants").update({
        "password_hash_bcrypt": new_hash,
        "password_hash": None # Clear legacy hash
    }).eq("tenant_id", tenant_id).execute()
    
    return {"success": True, "message": "Password updated successfully"}


@router.post("/invite")
async def invite_tenant(payload: TenantInvite, admin: dict = Depends(require_admin)):
    """Invite a new user (Admin only). Generates random password, sends email, and AUTO-CREATES client."""
    db = SupabasePersistence(tenant_id=None)
    
    # 1. Check if username exists
    existing = db.client.table("utm_tenants").select("tenant_id").eq("username", payload.username).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # 2. Auto-Create Client
    try:
        client_res = db.client.table("utm_clients").insert({"name": payload.username}).execute()
        if not client_res.data:
            raise Exception("Failed to create client record")
        new_client_id = client_res.data[0]["client_id"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create associated client: {str(e)}")

    # 3. Generate random password
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))
    
    # 4. Create tenant (Enforce role: "USER" and use new client_id)
    new_tenant = {
        "username": payload.username,
        "email": payload.email,
        "password_hash_bcrypt": hash_password_bcrypt(temp_password),
        "client_id": new_client_id,
        "role": "USER" 
    }
    
    try:
        res = db.client.table("utm_tenants").insert(new_tenant).execute()
        tenant_data = res.data[0]
        
        # 4. Send Email
        email_svc = EmailService()
        sent = email_svc.send_invitation(payload.username, payload.email, temp_password)
        
        if not sent:
            return {
                "success": True, 
                "message": "User created but email failed to send. Please provide password manually.",
                "temp_password": temp_password,
                "tenant_id": tenant_data["tenant_id"]
            }
            
        return {"success": True, "tenant_id": tenant_data["tenant_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.post("/reset-password")
async def reset_password(payload: dict, admin: dict = Depends(require_admin)):
    """Admin resets a user's password. Generates random password and sends email."""
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")

    db = SupabasePersistence(tenant_id=None)
    
    # 1. Fetch user email and username
    res = db.client.table("utm_tenants").select("username, email").eq("tenant_id", tenant_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = res.data[0]
    username = user["username"]
    email = user.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="User has no email associated. Cannot reset via email.")

    # 2. Generate random password
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))
    
    # 3. Update password hash
    new_hash = hash_password_bcrypt(temp_password)
    db.client.table("utm_tenants").update({
        "password_hash_bcrypt": new_hash,
        "password_hash": None # Clear legacy hash
    }).eq("tenant_id", tenant_id).execute()

    # 4. Send Email
    email_svc = EmailService()
    sent = email_svc.send_password_reset(username, email, temp_password)
    
    if not sent:
        return {
            "success": True, 
            "message": "Password reset successfully but email failed to send. Please provide password manually.",
            "temp_password": temp_password
        }
        
    return {"success": True, "message": f"Password reset successfully for {username}. Email sent to {email}."}
