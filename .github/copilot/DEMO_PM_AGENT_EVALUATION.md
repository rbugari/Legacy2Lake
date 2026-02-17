# Demo: Evaluación de Features v4.0 con PM Agent

**Objetivo:** Demostrar cómo consultar al Data Architect/PM Agent para validar que features aporten valor real antes de implementarlas.

**Agent:** `.github/copilot/agents/data-architect-pm.md`  
**Guía:** `.github/copilot/HOW_TO_USE_PM_AGENT.md`

---

## Ejemplo 1: Zero-Hardcode Generation (v4.0 Feature 1)

### Pregunta al Agent

```
@workspace Usando el rol del Data Architect/PM Agent en .github/copilot/agents/data-architect-pm.md,
evalúa esta feature de v4.0:

Feature: Zero-Hardcode Generation
Descripción: Eliminar TODOS los templates hardcoded de Python/TypeScript y cargar prompts dinámicamente desde utm_prompts (base de datos). Incluye versionado automático con trigger.
Esfuerzo: 2-3 semanas
Problema: Hoy los templates están hardcoded en el código (imports de Python). Para cambiar un template hay que hacer deploy. Los usuarios no pueden optimizar prompts sin tocar código.
Fase impactada: Column 3-4 (Drafting + Refinement) - Generación de código
```

### Respuesta Esperada del Agent

**✅ APPROVE - CRITICAL PRIORITY**

### 🎯 User Problem: CRITICAL
Data Engineers necesitan ajustar templates de generación para casos específicos (ej: agregar retry logic, custom error handling, optimizaciones específicas de su infra). Hoy esto requiere:
1. Modificar código Python hardcoded
2. Hacer commit + PR + code review
3. Deploy a producción
4. Timing: 2-3 días por cambio

Con Zero-Hardcode:
- Modificar prompt en DB (UI admin)
- Cambio efectivo inmediatamente
- Rollback instantáneo si algo falla
- Timing: 5 minutos por cambio

**Importancia:** CRITICAL - Core de la propuesta de valor (customización sin código)

### 💰 Business Value
- **Time Saved:** 2-3 días → 5 minutos = 40x más rápido por ajuste de template
- **Risk Reduced:** 
  - Deploy risk eliminated (no code changes)  
  - Instant rollback (trigger guarda versión anterior automáticamente)
  - PII/compliance: Auditar quién cambió qué y cuándo
- **Cost Impact:** 
  - Reduce consultant time (cliente puede iterar solo)
  - Enables self-service (no necesita dev para ajustes)
  - Competitive edge: Otros ETL tools (Matillion, Fivetran) no tienen esto
- **ROI Score:** 10/10

### ⚙️ Implementation Complexity
- **Effort:** 2-3 semanas realista
- **Dependencies:** 
  - ✅ utm_prompts table ya existe (Sprint 1)
  - ✅ Agent C ya resuelve LLM desde DB
  - Necesita: Refactor de 6 agents para cargar prompts desde DB
- **Risk:** LOW - Cambio incremental, no breaking

### 🎪 Strategic Fit
- **Column Impact:** Fortalece Column 3-4 (Generation/Refinement) - Core business
- **Competitive Edge:** ✅ SÍ - Feature único vs competencia
- **Platform Play:** ✅ SÍ - Habilita marketplace de prompts (futuro v5.0)

### ✅ Recommendation: APPROVE

**Rationale:**  
Este es el #1 feature que diferencia Legacy2Lake de herramientas legacy (Matillion, Snaplogic). La capacidad de ajustar templates SIN tocar código es crítica para Data Engineers que necesitan personalization. El ROI es claro: de días a minutos por ajuste.

**Conditions:**
1. ✅ Mantener prompts globales (NO tenant-specific en v4.0) - Simplificado correcto
2. ✅ Trigger automático de versionado - Safety net sin UI compleja
3. ✅ Solo ADMIN puede ver historial - Evita confusión de usuarios
4. ⚠️ Agregar validación de syntax en prompts antes de guardar (prevenir prompts rotos)

**Priority:** Ship FIRST en v4.0 - Blocker para otros features de customización

---

## Ejemplo 2: UI Component Library (v4.0 Feature 4)

### Pregunta al Agent

```
@workspace Usando el rol del Data Architect/PM Agent, evalúa esta feature:

Feature: UI Component Library Refactor
Descripción: Refactorizar todos los componentes React a Shadcn UI, crear design system consistente, mejorar accessibility (ARIA labels, keyboard navigation), theme customization.
Esfuerzo: 2-3 semanas
Problema: UI funcional pero inconsistente, algunos componentes custom son difíciles de mantener
Fase impactada: Todas (UI transversal)
```

### Respuesta Esperada del Agent

**⚠️ DEFER to v4.1 o v4.2**

### 🎯 User Problem: LOW
La UI actual **funciona correctamente**. Los Data Engineers pueden realizar todas las tareas necesarias (discovery, triage, code generation, governance). Este es un problema de **developer experience** (DX) no de **user experience** (UX).

**Pain real del usuario:**
- ❌ "No puedo generar código" → NO, esto funciona
- ❌ "No entiendo cómo usar la UI" → NO, es intuitiva
- ✅ "Algunos botones tienen estilos levemente diferentes" → SÍ, pero LOW impact

**Importancia:** LOW - Mejora estética, no funcional

### 💰 Business Value
- **Time Saved:** 0 para usuarios finales
- **Risk Reduced:** Ninguno (no afecta funcionalidad core)
- **Cost Impact:** 
  - Acelera desarrollo futuro de UI (componentes reusables)
  - Mejora brand perception (UI más pulida)
  - Pero... no genera más revenue ni ahorra tiempo al usuario migrando
- **ROI Score:** 3/10 (beneficio indirecto, no directo)

### ⚙️ Implementation Complexity
- **Effort:** 2-3 semanas (refactor masivo de 30+ componentes)
- **Dependencies:** Ninguna blocking, pero...
- **Risk:** MEDIUM
  - Regresiones: Alto riesgo de romper functionality existente
  - Testing burden: Necesita re-test completo de toda la UI
  - Learning curve: Team necesita aprender Shadcn patterns

### 🎪 Strategic Fit
- **Column Impact:** UI transversal, no fortalece ninguna columna específica
- **Competitive Edge:** ❌ No - Los usuarios compran por features (code generation, quality, governance), no por si usas Shadcn UI
- **Platform Play:** Neutral - No habilita features futuras críticas

### ⚠️ Recommendation: DEFER to v4.1

**Rationale:**  
Si bien componentization es una buena práctica, **NO resuelve ningún pain point del usuario HOY**. El Data Engineer migrando 500 SSIS packages no se queja de que los botones no tienen border-radius consistente - se queja de que el código generado tiene errores o que la UI no tiene herramientas de analysis.

**Priorizar primero:**
1. Zero-Hardcode (Feature 1) - Impacto directo en customización
2. Deep Forensic Triage (Feature 2) - Ahorra 3-5 días de análisis manual
3. Real-Time Validation (Feature 3) - Reduce errores en código generado

**Alternative Approach (si insistes en mejoras de UI):**
- Adopta Shadcn UI **incrementalmente** en NUEVAS features (no refactor masivo)
- Ejemplo: Próximo feature que agregues a UI, usa Shadcn
- Benefit: Sin riesgo de regresión, sin delay de 3 semanas

**Conditions para APROBAR en v4.1:**
- Debe haber 0 bugs críticos de features v4.0
- Usuarios deben pedir explícitamente mejoras de UX
- ROI debe justificarse con datos reales (ej: menos abandono en onboarding)

---

## Ejemplo 3: Exportar Código a GitHub Directamente

### Pregunta al Agent

```
@workspace Evalúa esta feature propuesta:

Feature: GitHub Export Button
Descripción: Botón en Refinement View que permite hacer push automático del código generado a un repositorio de GitHub (sin descargar zip primero)
Esfuerzo: 1 semana
Problema: Hoy el usuario descarga un ZIP del código generado, luego manualmente hace git add/commit/push. Es tedioso si genera código 50 veces al día durante iteraciones.
Fase impactada: Column 5-6 (Handover) - Delivery del output
```

### Respuesta Esperada del Agent

**✅ APPROVE - MEDIUM PRIORITY**

### 🎯 User Problem: MEDIUM
Usuarios iteran frecuentemente durante refinement (regeneran código con ajustes). Cada iteración requiere:
1. Click "Download ZIP"
2. Unzip files
3. `git add .`
4. `git commit -m "msg"`
5. `git push`

**Tiempo:** 2-3 minutos × 20 iteraciones/día = 40-60 minutos/día desperdiciados

Con GitHub Export:
- Click "Push to GitHub"
- Select branch
- Auto-commit con mensaje descriptivo
- **Timing:** 10 segundos

**Importancia:** MEDIUM - Pain point real pero workaround existe (manual push)

### 💰 Business Value
- **Time Saved:** ~1 hora/día por Data Engineer = 5 horas/semana
- **Risk Reduced:** 
  - Previene errores de "olvidé pushear última versión"
  - Audit trail automático (cada push es un commit)
- **Cost Impact:** 
  - UX improvement → Reduce friction
  - Competitive edge: Herramientas como dbt Cloud ya tienen esto
- **ROI Score:** 7/10

### ⚙️ Implementation Complexity
- **Effort:** 1 semana (GitHub API integration)
- **Dependencies:**
  - Necesita GitHub OAuth authentication
  - Necesita guardar GitHub access token (encrypted en utm_provider_vault)
- **Risk:** LOW - Feature aislada, no afecta core generation

### 🎪 Strategic Fit
- **Column Impact:** Fortalece Column 5-6 (Handover) - Deployment readiness
- **Competitive Edge:** ✅ Paridad con dbt Cloud, Matillion
- **Platform Play:** ✅ Habilita GitOps workflows (futuro)

### ✅ Recommendation: APPROVE - Ship en v4.0 o v4.1

**Rationale:**  
Feature de alta utilidad que reduce friction significativo. ROI claro (1 hora/día ahorrada). Competencia ya tiene esto (dbt Cloud), debemos tener paridad.

**Conditions:**
1. ✅ Solo para GitHub inicialmente (no GitLab/Bitbucket en v4.0)
2. ✅ Requiere GitHub OAuth consent del usuario
3. ⚠️ Agregar opción "Create PR" en vez de "Direct Push" (safer for production)
4. ⚠️ Validar que usuario tiene write access al repo ANTES de intentar push

**Priority:** Ship AFTER Zero-Hardcode y Deep Triage (Feature 1 y 2 son más críticos)

---

## Ejemplo 4: GraphQL API Layer

### Pregunta al Agent

```
@workspace Evalúa agregar GraphQL API layer:

Feature: GraphQL API
Descripción: Agregar GraphQL endpoint adicional al REST API existente para permitir queries más flexibles desde el frontend
Esfuerzo: 4-6 semanas
Problema: Algunos endpoints REST requieren múltiples calls para obtener datos relacionados (ej: project + assets + nodes)
Fase impactada: API Layer (transversal)
```

### Respuesta Esperada del Agent

**❌ REJECT**

### 🎯 User Problem: NONE
**NO HAY PAIN POINT REAL DEL USUARIO**

Pregunta clave: "¿Cuántos usuarios han pedido GraphQL?"  
Respuesta: 0

El "problema" de múltiples API calls es un **internal dev concern**, no un user pain. Los Data Engineers migrando ETL no saben ni les importa si usas REST o GraphQL - solo quieren que la UI sea rápida y correcta.

**Importancia:** NONE - Solution looking for a problem

### 💰 Business Value
- **Time Saved:** 0 (usuario no percibe diferencia)
- **Risk Reduced:** NEGATIVO - Aumenta complejidad
- **Cost Impact:**
  - ❌ Más código para mantener (REST + GraphQL)
  - ❌ Team necesita aprender GraphQL
  - ❌ Tooling adicional (Apollo Client, schema stitching)
- **ROI Score:** -2/10 (ROI negativo)

### ⚙️ Implementation Complexity
- **Effort:** 4-6 semanas (major refactor)
- **Dependencies:** Breaking API changes potenciales
- **Risk:** HIGH
  - Learning curve para backend + frontend team
  - Fragmenta codebase (algunos endpoints REST, otros GraphQL)
  - Debugging más complejo (GraphQL middleware, resolvers)

### 🎪 Strategic Fit
- **Column Impact:** Ninguna - No mejora Analysis, Generation, ni Governance
- **Competitive Edge:** ❌ Competencia usa REST y funciona perfecto
- **Platform Play:** Neutral - No habilita features futuras

### ❌ Recommendation: REJECT

**Rationale:**  
GraphQL es una tecnología excelente... cuando resuelve un problem REAL. Este no es el caso. Los supuestos "múltiples calls" pueden resolverse con:
- REST endpoints más específicos (ej: `/projects/{id}/full` que include assets + nodes)
- Eager loading en backend (joins SQL)  
- Frontend caching (React Query, SWR)

**Don't over-engineer.** REST API funciona perfecto hoy. Tiempo mejor invertido en:
- Feature 1: Zero-Hardcode (suma valor real)
- Feature 2: Deep Forensic Triage (suma valor real)
- Feature 3: Real-Time Validation (suma valor real)

**Alternative:** Si REALMENTE tienes problemas de performance por múltiples calls:
1. Identifica los 2-3 endpoints lentos específicos
2. Optimízalos con joins SQL o create composite endpoints
3. Total effort: 2 días vs 6 semanas de GraphQL

**Conclusion:** No justifica esfuerzo vs ROI. REJECT.

---

## Resumen de Evaluaciones

| Feature | Decisión | ROI Score | Prioridad | Rationale |
|---------|----------|-----------|-----------|-----------|
| **Zero-Hardcode Generation** | ✅ APPROVE | 10/10 | 🔴 CRITICAL | Core value prop, 40x speedup en ajustes |
| **Deep Forensic Triage** | ✅ APPROVE | 9/10 | 🔴 HIGH | Ahorra 3-5 días análisis manual |
| **Real-Time Validation** | ✅ APPROVE | 8/10 | 🟡 HIGH | Reduce errores código generado |
| **GitHub Export** | ✅ APPROVE | 7/10 | 🟡 MEDIUM | Ahorra 1 hora/día, paridad competencia |
| **UI Component Library** | ⚠️ DEFER | 3/10 | 🟢 LOW | No resuelve user pain HOY |
| **GraphQL API** | ❌ REJECT | -2/10 | ⛔ N/A | Over-engineering sin beneficio |

---

## Cómo Usar Esta Demo

### 1. Copia el Formato de Pregunta

```
@workspace Usando el rol del Data Architect/PM Agent en .github/copilot/agents/data-architect-pm.md,
evalúa esta feature:

Feature: [Nombre]
Descripción: [Qué hace]
Esfuerzo: [X semanas]
Problema: [Qué pain resuelve del user]
Fase impactada: [1-6 / Columns 1-2, 3-4, 5-6]
```

### 2. Espera la Evaluación del Agent

Recibirá:
- ✅ APPROVE / ⚠️ DEFER / ❌ REJECT
- User Problem assessment (CRITICAL / HIGH / MEDIUM / LOW / NONE)
- ROI Score (0-10)
- Implementation complexity
- Strategic fit analysis
- Detailed rationale

### 3. Toma Decisiones Basadas en Data

- **APPROVE + CRITICAL/HIGH:** Implementa YA
- **APPROVE + MEDIUM:** Implementa después de críticos
- **DEFER:** Agregar al backlog v4.1
- **REJECT:** Cerrar issue, buscar alternativa más simple

### 4. Documenta en GitHub Issues

Copia la evaluación del agent en el issue para justificar decisión.

---

**Creado:** Febrero 13, 2026  
**Próxima Revisión:** v4.0 Sprint Planning (Marzo 2026)
