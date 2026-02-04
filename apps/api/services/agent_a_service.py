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
        """Resolves LLM client strictly from Agent Matrix (DB)."""
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        resolved = await db.resolve_agent_model("agent-a")
        
        if not resolved:
            raise ValueError(f"LLM configuration not found for 'agent-a' (Tenant: {self.tenant_id}). Please check Agent Matrix and Provider Vault.")
            
        provider = resolved.get("provider", "azure").lower()
        endpoint = resolved.get("endpoint")
        key = resolved.get("api_key") 
        deployment = resolved.get("deployment")
        api_version = resolved.get("api_version")
        temperature = resolved.get("temperature", 0)
            
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

        SUPPORT INTELLIGENCE (Context & Docs from Storage):
        {json.dumps(manifest.get('support_intelligence', []), indent=2)}

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
        # Assuming gpt-4 or 4-turbo window is sufficient
        llm_config = await db.resolve_agent_model("agent-a")
        deployment_name = llm_config.get("deployment", "unknown")
        
        try: # This try block was missing in the original code, causing the indentation issue.
            llm = await self._get_llm()
            response = await llm.ainvoke(messages)
            content = response.content
            
            # Clean potential markdown formatting more robustly
            import re
            
            # 1. Try JSON extraction
            json_match = re.search(r'({.*})', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # 2. Try YAML extraction (Markdown block)
            yaml_match = re.search(r'```(?:yaml|yml)(.*?)```', content, re.DOTALL)
            if not yaml_match:
                # Try generic markdown block
                yaml_match = re.search(r'```(.*?)```', content, re.DOTALL)
                
            if yaml_match:
                try:
                    import yaml
                    parsed = yaml.safe_load(yaml_match.group(1))
                    
                    # Schema Mapping: If LLM used 'lineage_mesh' instead of 'mesh_graph'
                    if "lineage_mesh" in parsed and "mesh_graph" not in parsed:
                        parsed["mesh_graph"] = parsed.pop("lineage_mesh")
                    
                    # Ensure basic fields exist
                    if "mesh_graph" not in parsed:
                        parsed["mesh_graph"] = {"nodes": [], "edges": []}
                        
                    return parsed
                except Exception as ex:
                    logger.error(f"YAML Parsing fallback failed: {ex}", "Agent A")
            
            # 3. Last resort fallback
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
                return json.loads(content)
                
            return json.loads(content) # Final attempt (might raise exception)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Agent A response: {e}. Raw content length: {len(content)}", "Agent A")
            
            # Diagnostic info
            file_count = len(manifest.get("file_inventory", []))
            
            return {
                "error": f"Failed to parse LLM response: {str(e)}", 
                "diagnostic": {
                    "content_length": len(content),
                    "file_count": file_count,
                    "model_used": deployment_name
                },
                "raw_response": content[:1000], 
                "mesh_graph": {"nodes": [], "edges": []}
            }
        except Exception as e:
             logger.error(f"Agent A Analysis error: {e}", "Agent A")
             return {
                 "error": str(e),
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
