# Legacy2Lake UTM - System Architecture

**Version:** v3.9 + Sprint 1  
**Last Updated:** Febrero 10, 2026  
**Status:** Production Ready

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Multi-Tenancy Architecture](#multi-tenancy-architecture)
3. [Agent System Architecture](#agent-system-architecture)
4. [Cartridge System Architecture](#cartridge-system-architecture)
5. [Database Architecture](#database-architecture)
6. [Sprint 1: Database-First Prompts](#sprint-1-database-first-prompts)
7. [API Architecture](#api-architecture)
8. [Authentication & Security](#authentication--security)
9. [File Storage Architecture](#file-storage-architecture)
10. [Deployment Architecture](#deployment-architecture)
11. [Data Flow Diagrams](#data-flow-diagrams)
12. [Technology Stack](#technology-stack)

---

## Architecture Overview

### System Purpose
Legacy2Lake UTM is a **multi-tenant AI-powered platform** that transforms legacy data architectures into modern Data Lake/Lakehouse architectures using a **multi-agent system** with **cartridge-based code generation**.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Browser    │  │   Mobile     │  │  API Client  │          │
│  │   (React)    │  │  (Future)    │  │   (Future)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
└─────────┼──────────────────┼──────────────────┼───────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                    HTTPS / REST API
                             │
┌─────────────────────────────┼─────────────────────────────────────┐
│                       API LAYER (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Routers    │  │   Services   │  │ Middleware   │           │
│  │  (Endpoints) │  │ (Business    │  │ (Auth, CORS) │           │
│  │              │  │   Logic)     │  │              │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                  │                  │                   │
└─────────┼──────────────────┼──────────────────┼───────────────────┘
          │                  │                  │
          ├──────────────────┴──────────────────┤
          │                                      │
┌─────────┼──────────────────────────────────────┼───────────────────┐
│         │      AGENT ORCHESTRATION LAYER       │                   │
│  ┌──────▼───────┬───────────┬────────────┬────▼────┬──────────┐  │
│  │   Agent A    │  Agent C  │  Agent D   │ Agent F │ Agent G  │  │
│  │ (Architect)  │ (Coder)   │ (Auditor)  │(Refiner)│(Manager) │  │
│  ├──────────────┴───────────┴────────────┴─────────┴──────────┤  │
│  │                    Agent S (Scout)                          │  │
│  └──────────────────────────────────────────────────────────────┘ │
└────────┬──────────────────────────────────────┬────────────────────┘
         │                                       │
         │           ┌────────────────┐          │
         └──────────►│  LLM Service   │◄─────────┘
                     │  (Azure GPT-4) │
                     └────────┬───────┘
                              │
┌─────────────────────────────┼─────────────────────────────────────┐
│                    DATA & STORAGE LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Supabase    │  │ Cloudflare   │  │    Logs /    │           │
│  │ (PostgreSQL) │  │      R2      │  │  Monitoring  │           │
│  │   Database   │  │   Storage    │  │              │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Multi-Tenancy First**: Every table has `tenant_id` with Row-Level Security (RLS)
2. **Agent-Centric Design**: 6 specialized agents handle different aspects of the transformation
3. **Cartridge-Based Generation**: Technology-specific templates for code generation
4. **Database-First Prompts**: System prompts stored in DB for real-time updates (Sprint 1)
5. **Medallion Architecture**: Bronze → Silver → Gold layer structure
6. **User-Based Access**: Fine-grained permissions at project level (v3.9)

---

## Multi-Tenancy Architecture

### Tenant Isolation Model

```
┌──────────────────────────────────────────────────────────────────┐
│                    TENANT ISOLATION                               │
│                                                                   │
│  ┌─────────────────────────┐  ┌─────────────────────────┐       │
│  │     TENANT: demo3       │  │     TENANT: demo33      │       │
│  │  ┌───────────────────┐  │  │  ┌───────────────────┐  │       │
│  │  │  utm_users        │  │  │  │  utm_users        │  │       │
│  │  │  (5 users)        │  │  │  │  (3 users)        │  │       │
│  │  └───────────────────┘  │  │  └───────────────────┘  │       │
│  │  ┌───────────────────┐  │  │  ┌───────────────────┐  │       │
│  │  │  utm_projects     │  │  │  │  utm_projects     │  │       │
│  │  │  (2 projects)     │  │  │  │  (1 project)      │  │       │
│  │  └───────────────────┘  │  │  └───────────────────┘  │       │
│  │  ┌───────────────────┐  │  │  ┌───────────────────┐  │       │
│  │  │  utm_agents       │  │  │  │  utm_agents       │  │       │
│  │  │  (6 agents)       │  │  │  │  (6 agents)       │  │       │
│  │  └───────────────────┘  │  │  └───────────────────┘  │       │
│  │  ┌───────────────────┐  │  │  ┌───────────────────┐  │       │
│  │  │ utm_design_registry│ │  │  │ utm_design_registry│ │       │
│  │  │  (50 nodes)       │  │  │  │  (30 nodes)       │  │       │
│  │  └───────────────────┘  │  │  └───────────────────┘  │       │
│  └─────────────────────────┘  └─────────────────────────┘       │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐          │
│  │           GLOBAL (tenant_id IS NULL)                │          │
│  │  ┌──────────────────────────────────────────────┐  │          │
│  │  │  utm_prompts (24 cartridges + 6 agents)     │  │          │
│  │  └──────────────────────────────────────────────┘  │          │
│  └────────────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────────┘
```

### Row-Level Security (RLS) Pattern

**Every Table Follows This Pattern:**

```sql
-- Enable RLS
ALTER TABLE utm_table_name ENABLE ROW LEVEL SECURITY;

-- Policy: tenant_id isolation
CREATE POLICY "tenant_isolation_policy"
ON utm_table_name
USING (tenant_id::text = current_setting('request.jwt.claims', true)::json->>'tenant_id');

-- Policy: service role bypass (for admin operations)
CREATE POLICY "service_role_bypass_policy"
ON utm_table_name
TO service_role
USING (true);
```

**Application Context Setting:**

```python
# Before every database operation
await db.execute(
    "SELECT set_config('request.jwt.claims', $1, false)",
    json.dumps({"tenant_id": str(user_tenant_id)})
)
```

### User-Based Access Control (v3.9 Enhancement)

```
┌──────────────────────────────────────────────────────────────────┐
│                 PROJECT-LEVEL ACCESS CONTROL                      │
│                                                                   │
│  PROJECT: "Customer Data Migration"                              │
│                                                                   │
│  ┌─────────────────────┬──────────────────┬──────────────┐       │
│  │      User           │      Role        │  Permissions │       │
│  ├─────────────────────┼──────────────────┼──────────────┤       │
│  │ john@company.com    │  admin           │  All         │       │
│  │ mary@company.com    │  manager         │  Read+Write  │       │
│  │ bob@company.com     │  collaborator    │  Read+Write  │       │
│  │ jane@company.com    │  viewer          │  Read Only   │       │
│  └─────────────────────┴──────────────────┴──────────────┘       │
│                                                                   │
│  Role Hierarchy:                                                 │
│  admin > manager > collaborator > viewer                         │
│                                                                   │
│  Permissions Matrix:                                             │
│  ┌───────────────┬───────┬─────────┬───────────────┬────────┐   │
│  │               │ admin │ manager │ collaborator  │ viewer │   │
│  ├───────────────┼───────┼─────────┼───────────────┼────────┤   │
│  │ View Project  │  ✅   │   ✅    │      ✅       │   ✅   │   │
│  │ Edit Design   │  ✅   │   ✅    │      ✅       │   ❌   │   │
│  │ Run Agent     │  ✅   │   ✅    │      ✅       │   ❌   │   │
│  │ Invite Users  │  ✅   │   ✅    │      ❌       │   ❌   │   │
│  │ Manage Roles  │  ✅   │   ❌    │      ❌       │   ❌   │   │
│  │ Delete Project│  ✅   │   ❌    │      ❌       │   ❌   │   │
│  └───────────────┴───────┴─────────┴───────────────┴────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Agent System Architecture

### Agent Roster (6 Agents)

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT SYSTEM                              │
│                                                                  │
│  ┌──────────────────────┐         ┌──────────────────────┐      │
│  │      AGENT A         │         │      AGENT C         │      │
│  │    (Architect)       │────────▶│   (Code Generator)   │      │
│  │                      │         │                      │      │
│  │ - Analyze source     │         │ - Generate code      │      │
│  │ - Design Medallion   │         │ - Use cartridges     │      │
│  │ - Create registry    │         │ - DB-first prompts   │      │
│  └──────────┬───────────┘         └──────────┬───────────┘      │
│             │                                 │                  │
│             │                                 │                  │
│  ┌──────────▼───────────┐         ┌──────────▼───────────┐      │
│  │      AGENT D         │◀────────│      AGENT F         │      │
│  │    (Auditor)         │         │    (Optimizer)       │      │
│  │                      │         │                      │      │
│  │ - Audit compliance   │         │ - Review code        │      │
│  │ - Validate rules     │         │ - Optimize quality   │      │
│  │ - Check patterns     │         │ - Add best practices │      │
│  └──────────────────────┘         └──────────────────────┘      │
│             │                                 ▲                  │
│             │                                 │                  │
│  ┌──────────▼───────────┐         ┌──────────┴───────────┐      │
│  │      AGENT G         │         │      AGENT S         │      │
│  │  (Project Manager)   │────────▶│      (Scout)         │      │
│  │                      │         │                      │      │
│  │ - Track progress     │         │ - Detect gaps        │      │
│  │ - Coordinate agents  │         │ - Intelligence       │      │
│  │ - Manage workflow    │         │ - Recommendations    │      │
│  └──────────────────────┘         └──────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Interaction Flow

**Typical Pipeline: Source Analysis → Code Generation**

```
USER REQUEST: "Generate Bronze layer for customer table"
     |
     ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 1: Agent A (Architect)                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Input: Source schema (table: customers, 50 columns) │  │
│  │ Process: Analyze, design Medallion layers           │  │
│  │ Output: Design Registry Node                        │  │
│  │   {                                                  │  │
│  │     table_name: "customers",                        │  │
│  │     layer: "bronze",                                │  │
│  │     tech_id: "pyspark",                             │  │
│  │     columns: [50 column definitions]                │  │
│  │   }                                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
     |
     ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 2: Agent C (Code Generator)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Input: Design Registry Node + cartridge_prompt      │  │
│  │ Process:                                             │  │
│  │   1. Load prompt from DB (cartridge_pyspark_bronze) │  │
│  │   2. Inject node data into prompt                   │  │
│  │   3. Call Azure GPT-4 with 128K context             │  │
│  │   4. Generate PySpark code                          │  │
│  │ Output: 150-line PySpark script                     │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
     |
     ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 3: Agent F (Optimizer)                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Input: Generated code                                │  │
│  │ Process: Review, optimize, add best practices       │  │
│  │ Output: Optimized code with recommendations         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
     |
     ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 4: Agent D (Auditor)                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Input: Final code                                    │  │
│  │ Process: Audit compliance, validate patterns        │  │
│  │ Output: Compliance report                           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
     |
     ▼
   USER RECEIVES: Optimized, audited code ready for deployment
```

### Agent Configuration Per Tenant

Each tenant has **6 agent configurations** (one per agent):

```sql
SELECT agent_name, model, temperature, max_tokens
FROM utm_agents
WHERE tenant_id = 'demo3';

-- Result:
agent_a  │ gpt-4o │ 0 │ 128000
agent_c  │ gpt-4o │ 0 │ 128000
agent_d  │ gpt-4o │ 0 │ 128000
agent_f  │ gpt-4o │ 0 │ 128000
agent_g  │ gpt-4o │ 0 │ 128000
agent_s  │ gpt-4o │ 0 │ 128000
```

**Tenant-Specific Customization:**
- Different LLM providers (Azure, OpenAI, Anthropic)
- Different models (GPT-4, GPT-3.5, Claude)
- Different temperature settings
- Different token limits

---

## Cartridge System Architecture

### What is a Cartridge?

A **cartridge** is a technology-specific code generation template used by Agent C to generate production-ready code for specific data platforms.

### Cartridge Structure

```
┌──────────────────────────────────────────────────────────────┐
│                      CARTRIDGE ANATOMY                        │
│                                                               │
│  prompt_lab/cartridges/pyspark/                              │
│    ├── bronze_layer_instructions.md        (9.6 KB)         │
│    ├── silver_layer_instructions.md        (9.3 KB)         │
│    └── gold_layer_instructions.md          (11.3 KB)        │
│                                                               │
│  Each prompt contains:                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Role & Mission                                    │   │
│  │    "You are an expert PySpark engineer..."           │   │
│  │                                                       │   │
│  │ 2. Technical Context                                 │   │
│  │    - Bronze: Ingest raw data                         │   │
│  │    - Silver: Cleaned, validated                      │   │
│  │    - Gold: Business aggregates                       │   │
│  │                                                       │   │
│  │ 3. Code Structure Requirements                       │   │
│  │    - Imports                                         │   │
│  │    - Configuration                                   │   │
│  │    - Data reading                                    │   │
│  │    - Transformations                                 │   │
│  │    - Data writing                                    │   │
│  │                                                       │   │
│  │ 4. Quality Requirements                              │   │
│  │    - Error handling                                  │   │
│  │    - Logging                                         │   │
│  │    - Performance optimization                        │   │
│  │    - Best practices                                  │   │
│  │                                                       │   │
│  │ 5. Output Format                                     │   │
│  │    - Code fences expected                            │   │
│  │    - Comments required                               │   │
│  │    - No explanations outside code                    │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Supported Technologies (8 Cartridges)

```
┌────────────────────┬──────────┬──────────┬──────────┬─────────┐
│   Technology       │  Bronze  │  Silver  │   Gold   │  Status │
├────────────────────┼──────────┼──────────┼──────────┼─────────┤
│ PySpark            │  9.6 KB  │  9.3 KB  │ 11.3 KB  │   ✅    │
│ Snowflake (Snowpark)│  8.9 KB  │  9.7 KB  │  8.5 KB  │   ✅    │
│ MS Fabric          │  9.4 KB  │  9.7 KB  │ 12.1 KB  │   ✅    │
│ AWS Glue           │  9.6 KB  │  9.9 KB  │ 13.5 KB  │   ✅    │
│ dbt Core           │  8.2 KB  │  9.4 KB  │ 10.1 KB  │   ✅    │
│ GCP BigQuery       │  8.5 KB  │  7.2 KB  │  9.2 KB  │   ✅    │
│ Generic (Base)     │ 10.9 KB  │ 13.1 KB  │ 14.2 KB  │   ✅    │
│ Salesforce         │ 10.8 KB  │ 10.4 KB  │ 10.7 KB  │   ⚠️    │
└────────────────────┴──────────┴──────────┴──────────┴─────────┘
```

### Cartridge Selection Logic

```python
# Agent C cartridge resolution (simplified)

def select_cartridge(node_data: dict):
    """
    Resolves which cartridge to use based on node data.
    
    Priority:
    1. target_engine (user preference)
    2. tech_id (from design registry)
    3. Fallback to 'generic'
    """
    
    # Get target technology
    target = node_data.get("target_engine") or node_data.get("tech_id")
    
    # Normalize tech names
    tech_map = {
        "ms_fabric": "fabric",
        "base": "generic",
        "sf": "salesforce"
    }
    
    tech_id = tech_map.get(target, target)
    layer = node_data.get("layer", "bronze")
    
    # Load cartridge prompt from DB (Sprint 1)
    prompt_id = f"cartridge_{tech_id}_{layer}"
    prompt = await db.get_prompt(prompt_id, tenant_id=tenant_id)
    
    return prompt or fallback_to_filesystem(tech_id, layer)
```

---

## Database Architecture

### Schema Overview (15 Core Tables)

```
┌────────────────────────────────────────────────────────────────┐
│                     DATABASE SCHEMA (v3.9 + Sprint 1)          │
│                                                                 │
│  MULTI-TENANCY                                                 │
│  ├── utm_tenants              (Root isolation)                │
│  └── utm_users                (User management)               │
│                                                                 │
│  PROJECT MANAGEMENT (v3.9)                                     │
│  ├── utm_projects             (Projects)                      │
│  └── utm_project_members      (User-based access)             │
│                                                                 │
│  DESIGN REGISTRY                                               │
│  └── utm_design_registry      (Medallion nodes)               │
│                                                                 │
│  AGENT SYSTEM                                                  │
│  ├── utm_agents               (Agent configs)                 │
│  ├── utm_agent_matrix         (Phase mappings)                │
│  └── utm_prompts              (System prompts - Sprint 1)     │
│                                                                 │
│  SYSTEM CATALOG                                                │
│  └── utm_system_catalog       (Technology metadata)           │
│                                                                 │
│  PROCESS MANAGEMENT                                            │
│  └── utm_process_locks        (Concurrency control)           │
│                                                                 │
│  USER INVITATIONS                                              │
│  └── utm_invitations          (Invitation workflow)           │
│                                                                 │
│  FILE STORAGE                                                  │
│  └── utm_file_storage         (R2 metadata)                   │
│                                                                 │
│  LEGACY (Deprecated)                                           │
│  ├── utm_solution_context     (Old context storage)           │
│  ├── utm_column_mappings      (Old mappings)                  │
│  └── utm_tenants_old          (Migration artifact)            │
└────────────────────────────────────────────────────────────────┘
```

### Key Table: utm_design_registry

**Purpose:** Stores the Medallion Architecture design (nodes representing data transformations)

```sql
CREATE TABLE utm_design_registry (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES utm_tenants(id),
  project_id UUID NOT NULL REFERENCES utm_projects(id),
  node_id TEXT NOT NULL,              -- Unique node identifier
  node_data JSONB NOT NULL,           -- Complete node configuration
  status TEXT DEFAULT 'pending',      -- pending | in_progress | completed
  version INTEGER DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Example node_data structure:
{
  "table_name": "customers",
  "layer": "bronze",
  "tech_id": "pyspark",
  "source_system": "oracle",
  "columns": [
    {"name": "customer_id", "type": "STRING", "nullable": false},
    {"name": "customer_name", "type": "STRING", "nullable": true}
  ],
  "primary_keys": ["customer_id"],
  "partition_keys": ["created_date"],
  "cartridge_prompt": null  // Sprint 1: Now optional (DB-first)
}
```

### Key Table: utm_prompts (Sprint 1)

**Purpose:** Store system prompts (cartridges + agent prompts) for real-time updates

```sql
CREATE TABLE utm_prompts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES utm_tenants(id),  -- NULL = global
  prompt_id TEXT NOT NULL,                     -- cartridge_pyspark_bronze
  version_number INTEGER DEFAULT 1,
  content TEXT NOT NULL,                       -- Markdown prompt (~10KB)
  is_active BOOLEAN DEFAULT true,
  changelog TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  UNIQUE(tenant_id, prompt_id, version_number)
);

-- Example: Global cartridge prompt
INSERT INTO utm_prompts (tenant_id, prompt_id, content, metadata)
VALUES (
  NULL,
  'cartridge_pyspark_bronze',
  '# PySpark Bronze Layer Instructions\n\n...',
  '{"tech_id": "pyspark", "layer": "bronze", "seed_version": "1.0"}'
);

-- Example: Tenant-specific override
INSERT INTO utm_prompts (tenant_id, prompt_id, content, metadata)
VALUES (
  'demo3-tenant-id',
  'cartridge_pyspark_bronze',
  '# Custom PySpark Bronze for demo3\n\n...',
  '{"tech_id": "pyspark", "layer": "bronze", "custom": true}'
);
```

**Tenant Override Priority:**
1. **Tenant-specific prompt** (tenant_id = user's tenant)
2. **Global prompt** (tenant_id IS NULL)
3. **Filesystem fallback** (legacy cartridges/)

---

## Sprint 1: Database-First Prompts

### Architecture Before Sprint 1

```
┌────────────────────────────────────────────────────────────────┐
│                    LEGACY ARCHITECTURE                          │
│                                                                 │
│  User Request                                                  │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────┐                                           │
│  │   Agent C       │                                           │
│  │  (Code Gen)     │                                           │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  cartridge_instance.get_rules(node_data)             │     │
│  │  - Loads from filesystem                             │     │
│  │  - Requires deployment to update                     │     │
│  │  - No tenant customization                           │     │
│  └──────────────────────────────────────────────────────┘     │
│           │                                                     │
│           ▼                                                     │
│  prompt_lab/cartridges/pyspark/bronze_layer_instructions.md   │
└────────────────────────────────────────────────────────────────┘

Problems:
❌ Prompt updates require redeployment
❌ No tenant-specific customization
❌ No versioning
❌ No real-time updates
```

### Architecture After Sprint 1

```
┌────────────────────────────────────────────────────────────────┐
│                  DATABASE-FIRST ARCHITECTURE                    │
│                                                                 │
│  User Request                                                  │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────┐                                           │
│  │   Agent C       │                                           │
│  │  (Code Gen)     │                                           │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  3-TIER PROMPT LOADING (agent_c_service.py)          │     │
│  │                                                       │     │
│  │  Priority 1: node_data["cartridge_prompt"]           │     │
│  │  ├─ Check if explicit prompt provided                │     │
│  │  └─ Use if present (backward compatibility)          │     │
│  │                                                       │     │
│  │  Priority 2: utm_prompts table (NEW!)                │     │
│  │  ├─ Construct prompt_id: cartridge_{tech}_{layer}    │     │
│  │  ├─ Query: tenant-specific → global                  │     │
│  │  └─ Use if content length > 100                      │     │
│  │                                                       │     │
│  │  Priority 3: Filesystem fallback                     │     │
│  │  └─ cartridge_instance.get_rules(node_data)          │     │
│  └──────────────────────────────────────────────────────┘     │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  utm_prompts table                                   │     │
│  │  - 24 cartridge prompts                              │     │
│  │  - 6 agent prompts                                   │     │
│  │  - Tenant overrides supported                        │     │
│  │  - Version control                                   │     │
│  └──────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────┘

Benefits:
✅ Real-time prompt updates (no deployment)
✅ Tenant-specific customization
✅ Version control built-in
✅ 100% backward compatible
✅ Tenant override infrastructure
```

### Sprint 1 Code Changes

**File:** [apps/api/services/agent_c_service.py](../apps/api/services/agent_c_service.py#L118-L148)

```python
# NEW: Database-first prompt loading (Sprint 1)

# Priority 1: Check node_data (backward compatibility)
if node_data.get("cartridge_prompt"):
    rules = node_data["cartridge_prompt"]
    logger.info(f"Using cartridge_prompt from node_data")

# Priority 2: Load from utm_prompts (NEW!)
else:
    layer = node_data.get("layer", "bronze")
    cartridge_prompt_id = f"cartridge_{target_engine}_{layer}"
    
    logger.info(f"Loading prompt from DB: {cartridge_prompt_id}")
    
    db_prompt = await db.get_prompt(cartridge_prompt_id, tenant_id)
    
    if db_prompt and len(db_prompt) > 100:
        rules = db_prompt
        logger.info(f"✅ Using DB prompt (length: {len(db_prompt)})")
    else:
        # Priority 3: Filesystem fallback (legacy)
        rules = cartridge_instance.get_rules(node_data)
        logger.info(f"⚠️ Using filesystem fallback")
```

### Sprint 1 Migration Results

```
Phase 1: Discovery
  - Scanned prompt_lab/cartridges/
  - Found 24 cartridge files
  - 8 technologies x 3 layers

Phase 2: Reading
  - Read 24/24 files successfully
  - Total content: ~230 KB
  - Average prompt size: ~9.6 KB

Phase 3: Deduplication
  - Checked utm_prompts table
  - 0/24 existing (all new)
  - Ready to insert all

Phase 4: Insertion
  - 24/24 prompts inserted successfully
  - tenant_id: NULL (global)
  - version_number: 1
  - is_active: true

Status: ✅ 100% COMPLETE
```

---

## API Architecture

### REST API Endpoints

```
┌────────────────────────────────────────────────────────────────┐
│                        API STRUCTURE                            │
│                                                                 │
│  Authentication                                                │
│  ├── POST /auth/login          (Login)                        │
│  ├── POST /auth/register       (Register)                     │
│  └── POST /auth/refresh        (Refresh token)                │
│                                                                 │
│  Projects                                                      │
│  ├── GET    /projects          (List projects)                │
│  ├── POST   /projects          (Create project)               │
│  ├── GET    /projects/{id}     (Get project)                  │
│  ├── PUT    /projects/{id}     (Update project)               │
│  └── DELETE /projects/{id}     (Delete project)               │
│                                                                 │
│  Design Registry                                               │
│  ├── GET    /design-registry/{project_id}  (Get design)       │
│  ├── POST   /design-registry/{project_id}  (Add node)         │
│  ├── PUT    /design-registry/{node_id}     (Update node)      │
│  └── DELETE /design-registry/{node_id}     (Delete node)      │
│                                                                 │
│  Agents                                                        │
│  ├── POST /agents/architect    (Run Agent A)                  │
│  ├── POST /agents/coder        (Run Agent C)                  │
│  ├── POST /agents/auditor      (Run Agent D)                  │
│  ├── POST /agents/optimizer    (Run Agent F)                  │
│  ├── POST /agents/manager      (Run Agent G)                  │
│  └── POST /agents/scout        (Run Agent S)                  │
│                                                                 │
│  Tenants (Admin)                                               │
│  ├── GET    /tenants           (List tenants)                 │
│  ├── POST   /tenants           (Create tenant)                │
│  └── PUT    /tenants/{id}      (Update tenant)                │
│                                                                 │
│  Prompts (Admin)                                               │
│  ├── GET    /prompts           (List prompts)                 │
│  ├── POST   /prompts           (Create prompt)                │
│  ├── PUT    /prompts/{id}      (Update prompt)                │
│  └── GET    /prompts/{id}/versions  (Version history)         │
│                                                                 │
│  File Storage                                                  │
│  ├── POST   /files/upload      (Upload file)                  │
│  ├── GET    /files/{id}        (Download file)                │
│  └── DELETE /files/{id}        (Delete file)                  │
│                                                                 │
│  Health                                                        │
│  └── GET /health               (Health check)                 │
└────────────────────────────────────────────────────────────────┘
```

### Middleware Stack

```
Request Flow:
┌────────────────┐
│  Client Req    │
└────────┬───────┘
         │
         ▼
┌────────────────────────────────────────┐
│  1. CORS Middleware                    │
│     - Allow origins: ["*"]             │
│     - Allow credentials: true          │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  2. Auth Middleware                    │
│     - Extract JWT token                │
│     - Validate signature               │
│     - Extract tenant_id, user_id       │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  3. RLS Context Setting                │
│     - SET request.jwt.claims           │
│     - Inject tenant_id into session    │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  4. Business Logic (Router)            │
│     - Execute endpoint function        │
│     - Call services/agents             │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  5. Response Formatting                │
│     - JSON serialization               │
│     - Error handling                   │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────┐
│  Client Resp   │
└────────────────┘
```

---

## Authentication & Security

### JWT Token Structure

```json
{
  "sub": "user-uuid-here",
  "email": "john@company.com",
  "tenant_id": "demo3-tenant-uuid",
  "role": "admin",
  "exp": 1707600000,
  "iat": 1707596400
}
```

### Login Flow

```
┌────────────────────────────────────────────────────────────────┐
│                        LOGIN FLOW                               │
│                                                                 │
│  1. User submits credentials                                   │
│     POST /auth/login                                           │
│     Body: { email, password }                                  │
│         │                                                       │
│         ▼                                                       │
│  2. Backend validates credentials                              │
│     - Query utm_users by email                                │
│     - Verify password hash (bcrypt)                            │
│     - Check user.is_active                                     │
│         │                                                       │
│         ▼                                                       │
│  3. Generate JWT token                                         │
│     - Include: user_id, tenant_id, role                        │
│     - Sign with JWT_SECRET                                     │
│     - Set expiration (24 hours)                                │
│         │                                                       │
│         ▼                                                       │
│  4. Return token to client                                     │
│     Response: {                                                │
│       access_token: "eyJhbGci...",                             │
│       user: { id, email, role, tenant_id }                     │
│     }                                                           │
│         │                                                       │
│         ▼                                                       │
│  5. Client stores token                                        │
│     - localStorage or httpOnly cookie                          │
│     - Include in Authorization header:                         │
│       "Bearer eyJhbGci..."                                     │
│         │                                                       │
│         ▼                                                       │
│  6. Subsequent requests use token                              │
│     - Auth middleware validates                                │
│     - Extracts tenant_id for RLS                               │
│     - Allows access if valid                                   │
└────────────────────────────────────────────────────────────────┘
```

### Password Security

```python
# Password hashing (bcrypt)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# On registration/password change
hashed = pwd_context.hash(plain_password)  # Store this in DB

# On login
is_valid = pwd_context.verify(plain_password, hashed_password)
```

---

## File Storage Architecture

### Cloudflare R2 Integration

```
┌────────────────────────────────────────────────────────────────┐
│                   FILE STORAGE FLOW                             │
│                                                                 │
│  User uploads file (e.g., source schema CSV)                   │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  POST /files/upload                                  │     │
│  │  - Multipart form data                               │     │
│  │  - tenant_id from JWT                                │     │
│  │  - project_id from request                           │     │
│  └────────┬─────────────────────────────────────────────┘     │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  StorageFactory.get_storage()                        │     │
│  │  - Returns R2Storage instance                        │     │
│  └────────┬─────────────────────────────────────────────┘     │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  R2Storage.upload()                                  │     │
│  │  - Generate unique file_key                          │     │
│  │  - Path: {tenant_id}/{project_id}/triage/{filename}  │     │
│  │  - Upload to R2 bucket                               │     │
│  └────────┬─────────────────────────────────────────────┘     │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  Insert into utm_file_storage                        │     │
│  │  {                                                   │     │
│  │    tenant_id, project_id,                            │     │
│  │    file_key: "demo3/.../file.csv",                   │     │
│  │    file_name: "source_schema.csv",                   │     │
│  │    file_size: 1024,                                  │     │
│  │    content_type: "text/csv",                         │     │
│  │    storage_url: "https://r2.../demo3/.../file.csv"  │     │
│  │  }                                                   │     │
│  └────────┬─────────────────────────────────────────────┘     │
│           │                                                     │
│           ▼                                                     │
│  Return { file_id, file_key, storage_url }                    │
└────────────────────────────────────────────────────────────────┘
```

### Storage Path Structure

```
R2 Bucket: legacy2lake-utm-storage
├── demo3-tenant-uuid/
│   ├── project-1-uuid/
│   │   ├── triage/
│   │   │   ├── source_schema.csv
│   │   │   └── data_dictionary.xlsx
│   │   ├── drafting/
│   │   │   └── design_doc.md
│   │   └── refinement/
│   │       ├── bronze_customer.py
│   │       └── silver_customer.py
│   └── project-2-uuid/
│       └── ...
├── demo33-tenant-uuid/
│   └── ...
└── demo34-tenant-uuid/
    └── ...
```

---

## Deployment Architecture

### Production Environment

```
┌────────────────────────────────────────────────────────────────┐
│                   PRODUCTION DEPLOYMENT                         │
│                                                                 │
│  FRONTEND (Vercel)                                             │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  Next.js App                                         │     │
│  │  - Domain: utm.legacy2lake.com                       │     │
│  │  - CDN: Vercel Edge Network                          │     │
│  │  - SSR + Static Generation                           │     │
│  └────────┬─────────────────────────────────────────────┘     │
│           │  HTTPS                                             │
│           ▼                                                     │
│  BACKEND (Railway)                                             │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  FastAPI App                                         │     │
│  │  - Domain: api.utm.legacy2lake.com                   │     │
│  │  - Container: Python 3.11                            │     │
│  │  - Auto-scaling: 1-5 instances                       │     │
│  │  - Health checks: /health                            │     │
│  └────────┬─────────────────────────────────────────────┘     │
│           │                                                     │
│           ├──────────────────┬──────────────────┐              │
│           │                  │                  │              │
│           ▼                  ▼                  ▼              │
│  DATABASE           STORAGE          LLM PROVIDER              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Supabase    │  │ Cloudflare   │  │  Azure       │        │
│  │ (PostgreSQL) │  │      R2      │  │  OpenAI      │        │
│  │              │  │              │  │  GPT-4o      │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└────────────────────────────────────────────────────────────────┘
```

### Environment Variables (Production)

**Backend (Railway):**
```bash
# Database
SUPABASE_URL=https://<project-id>.supabase.co
SUPABASE_KEY=<service-role-key>

# LLM
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_API_VERSION=2023-05-15

# Storage
R2_ACCOUNT_ID=<cloudflare-account-id>
R2_ACCESS_KEY_ID=<access-key>
R2_SECRET_ACCESS_KEY=<secret-key>
R2_BUCKET_NAME=legacy2lake-utm-storage

# Security
JWT_SECRET=<random-256-bit-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS
FRONTEND_URL=https://utm.legacy2lake.com
```

**Frontend (Vercel):**
```bash
NEXT_PUBLIC_API_URL=https://api.utm.legacy2lake.com
NEXT_PUBLIC_ENV=production
NEXT_PUBLIC_SENTRY_DSN=<sentry-dsn>
```

---

## Data Flow Diagrams

### Complete User Journey: Source Analysis → Code Generation

```
USER: "I want to migrate my customer table to a Data Lake"

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: TRIAGE (Agent S - Scout)                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 1. User uploads source schema (CSV/Excel)                 │  │
│  │    - Columns: customer_id, name, email, created_date     │  │
│  │    - 50 columns total                                     │  │
│  │                                                           │  │
│  │ 2. Agent S analyzes schema                               │  │
│  │    - Detects data types                                  │  │
│  │    - Identifies primary keys                             │  │
│  │    - Recommends partitioning strategy                    │  │
│  │                                                           │  │
│  │ OUTPUT: Analyzed schema with recommendations             │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: DRAFTING (Agent A - Architect)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 1. Agent A receives analyzed schema                       │  │
│  │                                                           │  │
│  │ 2. Designs Medallion Architecture                        │  │
│  │    - Bronze: Raw ingestion (50 columns)                  │  │
│  │    - Silver: Cleaned + validated (48 columns)            │  │
│  │    - Gold: Business aggregates (15 columns)              │  │
│  │                                                           │  │
│  │ 3. Creates Design Registry Nodes                         │  │
│  │    - Node 1: customers_bronze                            │  │
│  │    - Node 2: customers_silver                            │  │
│  │    - Node 3: customers_gold                              │  │
│  │                                                           │  │
│  │ OUTPUT: 3 nodes in utm_design_registry                   │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: REFINEMENT (Agent C - Code Generator)                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ FOR EACH NODE (Bronze, Silver, Gold):                    │  │
│  │                                                           │  │
│  │ 1. User selects target technology (e.g., PySpark)        │  │
│  │                                                           │  │
│  │ 2. Agent C loads cartridge prompt from DB                │  │
│  │    - prompt_id: cartridge_pyspark_bronze                 │  │
│  │    - ~9.6 KB instruction set                             │  │
│  │                                                           │  │
│  │ 3. Injects node_data into cartridge prompt              │  │
│  │    - Table name, columns, keys                           │  │
│  │    - 50 column definitions                               │  │
│  │                                                           │  │
│  │ 4. Calls Azure GPT-4o                                    │  │
│  │    - Context: ~20K tokens (prompt + data)                │  │
│  │    - Temperature: 0 (deterministic)                      │  │
│  │    - Response time: 10-25 seconds                        │  │
│  │                                                           │  │
│  │ 5. Receives generated code                               │  │
│  │    - 150-line PySpark script                             │  │
│  │    - Imports, config, read, transform, write             │  │
│  │                                                           │  │
│  │ OUTPUT: 3 code files (bronze.py, silver.py, gold.py)     │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: OPTIMIZATION (Agent F - Optimizer)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 1. Agent F receives generated code                        │  │
│  │                                                           │  │
│  │ 2. Reviews for best practices                            │  │
│  │    - Error handling present?                             │  │
│  │    - Logging comprehensive?                              │  │
│  │    - Performance optimized?                              │  │
│  │                                                           │  │
│  │ 3. Suggests improvements                                 │  │
│  │    - Add caching for repeated reads                      │  │
│  │    - Optimize partition strategy                         │  │
│  │    - Add data quality checks                             │  │
│  │                                                           │  │
│  │ OUTPUT: Optimized code + recommendations                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 5: AUDIT (Agent D - Auditor)                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 1. Agent D receives final code                            │  │
│  │                                                           │  │
│  │ 2. Audits for compliance                                 │  │
│  │    - Medallion Architecture rules                        │  │
│  │    - Data governance policies                            │  │
│  │    - Security best practices                             │  │
│  │                                                           │  │
│  │ 3. Generates compliance report                           │  │
│  │    - ✅ Architecture compliant                            │  │
│  │    - ✅ Security checks passed                            │  │
│  │    - ⚠️ Consider adding PII masking                       │  │
│  │                                                           │  │
│  │ OUTPUT: Compliance report + final approval               │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
                    USER RECEIVES:
         3 production-ready code files
         + optimization recommendations
         + compliance report
         
         READY FOR DEPLOYMENT TO DATA LAKE
```

---

## Technology Stack

### Backend Stack
```
Language:           Python 3.11+
Framework:          FastAPI 0.104+
ORM:                Raw SQL (Supabase client)
LLM Integration:    LangChain
Password Hashing:   passlib (bcrypt)
JWT:                python-jose
Async:              asyncio, httpx
Testing:            pytest (future)
```

### Frontend Stack
```
Language:           TypeScript 5+
Framework:          Next.js 14
UI Library:         React 18
Styling:            Tailwind CSS
Components:         shadcn/ui
State Management:   React Context + hooks
HTTP Client:        fetch API
```

### Database
```
Platform:           Supabase (PostgreSQL 14+)
Migrations:         SQL files (manual)
Security:           Row-Level Security (RLS)
Indexes:            B-tree, GIN (JSONB)
```

### Storage
```
Provider:           Cloudflare R2
Protocol:           S3-compatible
SDK:                boto3
```

### LLM
```
Provider:           Azure OpenAI
Model:              GPT-4o
Context Window:     128K tokens
Temperature:        0 (deterministic)
```

### Infrastructure
```
Backend Hosting:    Railway
Frontend Hosting:   Vercel
Database Hosting:   Supabase Cloud
Storage Hosting:    Cloudflare R2
```

---

## Performance Characteristics

### Response Times (Dev Environment)
```
Health Check:              < 50ms
User Login:                100-200ms
Project List:              100-300ms
Design Registry Load:      200-500ms
Agent A (Design):          5-15 seconds
Agent C (Code Gen):        10-30 seconds
Agent F (Optimize):        8-20 seconds
Prompt Load from DB:       10-20ms (Sprint 1)
```

### Scalability Limits (Current)
```
Concurrent Users:          10-50 (estimated)
DB Connections:            Pooled (10-20)
LLM Rate Limit:            60 requests/min (Azure)
File Upload Size:          100 MB (configurable)
Design Registry Size:      1000 nodes per project (tested)
```

### Optimization Opportunities
```
Priority 1: Redis cache for prompts (reduce DB calls)
Priority 2: LLM response streaming (improve UX)
Priority 3: Parallel agent execution (reduce total time)
Priority 4: JSONB indexing (speed up registry queries)
Priority 5: CDN for static assets (reduce latency)
```

---

## Security Considerations

### Current Security Measures
```
✅ Row-Level Security (RLS) on all tables
✅ JWT token authentication
✅ Password hashing (bcrypt)
✅ HTTPS/TLS encryption
✅ Environment variables (no secrets in code)
✅ CORS configuration
✅ Input validation (Pydantic)
✅ SQL injection protection (parameterized queries)
```

### Future Security Enhancements
```
⏳ Rate limiting (API endpoint protection)
⏳ 2FA/MFA support
⏳ API key management for programmatic access
⏳ Audit logging (track all user actions)
⏳ Data encryption at rest (Supabase supports)
⏳ WAF (Web Application Firewall)
⏳ Penetration testing
```

---

## Monitoring & Observability

### Current Monitoring
```
✅ Health check endpoint (/health)
✅ Python logging (INFO level)
✅ Railway dashboard (CPU, memory, requests)
✅ Vercel analytics (page views, performance)
✅ Supabase dashboard (DB queries, connections)
```

### Planned Monitoring (Post-Launch)
```
⏳ Sentry (error tracking)
⏳ Prometheus + Grafana (metrics)
⏳ ELK Stack (log aggregation)
⏳ Uptime monitoring (Pingdom/UptimeRobot)
⏳ APM (Application Performance Monitoring)
⏳ User analytics (Mixpanel/Amplitude)
```

---

## Appendix: Glossary

- **Medallion Architecture**: Bronze (raw) → Silver (cleaned) → Gold (aggregated) data layers
- **Cartridge**: Technology-specific code generation template (~10KB markdown prompt)
- **Design Registry**: Database representation of Medallion Architecture design (nodes)
- **RLS**: Row-Level Security, Supabase/PostgreSQL feature for multi-tenant isolation
- **Agent**: Specialized AI assistant (A=Architect, C=Coder, D=Auditor, F=Optimizer, G=Manager, S=Scout)
- **Tenant**: Isolated customer environment (e.g., demo3, demo33)
- **Sprint 0**: Testing & validation phase (87.5% pass rate)
- **Sprint 1**: Database migration for system prompts (100% complete)

---

**Document Version:** 1.0  
**Last Updated:** Febrero 10, 2026  
**Maintained By:** Development Team  
**Status:** ✅ Complete and Current
