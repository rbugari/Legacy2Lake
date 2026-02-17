import os
import json
from datetime import datetime
from typing import Optional, Dict
from .profiler_service import ProfilerService
from .architect_service import ArchitectService
from .refactoring_service import RefactoringService
from .ops_auditor_service import OpsAuditorService

try:
    from apps.api.services.persistence_service import PersistenceService
except ImportError:
    try:
        from services.persistence_service import PersistenceService
    except ImportError:
        from ..persistence_service import PersistenceService

class RefinementOrchestrator:
    """
    Orchestrates Phase 3 (Medallion Transformation).
    Sequence: Profiler -> Architect -> Refactoring -> Ops -> Workflow
    """

    def __init__(self, project_name: str, project_uuid: str = None, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.project_name = project_name
        self.project_uuid = project_uuid or project_name
        self.tenant_id = tenant_id
        self.client_id = client_id
        
        # Services are instantiated once.
        # [Fix] Pass tenant_id AND client_id to sub-services for isolation
        self.profiler = ProfilerService(tenant_id=tenant_id, client_id=client_id)
        self.architect = ArchitectService(tenant_id=tenant_id, client_id=client_id)
        self.refactorer = RefactoringService(tenant_id=tenant_id, client_id=client_id)
        self.ops_auditor = OpsAuditorService(tenant_id=tenant_id, client_id=client_id)

    async def _resolve_agent_full_metadata(self, persistence, agent_id: str, default_name: str) -> str:
        """Resolves provider and model name for an agent. Returns default if DB lookup fails."""
        try:
            # If project_uuid is just a name like 'test10', resolve_agent_model might fail FK check
            # but we catch it here to allow pipeline to continue with R2 logic.
            model_info = await persistence.resolve_agent_model(agent_id)
            if model_info:
                provider = model_info.get("provider", "Unknown").capitalize()
                model = model_info.get("deployment") or model_info.get("model_id", "Unknown")
                return f"{default_name} (Provider: {provider}, Model: {model})"
        except Exception as e:
            # Silently fallback to default name to avoid blocking storage verification
            pass
        return f"{default_name} (Heuristic Engine)"

    async def run(self):
        """Standard entry point for the refinement pipeline."""
        # Use project_uuid for DB, but project_name for R2 Paths
        project_uuid = self.project_uuid
        project_name = self.project_name
        
        from apps.api.services.persistence_service import SupabasePersistence
        persistence = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        storage = PersistenceService.get_storage()
        
        # [Fix] R2 paths must use project_name for consistency with legacy folders
        base_path = PersistenceService.ensure_solution_dir(project_name, tenant_id=self.tenant_id)

        # Resolve models for agents dynamically
        p_info = await self._resolve_agent_full_metadata(persistence, "agent-p", "Pattern Discovery")
        a_info = await self._resolve_agent_full_metadata(persistence, "agent-a", "Medallion Mapper")
        r_info = await self._resolve_agent_full_metadata(persistence, "agent-r", "Spark Optimizer")
        o_info = await self._resolve_agent_full_metadata(persistence, "agent-o", "Compliance Auditor")

        # 0. Clear previous logs
        try:
            await persistence.clear_execution_logs(project_uuid, phase="REFINEMENT")
            log_key = f"{base_path.rstrip('/')}/refinement.log"
            storage.save_file(log_key, "--- REFINEMENT PIPELINE STARTED ---\n")
        except Exception as e:
            print(f"WARNING: Could not clear log storage/DB: {e}")

        models = {
            "Profiler": p_info,
            "Architect": a_info,
            "Refactoring": r_info,
            "OpsAuditor": o_info
        }
        
        # Store persistence, storage, and base_path for use in run_refinement
        self.persistence = persistence
        self.storage = storage
        self.base_path = base_path
        
        # Execute the refinement pipeline
        return await self.run_refinement(project_uuid, models)
        
    async def _check_cancellation(self, project_id: str):
        """Check if cancellation has been requested for this project."""
        try:
            return await self.persistence.check_cancellation(project_id)
        except: return False

    async def run_refinement(self, project_id: str, models: Dict[str, str]):
        """Executes the standard refinement pipeline."""
        timestamp_start = datetime.now().isoformat()
        
        # Reset cancellation flag for the new run
        try:
            await self.persistence.update_project_metadata(project_id, {"cancellation_requested": False})
        except: pass

        async def _log(msg: str, agent: str = "SYSTEM"):
            formatted_msg = f"[{datetime.now().strftime('%H:%M:%S')}] [{agent}] {msg}"
            
            # Log to database
            await self.persistence.log_execution(project_id, "REFINEMENT", msg, step=agent)
            
            # Also append to R2 log file for persistence
            try:
                log_key = f"{self.base_path.rstrip('/')}/refinement.log"
                existing = ""
                try:
                    existing = self.storage.read_file(log_key) or ""
                except: pass
                self.storage.save_file(log_key, existing + formatted_msg + "\n")
            except Exception as e:
                print(f"WARNING: Could not write log to R2: {e}")
            
            return formatted_msg
        
        local_log = [] 
        
        # 0. Header Block
        header = [
            "="*80,
            "REFINEMENT PIPELINE EXECUTION",
            "="*80,
            f"Date      : {timestamp_start}",
            f"Project   : {project_id}",
            f"Tenant    : {self.tenant_id}",
            f"Client    : {self.client_id}",
            "",
            "AGENT MATRIX CONFIGURATION:",
            f"- Profiler    : {models['Profiler']}",
            f"- Architect   : {models['Architect']}",
            f"- Refactoring : {models['Refactoring']}",
            f"- OpsAuditor  : {models['OpsAuditor']}",
            "="*80,
            ""
        ]
        for line in header: local_log.append(line)

        try:
            # Check for cancellation
            if await self._check_cancellation(project_id):
                msg = await _log("Refinement cancelled by user.", "SYSTEM")
                local_log.append(msg)
                return {"log": local_log, "status": "cancelled"}

            # 1. Profile (Agent P)
            local_log.append(f"--- [PHASE 1] PROFILER: {models['Profiler']} ---")
            print(f"[ORCHESTRATOR DEBUG] Starting Phase 1: PROFILER")
            msg = await _log("Starting analysis...", "Profiler")
            local_log.append(msg)
            
            profile_meta = await self.profiler.analyze_codebase(project_id, local_log, project_name=self.project_name)
            print(f"[ORCHESTRATOR DEBUG] Profiler complete. profile_meta keys: {profile_meta.keys() if profile_meta else 'None'}")
            print(f"[ORCHESTRATOR DEBUG] analyzed_files: {profile_meta.get('analyzed_files', []) if profile_meta else []}")
            
            # Check for cancellation
            if await self._check_cancellation(project_id):
                msg = await _log("Refinement cancelled by user.", "SYSTEM")
                local_log.append(msg)
                return {"log": local_log, "status": "cancelled"}

            msg = await _log(f"Complete. Analyzed {profile_meta.get('total_files', 0)} files.", "Profiler")
            local_log.append(msg)
            local_log.append("")
            
            # 2. Architect (Agent A)
            local_log.append(f"--- [PHASE 2] ARCHITECT: {models['Architect']} ---")
            print(f"[ORCHESTRATOR DEBUG] Starting Phase 2: ARCHITECT")
            print(f"[ORCHESTRATOR DEBUG] Calling architect.refine_project() with profile_meta")
            msg = await _log("Segmenting into Medallion Architecture (Bronze/Silver/Gold)...", "Architect")
            local_log.append(msg)
            architect_out = await self.architect.refine_project(project_id, profile_meta, local_log, project_name=self.project_name)
            print(f"[ORCHESTRATOR DEBUG] Architect complete. architect_out keys: {architect_out.keys() if architect_out else 'None'}")
            print(f"[ORCHESTRATOR DEBUG] refined_files: {architect_out.get('refined_files', {}) if architect_out else {}}")
            
            # Check for cancellation
            if await self._check_cancellation(project_id):
                msg = await _log("Refinement cancelled by user.", "SYSTEM")
                local_log.append(msg)
                return {"log": local_log, "status": "cancelled"}

            msg = await _log(f"Medallion structure created.", "Architect")
            local_log.append(msg)
            local_log.append("")
            
            # 3. Refactoring (Agent R)
            local_log.append(f"--- [PHASE 3] REFACTORING: {models['Refactoring']} ---")
            msg = await _log("Applying Spark Optimizations and Security Controls...", "Refactoring")
            local_log.append(msg)
            refactor_out = await self.refactorer.refactor_project(project_id, architect_out, local_log, project_name=self.project_name)
            
            # Check for cancellation
            if await self._check_cancellation(project_id):
                msg = await _log("Refinement cancelled by user.", "SYSTEM")
                local_log.append(msg)
                return {"log": local_log, "status": "cancelled"}
            
            msg = await _log(f"Optimized {refactor_out.get('optimized_files_count', 0)} files.", "Refactoring")
            local_log.append(msg)
            local_log.append("")
            
            # 4. Ops Auditor (Agent O)
            local_log.append(f"--- [PHASE 4] OPS AUDITOR: {models['OpsAuditor']} ---")
            msg = await _log("Validating operational readiness and generating DevOps assets...", "OpsAuditor")
            local_log.append(msg)
            ops_out = await self.ops_auditor.audit_project(project_id, architect_out, local_log, project_name=self.project_name)
            
            msg = await _log(f"Audit result: {ops_out['status']}", "OpsAuditor")
            local_log.append(msg)
            local_log.append("")
            
            local_log.append("="*80)
            msg = await _log("Pipeline Complete.", "Orchestrator")
            local_log.append(msg)
            local_log.append("="*80)

            return {
                "success": True,
                "status": "COMPLETED",
                "log": local_log,
                "artifacts": architect_out,
                "ops_audit": ops_out
            }

        except Exception as e:
            import traceback
            error_msg = f"Pipeline failed: {str(e)}\n{traceback.format_exc()}"
            local_log.append(error_msg)
            print(f"ERROR in run_refinement: {error_msg}")  # Print to Railway logs
            
            return {
                "success": False,
                "status": "FAILED",
                "log": local_log,
                "error": str(e)
            }
