
import os
import json
from typing import Optional
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
        # They handle project path resolution internally/per request if needed, 
        # or we pass project_id to their methods.
        self.profiler = ProfilerService()
        self.architect = ArchitectService()
        self.refactorer = RefactoringService()
        self.ops_auditor = OpsAuditorService()

    async def start_pipeline(self, project_id: str):
        # Release 3.5: DB Persistence
        # db = PersistenceService.get_persistence() 
        # Note: PersistenceService doesn't have get_persistence factory, it has SupabasePersistence class.
        # Let's import SupabasePersistence.
        
        from apps.api.services.persistence_service import SupabasePersistence
        persistence = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)

        
        async def _log(msg: str, step: str = None):
             await persistence.log_execution(project_id, "REFINEMENT", msg, step=step)
        
        try:
            # 1. Profile (Agent P)
            await _log("Starting analysis...", "Profiler")
            
            # Note: ProfilerService.analyze_codebase currently expects a list to append to.
            # We need to either update ProfilerService OR mock a list wrapper.
            # For now, let's keep the list for backward compat with inner services, 
            # BUT also log high-level events to DB.
            # Ideally, we refactor ProfilerService to take a callback, but that's a larger change.
            # Let's pass a list and log the result summary to DB.
            
            local_log = [] 
            profile_meta = self.profiler.analyze_codebase(project_id, local_log)
            # Flush local log to DB? Too spammy? 
            # Let's log just the high level for now, as user wants "real time" but maybe not granularity of every file if it's too much.
            # Actually, user wants to see what's happening.
            # Let's assume inner services log to the list we pass.
            
            await _log(f"Complete. Analyzed {profile_meta['total_files']} files.", "Profiler")
            
            # 2. Architect (Agent A)
            await _log("Segmenting into Medallion Architecture (Bronze/Silver/Gold)...", "Architect")
            architect_out = await self.architect.refine_project(project_id, profile_meta, local_log)
            await _log(f"Medallion structure created.", "Architect")
            
            # 3. Refactoring (Agent R)
            await _log("Applying Spark Optimizations and Security Controls...", "Refactoring")
            refactor_out = await self.refactorer.refactor_project(project_id, architect_out, local_log)
            await _log(f"Optimized {refactor_out.get('optimized_files_count', 0)} files.", "Refactoring")
            
            # 4. Ops Auditor (Agent O)
            await _log("Validating operational readiness and generating DevOps assets...", "OpsAuditor")
            ops_out = self.ops_auditor.audit_project(project_id, architect_out, local_log)
            await _log(f"Audit result: {ops_out['status']}", "OpsAuditor")
            
            await _log("Pipeline Complete.", "Orchestrator")
            local_log.append("Pipeline Complete.")

            # [Deprecated] File Persistence removed in favor of DB
            # But we might want to keep writing the detailed local_log to a file for deeper debug
            # if the inner services aren't converted yet.
            # Let's keep file writing for granular logs until inner services are refactored.
            project_path = PersistenceService.ensure_solution_dir(project_id)
            with open(os.path.join(project_path, "refinement.log"), "w", encoding="utf-8") as f:
                f.write("\n".join(local_log))

            return {
                "status": "COMPLETED",
                "log": local_log, # Return full detailed log for UI immediate response if needed
                "artifacts": architect_out,
                "ops_audit": ops_out
            }


            
        except Exception as e:
            import traceback
            error_msg = f"Pipeline failed: {str(e)}\n{traceback.format_exc()}"
            local_log.append(error_msg)
            
            # Try to save error log too
            try:
                project_path = PersistenceService.ensure_solution_dir(project_id)
                with open(os.path.join(project_path, "refinement.log"), "w", encoding="utf-8") as f:
                    f.write("\n".join(local_log))
            except: 
                pass

            return {
                "status": "FAILED",
                "log": local_log,
                "error": str(e)
            }
