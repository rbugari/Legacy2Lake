# Documentation Index - Legacy2Lake v4.0

> Last Updated: 2026-02-17  
> Architecture Version: **4.0 Zero-Hardcode GA** ✅  
> Status: **PRODUCTION READY** - Sprint 14 Phase 2 Released February 17, 2026

## 🚀 V4.0 LATEST: Zero-Hardcode Architecture (February 2026)

### ⭐ Sprint 14 Phase 2: UI Modernization & Performance (IN PROGRESS)
**Status:** 🔄 Active Development - Critical Performance Fixes Deployed

**Major Achievements:**
- ✅ **Unified Sidebar Architecture**: Lifted-state pattern across all stage views
- ✅ **95%+ Performance Improvement**: Backend load reduced from 30+ req/s to 0.1 req/s
- ✅ **Execution Status Feedback**: Visual indicators (⚠️ no data, 🔄 processing, ✅ ready)
- ✅ **Circular Dependency Elimination**: Zero infinite re-render loops
- 🔍 **Under Investigation**: Stage mismatch and metrics refresh issues

**Performance Crisis Resolution:**
- **Problem**: Backend bombarded with 30+ requests/second, 1-4s each
- **Root Cause**: Circular dependencies (fetchProject → fetchLayout → fetchTriageLogs → infinite loop)
- **Solution**: 
  - Increased polling intervals (3s → 10s for metrics, 3s → 5s for logs)
  - Broke callback dependency chains in useEffect hooks
  - Immediate file loading on component mount
- **Impact**: UI responsive, no more freezing, predictable backend load

**Technical Implementation:**
- **Frontend Changes:**
  - `TriageView.tsx`: Removed internal activeSection state, fixed circular deps
  - `DraftingView.tsx`: Props-based section control, JSX structure fixes
  - `RefinementView.tsx`: Turbopack parser fixes, IIFE language detection
  - `workspace/page.tsx`: Fixed to use projectStage (not activeView)
  - `SidebarHeader.tsx`: Added execution status banners with useMemo
  - `useSidebarMetrics.ts`: Polling interval optimization (3s → 10s)
- **Debug Logging**: Added comprehensive console tracking for diagnosis

---

### ⭐ Sprint 14 Phase 1: Database-Driven Parser Registry (COMPLETED)
**Status:** ✅ Production Ready - TRUE Zero-Hardcode Implementation

**Revolutionary Change:**
- **Before (v3.x):** Adding new technology (Talend, Oracle, etc.) required SERVICE CODE CHANGES ❌
- **After (v4.0):** Adding new technology requires only DB INSERT - ZERO code changes ✅

**Implementation Summary:**

**Backend Changes:**
- ✅ **knowledge_packet_service.py** refactored (-230 lines net)
  - Removed 6 tech-specific methods (`_extract_ssis_intelligence`, etc.)
  - Added `_resolve_parser_config()` - DB-driven resolver
  - Added `_extract_intelligence_dynamic()` - Data-driven extraction
  - Tests: 25/25 passing (100%)

**Database Schema:**
- ✅ **utm_source_tech_catalog** - Technology definitions (10 registered)
- ✅ **utm_parser_catalog** - Parser configurations with JSONB medulla_config
- ✅ **resolve_parser_by_tech()** - SQL function for parser resolution
- ✅ **list_supported_technologies()** - SQL function for tech listing

**Documentation:**
- ✅ [ZERO_HARDCODE_ARCHITECTURE.md](ZERO_HARDCODE_ARCHITECTURE.md) - 600+ lines, full architecture
- ✅ [DEPLOYMENT_STATUS_PHASE_B_ZERO_HARDCODE.md](DEPLOYMENT_STATUS_PHASE_B_ZERO_HARDCODE.md) - Deployment guide

**Key Achievement:**
```python
# Add Talend support = 2 SQL INSERTs, NO code changes
INSERT INTO utm_source_tech_catalog VALUES ('talend', ...);
INSERT INTO utm_parser_catalog VALUES ('parser-talend', '{...}'::jsonb, ...);
# Done! Service automatically uses new parser
```

**Technologies Supported:**
- ✅ SSIS (fully implemented)
- 🟡 Oracle, DataStage, Informatica (stub configs ready)
- ⚪ Talend, Pentaho, SAP BODS, Ab Initio, Teradata (registered, awaiting configs)
- ✅ Generic (fallback for unknown techs)

---

## 🎉 V3.9 Previous Updates (February 2026)

### ✨ Visualization Dashboards Integration (COMPLETED)
**Status:** ✅ Production Ready - 67% V3.9 Coverage (4/6 Phases)

#### **New Features Integrated:**

**Phase 2: Triage (Completed Previously)**
- ✅ **Quality Dashboard**: Real-time data quality metrics (completeness, accuracy, consistency)
- ✅ **Schema Viewer**: Interactive table/column explorer with data types
- ✅ **PII Heatmap**: Sensitive data detection with severity levels
- ✅ **Partition Recommendations**: Intelligent partitioning strategy suggestions

**Phase 3: Drafting** ⭐ NEW
- ✅ **Quality Sub-Tab**: Added as 5th execution tab alongside Logs/Code/Schema/Performance
- Component: `QualityDashboard` integrated into code generation phase
- Purpose: Monitor data quality metrics during IR generation

**Phase 4: Refinement** ⭐ NEW (4 Major Additions)
- ✅ **Code Review Tab**: Side-by-side diff viewer for generated vs legacy code
- ✅ **Schema Validation Tab**: Verify schema integrity post-transpilation
- ✅ **Quality Validation Tab**: End-to-end quality checks before deployment
- ✅ **Performance Metrics Tab**: Cache hit rates, optimization stats, parallel efficiency

#### **Technical Implementation:**
- **Frontend Changes:**
  - `DraftingView.tsx`: +1 component, expanded state type, new Quality render
  - `RefinementView.tsx`: +4 components, expanded TABS from 2→6, new icon imports
- **Backend Changes:**
  - `visualization.py`: Added 10 new endpoints (code, schema, quality, performance)
  - Mock data fallback strategy for development without full database schema
  - Contextual schema generation based on table name patterns
- **Infrastructure:**
  - `run.py`: Enhanced with Node.js/npm validation, .env checking, port cleanup

#### **Value Delivered:**
- **Integrated:** $240K of $400K total V3.9 value (60%)
- **Phases Complete:** 4/6 (Discovery, Triage, Drafting, Refinement)
- **Remaining:** 2/6 (Deployment, Observability) - Scheduled for future sprints

---

## Quick Start

- **[Installation Guide](INSTALL.md)** - Setup instructions for backend, frontend, and cloud services
- **[Introduction](INTRODUCTION.md)** - Platform overview, architecture, and key concepts
- **[User Guide](usr/GUIA_DEL_USUARIO.md)** - Spanish language user manual

## Core Documentation

### Platform Overview
- **[Introduction](INTRODUCTION.md)** - Vision, architecture, agent workforce
- **[Installation](INSTALL.md)** - Environment setup, R2 config, provider setup
- **[Release Notes](RELEASE_NOTES.md)** - Version history and changes
- **[Roadmap](ROADMAP.md)** - Future plans and features
- **[Roles & Onboarding](ROLES_AND_ONBOARDING.md)** - User roles and onboarding flow

### Migration Workflow (6 Stages)

1. **[Stage 1: Discovery](stages/STAGE_1_DISCOVERY.md)** - File upload, R2 storage, inventory
2. **[Stage 2: Triage](stages/STAGE_2_TRIAGE.md)** - Tech detection (Technology Scout), forensics
3. **[Stage 3: Drafting](stages/STAGE_3_DRAFTING.md)** - IR normalization, knowledge injection
4. **[Stage 4: Refinement](stages/STAGE_4_REFINEMENT.md)** - Code generation, cartridges
5. **[Stage 5: Certification](stages/STAGE_5_CERTIFICATION.md)** - Compliance, scoring, COP
6. **[Stage 6: Handover](stages/STAGE_6_HANDOVER.md)** - Deployment package, signed URLs

## Technical Documentation

### Architecture & Design
- **[Architecture Overview](technical/architecture.md)** - System design and components
- **[AI Infrastructure](technical/ai_infrastructure.md)** - Agent mesh and LLM integration
- **[System Prompts & Agents](technical/system_prompts_and_agents.md)** - Prompt Lab, Technology Scout, knowledge injection
- **[Data Model](technical/data_model.md)** - Database schema and relationships
- **[Database Structure](technical/database_structure.md)** - Supabase tables and RLS

### Development Guides
- **[Cartridge Manual](technical/cartridge_manual.md)** - Build custom code generators (6 cartridges)
- **[Universal IR](technical/universal_ir.md)** - Intermediate representation format
- **[Function Registry](technical/function_registry.md)** - Cross-platform function mapping
- **[Transpilation Examples](technical/transpilation_examples.md)** - Code generation samples
- **[API Contract](technical/api_contract.md)** - REST API endpoints and schemas

### Quality Assurance
- **[Test Scenarios](technical/test_scenarios.md)** - Testing strategies and examples

## Business & Planning
- **[Business Review](BUSINESS_REVIEW.md)** - Market analysis and value proposition
- **[Comprehensive Review](COMPREHENSIVE_REVIEW.md)** - Detailed system analysis
- **[Roadmap](ROADMAP.md)** - Strategic direction and future releases

### Release Planning
- **[Release Plan v3.9 Simplified](planning/RELEASE_PLAN_SIMPLE_v3.9.md)** - Multi-user simplified roadmap ✅ COMPLETED
- **[Release Plan v4.0 Simplified](planning/RELEASE_PLAN_v4.0_SIMPLIFIED.md)** ⭐ - Zero-Hardcode Core (ACTIVE)
- **[Future v4.0 Vision](planning/future_v4.0.md)** - Original comprehensive v4.0 vision (reference)
- **[Specification](SPECIFICATION.md)** - Functional and technical requirements

## v3.9 Key Features (CURRENT RELEASE)

### 🎨 Advanced Visualization Dashboards (February 2026)
- **QualityDashboard**: Real-time metrics for completeness, accuracy, consistency, conformity
- **SchemaViewer**: Interactive table/column explorer with data types and constraints
- **PIIHeatmap**: Privacy compliance with sensitive data detection
- **PartitionRecommendations**: AI-powered partitioning strategy suggestions
- **PerformanceDashboard**: Cache efficiency, optimization stats, parallel processing metrics
- **CodeViewer**: Syntax-highlighted diff viewer for legacy vs modern code

**Integration Coverage:**
- ✅ Triage (Phase 2): 4 visualization tabs
- ✅ Drafting (Phase 3): Quality sub-tab added
- ✅ Refinement (Phase 4): 4 new validation tabs
- ⏳ Deployment (Phase 5): Pending integration
- ⏳ Observability (Phase 6): Pending integration

### Multi-User Support
- **Separated User Identity**: `utm_users` table separates user accounts from `utm_tenants`
- **Role-Based Access**: ADMIN, MANAGER, COLLABORATOR, VIEWER roles with distinct permissions
- **User Management UI**: Complete UI at `/settings` for MANAGER to manage team
- **Project Access Control**: Granular project-level permissions via `utm_project_members`

### Platform Admin Dashboard
- **All Users View**: Cross-tenant view of all users in the system
- **Advanced Filters**: Filter by tenant, role, or search by username/email
- **Password Reset**: Platform ADMIN can reset any user's password
- **Ghost Mode**: Impersonate users for troubleshooting (see system as that user)

### Simplified Data Model
- **Removed Redundancy**: Eliminated `client_id` and `org_name` columns
- **Organization Model**: `utm_tenants` represents organizations with `display_name` and `tier`
- **User Separation**: Users stored in dedicated `utm_users` table

### Tenant Console (`/settings`)
- **User Management Tab**: Create, edit, and manage team members
- **Project Access Tab**: Control who accesses which projects
- **Role Selector**: Assign COLLABORATOR or VIEWER roles
- **Status Management**: Activate/deactivate users

## v3.8 Key Features

### Process Locking & Data Integrity (NEW)
- **Process Locks**: Prevents concurrent execution on same project (data corruption prevention)
- **Lock Management**: Admin interface with force-release capabilities
- **Smart Timeouts**: Process-specific lock durations (triage: 60min, drafting: 30min, etc.)
- **Auto-Expiration**: Stale locks automatically expire via database RPC function

### Professional UI Components (NEW)
- **ProcessLockModal**: Amber-themed modal showing lock details and user guidance
- **ProcessExecutionModal**: Real-time agent pipeline visualization with progress tracking
- **ReportsLibraryModal**: Unified interface for all project reports with stage-aware availability
- **Admin Tools**: Process lock viewer with force-release and auto-refresh

### Governance & Architecture (NEW)
- **3-Layer Ownership Model**: Clear boundaries (Admin/Tenant/User)
- **Technology Catalog Enforcement**: Strict validation against system catalog
- **Cost Ownership**: Formalized tenant responsibility for provider costs
- **Governance Documentation**: Comprehensive rules in GOVERNANCE_RULES.md

### Reports & Documentation (ENHANCED)
- **PDF Reports**: Triage (Discovery) and Final (Delivery) reports with Playwright generation
- **Reports Library**: Centralized modal access from workspace header (📚 icon)
- **Version-Agnostic Templates**: No hardcoded version numbers for maintenance-free updates
- **Professional Branding**: Jinja2 templates with logos, watermarks, headers/footers

### Cloud-Native Storage
- **Cloudflare R2**: S3-compatible object storage
- **Signed URLs**: Time-limited secure downloads (4h expiry)
- **Tenant Isolation**: Prefix-based data segregation
- **File Inventory**: `utm_file_inventory` for fast listing

### Multi-Tenancy
- **Row-Level Security (RLS)**: Supabase policies enforce tenant isolation
- **Provider Vault**: Encrypted API key storage per tenant
- **Agent Matrix**: Custom LLM assignments per tenant

### AI Agent System
- **Agent S (Scout)**: Technology detection (TSQL, PL/SQL, SSIS, etc.)
- **Agent A (Analyst)**: Dependency and risk analysis
- **Agent B (Interpreter)**: IR generation from legacy code
- **Agent C (Coder)**: Modern code synthesis with cartridges
- **Agent F (Critic)**: Code review and optimization
- **Agent G (Governor)**: Compliance auditing and COP generation

### Prompt Laboratory
- **22 Knowledge Modules**: 7 core + 9 origins + 6 destinations
- **Knowledge Injection**: Dynamic prompt enhancement with tech-specific rules
- **Contract Enforcement**: Schema validation for agent outputs
- **Versioning**: `origins/tsql/grammar_v1.json`, etc.

### Cartridge System
- **6 Production Cartridges**: Databricks, Snowflake, Fabric, BigQuery, Redshift, Salesforce
- **Jinja2 Templates**: Human-readable code generation
- **Type/Function Mapping**: Canonical IR → Target platform
- **Medallion Architecture**: Bronze, Silver, Gold layers

### Certified Output Package (COP)
- **Compliance Scoring**: 0-100 with SEC/PERF/BP/DOC checks
- **Modernization Runbook**: Auto-generated deployment guide
- **Variable Injection**: CI/CD-ready placeholders
- **Deployment Options**: Manual, CI/CD, or Direct cloud

## Obsolete Documentation (Pre-v3.8)

The following files may contain outdated information and should be reviewed:
- Files referencing local file storage (pre-R2 migration, before v3.5)
- Single-tenant architecture documentation (before v3.6)
- Hardcoded provider configurations (before v3.6)
- Individual report download buttons (consolidated in v3.8 Reports Library)

## Contributing

When updating documentation:
1. Mark version changes clearly (`v3.6 Update:`)
2. Use GitHub alerts for important notes (NOTE, TIP, WARNING, IMPORTANT)
3. Include code examples and diagrams (Mermaid)
4. Link files using `[text](file:///absolute/path)` format
5. Update this index when adding new docs

## Support

- **GitHub**: [https://github.com/rbugari/Legacy2Lake](https://github.com/rbugari/Legacy2Lake)
- **Documentation Issues**: Create GitHub issues with `docs` label
