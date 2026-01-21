import os
import json
from typing import Dict, Any, List
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
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
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence
        from .knowledge_service import KnowledgeService


class AgentCService:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-4"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY")
        )
        self.prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/agent_c_interpreter.md")
        self.standards_path = os.path.join(os.path.dirname(__file__), "../prompts/coding_standards.md")

    def _load_prompt(self, path: str = None) -> str:
        target_path = path or self.prompt_path
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()

    @logger.llm_debug("Agent-C-Developer")
    async def transpile_task(self, node_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Transpiles a single SSIS task into PySpark code following defined standards."""
        system_prompt = self._load_prompt(self.prompt_path)
        standards = self._load_prompt(self.standards_path)
        
        project_id = node_data.get('project_id')
        db = SupabasePersistence()
        registry_raw = await db.get_design_registry(project_id) if project_id else []
        registry = KnowledgeService.flatten_knowledge(registry_raw)
        
        human_content = f"""
        CODING STANDARDS TO FOLLOW:
        {standards}

        TRANSPILE THE FOLLOWING TASK:
        Task Name: {node_data.get('name')}
        Task Type: {node_data.get('type')}
        Task Description: {node_data.get('description')}
        
        CONTEXT:
        {json.dumps({
            **(context or {}),
            "load_strategy": node_data.get("load_strategy", "FULL_OVERWRITE"),
            "frequency": node_data.get("frequency", "DAILY"),
            "is_pii": node_data.get("is_pii", False),
            "masking_rule": node_data.get("masking_rule"),
            "target_name": node_data.get("target_name"),
            "business_entity": node_data.get("business_entity"),
            "global_design_registry": registry
        }, indent=2)}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content)
        ]

        response = await self.llm.ainvoke(messages)
        content = response.content.strip()

        # Clean JSON if LLM added markdown blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse LLM response as JSON",
                "raw_response": content
            }
