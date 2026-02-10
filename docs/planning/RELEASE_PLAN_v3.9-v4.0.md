# Legacy2Lake - Release Plan (v3.9 → v4.0)
## Roadmap to True Multi-User SaaS

**Created**: 2026-02-09  
**Author**: Development Team  
**Status**: DRAFT - Strategic Planning  
**Timeline**: Feb 2026 - Q3 2026

---

## 🎯 STRATEGIC VISION

### Current State (v3.8)
- ✅ Multi-tenant isolation (1 Client = N Tenants)
- ✅ Basic RBAC (ADMIN/USER roles)
- ✅ Process locking and governance
- ❌ **Limitation**: 1 Tenant = 1 User (No true team collaboration)

### Target State (v4.0)
- ✅ True SaaS: 1 Organization = N Teams = N Users
- ✅ Granular RBAC (Owner, Manager, Analyst, Viewer roles)
- ✅ Resource-level permissions (who can do what)
- ✅ Intelligent, prompt-driven AI generation
- ✅ Self-learning system

### Path Forward
```
v3.8 (NOW) → v3.9 (Multi-User) → v3.10 (RBAC) → v3.11 (Collaboration) → v4.0 (AI Revolution)
    ↓             ↓                  ↓                 ↓                      ↓
 Single User   N Users/Tenant    Permissions      Workflows           Autonomous AI
```

---

## 📋 RELEASE BREAKDOWN

---

# v3.9 - Multi-User Foundation (The Team Enablement Release)

**Theme**: "El Camino Suave al SaaS Multi-Usuario"  
**Duration**: 3-4 weeks  
**Target**: Early March 2026  
**Priority**: 🔴 CRITICAL - Fundamental Architecture Change

## 🎯 Core Objective

> **Enable multiple users to collaborate within a single tenant/organization, sharing projects and resources while maintaining clear ownership boundaries.**

### Current Pain Points
- ❌ Each tenant = 1 user only (1:1 mapping)
- ❌ No team collaboration within same organization
- ❌ Cannot share projects between team members
- ❌ No way to delegate or assign work
- ❌ Scaling requires creating separate tenants (poor UX)

### Solution Overview
```
BEFORE (v3.8):
┌──────────────┐
│ utm_tenants  │  (tenant_id = user, no separation)
├──────────────┤
│ tenant_id    │ <- Also acts as user_id
│ client_id    │
│ username     │
│ password     │
│ role         │
└──────────────┘

AFTER (v3.9):
┌──────────────┐         ┌──────────────┐
│ utm_tenants  │ 1 ----N │ utm_users    │
├──────────────┤         ├──────────────┤
│ tenant_id    │         │ user_id      │
│ client_id    │         │ tenant_id FK │
│ org_name     │         │ email        │
│ tier         │         │ password     │
│ settings     │         │ role         │
└──────────────┘         │ is_active    │
                         └──────────────┘
```

---

## 📊 Database Changes

### 1. New Table: `utm_users`
Separate user identity from tenant/organization concept.

```sql
CREATE TABLE utm_users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL,
    password_hash_bcrypt TEXT NOT NULL,
    
    -- Role within the tenant
    role VARCHAR(50) NOT NULL DEFAULT 'VIEWER',
    -- Options: OWNER, ADMIN, MANAGER, ANALYST, VIEWER
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    display_name VARCHAR(255),
    avatar_url TEXT,
    phone VARCHAR(50),
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES utm_users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(tenant_id, email)
);

-- Indexes
CREATE INDEX idx_users_tenant ON utm_users(tenant_id);
CREATE INDEX idx_users_email ON utm_users(email);
CREATE INDEX idx_users_role ON utm_users(role);

-- RLS (Row Level Security)
ALTER TABLE utm_users ENABLE ROW LEVEL SECURITY;

-- Users can view other users in their tenant
CREATE POLICY "Users can view tenant members" ON utm_users
    FOR SELECT
    USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- Only admins can insert/update/delete users
CREATE POLICY "Admins manage users" ON utm_users
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM utm_users
            WHERE user_id = current_setting('app.current_user')::uuid
            AND role IN ('OWNER', 'ADMIN')
            AND tenant_id = utm_users.tenant_id
        )
    );
```

### 2. Refactor: `utm_tenants` 
Transform from user identity to organization identity.

```sql
-- Migration Script
ALTER TABLE utm_tenants RENAME TO utm_tenants_old;

CREATE TABLE utm_tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES utm_clients(client_id),
    
    -- Organization Info
    org_name VARCHAR(255) NOT NULL,
    org_slug VARCHAR(100) UNIQUE NOT NULL, -- URL-friendly identifier
    
    -- Subscription/Tier
    tier VARCHAR(50) DEFAULT 'FREE', -- FREE, STARTER, PROFESSIONAL, ENTERPRISE
    max_users INTEGER DEFAULT 5,
    max_projects INTEGER DEFAULT 10,
    
    -- Settings
    settings JSONB DEFAULT '{}',
    -- Example: {"timezone": "America/New_York", "locale": "en-US", "branding": {...}}
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Migrate existing data (1 tenant per legacy user)
INSERT INTO utm_tenants (tenant_id, client_id, org_name, org_slug, tier, created_at)
SELECT 
    tenant_id, 
    client_id, 
    COALESCE(username, 'Organization'), 
    LOWER(REGEXP_REPLACE(username, '[^a-zA-Z0-9]', '-', 'g')),
    CASE WHEN role = 'ADMIN' THEN 'ENTERPRISE' ELSE 'FREE' END,
    created_at
FROM utm_tenants_old;

-- Migrate users
INSERT INTO utm_users (user_id, tenant_id, email, username, password_hash_bcrypt, role, is_active, created_at)
SELECT 
    tenant_id AS user_id, -- Keep same UUID for backward compat
    tenant_id,
    COALESCE(username || '@legacy.local', 'user@legacy.local'),
    username,
    password_hash_bcrypt,
    CASE WHEN role = 'ADMIN' THEN 'OWNER' ELSE 'ANALYST' END,
    is_active,
    created_at
FROM utm_tenants_old;

-- Drop old table after verification
-- DROP TABLE utm_tenants_old;
```

### 3. Update: `utm_projects`
Add user-level tracking for project ownership.

```sql
ALTER TABLE utm_projects
ADD COLUMN owner_user_id UUID REFERENCES utm_users(user_id),
ADD COLUMN shared_with UUID[] DEFAULT '{}', -- Array of user_ids with access
ADD COLUMN created_by_user_id UUID REFERENCES utm_users(user_id);

-- Migrate existing projects to first user of tenant
UPDATE utm_projects p
SET owner_user_id = (
    SELECT user_id FROM utm_users u 
    WHERE u.tenant_id = p.tenant_id 
    ORDER BY created_at ASC 
    LIMIT 1
);
```

### 4. Update: `utm_process_locks`
Track user who locked the process, not just tenant.

```sql
ALTER TABLE utm_process_locks
ADD COLUMN locked_by_user_email VARCHAR(255),
ADD COLUMN locked_by_display_name VARCHAR(255);

-- Index
CREATE INDEX idx_locks_user_email ON utm_process_locks(locked_by_user_email);
```

### 5. New Table: `utm_user_invitations`
Manage pending invitations to join a tenant.

```sql
CREATE TABLE utm_user_invitations (
    invitation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'VIEWER',
    
    -- Token for secure acceptance
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Status
    status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, ACCEPTED, EXPIRED, REVOKED
    
    -- Who invited
    invited_by UUID NOT NULL REFERENCES utm_users(user_id),
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Acceptance tracking
    accepted_at TIMESTAMP WITH TIME ZONE,
    accepted_by_ip VARCHAR(45),
    
    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_invitations_tenant ON utm_user_invitations(tenant_id);
CREATE INDEX idx_invitations_email ON utm_user_invitations(email);
CREATE INDEX idx_invitations_token ON utm_user_invitations(token);
```

---

## 🔧 Backend Changes

### 1. Auth Router Updates (`apps/api/routers/auth.py`)

**New Endpoints:**
```python
# User Management
POST   /auth/users/invite          # Invite user to tenant
POST   /auth/users/accept-invite   # Accept invitation via token
GET    /auth/users                 # List users in tenant
GET    /auth/users/{user_id}       # Get user details
PATCH  /auth/users/{user_id}       # Update user (role, status)
DELETE /auth/users/{user_id}       # Remove user from tenant

# Profile
GET    /auth/me                    # Current user profile
PATCH  /auth/me                    # Update own profile
POST   /auth/me/change-password    # Change own password

# Organization (Tenant)
GET    /auth/organization          # Get tenant details
PATCH  /auth/organization          # Update tenant settings (admin only)
GET    /auth/organization/stats    # Usage stats (users, projects, etc.)
```

**Updated Endpoints:**
```python
POST /auth/login
# Response now includes:
{
    "success": true,
    "tenant_id": "uuid",
    "user_id": "uuid",        # NEW
    "email": "user@org.com",  # NEW
    "role": "MANAGER",
    "org_name": "Acme Corp",  # NEW
    "token": "jwt_token"      # NEW (JWT for stateless auth)
}
```

### 2. Dependencies Updates (`apps/api/routers/dependencies.py`)

```python
async def get_identity(
    request: Request,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),  # NEW
    x_client_id: Optional[str] = Header(None, alias="X-Client-ID"),
) -> dict:
    """
    Enhanced identity resolution with user-level tracking.
    """
    return {
        "tenant_id": x_tenant_id,
        "user_id": x_user_id,  # NEW
        "client_id": x_client_id,
        "role": request.headers.get("X-Role", "VIEWER")
    }

async def require_permission(permission: str):
    """
    Dependency to check user has specific permission.
    Example: Depends(require_permission("projects.create"))
    """
    async def _check(identity: dict = Depends(get_identity)):
        user_role = identity.get("role", "VIEWER")
        if not has_permission(user_role, permission):
            raise HTTPException(403, f"Permission denied: {permission}")
        return identity
    return _check

# Role-based dependencies
async def require_owner(identity: dict = Depends(get_identity)):
    if identity.get("role") != "OWNER":
        raise HTTPException(403, "Owner access required")
    return identity

async def require_admin_or_manager(identity: dict = Depends(get_identity)):
    if identity.get("role") not in ["OWNER", "ADMIN", "MANAGER"]:
        raise HTTPException(403, "Admin or Manager access required")
    return identity
```

### 3. Persistence Service Updates

```python
class SupabasePersistence:
    def __init__(self, tenant_id: str = None, user_id: str = None, client_id: str = None):
        self.tenant_id = tenant_id
        self.user_id = user_id  # NEW
        self.client_id = client_id
        # Set RLS context
        if tenant_id:
            self.client.rpc('set_tenant_context', {'tenant_id': tenant_id})
        if user_id:
            self.client.rpc('set_user_context', {'user_id': user_id})
    
    # User Management Methods
    async def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        pass
    
    async def list_tenant_users(self, tenant_id: str) -> List[Dict]:
        """List all users in a tenant."""
        pass
    
    async def invite_user(self, tenant_id: str, email: str, role: str, invited_by: str) -> Dict:
        """Create invitation for new user."""
        pass
    
    async def remove_user(self, user_id: str, removed_by: str) -> bool:
        """Remove user from tenant (soft delete)."""
        pass
```

### 4. New Service: `apps/api/services/permission_service.py`

```python
"""
Permission management and RBAC enforcement.
"""

# Permission Matrix
PERMISSIONS = {
    "OWNER": [
        "*"  # All permissions
    ],
    "ADMIN": [
        "users.view", "users.invite", "users.edit", "users.remove",
        "projects.view", "projects.create", "projects.edit", "projects.delete",
        "settings.view", "settings.edit",
        "vault.view", "vault.edit",
        "agents.view", "knowledge.view"
    ],
    "MANAGER": [
        "users.view", "users.invite",
        "projects.view", "projects.create", "projects.edit",
        "settings.view",
        "vault.view",
        "agents.view", "knowledge.view"
    ],
    "ANALYST": [
        "projects.view", "projects.create", "projects.edit_own",
        "agents.view", "knowledge.view"
    ],
    "VIEWER": [
        "projects.view",
        "agents.view", "knowledge.view"
    ]
}

def has_permission(role: str, permission: str) -> bool:
    """Check if role has permission."""
    role_perms = PERMISSIONS.get(role, [])
    return "*" in role_perms or permission in role_perms

def can_edit_project(user_role: str, user_id: str, project: Dict) -> bool:
    """Check if user can edit specific project."""
    # Owner/Admin/Manager can edit any
    if user_role in ["OWNER", "ADMIN", "MANAGER"]:
        return True
    
    # Analyst can edit if they created it
    if user_role == "ANALYST":
        return project.get("owner_user_id") == user_id
    
    return False
```

---

## 🎨 Frontend Changes

### 1. Auth Context Updates (`apps/web/app/context/AuthContext.tsx`)

```typescript
interface User {
  user_id: string;      // NEW
  email: string;        // NEW
  username: string;
  display_name: string; // NEW
  role: string;
  tenant_id: string;
  org_name: string;     // NEW
  client_id: string;
}

const login = async (email: string, password: string) => {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  
  // Store in localStorage
  localStorage.setItem("x_tenant_id", data.tenant_id);
  localStorage.setItem("x_user_id", data.user_id);  // NEW
  localStorage.setItem("auth_token", data.token);   // NEW
  
  setUser({
    user_id: data.user_id,
    email: data.email,
    username: data.username,
    display_name: data.display_name,
    role: data.role,
    tenant_id: data.tenant_id,
    org_name: data.org_name,
    client_id: data.client_id
  });
};
```

### 2. New Page: Team Management (`apps/web/app/team/page.tsx`)

```typescript
/**
 * Team Management Page
 * - List all users in the organization
 * - Invite new users
 * - Edit user roles
 * - Remove users
 */
export default function TeamPage() {
  const [users, setUsers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  
  // Features:
  // - User list with role badges
  // - Invite modal with email + role selector
  // - Edit role inline
  // - Remove confirmation modal
  // - Pending invitations list
  
  return (
    <div>
      <h1>Team Members</h1>
      <UserList users={users} />
      <InviteButton />
      <PendingInvitations invitations={invitations} />
    </div>
  );
}
```

### 3. Update: Project Creation

```typescript
// Add owner selection when creating project
const createProject = async (projectData) => {
  await fetch("/api/projects", {
    method: "POST",
    headers: {
      "X-Tenant-ID": user.tenant_id,
      "X-User-ID": user.user_id,  // NEW
      "X-Client-ID": user.client_id
    },
    body: JSON.stringify({
      ...projectData,
      owner_user_id: user.user_id  // NEW
    })
  });
};
```

### 4. New Components

- `TeamMemberCard.tsx` - User card with avatar, role, status
- `InviteUserModal.tsx` - Invitation form
- `RoleSelector.tsx` - Dropdown with role descriptions
- `UserPermissionBadge.tsx` - Visual permission indicator
- `ActivityFeed.tsx` - Timeline of team activities

---

## 🔐 Security & Permissions

### Role Hierarchy
```
OWNER (Owner de la organización)
  └─ Full control: billing, delete org, manage all

ADMIN (Administrador)
  └─ User management, settings, full project access

MANAGER (Gestor de Proyectos)
  └─ Create/edit projects, invite users (no delete users)

ANALYST (Analista)
  └─ Create own projects, edit own projects, view others

VIEWER (Solo Lectura)
  └─ View projects, view reports (no modifications)
```

### Permission Guards

**Backend (FastAPI):**
```python
@router.post("/projects")
async def create_project(
    payload: ProjectCreate,
    identity: dict = Depends(require_permission("projects.create"))
):
    # Only OWNER/ADMIN/MANAGER/ANALYST can create
    pass
```

**Frontend (React):**
```typescript
{hasPermission(user.role, "users.invite") && (
  <InviteButton />
)}
```

---

## 📋 Migration Strategy

### Phase 1: Database Migration (CRITICAL ⚠️)
```bash
# 1. Backup production database
pg_dump $DATABASE_URL > backup_pre_v3.9.sql

# 2. Run migration in transaction
psql $DATABASE_URL << EOF
BEGIN;
  -- Create new tables
  \i migrations/v3.9_create_users_table.sql
  
  -- Migrate data
  \i migrations/v3.9_migrate_tenants_to_users.sql
  
  -- Verify data integrity
  SELECT count(*) FROM utm_users;
  SELECT count(*) FROM utm_tenants;
  
  -- If everything looks good:
  COMMIT;
  -- Otherwise:
  -- ROLLBACK;
EOF
```

### Phase 2: Backend Deploy
1. Deploy new API with backward compatibility
2. Monitor error rates
3. Gradual rollout with feature flags

### Phase 3: Frontend Deploy
1. Update headers to include X-User-ID
2. New Team Management page (hidden behind flag)
3. Enable feature flag for testing tenants
4. Full rollout after 48h of monitoring

### Phase 4: Cleanup Legacy
1. Remove deprecated utm_tenants_old table
2. Clean up old single-user assumptions in code
3. Update documentation

---

## ✅ Acceptance Criteria

### Database
- [ ] `utm_users` table created with proper indexes and RLS
- [ ] `utm_tenants` refactored to organization model
- [ ] Existing data migrated successfully (zero data loss)
- [ ] All foreign keys updated to reference user_id instead of tenant_id where appropriate
- [ ] RLS policies enforce tenant isolation

### Backend
- [ ] All new auth endpoints implemented and tested
- [ ] Permission system verifies role-based access
- [ ] Process locks track individual users
- [ ] Audit logs record user_id for all actions
- [ ] Backward compatibility maintained for existing clients

### Frontend
- [ ] Team Management page fully functional
- [ ] User can invite others via email
- [ ] Role changes reflected immediately
- [ ] Login flow updated with JWT tokens
- [ ] All headers include X-User-ID
- [ ] Permission guards hide unauthorized actions

### Testing
- [ ] Unit tests for permission service
- [ ] Integration tests for multi-user scenarios
- [ ] E2E test: Invite user → Accept → Create project → Share
- [ ] Load test: 50 users in same tenant
- [ ] Security audit: No privilege escalation possible

### Documentation
- [ ] Updated DATABASE_STRUCTURE.md
- [ ] Migration guide for existing tenants
- [ ] API documentation for new endpoints
- [ ] User guide: "How to invite team members"

---

## 📊 Success Metrics

- 📈 **User Adoption**: 50% of tenants invite at least 1 additional user within 30 days
- 📈 **Collaboration**: Average projects per tenant increases by 30%
- 📈 **Scalability**: System handles 100 concurrent users per tenant
- 📉 **Support Tickets**: < 5% increase (smooth transition)

---

## 🚧 Known Limitations & Future Work

### v3.9 Will NOT Include:
- ❌ Project-level sharing with external tenants (cross-tenant collaboration)
- ❌ Real-time collaboration (multiple users editing same asset)
- ❌ Advanced audit logs (full activity timeline)
- ❌ Custom roles (only predefined roles)
- ❌ SSO/SAML integration
- ❌ Usage-based billing

### Planned for v3.10+:
- ✅ Custom role builder (define your own permissions)
- ✅ Project-level permissions (not just tenant-level)
- ✅ Activity feed and notifications
- ✅ API keys for programmatic access

---

# v3.10 - RBAC & Permissions (The Fine-Grained Control Release)

**Theme**: "Granular Control & Resource Security"  
**Duration**: 3 weeks  
**Target**: Late March 2026  
**Priority**: 🟡 HIGH - Security Enhancement

## 🎯 Core Objective

> **Implement fine-grained, resource-level permissions beyond role-based access. Enable per-project permissions, custom roles, and detailed audit trails.**

---

## 🔧 Key Features

### 1. Project-Level Permissions
```sql
CREATE TABLE utm_project_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES utm_users(user_id) ON DELETE CASCADE,
    
    -- Granular permissions
    can_view BOOLEAN DEFAULT TRUE,
    can_edit BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE,
    can_execute_triage BOOLEAN DEFAULT FALSE,
    can_execute_drafting BOOLEAN DEFAULT FALSE,
    can_execute_refinement BOOLEAN DEFAULT FALSE,
    can_download_reports BOOLEAN DEFAULT TRUE,
    can_share BOOLEAN DEFAULT FALSE,
    
    -- Audit
    granted_by UUID NOT NULL REFERENCES utm_users(user_id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- Optional expiration
    
    UNIQUE(project_id, user_id)
);
```

### 2. Custom Roles
```sql
CREATE TABLE utm_custom_roles (
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    role_name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL, -- Array of permission strings
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(tenant_id, role_name)
);

-- Example custom role:
{
    "role_name": "Data Engineer",
    "permissions": [
        "projects.view",
        "projects.create",
        "projects.edit_own",
        "drafting.execute",
        "refinement.execute",
        "reports.download"
    ]
}
```

### 3. Enhanced Audit Logs
```sql
CREATE TABLE utm_audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id),
    user_id UUID REFERENCES utm_users(user_id),
    
    -- Action tracking
    action VARCHAR(100) NOT NULL, -- "project.created", "user.invited", etc.
    resource_type VARCHAR(50), -- "project", "user", "vault", etc.
    resource_id UUID,
    
    -- Change details
    changes JSONB, -- Before/after values
    
    -- Context
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(255),
    
    -- Result
    status VARCHAR(20) DEFAULT 'success', -- success, failure, error
    error_message TEXT,
    
    -- Metadata
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON utm_audit_logs(tenant_id);
CREATE INDEX idx_audit_user ON utm_audit_logs(user_id);
CREATE INDEX idx_audit_action ON utm_audit_logs(action);
CREATE INDEX idx_audit_timestamp ON utm_audit_logs(timestamp DESC);
CREATE INDEX idx_audit_resource ON utm_audit_logs(resource_type, resource_id);
```

### 4. Resource Sharing
```typescript
// Share project with specific users
POST /api/projects/{project_id}/share
{
  "users": [
    {
      "user_id": "uuid",
      "permissions": {
        "can_view": true,
        "can_edit": false,
        "can_execute_triage": true
      }
    }
  ],
  "notify": true // Send email notification
}
```

---

## 🎨 UI Enhancements

### 1. Project Sharing Modal
- Select users from team
- Granular permission checkboxes
- Expiration date picker
- Share link generation (optional)

### 2. Audit Log Viewer
- Filterable timeline (user, action, date range)
- Export to CSV/Excel
- Real-time updates
- Drill-down into change details

### 3. Custom Role Editor
- Visual permission builder
- Test role simulation
- Clone existing roles
- Assign to users in bulk

---

## ✅ Acceptance Criteria

- [ ] Project-level permissions enforced throughout API
- [ ] Custom roles can be created and assigned
- [ ] Audit logs capture all significant actions
- [ ] Users can share projects with granular permissions
- [ ] Admin can view full audit trail
- [ ] Performance: < 50ms overhead for permission checks
- [ ] UI shows permission-aware controls (disabled buttons, tooltips)

---

# v3.11 - Team Collaboration (The Workflow Enhancement Release)

**Theme**: "Real-Time Teamwork & Notifications"  
**Duration**: 3 weeks  
**Target**: Mid-April 2026  
**Priority**: 🟢 MEDIUM - UX Enhancement

## 🎯 Core Objective

> **Enable real-time collaboration features: notifications, comments, activity feeds, and team workflows.**

---

## 🔧 Key Features

### 1. Notifications System
```sql
CREATE TABLE utm_notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES utm_users(user_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id),
    
    -- Notification details
    type VARCHAR(50) NOT NULL, -- "project.shared", "comment.mention", "stage.completed"
    title VARCHAR(255) NOT NULL,
    message TEXT,
    
    -- Related resources
    resource_type VARCHAR(50),
    resource_id UUID,
    resource_url TEXT, -- Deep link to relevant page
    
    -- Action button (optional)
    action_label VARCHAR(50), -- "View Project", "Reply", etc.
    action_url TEXT,
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE -- Auto-delete old notifications
);

CREATE INDEX idx_notifications_user ON utm_notifications(user_id);
CREATE INDEX idx_notifications_unread ON utm_notifications(user_id, is_read);
CREATE INDEX idx_notifications_created ON utm_notifications(created_at DESC);
```

### 2. Comments & Discussions
```sql
CREATE TABLE utm_comments (
    comment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_comment_id UUID REFERENCES utm_comments(comment_id), -- For threading
    
    -- Context
    resource_type VARCHAR(50) NOT NULL, -- "project", "asset", "transformation"
    resource_id UUID NOT NULL,
    
    -- Author
    user_id UUID NOT NULL REFERENCES utm_users(user_id),
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id),
    
    -- Content
    content TEXT NOT NULL,
    mentions UUID[], -- Array of mentioned user_ids
    attachments JSONB, -- Optional file attachments
    
    -- Status
    is_edited BOOLEAN DEFAULT FALSE,
    edited_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_comments_resource ON utm_comments(resource_type, resource_id);
CREATE INDEX idx_comments_user ON utm_comments(user_id);
CREATE INDEX idx_comments_tenant ON utm_comments(tenant_id);
```

### 3. Activity Feed
```typescript
// Real-time activity feed per project/tenant
GET /api/activity?project_id={id}&limit=50

Response:
[
  {
    "id": "uuid",
    "type": "project.stage_completed",
    "actor": {
      "user_id": "uuid",
      "display_name": "John Doe",
      "avatar_url": "..."
    },
    "resource": {
      "type": "project",
      "id": "uuid",
      "name": "ETL Migration"
    },
    "message": "completed Stage 3: Drafting",
    "timestamp": "2026-03-15T14:30:00Z"
  }
]
```

### 4. Assignments & Tasks
```sql
CREATE TABLE utm_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES utm_projects(project_id),
    
    -- Assignment
    assigned_to UUID REFERENCES utm_users(user_id),
    assigned_by UUID REFERENCES utm_users(user_id),
    
    -- Task details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(50), -- "review_asset", "execute_stage", "review_report"
    
    -- Related resource
    resource_type VARCHAR(50),
    resource_id UUID,
    
    -- Status
    status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    priority VARCHAR(20) DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, URGENT
    
    -- Timeline
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 5. WebSocket Integration (Real-Time)
```typescript
// Real-time updates for:
// - New comments
// - Project stage progress
// - User presence (who's viewing what)
// - Lock status changes
// - Notifications

// Client-side:
const socket = new WebSocket(`ws://api/ws/${tenant_id}`);

socket.on('notification', (data) => {
  showNotificationToast(data);
});

socket.on('project.stage_update', (data) => {
  updateProjectStatus(data);
});

socket.on('user.presence', (data) => {
  showActiveUsers(data.users);
});
```

---

## 🎨 UI Components

### 1. Notification Center
- Bell icon with unread count badge
- Dropdown with recent notifications
- Mark as read/unread
- Notification preferences (email, in-app, push)

### 2. Comment Threads
- Inline comments on assets/transformations
- @mention autocomplete
- Rich text editor (markdown support)
- File attachments

### 3. Activity Timeline
- Visual timeline of project events
- Filter by user, action type, date range
- Export activity report

### 4. User Presence Indicators
- Show who's currently viewing a project
- Active user avatars
- "X is editing..." indicators

### 5. Task Management Panel
- Kanban board (To Do, In Progress, Done)
- Assign tasks to team members
- Due date reminders
- Task completion tracking

---

## ✅ Acceptance Criteria

- [ ] Notifications delivered in real-time via WebSocket
- [ ] Users can comment on projects, assets, transformations
- [ ] @mentions trigger notifications
- [ ] Activity feed shows comprehensive project history
- [ ] Tasks can be created and assigned
- [ ] Email notifications sent for critical events
- [ ] User presence visible in project workspace
- [ ] System supports 500+ concurrent WebSocket connections
- [ ] Email digest option (daily/weekly summary)

---

# v4.0 - AI Revolution (The Autonomous Intelligence Release)

**Theme**: "Zero-Hardcode, Prompt-Driven Everything"  
**Duration**: 8-10 weeks  
**Target**: Q3 2026  
**Priority**: 🔴 CRITICAL - Strategic Transformation

## 🎯 Core Objective (Refined)

> **Eliminate ALL hardcoded generation logic in Python/TypeScript. Make the system fully autonomous, prompt-driven, and self-learning while supporting multi-user collaboration and fine-grained permissions established in v3.9-v3.11.**

---

## 🔧 Key Features (Inherited from v4.0 Vision + Refined)

All features from `future_v4.0.md` PLUS:

### 1. Team-Aware AI Agents
- Agents understand who requested the generation
- Outputs customized per user role (detailed for Analysts, summary for Managers)
- Knowledge injection includes team preferences and standards

### 2. Collaborative Prompt Engineering
- Teams can build shared prompt libraries
- Custom cartridges per organization
- A/B testing of prompts with team voting

### 3. Multi-User Orchestration
- Agent mesh aware of simultaneous executions
- Smart queuing when multiple users trigger processes
- Load balancing across model providers

### 4. Permission-Aware Code Generation
```
# Agent F (Compliance Auditor) ALSO checks:
- Does user have permission to generate for this destination?
- Are credentials in vault owned by this tenant active?
- Is the target cartridge enabled for this user's role?
```

### 5. Detailed Audit for AI Actions
```sql
CREATE TABLE utm_ai_execution_logs (
    execution_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    agent_id VARCHAR(50),
    prompt_used TEXT,
    model_used VARCHAR(100),
    tokens_used INTEGER,
    cost_usd DECIMAL(10,4),
    execution_time_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## 📅 Detailed Timeline

```
┌─────────────────────────────────────────────────────────────┐
│  Feb 2026        Mar 2026        Apr 2026        Q3 2026    │
├─────────────────────────────────────────────────────────────┤
│  v3.8      │   v3.9      │   v3.10     │   v3.11   │  v4.0 │
│ (CURRENT)  │ MultiUser   │    RBAC     │   Collab  │   AI  │
│            │  Foundation │ Permissions │  Workflow │ Revol │
│            │             │             │           │       │
│    ✅      │  Week 1-4   │  Week 1-3   │  Week 1-3 │Week1-10│
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Summary: Strategic Roadmap

### The Journey
1. **v3.9** - Foundation for multi-user SaaS (users can collaborate)
2. **v3.10** - Security & control (who can do what)
3. **v3.11** - Productivity & UX (real-time work together)
4. **v4.0** - Intelligence & autonomy (AI does the heavy lifting)

### Key Milestones
- **March 2026**: Organizations can invite teams (v3.9)
- **End of March**: Granular permissions live (v3.10)
- **Mid-April**: Real-time collaboration working (v3.11)
- **Q3 2026**: Fully autonomous AI generation (v4.0)

### Business Impact
- 📈 **ARR Growth**: Multi-user support unlocks enterprise deals
- 📈 **User Engagement**: Teams collaborate 3x more than individuals
- 📈 **Market Position**: First AI-powered migration platform with true team collaboration
- 📉 **Churn**: Better onboarding and shared knowledge reduces churn by 40%

---

## 🚨 Risk Mitigation

### Technical Risks
- **Data Migration Complexity**: Extensive testing in staging, rollback plan
- **Performance Degradation**: Load testing before each release
- **WebSocket Scalability**: Use managed services (Pusher, Ably) if needed

### Business Risks
- **User Confusion**: Comprehensive migration guide + onboarding videos
- **Feature Creep**: Strict scope control, defer non-critical features
- **Competition**: Fast execution (16 weeks total = 4 months to v4.0)

---

## ✅ Go/No-Go Checklist per Release

### Before v3.9 Launch:
- [ ] Database migration tested on copy of production
- [ ] Zero data loss verified
- [ ] Existing API clients still work (backward compat)
- [ ] At least 3 beta tenants onboarded and tested
- [ ] Performance tests pass (< 200ms API response time)
- [ ] Security audit completed (no privilege escalation)
- [ ] Rollback plan documented and rehearsed

### Before v3.10 Launch:
- [ ] Permission checks add < 50ms overhead
- [ ] Audit logs indexing optimized (< 1s query time)
- [ ] Custom roles UI validated by 5 power users
- [ ] Load test: 100 concurrent users with permissions

### Before v3.11 Launch:
- [ ] WebSocket server handles 1000 concurrent connections
- [ ] Email notifications deliver within 60 seconds
- [ ] Comment system handles 10,000+ comments per project
- [ ] Mobile-responsive UI for notifications

### Before v4.0 Launch:
- [ ] All hardcoded templates removed from Python
- [ ] Prompt database fully populated (50+ prompts)
- [ ] Agent mesh handles 20 concurrent executions
- [ ] Self-learning feedback loop operational
- [ ] Cost per generation < $0.50 USD

---

*Release Plan maintained by: Development Team*  
*Created: February 9, 2026*  
*Status: DRAFT - Pending Stakeholder Approval*
