import os
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any
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
    
    def __init__(self):
        
        self.prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "agent_a_discovery.md")

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
        
        self.prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "agent_a_discovery.md")
        
    def _load_prompt(self, path: str = None) -> str:
        target_path = path or self.prompt_path
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()

    def save_prompt(self, content: str):
        """Updates the system prompt file."""
        with open(self.prompt_path, "w", encoding="utf-8") as f:
            f.write(content)


    async def analyze_manifest(self, manifest: Dict[str, Any], system_prompt_override: str = None) -> Dict[str, Any]:
        """Analyzes the full project manifest to build the Mesh Graph."""
        
        system_prompt = system_prompt_override or self._load_prompt()
        project_id = manifest.get('project_id')
        
        # Release 1.3: Fetch Design Registry
        db = SupabasePersistence()
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
        1. Process the FILE INVENTORY.
        2. **PRIORITY**: If a file in the inventory has entries in USER CONTEXT, those rules/descriptions MUST take precedence over automated inference.
        3. **VIRTUAL STEPS**: If the USER CONTEXT describes a logical process, validation, or manual step that DOES NOT exist in the FILE INVENTORY, you MUST create a node for it:
            - Set `id` to `virtual_[unique_name]`.
            - Set `category` to `CORE`.
            - Create `edges` from/to this virtual node based on the context description.
        4. **OPERATIONAL INTELLIGENCE**: For each file, infer:
            - `frequency`: (HOURLY, DAILY, MONTHLY, NEAR-RT) based on names like 'hourly_load' or context.
            - `load_strategy`: (INCREMENTAL, FULL_OVERWRITE, SCD_2) based on presence of watermarks, merge logic, or 'Dim' naming (for SCD).
            - `criticality`: (P1, P2, P3) based on importance.
        5. **SOVEREIGNTY & SECURITY**: Analyze `signatures` and `snippet` to detect:
            - `is_pii`: Set to true if you detect columns/data like emails, SSN, personal IDs, birthdays, or salaries.
            - `masking_rule`: Suggest a logic like 'SHA2 hashing' or 'Redacted'.
        6. Assign a FUNCTIONAL CATEGORY (CORE, SUPPORT, IGNORED) to all relevant files.
        7. Discover dependencies (Edges).
        8. Synthesize the Mesh Graph. Return ONLY the JSON requested in the System Prompt. Ensure the 'nodes' in your response include the new fields: `frequency`, `load_strategy`, `criticality`, `is_pii`, `masking_rule`.
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
        system_prompt = self._load_prompt()
        
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
