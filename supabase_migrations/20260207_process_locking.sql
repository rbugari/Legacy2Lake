-- Migration: Process Locking System
-- Created: 2026-02-07
-- Description: Prevents concurrent execution of the same process on a project

-- Process Locks Table
CREATE TABLE IF NOT EXISTS utm_process_locks (
    lock_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    process_type VARCHAR(50) NOT NULL, -- 'triage', 'drafting', 'refinement', 'certification', 'governance'
    locked_by_user_id UUID NOT NULL,
    locked_by_username TEXT NOT NULL, -- Denormalized for quick display
    locked_by_session_id VARCHAR(255) NOT NULL,
    locked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'completed', 'expired', 'released'
    user_agent TEXT,
    ip_address VARCHAR(45),
    
    -- Ensure only ONE active lock per project + process type
    CONSTRAINT unique_active_lock UNIQUE (project_id, process_type, status)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_process_locks_project ON utm_process_locks(project_id);
CREATE INDEX IF NOT EXISTS idx_process_locks_status ON utm_process_locks(status);
CREATE INDEX IF NOT EXISTS idx_process_locks_expires_at ON utm_process_locks(expires_at);

-- Function to auto-expire locks
CREATE OR REPLACE FUNCTION expire_stale_locks()
RETURNS void AS $$
BEGIN
    UPDATE utm_process_locks
    SET status = 'expired'
    WHERE status = 'active'
    AND expires_at < now();
END;
$$ LANGUAGE plpgsql;

-- Optional: Create a scheduled job to clean up stale locks
-- Note: This requires pg_cron extension, comment out if not available
-- SELECT cron.schedule('expire-locks', '*/5 * * * *', 'SELECT expire_stale_locks()');

-- Grant permissions to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON utm_process_locks TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON utm_process_locks TO service_role;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION expire_stale_locks() TO authenticated;
GRANT EXECUTE ON FUNCTION expire_stale_locks() TO service_role;

COMMENT ON TABLE utm_process_locks IS 'Prevents concurrent execution of processes on the same project';
COMMENT ON COLUMN utm_process_locks.process_type IS 'Type of process: triage, drafting, refinement, certification, governance';
COMMENT ON COLUMN utm_process_locks.status IS 'Lock status: active, completed, expired, released';
