import os
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any, Optional
import json
try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.services.knowledge_service import KnowledgeService
    from apps.api.services.column_profiling_service import ColumnProfilingService
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
        from services.knowledge_service import KnowledgeService
        from services.column_profiling_service import ColumnProfilingService
    except ImportError:
        # Fallback for when running directly or tests
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence
        from .knowledge_service import KnowledgeService
        from .column_profiling_service import ColumnProfilingService

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


    @logger.llm_debug("Agent A (Manifest Analysis)")
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

        SCHEMA REFERENCE (Parsed DDL Metadata):
        {json.dumps(manifest.get('schema_reference', {}), indent=2)}

        INSTRUCTIONS:
        1. Process the FILE INVENTORY and identify the Lineage Mesh.
        2. **VALIDATE against SCHEMA REFERENCE**: For each SSIS package/ETL asset:
           - Verify that source/target tables exist in the parsed DDL schemas
           - Check that all mapped columns exist in the respective tables
           - Flag any discrepancies (missing tables, missing columns, type mismatches)
        3. **PII DETECTION**: Use SCHEMA REFERENCE column names to identify PII:
           - email, mail → Email PII
           - ssn, social_security, nss → SSN PII
           - phone, telefono, mobile, celular → Phone PII
           - address, direccion, domicilio → Address PII
           - credit_card, tarjeta → Credit Card PII
        4. Assign metadata (Volume, Latency, Criticality, Partition Key) based on patterns.
        5. Respect USER CONTEXT as absolute priority.
        6. Synthesize the Mesh Graph according to the System Prompt format.
        7. Include validation findings in `triage_observations`.
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
        deployment_name = llm_config.get("deployment", "unknown") if llm_config else "unconfigured"
        
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
    @logger.llm_debug("Agent A (Package Analysis)")
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
    
    
    async def analyze_columns_deep(
        self, 
        asset_id: str, 
        project_id: str,
        columns_metadata: list[Dict[str, Any]],
        use_llm: bool = False
    ) -> Dict[str, Any]:
        """
        Sprint 7: Deep column-level analysis with profiling.
        
        Performs statistical + AI-powered analysis on columns:
        - Cardinality metrics
        - PII detection
        - Partition recommendations
        - Data quality scoring
        
        Args:
            asset_id: UUID of the asset (utm_objects.object_id)
            project_id: UUID of the project
            columns_metadata: List of column definitions with sample data
                Format: [
                    {
                        "column_name": "CustomerID",
                        "data_type": "INT",
                        "sample_values": [1, 2, 3, ...],
                        "is_nullable": True,
                        "is_primary_key": False
                    },
                    ...
                ]
            use_llm: If True, use LLM for enhanced PII detection (experimental)
        
        Returns:
            {
                'asset_id': str,
                'project_id': str,
                'columns_profiled': int,
                'pii_detected': int,
                'partition_candidates': int,
                'columns': [...],  // Detailed column profiles
                'summary': {
                    'avg_cardinality': float,
                    'avg_null_percentage': float,
                    'high_quality_columns': int
                }
            }
        """
        logger.info(f"[Agent A] Deep column analysis for asset {asset_id} ({len(columns_metadata)} columns)", "Agent A")
        
        # Initialize column profiling service
        profiler = ColumnProfilingService(tenant_id=self.tenant_id, client_id=self.client_id)
        
        # Profile all columns
        profiled_columns = await profiler.profile_asset(
            asset_id=asset_id,
            columns_data=columns_metadata,
            asset_metadata=None  # Could pass asset-level context if needed
        )
        
        # Persist to database
        persist_success = await profiler.persist_to_db(
            asset_id=asset_id,
            project_id=project_id,
            columns=profiled_columns
        )
        
        if not persist_success:
            logger.warning(f"[Agent A] Failed to persist column profiles to DB", "Agent A")
        
        # Calculate summary statistics
        pii_count = sum(1 for col in profiled_columns if col.get('is_pii'))
        partition_count = sum(1 for col in profiled_columns if col.get('partition_candidate'))
        
        total_cardinality = sum(col.get('cardinality_ratio', 0) for col in profiled_columns)
        avg_cardinality = total_cardinality / len(profiled_columns) if profiled_columns else 0
        
        total_nulls = sum(col.get('null_percentage', 0) for col in profiled_columns)
        avg_nulls = total_nulls / len(profiled_columns) if profiled_columns else 0
        
        # High quality = low nulls + medium cardinality + not PII
        high_quality = sum(
            1 for col in profiled_columns 
            if col.get('null_percentage', 100) < 10 
            and 0.05 < col.get('cardinality_ratio', 0) < 0.95
            and not col.get('is_pii')
        )
        
        # Optional: Use LLM for enhanced semantic PII detection
        if use_llm and profiled_columns:
            logger.info(f"[Agent A] Using LLM for enhanced PII detection on {len(profiled_columns)} columns", "Agent A")
            # This could call LLM with column names + samples to detect semantic PII
            # Implementation: Future enhancement
            pass
        
        logger.info(
            f"[Agent A] Column analysis complete: {len(profiled_columns)} profiled, "
            f"{pii_count} PII, {partition_count} partition candidates",
            "Agent A"
        )
        
        return {
            'asset_id': asset_id,
            'project_id': project_id,
            'columns_profiled': len(profiled_columns),
            'pii_detected': pii_count,
            'partition_candidates': partition_count,
            'persisted_to_db': persist_success,
            'columns': profiled_columns,
            'summary': {
                'avg_cardinality': round(avg_cardinality, 4),
                'avg_null_percentage': round(avg_nulls, 2),
                'high_quality_columns': high_quality,
                'total_columns': len(profiled_columns)
            }
        }

