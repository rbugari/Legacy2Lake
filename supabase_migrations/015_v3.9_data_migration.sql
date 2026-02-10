-- v3.9 Migration Script 015
-- Data Migration: Tenants → Organizations + Users
-- Author: Development Team
-- Date: 2026-02-09

-- ⚠️  CRITICAL: This script migrates all existing data
-- Must be run AFTER scripts 010-014

-- Description:
-- 1. Migrates utm_tenants_old → utm_tenants (as organizations)
-- 2. Creates first user per tenant in utm_users
-- 3. Updates utm_projects to reference users
-- 4. Validates data integrity

BEGIN;

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Step 1/4: Migrating tenants to organizations...';
    RAISE NOTICE '============================================';
END $$;

INSERT INTO utm_tenants (tenant_id, client_id, org_name, tier, is_active, created_at)
SELECT 
    tenant_id, 
    client_id, 
    COALESCE(username, 'Organization') AS org_name,
    CASE 
        WHEN role = 'ADMIN' THEN 'PREMIUM'::VARCHAR
        ELSE 'STANDARD'::VARCHAR
    END AS tier,
    COALESCE(is_active, TRUE) AS is_active,
    created_at
FROM utm_tenants_old
ON CONFLICT (tenant_id) DO NOTHING;

-- Verify count
DO $$
DECLARE
    old_count INTEGER;
    new_count INTEGER;
BEGIN
    SELECT count(*) INTO old_count FROM utm_tenants_old;
    SELECT count(*) INTO new_count FROM utm_tenants;
    
    RAISE NOTICE 'Tenants migrated: % → %', old_count, new_count;
    
    IF old_count != new_count THEN
        RAISE EXCEPTION 'MIGRATION ERROR: Tenant count mismatch (old=%, new=%)', old_count, new_count;
    END IF;
END $$;

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Step 2/4: Creating users from legacy tenants...';
    RAISE NOTICE '============================================';
END $$;

INSERT INTO utm_users (
    user_id, 
    tenant_id, 
    email, 
    username, 
    password_hash_bcrypt, 
    role, 
    is_active,
    display_name,
    created_at
)
SELECT 
    tenant_id AS user_id, -- ⚠️ Keep same UUID for backward compatibility
    tenant_id,
    -- Generate email from username (will be unique)
    CASE 
        WHEN username IS NOT NULL THEN username || '@legacy.local'
        ELSE 'admin_' || SUBSTRING(tenant_id::TEXT, 1, 8) || '@legacy.local'
    END AS email,
    COALESCE(username, 'admin') AS username,
    -- Use bcrypt if available, fallback to SHA256 (will need migration)
    COALESCE(
        password_hash_bcrypt, 
        password_hash,
        '$2b$12$DUMMY_HASH_NEEDS_RESET' -- Dummy hash if none exists
    ) AS password_hash_bcrypt,
    'ADMIN'::VARCHAR AS role, -- All legacy users become ADMIN
    COALESCE(is_active, TRUE) AS is_active,
    COALESCE(username, 'Administrator') AS display_name,
    created_at
FROM utm_tenants_old
ON CONFLICT (user_id) DO NOTHING;

-- Verify user count matches tenant count
DO $$
DECLARE
    tenant_count INTEGER;
    user_count INTEGER;
BEGIN
    SELECT count(*) INTO tenant_count FROM utm_tenants;
    SELECT count(*) INTO user_count FROM utm_users;
    
    RAISE NOTICE 'Users created: %', user_count;
    
    IF tenant_count != user_count THEN
        RAISE EXCEPTION 'MIGRATION ERROR: User count mismatch (tenants=%, users=%)', tenant_count, user_count;
    END IF;
END $$;

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Step 3/4: Updating projects with user ownership...';
    RAISE NOTICE '============================================';
END $$;

UPDATE utm_projects p
SET created_by_user_id = (
    SELECT user_id 
    FROM utm_users u 
    WHERE u.tenant_id = p.tenant_id 
    ORDER BY created_at ASC 
    LIMIT 1
)
WHERE created_by_user_id IS NULL;

-- Verify all projects have owner
DO $$
DECLARE
    null_owners INTEGER;
BEGIN
    SELECT count(*) INTO null_owners 
    FROM utm_projects 
    WHERE created_by_user_id IS NULL;
    
    IF null_owners > 0 THEN
        RAISE WARNING 'MIGRATION WARNING: % projects have no owner', null_owners;
    ELSE
        RAISE NOTICE 'All projects have owners assigned';
    END IF;
END $$;

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Step 4/4: Final validation...';
    RAISE NOTICE '============================================';
END $$;

DO $$
DECLARE
    old_tenant_count INTEGER;
    new_tenant_count INTEGER;
    user_count INTEGER;
    project_count INTEGER;
    orphan_projects INTEGER;
BEGIN
    -- Get counts
    SELECT count(*) INTO old_tenant_count FROM utm_tenants_old;
    SELECT count(*) INTO new_tenant_count FROM utm_tenants;
    SELECT count(*) INTO user_count FROM utm_users;
    SELECT count(*) INTO project_count FROM utm_projects;
    SELECT count(*) INTO orphan_projects FROM utm_projects WHERE created_by_user_id IS NULL;
    
    -- Log summary
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION SUMMARY:';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Old tenants: %', old_tenant_count;
    RAISE NOTICE 'New tenants: %', new_tenant_count;
    RAISE NOTICE 'Users created: %', user_count;
    RAISE NOTICE 'Projects updated: %', project_count;
    RAISE NOTICE 'Orphan projects: %', orphan_projects;
    RAISE NOTICE '========================================';
    
    -- Validation
    IF old_tenant_count != new_tenant_count THEN
        RAISE EXCEPTION 'CRITICAL: Tenant count mismatch!';
    END IF;
    
    IF new_tenant_count != user_count THEN
        RAISE EXCEPTION 'CRITICAL: User count mismatch!';
    END IF;
    
    IF orphan_projects > 0 THEN
        RAISE WARNING 'WARNING: % orphan projects exist', orphan_projects;
    END IF;
    
    RAISE NOTICE '✅ Migration validation PASSED';
END $$;

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'OPTIONAL: Drop old table (commented out for safety)';
    RAISE NOTICE '============================================';
    RAISE NOTICE '✅ Data migration completed successfully';
    RAISE NOTICE '⚠️  IMPORTANT: Keep utm_tenants_old for 1 week before dropping';
END $$;

-- Uncomment ONLY after verifying everything works in production for 1 week
-- DROP TABLE utm_tenants_old CASCADE;

COMMIT;
