-- Migration: 020 Add Project-Level Invitations
-- Description: Permite invitar COLLABORATOR/VIEWER a proyectos específicos

BEGIN;

-- 1. Agregar project_id a invitations (NULL = invitación a nivel tenant/MANAGER)
ALTER TABLE utm_user_invitations
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES utm_projects(project_id) ON DELETE CASCADE;

-- 2. Actualizar constraint de roles
ALTER TABLE utm_user_invitations DROP CONSTRAINT IF EXISTS utm_user_invitations_role_check;
ALTER TABLE utm_user_invitations ADD CONSTRAINT utm_user_invitations_role_check 
    CHECK (role IN ('MANAGER', 'COLLABORATOR', 'VIEWER'));

-- 3. Constraint de lógica de negocio:
--    - MANAGER: project_id debe ser NULL (invitación a nivel tenant)
--    - COLLABORATOR/VIEWER: project_id debe ser NOT NULL (invitación a proyecto específico)
ALTER TABLE utm_user_invitations ADD CONSTRAINT utm_invitations_project_role_logic
    CHECK (
        (role = 'MANAGER' AND project_id IS NULL) OR
        (role IN ('COLLABORATOR', 'VIEWER') AND project_id IS NOT NULL)
    );

-- 4. Índice para búsquedas por proyecto
CREATE INDEX IF NOT EXISTS idx_invitations_project ON utm_user_invitations(project_id);

-- 5. Comentarios
COMMENT ON TABLE utm_user_invitations IS 'Invitaciones de usuarios: MANAGER (tenant), COLLABORATOR/VIEWER (proyecto)';
COMMENT ON COLUMN utm_user_invitations.project_id IS 'NULL para MANAGER (tenant), NOT NULL para COLLABORATOR/VIEWER (proyecto específico)';
COMMENT ON COLUMN utm_user_invitations.role IS 'MANAGER (gestiona tenant), COLLABORATOR (trabaja en proyecto), VIEWER (solo lectura)';

COMMIT;
