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
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"), 
    x_client_id: Optional[str] = Header(None, alias="X-Client-ID")
) -> dict:
    """
    Extracts tenant identity from request headers.
    Used for multi-tenant isolation.
    """
    return {"tenant_id": x_tenant_id, "client_id": x_client_id}


async def get_db(identity: dict = Depends(get_identity)) -> SupabasePersistence:
    """
    Returns a tenant-scoped database persistence instance.
    """
    return SupabasePersistence(
        tenant_id=identity["tenant_id"], 
        client_id=identity["client_id"]
    )


# --- Security Utilities ---
def verify_tenant_access(identity: dict, required_role: Optional[str] = None) -> bool:
    """
    Verifies the current user has access.
    Extend this for role-based access control.
    """
    if not identity.get("tenant_id"):
        return False
    # TODO: Add role verification when RBAC is implemented
    return True


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
