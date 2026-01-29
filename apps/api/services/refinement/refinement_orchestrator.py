import os
import json
import datetime
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
        # [Fix] Pass tenant_id to sub-services for isolation
        self.profiler = ProfilerService(tenant_id=tenant_id)
        self.architect = ArchitectService(tenant_id=tenant_id)
        self.refactorer = RefactoringService(tenant_id=tenant_id)
        self.ops_auditor = OpsAuditorService(tenant_id=tenant_id)

    async def _resolve_agent_full_metadata(self, persistence, agent_id: str, default_name: str) -> str:
        """Resolves provider and model name for an agent."""
        try:
            model_info = await persistence.resolve_agent_model(agent_id)
            if model_info:
                provider = model_info.get("provider", "Unknown").capitalize()
                model = model_info.get("deployment") or model_info.get("model_id", "Unknown")
                return f"{default_name} (Provider: {provider}, Model: {model})"
        except:
            pass
        return f"{default_name} (Heuristic Engine)"

    async def start_pipeline(self, project_id: str):
        from apps.api.services.persistence_service import SupabasePersistence
        persistence = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)

        # Resolve models for agents dynamically
        p_info = await self._resolve_agent_full_metadata(persistence, "agent-p", "Pattern Discovery")
        a_info = await self._resolve_agent_full_metadata(persistence, "agent-a", "Medallion Mapper")
        r_info = await self._resolve_agent_full_metadata(persistence, "agent-r", "Spark Optimizer")
        o_info = await self._resolve_agent_full_metadata(persistence, "agent-o", "Compliance Auditor")

        models = {
            "Profiler": p_info,
            "Architect": a_info,
            "Refactoring": r_info,
            "OpsAuditor": o_info
        }
        
        timestamp_start = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        async def _log(msg: str, step: str = None):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # For the per-line log, we might want a shorter version or the same
            model_label = models.get(step, "System")
            # If model_label is long (like with provider), maybe just use the agent name or truncate
            # But the user asked for it, so let's use it.
            formatted_msg = f"[{timestamp}] [{step or 'SYSTEM'}] [{model_label}] {msg}"
            await persistence.log_execution(project_id, "REFINEMENT", msg, step=step)
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
        local_log.extend(header)

        try:
            # 1. Profile (Agent P)
            local_log.append(f"--- [PHASE 1] PROFILER: {models['Profiler']} ---")
            msg = await _log("Starting analysis...", "Profiler")
            local_log.append(msg)
            
            profile_meta = self.profiler.analyze_codebase(project_id, local_log)
            
            msg = await _log(f"Complete. Analyzed {profile_meta.get('total_files', 0)} files.", "Profiler")
            local_log.append(msg)
            local_log.append("")
            
            # 2. Architect (Agent A)
            local_log.append(f"--- [PHASE 2] ARCHITECT: {models['Architect']} ---")
            msg = await _log("Segmenting into Medallion Architecture (Bronze/Silver/Gold)...", "Architect")
            local_log.append(msg)
            architect_out = await self.architect.refine_project(project_id, profile_meta, local_log)
            
            msg = await _log(f"Medallion structure created.", "Architect")
            local_log.append(msg)
            local_log.append("")
            
            # 3. Refactoring (Agent R)
            local_log.append(f"--- [PHASE 3] REFACTORING: {models['Refactoring']} ---")
            msg = await _log("Applying Spark Optimizations and Security Controls...", "Refactoring")
            local_log.append(msg)
            refactor_out = await self.refactorer.refactor_project(project_id, architect_out, local_log)
            
            msg = await _log(f"Optimized {refactor_out.get('optimized_files_count', 0)} files.", "Refactoring")
            local_log.append(msg)
            local_log.append("")
            
            # 4. Ops Auditor (Agent O)
            local_log.append(f"--- [PHASE 4] OPS AUDITOR: {models['OpsAuditor']} ---")
            msg = await _log("Validating operational readiness and generating DevOps assets...", "OpsAuditor")
            local_log.append(msg)
            ops_out = self.ops_auditor.audit_project(project_id, architect_out, local_log)
            
            msg = await _log(f"Audit result: {ops_out['status']}", "OpsAuditor")
            local_log.append(msg)
            local_log.append("")
            
            local_log.append("="*80)
            msg = await _log("Pipeline Complete.", "Orchestrator")
            local_log.append(msg)
            local_log.append("="*80)

            project_path = PersistenceService.ensure_solution_dir(project_id, tenant_id=self.tenant_id)
            with open(os.path.join(project_path, "refinement.log"), "w", encoding="utf-8") as f:
                f.write("\n".join(local_log))

            return {
                "status": "COMPLETED",
                "log": local_log,
                "artifacts": architect_out,
                "ops_audit": ops_out
            }


            
        except Exception as e:
            import traceback
            error_msg = f"Pipeline failed: {str(e)}\n{traceback.format_exc()}"
            local_log.append(error_msg)
            
            # Try to save error log too
            try:
                project_path = PersistenceService.ensure_solution_dir(project_id, tenant_id=self.tenant_id)
                with open(os.path.join(project_path, "refinement.log"), "w", encoding="utf-8") as f:
                    f.write("\n".join(local_log))
            except: 
                pass

            return {
                "status": "FAILED",
                "log": local_log,
                "error": str(e)
            }
