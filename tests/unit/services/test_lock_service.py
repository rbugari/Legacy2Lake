"""
Unit Tests for Process Locking Service
Tests lock acquisition, release, and concurrency handling.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from apps.api.services.lock_service import LockService, ProcessLockError, LOCK_TIMEOUTS

# Mock SupabasePersistence for testing
class MockSupabasePersistence:
    def __init__(self, tenant_id=None, client_id=None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.locks = []  # In-memory lock storage
        
    async def get_active_lock(self, project_id: str, process_type: str):
        """Get active lock from mock storage."""
        for lock in self.locks:
            if (lock['project_id'] == project_id and 
                lock['process_type'] == process_type and 
                lock['status'] == 'active' and
                datetime.fromisoformat(lock['expires_at']) > datetime.utcnow()):
                return lock
        return None
    
    async def create_lock(self, lock_data: dict):
        """Create a lock in mock storage."""
        lock = {
            'lock_id': f"mock-lock-{len(self.locks)}",
            **lock_data
        }
        self.locks.append(lock)
        return lock
    
    async def update_lock(self, lock_id: str, updates: dict):
        """Update lock in mock storage."""
        for lock in self.locks:
            if lock['lock_id'] == lock_id:
                lock.update(updates)
                return True
        return False
    
    async def expire_stale_locks(self):
        """Mark expired locks."""
        now = datetime.utcnow()
        for lock in self.locks:
            if (lock['status'] == 'active' and 
                datetime.fromisoformat(lock['expires_at']) < now):
                lock['status'] = 'expired'


class TestProcessLocking:
    """Test suite for process locking functionality."""
    
    @pytest.mark.asyncio
    async def test_acquire_lock_success(self):
        """Test successful lock acquisition."""
        service = LockService(tenant_id="test-tenant-1")
        
        lock = await service.acquire_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1",
            username="Test User 1",
            session_id="session-1"
        )
        
        assert lock is not None
        assert lock['lock_id']
        assert lock['project_id'] == "project-123"
        assert lock['process_type'] == "triage"
        assert lock['locked_by_username'] == "Test User 1"
        assert lock['status'] == 'active'
    
    @pytest.mark.asyncio
    async def test_acquire_lock_when_locked_by_other(self):
        """Test that lock acquisition fails when already locked by another user."""
        service = LockService(tenant_id="test-tenant-1")
        
        # User 1 acquires lock
        lock1 = await service.acquire_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1",
            username="User 1",
            session_id="session-1"
        )
        
        # User 2 tries to acquire the same lock - should fail
        with pytest.raises(ProcessLockError) as exc_info:
            await service.acquire_lock(
                project_id="project-123",
                process_type="triage",
                user_id="user-2",
                username="User 2",
                session_id="session-2"
            )
        
        assert "already running" in str(exc_info.value.message).lower()
        assert exc_info.value.locked_by == "User 1"
    
    @pytest.mark.asyncio
    async def test_same_user_different_session_blocked(self):
        """Test that same user with different session is blocked."""
        service = LockService(tenant_id="test-tenant-1")
        
        # User 1, Session 1 acquires lock
        lock1 = await service.acquire_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1",
            username="User 1",
            session_id="session-1"
        )
        
        # Same user, different session - should be blocked
        with pytest.raises(ProcessLockError):
            await service.acquire_lock(
                project_id="project-123",
                process_type="triage",
                user_id="user-1",
                username="User 1",
                session_id="session-2"  # Different session
            )
    
    @pytest.mark.asyncio
    async def test_same_user_same_session_extends_lock(self):
        """Test that same user/session re-acquiring extends the lock."""
        service = LockService(tenant_id="test-tenant-1")
        
        # First acquisition
        lock1 = await service.acquire_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1",
            username="User 1",
            session_id="session-1"
        )
        
        original_expires_at = lock1['expires_at']
        
        # Wait a bit
        await asyncio.sleep(1)
        
        # Same user/session re-acquires - should extend
        lock2 = await service.acquire_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1",
            username="User 1",
            session_id="session-1"  # Same session
        )
        
        # Should be the same lock, but with extended expiration
        assert lock2['lock_id'] == lock1['lock_id']
        assert lock2['expires_at'] >= original_expires_at
    
    @pytest.mark.asyncio
    async def test_release_lock_by_lock_id(self):
        """Test releasing lock by lock_id."""
        service = LockService(tenant_id="test-tenant-1")
        
        lock = await service.acquire_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1",
            username="User 1",
            session_id="session-1"
        )
        
        # Release by lock_id
        success = await service.release_lock(lock_id=lock['lock_id'], user_id="user-1")
        assert success
        
        # Check that lock is no longer active
        check = await service.check_lock("project-123", "triage")
        assert check is None
    
    @pytest.mark.asyncio
    async def test_release_lock_by_project_process(self):
        """Test releasing lock by project_id + process_type."""
        service = LockService(tenant_id="test-tenant-1")
        
        lock = await service.acquire_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1",
            username="User 1",
            session_id="session-1"
        )
        
        # Release by project + process
        success = await service.release_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1"
        )
        assert success
    
    @pytest.mark.asyncio
    async def test_different_process_types_separate_locks(self):
        """Test that different process types can have separate locks."""
        service = LockService(tenant_id="test-tenant-1")
        
        # Acquire lock for triage
        lock1 = await service.acquire_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1",
            username="User 1",
            session_id="session-1"
        )
        
        # Acquire lock for drafting on same project - should succeed
        lock2 = await service.acquire_lock(
            project_id="project-123",
            process_type="drafting",
            user_id="user-1",
            username="User 1",
            session_id="session-1"
        )
        
        assert lock1['lock_id'] != lock2['lock_id']
        assert lock1['process_type'] == 'triage'
        assert lock2['process_type'] == 'drafting'
    
    @pytest.mark.asyncio
    async def test_check_lock_when_locked(self):
        """Test checking lock status when locked."""
        service = LockService(tenant_id="test-tenant-1")
        
        # Acquire lock
        lock = await service.acquire_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1",
            username="User 1",
            session_id="session-1"
        )
        
        # Check lock
        check = await service.check_lock("project-123", "triage")
        assert check is not None
        assert check['locked_by_username'] == "User 1"
    
    @pytest.mark.asyncio
    async def test_check_lock_when_available(self):
        """Test checking lock status when available."""
        service = LockService(tenant_id="test-tenant-1")
        
        check = await service.check_lock("project-999", "triage")
        assert check is None
    
    @pytest.mark.asyncio
    async def test_force_release_lock(self):
        """Test admin force-releasing a lock."""
        service = LockService(tenant_id="test-tenant-1")
        
        # User acquires lock
        lock = await service.acquire_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1",
            username="User 1",
            session_id="session-1"
        )
        
        # Admin force-releases
        success = await service.force_release_lock(
            project_id="project-123",
            process_type="triage",
            admin_user_id="admin-1"
        )
        assert success
        
        # Lock should now be available
        check = await service.check_lock("project-123", "triage")
        assert check is None
    
    @pytest.mark.asyncio
    async def test_lock_timeout_values(self):
        """Test that different process types have correct timeouts."""
        assert LOCK_TIMEOUTS['triage'] == 60
        assert LOCK_TIMEOUTS['drafting'] == 30
        assert LOCK_TIMEOUTS['refinement'] == 120
        assert LOCK_TIMEOUTS['certification'] == 45
        assert LOCK_TIMEOUTS['governance'] == 20
        assert LOCK_TIMEOUTS['default'] == 30
    
    @pytest.mark.asyncio
    async def test_get_project_locks(self):
        """Test retrieving all locks for a project."""
        service = LockService(tenant_id="test-tenant-1")
        
        # Create multiple locks
        lock1 = await service.acquire_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1",
            username="User 1",
            session_id="session-1"
        )
        
        await service.release_lock(lock_id=lock1['lock_id'])
        
        lock2 = await service.acquire_lock(
            project_id="project-123",
            process_type="drafting",
            user_id="user-1",
            username="User 1",
            session_id="session-1"
        )
        
        # Get all locks for project
        locks = await service.get_project_locks("project-123")
        
        assert len(locks) >= 2
        assert any(l['process_type'] == 'triage' for l in locks)
        assert any(l['process_type'] == 'drafting' for l in locks)


# Integration tests would go here (require actual Supabase connection)
class TestProcessLockingIntegration:
    """Integration tests requiring database connection."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_database_lock_flow(self):
        """Test full lock flow with real database."""
        # This would use actual Supabase connection
        # Marked with @pytest.mark.integration to run separately
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
