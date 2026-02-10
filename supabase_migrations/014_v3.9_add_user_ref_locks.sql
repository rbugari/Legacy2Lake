-- v3.9 Migration Script 014
-- Add user references to utm_process_locks
-- Author: Development Team
-- Date: 2026-02-09

-- Description:
-- Adds locked_by_user_email to process locks for better tracking.
-- Helps identify which user is currently processing an asset.

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Adding user references to utm_process_locks...';
END $$;

-- Add new column
ALTER TABLE utm_process_locks 
ADD COLUMN IF NOT EXISTS locked_by_user_email VARCHAR(255);

-- Index for lookup
CREATE INDEX IF NOT EXISTS idx_locks_user_email ON utm_process_locks(locked_by_user_email);

-- Comment
COMMENT ON COLUMN utm_process_locks.locked_by_user_email IS 'v3.9: Email of user who owns this lock';

-- Verify
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utm_process_locks' AND column_name = 'locked_by_user_email'
    ) THEN
        RAISE NOTICE '✅ Column locked_by_user_email added successfully';
    ELSE
        RAISE EXCEPTION 'Failed to add locked_by_user_email column';
    END IF;
END $$;

COMMIT;
