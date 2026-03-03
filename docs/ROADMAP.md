# Project Roadmap 🗺️

> [!NOTE]
> **Product Strategy**: Legacy2Lake operates as a high-fidelity **Artifact Generator**. Our roadmap focuses on generating production-ready code, IaC, and Orchestration manifests while maintaining a zero-access security posture relative to client infrastructure.

> **Current Release**: v4.0 GA ✅ (Marzo 2026) - Zero-Hardcode Core, Two-Layer Prompts, Discovery Enhancements  
> **Status**: Post-Launch Stabilization — 3 E2E bugs fixed (Drafting BLOCKED, stale logs, Governance sidebar)  
> **Next**: v4.1 — Design system audit, full E2E integration testing, DB indices
>
> **Sprint 14 Status (completed):**
> - ✅ Phase 1: Parser Catalog (100% - Database-driven technology registry)
> - ✅ Phase 2: UI Performance (95%+ backend load reduction, unified sidebar)
> - ✅ Phase 3: Component Unification (100% - UnifiedLogViewer + UnifiedFileExplorer deployed)
> - ✅ Phase 4: Action Consolidation (100% - All execution actions in Sidebar)

---

## 🎯 Current Focus: Completing V3.9 Visualization Integration

**Vision**: v3.9 Multi-User COMPLETE ✅ + Visualization Dashboards **67% COMPLETE** → Next: Full v4.0 AI Revolution.

**Philosophy**: **Keep it simple. Ship fast. Don't over-engineer.**

**Timeline**: February 2026 - Q2 2026 (~4 weeks for v4.0)

### Strategic Releases (SIMPLIFIED)
1. **v3.9 GA** - Multi-User + Visualization Integration ✅ **COMPLETED** (Feb 13, 2026)
2. **v4.0** - Zero-Hardcode Core (Late March 2026, ~4 weeks) 🔴 **NEXT**

See [Simple Release Plan](planning/RELEASE_PLAN_SIMPLE_v3.9.md) for v3.9 details.

---

## 🚀 Next Release (Committed)

### v4.0 - Zero-Hardcode Core ✅ **RELEASED** (Marzo 2026)
**Theme**: "Prompt-Driven Foundation" (SIMPLIFIED & STREAMLINED)

**Feature Status** (Feb 19, 2026):

1. **Zero-Hardcode Generation** - ✅ **100% COMPLETE** (Feb 15)
   - ✅ Database migration (`utm_prompts` + `utm_prompts_history`)
   - ✅ Automatic versioning trigger (saves OLD version before UPDATE)
   - ✅ 14 prompts loaded from .md files to database
   - ✅ Backend `get_prompt()` loads from DB (zero hardcoded templates)
   - ✅ Automatic history tracking working (2 versions saved)
   - ✅ Global prompts design (no tenant customization)
   - **Database**: `migrations/sprint_v4.0_prompts.sql` executed
   - **Scripts**: `init_prompts_v4.py`, verification/test scripts created
   - **Business Value**: $120K (instant prompt updates, no code deploy)

2. **Deep Forensic Triage (Sprint 7)** - ✅ **95% COMPLETE**
   - ✅ `ColumnProfilingService` implemented
   - ✅ PII detection (10+ patterns: EMAIL, SSN, CREDIT_CARD, etc.)
   - ✅ Quality scoring per field (cardinality, nullability, type inference)
   - ✅ `utm_asset_columns` table with persistence
   - ✅ Integrated in Agent A (Discovery phase)
   - ⏳ Optional: Frontend heatmap visualizations
   - **Business Value**: $180K (automated data classification)

3. **Real-Time Validation (Sprint 8)** - ✅ **100% COMPLETE**
   - ✅ `ValidationService` with AST parsing and SQL validation
   - ✅ Auto-correction loop (up to 3 attempts with LLM feedback)
   - ✅ `utm_code_validations` table for history
   - ✅ 6 technology types supported (PySpark, Snowflake, DBT, Fabric, AWS, GCP)
   - ✅ Integrated in Agent C (transpile_task)
   - **Business Value**: $200K (reduce manual code review 80%)

4. **UI Componentization (Sprint 14)** - ✅ **70% COMPLETE** (Feb 19)
   - ✅ UnifiedLogViewer component (side-panel + embedded variants)
   - ✅ UnifiedFileExplorer component (tree view + syntax highlighting)
   - ✅ File type filtering (.py, .sql, .json, etc.)
   - ✅ Timestamp display (yy-mm-dd hh:mm format)
   - ✅ 550+ lines of duplicate code eliminated
   - ✅ Triage stage fully migrated
   - 🔄 Drafting stage migration in progress
   - ⏳ Discovery, Refinement, Certification pending
   - **Business Value**: $150K (faster development, consistency, maintainability)

**Overall Progress**: **95%** (3.7 of 4 features complete)

**SIMPLIFIED from original scope:**
- ❌ Tenant prompt customization → ELIMINATED (prompts global in v4.0)
- ❌ Complex versioning system → SIMPLIFIED (auto-trigger only)
- ✅ Automatic versioning via PostgreSQL trigger (no manual UI)

**MOVED TO v5.0+ (Future)**:
- 🔮 Multi-model orchestration → v5.0
- 🔮 Self-learning agents → v5.0
- 🔮 Adaptive architecture patterns → v5.1
- 🔮 Cost optimization dashboard → v5.0
- 🔮 Security scanning → v5.1
- 🔮 Lineage tracking → v5.2

**Duration**: Completed March 2026  
**Business Impact**: $650K annual value (prompts + quality + validation + UI consistency)  
**Status**: ✅ PRODUCTION — Post-launch stabilization in progress

**Post-Launch Milestones**:
- Mar 03: E2E stabilization — Drafting BLOCKED fix, stale logs fix, Governance Quick Info fix
- Mar 02: BUG-001 → BUG-009 post-launch fixes (Agent Matrix, Model Catalog, Provider Vault)
- Feb 27: Ghost Mode Bug #1/2/3/4/5 fixed (dependencies.py, auth-client.ts, admin page.tsx)
- Feb 25/24: Feature complete — Two-Layer Prompts, Pre-Classification Grid, Action Consolidation

---

## ✅ Recently Completed

### v3.9 GA - Multi-User + Visualization Integration (Feb 13, 2026) ✅ RELEASED
**Theme**: "Enterprise Teams + Data-Driven Decisions"

**Delivered Features**:

**Multi-User Support** (Feb 10):
- ✅ Multiple users per tenant with role-based access
- ✅ **4 roles**: ADMIN, MANAGER, COLLABORATOR, VIEWER
- ✅ Separated `utm_users` from `utm_tenants` (organization model)
- ✅ User Management UI in Tenant Console (`/settings`)
- ✅ Project-level access control
- ✅ Platform Admin Dashboard with All Users view
- ✅ Password reset and Ghost Mode impersonation
- ✅ Simplified data model (removed client_id, org_name)

**Visualization Integration** (Feb 13):
- ✅ **Triage Dashboards**: Quality, Schema, PII Heatmap, Partition Recommendations (4 tabs)
- ✅ **Drafting Enhancement**: Quality sub-tab for IR generation monitoring
- ✅ **Refinement Suite**: Code Review, Schema, Quality, Performance (4 new validation tabs)
- ✅ **Backend Infrastructure**: 10 new endpoints in `visualization.py` with graceful fallback
- ✅ **Enhanced Launcher**: `run.py` with Node/npm/env validation

**Database Changes Delivered**:
- ✅ `utm_users` table (separate user identities)
- ✅ `utm_user_invitations` table
- ✅ `utm_project_members` table (project-level access)
- ✅ `utm_tenants` simplified (tenant_id + display_name + tier)
- ✅ `utm_quality_metrics` table (quality tracking)
- ✅ Migrations 020-025 executed

**Business Impact**: Enterprise collaboration + $240K visualization value (60% of V3.9 roadmap)

---

## 💼 Post-v4.0: Pricing Tiers (S/M/L)

**Models de Consumo** (Q4 2026 o después):

```
STARTER (S)      STANDARD (M)     PREMIUM (L)
$49/mes          $149/mes         $499/mes
1 usuario        3 usuarios       10 usuarios
5 proyectos      20 proyectos     Unlimited
GPT-4o-mini      GPT-4o           Claude Opus
```

**Implementation**:
- Field `tier` already exists in `utm_tenants` (v3.9)
- Enforce limits in API
- Stripe integration
- Usage dashboard

**Priority**: Medium (after v4.0 is stable)

---

## 📦 Long-Term Backlog (Post-v4.0)

### Phase E: Infrastructure as Code (IaC) - **DEFERRED**
- [ ] **Terraform/Bicep Generation**: Auto-generate IaC for Cloud Storage, Databricks Clusters, and Secrets Managers.
- [ ] **Network & Security Provisioning**: Automate VNet injection.

### Phase G: Real-time Modernization - **DEFERRED**
- [ ] **Delta Live Tables (DLT)**: Streaming-ready pipelines.
- [ ] **CDC Pattern Automation**: Merge/Upsert patterns for real-time ingest.

### Phase H: Multi-Dialect Expansion - **DEFERRED**
- [ ] **Informatica/DataStage**: XML exports support.
- [ ] **PL/SQL Modernization**: Oracle package conversion.

## 📦 Delivered Scope (v3.9)
The **Enterprise Multi-User Suite** is feature complete with role-based access control, user management UI, project-level permissions, and platform administration dashboard. Ready for team collaboration in enterprise environments.

## 📅 Release History

### v3.9 (The Multi-User Simplificado Release) - LATEST ⭐ - Feb 10, 2026
- **Multi-User Support**: Multiple users per tenant with role-based access (ADMIN/MANAGER/COLLABORATOR/VIEWER)
- **User Management**: Complete UI in Tenant Console for creating, editing, and managing users
- **Project Access Control**: Granular project-level permissions via `utm_project_members`
- **Platform Admin Dashboard**: All Users view with filters, password reset, and Ghost Mode impersonation
- **Simplified Data Model**: Removed `client_id` and `org_name`, kept only `tenant_id` + `display_name`
- **Database Separation**: `utm_users` separated from `utm_tenants` (organization model)
- **Migrations**: 020-025 (users table, invitations, project members, simplified tenants)

### v3.8 (The Governance & Architecture Clarity Release) - Feb 9, 2026
- **Process Locking**: Complete system to prevent concurrent execution and data corruption
- **Admin Tools**: Process lock management interface with force-release capabilities
- **Professional Modals**: ProcessLockModal, ProcessExecutionModal, and ReportsLibraryModal for enhanced UX
- **Governance Rules**: Formalized 3-layer ownership model (Admin/Tenant/User)
- **Reports Library**: Unified modal for centralized report access with stage-aware availability
- **Version-Agnostic Templates**: PDF reports no longer include version numbers
- **Bug Fixes**: Lock service async issues, duplicate navbar, code viewer expansion
- **UI Cleanup**: Removed Workbench (Diff) tab, cleaned stage toolbars, consistent dark mode

### v3.7 (The System & Identity Release) - Feb 6, 2026
- **System Router Refactor**: Centralized `/system/*` endpoints for admin operations
- **Dynamic Agent Loading**: Agents loaded from database, not hardcoded
- **Identity Management**: Full admin UI for Tenants, Users, and Clients
- **Provider Vault**: Strict filtering of configured providers per tenant

### v3.6 (Quality & Stability Enhancement) - Feb 3, 2026
- **UI Refinements**: Resizable split pane in Drafting explorer with persistent user preferences
- **Compliance Externalization**: Dynamic rule fetching from `utm_system_catalog` for Agent F compliance checks
- **Pipeline Stability**: Fixed critical cartridge factory synchronization bug in Architect service
- **Migration Bitácora**: Auto-generated markdown logbook documenting Agent F critiques and reasoning
- **Documentation Update**: Full alignment across all docs with v3.6 changes

### v3.5 (The Cloud-Native & Multi-Tenant Reset)
- **Cloudflare R2 Storage**: Complete migration to object storage with tenant isolation
- **Prompt Laboratory**: Dynamic prompt management system with 22 knowledge modules
- **Agent S (Scout)**: Technology detection for automatic source platform identification

### v3.2 (The Enterprise Modernization Suite)
- **Architect v2.0**: Automated inference of partitioning, volume, and latency.
- **Discovery Analytics**: Real-time heatmaps for PII and Business Criticality.
- **Governance Audit (Agent G)**: AI-driven compliance scoring and automated Runbook generation.
- **High-Fidelity Generation**: Context-aware PySpark code with partition-by and PII masking support.
- **Variable Injection**: Dynamic Environment parameterization (e.g. `${S3_ROOT}`).
- **Data Quality**: Auto-generated Great Expectations & Soda validation suites.

### v3.1 (The Discovery Gate & Management Hub) 

### v3.0 (The Enterprise Compliance Hub)
- **AI Audit Engine**: Automated architectural reviews with scoring and suggestions.
- **Column Mapping Editor**: Detailed field-level mapping with business context.
- **Universal Orchestration**: Airflow, Databricks, and YAML DAG generation.
- **Project Export**: ZIP bundle generation with all modernization artifacts.
- **Glassmorphism UI**: Premium visual overhaul (Purple accent theme).

### v2.0 (The Style Master)
- **Contextual Config**: Embedded "Solution Config" tabs in Drafting and Refinement.
- **Technology Mixer**: UI toggles for PySpark, Pure SQL, or Mixed generation.
- **Design Registry**: Global policy engine for naming and paths.
- **Expanded Layout**: 80% width optimization for engineering workflows.

### v1.5: Governance & Lineage
- **Lineage Mapper**: Mapping legacy artifacts to OpenLineage-compliant targets.
- **Certification**: Automated compliance scores.

### v1.0 - v1.3: The Contextual Architect
- **Context Injection**: "Virtual Steps" for business logic.
- **Operational Intelligence**: Automated load strategy and PII detection.
- **Base Registry**: Initial implementation of naming conventions.
