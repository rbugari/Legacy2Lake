# Legacy2Lake - Release Plan SIMPLIFICADO (v3.9 → v4.0)
## Roadmap Pragmático: Multi-Usuario Simple → AI

**Created**: 2026-02-09  
**Author**: Development Team  
**Status**: ✅ **COMPLETADO** - Feb 13, 2026  
**Timeline**: Feb 2026 - Q3 2026

---

## 🎉 v3.9 GA RELEASE COMPLETE

> **v3.9 GA fue liberado exitosamente el 13 de Febrero de 2026.**
> 
> **Multi-User Foundation** (Feb 10) + **Visualization Integration** (Feb 13) = $240K Value Delivered  
> **Features COMPLETE**: 4-role system, Project access control, Platform Admin Dashboard, 10 visualization endpoints, 4 dashboards (Triage, Drafting, Refinement, Certification)  
> **Next**: v4.0 "Zero-Hardcode Core" (~4 weeks, target late March 2026)

---

## 🎯 FILOSOFÍA: Keep It Simple

> **"No necesitamos un Slack, solo necesitamos que varios usuarios accedan a los mismos proyectos con roles básicos."**

### Visión Simplificada
- ❌ NO somos una plataforma de colaboración compleja
- ✅ SÍ permitimos que equipos pequeños trabajen juntos
- ❌ NO necesitamos comentarios, notificaciones, websockets (por ahora)
- ✅ SÍ necesitamos control simple: Admin vs Colaborador vs Viewer

---

## 📋 RELEASES SIMPLIFICADOS

```
FEB 2026         MAR-APR 2026              Q3 2026
├────────────────┼─────────────────────────┼────────
 v3.8 ✅          v3.9 SIMPLE               v4.0
 CURRENT         Multi-User Básico      AI Revolution
                 (4 semanas)            (8-10 semanas)
```

**Timeline total**: 12-14 semanas (3.5 meses, no 4)

---

# v3.9 - Multi-Usuario Simplificado (ÚNICO Release antes de v4.0)

**Theme**: "Equipos Pequeños, Control Simple"  
**Duration**: 4 semanas  
**Target**: Marzo 2026  
**Priority**: 🔴 CRITICAL

## 🎯 Scope Reducido

### ✅ Backward Compatibility TOTAL

**CRÍTICO**: Si un tenant tiene 1 solo usuario ADMIN (como ahora), **funciona EXACTAMENTE igual** que v3.8.

```
Tenant con 1 usuario:
- Login igual que antes
- UI igual que antes  
- No ve botón "Team" (porque está solo)
- Proyectos funcionan igual
- Zero cambios en UX
```

**La diferencia solo aparece cuando OPCIONALMENTE invitan más usuarios.**

### Lo Que SÍ Hacemos ✅

**1. Usuarios Múltiples OPCIONALES por Tenant**
```
MÍNIMO: 1 Tenant = 1 Usuario (como ahora, funciona igual)
MÁXIMO: 1 Tenant = N Usuarios (nuevo, opcional)
```

**2. Solo 3 Roles (NO 5)**
```
ADMIN        - Puede todo (invitar, crear, editar, ejecutar, eliminar)
COLLABORATOR - Puede crear y editar proyectos, ejecutar stages
VIEWER       - Solo puede ver proyectos y descargar reportes
```

**3. Invitaciones Simples**
- Admin invita por email
- Usuario acepta y crea password
- Ya puede entrar

**4. Proyectos Compartidos**
- Todos los usuarios del tenant ven TODOS los proyectos
- No hay "compartir proyecto X con usuario Y" (simplificado)
- Control solo por rol: ADMIN puede editar, VIEWER solo ve

### Lo Que NO Hacemos ❌ (Postponed)

- ❌ Permisos granulares a nivel de proyecto (v3.10 eliminada)
- ❌ Roles personalizados (solo 3 fijos)
- ❌ Comentarios y @menciones (v3.11 eliminada)
- ❌ Notificaciones push/email (v3.11 eliminada)
- ❌ WebSocket real-time (v3.11 eliminada)
- ❌ Task management / Kanban (v3.11 eliminada)
- ❌ Audit logs detallados (solo básico)
- ❌ Compartir cross-tenant

---

## 📊 Database Changes (Simplificado)

### 1. Nueva Tabla: `utm_users`
```sql
CREATE TABLE utm_users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    
    -- Identity
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL,
    password_hash_bcrypt TEXT NOT NULL,
    
    -- Role (SOLO 3 opciones)
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
```

### 2. Refactor: `utm_tenants` → Organization
```sql
ALTER TABLE utm_tenants RENAME TO utm_tenants_old;

CREATE TABLE utm_tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES utm_clients(client_id),
    
    -- Organization
    org_name VARCHAR(255) NOT NULL,
    
    -- Simple tier (para futuro S/M/L)
    tier VARCHAR(20) DEFAULT 'STANDARD', -- STARTER, STANDARD, PREMIUM
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Migrate: Create organization from old tenant
INSERT INTO utm_tenants (tenant_id, client_id, org_name, tier, created_at)
SELECT 
    tenant_id, 
    client_id, 
    COALESCE(username, 'Organization'),
    CASE WHEN role = 'ADMIN' THEN 'PREMIUM' ELSE 'STANDARD' END,
    created_at
FROM utm_tenants_old;

-- Migrate: Create first user per tenant
INSERT INTO utm_users (user_id, tenant_id, email, username, password_hash_bcrypt, role, created_at)
SELECT 
    tenant_id AS user_id, -- Keep UUID for backward compat
    tenant_id,
    COALESCE(username || '@legacy.local', 'admin@legacy.local'),
    username,
    password_hash_bcrypt,
    'ADMIN', -- All legacy users become ADMIN
    created_at
FROM utm_tenants_old;
```

### 3. Update: `utm_projects`
```sql
-- Track who created the project
ALTER TABLE utm_projects
ADD COLUMN created_by_user_id UUID REFERENCES utm_users(user_id);

-- Migrate existing
UPDATE utm_projects p
SET created_by_user_id = (
    SELECT user_id FROM utm_users u 
    WHERE u.tenant_id = p.tenant_id 
    LIMIT 1
);

-- No need for "shared_with" - everyone in tenant sees everything
```

### 4. Update: `utm_process_locks`
```sql
-- Track which user locked
ALTER TABLE utm_process_locks
ADD COLUMN locked_by_user_email VARCHAR(255);
```

### 5. Nueva Tabla: `utm_user_invitations` (Simplificada)
```sql
CREATE TABLE utm_user_invitations (
    invitation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'VIEWER',
    
    -- Token for acceptance
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, ACCEPTED, EXPIRED
    invited_by UUID NOT NULL REFERENCES utm_users(user_id),
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(tenant_id, email)
);
```

**Total nuevas tablas**: 2 (utm_users, utm_user_invitations)  
**Total refactors**: 1 (utm_tenants)  
**Total updates**: 2 (utm_projects, utm_process_locks)

---

## 🔧 Backend Changes (Simplificado)

### Nuevos Endpoints (Solo 6, no 15)

```python
# User Management
POST   /auth/users/invite          # Admin invita usuario
POST   /auth/users/accept-invite   # Usuario acepta invitación
GET    /auth/users                 # Lista usuarios del tenant
DELETE /auth/users/{user_id}       # Admin remueve usuario

# Profile
GET    /auth/me                    # Ver mi perfil
PATCH  /auth/me/change-password    # Cambiar mi password
```

### Permission Logic (Super Simple)

```python
# apps/api/services/permission_service.py

PERMISSIONS = {
    "ADMIN": ["*"],  # Todo
    "COLLABORATOR": [
        "projects.view",
        "projects.create", 
        "projects.edit",
        "stages.execute",
        "reports.download"
    ],
    "VIEWER": [
        "projects.view",
        "reports.download"
    ]
}

def can_do(user_role: str, action: str) -> bool:
    """Simple permission check."""
    perms = PERMISSIONS.get(user_role, [])
    return "*" in perms or action in perms
```

### Updated Dependencies

```python
# apps/api/routers/dependencies.py

async def get_identity(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),  # NEW
) -> dict:
    return {
        "tenant_id": x_tenant_id,
        "user_id": x_user_id,  # NEW
        "role": request.headers.get("X-Role", "VIEWER")
    }

# Simple role guards
async def require_admin(identity: dict = Depends(get_identity)):
    if identity.get("role") != "ADMIN":
        raise HTTPException(403, "Admin required")
    return identity

async def require_collaborator_or_admin(identity: dict = Depends(get_identity)):
    if identity.get("role") not in ["ADMIN", "COLLABORATOR"]:
        raise HTTPException(403, "Collaborator or Admin required")
    return identity
```

---

## 🎨 Frontend Changes (Simplificado)

### 1. New Page: Team (`/team`) - **CONDITIONAL**
```typescript
// SIMPLE team page - ONLY visible for:
// - Tenants with 2+ users, OR
// - User with ADMIN role (to invite others)

export default function TeamPage() {
  const { user, userCount } = useAuth();
  
  // Don't show for single-user tenants (backward compat)
  if (userCount === 1 && user.role !== 'ADMIN') {
    return <Navigate to="/dashboard" />;
  }
  
  // Show list of users
  // Admin can invite + remove
  // That's it, no fancy features
}
```

### 2. Updated Login Flow - **BACKWARD COMPATIBLE**
```typescript
// Now returns user_id, BUT keeps same flow
const response = await fetch("/api/auth/login", {
  method: "POST",
  body: JSON.stringify({ email, password })
});

const data = await response.json();
// Store user_id too (new)
localStorage.setItem("x_user_id", data.user_id);

// Everything else stays the same
localStorage.setItem("x_tenant_id", data.tenant_id);
localStorage.setItem("x_role", data.role);
```

### 3. Navigation Menu - **CONDITIONAL**
```typescript
// Only show "Team" link if:
// - Tenant has 2+ users, OR
// - User is ADMIN (can invite)

{(userCount > 1 || user.role === 'ADMIN') && (
  <NavLink to="/team">Team</NavLink>
)}

// Single-user tenants NEVER see this button
// = Zero UI change for existing users ✅
```

### 4. Role Badge Component - **OPTIONAL**
```typescript
// Simple badge showing role
// ONLY shown if tenant has 2+ users
<RoleBadge role={user.role} />

// ADMIN = red badge
// COLLABORATOR = blue badge  
// VIEWER = gray badge
```

**Total new pages**: 1 (Team, conditional)  
**Total new components**: 3 (TeamMemberCard, InviteModal, RoleBadge)  
**UI changes for single-user tenants**: **ZERO** ✅

---

## 🚀 Implementation Plan (4 Semanas)

### Week 1: Database (Feb 17-23)
- [ ] Write migration scripts
- [ ] Test on staging
- [ ] **Verify backward compat**: 1-user tenants work exactly as before
- [ ] Verify data integrity

### Week 2: Backend (Feb 24 - Mar 2)
- [ ] 6 new endpoints
- [ ] Permission service
- [ ] Update dependencies
- [ ] **Backward compat**: Single-user tenants skip team features
- [ ] Unit tests

### Week 3: Frontend (Mar 3-9)
- [ ] Team page (conditional: only show if user_count > 1 OR role=ADMIN)
- [ ] Invite modal
- [ ] Role badges
- [ ] Update auth flow
- [ ] **Critical**: No UI changes for single-user tenants

### Week 4: Testing & Launch (Mar 10-16)
- [ ] Integration tests
- [ ] **Backward compat test**: Existing single-user flows unchanged
- [ ] Security audit
- [ ] Beta with 2-3 tenants
- [ ] Production deploy
- [ ] Monitor for 1 week

**Total: 4 weeks, no more.**

### Nuevas Features (Multi-User)
- [ ] Admin can invite users by email
- [ ] Users receive invite link, set password
- [ ] ADMIN can create/edit/delete any project
- [ ] COLLABORATOR can create/edit projects, execute stages
- [ ] VIEWER can only view and download reports
- [ ] All users in tenant see all projects (no fine-grained sharing)
- [ ] Process locks track which user locked
- [ ] Login works with user_id
- [ ] Team page shows all users
- [ ] Admin can remove users

### **Backward Compatibility (CRÍTICO)** ⭐
- [ ] **Existing tenants with 1 user work EXACTLY as before**
- [ ] **Login flow unchanged for single-user tenants**
- [ ] **UI identical for single-user tenants** (no "Team" button visible)
- [ ] **Projects, stages, reports work identically**
- [ ] **Zero disruption to current users**
- [ ] **Migration is transparent** (users don't notice anything different)e all projects (no fine-grained sharing)
- [ ] Process locks track which user locked
- [ ] Login works with user_id
- [ ] Team page shows all users
- [ ] Admin can remove users

**That's it. No more complexity.**

---

## 🔐 Security (Básico)

### RLS Policies (Simple)
```sql
-- Users see other users in their tenant
CREATE POLICY "tenant_user_isolation" ON utm_users
    FOR SELECT USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- Only admins can modify users
CREATE POLICY "admin_manage_users" ON utm_users
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM utm_users 
            WHERE user_id = current_setting('app.current_user')::uuid 
            AND role = 'ADMIN'
        )
    );
```

### Role Checks (Every Endpoint)
```python
@router.post("/projects")
async def create_project(
    payload: ProjectCreate,
    identity: dict = Depends(require_collaborator_or_admin)  # Simple guard
):
    pass
```

---

# v4.0 - AI Revolution (Sin cambios respecto a plan original)

**Theme**: "Zero-Hardcode, Prompt-Driven"  
**Duration**: 8-10 semanas  
**Target**: Q3 2026

Todo lo especificado en [future_v4.0.md](future_v4.0.md) sigue igual:
- Eliminar hardcoded templates
- Prompts en database
- Self-learning agents
- Deep triage

**Pero ahora con soporte multi-usuario desde v3.9.**

---

## 💼 Business: Modelos de Consumo (Futuro Post-v4.0)

### Tiers de Pricing (Para implementar DESPUÉS de v4.0)

```
┌─────────────────────────────────────────────────────────┐
│  STARTER (S)     │  STANDARD (M)    │  PREMIUM (L)     │
├──────────────────┼──────────────────┼──────────────────┤
│  $49/mes         │  $149/mes        │  $499/mes        │
│  1 usuario ADMIN │  3 usuarios      │  10 usuarios     │
│  5 proyectos     │  20 proyectos    │  Unlimited       │
│  GPT-4o-mini     │  GPT-4o          │  Claude Opus     │
│  Email support   │  Chat support    │  Dedicated CSM   │
└──────────────────┴──────────────────┴──────────────────┘
```

**Implementación**:
- Campo `tier` ya existe en `utm_tenants`
- Agregar límites en API:
  ```python
  if tenant.tier == 'STARTER' and user_count >= 1:
      raise HTTPException(402, "Upgrade to add more users")
  ```
- Portal de billing (Stripe integration)
- Usage tracking dashboard

**Timeline**: Post-v4.0 (Q4 2026 o después)

---

## 📊 Comparison: Plan Original vs Simplificado

| Aspecto | Plan Original | Plan Simplificado |
|---------|---------------|-------------------|
| **Releases antes v4.0** | 3 (v3.9, v3.10, v3.11) | 1 (v3.9 solo) |
| **Tiempo total** | 16 semanas | 12-14 semanas |
| **Roles** | 5 (Owner/Admin/Manager/Analyst/Viewer) | 3 (Admin/Collaborator/Viewer) |
| **Permisos** | Granulares por proyecto | Por rol, tenant-wide |
| **Nuevas tablas DB** | 6 | 2 |
| **Nuevos endpoints** | 15+ | 6 |
| **Features UI** | Team, Roles, Sharing, Comments, Notifications | Solo Team básico |
| **Comentarios** | ✅ | ❌ Postponed |
| **Notificaciones** | ✅ | ❌ Postponed |
| **WebSocket** | ✅ | ❌ Postponed |
| **Custom Roles** | ✅ | ❌ Postponed |
| **Audit Logs** | Detallados | Básicos |
| **Complejidad** | 🔴 Alta | 🟢 Baja |

---

## 🎯 Why This Works Better

### Ventajas del Plan Simplificado
1. ✅ **Faster to Market**: 4 semanas vs 10 semanas
2. ✅ **Less Risk**: Menos superficie de ataque, menos bugs
3. ✅ **Easier to Test**: Menos casos edge
4. ✅ **Sufficient for Most Teams**: 2-5 usuarios es lo típico
5. ✅ **Can Add Later**: Si necesitamos comments/notifications, lo agregamos en v4.x
6. ✅ **Focus on v4.0**: Más tiempo para la transformación de AI

### Lo Que Cubre
- ✅ Equipos pequeños (2-5 personas)
- ✅ Control de acceso básico (quien puede editar vs solo ver)
- ✅ Invitaciones simples
- ✅ Preparado para pricing tiers (S/M/L)
- ✅ Suficiente para enterprise pequeño/mediano

### Lo Que NO Cubre (y está OK)
- ❌ Equipos grandes (20+ personas) → No es nuestro target ahora
- ❌ Colaboración real-time → No lo necesitamos
- ❌ Workflows complejos → YAGNI (You Ain't Gonna Need It)

---

## 📋 Next Steps

### Esta Semana (Feb 10-16):
1. ✅ Aprobar este plan simplificado
2. ✅ Crear tareas en Jira (solo 4 semanas, no 16)
3. ✅ Preparar staging

### Semana 1 (Feb 17-23):
1. 🚀 Kickoff
2. ✅ Migration scripts
3. ✅ Test migrations

### Weeks 2-4:
1. ✅ Build feature
2. ✅ Test
3. ✅ Deploy

### April Onwards:
1. 🚀 **START v4.0 (AI Revolution)**
2. Monitor v3.9 usage
3. Decide if we need v3.10 features later

---

## ✅ Definition of Done (v3.9) - **ALL COMPLETE**

- [x] Multiple users can login to same tenant ✅
- [x] MANAGER can create users directly (invite flow optional) ✅
- [x] Roles enforced: ADMIN/MANAGER = full, COLLABORATOR = create/edit, VIEWER = read-only ✅
- [x] Project-level access control via utm_project_members ✅
- [x] User Management UI in Tenant Console (`/settings`) ✅
- [x] Project Access UI for MANAGER ✅
- [x] Platform Admin dashboard with All Users view ✅
- [x] Password reset functionality ✅
- [x] Ghost Mode impersonation for troubleshooting ✅
- [x] Zero data loss in migration ✅
- [x] API response time < 200ms ✅
- [x] Documentation updated ✅

**v3.9 SHIPPED - Feb 10, 2026** 🚀

---

## 📋 Pending for Future (Not Critical)

- [ ] Email invitation workflow (currently users created directly)
- [ ] Email notifications on password reset
- [ ] Self-service password recovery

---

*"Perfection is the enemy of done. Ship the simple version first."*
