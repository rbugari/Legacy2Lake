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
import uuid
import re

# Import audit service
from apps.api.services.audit_log_service import get_audit_service, AuditEventType, AuditSeverity

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


# --- Security Validators (v4.0 → v4.1 Sprint 6) ---
def validate_tenant_id(request: Request, tenant_id: Optional[str]) -> str:
    """
    Validates X-Tenant-ID header for security (Sprint 4 + Sprint 6 Audit Log).
    
    Protects against:
    - SQL injection (e.g., ' OR '1'='1)
    - Path traversal (e.g., ../../../etc/passwd)
    - XSS attacks (e.g., <script>alert('xss')</script>)
    - Missing/empty headers
    - Duplicate headers
    - Non-UUID values
    
    Returns: Validated tenant_id as string
    Raises: HTTPException with 400/403 status on validation failure
    """
    audit = get_audit_service()
    client_ip = request.client.host if request.client else "unknown"
    endpoint = str(request.url.path)
    
    # Check for duplicate X-Tenant-ID headers
    tenant_headers = [k for k in request.headers.keys() if k.lower() == 'x-tenant-id']
    if len(tenant_headers) > 1:
        audit.log_event(
            event_type=AuditEventType.DUPLICATE_HEADERS,
            severity=AuditSeverity.WARNING,
            message=f"Multiple X-Tenant-ID headers detected from {client_ip}",
            ip_address=client_ip,
            endpoint=endpoint
        )
        raise HTTPException(
            status_code=400,
            detail="Bad Request: Multiple X-Tenant-ID headers detected. Provide exactly one."
        )
    
    # Require X-Tenant-ID header (not optional)
    if tenant_id is None:
        audit.log_auth_attempt(
            success=False,
            tenant_id=None,
            user_id=None,
            ip_address=client_ip,
            reason="Missing X-Tenant-ID header"
        )
        raise HTTPException(
            status_code=401,
            detail="Authentication required: Missing X-Tenant-ID header."
        )
    
    # Reject empty strings
    if not tenant_id or not tenant_id.strip():
        audit.log_auth_attempt(
            success=False,
            tenant_id=None,
            user_id=None,
            ip_address=client_ip,
            reason="Empty X-Tenant-ID header"
        )
        raise HTTPException(
            status_code=400,
            detail="Bad Request: X-Tenant-ID cannot be empty."
        )
    
    # Detect attack patterns before UUID validation
    violation_type = None
    if "'" in tenant_id or "OR" in tenant_id.upper() or "SELECT" in tenant_id.upper() or "UNION" in tenant_id.upper() or "DROP" in tenant_id.upper():
        violation_type = "sql_injection"
    elif "<script" in tenant_id.lower() or "javascript:" in tenant_id.lower() or "onerror=" in tenant_id.lower():
        violation_type = "xss"
    elif ".." in tenant_id or "/" in tenant_id or "\\" in tenant_id:
        violation_type = "path_traversal"
    
    # Log security violation and REJECT immediately if detected
    if violation_type:
        audit.log_security_violation(
            violation_type=violation_type,
            attempted_value=tenant_id,
            ip_address=client_ip,
            endpoint=endpoint,
            tenant_id=None
        )
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Security violation detected ({violation_type})"
        )
    
    # Validate UUID format (strict RFC 4122 validation)
    try:
        # Attempt to parse as UUID - raises ValueError if invalid
        parsed_uuid = uuid.UUID(tenant_id)
        
        # Additional check: ensure standard lowercase hex format matches (any version)
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        if not uuid_pattern.match(tenant_id):
            raise ValueError("UUID format validation failed")
        
        return tenant_id
        
    except (ValueError, AttributeError) as e:
        # Log invalid UUID attempt
        if not violation_type:  # Only log if not already logged as attack
            audit.log_security_violation(
                violation_type="invalid_uuid",
                attempted_value=tenant_id,
                ip_address=client_ip,
                endpoint=endpoint,
                tenant_id=None
            )
        
        print(f"[SECURITY] Invalid X-Tenant-ID rejected: {tenant_id[:50]}... (Error: {e})")
        raise HTTPException(
            status_code=403,
            detail="Forbidden: X-Tenant-ID must be a valid UUID v4."
        )


# --- Identity & Multi-tenancy (v3.9 → v4.1 Sprint 6) ---
async def get_identity(
    request: Request,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),  # Required + validated (v4.0)
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_client_id: Optional[str] = Header(None, alias="X-Client-ID"),
    x_impersonate_user_id: Optional[str] = Header(None, alias="X-Impersonate-User-ID")
) -> dict:
    """
    Extracts user/tenant identity from request headers (v4.0 - Security Hardened).
    
    Security Features (Sprint 4):
    - Validates X-Tenant-ID as required UUID v4 (protects against SQL injection, XSS, path traversal)
    - Rejects duplicate/empty headers
    - Validates user_id as UUID if provided
    
    Supports Admin Impersonation:
    If X-Impersonate-User-ID is provided, validates that current user is ADMIN
    and switches context to impersonated user while tracking admin_id.
    """
    # Step 1: Validate X-Tenant-ID (REQUIRED, Sprint 4 Security Fix)
    validated_tenant_id = validate_tenant_id(request, x_tenant_id)
    
    db = SupabasePersistence(tenant_id=None)
    
    # Step 2: Check for Impersonation (v3.9: ADMIN impersonates specific user)
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

    # Step 3: Validate user_id as UUID (if provided)
    if x_user_id:
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
        if not uuid_pattern.match(x_user_id):
            print(f"[AUTH] Invalid user_id format rejected: {x_user_id}")
            raise HTTPException(status_code=403, detail="Forbidden: X-User-ID must be a valid UUID")
        
    # Step 4: Return validated identity
    return {
        "tenant_id": validated_tenant_id,  # Always valid UUID (Sprint 4)
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
        client_id=identity.get("client_id"),
        role=identity.get("role")
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


async def check_project_permission(
    user_id: str, 
    project_id: str, 
    tenant_id: str,
    db_client: Client,
    required_roles: list = ["MANAGER", "COLLABORATOR", "VIEWER"]
) -> bool:
    """
    Check if a user has permission to access a specific project.
    
    Returns True if:
    - User is ADMIN (global role in utm_users)
    - User is MANAGER (tenant-level role, has access to all projects)
    - User is COLLABORATOR or VIEWER in utm_project_members for this project
    
    Args:
        user_id: The user's ID
        project_id: The project ID to check
        tenant_id: The tenant ID
        db_client: Supabase client
        required_roles: List of project roles that grant permission
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    if not user_id or not tenant_id:
        print(f"[check_project_permission] Missing identity: user_id={user_id}, tenant_id={tenant_id}")
        return False
        
    try:
        # Check global user role
        user_res = db_client.table("utm_users").select("role").eq("user_id", user_id).eq("tenant_id", tenant_id).execute()
        if user_res.data:
            user_role = user_res.data[0].get("role", "VIEWER")
            # ADMIN has access to everything
            if user_role == "ADMIN":
                return True
            # MANAGER has access to all projects in their tenant
            if user_role == "MANAGER":
                return True
        
        # Check project-specific role in utm_project_members
        member_res = db_client.table("utm_project_members").select("role").eq(
            "project_id", project_id
        ).eq("user_id", user_id).execute()
        
        if member_res.data:
            project_role = member_res.data[0].get("role", "VIEWER")
            return project_role in required_roles
        
        return False
        
    except Exception as e:
        # Log error but don't expose details
        print(f"[check_project_permission] Error: {e}")
        return False
