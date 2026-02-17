# Cómo Usar el Data Architect/PM Agent

**Para qué sirve:** Consultar a un "Product Manager virtual" antes de implementar features para asegurar que aporten valor real al usuario (Data Engineer migrando ETL legacy).

---

## Escenarios de Uso

### 1. Evaluar una Nueva Feature

**Antes de codear**, pregunta al agent si la feature suma:

```
@workspace Usando el rol del Data Architect/PM Agent en .github/copilot/agents/data-architect-pm.md, 
evalúa esta feature:

Feature: Exportar código generado a GitHub directamente desde la UI
Descripción: Botón en Refinement View que hace push automático a un repo de GitHub
Esfuerzo estimado: 2 semanas
```

**El agent responderá con:**
- ✅ APPROVE / ⚠️ DEFER / ❌ REJECT
- Evaluación de valor para el usuario
- ROI estimado
- Condiciones o alternativas sugeridas

---

### 2. Revisar Prioridades del Backlog

**Al planificar un sprint**, pide revisión del scope:

```
@workspace Usando el rol del Data Architect/PM Agent, revisa y prioriza estas features 
del backlog v4.0 por ROI para el usuario:

1. Zero-Hardcode Generation (prompts en DB)
2. Deep Forensic Triage (column profiling + PII)
3. Real-Time Validation (syntax + semantic checks)
4. UI Component Library (Shadcn UI refactor)
5. GraphQL API Layer

Ordénalas por impacto en las 3 columnas del sistema.
```

---

### 3. Evaluar Decisiones de Arquitectura

**Cuando hay dos enfoques posibles:**

```
@workspace Desde la perspectiva del Data Architect/PM Agent, ¿cuál enfoque es mejor 
para el usuario final?

Problema: Cómo almacenar prompts del sistema

Opción A: Prompts globales en DB (utm_prompts sin tenant_id) con trigger de versionado
Opción B: Prompts customizables por tenant con UI de versiones y rollback

Contexto: v4.0 Feature 1 (Zero-Hardcode)
```

---

### 4. Criticar una Implementación Existente

**Post-mortem de una feature:**

```
@workspace Usando el rol del Data Architect/PM Agent, critica esta implementación 
desde la perspectiva funcional:

Feature: Sprint 13 - Visualization Dashboards
- Se agregaron 4 tabs en Triage (Quality, Schema, PII, Partitions)
- Se agregaron 4 tabs en Refinement (Code Review, Schema, Quality, Performance)
- 10 nuevos endpoints en backend

¿Esto realmente ayuda al Data Engineer? ¿O es feature creep?
```

---

### 5. Validar que un Feature Encaja en las 3 Columnas

**Durante code review:**

```
@workspace Según el Data Architect/PM Agent, ¿en qué columna encaja esta feature y 
está bien diseñada para ese propósito?

Feature: Detección automática de partitioning strategies
Implementación: Agent A analiza volumetría y sugiere partition keys
Output: Recommendations en Triage dashboard

¿Es Column 1-2 (Analysis) o Column 3-4 (Generation)?
```

---

## Preguntas Clave que el Agent Responderá

### Sobre Valor para el Usuario
- "¿Esto ahorra tiempo al Data Engineer migrando?"
- "¿Reduce riesgos (compliance, quality, security)?"
- "¿Es MUST-HAVE o NICE-TO-HAVE?"

### Sobre ROI
- "¿Cuántas horas/días ahorra por proyecto?"
- "¿Previene errores costosos?"
- "¿Justifica el esfuerzo de implementación?"

### Sobre las 3 Columnas
- "¿En qué columna encaja esta feature?"
- "¿Balancea bien con las otras columnas?"
- "¿Alguna columna está sub-desarrollada?"

### Sobre Complejidad
- "¿Hay una forma más simple de resolver esto?"
- "¿Es over-engineering?"
- "¿Estamos acumulando deuda técnica?"

---

## Ejemplos Reales de Evaluaciones

### ✅ APROBADO: Deep Forensic Triage

**Pregunta:**
```
@workspace Evalúa Feature 2 de v4.0: Deep Forensic Triage con column profiling 
automático y detección de PII
```

**Respuesta del Agent:**
> **✅ APPROVE - HIGH PRIORITY**
> 
> **User Problem:** CRITICAL. Data Engineers pierden 3-5 días manualmente profiling 
> columnas para entender calidad y riesgos PII antes de migrar.
> 
> **ROI Score:** 9/10
> - Time Saved: 3-5 días por proyecto
> - Risk Reduced: CRÍTICO - Previene migrar PII a entornos non-compliant
> - Cost Impact: Un solo compliance violation cuesta $100K+ en multas
> 
> **Strategic Fit:** Fortalece Column 1-2 (Analysis). Diferenciador competitivo con 
> PII detection powered by AI.
> 
> **Recommendation:** Implementa YA. Este es el #1 pain point en fase de Triage.

---

### ⚠️ DIFERIDO: UI Component Library

**Pregunta:**
```
@workspace Evalúa Feature 4 de v4.0: Refactor UI con Shadcn component library
```

**Respuesta del Agent:**
> **⚠️ DEFER to v4.1**
> 
> **User Problem:** LOW. UI funciona bien hoy. Esto es dev efficiency, no user value.
> 
> **ROI Score:** 3/10
> - Time Saved: 0 para usuarios (solo acelera futuro UI dev)
> - Risk Reduced: None
> 
> **Recommendation:** Difiere a v4.1. Prioriza Zero-Hardcode y Deep Triage primero - 
> esos entregan ROI inmediato.
> 
> **Alternative:** Adopta Shadcn UI incrementalmente en nuevas features, no refactor masivo.

---

### ❌ RECHAZADO: GraphQL API Layer

**Pregunta:**
```
@workspace ¿Deberíamos agregar GraphQL API layer en v4.0?
```

**Respuesta del Agent:**
> **❌ REJECT**
> 
> **User Problem:** NONE. Nadie ha pedido GraphQL. REST funciona perfecto.
> 
> **ROI Score:** 1/10
> - Implementation: 4-6 semanas (major refactor)
> - Maintenance burden: HIGH (nuevo stack, tooling, learning curve)
> 
> **Recommendation:** NO. Esto es solution looking for a problem. REST API con 
> pagination/filtering apropiados cumple todas las necesidades. No over-engineer.

---

## Tips para Mejores Evaluaciones

### 1. Sé Específico
❌ "Evalúa esta idea"  
✅ "Evalúa: Exportar código a GitHub automáticamente desde UI en Refinement view"

### 2. Provee Contexto
Incluye:
- Descripción de la feature
- Esfuerzo estimado
- Problema que resuelve
- Fase del sistema donde encaja (1-6)

### 3. Pregunta Directamente
- "¿Esto suma o no suma?"
- "¿Es prioritario vs Feature X?"
- "¿Hay una forma más simple?"

### 4. Solicita Alternativas
Si el agent rechaza/difiere, pide:
- "¿Qué feature resolvería mejor este problema?"
- "¿Cuál es la versión 80/20 de esto?"

---

## Cuándo NO Usar al Agent

**NO uses al agent para:**
- ❌ Decisiones técnicas de implementación (usa tech lead)
- ❌ Bugs o fixes urgentes (fixea directamente)
- ❌ Detalles de código (cómo nombrar variables, etc.)
- ❌ Preguntas de infraestructura (deployment, hosting)

**SÍ usa al agent para:**
- ✅ Evaluar si una feature aporta valor al usuario
- ✅ Priorizar backlog por ROI
- ✅ Decidir entre múltiples enfoques funcionales
- ✅ Revisar si estamos balanceando las 3 columnas
- ✅ Validar que entendemos el problema del usuario

---

## Integración con GitHub Issues

**Al crear un issue de feature:**

1. Consulta al agent primero
2. Copia la evaluación del agent en el issue
3. Si es APPROVE, etiqueta como `approved-by-pm`
4. Si es DEFER, marca como `backlog-review`
5. Si es REJECT, cierra el issue con la justificación

**Template de Issue:**

```markdown
## Feature Description
[Tu descripción]

## PM Agent Evaluation
[Pega aquí la respuesta del agent]

## Implementation Plan
[Si fue aprobado, tu plan de implementación]
```

---

## Mantenimiento del Agent

**El agent debe actualizarse cuando:**
- Cambian las 3 columnas del sistema (nueva fase, refactor)
- Obtienes feedback real de usuarios sobre pain points
- Cambias el target audience (ej: de SSIS a Informatica focus)
- Competencia lanza features que nos hacen falta

**Ubicación del agent:**
`.github/copilot/agents/data-architect-pm.md`

---

**Última Actualización:** Febrero 13, 2026  
**Maintainer:** Product Team
