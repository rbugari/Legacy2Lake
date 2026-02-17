"""
Prompts Router - v4.0 Zero-Hardcode Core
==========================================

Handles CRUD operations for dynamic prompts stored in database.

Features:
- List prompts (with filtering)
- Get single prompt
- Create prompt (ADMIN only)
- Update prompt (ADMIN only)
- Delete prompt (ADMIN only)
- View prompt history (ADMIN only)
- Test prompt assembly

Author: Legacy2Lake Engineering
Date: February 14, 2026
Version: v4.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from apps.api.services.persistence_service import SupabasePersistence
from apps.api.services.prompts.prompt_service import PromptService, Prompt
from apps.api.services.prompts.prompt_assembler import PromptAssembler
from apps.api.routers.dependencies import get_db, get_identity

router = APIRouter(prefix="/api/v1/prompts", tags=["Prompts (v4.0)"])


# ================================================================
# REQUEST / RESPONSE MODELS
# ================================================================

class CreatePromptRequest(BaseModel):
    """Request model for creating a new prompt"""
    prompt_id: str = Field(..., description="Unique prompt identifier (e.g., 'agent_c_bronze_pyspark')")
    content: str = Field(..., description="Prompt template content with {{variable}} placeholders")
    tech_stack: Optional[str] = Field(None, description="Technology: pyspark, snowflake, dbt, fabric, aws, gcp")
    pattern_type: Optional[str] = Field(None, description="Pattern: bronze, silver, gold, incremental, scd")
    agent_id: Optional[str] = Field(None, description="Agent: agent-a, agent-c, agent-f, agent-g, agent-s, agent-d")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class UpdatePromptRequest(BaseModel):
    """Request model for updating an existing prompt"""
    content: Optional[str] = Field(None, description="New prompt content")
    tech_stack: Optional[str] = Field(None, description="New technology")
    pattern_type: Optional[str] = Field(None, description="New pattern")
    agent_id: Optional[str] = Field(None, description="New agent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="New metadata")
    is_active: Optional[bool] = Field(None, description="Active status")


class TestPromptRequest(BaseModel):
    """Request model for testing prompt assembly"""
    prompt_id: str = Field(..., description="Prompt ID to test")
    context: Dict[str, Any] = Field(..., description="Context variables for assembly")
    format: str = Field("simple", description="Assembly format: simple, handlebars, jinja2")


class PromptResponse(BaseModel):
    """Response model for a single prompt"""
    prompt_id: str
    content: str
    tech_stack: Optional[str]
    pattern_type: Optional[str]
    agent_id: Optional[str]
    is_active: bool
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class PromptListResponse(BaseModel):
    """Response model for list of prompts"""
    prompts: List[PromptResponse]
    total: int


class PromptHistoryResponse(BaseModel):
    """Response model for prompt history"""
    history_id: str
    prompt_id: str
    content: str
    changed_by: Optional[str]
    changed_at: str
    metadata: Optional[Dict[str, Any]]


# ================================================================
# ENDPOINTS
# ================================================================

@router.get("", response_model=PromptListResponse)
async def list_prompts(
    agent_id: Optional[str] = Query(None, description="Filter by agent"),
    tech_stack: Optional[str] = Query(None, description="Filter by technology"),
    pattern_type: Optional[str] = Query(None, description="Filter by pattern"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: SupabasePersistence = Depends(get_db)
):
    """
    List all prompts with optional filtering.
    
    Available for all authenticated users (read-only).
    """
    try:
        prompt_service = PromptService(tenant_id=db.tenant_id, client_id=db.client_id)
        
        prompts = await prompt_service.list_prompts(
            agent_id=agent_id,
            tech_stack=tech_stack,
            pattern_type=pattern_type,
            is_active=is_active
        )
        
        prompt_responses = [PromptResponse(**prompt.to_dict()) for prompt in prompts]
        
        return PromptListResponse(
            prompts=prompt_responses,
            total=len(prompt_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list prompts: {str(e)}")


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Get a single prompt by ID.
    
    Available for all authenticated users (read-only).
    """
    try:
        prompt_service = PromptService(tenant_id=db.tenant_id, client_id=db.client_id)
        
        prompt = await prompt_service.get_prompt(prompt_id, use_cache=False)
        
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_id}")
        
        return PromptResponse(**prompt.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prompt: {str(e)}")


@router.post("", response_model=PromptResponse, status_code=201)
async def create_prompt(
    payload: CreatePromptRequest,
    db: SupabasePersistence = Depends(get_db),
    identity: Dict[str, Any] = Depends(get_identity)
):
    """
    Create a new prompt.
    
    **ADMIN ONLY** - Requires admin role.
    """
    try:
        # Check admin role
        user_role = identity.get("role")
        if user_role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin role required to create prompts"
            )
        
        prompt_service = PromptService(tenant_id=db.tenant_id, client_id=db.client_id)
        
        # Check if prompt already exists
        existing = await prompt_service.get_prompt(payload.prompt_id, use_cache=False)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Prompt already exists: {payload.prompt_id}"
            )
        
        # Create prompt
        prompt = await prompt_service.create_prompt(
            prompt_id=payload.prompt_id,
            content=payload.content,
            tech_stack=payload.tech_stack,
            pattern_type=payload.pattern_type,
            agent_id=payload.agent_id,
            metadata=payload.metadata,
            created_by=identity.get("user_id")
        )
        
        return PromptResponse(**prompt.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create prompt: {str(e)}")


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str,
    payload: UpdatePromptRequest,
    db: SupabasePersistence = Depends(get_db),
    identity: Dict[str, Any] = Depends(get_identity)
):
    """
    Update an existing prompt.
    
    **ADMIN ONLY** - Requires admin role.
    
    Note: Update will trigger automatic versioning (saved to utm_prompts_history).
    """
    try:
        # Check admin role
        user_role = identity.get("role")
        if user_role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin role required to update prompts"
            )
        
        prompt_service = PromptService(tenant_id=db.tenant_id, client_id=db.client_id)
        
        # Check if prompt exists
        existing = await prompt_service.get_prompt(prompt_id, use_cache=False)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_id}")
        
        # Update prompt
        prompt = await prompt_service.update_prompt(
            prompt_id=prompt_id,
            content=payload.content,
            tech_stack=payload.tech_stack,
            pattern_type=payload.pattern_type,
            agent_id=payload.agent_id,
            metadata=payload.metadata,
            is_active=payload.is_active,
            updated_by=identity.get("user_id")
        )
        
        return PromptResponse(**prompt.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update prompt: {str(e)}")


@router.delete("/{prompt_id}", status_code=204)
async def delete_prompt(
    prompt_id: str,
    db: SupabasePersistence = Depends(get_db),
    identity: Dict[str, Any] = Depends(get_identity)
):
    """
    Delete a prompt.
    
    **ADMIN ONLY** - Requires admin role.
    
    Caution: Consider using soft delete (set is_active=false) instead.
    """
    try:
        # Check admin role
        user_role = identity.get("role")
        if user_role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin role required to delete prompts"
            )
        
        prompt_service = PromptService(tenant_id=db.tenant_id, client_id=db.client_id)
        
        # Check if prompt exists
        existing = await prompt_service.get_prompt(prompt_id, use_cache=False)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_id}")
        
        # Delete prompt
        await prompt_service.delete_prompt(prompt_id)
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete prompt: {str(e)}")


@router.get("/{prompt_id}/history")
async def get_prompt_history(
    prompt_id: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum history records to return"),
    db: SupabasePersistence = Depends(get_db),
    identity: Dict[str, Any] = Depends(get_identity)
):
    """
    Get version history for a prompt.
    
    **ADMIN ONLY** - Requires admin role.
    
    History is automatically saved by database trigger when prompts are updated.
    """
    try:
        # Check admin role
        user_role = identity.get("role")
        if user_role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin role required to view prompt history"
            )
        
        prompt_service = PromptService(tenant_id=db.tenant_id, client_id=db.client_id)
        
        # Check if prompt exists
        existing = await prompt_service.get_prompt(prompt_id, use_cache=False)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_id}")
        
        # Get history
        history = await prompt_service.get_prompt_history(prompt_id, limit=limit)
        
        return {
            "prompt_id": prompt_id,
            "history": history,
            "total": len(history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prompt history: {str(e)}")


@router.post("/test", response_model=Dict[str, Any])
async def test_prompt_assembly(
    payload: TestPromptRequest,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Test prompt assembly with context injection.
    
    Useful for testing prompts before deploying to production.
    Available for all authenticated users.
    """
    try:
        prompt_service = PromptService(tenant_id=db.tenant_id, client_id=db.client_id)
        prompt_assembler = PromptAssembler()
        
        # Get prompt
        prompt = await prompt_service.get_prompt(payload.prompt_id, use_cache=False)
        
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt not found: {payload.prompt_id}")
        
        # Assemble prompt with context
        assembled = prompt_assembler.build(
            base_prompt=prompt.content,
            context=payload.context,
            format=payload.format
        )
        
        return {
            "prompt_id": payload.prompt_id,
            "original_content": prompt.content,
            "assembled_content": assembled,
            "context": payload.context,
            "format": payload.format,
            "original_length": len(prompt.content),
            "assembled_length": len(assembled)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test prompt assembly: {str(e)}")


@router.post("/cache/clear", status_code=204)
async def clear_prompt_cache(
    db: SupabasePersistence = Depends(get_db),
    identity: Dict[str, Any] = Depends(get_identity)
):
    """
    Clear prompt cache.
    
    **ADMIN ONLY** - Requires admin role.
    
    Use after updating prompts to ensure changes are immediately visible.
    """
    try:
        # Check admin role
        user_role = identity.get("role")
        if user_role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin role required to clear cache"
            )
        
        prompt_service = PromptService(tenant_id=db.tenant_id, client_id=db.client_id)
        prompt_service.clear_cache()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
