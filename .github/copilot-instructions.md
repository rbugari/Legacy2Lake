# GitHub Copilot Instructions - Legacy2Lake UTM

**Project:** Legacy2Lake UTM v3.9 GA (Multi-Tenant AI-Powered ETL Modernization Platform)  
**Last Updated:** February 13, 2026  
**Architecture:** Multi-Agent System with Cartridge-Based Code Generation

---

## 🎯 Project Overview

Legacy2Lake is a **cloud-native, multi-tenant platform** that transforms legacy ETL architectures (SSIS, Informatica, DataStage, etc.) into modern Data Lake/Lakehouse solutions (Databricks, Snowflake, Fabric, BigQuery) using **6 specialized AI agents** and **15+ technology cartridges**.

### Core Architecture Components
- **Backend:** FastAPI (Python 3.11+) + Supabase PostgreSQL + LangChain/LangGraph
- **Frontend:** Next.js 15 + React 19 + TypeScript
- **AI:** 6 LLM Agents (A/Architect, S/Scout, C/Coder, F/Critic, G/Governance, D/Deliverer)
- **Storage:** Cloudflare R2 (asset storage) + Supabase (metadata/state)
- **Security:** Row-Level Security (RLS), JWT auth, multi-tenant isolation

### 6-Stage Migration Flow
1. **Discovery** - File upload to R2, asset inventory
2. **Triage** - Technology detection (Agent S), forensic analysis
3. **Drafting** - IR normalization (Agent C), zero-hardcode generation
4. **Refinement** - Code generation with cartridges, real-time validation
5. **Certification** - Quality scoring, compliance checks (Agent F)
6. **Handover** - COP bundle generation (Agent G)

---

## 🔒 CRITICAL: Multi-Tenancy Patterns (ALWAYS ENFORCE)

### Rule 1: Every Database Operation MUST Include tenant_id

```python
# ✅ CORRECT - Always filter by tenant_id
query = self.client.table("utm_projects").select("*")
if self.tenant_id:
    query = query.eq("tenant_id", self.tenant_id)
res = query.execute()

# ❌ WRONG - Missing tenant isolation
query = self.client.table("utm_projects").select("*").execute()
```

### Rule 2: All Services Must Accept tenant_id in Constructor

```python
# ✅ CORRECT - Multi-tenant service pattern
class MyService:
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)

# ❌ WRONG - No tenant context
class MyService:
    def __init__(self):
        self.db = SupabasePersistence()
```

### Rule 3: FastAPI Dependency Injection for Multi-Tenancy

```python
# ✅ CORRECT - Use dependency injection
from apps.api.routers.dependencies import get_db

@router.get("/projects")
async def list_projects(db: SupabasePersistence = Depends(get_db)):
    # db already has tenant_id from X-Tenant-ID header
    return await db.get_projects()

# ❌ WRONG - Manual tenant handling
@router.get("/projects")
async def list_projects(tenant_id: str):
    db = SupabasePersistence(tenant_id=tenant_id)
    return await db.get_projects()
```

### Rule 4: Validate UUIDs for tenant_id and project_id

```python
# ✅ CORRECT - UUID validation
from uuid import UUID

def validate_tenant_id(tenant_id: str) -> bool:
    try:
        UUID(tenant_id)
        return True
    except ValueError:
        return False
```

---

## 🤖 AI Agent Service Pattern (6 Agents)

### Standard Agent Structure

```python
from typing import Optional, Dict, Any
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class Agent{X}Service:
    """
    Agent {X}: {Purpose}
    """
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
    
    async def _get_llm(self, project_id: Optional[str] = None):
        """Resolves LLM client strictly from Agent Matrix (DB)"""
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        config = await db.resolve_agent_model("agent-{x}")
        
        if config["provider"] == "azure":
            return AzureChatOpenAI(
                deployment_name=config["deployment_name"],
                api_key=config["api_key"],
                azure_endpoint=config["endpoint"],
                api_version=config.get("api_version", "2024-05-01-preview")
            )
        else:  # openai, groq
            return ChatOpenAI(
                model=config["model"],
                api_key=config["api_key"],
                base_url=config.get("base_url")
            )
    
    async def _load_prompt(self, prompt_id: str = "agent_{x}_name") -> str:
        """Load prompt from database (global or tenant-specific)"""
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        return await db.get_prompt(prompt_id)
    
    async def save_prompt(self, prompt_id: str, content: str):
        """Save prompt to database (requires admin role)"""
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        await db.save_prompt(prompt_id, content)
```

### Agent Roster

| Agent | ID | Purpose | Key Method |
|-------|-----|---------|------------|
| **Architect** | agent-a | Discovery & forensics | `analyze_repository()` |
| **Scout** | agent-s | Technology detection | `detect_technology()` |
| **Coder** | agent-c | Code generation (IR → Target) | `transpile_task()` |
| **Critic** | agent-f | Code review & refinement | `critique_code()` |
| **Governance** | agent-g | Documentation & COP | `generate_documentation()` |
| **Deliverer** | agent-d | Handover package | `create_bundle()` |

---

## 📦 Import Resolution Pattern (All Service Files)

```python
# ✅ CORRECT - Multi-context import handling
try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.services.agent_c_service import AgentCService
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
        from services.agent_c_service import AgentCService
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence
        from .agent_c_service import AgentCService
```

**Rationale:** Supports execution from multiple contexts (API server, scripts, tests).

---

## 🗄️ Database Schema Reference

### Core Tables (15 total)

| Table | Purpose | RLS Enabled | Key Columns |
|-------|---------|-------------|-------------|
| `utm_tenants` | Multi-tenant root | ✅ | tenant_id (PK), name, plan |
| `utm_users` | User accounts | ✅ | user_id (PK), tenant_id (FK), role |
| `utm_projects` | Migration projects | ✅ | project_id (PK), tenant_id (FK), owner_id |
| `utm_project_members` | Access control | ✅ | project_id (FK), user_id (FK), role |
| `utm_objects` | Source assets | ✅ | object_id (PK), project_id (FK), source_tech |
| `utm_design_registry` | Medallion nodes | ✅ | node_id (PK), project_id (FK), layer |
| `utm_prompts` | System prompts | ⚠️ | prompt_id (PK), tenant_id (nullable), content |
| `utm_agent_matrix` | Agent-phase mappings | ✅ | tenant_id (FK), agent_id, model_id |
| `utm_provider_vault` | LLM API keys | ✅ | tenant_id (FK), provider, api_key |
| `utm_model_catalog` | Enabled LLM models | ✅ | tenant_id (FK), model_id, is_active |

**Full schema:** See [DATABASE_SCHEMA.md](../docs/DATABASE_SCHEMA.md)

### Supabase Query Pattern

```python
# ✅ CORRECT - RLS-aware query
async def get_projects(self) -> List[Dict[str, Any]]:
    query = self.client.table("utm_projects").select("*")
    if self.tenant_id:
        query = query.eq("tenant_id", self.tenant_id)
    return query.execute().data

# ✅ CORRECT - Join with RLS
projects_with_members = (
    self.client
    .table("utm_projects")
    .select("*, utm_project_members(user_id, role)")
    .eq("tenant_id", self.tenant_id)
    .execute()
)
```

---

## 🎨 FastAPI Router Pattern (CRUD Endpoints)

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from apps.api.routers.dependencies import get_db
from apps.api.services.persistence_service import SupabasePersistence

router = APIRouter(prefix="/api/v1/resource", tags=["resource"])

# Request/Response Models
class CreateResourceRequest(BaseModel):
    name: str
    description: Optional[str] = None
    settings: Optional[dict] = None

class ResourceResponse(BaseModel):
    resource_id: str
    tenant_id: str
    name: str
    created_at: str

# Endpoints
@router.get("/", response_model=List[ResourceResponse])
async def list_resources(db: SupabasePersistence = Depends(get_db)):
    """List all resources for current tenant"""
    return await db.get_resources()

@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(resource_id: str, db: SupabasePersistence = Depends(get_db)):
    """Get specific resource by ID"""
    resource = await db.get_resource(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource

@router.post("/", response_model=ResourceResponse, status_code=201)
async def create_resource(
    payload: CreateResourceRequest,
    db: SupabasePersistence = Depends(get_db)
):
    """Create new resource"""
    return await db.create_resource(payload.dict())

@router.delete("/{resource_id}", status_code=204)
async def delete_resource(resource_id: str, db: SupabasePersistence = Depends(get_db)):
    """Delete resource by ID"""
    await db.delete_resource(resource_id)
    return None
```

---

## ⚛️ React/TypeScript Component Pattern

### Standard Component Structure

```typescript
"use client";

import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '@/lib/auth-client';

interface ComponentProps {
    projectId: string;
    tenantId?: string;
}

interface DataItem {
    id: string;
    name: string;
    status: string;
}

export default function MyComponent({ projectId, tenantId }: ComponentProps) {
    const [data, setData] = useState<DataItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadData();
    }, [projectId]);

    const loadData = async () => {
        setIsLoading(true);
        setError(null);
        
        try {
            const response = await fetchWithAuth(
                `/api/v1/projects/${projectId}/items`
            );
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const result = await response.json();
            setData(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            console.error('[MyComponent] Load failed:', err);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) return <div>Loading...</div>;
    if (error) return <div className="text-red-500">Error: {error}</div>;

    return (
        <div className="p-4">
            {data.map(item => (
                <div key={item.id}>{item.name}</div>
            ))}
        </div>
    );
}
```

### fetchWithAuth Pattern

```typescript
// ✅ CORRECT - Always use fetchWithAuth for API calls
import { fetchWithAuth } from '@/lib/auth-client';

const response = await fetchWithAuth('/api/v1/endpoint', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key: 'value' })
});

// ❌ WRONG - Missing auth headers
const response = await fetch('/api/v1/endpoint');
```

---

## 🔬 Real-Time Validation (Sprint 8)

### Validation Service Usage

```python
from apps.api.services.validation_service import ValidationService

validator = ValidationService()

result = await validator.validate_code(
    code="from pyspark.sql import SparkSession...",
    tech_id="pyspark",  # pyspark, snowflake, dbt, fabric, aws, gcp
    layer="bronze",     # bronze, silver, gold
    context={"source_table": "customers", "target_table": "bronze_customers"}
)

if not result.is_valid:
    print(f"Errors: {result.errors_count}")
    print(f"Warnings: {result.warnings_count}")
    print(result.get_llm_feedback())
```

### Validation API Contracts

```python
# Request Model
class ValidateCodeRequest(BaseModel):
    code: str
    tech_id: str  # pyspark, snowflake, dbt, fabric, aws, gcp
    layer: str = "bronze"
    strict_mode: bool = True
    context: Optional[Dict[str, Any]] = None

# Response Model
class ValidateCodeResponse(BaseModel):
    is_valid: bool
    tech_id: str
    layer: str
    errors_count: int
    warnings_count: int
    info_count: int
    validated_at: str
    issues: List[ValidationIssueResponse]
    llm_feedback: Optional[str] = None
```

---

## 🎯 Cartridge System

### Cartridge Types

**Source Extraction Cartridges** (8 total):
- SQL Server, Oracle, MySQL, PostgreSQL
- Talend, Informatica, DataStage, Pentaho, SAP BODS

**Destination/Generation Cartridges** (6 total):
- Databricks (PySpark), Snowflake (SQL), Microsoft Fabric (Notebooks)
- BigQuery (SQL), Redshift (SQL), Salesforce (Apex)

### Cartridge Selection Pattern

```python
from apps.api.services.generation.cartridges.factory import CartridgeFactory

# Get appropriate cartridge based on project settings
cartridge = CartridgeFactory.get_cartridge(
    project_id=project_id,
    registry=design_registry,
    tenant_id=tenant_id
)

# Generate code using cartridge
output = await cartridge.generate(
    node_data=node_data,
    context=context
)
```

---

## 📝 Logging Pattern

```python
from apps.api.utils.logger import logger

# ✅ CORRECT - Structured logging with context
logger.info(
    f"[ServiceName] Processing started: project_id={project_id}, tenant_id={tenant_id}",
    "ServiceName"
)

logger.error(
    f"[ServiceName] Error occurred: {str(e)}",
    "ServiceName"
)

# For LLM calls (special decorator)
@logger.llm_debug("Agent-C-Developer")
async def transpile_task(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
    # Method implementation
    pass
```

---

## 🚫 Common Anti-Patterns to AVOID

### ❌ NO: Hardcoded Prompts (v4.0 Migration)

```python
# ❌ WRONG - Hardcoded template (v3.x legacy)
PYSPARK_TEMPLATE = """
from pyspark.sql import SparkSession
# ... hardcoded code
"""

# ✅ CORRECT - Load from database (v4.0)
prompt = await self.db.get_prompt(
    prompt_id="agent_c_bronze_pyspark",
    tech_stack="pyspark",
    pattern_type="bronze"
)
```

### ❌ NO: Missing Error Handling

```python
# ❌ WRONG - No error handling
result = await api_call()
return result

# ✅ CORRECT - Proper error handling
try:
    result = await api_call()
    return result
except Exception as e:
    logger.error(f"[Service] API call failed: {e}", "Service")
    raise HTTPException(status_code=500, detail=str(e))
```

### ❌ NO: Mixing Sync and Async

```python
# ❌ WRONG - Mixing sync/async incorrectly
async def my_function():
    result = sync_function()  # Blocking call in async context
    return result

# ✅ CORRECT - Use async throughout or run_in_executor
async def my_function():
    result = await async_function()
    return result
```

---

## 📚 Key Documentation Files

- **[SYSTEM_ARCHITECTURE.md](../docs/SYSTEM_ARCHITECTURE.md)** - Complete architecture overview
- **[DATABASE_SCHEMA.md](../docs/DATABASE_SCHEMA.md)** - All table schemas and RLS policies
- **[technical/system_prompts_and_agents.md](../docs/technical/system_prompts_and_agents.md)** - Agent system details
- **[technical/cartridge_manual.md](../docs/technical/cartridge_manual.md)** - Cartridge development guide
- **[API Contract Reference](.github/copilot/schemas/api-contracts.md)** - All Pydantic models
- **[Database Tables Reference](.github/copilot/schemas/database-tables.md)** - Table definitions

---

## 🎯 Code Generation Priorities

When generating code, prioritize in this order:

1. **Multi-tenancy enforcement** - Always include tenant_id filtering
2. **Type safety** - Use Pydantic models for validation
3. **Error handling** - Wrap in try/except with proper logging
4. **Async/await** - Use async throughout for I/O operations
5. **Documentation** - Include docstrings and type hints
6. **Testing** - Follow pytest patterns with fixtures

---

**Questions?** Refer to project documentation in `/docs` or ask for clarification on specific patterns.
