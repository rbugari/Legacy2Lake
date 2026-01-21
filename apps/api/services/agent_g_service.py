import os
import json
from typing import Dict, Any, List
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
try:
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from .persistence_service import SupabasePersistence


class AgentGService:
    async def _get_llm(self):
        """Resolves LLM client from Global Config or Env Vars."""
        db = SupabasePersistence()
        config = await db.get_global_config("provider_settings")
        
        # Default fallback to env
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-4")
        
        # Override from DB if available and enabled
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

    def __init__(self):
        self.prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/agent_g_governance.md")

    def _load_prompt(self, path: str = None) -> str:
        target_path = path or self.prompt_path
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()

    def save_prompt(self, content: str):
        """Updates the system prompt file."""
        with open(self.prompt_path, "w", encoding="utf-8") as f:
            f.write(content)

    async def generate_documentation(self, project_name: str, mesh: Dict[str, Any], transformations: List[Dict[str, Any]]) -> str:
        """Generates technical documentation and lineage for a project."""
        system_prompt = self._load_prompt(self.prompt_path)
        
        human_content = f"""
        PROJECT NAME: {project_name}
        
        EXECUTION MESH (Logic Relationships):
        {json.dumps(mesh, indent=2)}
        
        TRANSFORMED CODE (PySpark Logic):
        {json.dumps(transformations, indent=2)}
        
        Please generate the Governance Documentation following the structure defined in your system prompt.
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content)
        ]

        llm = await self._get_llm()
        response = await llm.ainvoke(messages)
        return response.content.strip()
