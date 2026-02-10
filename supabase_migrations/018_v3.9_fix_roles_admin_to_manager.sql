-- v3.9 Migration Script 018
-- Fix Roles: ADMIN → MANAGER (tenant users)
-- Author: Development Team
-- Date: 2026-02-09

-- Description:
-- Clarifica la diferencia conceptual entre ADMIN de plataforma y usuarios de tenant.
-- - ADMIN = Dueño de plataforma (escudo naranja), NO pertenece a tenant
-- - MANAGER = Responsable de tenant, crea proyectos, invita usuarios
-- - COLLABORATOR = Trabaja en proyectos, no puede borrarlos
-- - VIEWER = Solo lectura en proyectos de su tenant

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Actualizando roles de usuarios de tenant...';
END $$;

-- ============================================
-- 1. Primero dropar constraint antiguo
-- ============================================

-- Drop old constraint
ALTER TABLE utm_users DROP CONSTRAINT IF EXISTS utm_users_role_check;

DO $$
BEGIN
    RAISE NOTICE 'Constraint antiguo eliminado';
END $$;

-- ============================================
-- 2. Actualizar usuarios existentes ADMIN → MANAGER
-- ============================================

UPDATE utm_users 
SET role = 'MANAGER' 
WHERE role = 'ADMIN';

DO $$
BEGIN
    RAISE NOTICE 'Usuarios actualizados de ADMIN a MANAGER';
END $$;

-- ============================================
-- 3. Crear nuevo constraint con roles actualizados
-- ============================================

-- Create new constraint with updated roles
ALTER TABLE utm_users ADD CONSTRAINT utm_users_role_check 
CHECK (role IN ('MANAGER', 'COLLABORATOR', 'VIEWER'));

DO $$
BEGIN
    RAISE NOTICE 'Constraint de roles actualizado: MANAGER, COLLABORATOR, VIEWER';
END $$;

-- ============================================
-- 3. Actualizar default role a VIEWER
-- ============================================

ALTER TABLE utm_users ALTER COLUMN role SET DEFAULT 'VIEWER';

-- ============================================
-- 4. Actualizar tabla de invitaciones
-- ============================================

-- Drop old constraint first
ALTER TABLE utm_user_invitations DROP CONSTRAINT IF EXISTS utm_user_invitations_role_check;

-- Update any existing invitations (if any)
UPDATE utm_user_invitations 
SET role = 'MANAGER' 
WHERE role = 'ADMIN';

-- Create new constraint
ALTER TABLE utm_user_invitations ADD CONSTRAINT utm_user_invitations_role_check 
CHECK (role IN ('MANAGER', 'COLLABORATOR', 'VIEWER'));

DO $$
BEGIN
    RAISE NOTICE 'Constraint de invitaciones actualizado';
END $$;

-- ============================================
-- 5. Actualizar función get_user_role
-- ============================================

-- La función ya existe, solo agregamos comentario actualizado
COMMENT ON FUNCTION get_user_role IS 'v3.9: Helper to get user role within tenant (MANAGER/COLLABORATOR/VIEWER)';

-- ============================================
-- 6. Actualizar RLS policies para nuevos roles
-- ============================================

DO $$
BEGIN
    RAISE NOTICE 'Actualizando RLS policies con nuevos roles...';
END $$;

-- Projects: MANAGER y COLLABORATOR pueden crear
DROP POLICY IF EXISTS projects_create_admin_collab ON utm_projects;
CREATE POLICY projects_create_manager_collab
ON utm_projects FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_projects.tenant_id
        AND u.user_id = auth.uid()
        AND u.role IN ('MANAGER', 'COLLABORATOR')
        AND u.is_active = TRUE
    )
);

-- Projects: MANAGER y COLLABORATOR pueden actualizar
DROP POLICY IF EXISTS projects_update_admin_collab ON utm_projects;
CREATE POLICY projects_update_manager_collab
ON utm_projects FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_projects.tenant_id
        AND u.user_id = auth.uid()
        AND u.role IN ('MANAGER', 'COLLABORATOR')
        AND u.is_active = TRUE
    )
);

-- Projects: Solo MANAGER puede borrar
DROP POLICY IF EXISTS projects_delete_admin_only ON utm_projects;
CREATE POLICY projects_delete_manager_only
ON utm_projects FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_projects.tenant_id
        AND u.user_id = auth.uid()
        AND u.role = 'MANAGER'
        AND u.is_active = TRUE
    )
);

-- Users: Solo MANAGER puede gestionar usuarios de su tenant
DROP POLICY IF EXISTS users_manage_admin_only ON utm_users;
CREATE POLICY users_manage_manager_only
ON utm_users FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM utm_users manager
        WHERE manager.tenant_id = utm_users.tenant_id
        AND manager.user_id = auth.uid()
        AND manager.role = 'MANAGER'
        AND manager.is_active = TRUE
    )
);

-- Invitations: Solo MANAGER puede invitar
DROP POLICY IF EXISTS invitations_manage_admin_only ON utm_user_invitations;
CREATE POLICY invitations_manage_manager_only
ON utm_user_invitations FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM utm_users u
        WHERE u.tenant_id = utm_user_invitations.tenant_id
        AND u.user_id = auth.uid()
        AND u.role = 'MANAGER'
        AND u.is_active = TRUE
    )
);

DO $$
BEGIN
    RAISE NOTICE 'RLS policies actualizadas con roles MANAGER/COLLABORATOR/VIEWER';
END $$;

COMMIT;

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 018 completada';
    RAISE NOTICE 'Roles actualizados:';
    RAISE NOTICE '  MANAGER: Crea proyectos, invita usuarios, gestiona tenant';
    RAISE NOTICE '  COLLABORATOR: Trabaja en proyectos, no puede borrarlos';
    RAISE NOTICE '  VIEWER: Solo lectura en proyectos de su tenant';
    RAISE NOTICE '========================================';
END $$;
