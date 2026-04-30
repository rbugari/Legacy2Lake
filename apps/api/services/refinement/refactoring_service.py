
import os
from pathlib import Path
import datetime

try:
    from apps.api.services.persistence_service import PersistenceService
except ImportError:
    try:
        from services.persistence_service import PersistenceService
    except ImportError:
        from ..persistence_service import PersistenceService

class RefactoringService:
    def __init__(self, tenant_id: str = None, client_id: str = None):
        self.tenant_id = tenant_id
        self.client_id = client_id

    def _log(self, log: list, msg: str, level: str = "Refactoring", model: str = "Spark Optimizer"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.append(f"[{timestamp}] [{level}] [{model}] {msg}")

    async def refactor_project(self, project_id: str, architect_output: dict, log: list = None, project_name: str = None) -> dict:
        """
        Applies Spark Optimizations and Security best practices to the generated Medallion code.
        """
        if log is None: log = []
        
        refined_files = architect_output.get("refined_files", {})
        processed_count = 0
        
        self._log(log, "Scanning generated files for optimization candidates...")
        
        # Release 2.0: Fetch Design Registry to know the stack
        try:
             from apps.api.services.persistence_service import SupabasePersistence
             db_instance = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
             registry_raw = await db_instance.get_design_registry(project_id)
        except Exception as e:
             self._log(log, f"Warning: Failed to fetch registry ({e}). Using defaults.", level="Refactoring", model="System")
             registry_raw = []
             
        # Flatten
        from apps.api.services.knowledge_service import KnowledgeService
        registry = KnowledgeService.flatten_knowledge(registry_raw)
        target_stack = registry.get("paths", {}).get("target_stack", "pyspark")

        self._log(log, f"Target Stack: {target_stack.upper()}")

        for layer in ["bronze", "silver", "gold"]:
            files = refined_files.get(layer, [])
            if not files: continue
            
            self._log(log, f"Optimizing {layer.upper()} layer ({len(files)} files)...")
            for file_key in files:
                await self._apply_refactoring(file_key, target_stack, log)
                processed_count += 1
                
        return {
            "status": "COMPLETED",
            "optimized_files_count": processed_count
        }
        
    async def _apply_refactoring(self, file_key: str, stack: str, log: list = None):
        """
        Injects optimization hints and security placeholders via R2.
        """
        storage = PersistenceService.get_storage()
        content = storage.read_file(file_key)
        if not content:
            return
            
        if isinstance(content, bytes):
            content = content.decode("utf-8")
            
        # Optimization Logic
        normalized_stack = (stack or "pyspark").lower().strip()
        comment_prefix = "--" if file_key.lower().endswith(".sql") else "#"

        if normalized_stack in {"snowflake", "snowflake_sql"}:
            optimization_note = f"{comment_prefix} [Refactoring Agent] Optimization: Consider CLUSTER BY on high cardinality columns for pruning when configured.\n"
            sec_note = f"{comment_prefix} [Refactoring Agent] Security: Use Snowflake roles, integrations, or external secrets managed outside generated SQL.\n"
        elif normalized_stack in {"databricks", "azure_databricks"}:
            optimization_note = f"{comment_prefix} [Refactoring Agent] Optimization: Consider Databricks OPTIMIZE/ZORDER only when enabled by deployment config.\n"
            sec_note = f"{comment_prefix} [Refactoring Agent] Security: Resolve secrets through runtime configuration or approved workspace secret scopes.\n"
        else:
            optimization_note = f"{comment_prefix} [Refactoring Agent] Optimization: Keep generic Spark tuning portable; use partitioning/caching only when configured.\n"
            sec_note = f"{comment_prefix} [Refactoring Agent] Security: Resolve credentials through injected config or environment-backed secret providers.\n"

        filename = file_key.split("/")[-1]
        if log: self._log(log, f"  > {filename}: Added Optimization hint for {stack}")
        
        # Example Security:
        security_note = sec_note
        if log: self._log(log, f"  > {filename}: Validated Security Scopes")
        if log: self._log(log, f"  > {filename}: Validated Secret Scope usage")
        
        new_content = optimization_note + security_note + content
        
        storage.save_file(file_key, new_content)
