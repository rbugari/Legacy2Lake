"""
System Router
Handles global configuration, model catalog, provider vault, and tech cartridges.
Migrated from main.py for v3.7.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os

from routers.dependencies import get_db
from services.persistence_service import SupabasePersistence, PersistenceService
from services.knowledge_service import KnowledgeService
from apps.api.utils.logger import logger

router = APIRouter(tags=["System & Administration"])

# --- Models ---

class CartridgeUpdate(BaseModel):
    id: str
    enabled: bool

class ProviderUpdate(BaseModel):
    id: str
    enabled: bool
    model: str = None
    api_key: str = None
    endpoint: str = None

# --- Technologies Catalog ---

@router.get("/config/technologies")
async def get_supported_technologies(db: SupabasePersistence = Depends(get_db)):
    """Returns valid source/target technologies from unified catalog."""
    try:
        data = await db.list_system_catalog()
        for item in data:
            if "role" not in item:
                item["role"] = "SOURCE" if item["type"] == "origin" else "TARGET"
            if "label" not in item:
                item["label"] = item["name"]
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prompts")
async def list_system_prompts(db: SupabasePersistence = Depends(get_db)):
    """Returns all available system prompts for management, directly from utm_prompts."""
    try:
        # 1. Fetch all active global prompts from DB
        res = db.client.table("utm_prompts") \
            .select("prompt_id, content") \
            .is_("tenant_id", "null") \
            .eq("is_active", True) \
            .execute()
            
        if not res.data:
            logger.warning("No active global prompts found in utm_prompts")
            return {"prompts": []}
            
        # 2. Map and format for frontend
        prompts = []
        for row in res.data:
            p_id = row["prompt_id"]
            content = row.get("content") or "--- EMPTY CONTENT ---"
            
            # Formatear nombre: agent_s_scout -> AGENT S SCOUT
            display_name = p_id.replace("_", " ").replace("-", " ").upper()
            
            prompts.append({
                "id": p_id,
                "name": display_name,
                "content": content
            })
            
        # Sort alphabetically by name
        prompts.sort(key=lambda x: x["name"])
        
        return {"prompts": prompts}
    except Exception as e:
        logger.error(f"Global error loading dynamic prompts from DB: {e}")
        raise HTTPException(status_code=500, detail="Failed to load system prompts")

@router.post("/validate")
async def validate_prompt(payload: dict, db: SupabasePersistence = Depends(get_db)):
    """Runs a quick validation test for a prompt."""
    agent_id = payload.get("agent_id")
    user_input = payload.get("user_input")
    prompt_content = payload.get("prompt_content") # Optional override from editor
    
    if not agent_id or not user_input:
        raise HTTPException(status_code=400, detail="agent_id and user_input required")
        
    from services.agent_a_service import AgentAService
    agent = AgentAService(tenant_id=db.tenant_id, client_id=db.client_id)
    llm = await agent._get_llm()
    
    current_prompt = prompt_content
    if not current_prompt:
        current_prompt = await agent._load_prompt()
        
    from langchain_core.messages import SystemMessage, HumanMessage
    messages = [
        SystemMessage(content=current_prompt),
        HumanMessage(content=user_input)
    ]
    
    response = await llm.ainvoke(messages)
    return {"success": True, "response": response.content}

@router.post("/scout/assess")
async def run_scout_assessment(payload: dict, db: SupabasePersistence = Depends(get_db)):
    """Runs a forensic assessment of project files using Agent S."""
    project_id = payload.get("project_id")
    file_list = payload.get("file_list")
    
    if not project_id or not file_list:
        raise HTTPException(status_code=400, detail="project_id and file_list required")
        
    from services.agent_s_service import AgentSService
    scout = AgentSService(tenant_id=db.tenant_id, client_id=db.client_id)
    
    try:
        # Agent S returns the assessment JSON
        report = await scout.assess_repository(file_list)
        return report
    except Exception as e:
        logger.error(f"Agent S assessment failed for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Model Catalog ---

@router.get("/catalog")
async def get_model_catalog(db: SupabasePersistence = Depends(get_db)):
    """Fetches the global model catalog (Filtered by Tenant/Vault)."""
    models = await db.list_models()
    return {"catalog": models}

@router.post("/catalog")
async def create_custom_model(payload: dict, db: SupabasePersistence = Depends(get_db)):
    """Adds a custom model to the catalog."""
    model_id = payload.get("id") or payload.get("model_id")
    if not model_id:
        raise HTTPException(status_code=400, detail="Model ID required")

    existing = db.client.table("utm_model_catalog").select("model_id").eq("model_id", model_id).execute()
    if existing.data:
         raise HTTPException(status_code=400, detail="Model ID already exists")
         
    data = {
        "model_id": model_id,
        "label": payload.get("name") or payload.get("label"),
        "provider": payload.get("provider_id") or payload.get("provider"),
        "context_window": int(payload.get("context") or payload.get("context_window") or 0),
        "deployment_id": payload.get("deployment_id"),
        "api_version": payload.get("api_version"),
        "api_url": payload.get("api_url"),
        "is_active": True,
        "tenant_id": db.tenant_id
    }
    
    if not data["tenant_id"]:
        raise HTTPException(status_code=400, detail="Missing Tenant Context.")
    
    db.client.table("utm_model_catalog").insert(data).execute()
    return {"success": True}

# --- Agent Matrix ---

@router.get("/matrix")
async def get_tenant_matrix(db: SupabasePersistence = Depends(get_db)):
    """Fetches the Agent Matrix for the current tenant."""
    if not db.tenant_id:
        return {"matrix": []}
    res = db.client.table("utm_agent_matrix").select("*").eq("tenant_id", db.tenant_id).execute()
    matrix = [{"agent": row["agent_id"], "provider": row["provider"], "model": row["model_id"]} for row in res.data]
    return {"matrix": matrix}

@router.post("/matrix")
async def update_tenant_matrix(payload: dict, db: SupabasePersistence = Depends(get_db)):
    """Updates the matrix for a specific agent."""
    agent = payload.get("agent")
    if not agent: raise HTTPException(status_code=400, detail="Missing Agent ID")
    if not db.tenant_id: raise HTTPException(status_code=403, detail="Tenant context required")

    data = {
        "agent_id": agent,
        "tenant_id": db.tenant_id,
        "provider": payload.get("provider"),
        "model_id": payload.get("model")
    }
    
    existing = db.client.table("utm_agent_matrix").select("id").eq("agent_id", agent).eq("tenant_id", db.tenant_id).execute()
    if existing.data:
        db.client.table("utm_agent_matrix").update(data).eq("id", existing.data[0]["id"]).execute()
    else:
        db.client.table("utm_agent_matrix").insert(data).execute()
    return {"success": True}

# --- Provider Vault ---

@router.get("/vault")
async def get_vault(request: Request, db: SupabasePersistence = Depends(get_db)):
    """Fetches credential status (masked) for the current tenant."""
    tenant_id = db.tenant_id or request.headers.get("x-tenant-id")
    if not tenant_id: return {"credentials": []}
    res = db.client.table("utm_provider_vault").select("provider_name, is_active, base_url").eq("tenant_id", tenant_id).execute()
    return {"credentials": res.data}

@router.post("/vault/update")
async def update_vault(request: Request, payload: dict, db: SupabasePersistence = Depends(get_db)):
    """Updates API Key for a provider."""
    tenant_id = db.tenant_id or request.headers.get("x-tenant-id")
    if not tenant_id: raise HTTPException(status_code=400, detail="Missing Tenant Context")
    
    provider = payload.get("provider")
    if not provider or not payload.get("api_key"):
        raise HTTPException(status_code=400, detail="Provider and API Key required")
        
    data = {"api_key": payload.get("api_key"), "base_url": payload.get("base_url")}
    existing = db.client.table("utm_provider_vault").select("id").eq("tenant_id", tenant_id).ilike("provider_name", provider).execute()
    
    if existing.data:
        db.client.table("utm_provider_vault").update(data).eq("id", existing.data[0]["id"]).execute()
    else:
        data["provider_name"] = provider
        data["tenant_id"] = tenant_id
        db.client.table("utm_provider_vault").insert(data).execute()
    return {"success": True}

# --- Cartridges ---

@router.get("/cartridges")
async def list_cartridges(db: SupabasePersistence = Depends(get_db)):
    """Returns available cartridges and their status."""
    res = db.client.table("utm_system_catalog").select("*").execute()
    # Map for frontend compatibility (enabled vs is_active)
    cartridges = []
    for item in res.data:
        cartridges.append({
            "id": item.get("tech_id") or str(item.get("id")),
            "tech_id": item.get("tech_id"),
            "name": item.get("name"),
            "type": item.get("type"),
            "enabled": item.get("is_active", True),
            "config": item.get("config", {})
        })
    return {"cartridges": cartridges}

@router.post("/cartridges")
async def add_cartridge(payload: dict, db: SupabasePersistence = Depends(get_db)):
    """Add a new cartridge to the catalog."""
    data = {
        "tech_id": payload.get("tech_id") or payload.get("name").lower().replace(" ", "_"),
        "name": payload.get("name"),
        "type": payload.get("type", "origin"),
        "description": payload.get("description"),
        "config": payload.get("config", {}),
        "is_active": True
    }
    db.client.table("utm_system_catalog").insert(data).execute()
    return {"success": True}

@router.post("/cartridges/{cartridge_id}/toggle")
async def toggle_cartridge(cartridge_id: str, payload: dict, db: SupabasePersistence = Depends(get_db)):
    """Toggle cartridge status (active/disabled)."""
    status = payload.get("status") # 'active' or 'disabled'
    is_active = (status == "active")
    db.client.table("utm_system_catalog").update({"is_active": is_active}).eq("tech_id", cartridge_id).execute()
    return {"success": True}

@router.post("/cartridges/{cartridge_id}/config")
async def update_cartridge_config(cartridge_id: str, payload: dict, db: SupabasePersistence = Depends(get_db)):
    """Update cartridge configuration JSON."""
    config = payload.get("config")
    db.client.table("utm_system_catalog").update({"config": config}).eq("tech_id", cartridge_id).execute()
    return {"success": True}

@router.delete("/cartridges/{cartridge_id}")
async def delete_cartridge(cartridge_id: str, db: SupabasePersistence = Depends(get_db)):
    """Remove a cartridge from the catalog."""
    db.client.table("utm_system_catalog").delete().eq("tech_id", cartridge_id).execute()
    return {"success": True}

@router.get("/origins")
async def list_origins(db: SupabasePersistence = Depends(get_db)):
    """Backward compatibility for origins."""
    res = db.client.table("utm_system_catalog").select("*").eq("type", "origin").eq("is_active", True).execute()
    # Map for frontend compatibility
    origins = []
    for item in res.data:
        origins.append({
            "id": str(item.get("id") or item.get("tech_id")),
            "name": item.get("name") or item.get("label"),
            "desc": item.get("description"),
            "icon": item.get("logo_url"),
            "enabled": True
        })
    return {"origins": origins}

@router.get("/destinations")
async def list_destinations(db: SupabasePersistence = Depends(get_db)):
    """Backward compatibility for destinations."""
    res = db.client.table("utm_system_catalog").select("*").eq("type", "destination").eq("is_active", True).execute()
    # Map for frontend compatibility
    destinations = []
    for item in res.data:
        destinations.append({
            "id": str(item.get("id") or item.get("tech_id")),
            "name": item.get("name") or item.get("label"),
            "desc": item.get("description"),
            "icon": item.get("logo_url"),
            "enabled": True
        })
    return {"destinations": destinations}
