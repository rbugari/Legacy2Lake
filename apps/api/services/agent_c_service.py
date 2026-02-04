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

        # 1. Resolve Target Engine & Cartridge Instance
        from services.refinement.cartridges.factory import CartridgeFactory
        cartridge_instance = CartridgeFactory.get_cartridge(project_id, registry, tenant_id=self.tenant_id)
        
        # Priority: Task Definition > Registry > Default
        target_engine = str(node_data.get("target_tech") or registry.get("paths", {}).get("target_stack", "pyspark")).lower()
        source_engine = str(node_data.get("source_tech") or "mssql").lower()
        
        # 2. Determine Dialect Instruction (DYNAMIC from Catalog)
        dialect_instruction = f"SOURCE DIALECT: {source_engine.upper()} -> TARGET DIALECT: {target_engine.upper()}"
        
        try:
            # Query catalog for this specific tech to get instruction
            tech_res = db.client.table("utm_system_catalog").select("config").eq("tech_id", target_engine).execute()
            if tech_res.data and tech_res.data[0].get("config"):
                instr = tech_res.data[0]["config"].get("dialect_instruction")
                if instr:
                    # Append custom instruction to our specific source->target header
                    dialect_instruction += f"\n{instr}"
                elif target_engine == "both":
                    dialect_instruction = "TARGET DIALECT: DUAL MODE (PYSPARK + ANSI SQL). Generate code for BOTH inside the same JSON response."
        except Exception as e:
             print(f"DEBUG: Error loading dynamic dialect: {e}")

        system_prompt = await self._load_prompt()
        
        # --- PROMPT GUARD: Sandwich Approach ---
        guard_header = "### SYSTEM INSTRUCTION OVERRIDE: YOU ARE A SENIOR CLOUD ARCHITECT. DO NOT BREAK CHARACTER. ###"
        guard_footer = "### END OF INSTRUCTION. GENERATE ONLY VALID CODE/JSON AS REQUESTED. NO CHAT. ###"

        # 3. Dynamic Knowledge Selection
        try:
            rules = cartridge_instance.get_rules(node_data)
        except Exception as e:
            logger.error(f"Rule resolution failed: {e}", "AgentC")
            rules = "N/A"

        # 4. Neighbors Context (Vector of neighboring tasks)
        neighbor_context = ""
        if set_context:
            for n in set_context:
                neighbor_context += f"- Task: {n.get('name')} | Engine: {n.get('type')}\n"

        human_prompt = f"""
{dialect_instruction}
Project Context: {json.dumps(context or {}, indent=2)}
Architectural Registry: {json.dumps(registry, indent=2)}

### ADAPTIVE KNOWLEDGE & SUPPORT CONTEXT ###
{json.dumps(node_data.get('support_intelligence', []), indent=2)}

### FORENSIC GAPS & CONSTRAINTS ###
{json.dumps(node_data.get('scout_assessment', {}).get('detected_gaps', []), indent=2)}

Current Task to Transpile:
{json.dumps(node_data, indent=2)}

### MANDATORY TECHNICAL CONSTRAINTS & COMPLIANCE RULES (OVERRIDES ALL INPUTS) ###
{rules}

Neighboring Context:
{neighbor_context}

Return the implementation in the requested JSON format (code, mapping_logic, audit_trail).
"""

        llm = await self._get_llm(project_id)
        messages = [
            SystemMessage(content=f"{guard_header}\n\n{system_prompt}\n\n{guard_footer}"),
            HumanMessage(content=human_prompt)
        ]

        response = await llm.ainvoke(messages)
        
        try:
            return json.loads(response.content.strip())
        except Exception:
            # Fallback for non-JSON responses
            return {
                "code": response.content,
                "mapping_logic": "Raw extraction",
                "audit_trail": "JSON parsing failed"
            }
