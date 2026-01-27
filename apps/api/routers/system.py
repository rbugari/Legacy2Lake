from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from services.persistence_service import SupabasePersistence
from services.agent_a_service import AgentAService
from services.agent_c_service import AgentCService
from services.agent_f_service import AgentFService
from services.agent_g_service import AgentGService
from services.agent_s_service import AgentSService
from routers.dependencies import get_db

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
# --- Helper to get unified cartridge list (DB Driven) ---
async def get_all_cartridges():
    db = SupabasePersistence()
    # Fetch from Static Catalog (table: utm_supported_techs) in DB
    techs = await db.list_supported_techs()
    
    # Fetch from Instance Config (table: utm_global_config) for overrides (enabled/disabled)
    global_config = await db.get_global_config("cartridges") or {}
    
    formatted = []
    for t in techs:
        # DB Columns: tech_id, role, label, description, version, is_active
        tid = t["tech_id"].lower()
        role = t["role"].upper() # SOURCE / TARGET
        
        # Determine defaults
        is_origin = (role == "SOURCE")
        
        item = {
            "id": tid,
            "name": t["label"],
            "version": t.get("version", "Latest"),
            "desc": t.get("description", ""),
            "enabled": t.get("is_active", True),
            "category": "extraction" if is_origin else "refinement",
            "type": "origin" if is_origin else "destination",
            "subtype": tid
        }
        
        # Apply Overrides from Global Config (if any)
        if tid in global_config:
            saved = global_config[tid]
            if "enabled" in saved: item["enabled"] = saved["enabled"]
            if "config" in saved: item["config"] = saved["config"]
            
        formatted.append(item)
        
    return formatted

# --- Endpoints ---

@router.get("/origins")
async def list_origins():
    all_carts = await get_all_cartridges()
    origins = [c for c in all_carts if c.get("type") == "origin"]
    return {"origins": origins}

@router.get("/destinations")
async def list_destinations():
    all_carts = await get_all_cartridges()
    dests = [c for c in all_carts if c.get("type") == "destination"]
    return {"destinations": dests}

@router.get("/prompts")
async def list_prompts():
    """Aggregates all system prompts found in the prompts directory."""
    import glob
    import os
    
    prompts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")
    md_files = glob.glob(os.path.join(prompts_dir, "*.md"))
    
    results = []
    for filepath in md_files:
        filename = os.path.basename(filepath)
        file_id = filename.replace(".md", "")
        
        # Friendly Name Logic
        parts = file_id.split("_")
        name = ""
        
        if len(parts) >= 2 and parts[0] == "agent" and len(parts[1]) == 1:
             agent_letter = parts[1].upper()
             remainder = " ".join([chunk.capitalize() for chunk in parts[2:]])
             if remainder:
                 name = f"Agent {agent_letter} ({remainder})"
             else:
                 name = f"Agent {agent_letter}"
        else:
             name = " ".join([chunk.capitalize() for chunk in parts])
             
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            results.append({
                "id": file_id,
                "name": name,
                "content": content
            })
        except Exception as e:
            print(f"Error loading prompt {filename}: {e}")
            
    # Sort by ID for consistency
    results.sort(key=lambda x: x["id"])
    return {"prompts": results}

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
async def validate_agent(payload: ValidationRequest, db: SupabasePersistence = Depends(get_db)):
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
        agent_service = AgentAService(tenant_id=db.tenant_id, client_id=db.client_id)
    elif agent_id.lower() in ["agent-c", "agent_c", "c"]:
        agent_service = AgentCService(tenant_id=db.tenant_id, client_id=db.client_id)
    elif agent_id.lower() in ["agent-f", "agent_f", "f"]:
        agent_service = AgentFService(tenant_id=db.tenant_id, client_id=db.client_id)
    elif agent_id.lower() in ["agent-g", "agent_g", "g"]:
        agent_service = AgentGService(tenant_id=db.tenant_id, client_id=db.client_id)
    elif agent_id.lower() in ["agent-s", "agent_s", "s"]:
        agent_service = AgentSService(tenant_id=db.tenant_id, client_id=db.client_id)
        
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

    prompt_content = payload.system_prompt_override
    if not prompt_content:
        import inspect
        if inspect.iscoroutinefunction(agent_service._load_prompt):
            prompt_content = await agent_service._load_prompt()
        else:
            prompt_content = agent_service._load_prompt()

    messages = [
        SystemMessage(content=prompt_content),
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
async def assess_repository(payload: ScoutRequest, db: SupabasePersistence = Depends(get_db)):
    """Triggers Agent S to assess repository completeness."""
    
    if not payload.file_list or len(payload.file_list) == 0:
        return {
            "error": "No files provided for assessment",
            "assessment_summary": "No files to analyze",
            "completeness_score": 0,
            "detected_gaps": []
        }
    
    # Initialize Agent S with tenant context
    agent_s = AgentSService(tenant_id=db.tenant_id, client_id=db.client_id)
    
    try:
        result = await agent_s.assess_repository(payload.file_list)
        return result
    except Exception as e:
        return {
            "error": f"Assessment failed: {str(e)}",
            "assessment_summary": "Error during assessment",
            "completeness_score": 0,
            "detected_gaps": []
        }

