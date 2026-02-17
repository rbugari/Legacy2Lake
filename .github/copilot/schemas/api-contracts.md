# Legacy2Lake API Contracts Reference

**Version:** v3.9 GA  
**Last Updated:** February 13, 2026  
**Architecture:** Multi-Tenant FastAPI + Supabase

---

## Table of Contents

1. [Authentication API](#authentication-api)
2. [Projects API](#projects-api)
3. [Triage & Discovery API](#triage--discovery-api)
4. [Validation API](#validation-api)
5. [Transpilation & Orchestration API](#transpilation--orchestration-api)
6. [Governance & Refinement API](#governance--refinement-api)
7. [Visualization API](#visualization-api)
8. [System & Configuration API](#system--configuration-api)
9. [Agent Prompts API](#agent-prompts-api)
10. [Project Members API](#project-members-api)
11. [Process Locks API](#process-locks-api)
12. [Reports API](#reports-api)
13. [Lab API](#lab-api)

---

## Authentication API

**Base Path:** `/`  
**Tags:** `["Authentication"]`

### Endpoints

#### POST /login
Authenticate user with username/password (bcrypt + JWT).

**Request Model:** `LoginPayload`  
**Response Model:** `LoginResponse`

#### POST /change-password
User changes their own password.

**Request Model:** `PasswordChange`

#### GET /tenants
List all tenants (Admin only).

**Response:** List of tenant dictionaries

#### POST /tenants
Create new tenant with first MANAGER user (Admin only).

**Request Model:** `TenantCreate`

#### PATCH /tenants/{tenant_id}
Update tenant details (Admin only).

**Request Model:** `TenantUpdate`

#### DELETE /tenants/{tenant_id}
Remove tenant (Admin only).

#### GET /users
List all users in MANAGER's tenant.

**Response:** List of user dictionaries

#### POST /users
Create new user in tenant (MANAGER can create COLLABORATOR/VIEWER).

**Request Model:** `UserCreate`

#### PATCH /users/{user_id}
Update user details (role, active status).

**Request Model:** `UserUpdate`

#### POST /users/{user_id}/reset-password
Reset user password (MANAGER only).

**Request Model:** `UserPasswordReset`

#### POST /admin/impersonate
ADMIN impersonates another user for support.

**Request Model:** `ImpersonatePayload`

#### POST /admin/stop-impersonate
Stop impersonation session.

#### GET /admin/users
List all users across all tenants (Admin only).

### Models

#### LoginPayload
```python
class LoginPayload(BaseModel):
    username: str
    password: str
```

#### LoginResponse
```python
class LoginResponse(BaseModel):
    success: bool
    tenant_id: str
    user_id: str  # v3.9: Separate user identity
    display_name: str  # Organization display name
    role: Optional[str] = None
    message: str
```

#### TenantCreate
```python
class TenantCreate(BaseModel):
    username: str
    password: Optional[str] = None
    email: Optional[str] = None
    display_name: str  # Friendly organization name (required)
    tier: Optional[str] = "STANDARD"  # STANDARD, PREMIUM, or ENTERPRISE
    role: str = "MANAGER"  # First user of tenant is MANAGER
```

#### TenantUpdate
```python
class TenantUpdate(BaseModel):
    role: Optional[str] = None
    display_name: Optional[str] = None
    tier: Optional[str] = None
    password: Optional[str] = None
```

#### PasswordChange
```python
class PasswordChange(BaseModel):
    current_password: str
    new_password: str
```

#### UserCreate
```python
class UserCreate(BaseModel):
    """Model for MANAGER creating a new user in their tenant."""
    username: str
    email: str
    password: Optional[str] = None  # Auto-generated if not provided
    role: str = "COLLABORATOR"  # MANAGER, COLLABORATOR, or VIEWER
    display_name: Optional[str] = None
```

#### UserUpdate
```python
class UserUpdate(BaseModel):
    """Model for MANAGER updating a user."""
    role: Optional[str] = None
    is_active: Optional[bool] = None
    display_name: Optional[str] = None
    email: Optional[str] = None
```

#### UserPasswordReset
```python
class UserPasswordReset(BaseModel):
    """Model for MANAGER resetting user password."""
    new_password: str
```

#### ImpersonatePayload
```python
class ImpersonatePayload(BaseModel):
    target_user_id: str  # User to impersonate (preferably MANAGER)
```

---

## Projects API

**Base Path:** `/projects`  
**Tags:** `["Projects"]`

### Endpoints

#### GET /projects
List all projects for current tenant.

**Response:** List of project dictionaries

#### GET /projects/{project_id}
Get project details by UUID or name.

**Response:** Project metadata dictionary

#### POST /projects/create
Create new project from ZIP file, GitHub URL, or empty.

**Request:** Form data with fields:
- `name: str` (required)
- `project_id: str` (required)
- `source_type: str` (required - "zip", "github", "empty")
- `github_url: str` (optional)
- `overwrite: bool` (optional)
- `file: UploadFile` (optional)
- `origin: str` (optional - source technology)
- `destination: str` (optional - target technology)

**Response:**
```json
{
  "success": true,
  "project_id": "string"
}
```

#### DELETE /projects/{project_id}
Delete project from DB and filesystem.

**Response:**
```json
{
  "success": true,
  "details": {
    "db_deleted": true,
    "fs_deleted": true
  }
}
```

#### GET /projects/{project_id}/assets
Get project asset inventory.

**Response:**
```json
{
  "assets": [...]
}
```

#### GET /projects/{project_id}/stats
Get project statistics (core, ignored, pending).

**Response:** Stats dictionary

#### GET /projects/{project_id}/files
Get project file tree.

**Response:** File tree structure

#### GET /projects/{project_id}/files/content
Get specific file content.

**Query Params:** `path: str`

**Response:**
```json
{
  "content": "string"
}
```

#### POST /projects/{project_id}/layout
Save graph layout.

**Request Body:** `layout: Dict[str, Any]`

**Response:**
```json
{
  "success": true,
  "asset_id": "string"
}
```

#### GET /projects/{project_id}/layout
Retrieve graph layout.

**Response:** Layout dictionary

#### POST /projects/{project_id}/stage
Update project stage.

**Request Body:**
```json
{
  "stage": "string"
}
```

#### POST /projects/{project_id}/reset
Reset project data (clear assets, FS folders, reset stage/status).

**Response:**
```json
{
  "success": true
}
```

#### PATCH /projects/{project_id}/settings
Update project settings (source/target tech, etc.).

**Request Body:** Settings dictionary

**Response:**
```json
{
  "success": true
}
```

#### GET /projects/{project_id}/settings
Retrieve project settings.

**Response:** Settings dictionary

#### POST /projects/{project_id}/approve
Lock project scope and transition to DRAFTING.

**Response:**
```json
{
  "success": true,
  "status": "DRAFTING"
}
```

#### POST /projects/{project_id}/unlock
Unlock project scope and transition to TRIAGE.

**Response:**
```json
{
  "success": true,
  "status": "TRIAGE"
}
```

#### POST /projects/{project_id}/cancel
Request cancellation for long-running process.

**Response:**
```json
{
  "success": true
}
```

#### GET /projects/{project_id}/logs
Get project logs (triage, migration, refinement).

**Query Params:** `type: str` (default: "migration")

**Response:**
```json
{
  "logs": "string"
}
```

#### GET /projects/{project_id}/execution-logs
Fetch execution logs from database.

**Query Params:** `type: str` (default: "Triage")

**Response:**
```json
{
  "logs": "string"
}
```

#### GET /projects/{project_id}/triage/files
List all files in Triage folder for forensic analysis.

**Response:**
```json
{
  "success": true,
  "project_id": "string",
  "triage_path": "Triage",
  "file_count": 0,
  "file_types": {},
  "files": []
}
```

#### POST /projects/{project_id}/triage/upload
Upload files to Triage directory.

**Request:** Form data with multiple files

**Response:**
```json
{
  "success": true,
  "project_id": "string",
  "uploaded_count": 0,
  "files": []
}
```

### Models

**Note:** Projects API uses form data and dynamic dictionaries. No Pydantic models defined in router.

---

## Triage & Discovery API

**Base Path:** `/projects/{project_id}`  
**Tags:** `["Triage & Discovery"]`

### Endpoints

#### GET /discovery/project/{project_id}
Get all assets and system prompt for project.

**Response:**
```json
{
  "assets": [...],
  "prompt": "string",
  "source_tech": "string",
  "target_tech": "string"
}
```

#### GET /discovery/status/{project_id}
Get discovery/triage status.

**Response:**
```json
{
  "status": "TRIAGE",
  "stage": "1",
  "is_ready": false
}
```

#### POST /projects/{project_id}/triage
Run triage (discovery) process with agentic reasoning.

**Request Model:** `TriageParams`

**Response:**
```json
{
  "assets": [...],
  "nodes": [...],
  "edges": [...],
  "log": "string"
}
```

**Note:** Requires COLLABORATOR, MANAGER, or ADMIN role. Process locking enabled.

#### POST /projects/{project_id}/sync-graph
Rebuild graph layout based on selected assets.

**Response:**
```json
{
  "success": true,
  "nodes": [...],
  "edges": [...]
}
```

#### PATCH /projects/{project_id}/prompt
Update customized system prompt.

**Request Body:**
```json
{
  "prompt": "string"
}
```

#### PATCH /assets/{asset_id}
Update asset metadata (type, selected status).

**Request Body:** Updates dictionary

**Response:**
```json
{
  "success": true
}
```

#### POST /projects/{project_id}/context
Save human context for asset.

**Request Model:** `AssetContextPayload`

**Response:**
```json
{
  "success": true
}
```

#### GET /projects/{project_id}/context
Retrieve all context entries for project.

**Response:**
```json
{
  "contexts": [...]
}
```

#### POST /assets/{asset_id}/analyze-columns
Sprint 7: Deep column-level analysis.

**Request Body:** List of column metadata dictionaries

**Response:**
```json
{
  "asset_id": "string",
  "project_id": "string",
  "columns_profiled": 0,
  "pii_detected": 0,
  "partition_candidates": 0,
  "columns": [...],
  "summary": {}
}
```

#### GET /assets/{asset_id}/columns
Sprint 7: Retrieve profiled columns for asset.

**Response:**
```json
{
  "asset_id": "string",
  "columns": [...],
  "total_columns": 0
}
```

#### GET /projects/{project_id}/pii-heatmap
Sprint 7: PII heatmap data for entire project.

**Response:**
```json
{
  "total_columns": 0,
  "pii_columns": 0,
  "pii_percentage": 0.0,
  "pii_by_category": {},
  "high_risk_assets": [],
  "asset_pii_counts": {}
}
```

#### GET /projects/{project_id}/partition-recommendations
Sprint 7: Partition key recommendations.

**Query Params:** `min_score: float` (default: 0.5)

**Response:**
```json
{
  "project_id": "string",
  "recommendations": [...],
  "total_candidates": 0
}
```

### Models

#### TriageParams
```python
class TriageParams(BaseModel):
    system_prompt: Optional[str] = None
    user_context: Optional[str] = None
```

#### AssetContextPayload
```python
class AssetContextPayload(BaseModel):
    source_path: str
    notes: str
    rules: Optional[Dict[str, Any]] = None
```

---

## Validation API

**Base Path:** `/api/v1/validation`  
**Tags:** `["validation"]`

### Endpoints

#### POST /api/v1/validation/python
Validate Python code (PySpark, Fabric, AWS Glue, etc.).

**Request Model:** `ValidateCodeRequest`  
**Response Model:** `ValidateCodeResponse`

#### POST /api/v1/validation/sql
Validate SQL code (Snowflake, DBT, etc.).

**Request Model:** `ValidateCodeRequest`  
**Response Model:** `ValidateCodeResponse`

#### POST /api/v1/validation/generate-tests
Generate pytest test cases from code.

**Request Model:** `GenerateTestsRequest`  
**Response Model:** `GenerateTestsResponse`

#### GET /api/v1/validation/history/{project_id}
Get validation history for project.

**Query Params:**
- `limit: int` (default: 50)
- `offset: int` (default: 0)

**Response Model:** `List[ValidationHistoryItem]`

#### GET /api/v1/validation/stats/{project_id}
Get validation statistics for project.

**Response Model:** `ValidationStatsResponse`

### Models

#### ValidateCodeRequest
```python
class ValidateCodeRequest(BaseModel):
    """Request model for code validation"""
    code: str = Field(..., description="Code to validate")
    tech_id: str = Field(..., description="Technology ID (pyspark, snowflake, dbt, etc.)")
    layer: str = Field(default="bronze", description="Medallion layer (bronze, silver, gold)")
    strict_mode: bool = Field(default=True, description="If True, warnings count as errors")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context (source_table, target_table, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "from pyspark.sql import SparkSession\n\nspark = SparkSession.builder.appName('test').getOrCreate()",
                "tech_id": "pyspark",
                "layer": "bronze",
                "strict_mode": False,
                "context": {"source_table": "customers", "target_table": "bronze_customers"}
            }
        }
```

#### ValidationIssueResponse
```python
class ValidationIssueResponse(BaseModel):
    """Individual validation issue"""
    level: str
    check_name: str
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    suggestion: Optional[str] = None
```

#### ValidateCodeResponse
```python
class ValidateCodeResponse(BaseModel):
    """Response model for code validation"""
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

#### GenerateTestsRequest
```python
class GenerateTestsRequest(BaseModel):
    """Request model for test case generation"""
    code: str = Field(..., description="Code to generate tests for")
    tech_id: str = Field(..., description="Technology ID (pyspark, snowflake, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata (source_table, target_table, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "def transform_customers(df):\n    return df.filter(df.age > 18)",
                "tech_id": "pyspark",
                "metadata": {"source_table": "customers", "target_table": "bronze_customers"}
            }
        }
```

#### GenerateTestsResponse
```python
class GenerateTestsResponse(BaseModel):
    """Response model for test case generation"""
    test_code: str
    test_cases_count: int
    tech_id: str
    generated_at: str
```

#### ValidationHistoryItem
```python
class ValidationHistoryItem(BaseModel):
    """Validation history item"""
    validation_id: str
    project_id: str
    task_id: Optional[str]
    tech_id: str
    layer: str
    is_valid: bool
    errors_count: int
    warnings_count: int
    validated_at: str
```

#### ValidationStatsResponse
```python
class ValidationStatsResponse(BaseModel):
    """Validation statistics for a project"""
    project_id: str
    total_validations: int
    passed: int
    failed: int
    pass_rate: float
    avg_errors_per_validation: float
    most_common_errors: List[Dict[str, Any]]
```

---

## Transpilation & Orchestration API

**Base Path:** `/transpile`  
**Tags:** `["Transpilation & Orchestration"]`

### Endpoints

#### POST /transpile/task
Chain Agent C (Interpreter) and Agent F (Critic) for single task.

**Request Model:** `TranspileRequest`

**Response:**
```json
{
  "interpreter": {...},
  "critic": {...},
  "final_code": "string",
  "saved_at": "string"
}
```

#### POST /transpile/all
Iteratively transpile all nodes in a mesh.

**Request Model:** `TranspileAllRequest`

**Response:**
```json
{
  "summary": [...],
  "solution_path": "string"
}
```

#### POST /transpile/optimize
Re-run Agent F with specific optimization flags.

**Request Model:** `OptimizeRequest`

**Response:**
```json
{
  "original": "string",
  "optimized": "string",
  "score": 0,
  "suggestions": [...]
}
```

#### POST /transpile/orchestrate
Trigger full Migration Orchestrator (Agents C → F → G).

**Request Body:**
```json
{
  "project_id": "string",
  "limit": 0
}
```

**Response:** Orchestration result dictionary

**Note:** Requires COLLABORATOR, MANAGER, or ADMIN role. Process locking enabled for drafting, certification, and governance.

### Models

#### TranspileRequest
```python
class TranspileRequest(BaseModel):
    node_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
```

#### TranspileAllRequest
```python
class TranspileAllRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None
```

#### OptimizeRequest
```python
class OptimizeRequest(BaseModel):
    code: str
    optimizations: Optional[List[str]] = []
    context: Optional[Dict[str, Any]] = None
```

---

## Governance & Refinement API

**Base Path:** `/`  
**Tags:** `["Refinement & Governance"]`

### Endpoints

#### POST /refine/start
Legacy alias for starting refinement (used by RefinementView.tsx).

**Request Body:** Payload with `project_id`

**Response:** Refinement result dictionary

#### POST /projects/{project_id}/refinement/start
Trigger Refinement Phase (Profiler → Architect → Refactor → Ops).

**Request Body:** Payload dictionary

**Response:** Refinement result dictionary

**Note:** Process locking enabled. Updates stage to REFINEMENT (3) then GOVERNANCE (4) on success.

#### GET /projects/{project_id}/refinement/state
Get persisted state of Phase 3 (logs and profile).

**Response:**
```json
{
  "log": [],
  "profile": null
}
```

#### GET /projects/{project_id}/status
Get current governance status.

**Response:**
```json
{
  "status": "string"
}
```

#### GET /projects/{project_id}/governance
Get certification report and lineage.

**Response:** Certification report dictionary

#### GET /projects/{project_id}/audit
Trigger fresh audit execution (alias for /governance).

**Response:** Audit report dictionary

#### POST /governance/document
Generate and persist technical/governance documentation.

**Request Model:** `DocumentRequest`

**Response:**
```json
{
  "status": "success",
  "documentation": "string",
  "saved_at": "string"
}
```

#### GET /projects/{project_id}/export/governance
Stream project solution as full governance ZIP bundle.

**Response:** StreamingResponse with ZIP file

#### GET /projects/{project_id}/export/delivery
Stream technical deployment-only ZIP bundle (COP).

**Response:** StreamingResponse with ZIP file

### Models

#### RefinementRequest
```python
class RefinementRequest(BaseModel):
    project_id: str
    options: Optional[Dict[str, Any]] = None
```

#### DocumentRequest
```python
class DocumentRequest(BaseModel):
    project_name: str
    mesh: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
```

---

## Visualization API

**Base Path:** `/projects/{project_id}`  
**Tags:** `["Sprint 13: Visualization"]`

### Endpoints

#### GET /projects/{project_id}/generated-code
Get all generated code for project (aggregated view).

**Response:**
```json
{
  "code": "string",
  "metadata": {
    "object_id": "string",
    "object_name": "string",
    "tech_id": "string",
    "layer": "string",
    "timestamp": "string"
  }
}
```

#### GET /projects/{project_id}/objects/{object_id}/code
Get generated code for specific object.

**Response:**
```json
{
  "code": "string",
  "metadata": {
    "object_id": "string",
    "object_name": "string",
    "tech_id": "string",
    "layer": "string",
    "timestamp": "string",
    "validation": {},
    "optimization": {}
  }
}
```

#### GET /projects/{project_id}/schema
Get aggregated schema metadata for project.

**Response:**
```json
{
  "table_name": "string",
  "columns": [...],
  "row_count": 0,
  "primary_key": "string",
  "foreign_keys": [...]
}
```

#### GET /projects/{project_id}/objects/{object_id}/schema
Get schema metadata for specific object (Sprint 9).

**Response:**
```json
{
  "table_name": "string",
  "columns": [...],
  "row_count": 0,
  "primary_key": "string",
  "foreign_keys": [...],
  "version_number": 1
}
```

#### GET /projects/{project_id}/objects/{object_id}/schema/versions
Get schema version history (Sprint 10).

**Response:**
```json
{
  "versions": [...]
}
```

#### GET /projects/{project_id}/quality
Get quality metrics for entire project (Sprint 11).

**Response:**
```json
{
  "metrics": {
    "overall_score": 85.0,
    "completeness": 92.0,
    "accuracy": 88.0,
    "consistency": 90.0,
    "conformity": 85.0,
    "uniqueness": 95.0,
    "timeliness": 78.0
  },
  "violations": [],
  "anomalies": []
}
```

#### GET /projects/{project_id}/objects/{object_id}/quality
Get quality metrics for specific object.

**Response:** Quality metrics dictionary

#### GET /projects/{project_id}/performance
Get performance metrics (Sprint 12).

**Response:**
```json
{
  "cache": {
    "hit_rate": 75.5,
    "total_requests": 1250,
    ...
  },
  "optimization": {
    "total_optimizations_applied": 45,
    ...
  },
  "parallel": {
    "concurrent_tasks": 8,
    ...
  }
}
```

#### GET /projects/{project_id}/origin-analysis
Get origin system analysis from SSIS parsing (Sprint 8.5).

**Response:**
```json
{
  "source_type": "string",
  "server": "string",
  "database": "string",
  "package_name": "string",
  "connections": [],
  "statistics": {},
  "timestamp": "string"
}
```

#### GET /projects/{project_id}/transformations
Get transformations matrix (LOOKUP, Derived Column, etc.) from SSIS (Sprint 8.5).

**Response:**
```json
{
  "package_name": "string",
  "complexity_score": 0,
  "transformations_matrix": [],
  "total_transformations": 0,
  "recommendations": [],
  "timestamp": "string"
}
```

#### GET /projects/{project_id}/source-queries
Get source SQL queries extracted from SSIS components (Sprint 8.5).

**Response:**
```json
{
  "package_name": "string",
  "queries": [],
  "total_queries": 0,
  "main_query": "string",
  "timestamp": "string"
}
```

### Models

**Note:** Visualization API uses dynamic dictionaries. No Pydantic models defined in router.

---

## System & Configuration API

**Base Path:** `/`  
**Tags:** `["System & Administration"]`

### Endpoints

#### GET /config/technologies
Get valid source/target technologies from unified catalog.

**Response:** List of technology dictionaries

#### GET /prompts
Get all available system prompts from utm_prompts.

**Response:**
```json
{
  "prompts": [
    {
      "id": "string",
      "name": "string",
      "content": "string"
    }
  ]
}
```

#### POST /validate
Run validation test for prompt.

**Request Body:**
```json
{
  "agent_id": "string",
  "user_input": "string",
  "prompt_content": "string"
}
```

**Response:**
```json
{
  "success": true,
  "response": "string"
}
```

#### POST /scout/assess
Run forensic assessment using Agent S.

**Request Body:**
```json
{
  "project_id": "string",
  "file_list": [...]
}
```

**Response:** Assessment report dictionary

#### GET /catalog
Fetch global model catalog (filtered by tenant/vault).

**Response:**
```json
{
  "catalog": [...]
}
```

#### POST /catalog
Add custom model to catalog.

**Request Body:** Model dictionary

**Response:**
```json
{
  "success": true
}
```

#### GET /matrix
Fetch Agent Matrix for current tenant.

**Response:**
```json
{
  "matrix": [
    {
      "agent": "string",
      "provider": "string",
      "model": "string"
    }
  ]
}
```

#### POST /matrix
Update matrix for specific agent.

**Request Body:**
```json
{
  "agent": "string",
  "provider": "string",
  "model": "string"
}
```

#### GET /vault
Fetch credential status (masked) for current tenant.

**Response:**
```json
{
  "credentials": [...]
}
```

#### POST /vault/update
Update API Key for provider.

**Request Body:**
```json
{
  "provider": "string",
  "api_key": "string",
  "base_url": "string"
}
```

#### GET /cartridges
Get available cartridges and their status.

**Response:**
```json
{
  "cartridges": [...]
}
```

#### POST /cartridges
Add new cartridge to catalog.

**Request Body:** Cartridge dictionary

**Response:**
```json
{
  "success": true
}
```

#### POST /cartridges/{cartridge_id}/toggle
Toggle cartridge status (active/disabled).

**Request Body:**
```json
{
  "status": "active"
}
```

#### POST /cartridges/{cartridge_id}/config
Update cartridge configuration JSON.

**Request Body:**
```json
{
  "config": {}
}
```

#### DELETE /cartridges/{cartridge_id}
Remove cartridge from catalog.

**Response:**
```json
{
  "success": true
}
```

#### GET /cartridges/{cartridge_id}/knowledge
Get expert knowledge (improvements.md) for cartridge.

**Response:**
```json
{
  "knowledge": "string",
  "has_knowledge": true
}
```

#### PUT /cartridges/{cartridge_id}/knowledge
Update expert knowledge for cartridge.

**Request Body:**
```json
{
  "knowledge": "string"
}
```

**Response:**
```json
{
  "success": true,
  "message": "string"
}
```

#### GET /origins
Get origin cartridges (backward compatibility).

**Response:**
```json
{
  "origins": [...]
}
```

#### GET /destinations
Get destination cartridges (backward compatibility).

**Response:**
```json
{
  "destinations": [...]
}
```

#### GET /agents
Get all active agents with display names and descriptions.

**Response:**
```json
{
  "agents": [...]
}
```

#### PUT /agents/{agent_id}
Update agent details (Admin only).

**Request Body:** Agent update dictionary

**Response:**
```json
{
  "success": true,
  "message": "string"
}
```

### Models

#### CartridgeUpdate
```python
class CartridgeUpdate(BaseModel):
    id: str
    enabled: bool
```

#### ProviderUpdate
```python
class ProviderUpdate(BaseModel):
    id: str
    enabled: bool
    model: str = None
    api_key: str = None
    endpoint: str = None
```

#### SupportedTech
```python
class SupportedTech(BaseModel):
    tech_id: str
    role: str
    label: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool
    config_schema: Optional[Dict[str, Any]] = None
```

---

## Agent Prompts API

**Base Path:** `/prompts`  
**Tags:** `["Agent Prompts"]`

### Endpoints

#### GET /prompts/agent-a
Get current default system prompt for Agent A.

**Response Model:** `PromptResponse`

#### POST /prompts/agent-a
Update system prompt for Agent A.

**Request Model:** `PromptUpdate`

**Response:**
```json
{
  "success": true
}
```

#### GET /prompts/agent-c
Get current default system prompt for Agent C.

**Response Model:** `PromptResponse`

#### POST /prompts/agent-c
Update system prompt for Agent C.

**Request Model:** `PromptUpdate`

#### GET /prompts/agent-f
Get current default system prompt for Agent F.

**Response Model:** `PromptResponse`

#### POST /prompts/agent-f
Update system prompt for Agent F.

**Request Model:** `PromptUpdate`

#### GET /prompts/agent-g
Get current default system prompt for Agent G.

**Response Model:** `PromptResponse`

#### POST /prompts/agent-g
Update system prompt for Agent G.

**Request Model:** `PromptUpdate`

### Models

#### PromptUpdate
```python
class PromptUpdate(BaseModel):
    prompt: str
```

#### PromptResponse
```python
class PromptResponse(BaseModel):
    prompt: str
```

---

## Project Members API

**Base Path:** `/projects/{project_id}/members`  
**Tags:** `["Project Members"]`

### Endpoints

#### GET /projects/{project_id}/members
List all members assigned to specific project (MANAGER only).

**Response:**
```json
{
  "project": {...},
  "members": [...]
}
```

#### POST /projects/{project_id}/members
Add COLLABORATOR or VIEWER user to project (MANAGER only).

**Request Model:** `ProjectMemberAdd`

**Response:**
```json
{
  "success": true,
  "message": "string"
}
```

#### DELETE /projects/{project_id}/members/{user_id}
Remove user from project (MANAGER only).

**Response:**
```json
{
  "success": true,
  "message": "string"
}
```

#### PATCH /projects/{project_id}/members/{user_id}
Update member's role in project (MANAGER only).

**Request Body:**
```json
{
  "role": "COLLABORATOR"
}
```

**Response:**
```json
{
  "success": true,
  "message": "string"
}
```

### Models

#### ProjectMemberAdd
```python
class ProjectMemberAdd(BaseModel):
    """Add a user to a project."""
    user_id: str
    role: str  # COLLABORATOR or VIEWER
```

#### ProjectMemberResponse
```python
class ProjectMemberResponse(BaseModel):
    """Project member information."""
    project_id: str
    user_id: str
    username: str
    email: str
    role: str
    added_by: Optional[str]
    added_at: str
```

---

## Process Locks API

**Base Path:** `/locks`  
**Tags:** `["Process Locks"]`

### Endpoints

#### POST /locks/acquire
Acquire lock for process on project.

**Request Model:** `AcquireLockRequest`  
**Response Model:** `LockResponse`

Returns 423 Locked if already locked by another user/session.

#### POST /locks/release
Release process lock (by lock_id or project_id + process_type).

**Request Model:** `ReleaseLockRequest`

**Response:**
```json
{
  "message": "Lock released successfully"
}
```

#### POST /locks/check
Check if process is locked on project.

**Request Model:** `CheckLockRequest`  
**Response Model:** `LockStatusResponse`

#### POST /locks/force-release
Admin-only: Force release a lock.

**Request Model:** `ForceReleaseRequest`

**Response:**
```json
{
  "message": "Lock force-released successfully"
}
```

#### GET /locks/project/{project_id}
Get all locks (active and historical) for project.

**Response:**
```json
{
  "project_id": "string",
  "locks": [...]
}
```

#### GET /locks/all
Admin Only: Get all active locks across all projects (requires admin role).

**Response:**
```json
{
  "success": true,
  "count": 0,
  "locks": [...]
}
```

#### POST /locks/{lock_id}/force-release
Admin Only: Force-release specific lock by lock_id.

**Response:**
```json
{
  "success": true,
  "message": "string",
  "lock_id": "string"
}
```

### Models

#### AcquireLockRequest
```python
class AcquireLockRequest(BaseModel):
    project_id: str
    process_type: str  # 'triage', 'drafting', 'refinement', 'certification', 'governance'
```

#### ReleaseLockRequest
```python
class ReleaseLockRequest(BaseModel):
    lock_id: Optional[str] = None
    project_id: Optional[str] = None
    process_type: Optional[str] = None
```

#### CheckLockRequest
```python
class CheckLockRequest(BaseModel):
    project_id: str
    process_type: str
```

#### ForceReleaseRequest
```python
class ForceReleaseRequest(BaseModel):
    project_id: str
    process_type: str
```

#### LockResponse
```python
class LockResponse(BaseModel):
    lock_id: str
    project_id: str
    process_type: str
    locked_by_username: str
    locked_at: str
    expires_at: str
    status: str
```

#### LockStatusResponse
```python
class LockStatusResponse(BaseModel):
    is_locked: bool
    lock_info: Optional[Dict[str, Any]] = None
```

---

## Reports API

**Base Path:** `/projects/{project_id}/reports`  
**Tags:** `["Reports"]`

### Endpoints

#### POST /projects/{project_id}/reports/triage
Generate PDF Discovery Analysis Report (Post-Triage).

**Response:** PDF file attachment

**Headers:**
- `Content-Disposition: attachment; filename="{project_name}_triage_report.pdf"`
- `X-Suggested-Filename: {project_name}_triage_report.pdf`

#### POST /projects/{project_id}/reports/final
Generate PDF Migration Delivery Report (Final Handover).

**Response:** PDF file attachment

**Headers:**
- `Content-Disposition: attachment; filename="{project_name}_final_report.pdf"`
- `X-Suggested-Filename: {project_name}_final_report.pdf`

### Models

**Note:** Reports API uses dynamic dictionaries. No Pydantic models defined in router.

---

## Lab API

**Base Path:** `/lab`  
**Tags:** `["Lab"]`

### Endpoints

#### POST /lab/export
Export prompts to prompt_lab_export directory.

**Response:** Export result dictionary

#### POST /lab/import
Import prompt from lab path.

**Query Params:**
- `prompt_id: str`
- `lab_path: str`

**Response:** Import result dictionary

#### POST /lab/activate
Activate specific prompt version.

**Query Params:**
- `prompt_id: str`
- `version: int`

**Response:** Activation result dictionary

#### GET /lab/versions/{prompt_id}
List all versions of prompt.

**Response:**
```json
{
  "versions": [...]
}
```

#### GET /lab/download
Download prompt_lab_export.zip.

**Response:** ZIP file download

#### GET /lab/prompts/enriched
Get enriched prompt for specific agent and technology stack.

**Query Params:**
- `agent_id: str`
- `origin_tech: Optional[str]`
- `dest_tech: Optional[str]`

**Response:** Enriched prompt dictionary

### Models

**Note:** Lab API uses dynamic dictionaries. No Pydantic models defined in router.

---

## Common Patterns

### Multi-Tenancy Headers

All API requests must include tenant identification:

```http
X-Tenant-ID: <tenant_uuid>
```

For admin impersonation:

```http
X-Impersonate-User-ID: <user_uuid>
```

### Error Responses

Standard error format:

```json
{
  "detail": "Error message"
}
```

Process lock errors (423 Locked):

```json
{
  "error": "Process already running",
  "message": "Detailed message",
  "locked_by": {
    "username": "string",
    "locked_at": "string",
    "expires_at": "string"
  }
}
```

### Role-Based Access

- **VIEWER**: Read-only access
- **COLLABORATOR**: Can execute project phases
- **MANAGER**: Full project management + user management
- **ADMIN**: Platform-wide administration

Endpoints marked with `Depends(require_manager)` or `Depends(require_admin)` enforce role checks.

---

## Deprecated Endpoints

The following endpoints are deprecated in v3.9:

- User invitation endpoints (will use `utm_user_invitations` table in future)
- Legacy tenant password management (replaced by user-level auth)

---

**For implementation details, see:**
- [DATABASE_SCHEMA.md](../../docs/DATABASE_SCHEMA.md) - Database table definitions
- [SYSTEM_ARCHITECTURE.md](../../docs/SYSTEM_ARCHITECTURE.md) - Architecture overview
- [system_prompts_and_agents.md](../../docs/technical/system_prompts_and_agents.md) - Agent system details
