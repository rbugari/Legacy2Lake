"""
Agents Router
Handles prompt management and configuration for AI agents (A, C, F, G).
Migrated from main.py for better modularity.
"""
from routers.dependencies import get_db
from services.persistence_service import SupabasePersistence
from services.agent_a_service import AgentAService
from services.agent_c_service import AgentCService
from services.agent_f_service import AgentFService
from services.agent_g_service import AgentGService
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/prompts", tags=["Agent Prompts"])


# --- Models ---

class PromptUpdate(BaseModel):
    prompt: str


class PromptResponse(BaseModel):
    prompt: str


# --- Agent A (Triage/Discovery) ---

@router.get("/agent-a", response_model=PromptResponse)
async def get_agent_a_prompt(db: SupabasePersistence = Depends(get_db)):
    """Returns the current default system prompt for Agent A."""
    agent_a = AgentAService(tenant_id=db.tenant_id, client_id=db.client_id)
    return {"prompt": await agent_a._load_prompt()}


@router.post("/agent-a")
async def update_agent_a_prompt(payload: PromptUpdate, db: SupabasePersistence = Depends(get_db)):
    """Updates the system prompt for Agent A."""
    agent = AgentAService(tenant_id=db.tenant_id, client_id=db.client_id)
    await agent.save_prompt(payload.prompt)
    return {"success": True}


# --- Agent C (Interpreter/Transpiler) ---

@router.get("/agent-c", response_model=PromptResponse)
async def get_agent_c_prompt(db: SupabasePersistence = Depends(get_db)):
    """Returns the current default system prompt for Agent C."""
    agent_c = AgentCService(tenant_id=db.tenant_id, client_id=db.client_id)
    return {"prompt": await agent_c._load_prompt()}


@router.post("/agent-c")
async def update_agent_c_prompt(payload: PromptUpdate, db: SupabasePersistence = Depends(get_db)):
    """Updates the system prompt for Agent C."""
    agent = AgentCService(tenant_id=db.tenant_id, client_id=db.client_id)
    await agent.save_prompt(payload.prompt)
    return {"success": True}


# --- Agent F (Critic/Auditor) ---

@router.get("/agent-f", response_model=PromptResponse)
async def get_agent_f_prompt(db: SupabasePersistence = Depends(get_db)):
    """Returns the current default system prompt for Agent F."""
    agent_f = AgentFService(tenant_id=db.tenant_id, client_id=db.client_id)
    return {"prompt": await agent_f._load_prompt()}


@router.post("/agent-f")
async def update_agent_f_prompt(payload: PromptUpdate, db: SupabasePersistence = Depends(get_db)):
    """Updates the system prompt for Agent F."""
    agent = AgentFService(tenant_id=db.tenant_id, client_id=db.client_id)
    await agent.save_prompt(payload.prompt)
    return {"success": True}


# --- Agent G (Governance/Documentation) ---

@router.get("/agent-g", response_model=PromptResponse)
async def get_agent_g_prompt(db: SupabasePersistence = Depends(get_db)):
    """Returns the current default system prompt for Agent G."""
    agent_g = AgentGService(tenant_id=db.tenant_id, client_id=db.client_id)
    return {"prompt": await agent_g._load_prompt()}


@router.post("/agent-g")
async def update_agent_g_prompt(payload: PromptUpdate, db: SupabasePersistence = Depends(get_db)):
    """Updates the system prompt for Agent G."""
    agent = AgentGService(tenant_id=db.tenant_id, client_id=db.client_id)
    await agent.save_prompt(payload.prompt)
    return {"success": True}
