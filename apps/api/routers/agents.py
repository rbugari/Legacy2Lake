"""
Agents Router
Handles prompt management and configuration for AI agents (A, C, F, G).
Migrated from main.py for better modularity.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

from services.agent_a_service import AgentAService
from services.agent_c_service import AgentCService
from services.agent_f_service import AgentFService
from services.agent_g_service import AgentGService

router = APIRouter(prefix="/prompts", tags=["Agent Prompts"])


# --- Models ---

class PromptUpdate(BaseModel):
    prompt: str


class PromptResponse(BaseModel):
    prompt: str


# --- Agent A (Triage/Discovery) ---

@router.get("/agent-a", response_model=PromptResponse)
async def get_agent_a_prompt():
    """Returns the current default system prompt for Agent A."""
    agent_a = AgentAService()
    return {"prompt": agent_a._load_prompt()}


@router.post("/agent-a")
async def update_agent_a_prompt(payload: PromptUpdate):
    """Updates the system prompt for Agent A."""
    agent = AgentAService()
    agent.save_prompt(payload.prompt)
    return {"success": True}


# --- Agent C (Interpreter/Transpiler) ---

@router.get("/agent-c", response_model=PromptResponse)
async def get_agent_c_prompt():
    """Returns the current default system prompt for Agent C."""
    agent_c = AgentCService()
    return {"prompt": agent_c._load_prompt()}


@router.post("/agent-c")
async def update_agent_c_prompt(payload: PromptUpdate):
    """Updates the system prompt for Agent C."""
    agent = AgentCService()
    agent.save_prompt(payload.prompt)
    return {"success": True}


# --- Agent F (Critic/Auditor) ---

@router.get("/agent-f", response_model=PromptResponse)
async def get_agent_f_prompt():
    """Returns the current default system prompt for Agent F."""
    agent_f = AgentFService()
    return {"prompt": agent_f._load_prompt()}


@router.post("/agent-f")
async def update_agent_f_prompt(payload: PromptUpdate):
    """Updates the system prompt for Agent F."""
    agent = AgentFService()
    agent.save_prompt(payload.prompt)
    return {"success": True}


# --- Agent G (Governance/Documentation) ---

@router.get("/agent-g", response_model=PromptResponse)
async def get_agent_g_prompt():
    """Returns the current default system prompt for Agent G."""
    agent_g = AgentGService()
    return {"prompt": agent_g._load_prompt()}


@router.post("/agent-g")
async def update_agent_g_prompt(payload: PromptUpdate):
    """Updates the system prompt for Agent G."""
    agent = AgentGService()
    agent.save_prompt(payload.prompt)
    return {"success": True}
