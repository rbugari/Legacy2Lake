-- Migration: 021 Project Members Table
-- Description: Relación usuarios-proyectos con roles específicos

BEGIN;

-- 1. Tabla de miembros del proyecto
CREATE TABLE IF NOT EXISTS utm_project_members (
    project_id UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES utm_users(user_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    
    -- Auditoría
    added_by UUID REFERENCES utm_users(user_id) ON DELETE SET NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- PK compuesta
    PRIMARY KEY (project_id, user_id),
    
    -- Solo COLLABORATOR y VIEWER a nivel proyecto
    -- Los MANAGER tienen acceso a TODOS los proyectos del tenant
    CHECK (role IN ('COLLABORATOR', 'VIEWER'))
);

-- 2. Índices
CREATE INDEX IF NOT EXISTS idx_project_members_user ON utm_project_members(user_id);
CREATE INDEX IF NOT EXISTS idx_project_members_project ON utm_project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_role ON utm_project_members(role);

-- 3. Comentarios
COMMENT ON TABLE utm_project_members IS 'Miembros de proyectos con roles específicos (COLLABORATOR/VIEWER). Los MANAGER tienen acceso automático a todos los proyectos.';
COMMENT ON COLUMN utm_project_members.role IS 'COLLABORATOR (edita) o VIEWER (solo lectura) - MANAGER no se registra aquí';
COMMENT ON COLUMN utm_project_members.added_by IS 'MANAGER que agregó este miembro al proyecto';

-- 4. RLS Policy: Solo managers del tenant y miembros del proyecto pueden ver
ALTER TABLE utm_project_members ENABLE ROW LEVEL SECURITY;

-- Policy: Usuarios pueden ver sus propias membresías
CREATE POLICY utm_project_members_select_own ON utm_project_members
    FOR SELECT
    USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM utm_users u
            WHERE u.user_id = auth.uid()
            AND u.tenant_id = (SELECT tenant_id FROM utm_projects WHERE project_id = utm_project_members.project_id)
            AND u.role = 'MANAGER'
        )
    );

-- Policy: Solo MANAGER puede agregar/eliminar miembros
CREATE POLICY utm_project_members_insert_manager ON utm_project_members
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM utm_users u
            WHERE u.user_id = auth.uid()
            AND u.tenant_id = (SELECT tenant_id FROM utm_projects WHERE project_id = utm_project_members.project_id)
            AND u.role = 'MANAGER'
        )
    );

CREATE POLICY utm_project_members_delete_manager ON utm_project_members
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM utm_users u
            WHERE u.user_id = auth.uid()
            AND u.tenant_id = (SELECT tenant_id FROM utm_projects WHERE project_id = utm_project_members.project_id)
            AND u.role = 'MANAGER'
        )
    );

COMMIT;
