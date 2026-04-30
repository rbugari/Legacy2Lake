import os
import json
import asyncio
import contextlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Cartridges
from apps.api.services.generation.cartridges.spark_destination import SparkDestination
from apps.api.services.generation.cartridges.snowflake_destination import SnowflakeDestination
try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.services.knowledge_service import KnowledgeService
    # Sprint 8: Real-Time Validation
    from apps.api.services.validation_service import ValidationService
    from apps.api.services.test_generator_service import TestGeneratorService
    # Sprint 9: Zero-Hardcode Generation (Legacy)
    from apps.api.services.schema_metadata_service import SchemaMetadataService
    from apps.api.services.parameter_extractor_service import ParameterExtractor
    # v4.0: Zero-Hardcode Core (Database-driven prompts)
    from apps.api.services.prompts.prompt_service import PromptService
    from apps.api.services.prompts.prompt_assembler import PromptAssembler
    from apps.api.prompts.catalog import build_cartridge_prompt_id, normalize_tech_stack
    # Sprint 10: Schema Evolution
    from apps.api.services.schema_version_service import SchemaVersionService
    from apps.api.services.migration_generator_service import MigrationGeneratorService, Platform
    from apps.api.services.compatibility_checker_service import CompatibilityChecker
    # Sprint 11: Data Quality Framework
    from apps.api.services.quality_rule_engine_service import QualityRuleEngine
    from apps.api.services.metrics_calculator_service import MetricsCalculator
    from apps.api.services.anomaly_detector_service import AnomalyDetector
    # Sprint 12: Performance Optimization
    from apps.api.services.query_optimizer_service import QueryOptimizer
    from apps.api.services.cache_manager_service import CacheManager
    from apps.api.services.parallel_processor_service import ParallelProcessor
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
        from services.knowledge_service import KnowledgeService
        # Sprint 8: Real-Time Validation
        from services.validation_service import ValidationService
        from services.test_generator_service import TestGeneratorService
        # Sprint 9: Zero-Hardcode Generation (Legacy)
        from services.schema_metadata_service import SchemaMetadataService
        from services.parameter_extractor_service import ParameterExtractor
        # v4.0: Zero-Hardcode Core (Database-driven prompts)
        from services.prompts.prompt_service import PromptService
        from services.prompts.prompt_assembler import PromptAssembler
        from apps.api.prompts.catalog import build_cartridge_prompt_id, normalize_tech_stack
        # Sprint 10: Schema Evolution
        from services.schema_version_service import SchemaVersionService
        from services.migration_generator_service import MigrationGeneratorService, Platform
        from services.compatibility_checker_service import CompatibilityChecker
        # Sprint 11: Data Quality Framework
        from services.quality_rule_engine_service import QualityRuleEngine
        from services.metrics_calculator_service import MetricsCalculator
        from services.anomaly_detector_service import AnomalyDetector
        # Sprint 12: Performance Optimization
        from services.query_optimizer_service import QueryOptimizer
        from services.cache_manager_service import CacheManager
        from services.parallel_processor_service import ParallelProcessor
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence
        from .knowledge_service import KnowledgeService
        # Sprint 8: Real-Time Validation
        from .validation_service import ValidationService
        from .test_generator_service import TestGeneratorService
        # Sprint 9: Zero-Hardcode Generation (Legacy)
        from .schema_metadata_service import SchemaMetadataService
        from .parameter_extractor_service import ParameterExtractor
        # v4.0: Zero-Hardcode Core (Database-driven prompts)
        from .prompts.prompt_service import PromptService
        from .prompts.prompt_assembler import PromptAssembler
        from apps.api.prompts.catalog import build_cartridge_prompt_id, normalize_tech_stack
        # Sprint 10: Schema Evolution
        from .schema_version_service import SchemaVersionService
        from .migration_generator_service import MigrationGeneratorService, Platform
        from .compatibility_checker_service import CompatibilityChecker
        # Sprint 11: Data Quality Framework
        from .quality_rule_engine_service import QualityRuleEngine
        from .metrics_calculator_service import MetricsCalculator
        from .anomaly_detector_service import AnomalyDetector
        # Sprint 12: Performance Optimization
        from .query_optimizer_service import QueryOptimizer
        from .cache_manager_service import CacheManager
        from .parallel_processor_service import ParallelProcessor


class AgentCService:
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.standards_path = os.path.join(os.path.dirname(__file__), "../prompts/coding_standards.md")
        self.tenant_id = tenant_id
        self.client_id = client_id
        
        # v4.0: Zero-Hardcode Core - Initialize prompt services
        self.prompt_service: Optional[PromptService] = None
        self.prompt_assembler: Optional[PromptAssembler] = None
        self._prompts_initialized = False
        
        # Sprint 12: Performance Optimization - Initialize services
        self.cache_manager: Optional[CacheManager] = None
        self.query_optimizer: Optional[QueryOptimizer] = None
        self.parallel_processor: Optional[ParallelProcessor] = None
        self._cache_initialized = False

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

    async def _ainvoke_with_cancellation(self, llm, messages, project_id: Optional[str], poll_seconds: float = 2.0):
        """Invoke LLM while polling cancellation flag so stop requests can interrupt long calls."""
        if not project_id:
            return await llm.ainvoke(messages)

        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        invoke_task = asyncio.create_task(llm.ainvoke(messages))

        try:
            while True:
                done, _ = await asyncio.wait({invoke_task}, timeout=poll_seconds)
                if invoke_task in done:
                    return invoke_task.result()

                if await db.check_cancellation(project_id):
                    invoke_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await invoke_task
                    raise RuntimeError("Process cancelled by user")
        finally:
            if not invoke_task.done():
                invoke_task.cancel()

    async def _load_prompt(self) -> str:
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        return await db.get_prompt("agent_c_interpreter")

    async def save_prompt(self, content: str):
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        await db.save_prompt("agent_c_interpreter", content)

    async def _initialize_prompts(self):
        """Initialize v4.0 prompt services (lazy initialization)."""
        if not self._prompts_initialized:
            try:
                self.prompt_service = PromptService(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id
                )
                self.prompt_assembler = PromptAssembler()
                
                self._prompts_initialized = True
                logger.info("[AgentC v4.0] Prompt services initialized", "AgentC")
                
            except Exception as e:
                logger.error(f"[AgentC v4.0] Failed to initialize prompt services: {e}", "AgentC")
                raise
    
    async def _initialize_cache(self):
        """Initialize cache manager on first use (lazy initialization)."""
        if not self._cache_initialized:
            try:
                # Get Redis URL from environment or use default
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
                
                self.cache_manager = CacheManager(
                    redis_url=redis_url,
                    default_ttl=3600,  # 1 hour for code generation
                    key_prefix="utm:agent_c:"
                )
                
                await self.cache_manager.connect()
                logger.info("[AgentC Sprint12] Cache manager initialized", "AgentC")
                
                # Initialize query optimizer
                self.query_optimizer = QueryOptimizer(platform="databricks")
                logger.info("[AgentC Sprint12] Query optimizer initialized", "AgentC")
                
                # Initialize parallel processor
                self.parallel_processor = ParallelProcessor(max_workers=10, mode="auto")
                logger.info("[AgentC Sprint12] Parallel processor initialized", "AgentC")
                
                self._cache_initialized = True
                
            except Exception as e:
                logger.warning(f"[AgentC Sprint12] Cache initialization failed: {e}. Running without cache.", "AgentC")
                self.cache_manager = None
                self.query_optimizer = None
                self.parallel_processor = None

    def _normalize_layer_value(self, raw_value: Optional[Any]) -> Optional[str]:
        if raw_value in (None, ""):
            return None

        value = str(raw_value).strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "direct": "direct",
            "direct_translation": "direct",
            "raw": "bronze",
            "landing": "bronze",
            "staging": "bronze",
            "bronze": "bronze",
            "curated": "silver",
            "refined": "silver",
            "silver": "silver",
            "serving": "gold",
            "presentation": "gold",
            "gold": "gold"
        }
        return aliases.get(value)

    def _resolve_execution_layer(self, node_data: Dict[str, Any], target_engine: str) -> str:
        metadata = node_data.get("metadata") or {}
        logical_medulla = metadata.get("logical_medulla") or {}

        preferred_candidates = [
            metadata.get("lineage_group"),
            logical_medulla.get("layer"),
            logical_medulla.get("lineage_group"),
            metadata.get("layer"),
        ]

        for candidate in preferred_candidates:
            normalized = self._normalize_layer_value(candidate)
            if normalized and normalized != "direct":
                return normalized

        weak_candidates = [
            node_data.get("layer"),
            metadata.get("layer"),
            metadata.get("lineage_group"),
            logical_medulla.get("layer"),
            logical_medulla.get("lineage_group"),
        ]

        for candidate in weak_candidates:
            normalized = self._normalize_layer_value(candidate)
            if normalized:
                return normalized

        asset_name = str(node_data.get("package_name") or node_data.get("name") or "").lower()
        asset_type = str(node_data.get("type") or "").lower()
        if target_engine in {"pyspark", "databricks", "fabric"} and (
            asset_name.endswith(".dtsx") or "ssis" in asset_type
        ):
            return "silver"

        return "direct"
    
    async def _load_project_custom_instructions(self, project_id: str) -> str:
        """
        Load project-specific custom instructions from project settings (v4.0).
        
        This is Level 3 of the 3-level prompt architecture:
        - Level 1: Agent System Prompt (platform-managed)
        - Level 2: Cartridge Prompt (generic tech template)
        - Level 3: Project Custom Instructions (user-editable)
        
        Args:
            project_id: Project UUID
            
        Returns:
            Custom instructions as markdown string (empty if not set)
        """
        try:
            db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
            settings = await db.get_project_settings(project_id)
            
            if settings and isinstance(settings, dict):
                custom_instructions = settings.get('custom_instructions', '')
                
                if custom_instructions and len(custom_instructions.strip()) > 0:
                    logger.info(
                        f"[AgentC v4.0] ✅ Loaded project custom instructions: {len(custom_instructions)} chars",
                        "AgentC"
                    )
                    return custom_instructions
                else:
                    logger.info("[AgentC v4.0] No custom instructions found for project", "AgentC")
                    return ""
            else:
                logger.warning(f"[AgentC v4.0] Project settings not found for project_id={project_id}", "AgentC")
                return ""
                
        except Exception as e:
            logger.error(f"[AgentC v4.0] Failed to load custom instructions: {e}", "AgentC")
            return ""

    @staticmethod
    def _resolve_refinement_strategy(post_drafting_mode: Optional[str]) -> str:
        """Return mode-aware strategy guidance used by prompt assembly and human prompt."""
        return {
            "drafting_delivery": "Terminal path selected. Keep output faithful and avoid additional refinement assumptions.",
            "structured_refinement": "Apply bounded medallion optimization (Bronze/Silver/Gold) with quality and governance consistency.",
            "intelligent_reengineering": "Allow advanced optimization opportunities and structural improvements when they clearly improve target architecture.",
        }.get(post_drafting_mode, "Use standard direct modernization guidance for the selected layer.")

    @staticmethod
    def _resolve_generation_layer(layer: str, post_drafting_mode: Optional[str]) -> str:
        """In drafting delivery, force direct-transpilation prompts even for medallion-tagged assets."""
        normalized_layer = str(layer or "direct").lower()
        if post_drafting_mode in (None, "drafting_delivery"):
            return "direct"
        return normalized_layer

    @staticmethod
    def _resolve_target_table_alias(
        node_data: Dict[str, Any],
        schema_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Resolve target table alias for prompt variables, including SQL assets that only expose outputs."""

        direct_target = (
            node_data.get("target_table")
            or node_data.get("target_name")
            or (schema_context or {}).get("table_name")
        )
        if direct_target:
            return str(direct_target).strip()

        outputs = node_data.get("outputs") or []
        if isinstance(outputs, list):
            for output in outputs:
                if not output:
                    continue
                normalized = str(output).strip().strip("[]")
                if normalized:
                    return normalized

        return None

    @staticmethod
    def _build_parameter_aliases(
        parameters_context: Optional[Dict[str, Any]],
        execution_layer: str,
    ) -> Dict[str, Any]:
        """Expose flat aliases commonly used by cartridges/prompts.

        This is a compatibility layer only: it does not alter source-of-truth
        parameters, it only surfaces equivalent keys to improve template fill.
        """
        params = parameters_context or {}
        layer = str(execution_layer or "direct").lower()

        return {
            "catalog": params.get("catalog_name", "main"),
            "source_schema": params.get("bronze_schema", "bronze_raw"),
            "target_schema": params.get(f"{layer}_schema", layer),
            "bronze_schema": params.get("bronze_schema", "bronze_raw"),
            "silver_schema": params.get("silver_schema", "silver_curated"),
            "gold_schema": params.get("gold_schema", "gold_business"),
            "bronze_path": params.get("bronze_path", "/mnt/datalake/bronze"),
            "silver_path": params.get("silver_path", "/mnt/datalake/silver"),
            "gold_path": params.get("gold_path", "/mnt/datalake/gold"),
            "bronze_prefix": params.get("bronze_prefix", "raw_"),
            "silver_prefix": params.get("silver_prefix", "stg_"),
            "gold_prefix": params.get("gold_prefix", ""),
            "tech_stack": params.get("tech_stack"),
        }

    @staticmethod
    def _is_sql_target_engine(target_engine: Optional[str]) -> bool:
        return AgentCService._resolve_target_output_family(target_engine) == "sql"

    @staticmethod
    def _is_pyspark_target_engine(target_engine: Optional[str]) -> bool:
        return AgentCService._resolve_target_output_family(target_engine) == "pyspark"

    @staticmethod
    def _resolve_target_output_family(target_engine: Optional[str]) -> Optional[str]:
        """Classify the target into the output family expected by cartridges/prompts."""
        try:
            from apps.api.services.refinement.cartridges.tech_stack_contracts import SQLFlavor, resolve_contract
        except ImportError:
            try:
                from services.refinement.cartridges.tech_stack_contracts import SQLFlavor, resolve_contract
            except ImportError:
                from .refinement.cartridges.tech_stack_contracts import SQLFlavor, resolve_contract

        contract = resolve_contract(target_engine)
        if contract:
            return "pyspark" if contract.sql_flavor == SQLFlavor.PYSPARK else "sql"

        normalized = normalize_tech_stack(str(target_engine or "").lower()) or str(target_engine or "").lower()
        if normalized in {"pyspark", "spark", "ms_fabric", "snowflake"}:
            return "pyspark"
        if normalized:
            return "sql"
        return None

    @classmethod
    def _extract_generated_code_for_target(
        cls,
        raw_result: Dict[str, Any],
        target_engine: Optional[str],
    ) -> tuple[str, str]:
        """Prefer the target-matching code field and avoid cross-language ambiguity."""
        if cls._is_sql_target_engine(target_engine):
            if raw_result.get("sql_code"):
                return raw_result.get("sql_code") or "", "sql_code"
            if raw_result.get("code"):
                return raw_result.get("code") or "", "code"
            return raw_result.get("pyspark_code") or "", "pyspark_code"

        if cls._is_pyspark_target_engine(target_engine):
            if raw_result.get("pyspark_code"):
                return raw_result.get("pyspark_code") or "", "pyspark_code"
            if raw_result.get("code"):
                return raw_result.get("code") or "", "code"
            return raw_result.get("sql_code") or "", "sql_code"

        for field_name in ("code", "pyspark_code", "sql_code"):
            if raw_result.get(field_name):
                return raw_result.get(field_name) or "", field_name
        return "", "none"

    @classmethod
    def _normalize_generated_output_fields(
        cls,
        final_result: Dict[str, Any],
        target_engine: Optional[str],
    ) -> Dict[str, Any]:
        """Keep only the language output that matches the resolved target."""
        normalized_result = dict(final_result)
        code_value = normalized_result.get("code")

        if cls._is_pyspark_target_engine(target_engine):
            if code_value and not normalized_result.get("pyspark_code"):
                normalized_result["pyspark_code"] = code_value
            normalized_result.pop("sql_code", None)
            return normalized_result

        if cls._is_sql_target_engine(target_engine):
            if code_value and not normalized_result.get("sql_code"):
                normalized_result["sql_code"] = code_value
            normalized_result.pop("pyspark_code", None)
            return normalized_result

        return normalized_result
    
    def _extract_schema_from_code(self, code: str, table_name: str) -> Dict[str, Any]:
        """
        Extract schema from generated PySpark/SQL code (Sprint 13).
        
        Looks for patterns like:
            inferred_schema = [("col1", "type1"), ("col2", "type2")]
            StructType([StructField("col1", StringType())])
            CREATE TABLE ... (col1 TYPE1, col2 TYPE2)
            enforced_schema = \"\"\"col1 TYPE1, col2 TYPE2\"\"\"
        
        Returns schema_context compatible dict with columns array.
        """
        import re
        
        columns = []
        
        # Pattern 1: inferred_schema = [("col", "type"), ...]
        pattern1 = r'inferred_schema\s*=\s*\[((?:\s*\(["\'][\w_]+["\']\s*,\s*["\'][\w_]+["\']\)\s*,?\s*)*)\]'
        match1 = re.search(pattern1, code, re.DOTALL)
        
        if match1:
            schema_str = match1.group(1)
            # Parse tuples: ("column", "type")
            tuple_pattern = r'\(["\'](\w+)["\']\s*,\s*["\'](\w+)["\']\)'
            for col_match in re.finditer(tuple_pattern, schema_str):
                col_name = col_match.group(1)
                col_type = col_match.group(2)
                columns.append({
                    'name': col_name,
                    'type': col_type,
                    'nullable': True,
                    'is_primary_key': False,
                    'is_foreign_key': False
                })
        
        # Pattern 2: StructType with StructField (PySpark)
        if not columns:
            pattern2 = r'StructType\(\[(.*?)\]\)'
            match2 = re.search(pattern2, code, re.DOTALL)
            if match2:
                struct_str = match2.group(1)
                # Parse StructField("col", Type(), nullable)
                field_pattern = r'StructField\(["\'](\w+)["\']\s*,\s*(\w+Type\(\))'
                for field_match in re.finditer(field_pattern, struct_str):
                    col_name = field_match.group(1)
                    col_type = field_match.group(2).replace('Type()', '').lower()
                    columns.append({
                        'name': col_name,
                        'type': col_type,
                        'nullable': True,
                        'is_primary_key': False,
                        'is_foreign_key': False
                    })
        
        # Pattern 3: CREATE TABLE syntax (SQL)
        if not columns:
            pattern3 = r'CREATE\s+TABLE.*?\((.*?)\)'
            match3 = re.search(pattern3, code, re.IGNORECASE | re.DOTALL)
            if match3:
                ddl_str = match3.group(1)
                # Parse: column_name TYPE [NOT NULL]
                col_pattern = r'(\w+)\s+([\w\(\)]+)(?:\s+NOT\s+NULL)?'
                for col_match in re.finditer(col_pattern, ddl_str):
                    col_name = col_match.group(1).lower()
                    col_type = col_match.group(2).upper()
                    if col_name not in ['constraint', 'primary', 'foreign', 'key']:
                        columns.append({
                            'name': col_name,
                            'type': col_type,
                            'nullable': 'NOT NULL' not in col_match.group(0).upper(),
                            'is_primary_key': False,
                            'is_foreign_key': False
                        })
        
        # Pattern 4: enforced_schema/schema = """col TYPE, ..."""
        if not columns:
            pattern4 = r'(?:enforced_schema|schema)\s*=\s*"""(.*?)"""'
            match4 = re.search(pattern4, code, re.DOTALL)
            if match4:
                schema_block = match4.group(1)
                # Parse each line: col_name TYPE,
                line_pattern = r'^\s*(\w+)\s+([\w\(\)]+)\s*,?\s*$'
                for line in schema_block.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    col_match = re.match(line_pattern, line)
                    if col_match:
                        col_name = col_match.group(1).lower()
                        col_type = col_match.group(2).upper()
                        columns.append({
                            'name': col_name,
                            'type': col_type,
                            'nullable': True,
                            'is_primary_key': False,
                            'is_foreign_key': False
                        })
        
        if columns:
            return {
                'table_name': table_name,
                'columns': columns,
                'primary_key': [],
                'foreign_keys': [],
                'row_count': None
            }
        
        return None
    
    @logger.llm_debug("Agent-C-Developer")
    async def transpile_task(self, node_data: Dict[str, Any], context: Dict[str, Any] = None, set_context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        def _json_serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)
        
        """
        Transpiles a task using the configured Destination Generator.
        'set_context' provides visibility into neighboring tasks for consistency.
        
        Sprint 8 Enhancement:
            - Real-time validation of generated code
            - Automatic test case generation
            - Retry logic if validation fails (max 3 attempts)
        
        Sprint 9 Enhancement:
            - Zero-hardcode generation using schema metadata
            - Extracts table schema from utm_objects.metadata
            - Extracts project parameters from utm_design_registry
            - Generates template-based code with Jinja2
            - Injects schema + parameters into LLM context
            - Returns schema and parameters in response
        
        Sprint 10 Enhancement:
            - Schema evolution tracking and version management
            - Automatic schema change detection
            - Migration script generation for schema changes
            - Breaking change identification and warnings
            - Compatibility scoring between schema versions
        
        Sprint 11 Enhancement:
            - Data quality validation using configurable rules
            - Quality metrics calculation (completeness, accuracy, consistency, etc.)
            - Anomaly detection (statistical outliers, volume spikes, null spikes)
            - Quality scoring (0-100%) for generated tables
            - Automatic quality reporting and violation tracking
        
        Sprint 12 Enhancement:
            - Distributed caching for fast responses (70-90% cache hit rate target)
            - Query optimization (predicate pushdown, partition pruning, etc.)
            - Performance metrics tracking
            - Cache invalidation on schema changes
        """
        # ================================================================
        # SPRINT 12: PERFORMANCE OPTIMIZATION (Cache Check)
        # ================================================================
        import time
        import hashlib
        
        start_time = time.time()
        cache_hit = False
        optimization_metadata = None
        
        # Initialize cache if not already done
        await self._initialize_cache()
        
        # Generate cache key from node_data (deterministic hash)
        if self.cache_manager:
            retry_feedback = node_data.get('agent_f_retry_feedback') or {}
            retry_signature = None
            if retry_feedback:
                retry_signature = hashlib.sha256(
                    json.dumps(retry_feedback, sort_keys=True, default=str).encode('utf-8')
                ).hexdigest()[:16]
            cache_key_data = {
                'asset_id': node_data.get('asset_id'),
                'project_id': node_data.get('project_id'),
                'tech_id': node_data.get('tech_id'),
                'layer': node_data.get('layer'),
                'source_tech': node_data.get('source_tech'),
                'retry_signature': retry_signature,
                'version': '12.2_agent_f_retry_contracts'  # Cache version (invalidate on prompt/contract changes)
            }
            cache_key = self.cache_manager.generate_key("transpile", **cache_key_data)
            
            # Check cache
            logger.info(f"[AgentC Sprint12] Checking cache: {cache_key}", "AgentC")
            cached_result = await self.cache_manager.get(cache_key)
            
            if cached_result:
                cache_hit = True
                cache_duration_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"[AgentC Sprint12] ✅ Cache HIT! Response time: {cache_duration_ms:.1f}ms",
                    "AgentC"
                )
                
                # Add cache metadata
                cached_result["performance"] = {
                    "cache_hit": True,
                    "response_time_ms": round(cache_duration_ms, 2),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                return cached_result
            
            logger.info(f"[AgentC Sprint12] Cache MISS. Generating code...", "AgentC")
        
        # 1. Resolve Target Engine
        project_id = node_data.get('project_id')
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        registry_raw = await db.get_design_registry(project_id) if project_id else []
        registry = KnowledgeService.flatten_knowledge(registry_raw)
        post_drafting_mode = await db.get_post_drafting_mode(project_id) if project_id else None
        refinement_strategy = self._resolve_refinement_strategy(post_drafting_mode)

        # 1. Resolve Target Engine & Cartridge Instance
        try:
            from apps.api.services.refinement.cartridges.factory import CartridgeFactory
        except ImportError:
            try:
                from services.refinement.cartridges.factory import CartridgeFactory
            except ImportError:
                from .refinement.cartridges.factory import CartridgeFactory
        
        # Priority: Task Definition > Registry > Default
        # Accept both tech_id (Sprint 0 tests) and target_tech (legacy)
        target_engine_raw = str(node_data.get("tech_id") or node_data.get("target_tech") or registry.get("paths", {}).get("target_stack", "pyspark"))
        
        # Normalize target_engine: remove spaces, parentheses, extract main tech name
        # "Databricks (PySpark)" -> "databricks"
        # "Snowflake" -> "snowflake"
        # "Azure Synapse" -> "azure_synapse"
        target_engine = target_engine_raw.lower()
        if '(' in target_engine:
            target_engine = target_engine.split('(')[0].strip()
        target_engine = target_engine.replace(' ', '_')
        
        source_engine = str(node_data.get("source_tech") or "mssql").lower()
        layer = self._resolve_execution_layer(node_data, target_engine)
        generation_layer = self._resolve_generation_layer(layer, post_drafting_mode)
        
        logger.info(
            f"[AgentC] target_engine={target_engine}, source_engine={source_engine}, "
            f"execution_layer={layer}, generation_layer={generation_layer}",
            "AgentC"
        )
        
        # Pass target_engine to factory so it can override registry default
        cartridge_instance = CartridgeFactory.get_cartridge(project_id, registry, tenant_id=self.tenant_id, target_tech=target_engine)
        logger.info(f"[AgentC] Cartridge selected: {cartridge_instance.__class__.__name__}", "AgentC")
        
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

        try:
            system_prompt = await self._load_prompt()
            if not system_prompt:
                logger.warning("system_prompt is None. No mock fallback will be used!", "AgentC")
                system_prompt = ""
        except Exception as e:
            logger.error(f"Error loading system prompt: {e}. No mock fallback will be used!", "AgentC")
            system_prompt = ""
        
        # --- PROMPT GUARD: Sandwich Approach ---
        guard_header = "### SYSTEM INSTRUCTION OVERRIDE: YOU ARE A SENIOR CLOUD ARCHITECT. DO NOT BREAK CHARACTER. ###"
        guard_footer = "### END OF INSTRUCTION. GENERATE ONLY VALID CODE/JSON AS REQUESTED. NO CHAT. ###"

        # ================================================================
        # SPRINT 9: ZERO-HARDCODE GENERATION (Schema + Parameters Extraction)
        # ================================================================
        schema_context = None
        parameters_context = None
        template_code = None
        
        # Extract asset schema from utm_objects.metadata
        asset_id = node_data.get('asset_id') or node_data.get('object_id')
        
        if asset_id and project_id:
            try:
                logger.info(f"[AgentC Sprint9] Extracting schema for asset_id={asset_id}", "AgentC")
                
                # Extract schema metadata
                schema_service = SchemaMetadataService(tenant_id=self.tenant_id, project_id=project_id)
                table_schema = await schema_service.get_table_schema(asset_id)
                
                if table_schema:
                    schema_context = {
                        'table_name': table_schema.table_name,
                        'columns': [
                            {
                                'name': col.name,
                                'type': col.data_type,
                                'nullable': col.nullable,
                                'is_primary_key': col.is_primary_key,
                                'is_foreign_key': col.is_foreign_key
                            }
                            for col in table_schema.columns
                        ],
                        'primary_key': table_schema.primary_key,
                        'foreign_keys': [
                            {
                                'column': fk.column,
                                'ref_table': fk.ref_table,
                                'ref_column': fk.ref_column
                            }
                            for fk in table_schema.foreign_keys
                        ],
                        'row_count': table_schema.row_count
                    }
                    
                    logger.info(
                        f"[AgentC Sprint9] ✅ Schema extracted: {table_schema.table_name}, "
                        f"{len(table_schema.columns)} columns, PK={table_schema.primary_key}",
                        "AgentC"
                    )
                else:
                    logger.warning(f"[AgentC Sprint9] No schema found for asset_id={asset_id}", "AgentC")
                    
            except Exception as e:
                logger.error(f"[AgentC Sprint9] Schema extraction failed: {e}", "AgentC")
        
        # Extract project parameters from utm_design_registry
        if project_id:
            try:
                logger.info(f"[AgentC Sprint9] Extracting parameters for project_id={project_id}", "AgentC")
                
                # Extract parameters
                param_extractor = ParameterExtractor(tenant_id=self.tenant_id, project_id=project_id)
                params = await param_extractor.extract_parameters()
                
                if params:
                    parameters_context = {
                        'bronze_path': params.bronze_path,
                        'silver_path': params.silver_path,
                        'gold_path': params.gold_path,
                        'bronze_schema': params.bronze_schema,
                        'silver_schema': params.silver_schema,
                        'gold_schema': params.gold_schema,
                        'bronze_prefix': params.bronze_prefix,
                        'silver_prefix': params.silver_prefix,
                        'gold_prefix': params.gold_prefix,
                        'catalog_name': params.catalog_name,
                        'tech_stack': target_engine
                    }
                    
                    logger.info(
                        f"[AgentC Sprint9] ✅ Parameters extracted: "
                        f"catalog={params.catalog_name}, tech={target_engine}",
                        "AgentC"
                    )
                else:
                    logger.warning(f"[AgentC Sprint9] No parameters found for project_id={project_id}", "AgentC")
                    
            except Exception as e:
                logger.error(f"[AgentC Sprint9] Parameter extraction failed: {e}", "AgentC")
        
        # ================================================================
        # SPRINT 8.5: ORIGIN ANALYSIS (SSIS Parsing for Triage Dashboard)
        # ================================================================
        origin_analysis = None
        transformations_list = []
        source_queries = []
        complexity_score = 0
        
        if asset_id and project_id:
            try:
                logger.info(f"[AgentC Sprint8.5] Extracting origin analysis for asset_id={asset_id}", "AgentC")
                
                # Get asset info to find the original SSIS file
                asset_info = await db.get_asset_by_id(asset_id)
                
                if asset_info and asset_info.get('metadata', {}).get('logical_medulla'):
                    # Asset already has medulla from Discovery
                    medulla = asset_info['metadata']['logical_medulla']
                    connections = asset_info['metadata'].get('connections', [])
                    
                    logger.info(f"[AgentC Sprint8.5] Using medulla from Discovery (cached)", "AgentC")
                    
                    # Extract origin analysis from medulla
                    origin_analysis = await self._extract_origin_analysis(medulla, connections)
                    transformations_list = await self._extract_transformations(medulla)
                    source_queries = await self._extract_source_queries(medulla)
                    complexity_score = await self._calculate_complexity_score(transformations_list)
                    
                    logger.info(
                        f"[AgentC Sprint8.5] ✅ Origin analysis complete: "
                        f"{len(transformations_list)} transformations, "
                        f"complexity={complexity_score}/100",
                        "AgentC"
                    )
                    
                    # Persist to utm_objects Sprint 8 columns
                    await self._persist_origin_analysis(
                        object_id=asset_id,  # Use asset_id (same as object_id)
                        origin_analysis=origin_analysis,
                        transformations_list=transformations_list,
                        source_queries=source_queries,
                        complexity_score=complexity_score,
                        db=db
                    )
                    
            except Exception as e:
                logger.warning(f"[AgentC Sprint8.5] Origin analysis unavailable: {e}. Continuing without this enrichment.", "AgentC")
                # Continue without origin analysis - not critical for code generation
        
        # ================================================================
        # SPRINT 10: SCHEMA EVOLUTION (Version Tracking & Migration)
        # ================================================================
        schema_version_info = None
        migration_scripts = None
        compatibility_info = None
        
        if schema_context and asset_id and project_id:
            try:
                logger.info(f"[AgentC Sprint10] Tracking schema evolution for asset_id={asset_id}", "AgentC")
                
                # Initialize Sprint 10 services
                version_service = SchemaVersionService(tenant_id=self.tenant_id, project_id=project_id)
                
                # Capture current schema snapshot
                current_snapshot = await version_service.capture_schema_snapshot(asset_id)
                
                schema_version_info = {
                    'version_number': current_snapshot.version_number,
                    'timestamp': current_snapshot.timestamp.isoformat(),
                    'is_breaking': False,
                    'changes_detected': 0
                }
                
                logger.info(
                    f"[AgentC Sprint10] ✅ Schema snapshot captured: v{current_snapshot.version_number}",
                    "AgentC"
                )
                
                # Check if there's a previous version to compare
                if current_snapshot.version_number > 1:
                    try:
                        # Get previous version
                        previous_snapshot = await version_service.get_schema_version(
                            asset_id, 
                            current_snapshot.version_number - 1
                        )
                        
                        # Detect changes
                        changes = version_service._detect_changes(previous_snapshot, current_snapshot)
                        
                        if changes:
                            logger.info(
                                f"[AgentC Sprint10] 📊 Schema changes detected: {len(changes)} changes",
                                "AgentC"
                            )
                            
                            # Check compatibility
                            checker = CompatibilityChecker()
                            compatibility_result = checker.check_compatibility(
                                previous_snapshot,
                                current_snapshot
                            )
                            
                            compatibility_info = compatibility_result.to_dict()
                            
                            # Generate migration scripts
                            platform_map = {
                                'pyspark': Platform.PYSPARK,
                                'spark': Platform.PYSPARK,
                                'snowflake': Platform.SNOWFLAKE,
                                'fabric': Platform.MS_FABRIC,
                                'gcp': Platform.GCP_BIGQUERY,
                                'aws': Platform.AWS_REDSHIFT,
                                'postgresql': Platform.POSTGRESQL
                            }
                            
                            platform = platform_map.get(target_engine, Platform.PYSPARK)
                            migration_generator = MigrationGeneratorService(platform=platform)
                            
                            migration_script = migration_generator.generate_migration(
                                table_name=schema_context['table_name'],
                                changes=changes,
                                catalog=parameters_context.get('catalog_name', 'main') if parameters_context else 'main',
                                schema=parameters_context.get(f'{layer}_schema', layer) if parameters_context else layer
                            )
                            
                            migration_scripts = {
                                'forward_sql': migration_script.forward_sql,
                                'rollback_sql': migration_script.rollback_sql,
                                'description': migration_script.description,
                                'breaking': migration_script.breaking,
                                'requires_data_migration': migration_script.requires_data_migration,
                                'data_migration_sql': migration_script.data_migration_sql,
                                'risk_assessment': migration_generator.estimate_migration_risk(changes),
                                'migration_strategy': checker.suggest_migration_strategy(compatibility_result)
                            }
                            
                            schema_version_info['is_breaking'] = migration_script.breaking
                            schema_version_info['changes_detected'] = len(changes)
                            
                            logger.info(
                                f"[AgentC Sprint10] ✅ Migration scripts generated: "
                                f"breaking={migration_script.breaking}, "
                                f"compatibility={compatibility_result.compatibility_score:.1f}%",
                                "AgentC"
                            )
                            
                            # Log warnings if breaking changes detected
                            if compatibility_result.breaking_changes:
                                for warning in compatibility_result.warnings:
                                    logger.warning(f"[AgentC Sprint10] {warning}", "AgentC")
                        else:
                            logger.info(f"[AgentC Sprint10] No schema changes detected", "AgentC")
                    
                    except Exception as e:
                        logger.error(f"[AgentC Sprint10] Schema comparison failed: {e}", "AgentC")
                        
            except Exception as e:
                logger.error(f"[AgentC Sprint10] Schema evolution tracking failed: {e}", "AgentC")
        
        # ================================================================
        # SPRINT 11: DATA QUALITY FRAMEWORK (Quality Validation)
        # ================================================================
        quality_report = None
        metrics_report = None
        anomaly_report = None
        
        if schema_context and asset_id and project_id:
            try:
                logger.info(f"[AgentC Sprint11] Validating data quality for table={schema_context.get('table_name')}", "AgentC")
                
                table_name = schema_context.get('table_name')
                catalog = parameters_context.get('catalog_name', 'main') if parameters_context else 'main'
                schema = parameters_context.get(f'{layer}_schema', layer) if parameters_context else layer
                
                # Initialize Sprint 11 services
                rule_engine = QualityRuleEngine(tenant_id=self.tenant_id, project_id=project_id)
                metrics_calculator = MetricsCalculator(tenant_id=self.tenant_id, project_id=project_id)
                anomaly_detector = AnomalyDetector(tenant_id=self.tenant_id, project_id=project_id)
                
                # 1. Evaluate quality rules
                quality_result = await rule_engine.evaluate_table(
                    table_name=table_name,
                    catalog=catalog,
                    schema=schema
                )
                
                quality_report = {
                    'quality_score': quality_result.quality_score,
                    'rules_evaluated': quality_result.rules_evaluated,
                    'rules_passed': quality_result.rules_passed,
                    'rules_failed': quality_result.rules_failed,
                    'total_rows': quality_result.total_rows,
                    'violations': [v.to_dict() for v in quality_result.violations[:5]],  # Top 5 violations
                    'timestamp': quality_result.timestamp.isoformat()
                }
                
                logger.info(
                    f"[AgentC Sprint11] ✅ Quality validation complete: "
                    f"score={quality_result.quality_score:.1f}%, "
                    f"passed={quality_result.rules_passed}/{quality_result.rules_evaluated}",
                    "AgentC"
                )
                
                # 2. Calculate quality metrics
                metrics_result = await metrics_calculator.calculate_metrics(
                    table_name=table_name,
                    catalog=catalog,
                    schema=schema
                )
                
                metrics_report = {
                    'overall_score': metrics_result.overall_score,
                    'completeness': metrics_result.completeness_score,
                    'accuracy': metrics_result.accuracy_score,
                    'consistency': metrics_result.consistency_score,
                    'timeliness': metrics_result.timeliness_score,
                    'validity': metrics_result.validity_score,
                    'uniqueness': metrics_result.uniqueness_score,
                    'timestamp': metrics_result.timestamp.isoformat()
                }
                
                logger.info(
                    f"[AgentC Sprint11] 📊 Metrics calculated: overall={metrics_result.overall_score:.1f}%",
                    "AgentC"
                )
                
                # 3. Detect anomalies
                anomalies_result = await anomaly_detector.detect_anomalies(
                    table_name=table_name,
                    catalog=catalog,
                    schema=schema
                )
                
                anomaly_report = {
                    'anomalies_detected': anomalies_result.anomalies_detected,
                    'critical_count': anomalies_result.critical_count,
                    'high_count': anomalies_result.high_count,
                    'medium_count': anomalies_result.medium_count,
                    'low_count': anomalies_result.low_count,
                    'anomalies': [a.to_dict() for a in anomalies_result.anomalies[:5]],  # Top 5 anomalies
                    'timestamp': anomalies_result.timestamp.isoformat()
                }
                
                logger.info(
                    f"[AgentC Sprint11] 🔍 Anomaly detection complete: "
                    f"{anomalies_result.anomalies_detected} anomalies found "
                    f"({anomalies_result.critical_count} critical)",
                    "AgentC"
                )
                
                # Log warnings for critical quality issues
                if quality_result.quality_score < 70:
                    logger.warning(
                        f"[AgentC Sprint11] ⚠️ Low quality score: {quality_result.quality_score:.1f}% "
                        f"({quality_result.rules_failed} rules failed)",
                        "AgentC"
                    )
                
                if anomalies_result.critical_count > 0:
                    logger.warning(
                        f"[AgentC Sprint11] ⚠️ {anomalies_result.critical_count} critical anomalies detected",
                        "AgentC"
                    )
                
            except Exception as e:
                logger.error(f"[AgentC Sprint11] Data quality validation failed: {e}", "AgentC")
        
        # v4.0: Generate code using database-driven prompts (if schema + params available)
        if schema_context and parameters_context:
            try:
                logger.info(f"[AgentC v4.0] Generating code from DB prompt for layer={generation_layer}", "AgentC")
                
                # Initialize prompt services
                await self._initialize_prompts()
                
                # Load prompt from database
                prompt = await self.prompt_service.get_active_prompt(
                    agent_id="agent-c",
                    tech_stack=target_engine,
                    pattern_type=generation_layer
                )
                
                if prompt:
                    # Build context for prompt assembly
                    context = {
                        'schema': table_schema.__dict__ if hasattr(table_schema, '__dict__') else table_schema,
                        'params': params.__dict__ if hasattr(params, '__dict__') else params,
                        'layer': generation_layer,
                        'target_engine': target_engine,
                        'table_name': table_schema.table_name if hasattr(table_schema, 'table_name') else 'unknown',
                        'columns': [col.__dict__ if hasattr(col, '__dict__') else col for col in table_schema.columns] if hasattr(table_schema, 'columns') else [],
                    }

                    # Top-level aliases used by prompt templates/cartridges
                    context.update(self._build_parameter_aliases(parameters_context, layer))
                    
                    # Enrich context with formatted helpers
                    context = self.prompt_assembler.enrich_context(context)
                    
                    # Assemble final prompt with context injection
                    template_code = self.prompt_assembler.build(
                        base_prompt=prompt.content,
                        context=context,
                        format="simple"
                    )
                    
                    logger.info(
                        f"[AgentC v4.0] ✅ Code generated from DB prompt: {len(template_code)} chars (prompt: {prompt.prompt_id})",
                        "AgentC"
                    )
                else:
                    logger.warning(
                        f"[AgentC v4.0] No prompt found for agent-c/{target_engine}/{generation_layer}, skipping template generation",
                        "AgentC"
                    )
                    template_code = None
                
            except Exception as e:
                logger.error(f"[AgentC v4.0] DB prompt generation failed: {e}", "AgentC")
                template_code = None

        # 3. Dynamic Knowledge Selection (v4.0 Core + Override Architecture)
        # Level 1: Core System Rules (Read-only, dictates structure)
        # Level 2: Project-specific Overrides (User-editable extensions)
        
        rules = ""
        core_rules = ""
        cartridge_override = ""
        
        if node_data.get("cartridge_prompt"):
            # Backward compatibility: Direct injection (Sprint 0 tests)
            core_rules = node_data["cartridge_prompt"]
            logger.info(f"[AgentC] Using cartridge_prompt from node_data ({len(core_rules)} chars)", "AgentC")
        else:
            # v4.0 Database-driven approach
            cartridge_prompt_id = build_cartridge_prompt_id(generation_layer, target_engine) or f"agent_c_{generation_layer}_{target_engine}"
            
            try:
                await self._initialize_prompts()
                
                # Fetch CORE rules
                logger.info(f"[AgentC] Fetching CORE cartridge: {cartridge_prompt_id}", "AgentC")
                prompt_obj = await self.prompt_service.get_prompt(cartridge_prompt_id)
                if prompt_obj:
                    core_rules = prompt_obj.content
                    logger.info(f"[AgentC] \u2705 Loaded {cartridge_prompt_id} from DB ({len(core_rules)} chars)", "AgentC")
                else:
                    logger.warning(f"[AgentC] CORE Prompt {cartridge_prompt_id} not found in utm_prompts. No mock will be used.", "AgentC")
                    core_rules = ""
                
                # Fetch PROJECT-SPECIFIC OVERRIDE
                if project_id:
                    logger.info(f"[AgentC] Fetching OVERRIDE for {cartridge_prompt_id} in project {project_id}", "AgentC")
                    cartridge_override = await self.prompt_service.get_prompt_override(project_id, cartridge_prompt_id)
                    if cartridge_override:
                        logger.info(f"[AgentC] \u2705 Loaded project-specific override ({len(cartridge_override)} chars)", "AgentC")
                
            except Exception as e:
                logger.error(f"[AgentC] DB prompt load failed: {e}. No mock will be used. Proceeding with empty rules.", "AgentC")
                core_rules = ""
        
        # Combine Core + Override
        rules = f"{core_rules}"
        if cartridge_override:
            rules += f"\n\n### PROJECT-SPECIFIC CARTRIDGE RULES (USER OVERRIDES) ###\n"
            rules += f"The following rules were defined by the user for this project and MUST be followed alongside the core rules above:\n"
            rules += cartridge_override

        # v4.0: Pre-resolve variables in Level 2 prompts (Cartridges)
        # This ensures placeholders like {gold_schema} are resolved before reaching the LLM
        if rules and (schema_context or parameters_context):
            try:
                logger.info(f"[AgentC v4.0] Pre-resolving variables in cartridge rules", "AgentC")
                await self._initialize_prompts()
                
                # Build resolution context (flat for alias matching)
                res_context = {
                    'layer': generation_layer,
                    'target_engine': target_engine,
                    'post_drafting_mode': post_drafting_mode,
                    'refinement_strategy': refinement_strategy,
                }
                res_context.update(node_data)
                if parameters_context:
                    res_context.update(parameters_context)
                if schema_context:
                    res_context.update(schema_context)

                # Alias compatibility for cartridge placeholders
                if parameters_context:
                    res_context.update(self._build_parameter_aliases(parameters_context, layer))

                # Common aliases used by direct cartridges
                target_table = self._resolve_target_table_alias(node_data, schema_context)
                source_table = (
                    node_data.get("source_table")
                    or node_data.get("source_name")
                    or node_data.get("business_entity")
                )
                if target_table:
                    res_context["target_table"] = target_table
                if source_table:
                    res_context["source_table"] = source_table
                
                # Enrich and build
                res_context = self.prompt_assembler.enrich_context(res_context)
                rules = self.prompt_assembler.build(
                    base_prompt=rules,
                    context=res_context,
                    format="simple"
                )
                logger.info(f"[AgentC v4.0] ✅ Cartridge rules resolved ({len(rules)} chars)", "AgentC")
            except Exception as e:
                logger.error(f"[AgentC v4.0] Failed to resolve cartridge variables: {e}", "AgentC")

        # 3.5. Load Project Custom Instructions (v4.0: 3-Level Architecture)
        # Level 3: Project-specific user adjustments (editable via UI)
        custom_instructions = ""
        if project_id:
            custom_instructions = await self._load_project_custom_instructions(project_id)

        # 4. Neighbors Context (Vector of neighboring tasks)
        neighbor_context = ""
        if set_context:
            for n in set_context:
                neighbor_context += f"- Task: {n.get('name')} | Engine: {n.get('type')}\n"

        retry_code_lang = "sql" if target_engine not in {"pyspark", "spark", "databricks", "ms_fabric", "snowflake"} else "python"
        retry_feedback_block = ""
        if node_data.get('agent_f_retry_feedback'):
            retry_feedback_block = f"""
    ### AGENT F RETRY CONTRACT (MANDATORY REPAIR PASS) ###
    This generation is a retry after Agent F rejected the previous implementation.
    You MUST fix every item below before returning code.
    {json.dumps(node_data.get('agent_f_retry_feedback'), indent=2, default=_json_serialize)}

    ### PREVIOUS REJECTED IMPLEMENTATION ###
    ```{retry_code_lang}
    {node_data.get('previous_generated_code') or '(not available)'}
    ```
    """

        human_prompt = f"""
{dialect_instruction}
Project Context: {json.dumps(context or {}, indent=2, default=_json_serialize)}
Architectural Registry: {json.dumps(registry, indent=2, default=_json_serialize)}

    ### POST-DRAFTING EXECUTION MODE ###
    Mode: {post_drafting_mode or "not_selected"}
    Strategy Guidance: {refinement_strategy}

### SPRINT 9: ZERO-HARDCODE SCHEMA & PARAMETERS (USE THESE FOR ALL CODE GENERATION) ###
Schema Metadata:
{json.dumps(schema_context, indent=2, default=_json_serialize) if schema_context else "N/A"}

Project Parameters:
{json.dumps(parameters_context, indent=2, default=_json_serialize) if parameters_context else "N/A"}

Template Code (Reference):
```python
{template_code if template_code else "N/A"}
```

IMPORTANT: Use the schema metadata and project parameters above to generate code WITHOUT HARDCODED VALUES.
- Column names: Use schema.columns list
- Table names: Use parameters.{layer}_prefix + schema.table_name
- Paths: Use parameters.{layer}_path
- Primary keys: Use schema.primary_key
- Foreign keys: Use schema.foreign_keys

### ADAPTIVE KNOWLEDGE & SUPPORT CONTEXT ###
{json.dumps(node_data.get('support_intelligence', []), indent=2, default=_json_serialize)}

### FORENSIC GAPS & CONSTRAINTS ###
{json.dumps(node_data.get('scout_assessment', {}).get('detected_gaps', []), indent=2, default=_json_serialize)}

{retry_feedback_block}

### SOURCE SCRIPT (COMPLETE ORIGINAL CODE - TRANSPILE THIS FAITHFULLY) ###
This is the full original source code you MUST transpile. Do NOT generate a generic stub.
Translate ALL logic: every column, every JOIN, every condition, every business rule.
```
{node_data.get('raw_content') or '(source code not available - use schema metadata and inputs/outputs above)'}
```

Current Task to Transpile:
{json.dumps(node_data, indent=2, default=_json_serialize)}

### MANDATORY TECHNICAL CONSTRAINTS & COMPLIANCE RULES (OVERRIDES ALL INPUTS) ###
{rules}

### PROJECT CUSTOM INSTRUCTIONS (USER-DEFINED ADJUSTMENTS) ###
{custom_instructions if custom_instructions else "(No custom instructions defined for this project)"}

Neighboring Context:
{neighbor_context}

OUTPUT CONTRACT:
- If target is SQL, return the implementation in `sql_code` and do NOT return `pyspark_code`.
- If target is PySpark, return the implementation in `pyspark_code` and do NOT return `sql_code`.
- Include `code` only as a compatibility mirror of the primary implementation.
- The implementation must faithfully transpile the provided SOURCE SCRIPT, not a 2-line generic stub.
- Preserve procedures, temp tables, handlers, variables, joins, filters, hashes, SCD logic, control-table writes, and business transformations whenever present in the source.

Return the implementation in the requested JSON format (mapping_logic, audit_trail, and the correct target-specific code field).
"""

        llm = await self._get_llm(project_id)
        messages = [
            SystemMessage(content=f"{guard_header}\n\n{system_prompt}\n\n{guard_footer}"),
            HumanMessage(content=human_prompt)
        ]
        
        # ================================================================
        # SPRINT 8: REAL-TIME VALIDATION LOOP (MAX 3 ATTEMPTS)
        # ================================================================
        validator = ValidationService()
        test_generator = TestGeneratorService()
        
        max_attempts = 3
        attempt = 0
        generated_code = None
        validation_result = None
        validation_history = []
        
        while attempt < max_attempts:
            attempt += 1
            logger.info(f"[AgentC] Code generation attempt {attempt}/{max_attempts}", "AgentC")
            
            # Generate code (with transient network retry)
            llm_retry_attempts = 3
            response = None
            last_invoke_error = None
            for llm_attempt in range(1, llm_retry_attempts + 1):
                try:
                    response = await self._ainvoke_with_cancellation(llm, messages, project_id)
                    break
                except Exception as invoke_error:
                    last_invoke_error = invoke_error
                    error_name = type(invoke_error).__name__
                    error_text = str(invoke_error).lower()

                    if "cancelled by user" in error_text:
                        raise

                    is_transient = (
                        "connection error" in error_text
                        or "timeout" in error_text
                        or "readerror" in error_text
                        or "apiconnectionerror" in error_name.lower()
                        or "apitimeouterror" in error_name.lower()
                    )

                    if not is_transient or llm_attempt >= llm_retry_attempts:
                        raise

                    backoff_seconds = 2 ** (llm_attempt - 1)
                    logger.warning(
                        f"[AgentC] Transient LLM error on attempt {llm_attempt}/{llm_retry_attempts}: {error_name}. Retrying in {backoff_seconds}s",
                        "AgentC"
                    )
                    await asyncio.sleep(backoff_seconds)

            if response is None:
                raise last_invoke_error or RuntimeError("LLM returned no response")
            
            # DEBUG: Log raw LLM response
            logger.info(f"[AgentC DEBUG] Raw LLM response type: {type(response)}", "AgentC")
            logger.info(f"[AgentC DEBUG] Raw LLM response content length: {len(str(response.content))}", "AgentC")
            logger.info(f"[AgentC DEBUG] Raw LLM response (first 500 chars): {str(response.content)[:500]}", "AgentC")
            
            try:
                raw_result = json.loads(response.content.strip())
                generated_code, code_field_used = self._extract_generated_code_for_target(raw_result, target_engine)
                logger.info(f"[AgentC DEBUG] Parsed as JSON, extracted '{code_field_used}' field: {len(generated_code)} chars", "AgentC")
            except Exception as e:
                # Fallback for non-JSON responses
                logger.warning(f"[AgentC DEBUG] JSON parsing failed: {e}, using raw content", "AgentC")
                generated_code = response.content
                raw_result = {
                    "code": generated_code,
                    "mapping_logic": "Raw extraction",
                    "audit_trail": "JSON parsing failed"
                }
            
            # Validate generated code
            logger.info(f"[AgentC] Validating generated code ({len(generated_code)} chars)", "AgentC")
            
            validation_result = await validator.validate_code(
                code=generated_code,
                tech_id=target_engine,
                layer=generation_layer,
                context=node_data
            )
            
            validation_history.append({
                'attempt': attempt,
                'is_valid': validation_result.is_valid,
                'errors_count': validation_result.errors_count,
                'warnings_count': validation_result.warnings_count
            })
            
            if validation_result.is_valid:
                # Validation passed! Break loop
                logger.info(f"[AgentC] ✅ Validation passed on attempt {attempt}", "AgentC")
                break
            else:
                # Validation failed
                logger.warning(
                    f"[AgentC] ❌ Validation failed on attempt {attempt}: "
                    f"{validation_result.errors_count} errors, {validation_result.warnings_count} warnings",
                    "AgentC"
                )
                
                if attempt < max_attempts:
                    # Provide feedback to LLM for regeneration
                    feedback = validation_result.get_llm_feedback()
                    logger.info(f"[AgentC] Providing feedback to LLM:\n{feedback}", "AgentC")
                    
                    # Add feedback to messages for retry
                    messages.append(HumanMessage(content=generated_code))
                    messages.append(SystemMessage(content=f"CODE VALIDATION FAILED:\n\n{feedback}\n\nPlease regenerate the code fixing the issues above."))
                else:
                    # Max attempts reached
                    logger.error(
                        f"[AgentC] ❌ Max validation attempts ({max_attempts}) reached. Returning code with errors.",
                        "AgentC"
                    )
        
        # ================================================================
        # SPRINT 8: GENERATE TEST CASES (if validation passed)
        # ================================================================
        test_code = None
        if validation_result and validation_result.is_valid:
            try:
                logger.info(f"[AgentC] Generating test cases for validated code", "AgentC")
                
                test_metadata = {
                    'source_table': node_data.get('source_table'),
                    'target_table': node_data.get('target_table'),
                    'layer': generation_layer,
                    'tech_id': target_engine
                }
                
                test_code = await test_generator.generate_tests(
                    code=generated_code,
                    tech_id=target_engine,
                    metadata=test_metadata
                )
                
                logger.info(f"[AgentC] ✅ Test cases generated ({len(test_code)} chars)", "AgentC")
            
            except Exception as e:
                logger.error(f"[AgentC] Test generation failed: {e}", "AgentC")
                test_code = None
        
        # ================================================================
        # BUILD FINAL RESPONSE (Enhanced with Sprint 8 data)
        # ================================================================
        try:
            final_result = json.loads(response.content.strip())
        except Exception:
            final_result = {
                "code": generated_code,
                "mapping_logic": "Raw extraction",
                "audit_trail": "JSON parsing failed"
            }
        
        # Add Sprint 8 validation metadata
        final_result["validation"] = {
            "is_valid": validation_result.is_valid if validation_result else False,
            "attempts": attempt,
            "errors_count": validation_result.errors_count if validation_result else 0,
            "warnings_count": validation_result.warnings_count if validation_result else 0,
            "history": validation_history,
            "details": validation_result.to_dict() if validation_result else None
        }
        
        # Add test cases
        final_result["test_code"] = test_code
        
        # Add Sprint 9 schema & parameters
        final_result["schema"] = schema_context
        final_result["parameters"] = parameters_context
        
        # Add Sprint 10 schema evolution data
        final_result["schema_version"] = schema_version_info
        final_result["migration_scripts"] = migration_scripts
        final_result["compatibility"] = compatibility_info
        
        # Add Sprint 11 data quality data
        final_result["quality"] = quality_report
        final_result["metrics"] = metrics_report
        final_result["anomalies"] = anomaly_report
        
        # ================================================================
        # SPRINT 12: QUERY OPTIMIZATION & CACHING
        # ================================================================
        
        # Optimize queries in generated code
        if self.query_optimizer and generated_code and validation_result and validation_result.is_valid:
            try:
                logger.info(f"[AgentC Sprint12] Optimizing queries in generated code", "AgentC")
                
                # Detect query type (SQL vs PySpark)
                query_type = "pyspark" if target_engine in ["pyspark", "spark"] else "sql"
                
                # Simple heuristic: Look for SELECT/FROM patterns
                if "SELECT" in generated_code.upper() or "FROM" in generated_code.upper():
                    # Build table statistics (if available from schema)
                    table_stats = {}
                    if schema_context:
                        table_stats[schema_context['table_name']] = {
                            'rows': schema_context.get('row_count', 1000000),
                            'partitions': []  # TODO: Extract from schema metadata
                        }
                    
                    # Optimize
                    optimization_result = await self.query_optimizer.optimize_query(
                        query=generated_code,
                        query_type=query_type,
                        table_stats=table_stats
                    )
                    
                    optimization_metadata = {
                        'optimizations_applied': optimization_result.optimizations_applied,
                        'estimated_speedup': optimization_result.estimated_speedup,
                        'cost_before': optimization_result.cost_before.total_cost,
                        'cost_after': optimization_result.cost_after.total_cost,
                        'recommendations': optimization_result.optimizations_applied
                    }
                    
                    logger.info(
                        f"[AgentC Sprint12] ✅ Query optimized: {len(optimization_result.optimizations_applied)} optimizations, "
                        f"estimated speedup: {optimization_result.estimated_speedup:.2f}x",
                        "AgentC"
                    )
                else:
                    logger.info(f"[AgentC Sprint12] No queries detected in code, skipping optimization", "AgentC")
                    
            except Exception as e:
                logger.error(f"[AgentC Sprint12] Query optimization failed: {e}", "AgentC")
        
        # Add performance metadata
        total_duration_ms = (time.time() - start_time) * 1000
        
        final_result["performance"] = {
            "cache_hit": cache_hit,
            "response_time_ms": round(total_duration_ms, 2),
            "optimization": optimization_metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache successful results
        if self.cache_manager and validation_result and validation_result.is_valid:
            try:
                # Cache for 1 hour (queries), 24 hours if schema-based
                ttl = 86400 if schema_context else 3600
                
                await self.cache_manager.set(cache_key, final_result, ttl=ttl)
                
                logger.info(
                    f"[AgentC Sprint12] ✅ Result cached: key={cache_key}, ttl={ttl}s",
                    "AgentC"
                )
                
                # Invalidate old cache if schema changed (Sprint 10 integration)
                if migration_scripts and migration_scripts.get('breaking'):
                    table_name = schema_context.get('table_name') if schema_context else None
                    if table_name:
                        await self.cache_manager.invalidate_table_cache(table_name, self.tenant_id)
                        logger.info(
                            f"[AgentC Sprint12] ✅ Breaking change detected, cache invalidated for table: {table_name}",
                            "AgentC"
                        )
            
            except Exception as e:
                logger.error(f"[AgentC Sprint12] Cache storage failed: {e}", "AgentC")
        
        # Build quality score string safely
        quality_str = 'N/A'
        if quality_report:
            quality_str = f"{quality_report['quality_score']}%"
        
        # Build schema version string safely
        version_str = 'N/A'
        if schema_version_info:
            version_str = f"v{schema_version_info['version_number']}"
        
        logger.info(
            f"[AgentC] Code generation complete: valid={validation_result.is_valid if validation_result else False}, "
            f"attempts={attempt}, tests={'generated' if test_code else 'none'}, "
            f"schema={'extracted' if schema_context else 'N/A'}, "
            f"params={'extracted' if parameters_context else 'N/A'}, "
            f"schema_version={version_str}, "
            f"migration={'generated' if migration_scripts else 'N/A'}, "
            f"quality={quality_str}, "
            f"anomalies={anomaly_report['anomalies_detected'] if anomaly_report else 'N/A'}, "
            f"cache={'HIT' if cache_hit else 'MISS'}, "
            f"response_time={total_duration_ms:.1f}ms, "
            f"optimizations={len(optimization_metadata['optimizations_applied']) if optimization_metadata else 0}",
            "AgentC"
        )
        
        # SPRINT 13: Persist generated data to utm_objects for visualization
        # ================================================================
        asset_id = node_data.get('asset_id') or node_data.get('object_id')
        logger.info(
            f"[AgentC Sprint13 DEBUG] Persistence check: asset_id={asset_id}, "
            f"valid={validation_result.is_valid if validation_result else False}, "
            f"code_len={len(generated_code) if generated_code else 0}",
            "AgentC"
        )
        
        if asset_id and validation_result and validation_result.is_valid and generated_code:
            try:
                persistence_updates = {
                    "generated_code": generated_code,  # Use the variable, not final_result
                    "tech_id": node_data.get('tech_id'),
                    "layer": node_data.get('layer'),
                    "object_name": node_data.get('source_name') or node_data.get('object_name') or node_data.get('name'),
                }
                
                # Add validation results (Sprint 8/11)
                if validation_result:
                    persistence_updates["validation_result"] = {
                        "is_valid": validation_result.is_valid,
                        "errors": validation_result.errors if hasattr(validation_result, 'errors') else [],
                        "warnings": validation_result.warnings if hasattr(validation_result, 'warnings') else []
                    }
                
                # Add optimization metadata (Sprint 12)
                if optimization_metadata:
                    persistence_updates["optimization_metadata"] = optimization_metadata
                
                # Add schema metadata (Sprint 9/10/13)
                # If schema_context has no columns, try to extract from generated code
                if schema_context and len(schema_context.get('columns', [])) == 0 and generated_code:
                    logger.info("[AgentC Sprint13] Schema empty, attempting to extract from generated code", "AgentC")
                    extracted_schema = self._extract_schema_from_code(generated_code, node_data.get('source_name', 'table'))
                    if extracted_schema and len(extracted_schema.get('columns', [])) > 0:
                        schema_context = extracted_schema
                        logger.info(f"[AgentC Sprint13] ✅ Extracted {len(extracted_schema['columns'])} columns from code", "AgentC")
                
                if schema_context:
                    persistence_updates["schema_metadata"] = schema_context
                    persistence_updates["row_count"] = schema_context.get('row_count', 0)
                    persistence_updates["column_count"] = len(schema_context.get('columns', []))
                
                # Add quality metrics (Sprint 11)
                if quality_report:
                    persistence_updates["quality_score"] = quality_report.get('quality_score')
                    persistence_updates["quality_violations"] = quality_report.get('violations', [])
                
                logger.info(
                    f"[AgentC Sprint13 DEBUG] Attempting persistence for asset {asset_id} with {len(persistence_updates)} fields",
                    "AgentC"
                )
                
                # Persist to database
                await db.update_asset_metadata(asset_id, persistence_updates)
                
                logger.info(
                    f"[AgentC Sprint13] ✅ Persisted visualization data for asset {asset_id}: "
                    f"code={len(generated_code)} chars, "
                    f"schema={schema_context is not None}, "
                    f"quality={quality_report is not None}",
                    "AgentC"
                )
                
            except Exception as e:
                logger.error(f"[AgentC Sprint13] Failed to persist visualization data: {e}", "AgentC")
        
        # Normalize output fields so downstream consumers always get a stable contract.
        # SQL Flavor Validation (v4.0 Contract Enforcement)
        if generated_code and target_engine:
            try:
                from apps.api.services.refinement.cartridges.tech_stack_contracts import validate_sql_flavor_coverage
            except ImportError:
                try:
                    from services.refinement.cartridges.tech_stack_contracts import validate_sql_flavor_coverage
                except ImportError:
                    from .refinement.cartridges.tech_stack_contracts import validate_sql_flavor_coverage
            
            flavor_result = validate_sql_flavor_coverage(
                tech_input=target_engine,
                generated_code=generated_code,
                layer=layer
            )
            
            if flavor_result.get('issues'):
                logger.warning(
                    f"[AgentC v4.0] SQL Flavor Validation: {', '.join(flavor_result['issues'])}",
                    "AgentC"
                )
            
            final_result["flavor_validation"] = {
                "flavor_expected": flavor_result.get("flavor_expected"),
                "is_compliant": flavor_result.get("valid", False),
                "issues": flavor_result.get("issues", [])
            }
        
        return self._normalize_generated_output_fields(final_result, target_engine)
    # ================================================================
    # SPRINT 8.5: ORIGIN ANALYSIS HELPER METHODS
    # ================================================================
    
    async def _extract_origin_analysis(self, medulla: Dict[str, Any], connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract origin system analysis from SSIS medulla"""
        origin = {
            "source_type": None,
            "server": None,
            "database": None,
            "connections": []
        }
        
        # Parse connections
        for conn in connections:
            conn_string = conn.get("connection_string", [""])[0] if isinstance(conn.get("connection_string"), list) else conn.get("connection_string", "")
            
            if conn_string:
                # Parse connection string to extract server and database
                parsed = self._parse_connection_string(conn_string)
                
                origin["connections"].append({
                    "name": conn.get("name"),
                    "id": conn.get("id"),
                    "type": parsed.get("type", "OLEDB"),
                    "server": parsed.get("server"),
                    "database": parsed.get("database")
                })
                
                # Set main origin info from first connection
                if not origin["source_type"]:
                    origin["source_type"] = f"SQL Server ({parsed.get('type', 'OLEDB')})"
                    origin["server"] = parsed.get("server")
                    origin["database"] = parsed.get("database")
        
        return origin
    
    def _parse_connection_string(self, conn_string: str) -> Dict[str, Any]:
        """Parse OLEDB/ODBC connection string to extract server and database"""
        import re
        
        parsed = {
            "type": "OLEDB",
            "server": None,
            "database": None
        }
        
        # Detect type
        if "ODBC" in conn_string.upper():
            parsed["type"] = "ODBC"
        
        # Extract Data Source / Server
        server_match = re.search(r'Data Source=([^;]+)', conn_string, re.IGNORECASE)
        if server_match:
            parsed["server"] = server_match.group(1).strip()
        else:
            server_match = re.search(r'Server=([^;]+)', conn_string, re.IGNORECASE)
            if server_match:
                parsed["server"] = server_match.group(1).strip()
        
        # Extract Initial Catalog / Database
        db_match = re.search(r'Initial Catalog=([^;]+)', conn_string, re.IGNORECASE)
        if db_match:
            parsed["database"] = db_match.group(1).strip()
        else:
            db_match = re.search(r'Database=([^;]+)', conn_string, re.IGNORECASE)
            if db_match:
                parsed["database"] = db_match.group(1).strip()
        
        return parsed
    
    async def _extract_transformations(self, medulla: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract list of transformations from SSIS medulla"""
        transformations = []
        
        data_flow = medulla.get("data_flow_logic", [])
        
        for comp in data_flow:
            comp_type = comp.get("type", "UNKNOWN")
            comp_name = comp.get("name", "")
            raw_props = comp.get("raw_properties", {})
            
            # Extract SQL query if present
            sql_query = None
            for prop_key in ["SqlCommand", "OpenRowset", "TableOrViewName", "SqlStatementSource"]:
                if prop_key in raw_props and raw_props[prop_key]:
                    sql_query = raw_props[prop_key][:500]  # Truncate to 500 chars
                    break
            
            transformations.append({
                "type": comp_type,
                "name": comp_name,
                "sql_query": sql_query,
                "complexity_factor": self._get_transformation_complexity_factor(comp_type)
            })
        
        return transformations
    
    def _get_transformation_complexity_factor(self, comp_type: str) -> int:
        """Return complexity factor (1-10) for a transformation type"""
        complexity_map = {
            "SOURCE_DB": 2,
            "DESTINATION_DB": 2,
            "LOOKUP": 5,
            "MERGE": 8,
            "DERIVED_COLUMN": 3,
            "AGGREGATE": 6,
            "CONDITIONAL": 4,
            "DATA_CONVERSION": 2,
            "SORT": 3,
            "UNION_ALL": 4,
            "MULTICAST": 3,
            "SCRIPT_COMPONENT": 9,
            "UNKNOWN": 1
        }
        
        return complexity_map.get(comp_type, 2)
    
    async def _extract_source_queries(self, medulla: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract source SQL queries from SSIS medulla"""
        queries = []
        
        data_flow = medulla.get("data_flow_logic", [])
        
        for comp in data_flow:
            comp_type = comp.get("type", "UNKNOWN")
            comp_name = comp.get("name", "")
            raw_props = comp.get("raw_properties", {})
            
            # Only extract queries from SOURCE and LOOKUP components
            if comp_type in ["SOURCE_DB", "LOOKUP"]:
                for prop_key in ["SqlCommand", "OpenRowset", "TableOrViewName", "SqlStatementSource"]:
                    if prop_key in raw_props and raw_props[prop_key]:
                        queries.append({
                            "component_type": comp_type,
                            "component_name": comp_name,
                            "query": raw_props[prop_key]
                        })
                        break
        
        return queries
    
    async def _calculate_complexity_score(self, transformations_list: List[Dict[str, Any]]) -> int:
        """Calculate complexity score (0-100) based on transformations"""
        if not transformations_list:
            return 0
        
        # Base score on number and type of transformations
        total_complexity = sum(t.get("complexity_factor", 1) for t in transformations_list)
        num_transformations = len(transformations_list)
        
        # Calculate score (capped at 100)
        # Formula: (total_complexity / num_transformations) * 10
        avg_complexity = total_complexity / num_transformations if num_transformations > 0 else 0
        score = min(int(avg_complexity * 10), 100)
        
        # Apply modifiers
        if num_transformations > 10:
            score = min(score + 20, 100)  # Bonus for many transformations
        
        return score
    
    async def _persist_origin_analysis(
        self,
        object_id: str,  # Changed from project_id + object_name
        origin_analysis: Dict[str, Any],
        transformations_list: List[Dict[str, Any]],
        source_queries: List[Dict[str, Any]],
        complexity_score: int,
        db: SupabasePersistence
    ):
        """Persist origin analysis to utm_objects Sprint 8 columns"""
        try:
            # Build update payload
            updates = {
                "source_connection": json.dumps(origin_analysis.get("connections", [])),
                "source_type": origin_analysis.get("source_type"),
                "source_query": source_queries[0].get("query") if source_queries else None,
                "transformations": json.dumps(transformations_list),
                "complexity_score": complexity_score,
                "data_flow_analysis": json.dumps({
                    "origin": origin_analysis,
                    "queries": source_queries,
                    "transformations_count": len(transformations_list)
                })
            }
            
            # Update utm_objects by object_id (more reliable than object_name which can be NULL)
            result = db.client.table("utm_objects") \
                .update(updates) \
                .eq("object_id", object_id) \
                .execute()
            
            logger.info(
                f"[AgentC Sprint8.5] ✅ Persisted origin analysis for object_id={object_id[:8]}: "
                f"connections={len(origin_analysis.get('connections', []))}, "
                f"transformations={len(transformations_list)}, "
                f"queries={len(source_queries)}, "
                f"complexity={complexity_score}",
                "AgentC"
            )
            
        except Exception as e:
            logger.error(f"[AgentC Sprint8.5] Failed to persist origin analysis: {e}", "AgentC")
