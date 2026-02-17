"""
Project Members Router
Handles assignment of COLLABORATOR and VIEWER users to projects.
MANAGER users have automatic access to all projects in their tenant.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from apps.api.services.persistence_service import SupabasePersistence
from apps.api.routers.dependencies import get_db, require_manager

router = APIRouter(prefix="/projects", tags=["Project Members"])


class ProjectMemberAdd(BaseModel):
    """Add a user to a project."""
    user_id: str
    role: str  # COLLABORATOR or VIEWER


class ProjectMemberResponse(BaseModel):
    """Project member information."""
    project_id: str
    user_id: str
    username: str
    email: str
    role: str
    added_by: Optional[str]
    added_at: str


# --- List Members of a Project ---

@router.get("/{project_id}/members")
async def list_project_members(
    project_id: str,
    manager: dict = Depends(require_manager),
    db: SupabasePersistence = Depends(get_db)
):
    """
    List all members assigned to a specific project.
    Returns COLLABORATOR and VIEWER users (MANAGER users have automatic access).
    """
    tenant_id = manager.get("tenant_id")
    
    # Verify project belongs to this tenant
    project = db.client.table("utm_projects").select("project_id, name").eq(
        "project_id", project_id
    ).eq("tenant_id", tenant_id).execute()
    
    if not project.data:
        raise HTTPException(status_code=404, detail="Project not found in your tenant")
    
    # Get members
    members_res = db.client.table("utm_project_members").select(
        "project_id, user_id, role, added_by, added_at"
    ).eq("project_id", project_id).execute()
    
    # Enrich with user details
    enriched_members = []
    for member in members_res.data:
        user_res = db.client.table("utm_users").select(
            "username, email, display_name"
        ).eq("user_id", member["user_id"]).execute()
        
        if user_res.data:
            user = user_res.data[0]
            enriched_members.append({
                **member,
                "username": user["username"],
                "email": user["email"],
                "display_name": user.get("display_name")
            })
    
    return {
        "project": project.data[0],
        "members": enriched_members
    }


# --- Add Member to Project ---

@router.post("/{project_id}/members")
async def add_project_member(
    project_id: str,
    payload: ProjectMemberAdd,
    manager: dict = Depends(require_manager),
    db: SupabasePersistence = Depends(get_db)
):
    """
    Add a COLLABORATOR or VIEWER user to a project.
    Only MANAGER can use this endpoint.
    """
    tenant_id = manager.get("tenant_id")
    manager_user_id = manager.get("user_id") or None
    
    # Validate role
    if payload.role not in ["COLLABORATOR", "VIEWER"]:
        raise HTTPException(
            status_code=400, 
            detail="Role must be COLLABORATOR or VIEWER. MANAGER users have automatic access to all projects."
        )
    
    # Verify project belongs to this tenant
    project = db.client.table("utm_projects").select("project_id").eq(
        "project_id", project_id
    ).eq("tenant_id", tenant_id).execute()
    
    if not project.data:
        raise HTTPException(status_code=404, detail="Project not found in your tenant")
    
    # Verify user exists in this tenant and is COLLABORATOR or VIEWER
    user_res = db.client.table("utm_users").select("user_id, role").eq(
        "user_id", payload.user_id
    ).eq("tenant_id", tenant_id).execute()
    
    if not user_res.data:
        raise HTTPException(status_code=404, detail="User not found in your tenant")
    
    user_role = user_res.data[0]["role"]
    
    if user_role == "MANAGER":
        raise HTTPException(
            status_code=400, 
            detail="MANAGER users already have automatic access to all projects. No need to add them."
        )
    
    if user_role not in ["COLLABORATOR", "VIEWER"]:
        raise HTTPException(
            status_code=400, 
            detail=f"User has role {user_role}. Only COLLABORATOR and VIEWER users can be assigned to projects."
        )
    
    # Check if already a member
    existing = db.client.table("utm_project_members").select("*").eq(
        "project_id", project_id
    ).eq("user_id", payload.user_id).execute()
    
    if existing.data:
        raise HTTPException(status_code=400, detail="User is already a member of this project")
    
    # Add member
    db.client.table("utm_project_members").insert({
        "project_id": project_id,
        "user_id": payload.user_id,
        "role": payload.role,
        "added_by": manager_user_id,
        "added_at": datetime.utcnow().isoformat()
    }).execute()
    
    return {
        "success": True,
        "message": f"User added to project as {payload.role}"
    }


# --- Remove Member from Project ---

@router.delete("/{project_id}/members/{user_id}")
async def remove_project_member(
    project_id: str,
    user_id: str,
    manager: dict = Depends(require_manager),
    db: SupabasePersistence = Depends(get_db)
):
    """
    Remove a user from a project.
    Only MANAGER can use this endpoint.
    """
    tenant_id = manager.get("tenant_id")
    
    # Verify project belongs to this tenant
    project = db.client.table("utm_projects").select("project_id").eq(
        "project_id", project_id
    ).eq("tenant_id", tenant_id).execute()
    
    if not project.data:
        raise HTTPException(status_code=404, detail="Project not found in your tenant")
    
    # Remove member
    result = db.client.table("utm_project_members").delete().eq(
        "project_id", project_id
    ).eq("user_id", user_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="User is not a member of this project")
    
    return {
        "success": True,
        "message": "User removed from project"
    }


# --- Update Member Role ---

@router.patch("/{project_id}/members/{user_id}")
async def update_project_member_role(
    project_id: str,
    user_id: str,
    payload: dict,
    manager: dict = Depends(require_manager),
    db: SupabasePersistence = Depends(get_db)
):
    """
    Update a member's role in a project (e.g., VIEWER to COLLABORATOR).
    Only MANAGER can use this endpoint.
    """
    tenant_id = manager.get("tenant_id")
    new_role = payload.get("role")
    
    if not new_role or new_role not in ["COLLABORATOR", "VIEWER"]:
        raise HTTPException(status_code=400, detail="Role must be COLLABORATOR or VIEWER")
    
    # Verify project belongs to this tenant
    project = db.client.table("utm_projects").select("project_id").eq(
        "project_id", project_id
    ).eq("tenant_id", tenant_id).execute()
    
    if not project.data:
        raise HTTPException(status_code=404, detail="Project not found in your tenant")
    
    # Update member role
    result = db.client.table("utm_project_members").update({
        "role": new_role
    }).eq("project_id", project_id).eq("user_id", user_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="User is not a member of this project")
    
    return {
        "success": True,
        "message": f"Member role updated to {new_role}"
    }
