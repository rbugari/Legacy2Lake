"""
Workflow State Manager - Sprint 2 Enhancement
Manages workflow state persistence, checkpoints, and resume capability
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

try:
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.utils.logger import logger
except ImportError:
    from services.persistence_service import SupabasePersistence
    from utils.logger import logger


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PackageStatus(str, Enum):
    """Individual package processing status"""
    PENDING = "PENDING"
    GENERATING = "GENERATING"  # Agent C
    AUDITING = "AUDITING"      # Agent F
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class WorkflowStateManager:
    """
    Manages workflow state with checkpoints and resume capability.
    Enables pause/resume, progress tracking, and error recovery.
    """
    
    def __init__(self, project_uuid: str, tenant_id: Optional[str] = None):
        self.project_uuid = project_uuid
        self.tenant_id = tenant_id
        self.persistence = SupabasePersistence(tenant_id=tenant_id)
        
        # In-memory state cache
        self.state: Optional[Dict[str, Any]] = None
    
    async def initialize_workflow(self, total_packages: int, phases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Initialize new workflow state"""
        state = {
            "project_uuid": self.project_uuid,
            "status": WorkflowStatus.PENDING,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            
            # Progress tracking
            "total_packages": total_packages,
            "processed_packages": 0,
            "succeeded_packages": 0,
            "failed_packages": 0,
            
            # Phase tracking
            "total_phases": len(phases),
            "current_phase_index": 0,
            "current_phase_name": phases[0]["phase"] if phases else None,
            
            # Package tracking
            "packages": {},  # package_name -> PackageState
            
            # Checkpoint data
            "checkpoint": {
                "last_completed_package": None,
                "last_completed_phase": None,
                "resume_from_phase": 0,
                "resume_from_package": None
            },
            
            # Results
            "succeeded": [],
            "failed": [],
            
            # Metadata
            "phases": phases,
            "cancellation_requested": False
        }
        
        self.state = state
        await self._persist_state()
        logger.info(f"Workflow state initialized for project {self.project_uuid}", "WorkflowState")
        return state
    
    async def load_workflow(self) -> Optional[Dict[str, Any]]:
        """Load existing workflow state from database"""
        try:
            # Query workflow state from utm_workflow_states table
            response = self.persistence.client.table("utm_workflow_states").select("*").eq(
                "project_uuid", self.project_uuid
            ).order("updated_at", desc=True).limit(1).execute()
            
            if response.data and len(response.data) > 0:
                state_record = response.data[0]
                self.state = state_record.get("state_data", {})
                logger.info(f"Loaded workflow state: {self.state.get('status')}", "WorkflowState")
                return self.state
            
            return None
        except Exception as e:
            logger.error(f"Failed to load workflow state: {e}", "WorkflowState")
            return None
    
    async def can_resume(self) -> bool:
        """Check if workflow can be resumed"""
        if not self.state:
            await self.load_workflow()
        
        if not self.state:
            return False
        
        status = self.state.get("status")
        return status in [WorkflowStatus.PAUSED, WorkflowStatus.FAILED]
    
    async def resume_workflow(self) -> Dict[str, Any]:
        """Resume paused/failed workflow"""
        if not await self.can_resume():
            raise ValueError("Workflow cannot be resumed")
        
        checkpoint = self.state.get("checkpoint", {})
        self.state["status"] = WorkflowStatus.RUNNING
        self.state["resumed_at"] = datetime.utcnow().isoformat()
        
        await self._persist_state()
        
        logger.info(
            f"Workflow resumed from phase {checkpoint.get('resume_from_phase')}, "
            f"package {checkpoint.get('resume_from_package')}",
            "WorkflowState"
        )
        
        return {
            "resume_from_phase": checkpoint.get("resume_from_phase", 0),
            "resume_from_package": checkpoint.get("resume_from_package"),
            "processed_count": self.state.get("processed_packages", 0)
        }
    
    async def update_phase(self, phase_index: int, phase_name: str):
        """Update current phase"""
        if not self.state:
            raise ValueError("Workflow not initialized")
        
        self.state["current_phase_index"] = phase_index
        self.state["current_phase_name"] = phase_name
        self.state["updated_at"] = datetime.utcnow().isoformat()
        
        # Update checkpoint
        self.state["checkpoint"]["last_completed_phase"] = phase_name
        self.state["checkpoint"]["resume_from_phase"] = phase_index
        
        await self._persist_state()
    
    async def start_package(self, package_name: str, phase_name: str):
        """Mark package as started"""
        if not self.state:
            raise ValueError("Workflow not initialized")
        
        self.state["packages"][package_name] = {
            "status": PackageStatus.GENERATING,
            "phase": phase_name,
            "started_at": datetime.utcnow().isoformat(),
            "agent_c_attempts": 0,
            "agent_f_attempts": 0,
            "last_error": None
        }
        
        await self._persist_state()
    
    async def update_package_status(
        self, 
        package_name: str, 
        status: PackageStatus,
        agent: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Update package processing status"""
        if not self.state:
            raise ValueError("Workflow not initialized")
        
        if package_name not in self.state["packages"]:
            logger.warning(f"Package {package_name} not found in state", "WorkflowState")
            return
        
        pkg_state = self.state["packages"][package_name]
        pkg_state["status"] = status
        pkg_state["updated_at"] = datetime.utcnow().isoformat()
        
        if agent:
            pkg_state[f"{agent}_completed_at"] = datetime.utcnow().isoformat()
        
        if error:
            pkg_state["last_error"] = error
        
        if status == PackageStatus.COMPLETED:
            pkg_state["completed_at"] = datetime.utcnow().isoformat()
            self.state["processed_packages"] += 1
            self.state["succeeded_packages"] += 1
            self.state["succeeded"].append(package_name)
            
            # Update checkpoint
            self.state["checkpoint"]["last_completed_package"] = package_name
            
        elif status == PackageStatus.FAILED:
            self.state["processed_packages"] += 1
            self.state["failed_packages"] += 1
            self.state["failed"].append({
                "package": package_name,
                "error": error or "Unknown error"
            })
        
        await self._persist_state()
    
    async def increment_retry_count(self, package_name: str, agent: str) -> int:
        """Increment and return retry count for agent"""
        if not self.state or package_name not in self.state["packages"]:
            return 0
        
        pkg_state = self.state["packages"][package_name]
        attempt_key = f"{agent}_attempts"
        pkg_state[attempt_key] = pkg_state.get(attempt_key, 0) + 1
        
        await self._persist_state()
        return pkg_state[attempt_key]
    
    async def pause_workflow(self, reason: Optional[str] = None):
        """Pause workflow execution"""
        if not self.state:
            return
        
        self.state["status"] = WorkflowStatus.PAUSED
        self.state["paused_at"] = datetime.utcnow().isoformat()
        self.state["pause_reason"] = reason
        
        await self._persist_state()
        logger.info(f"Workflow paused: {reason}", "WorkflowState")
    
    async def complete_workflow(self, success: bool = True):
        """Mark workflow as completed"""
        if not self.state:
            return
        
        self.state["status"] = WorkflowStatus.COMPLETED if success else WorkflowStatus.FAILED
        self.state["completed_at"] = datetime.utcnow().isoformat()
        
        await self._persist_state()
        logger.info(
            f"Workflow completed: {self.state['succeeded_packages']}/{self.state['total_packages']} succeeded",
            "WorkflowState"
        )
    
    async def cancel_workflow(self):
        """Mark workflow as cancelled"""
        if not self.state:
            return
        
        self.state["status"] = WorkflowStatus.CANCELLED
        self.state["cancelled_at"] = datetime.utcnow().isoformat()
        self.state["cancellation_requested"] = True
        
        await self._persist_state()
        logger.info("Workflow cancelled", "WorkflowState")
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current workflow progress"""
        if not self.state:
            return {"progress": 0, "status": "NOT_STARTED"}
        
        total = self.state.get("total_packages", 1)
        processed = self.state.get("processed_packages", 0)
        
        return {
            "status": self.state.get("status"),
            "progress": (processed / total * 100) if total > 0 else 0,
            "processed": processed,
            "total": total,
            "succeeded": self.state.get("succeeded_packages", 0),
            "failed": self.state.get("failed_packages", 0),
            "current_phase": self.state.get("current_phase_name"),
            "phase_progress": f"{self.state.get('current_phase_index', 0) + 1}/{self.state.get('total_phases', 0)}"
        }
    
    async def _persist_state(self):
        """Persist state to database"""
        if not self.state:
            return
        
        self.state["updated_at"] = datetime.utcnow().isoformat()
        
        try:
            # Upsert to utm_workflow_states
            data = {
                "project_uuid": self.project_uuid,
                "tenant_id": self.tenant_id,
                "state_data": self.state,
                "status": self.state.get("status"),
                "updated_at": self.state["updated_at"]
            }
            
            # Check if exists
            existing = self.persistence.client.table("utm_workflow_states").select("id").eq(
                "project_uuid", self.project_uuid
            ).execute()
            
            if existing.data and len(existing.data) > 0:
                # Update
                self.persistence.client.table("utm_workflow_states").update(data).eq(
                    "project_uuid", self.project_uuid
                ).execute()
            else:
                # Insert
                self.persistence.client.table("utm_workflow_states").insert(data).execute()
            
        except Exception as e:
            logger.error(f"Failed to persist workflow state: {e}", "WorkflowState")
            # Continue execution even if persistence fails
