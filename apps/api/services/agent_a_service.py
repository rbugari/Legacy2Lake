import os
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any, Optional
import json
try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.services.knowledge_service import KnowledgeService
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
        from services.knowledge_service import KnowledgeService
    except ImportError:
        # Fallback for when running directly or tests
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence
        from .knowledge_service import KnowledgeService

class AgentAService:
    """Service for Agent A (Detective) using Azure OpenAI."""
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
         self.tenant_id = tenant_id
         self.client_id = client_id

    async def _get_llm(self):
        """Resolves LLM client from Agent Matrix (DB) or Env Vars."""
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        
        # 1. Try DB Resolution (Universal Persistence)
        resolved = await db.resolve_agent_model("agent-a")
        
        # Default fallback to values from ENV
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-4")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        temperature = 0
        provider = "azure"
        
        if resolved:
            provider = resolved.get("provider", "azure")
            if resolved.get("endpoint"): endpoint = resolved.get("endpoint")
            if resolved.get("api_key"): key = resolved.get("api_key") 
            if resolved.get("deployment"): deployment = resolved.get("deployment")
            if resolved.get("api_version"): api_version = resolved.get("api_version")
            if "temperature" in resolved: temperature = resolved["temperature"]
            
        if provider == "azure":
            return AzureChatOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=deployment,
                openai_api_version=api_version,
                api_key=key,
                temperature=temperature
            )
        else:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=deployment,
                api_key=key,
                base_url=endpoint,
                temperature=temperature
            )
        
        
    async def _load_prompt(self, path: str = None) -> str:
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        return await db.get_prompt("agent_a_discovery")

    async def save_prompt(self, content: str):
        """Updates the system prompt in DB."""
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        await db.save_prompt("agent_a_discovery", content)


    async def analyze_manifest(self, manifest: Dict[str, Any], system_prompt_override: str = None) -> Dict[str, Any]:
        """Analyzes the full project manifest to build the Mesh Graph."""
        
        system_prompt = system_prompt_override or await self._load_prompt()
        project_id = manifest.get('project_id')
        
        # Release 1.3: Fetch Design Registry
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        registry_raw = await db.get_design_registry(project_id) if project_id else []
        registry = KnowledgeService.flatten_knowledge(registry_raw)
        
        # Prepare content for LLM (might need truncation if too large)
        # We send the structure and snippets.
        
        user_message = f"""
        PROJECT MANIFEST:
        -----------------
        Project ID: {manifest.get('project_id')}
        Tech Stack Stats: {json.dumps(manifest.get('tech_stats'), indent=2)}
        
        FILE INVENTORY:
        {json.dumps(manifest.get('file_inventory'), indent=2)}
        
        USER CONTEXT & BUSINESS RULES:
        {json.dumps(manifest.get('user_context', []), indent=2)}

        GLOBAL DESIGN REGISTRY:
        {json.dumps(registry, indent=2)}

        INSTRUCTIONS:
        1. Process the FILE INVENTORY and identify the Lineage Mesh.
        2. Assign metadata (Volume, Latency, Criticality, PII, Partition Key) based on patterns in filenames and signatures.
        3. Respect USER CONTEXT as absolute priority.
        4. Synthesize the Mesh Graph according to the System Prompt format.
        """
        
        logger.info(f"Agent A analyzing manifest for {manifest.get('project_id')}...", "Agent A")
        
        # --- DEBUG LOGGING START ---
        # User requested "more complete dump" of parameters
        logger.debug(f"=== [Agent A] SYSTEM PROMPT ===\n{system_prompt}\n===============================", "Agent A")
        logger.debug(f"=== [Agent A] USER MESSAGE (MANIFEST) ===\n{user_message}\n=======================================", "Agent A")
        # --- DEBUG LOGGING END ---

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        # Using a larger context model might be needed if inventory is huge. 
        # Assuming gpt-4 or 4-turbo window is sufficient for this demo.
        # Assuming gpt-4 or 4-turbo window is sufficient for this demo.
        llm = await self._get_llm()
        response = await llm.ainvoke(messages)
        content = response.content
        
        logger.debug(f"=== [Agent A] RAW RESPONSE ===\n{content}\n==============================", "Agent A")
        
        # Clean potential markdown formatting
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error("Failed to parse Agent A response", "Agent A")
            # Fallback for partial JSON or comments
            return {
                "error": "Failed to parse LLM response", 
                "raw_response": content,
                "mesh_graph": {"nodes": [], "edges": []}
            }
    async def analyze_package(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes a single SSIS package summary (legacy/individual ingest)."""
        system_prompt = await self._load_prompt()
        
        user_message = f"""
        ANALYZE THIS SSIS PACKAGE:
        -------------------------
        Summary: {json.dumps(summary, indent=2)}
        
        INSTRUCTIONS:
        Identify the primary purpose of this package and any critical tasks.
        Return a summary and classification.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        llm = await self._get_llm()
        response = await llm.ainvoke(messages)
        content = response.content
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        try:
            return json.loads(content)
        except:
            return {"raw_analysis": content}
