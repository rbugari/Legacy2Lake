"""
Process Locking Service
Prevents concurrent execution of processes on the same project.
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from supabase import create_client, Client

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    from ..utils.logger import logger
    from .persistence_service import SupabasePersistence

# Default lock timeouts per process type (in minutes)
LOCK_TIMEOUTS = {
    "triage": 60,
    "drafting": 30,
    "refinement": 120,
    "certification": 45,
    "governance": 20,
    "default": 30
}


class ProcessLockError(Exception):
    """Raised when a process cannot acquire a lock."""
    def __init__(self, message: str, locked_by: str = None):
        self.message = message
        self.locked_by = locked_by
        super().__init__(self.message)


class LockService:
    """Service for managing process locks."""
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
        
    async def acquire_lock(
        self,
        project_id: str,
        process_type: str,
        user_id: str,
        username: str,
        session_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Attempts to acquire a lock for a process.
        
        Args:
            project_id: UUID of the project
            process_type: Type of process (triage, drafting, refinement, etc.)
            user_id: UUID of the user requesting the lock
            username: Username for display purposes
            session_id: Unique session identifier
            user_agent: Browser user agent string
            ip_address: Client IP address
            
        Returns:
            Lock information dict with lock_id
            
        Raises:
            ProcessLockError: If lock cannot be acquired
        """
        # First, expire any stale locks
        await self._expire_stale_locks()
        
        # Check if there's an active lock
        existing_lock = await self._get_active_lock(project_id, process_type)
        
        if existing_lock:
            # Check if it's the same user/session trying to re-acquire
            if (existing_lock['locked_by_user_id'] == user_id and 
                existing_lock['locked_by_session_id'] == session_id):
                # Same session trying to re-acquire - extend the lock
                logger.info(f"Extending existing lock {existing_lock['lock_id']} for same session")
                return await self._extend_lock(existing_lock['lock_id'])
            else:
                # Different user/session - lock is held
                raise ProcessLockError(
                    message=f"Process '{process_type}' is already running on this project",
                    locked_by=existing_lock['locked_by_username']
                )
        
        # No active lock - create one
        timeout_minutes = LOCK_TIMEOUTS.get(process_type, LOCK_TIMEOUTS['default'])
        expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)
        
        lock_data = {
            'project_id': project_id,
            'process_type': process_type,
            'locked_by_user_id': user_id,
            'locked_by_username': username,
            'locked_by_session_id': session_id,
            'expires_at': expires_at.isoformat(),
            'status': 'active',
            'user_agent': user_agent,
            'ip_address': ip_address
        }
        
        try:
            result = self.db.client.table('utm_process_locks').insert(lock_data).execute()
            lock = result.data[0] if result.data else None
            
            if lock:
                logger.info(f"Lock acquired: {lock['lock_id']} for {process_type} on project {project_id}")
                return lock
            else:
                raise ProcessLockError("Failed to create lock")
                
        except Exception as e:
            logger.error(f"Error acquiring lock: {str(e)}")
            # Check if it's a unique constraint violation (race condition)
            if 'unique_active_lock' in str(e).lower():
                # Another request beat us to it - fetch the existing lock
                existing_lock = self._get_active_lock(project_id, process_type)
                if existing_lock:
                    raise ProcessLockError(
                        message=f"Process '{process_type}' is already running on this project",
                        locked_by=existing_lock['locked_by_username']
                    )
            raise ProcessLockError(f"Failed to acquire lock: {str(e)}")
    
    async def release_lock(
        self,
        lock_id: Optional[str] = None,
        project_id: Optional[str] = None,
        process_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Releases a process lock by DELETING it.
        
        Args:
            lock_id: Specific lock ID to release (preferred)
            project_id: Project ID (used with process_type if lock_id not provided)
            process_type: Process type (used with project_id if lock_id not provided)
            user_id: User ID (optional verification)
            
        Returns:
            True if lock was released successfully
        """
        try:
            if lock_id:
                # Release by lock_id - DELETE instead of UPDATE to avoid unique constraint issues
                query = self.db.client.table('utm_process_locks').delete().eq('lock_id', lock_id).eq('status', 'active')
                
                if user_id:
                    query = query.eq('locked_by_user_id', user_id)
                    
            elif project_id and process_type:
                # Release by project + process type - DELETE instead of UPDATE
                query = self.db.client.table('utm_process_locks').delete().eq('project_id', project_id).eq('process_type', process_type).eq('status', 'active')
                
                if user_id:
                    query = query.eq('locked_by_user_id', user_id)
            else:
                logger.error("Must provide either lock_id or (project_id + process_type)")
                return False
            
            result = query.execute()
            
            if result.data:
                logger.info(f"Lock released successfully: {lock_id or f'{project_id}/{process_type}'}")
                return True
            else:
                logger.warning(f"No active lock found to release: {lock_id or f'{project_id}/{process_type}'}")
                return False
                
        except Exception as e:
            logger.error(f"Error releasing lock: {str(e)}")
            return False
    
    async def check_lock(
        self,
        project_id: str,
        process_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Checks if there's an active lock for a process.
        
        Returns:
            Lock information if locked, None if available
        """
        await self._expire_stale_locks()
        return await self._get_active_lock(project_id, process_type)
    
    async def force_release_lock(
        self,
        project_id: str,
        process_type: str,
        admin_user_id: str
    ) -> bool:
        """
        Admin-only: Force release a lock by DELETING it.
        
        Args:
            project_id: Project ID
            process_type: Process type
            admin_user_id: ID of admin user performing the action
            
        Returns:
            True if successful
        """
        try:
            # DELETE instead of UPDATE to avoid constraint issues
            result = self.db.client.table('utm_process_locks').delete().eq('project_id', project_id).eq('process_type', process_type).eq('status', 'active').execute()
            
            if result.data:
                logger.warning(f"Lock force-released by admin {admin_user_id}: {project_id}/{process_type}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error force-releasing lock: {str(e)}")
            return False
    
    async def get_project_locks(self, project_id: str) -> list:
        """Get all locks (active and historical) for a project."""
        try:
            result = self.db.client.table('utm_process_locks')\
                .select('*')\
                .eq('project_id', project_id)\
                .order('locked_at', desc=True)\
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error fetching project locks: {str(e)}")
            return []
    
    # Private helper methods
    
    async def _get_active_lock(self, project_id: str, process_type: str) -> Optional[Dict[str, Any]]:
        """Fetch active lock for project + process type."""
        try:
            result = self.db.client.table('utm_process_locks')\
                .select('*')\
                .eq('project_id', project_id)\
                .eq('process_type', process_type)\
                .eq('status', 'active')\
                .single()\
                .execute()
            return result.data if result.data else None
        except Exception:
            # No active lock found
            return None
    
    async def _expire_stale_locks(self):
        """Mark expired locks as 'expired'."""
        try:
            self.db.client.rpc('expire_stale_locks').execute()
        except Exception as e:
            logger.error(f"Error expiring stale locks: {str(e)}")
    
    async def _extend_lock(self, lock_id: str) -> Dict[str, Any]:
        """Extend the expiration time of an existing lock."""
        try:
            # Get current lock to determine process type
            result = self.db.client.table('utm_process_locks')\
                .select('process_type')\
                .eq('lock_id', lock_id)\
                .single()\
                .execute()
            
            if result.data:
                process_type = result.data['process_type']
                timeout_minutes = LOCK_TIMEOUTS.get(process_type, LOCK_TIMEOUTS['default'])
                new_expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)
                
                update_result = self.db.client.table('utm_process_locks').update({
                    'expires_at': new_expires_at.isoformat()
                }).eq('lock_id', lock_id).execute()
                
                return update_result.data[0] if update_result.data else None
            return None
            
        except Exception as e:
            logger.error(f"Error extending lock: {str(e)}")
            raise ProcessLockError(f"Failed to extend lock: {str(e)}")
