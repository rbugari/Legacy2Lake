"""
Unit Tests for Process Locking Service
Tests lock acquisition, release, and concurrency handling.
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from apps.api.services.lock_service import LockService, ProcessLockError, LOCK_TIMEOUTS


# ---------------------------------------------------------------------------
# In-memory Supabase mock that honours the self.db.client.table() interface
# used by LockService without making real network calls.
# ---------------------------------------------------------------------------

class _MockTable:
    """Simulates a Supabase query builder for a single table."""

    def __init__(self, store: list):
        self._store = store  # shared list reference across all _MockTable instances
        self._op = None
        self._data = None
        self._filters: dict = {}
        self._single = False

    def select(self, *args):
        self._op = 'select'
        return self

    def insert(self, data):
        self._op = 'insert'
        self._data = dict(data)
        return self

    def update(self, data):
        self._op = 'update'
        self._data = dict(data)
        return self

    def delete(self):
        self._op = 'delete'
        return self

    def eq(self, k, v):
        self._filters[k] = v
        return self

    def neq(self, k, v):  # noqa – unused filter, just allow chaining
        return self

    def lt(self, k, v):  # noqa
        return self

    def order(self, k, **kw):  # noqa
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if self._op == 'insert':
            lock = {'lock_id': str(uuid.uuid4()), **self._data}
            self._store.append(lock)
            return MagicMock(data=[lock])

        matched = [
            l for l in list(self._store)
            if all(l.get(k) == v for k, v in self._filters.items())
        ]

        if self._op == 'select':
            if self._single:
                return MagicMock(data=matched[0] if matched else None)
            return MagicMock(data=matched)

        if self._op == 'update':
            for lock in matched:
                lock.update(self._data)
            return MagicMock(data=matched)

        if self._op == 'delete':
            for lock in matched:
                self._store.remove(lock)
            return MagicMock(data=matched)

        return MagicMock(data=None)


class _MockClient:
    """Simulates supabase.Client with an in-memory lock store."""

    def __init__(self):
        self._store: list = []

    def table(self, name: str):
        return _MockTable(self._store)

    def rpc(self, func_name: str):
        mock = MagicMock()
        mock.execute.return_value = MagicMock(data=None)
        return mock


class InMemoryMockDB:
    """Drop-in for SupabasePersistence in unit tests (no network calls)."""

    def __init__(self, tenant_id=None, client_id=None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client = _MockClient()


class TestProcessLocking:
    """Test suite for process locking functionality."""

    @pytest.fixture(autouse=True)
    def mock_lock_db(self, monkeypatch):
        """Patch SupabasePersistence in lock_service with in-memory mock."""
        monkeypatch.setattr(
            'apps.api.services.lock_service.SupabasePersistence',
            InMemoryMockDB,
        )
    
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
    async def test_same_user_different_session_extends_lock(self):
        """Test that same user with different session extends the lock."""
        service = LockService(tenant_id="test-tenant-1")
        
        # User 1, Session 1 acquires lock
        lock1 = await service.acquire_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1",
            username="User 1",
            session_id="session-1"
        )
        
        # Same user, different session - should extend the existing lock
        lock2 = await service.acquire_lock(
            project_id="project-123",
            process_type="triage",
            user_id="user-1",
            username="User 1",
            session_id="session-2"  # Different session
        )

        assert lock2['lock_id'] == lock1['lock_id']
    
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
        # Note: release_lock DELETES the lock record; only active locks remain.
        locks = await service.get_project_locks("project-123")

        assert len(locks) >= 1
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
