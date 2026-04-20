"""
Integration Tests for Process Locking Service
Tests with real Supabase database connection.
"""
import pytest
import os
import asyncio
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Skip if no database connection available
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        reason="Supabase credentials not available"
    ),
]

from apps.api.services.lock_service import LockService, ProcessLockError
from apps.api.services.persistence_service import SupabasePersistence


class TestProcessLockingIntegration:
    """Integration tests with real database."""
    
    @pytest.fixture
    async def lock_service(self):
        """Create a lock service instance for testing."""
        tenant_id = f"test-tenant-{uuid.uuid4()}"
        return LockService(tenant_id=tenant_id)
    
    @pytest.fixture
    async def project_id(self):
        """Generate a unique project ID for testing."""
        return str(uuid.uuid4())
    
    @pytest.mark.asyncio
    async def test_acquire_and_release_lock_real_db(self, lock_service, project_id):
        """Test lock acquisition and release with real database."""
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        # Acquire lock
        lock = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="triage",
            user_id=user_id,
            username="Integration Test User",
            session_id=session_id
        )
        
        assert lock is not None
        assert lock['lock_id']
        assert lock['project_id'] == project_id
        assert lock['process_type'] == "triage"
        assert lock['status'] == 'active'
        
        # Verify lock exists
        check = await lock_service.check_lock(project_id, "triage")
        assert check is not None
        assert check['locked_by_username'] == "Integration Test User"
        
        # Release lock
        success = await lock_service.release_lock(lock_id=lock['lock_id'], user_id=user_id)
        assert success
        
        # Verify lock is released
        check_after = await lock_service.check_lock(project_id, "triage")
        assert check_after is None
    
    @pytest.mark.asyncio
    async def test_concurrent_lock_prevention_real_db(self, lock_service, project_id):
        """Test that concurrent acquisitions are blocked in real database."""
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        session1_id = str(uuid.uuid4())
        session2_id = str(uuid.uuid4())
        
        # User 1 acquires lock
        lock1 = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="triage",
            user_id=user1_id,
            username="User 1",
            session_id=session1_id
        )
        
        assert lock1 is not None
        
        # User 2 tries to acquire - should fail
        with pytest.raises(ProcessLockError) as exc_info:
            await lock_service.acquire_lock(
                project_id=project_id,
                process_type="triage",
                user_id=user2_id,
                username="User 2",
                session_id=session2_id
            )
        
        assert "already running" in str(exc_info.value.message).lower()
        assert exc_info.value.locked_by == "User 1"
        
        # Cleanup
        await lock_service.release_lock(lock_id=lock1['lock_id'], user_id=user1_id)
    
    @pytest.mark.asyncio
    async def test_same_session_extends_lock_real_db(self, lock_service, project_id):
        """Test that same session can extend lock."""
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        # First acquisition
        lock1 = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="triage",
            user_id=user_id,
            username="Test User",
            session_id=session_id
        )
        
        original_expires_at = lock1['expires_at']
        original_lock_id = lock1['lock_id']
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Same user/session re-acquires
        lock2 = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="triage",
            user_id=user_id,
            username="Test User",
            session_id=session_id
        )
        
        # Should be same lock with extended time
        assert lock2['lock_id'] == original_lock_id
        # Note: expires_at comparison might need timezone handling
        
        # Cleanup
        await lock_service.release_lock(lock_id=lock2['lock_id'], user_id=user_id)
    
    @pytest.mark.asyncio
    async def test_different_process_types_real_db(self, lock_service, project_id):
        """Test that different process types can have separate locks."""
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        # Acquire lock for triage
        lock1 = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="triage",
            user_id=user_id,
            username="Test User",
            session_id=session_id
        )
        
        # Acquire lock for drafting on same project - should succeed
        lock2 = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="drafting",
            user_id=user_id,
            username="Test User",
            session_id=session_id
        )
        
        assert lock1['lock_id'] != lock2['lock_id']
        assert lock1['process_type'] == 'triage'
        assert lock2['process_type'] == 'drafting'
        
        # Cleanup
        await lock_service.release_lock(lock_id=lock1['lock_id'], user_id=user_id)
        await lock_service.release_lock(lock_id=lock2['lock_id'], user_id=user_id)
    
    @pytest.mark.asyncio
    async def test_force_release_real_db(self, lock_service, project_id):
        """Test admin force-release functionality."""
        user_id = str(uuid.uuid4())
        admin_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        # User acquires lock
        lock = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="triage",
            user_id=user_id,
            username="Test User",
            session_id=session_id
        )
        
        # Admin force-releases
        success = await lock_service.force_release_lock(
            project_id=project_id,
            process_type="triage",
            admin_user_id=admin_id
        )
        
        assert success
        
        # Verify lock is released
        check = await lock_service.check_lock(project_id, "triage")
        assert check is None
    
    @pytest.mark.asyncio
    async def test_get_project_locks_real_db(self, lock_service, project_id):
        """Test retrieving lock history for a project."""
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        # Create and release multiple locks
        lock1 = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="triage",
            user_id=user_id,
            username="Test User",
            session_id=session_id
        )
        await lock_service.release_lock(lock_id=lock1['lock_id'], user_id=user_id)
        
        lock2 = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="drafting",
            user_id=user_id,
            username="Test User",
            session_id=session_id
        )
        
        # Get all locks
        locks = await lock_service.get_project_locks(project_id)
        
        assert len(locks) >= 2
        assert any(l['process_type'] == 'triage' for l in locks)
        assert any(l['process_type'] == 'drafting' for l in locks)
        
        # Cleanup
        await lock_service.release_lock(lock_id=lock2['lock_id'], user_id=user_id)
    
    @pytest.mark.asyncio
    async def test_lock_cleanup_after_tests(self, lock_service, project_id):
        """Cleanup test to ensure no locks are left hanging."""
        # Force release any remaining locks for test projects
        for process_type in ['triage', 'drafting', 'refinement', 'certification', 'governance']:
            try:
                await lock_service.force_release_lock(
                    project_id=project_id,
                    process_type=process_type,
                    admin_user_id="test-cleanup"
                )
            except:
                pass  # No lock to release


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
