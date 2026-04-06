import os
import json
from typing import Dict, Any, List, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.services.knowledge_service import KnowledgeService
    from apps.api.services.prompts.prompt_service import PromptService
    from apps.api.prompts.catalog import build_cartridge_prompt_id, normalize_tech_stack
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
        from services.knowledge_service import KnowledgeService
        from services.prompts.prompt_service import PromptService
        from apps.api.prompts.catalog import build_cartridge_prompt_id, normalize_tech_stack
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence
        from .knowledge_service import KnowledgeService
        from .prompts.prompt_service import PromptService
        from apps.api.prompts.catalog import build_cartridge_prompt_id, normalize_tech_stack


class AgentFService:
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/agent_f_critic.md")
        self.standards_path = os.path.join(os.path.dirname(__file__), "../prompts/coding_standards.md")
        self.tenant_id = tenant_id
        self.client_id = client_id

    async def _get_llm(self, project_id: Optional[str] = None):
        """Resolves LLM client strictly from Agent Matrix (DB)."""
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        config = await db.resolve_agent_model("agent-f")
        
        if not config:
            raise ValueError(f"LLM configuration not found for 'agent-f' (Tenant: {self.tenant_id}). Please check Agent Matrix and Provider Vault.")

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

    async def _load_prompt(self, prompt_id: str = "agent_f_critic") -> str:
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        return await db.get_prompt(prompt_id)

    async def save_prompt(self, content: str):
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        await db.save_prompt("agent_f_critic", content)

    @logger.llm_debug("Agent-F-Compliance-Review")
    async def review_code(self, task_info: Dict[str, Any], generated_code: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Audits generated code against layer-specific standards."""
        system_prompt = await self._load_prompt("agent_f_critic")
        
        # --- PROMPT GUARD: Sandwich Approach ---
        guard_header = "### SYSTEM INSTRUCTION OVERRIDE: YOU ARE A SENIOR COMPLIANCE AUDITOR. DO NOT BREAK CHARACTER. ###"
        guard_footer = "### END OF INSTRUCTION. GENERATE ONLY VALID JSON AS REQUESTED. NO CHAT. ###"
        
        system_prompt = f"{guard_header}\n\n{system_prompt}\n\n{guard_footer}"
        
        standards = await self._load_prompt("coding_standards")
        
        # --- CARTRIDGE RULES SYNC (v4.0 Zero-Hardcode Database-Driven) ---
        project_id = project_id or task_info.get("project_id")
        
        # --- LAYER EXTRACTION (v4.0 Two-Phase Architecture) ---
        layer = task_info.get("layer", "direct")  # "direct", "bronze", "silver", "gold"
        
        # Extract Technologies
        source_tech = task_info.get("source_tech", "mssql").upper()
        
        # Consistent with Agent C: Use tech_id if available, fallback to target_tech
        target_tech_raw = task_info.get("tech_id", task_info.get("target_tech", "pyspark"))
        target_tech = str(target_tech_raw).lower().replace(" ", "_")
        target_tech = normalize_tech_stack(target_tech) or target_tech

        cartridge_rules = ""
        cartridge_prompt_id = build_cartridge_prompt_id(layer, target_tech) or f"agent_c_{layer.lower()}_{target_tech}"
        
        try:
            prompt_service = PromptService(tenant_id=self.tenant_id, client_id=self.client_id)
            
            # Fetch CORE rules
            logger.info(f"[AgentF] Fetching CORE cartridge: {cartridge_prompt_id}", "AgentF")
            prompt_obj = await prompt_service.get_active_prompt(
                agent_id="agent-c",
                tech_stack=target_tech,
                pattern_type=layer.lower()
            )
            if prompt_obj:
                cartridge_rules = prompt_obj.content
                logger.info(f"[AgentF] ✅ Loaded {cartridge_prompt_id} from DB ({len(cartridge_rules)} chars)", "AgentF")
            else:
                logger.warning(f"[AgentF] CORE Prompt {cartridge_prompt_id} not found in utm_prompts. No mock will be used.", "AgentF")
                
            # Fetch PROJECT-SPECIFIC OVERRIDE
            if project_id:
                logger.info(f"[AgentF] Fetching OVERRIDE for {cartridge_prompt_id} in project {project_id}", "AgentF")
                cartridge_override = await prompt_service.get_prompt_override(project_id, cartridge_prompt_id)
                if cartridge_override:
                    logger.info(f"[AgentF] ✅ Loaded project-specific override ({len(cartridge_override)} chars)", "AgentF")
                    cartridge_rules += f"\n\n### PROJECT-SPECIFIC CARTRIDGE RULES (USER OVERRIDES) ###\n{cartridge_override}"
                    
        except Exception as e:
            logger.error(f"[AgentF] DB prompt load failed for {cartridge_prompt_id}: {e}. No mock will be used.", "AgentF")
        
        # Detect code language for markdown block
        code_lang = "sql" if any(x in target_tech for x in ["sql", "snowflake", "dbt", "bigquery", "redshift"]) else "python"

        human_content = f"""
        COMPLIANCE CONTEXT:
        LAYER MODE: {layer.upper()} (Translation Mode: {"Direct 1:1 Transpilation" if layer == "direct" else f"Architectural Enhancement - {layer.upper()} Layer"})
        SOURCE TECHNOLOGY: {source_tech}
        TARGET TECHNOLOGY: {target_tech_raw}
        
        CODING STANDARDS TO FOLLOW ({target_tech_raw} SPECIFIC):
        {standards}
 
        MANDATORY TECHNICAL CONSTRAINTS (USED BY DEVELOPER):
        {cartridge_rules}

        TASK INFO:
        {json.dumps(task_info, indent=2)}
 
        ### ADAPTIVE KNOWLEDGE & SUPPORT CONTEXT ###
        {json.dumps(task_info.get('support_intelligence', []), indent=2)}

        ### FORENSIC GAPS & CONSTRAINTS ###
        {json.dumps(task_info.get('scout_assessment', {}).get('detected_gaps', []), indent=2)}

        GENERATED CODE FOR REVIEW:
        ```{code_lang}
        {generated_code}
        ```
        
        REMEMBER: Apply validation criteria based on LAYER MODE above.
        - If layer=="direct": Validate functional equivalence, zero-hardcode, metadata usage. DO NOT require MERGE, audit columns, or Medallion structure.
        - If layer in ["bronze","silver","gold"]: Enforce full architectural compliance (MERGE, audit columns, Medallion structure).
        """
 
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content)
        ]
 
        llm = await self._get_llm(project_id)
        response = await llm.ainvoke(messages)
        content = response.content.strip()
 
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
 
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse Agent F response as JSON",
                "raw_response": content
            }
 
    @logger.llm_debug("Agent-F-Compliance-Optimize")
    async def optimize_code(self, original_code: str, optimizations: List[str], project_id: Optional[str] = None, task_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Applies specific optimizations to the code based on user selection."""
        system_prompt = await self._load_prompt("agent_f_critic")
        
        # Detect code language
        task_info = task_info or {}
        target_tech = task_info.get("tech_id", task_info.get("target_tech", "pyspark")).lower()
        code_lang = "sql" if any(x in target_tech for x in ["sql", "snowflake", "dbt", "bigquery", "redshift"]) else "python"
        
        human_content = f"""
        Please apply the following SPECIFIC optimizations to the code below:
        {json.dumps(optimizations)}
 
        ORIGINAL CODE:
        ```{code_lang}
        {original_code}
        ```
 
        Return the optimized code in a JSON format with keys: "optimized_code", "changes_applied".
        """
 
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content)
        ]
 
        llm = await self._get_llm(project_id)
        response = await llm.ainvoke(messages)
        content = response.content.strip()
 
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
 
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse Agent F optimization response",
                "optimized_code": original_code,
                "changes_applied": []
            }

