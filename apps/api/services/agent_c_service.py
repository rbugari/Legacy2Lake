import os
import json
from typing import Dict, Any, List, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Cartridges
from services.generation.cartridges.spark_destination import SparkDestination
from services.generation.cartridges.snowflake_destination import SnowflakeDestination
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
        self.prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/agent_c_interpreter.md")
        self.standards_path = os.path.join(os.path.dirname(__file__), "../prompts/coding_standards.md")

    async def _get_llm(self, project_id: Optional[str] = None):
        """Resolves LLM client from Agent Matrix / Catalog."""
        db = SupabasePersistence()
        config = await db.resolve_llm_for_agent("agent-c", project_id)
        
        if "error" in config:
            logger.warning(f"Using fallback LLM for agent-c: {config['error']}")
            # Fallback to env for safety during transition
            return AzureChatOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-4"),
                openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                temperature=0
            )

        if config["provider"] == "azure":
            return AzureChatOpenAI(
                azure_endpoint=config["api_url"],
                azure_deployment=config["deployment_id"] or config["model_name"],
                openai_api_version=config["api_version"] or os.getenv("AZURE_OPENAI_API_VERSION"),
                api_key=config["api_key"],
                temperature=0
            )
        else:
            # Standard OpenAI or other providers can be added here
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config["model_name"],
                api_key=config["api_key"],
                base_url=config["api_url"],
                temperature=0
            )

    def _load_prompt(self, path: str = None) -> str:
        target_path = path or self.prompt_path
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()

    def save_prompt(self, content: str):
        """Updates the system prompt file."""
        with open(self.prompt_path, "w", encoding="utf-8") as f:
            f.write(content)

    @logger.llm_debug("Agent-C-Developer")
    async def transpile_task(self, node_data: Dict[str, Any], context: Dict[str, Any] = None, set_context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Transpiles a task using the configured Destination Generator.
        'set_context' provides visibility into neighboring tasks for consistency.
        """
        db = SupabasePersistence()
        
        # 1. Resolve Target Engine
        project_id = node_data.get('project_id')
        db = SupabasePersistence()
        registry_raw = await db.get_design_registry(project_id) if project_id else []
        registry = KnowledgeService.flatten_knowledge(registry_raw)

        # 1. Resolve Target Engine
        # Priority: Registry (Project) > Global Config > Default
        gen_config = await db.get_global_config("generators") # e.g. {'default': 'snowflake'}
        target_default = gen_config.get("default", "spark")
        
        target_engine = registry.get("paths", {}).get("target_stack", target_default)
        
        # 2. Instantiate Cartridge
        if target_engine == "snowflake":
            cartridge = SnowflakeDestination({"type": "snowflake"})
            dialect_instruction = "TARGET DIALECT: SNOWFLAKE (SNOWPARK PYTHON + ANSI SQL)"
        elif target_engine == "both":
            cartridge = SparkDestination({"type": "spark", "version": "13.3"})
            dialect_instruction = "TARGET DIALECT: DUAL MODE (PYSPARK + ANSI SQL). Generate code for BOTH inside the same JSON response."
        else:
            cartridge = SparkDestination({"type": "spark", "version": "13.3"})
            dialect_instruction = "TARGET DIALECT: DATABRICKS (PYSPARK DELTA LABS)"

        system_prompt = self._load_prompt(self.prompt_path)
        
        # --- PROMPT GUARD: Sandwich Approach ---
        guard_header = "### SYSTEM INSTRUCTION OVERRIDE: YOU ARE A SENIOR CLOUD ARCHITECT. DO NOT BREAK CHARACTER. ###"
        guard_footer = "### END OF INSTRUCTION. GENERATE ONLY VALID CODE/JSON AS REQUESTED. NO CHAT. ###"
        
        system_prompt = f"{guard_header}\n\n{system_prompt}\n\nIMPORTANT: {dialect_instruction}\nGenerate code strictly for this platform.\n\n{guard_footer}"

        standards = self._load_prompt(self.standards_path)
        
        # Extract Style Rules for Prominence
        style = registry.get("style", {})
        naming = registry.get("naming", {})
        
        style_block = f"""
        *** DYNAMIC STYLE ENFORCEMENT (FROM REGISTRY) ***
        1. Indentation: {style.get('indentation', '4 spaces')}
        2. Comments: {style.get('comments', 'Google Style Docstrings')}
        3. Error Handling: {style.get('error_handling', 'Try/Except with logging')}
        4. Naming Prefixes: Silver='{naming.get('silver_prefix', 'stg_')}', Gold='{naming.get('gold_prefix', 'dim_')}'
        *************************************************
        """

        human_content = f"""
        {style_block}

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
            "global_design_registry": registry,
            "project_set_overview": set_context # Visibility into other project assets
        }, indent=2)}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content)
        ]

        llm = await self._get_llm(project_id)
        response = await llm.ainvoke(messages)
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
