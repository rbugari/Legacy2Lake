# Metadata Store: Data Model Specification (v3.9)

**Version:** v3.9 (Multi-User Architecture)  
**Last Updated:** 2026-02-10

The **Metadata Store** is the central repository where the "intelligence" of Legacy2Lake resides. **v3.9** introduces a fundamental architectural shift: **separation of user identity from organization/tenant**, enabling true multi-user collaboration with granular role-based access control.

## Recent Updates

### v3.9 (Multi-User Architecture) - Feb 2026 ⭐ CURRENT:
- **User/Tenant Separation**: `utm_users` table separates user identity from organization
- **`utm_tenants` Simplification**: Now represents pure organizations (removed user fields, client_id, org_name)
- **Removed `utm_clients`**: Consolidated into `utm_tenants` (migration 024)
- **`utm_user_invitations`**: Email-based onboarding workflow with token validation
- **`utm_project_members`**: Granular project-level access control (COLLABORATOR/VIEWER roles)
- **Role System**: 4-tier hierarchy (ADMIN/MANAGER/COLLABORATOR/VIEWER)
- **User Tracking**: Projects now track `created_by_user_id`, locks track `locked_by_user_email`

### v3.8 (Process Locking & Governance):
- **`utm_process_locks`**: New table for concurrent execution prevention with smart timeouts
- **Lock Management**: Admin force-release capabilities and auto-expiration via RPC function
- **Governance Rules**: Formalized 3-layer ownership model (Admin/Tenant/User) documented
- **Reports Enhancement**: Version-agnostic templates and centralized Reports Library modal

### v3.5 (Cloud-Native & Multi-Tenant):
- **`tenant_id` Enforcement**: All project-related tables now transition to a mandatory `tenant_id` (UUID) for strict isolation via Supabase RLS.
- **R2 Storage Inventory**: The new `utm_file_inventory` table provides a metadata cache of objects stored in Cloudflare R2, enabling high-performance listing without constant S3-API calls.
- **Project Settings v2**: `utm_projects.settings` now includes environment variables, source/target tech, and tenant-specific configuration
- **Audit Persistence**: `utm_execution_logs` now stores structured phase-specific trace data (Phase 1-10).

---

## 1. Entity-Relationship Diagram (Logical Structure)

```mermaid
erDiagram
    utm_tenants ||--o{ utm_users : "employs"
    utm_tenants ||--o{ utm_projects : "owns"
    utm_tenants ||--o{ utm_user_invitations : "invites to"
    utm_tenants ||--o{ utm_provider_vault : "configures"
    
    utm_users ||--o{ utm_projects : "creates"
    utm_users ||--o{ utm_project_members : "has access to"
    utm_users ||--o{ utm_user_invitations : "invited by"
    
    utm_projects ||--o{ utm_objects : "contains assets"
    utm_projects ||--o{ utm_project_members : "grants access"
    utm_projects ||--o{ utm_design_registry : "configures"
    utm_projects ||--o{ utm_execution_logs : "logs"
    utm_projects ||--o{ utm_file_inventory : "indexes files"
    utm_projects ||--o| utm_process_locks : "locked by"
    
    utm_objects ||--o{ utm_logical_steps : "transforms to"
    utm_objects ||--o{ utm_transformations : "generates code"
    utm_objects ||--o{ utm_column_mappings : "maps columns"
    
    utm_logical_steps ||--o{ utm_user_overrides : "adjusted by"
    
    utm_agent_matrix }|--|| utm_agent_catalog : "assigns model to"
    utm_model_catalog }|--|| utm_agent_matrix : "used by"

    utm_tenants {
        uuid tenant_id PK
        string display_name
        string tier
        boolean is_active
    }

    utm_users {
        uuid user_id PK
        uuid tenant_id FK
        string email UNIQUE
        string username
        string password_hash_bcrypt
        string role
        boolean is_active
        timestamp last_login
    }

    utm_user_invitations {
        uuid invitation_id PK
        uuid tenant_id FK
        string email
        string role
        string token UNIQUE
        timestamp expires_at
        string status
        uuid invited_by FK
    }

    utm_project_members {
        uuid member_id PK
        uuid project_id FK
        uuid user_id FK
        string role
        uuid added_by FK
        timestamp added_at
    }

    utm_projects {
        uuid project_id PK
        uuid tenant_id FK
        uuid created_by_user_id FK
        string name
        jsonb settings
        jsonb config
        string status
    }

    utm_objects {
        uuid object_id PK
        uuid project_id FK
        string source_name
        string type
        jsonb metadata
    }

    utm_logical_steps {
        uuid step_id PK
        uuid object_id FK
        string step_type
        jsonb ir_payload
        string status
    }
    
    utm_column_mappings {
        uuid id PK
        uuid asset_id FK
        string source_column
        string target_column
        text logic
    }

    utm_process_locks {
        uuid lock_id PK
        uuid project_id FK
        string phase
        string locked_by_user_email
        timestamp locked_at
        timestamp expires_at
    }
```

### 1.1 Multi-User Architecture (v3.9)
*   **`utm_tenants`**: Represents the organization/company. **No longer stores user data** - purely organizational entity.
*   **`utm_users`**: NEW table storing user identity. Each user belongs to ONE tenant and has a role (`ADMIN`, `MANAGER`, `COLLABORATOR`, `VIEWER`).
    *   **ADMIN**: Platform-level operations (cross-tenant). Can perform Ghost Mode, manage all users, force-release locks.
    *   **MANAGER**: Tenant-level operations. Can invite users, assign project access, configure providers.
    *   **COLLABORATOR**: Project-level editor. Can create/edit projects, execute stages, view execution logs.
    *   **VIEWER**: Project-level read-only. Can view projects, download reports, but cannot modify.
*   **`utm_user_invitations`**: Email-based onboarding. MANAGER sends invitation with token, user accepts and creates account.
*   **`utm_project_members`**: Granular access control. Users can be granted COLLABORATOR or VIEWER roles on specific projects.

### 1.2 Project & Multi-Tenancy Core
*   **`utm_projects`**: The central entity. Contains global `settings` (source/target tech) and `config` (variables).
    *   *Relations*: Belongs to a Tenant. Created by a User (`created_by_user_id`). Parent of Objects, Logs, and Inventory.
    *   *Access Control*: Tenant MANAGER and project members (via `utm_project_members`) can access.

### 1.3 Asset Management (`utm_objects`)
Represents artifacts (files) from the source system.
*   `metadata` (JSONB): Stores "Architect" inferences (Volume, PII, Complexity).
*   `type`: `LAYOUT` (Manifests), `DTSX` (SSIS), `SQL`, `NOTEBOOK`.

### 1.4 The Refinement Core (`utm_logical_steps`)
Stores the normalized Intermediate Representation (IR).
*   `ir_payload` (JSONB): The Universal Grammar JSON (Source -> Transformation -> Sink).
*   `status`: `DRAFT` -> `VALIDATED` -> `REFINED`.

### 1.5 Transformation & Code Gen
*   **`utm_transformations`**: Physical code generated from the Logical Steps.
*   **`utm_user_overrides`**: Stores human edits to the IR, ensuring reproducibility.
*   **`utm_column_mappings`**: Detailed field-level lineage and transformations.

### 1.6 Agent Orchestration
*   **`utm_agent_catalog`**: Registry of available agents (Name, Role).
*   **`utm_agent_matrix`**: Configuration linking Agents to specific LLM Models per Tenant/Project.
*   **`utm_provider_vault`**: Secure storage for LLM Provider API Keys (OpenAI, Azure) per Tenant.

### 1.7 Process Governance (v3.8)
*   **`utm_process_locks`**: Prevents concurrent execution on the same project. Includes `locked_by_user_email` (v3.9) for auditing.
    *   Locks auto-expire after 30 minutes (configurable).
    *   ADMIN users can force-release locks via `force_expire_lock(project_id)` RPC.

---

## 2. Persistence & Consumption Logic

### Multi-User Workflow (v3.9):
0. **User Onboarding**:
   - MANAGER invites user via email → `utm_user_invitations` record created with unique token
   - User accepts invitation → `utm_users` record created with provided credentials
   - User assigned to tenant and granted initial role

1. **Project Creation**: 
   - User with MANAGER or COLLABORATOR role creates project → `utm_projects` record with `created_by_user_id`
   - MANAGER can assign additional users via `utm_project_members` (COLLABORATOR or VIEWER roles)

2. **Ingestion**: The **Parser Agent** populates `utm_objects` with source files.

3. **Process Locking**: When execution starts, `utm_process_locks` record created with `locked_by_user_email` for audit trail.

4. **Forensics (Phase 5)**: **Architect v2.0** analyzes schema and populates `utm_objects.metadata`.

5. **Normalization**: The **Kernel Agent** reads `utm_objects`, processes logic, and generates multiple records in `utm_logical_steps`.

6. **Column Mapping (Phase 6)**: User defines transformations in `utm_column_mappings`, including custom `logic` expressions.

7. **Change Management**: When a user edits a step in the UI, the system inserts a record into `utm_user_overrides` instead of overwriting the `ir_payload`.

8. **Code Generation (Phase 6)**: The **Output Cartridge** queries `utm_logical_steps`, applies any existing `utm_user_overrides`, and processes the Jinja2 template. Uses `metadata` for optimizations (partitioning, PII masking) and `variables` for parameterization.

9. **Governance (Phase 7)**: **Agent G** audits final code, generates certification report and runbook.

10. **Quality Contracts (Phase 9)**: **QualityService** reads `utm_column_mappings` rules and generates validation suites.

11. **Access Control**: 
    - RLS policies enforce tenant isolation (users can only see their tenant's data)
    - Project-level access enforced via `utm_project_members` checks
    - ADMIN can use Ghost Mode to access any tenant's data for support

---

## 3. Technical Considerations

### Multi-User Architecture (v3.9):
- **User/Tenant Separation**: Clear distinction between user identity (`utm_users`) and organizational entity (`utm_tenants`) enables multiple users per organization.
- **Role-Based Access Control**: 4-tier hierarchy ensures appropriate access levels (ADMIN > MANAGER > COLLABORATOR > VIEWER).
- **Project-Level Granularity**: `utm_project_members` allows fine-grained access control per project, not just tenant-wide.
- **Invitation Workflow**: Token-based email invitations with expiration provide secure onboarding without sharing credentials.
- **Audit Trail**: All projects track `created_by_user_id`, all locks track `locked_by_user_email` for complete accountability.

### Data Integrity & Governance:
- **Referential Integrity**: Maintaining Foreign Keys is vital for automatic column-level lineage and user/project relationships.
- **Auditability**: `utm_user_overrides` is the most important table for Compliance, explaining why final code differs from legacy logic.
- **Process Safety**: `utm_process_locks` prevents race conditions and data corruption from concurrent executions.
- **Row-Level Security**: Supabase RLS policies enforce tenant isolation automatically at database level.

### Scalability & Flexibility:
- **Scalability**: Using `JSONB` for payloads allows adding new operational types without altering physical table structures.
- **Metadata Evolution**: The `metadata` JSONB field in `utm_objects` is version-safe—Architect v2.0 fields coexist with future enhancements.
- **Variable Injection**: Variables in `utm_projects.settings.variables` are injected at code generation time, enabling environment-agnostic artifacts.
- **Provider Flexibility**: Per-tenant `utm_provider_vault` allows different organizations to use different LLM providers/keys.

### Security Best Practices:
- **Password Hashing**: All passwords stored with Bcrypt (`password_hash_bcrypt` in `utm_users`).
- **API Key Safety**: `utm_provider_vault` should implement encryption at rest for `api_key` column.
- **Token Expiration**: Invitation tokens expire automatically (`expires_at` in `utm_user_invitations`).
- **Lock Expiration**: Process locks auto-expire to prevent deadlocks (default 30 minutes).
- **Email Uniqueness**: `utm_users.email` has UNIQUE constraint to prevent duplicate accounts.

---

## 4. Foreign Key Relationships (v3.9)

### User & Organization Layer:
```
utm_tenants (tenant_id)
    ├─→ utm_users (tenant_id)              [1:N - One org has many users]
    ├─→ utm_projects (tenant_id)           [1:N - One org owns many projects]
    ├─→ utm_user_invitations (tenant_id)   [1:N - One org has many invitations]
    └─→ utm_provider_vault (tenant_id)     [1:N - One org has many provider configs]

utm_users (user_id)
    ├─→ utm_projects (created_by_user_id)  [1:N - One user creates many projects]
    ├─→ utm_project_members (user_id)      [1:N - One user has access to many projects]
    ├─→ utm_project_members (added_by)     [1:N - One user grants access to many others]
    └─→ utm_user_invitations (invited_by)  [1:N - One user invites many others]
```

### Project & Asset Layer:
```
utm_projects (project_id)
    ├─→ utm_objects (project_id)           [1:N - One project has many assets]
    ├─→ utm_project_members (project_id)   [1:N - One project has many members]
    ├─→ utm_execution_logs (project_id)    [1:N - One project has many log entries]
    ├─→ utm_file_inventory (project_id)    [1:N - One project indexes many files]
    ├─→ utm_design_registry (project_id)   [1:N - One project has many config entries]
    └─→ utm_process_locks (project_id)     [1:1 - One project has one active lock]

utm_objects (object_id)
    ├─→ utm_logical_steps (object_id)      [1:N - One asset has many IR steps]
    ├─→ utm_transformations (asset_id)     [1:N - One asset has many code outputs]
    └─→ utm_column_mappings (asset_id)     [1:N - One asset has many column mappings]

utm_logical_steps (step_id)
    └─→ utm_user_overrides (step_id)       [1:N - One step has many manual overrides]
```

### Configuration Layer:
```
utm_agent_catalog (agent_id)
    └─→ utm_agent_matrix (agent_id)        [1:N - One agent has many model assignments]

utm_model_catalog (model_id)
    └─→ utm_agent_matrix (model_id)        [1:N - One model used by many agents]
```

---

## 5. Migration History (v3.5 → v3.9)

### v3.9 (Multi-User Architecture) - Migrations 020-025:

**Migration 020**: Project-Level Invitations Foundation
- Created foundational structure for invitation system

**Migration 021**: Project Members Table (+ 021b RLS Fix)
- `CREATE TABLE utm_project_members` for granular project access
- Columns: `member_id`, `project_id`, `user_id`, `role`, `added_by`, `added_at`
- RLS policies for tenant isolation

**Migration 022**: Global System Catalog
- Simplified `utm_system_catalog` with unified `tech_id` approach
- Compliance rules stored in `config` JSONB

**Migration 023**: Admin Role & Deployment Fields
- Added `ADMIN` role support (platform-level operations)
- Deployment metadata fields in `utm_projects`

**Migration 024**: Remove `client_id` Simplification ⚠️ BREAKING
- Dropped `utm_clients` table entirely
- Removed `client_id` FK from `utm_projects`
- Consolidated organization concept into `utm_tenants`

**Migration 025**: Remove `org_name` Simplification ⚠️ BREAKING
- Removed `org_name` redundant column from `utm_tenants`
- Standardized on `display_name` for all entities

**Migration 026** (Implicit - Schema Refactoring):
- Created `utm_users` table separating user identity from tenant
- Created `utm_user_invitations` table for email-based onboarding
- Removed user-related columns from `utm_tenants`: `username`, `password_hash`, `password_hash_bcrypt`, `role`
- Added `created_by_user_id` to `utm_projects`
- Added `locked_by_user_email` to `utm_process_locks`

### v3.8 (Process Locking) - Migration 019:
- `CREATE TABLE utm_process_locks` for concurrent execution prevention
- Columns: `lock_id`, `project_id`, `phase`, `locked_at`, `expires_at`
- RPC function `force_expire_lock(uuid)` for admin override

### v3.5 (Cloud-Native Storage):
- Added `utm_file_inventory` for R2 object metadata caching
- Enhanced `utm_projects.settings` with source/target tech config
- Mandatory `tenant_id` enforcement across all tables

---

## 6. Recommended Next Steps

For developers implementing features that interact with the Metadata Store:

1. **Always Query User Context**: Include `user_id` and `tenant_id` in all operations for proper RLS enforcement.
2. **Check Project Membership**: Before allowing project operations, verify user has appropriate role via `utm_project_members`.
3. **Audit User Actions**: Log user email in operations (similar to `locked_by_user_email` pattern).
4. **Respect Role Hierarchy**: Implement checks for ADMIN > MANAGER > COLLABORATOR > VIEWER permissions.
5. **Handle Invitations**: Implement token validation, expiration checks, and email uniqueness for user invitations.
6. **Lock Project Operations**: Create `utm_process_locks` entry before long-running operations to prevent race conditions.
7. **Clean Up Resources**: Implement auto-expiration logic for invitations and locks to prevent stale data.
