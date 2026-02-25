# Análisis del Sidebar de Refinement (Stage 3)

**Fecha:** 20 de Febrero de 2026  
**Contexto:** Sprint 14 - Fase de Refinamiento Inteligente  
**Objetivo:** Aplicar arquitectura Medallion (Bronze/Silver/Gold) a código generado en Drafting

---

## 🎯 Filosofía de Refinement

**Input:** Código 1:1 generado en Drafting (funcional pero no optimizado)  
**Apoyo:** Metadata y análisis de Triage (cuando sea necesario)  
**Output:** Código optimizado con arquitectura Medallion (3 capas)  
**Agente Principal:** Agent F (Crítico/Auditor de Calidad)

### Flujo de Transformación

```
Drafting (Stage 2)                Refinement (Stage 3)
┌─────────────────┐              ┌──────────────────────┐
│ SSIS Package 1  │  ────────▶   │ Bronze_pkg1.py       │
│ SSIS Package 2  │  ────────▶   │ Silver_pkg2.py       │
│ SSIS Package 3  │  ────────▶   │ Gold_pkg3.py         │
│                 │              │                      │
│ • 1:1 Mapping   │              │ • Layered Design     │
│ • Basic Logic   │              │ • Best Practices     │
│ • No Structure  │              │ • Optimized Queries  │
└─────────────────┘              │ • Schema Validation  │
                                 └──────────────────────┘
```

---

## 📊 Estructura Actual del Sidebar

### ✅ **1. Refinement Status** (Implementado)
**ID:** `status`  
**Icono:** RefreshCw (morado)  
**Componente:** Vista de logs en tiempo real

**Valor:**
- ✅ Monitoreo en tiempo real del proceso de refinamiento
- ✅ Logs del orquestador (Agent F)
- ✅ Métricas de archivos analizados
- ✅ Detección de conexiones compartidas
- ✅ Indicador de progreso

**Estado:** ✅ COMPLETO - Usa `UnifiedLogViewer` con polling cada 3 segundos

**Uso:**
```tsx
// Botón principal
<button onClick={handleRunRefinement}>Refine & Modernize</button>

// Logs en tiempo real
<UnifiedLogViewer 
    mode="realtime"
    isRunning={isRefinementRunning}
    logs={logs}
/>
```

---

### ✅ **2. Code Review** (Parcialmente Implementado)
**ID:** `review` (Grupo)  
**Icono:** Eye  
**Children:** 4 sub-secciones

#### 2.1. **Orchestrator Logs** ✅ COMPLETO
**ID:** `logs`  
**Valor:**
- Logs detallados del proceso
- Decisiones del Agent F
- Errores y warnings

**Estado:** ✅ Implementado (redirige a `status`)

#### 2.2. **Code Review** ⚠️ PENDIENTE (aparece como 'comparison')
**ID:** `comparison`  
**Valor Esperado:**
- Vista diff lado a lado (original vs refinado)
- Comparación Bronze vs Silver vs Gold
- Highlighting de cambios arquitecturales
- Anotaciones de Agent F

**Estado:** ⚠️ MAPEADO A `diff` - Implementado pero con nombre diferente

**Implementación Actual:**
```tsx
{activeSection === 'diff' && (
    <div className="flex h-full gap-4">
        {/* File Explorer (25%) */}
        <div className="w-1/4">
            <FileTreeSection />
        </div>
        
        {/* Code Viewer (75%) */}
        <div className="flex-1">
            <SyntaxHighlighter 
                language="python|sql"
                showLineNumbers={true}
            />
        </div>
    </div>
)}
```

**Badges de Capa:**
- 🟠 BRONZE (raw ingestion)
- ⚪ SILVER (cleaned/validated)
- 🟡 GOLD (aggregated/business)

#### 2.3. **Schema Validation** ✅ COMPLETO
**ID:** `schema` (pero mapeado a 'validation')  
**Valor:**
- Validación de esquemas Bronze/Silver/Gold
- Historial de cambios de schema
- Detección de incompatibilidades

**Estado:** ✅ Implementado como `validation` - Usa `SchemaViewer`

```tsx
{activeSection === 'validation' && (
    <SchemaViewer projectId={projectId} showHistory={true} />
)}
```

#### 2.4. **Issues** ✅ COMPLETO
**ID:** `issues`  
**Badges:** `issueCount`  
**Valor:**
- Lista de problemas detectados
- Code smells
- Anti-patterns
- Warnings de Agent F

**Estado:** ✅ Implementado - Usa `CodeViewer`

```tsx
{activeSection === 'issues' && (
    <CodeViewer projectId={projectId} showHeader={true} />
)}
```

---

### ✅ **3. Optimization** (Completamente Implementado)
**ID:** `optimization` (Grupo)  
**Icono:** Zap  
**Children:** 4 dashboards

#### 3.1. **Quality** ✅ COMPLETO
**ID:** `quality`  
**Badges:** `qualityDelta` (diferencia antes/después)  
**Valor:**
- Métricas de código (complejidad ciclomática, duplicación)
- Scores de calidad por archivo
- Comparación pre/post refinamiento
- Recomendaciones de Agent F

**Estado:** ✅ Implementado - `QualityDashboard`

```tsx
{activeSection === 'quality' && (
    <QualityDashboard projectId={projectId} />
)}
```

#### 3.2. **Performance** ✅ COMPLETO
**ID:** `performance`  
**Valor:**
- Análisis de queries (explain plans)
- Detección de joins costosos
- Sugerencias de índices
- Estimación de tiempos de ejecución

**Estado:** ✅ Implementado - `PerformanceDashboard`

```tsx
{activeSection === 'performance' && (
    <PerformanceDashboard projectId={projectId} />
)}
```

#### 3.3. **Security** ❌ NO IMPLEMENTADO
**ID:** `security`  
**Valor Esperado:**
- Detección de vulnerabilidades SQL injection
- Validación de credenciales hardcodeadas
- Permisos de acceso
- Compliance checks (GDPR, HIPAA)

**Estado:** ❌ FALTA IMPLEMENTAR

**Propuesta:**
```tsx
{activeSection === 'security' && (
    <SecurityAuditPanel 
        projectId={projectId}
        checks={[
            'sql_injection',
            'hardcoded_credentials',
            'rbac_compliance',
            'data_encryption'
        ]}
    />
)}
```

#### 3.4. **Best Practices** ❌ NO IMPLEMENTADO
**ID:** `practices`  
**Valor Esperado:**
- Checklist de estándares aplicados
- Convenciones de naming
- Patrones de diseño detectados
- Score de adherencia

**Estado:** ❌ FALTA IMPLEMENTAR

**Propuesta:**
```tsx
{activeSection === 'practices' && (
    <BestPracticesAudit 
        projectId={projectId}
        categories={[
            'naming_conventions',
            'error_handling',
            'logging',
            'documentation',
            'modularity'
        ]}
    />
)}
```

---

### ⚠️ **4. Actions** (Parcialmente Implementado)
**ID:** `actions` (Grupo)  
**Icono:** Settings  
**Children:** 2 configuraciones

#### 4.1. **Settings** ✅ COMPLETO
**ID:** `settings`  
**Valor:**
- Configuración de arquitectura (Design Registry)
- Naming conventions (silver_prefix, gold_prefix)
- Paths y storage locations
- Privacy settings (masking_method)

**Estado:** ✅ COMPLETO - Usa `DesignRegistryPanel` con auto-inicialización

**Implementación:**
```tsx
{activeSection === 'settings' && (
    <DesignRegistryPanel projectId={projectId} />
)}
```

**Nota:** La tecnología (target_tech) se selecciona en **Stage 2 (Drafting)**, no en Refinement.
Cambiar la tecnología después de Drafting invalidaría todo el código generado.
```tsx
{activeSection === 'settings' && (
    <DesignRegistryPanel projectId={projectId} />
)}
```

#### 4.2. **Cartridges (Prompts)** ✅ COMPLETO
**ID:** `prompts`  
**Componente:** `CartridgePromptsEditor`  
**Valor:**
- Editar prompts de cartridge específicos de la tecnología elegida
- Solo muestra Bronze, Silver y Gold de la tecnología del proyecto
- Prompts de sistema (globales) son read-only
- Solo administradores pueden modificar cartridges

**Estado:** ✅ COMPLETO - Usa `CartridgePromptsEditor` con filtrado por tecnología

**Implementación:**
```tsx
{activeSection === 'prompts' && (
    <CartridgePromptsEditor projectId={projectId} />
)}
```

**Ejemplo:** Si el proyecto usa **Databricks (PySpark)**, se mostrarán:
- 🟤 `cartridge_databricks_bronze` - Patrones de ingesta raw
- ⚪ `cartridge_databricks_silver` - Transformaciones y limpieza
- 🟡 `cartridge_databricks_gold` - Lógica de negocio y agregaciones

**Restricciones:**
- ✅ Automáticamente detecta la tecnología del proyecto
- ✅ Solo muestra cartridges relevantes (no agent prompts)
- ⚠️ Requiere rol ADMIN para modificar
- ✅ Prompts globales (system) son read-only
- ✅ Cambios solo afectan código futuro (re-ejecutar Refinement)
```tsx
{activeSection === 'prompts' && (
    <PromptsExplorer projectId={projectId} />
)}
```

---

## 🔗 Conexión con Otras Fases

### Desde Triage (Stage 1)
**Datos Utilizados:**
- ✅ Metadata de assets (`utm_objects`)
- ✅ Esquemas de tablas (`utm_asset_columns`)
- ✅ Contexto de negocio (`utm_asset_context`)
- ✅ Análisis de complejidad
- ✅ Detección de PII

**Escenario de Uso:**
```python
# Agent F verifica contra metadata de Triage
triage_schema = db.get_asset_columns(object_id)
refined_schema = parse_bronze_notebook(notebook_path)

if refined_schema != triage_schema:
    log_warning("Schema drift detected, applying corrections...")
```

### Desde Drafting (Stage 2)
**Datos Utilizados:**
- ✅ Código generado 1:1 (`/drafting/*.py`)
- ✅ Registry de diseño (`utm_design_registry`)
- ✅ Target technology seleccionado
- ✅ Logs de generación

**Transformación:**
```
Drafting Output               Refinement Input
┌─────────────────┐          ┌──────────────────┐
│ job_customers.py│    ───▶  │ Bronze:          │
│ (1 archivo)     │          │  - ingest_raw    │
│                 │          │ Silver:          │
│ • Lógica básica │          │  - cleanse       │
│ • Sin layers    │          │  - validate      │
│ • Monolítico    │          │ Gold:            │
└─────────────────┘          │  - aggregate     │
                             │  - business_kpis │
                             └──────────────────┘
```

---

## 📈 Métricas del Sidebar (Badges)

| Badge | Fuente | Endpoint | Descripción |
|-------|--------|----------|-------------|
| `issueCount` | CodeViewer | `/projects/{id}/code-issues` | Cantidad de problemas detectados |
| `qualityDelta` | QualityDashboard | `/projects/{id}/quality-metrics` | Mejora de calidad (%) |
| `filesGenerated` | FileSystem | `/projects/{id}/files` | Archivos en `/refinement` |

**Hook para Métricas:**
```typescript
// apps/web/app/hooks/useSidebarMetrics.ts
const { metrics } = useSidebarMetrics(projectId, stage, autoRefresh=true);

// Retorna:
{
    issueCount: 12,
    qualityDelta: +34, // 34% de mejora
    filesGenerated: 45,
    bronzeNodes: 15,
    silverNodes: 18,
    goldNodes: 12
}
```

---

## 🎨 Estado Visual de Secciones

```
✅ COMPLETO       - Implementado y funcional
⚠️ PARCIAL        - Componente existe pero no conectado
❌ FALTA          - No implementado
🔗 DEPENDENCIA    - Requiere datos de otra fase
```

**Resumen de Implementación:**

| Sección | Estado | Prioridad | Effort |
|---------|--------|-----------|--------|
| Refinement Status | ✅ | N/A | - |
| Orchestrator Logs | ✅ | N/A | - |
| Code Review | ✅ | N/A | - |
| Schema Validation | ✅ | N/A | - |
| Issues | ✅ | N/A | - |
| Quality | ✅ | N/A | - |
| Performance | ✅ | N/A | - |
| Settings | ✅ | N/A | - |
| Prompts | ✅ | N/A | - |
| **Security** | ❌ | 🔥 HIGH | Sprint 15 |
| **Best Practices** | ❌ | 🔥 HIGH | Sprint 15 |

---

## ✅ Refinement Sidebar - Estado Final

### Completado (10/12 secciones - 83%)

**Status Section (1/1):**
- ✅ status - Refinement Status (con logs en tiempo real)

**Review Section (4/4):**
- ✅ logs - Orchestrator Logs
- ✅ comparison/diff - Code Review (con Medallion badges)
- ✅ schema/validation - Schema Validation
- ✅ issues - Issues Viewer

**Optimization Section (2/4):**
- ✅ quality - Quality Dashboard
- ✅ performance - Performance Dashboard
- 🟡 security - Placeholder (Sprint 15)
- 🟡 practices - Placeholder (Sprint 15)

**Actions Section (2/2):**
- ✅ settings - Design Registry (con auto-inicialización)
- ✅ prompts - Cartridge Editor (filtrado por tecnología del proyecto)

### Notas de Diseño

1. **¿Por qué no está Tech Mixer?**
   - La tecnología se elige en **Drafting (Stage 2)**
   - Cambiar tecnología en Refinement invalidaría todo el código generado
   - Si necesitas cambiar tecnología, debes volver a Drafting

2. **¿Qué prompts se pueden editar en Cartridges?**
   - Solo los 3 cartridges de la tecnología del proyecto: Bronze, Silver, Gold
   - Ejemplo: Si es Databricks → `cartridge_databricks_bronze`, `cartridge_databricks_silver`, `cartridge_databricks_gold`
   - Los agent prompts (Agent A, C, F, G) NO se editan aquí
   - Prompts globales (system) son read-only
   - Requiere rol ADMIN para modificar

3. **Security y Best Practices pendientes:**
   - Planificadas para Sprint 15
   - Requieren integración con herramientas de análisis estático
   - Incluirán: SQL injection detection, credential scanning, RBAC compliance

---

## 🚀 Próximos Pasos (Sprint 15)

### 1. Security Audit Panel
- Integrar con herramientas de análisis estático
- Detección automática de vulnerabilidades (SQL injection, hardcoded credentials)
- RBAC compliance scoring
- Data encryption validation

### 2. Best Practices Dashboard
- Checklist interactivo de mejores prácticas
- Documentación inline de patrones
- Auto-fix de issues menores
- Code smell detection

**Total estimado: 2 sprints completos 🎯**

---

## 🔮 Futuras Mejoras (v4.1+)

### 1. Diff View Mejorado
- Split view (side-by-side)
- Syntax-aware diffing
- Comentarios de Agent F inline
- Blame/history de cambios

### 4. Architecture Visualization
- Diagrama de flujo Bronze → Silver → Gold
- Mapa de dependencias
- Impact analysis

---

## 📚 Referencias

- **Componentes V3.9:** `apps/web/app/components/visualization/`
- **Config Sidebar:** `apps/web/app/config/sidebar-sections.ts`
- **RefinementView:** `apps/web/app/components/stages/RefinementView.tsx`
- **Métricas Hook:** `apps/web/app/hooks/useSidebarMetrics.ts`

---

**Conclusión:**  
La barra de Refinement está **83% completa (10/12 secciones)** con todos los componentes core funcionando. Security y Best Practices están planificadas para Sprint 15. Tech Mixer fue excluido intencionalmente ya que la tecnología se selecciona en Drafting (Stage 2).

