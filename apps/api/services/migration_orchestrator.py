import os
import json
import asyncio
from typing import Dict, Any, List

# Import all agents
from services.librarian_service import LibrarianService
from services.topology_service import TopologyService
from services.agent_c_service import AgentCService
from services.agent_f_service import AgentFService

from services.persistence_service import PersistenceService, SupabasePersistence
try:
    from apps.api.utils.logger import logger
except ImportError:
    try:
        from utils.logger import logger
    except ImportError:
        from ..utils.logger import logger

class MigrationOrchestrator:
    """
    The Director: Manages the end-to-end migration lifecycle.
    Orchestrates the hand-offs between Librarian, Topology, Developer, and Compliance agents.
    """

    def __init__(self, project_id: str, project_uuid: str = None, tenant_id: str = None, client_id: str = None):

        self.project_id = project_id # This acts as Project Name / Folder Name
        self.project_uuid = project_uuid or project_id # Fallback if not provided, though DB will fail if not UUID
        
        # Persistence Service should handle paths ideally, but keeping this for now
        # resolving absolute paths robustly
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # apps/api/services -> apps/api
        self.base_path = PersistenceService.ensure_solution_dir(project_id, tenant_id=tenant_id)
        self.output_path = os.path.join(self.base_path, PersistenceService.STAGE_DRAFTING)
        
        # Load Platform Spec (Robust Path)
        self.spec_path = os.path.join(base_dir, "config", "platform_spec.json")
        try:
            with open(self.spec_path, "r") as f:
                self.platform_spec = json.load(f)
        except FileNotFoundError:
            # Fallback if base_dir calculation is off, try relative to CWD
            self.spec_path = os.path.abspath(os.path.join("apps", "api", "config", "platform_spec.json"))
            with open(self.spec_path, "r") as f:
                self.platform_spec = json.load(f)

        # Initialize Agents
        self.librarian = LibrarianService(project_id, tenant_id=tenant_id)
        self.topology = TopologyService(project_id, tenant_id=tenant_id)
        self.agent_c = AgentCService(tenant_id=tenant_id, client_id=client_id)
        self.agent_f = AgentFService(tenant_id=tenant_id, client_id=client_id)
        self.persistence = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)

        
        # Log Persistence
        self.log_file = os.path.join(self.base_path, "migration.log")

    async def _log_persistence(self, message: str, step: str = "SYSTEM"):
        """Persists a message to the database log and file."""
        # Use UUID for DB logging if possible
        target_id = self.project_uuid if len(str(self.project_uuid)) > 30 else self.project_id
        await self.persistence.log_execution(target_id, "MIGRATION", message, step=step)
        
        # File Persistence with Standard Format
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{now}] [{step.upper()}] {message}"
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"{formatted_msg}\n")
        except:
            pass

    async def run_full_migration(self, limit: int = 0):
        """Executes the complete Shift-T loop."""
        print(f"DEBUG: Starting run_full_migration for {self.project_id}")
        
        # 0. Clear previous logs (File & DB)
        try:
            # Clear Database Logs for MIGRATION phase
            await self.persistence.clear_execution_logs(self.project_uuid or self.project_id, phase="MIGRATION")
            
            # Clear File Logs
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write(f"--- Migration Started for {self.project_id} ---\n")
                f.write(f"Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception as e:
            print(f"WARNING: Could not clear log file/DB: {e}")
            # We continue anyway, but the warning will be in the server console

        await self._log_persistence(f"Starting Migration for {self.project_id}")
        logger.info(f"Starting Migration for {self.project_id}", "Orchestrator")
        
        # 1. Governance Check
        # Use UUID for status check
        status = await self.persistence.get_project_status(self.project_uuid)
        if status != "DRAFTING":
            logger.error(f"BLOCKED: Project status is '{status}'. Must be 'DRAFTING'.", "Orchestrator")
            await self._log_persistence(f"BLOCKED: Project status is '{status}'. Must be 'DRAFTING'.")
            return {
                "project_id": self.project_id,
                "error": f"Project is in {status} mode. Approve Triage first.",
                "succeeded": [],
                "failed": []
            }

        # 1. THE LIBRARIAN (Context)
        logger.info("Step 1: Librarian - Scanning Schema Context...", "Orchestrator")
        await self._log_persistence("Step 1: Librarian - Scanning Schema Context...")
        schema_ref = self.librarian.scan_project()
        logger.info(f"Found {len(schema_ref['tables'])} tables.", "Librarian")
        await self._log_persistence(f"Librarian: Found {len(schema_ref['tables'])} tables.")
        logger.debug("Schema Reference", "Librarian", schema_ref)

        # 2. THE TOPOLOGY ARCHITECT (Plan)
        logger.info("Step 2: Topology - Building Orchestration Plan...", "Orchestrator")
        await self._log_persistence("Step 2: Topology - Building Orchestration Plan...")
        topology_result = self.topology.build_orchestration_plan()
        orchestration = topology_result["orchestration"]
        package_metadatas = topology_result["package_metadatas"]
        
        logger.info(f"Generated DAG with {len(orchestration['dag_execution'])} phases.", "Topology")
        await self._log_persistence(f"Topology: Generated DAG with {len(orchestration['dag_execution'])} phases.")
        logger.debug("Orchestration Plan", "Topology", orchestration)

        # 3. EXECUTION LOOP (Developer + Compliance)
        logger.info("Step 3: Execution - Generating & Auditing Code...", "Orchestrator")
        await self._log_persistence("Step 3: Execution - Generating & Auditing Code...")
        
        # Pre-fetch and cache DB assets for enrichment
        db_assets = await self.persistence.get_project_assets(self.project_uuid)
        
        results = {
            "project_id": self.project_id,
            "succeeded": [],
            "failed": []
        }

        # Create metadata lookup map
        metadata_map = { pm["package_name"]: pm for pm in package_metadatas }

        for phase in orchestration["dag_execution"]:
            if limit > 0 and len(results["succeeded"]) + len(results["failed"]) >= limit:
                break

            logger.info(f"Entering Phase: {phase['phase']}", "Orchestrator")
            await self._log_persistence(f"Entering Phase: {phase['phase']}")
            
            # Resolve models once per phase for logging clarity
            config_c = await self.persistence.resolve_llm_for_agent("agent-c", self.project_uuid)
            config_f = await self.persistence.resolve_llm_for_agent("agent-f", self.project_uuid)
            model_c = config_c.get("model_name", "Unknown")
            model_f = config_f.get("model_name", "Unknown")
            for pkg_name in phase["packages"]:
                if limit > 0 and len(results["succeeded"]) + len(results["failed"]) >= limit:
                    break
                
                logger.info(f"Processing: {pkg_name}", "Orchestrator")
                await self._log_persistence(f"Processing: {pkg_name}...")
                
                # A. Prepare Task Context
                pm = metadata_map.get(pkg_name, {})
                
                # Enrich with DB Metadata if available
                asset_meta = next((a for a in db_assets if a.get("source_name") == pkg_name), {})
                
                task_def = {
                    "project_id": self.project_uuid,
                    "package_name": pkg_name,
                    "name": pkg_name, # Compatibility with Agent C expecting 'name'
                    "type": "SSIS Package",
                    "description": f"Transpilation of {pkg_name}",
                    "inputs": pm.get("inputs", []),
                    "outputs": pm.get("outputs", []),
                    "lookups": pm.get("lookups", []),
                    # Pass through user-configured metadata from DB
                    "frequency": asset_meta.get("frequency"),
                    "load_strategy": asset_meta.get("load_strategy"),
                    "is_pii": asset_meta.get("is_pii"),
                    "masking_rule": asset_meta.get("masking_rule"),
                    "business_entity": asset_meta.get("business_entity"),
                    "target_name": asset_meta.get("target_name"),
                    "metadata": asset_meta.get("metadata", {}) # Extracted XML metadata
                }
                
                # B. AGENT-C: DEVELOPER (Write)
                provider_c = config_c.get("provider", "UNKNOWN").upper()
                await self._log_persistence(f"Initiating Agent C (Developer) via {provider_c} using model {model_c}", step="Developer")
                
                # Set-based Operations: Provide context of other packages
                set_context = package_metadatas if len(package_metadatas) < 50 else [] # Limit size for tokens
                code_result = await self.agent_c.transpile_task(task_def, set_context=set_context)
                
                notebook_content = code_result.get("pyspark_code", "")
                sql_content = code_result.get("sql_code", "")
                
                if not notebook_content and not sql_content:
                    reason = code_result.get("error") or code_result.get("reason", "Empty code response")
                    logger.error(f"Agent-C failed to generate code for {pkg_name}: {reason}", "Orchestrator")
                    await self._log_persistence(f"Agent-C: Failed to generate code for {pkg_name} - Reason: {reason}", step="Developer")
                    results["failed"].append({"package": pkg_name, "reason": reason})
                    continue

                # C. AGENT-F: COMPLIANCE (Audit)
                provider_f = config_f.get("provider", "UNKNOWN").upper()
                await self._log_persistence(f"Initiating Agent F (Compliance) via {provider_f} using model {model_f}", step="Compliance")
                
                audit_report = await self.agent_f.review_code(task_def, notebook_content, project_id=self.project_uuid)
                
                status = audit_report.get("status", "UNKNOWN")
                logger.info(f"Audit Status: {status} (Score: {audit_report.get('score', 0)})", "Compliance")
                
                # Save Artifacts
                clean_name = pkg_name.replace(".dtsx", "")
                if notebook_content:
                    self._save_artifact(f"{clean_name}.py", notebook_content)
                if sql_content:
                    self._save_artifact(f"{clean_name}.sql", sql_content)
                
                self._save_artifact(f"{clean_name}_audit.json", json.dumps(audit_report, indent=2))
                
                if status in ["APPROVED", "IMPROVED"]:
                    results["succeeded"].append(pkg_name)
                    display_status = "APPROVED" if status == "APPROVED" else "IMPROVED (Optimized)"
                    await self._log_persistence(f"Compliance: {display_status} {pkg_name} (Score: {audit_report.get('score')})")
                    
                    # If improved, we might want to use the optimized code
                    if status == "IMPROVED" and audit_report.get("optimized_code"):
                         notebook_content = audit_report.get("optimized_code")
                         # Re-save with optimized content
                         self._save_artifact(f"{clean_name}.py", notebook_content)
                else:
                    await self._log_persistence(f"Compliance: REJECTED {pkg_name} (Score: {audit_report.get('score')})")
                    results["failed"].append({
                        "package": pkg_name, 
                        "reason": audit_report.get("critique", "Audit Rejected"), 
                        "violations": audit_report.get("violations")
                    })

        if limit > 0 and len(results["succeeded"]) + len(results["failed"]) >= limit:
            logger.warning(f"Limit Reached: Stopping after {limit} packages.", "Orchestrator")
            await self._log_persistence(f"Limit Reached: Stopping after {limit} packages.")

        logger.info(f"Migration Complete. Succeeded: {len(results['succeeded'])}, Failed: {len(results['failed'])}", "Orchestrator")
        await self._log_persistence("Migration Complete.")
        return results

    def _save_artifact(self, filename: str, content: str):
        path = os.path.join(self.output_path, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
