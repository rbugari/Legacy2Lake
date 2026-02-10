-- v3.9 Migration Script 016
-- Update RLS Policies for Multi-User
-- Author: Development Team
-- Date: 2026-02-09

-- Description:
-- Updates Row Level Security policies to support multiple users per tenant.
-- Implements role-based access control (ADMIN, COLLABORATOR, VIEWER).

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Updating RLS policies for multi-user support...';
END $$;

-- ============================================
-- Helper Function: Get user role
-- ============================================

CREATE OR REPLACE FUNCTION get_user_role(user_uuid UUID, tenant_uuid UUID)
RETURNS VARCHAR AS $$
DECLARE
    user_role VARCHAR;
BEGIN
    SELECT role INTO user_role
    FROM utm_users
    WHERE user_id = user_uuid 
    AND tenant_id = tenant_uuid
    AND is_active = TRUE;
    
    RETURN user_role;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_user_role IS 'v3.9: Helper to get user role within tenant';

-- ============================================
-- utm_projects: Role-based RLS
-- ============================================

DO $$
BEGIN
    RAISE NOTICE 'Updating utm_projects RLS policies...';
END $$;

-- Drop old policies
DROP POLICY IF EXISTS projects_tenant_isolation ON utm_projects;

-- New policies with role checks
CREATE POLICY projects_read_all 
ON utm_projects FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_projects.tenant_id
        AND u.user_id = auth.uid()
        AND u.is_active = TRUE
    )
);

CREATE POLICY projects_create_admin_collab
ON utm_projects FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_projects.tenant_id
        AND u.user_id = auth.uid()
        AND u.role IN ('ADMIN', 'COLLABORATOR')
        AND u.is_active = TRUE
    )
);

CREATE POLICY projects_update_admin_collab
ON utm_projects FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_projects.tenant_id
        AND u.user_id = auth.uid()
        AND u.role IN ('ADMIN', 'COLLABORATOR')
        AND u.is_active = TRUE
    )
);

CREATE POLICY projects_delete_admin_only
ON utm_projects FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_projects.tenant_id
        AND u.user_id = auth.uid()
        AND u.role = 'ADMIN'
        AND u.is_active = TRUE
    )
);

-- ============================================
-- utm_asset_context: Same as projects
-- ============================================
-- NOTA: Tabla utm_assets no existe, usando utm_asset_context

DO $$
BEGIN
    RAISE NOTICE 'Updating utm_asset_context RLS policies...';
END $$;

-- Comentado por ahora - estructura de assets pendiente de definir
-- DROP POLICY IF EXISTS assets_tenant_isolation ON utm_asset_context;

/*
CREATE POLICY assets_read_all
ON utm_asset_context FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM utm_users u
        JOIN utm_projects p ON p.tenant_id = u.tenant_id
        WHERE p.project_id = utm_asset_context.project_id
        AND u.user_id = auth.uid()
        AND u.is_active = TRUE
    )
);

CREATE POLICY assets_create_admin_collab
ON utm_asset_context FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM utm_users u
        JOIN utm_projects p ON p.tenant_id = u.tenant_id
        WHERE p.project_id = utm_asset_context.project_id
        AND u.user_id = auth.uid()
        AND u.role IN ('ADMIN', 'COLLABORATOR')
        AND u.is_active = TRUE
    )
);

CREATE POLICY assets_update_admin_collab
ON utm_asset_context FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM utm_users u
        JOIN utm_projects p ON p.tenant_id = u.tenant_id
        WHERE p.project_id = utm_asset_context.project_id
        AND u.user_id = auth.uid()
        AND u.role IN ('ADMIN', 'COLLABORATOR')
        AND u.is_active = TRUE
    )
);

CREATE POLICY assets_delete_admin_only
ON utm_asset_context FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM utm_users u
        JOIN utm_projects p ON p.tenant_id = u.tenant_id
        WHERE p.project_id = utm_asset_context.project_id
        AND u.user_id = auth.uid()
        AND u.role = 'ADMIN'
        AND u.is_active = TRUE
    )
);
*/

-- ============================================
-- utm_users: Self + Admin access
-- ============================================

DO $$
BEGIN
    RAISE NOTICE 'Creating utm_users RLS policies...';
END $$;

ALTER TABLE utm_users ENABLE ROW LEVEL SECURITY;

-- Users can read themselves + same tenant
CREATE POLICY users_read_same_tenant
ON utm_users FOR SELECT
USING (
    tenant_id IN (
        SELECT tenant_id FROM utm_users WHERE user_id = auth.uid()
    )
);

-- Only ADMIN can create users (via invitations)
CREATE POLICY users_create_admin_only
ON utm_users FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_users.tenant_id
        AND u.user_id = auth.uid()
        AND u.role = 'ADMIN'
        AND u.is_active = TRUE
    )
);

-- Users can update themselves, ADMIN can update all
CREATE POLICY users_update_self_or_admin
ON utm_users FOR UPDATE
USING (
    user_id = auth.uid() -- Self
    OR EXISTS ( -- Or I'm admin of this tenant
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_users.tenant_id
        AND u.user_id = auth.uid()
        AND u.role = 'ADMIN'
        AND u.is_active = TRUE
    )
);

-- Only ADMIN can delete users
CREATE POLICY users_delete_admin_only
ON utm_users FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_users.tenant_id
        AND u.user_id = auth.uid()
        AND u.role = 'ADMIN'
        AND u.is_active = TRUE
    )
);

-- ============================================
-- utm_user_invitations: Admin access only
-- ============================================

DO $$
BEGIN
    RAISE NOTICE 'Creating utm_user_invitations RLS policies...';
END $$;

ALTER TABLE utm_user_invitations ENABLE ROW LEVEL SECURITY;

-- Only ADMIN can read invitations
CREATE POLICY invitations_read_admin_only
ON utm_user_invitations FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_user_invitations.tenant_id
        AND u.user_id = auth.uid()
        AND u.role = 'ADMIN'
        AND u.is_active = TRUE
    )
);

-- Only ADMIN can send invitations
CREATE POLICY invitations_create_admin_only
ON utm_user_invitations FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_user_invitations.tenant_id
        AND u.user_id = auth.uid()
        AND u.role = 'ADMIN'
        AND u.is_active = TRUE
    )
);

-- Only ADMIN can revoke invitations
CREATE POLICY invitations_update_admin_only
ON utm_user_invitations FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_user_invitations.tenant_id
        AND u.user_id = auth.uid()
        AND u.role = 'ADMIN'
        AND u.is_active = TRUE
    )
);

-- ============================================
-- Verification
-- ============================================

DO $$
DECLARE
    policy_count INTEGER;
BEGIN
    SELECT count(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public'
    AND tablename IN ('utm_projects', 'utm_assets', 'utm_users', 'utm_user_invitations');
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'RLS Policies created: %', policy_count;
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ RLS policies updated for multi-user';
END $$;

COMMIT;
