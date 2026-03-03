"""
System Router
Handles global configuration, model catalog, provider vault, and tech cartridges.
Migrated from main.py for v3.7.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os

from apps.api.routers.dependencies import get_db
from apps.api.services.persistence_service import SupabasePersistence, PersistenceService
from apps.api.services.knowledge_service import KnowledgeService
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
        
    from apps.api.services.agent_a_service import AgentAService
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

@router.post("/catalog/test")
async def test_model_connection(payload: dict, db: SupabasePersistence = Depends(get_db)):
    """
    Pings a specific model with a simple 'Hello, who are you?' message to
    verify the connection, credentials, and deployment are working.
    Accepts { model_id } in the body.
    Returns { success, response, latency_ms, model_id, provider, deployment }.
    """
    import time
    from langchain_core.messages import HumanMessage

    model_id = payload.get("model_id")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id required")

    # 1. Load model config from catalog
    model_res = db.client.table("utm_model_catalog").select("*").eq("model_id", model_id).execute()
    if not model_res.data:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found in catalog")
    model = model_res.data[0]

    provider = (model.get("provider") or "azure").lower()
    deployment = model.get("deployment_id") or model.get("model_id")
    api_version = model.get("api_version")
    api_url = model.get("api_url")

    # 2. Load credentials from vault (tenant-specific)
    tenant_id = db.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required to access vault credentials")

    vault_res = db.client.table("utm_provider_vault")\
        .select("api_key, base_url")\
        .eq("tenant_id", tenant_id)\
        .ilike("provider_name", provider)\
        .execute()

    if not vault_res.data or not vault_res.data[0].get("api_key"):
        raise HTTPException(
            status_code=400,
            detail=f"No API Key found for provider '{provider}' in vault. Please configure it in Settings > Provider Vault."
        )

    api_key = vault_res.data[0]["api_key"]
    vault_url = vault_res.data[0].get("base_url")
    endpoint = vault_url or api_url

    if not endpoint:
        raise HTTPException(status_code=400, detail="No endpoint URL found in vault or model config")

    # 3. Build LLM client
    try:
        if provider == "azure":
            from langchain_openai import AzureChatOpenAI
            llm = AzureChatOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=deployment,
                openai_api_version=api_version or "2024-05-01-preview",
                api_key=api_key,
                temperature=0,
                max_tokens=200
            )
        else:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=deployment,
                api_key=api_key,
                base_url=endpoint,
                temperature=0,
                max_tokens=200
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize LLM client: {str(e)}")

    # 4. Send test ping
    t0 = time.time()
    try:
        response = await llm.ainvoke([HumanMessage(content="Hello! Who are you? Answer in one sentence.")])
        latency_ms = int((time.time() - t0) * 1000)
        return {
            "success": True,
            "response": response.content,
            "latency_ms": latency_ms,
            "model_id": model_id,
            "provider": provider,
            "deployment": deployment
        }
    except Exception as e:
        latency_ms = int((time.time() - t0) * 1000)
        error_msg = str(e)
        # Simplify common Azure error messages
        if "401" in error_msg or "Unauthorized" in error_msg:
            error_msg = "Invalid API Key (401 Unauthorized)"
        elif "404" in error_msg or "DeploymentNotFound" in error_msg:
            error_msg = f"Deployment '{deployment}' not found (404). Check the deployment name."
        elif "InvalidURL" in error_msg or "connect" in error_msg.lower():
            error_msg = f"Cannot connect to endpoint: {endpoint}"
        raise HTTPException(status_code=502, detail=f"LLM test failed after {latency_ms}ms: {error_msg}")

@router.delete("/catalog")
async def delete_model(payload: dict, db: SupabasePersistence = Depends(get_db)):
    """
    Deletes a model from the catalog.
    Accepts model_id in the request body to avoid URL-encoding issues
    when the model_id itself is a URL (e.g. https://...).
    """
    model_id = payload.get("model_id")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id required")
    db.client.table("utm_model_catalog").delete().eq("model_id", model_id).execute()
    return {"success": True}

@router.post("/catalog/toggle")
async def toggle_model(payload: dict, db: SupabasePersistence = Depends(get_db)):
    """
    Toggles a model's active state.
    Accepts model_id in the request body to avoid URL path-routing issues.
    """
    model_id = payload.get("model_id")
    is_active = payload.get("is_active")
    if model_id is None or is_active is None:
        raise HTTPException(status_code=400, detail="model_id and is_active required")
    db.client.table("utm_model_catalog").update({"is_active": is_active}).eq("model_id", model_id).execute()
    return {"success": True}

@router.post("/catalog/update")
async def update_model(payload: dict, db: SupabasePersistence = Depends(get_db)):
    """
    Updates a model's metadata.
    Accepts model_id in the request body to avoid URL path-routing issues.
    """
    model_id = payload.get("model_id") or payload.get("id")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id required")
    updates = {}
    if "name" in payload:
        updates["label"] = payload["name"]
    if "label" in payload:
        updates["label"] = payload["label"]
    if "context" in payload:
        updates["context_window"] = int(payload["context"])
    if "deployment_id" in payload:
        updates["deployment_id"] = payload["deployment_id"]
    if "api_version" in payload:
        updates["api_version"] = payload["api_version"]
    if "api_url" in payload:
        updates["api_url"] = payload["api_url"]
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    db.client.table("utm_model_catalog").update(updates).eq("model_id", model_id).execute()
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

@router.post("/vault/delete")
async def delete_vault_provider(request: Request, payload: dict, db: SupabasePersistence = Depends(get_db)):
    """
    Deletes a provider from the vault.
    Blocked if the tenant has models in utm_model_catalog that use this provider.
    """
    tenant_id = db.tenant_id or request.headers.get("x-tenant-id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Missing Tenant Context")

    provider = payload.get("provider")
    if not provider:
        raise HTTPException(status_code=400, detail="provider required")

    # Guardian: block if any models still reference this provider
    models_res = db.client.table("utm_model_catalog")\
        .select("model_id, label")\
        .eq("tenant_id", tenant_id)\
        .ilike("provider", provider)\
        .execute()

    if models_res.data:
        model_names = ", ".join([m.get("label") or m.get("model_id") for m in models_res.data[:3]])
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: {len(models_res.data)} model(s) still use this provider ({model_names}). Remove them first from Model Catalog."
        )

    db.client.table("utm_provider_vault")\
        .delete()\
        .eq("tenant_id", tenant_id)\
        .ilike("provider_name", provider)\
        .execute()

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

@router.get("/cartridges/{cartridge_id}/knowledge")
async def get_cartridge_knowledge(cartridge_id: str, db: SupabasePersistence = Depends(get_db)):
    """Get expert knowledge (improvements.md) for a cartridge."""
    try:
        # Get cartridge type (origin or destination)
        res = db.client.table("utm_system_catalog").select("type").eq("tech_id", cartridge_id).limit(1).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Cartridge not found")
        
        cartridge_type = res.data[0].get("type")
        category_dir = "origins" if cartridge_type == "origin" else "destinations"
        
        # Build path to improvements.md
        lab_path = os.path.join(os.getcwd(), "prompt_lab_export", category_dir, cartridge_id, "improvements.md")
        
        if os.path.exists(lab_path):
            with open(lab_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"knowledge": content, "has_knowledge": True}
        else:
            # Return empty template if file doesn't exist
            template = f"# Expert Knowledge: {cartridge_id.upper()}\n\n## Best Practices\n\n- Add your expert knowledge here...\n\n## Common Patterns\n\n- Document common patterns...\n"
            return {"knowledge": template, "has_knowledge": False}
    except Exception as e:
        logger.error(f"Error loading knowledge for {cartridge_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/cartridges/{cartridge_id}/knowledge")
async def update_cartridge_knowledge(cartridge_id: str, payload: dict, db: SupabasePersistence = Depends(get_db)):
    """Update expert knowledge (improvements.md) for a cartridge."""
    try:
        knowledge = payload.get("knowledge", "")
        
        # Get cartridge type (origin or destination)
        res = db.client.table("utm_system_catalog").select("type").eq("tech_id", cartridge_id).limit(1).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Cartridge not found")
        
        cartridge_type = res.data[0].get("type")
        category_dir = "origins" if cartridge_type == "origin" else "destinations"
        
        # Build path to improvements.md
        lab_dir = os.path.join(os.getcwd(), "prompt_lab_export", category_dir, cartridge_id)
        os.makedirs(lab_dir, exist_ok=True)
        
        improvements_path = os.path.join(lab_dir, "improvements.md")
        
        with open(improvements_path, "w", encoding="utf-8") as f:
            f.write(knowledge)
        
        logger.info(f"Knowledge updated for cartridge {cartridge_id}")
        return {"success": True, "message": f"Knowledge saved to {improvements_path}"}
    except Exception as e:
        logger.error(f"Error updating knowledge for {cartridge_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/origins")
async def list_origins(db: SupabasePersistence = Depends(get_db)):
    """Backward compatibility for origins."""
    res = db.client.table("utm_system_catalog").select("*").eq("type", "origin").eq("is_active", True).execute()
    # Map for frontend compatibility
    origins = []
    for item in res.data:
        origins.append({
            "id": str(item.get("id") or item.get("tech_id")),
            "tech_id": item.get("tech_id"),
            "name": item.get("name") or item.get("label"),
            "desc": item.get("description"),
            "icon": item.get("logo_url"),
            "enabled": True,
            "config": item.get("config") or {}
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
            "tech_id": item.get("tech_id"),
            "name": item.get("name") or item.get("label"),
            "desc": item.get("description"),
            "icon": item.get("logo_url"),
            "enabled": True,
            "config": item.get("config") or {}
        })
    return {"destinations": destinations}

# --- Agents Catalog ---

@router.get("/agents")
async def list_agents(db: SupabasePersistence = Depends(get_db)):
    """Returns all active agents with their display names and descriptions."""
    try:
        res = db.client.table("utm_agent_catalog").select("*").eq("is_active", True).order("agent_id").execute()
        agents = []
        for agent in res.data:
            agents.append({
                "agent_id": agent.get("agent_id"),
                "name": agent.get("name"),  # Original internal name
                "display_name": agent.get("display_name") or agent.get("name"),
                "description": agent.get("description") or agent.get("role_description"),
                "role_description": agent.get("role_description"),
                "is_active": agent.get("is_active", True),
                "phases": agent.get("phases") or []
            })
        return {"agents": agents}
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to load agents catalog")

@router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, payload: dict, db: SupabasePersistence = Depends(get_db)):
    """Updates an agent's display name, description and phases. Admin only."""
    try:
        data = {}
        if "display_name" in payload:
            data["display_name"] = payload["display_name"]
        if "description" in payload:
            data["description"] = payload["description"]
        if "is_active" in payload:
            data["is_active"] = payload["is_active"]
        if "phases" in payload:
            data["phases"] = payload["phases"]
        
        if not data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        db.client.table("utm_agent_catalog").update(data).eq("agent_id", agent_id).execute()
        return {"success": True, "message": f"Agent {agent_id} updated successfully"}
    except Exception as e:
        logger.error(f"Error updating agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
