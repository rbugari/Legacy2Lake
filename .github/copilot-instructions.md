# GitHub Copilot Instructions - Legacy2Lake UTM

Last Updated: 2026-03-30
Status: v4.0 stabilized, production
Scope: Repository-wide engineering guidance

PROJECT_ROOT: . (Current Directory). Always execute from here. Do not assume other paths.

## Project Overview

Legacy2Lake UTM is a multi-tenant data modernization factory.

The platform ingests legacy assets such as:
- SQL
- SSIS `.dtsx`
- DDL
- manifests
- support files

It then orchestrates specialized agents and deterministic services to produce:
- Snowflake SQL
- PySpark
- dbt
- Microsoft Fabric outputs
- governance and handover artifacts

Current architecture is not a generic LLM wrapper.
It is a staged modernization platform with:
- FastAPI backend
- Next.js frontend
- Supabase for metadata and runtime configuration
- tenant-scoped storage for source and generated artifacts
- disk-canonical and DB-mirrored prompt model

## Current Operating Model

Use the stabilized v4.0 architecture as the source of truth.

Important realities:
- disk is canonical for Level 1 and Level 2 prompts
- Supabase is the runtime mirror
- project-specific custom instructions are optional
- the validated drafting chain is `Agent A -> Agent C -> Agent F -> Agent G`
- `QuickAssessmentService` is part of the real production flow
- `direct` mode is faithful translation, not redesign
- governance findings are not automatically runtime failures

Do not write code based on outdated assumptions such as:
- v3.9 GA is still the current operating model
- all migrations are PySpark-first
- Level 3 project instructions are required for normal operation
- Agent S is the only early-stage assessment path

## Core Principles

1. Multi-tenancy first
2. Reuse existing platform services before adding new abstractions
3. Prefer explicit staged behavior over hidden magic
4. Keep prompt architecture stable unless change is clearly justified
5. Treat project context as optional enrichment, not a patch for weak system behavior
6. Preserve the distinction between `direct` translation and medallion modernization

## Multi-Tenancy Rules

These are mandatory.

1. Every database query must respect `tenant_id` when applicable.
2. Services must accept `tenant_id` and `client_id` in constructors when they operate on tenant data.
3. FastAPI routes should prefer dependency injection through the existing database dependency.
4. Do not introduce cross-tenant reads or writes.
5. Validate UUID-like tenant and project identifiers when required.
6. Do not bypass current persistence patterns for convenience.

Preferred service pattern:

```python
class MyService:
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
```

Preferred router pattern:

```python
@router.get("/projects")
async def list_projects(db: SupabasePersistence = Depends(get_db)):
    return await db.list_projects()
```

Preferred Supabase query pattern:

```python
query = self.client.table("utm_projects").select("*")
if self.tenant_id:
    query = query.eq("tenant_id", self.tenant_id)
res = query.execute()
```

## Prompt Architecture Rules

Legacy2Lake uses a 3-level prompt model:

1. Level 1: agent prompt
2. Level 2: cartridge prompt
3. Level 3: project custom instructions

Guidance:
- do not hardcode prompt text into business logic unless clearly unavoidable
- prefer prompt loading through the existing prompt and persistence path
- do not treat Level 3 as required input
- do not add project-specific hacks into Level 1 or Level 2 logic
- preserve the canonical-on-disk plus runtime-in-DB model

## Stage Model

The product is stage-driven and the UI should respect that.

Current runtime stages:
1. Discovery
2. Triage
3. Drafting
4. Refinement
5. Certification
6. Handover

When changing stage behavior:
- preserve the operational landing model
- keep overview pages meaningful
- do not make transient `run-*` actions sticky views
- completed stages should bias toward summaries and reports
- active stages should bias toward logs and progress

## Agent And Service Guidance

Current LLM agents include:
- `agent-qa`
- `agent-s`
- `agent-a`
- `agent-c`
- `agent-f`
- `agent-g`
- `agent-d`

Current deterministic and support services include:
- `QuickAssessmentService`
- `DiscoveryService`
- `ValidationService`
- `TopologyService`
- `LibrarianService`

Guidance:
- use the existing service layer before creating parallel logic
- extend current services when the feature is a natural continuation of existing behavior
- avoid duplicate orchestration paths
- do not hardcode models, deployments, or providers inside agent services
- resolve LLM settings through tenant-scoped runtime configuration

## Import Resolution Pattern

Service files may need multi-context imports.
Preserve the current fallback style when working in existing service modules:

```python
try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence
```

Use this only where the file already follows that pattern or where the module must support multiple execution contexts.

## Backend Coding Guidance

Prefer:
- FastAPI routers with explicit request and response models
- async flows for I/O
- structured logging
- small service methods with clear ownership
- existing persistence and storage abstractions

Avoid:
- direct raw client calls scattered across routers when a service already exists
- blocking calls inside async routes
- hardcoded provider configuration
- bypassing tenant filters
- introducing schema writes without a migration

Before adding new backend code:
1. check if a similar service already exists
2. check if the data already exists in `utm_projects`, `utm_objects`, or related tables
3. check if the frontend already has a place to surface the new information
4. prefer consolidation over duplication

## Frontend Coding Guidance

Frontend stack is Next.js 15 + React 19 + TypeScript.

Prefer:
- existing stage views and current workspace navigation model
- `fetchWithAuth` for API requests
- consistent stage-level summaries and operational panels
- extending existing views before inventing new top-level routes
- reuse of existing metrics, dashboards, and summary components when they already fit

Avoid:
- generic placeholder UI
- introducing a new phase when a tab or section fits better
- `alert`, `confirm`, and hard reloads unless no existing modal or pattern exists
- duplicating backend-derived summaries in local-only logic
- building UI around assumptions that are not persisted or API-backed

When adding product-facing status concepts:
- make them explainable
- show reasons, blockers, or next actions
- do not present opaque scores without interpretation

## Data And Schema Guidance

Before adding tables or columns:
- verify whether the capability is already partially represented in `utm_projects`, `utm_objects`, or existing context tables
- add migrations for all schema changes
- keep tenant isolation explicit
- prefer simple project-level JSONB fields before introducing new workflow tables when validating a concept
- introduce a dedicated table only when the feature requires lifecycle, resolution states, ownership, or auditability

Examples:
- project-level summary or readiness state can start as a JSONB field on `utm_projects`
- a true gap or decision workflow should use a dedicated table rather than freeform JSON

## Product-Specific Guidance

Current near-term work should be interpreted through the real repo state.

Already present in partial form:
- quick assessment
- discovery scoring and blockers
- governance score and audit views
- handover readiness summary
- project and asset manual context

Not yet fully productized:
- formal readiness model
- executive summary as a unified experience
- formal gap and decision workspace

This means:
- readiness features should consolidate existing signals
- executive summaries should reuse existing reporting and governance surfaces
- gap workspace should be treated as a new workflow feature, not just another text field

## Validation And Testing

When changing behavior:
- verify tenant-safe access paths
- verify stage navigation still behaves correctly
- verify production summaries are grounded in persisted data
- verify existing report and governance flows still work
- prefer focused tests near the service or router you changed

If a feature depends on staged outputs:
- check Discovery and Triage signals first
- then check Drafting and Governance outputs
- do not assume every project has all later-stage artifacts available

## Historical Docs

The repo contains historical planning material.
Do not rely on older sprint language when current architecture docs or runtime behavior say otherwise.

Prefer these as source of truth:
- `README.md`
- `docs/INDEX.md`
- `docs/SYSTEM_ARCHITECTURE.md`
- `docs/technical/system_prompts_and_agents.md`
- `docs/technical/cartridge_manual.md`
- `docs/RELEASE_NOTES.md`

Use older planning docs only as context, not as authoritative implementation guidance.

## Final Rule

Be conservative with architecture changes.

For this repo, the best default is:
- consolidate existing capabilities
- preserve staged behavior
- preserve tenant isolation
- keep prompt architecture stable
- add new workflow entities only when the product truly needs them
            
