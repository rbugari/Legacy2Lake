"""
Shared dependencies for FastAPI routers.
Centralizes authentication, database access, and common utilities.
"""
from fastapi import Header, Depends, HTTPException, Request
from typing import Optional
from services.persistence_service import SupabasePersistence
from supabase import create_client, Client
import os

# --- Supabase Client (Singleton) ---
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """Returns a singleton Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        _supabase_client = create_client(url, key)
    return _supabase_client


# --- Identity & Multi-tenancy ---
async def get_identity(
    request: Request,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"), 
    x_client_id: Optional[str] = Header(None, alias="X-Client-ID"),
    x_admin_tenant_id: Optional[str] = Header(None, alias="X-Admin-Tenant-ID")
) -> dict:
    """
    Extracts tenant identity from request headers.
    Supports Admin Impersonation:
    If X-Admin-Tenant-ID is provided and belongs to an ADMIN, 
    the context is set to X-Tenant-ID / X-Client-ID.
    """
    db_admin = SupabasePersistence(tenant_id=None)
    
    # 1. Check for Impersonation Attempt
    if x_admin_tenant_id:
        admin_user = await db_admin.get_tenant_by_id(x_admin_tenant_id)
        if admin_user and admin_user.get("role") == "ADMIN":
            print(f"[AUTH] Admin {x_admin_tenant_id} impersonating Tenant {x_tenant_id} for Client {x_client_id}")
            return {
                "tenant_id": x_tenant_id, 
                "client_id": x_client_id, 
                "admin_id": x_admin_tenant_id,
                "role": "ADMIN" # They keep their admin power even if impersonating
            }
        else:
            print(f"[AUTH] Unauthorized impersonation attempt by {x_admin_tenant_id}")
            raise HTTPException(status_code=403, detail="Unauthorized impersonation")

    # 2. Standard Identity
    # In a simple SaaS, we assume the frontend sends the correct headers.
    # [Fix] Sanitize non-UUID tenant_id which causes database syntax errors (Release 3.6)
    if x_tenant_id:
        import re
        # Basic UUID regex: 8-4-4-4-12 hex chars
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
        if not uuid_pattern.match(x_tenant_id):
            print(f"[AUTH] Sanitizing non-UUID tenant_id: {x_tenant_id}")
            x_tenant_id = None
        
    return {
        "tenant_id": x_tenant_id, 
        "client_id": x_client_id,
        "role": request.headers.get("X-Role", "USER")
    }


async def get_db(identity: dict = Depends(get_identity)) -> SupabasePersistence:
    """
    Returns a tenant-scoped database persistence instance.
    """
    return SupabasePersistence(
        tenant_id=identity["tenant_id"], 
        client_id=identity["client_id"]
    )


# --- Security Utilities ---
async def require_admin(identity: dict = Depends(get_identity)):
    """
    Dependency that ensures the user has administrative privileges.
    """
    if identity.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    return identity


async def require_auth(identity: dict = Depends(get_identity)):
    """
    Dependency that requires valid authentication headers.
    Use: Depends(require_auth)
    """
    if not identity.get("tenant_id"):
        raise HTTPException(
            status_code=401, 
            detail="Authentication required. Missing X-Tenant-ID header."
        )
    return identity
