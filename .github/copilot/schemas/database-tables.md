# Database Tables Reference - Legacy2Lake UTM

**Database:** PostgreSQL (Supabase)  
**Version:** v3.9 GA + Sprint Extensions  
**Last Updated:** February 13, 2026

This document provides the complete schema definitions for all database tables. Use this reference when writing queries or creating new services.

---

## 🔒 Multi-Tenancy & Security

**Row-Level Security (RLS):** Enabled on all tenant-scoped tables
**Isolation Method:** `tenant_id` column with RLS policies
**Authentication:** JWT tokens with tenant claims

---

## 🏢 Core Tables

### 1. utm_tenants

**Purpose:** Root level of multi-tenancy isolation  
**RLS:** Enabled  
**Primary Key:** tenant_id

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

**Key Fields:**
- `plan`: Controls feature access (free/pro/enterprise)
- `settings`: Tenant-specific configurations (JSONB)

**Query Pattern:**
```python
# ✅ CORRECT - Always filter by tenant_id
tenants = self.client.table("utm_tenants") \
    .select("*") \
    .eq("tenant_id", self.tenant_id) \
    .execute()
```

---

### 2. utm_users

**Purpose:** User accounts with role-based access  
**RLS:** Enabled  
**Primary Key:** user_id  
**Foreign Keys:** tenant_id → utm_tenants

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
admin        → Full tenant control, user management, system config
manager      → Project creation, team management, provider config
collaborator → Project access, code generation, asset management
viewer       → Read-only access to projects
```

**Query Pattern:**
```python
# Get all users in tenant
users = self.client.table("utm_users") \
    .select("user_id, username, email, role, is_active") \
    .eq("tenant_id", self.tenant_id) \
    .eq("is_active", True) \
    .execute()
```

---

### 3. utm_projects

**Purpose:** Data migration project definitions  
**RLS:** Enabled  
**Primary Key:** project_id  
**Foreign Keys:** tenant_id → utm_tenants, owner_id → utm_users

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

**Settings JSONB Fields:**
```json
{
    "source_tech": "SSIS",           // Source technology
    "target_tech": "DATABRICKS",     // Target platform
    "naming_convention": "snake_case",
    "include_audit_columns": true,
    "medallion_layers": ["bronze", "silver", "gold"],
    "validation_enabled": true
}
```

**Query Pattern:**
```python
# Get projects with member access
projects = self.client.table("utm_projects") \
    .select("*, utm_project_members!inner(user_id, role)") \
    .eq("tenant_id", self.tenant_id) \
    .eq("utm_project_members.user_id", self.user_id) \
    .execute()
```

---

### 4. utm_project_members

**Purpose:** Fine-grained project access control (v3.9)  
**RLS:** Enabled  
**Primary Key:** id  
**Foreign Keys:** project_id → utm_projects, user_id → utm_users

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

**Query Pattern:**
```python
# Get project members with user details
members = self.client.table("utm_project_members") \
    .select("*, utm_users(username, email)") \
    .eq("project_id", project_id) \
    .execute()
```

---

### 5. utm_objects

**Purpose:** Source assets/tables discovered in projects  
**RLS:** Enabled  
**Primary Key:** object_id  
**Foreign Keys:** project_id → utm_projects

```sql
CREATE TABLE utm_objects (
    object_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    source_name         TEXT NOT NULL,
    source_tech         TEXT,  -- SSIS, ORACLE, SQLSERVER, etc.
    type                TEXT,  -- table, view, procedure, package
    metadata            JSONB DEFAULT '{}',
    status              TEXT DEFAULT 'pending',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

CREATE INDEX idx_objects_project ON utm_objects(project_id);
CREATE INDEX idx_objects_source_tech ON utm_objects(source_tech);
CREATE INDEX idx_objects_status ON utm_objects(status);
```

**Metadata JSONB Fields:**
```json
{
    "columns": [
        {
            "name": "customer_id",
            "data_type": "INTEGER",
            "nullable": false,
            "is_primary_key": true,
            "is_pii": false
        },
        {
            "name": "email",
            "data_type": "VARCHAR(255)",
            "nullable": true,
            "is_pii": true,
            "pii_type": "EMAIL"
        }
    ],
    "row_count": 150000,
    "size_mb": 45.2,
    "partitions": ["year", "month"]
}
```

**Query Pattern:**
```python
# Get assets with column details
assets = self.client.table("utm_objects") \
    .select("object_id, source_name, source_tech, metadata") \
    .eq("project_id", project_id) \
    .eq("status", "completed") \
    .execute()
```

---

### 6. utm_design_registry

**Purpose:** Medallion architecture node definitions  
**RLS:** Enabled  
**Primary Key:** node_id  
**Foreign Keys:** project_id → utm_projects

```sql
CREATE TABLE utm_design_registry (
    node_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    node_type           TEXT NOT NULL,  -- READ, TRANSFORM, JOIN, AGGREGATE, WRITE
    layer               TEXT NOT NULL,  -- bronze, silver, gold
    source_object_id    UUID REFERENCES utm_objects(object_id),
    target_table        TEXT NOT NULL,
    transformation_logic JSONB DEFAULT '{}',
    dependencies        JSONB DEFAULT '[]',  -- Array of node_ids
    metadata            JSONB DEFAULT '{}',
    status              TEXT DEFAULT 'draft',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_node_type CHECK (node_type IN ('READ', 'TRANSFORM', 'JOIN', 'AGGREGATE', 'FILTER', 'WRITE')),
    CONSTRAINT valid_layer CHECK (layer IN ('bronze', 'silver', 'gold'))
);

CREATE INDEX idx_registry_project ON utm_design_registry(project_id);
CREATE INDEX idx_registry_layer ON utm_design_registry(layer);
CREATE INDEX idx_registry_status ON utm_design_registry(status);
```

**Transformation Logic JSONB:**
```json
{
    "operations": [
        {
            "type": "SELECT",
            "columns": ["customer_id", "name", "email"]
        },
        {
            "type": "FILTER",
            "condition": "is_active = true"
        },
        {
            "type": "DERIVE",
            "new_column": "full_name",
            "expression": "CONCAT(first_name, ' ', last_name)"
        }
    ]
}
```

---

### 7. utm_prompts

**Purpose:** System prompts with versioning (v4.0)  
**RLS:** Partial (tenant_id can be NULL for global prompts)  
**Primary Key:** prompt_id

```sql
CREATE TABLE utm_prompts (
    prompt_id           TEXT PRIMARY KEY,
    tenant_id           UUID REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,  -- NULL = global
    content             TEXT NOT NULL,
    tech_stack          TEXT,
    pattern_type        TEXT,  -- bronze, silver, gold
    agent_id            TEXT,  -- agent-a, agent-c, agent-f, etc.
    is_active           BOOLEAN DEFAULT TRUE,
    metadata            JSONB DEFAULT '{}',
    created_by          UUID REFERENCES utm_users(user_id),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_prompts_tenant ON utm_prompts(tenant_id);
CREATE INDEX idx_prompts_agent ON utm_prompts(agent_id);
CREATE INDEX idx_prompts_tech ON utm_prompts(tech_stack);
```

**Key Concepts:**
- `tenant_id = NULL`: Global prompt (used by all tenants)
- `tenant_id = <uuid>`: Tenant-specific override
- `prompt_id` format: `agent_{x}_{tech}_{layer}` (e.g., `agent_c_pyspark_bronze`)

**Query Pattern:**
```python
# Load prompt (tenant override or global)
result = self.client.table("utm_prompts") \
    .select("content") \
    .eq("prompt_id", "agent_c_pyspark_bronze") \
    .or_(f"tenant_id.eq.{self.tenant_id},tenant_id.is.null") \
    .order("tenant_id", desc=True) \  # Tenant override first
    .limit(1) \
    .execute()
```

---

### 8. utm_agent_matrix

**Purpose:** Agent-phase-tech mappings with model assignments  
**RLS:** Enabled  
**Primary Key:** (tenant_id, agent_id, phase, tech_stack)

```sql
CREATE TABLE utm_agent_matrix (
    tenant_id           UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    agent_id            TEXT NOT NULL,  -- agent-a, agent-c, etc.
    phase               TEXT NOT NULL,  -- discovery, triage, drafting, etc.
    tech_stack          TEXT,           -- pyspark, snowflake, NULL = all
    model_id            TEXT NOT NULL,  -- gpt-4o, claude-3-5-sonnet, etc.
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (tenant_id, agent_id, phase, COALESCE(tech_stack, ''))
);

CREATE INDEX idx_agent_matrix_tenant ON utm_agent_matrix(tenant_id);
CREATE INDEX idx_agent_matrix_agent ON utm_agent_matrix(agent_id);
```

**Query Pattern:**
```python
# Resolve LLM model for agent
config = self.client.table("utm_agent_matrix") \
    .select("model_id") \
    .eq("tenant_id", self.tenant_id) \
    .eq("agent_id", "agent-c") \
    .eq("phase", "refinement") \
    .eq("is_active", True) \
    .limit(1) \
    .execute()
```

---

### 9. utm_provider_vault

**Purpose:** LLM provider API keys (encrypted)  
**RLS:** Enabled  
**Primary Key:** (tenant_id, provider)

```sql
CREATE TABLE utm_provider_vault (
    tenant_id           UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    provider            TEXT NOT NULL,  -- azure, openai, groq
    api_key             TEXT NOT NULL,  -- Encrypted
    endpoint            TEXT,           -- Azure only
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (tenant_id, provider)
);

CREATE INDEX idx_provider_vault_tenant ON utm_provider_vault(tenant_id);
```

**Security:**
- API keys are encrypted at rest
- Never log or expose in plain text
- Use environment variables for development only

---

### 10. utm_model_catalog

**Purpose:** Enabled LLM models per tenant  
**RLS:** Enabled  
**Primary Key:** (tenant_id, model_id)

```sql
CREATE TABLE utm_model_catalog (
    tenant_id           UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    model_id            TEXT NOT NULL,
    label               TEXT NOT NULL,
    provider            TEXT NOT NULL,  -- azure, openai, groq
    context_window      INTEGER DEFAULT 128000,
    deployment_id       TEXT,           -- Azure deployment name
    api_version         TEXT,           -- Azure API version
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (tenant_id, model_id)
);

CREATE INDEX idx_model_catalog_tenant ON utm_model_catalog(tenant_id);
CREATE INDEX idx_model_catalog_active ON utm_model_catalog(tenant_id, is_active);
```

---

## 📊 Sprint Extensions

### 11. utm_code_validations (Sprint 8)

**Purpose:** Real-time validation results history  
**RLS:** Enabled via project_id  
**Primary Key:** validation_id

```sql
CREATE TABLE utm_code_validations (
    validation_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    task_id             UUID,  -- node_id or asset_id
    tech_id             TEXT NOT NULL,  -- pyspark, snowflake, etc.
    layer               TEXT NOT NULL,  -- bronze, silver, gold
    is_valid            BOOLEAN NOT NULL,
    errors_count        INTEGER DEFAULT 0,
    warnings_count      INTEGER DEFAULT 0,
    issues              JSONB DEFAULT '[]',
    validated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_validations_project ON utm_code_validations(project_id);
CREATE INDEX idx_validations_task ON utm_code_validations(task_id);
```

---

### 12. utm_asset_columns (Sprint 7)

**Purpose:** Detailed column-level metadata  
**RLS:** Enabled via object_id → utm_objects  
**Primary Key:** column_id

```sql
CREATE TABLE utm_asset_columns (
    column_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    object_id           UUID NOT NULL REFERENCES utm_objects(object_id) ON DELETE CASCADE,
    column_name         TEXT NOT NULL,
    data_type           TEXT NOT NULL,
    nullable            BOOLEAN DEFAULT TRUE,
    is_primary_key      BOOLEAN DEFAULT FALSE,
    is_foreign_key      BOOLEAN DEFAULT FALSE,
    is_pii              BOOLEAN DEFAULT FALSE,
    pii_type            TEXT,  -- EMAIL, SSN, PHONE, etc.
    pii_confidence      FLOAT,  -- 0.0 to 1.0
    statistics          JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_column_per_object UNIQUE (object_id, column_name)
);

CREATE INDEX idx_asset_columns_object ON utm_asset_columns(object_id);
CREATE INDEX idx_asset_columns_pii ON utm_asset_columns(is_pii);
```

**Statistics JSONB:**
```json
{
    "distinct_count": 98234,
    "null_count": 152,
    "null_percentage": 0.15,
    "min_value": 1,
    "max_value": 999999,
    "avg_value": 50124.5,
    "sample_values": ["john@example.com", "jane@company.com"]
}
```

---

### 13. utm_audit_logs (Sprint 6)

**Purpose:** System-wide audit trail  
**RLS:** No (admin access only)  
**Primary Key:** log_id

```sql
CREATE TABLE utm_audit_logs (
    log_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID REFERENCES utm_tenants(tenant_id),
    user_id             UUID REFERENCES utm_users(user_id),
    action              TEXT NOT NULL,  -- CREATE, UPDATE, DELETE, LOGIN
    resource_type       TEXT NOT NULL,  -- project, user, prompt, etc.
    resource_id         UUID,
    details             JSONB DEFAULT '{}',
    ip_address          TEXT,
    user_agent          TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON utm_audit_logs(tenant_id);
CREATE INDEX idx_audit_user ON utm_audit_logs(user_id);
CREATE INDEX idx_audit_created ON utm_audit_logs(created_at);
```

---

## 🔍 Common Query Patterns

### Multi-Tenant Joins

```python
# Projects with owner details (multi-tenant safe)
projects = self.client.table("utm_projects") \
    .select("*, utm_users!owner_id(username, email)") \
    .eq("tenant_id", self.tenant_id) \
    .execute()

# Design registry with source asset info
nodes = self.client.table("utm_design_registry") \
    .select("*, utm_objects!source_object_id(source_name, source_tech)") \
    .eq("project_id", project_id) \
    .eq("layer", "bronze") \
    .execute()
```

### Aggregations

```python
# Project statistics
stats = self.client.rpc(
    "get_project_stats",
    {"p_project_id": project_id}
).execute()

# Custom aggregation
result = self.client.table("utm_objects") \
    .select("source_tech, status", count="exact") \
    .eq("project_id", project_id) \
    .execute()
```

### Upsert Operations

```python
# Insert or update prompt
self.client.table("utm_prompts") \
    .upsert({
        "prompt_id": "agent_c_pyspark_bronze",
        "tenant_id": self.tenant_id,
        "content": new_prompt,
        "agent_id": "agent-c",
        "updated_at": datetime.utcnow().isoformat()
    }) \
    .execute()
```

---

## 🎯 Best Practices

### 1. Always Filter by tenant_id

```python
# ✅ CORRECT
query = self.client.table("utm_projects").select("*")
if self.tenant_id:
    query = query.eq("tenant_id", self.tenant_id)
result = query.execute()

# ❌ WRONG - Security risk!
result = self.client.table("utm_projects").select("*").execute()
```

### 2. Use Transactions for Related Inserts

```python
# Creating project with initial member
async with self.client.transaction():
    # Create project
    project = self.client.table("utm_projects").insert({
        "tenant_id": self.tenant_id,
        "name": "New Project",
        "owner_id": self.user_id
    }).execute()
    
    # Add owner as manager
    self.client.table("utm_project_members").insert({
        "project_id": project.data[0]["project_id"],
        "user_id": self.user_id,
        "role": "manager"
    }).execute()
```

### 3. Handle JSONB Fields Properly

```python
# ✅ CORRECT - Use jsonb_set for updates
self.client.table("utm_projects") \
    .update({
        "settings": {
            **existing_settings,
            "new_key": "new_value"
        }
    }) \
    .eq("project_id", project_id) \
    .execute()
```

### 4. Use Indexes for Performance

```sql
-- Add index if querying by custom field frequently
CREATE INDEX idx_projects_repo_url ON utm_projects(repo_url) 
WHERE repo_url IS NOT NULL;

-- Composite index for common filters
CREATE INDEX idx_objects_project_status ON utm_objects(project_id, status);
```

---

## 🔗 Foreign Key Relationships

```
utm_tenants (root)
    ├── utm_users
    │   └── utm_projects (owner_id)
    │       ├── utm_project_members
    │       ├── utm_objects
    │       │   ├── utm_asset_columns
    │       │   └── utm_design_registry (source_object_id)
    │       └── utm_code_validations
    ├── utm_prompts (tenant_id nullable)
    ├── utm_agent_matrix
    ├── utm_provider_vault
    └── utm_model_catalog
```

---

**For Complete Schema:** See [DATABASE_SCHEMA.md](../../docs/DATABASE_SCHEMA.md)  
**For RLS Policies:** See [SYSTEM_ARCHITECTURE.md](../../docs/SYSTEM_ARCHITECTURE.md)
