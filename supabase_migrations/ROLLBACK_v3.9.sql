-- v3.9 EMERGENCY ROLLBACK
-- Use ONLY if migration fails critically
-- Author: Development Team
-- Date: 2026-02-09

-- ⚠️  WARNING: This will DESTROY v3.9 changes
-- Only run if you need to revert to v3.8 state

BEGIN;

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'EMERGENCY ROLLBACK - v3.9 → v3.8';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Step 1/4: Dropping new tables...';
END $$;

DROP TABLE IF EXISTS utm_user_invitations CASCADE;
DROP TABLE IF EXISTS utm_users CASCADE;
DROP TABLE IF EXISTS utm_tenants CASCADE;

DO $$
BEGIN
    RAISE NOTICE 'Step 2/4: Restoring utm_tenants_old...';
END $$;

DO $$
BEGIN
    RAISE NOTICE 'Step 3/4: Removing new columns...';
END $$
-- Step 3: Remove new columns from existing tables
RAISE NOTICE 'Step 3/4: Removing new columns...';

ALTER TABLE utm_projects 
DROP COLUMN IF EXISTS created_by_user_id;

ALTER TABLE utm_process_locks 
DO $$
BEGIN
    RAISE NOTICE 'Step 4/4: Verifying rollback...';
END $$
-- Step 4: Verify rollback
RAISE NOTICE 'Step 4/4: Verifying rollback...';

DO $$
DECLARE
    tenant_count INTEGER;
BEGIN
    -- Check utm_tenants exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'utm_tenants') THEN
        RAISE EXCEPTION 'ROLLBACK FAILED: utm_tenants table missing';
    END IF;
    
    -- Check old structure
    SELECT count(*) INTO tenant_count FROM utm_tenants;
    RAISE NOTICE 'Tenants restored: %', tenant_count;
    
    -- Check new tables gone
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'utm_users') THEN
        RAISE EXCEPTION 'ROLLBACK FAILED: utm_users still exists';
    END IF;
    
    RAISE NOTICE '✅ Rollback completed successfully';
    RAISE NOTICE '⚠️  System reverted to v3.8 state';
END $$;

COMMIT;

-- Instructions after rollback:
-- 1. Restart backend API
-- 2. Clear any cached data
-- 3. Notify users of maintenance completion
-- 4. Investigate root cause before retry
