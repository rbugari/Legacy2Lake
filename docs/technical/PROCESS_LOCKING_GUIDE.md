# Process Locking Integration Guide

This document explains how to integrate the Process Locking System into existing and new process endpoints.

## Overview

The Process Locking System prevents concurrent execution of the same process on a project, avoiding data corruption and race conditions.

## Key Components

1. **Migration**: `supabase_migrations/20260207_process_locking.sql`
2. **Service**: `apps/api/services/lock_service.py`
3. **Router**: `apps/api/routers/locks.py`

## Process Types

The following process types are supported with their default timeouts:

- `triage`: 60 minutes
- `drafting`: 30 minutes
- `refinement`: 120 minutes
- `certification`: 45 minutes
- `governance`: 20 minutes

## Integration Pattern

### 1. Import Required Dependencies

```python
from apps.api.services.lock_service import LockService, ProcessLockError
from apps.api.routers.dependencies import get_identity
```

### 2. Add Lock Acquisition at Process Start

Here's the recommended pattern for integrating locks into your process endpoints:

```python
@router.post("/projects/{project_id}/triage")
async def run_triage(
    project_id: str,
    params: TriageParams,
    request: Request,
    identity: dict = Depends(get_identity),
    db: SupabasePersistence = Depends(get_db)
):
    """Re-runs the triage (discovery) process."""
    
    # 1. Initialize lock service
    lock_service = LockService(
        tenant_id=identity.get("tenant_id"),
        client_id=identity.get("client_id")
    )
    
    # 2. Get user info for lock
    username = identity.get("username", "Unknown User")
    user_id = identity.get("tenant_id")
    session_id = request.headers.get("X-Session-ID") or str(uuid.uuid4())
    
    # 3. Try to acquire lock
    lock_id = None
    try:
        lock = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="triage",
            user_id=user_id,
            username=username,
            session_id=session_id,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.headers.get("x-forwarded-for") or "unknown"
        )
        lock_id = lock['lock_id']
        
    except ProcessLockError as e:
        # Lock is held by another user/session
        raise HTTPException(
            status_code=423,  # 423 Locked
            detail={
                "error": "Process already running",
                "message": e.message,
                "locked_by": e.locked_by
            }
        )
    
    # 4. Execute your process
    try:
        # Your existing process logic here
        result = await execute_triage_logic(project_id, params, db)
        
        # 5. Release lock on success
        await lock_service.release_lock(lock_id=lock_id, user_id=user_id)
        
        return result
        
    except Exception as e:
        # 6. Release lock on error
        try:
            await lock_service.release_lock(lock_id=lock_id, user_id=user_id)
        except:
            pass  # Best effort release
        raise e
```

### 3. Alternative: Using Context Manager Pattern

For cleaner code, you can create a context manager:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def acquire_process_lock(
    lock_service: LockService,
    project_id: str,
    process_type: str,
    user_id: str,
    username: str,
    session_id: str,
    user_agent: str = None,
    ip_address: str = None
):
    """Context manager for acquiring and releasing process locks."""
    lock_id = None
    try:
        lock = await lock_service.acquire_lock(
            project_id=project_id,
            process_type=process_type,
            user_id=user_id,
            username=username,
            session_id=session_id,
            user_agent=user_agent,
            ip_address=ip_address
        )
        lock_id = lock['lock_id']
        yield lock_id
    finally:
        if lock_id:
            try:
                await lock_service.release_lock(lock_id=lock_id, user_id=user_id)
            except Exception as e:
                print(f"Warning: Failed to release lock {lock_id}: {e}")

# Usage:
@router.post("/projects/{project_id}/triage")
async def run_triage(
    project_id: str,
    params: TriageParams,
    request: Request,
    identity: dict = Depends(get_identity),
    db: SupabasePersistence = Depends(get_db)
):
    lock_service = LockService(tenant_id=identity.get("tenant_id"))
    
    try:
        async with acquire_process_lock(
            lock_service=lock_service,
            project_id=project_id,
            process_type="triage",
            user_id=identity.get("tenant_id"),
            username=identity.get("username", "Unknown"),
            session_id=request.headers.get("X-Session-ID") or str(uuid.uuid4())
        ) as lock_id:
            # Your process logic here
            return await execute_triage_logic(project_id, params, db)
            
    except ProcessLockError as e:
        raise HTTPException(status_code=423, detail={
            "error": "Process already running",
            "locked_by": e.locked_by
        })
```

## Frontend Integration

### 1. Check Lock Before Starting Process

```typescript
async function checkProcessLock(projectId: string, processType: string): Promise<boolean> {
  const response = await fetch('/locks/check', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-ID': getTenantId(),
      'X-Session-ID': getSessionId()
    },
    body: JSON.stringify({ project_id: projectId, process_type: processType })
  });
  
  const data = await response.json();
  return data.is_locked;
}
```

### 2. Handle Lock Errors

```typescript
async function startTriage(projectId: string) {
  try {
    const response = await fetch(`/projects/${projectId}/triage`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-ID': getTenantId(),
        'X-Session-ID': getSessionId()
      },
      body: JSON.stringify({ /* params */ })
    });
    
    if (response.status === 423) {
      // Process is locked
      const error = await response.json();
      showModal({
        title: 'Process Already Running',
        message: `Triage is currently being executed by ${error.locked_by}. Please wait for it to complete.`,
        type: 'warning'
      });
      return;
    }
    
    // Process started successfully
    const result = await response.json();
    // ...
    
  } catch (error) {
    console.error('Failed to start triage:', error);
  }
}
```

### 3. Session ID Management

Store a session ID in sessionStorage or generate a unique ID per tab:

```typescript
function getSessionId(): string {
  let sessionId = sessionStorage.getItem('session-id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    sessionStorage.setItem('session-id', sessionId);
  }
  return sessionId;
}

// Add to all API requests
const headers = {
  'X-Session-ID': getSessionId(),
  'X-Tenant-ID': getTenantId(),
  // ...
};
```

## Admin Tools

### Force Release a Lock

Admins can force-release locks that are stuck:

```bash
curl -X POST "http://localhost:8000/locks/force-release" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: <admin-tenant-id>" \
  -H "X-Role: ADMIN" \
  -d '{
    "project_id": "project-uuid",
    "process_type": "triage"
  }'
```

### View Lock History

```bash
curl "http://localhost:8000/locks/project/{project_id}" \
  -H "X-Tenant-ID: <tenant-id>"
```

## Testing

### Unit Tests

```python
import pytest
from apps.api.services.lock_service import LockService, ProcessLockError

@pytest.mark.asyncio
async def test_acquire_and_release_lock():
    """Test basic lock acquisition and release."""
    service = LockService(tenant_id="test-tenant")
    
    # Acquire lock
    lock = await service.acquire_lock(
        project_id="test-project",
        process_type="triage",
        user_id="user-1",
        username="Test User",
        session_id="session-1"
    )
    
    assert lock['lock_id']
    assert lock['status'] == 'active'
    
    # Release lock
    success = await service.release_lock(lock_id=lock['lock_id'])
    assert success

@pytest.mark.asyncio
async def test_concurrent_lock_acquisition():
    """Test that concurrent acquisitions are blocked."""
    service = LockService(tenant_id="test-tenant")
    
    # User 1 acquires lock
    lock1 = await service.acquire_lock(
        project_id="test-project",
        process_type="triage",
        user_id="user-1",
        username="User 1",
        session_id="session-1"
    )
    
    # User 2 tries to acquire - should fail
    with pytest.raises(ProcessLockError) as exc:
        await service.acquire_lock(
            project_id="test-project",
            process_type="triage",
            user_id="user-2",
            username="User 2",
            session_id="session-2"
        )
    
    assert "already running" in str(exc.value)
    
    # Cleanup
    await service.release_lock(lock_id=lock1['lock_id'])
```

## Migration Instructions

1. **Apply SQL Migration**:
   ```bash
   python scripts/apply_process_locking_migration.py
   ```
   Or manually via Supabase Dashboard SQL Editor.

2. **Update All Process Endpoints**:
   - `POST /projects/{id}/triage` - Add lock for 'triage'
   - `POST /projects/{id}/draft` - Add lock for 'drafting'
   - `POST /projects/{id}/refine` - Add lock for 'refinement'
   - `POST /projects/{id}/certify` - Add lock for 'certification'
   - `POST /projects/{id}/governance` - Add lock for 'governance'

3. **Test Thoroughly**:
   - Single user workflow (should work normally)
   - Multiple users on same project (should block)
   - Same user, different tabs (should block with friendly message)
   - Lock expiration (should auto-expire after timeout)
   - Admin force-release (should work)

## Troubleshooting

### Lock Not Released After Process Completion

Check for:
1. Exceptions not caught properly in try/finally
2. Process crashed without cleanup
3. Check `utm_process_locks` table for status='active' with old timestamps

Solution: Use admin force-release or wait for auto-expiration

### "Unique Constraint Violation" Error

This happens during race conditions when two requests try to acquire the same lock simultaneously. The second request should catch this and return a proper error. If you see this in logs, it's working as expected.

### Lock Expires Too Quickly

Adjust timeouts in `lock_service.py`:

```python
LOCK_TIMEOUTS = {
    "triage": 90,  # Increase from 60 to 90 minutes
    # ...
}
```

## Future Enhancements

1. **WebSocket Notifications**: Real-time notification when lock is released
2. **Lock Queueing**: Allow users to queue for lock when it becomes available
3. **Partial Locks**: Lock specific assets instead of entire project
4. **Lock Transfer**: Allow user to transfer lock to another user

---

*Document created: 2026-02-07*  
*Last updated: 2026-02-07*  
*Version: 1.0*
