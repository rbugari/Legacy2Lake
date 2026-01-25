import os
import json
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any, List

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence

class AgentSService:
    """Service for Agent S (Scout) - Forensic Repository Assessment."""
    
    def __init__(self):
        self.prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "agent_s_scout.md")

    async def _get_llm(self):
        """Resolves LLM client from Global Config or Env Vars."""
        db = SupabasePersistence()
        config = await db.get_global_config("provider_settings")
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-4")
        
        azure_config = config.get("azure", {})
        if azure_config.get("enabled"):
            if azure_config.get("endpoint"): endpoint = azure_config.get("endpoint")
            if azure_config.get("api_key"): key = azure_config.get("api_key")
            if azure_config.get("model"): deployment = azure_config.get("model")
            
        return AzureChatOpenAI(
            azure_endpoint=endpoint,
            azure_deployment=deployment,
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            api_key=key,
            temperature=0
        )
        
    def _load_prompt(self) -> str:
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def save_prompt(self, content: str):
        with open(self.prompt_path, "w", encoding="utf-8") as f:
            f.write(content)

    async def assess_repository(self, file_list: List[str], system_prompt_override: str = None) -> Dict[str, Any]:
        """Performs forensic assessment of the provided file list."""
        system_prompt = system_prompt_override or self._load_prompt()
        
        user_message = f"""
        FILE INVENTORY TO ASSESS:
        -------------------------
        Files found:
        {json.dumps(file_list, indent=2)}
        
        INSTRUCTIONS:
        Analyze the inventory and identify missing context (Gaps).
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        llm = await self._get_llm()
        response = await llm.ainvoke(messages)
        content = response.content
        
        # Clean potential markdown formatting
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error("Failed to parse Agent S response", "Agent S")
            return {
                "error": "Failed to parse LLM response", 
                "raw_response": content,
                "detected_gaps": []
            }
