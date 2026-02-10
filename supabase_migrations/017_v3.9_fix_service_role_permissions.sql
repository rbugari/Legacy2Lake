-- v3.9 Migration Script 017
-- Fix Service Role Permissions
-- Author: Development Team
-- Date: 2026-02-09

-- Description:
-- Grants necessary permissions to postgres and service_role for v3.9 tables.
-- The service role bypasses RLS, but still needs table-level GRANT permissions.

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Granting service role permissions on v3.9 tables...';
END $$;

-- Grant ALL on utm_users (required for auth operations)
GRANT ALL ON utm_users TO postgres;
GRANT ALL ON utm_users TO service_role;
GRANT ALL ON utm_users TO authenticated;
GRANT SELECT ON utm_users TO anon;

-- Grant ALL on utm_user_invitations (required for invite operations)
GRANT ALL ON utm_user_invitations TO postgres;
GRANT ALL ON utm_user_invitations TO service_role;
GRANT ALL ON utm_user_invitations TO authenticated;

-- Grant ALL on utm_tenants (required for tenant operations)
GRANT ALL ON utm_tenants TO postgres;
GRANT ALL ON utm_tenants TO service_role;
GRANT ALL ON utm_tenants TO authenticated;

-- Grant ALL on utm_projects (already should exist, but ensuring)
GRANT ALL ON utm_projects TO postgres;
GRANT ALL ON utm_projects TO service_role;
GRANT ALL ON utm_projects TO authenticated;

-- Grant ALL on utm_asset_context (if needed)
GRANT ALL ON utm_asset_context TO postgres;
GRANT ALL ON utm_asset_context TO service_role;
GRANT ALL ON utm_asset_context TO authenticated;

DO $$
BEGIN
    RAISE NOTICE 'Service role permissions granted successfully';
END $$;

COMMIT;

DO $$
BEGIN
    RAISE NOTICE 'Migration 017 completed: Service role permissions fixed';
END $$;
