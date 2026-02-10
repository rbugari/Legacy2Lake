from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
import hashlib
import bcrypt
from typing import Optional, List
from datetime import datetime

from services.persistence_service import SupabasePersistence
from services.email_service import EmailService
from routers.dependencies import require_admin, require_manager, get_identity
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
    user_id: str  # v3.9: Separate user identity
    display_name: str  # Organization display name
    role: Optional[str] = None
    message: str


class TenantCreate(BaseModel):
    username: str
    password: Optional[str] = None
    email: Optional[str] = None
    display_name: str  # Friendly organization name (required)
    tier: Optional[str] = "STANDARD"  # STANDARD, PREMIUM, or ENTERPRISE
    role: str = "MANAGER"  # First user of tenant is MANAGER


class TenantInvite(BaseModel):
    username: str
    email: str
    client_id: Optional[str] = None # Optional now as we auto-create
    role: str = "VIEWER"  # Default role for invited users


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class UserCreate(BaseModel):
    """Model for MANAGER creating a new user in their tenant."""
    username: str
    email: str
    password: Optional[str] = None  # Auto-generated if not provided
    role: str = "COLLABORATOR"  # MANAGER, COLLABORATOR, or VIEWER
    display_name: Optional[str] = None


class UserUpdate(BaseModel):
    """Model for MANAGER updating a user."""
    role: Optional[str] = None
    is_active: Optional[bool] = None
    display_name: Optional[str] = None
    email: Optional[str] = None


class UserPasswordReset(BaseModel):
    """Model for MANAGER resetting user password."""
    new_password: str


class TenantUpdate(BaseModel):
    role: Optional[str] = None
    display_name: Optional[str] = None
    tier: Optional[str] = None
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
    
    # 2. Fetch User (v3.9: from utm_users, not utm_tenants)
    # Support login with email OR username (case-insensitive)
    username_lower = username.lower()
    res = db.client.table("utm_users").select(
        "user_id, tenant_id, email, username, password_hash_bcrypt, role, is_active"
    ).or_(f"email.ilike.{username_lower},username.ilike.{username}").execute()
    
    if not res.data:
        print(f"[AUTH] User {username} not found")
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    
    user = res.data[0]
    
    # Check if user is active
    if not user.get("is_active", True):
        print(f"[AUTH] User {username} is inactive")
        raise HTTPException(status_code=401, detail="Account is inactive")
    
    # 3. Verify Password (bcrypt only in v3.9)
    password_valid = verify_password_bcrypt(password, user["password_hash_bcrypt"])
    
    if not password_valid:
        print(f"[AUTH] Password verification failed for user: {username}")
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    
    # 4. Get tenant info
    tenant_res = db.client.table("utm_tenants").select(
        "display_name"
    ).eq("tenant_id", user["tenant_id"]).execute()
    
    tenant = tenant_res.data[0] if tenant_res.data else {"display_name": "Unknown"}
    
    # 5. Update last login
    db.client.table("utm_users").update({
        "last_login": datetime.utcnow().isoformat()
    }).eq("user_id", user["user_id"]).execute()
    
    # 6. Return Identity (Frontend should store both tenant_id and user_id)
    return LoginResponse(
        success=True,
        tenant_id=user["tenant_id"],
        user_id=user["user_id"],
        display_name=tenant["display_name"],
        role=user.get("role"),
        message=f"Welcome {user.get('username', user.get('email'))}"
    )


# --- Admin Management Endpoints ---

@router.get("/tenants", response_model=List[dict])
async def list_tenants(admin: dict = Depends(require_admin)):
    """List all tenants (Admin only)."""
    db = SupabasePersistence(tenant_id=None)
    res = db.client.table("utm_tenants").select(
        "tenant_id, display_name, tier, is_active, created_at"
    ).execute()
    return res.data


@router.post("/tenants")
async def create_tenant(payload: TenantCreate, admin: dict = Depends(require_admin)):
    """Create a new tenant with first MANAGER user (Admin only)."""
    db = SupabasePersistence(tenant_id=None)
    
    # Check if user exists
    existing = db.client.table("utm_users").select("user_id").or_(
        f"email.eq.{payload.email},username.eq.{payload.username}"
    ).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # 1. Create tenant (organization)
    # Validate tier
    tier = payload.tier or "STANDARD"
    if tier not in ["STANDARD", "PREMIUM", "ENTERPRISE"]:
        tier = "STANDARD"
    
    new_tenant = {
        "display_name": payload.display_name,
        "tier": tier,
        "is_active": True
    }
    
    tenant_res = db.client.table("utm_tenants").insert(new_tenant).execute()
    tenant_id = tenant_res.data[0]["tenant_id"]
    
    # 2. Create manager user (first user of tenant)
    if not payload.password:
        raise HTTPException(status_code=400, detail="Password required")
    
    new_user = {
        "tenant_id": tenant_id,
        "user_id": tenant_id,  # v3.9: user_id = tenant_id for backward compatibility
        "email": payload.email or f"{payload.username}@legacy.local",
        "username": payload.username,
        "password_hash_bcrypt": hash_password_bcrypt(payload.password),
        "role": "MANAGER",  # First user is always MANAGER
        "is_active": True,
        "display_name": payload.username
    }
    
    db.client.table("utm_users").insert(new_user).execute()
    
    return {"success": True, "tenant_id": tenant_id}


@router.patch("/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, payload: TenantUpdate, admin: dict = Depends(require_admin)):
    """Update tenant details (Admin only)."""
    db = SupabasePersistence(tenant_id=None)
    
    # Update tenant info
    tenant_update = {}
    if hasattr(payload, 'display_name') and payload.display_name:
        tenant_update["display_name"] = payload.display_name
    if hasattr(payload, 'tier') and payload.tier:
        if payload.tier in ["STANDARD", "PREMIUM", "ENTERPRISE"]:
            tenant_update["tier"] = payload.tier
    
    if tenant_update:
        db.client.table("utm_tenants").update(tenant_update).eq("tenant_id", tenant_id).execute()
    
    # Update manager user (first user of tenant)
    user_update = {}
    if payload.role: 
        # Validate role
        if payload.role not in ["MANAGER", "COLLABORATOR", "VIEWER"]:
            raise HTTPException(status_code=400, detail="Invalid role. Must be MANAGER, COLLABORATOR, or VIEWER")
        user_update["role"] = payload.role
    if payload.password:
        user_update["password_hash_bcrypt"] = hash_password_bcrypt(payload.password)
    
    if user_update:
        db.client.table("utm_users").update(user_update).eq("tenant_id", tenant_id).eq("user_id", tenant_id).execute()
    
    return {"success": True}


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, admin: dict = Depends(require_admin)):
    """Remove a tenant (Admin only)."""
    db = SupabasePersistence(tenant_id=None)
    db.client.table("utm_tenants").delete().eq("tenant_id", tenant_id).execute()
    return {"success": True}


# --- User Self-Service ---

@router.post("/change-password")
async def change_password(payload: PasswordChange, identity: dict = Depends(get_identity)):
    """User changes their own password (v3.9: uses utm_users)."""
    user_id = identity.get("user_id") or identity.get("tenant_id")  # Backward compatible
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid Session")

    db = SupabasePersistence(tenant_id=None)
    
    # 1. Fetch current user from utm_users
    res = db.client.table("utm_users").select(
        "user_id, password_hash_bcrypt"
    ).eq("user_id", user_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")
        
    user = res.data[0]
    
    # 2. Verify current password
    password_valid = verify_password_bcrypt(payload.current_password, user["password_hash_bcrypt"])
        
    if not password_valid:
        raise HTTPException(status_code=400, detail="Current password incorrect")
        
    # 3. Update to new bcrypt hash
    new_hash = hash_password_bcrypt(payload.new_password)
    db.client.table("utm_users").update({
        "password_hash_bcrypt": new_hash,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("user_id", user_id).execute()
    
    return {"success": True, "message": "Password updated successfully"}


# --- User Management (MANAGER) ---

@router.get("/users")
async def list_tenant_users(manager: dict = Depends(require_manager)):
    """
    List all users in the MANAGER's tenant.
    MANAGER and ADMIN can use this endpoint.
    """
    tenant_id = manager.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    db = SupabasePersistence(tenant_id=tenant_id)
    
    # Get all users in this tenant
    res = db.client.table("utm_users").select(
        "user_id, email, username, role, is_active, display_name, created_at, last_login"
    ).eq("tenant_id", tenant_id).order("role", desc=True).order("username").execute()
    
    return {"users": res.data}


@router.post("/users")
async def create_tenant_user(payload: UserCreate, manager: dict = Depends(require_manager)):
    """
    Create a new user in the MANAGER's tenant.
    MANAGER can create COLLABORATOR or VIEWER users.
    Only ADMIN can create MANAGER users.
    """
    tenant_id = manager.get("tenant_id")
    manager_role = manager.get("role")
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    # Security: Only ADMIN can create MANAGER users
    if payload.role == "MANAGER" and manager_role != "ADMIN":
        raise HTTPException(
            status_code=403, 
            detail="Only ADMIN can create MANAGER users"
        )
    
    # Security: Cannot create ADMIN users via this endpoint
    if payload.role == "ADMIN":
        raise HTTPException(
            status_code=403, 
            detail="Cannot create ADMIN users via this endpoint"
        )
    
    # Validate role
    if payload.role not in ["MANAGER", "COLLABORATOR", "VIEWER"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    db = SupabasePersistence(tenant_id=tenant_id)
    
    # Check if username or email already exists
    existing = db.client.table("utm_users").select("user_id").or_(
        f"username.eq.{payload.username},email.eq.{payload.email}"
    ).execute()
    
    if existing.data:
        raise HTTPException(
            status_code=400, 
            detail="Username or email already exists"
        )
    
    # Generate password if not provided
    password = payload.password
    if not password:
        # Generate secure random password
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
    
    # Hash password with bcrypt
    password_hash = hash_password_bcrypt(password)
    
    # Create user
    new_user = {
        "tenant_id": tenant_id,
        "username": payload.username,
        "email": payload.email,
        "password_hash_bcrypt": password_hash,
        "role": payload.role,
        "display_name": payload.display_name or payload.username,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }
    
    result = db.client.table("utm_users").insert(new_user).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create user")
    
    created_user = result.data[0]
    
    # Return user info with temporary password
    return {
        "success": True,
        "user": {
            "user_id": created_user["user_id"],
            "username": created_user["username"],
            "email": created_user["email"],
            "role": created_user["role"]
        },
        "temporary_password": password if not payload.password else None,
        "message": f"User {payload.username} created successfully"
    }


@router.patch("/users/{user_id}")
async def update_tenant_user(
    user_id: str, 
    payload: UserUpdate, 
    manager: dict = Depends(require_manager)
):
    """
    Update a user in the MANAGER's tenant.
    Can update role, active status, and display name.
    """
    tenant_id = manager.get("tenant_id")
    manager_role = manager.get("role")
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    db = SupabasePersistence(tenant_id=tenant_id)
    
    # Verify user exists and belongs to this tenant
    user_res = db.client.table("utm_users").select(
        "user_id, role"
    ).eq("user_id", user_id).eq("tenant_id", tenant_id).execute()
    
    if not user_res.data:
        raise HTTPException(status_code=404, detail="User not found in your tenant")
    
    current_user = user_res.data[0]
    
    # Security: Only ADMIN can modify MANAGER users
    if current_user["role"] == "MANAGER" and manager_role != "ADMIN":
        raise HTTPException(
            status_code=403, 
            detail="Only ADMIN can modify MANAGER users"
        )
    
    # Security: Cannot change role to ADMIN
    if payload.role == "ADMIN":
        raise HTTPException(
            status_code=403, 
            detail="Cannot assign ADMIN role via this endpoint"
        )
    
    # Security: Only ADMIN can promote to MANAGER
    if payload.role == "MANAGER" and manager_role != "ADMIN":
        raise HTTPException(
            status_code=403, 
            detail="Only ADMIN can promote users to MANAGER"
        )
    
    # Build update dict
    updates = {"updated_at": datetime.utcnow().isoformat()}
    
    if payload.role is not None:
        if payload.role not in ["MANAGER", "COLLABORATOR", "VIEWER"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        updates["role"] = payload.role
    
    if payload.is_active is not None:
        updates["is_active"] = payload.is_active
    
    if payload.display_name is not None:
        updates["display_name"] = payload.display_name
    
    if payload.email is not None:
        # Check if email already exists in this tenant
        email_check = db.client.table("utm_users").select("user_id").eq(
            "email", payload.email
        ).eq("tenant_id", tenant_id).neq("user_id", user_id).execute()
        
        if email_check.data:
            raise HTTPException(status_code=400, detail="Email already in use by another user")
        
        updates["email"] = payload.email
    
    # Update user
    db.client.table("utm_users").update(updates).eq("user_id", user_id).execute()
    
    return {
        "success": True,
        "message": f"User {user_id} updated successfully"
    }


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    payload: UserPasswordReset,
    manager: dict = Depends(require_manager)
):
    """
    Reset a user's password.
    MANAGER can reset passwords for users in their tenant.
    """
    tenant_id = manager.get("tenant_id")
    manager_role = manager.get("role")
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    db = SupabasePersistence(tenant_id=tenant_id)
    
    # Verify user exists and belongs to this tenant
    user_res = db.client.table("utm_users").select(
        "user_id, username, role"
    ).eq("user_id", user_id).eq("tenant_id", tenant_id).execute()
    
    if not user_res.data:
        raise HTTPException(status_code=404, detail="User not found in your tenant")
    
    target_user = user_res.data[0]
    
    # Security: Only ADMIN can reset MANAGER passwords
    if target_user["role"] == "MANAGER" and manager_role != "ADMIN":
        raise HTTPException(
            status_code=403, 
            detail="Only ADMIN can reset MANAGER passwords"
        )
    
    # Hash new password
    new_hash = hash_password_bcrypt(payload.new_password)
    
    # Update password
    db.client.table("utm_users").update({
        "password_hash_bcrypt": new_hash,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("user_id", user_id).execute()
    
    return {
        "success": True,
        "message": f"Password reset for user {target_user['username']}"
    }


@router.patch("/auth/users/{user_id}/reset-password")
async def admin_reset_user_password(
    user_id: str,
    payload: UserPasswordReset,
    admin: dict = Depends(require_admin)
):
    """
    Platform ADMIN endpoint to reset any user's password across all tenants.
    Used by All Users Dashboard for cross-tenant user management.
    """
    # Platform ADMIN can reset ANY user password without tenant restrictions
    db = SupabasePersistence(tenant_id=admin.get("tenant_id"))
    
    # Verify user exists (no tenant restriction)
    user_res = db.client.table("utm_users").select(
        "user_id, username, tenant_id, role"
    ).eq("user_id", user_id).execute()
    
    if not user_res.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    target_user = user_res.data[0]
    
    # Hash new password
    new_hash = hash_password_bcrypt(payload.new_password)
    
    # Update password (ADMIN can reset anyone's password)
    db.client.table("utm_users").update({
        "password_hash_bcrypt": new_hash,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("user_id", user_id).execute()
    
    return {
        "success": True,
        "message": f"Password reset for user {target_user['username']} (tenant: {target_user['tenant_id'][:8]}...)"
    }


# --- Admin Impersonation (v3.9) ---

class ImpersonatePayload(BaseModel):
    target_user_id: str  # User to impersonate (preferably MANAGER)


@router.post("/admin/impersonate")
async def start_impersonation(payload: ImpersonatePayload, admin: dict = Depends(require_admin)):
    """
    ADMIN impersonates another user for support purposes.
    Returns user context to be used with X-Impersonate-User-ID header.
    """
    db = SupabasePersistence(tenant_id=None)
    
    # Verify target user exists
    target_res = db.client.table("utm_users").select(
        "user_id, tenant_id, email, username, role"
    ).eq("user_id", payload.target_user_id).execute()
    
    if not target_res.data:
        raise HTTPException(status_code=404, detail="Target user not found")
    
    target_user = target_res.data[0]
    
    # Get tenant info
    tenant_res = db.client.table("utm_tenants").select(
        "display_name"
    ).eq("tenant_id", target_user["tenant_id"]).execute()
    
    tenant = tenant_res.data[0] if tenant_res.data else {"display_name": "Unknown"}
    
    print(f"[IMPERSONATE] ADMIN starting impersonation of {target_user['username']} ({target_user['user_id']})")
    
    return {
        "success": True,
        "impersonate": {
            "user_id": target_user["user_id"],
            "tenant_id": target_user["tenant_id"],
            "username": target_user["username"],
            "email": target_user["email"],
            "role": target_user["role"],
            "display_name": tenant["display_name"]
        },
        "message": f"Now impersonating {target_user['username']} ({target_user['role']}) from {tenant['display_name']}"
    }


@router.post("/admin/stop-impersonate")
async def stop_impersonation(admin: dict = Depends(require_admin)):
    """
    Stops current impersonation session.
    Frontend should remove X-Impersonate-User-ID header.
    """
    print(f"[IMPERSONATE] ADMIN stopping impersonation")
    
    return {
        "success": True,
        "message": "Impersonation session ended. Returning to admin context."
    }


@router.get("/admin/users")
async def list_all_users(admin: dict = Depends(require_admin)):
    """
    List all users in the system (for impersonation selection).
    Admin only.
    """
    db = SupabasePersistence(tenant_id=None)
    
    # Get all users with tenant info
    res = db.client.table("utm_users").select(
        "user_id, tenant_id, email, username, role, is_active, display_name"
    ).order("username").execute()
    
    users = []
    for user in res.data:
        # Get tenant info
        tenant_res = db.client.table("utm_tenants").select(
            "display_name"
        ).eq("tenant_id", user["tenant_id"]).execute()
        
        tenant = tenant_res.data[0] if tenant_res.data else {"display_name": "Unknown"}
        
        users.append({
            "user_id": user["user_id"],
            "tenant_id": user["tenant_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "is_active": user.get("is_active", True),
            "display_name": user.get("display_name", user["username"]),
            "tenant_display_name": tenant["display_name"]
        })
    
    return {"users": users}


# NOTE: invite and reset-password endpoints deprecated in v3.9
# Will be reimplemented using utm_user_invitations table
