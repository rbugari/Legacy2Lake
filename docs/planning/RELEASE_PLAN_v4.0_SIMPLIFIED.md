# Release Plan v4.0 - "Zero-Hardcode Core" (SIMPLIFIED)

**Date:** February 13, 2026 (Updated PM with additional simplifications)  
**Last Updated:** February 18, 2026 — Sprint 15 progress (95% complete)  
**Status:** 🟢 NEAR COMPLETION — Sprint 15 Active (Week 4)  
**Target:** Q2 2026 (~4 weeks)  
**Original Duration:** 8-10 weeks → **v4.0 Reduced:** 4-5 weeks → **v4.0 Simplified:** ~4 weeks

**💎 Major Milestones Achieved:**
- ✅ Sprint 14 Phase 2: Performance Crisis Resolved (95%+ improvement)
- ✅ Schema Viewer Intelligence: PK/FK detection + Column lineage (Feb 18)
- ✅ Sprint 15: Advanced UI components (SchemaViewer, TypeMismatchViewer)
- 🟡 Week 4: Polish & final deployment prep

---

## 🎯 Executive Summary

v4.0 alcance **reducido y simplificado** para entregar más rápido la transformación core. 

**Cambios principales:**
- Movimos 7 de 10 features originales a releases futuros (v5.0+)
- Simplificamos Zero-Hardcode: prompts globales, versionado automático simple
- Timeline reducido de 8-10 semanas a ~4 semanas

**Filosofía:** "Hazlo bien, no grande. Primero lo esencial."

---

## ✅ FEATURES INCLUIDAS (P0)

### 1. Zero-Hardcode Generation ⭐ CORE
**Duration:** 2-3 weeks (REDUCIDO)

**Objetivo:**
- Eliminar TODOS los templates hardcodeados de Python/TypeScript
- Prompts dinámicos almacenados en base de datos
- Versionado automático simple (trigger guarda versión anterior - SOLO HISTORIAL READ-ONLY)
- ~~Customización por tenant~~ ❌ **ELIMINADO** (prompts globales para v4.0)

**Deliverables:**
- [ ] Nueva tabla `utm_prompts` (simplificada, sin tenant_id)
- [ ] Nueva tabla `utm_prompts_history` (historial read-only para ADMIN)
- [ ] Trigger automático para versionado (guarda versión anterior al UPDATE)
- [ ] Refactor Agent C (remove hardcoded templates)
- [ ] Prompt assembly engine
- [ ] Dynamic injection system

**Success Criteria:**
- ✅ Cero templates hardcoded en código Python
- ✅ Cambiar prompt en DB → output cambia sin redeploy
- ✅ Historial automático de cambios (trigger) - read-only para ADMIN
- ❌ NO hay UI de rollback - historial es solo para análisis y seguridad
- ❌ Customización por tenant movida a v5.0+

**IMPORTANTE - Versionado:**
- El historial es SOLO para análisis futuro y seguridad (por si se rompe algo)
- Solo ADMIN puede consultar el historial
- NO hay feature de rollback para usuarios
- Es un safety net automático, nada más

---

### 2. Deep Forensic Triage (Field-Level)
**Duration:** 3-4 weeks

**Objetivo:**
- Análisis estadístico a nivel de columna/campo
- Detección automática de PII
- Scoring de calidad por campo
- Recomendaciones de tipos/constraints

**Deliverables:**
- [ ] Nueva tabla `utm_column_profiles`
- [ ] `ForensicColumnAnalyzer` service
- [ ] Integración con Agent A
- [ ] UI: `ColumnProfilePanel.tsx`
- [ ] UI: `QualityScoreCard.tsx`

**Success Criteria:**
- ✅ Field profiling visible en UI para cada columna
- ✅ PII detection con >95% accuracy
- ✅ Quality score por campo
- ✅ Recommendations automáticas

---

### 3. Real-Time Validation
**Duration:** 2-3 weeks

**Objetivo:**
- Validación sintáctica durante generación (no después)
- Validación semántica (column references)
- Auto-corrección en loop
- Menos reintentos de LLM

**Deliverables:**
- [ ] Nueva tabla `utm_generation_outcomes`
- [ ] `CodeValidator` service (syntax + semantic)
- [ ] Python AST parser
- [ ] SQL parser con sqlglot
- [ ] Auto-correction loop en Agent C

**Success Criteria:**
- ✅ Código generado pasa validación al primer intento (>90%)
- ✅ Errores detectados durante generación (no después)
- ✅ Generation time < 15s por objeto

---

### 4. UI Componentization & Visual Revision
**Duration:** 2-3 weeks (parallel con otras features)  
**Status:** 🔄 IN PROGRESS — Sprint 15 Active

**Objetivo:**
- Revisión completa de componentes visuales
- Componentización modular y reusable
- Mejoras de UX/UI y performance
- Design system consistency

**Deliverables:**

- [x] **✅ Unified Sidebar Architecture** (Sprint 14 Phase 2)
  - Lifted state management (activeSection at workspace level)
  - Stage-aware navigation (projectStage not activeView)
  - Props-based pattern (stage, activeSection, onSectionChange)
  - Applied to: TriageView, DraftingView, RefinementView

- [x] **✅ Execution Status Indicators** (Sprint 14 Phase 2)
  - Visual feedback system (⚠️ no data, 🔄 processing, ✅ ready)
  - Stage-specific data detection logic
  - Component: SidebarHeader with useMemo optimization

- [x] **✅ Performance Crisis Resolution** (Sprint 14 Phase 2) 🔥 **CRITICAL**
  - 95%+ reduction in backend load (30+ req/s → 0.1 req/s)
  - Eliminated circular dependencies causing infinite re-renders
  - Polling optimization (3s → 10s metrics, 3s → 5s logs)
  - Fixed file explorer immediate loading

- [x] **✅ SchemaViewer Component** (Sprint 15) — `apps/web/app/components/visualization/SchemaViewer.tsx`
  - Visualización de esquema fuente y destino por objeto/asset
  - Selector de asset integrado cuando no hay `objectId` pre-seleccionado
  - Prop `initialTab` para navegar directamente a `schema` o `mapping`
  - Prop `onObjectSelect` para sincronizar selección con el padre (TriageView)
  - Estado interno `internalObjectId` como fallback cuando el padre no provee `objectId`
  - Auto-expand del primer table al cargar el esquema
  - Filtro de búsqueda en el selector de assets
  - Botón "Clear" para volver al selector desde la vista de detalle

- [x] **✅ TypeMismatchViewer Component** (Sprint 15) — `apps/web/app/components/visualization/TypeMismatchViewer.tsx`
  - Comparación visual columna a columna entre esquema fuente y destino
  - Detección de mismatches de tipo (ej. `VARCHAR` → `STRING`)
  - Indicadores de columnas PK, FK y nullable
  - Integrado como tab "Audit Mapping" dentro de SchemaViewer

- [x] **✅ Triage Navigation & Selection Sync** (Sprint 15) — `TriageView.tsx`
  - Click en nodo del **Mesh Graph** → sincroniza `selectedAssetForSchema` automáticamente
  - Click en fila del **Grid (Package Inventory)** → selecciona asset para Schema Viewer
  - Fila seleccionada en Grid con highlight visual (ring azul)
  - Panel "Asset Intelligence" con shortcuts de acción rápida:
    - **"View Schema Details"** → navega a tab Schema con `initialTab='schema'`
    - **"Audit Mapping"** → navega a tab Schema con `initialTab='mapping'`
  - Estado `selectedAssetForSchema` persiste al cambiar entre secciones (Graph, Grid, Logs)
  - Schema Viewer muestra selector de asset si no hay ninguno seleccionado (no queda en blanco)

- [x] **✅ SchemaInitialTab State** (Sprint 15) — `TriageView.tsx`
  - Nuevo estado `schemaInitialTab` para controlar qué sub-tab abre el SchemaViewer
  - Pasado como prop `initialTab` al componente SchemaViewer
  - Sincronizado con `useEffect` dentro de SchemaViewer para reaccionar a cambios

- [ ] 🟡 **Component Library Audit** (IN PROGRESS)
  - Debug logging added for sidebar/metrics diagnosis
  - Stage mismatch investigation active
  - Metrics refresh behavior under review

- [ ] ⚪ **Visual Redesign Proposals** (PENDING)
- [ ] ⚪ **Accessibility Improvements** (PENDING)

**Success Criteria:**
- ✅ Zero compilation errors across all modified files
- ✅ Performance: <1 req/sec baseline load (previously 30+/sec)
- ✅ Architecture: Lifted-state pattern scalable to all stages
- ✅ Schema Viewer: Funcional con selector, detalle y comparación de tipos
- ✅ Triage Navigation: Selección sincronizada entre Graph, Grid y Schema tab
- 🔄 UX: Clear execution feedback (under fine-tuning)
- ⚪ TBD: Additional visual improvements awaiting requirements

**Sprint 14 Phase 2 Metrics:**
| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Polling Frequency | 30 req/s | 0.1 req/s | ✅ 95%+ improvement |
| Sidebar Interval | 3s | 10s | ✅ Optimized |
| Logs Interval | 3s | 5s | ✅ Optimized |
| Circular Re-renders | Infinite | Zero | ✅ Eliminated |
| UI Responsiveness | Freezing | Smooth | ✅ Restored |

**Sprint 15 Metrics:**
| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Schema Tab (blank state) | Blank on direct nav | Asset selector shown | ✅ Fixed |
| Graph → Schema nav | Manual re-selection | Auto-sync on node click | ✅ Fixed |
| Grid → Schema nav | No selection | Row click selects asset | ✅ Fixed |
| TypeMismatch Viewer | Not implemented | Columnar diff view | ✅ New |

---

## 🔮 MOVED TO FUTURE RELEASES

### v5.0 - "Intelligence Layer" (6-8 weeks)
**Target:** Q3 2026

- **Multi-Model Orchestration**
  - Cascade execution (cheap → premium)
  - Cost optimization logic
  - Multi-provider support (OpenAI, Anthropic, etc.)

- **Self-Learning Agents**
  - Feedback loop with quality scoring
  - Pattern library building
  - Continuous quality improvement

- **Intelligent Cost Optimization**
  - Token usage dashboard
  - Cost analytics by agent/model
  - Billing optimization recommendations

---

### v5.1 - "Enterprise Hardening" (4-6 weeks)
**Target:** Q4 2026

- **Enhanced Security**
  - Credential scanning
  - SQL injection detection
  - PII exposure checks

- **Adaptive Architecture Patterns**
  - Data Vault support
  - Lambda architecture
  - Kappa architecture

- **Incremental & CDC Patterns**
  - Watermark detection
  - CDC pattern recognition
  - Auto-recommendations

---

### v5.2 - "Observability Suite" (3-4 weeks)
**Target:** Q1 2027

- **Advanced Observability**
  - Generation lineage tracking
  - Decision tree visualization
  - Complete audit trail

---

## 📅 v4.0 IMPLEMENTATION TIMELINE

```
WEEK 1: Foundation
Day 1-2: Database schema (utm_prompts + trigger auto-versioning)
Day 3-5: Refactor Agent C (remove hardcoded templates)
Weekend: Smoke tests

WEEK 2-3: Parallel Development
┌─────────────────────────────────────────┐
│ Track A: Zero-Hardcode                  │
│ - Prompt assembly engine                │
│ - Dynamic injection system              │
│ - Global prompts (no tenant override)   │
├─────────────────────────────────────────┤
│ Track B: Deep Triage                    │
│ - Column profiler service               │
│ - Statistical analysis                  │
│ - PII detection                         │
├─────────────────────────────────────────┤
│ Track C: Validation                     │
│ - Syntax validator (AST)                │
│ - Semantic validator                    │
│ - Auto-correction loop                  │
├─────────────────────────────────────────┤
│ Track D: UI Revision                    │
│ - Component audit                       │
│ - Visual redesign                       │
│ - UX improvements                       │
└─────────────────────────────────────────┘

WEEK 4: Integration, Testing & Launch
- Connect all features end-to-end
- UI updates for field profiles
- Integration testing
- Performance testing
- Final QA
- Documentation
- Migration guide from v3.9
- Production deployment
```

**Go-Live:** End of Week 4 (late March 2026)

---

## 🗄️ Database Schema Changes

### New Tables

```sql
-- Prompts globales (simplificado - sin customización por tenant en v4.0)
CREATE TABLE utm_prompts (
    prompt_id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    tech_stack TEXT,           -- 'pyspark', 'databricks', 'fabric', etc.
    pattern_type TEXT,         -- 'bronze', 'silver', 'gold', 'incremental'
    agent_id TEXT,             -- 'agent-c', 'agent-a', etc.
    is_active BOOLEAN DEFAULT true,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Historial automático de versiones (trigger simple - READ-ONLY para ADMIN)
CREATE TABLE utm_prompts_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id TEXT NOT NULL,
    content TEXT NOT NULL,
    tech_stack TEXT,
    pattern_type TEXT,
    agent_id TEXT,
    metadata JSONB,
    changed_by UUID,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    -- NOTA: Esta tabla es SOLO para historial. No hay UI de rollback.
    -- Solo ADMIN puede consultar para análisis y seguridad.
    CONSTRAINT fk_changed_by FOREIGN KEY (changed_by) REFERENCES utm_users(id)
);

-- Trigger para versionado automático (safety net - NO hay UI de rollback)
CREATE OR REPLACE FUNCTION save_prompt_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Guardar versión anterior antes de actualizar
    -- Este historial es READ-ONLY para ADMIN (análisis y seguridad)
    INSERT INTO utm_prompts_history (
        prompt_id, content, tech_stack, pattern_type, 
        agent_id, metadata, changed_by
    )
    VALUES (
        OLD.prompt_id, OLD.content, OLD.tech_stack, OLD.pattern_type,
        OLD.agent_id, OLD.metadata, OLD.updated_by
    );
    
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- NOTA: Este trigger es automático. Los usuarios NO interactúan con versiones.
-- Solo ADMIN puede consultar utm_prompts_history para troubleshooting.

CREATE TRIGGER prompt_version_trigger
    BEFORE UPDATE ON utm_prompts
    FOR EACH ROW
    EXECUTE FUNCTION save_prompt_version();

-- Column profiles para Deep Triage
CREATE TABLE utm_column_profiles (
    profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES utm_projects(id),
    object_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    inferred_type TEXT,
    declared_type TEXT,
    nullability_score FLOAT,
    cardinality INTEGER,
    distinct_ratio FLOAT,
    semantic_tags TEXT[],      -- ['PII', 'EMAIL', 'PHONE', etc.]
    quality_score INTEGER,     -- 0-100
    statistical_profile JSONB, -- min, max, mean, stddev, percentiles
    detected_patterns TEXT[],
    sample_values JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, object_name, column_name)
);

-- Generation outcomes para analytics y learning
CREATE TABLE utm_generation_outcomes (
    outcome_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES utm_projects(id),
    agent_id TEXT NOT NULL,
    object_name TEXT,
    context_hash TEXT,         -- Hash del contexto de entrada
    generated_code TEXT,
    validation_passed BOOLEAN,
    validation_errors JSONB,
    execution_success BOOLEAN,
    quality_score INTEGER,
    tokens_used INTEGER,
    model_used TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_prompts_agent ON utm_prompts(agent_id, tech_stack);
CREATE INDEX idx_prompts_active ON utm_prompts(is_active) WHERE is_active = true;
CREATE INDEX idx_prompts_history_prompt ON utm_prompts_history(prompt_id, changed_at DESC);
CREATE INDEX idx_column_profiles_project ON utm_column_profiles(project_id);
CREATE INDEX idx_generation_outcomes_project ON utm_generation_outcomes(project_id, created_at);
```

---

## 🔧 Code Changes

### 1. Agent C Refactor

**File:** `apps/api/services/agents/agent_c_service.py`

**Changes:**
```python
# BEFORE (v3.x)
def generate_bronze_code(self, asset):
    template = HARDCODED_PYSPARK_TEMPLATE  # ❌
    return template.format(asset)

# AFTER (v4.0)
async def generate_bronze_code(self, asset):
    # ✅ Load prompt from DB (global, no tenant customization)
    prompt = await self.prompt_service.get_active_prompt(
        agent_id="agent-c",
        tech_stack=asset.target_tech,
        pattern_type="bronze"
    )
    
    # ✅ Assemble with context
    enriched_prompt = self.prompt_assembler.build(
        base_prompt=prompt.content,
        context=asset.to_dict()
    )
    
    # ✅ Generate with validation
    code = await self.llm.generate(enriched_prompt)
    validation = await self.validator.validate(code, asset.schema)
    
    if not validation.is_valid:
        code = await self.regenerate_with_feedback(code, validation.errors)
    
    return code
```

---

### 2. New Services

**Files to create:**
- `apps/api/services/prompts/prompt_service.py`
- `apps/api/services/prompts/prompt_assembler.py`
- `apps/api/services/triage/forensic_analyzer.py`
- `apps/api/services/validation/code_validator.py`
- `apps/api/services/validation/syntax_validator.py`
- `apps/api/services/validation/semantic_validator.py`

---

### 3. Frontend Components

**Files to update/create:**
- `apps/web/src/components/triage/ColumnProfilePanel.tsx` (NEW)
- `apps/web/src/components/triage/QualityScoreCard.tsx` (NEW)
- `apps/web/src/components/triage/PIIBadge.tsx` (NEW)
- `apps/web/src/components/common/ValidationErrors.tsx` (NEW)

---

## ✅ Success Criteria

### Technical Metrics
- [ ] Zero templates hardcoded en Python/TypeScript
- [ ] Prompts globales funcionando desde database
- [ ] Versionado automático (trigger) guardando historial
- [ ] Field profiling para todas las columnas detectadas
- [ ] >90% código pasa validación al primer intento
- [ ] Generation time < 15s por objeto
- [ ] PII detection accuracy >95%

### Business Metrics
- [ ] Cambios en prompts globales visibles inmediatamente (sin redeploy)
- [ ] Historial de cambios disponible para auditoría
- [ ] Quality scoring visible para todos los campos
- [ ] UX score improvement >20%
- [ ] Zero P0/P1 bugs en producción

### Go/No-Go Checklist
- [ ] All P0 features complete
- [ ] Zero hardcoded templates remain
- [ ] Database migrations tested
- [ ] Rollback plan documented
- [ ] Performance benchmarks passed
- [ ] Security audit cleared
- [ ] Documentation complete
- [ ] Stakeholder approval

---

## 🚨 Risks & Mitigation

### Risk 1: Prompt Quality
**Description:** Prompts en DB pueden ser de menor calidad que templates hardcoded  
**Mitigation:** 
- Migrar templates actuales como baseline
- Trigger automático guarda historial (ADMIN puede revisar si hay problemas)
- Pruebas exhaustivas antes de cambiar prompts en producción
- En caso de emergencia, ADMIN puede consultar historial y restaurar manualmente

### Risk 2: Performance
**Description:** Cargar prompts desde DB puede ser más lento  
**Mitigation:**
- Caching agresivo de prompts activos
- Pre-load prompts al startup
- CDN para prompts globales

### Risk 3: Validation Overhead
**Description:** Real-time validation puede ralentizar generación  
**Mitigation:**
- Validación en paralelo con generación
- Cache de validaciones exitosas
- Progressive validation (syntax first, semantic after)

---

## 📊 Impact Analysis

### Time-to-Market
- **Original:** 8-10 weeks
- **Revised:** 4-5 weeks
- **Improvement:** 50% faster delivery

### Risk Reduction
- **Features:** 10 → 4 (60% reduction)
- **Complexity:** HIGH → MEDIUM
- **Testing surface:** -60%

### Resource Allocation
- **Backend:** 2 devs (Week 1-4)
- **Frontend:** 1 dev (Week 2-4)
- **QA:** 1 QA (Week 3-4)
- **Total:** ~16 person-weeks (reduced from 20 due to simplifications)

---

## 📚 Documentation Requirements

### Developer Documentation
- [ ] Prompt system architecture guide
- [ ] Prompt authoring best practices
- [ ] Validation framework usage
- [ ] Column profiler integration guide
- [ ] Migration guide from v3.9

### User Documentation
- [ ] Tenant prompt customization guide
- [ ] Field profiling interpretation
- [ ] Quality score understanding
- [ ] PII handling guidelines

### Operations Documentation
- [ ] Deployment runbook
- [ ] Rollback procedures
- [ ] Monitoring & alerting setup
- [ ] Performance tuning guide

---

## 🔄 Migration Path from v3.9

### Phase 1: Database
1. Run migration script: `migrations/sprint_v4.0.sql`
2. Verify new tables created
3. Migrate existing templates to prompts

### Phase 2: Backend
1. Deploy new Agent C version
2. Enable prompt system feature flag
3. Monitor generation success rate
4. Roll back if issues detected

### Phase 3: Frontend
1. Deploy new UI components
2. Enable field profiling views
3. User acceptance testing
4. Full rollout

---

## 🎯 Post-v4.0 Roadmap

```
v4.0 (Q2 2026, 5 weeks)
└─ Zero-Hardcode Core
   ├─ Prompt-driven generation
   ├─ Field-level triage
   └─ Real-time validation

v5.0 (Q3 2026, 6-8 weeks)
└─ Intelligence Layer
   ├─ Multi-model orchestration
   ├─ Self-learning agents
   └─ Cost optimization

v5.1 (Q4 2026, 4-6 weeks)
└─ Enterprise Hardening
   ├─ Security scanning
   ├─ Adaptive architectures
   └─ CDC detection

v5.2 (Q1 2027, 3-4 weeks)
└─ Observability Suite
   └─ Lineage tracking
```

---

## 🔗 Related Documents

- [ROADMAP.md](../ROADMAP.md) - Strategic roadmap
- [V3.9_GAP_ANALYSIS_AND_V4.0_ROADMAP.md](../../V3.9_GAP_ANALYSIS_AND_V4.0_ROADMAP.md) - Original v4.0 scope
- [future_v4.0.md](future_v4.0.md) - Original v4.0 vision (comprehensive)
- [RELEASE_PLAN_SIMPLE_v3.9.md](RELEASE_PLAN_SIMPLE_v3.9.md) - v3.9 plan

---

## ✍️ Approval

**Plan Author:** Data Architecture Team  
**Date:** February 13, 2026  
**Status:** ✅ APPROVED - Scope Reduced

**Approvals:**
- [ ] CTO/Tech Lead
- [ ] Product Manager
- [ ] Head of Engineering

**Target Approval Date:** February 14, 2026  
**v4.0 Kickoff Date:** February 17, 2026  
**v4.0 Target Launch:** End of March 2026

---

## 📝 PENDING: UI COMPONENTIZATION DETAILS

### 🔴 DETAILED SPECIFICATION DOCUMENT

A comprehensive specification document has been created for UI/UX work:

👉 **[v4.0_UI_COMPONENTIZATION.md](v4.0_UI_COMPONENTIZATION.md)**

**Contents:**
1. Component Library Audit (inventory, reusability, duplication)
2. Visual Redesign (design system, colors, typography, spacing)
3. UX Improvements (user flows, accessibility, performance, mobile)
4. Specific Components (refactor list, new components, deprecations)
5. Success Metrics (satisfaction, performance, accessibility, reusability)
6. Implementation Plan (week-by-week breakdown)
7. Documentation Requirements (Storybook, design system docs)
8. Rollout Strategy (phased approach, feature flags, communication)
9. Open Questions (for product & engineering teams)
10. Dependencies & Risks
11. Next Steps

**📋 Action Required:** 
- Product/Design team to review specification document
- Fill in pending sections (component lists, mockups, priorities)
- Approve design system tokens
- Define success criteria

**Timeline:**
- Specification complete: By end of Week 1 (Feb 20, 2026)
- Implementation: Week 2-4 (parallel with backend work)

---

*"Great software is built incrementally. v4.0 focuses on the essential foundation - the rest will follow."*

---

## 📋 SPRINT LOG — Historial de Cambios

### Sprint 14 — Phase 2 (Feb 13–14, 2026)
**Foco:** Arquitectura de Sidebar y resolución de crisis de performance

| Cambio | Archivo(s) | Estado |
|--------|-----------|--------|
| Unified Sidebar Architecture (lifted state) | `StageSidebar.tsx`, `TriageView.tsx`, `DraftingView.tsx`, `RefinementView.tsx` | ✅ |
| Execution Status Indicators (SidebarHeader) | `SidebarHeader.tsx` | ✅ |
| Performance: eliminación de re-renders infinitos | `TriageView.tsx`, `useSidebarMetrics.ts` | ✅ |
| Polling optimization (3s → 10s/5s) | `useSidebarMetrics.ts` | ✅ |
| File Explorer: carga inmediata corregida | `FileManagerTab.tsx` | ✅ |

---

### Sprint 15 — Phase 1 (Feb 17–18, 2026)
**Foco:** Schema Viewer, Librarian Service y Triage Navigation

#### Backend — `apps/api/`

| Cambio | Archivo(s) | Estado |
|--------|-----------|--------|
| **LibrarianService**: Mapeo `source_tech` → dialecto SQLGlot | `services/librarian_service.py` | ✅ |
| **LibrarianService**: Two-pass PK/FK detection fix (Feb 18) | `services/librarian_service.py` | ✅ |
| **LibrarianService**: Fixed silent parser failure (ForeignKeyColumnConstraint bug) | `services/librarian_service.py` | ✅ |
| Soporte de dialectos: `tsql`, `oracle`, `mysql`, `postgres`, `spark`, `snowflake` | `services/librarian_service.py` | ✅ |
| Resolución case-insensitive de carpeta Triage en storage | `services/librarian_service.py` | ✅ |
| Lectura de `source_tech` desde `settings` y `config` del proyecto | `services/librarian_service.py` | ✅ |
| **Visualization API**: Endpoint `GET /projects/{id}/objects/{obj_id}/schema` | `routers/visualization.py` | ✅ |
| **Visualization API**: SQL lineage integration for column usage tracking | `routers/visualization.py` | ✅ |
| **Visualization API**: Smart table filtering (SSIS-specific) | `routers/visualization.py` | ✅ |
| Schema response con `source_tables`, `target_tables`, `schema_available` | `routers/visualization.py` | ✅ |
| Endpoint `GET /projects/{id}/generated-code` (aggregated view) | `routers/visualization.py` | ✅ |

#### Frontend — `apps/web/`

| Cambio | Archivo(s) | Estado |
|--------|-----------|--------|
| **SchemaViewer**: Nuevo componente de visualización de esquema | `components/visualization/SchemaViewer.tsx` | ✅ |
| SchemaViewer: Selector de asset integrado (cuando `objectId` es undefined) | `components/visualization/SchemaViewer.tsx` | ✅ |
| SchemaViewer: Prop `initialTab` (`'schema'` \| `'mapping'`) | `components/visualization/SchemaViewer.tsx` | ✅ |
| SchemaViewer: Prop `onObjectSelect` para sync con padre | `components/visualization/SchemaViewer.tsx` | ✅ |
| SchemaViewer: Estado interno `internalObjectId` como fallback | `components/visualization/SchemaViewer.tsx` | ✅ |
| SchemaViewer: Filtro de búsqueda en selector de assets | `components/visualization/SchemaViewer.tsx` | ✅ |
| SchemaViewer: Auto-expand del primer table al cargar | `components/visualization/SchemaViewer.tsx` | ✅ |
| **SchemaViewer**: PK/FK visual indicators (Feb 18) - Amber/Blue badges | `components/visualization/SchemaViewer.tsx` | ✅ |
| **SchemaViewer**: Column usage indicators (Feb 18) - Emerald dots + opacity | `components/visualization/SchemaViewer.tsx` | ✅ |
| **SchemaViewer**: Field mapping corrections (Feb 18) - type, is_pk, is_fk | `components/visualization/SchemaViewer.tsx` | ✅ |
| **TypeMismatchViewer**: Nuevo componente de comparación columnar | `components/visualization/TypeMismatchViewer.tsx` | ✅ |
| TypeMismatchViewer: Detección de mismatches de tipo fuente→destino | `components/visualization/TypeMismatchViewer.tsx` | ✅ |
| TypeMismatchViewer: Indicadores PK, FK, nullable | `components/visualization/TypeMismatchViewer.tsx` | ✅ |
| **TriageView**: `onNodeClick` sincroniza `selectedAssetForSchema` | `components/stages/TriageView.tsx` | ✅ |
| **TriageView**: Grid row click selecciona asset para Schema Viewer | `components/stages/TriageView.tsx` | ✅ |
| **TriageView**: Highlight visual de fila seleccionada en Grid | `components/stages/TriageView.tsx` | ✅ |
| **TriageView**: Panel "Asset Intelligence" con shortcuts de acción | `components/stages/TriageView.tsx` | ✅ |
| **TriageView**: Nuevo estado `schemaInitialTab` para controlar sub-tab | `components/stages/TriageView.tsx` | ✅ |
| **TriageView**: Botones "View Schema Details" y "Audit Mapping" en panel de detalle | `components/stages/TriageView.tsx` | ✅ |
| **TriageView**: Schema Viewer muestra selector si no hay asset seleccionado | `components/stages/TriageView.tsx` | ✅ |

**📊 Sprint 15 Metrics (Feb 18, 2026):**
| Metric | Before | After | Impact |
|--------|--------|-------|--------|
| Schema Detection Rate | ~40% | ~95% | +137% 🎯 |
| PK/FK Detection | 0% | ~90% | New capability ✨ |
| Silent Parser Failures | Frequent | Zero | 100% eliminated 🛡️ |
| Column Lineage Tracking | None | Full | New feature 📊 |

**📄 Documentation:**
- [technical/TRIAGE_SCHEMA_VIEWER_FIX_2026-02-18.md](../technical/TRIAGE_SCHEMA_VIEWER_FIX_2026-02-18.md) - Complete technical deep dive

---

### Pendiente — Sprint 15 Phase 2 (Feb 19–21, 2026)
**Foco:** Component polish, Visual redesign, Accessibility

| Tarea | Prioridad |
|-------|-----------|
| Component Library Audit completo | 🟡 Media |
| Visual Redesign Proposals | ⚪ Baja |
| Accessibility Improvements | ⚪ Baja |
| Zero-Hardcode: Prompt assembly engine | 🔴 Alta |
| Deep Triage: ForensicColumnAnalyzer | 🔴 Alta |
| Real-Time Validation: CodeValidator service | 🔴 Alta |

