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

    @staticmethod
    def _resolve_refinement_strategy(post_drafting_mode: Optional[str]) -> str:
        """Return mode-aware strategy guidance for Agent F review/optimization."""
        return {
            "drafting_delivery": "Terminal delivery path. Prioritize faithful equivalence and avoid imposing modernization-only patterns.",
            "structured_refinement": "Bounded refinement path. Enforce medallion consistency and governance quality without aggressive redesign.",
            "intelligent_reengineering": "Advanced path. Allow architectural improvements while preserving traceability and safety controls.",
        }.get(post_drafting_mode, "Default review path. Enforce layer-aware constraints from the task metadata.")

    @staticmethod
    def _resolve_review_layer(layer: str, post_drafting_mode: Optional[str]) -> str:
        """Drafting delivery evaluates functional equivalence even if execution layer is medallion-tagged."""
        normalized_layer = str(layer or "direct").lower()
        if post_drafting_mode in (None, "drafting_delivery"):
            return "direct"
        return normalized_layer

    @staticmethod
    def _is_reasonably_executable_direct_code(generated_code: str, target_tech: str) -> bool:
        """Use a narrow, tech-specific bar for drafting success in direct mode."""
        normalized_target = normalize_tech_stack(target_tech) or str(target_tech or "").lower()
        code = generated_code or ""

        if normalized_target != "pyspark":
            return False

        has_read = any(token in code for token in ["spark.read", ".read.table(", ".read.format(", ".read.parquet("])
        has_write = any(token in code for token in [".write", "saveAsTable(", ".parquet(", ".save("])
        has_config = "config.get(" in code or "globals().get(\"config\"" in code or "globals().get('config'" in code

        return has_read and has_write and has_config

    @staticmethod
    def _is_soft_drafting_direct_critique(critique_text: str) -> bool:
        """Identify critiques that are too strict for drafting but acceptable for refinement."""
        text = str(critique_text or "").lower()

        blocker_patterns = [
            "hardcoded",
            "zero-hardcode",
            "syntax error",
            "failed to parse",
            "empty code",
            "missing required import",
            "unresolved placeholder",
            "does not read",
            "does not write",
        ]
        if any(pattern in text for pattern in blocker_patterns):
            return False

        soft_patterns = [
            "header format is incorrect",
            "parameter semantics",
            "not tied to the documented metadata contract",
            "source query structure",
            "source read path is not functionally equivalent",
            "qualified_source",
            "qualified_target",
            "overwrite/union",
            "overwrite semantics",
            "delta existence checks",
            "target_path-based merge/write branching",
            "adds modernization/optimization behavior",
            "fallback logic",
            "type fidelity is uncertain",
            "simplified overwrite",
            "max_",
            # execution-layer / medallion concepts — not expected in direct drafting
            "silver layer",
            "silver-layer",
            "scd_2",
            "scd type 2",
            "slowly changing",
            "medallion",
            "historical version",
            "valid_from",
            "valid_to",
            "is_current",
            "incremental silver",
            "load strategy",
            "load_strategy",
            "merge logic",
            "upsert",
        ]
        return any(pattern in text for pattern in soft_patterns)

    @staticmethod
    def _code_has_literal_hardcodes(code: str) -> bool:
        """Detect hardcoded string literals for table/schema/catalog names in generated code.
        Mirrors the key checks in ValidationService._validate_direct_zero_hardcode so the
        normalizer doesn't promote code that the local validator already flagged."""
        import re
        patterns = [
            # Variable assignment: source_table = "literal", target_schema = "literal", etc.
            r'^\s*[A-Za-z_][A-Za-z0-9_]*(?:catalog|schema|table|table_name|path|object_name|source_name|target_name)\s*=\s*["\'][^"\']+["\']',
            # config.get with literal default for table/schema/catalog keys
            r'\bconfig\.get\(\s*["\'][^"\']*(?:table|schema|catalog)[^"\']*["\']\s*,\s*["\'][^"\']+["\']\s*\)',
            # spark.read.table("literal") or .load("literal") — literal passed directly
            r'spark\.read\b[\s\S]*?\.(?:table|load)\s*\(\s*["\'][^"\']+["\']',
            # df.write...saveAsTable("literal")
            r'\.saveAsTable\s*\(\s*["\'][^"\']+["\']',
        ]
        for line in code.splitlines():
            for p in patterns:
                if re.search(p, line, re.IGNORECASE):
                    return True
        return False

    @staticmethod
    def _is_structural_critique_blocker(critique_text: str) -> bool:
        """Only true structural issues (syntax, missing read/write) block drafting promotion.
        Style, architecture layer, and equivalence concerns are deferred to refinement."""
        text = str(critique_text or "").lower()
        structural_blockers = [
            "syntax error",
            "failed to parse",
            "empty code",
            "missing required import",
            "does not read",
            "does not write",
            "unresolved placeholder",
        ]
        return any(p in text for p in structural_blockers)

    @classmethod
    def _normalize_drafting_direct_review(
        cls,
        audit_report: Dict[str, Any],
        generated_code: str,
        target_tech: str,
        review_layer: str,
        post_drafting_mode: Optional[str],
    ) -> Dict[str, Any]:
        """Keep drafting permissive: promote REJECTED→IMPROVED when the code is
        structurally executable, contains no hardcoded literal table/schema names,
        and Agent F has no structural blockers (syntax errors, missing read/write).
        Architecture-layer, SCD, and semantics concerns are deferred to refinement."""
        if review_layer != "direct" or post_drafting_mode not in (None, "drafting_delivery"):
            return audit_report

        if (audit_report or {}).get("status") != "REJECTED":
            return audit_report

        if not cls._is_reasonably_executable_direct_code(generated_code, target_tech):
            return audit_report

        # Code-level check: real hardcoded literals block promotion (not critique text analysis)
        if cls._code_has_literal_hardcodes(generated_code):
            return audit_report

        critiques = audit_report.get("critique") or []
        if isinstance(critiques, str):
            critiques = [critiques]

        # Block only on structural critique issues (not style/architecture/equivalence)
        if any(cls._is_structural_critique_blocker(item) for item in critiques):
            return audit_report

        normalized = dict(audit_report)
        normalized["status"] = "IMPROVED"
        normalized["score"] = max(int(normalized.get("score") or 0), 7)
        normalized.setdefault("optimized_code", generated_code)
        normalized["critique"] = list(critiques) + [
            "Drafting direct normalization applied: code is executable and remaining objections are deferred to refinement."
        ]
        return normalized

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
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        post_drafting_mode = await db.get_post_drafting_mode(project_id) if project_id else None
        refinement_strategy = self._resolve_refinement_strategy(post_drafting_mode)
        
        # --- LAYER EXTRACTION (v4.0 Two-Phase Architecture) ---
        layer = task_info.get("layer", "direct")  # execution layer: "direct", "bronze", "silver", "gold"
        review_layer = self._resolve_review_layer(layer, post_drafting_mode)
        
        # Extract Technologies
        source_tech = task_info.get("source_tech", "mssql").upper()
        
        # Consistent with Agent C: Use tech_id if available, fallback to target_tech
        target_tech_raw = task_info.get("tech_id", task_info.get("target_tech", "pyspark"))
        target_tech = str(target_tech_raw).lower().replace(" ", "_")
        target_tech = normalize_tech_stack(target_tech) or target_tech

        cartridge_rules = ""
        # CRITICAL FIX: Load cartridge rules based on REVIEW_LAYER, not execution layer
        # In Drafting (post_drafting_mode=None), review_layer="direct" overrides silver/gold execution tags
        cartridge_prompt_id = build_cartridge_prompt_id(review_layer, target_tech) or f"agent_c_{review_layer.lower()}_{target_tech}"
        
        try:
            prompt_service = PromptService(tenant_id=self.tenant_id, client_id=self.client_id)
            
            # Fetch CORE rules
            logger.info(f"[AgentF] Fetching CORE cartridge: {cartridge_prompt_id}", "AgentF")
            prompt_obj = await prompt_service.get_active_prompt(
                agent_id="agent-c",
                tech_stack=target_tech,
                pattern_type=review_layer.lower()
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
        EXECUTION LAYER: {str(layer).upper()}
        REVIEW LAYER MODE: {review_layer.upper()} (Translation Mode: {"Direct 1:1 Transpilation" if review_layer == "direct" else f"Architectural Enhancement - {review_layer.upper()} Layer"})
        SOURCE TECHNOLOGY: {source_tech}
        TARGET TECHNOLOGY: {target_tech_raw}
        POST-DRAFTING MODE: {post_drafting_mode or "not_selected"}
        STRATEGY GUIDANCE: {refinement_strategy}
        
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
        
        REMEMBER: Apply validation criteria based on REVIEW LAYER MODE above.
        - If review_layer=="direct": Validate functional equivalence, zero-hardcode, metadata usage. DO NOT require MERGE, audit columns, or Medallion structure.
        - If review_layer in ["bronze","silver","gold"]: Enforce full architectural compliance (MERGE, audit columns, Medallion structure).
        - If post_drafting_mode=="drafting_delivery": Prefer strict equivalence checks and do not over-penalize for missing modernization patterns.
        - If post_drafting_mode=="structured_refinement": Prioritize bounded medallion consistency and deterministic governance controls.
        - If post_drafting_mode=="intelligent_reengineering": Accept higher-order improvements only if traceability and safety are preserved.
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
            parsed = json.loads(content)
            return self._normalize_drafting_direct_review(
                parsed,
                generated_code,
                target_tech,
                review_layer,
                post_drafting_mode,
            )
        except json.JSONDecodeError:
            recovered = self._recover_json_object(content)
            if recovered is not None:
                return self._normalize_drafting_direct_review(
                    recovered,
                    generated_code,
                    target_tech,
                    review_layer,
                    post_drafting_mode,
                )

            # Fallback: model returned plain optimized code instead of JSON contract.
            inferred_code = content
            if inferred_code.lower().startswith("python\n"):
                inferred_code = inferred_code.split("\n", 1)[1].strip()

            if inferred_code:
                return {
                    "status": "IMPROVED",
                    "optimized_code": inferred_code,
                    "critique": ["Agent F returned code-only output; JSON envelope was reconstructed automatically."],
                    "score": 7,
                    "raw_response": content
                }

            return {
                "error": "Failed to parse Agent F response as JSON",
                "raw_response": content
            }

    def _recover_json_object(self, text: str) -> Optional[Dict[str, Any]]:
        """Best-effort extraction when the model wraps JSON with extra text."""
        if not text:
            return None

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        candidate = text[start:end + 1]
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
 
    @logger.llm_debug("Agent-F-Compliance-Optimize")
    async def optimize_code(self, original_code: str, optimizations: List[str], project_id: Optional[str] = None, task_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Applies specific optimizations to the code based on user selection."""
        system_prompt = await self._load_prompt("agent_f_critic")
        
        # Detect code language
        task_info = task_info or {}
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        post_drafting_mode = await db.get_post_drafting_mode(project_id) if project_id else None
        refinement_strategy = self._resolve_refinement_strategy(post_drafting_mode)
        target_tech = task_info.get("tech_id", task_info.get("target_tech", "pyspark")).lower()
        code_lang = "sql" if any(x in target_tech for x in ["sql", "snowflake", "dbt", "bigquery", "redshift"]) else "python"
        
        human_content = f"""
        Please apply the following SPECIFIC optimizations to the code below:
        {json.dumps(optimizations)}

        POST-DRAFTING MODE: {post_drafting_mode or "not_selected"}
        STRATEGY GUIDANCE: {refinement_strategy}
 
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
            recovered = self._recover_json_object(content)
            if recovered is not None:
                return recovered

            inferred_code = content
            if inferred_code.lower().startswith("python\n"):
                inferred_code = inferred_code.split("\n", 1)[1].strip()

            if inferred_code:
                return {
                    "optimized_code": inferred_code,
                    "changes_applied": ["Recovered from non-JSON model output"]
                }

            return {
                "error": "Failed to parse Agent F optimization response",
                "optimized_code": original_code,
                "changes_applied": []
            }

