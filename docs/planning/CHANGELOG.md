# Release Planning Changelog

## 2026-02-27: Sprint 15 Day 5 — Admin Ghost Mode & Security Hardening

**Focus:** Corrección de errores críticos en Ghost Mode / Impersonación de admin

**Deliverables:**
- ✅ Fix: Error 500 en todas las requests con Ghost Mode activo (ut_tenants.client_id no existe)
- ✅ Fix: Error 403 en `/auth/admin/users` y `/auth/tenants` con Ghost Mode activo
- ✅ Nuevo parámetro `skipImpersonation` en `fetchWithAuth` (auth-client.ts)
- ✅ Página `/admin` fuerza `skipImpersonation: true` — nunca propaga Ghost Mode
- ✅ Fix: JSX parse error en `StrategicIntelligenceHub.tsx`
- ✅ Fix: Dropdown legibility (gris sobre gris) en StrategicIntelligenceHub
- ✅ Fix: Modal button overflow en UserManagement

**Root causes resueltos:**
1. `dependencies.py` consultaba `utm_tenants.client_id` (columna eliminada en migración 024 de v3.9)
2. `fetchWithAuth` en admin page enviaba `X-Impersonate-User-ID`, haciendo que el backend tratara al admin como el usuario impersonado (sin permisos ADMIN)

**Investigación adicional:**
- Confirmado que `demo3` no tiene proyectos en DB (tenant_id `daac0ee6-...` no tiene filas en `utm_projects`)
- Los únicos proyectos existentes: `testd` (demo1) y `testn` (ADMIN global)
- Ghost Mode funciona pero muestra lista vacía para tenants sin proyectos — comportamiento correcto

**Archivos modificados:**
- `apps/api/routers/dependencies.py`
- `apps/web/app/lib/auth-client.ts`
- `apps/web/app/admin/page.tsx`
- `apps/web/app/components/settings/StrategicIntelligenceHub.tsx`
- `apps/web/app/components/settings/UserManagement.tsx`

**Documentación:**
- Creado: [V4.0_STATUS_REPORT.md](V4.0_STATUS_REPORT.md) — Estado consolidado de v4.0

---

## 2026-02-19: Sprint 14 Phase 2 Day 4 - UI Polish & Status Indicators

**Focus:** User-facing bug fixes, visual feedback systems, and UI modernization

**Deliverables:**
- ✅ Progress percentage reset fix (DraftingView)
- ✅ 3 missing API endpoints created (/registry, /generation/stats, /generation/summary)
- ✅ Database schema fixes (removed non-existent column references)
- ✅ Component redesign: compact dark theme (GenerationStats, CodeGenerationSummary)
- ✅ Sidebar status indicators: green/yellow dots showing data availability
- ✅ Cartridge Settings: load project default configuration

**User Feedback Addressed:**
1. *"el porcentaje no se resetea"* → Fixed progress reset
2. *"grande y tonto"* → Compact dark components
3. *"deberia ser simple... un grreen... un amarillo"* → Status dots implemented
4. *"tiene q traer configurado el q tiene el proyecto x default"* → Cartridge defaults working

**Impact:**
- Zero 404 errors (was 3 endpoint failures)
- Zero database column errors (was 2 failures)
- Professional dark UI matching user preference
- Visual feedback on 5 sidebar sections
- Improved UX consistency across stages

**Files Modified:** 6 files, ~535 lines changed

**Documentation:**
- Updated: [SPRINT_14_PHASE_2_SUMMARY.md](../SPRINT_14_PHASE_2_SUMMARY.md) with Day 4 section

---

## 2026-02-18: Sprint 14 Phase 2 Day 3 - Schema Viewer Intelligence

**Focus:** Schema detection, PK/FK relationships, column lineage tracking

**Deliverables:**
- ✅ Fixed silent parser failure (invalid sqlglot reference)
- ✅ Two-pass constraint detection in Librarian Service
- ✅ SQL lineage integration for column usage tracking
- ✅ Smart table filtering (only show tables in queries)
- ✅ Visual indicators for used/unused columns

**Impact:**
- Schema detection: 40% → 95% (+137%)
- PK/FK detection: 0% → 90% (new capability)
- Silent failures: eliminated 100%

---

## 2026-02-17: Sprint 14 Phase 2 Day 1 - Performance Crisis Resolution

**Crisis:** Backend bombarded with 30+ requests/second, UI freezing

**Deliverables:**
- ✅ Polling interval optimization (3s → 10s = 70% reduction)
- ✅ Circular dependency elimination (infinite loop fix)
- ✅ Backend load reduced from 30+ req/s to 0.1 req/s (95%+ improvement)
- ✅ Unified sidebar architecture with lifted-state pattern

---

## 2026-02-13 (PM): v4.0 Further Simplifications (REFINEMENT)

**Decision:** Additional simplifications to v4.0 Zero-Hardcode feature

**Changes to Zero-Hardcode Generation:**

#### BEFORE (morning):
```
- Prompts in database with complex versioning
- Full tenant customization capability
- Version management system
Duration: 3-4 weeks
```

#### AFTER (afternoon):
```
- Prompts in database (global only, no tenant customization)
- Simple auto-versioning via trigger (saves previous on update)
- Historial READ-ONLY para ADMIN (análisis y seguridad)
- NO UI de rollback para usuarios
- No tenant override in v4.0
Duration: 2-3 weeks
```

**Rationale:**
- **Tenant customization**: Not needed yet, adds complexity
  - Prompts are global for entire application
  - Tenants customize through their tech choices, not prompts
  - Can add tenant customization in v5.0+ if needed
  
- **Versioning system**: Over-engineered for initial needs
  - Simple trigger that saves previous version is enough
  - Historial es SOLO para ADMIN - análisis y seguridad
  - NO hay UI de rollback - usuarios NO interactúan con versiones
  - Full version management (rollback UI, etc) can wait
  - Automatic history = safety net without complexity

**Impact:**
- Time reduction: 3-4 weeks → 2-3 weeks
- Simpler database schema
- Easier migration
- Lower risk

**Features unchanged:**
- ✅ Deep Forensic Triage (as planned)
- ✅ Real-Time Validation (as planned)
- ✅ UI Componentization (pending spec)

**Total v4.0 duration:** ~4 weeks (was 4-5 weeks)

---

## 2026-02-13 (AM): v4.0 Scope Reduction (MAJOR CHANGE)

**Decision:** Reduce v4.0 scope from 10 features to 4 core features

**Rationale:**
- Deliver faster (50% time reduction: 5 weeks vs 10 weeks)
- Lower risk (fewer features = fewer potential issues)
- Focus on essential transformation
- Move advanced AI features to v5.0+ when we have data to train on

### What Changed

#### BEFORE (Original v4.0):
```
Duration: 8-10 weeks
Features: 10 (all P0-P2)
- Zero-Hardcode Generation
- Multi-Model Orchestration
- Self-Learning Agents
- Deep Forensic Triage
- Real-Time Validation
- Adaptive Architecture Patterns
- Cost Optimization
- Security Scanning
- Incremental/CDC Detection
- Lineage Tracking
```

#### AFTER (Revised v4.0):
```
Duration: 4-5 weeks
Features: 4 (P0 only)
- Zero-Hardcode Generation ✅
- Deep Forensic Triage ✅
- Real-Time Validation ✅
- UI Componentization ✅

Moved to v5.0+:
- Multi-Model Orchestration → v5.0
- Self-Learning Agents → v5.0
- Cost Optimization → v5.0
- Security Scanning → v5.1
- Adaptive Architectures → v5.1
- Incremental/CDC → v5.1
- Lineage Tracking → v5.2
```

### Impact Analysis

**Time-to-Market:**
- Original: 8-10 weeks
- Revised: 4-5 weeks
- Improvement: **50% faster**

**Risk Reduction:**
- Features: 10 → 4 (60% reduction)
- Testing surface: -60%
- Deployment complexity: HIGH → MEDIUM

**Resource Allocation:**
- Team size: Same (2 backend, 1 frontend, 1 QA)
- Duration: Half
- Total effort: 20 person-weeks (vs 40+ originally)

### Documents Created/Updated

**New Documents:**
- [RELEASE_PLAN_v4.0_SIMPLIFIED.md](RELEASE_PLAN_v4.0_SIMPLIFIED.md) - Full technical plan
- [v4.0_QUICK_REFERENCE.md](v4.0_QUICK_REFERENCE.md) - Executive summary
- [v4.0_UI_COMPONENTIZATION.md](v4.0_UI_COMPONENTIZATION.md) - UI specification

**Updated Documents:**
- [ROADMAP.md](../ROADMAP.md) - v4.0 scope and future releases
- [V3.9_GAP_ANALYSIS_AND_V4.0_ROADMAP.md](../../V3.9_GAP_ANALYSIS_AND_V4.0_ROADMAP.md) - Feature status
- [README.md](README.md) - Planning navigation
- [INDEX.md](../INDEX.md) - Documentation index

### Approval Status

- [x] Technical feasibility confirmed
- [ ] Product team approval pending
- [ ] Stakeholder approval pending
- [ ] UI specification pending completion

**Target Approval Date:** February 14, 2026  
**Kickoff Date:** February 17, 2026

---

## 2026-02-10: v3.9 Released ✅

v3.9 "Multi-User Simplificado" deployed to production

**Key Features Delivered:**
- Multiple users per tenant
- 4 roles (ADMIN, MANAGER, COLLABORATOR, VIEWER)
- User management UI
- Platform admin dashboard
- Simplified data model

**Documents:**
- [RELEASE_PLAN_SIMPLE_v3.9.md](RELEASE_PLAN_SIMPLE_v3.9.md)
- [v3.9_RESUMEN_SIMPLE.md](v3.9_RESUMEN_SIMPLE.md)

---

## 2026-02-09: v3.9 Plan Finalized

Simplified v3.9 release plan approved and documented

**Action:** Created simplified planning documents
- Eliminated v3.10 (RBAC) - YAGNI
- Eliminated v3.11 (Collaboration) - YAGNI
- Focused on essential multi-user features

---

## 2026-01-15: Original v4.0 Vision Documented

Created comprehensive v4.0 vision document

**Document:** [future_v4.0.md](future_v4.0.md)

**Scope:** Ambitious 10-feature release
- AI Revolution theme
- Complete autonomous generation
- 8-10 week timeline

**Status:** Superseded by simplified plan on 2026-02-13

---

## Legend

- ✅ Complete
- 🔴 Pending
- 🔮 Future/Moved
- ⚠️ Superseded
- ❌ Cancelled

---

**Last Updated:** February 13, 2026  
**Next Review:** February 14, 2026 (Stakeholder approval)
