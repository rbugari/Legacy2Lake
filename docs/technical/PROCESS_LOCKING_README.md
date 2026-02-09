# Process Locking System - Implementation Summary

## ✅ Completed Components

### 1. Database Schema
**File**: `supabase_migrations/20260207_process_locking.sql`

- Created `utm_process_locks` table
- Unique constraint for active locks per project/process
- Indexes for performance
- Auto-expiration function
- Comments and documentation

**Key Features**:
- Prevents duplicate active locks via unique constraint
- Auto-expires stale locks
- Stores lock metadata (user, session, IP, user agent)
- Supports multiple process types per project

### 2. Backend Service
**File**: `apps/api/services/lock_service.py`

**Class**: `LockService`

**Methods**:
- `acquire_lock()` - Acquire lock for a process
- `release_lock()` - Release a lock (by ID or project+type)
- `check_lock()` - Check if process is locked
- `force_release_lock()` - Admin-only forced release
- `get_project_locks()` - Get all locks for a project

**Features**:
- Automatic lock expiration check
- Same session re-acquisition extends lock
- Custom timeouts per process type (60min, 30min, 120min, etc.)
- Race condition handling via unique constraint
- Comprehensive error handling

### 3. API Router
**File**: `apps/api/routers/locks.py`

**Endpoints**:
- `POST /locks/acquire` - Acquire a lock
- `POST /locks/release` - Release a lock
- `POST /locks/check` - Check lock status
- `POST /locks/force-release` - Admin force-release
- `GET /locks/project/{project_id}` - Get project lock history

**Response Codes**:
- `200` - Success
- `423 Locked` - Process already locked
- `404` - Lock not found
- `401` - Authentication required
- `403` - Admin access required (for force-release)

**Models**:
- `AcquireLockRequest`
- `ReleaseLockRequest`
- `CheckLockRequest`
- `ForceReleaseRequest`
- `LockResponse`
- `LockStatusResponse`

### 4. Router Registration
**File**: `apps/api/main.py`

- Imported `locks_router`
- Registered with FastAPI app
- Available at `/locks/*` endpoints

### 5. Documentation
**File**: `docs/technical/PROCESS_LOCKING_GUIDE.md`

**Sections**:
- Overview and architecture
- Process types and timeouts
- Integration patterns (try/finally and context manager)
- Frontend integration examples
- Admin tools and troubleshooting
- Testing guidelines
- Migration instructions

### 6. Migration Script
**File**: `scripts/apply_process_locking_migration.py`

- Reads SQL migration file
- Provides instructions for manual application
- Can be extended for automated migration

### 7. Unit Tests
**File**: `tests/unit/services/test_lock_service.py`

**Test Cases**:
- ✅ Lock acquisition success
- ✅ Concurrent lock prevention
- ✅ Same user different session blocking
- ✅ Same user same session extension
- ✅ Lock release by ID
- ✅ Lock release by project+process
- ✅ Separate locks for different process types
- ✅ Lock status checking
- ✅ Admin force-release
- ✅ Project lock history

## 📋 Next Steps

### Immediate (Required for Production)

1. **Apply Migration**
   ```bash
   # Via Supabase Dashboard SQL Editor
   # Copy/paste from: supabase_migrations/20260207_process_locking.sql
   ```

2. **Integrate into Existing Endpoints**
   - [ ] `/projects/{id}/triage` - Triage process
   - [ ] `/projects/{id}/draft` - Drafting process
   - [ ] `/projects/{id}/refine` - Refinement process
   - [ ] `/projects/{id}/certify` - Certification process
   - [ ] `/projects/{id}/governance` - Governance process

3. **Frontend Integration**
   - [ ] Add session ID management (sessionStorage)
   - [ ] Update process start handlers to check locks
   - [ ] Handle 423 Locked responses
   - [ ] Show "Process running by X" message
   - [ ] Add admin force-release UI (admin panel)

4. **Testing**
   - [ ] Run unit tests: `pytest tests/unit/services/test_lock_service.py`
   - [ ] Integration tests with real database
   - [ ] End-to-end testing scenarios:
     - Single user normal flow
     - Multiple users concurrent access
     - Same user multiple tabs
     - Lock expiration
     - Admin force-release

### Optional Enhancements

5. **WebSocket Real-time Updates**
   - Notify users when locks are released
   - Show queue position if queueing implemented

6. **Lock Queueing**
   - Allow users to queue for lock
   - Auto-start when lock becomes available

7. **Granular Locking**
   - Lock specific objects/assets instead of entire project
   - Useful for large projects

8. **Monitoring & Alerts**
   - Alert admins about stuck locks
   - Dashboard for lock statistics
   - Identify processes that frequently timeout

## 🔧 Configuration

### Lock Timeouts

Current defaults in `apps/api/services/lock_service.py`:

```python
LOCK_TIMEOUTS = {
    "triage": 60,         # 60 minutes
    "drafting": 30,       # 30 minutes
    "refinement": 120,    # 120 minutes (2 hours)
    "certification": 45,  # 45 minutes
    "governance": 20,     # 20 minutes
    "default": 30         # Default for unknown types
}
```

**To adjust**: Edit `LOCK_TIMEOUTS` dict in `lock_service.py`

### Database Cleanup

Stale locks are auto-expired by the `expire_stale_locks()` function, called before each lock acquisition.

**Optional**: Set up cron job for periodic cleanup:
```sql
-- Requires pg_cron extension
SELECT cron.schedule(
    'expire-locks', 
    '*/5 * * * *',  -- Every 5 minutes
    'SELECT expire_stale_locks()'
);
```

## 📊 Integration Example

### Backend (Python)

```python
from apps.api.services.lock_service import LockService, ProcessLockError

@router.post("/projects/{project_id}/triage")
async def run_triage(
    project_id: str,
    request: Request,
    identity: dict = Depends(get_identity),
    db: SupabasePersistence = Depends(get_db)
):
    lock_service = LockService(
        tenant_id=identity["tenant_id"],
        client_id=identity["client_id"]
    )
    
    try:
        lock = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="triage",
            user_id=identity["tenant_id"],
            username=identity.get("username", "Unknown"),
            session_id=request.headers.get("X-Session-ID", str(uuid.uuid4()))
        )
        
        try:
            result = await execute_triage(project_id, db)
            await lock_service.release_lock(lock_id=lock['lock_id'])
            return result
        except Exception as e:
            await lock_service.release_lock(lock_id=lock['lock_id'])
            raise e
            
    except ProcessLockError as e:
        raise HTTPException(status_code=423, detail={
            "message": e.message,
            "locked_by": e.locked_by
        })
```

### Frontend (TypeScript)

```typescript
async function startTriage(projectId: string) {
  try {
    const response = await fetch(`/projects/${projectId}/triage`, {
      method: 'POST',
      headers: {
        'X-Tenant-ID': getTenantId(),
        'X-Session-ID': getSessionId(),  // From sessionStorage
        'Content-Type': 'application/json'
      }
    });
    
    if (response.status === 423) {
      const error = await response.json();
      showModal({
        title: 'Process Already Running',
        message: `Triage is being executed by ${error.locked_by}`,
        type: 'warning'
      });
      return;
    }
    
    // Process started successfully
    await handleTriageResult(await response.json());
    
  } catch (error) {
    console.error('Failed to start triage:', error);
  }
}
```

## 🎯 Success Criteria

- [x] Database schema created
- [x] Backend service implemented
- [x] API endpoints created
- [x] Router registered
- [x] Documentation written
- [x] Unit tests created
- [ ] Migration applied to database
- [ ] Integrated into process endpoints
- [ ] Frontend integration complete
- [ ] End-to-end testing passed

## 📝 Notes

- **Session ID**: Currently uses `X-Session-ID` header. Frontend should generate unique ID per tab/session.
- **Lock Ownership**: Locks are owned by user_id + session_id combination.
- **Admin Override**: Admins can force-release any lock via `/locks/force-release`.
- **Expiration**: Locks auto-expire based on process type timeout.
- **Race Conditions**: Handled via database unique constraint on (project_id, process_type, status='active').

---

**Implementation Date**: 2026-02-07  
**Version**: 1.0  
**Status**: ✅ COMPLETE (Ready for migration and integration)  
**Next Feature**: Agent Management UX
