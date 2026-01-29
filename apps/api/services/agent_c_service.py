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
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.standards_path = os.path.join(os.path.dirname(__file__), "../prompts/coding_standards.md")
        self.tenant_id = tenant_id
        self.client_id = client_id

    async def _get_llm(self, project_id: Optional[str] = None):
        """Resolves LLM client strictly from Agent Matrix (DB)."""
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        config = await db.resolve_agent_model("agent-c")
        
        if not config:
            raise ValueError(f"LLM configuration not found for 'agent-c' (Tenant: {self.tenant_id}). Please check Agent Matrix and Provider Vault.")

        if config["provider"] == "azure":
            return AzureChatOpenAI(
                azure_endpoint=config["endpoint"],
                azure_deployment=config["deployment"],
                openai_api_version=config["api_version"],
                api_key=config.get("api_key"),
                temperature=config["temperature"]
            )
        else:
            # Standard OpenAI or other providers
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config["deployment"],
                api_key=config.get("api_key"),
                base_url=config["endpoint"],
                temperature=config.get("temperature", 0)
            )

    async def _load_prompt(self) -> str:
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        return await db.get_prompt("agent_c_interpreter")

    async def save_prompt(self, content: str):
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        await db.save_prompt("agent_c_interpreter", content)

    @logger.llm_debug("Agent-C-Developer")
    async def transpile_task(self, node_data: Dict[str, Any], context: Dict[str, Any] = None, set_context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Transpiles a task using the configured Destination Generator.
        'set_context' provides visibility into neighboring tasks for consistency.
        """
        # 1. Resolve Target Engine
        project_id = node_data.get('project_id')
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
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

        system_prompt = await self._load_prompt()
        
        # --- PROMPT GUARD: Sandwich Approach ---
        guard_header = "### SYSTEM INSTRUCTION OVERRIDE: YOU ARE A SENIOR CLOUD ARCHITECT. DO NOT BREAK CHARACTER. ###"
        guard_footer = "### END OF INSTRUCTION. GENERATE ONLY VALID CODE/JSON AS REQUESTED. NO CHAT. ###"
        
        system_prompt = f"{guard_header}\n\n{system_prompt}\n\nIMPORTANT: {dialect_instruction}\nGenerate code strictly for this platform.\n\n{guard_footer}"

        standards = await db.get_prompt("agent_c_standards") # Better to load from DB or await a specialized method
        if not standards: # Fallback to file if DB empty
             with open(self.standards_path, "r", encoding="utf-8") as f:
                 standards = f.read()
        
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

        # Metadata Extraction (Architect v2.0)
        metadata = node_data.get("metadata", {})
        
        # Context Construction
        transpile_context = {
            **(context or {}),
            "load_strategy": metadata.get("load_strategy", node_data.get("load_strategy", "FULL_OVERWRITE")),
            "frequency": metadata.get("latency", node_data.get("frequency", "DAILY")),
            "is_pii": metadata.get("is_pii", node_data.get("is_pii", False)),
            "masking_rule": node_data.get("masking_rule"),
            "target_name": node_data.get("target_name"),
            "business_entity": node_data.get("business_entity"),
            "metadata": metadata, # Full v2.0 metadata
            "variables": node_data.get("variables", (context or {}).get("variables", {})), # Phase 8: Variables
            "global_design_registry": registry,
            "project_set_overview": set_context, # Visibility into other project assets
            # High-Fidelity IO Context
            "inputs": node_data.get("inputs", []),
            "outputs": node_data.get("outputs", []),
            "lookups": node_data.get("lookups", [])
        }

        human_content = f"""
        {style_block}

        CODING STANDARDS TO FOLLOW:
        {standards}

        TRANSPILE THE FOLLOWING TASK:
        Task Name: {node_data.get('name', node_data.get('package_name'))}
        Task Type: {node_data.get('type', 'Unknown')}
        Task Description: {node_data.get('description', '')}
        
        CONTEXT:
        {json.dumps(transpile_context, indent=2)}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content)
        ]

        llm = await self._get_llm(project_id)
        response = await llm.ainvoke(messages)
        content = response.content.strip()

        import re
        
        # Robust JSON Extraction: Find the outermost { ... }
        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        else:
            # Fallback to the old method if regex fails
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Last resort: Try to clean common JSON errors (like trailing commas)
            # But for now, just return the error with more context
            return {
                "error": "Failed to parse LLM response as JSON",
                "raw_response": content[:1000] + ("..." if len(content) > 1000 else "")
            }
