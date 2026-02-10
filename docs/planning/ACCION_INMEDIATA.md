# v3.9 Multi-User - Plan de Acción Inmediato

**Fecha**: 9 de Febrero, 2026  
**Status**: READY TO START  
**Kickoff**: 17 de Febrero, 2026

---

## 🎯 Esta Semana (Feb 10-16): Pre-Kickoff

### ✅ Lunes 10 Feb - Aprobación & Setup

**Tasks**:
1. [ ] **Stakeholder Review** (2 horas)
   - Presentar plan simplificado a CTO/Product
   - Obtener sign-off formal
   - Confirmar presupuesto y timeline

2. [ ] **Team Assignment** (1 hora)
   - Backend: [NOMBRE] 
   - Frontend: [NOMBRE]
   - QA: [NOMBRE]
   - DevOps: [NOMBRE]

3. [ ] **Environment Setup** (2 horas)
   ```powershell
   # Clone producción a staging
   pg_dump $PROD_DB_URL > staging_backup_$(Get-Date -Format 'yyyyMMdd').sql
   psql $STAGING_DB_URL < staging_backup_$(Get-Date -Format 'yyyyMMdd').sql
   
   # Verify
   psql $STAGING_DB_URL -c "SELECT count(*) FROM utm_tenants;"
   psql $STAGING_DB_URL -c "SELECT count(*) FROM utm_projects;"
   ```

---

### ✅ Martes 11 Feb - Documentación Técnica

**Tasks**:
1. [ ] **Crear Migration Scripts Skeleton** (3 horas)
   ```powershell
   cd c:\proyectos_dev\UTM\supabase_migrations
   
   # Crear archivos
   New-Item -Path ".\010_v3.9_create_users_table.sql" -ItemType File
   New-Item -Path ".\011_v3.9_create_invitations_table.sql" -ItemType File
   New-Item -Path ".\012_v3.9_refactor_tenants.sql" -ItemType File
   New-Item -Path ".\013_v3.9_update_projects.sql" -ItemType File
   New-Item -Path ".\014_v3.9_update_process_locks.sql" -ItemType File
   New-Item -Path ".\015_v3.9_data_migration.sql" -ItemType File
   New-Item -Path ".\016_v3.9_rls_policies.sql" -ItemType File
   ```

2. [ ] **API Spec Document** (2 horas)
   - Documentar 6 nuevos endpoints en Swagger
   - Request/response schemas
   - Error codes

3. [ ] **UI Mockups** (2 horas)
   - Team page wireframe (Figma/Excalidraw)
   - Invite modal mockup
   - Role badge designs

---

### ✅ Miércoles 12 Feb - Migration Scripts (Parte 1)

**Tasks**:
1. [ ] **Script 010: Create utm_users** (2 horas)
   
   File: `supabase_migrations/010_v3.9_create_users_table.sql`
   ```sql
   -- Create utm_users table
   CREATE TABLE utm_users (
       user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
       
       -- Identity
       email VARCHAR(255) NOT NULL UNIQUE,
       username VARCHAR(100) NOT NULL,
       password_hash_bcrypt TEXT NOT NULL,
       
       -- Role (3 options)
       role VARCHAR(20) NOT NULL DEFAULT 'VIEWER',
       CHECK (role IN ('ADMIN', 'COLLABORATOR', 'VIEWER')),
       
       -- Status
       is_active BOOLEAN DEFAULT TRUE,
       last_login TIMESTAMP WITH TIME ZONE,
       
       -- Basic info
       display_name VARCHAR(255),
       
       -- Audit
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       
       UNIQUE(tenant_id, email)
   );
   
   CREATE INDEX idx_users_tenant ON utm_users(tenant_id);
   CREATE INDEX idx_users_email ON utm_users(email);
   CREATE INDEX idx_users_role ON utm_users(role);
   
   COMMENT ON TABLE utm_users IS 'v3.9: Separate user identity from tenant/organization';
   ```

2. [ ] **Script 011: Create utm_user_invitations** (1 hora)
   
   File: `supabase_migrations/011_v3.9_create_invitations_table.sql`
   ```sql
   CREATE TABLE utm_user_invitations (
       invitation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
       email VARCHAR(255) NOT NULL,
       role VARCHAR(20) NOT NULL DEFAULT 'VIEWER',
       CHECK (role IN ('ADMIN', 'COLLABORATOR', 'VIEWER')),
       
       -- Token for acceptance
       token VARCHAR(255) UNIQUE NOT NULL,
       expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
       
       -- Status
       status VARCHAR(20) DEFAULT 'PENDING',
       CHECK (status IN ('PENDING', 'ACCEPTED', 'EXPIRED', 'REVOKED')),
       
       invited_by UUID NOT NULL REFERENCES utm_users(user_id),
       invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       accepted_at TIMESTAMP WITH TIME ZONE,
       
       UNIQUE(tenant_id, email)
   );
   
   CREATE INDEX idx_invitations_tenant ON utm_user_invitations(tenant_id);
   CREATE INDEX idx_invitations_email ON utm_user_invitations(email);
   CREATE INDEX idx_invitations_token ON utm_user_invitations(token);
   CREATE INDEX idx_invitations_status ON utm_user_invitations(status);
   ```

---

### ✅ Jueves 13 Feb - Migration Scripts (Parte 2)

**Tasks**:
1. [ ] **Script 012: Refactor utm_tenants** (3 horas)
   
   File: `supabase_migrations/012_v3.9_refactor_tenants.sql`
   ```sql
   -- CRITICAL: This must preserve all existing data
   
   -- Step 1: Rename old table
   ALTER TABLE utm_tenants RENAME TO utm_tenants_old;
   
   -- Step 2: Create new structure
   CREATE TABLE utm_tenants (
       tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       client_id UUID REFERENCES utm_clients(client_id),
       
       -- Organization
       org_name VARCHAR(255) NOT NULL,
       
       -- Tier (for future S/M/L pricing)
       tier VARCHAR(20) DEFAULT 'STANDARD',
       CHECK (tier IN ('STARTER', 'STANDARD', 'PREMIUM')),
       
       -- Status
       is_active BOOLEAN DEFAULT TRUE,
       
       -- Audit
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   
   -- Step 3: Migrate data (in 015_data_migration.sql)
   -- This script just creates structure
   ```

2. [ ] **Script 013-014: Update Projects & Locks** (2 horas)
   
   File: `supabase_migrations/013_v3.9_update_projects.sql`
   ```sql
   -- Add user tracking to projects
   ALTER TABLE utm_projects
   ADD COLUMN created_by_user_id UUID REFERENCES utm_users(user_id);
   
   CREATE INDEX idx_projects_created_by ON utm_projects(created_by_user_id);
   
   COMMENT ON COLUMN utm_projects.created_by_user_id IS 'v3.9: Track which user created project';
   ```
   
   File: `supabase_migrations/014_v3.9_update_process_locks.sql`
   ```sql
   -- Track user who locked
   ALTER TABLE utm_process_locks
   ADD COLUMN locked_by_user_email VARCHAR(255);
   
   CREATE INDEX idx_locks_user_email ON utm_process_locks(locked_by_user_email);
   ```

---

### ✅ Viernes 14 Feb - Migration Scripts (Parte 3)

**Tasks**:
1. [ ] **Script 015: Data Migration** (4 horas) **CRÍTICO**
   
   File: `supabase_migrations/015_v3.9_data_migration.sql`
   ```sql
   -- CRITICAL: This script migrates existing data
   -- Must be idempotent and transaction-safe
   
   BEGIN;
   
   -- Migrate tenants (create organizations from users)
   INSERT INTO utm_tenants (tenant_id, client_id, org_name, tier, created_at)
   SELECT 
       tenant_id, 
       client_id, 
       COALESCE(username, 'Organization') AS org_name,
       CASE 
           WHEN role = 'ADMIN' THEN 'PREMIUM'
           ELSE 'STANDARD'
       END AS tier,
       created_at
   FROM utm_tenants_old
   ON CONFLICT (tenant_id) DO NOTHING;
   
   -- Migrate users (create first user per tenant)
   INSERT INTO utm_users (
       user_id, 
       tenant_id, 
       email, 
       username, 
       password_hash_bcrypt, 
       role, 
       is_active,
       created_at
   )
   SELECT 
       tenant_id AS user_id, -- Keep same UUID for backward compat
       tenant_id,
       COALESCE(username || '@legacy.local', 'admin@legacy.local') AS email,
       username,
       COALESCE(password_hash_bcrypt, password_hash) AS password_hash_bcrypt,
       'ADMIN' AS role, -- All legacy users become ADMIN
       COALESCE(is_active, TRUE) AS is_active,
       created_at
   FROM utm_tenants_old
   ON CONFLICT (user_id) DO NOTHING;
   
   -- Update projects to reference first user
   UPDATE utm_projects p
   SET created_by_user_id = (
       SELECT user_id 
       FROM utm_users u 
       WHERE u.tenant_id = p.tenant_id 
       ORDER BY created_at ASC 
       LIMIT 1
   )
   WHERE created_by_user_id IS NULL;
   
   -- Verify counts match
   DO $$
   DECLARE
       old_count INTEGER;
       new_count INTEGER;
   BEGIN
       SELECT count(*) INTO old_count FROM utm_tenants_old;
       SELECT count(*) INTO new_count FROM utm_tenants;
       
       IF old_count != new_count THEN
           RAISE EXCEPTION 'Migration failed: tenant count mismatch (old=%, new=%)', old_count, new_count;
       END IF;
       
       RAISE NOTICE 'Migration successful: % tenants migrated', new_count;
   END $$;
   
   COMMIT;
   ```

2. [ ] **Script 016: RLS Policies** (2 horas)
   
   File: `supabase_migrations/016_v3.9_rls_policies.sql`
   ```sql
   -- Enable RLS
   ALTER TABLE utm_users ENABLE ROW LEVEL SECURITY;
   
   -- Users can view other users in their tenant
   CREATE POLICY "tenant_user_isolation" ON utm_users
       FOR SELECT
       USING (tenant_id = current_setting('app.current_tenant', TRUE)::uuid);
   
   -- Only admins can manage users
   CREATE POLICY "admin_manage_users" ON utm_users
       FOR ALL
       USING (
           EXISTS (
               SELECT 1 FROM utm_users 
               WHERE user_id = current_setting('app.current_user', TRUE)::uuid 
               AND role = 'ADMIN'
               AND tenant_id = utm_users.tenant_id
           )
       );
   
   -- Invitations
   ALTER TABLE utm_user_invitations ENABLE ROW LEVEL SECURITY;
   
   CREATE POLICY "tenant_invitation_isolation" ON utm_user_invitations
       FOR SELECT
       USING (tenant_id = current_setting('app.current_tenant', TRUE)::uuid);
   ```

3. [ ] **Test ALL scripts on staging** (2 horas)
   ```powershell
   # Run each script
   psql $STAGING_DB_URL -f supabase_migrations/010_v3.9_create_users_table.sql
   psql $STAGING_DB_URL -f supabase_migrations/011_v3.9_create_invitations_table.sql
   psql $STAGING_DB_URL -f supabase_migrations/012_v3.9_refactor_tenants.sql
   psql $STAGING_DB_URL -f supabase_migrations/013_v3.9_update_projects.sql
   psql $STAGING_DB_URL -f supabase_migrations/014_v3.9_update_process_locks.sql
   psql $STAGING_DB_URL -f supabase_migrations/015_v3.9_data_migration.sql
   psql $STAGING_DB_URL -f supabase_migrations/016_v3.9_rls_policies.sql
   
   # Verify
   psql $STAGING_DB_URL -c "SELECT count(*) FROM utm_users;"
   psql $STAGING_DB_URL -c "SELECT count(*) FROM utm_tenants;"
   psql $STAGING_DB_URL -c "SELECT * FROM utm_users LIMIT 5;"
   ```

---

### ✅ Sábado-Domingo 15-16 Feb - Preparación Final

**Tasks**:
1. [ ] **Rollback Scripts** (2 horas)
   
   File: `supabase_migrations/ROLLBACK_v3.9.sql`
   ```sql
   -- EMERGENCY ROLLBACK if migration fails
   BEGIN;
   
   -- Drop new tables
   DROP TABLE IF EXISTS utm_user_invitations CASCADE;
   DROP TABLE IF EXISTS utm_users CASCADE;
   DROP TABLE IF EXISTS utm_tenants CASCADE;
   
   -- Restore old table
   ALTER TABLE utm_tenants_old RENAME TO utm_tenants;
   
   -- Remove columns from projects
   ALTER TABLE utm_projects DROP COLUMN IF EXISTS created_by_user_id;
   ALTER TABLE utm_process_locks DROP COLUMN IF EXISTS locked_by_user_email;
   
   COMMIT;
   ```

2. [ ] **Kickoff Meeting Agenda** (1 hora)
   - Review plan
   - Team roles
   - Communication channels
   - Daily standup schedule

3. [ ] **Create Jira/Linear Tickets** (2 horas)
   - Epic: v3.9 Multi-User Foundation
   - Stories for each week
   - Subtasks for each script/endpoint/component

---

## 📅 Semana 1 (Feb 17-23): Database Migration

### Lunes 17 Feb - KICKOFF 🚀

**Morning (9am-12pm)**:
- [ ] Kickoff meeting (2 horas)
- [ ] Review migration scripts (todos)
- [ ] Assign tasks

**Afternoon (2pm-6pm)**:
- [ ] Backend: Review RLS policies
- [ ] Backend: Setup feature flags
- [ ] DevOps: Prepare rollback procedure

---

### Martes 18 Feb - Migration Testing

**Backend Team**:
- [ ] Run migrations on LOCAL dev DB (cada dev)
- [ ] Verify data integrity
- [ ] Test rollback procedure
- [ ] Document any issues

**Frontend Team**:
- [ ] Start AuthContext changes (preparar para user_id)
- [ ] Design Team page layout

---

### Miércoles 19 Feb - Staging Migration

**DevOps + Backend**:
- [ ] **Staging Migration** (evento coordinado)
  ```powershell
  # Backup staging primero
  pg_dump $STAGING_DB_URL > staging_pre_migration_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql
  
  # Run migrations
  # (ejecutar scripts 010-016)
  
  # Verify
  # (queries de verificación)
  
  # Test login
  # Test API endpoints
  ```

- [ ] Smoke tests en staging
- [ ] Verify backward compatibility

---

### Jueves 20 Feb - Backend API Skeleton

**Backend Team**:
- [ ] Create `apps/api/routers/users.py`
  ```python
  from fastapi import APIRouter, Depends, HTTPException
  from typing import List
  
  router = APIRouter(prefix="/auth/users", tags=["users"])
  
  @router.post("/invite")
  async def invite_user(payload: dict):
      # TODO: Implement
      pass
  
  @router.post("/accept-invite")
  async def accept_invite(token: str):
      # TODO: Implement
      pass
  
  @router.get("")
  async def list_users():
      # TODO: Implement
      pass
  
  @router.delete("/{user_id}")
  async def remove_user(user_id: str):
      # TODO: Implement
      pass
  
  @router.get("/me")
  async def get_current_user():
      # TODO: Implement
      pass
  
  @router.patch("/me/change-password")
  async def change_password(payload: dict):
      # TODO: Implement
      pass
  ```

---

### Viernes 21 Feb - Week 1 Review

**Team**:
- [ ] Demo: Migration successfull
- [ ] Code review: API skeleton
- [ ] Retrospective
- [ ] Plan week 2

---

## 📅 Semana 2 (Feb 24 - Mar 2): Backend Implementation

### Daily Tasks

**Backend**:
- Implementar 6 endpoints completos
- Permission service
- Update dependencies.py
- Unit tests

**Frontend**:
- AuthContext updates
- Team page scaffold

**QA**:
- Test plans
- Postman collections

---

## 📅 Semana 3 (Mar 3-9): Frontend Implementation

**Frontend**:
- Team page completo
- Invite modal
- Role badges
- Integration con backend

---

## 📅 Semana 4 (Mar 10-16): Testing & Launch

**Todo el equipo**:
- Integration tests
- Backward compat tests
- Beta rollout
- Production deploy

---

## 🚨 Checklist Pre-Producción

Antes de deploy a PROD:

- [ ] Staging funcionando perfecto (1 semana sin issues)
- [ ] Todos los tests pasan
- [ ] Backward compatibility verificado
- [ ] Rollback plan probado
- [ ] Backup de producción creado
- [ ] Comunicación a usuarios preparada
- [ ] Monitoring setup
- [ ] On-call schedule definido

---

## 📞 Contacts & Resources

**Team**:
- Tech Lead: [NOMBRE]
- Backend: [NOMBRE]
- Frontend: [NOMBRE]
- QA: [NOMBRE]
- DevOps: [NOMBRE]

**Channels**:
- Slack: #v3-9-multi-user
- Jira: [LINK]
- Docs: `/docs/planning/`

**Databases**:
- Local: `postgresql://localhost:5432/legacy2lake_dev`
- Staging: `$STAGING_DB_URL`
- Production: `$PROD_DB_URL` (DO NOT TOUCH until week 4)

---

## ✅ Ready to Start?

1. [ ] Plan revisado y aprobado ✅
2. [ ] Team asignado ✅
3. [ ] Staging preparado ✅
4. [ ] Scripts skeleton creados ✅
5. [ ] Kickoff agendado (Feb 17, 9am) ✅

**LET'S GO! 🚀**
