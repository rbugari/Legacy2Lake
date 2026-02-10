"""
Shared dependencies for FastAPI routers.
Centralizes authentication, database access, and common utilities.
"""
from fastapi import Header, Depends, HTTPException, Request
from typing import Optional
from apps.api.services.persistence_service import SupabasePersistence
from supabase import create_client, Client, ClientOptions
import os
import httpx

# --- Supabase Client (Singleton) ---
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """Returns a singleton Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        if not url or not key:
            raise ValueError(f"CRITICAL: SUPABASE_URL ('{url}') or SUPABASE_SERVICE_ROLE_KEY missing in environment.")
        
        _supabase_client = create_client(url, key)
            
    return _supabase_client


# --- Identity & Multi-tenancy (v3.9) ---
async def get_identity(
    request: Request,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"), 
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_client_id: Optional[str] = Header(None, alias="X-Client-ID"),
    x_impersonate_user_id: Optional[str] = Header(None, alias="X-Impersonate-User-ID")
) -> dict:
    """
    Extracts user/tenant identity from request headers (v3.9).
    
    Supports Admin Impersonation:
    If X-Impersonate-User-ID is provided, validates that current user is ADMIN
    and switches context to impersonated user while tracking admin_id.
    """
    db = SupabasePersistence(tenant_id=None)
    
    # 1. Check for Impersonation (v3.9: ADMIN impersonates specific user)
    if x_impersonate_user_id and x_user_id:
        # Verify admin user
        admin_res = db.client.table("utm_users").select(
            "user_id, role"
        ).eq("user_id", x_user_id).execute()
        
        if admin_res.data and admin_res.data[0].get("role") == "ADMIN":
            # Load impersonated user
            target_res = db.client.table("utm_users").select(
                "user_id, tenant_id, role"
            ).eq("user_id", x_impersonate_user_id).execute()
            
            if not target_res.data:
                raise HTTPException(status_code=404, detail="Impersonated user not found")
            
            target_user = target_res.data[0]
            
            # Get client_id from tenant
            tenant_res = db.client.table("utm_tenants").select(
                "client_id"
            ).eq("tenant_id", target_user["tenant_id"]).execute()
            
            target_client_id = tenant_res.data[0]["client_id"] if tenant_res.data else "UNKNOWN"
            
            print(f"[AUTH] ADMIN {x_user_id} impersonating User {x_impersonate_user_id}")
            
            return {
                "tenant_id": target_user["tenant_id"],
                "user_id": target_user["user_id"],
                "client_id": target_client_id,
                "role": target_user["role"],
                "admin_id": x_user_id,  # Track original admin
                "is_impersonating": True
            }
        else:
            print(f"[AUTH] Unauthorized impersonation attempt by {x_user_id}")
            raise HTTPException(status_code=403, detail="Only ADMIN can impersonate users")

    # 2. Standard Identity (v3.9: with user_id)
    # Sanitize UUIDs
    if x_tenant_id:
        import re
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
        if not uuid_pattern.match(x_tenant_id):
            print(f"[AUTH] Sanitizing non-UUID tenant_id: {x_tenant_id}")
            x_tenant_id = None
    
    if x_user_id:
        import re
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
        if not uuid_pattern.match(x_user_id):
            print(f"[AUTH] Sanitizing non-UUID user_id: {x_user_id}")
            x_user_id = None
        
    return {
        "tenant_id": x_tenant_id, 
        "user_id": x_user_id,
        "client_id": x_client_id,
        "role": request.headers.get("X-Role", "VIEWER"),
        "is_impersonating": False
    }


async def get_db(identity: dict = Depends(get_identity)) -> SupabasePersistence:
    """
    Returns a tenant-scoped database persistence instance (v3.9).
    """
    return SupabasePersistence(
        tenant_id=identity.get("tenant_id"), 
        user_id=identity.get("user_id"),
        client_id=identity.get("client_id")
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


async def require_manager(identity: dict = Depends(get_identity)):
    """
    Dependency that ensures the user has MANAGER or ADMIN role.
    MANAGERs can manage users within their tenant.
    """
    role = identity.get("role", "VIEWER")
    if role not in ["ADMIN", "MANAGER"]:
        raise HTTPException(
            status_code=403, 
            detail="Forbidden: Manager or Admin access required"
        )
    return identity
