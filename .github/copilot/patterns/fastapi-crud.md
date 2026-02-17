# FastAPI CRUD Router Pattern

**Category:** Backend - API Routers  
**Use Case:** Creating standardized CRUD endpoints for resources

## Pattern Template

```python
"""
{Resource} Router
==================

Purpose:
    {Description of what this router manages}

Endpoints:
    GET    /api/v1/{resource}              - List all {resources}
    GET    /api/v1/{resource}/{id}         - Get specific {resource}
    POST   /api/v1/{resource}              - Create new {resource}
    PATCH  /api/v1/{resource}/{id}         - Update {resource}
    DELETE /api/v1/{resource}/{id}         - Delete {resource}

Author: Legacy2Lake Engineering
Date: {Current Date}
Version: v1.0
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID

try:
    from apps.api.routers.dependencies import get_db
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.utils.logger import logger
except ImportError:
    from routers.dependencies import get_db
    from services.persistence_service import SupabasePersistence
    from utils.logger import logger


# ================================================================
# ROUTER INITIALIZATION
# ================================================================

router = APIRouter(
    prefix="/api/v1/{resource}",
    tags=["{resource}"]
)


# ================================================================
# REQUEST/RESPONSE MODELS
# ================================================================

class Create{Resource}Request(BaseModel):
    """Request model for creating a {resource}"""
    name: str = Field(..., description="{Resource} name")
    description: Optional[str] = Field(None, description="Optional description")
    settings: Optional[Dict[str, Any]] = Field(None, description="Additional settings")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Example {Resource}",
                "description": "This is an example",
                "settings": {"key": "value"}
            }
        }


class Update{Resource}Request(BaseModel):
    """Request model for updating a {resource}"""
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class {Resource}Response(BaseModel):
    """{Resource} response model"""
    {resource}_id: str
    tenant_id: str
    name: str
    description: Optional[str]
    settings: Dict[str, Any]
    status: str
    created_at: str
    updated_at: str


class {Resource}ListResponse(BaseModel):
    """List response with pagination"""
    {resources}: List[{Resource}Response]
    total: int
    page: int = 1
    page_size: int = 50


# ================================================================
# ENDPOINTS
# ================================================================

@router.get("/", response_model={Resource}ListResponse)
async def list_{resources}(
    page: int = 1,
    page_size: int = 50,
    status: Optional[str] = None,
    db: SupabasePersistence = Depends(get_db)
):
    """
    List all {resources} for current tenant.
    
    Query Parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 50, max: 100)
        - status: Filter by status (optional)
    """
    logger.info(
        f"[{Resource}Router] Listing {resources}: page={page}, size={page_size}",
        "{Resource}Router"
    )
    
    try:
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build query
        query = db.client.table("utm_{resources}").select("*", count="exact")
        
        # Apply tenant filter
        if db.tenant_id:
            query = query.eq("tenant_id", db.tenant_id)
        
        # Apply status filter if provided
        if status:
            query = query.eq("status", status)
        
        # Apply pagination
        query = query.range(offset, offset + page_size - 1).order("created_at", desc=True)
        
        # Execute query
        result = query.execute()
        
        return {Resource}ListResponse(
            {resources}=result.data,
            total=result.count or 0,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        logger.error(f"[{Resource}Router] Failed to list {resources}: {e}", "{Resource}Router")
        raise HTTPException(status_code=500, detail=f"Failed to list {resources}: {str(e)}")


@router.get("/{{{resource}_id}}", response_model={Resource}Response)
async def get_{resource}(
    {resource}_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Get specific {resource} by ID.
    
    Path Parameters:
        - {resource}_id: UUID of the {resource}
    """
    logger.info(f"[{Resource}Router] Getting {resource}: {resource}_id={{resource}_id}", "{Resource}Router")
    
    try:
        # Validate UUID
        try:
            UUID({resource}_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid {resource} ID format")
        
        # Query {resource}
        query = db.client.table("utm_{resources}").select("*").eq("{resource}_id", {resource}_id)
        
        # Apply tenant filter
        if db.tenant_id:
            query = query.eq("tenant_id", db.tenant_id)
        
        result = query.execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="{Resource} not found")
        
        return {Resource}Response(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{Resource}Router] Failed to get {resource}: {e}", "{Resource}Router")
        raise HTTPException(status_code=500, detail=f"Failed to get {resource}: {str(e)}")


@router.post("/", response_model={Resource}Response, status_code=201)
async def create_{resource}(
    payload: Create{Resource}Request,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Create new {resource}.
    
    Request Body:
        - name: {Resource} name (required)
        - description: Optional description
        - settings: Additional settings (optional)
    """
    logger.info(f"[{Resource}Router] Creating {resource}: name={payload.name}", "{Resource}Router")
    
    try:
        # Prepare data
        data = {
            "tenant_id": db.tenant_id,
            "name": payload.name,
            "description": payload.description,
            "settings": payload.settings or {},
            "status": "active",
            "created_by": db.user_id  # If user_id is tracked
        }
        
        # Insert into database
        result = db.client.table("utm_{resources}").insert(data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create {resource}")
        
        logger.info(
            f"[{Resource}Router] ✅ {Resource} created: {resource}_id={result.data[0]['{resource}_id']}",
            "{Resource}Router"
        )
        
        return {Resource}Response(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{Resource}Router] Failed to create {resource}: {e}", "{Resource}Router")
        raise HTTPException(status_code=500, detail=f"Failed to create {resource}: {str(e)}")


@router.patch("/{{{resource}_id}}", response_model={Resource}Response)
async def update_{resource}(
    {resource}_id: str,
    payload: Update{Resource}Request,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Update existing {resource}.
    
    Path Parameters:
        - {resource}_id: UUID of the {resource}
    
    Request Body:
        - Fields to update (all optional)
    """
    logger.info(f"[{Resource}Router] Updating {resource}: {resource}_id={{resource}_id}", "{Resource}Router")
    
    try:
        # Validate UUID
        try:
            UUID({resource}_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid {resource} ID format")
        
        # Check if {resource} exists
        existing = db.client.table("utm_{resources}") \
            .select("{resource}_id") \
            .eq("{resource}_id", {resource}_id)
        
        if db.tenant_id:
            existing = existing.eq("tenant_id", db.tenant_id)
        
        existing_result = existing.execute()
        
        if not existing_result.data:
            raise HTTPException(status_code=404, detail="{Resource} not found")
        
        # Prepare update data (only include provided fields)
        update_data = {}
        if payload.name is not None:
            update_data["name"] = payload.name
        if payload.description is not None:
            update_data["description"] = payload.description
        if payload.settings is not None:
            update_data["settings"] = payload.settings
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = "NOW()"
        
        # Perform update
        result = db.client.table("utm_{resources}") \
            .update(update_data) \
            .eq("{resource}_id", {resource}_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update {resource}")
        
        logger.info(f"[{Resource}Router] ✅ {Resource} updated: {resource}_id={{resource}_id}", "{Resource}Router")
        
        return {Resource}Response(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{Resource}Router] Failed to update {resource}: {e}", "{Resource}Router")
        raise HTTPException(status_code=500, detail=f"Failed to update {resource}: {str(e)}")


@router.delete("/{{{resource}_id}}", status_code=204)
async def delete_{resource}(
    {resource}_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Delete {resource} by ID.
    
    Path Parameters:
        - {resource}_id: UUID of the {resource}
    """
    logger.info(f"[{Resource}Router] Deleting {resource}: {resource}_id={{resource}_id}", "{Resource}Router")
    
    try:
        # Validate UUID
        try:
            UUID({resource}_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid {resource} ID format")
        
        # Check if {resource} exists
        query = db.client.table("utm_{resources}") \
            .select("{resource}_id") \
            .eq("{resource}_id", {resource}_id)
        
        if db.tenant_id:
            query = query.eq("tenant_id", db.tenant_id)
        
        result = query.execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="{Resource} not found")
        
        # Delete {resource}
        db.client.table("utm_{resources}") \
            .delete() \
            .eq("{resource}_id", {resource}_id) \
            .execute()
        
        logger.info(f"[{Resource}Router] ✅ {Resource} deleted: {resource}_id={{resource}_id}", "{Resource}Router")
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{Resource}Router] Failed to delete {resource}: {e}", "{Resource}Router")
        raise HTTPException(status_code=500, detail=f"Failed to delete {resource}: {str(e)}")
```

## Usage Example

```python
# Create a new router for "workflows" resource:
# 1. Copy this template
# 2. Replace {Resource} with Workflow
# 3. Replace {resource} with workflow
# 4. Replace {resources} with workflows
# 5. Adjust model fields as needed
# 6. Add custom business logic if required
```

## Key Features

- ✅ Multi-tenancy enforcement via `get_db` dependency
- ✅ UUID validation for IDs
- ✅ Proper error handling with HTTP exceptions
- ✅ Structured logging with context
- ✅ Pagination support for list endpoints
- ✅ Optional filtering by status
- ✅ Pydantic models for type safety
- ✅ OpenAPI documentation support

## Testing

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_{resource}(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/{resources}",
        json={
            "name": "Test {Resource}",
            "description": "Test description"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test {Resource}"

@pytest.mark.asyncio
async def test_list_{resources}(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/{resources}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "{resources}" in data
    assert "total" in data
```
