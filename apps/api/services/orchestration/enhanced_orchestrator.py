"""
Enhanced Migration Orchestrator - Sprint 2
Integrates workflow state, context sharing, retry logic, and pipeline optimization
"""
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# Core agents
from services.librarian_service import LibrarianService
from services.topology_service import TopologyService
from services.agent_g_service import AgentGService

# Persistence
from services.persistence_service import PersistenceService, SupabasePersistence

# Sprint 2 Orchestration components
try:
    from services.orchestration.workflow_state_manager import WorkflowStateManager, WorkflowStatus, PackageStatus
    from services.orchestration.context_manager import SharedContext
    from services.orchestration.retry_manager import retry_manager
    from services.orchestration.pipeline_optimizer import PipelineOptimizer
except ImportError:
    from apps.api.services.orchestration.workflow_state_manager import WorkflowStateManager, WorkflowStatus, PackageStatus
    from apps.api.services.orchestration.context_manager import SharedContext
    from apps.api.services.orchestration.retry_manager import retry_manager
    from apps.api.services.orchestration.pipeline_optimizer import PipelineOptimizer

try:
    from apps.api.utils.logger import logger
except ImportError:
    try:
        from utils.logger import logger
    except ImportError:
        from ..utils.logger import logger


class EnhancedMigrationOrchestrator:
    """
    Enhanced orchestrator with Sprint 2 improvements:
    - Workflow state management (pause/resume)
    - Centralized context sharing
    - Intelligent retry logic
    - Optimized C → F pipeline
    """
    
    def __init__(
        self,
        project_id: str,
        project_uuid: str = None,
        tenant_id: str = None,
        client_id: str = None
    ):
        self.project_id = project_id
        self.project_uuid = project_uuid or project_id
        self.tenant_id = tenant_id
        self.client_id = client_id
        
        # Storage setup
        self.base_path = PersistenceService.ensure_solution_dir(project_id, tenant_id=tenant_id)
        self.output_path = f"{self.base_path.rstrip('/')}/{PersistenceService.STAGE_DRAFTING}"
        self.storage = PersistenceService.get_storage()
        self.persistence = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
        
        # Load platform spec
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.spec_path = os.path.join(base_dir, "config", "platform_spec.json")
        try:
            with open(self.spec_path, "r") as f:
                self.platform_spec = json.load(f)
        except FileNotFoundError:
            self.spec_path = os.path.abspath(os.path.join("apps", "api", "config", "platform_spec.json"))
            with open(self.spec_path, "r") as f:
                self.platform_spec = json.load(f)
        
        # Initialize core agents
        self.librarian = LibrarianService(project_id, tenant_id=tenant_id)
        self.topology = TopologyService(project_id, tenant_id=tenant_id)
        
        # Sprint 2 Components
        self.workflow_state = WorkflowStateManager(self.project_uuid, tenant_id=tenant_id)
        self.context_manager = SharedContext(self.project_uuid, tenant_id=tenant_id)
        self.pipeline = PipelineOptimizer(
            tenant_id=tenant_id,
            client_id=client_id,
            context_manager=self.context_manager
        )
        
        # Bitácora
        self.bitacora = []
        
        logger.info(f"✨ Enhanced Orchestrator initialized for {project_id}", "EnhancedOrchestrator")
    
    async def run_full_migration(
        self,
        limit: int = 0,
        resume: bool = False
    ) -> Dict[str, Any]:
        """
        Execute complete migration with enhanced orchestration.
        
        Args:
            limit: Maximum packages to process (0 = no limit)
            resume: Whether to resume from previous checkpoint
        """
        logger.info(f"🚀 Starting Enhanced Migration for {self.project_id}", "EnhancedOrchestrator")
        
        # Check if resuming
        resume_info = None
        if resume:
            can_resume = await self.workflow_state.can_resume()
            if can_resume:
                resume_info = await self.workflow_state.resume_workflow()
                logger.info(
                    f"▶️  Resuming from phase {resume_info['resume_from_phase']}, "
                    f"processed: {resume_info['processed_count']}",
                    "EnhancedOrchestrator"
                )
            else:
                logger.warning("Cannot resume workflow, starting fresh", "EnhancedOrchestrator")
                resume = False
        
        # Governance check
        status = await self.persistence.get_project_status(self.project_uuid)
        if status != "DRAFTING":
            logger.error(f"BLOCKED: Project status is '{status}'", "EnhancedOrchestrator")
            return {
                "project_id": self.project_id,
                "error": f"Project is in {status} mode. Must be DRAFTING.",
                "succeeded": [],
                "failed": []
            }
        
        # Phase 1: Librarian - Schema Context
        logger.info("📚 Phase 1: Librarian - Scanning schema...", "EnhancedOrchestrator")
        schema_ref = await self.librarian.scan_project()
        self.context_manager.set_schema_context(schema_ref)
        logger.info(f"Found {len(schema_ref['tables'])} tables", "Librarian")
        
        # Phase 2: Topology - Build Plan
        logger.info("🗺️  Phase 2: Topology - Building execution plan...", "EnhancedOrchestrator")
        topology_result = self.topology.build_orchestration_plan()
        orchestration = topology_result["orchestration"]
        package_metadatas = topology_result["package_metadatas"]
        
        self.context_manager.set_topology_context(orchestration)
        logger.info(
            f"Generated DAG with {len(orchestration['dag_execution'])} phases, "
            f"{len(package_metadatas)} packages",
            "Topology"
        )
        
        # Load and set intelligence context
        project_meta = await self.persistence.get_project_metadata(self.project_uuid)
        settings = project_meta.get("settings", {})
        config = project_meta.get("config", {})
        
        intelligence = {
            "support_intel": settings.get("support_intelligence", []),
            "scout_assessment": settings.get("scout_assessment", {})
        }
        self.context_manager.set_intelligence_context(intelligence)
        
        # Add package metadata to context manager
        for pm in package_metadatas:
            self.context_manager.add_package_metadata(pm["package_name"], pm)
        
        # Get technologies
        source_tech = settings.get("source_tech") or config.get("source_tech", "mssql")
        target_tech = settings.get("target_tech") or config.get("target_tech", "pyspark")
        
        # Initialize workflow state (or load if resuming)
        if not resume:
            total_packages = len(package_metadatas)
            await self.workflow_state.initialize_workflow(
                total_packages=total_packages,
                phases=orchestration["dag_execution"]
            )
        
        # Update workflow to RUNNING
        if self.workflow_state.state:
            self.workflow_state.state["status"] = WorkflowStatus.RUNNING
            await self.workflow_state._persist_state()
        
        # Phase 3: Execution Loop
        logger.info("⚙️  Phase 3: Executing code generation pipeline...", "EnhancedOrchestrator")
        
        results = {
            "project_id": self.project_id,
            "succeeded": [],
            "failed": []
        }
        
        # Determine starting point
        start_phase = resume_info["resume_from_phase"] if resume_info else 0
        
        for phase_idx, phase in enumerate(orchestration["dag_execution"]):
            # Skip phases if resuming
            if phase_idx < start_phase:
                logger.info(f"⏭️  Skipping phase {phase_idx}: {phase['phase']}", "EnhancedOrchestrator")
                continue
            
            # Check cancellation
            if await self._check_cancellation():
                await self.workflow_state.cancel_workflow()
                return self._build_result(results, cancelled=True)
            
            # Check limit
            if limit > 0 and len(results["succeeded"]) + len(results["failed"]) >= limit:
                logger.info(f"🛑 Limit reached: {limit} packages", "EnhancedOrchestrator")
                break
            
            logger.info(f"🔄 Phase {phase_idx + 1}/{len(orchestration['dag_execution'])}: {phase['phase']}", "EnhancedOrchestrator")
            await self.workflow_state.update_phase(phase_idx, phase["phase"])
            
            for pkg_name in phase["packages"]:
                # Check cancellation
                if await self._check_cancellation():
                    await self.workflow_state.cancel_workflow()
                    return self._build_result(results, cancelled=True)
                
                # Check limit
                if limit > 0 and len(results["succeeded"]) + len(results["failed"]) >= limit:
                    break
                
                logger.info(f"📦 Processing: {pkg_name}", "EnhancedOrchestrator")
                await self.workflow_state.start_package(pkg_name, phase["phase"])
                
                # Build task definition
                pm = self.context_manager.get_package_metadata(pkg_name)
                if not pm:
                    logger.warning(f"No metadata for {pkg_name}, skipping", "EnhancedOrchestrator")
                    await self.workflow_state.update_package_status(
                        pkg_name,
                        PackageStatus.SKIPPED,
                        error="No metadata found"
                    )
                    continue
                
                task_def = {
                    "project_id": self.project_uuid,
                    "package_name": pkg_name,
                    "name": pkg_name,
                    "type": "SSIS Package",
                    "description": f"Transpilation of {pkg_name}",
                    "source_tech": source_tech,
                    "target_tech": target_tech,
                    "tech_id": target_tech,
                    **pm  # Merge package metadata
                }
                
                # Execute pipeline (C → F with retry and optimization)
                success, pipeline_result = await self.pipeline.execute_pipeline(
                    package_name=pkg_name,
                    task_definition=task_def,
                    project_uuid=self.project_uuid
                )
                
                if success:
                    # Save artifacts
                    final_code = pipeline_result["final_code"]
                    clean_name = pkg_name.replace(".dtsx", "")
                    
                    self._save_artifact(f"{clean_name}.py", final_code)
                    self._save_artifact(
                        f"{clean_name}_audit.json",
                        json.dumps(pipeline_result["agent_f_result"], indent=2)
                    )
                    
                    results["succeeded"].append(pkg_name)
                    await self.workflow_state.update_package_status(
                        pkg_name,
                        PackageStatus.COMPLETED
                    )
                    
                    logger.info(
                        f"✅ {pkg_name}: {pipeline_result['status']} "
                        f"(Score: {pipeline_result['score']})",
                        "EnhancedOrchestrator"
                    )
                else:
                    # Failed
                    error_msg = pipeline_result.get("error", "Unknown error")
                    results["failed"].append({
                        "package": pkg_name,
                        "error": error_msg,
                        "phase_failed": pipeline_result.get("phase_failed")
                    })
                    await self.workflow_state.update_package_status(
                        pkg_name,
                        PackageStatus.FAILED,
                        error=error_msg
                    )
                    
                    logger.error(f"❌ {pkg_name}: {error_msg}", "EnhancedOrchestrator")
        
        # Phase 4: Governance (if any succeeded)
        if results["succeeded"]:
            logger.info("📋 Phase 4: Generating governance documentation...", "EnhancedOrchestrator")
            await self._generate_governance(results, orchestration, package_metadatas, target_tech)
        
        # Complete workflow
        await self.workflow_state.complete_workflow(success=len(results["succeeded"]) > 0)
        
        # Log statistics
        self._log_statistics()
        
        return self._build_result(results)
    
    async def _check_cancellation(self) -> bool:
        """Check if cancellation requested"""
        try:
            cancelled = await self.persistence.check_cancellation(self.project_uuid)
            if cancelled:
                logger.info("🛑 Cancellation requested", "EnhancedOrchestrator")
            return cancelled
        except Exception as e:
            logger.error(f"Error checking cancellation: {e}", "EnhancedOrchestrator")
            return False
    
    async def _generate_governance(
        self,
        results: Dict[str, List],
        orchestration: Dict[str, Any],
        package_metadatas: List[Dict[str, Any]],
        target_tech: str
    ):
        """Generate governance documentation with Agent G"""
        try:
            agent_g = AgentGService(tenant_id=self.tenant_id, client_id=self.client_id)
            
            mesh = {
                "nodes": package_metadatas,
                "edges": [],
                "phases": orchestration.get("dag_execution", [])
            }
            
            # Sample transformations
            sample_transformations = []
            for pkg_name in results["succeeded"][:3]:
                clean_name = pkg_name.replace(".dtsx", "")
                code_key = f"{self.output_path.rstrip('/')}/{clean_name}.py"
                audit_key = f"{self.output_path.rstrip('/')}/{clean_name}_audit.json"
                
                try:
                    code_content = self.storage.read_file(code_key)
                    audit_content = self.storage.read_file(audit_key)
                    sample_transformations.append({
                        "name": pkg_name,
                        "code": code_content,
                        "audit": json.loads(audit_content) if audit_content else {}
                    })
                except Exception as e:
                    logger.warning(f"Could not load sample for {pkg_name}: {e}", "Governance")
            
            governance_result = await agent_g.generate_governance(
                project_name=self.project_id,
                mesh=mesh,
                transformations=sample_transformations,
                metadata={
                    "total_packages": len(results["succeeded"]) + len(results["failed"]),
                    "succeeded": len(results["succeeded"]),
                    "failed": len(results["failed"]),
                    "target_platform": target_tech
                }
            )
            
            if governance_result.get("runbook"):
                self._save_artifact("governance_runbook.md", governance_result["runbook"])
            
            if governance_result.get("certification"):
                self._save_artifact(
                    "certification_audit.json",
                    json.dumps(governance_result["certification"], indent=2)
                )
            
            logger.info("✅ Governance documentation generated", "Governance")
        except Exception as e:
            logger.error(f"Agent G failed: {e}", "Governance")
    
    def _save_artifact(self, filename: str, content: str):
        """Save artifact to storage"""
        artifact_key = f"{self.output_path.rstrip('/')}/{filename}"
        self.storage.save_file(artifact_key, content)
    
    def _log_statistics(self):
        """Log orchestration statistics"""
        workflow_progress = self.workflow_state.get_progress()
        context_stats = self.context_manager.get_stats()
        retry_stats = retry_manager.get_stats()
        pipeline_metrics = self.pipeline.get_metrics()
        
        logger.info("="*80, "Statistics")
        logger.info("📊 ORCHESTRATION STATISTICS", "Statistics")
        logger.info("="*80, "Statistics")
        
        logger.info(f"Workflow: {workflow_progress['status']} - {workflow_progress['progress']:.1f}%", "Statistics")
        logger.info(
            f"Progress: {workflow_progress['processed']}/{workflow_progress['total']} packages "
            f"({workflow_progress['succeeded']} succeeded, {workflow_progress['failed']} failed)",
            "Statistics"
        )
        
        logger.info(f"\n{self.context_manager.summary()}", "Statistics")
        logger.info(f"{retry_manager.get_summary()}", "Statistics")
        logger.info(f"{self.pipeline.get_summary()}", "Statistics")
        
        logger.info("="*80, "Statistics")
    
    def _build_result(self, results: Dict[str, List], cancelled: bool = False) -> Dict[str, Any]:
        """Build final result dictionary"""
        result = {
            "project_id": self.project_id,
            "project_uuid": self.project_uuid,
            "succeeded": results["succeeded"],
            "failed": results["failed"],
            "total": len(results["succeeded"]) + len(results["failed"]),
            "success_rate": (
                len(results["succeeded"]) / (len(results["succeeded"]) + len(results["failed"]))
                if (len(results["succeeded"]) + len(results["failed"])) > 0
                else 0
            )
        }
        
        if cancelled:
            result["cancelled"] = True
            result["status"] = "CANCELLED"
        else:
            result["status"] = "COMPLETED"
        
        # Add statistics
        result["statistics"] = {
            "workflow": self.workflow_state.get_progress(),
            "context": self.context_manager.get_stats(),
            "retry": retry_manager.get_stats(),
            "pipeline": self.pipeline.get_metrics()
        }
        
        return result
