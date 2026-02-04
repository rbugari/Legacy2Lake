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
    existing = db.client.table("utm_provider_vault").select("id").eq("tenant_id", tenant_id).eq("provider_name", provider).execute()
    
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
    return {"cartridges": res.data}

@router.post("/cartridges/update")
async def update_cartridge_status(payload: CartridgeUpdate, db: SupabasePersistence = Depends(get_db)):
    """Updates the enabled status of a cartridge."""
    db.client.table("utm_system_catalog").update({"is_active": payload.enabled}).eq("tech_id", payload.id).execute()
    return {"success": True}
