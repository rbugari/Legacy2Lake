from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from services.persistence_service import SupabasePersistence
from services.agent_a_service import AgentAService
from services.agent_c_service import AgentCService
from services.agent_f_service import AgentFService
from services.agent_g_service import AgentGService
from services.agent_s_service import AgentSService

router = APIRouter(prefix="/system", tags=["System"])

# --- Models ---
class CartridgeConfig(BaseModel):
    name: str
    type: str # 'origin' or 'destination'
    subtype: str
    version: str
    config: Dict[str, Any]

class TogglePayload(BaseModel):
    status: str # 'active' or 'inactive'

class ConfigPayload(BaseModel):
    config: Dict[str, Any]

# --- Helper to get unified cartridge list (Logic reused from main.py) ---
async def get_all_cartridges():
    db = SupabasePersistence()
    config = await db.get_global_config("cartridges") or {}
    
    defaults = {
        # Extraction
        "mysql": {"id": "mysql", "name": "MySQL Extraction", "version": "v8.0", "desc": "Extracts schemas and data from MySQL.", "enabled": True, "category": "extraction", "type": "origin"},
        "oracle": {"id": "oracle", "name": "Oracle Extraction", "version": "v19c", "desc": "Extracts PL/SQL packages and schemas.", "enabled": True, "category": "extraction", "type": "origin"},
        "sqlserver": {"id": "sqlserver", "name": "SQL Server Extraction", "version": "v2019", "desc": "Extracts T-SQL stored procedures.", "enabled": True, "category": "extraction", "type": "origin"},
        
        # Refinement
        "pyspark": {"id": "pyspark", "name": "PySpark (Databricks)", "version": "v3.2", "desc": "Generates PySpark code optimized for Databricks.", "enabled": True, "category": "refinement", "type": "destination"},
        "dbt": {"id": "dbt", "name": "dbt Core (Snowflake)", "version": "v1.8", "desc": "Generates dbt models and tests.", "enabled": True, "category": "refinement", "type": "destination"},
        "snowflake": {"id": "snowflake", "name": "Snowflake Native", "version": "v1.0", "desc": "Generates Snowflake SQL SPs.", "enabled": True, "category": "refinement", "type": "destination"},
        "sql": {"id": "sql", "name": "Pure SQL (Postgres/Redshift)", "version": "v1.0", "desc": "Generates Standard SQL scripts.", "enabled": False, "category": "refinement", "type": "destination"}
    }
    
    # Merge
    merged = []
    for key, default in defaults.items():
        saved = config.get(key, {})
        item = default.copy()
        if "enabled" in saved: item["enabled"] = saved["enabled"]
        # Allow Config overrides
        if "config" in saved: item["config"] = saved["config"]
        merged.append(item)
        
    # Add custom ones if any (simple iteration over config keys not in defaults)
    for key, val in config.items():
        if key not in defaults:
            # Custom cartridge
            val["id"] = key
            merged.append(val)
            
    return merged

# --- Endpoints ---

@router.get("/origins")
async def list_origins():
    all_carts = await get_all_cartridges()
    origins = [c for c in all_carts if c.get("type") == "origin" or c.get("category") == "extraction"]
    return {"origins": origins}

@router.get("/destinations")
async def list_destinations():
    all_carts = await get_all_cartridges()
    dests = [c for c in all_carts if c.get("type") == "destination" or c.get("category") == "refinement"]
    return {"destinations": dests}

@router.get("/prompts")
async def list_prompts():
    """Aggregates all system prompts for the UI."""
    # We load them live
    a = AgentAService()._load_prompt()
    c = AgentCService()._load_prompt()
    f = AgentFService()._load_prompt()
    g = AgentGService()._load_prompt()
    s = AgentSService()._load_prompt()
    
    return {"prompts": [
        {"id": "agent-a", "name": "Agent A (Architect)", "content": a},
        {"id": "agent-c", "name": "Agent C (Interpreter)", "content": c},
        {"id": "agent-f", "name": "Agent F (Critic)", "content": f},
        {"id": "agent-g", "name": "Agent G (Governance)", "content": g},
        {"id": "agent-s", "name": "Agent S (Scout)", "content": s},
    ]}

@router.post("/cartridges")
async def add_cartridge(payload: CartridgeConfig):
    db = SupabasePersistence()
    config = await db.get_global_config("cartridges") or {}
    
    # Generate ID
    new_id = f"custom-{payload.subtype}-{len(config)}"
    
    entry = {
        "id": new_id,
        "name": payload.name,
        "type": payload.type,
        "subtype": payload.subtype,
        "version": payload.version,
        "desc": "Custom Cartridge",
        "enabled": True,
        "config": payload.config,
        "category": "extraction" if payload.type == "origin" else "refinement"
    }
    
    config[new_id] = entry
    await db.set_global_config("cartridges", config)
    return {"success": True, "id": new_id}

@router.post("/cartridges/{cartridge_id}/toggle")
async def toggle_cartridge(cartridge_id: str, payload: TogglePayload):
    db = SupabasePersistence()
    config = await db.get_global_config("cartridges") or {}
    
    if cartridge_id not in config:
        # If it's a default one not yet in config, we need to add it to config first
        # But for simpler logic, we assume we just set the override
        config[cartridge_id] = {}
        
    config[cartridge_id]["enabled"] = (payload.status == "active")
    await db.set_global_config("cartridges", config)
    return {"success": True}

@router.post("/cartridges/{cartridge_id}/config")
async def update_cartridge_config(cartridge_id: str, payload: ConfigPayload):
    db = SupabasePersistence()
    config = await db.get_global_config("cartridges") or {}
    
    if cartridge_id not in config:
        config[cartridge_id] = {}
        
    config[cartridge_id]["config"] = payload.config
    await db.set_global_config("cartridges", config)
    return {"success": True}

@router.delete("/cartridges/{cartridge_id}")
async def delete_cartridge(cartridge_id: str):
    db = SupabasePersistence()
    config = await db.get_global_config("cartridges") or {}
    
    if cartridge_id in config:
        del config[cartridge_id]
        await db.set_global_config("cartridges", config)
        
    return {"success": True}

# --- Validation / Test Endpoint ---
class ValidationRequest(BaseModel):
    agent_id: Optional[str] = None
    agente_id: Optional[str] = None # Legacy alias
    user_input: str
    system_prompt_override: Optional[str] = None

@router.post("/validate")
async def validate_agent(payload: ValidationRequest):
    """
    Test runs an agent with specific input to validate the prompt.
    Handles 'agente_id' vs 'agent_id' compatibility.
    """
    from langchain_core.messages import SystemMessage, HumanMessage
    
    agent_id = payload.agent_id or payload.agente_id
    if not agent_id:
        raise HTTPException(status_code=400, detail="Agent ID (or agente_id) is required")

    # Resolve Agent Service
    agent_service = None
    if agent_id.lower() in ["agent-a", "agent_a", "a"]:
        agent_service = AgentAService()
    elif payload.agent_id.lower() in ["agent-c", "agent_c", "c"]:
        agent_service = AgentCService()
    elif payload.agent_id.lower() in ["agent-f", "agent_f", "f"]:
        agent_service = AgentFService()
    elif payload.agent_id.lower() in ["agent-g", "agent_g", "g"]:
        agent_service = AgentGService()
    elif payload.agent_id.lower() in ["agent-s", "agent_s", "s"]:
        agent_service = AgentSService()
        
    if not agent_service:
        raise HTTPException(status_code=400, detail="Invalid Agent ID")
        
    # Get LLM (using Agent A's helper for now, assuming shared config)
    # Ideally each service has _get_llm exposed or shared base class.
    # AgentAService has _get_llm public-ish.
    try:
        llm = await agent_service._get_llm()
    except AttributeError:
        # Fallback if service doesn't expose _get_llm (e.g. Agent G might differ)
        # Use Agent A's method as generic provider
        llm = await AgentAService()._get_llm()

    messages = [
        SystemMessage(content=payload.system_prompt_override or agent_service._load_prompt()),
        HumanMessage(content=payload.user_input)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        return {
            "success": True, 
            "response": response.content,
            "used_prompt": payload.system_prompt_override or "Default"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Stage 0.5 Scout ---
class ScoutRequest(BaseModel):
    file_list: List[str]

@router.post("/scout/assess")
async def assess_repository(payload: ScoutRequest):
    """Triggers Agent S to assess repository completeness."""
    agent_s = AgentSService()
    result = await agent_s.assess_repository(payload.file_list)
    return result
