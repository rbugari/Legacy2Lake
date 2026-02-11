# Legacy2Lake UTM - Database Schema Documentation

**Fecha:** Febrero 10, 2026  
**Versión:** v3.9 + Sprint 1 Extensions  
**Database:** PostgreSQL (Supabase)  
**RLS:** Enabled (Row Level Security)

---

## 📊 Database Overview

### Core Tables (15)
- **utm_tenants** - Multi-tenant organization management
- **utm_users** - User accounts with authentication
- **utm_projects** - Data migration projects
- **utm_project_members** - Project access control
- **utm_invitations** - User invitation system
- **utm_design_registry** - Medallion architecture definitions
- **utm_process_locks** - Concurrent process management
- **utm_agents** - LLM agent configurations
- **utm_agent_matrix** - Agent-phase-tech mappings
- **utm_prompts** - System prompts with versioning
- **utm_system_catalog** - Technology stack catalog
- **utm_solution_context** - Project context metadata
- **utm_column_mappings** - Column transformation mappings
- **utm_file_storage** - File metadata tracking
- **utm_audit_logs** - System audit trail

---

## 🏢 Multi-Tenancy Architecture

### utm_tenants
**Purpose:** Root level of multi-tenancy isolation

```sql
CREATE TABLE utm_tenants (
    tenant_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL UNIQUE,
    display_name        TEXT,
    email               TEXT,
    plan                TEXT DEFAULT 'free',  -- free, pro, enterprise
    settings            JSONB DEFAULT '{}',
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tenants_name ON utm_tenants(name);
CREATE INDEX idx_tenants_active ON utm_tenants(is_active);
```

**RLS Policy:**
```sql
-- Users can only see their own tenant
CREATE POLICY tenant_isolation ON utm_tenants
    USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

**Key Fields:**
- `plan`: Controls feature access (free/pro/enterprise)
- `settings`: Tenant-specific configurations (JSONB)
- `email`: Contact email for tenant admin

**Sprint 1 Usage:**
- Prompts con `tenant_id = NULL` son globales
- Prompts con `tenant_id` específico son tenant overrides

---

## 👥 User Management

### utm_users
**Purpose:** User accounts with role-based access

```sql
CREATE TABLE utm_users (
    user_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    email               TEXT NOT NULL,
    username            TEXT NOT NULL,
    password_hash       TEXT,  -- Nullable for SSO users
    role                TEXT NOT NULL DEFAULT 'collaborator',
    is_active           BOOLEAN DEFAULT TRUE,
    last_login          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_email_per_tenant UNIQUE (tenant_id, email),
    CONSTRAINT unique_username_per_tenant UNIQUE (tenant_id, username),
    CONSTRAINT valid_role CHECK (role IN ('admin', 'manager', 'collaborator', 'viewer'))
);

CREATE INDEX idx_users_tenant ON utm_users(tenant_id);
CREATE INDEX idx_users_email ON utm_users(tenant_id, email);
CREATE INDEX idx_users_active ON utm_users(is_active);
```

**Roles Hierarchy:**
```
admin        → Full tenant control, user management
manager      → Project creation, team management  
collaborator → Project access, code generation
viewer       → Read-only access
```

**RLS Policy:**
```sql
-- Users see only users in their tenant
CREATE POLICY tenant_users ON utm_users
    USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

**Sprint 1 Note:** User management for tenant-specific prompt overrides

---

## 📋 Project Management

### utm_projects
**Purpose:** Data migration project definitions

```sql
CREATE TABLE utm_projects (
    project_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    owner_id            UUID REFERENCES utm_users(user_id) ON DELETE SET NULL,
    name                TEXT NOT NULL,
    description         TEXT,
    repo_url            TEXT,
    settings            JSONB DEFAULT '{}',
    status              TEXT DEFAULT 'draft',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_project_name UNIQUE (tenant_id, name),
    CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'completed', 'archived'))
);

CREATE INDEX idx_projects_tenant ON utm_projects(tenant_id);
CREATE INDEX idx_projects_owner ON utm_projects(owner_id);
CREATE INDEX idx_projects_status ON utm_projects(status);
```

**Key Fields:**
- `settings`: Project configurations (source_tech, target_tech, paths, naming)
- `status`: Project lifecycle management
- `owner_id`: Project creator (v3.9)

**RLS Policy:**
```sql
-- Users see projects they have access to via utm_project_members
CREATE POLICY project_member_access ON utm_projects
    USING (
        EXISTS (
            SELECT 1 FROM utm_project_members pm
            WHERE pm.project_id = utm_projects.project_id
            AND pm.user_id = current_setting('app.current_user')::uuid
        )
    );
```

---

### utm_project_members
**Purpose:** Fine-grained project access control

```sql
CREATE TABLE utm_project_members (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES utm_users(user_id) ON DELETE CASCADE,
    role                TEXT NOT NULL DEFAULT 'collaborator',
    added_by            UUID REFERENCES utm_users(user_id) ON DELETE SET NULL,
    added_at            TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_project_member UNIQUE (project_id, user_id),
    CONSTRAINT valid_project_role CHECK (role IN ('manager', 'collaborator', 'viewer'))
);

CREATE INDEX idx_project_members_project ON utm_project_members(project_id);
CREATE INDEX idx_project_members_user ON utm_project_members(user_id);
```

**Project Roles:**
- `manager`: Full project control, member management
- `collaborator`: Code generation, editing
- `viewer`: Read-only access

**v3.9 Feature:** Replaces client-based isolation with user-based access

---

## 🎨 Design Registry (Medallion Architecture)

### utm_design_registry
**Purpose:** Stores Medallion Architecture node definitions

```sql
CREATE TABLE utm_design_registry (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    tenant_id           UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    node_id             TEXT NOT NULL,
    node_data           JSONB NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_node_per_project UNIQUE (project_id, node_id)
);

CREATE INDEX idx_registry_project ON utm_design_registry(project_id);
CREATE INDEX idx_registry_tenant ON utm_design_registry(tenant_id);
CREATE INDEX idx_registry_node_type ON utm_design_registry((node_data->>'type'));
```

**node_data Structure (JSONB):**
```json
{
    "name": "bronze_dim_customers",
    "label": "Bronze - Raw Customers",
    "type": "ingestion",
    "layer": "bronze",
    "tech_id": "pyspark",
    "source_table": "dbo.DimCustomers",
    "target_table": "bronze_raw.dim_customers",
    "primary_keys": ["CustomerKey"],
    "cartridge_prompt": "...",  // Sprint 0 injection (optional)
    "generated_code": "...",
    "status": "draft"
}
```

**Usage:**
- Agent A creates initial nodes
- Agent C generates code per node
- Agent F optimizes generated code
- Frontend visualizes as diagram

---

## 🤖 Agent System

### utm_agents
**Purpose:** LLM agent configurations per tenant

```sql
CREATE TABLE utm_agents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    agent_id            TEXT NOT NULL,  -- 'agent_a', 'agent_c', etc.
    display_name        TEXT NOT NULL,
    provider            TEXT NOT NULL,  -- 'azure_openai', 'openai', 'anthropic'
    deployment          TEXT NOT NULL,  -- Model name
    endpoint            TEXT,
    api_key             TEXT,
    temperature         NUMERIC DEFAULT 0,
    max_tokens          INTEGER,
    is_active           BOOLEAN DEFAULT TRUE,
    phase               TEXT,  -- 'triage', 'drafting', 'refinement'
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_agent_per_tenant UNIQUE (tenant_id, agent_id)
);

CREATE INDEX idx_agents_tenant ON utm_agents(tenant_id);
CREATE INDEX idx_agents_phase ON utm_agents(phase);
CREATE INDEX idx_agents_active ON utm_agents(is_active);
```

**Agents Implemented:**
- **Agent A** (Architect): Design registry creation
- **Agent C** (Code Generator): Cartridge-based code generation
- **Agent D** (Auditor): Architecture compliance
- **Agent F** (Optimizer): Code optimization & review
- **Agent G** (Project Manager): Project orchestration
- **Agent S** (Scout): Gap detection & intelligence

**Sprint 1 Integration:** Agent C loads prompts from utm_prompts

---

### utm_agent_matrix
**Purpose:** Maps agents to phases and technologies

```sql
CREATE TABLE utm_agent_matrix (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id            TEXT NOT NULL,
    phase               TEXT NOT NULL,
    tech_stack          TEXT NOT NULL,
    is_active           BOOLEAN DEFAULT TRUE,
    priority            INTEGER DEFAULT 0,
    
    CONSTRAINT unique_agent_phase_tech UNIQUE (agent_id, phase, tech_stack)
);

CREATE INDEX idx_matrix_agent ON utm_agent_matrix(agent_id);
CREATE INDEX idx_matrix_phase ON utm_agent_matrix(phase);
CREATE INDEX idx_matrix_tech ON utm_agent_matrix(tech_stack);
```

**Phases:**
- `triage`: Initial analysis (Agent A, Agent S)
- `drafting`: Design creation (Agent A, Agent G)
- `refinement`: Code generation & optimization (Agent C, Agent F, Agent D)

---

## 💬 System Prompts (Sprint 1)

### utm_prompts
**Purpose:** Versioned system prompts with tenant overrides

```sql
CREATE TABLE utm_prompts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    prompt_id           TEXT NOT NULL,
    version_number      INTEGER NOT NULL DEFAULT 1,
    version             TEXT DEFAULT '1.0',
    content             TEXT NOT NULL,
    is_active           BOOLEAN DEFAULT TRUE,
    changelog           TEXT,
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    created_by          UUID REFERENCES utm_users(user_id),
    
    CONSTRAINT unique_active_prompt UNIQUE (tenant_id, prompt_id, is_active)
);

CREATE INDEX idx_prompts_lookup ON utm_prompts(tenant_id, prompt_id, is_active);
CREATE INDEX idx_prompts_tenant ON utm_prompts(tenant_id);
CREATE INDEX idx_prompts_type ON utm_prompts((metadata->>'tech_id'));
```

**Prompt Types:**
1. **Agent Prompts**: `agent_a_architect`, `agent_c_interpreter`, `agent_f_critic`, etc.
2. **Cartridge Prompts**: `cartridge_{tech_id}_{layer}` (Sprint 1)
   - Examples: `cartridge_pyspark_bronze`, `cartridge_snowflake_silver`

**Naming Convention (Sprint 1):**
```
cartridge_{tech_id}_{layer}

Tech IDs: pyspark, snowflake, fabric, dbt, gcp, aws, generic, salesforce
Layers: bronze, silver, gold
```

**Tenant Override Priority:**
```
1. Tenant-specific prompt (tenant_id = <UUID>, is_active = true)
2. Global prompt (tenant_id = NULL, is_active = true)
3. Fallback to filesystem (auto-seed to DB)
```

**metadata Structure:**
```json
{
    "tech_id": "pyspark",
    "layer": "bronze",
    "source_folder": "pyspark",
    "seeded_from": "prompt_lab/cartridges/pyspark/bronze_layer.md",
    "seed_version": "sprint_1_migration"
}
```

**Sprint 1 Results:**
- 24 cartridge prompts migrated
- ~230KB total content
- 8 technologies x 3 layers

---

## 📚 System Catalog

### utm_system_catalog
**Purpose:** Technology stack and cartridge metadata

```sql
CREATE TABLE utm_system_catalog (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tech_id             TEXT NOT NULL UNIQUE,
    display_name        TEXT NOT NULL,
    category            TEXT,  -- 'source', 'target', 'both'
    config              JSONB DEFAULT '{}',
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_catalog_tech ON utm_system_catalog(tech_id);
CREATE INDEX idx_catalog_category ON utm_system_catalog(category);
```

**config Structure:**
```json
{
    "dialect_instruction": "...",
    "compliance_rules": {
        "base": "...",
        "source_overrides": {...}
    },
    "warehouse": "...",
    "default_paths": {...}
}
```

**Technologies Registered:**
- **Source**: mssql, oracle, db2, mysql, postgres
- **Target**: pyspark, snowflake, fabric, databricks, aws_glue, gcp_bigquery, dbt
- **Both**: generic (pseudocode)

---

## 🔒 Process Management

### utm_process_locks
**Purpose:** Prevent concurrent modifications

```sql
CREATE TABLE utm_process_locks (
    lock_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    user_id             UUID REFERENCES utm_users(user_id) ON DELETE SET NULL,
    lock_type           TEXT NOT NULL,  -- 'triage', 'drafting', 'refinement'
    acquired_at         TIMESTAMPTZ DEFAULT NOW(),
    expires_at          TIMESTAMPTZ NOT NULL,
    is_active           BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT unique_active_lock UNIQUE (project_id, lock_type, is_active)
);

CREATE INDEX idx_locks_project ON utm_process_locks(project_id);
CREATE INDEX idx_locks_expiry ON utm_process_locks(expires_at);
```

**Lock Types:**
- `triage`: Analysis phase lock
- `drafting`: Design phase lock
- `refinement`: Code generation lock

**Auto-expiry:** Locks auto-expire based on expires_at (typically 30-60 min)

---

## 👤 User Invitations

### utm_invitations
**Purpose:** User invitation workflow

```sql
CREATE TABLE utm_invitations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    project_id          UUID REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    email               TEXT NOT NULL,
    role                TEXT NOT NULL,
    invited_by          UUID REFERENCES utm_users(user_id) ON DELETE SET NULL,
    token               TEXT NOT NULL UNIQUE,
    status              TEXT DEFAULT 'pending',
    expires_at          TIMESTAMPTZ NOT NULL,
    accepted_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_invitation_role CHECK (role IN ('admin', 'manager', 'collaborator', 'viewer')),
    CONSTRAINT valid_invitation_status CHECK (status IN ('pending', 'accepted', 'expired', 'cancelled'))
);

CREATE INDEX idx_invitations_tenant ON utm_invitations(tenant_id);
CREATE INDEX idx_invitations_project ON utm_invitations(project_id);
CREATE INDEX idx_invitations_token ON utm_invitations(token);
CREATE INDEX idx_invitations_status ON utm_invitations(status);
```

**Workflow:**
1. Manager invites user (creates pending invitation)
2. Email sent with invitation token
3. User accepts (creates utm_users entry + utm_project_members if project_id)
4. Invitation marked as accepted

---

## 📄 File Storage Metadata

### utm_file_storage
**Purpose:** Track files stored in R2/S3

```sql
CREATE TABLE utm_file_storage (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    tenant_id           UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    file_key            TEXT NOT NULL,  -- R2 storage key
    file_name           TEXT NOT NULL,
    file_type           TEXT,  -- 'code', 'diagram', 'document'
    file_size           BIGINT,
    mime_type           TEXT,
    stage               TEXT,  -- 'triage', 'drafting', 'refinement'
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_file_key UNIQUE (project_id, file_key)
);

CREATE INDEX idx_storage_project ON utm_file_storage(project_id);
CREATE INDEX idx_storage_tenant ON utm_file_storage(tenant_id);
CREATE INDEX idx_storage_stage ON utm_file_storage(stage);
```

**Storage Provider:** Cloudflare R2 (abstracted via StorageFactory)

---

## 📊 Supporting Tables

### utm_solution_context
**Purpose:** Project metadata and context

```sql
CREATE TABLE utm_solution_context (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    context_data        JSONB NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

### utm_column_mappings
**Purpose:** Source → Target column transformations

```sql
CREATE TABLE utm_column_mappings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    source_column       TEXT NOT NULL,
    target_column       TEXT NOT NULL,
    transformation      TEXT,
    data_type_source    TEXT,
    data_type_target    TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

### utm_audit_logs
**Purpose:** System audit trail

```sql
CREATE TABLE utm_audit_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID REFERENCES utm_tenants(tenant_id),
    user_id             UUID REFERENCES utm_users(user_id),
    action              TEXT NOT NULL,
    resource_type       TEXT,
    resource_id         UUID,
    details             JSONB,
    ip_address          TEXT,
    user_agent          TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON utm_audit_logs(tenant_id);
CREATE INDEX idx_audit_user ON utm_audit_logs(user_id);
CREATE INDEX idx_audit_action ON utm_audit_logs(action);
CREATE INDEX idx_audit_created ON utm_audit_logs(created_at);
```

---

## 🔐 Row Level Security (RLS)

### Global RLS Pattern
All tables use tenant isolation:

```sql
ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON <table_name>
    USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

### Service Role Bypass
Service role (backend) bypasses RLS for:
- Admin operations
- Cross-tenant analytics
- System migrations

### Setting Context (Backend)
```python
# Set tenant context for RLS
db.client.rpc('set_tenant_context', {'tenant_uuid': tenant_id})

# Or via headers
headers = {
    'X-Tenant-ID': tenant_id,
    'X-User-ID': user_id
}
```

---

## 📈 Database Statistics

### Current State (Post-Sprint 1)
```
Tables:               15 core tables
Indexes:              ~50 indexes
RLS Policies:         ~15 policies
Total Prompts:        24 cartridge + 6 agent = 30
Storage:              R2 abstraction (PersistenceService)
Migrations:           25 migration files
Version:              v3.9 + Sprint 1
```

### Data Volumes (Dev Environment)
```
utm_tenants:          3 tenants (demo3, demo33, demo34)
utm_users:            ~10 users
utm_projects:         ~5 projects
utm_prompts:          30 prompts (~300KB)
utm_agents:           6 agents x 3 tenants = 18 configs
utm_design_registry:  Varies per project
```

---

## 🔄 Migration History

### Major Versions
- **v3.9**: User-based access control (replaced client-based)
- **Sprint 1**: Database-first prompts (24 cartridges migrated)

### Migration Files
```
supabase_migrations/
├── 010_v3.9_create_users_table.sql
├── 011_v3.9_create_invitations_table.sql
├── 012_v3.9_refactor_tenants.sql
├── 013_v3.9_add_user_ref_projects.sql
├── 014_v3.9_add_user_ref_locks.sql
├── 015_v3.9_data_migration.sql
├── 016_v3.9_update_rls_policies.sql
├── 020_v3.9_project_level_invitations.sql
├── 021_v3.9_project_members_table.sql
└── ... (25 files total)
```

---

## 🚀 Sprint 1 Database Impact

### New Capabilities
- ✅ Cartridge prompts in database (24 prompts)
- ✅ Tenant-specific prompt overrides (infrastructure ready)
- ✅ Version control for prompts
- ✅ Real-time prompt updates (no deployment)

### Query Patterns
```sql
-- Get active cartridge prompt with tenant override
SELECT content 
FROM utm_prompts
WHERE prompt_id = 'cartridge_pyspark_bronze'
  AND (tenant_id = $1 OR tenant_id IS NULL)
  AND is_active = TRUE
ORDER BY tenant_id DESC NULLS LAST
LIMIT 1;

-- List all cartridge prompts
SELECT 
    prompt_id,
    version_number,
    length(content) as size,
    metadata->>'tech_id' as tech,
    metadata->>'layer' as layer
FROM utm_prompts
WHERE prompt_id LIKE 'cartridge_%'
ORDER BY prompt_id;

-- Create new prompt version
INSERT INTO utm_prompts (tenant_id, prompt_id, version_number, content, is_active, changelog)
VALUES (NULL, 'cartridge_pyspark_bronze', 2, $content, TRUE, 'Sprint 0 Day 5 refinements');
```

---

## 📝 Best Practices

### Indexing Strategy
- Always index foreign keys (tenant_id, project_id, user_id)
- Composite indexes for common query patterns
- JSONB indexes for frequently queried fields
- Partial indexes for filtered queries (is_active = TRUE)

### JSONB Usage
- Flexible schema for `settings`, `metadata`, `config`
- GIN indexes for JSONB column searches
- Avoid deeply nested structures (max 3 levels)

### RLS Performance
- Keep policies simple (single equality check)
- Use indexes on RLS filter columns
- Service role bypasses for admin operations

### Versioning Pattern
- `version_number`: Integer for ordering
- `version`: Semantic version string (display)
- `is_active`: Only one active version per tenant
- `changelog`: Human-readable change description

---

## 🔮 Future Enhancements

### Planned (Post-Sprint 1)
- [ ] Prompt analytics table (usage tracking)
- [ ] Code generation metrics table
- [ ] Agent execution logs table
- [ ] Tenant usage quotas enforcement
- [ ] Prompt A/B testing infrastructure

### Considerations
- Partitioning for audit logs (date-based)
- Read replicas for analytics queries
- Caching layer (Redis) for prompts
- Archive strategy for old versions

---

**Document Version:** 1.0  
**Last Updated:** Febrero 10, 2026  
**Maintainer:** Legacy2Lake Development Team  
**References:** 
- Sprint 0 Retrospective
- Sprint 1 Completion Report
- Supabase Migrations directory
