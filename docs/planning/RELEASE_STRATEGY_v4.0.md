# Legacy2Lake v4.0 - Release Strategy
## Monolítico vs Sub-Releases Incrementales

**Fecha:** 2026-02-10  
**Autor:** Development Team  
**Status:** PROPOSAL - Requiere Decisión  
**Contexto:** v3.9 ✅ completada → Planificando estrategia para v4.0

---

## 🎯 EL DILEMA

v4.0 representa un **cambio arquitectónico fundamental**:
- Eliminar TODO el hardcode
- Prompts en DB con 3 capas
- Refactorizar 7 cartridges
- Deep Forensic Triage
- Multi-Model Orchestration
- Self-Learning Agents

**Pregunta Crítica:**
> ¿Liberamos v4.0 de golpe (monolítico) o en sub-releases incrementales?

---

## 📊 COMPARATIVA: DOS ESTRATEGIAS

### OPCIÓN A: Monolítico (v4.0 Big Bang)

```
v3.9 ✅ ────────────────> v4.0 🚀 (8-10 semanas)
                           │
                           └─> TODO implementado a la vez
```

**Contenido de v4.0:**
- ✅ Infraestructura de prompts (DB + .md)
- ✅ 7 cartridges refactorizados
- ✅ Deep Forensic Triage
- ✅ Multi-Model Orchestration
- ✅ UI de administración de prompts
- ✅ Self-Learning (básico)
- ✅ MCP Servers integrados

**Timeline:** 8-10 semanas de desarrollo, 1 release único

---

### OPCIÓN B: Sub-Releases Incrementales

```
v3.9 ✅ ─> v4.0 ─> v4.1 ─> v4.2 ─> v4.3 ─> v4.4
           (3w)   (2w)   (2w)   (2w)   (1w)
```

**Desglose por versión:**

#### **v4.0 - Foundation** (3 semanas)
**Tema:** "Infraestructura Base de Prompts"

**Contenido:**
- ✅ Tablas de DB (`utm_system_prompts`, etc.)
- ✅ `PromptManagementService`
- ✅ `PromptSyncService` (DB ↔ .md)
- ✅ Estructura `prompt_lab/`
- ✅ API básica de prompts (`GET /prompts`)
- ✅ 1 cartridge piloto refactorizado (PySpark)

**Impacto Usuario:** NINGUNO (cambios internos)  
**Backwards Compatible:** 100%  
**Riesgo:** 🟢 BAJO

---

#### **v4.1 - Cartridge Migration** (2 semanas)
**Tema:** "Eliminación de Hardcode"

**Contenido:**
- ✅ Refactorizar 6 cartridges restantes:
  - Snowflake
  - dbt
  - MS Fabric
  - GCP
  - AWS
  - Salesforce
- ✅ Eliminar directorio `/generation/cartridges/`
- ✅ `PromptComposer` con resolución de 3 capas
- ✅ Tests de equivalencia (v3.9 vs v4.1)

**Impacto Usuario:** Código generado idéntico pero sin hardcode  
**Backwards Compatible:** 100%  
**Riesgo:** 🟡 MEDIO

---

#### **v4.2 - Deep Triage** (2 semanas)
**Tema:** "Análisis Forense Profundo"

**Contenido:**
- ✅ Field-level analysis (tipos, nullability, cardinalidad)
- ✅ Pattern detection (joins, aggregations, window functions)
- ✅ Volumetric profiling (tamaños reales de tablas)
- ✅ Dependency graph transitive
- ✅ Business rules extraction (WHERE/CASE statements)
- ✅ Agent A refactorizado para deep triage

**Impacto Usuario:** Mejor calidad en metadata de discovery  
**Backwards Compatible:** 100%  
**Riesgo:** 🟡 MEDIO

---

#### **v4.3 - AI Orchestration** (2 semanas)
**Tema:** "Multi-Model y Self-Learning"

**Contenido:**
- ✅ Multi-Model Router (GPT-4, Claude, Code Llama)
- ✅ Task-specific LLM selection
- ✅ Self-Learning básico (feedback loop)
- ✅ Prompt A/B testing framework
- ✅ Cost optimization (uso de modelos más baratos)

**Impacto Usuario:** Mejor código generado + menor costo  
**Backwards Compatible:** 100%  
**Riesgo:** 🟡 MEDIO

---

#### **v4.4 - Admin UI** (1 semana)
**Tema:** "Gestión Visual de Prompts"

**Contenido:**
- ✅ Admin panel `/admin/prompts`
- ✅ CRUD UI para prompts
- ✅ Version history viewer
- ✅ Tenant overrides UI
- ✅ Project-specific prompt customization
- ✅ Sync status dashboard

**Impacto Usuario:** Admins pueden editar prompts sin código  
**Backwards Compatible:** 100%  
**Riesgo:** 🟢 BAJO

---

## ⚖️ ANÁLISIS COMPARATIVO

| Criterio | Monolítico (A) | Incremental (B) | Ganador |
|----------|----------------|-----------------|---------|
| **Time to Market** | 8-10 semanas | 10-12 semanas total | 🅰️ Monolítico |
| **Riesgo Técnico** | 🔴 ALTO (todo a la vez) | 🟢 BAJO (controlado) | 🅱️ Incremental |
| **Testing** | Complejo (todo junto) | Fácil (aislado) | 🅱️ Incremental |
| **Rollback** | Difícil | Fácil (versión anterior) | 🅱️ Incremental |
| **Feedback Loop** | Al final (10 semanas) | Cada 2 semanas | 🅱️ Incremental |
| **User Impact** | Todo cambia | Gradual, transparente | 🅱️ Incremental |
| **Team Morale** | Presión final | Wins frecuentes | 🅱️ Incremental |
| **Business Value** | Tardío | Temprano (v4.0) | 🅱️ Incremental |
| **Complejidad PM** | Simple (1 release) | Mayor (5 releases) | 🅰️ Monolítico |
| **Deployment Risk** | 1 big bang | 5 pequeños | 🅱️ Incremental |

**Score:** Monolítico = 2/10 | Incremental = 8/10

---

## 🎯 RECOMENDACIÓN: OPCIÓN B (INCREMENTAL)

### Razones Principales:

#### 1. **Riesgo Controlado** 🛡️
```
Monolítico: Si falla algo en semana 8, pierdes TODO
Incremental: Si falla v4.2, v4.0 y v4.1 siguen funcionando
```

#### 2. **Feedback Temprano** 📊
```
Monolítico: Primera impresión en semana 10
Incremental: Feedback cada 2 semanas (ajustes rápidos)
```

#### 3. **Business Value Gradual** 💰
```
Monolítico: Valor en semana 10
Incremental: Valor desde v4.0 (semana 3)
  - v4.0: Infraestructura (no visible pero crítica)
  - v4.1: Sin hardcode (mantenimiento fácil)
  - v4.2: Mejor triage (mejor producto)
  - v4.3: Multi-model (menor costo)
  - v4.4: UI admin (usabilidad)
```

#### 4. **Compatibilidad con Lecciones de v3.9** 📚
```
Decisión v3.9: Eliminar v3.10/v3.11 porque NO eran necesarias
Contexto v4.0: Cada sub-release AGREGA VALOR real

v3.10 (permisos granulares) = YAGNI ❌
v4.2 (deep triage) = CORE FEATURE ✅
```

#### 5. **Alineación con Filosofía del Proyecto** 🎨
```
Principio Legacy2Lake: "Keep it simple. Ship fast."

Incremental = Ship v4.0 en 3 semanas (foundation lista)
Monolítico = Ship v4.0 en 10 semanas (todo o nada)
```

---

## 📅 ROADMAP DETALLADO RECOMENDADO

### Timeline Visual

```
┌─────────────────────────────────────────────────────────────────┐
│ 2026                                                            │
├─────────────────────────────────────────────────────────────────┤
│ Feb 10   │ Feb 17   │ Mar 3    │ Mar 17   │ Mar 31   │ Apr 14  │
│   NOW    │          │          │          │          │         │
├──────────┼──────────┼──────────┼──────────┼──────────┼─────────┤
│          │          │ v4.0     │ v4.1     │ v4.2     │ v4.3    │
│  v3.9 ✅ │ Sprint 0 │Foundation│Cartridge │  Deep    │   AI    │
│  DONE    │Extracción│  (3w)    │  (2w)    │ Triage   │  Orch   │
│          │          │          │          │  (2w)    │  (2w)   │
└──────────┴──────────┴──────────┴──────────┴──────────┴─────────┘
                                                        │ Apr 21  │
                                                        │  v4.4   │
                                                        │ AdminUI │
                                                        │  (1w)   │
                                                        └─────────┘

Total: ~11 semanas (vs 8-10 del plan monolítico)
Overhead: +2 semanas (20% más) pero con 80% menos riesgo
```

---

## 🚦 CRITERIOS DE ÉXITO POR VERSIÓN

### **v4.0 - Foundation** ✅

**Must Have:**
- [ ] Tablas creadas en Supabase
- [ ] `PromptSyncService` funcional (DB ↔ .md bidireccional)
- [ ] PySpark cartridge refactorizado (sin hardcode)
- [ ] Tests: código generado v3.9 === v4.0
- [ ] 0 regressions en CI/CD

**Success Metrics:**
- Tiempo de sync prompts: <5 segundos
- PySpark generation: idéntico a v3.9
- DB schema: validado con migrations

**Go/No-Go:** Si tests fallan, NO avanzar a v4.1

---

### **v4.1 - Cartridge Migration** ✅

**Must Have:**
- [ ] 6 cartridges refactorizados (Snowflake, dbt, Fabric, GCP, AWS, SF)
- [ ] `/generation/cartridges/` eliminado
- [ ] `PromptComposer` resolución 3 capas funcional
- [ ] Performance: overhead <200ms vs v3.9
- [ ] Tests de equivalencia: 100% pass rate

**Success Metrics:**
- 7/7 cartridges sin hardcode
- Tiempo de resolución 3 capas: <150ms promedio
- Código generado: <5% variación vs v3.9

**Go/No-Go:** Si performance >500ms, investigar antes de v4.2

---

### **v4.2 - Deep Triage** ✅

**Must Have:**
- [ ] Field-level analysis en Agent A
- [ ] Pattern detection (joins, aggregations)
- [ ] Volumetric profiling integrado
- [ ] Dependency graph visualización
- [ ] Business rules extraction funcional

**Success Metrics:**
- Detección de campos: 100% de tablas
- Accuracy de tipos: >95%
- Time to triage: <30 segundos por asset

**Go/No-Go:** Si accuracy <80%, mejorar prompts

---

### **v4.3 - AI Orchestration** ✅

**Must Have:**
- [ ] Multi-Model Router funcional
- [ ] Task routing configurado (3+ modelos)
- [ ] Self-Learning básico (feedback loop)
- [ ] A/B testing framework operativo
- [ ] Cost tracking por modelo

**Success Metrics:**
- Reducción de costos: >20% vs v4.2
- Calidad de código: mejora >10% (métricas sintácticas)
- Latency: <2x vs single-model

**Go/No-Go:** Si costos aumentan, revisar routing logic

---

### **v4.4 - Admin UI** ✅

**Must Have:**
- [ ] CRUD completo en `/admin/prompts`
- [ ] Version history navegable
- [ ] Tenant overrides UI funcional
- [ ] Project customization UI
- [ ] Sync status dashboard

**Success Metrics:**
- Time to edit prompt: <30 segundos
- Sync latency: <5 segundos post-edit
- User satisfaction: >4/5 (encuesta interna)

**Go/No-Go:** Si UX confusa, iterar antes de GA

---

## 🔄 ESTRATEGIA DE ROLLBACK

### Por Versión:

#### **v4.0 → v3.9**
```sql
-- Revertir migrations
BEGIN;
DROP TABLE IF EXISTS utm_system_prompts CASCADE;
DROP TABLE IF EXISTS utm_tenant_prompt_overrides CASCADE;
DROP TABLE IF EXISTS utm_project_prompts CASCADE;
DROP TABLE IF EXISTS utm_prompt_versions CASCADE;
COMMIT;
```
```python
# Reactivar hardcode en PySpark cartridge
git revert <commit_hash>
```

#### **v4.1 → v4.0**
```python
# Reactivar hardcode en 6 cartridges
git revert <commit_range>
# PySpark sigue con prompts (v4.0)
```

#### **v4.2 → v4.1**
```python
# Desactivar deep triage
# Settings: USE_DEEP_TRIAGE = False
# Código de generación no afectado
```

#### **v4.3 → v4.2**
```python
# Desactivar multi-model router
# Settings: USE_MULTI_MODEL = False
# Fallback a modelo único (GPT-4)
```

#### **v4.4 → v4.3**
```python
# Simplemente no desplegar frontend
# Backend sigue funcionando (API disponible)
```

**Key Point:** Cada versión es independiente, rollback selectivo posible.

---

## 💡 LECCIONES DE v3.9 APLICADAS

### ✅ Lo que SÍ aplicamos:

#### 1. **Simplicidad > Perfección**
```
v3.9: Eliminamos v3.10/v3.11 porque no agregaban valor
v4.0: Cada sub-release DEBE agregar valor tangible
```

#### 2. **YAGNI (You Aren't Gonna Need It)**
```
v3.9: Sin permisos granulares (no necesarios)
v4.0: Sin features especulativas (solo probado)
```

#### 3. **Ship Fast, Iterate**
```
v3.9: 3 semanas → producción
v4.x: Cada 2 semanas → feedback
```

### ❌ Lo que NO repetimos:

#### 1. **Over-Engineering Preventivo**
```
v3.9 Original Plan: 3 releases (v3.9, v3.10, v3.11)
v3.9 Final: 1 release (suficiente)

v4.0 NO será: "Por si acaso agreguemos X"
v4.0 SÍ será: "Esto es crítico, implementémoslo"
```

#### 2. **Monolitos Riesgosos**
```
v3.9: Aprendimos que releases pequeñas son mejores
v4.0: Aplicamos incremental (pero cada uno con valor)
```

---

## 🎬 PLAN DE ACCIÓN INMEDIATO

### **Esta Semana (Feb 10-17): Sprint 0 - Preparación**

**Tareas:**
1. ✅ **Decidir estrategia** (este documento)
2. ✅ **Extraer prompts de v3.9** (script automático)
3. ✅ **Crear estructura `prompt_lab/`**
4. ✅ **Diseñar migrations de DB**
5. ✅ **Setup MCP Servers críticos**

**Deliverables:**
- [ ] Prompts extraídos en formato .md
- [ ] Migrations SQL listas para review
- [ ] `prompt_lab/` en Git
- [ ] MCP servers instalados

---

### **Semana 1-3 (Feb 17 - Mar 3): v4.0 Foundation**

**Sprint Planning:**
- **Backend:** DB tables, PromptManagementService, PromptSyncService
- **Cartridge:** PySpark refactorizado
- **Testing:** Equivalence tests
- **No Frontend Changes** (internal only)

**Daily Standup Focus:**
- ¿Sync service funciona?
- ¿PySpark genera código idéntico?
- ¿Performance OK?

**Definition of Done:**
- CI/CD green
- Tests pass 100%
- Documentation updated

---

### **Semana 4-5 (Mar 3-17): v4.1 Cartridge Migration**

**Sprint Planning:**
- **Backend:** Refactorizar 6 cartridges
- **Core:** PromptComposer con 3 capas
- **Testing:** Todos los cartridges equivalentes
- **No Frontend Changes** (still internal)

**Risks:**
- Snowflake tiene más complejidad (Snowpark + SQL)
- dbt requiere YAML + SQL dual output

**Mitigation:**
- Start con cartridges simples (AWS, GCP)
- Dejar Snowflake y dbt para últimos días

---

### **Semana 6-7 (Mar 17-31): v4.2 Deep Triage**

**Sprint Planning:**
- **Backend:** Refactorizar Agent A
- **Core:** Field-level analysis, pattern detection
- **Testing:** Accuracy metrics >95%
- **No Frontend Changes** (metadata only)

**Visible Change:**
- Usuarios verán mejor metadata en Discovery
- Design Registry tiene más detalles

---

### **Semana 8-9 (Mar 31 - Apr 14): v4.3 AI Orchestration**

**Sprint Planning:**
- **Backend:** Multi-Model Router
- **Core:** Self-Learning básico
- **Testing:** Cost reduction validation
- **No Frontend Changes** (backend optimization)

**Business Impact:**
- Costos reducidos 20%+
- Mejor calidad de código

---

### **Semana 10 (Apr 14-21): v4.4 Admin UI**

**Sprint Planning:**
- **Frontend:** Admin panel completo
- **UI:** CRUD, version history, overrides
- **Testing:** E2E con Playwright
- **Documentation:** User guides

**Visible Change:**
- Admins pueden editar prompts en UI
- Tenants pueden customizar

---

## 📊 COMPARISON: RIESGO POR ESTRATEGIA

### Monolítico (A):

```
Riesgo Acumulado por Semana:
Semana 1: ██░░░░░░░░ 20%
Semana 2: ███░░░░░░░ 30%
Semana 3: ████░░░░░░ 40%
Semana 4: █████░░░░░ 50%
Semana 5: ██████░░░░ 60%
Semana 6: ███████░░░ 70%
Semana 7: ████████░░ 80%
Semana 8: █████████░ 90%
Semana 9: ██████████ 100% <- AQUÍ se testea TODO
Semana 10: Fix bugs o explota
```

**Riesgo Peak:** Semana 9 (todo integrado por primera vez)

---

### Incremental (B):

```
Riesgo por Release:
v4.0 (S1-3):   ████░░░░░░ 40% (pero contenido)
v4.1 (S4-5):   ████░░░░░░ 40% (pero contenido)
v4.2 (S6-7):   ███░░░░░░░ 30% (solo Agent A)
v4.3 (S8-9):   ███░░░░░░░ 30% (solo Router)
v4.4 (S10):    ██░░░░░░░░ 20% (solo UI)

Cada release es independiente, falla no afecta anteriores
```

**Riesgo Peak:** v4.0 y v4.1 (40% cada uno, pero aislado)

---

## 🎁 BENEFICIOS ADICIONALES DE INCREMENTAL

### 1. **Team Velocity Tracking**
```
Monolítico: Velocity medible solo al final
Incremental: Velocity cada 2 semanas (ajustes posibles)
```

### 2. **Marketing & Communication**
```
Monolítico: 1 big announcement (todo o nada)
Incremental: 5 anuncios (momentum sostenido)
  - "v4.0: Nueva infraestructura de prompts"
  - "v4.1: Eliminación completa de hardcode"
  - "v4.2: Análisis forense profundo"
  - "v4.3: AI multi-modelo inteligente"
  - "v4.4: Customización total para clientes"
```

### 3. **Hiring & Onboarding**
```
Monolítico: Difícil onboardear mid-sprint
Incremental: Nuevos devs se unen en v4.2/v4.3 fácilmente
```

### 4. **Customer Success**
```
Monolítico: Clientes esperan 10 semanas
Incremental: Clientes ven progreso cada 2 semanas
  - "Estamos migrando a arquitectura avanzada"
  - "Mejora continua visible"
```

---

## 🚀 DECISIÓN FINAL RECOMENDADA

### **OPCIÓN B: Sub-Releases Incrementales**

**Versiones:**
- **v4.0** - Foundation (3 semanas) - Mar 3
- **v4.1** - Cartridge Migration (2 semanas) - Mar 17
- **v4.2** - Deep Triage (2 semanas) - Mar 31
- **v4.3** - AI Orchestration (2 semanas) - Apr 14
- **v4.4** - Admin UI (1 semana) - Apr 21

**Total Time:** 10 semanas (vs 8-10 monolítico)  
**Risk:** 🟢 BAJO (vs 🔴 ALTO monolítico)  
**Business Value:** Gradual desde v4.0 (vs todo en v4.0)

---

## 📝 PRÓXIMOS PASOS

### Acción Inmediata (Hoy):
1. ✅ **Aprobar** esta estrategia incremental
2. ✅ **Crear** ticket para Sprint 0 (Feb 10-17)
3. ✅ **Kickoff** extracción de prompts de v3.9

### Acción Esta Semana:
1. ✅ Setup `prompt_lab/` estructura
2. ✅ Diseñar migrations SQL
3. ✅ Extraer prompts existentes
4. ⚠️ **MCP Servers: NO NECESARIOS** (VSCode + Python scripts son suficientes)

### Acción Próxima Semana (Feb 17):
1. ✅ **Start v4.0 Sprint** (Foundation)
2. ✅ Daily standups enfocados
3. ✅ CI/CD configurado para tests de equivalencia

---

**Documento Status:** PROPOSAL - Awaiting Approval  
**Decisión Requerida De:** Tech Lead, Product Owner  
**Deadline Decisión:** Feb 11, 2026  
**Owner:** Development Team  

---

## 🗳️ VOTACIÓN (Para equipo)

**Opción A: Monolítico (v4.0 Big Bang en 8-10 semanas)**
- Pros: Más rápido (2 semanas menos), menos overhead PM
- Cons: Alto riesgo, feedback tardío, difícil rollback

**Opción B: Incremental (v4.0 → v4.4 en 10 semanas)**
- Pros: Bajo riesgo, feedback continuo, rollback fácil, valor gradual
- Cons: +2 semanas, 5 releases vs 1

**Recomendación del Equipo:** ✅ **OPCIÓN B**

---

*"Ship fast, but ship safe. Value delivered incrementally beats value promised eventually."*
