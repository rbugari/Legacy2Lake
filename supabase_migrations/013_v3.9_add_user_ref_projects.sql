-- v3.9 Migration Script 013
-- Add user references to utm_projects
-- Author: Development Team
-- Date: 2026-02-09

-- Description:
-- Adds created_by_user_id to track which user created each project.
-- Required for multi-user collaboration audit trails.

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Adding user references to utm_projects...';
END $$;

-- Add new column
ALTER TABLE utm_projects 
ADD COLUMN IF NOT EXISTS created_by_user_id UUID REFERENCES utm_users(user_id) ON DELETE SET NULL;

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_projects_created_by ON utm_projects(created_by_user_id);

-- Comment
COMMENT ON COLUMN utm_projects.created_by_user_id IS 'v3.9: User who created this project (for audit trail)';

-- Verify
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utm_projects' AND column_name = 'created_by_user_id'
    ) THEN
        RAISE NOTICE '✅ Column created_by_user_id added successfully';
    ELSE
        RAISE EXCEPTION 'Failed to add created_by_user_id column';
    END IF;
END $$;

COMMIT;
