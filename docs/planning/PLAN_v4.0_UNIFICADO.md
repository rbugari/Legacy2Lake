# Plan Unificado v4.0 — Backend Intelligence Layer

**Fecha:** 15 de febrero de 2026  
**Estado:** EN EJECUCIÓN  
**Estrategia:** Todo el backend primero, visual al final  
**Versión:** v4.0 GA

---

## Índice

1. [Visión General](#1-visión-general)
2. [Diagnóstico — Los 7 Gaps](#2-diagnóstico--los-7-gaps)
3. [Fase A — Quick Assessment Service](#3-fase-a--quick-assessment-service)
4. [Fase B — Knowledge Packet Service](#4-fase-b--knowledge-packet-service)
5. [Fase C — Table Impact Registry](#5-fase-c--table-impact-registry)
6. [Fase D — Triage Pipeline v2 (Enrichment)](#6-fase-d--triage-pipeline-v2)
7. [Fase E — Visual (UI) — AL FINAL](#7-fase-e--visual-ui--al-final)
8. [Migración de Datos (SQL)](#8-migración-de-datos-sql)
9. [Endpoints API](#9-endpoints-api)
10. [Plan de Ejecución](#10-plan-de-ejecución)
11. [Decisiones Tomadas](#11-decisiones-tomadas)
12. [Testing](#12-testing)
13. [Archivos Afectados](#13-archivos-afectados)

---

## 1. Visión General

### Problema Central

El sistema parsea bien cada paquete individualmente, pero:

1. **No hay pre-evaluación** — El usuario espera 15-30 seg (LLM) para saber si su proyecto sirve
2. **Los datos recolectados no alimentan la generación** — Agent C ve "STRING" en vez de `INT`, `VARCHAR(50)`
3. **No hay vista Table-Centric** — Si 3 paquetes leen de `dbo.Customers`, no hay forma de saberlo sin abrir los 3 manualmente
4. **No hay forma de preguntar** — "¿Quién le pega a la tabla X y de qué forma?" → no hay agente que responda

### Solución: 4 Fases Backend + 1 Visual

| Fase | Qué | Servicio Nuevo | Tabla Nueva |
|------|-----|----------------|-------------|
| **A** | Pre-evaluación rápida del proyecto | `QuickAssessmentService` | — (usa `utm_projects.settings`) |
| **B** | Unificar 6 silos → 1 paquete por asset | `KnowledgePacketService` | — (read-only, sin tabla) |
| **C** | Vista table-centric: quién le pega a cada tabla | `TableImpactService` | `utm_table_impacts` |
| **D** | Enriquecer Triage: cruce, DAG, context | Mejoras en `triage.py` pipeline | — |
| **E** | UI: DiscoveryView, TriageView, TablesView | Frontend (TSX) | — |

### Diagrama de dependencias entre fases

```
Fase A (QA)                    ← Independiente, puede arrancar ya
   │
Fase B (Knowledge)             ← Independiente de A, puede ir en paralelo
   │
Fase C (Table Impact)          ← Independiente de A y B
   │
Fase D (Triage v2)             ← Depende de B + C (usa KnowledgePacket + TableImpact)
   │
Fase E (Visual)                ← ÚLTIMA. Depende de A + B + C + D
```

### Visión de Stages (futuro)

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Análisis   │ ──▶ │    Generación    │ ──▶ │   Entrega   │
│              │     │                  │     │             │
│  Assessment  │     │  Direct          │     │ Governance  │
│  Discovery   │     │  Re-Architecture │     │  Deploy     │
└──────────────┘     └──────────────────┘     └─────────────┘
```

> "Re-Architecture" porque Medallion es un patrón, no el único.
> Puede ser Medallion, Star Schema, Data Vault, u otro.

---

## 2. Diagnóstico — Los 7 Gaps

### GAP 1: No hay pre-evaluación rápida
- El usuario sube archivos → primera respuesta = Agent S (LLM, 15-30 seg, $$$)
- No puede saber si el proyecto es viable sin pagar LLM
- **Solución:** Fase A (Quick Assessment)

### GAP 2: 6 silos de datos desconectados
| # | Silo | Qué guarda | ¿Lo lee Agent C? |
|---|------|------------|-------------------|
| 1 | `utm_objects.metadata` (JSONB) | columns, medulla, connections | ⚠️ Solo columns (tipadas "STRING") |
| 2 | `utm_asset_columns` (Sprint 7) | 25+ campos: tipos, PII, cardinalidad | ❌ NO |
| 3 | `schema_reference.json` (R2) | Tipos DDL precisos (sqlglot) | ❌ NO |
| 4 | Sprint 8.5 cols en `utm_objects` | source_query, transformations, complexity | ❌ NO |
| 5 | `utm_column_mappings` | Reglas source→target (CAST, MASK) | ❌ NO |
| 6 | `utm_solution_context` | Contexto negocio editable | ❌ NO |

- **Solución:** Fase B (KnowledgePacket)

### GAP 3: Cruce SSIS ↔ DDL no existe
- SSIS parser extrae `SqlCommand: "SELECT * FROM dbo.Customers"`
- Librarian produce `schema_reference.json` con `CustomerID INT, Name VARCHAR(50)`
- **Nadie cruza los dos** → Agent C ve todo como "STRING"
- **Solución:** Fase B (`_resolve_columns_from_ddl()`)

### GAP 4: No hay vista Table-Centric (el que motivaste)
- Si 3 paquetes tocan `dbo.Customers`: uno INSERT, otro UPDATE, otro SELECT
- **No hay forma de saber eso** sin abrir los 3 paquetes uno por uno
- No hay visibilidad de "quién le pega a qué tabla y de qué forma"
- Puede que no sea conflicto (uno updatea campo A, otro campo B) pero hay que **verlo**
- **Solución:** Fase C (Table Impact Registry)

### GAP 5: Sprint 8.5 metadata no va al prompt de Agent A
- Triage guarda `source_query`, `transformations`, `complexity_score` en `utm_objects`
- Pero Agent A recibe `generate_manifest()` que NO incluye esos campos
- **Solución:** Fase D (Triage v2 enrichment)

### GAP 6: Business Context desconectado
- Usuario edita "Tribal Knowledge" → se guarda en `utm_solution_context`
- Agent A nunca lo lee → clasifica sin contexto de negocio
- **Solución:** Fase D (inyectar context en manifest)

### GAP 7: Dependency Graph implícito
- Triage detecta invocations (lee de X, escribe a Y) pero no construye DAG inter-asset
- No se calcula orden de ejecución → Agent C no sabe que FactSales depende de DimCustomer
- **Solución:** Fase C + D (DAG desde Table Impacts)

---

## 3. Fase A — Quick Assessment Service

### 3.1 Concepto

Evaluación híbrida post-upload: determinística (clasificación + score) + opinión LLM rápida.

- **Input:** Archivos en la carpeta Triage del proyecto
- **Output:** Score 0-100 + semáforo + desglose + opinión profesional
- **Tiempo:** 3-5 segundos
- **Trigger:** Botón manual "Quick Assess"

### 3.2 Clasificación de Archivos (4 categorías)

| Categoría | Extensiones | Score Impact |
|-----------|------------|-------------|
| **MIGRABLE** | `.dtsx`, `.dsx`, `.xml` (Informatica), `.kjb/.ktr` (Pentaho) | Alto positivo |
| **SOPORTE** | `.sql` (DDL/DML), `.csv`, `.xlsx`, `.json` (config) | Medio positivo |
| **DOCUMENTACION** | `.md`, `.txt`, `.pdf`, `.docx` | Neutral/bajo positivo |
| **NO_RECONOCIDO** | `.jpg`, `.exe`, `.zip`, otros | Negativo |

### 3.3 Fórmula del Score

```
score = (migrable * 4 + soporte * 2 + doc * 1 + no_reconocido * 0) / (total * 4) * 100

Ejemplos:
  10 SSIS + 2 SQL + 1 MD + 0 NR: (40+4+1) / (52) * 100 = 86.5 → 🟢
  5 SSIS + 0 SQL + 5 JPG:         (20+0)   / (40) * 100 = 50.0 → 🟡
  0 SSIS + 2 TXT + 4 EXE:         (0+0+2)  / (24) * 100 = 8.3  → 🔴
```

### 3.4 Semáforo

| Score | Semáforo | Significado |
|-------|----------|-------------|
| ≥ 60 | 🟢 **VERDE** | Viable. Suficientes archivos migrables. |
| 30-59 | 🟡 **AMARILLO** | Parcialmente viable. Revisar composición. |
| < 30 | 🔴 **ROJO** | No viable o faltan archivos. Bloqueadores listados. |

### 3.5 Servicio: `QuickAssessmentService`

**Archivo:** `apps/api/services/quick_assessment_service.py` (NUEVO)

```python
class QuickAssessmentResult(BaseModel):
    score: int                           # 0-100
    semaforo: str                        # "green" | "yellow" | "red"
    file_breakdown: Dict[str, int]       # {"migrable": 12, "soporte": 5, ...}
    detected_techs: List[str]            # ["SSIS", "SQL Server"]
    blockers: List[str]                  # Razones si es rojo
    file_details: List[FileClassification]
    total_files: int
    total_lines: int
    llm_opinion: Optional[str] = None    # Opinión profesional del LLM (si configurado)
    assessed_at: str

class FileClassification(BaseModel):
    filename: str
    category: str                        # MIGRABLE | SOPORTE | DOCUMENTACION | NO_RECONOCIDO
    detected_tech: Optional[str]
    complexity_hint: Optional[str]       # LOW | MEDIUM | HIGH
    size_bytes: int
    line_count: Optional[int]

class QuickAssessmentService:
    def __init__(self, tenant_id=None, client_id=None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
    
    async def assess(self, project_id: str) -> QuickAssessmentResult:
        """
        Evaluación híbrida: determinística + opinión LLM.
        """
        from apps.api.services.discovery_service import DiscoveryService
        from langchain_core.messages import SystemMessage, HumanMessage
        from datetime import datetime
        
        # 1. Reusar DiscoveryService.generate_manifest()
        manifest = DiscoveryService.generate_manifest(
            project_id, 
            tenant_id=self.tenant_id
        )
        
        file_inventory = manifest.get("file_inventory", [])
        if not file_inventory:
            raise ValueError("No hay archivos en la carpeta Triage")
        
        # 2. Clasificar cada archivo en 4 categorías
        breakdown = {"migrable": 0, "soporte": 0, "documentacion": 0, "no_reconocido": 0}
        file_details = []
        detected_techs = set()
        total_lines = 0
        
        for item in file_inventory:
            category, tech = self._classify_file(item)
            breakdown[category] += 1
            if tech:
                detected_techs.add(tech)
            
            file_details.append(FileClassification(
                filename=item["name"],
                category=category.upper(),
                detected_tech=tech,
                complexity_hint=self._estimate_complexity(item),
                size_bytes=item.get("size", 0),
                line_count=item.get("lines", 0)
            ))
            total_lines += item.get("lines", 0)
        
        # 3. Calcular score y semáforo
        total_files = len(file_inventory)
        score = self._calculate_score(breakdown, total_files)
        semaforo = self._get_semaforo(score)
        
        # 4. Identificar bloqueadores si score < 30
        blockers = self._identify_blockers(breakdown, total_files) if score < 30 else []
        
        # 5. Generar resumen compacto para LLM
        summary = self._build_summary(breakdown, detected_techs, total_files, total_lines)
        
        # 6. Obtener opinión LLM (si está configurado agent-qa)
        llm_opinion = None
        try:
            llm_opinion = await self._get_llm_opinion(summary, project_id)
        except Exception as e:
            logger.warning(f"[QA] No se pudo obtener opinión LLM: {e}", "QuickAssessment")
        
        return QuickAssessmentResult(
            score=score,
            semaforo=semaforo,
            file_breakdown=breakdown,
            detected_techs=list(detected_techs),
            blockers=blockers,
            file_details=file_details,
            total_files=total_files,
            total_lines=total_lines,
            llm_opinion=llm_opinion,
            assessed_at=datetime.utcnow().isoformat()
        )
    
    def _classify_file(self, item: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Clasifica un archivo en una de las 4 categorías."""
        filename = item["name"].lower()
        ext = filename.split('.')[-1] if '.' in filename else ''
        
        # MIGRABLE
        if ext in ['dtsx', 'dsx', 'kjb', 'ktr', 'pmx']:
            tech = None
            if ext == 'dtsx':
                tech = 'SSIS'
            elif ext == 'dsx':
                tech = 'DataStage'
            elif ext in ['kjb', 'ktr']:
                tech = 'Pentaho'
            elif ext == 'pmx':
                tech = 'Informatica'
            return ("migrable", tech)
        
        # Informatica XML
        if ext == 'xml' and 'informatica' in item.get('signatures', []):
            return ("migrable", "Informatica")
        
        # SOPORTE
        if ext in ['sql', 'csv', 'xlsx', 'xls', 'json', 'yaml', 'yml']:
            tech = None
            if ext == 'sql':
                tech = 'SQL'
            return ("soporte", tech)
        
        # DOCUMENTACION
        if ext in ['md', 'txt', 'pdf', 'docx', 'doc', 'rtf']:
            return ("documentacion", None)
        
        # NO_RECONOCIDO
        return ("no_reconocido", None)
    
    def _estimate_complexity(self, item: Dict[str, Any]) -> str:
        """Estima complejidad basado en líneas o signatures."""
        lines = item.get("lines", 0)
        if lines == 0:
            return "LOW"
        elif lines < 200:
            return "LOW"
        elif lines < 500:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _calculate_score(self, breakdown: Dict[str, int], total: int) -> int:
        """Calcula score de viabilidad."""
        if total == 0:
            return 0
        
        weighted_sum = (
            breakdown["migrable"] * 4 +
            breakdown["soporte"] * 2 +
            breakdown["documentacion"] * 1 +
            breakdown["no_reconocido"] * 0
        )
        
        max_possible = total * 4
        score = int((weighted_sum / max_possible) * 100)
        return min(max(score, 0), 100)
    
    def _get_semaforo(self, score: int) -> str:
        """Mapea score a semáforo."""
        if score >= 60:
            return "green"
        elif score >= 30:
            return "yellow"
        else:
            return "red"
    
    def _identify_blockers(self, breakdown: Dict[str, int], total: int) -> List[str]:
        """Identifica razones de bloqueo."""
        blockers = []
        
        if breakdown["migrable"] == 0:
            blockers.append("No se detectaron archivos migrables (SSIS, DataStage, etc.)")
        
        no_rec_pct = (breakdown["no_reconocido"] / total * 100) if total > 0 else 0
        if no_rec_pct > 70:
            blockers.append(f"{no_rec_pct:.0f}% de archivos no reconocidos")
        
        if breakdown["soporte"] == 0 and breakdown["migrable"] > 0:
            blockers.append("Faltan archivos de soporte (DDL, schemas)")
        
        return blockers
    
    def _build_summary(self, breakdown: Dict, techs: set, total: int, lines: int) -> str:
        """Resumen compacto para el LLM."""
        tech_list = ", ".join(techs) if techs else "No detectadas"
        return f"""Proyecto de migración. Archivos subidos: {total} ({lines:,} líneas)
- {breakdown['migrable']} paquetes migrables
- {breakdown['soporte']} archivos de soporte
- {breakdown['documentacion']} documentación
- {breakdown['no_reconocido']} no reconocidos
Tecnologías detectadas: {tech_list}
¿Es viable esta migración? ¿Riesgos principales? Responde en 3-4 líneas."""
    
    async def _get_llm_opinion(self, summary: str, project_id: str) -> Optional[str]:
        """Obtiene opinión del LLM vía Agent Matrix."""
        try:
            # Resolver modelo de agent-qa (o fallback a agent-helper)
            config = await self.db.resolve_agent_model("agent-qa")
            
            if config["provider"] == "azure":
                from langchain_openai import AzureChatOpenAI
                llm = AzureChatOpenAI(
                    deployment_name=config["deployment_name"],
                    api_key=config["api_key"],
                    azure_endpoint=config["endpoint"],
                    api_version=config.get("api_version", "2024-05-01-preview"),
                    temperature=0.3
                )
            else:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model=config["model"],
                    api_key=config["api_key"],
                    base_url=config.get("base_url"),
                    temperature=0.3
                )
            
            messages = [
                SystemMessage(content="Eres un experto en análisis de viabilidad de migraciones ETL."),
                HumanMessage(content=summary)
            ]
            
            response = await llm.ainvoke(messages)
            return response.content.strip()
        
        except Exception as e:
            logger.warning(f"[QA] Error obteniendo opinión LLM: {e}", "QuickAssessment")
            return None
```

### 3.6 Opinión LLM — Usa Agent Matrix existente

**No hay nada que tocar en la infraestructura de modelos.** `resolve_agent_model(agent_id)` acepta cualquier string. Solo:

1. Un INSERT en `utm_agent_catalog` para registrar `agent-qa`
2. El cliente asigna modelo desde la UI existente (`POST /config/matrix`)
3. Fallback: si no hay modelo configurado → `agent-helper` (ya implementado)
4. Si no hay ningún fallback → QA funciona sin opinión (solo parte determinística)

```sql
INSERT INTO utm_agent_catalog (agent_id, name, display_name, description, phases, is_active)
VALUES ('agent-qa', 'Agent QA', 'Quick Assessment',
        'Genera opinión profesional rápida sobre viabilidad de migración',
        ARRAY['assessment'], TRUE)
ON CONFLICT (agent_id) DO NOTHING;
```

### 3.7 Persistencia

Se guarda en `utm_projects.settings` (JSONB existente, sin migración):

```json
{
  "quick_assessment": {
    "score": 75,
    "semaforo": "green",
    "file_breakdown": {
      "migrable": 12,
      "soporte": 5,
      "documentacion": 3,
      "no_reconocido": 1
    },
    "detected_techs": ["SSIS", "SQL Server"],
    "blockers": [],
    "total_files": 21,
    "total_lines": 45200,
    "llm_opinion": "Escenario estándar de migración SSIS/SQL Server...",
    "assessed_at": "2026-02-15T14:30:00Z"
  }
}
```

### 3.8 Cambios en Pipeline de Triage

En `apps/api/routers/triage.py`:

| Paso actual | Acción |
|-------------|--------|
| Step 1: `generate_manifest()` | ✅ Se mantiene |
| Step 2: Agent A `analyze_manifest()` | ✅ Se mantiene |
| Step 3: Agent S `assess_repository()` | ❌ **SE ELIMINA** del pipeline |
| Step 4: Persistir assets + grafo | ✅ Se mantiene |

**Resultado:** Triage pasa de 2 llamadas LLM a 1 (solo Agent A). Reduce tiempo ~50%.

---

## 4. Fase B — Knowledge Packet Service

### 4.1 Concepto

Servicio **read-only** que unifica los 6 silos en un solo `KnowledgePacket` por asset. No crea tablas, no migra datos — solo lee y consolida.

### 4.2 Servicio: `KnowledgePacketService`

**Archivo:** `apps/api/services/knowledge_packet_service.py` (NUEVO)

```python
class KnowledgePacket(BaseModel):
    """Todo lo que Agent C necesita saber sobre un asset para generar código."""
    
    # Identity
    object_id: str
    source_name: str
    source_tech: str
    
    # Columnas (tipo resuelto por prioridad: DDL > profiled > metadata > STRING)
    columns: List[ColumnKnowledge]
    
    # Lógica fuente (Sprint 8.5)
    source_query: Optional[str]            # SQL fuente extraído de SqlCommand
    transformations: Optional[List[dict]]   # Cadena de transformaciones SSIS
    source_connections: Optional[List[dict]] # Conexiones OLEDB/ODBC
    complexity_score: Optional[int]         # 0-100
    
    # Column Mappings (utm_column_mappings)
    column_mappings: Optional[List[ColumnMapping]]
    
    # Contexto de negocio (utm_solution_context)
    business_context: Optional[str]
    
    # PII/Privacy
    pii_columns: List[str]
    masking_rules: Optional[Dict[str, str]] # columna → regla
    
    # Table Impact (de Fase C)
    table_impacts: Optional[List[dict]]     # Tablas que este asset toca

class ColumnKnowledge(BaseModel):
    name: str
    source_type: str       # Tipo real (DDL/profiling, no "STRING")
    target_type: str       # Mapeado al target
    is_pk: bool
    is_fk: bool
    is_nullable: bool
    is_pii: bool
    pii_category: Optional[str]
    cardinality_ratio: Optional[float]
    partition_candidate: Optional[bool]
    sample_values: Optional[List[str]]
    resolution_source: str  # "ddl" | "profiled" | "metadata" | "fallback"

class KnowledgePacketService:
    """
    Servicio read-only que consolida 6 silos por asset.
    """
    
    def __init__(self, tenant_id=None, project_id=None):
        self.tenant_id = tenant_id
        self.project_id = project_id
    
    async def get_packet(self, asset_id: str) -> KnowledgePacket:
        # 1. Leer utm_objects (metadata + Sprint 8.5 columns)
        # 2. Leer utm_asset_columns (tipos perfilados, PII)
        # 3. Leer utm_column_mappings (reglas source→target)
        # 4. Leer utm_solution_context (contexto de negocio)
        # 5. Cargar schema_reference.json de R2 (tipos DDL)
        # 6. Resolver tipos por prioridad: DDL > profiled > metadata
        # 7. Leer table impacts (de Fase C, si existe)
        # 8. Ensamblar KnowledgePacket
        pass
```

### 4.3 Prioridad de Resolución de Tipos

```
1. DDL (schema_reference.json)    → "VARCHAR(50)"    ← MÁS PRECISO
2. Profiled (utm_asset_columns)   → "varchar"
3. Metadata (utm_objects)         → "STRING"         ← MENOS PRECISO (fallback SSIS)
```

### 4.4 Cruce SSIS ↔ DDL

El eslabón clave. Dos mundos de datos que nunca se cruzan:

**Mundo 1 (SSIS parser):** Extrae `SqlCommand: "SELECT * FROM dbo.DimCustomers"` + columns con tipo "STRING"

**Mundo 2 (Librarian):** Parsea DDL → `DimCustomers: {CustomerID INT, Name VARCHAR(50)}`

**Cruce:** `_resolve_columns_from_ddl()` extrae tablas del SqlCommand, busca en schema_reference.json, reemplaza "STRING" con tipos reales.

```python
async def _resolve_columns_from_ddl(self, asset_metadata, schema_ref):
    """
    1. Extraer tablas de SqlCommand/OpenRowset/TableOrViewName
    2. Buscar en schema_reference.json
    3. Match → usar tipos DDL
    4. No match → fallback profiling → fallback "STRING"
    """
    medulla = asset_metadata.get("logical_medulla", {})
    
    referenced_tables = set()
    for comp in medulla.get("data_flow_logic", []):
        props = comp.get("raw_properties", {})
        for key in ["SqlCommand", "OpenRowset", "TableOrViewName"]:
            if key in props and props[key]:
                tables = self._extract_table_names(props[key])
                referenced_tables.update(tables)
    
    ddl_columns = {}
    for table_name in referenced_tables:
        clean = table_name.split(".")[-1].strip("[]\"")
        if clean in schema_ref.get("tables", {}):
            for col in schema_ref["tables"][clean]["columns"]:
                ddl_columns[col["name"].lower()] = col
    
    return ddl_columns
```

### 4.5 Conexión con Agent C

**Antes (actual):**
```
SCHEMA METADATA:
  columns: [{"name": "CustomerKey", "type": "STRING"}, ...]
```

**Después (con KnowledgePacket):**
```
SCHEMA METADATA:
  columns: [
    {"name": "CustomerKey", "type": "INT", "is_pk": true},
    {"name": "SSN", "type": "VARCHAR(11)", "is_pii": true, "masking": "sha256"}
  ]

SOURCE INTELLIGENCE:
  source_query: "SELECT c.CustomerKey, c.SSN FROM dbo.DimCustomers c"
  transformations: [
    {"type": "DERIVED_COLUMN", "expression": "GETDATE()"},
    {"type": "LOOKUP", "target": "dbo.DimRegion"}
  ]

BUSINESS CONTEXT:
  "Tabla de dimensión clientes. SCD Tipo 2."
```

---

## 5. Fase C — Table Impact Registry

### 5.1 El Problema

```
Vista PACKAGE-CENTRIC (lo que tenemos):

📦 DimCustomer.dtsx   → Lee staging.customers → Escribe dw.DimCustomer (INSERT)
📦 UpdateCustomer.dtsx → Lee dw.DimCustomer    → Escribe dw.DimCustomer (UPDATE)
📦 FactSales.dtsx      → Lee dw.DimCustomer    → Lee dw.DimProduct → Escribe dw.FactSales

Pregunta: "¿Quién le pega a dw.DimCustomer y de qué forma?"
Respuesta actual: ❌ NO HAY — abrí los 3 manualmente
```

### 5.2 La Solución: Vista TABLE-CENTRIC invertida

```
🗄️ Tabla: dw.DimCustomer
   Total impactos: 3

   📦 DimCustomer.dtsx    → INSERT (FULL_LOAD, diario)
   📦 UpdateCustomer.dtsx  → UPDATE (INCREMENTAL, horario)
   📦 FactSales.dtsx       → SELECT (JOIN, depende de DimCustomer terminado)

   ⚠️ Nota: INSERT y UPDATE sobre misma tabla — verificar si tocan mismos campos
```

> **Importante:** No necesariamente es un conflicto. Uno puede updatar campo A y otro 
> campo B. Pero hay que **verlo** para que el Data Engineer entienda el flujo completo.

### 5.3 Nueva Tabla: `utm_table_impacts`

```sql
CREATE TABLE utm_table_impacts (
    impact_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES utm_tenants(tenant_id),
    project_id      UUID NOT NULL REFERENCES utm_projects(project_id),
    
    -- La tabla afectada
    schema_name     TEXT,                    -- dbo, dw, staging
    table_name      TEXT NOT NULL,           -- DimCustomer, FactSales
    full_name       TEXT GENERATED ALWAYS AS (
                        COALESCE(schema_name || '.', '') || table_name
                    ) STORED,
    
    -- El asset que la toca
    asset_id        UUID REFERENCES utm_objects(object_id),
    asset_name      TEXT NOT NULL,           -- DimCustomer.dtsx
    
    -- Tipo de operación
    operation       TEXT NOT NULL,           -- SELECT, INSERT, UPDATE, DELETE, MERGE, TRUNCATE
    access_pattern  TEXT,                    -- FULL_LOAD, INCREMENTAL, LOOKUP, UPSERT, SCD
    
    -- Dirección
    is_source       BOOLEAN DEFAULT FALSE,
    is_target       BOOLEAN DEFAULT FALSE,
    
    -- Detalle
    sql_statement   TEXT,                    -- La query SQL real si existe
    columns_affected TEXT[],                 -- Columnas que toca (si se puede inferir)
    
    -- Metadata
    detected_at     TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE (project_id, asset_id, full_name, operation)
);

-- Índices para queries rápidas
CREATE INDEX idx_impacts_by_table ON utm_table_impacts(project_id, full_name);
CREATE INDEX idx_impacts_by_asset ON utm_table_impacts(project_id, asset_id);
CREATE INDEX idx_impacts_tenant ON utm_table_impacts(tenant_id);

-- RLS
ALTER TABLE utm_table_impacts ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON utm_table_impacts
    USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

### 5.4 Servicio: `TableImpactService`

**Archivo:** `apps/api/services/table_impact_service.py` (NUEVO)

```python
class TableImpactService:
    """
    Analiza impacto de assets sobre tablas.
    Construye la vista TABLE-CENTRIC invertida.
    """
    
    def __init__(self, project_id: str, tenant_id: str = None):
        self.project_id = project_id
        self.tenant_id = tenant_id
        self.db = SupabasePersistence(tenant_id=tenant_id)
    
    async def analyze_impacts(self) -> Dict[str, Any]:
        """
        Post-triage: Por cada asset en utm_objects:
        1. Leer metadata.logical_medulla
        2. Extraer tablas de SqlCommand, OpenRowset, TableOrViewName
        3. Determinar operation (SELECT, INSERT, UPDATE...)
        4. Inferir columns_affected si es posible
        5. Registrar en utm_table_impacts
        """
        pass
    
    async def get_table_summary(self) -> List[Dict]:
        """
        Retorna resumen de TODAS las tablas del proyecto.
        [
          {"table": "dbo.Customers", "readers": 2, "writers": 1, "operations": ["SELECT", "INSERT"]},
          {"table": "dw.DimCustomer", "readers": 1, "writers": 2, "operations": ["INSERT", "UPDATE", "SELECT"]},
          ...
        ]
        """
        pass
    
    async def get_table_detail(self, table_name: str) -> Dict[str, Any]:
        """
        Retorna todos los impactos sobre una tabla específica.
        {
          "table": "dw.DimCustomer",
          "total_impacts": 3,
          "readers": [
            {"asset": "FactSales.dtsx", "operation": "SELECT", "sql": "SELECT ..."}
          ],
          "writers": [
            {"asset": "DimCustomer.dtsx", "operation": "INSERT", "pattern": "FULL_LOAD"},
            {"asset": "UpdateCustomer.dtsx", "operation": "UPDATE", "pattern": "INCREMENTAL"}
          ],
          "notes": "INSERT y UPDATE en misma tabla — verificar si tocan mismos campos"
        }
        """
        pass
    
    def _extract_tables_from_component(self, comp: Dict) -> List[Dict]:
        """
        Extrae tablas y operación de un componente SSIS.
        Usa raw_properties: SqlCommand, OpenRowset, TableOrViewName.
        Parse SQL con sqlglot para determinar operation.
        """
        pass
    
    def _infer_columns_affected(self, sql: str, operation: str) -> List[str]:
        """
        Intenta inferir qué columnas toca una operación.
        - UPDATE dbo.X SET col1 = ..., col2 = ... → ["col1", "col2"]
        - INSERT INTO dbo.X (col1, col2) → ["col1", "col2"]
        - SELECT * → ["*"] (todas)
        
        Esto permite saber si dos UPDATEs tocan columnas distintas
        (no es conflicto) o las mismas (potencial conflicto).
        """
        pass
    
    async def build_dependency_dag(self) -> Dict[str, Any]:
        """
        Construye DAG de dependencias inter-asset basado en table impacts.
        
        Si Package A escribe a tabla X, y Package B lee de tabla X,
        entonces B depende de A → A debe ejecutarse primero.
        
        Retorna:
        {
          "nodes": ["DimCustomer.dtsx", "UpdateCustomer.dtsx", "FactSales.dtsx"],
          "edges": [
            {"from": "DimCustomer.dtsx", "to": "FactSales.dtsx", "via": "dw.DimCustomer"},
            {"from": "DimProduct.dtsx", "to": "FactSales.dtsx", "via": "dw.DimProduct"}
          ],
          "execution_order": [
            ["DimCustomer.dtsx", "DimProduct.dtsx"],   ← pueden ir en paralelo
            ["FactSales.dtsx"]                          ← depende de los anteriores
          ],
          "cycles": []  ← si hay dependencias circulares
        }
        """
        pass
```

### 5.5 Cómo se detectan operaciones

```python
def _classify_operation(self, comp: Dict) -> str:
    """
    intent del parser SSIS:
      "SOURCE"      → SELECT
      "DESTINATION"  → INSERT (default) o puede ser MERGE/UPDATE
    
    Si hay SqlCommand, parsear con sqlglot:
      "SELECT ..."   → SELECT
      "INSERT ..."   → INSERT
      "UPDATE ..."   → UPDATE
      "DELETE ..."   → DELETE
      "MERGE ..."    → MERGE
      "TRUNCATE ..." → TRUNCATE
    """
    # ...
```

### 5.6 Cómo se usa `columns_affected`

```
Ejemplo real de dos paquetes que escriben a dbo.DimCustomer:

📦 DimCustomer.dtsx:
   UPDATE dbo.DimCustomer SET CustomerName = @p1, Email = @p2 WHERE CustomerKey = @pk
   → columns_affected: ["CustomerName", "Email"]

📦 UpdateCustomer.dtsx:
   UPDATE dbo.DimCustomer SET Phone = @p1, Address = @p2 WHERE CustomerKey = @pk
   → columns_affected: ["Phone", "Address"]

Resultado: NO es conflicto real — tocan columnas distintas.
Pero el usuario lo VE y puede decidir.
```

---

## 6. Fase D — Triage Pipeline v2 (Enrichment)

### 6.1 Concepto

Mejorar el pipeline de Triage para que use los 3 servicios nuevos. NO cambia la UI — solo mejora la calidad de los datos persistidos.

### 6.2 Pipeline Actual vs Nuevo

**Actual:**
```
1. generate_manifest()          ← determinístico ✅
2. Agent A analyze_manifest()   ← LLM ✅
3. Agent S assess_repository()  ← LLM ❌ (se elimina)
4. Persistir assets             ← DB ✅
```

**Nuevo:**
```
1. generate_manifest()                       ← determinístico ✅ (ya existe)
2. Librarian.scan_project()                  ← determinístico ✅ (ya existe, ahora se corre aquí)
3. TableImpactService.analyze_impacts()      ← determinístico 🆕 (Fase C)
4. Agent A analyze_manifest(enriched)        ← LLM ✅ (recibe manifest enriquecido)
5. Persistir assets + table_impacts          ← DB ✅
6. KnowledgePackets disponibles              ← read-only 🆕 (Fase B, listo para Drafting)
```

### 6.3 Manifest Enriquecido para Agent A

**Antes:**
```python
manifest = DiscoveryService.generate_manifest(project_id)
# → file_inventory con columns = "STRING", sin dependencies
```

**Después:**
```python
manifest = DiscoveryService.generate_manifest(project_id)

# Enriquecer con schema_reference (Librarian)
schema_ref = await librarian.scan_project()

# Enriquecer con table impacts
impacts = await table_impact_service.analyze_impacts()

# Inyectar en manifest
manifest["schema_reference"] = schema_ref
manifest["table_impacts"] = impacts["summary"]
manifest["dependency_dag"] = impacts["dag"]

# Inyectar business context
solution_ctx = await db.get_solution_context(project_id)
if solution_ctx:
    manifest["business_context"] = solution_ctx

# Ahora Agent A tiene TODO el contexto
mesh = await agent_a.analyze_manifest(manifest)
```

### 6.4 Beneficio Cascada

```
Manifest enriquecido → Agent A clasifica mejor
                      → Assets con metadata completa en DB
                      → KnowledgePacket lee todo consolidado
                      → Agent C genera código con tipos reales + lógica fuente
                      → Data Engineer ve impacto por tabla
```

---

## 7. Fase E — Visual (UI) — AL FINAL

> **DECISIÓN:** No se toca el frontend hasta que las Fases A-D estén completas y testeadas.
> Primero todo el backend. El visual se adapta al final una sola vez.

### 7.1 Cambios Planificados (para después)

| Componente | Impacto | Fase que requiere |
|------------|---------|-------------------|
| **DiscoveryView** | 🔴 Reescritura parcial | Fase A (QA) |
| **TriageView** | 🟡 Agregar tab "Tables" | Fase C (Table Impact) |
| **StageHeader** | 🟡 Cambiar textos | Fase A |
| **WorkflowToolbar** | 🟡 Renombrar stages | Fase E (futuro) |
| **DraftingView** | ⚪ Sin cambio visual | Fase B mejora código generado invisiblemente |

### 7.2 DiscoveryView — Layout Propuesto

```
┌──────────────────────────────────────────────────────────┐
│  COLUMNA IZQ (7)              │  COLUMNA DER (5)         │
│                                │                          │
│  🚦 SEMÁFORO + Score           │  📊 Desglose Archivos   │
│  ┌──────────────────────┐     │  🟢 Migrables     12    │
│  │     ██ 🟢 75 ██      │     │  🔵 Soporte        5    │
│  │     VIABLE            │     │  ⚪ Documentación   3    │
│  └──────────────────────┘     │  🔴 No reconocido  1    │
│                                │                          │
│  🔍 Tecnologías Detectadas    │  📄 Tribal Knowledge    │
│  ┌──────┐ ┌──────┐            │  [Drag & drop upload]    │
│  │ SSIS │ │ SQL  │            │                          │
│  └──────┘ └──────┘            │  📋 Detalle por Archivo │
│                                │  LoadCustomers.dtsx      │
│  ⚠️ Bloqueadores (si 🔴)     │   → MIGRABLE | SSIS     │
│                                │  schema.ddl              │
│  💬 Opinión LLM               │   → SOPORTE | DDL        │
│  "Escenario estándar..."      │                          │
└──────────────────────────────────────────────────────────┘
```

### 7.3 TriageView — Tab "Tables" (nuevo)

```
┌──────────────────────────────────────────────────────────┐
│  [Assets]  [Tables]                                      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  dbo.DimCustomer    │ 📦 DimCustomer.dtsx → INSERT      │
│    2R / 1W          │ 📦 UpdateCustomer.dtsx → UPDATE   │
│                     │ 📦 FactSales.dtsx → SELECT        │
│  dbo.DimProduct     │                                   │
│    1R / 1W          │ columns_affected:                  │
│                     │   INSERT: [CustomerKey, Name, ...]│
│  dbo.FactSales      │   UPDATE: [Phone, Address]        │
│    0R / 1W          │                                   │
│                     │ → No conflicto (columnas distintas)│
└──────────────────────────────────────────────────────────┘
```

---

## 7.5. Complete Code Implementations (100% Ejecutable)

> **Sección:** Código completo y ejecutable para los métodos críticos de las Fases A, B, C y D.

### 7.5.1 Fase B - Knowledge Packet: `_extract_table_names()`

Implementación completa del extractor de nombres de tablas desde SqlCommand:

```python
def _extract_table_names(self, sql_command: str) -> List[str]:
    """
    Extrae nombres de tablas de SqlCommand usando regex y parsing básico.
    Soporta patrones SQL comunes con/sin schemas, con/sin corchetes.
    """
    import re
    
    if not sql_command:
        return []
    
    tables = set()
    
    # Patrones SQL comunes (capturan schema opcional + tabla)
    patterns = [
        # FROM table, FROM schema.table, FROM [dbo].[table]
        r'\bFROM\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
        # JOIN variants (INNER, LEFT, RIGHT, OUTER)
        r'\b(?:INNER\s+|LEFT\s+|RIGHT\s+|OUTER\s+)?JOIN\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
        # INTO table
        r'\bINTO\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
        # UPDATE table
        r'\bUPDATE\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
        # DELETE FROM table
        r'\bDELETE\s+FROM\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
        # INSERT INTO table
        r'\bINSERT\s+INTO\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, sql_command, re.IGNORECASE)
        for match in matches:
            groups = match.groups()
            if len(groups) >= 2:
                schema = groups[0] if groups[0] else None
                table = groups[1] if groups[1] else groups[0]
                
                if table:
                    # Formato: schema.table o solo table
                    full_name = f"{schema}.{table}" if schema else table
                    tables.add(full_name)
    
    # Limpiar nombres (remover corchetes residuales y palabras reservadas)
    cleaned = []
    reserved_words = {'select', 'from', 'where', 'values', 'set', 'inner', 'left', 'right', 'outer', 'join'}
    
    for t in tables:
        cleaned_name = t.replace('[', '').replace(']', '').strip()
        if cleaned_name and cleaned_name.lower() not in reserved_words:
            cleaned.append(cleaned_name)
    
    return sorted(list(set(cleaned)))
```

### 7.5.2 Fase C - Table Impact: `_classify_operation()` y helpers

Implementación completa del clasificador de operaciones SQL usando sqlglot:

```python
def _classify_operation(self, comp: Dict) -> str:
    """
    Clasifica la operación SQL basándose en:
    1. Intent del componente SSIS (SOURCE → SELECT, DESTINATION → INSERT default)
    2. Parsing sqlglot del SqlCommand si está disponible
    
    Returns: "SELECT" | "INSERT" | "UPDATE" | "DELETE" | "MERGE" | "TRUNCATE" | "UNKNOWN"
    """
    intent = comp.get("intent", "").upper()
    props = comp.get("raw_properties", {})
    
    # Si hay SqlCommand, parsearlo es más preciso
    sql_command = props.get("SqlCommand") or props.get("SqlCommandVariable")
    
    if sql_command:
        operation = self._parse_sql_operation(sql_command)
        if operation != "UNKNOWN":
            return operation
    
    # Fallback a inferencia por intent
    if intent == "SOURCE":
        return "SELECT"
    elif intent == "DESTINATION":
        # Puede ser INSERT, UPDATE, o MERGE — default INSERT
        # Si hay AccessMode en properties, chequearlo
        access_mode = props.get("AccessMode", "0")  # 0=Table/View, 3=SQL, 4=Variable
        if access_mode == "3":  # SQL command mode
            return "INSERT"  # default assumption
        return "INSERT"
    
    return "UNKNOWN"

def _parse_sql_operation(self, sql: str) -> str:
    """
    Usa sqlglot para determinar el tipo de operación SQL.
    Más robusto que regex porque maneja multi-statement y CTEs.
    """
    try:
        import sqlglot
        
        # Parse SQL (dialect agnostic, pero podemos especificar tsql si es necesario)
        parsed = sqlglot.parse_one(sql, dialect="tsql")
        
        if not parsed:
            return "UNKNOWN"
        
        # Determinar tipo de statement
        stmt_type = type(parsed).__name__
        
        if "Select" in stmt_type:
            return "SELECT"
        elif "Insert" in stmt_type:
            return "INSERT"
        elif "Update" in stmt_type:
            return "UPDATE"
        elif "Delete" in stmt_type:
            return "DELETE"
        elif "Merge" in stmt_type:
            return "MERGE"
        elif "Truncate" in stmt_type or "TRUNCATE" in sql.upper():
            return "TRUNCATE"
        
        return "UNKNOWN"
    
    except Exception as e:
        logger.warning(f"[TableImpact] sqlglot parse error: {e}", "TableImpact")
        
        # Fallback a regex simple si sqlglot falla
        sql_upper = sql.strip().upper()
        if sql_upper.startswith("SELECT"):
            return "SELECT"
        elif sql_upper.startswith("INSERT"):
            return "INSERT"
        elif sql_upper.startswith("UPDATE"):
            return "UPDATE"
        elif sql_upper.startswith("DELETE"):
            return "DELETE"
        elif sql_upper.startswith("MERGE"):
            return "MERGE"
        elif sql_upper.startswith("TRUNCATE"):
            return "TRUNCATE"
        
        return "UNKNOWN"

def _infer_columns_affected(self, sql: str, operation: str) -> List[str]:
    """
    Intenta inferir qué columnas toca una operación SQL.
    
    - UPDATE dbo.X SET col1 = ..., col2 = ... → ["col1", "col2"]
    - INSERT INTO dbo.X (col1, col2) VALUES (...) → ["col1", "col2"]
    - SELECT col1, col2 FROM dbo.X → ["col1", "col2"]
    - SELECT * FROM dbo.X → ["*"]
    
    Usa sqlglot para parsing preciso.
    """
    if not sql:
        return []
    
    try:
        import sqlglot
        from sqlglot import expressions as exp
        
        parsed = sqlglot.parse_one(sql, dialect="tsql")
        columns = []
        
        if operation == "UPDATE":
            # Buscar SET clauses
            for node in parsed.find_all(exp.Update):
                for set_item in node.find_all(exp.EQ):
                    # set_item.left es la columna
                    if isinstance(set_item.left, exp.Column):
                        columns.append(set_item.left.name)
        
        elif operation == "INSERT":
            # Buscar columnas en INSERT INTO table (col1, col2)
            for node in parsed.find_all(exp.Insert):
                if node.this:  # node.this es la tabla
                    # Columns explícitas
                    if hasattr(node, 'columns') and node.columns:
                        columns.extend([col.name for col in node.columns])
                    else:
                        # Si no hay columnas explícitas, asumimos todas
                        columns = ["*"]
        
        elif operation == "SELECT":
            # Buscar columnas en SELECT
            for node in parsed.find_all(exp.Select):
                for col in node.expressions:
                    if isinstance(col, exp.Star):
                        return ["*"]
                    elif isinstance(col, exp.Column):
                        columns.append(col.name)
                    elif isinstance(col, exp.Alias):
                        # Alias (col AS alias) → usar nombre original
                        if isinstance(col.this, exp.Column):
                            columns.append(col.this.name)
        
        elif operation == "DELETE":
            # DELETE no afecta columnas específicas, toda la fila
            return ["*"]
        
        elif operation == "MERGE":
            # MERGE puede UPDATE y INSERT — inferir ambos
            update_cols = []
            insert_cols = []
            
            for node in parsed.find_all(exp.Merge):
                # WHEN MATCHED THEN UPDATE SET ...
                for update in node.find_all(exp.Update):
                    for set_item in update.find_all(exp.EQ):
                        if isinstance(set_item.left, exp.Column):
                            update_cols.append(set_item.left.name)
                
                # WHEN NOT MATCHED THEN INSERT ...
                for insert in node.find_all(exp.Insert):
                    if hasattr(insert, 'columns') and insert.columns:
                        insert_cols.extend([col.name for col in insert.columns])
            
            columns = list(set(update_cols + insert_cols))
        
        return sorted(list(set(columns))) if columns else []
    
    except Exception as e:
        logger.warning(f"[TableImpact] Column inference error: {e}", "TableImpact")
        return []

async def build_dependency_dag(self) -> Dict[str, Any]:
    """
    Construye DAG de dependencias inter-asset basado en table impacts.
    
    Lógica:
    - Si Asset A ESCRIBE a tabla X (INSERT/UPDATE/MERGE)
    - Y Asset B LEE de tabla X (SELECT)
    - Entonces: B depende de A (edge: A → B)
    
    Retorna:
    {
      "nodes": ["Asset1.dtsx", "Asset2.dtsx", ...],
      "edges": [
        {"from": "Asset1.dtsx", "to": "Asset3.dtsx", "via": "dbo.TableX"},
        ...
      ],
      "execution_order": [
        ["Asset1.dtsx", "Asset2.dtsx"],  ← Nivel 0 (sin dependencias entrantes)
        ["Asset3.dtsx"],                  ← Nivel 1 (depende de nivel 0)
        ...
      ],
      "cycles": []  ← Lista de ciclos detectados (dependencias circulares)
    }
    """
    from collections import defaultdict, deque
    
    # Leer todos los impactos del proyecto
    query = (
        self.db.client.table("utm_table_impacts")
        .select("asset_name, full_name, operation, is_source, is_target")
        .eq("project_id", self.project_id)
    )
    
    if self.tenant_id:
        query = query.eq("tenant_id", self.tenant_id)
    
    impacts = query.execute().data
    
    # Mapear: tabla → assets que escriben / leen
    table_writers = defaultdict(set)  # tabla → {asset1, asset2, ...}
    table_readers = defaultdict(set)  # tabla → {asset3, asset4, ...}
    all_assets = set()
    
    for impact in impacts:
        asset = impact["asset_name"]
        table = impact["full_name"]
        operation = impact["operation"]
        
        all_assets.add(asset)
        
        if operation in ["INSERT", "UPDATE", "MERGE", "DELETE", "TRUNCATE"]:
            table_writers[table].add(asset)
        elif operation == "SELECT":
            table_readers[table].add(asset)
    
    # Construir edges: writer → reader (por cada tabla compartida)
    edges = []
    dependencies = defaultdict(set)  # asset → {assets de los que depende}
    
    for table, writers in table_writers.items():
        readers = table_readers.get(table, set())
        for writer in writers:
            for reader in readers:
                if writer != reader:  # Evitar auto-dependencia
                    edges.append({
                        "from": writer,
                        "to": reader,
                        "via": table
                    })
                    dependencies[reader].add(writer)
    
    # Detectar ciclos usando DFS
    cycles = self._detect_cycles(all_assets, dependencies)
    
    # Calcular orden de ejecución (topological sort)
    execution_order = self._topological_sort(all_assets, dependencies) if not cycles else []
    
    return {
        "nodes": sorted(list(all_assets)),
        "edges": edges,
        "execution_order": execution_order,
        "cycles": cycles
    }

def _detect_cycles(self, nodes: set, dependencies: Dict[str, set]) -> List[List[str]]:
    """
    Detecta ciclos en el grafo de dependencias usando DFS.
    Retorna lista de ciclos encontrados (cada ciclo es una lista de assets).
    """
    cycles = []
    visited = set()
    rec_stack = set()
    path = []
    
    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in dependencies.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                # Ciclo detectado
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)
                return True
        
        path.pop()
        rec_stack.remove(node)
        return False
    
    for node in nodes:
        if node not in visited:
            dfs(node)
    
    return cycles

def _topological_sort(self, nodes: set, dependencies: Dict[str, set]) -> List[List[str]]:
    """
    Ordena assets por niveles de ejecución usando Kahn's algorithm.
    Retorna [[nivel0_assets], [nivel1_assets], ...] donde:
    - Nivel 0: sin dependencias entrantes (pueden ejecutarse primero)
    - Nivel 1: dependen solo de nivel 0
    - ...
    """
    from collections import defaultdict, deque
    
    # Calcular in-degree (cuántos assets dependen de cada uno)
    in_degree = {node: 0 for node in nodes}
    reverse_deps = defaultdict(list)  # asset → [assets que dependen de él]
    
    for node, deps in dependencies.items():
        in_degree[node] = len(deps)
        for dep in deps:
            reverse_deps[dep].append(node)
    
    # Inicializar con nodos sin dependencias (in-degree = 0)
    queue = deque([node for node in nodes if in_degree[node] == 0])
    execution_order = []
    
    while queue:
        # Todos los nodos en la queue actual pueden ejecutarse en paralelo
        current_level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            current_level.append(node)
            
            # Reducir in-degree de vecinos
            for neighbor in reverse_deps[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        execution_order.append(sorted(current_level))
    
    return execution_order
```

### 7.5.3 Fase C - Table Impact: `analyze_impacts()` completo

Implementación completa del análisis de impactos:

```python
async def analyze_impacts(self) -> Dict[str, Any]:
    """
    Analiza todos los assets del proyecto y registra impactos en utm_table_impacts.
    
    Por cada asset:
    1. Leer metadata.logical_medulla
    2. Extraer tablas de cada componente (SqlCommand, OpenRowset, TableOrViewName)
    3. Determinar operation (SELECT, INSERT, UPDATE, etc.)
    4. Inferir columns_affected
    5. Registrar en utm_table_impacts
    
    Retorna resumen con stats.
    """
    # Leer todos los assets del proyecto
    query = (
        self.db.client.table("utm_objects")
        .select("object_id, name, metadata")
        .eq("project_id", self.project_id)
    )
    
    if self.tenant_id:
        query = query.eq("tenant_id", self.tenant_id)
    
    assets = query.execute().data
    
    total_impacts = 0
    total_tables = set()
    errors = []
    
    for asset in assets:
        try:
            metadata = asset.get("metadata", {})
            medulla = metadata.get("logical_medulla", {})
            
            if not medulla:
                continue
            
            # Extraer impactos de todos los componentes
            impacts = self._extract_impacts_from_asset(asset, medulla)
            
            # Guardar en DB
            for impact in impacts:
                await self._save_impact(impact)
                total_impacts += 1
                total_tables.add(impact["full_name"])
        
        except Exception as e:
            logger.error(f"[TableImpact] Error analyzing {asset['name']}: {e}", "TableImpact")
            errors.append({"asset": asset["name"], "error": str(e)})
    
    return {
        "status": "completed",
        "total_assets": len(assets),
        "total_impacts": total_impacts,
        "unique_tables": len(total_tables),
        "errors": errors
    }

def _extract_impacts_from_asset(self, asset: Dict, medulla: Dict) -> List[Dict]:
    """
    Extrae todos los impactos de tabla de un asset SSIS.
    Retorna lista de dicts con estructura de utm_table_impacts.
    """
    impacts = []
    
    # Iterar sobre todos los componentes del data flow
    for comp in medulla.get("data_flow_logic", []):
        tables_and_ops = self._extract_tables_from_component(comp)
        
        for table_info in tables_and_ops:
            # Inferir columns_affected
            columns = self._infer_columns_affected(
                table_info.get("sql_statement", ""),
                table_info["operation"]
            )
            
            impact = {
                "tenant_id": self.tenant_id,
                "project_id": self.project_id,
                "schema_name": table_info.get("schema_name"),
                "table_name": table_info["table_name"],
                "full_name": table_info["full_name"],
                "asset_id": asset["object_id"],
                "asset_name": asset["name"],
                "operation": table_info["operation"],
                "access_pattern": table_info.get("access_pattern"),
                "is_source": table_info["operation"] == "SELECT",
                "is_target": table_info["operation"] in ["INSERT", "UPDATE", "MERGE", "DELETE", "TRUNCATE"],
                "sql_statement": table_info.get("sql_statement"),
                "columns_affected": columns
            }
            
            impacts.append(impact)
    
    return impacts

def _extract_tables_from_component(self, comp: Dict) -> List[Dict]:
    """
    Extrae tablas y operación de un componente SSIS.
    
    Usa raw_properties:
    - SqlCommand: query SQL completa
    - OpenRowset: nombre de tabla directo
    - TableOrViewName: nombre de tabla/vista
    
    Retorna: [{"full_name": "dbo.Table", "operation": "SELECT", "sql_statement": "...", ...}, ...]
    """
    props = comp.get("raw_properties", {})
    results = []
    
    # Determinar operación
    operation = self._classify_operation(comp)
    
    # Extraer nombres de tablas según tipo de property
    tables = []
    sql_statement = None
    
    # 1. SqlCommand (más común e informativo)
    if "SqlCommand" in props and props["SqlCommand"]:
        sql_statement = props["SqlCommand"]
        tables = self._extract_table_names_basic(sql_statement)
    
    # 2. SqlCommandVariable (variable que contiene SQL)
    elif "SqlCommandVariable" in props and props["SqlCommandVariable"]:
        # No podemos resolverla en tiempo de análisis estático, pero la guardamos
        sql_statement = f"/* Variable: {props['SqlCommandVariable']} */"
        tables = []  # No podemos extraer tablas de variables
    
    # 3. OpenRowset (tabla directa sin query)
    elif "OpenRowset" in props and props["OpenRowset"]:
        raw_table = props["OpenRowset"]
        tables = [self._clean_table_name(raw_table)]
    
    # 4. TableOrViewName (componentes OLE DB Destination)
    elif "TableOrViewName" in props and props["TableOrViewName"]:
        raw_table = props["TableOrViewName"]
        tables = [self._clean_table_name(raw_table)]
    
    # Crear resultado por cada tabla detectada
    for table in tables:
        # Separar schema y tabla
        parts = table.split('.')
        if len(parts) == 2:
            schema_name, table_name = parts
        else:
            schema_name = None
            table_name = parts[0]
        
        results.append({
            "full_name": table,
            "schema_name": schema_name,
            "table_name": table_name,
            "operation": operation,
            "sql_statement": sql_statement,
            "access_pattern": self._infer_access_pattern(comp, operation)
        })
    
    return results

def _extract_table_names_basic(self, sql: str) -> List[str]:
    """
    Wrapper simple que llama al extractor regex avanzado.
    Ya implementado en section 7.5.1 (para KnowledgePacket).
    """
    return self._extract_table_names(sql)  # Método ya definido arriba

def _clean_table_name(self, raw_name: str) -> str:
    """
    Limpia nombre de tabla:
    - Remueve corchetes: [dbo].[Table] → dbo.Table
    - Remueve comillas: "dbo"."Table" → dbo.Table
    """
    import re
    cleaned = re.sub(r'[\[\]"]', '', raw_name)
    return cleaned.strip()

def _infer_access_pattern(self, comp: Dict, operation: str) -> Optional[str]:
    """
    Intenta inferir el patrón de acceso basándose en properties y operation.
    
    Returns: "FULL_LOAD" | "INCREMENTAL" | "LOOKUP" | "UPSERT" | "SCD" | None
    """
    props = comp.get("raw_properties", {})
    sql = props.get("SqlCommand", "").upper()
    
    # LOOKUP: componentes específicos de SSIS
    if comp.get("type") == "Lookup":
        return "LOOKUP"
    
    # INCREMENTAL: si hay WHERE con filtro de fecha o ID
    if "WHERE" in sql and any(word in sql for word in ["GETDATE", "DATE", "TIMESTAMP", ">"]):
        return "INCREMENTAL"
    
    # UPSERT/SCD: si hay MERGE o UPDATE seguido de INSERT
    if operation == "MERGE":
        return "UPSERT"
    
    # FULL_LOAD: SELECT sin WHERE o con WHERE 1=1
    if operation == "SELECT" and ("WHERE 1=1" in sql or "WHERE" not in sql):
        return "FULL_LOAD"
    
    return None

async def _save_impact(self, impact: Dict) -> None:
    """
    Guarda un impacto en utm_table_impacts.
    Usa UPSERT para evitar duplicados (UNIQUE constraint en tabla).
    """
    try:
        # Remover campos generados (full_name se genera en DB)
        data = {k: v for k, v in impact.items() if k != 'full_name'}
        
        # UPSERT
        self.db.client.table("utm_table_impacts").upsert(data).execute()
    
    except Exception as e:
        logger.error(f"[TableImpact] Error saving impact: {e}", "TableImpact")
        raise
```

### 7.5.4 Fase D - Triage v2: Diff completo para `triage.py`

Cambios exactos en `apps/api/routers/triage.py`:

```python
# UBICACIÓN: Línea ~850 (dentro de /start endpoint, después de generate_manifest)

# ===== CÓDIGO ACTUAL (REMOVER) =====
# Step 2: Agent S (LLM)
agent_s = AgentSService(tenant_id=tenant_id, client_id=client_id)
metrics = await agent_s.assess_repository(project_id)

# ==== CÓDIGO NUEVO (REEMPLAZAR) =====
# Step 2: Quick Assessment (reemplaza Agent S)
from apps.api.services.quick_assessment_service import QuickAssessmentService
qa_service = QuickAssessmentService(tenant_id=tenant_id, client_id=client_id)
quick_assessment = await qa_service.assess(project_id)

# Guardar resultado de QA en utm_projects.quick_assessment (nueva columna JSONB)
await db.update_project(project_id, {"quick_assessment": quick_assessment.dict()})

# Step 3: Librarian scan (determinístico)
from apps.api.services.librarian_service import LibrarianService
librarian = LibrarianService(tenant_id=tenant_id)
schema_reference = await librarian.scan_project()  # → schema_reference.json en R2

# Step 4: Table Impact analysis
from apps.api.services.table_impact_service import TableImpactService
impact_service = TableImpactService(project_id=project_id, tenant_id=tenant_id)
impacts = await impact_service.analyze_impacts()

# Step 5: Enrichir manifest antes de Agent A
manifest["schema_reference"] = schema_reference
manifest["table_impacts"] = {
    "summary": impacts,
    "dag": await impact_service.build_dependency_dag()
}

# Inyectar business context (utm_solution_context)
solution_ctx = await db.get_solution_context(project_id)
if solution_ctx:
    manifest["business_context"] = solution_ctx

# Step 6: Agent A con manifest enriquecido
agent_a = AgentAService(tenant_id=tenant_id, client_id=client_id)
mesh = await agent_a.analyze_manifest(manifest)

# Step 7: Persistir assets (sin cambios)
# ...código existente...
```

Cambio en línea ~900 (persistencia):

```python
# AGREGAR después de persistir assets en utm_objects:

# Persistir quick_assessment y table_impacts también en el estado del proyecto
await db.client.table("utm_projects").update({
    "quick_assessment": quick_assessment.dict(),
    "has_table_impacts": True,
    "last_triage_at": datetime.utcnow().isoformat()
}).eq("project_id", project_id).execute()
```

---

## 8. Migración de Datos (SQL)

### 8.1 Script de migración

**Archivo:** `migrations/v4.0_table_impacts.sql` (NUEVO)

```sql
-- ============================================
-- v4.0: Table Impact Registry + Agent QA
-- ============================================

-- 1. Nueva tabla: utm_table_impacts
CREATE TABLE IF NOT EXISTS utm_table_impacts (
    impact_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    project_id      UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    schema_name     TEXT,
    table_name      TEXT NOT NULL,
    full_name       TEXT GENERATED ALWAYS AS (COALESCE(schema_name || '.', '') || table_name) STORED,
    asset_id        UUID REFERENCES utm_objects(object_id) ON DELETE CASCADE,
    asset_name      TEXT NOT NULL,
    operation       TEXT NOT NULL,
    access_pattern  TEXT,
    is_source       BOOLEAN DEFAULT FALSE,
    is_target       BOOLEAN DEFAULT FALSE,
    sql_statement   TEXT,
    columns_affected TEXT[],
    detected_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (project_id, asset_id, full_name, operation)
);

CREATE INDEX IF NOT EXISTS idx_impacts_by_table ON utm_table_impacts(project_id, full_name);
CREATE INDEX IF NOT EXISTS idx_impacts_by_asset ON utm_table_impacts(project_id, asset_id);
CREATE INDEX IF NOT EXISTS idx_impacts_tenant ON utm_table_impacts(tenant_id);

ALTER TABLE utm_table_impacts ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_impacts ON utm_table_impacts
    USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- 2. Registrar Agent QA en catálogo
INSERT INTO utm_agent_catalog (agent_id, name, display_name, description, phases, is_active)
VALUES ('agent-qa', 'Agent QA', 'Quick Assessment',
        'Genera opinión profesional rápida sobre viabilidad de migración',
        ARRAY['assessment'], TRUE)
ON CONFLICT (agent_id) DO NOTHING;
```

---

## 9. Endpoints API

### 9.1 Endpoints Nuevos

| Fase | Método | Ruta | Propósito |
|------|--------|------|-----------|
| A | `POST` | `/projects/{id}/quick-assessment` | Ejecutar Quick Assessment |
| A | `GET` | `/projects/{id}/quick-assessment` | Obtener resultado cacheado |
| C | `GET` | `/projects/{id}/tables/summary` | Resumen de todas las tablas |
| C | `GET` | `/projects/{id}/tables/{name}/detail` | Impactos sobre una tabla |
| C | `GET` | `/projects/{id}/dependency-dag` | DAG de dependencias inter-asset |
| B | `GET` | `/projects/{id}/assets/{aid}/knowledge` | KnowledgePacket de un asset |

### 9.2 Endpoints Modificados

| Método | Ruta | Cambio |
|--------|------|--------|
| `POST` | `/projects/{id}/run-analysis` | Agregar pasos: Librarian + TableImpact + manifest enriquecido |

### 9.3 Endpoints Sin Cambio

| Método | Ruta | Razón |
|--------|------|-------|
| `POST` | `/system/scout/assess` | Se mantiene para Fase ② Deep Discovery futura |

---

## 10. Plan de Ejecución

### Orden Secuencial (Backend First)

```
Semana 1: Fase A (Quick Assessment — backend completo)
├── A1: Crear QuickAssessmentService + modelos Pydantic
├── A2: Crear endpoints POST/GET en projects.py
├── A3: Eliminar Agent S del pipeline de Triage
├── A4: Ejecutar migración SQL (agent-qa en catálogo)
└── A5: Tests unitarios QA

Semana 2: Fase C (Table Impact — tabla + servicio)
├── C1: Ejecutar migración SQL (utm_table_impacts)
├── C2: Crear TableImpactService con detección de operaciones
├── C3: Implementar _extract_tables + _infer_columns_affected
├── C4: Implementar build_dependency_dag()
├── C5: Crear endpoints GET tables/summary, tables/{name}/detail, dag
└── C6: Tests unitarios Table Impact

Semana 3: Fase B (Knowledge Packet — consolidación)
├── B1: Crear KnowledgePacketService con modelos Pydantic
├── B2: Implementar _resolve_columns_from_ddl() (cruce SSIS↔DDL)
├── B3: Implementar resolución de tipos (DDL > profiled > metadata)
├── B4: Crear endpoint GET assets/{id}/knowledge
├── B5: Wiring: integrar KnowledgePacket en Agent C prompt
└── B6: Tests: comparar prompts antes/después

Semana 4: Fase D (Triage v2 — enrichment pipeline)
├── D1: Integrar Librarian.scan_project() en triage pipeline
├── D2: Integrar TableImpactService.analyze_impacts() en pipeline
├── D3: Enriquecer manifest con schema_ref + impacts + context
├── D4: Tests end-to-end del pipeline completo
└── D5: Validar que Agent C genera mejor código

Semana 5: Fase E (Visual — UI)
├── E1: Reescribir DiscoveryView (QA cards, eliminar Agent S UI)
├── E2: Agregar tab "Tables" en TriageView
├── E3: Ajustar StageHeader textos
├── E4: Tests end-to-end UI + backend
└── E5: Cleanup + documentación final
```

### Tabla de Steps con Dependencias

| Step | Fase | Tarea | Esfuerzo | Depende de |
|------|------|-------|----------|------------|
| A1 | A | `QuickAssessmentService` + modelos | 🟢 Med | — |
| A2 | A | Endpoints POST/GET QA | 🟢 Med | A1 |
| A3 | A | Eliminar Agent S de triage pipeline | 🟢 Bajo | — |
| A4 | A | Migración SQL: agent-qa catálogo | 🟢 Bajo | — |
| A5 | A | Tests QA | 🟢 Med | A1, A2 |
| C1 | C | Migración SQL: utm_table_impacts | 🟢 Bajo | — |
| C2 | C | `TableImpactService` base | 🟡 Alto | C1 |
| C3 | C | Extract tables + infer columns | 🟡 Alto | C2 |
| C4 | C | Dependency DAG builder | 🟡 Alto | C3 |
| C5 | C | Endpoints tables/summary, detail, dag | 🟢 Med | C2 |
| C6 | C | Tests Table Impact | 🟢 Med | C2-C5 |
| B1 | B | `KnowledgePacketService` + modelos | 🟡 Alto | — |
| B2 | B | Cruce SSIS↔DDL (_resolve_columns_from_ddl) | 🟡 Alto | B1 |
| B3 | B | Resolución prioridad tipos | 🟡 Alto | B2 |
| B4 | B | Endpoint GET knowledge | 🟢 Med | B1 |
| B5 | B | Wiring Agent C ← KnowledgePacket | 🟡 Alto | B1 |
| B6 | B | Tests Knowledge | 🟢 Med | B5 |
| D1 | D | Librarian en triage pipeline | 🟢 Med | C2 |
| D2 | D | TableImpact en triage pipeline | 🟢 Med | C2 |
| D3 | D | Manifest enriquecido | 🟢 Med | D1, D2 |
| D4 | D | Tests end-to-end pipeline | 🟡 Alto | D3, B5 |
| D5 | D | Validar calidad código Agent C | 🟢 Med | D4 |
| E1 | E | DiscoveryView rewrite | 🟡 Alto | A1-A5 |
| E2 | E | TriageView tab "Tables" | 🟡 Alto | C2-C6 |
| E3 | E | StageHeader ajustes | 🟢 Bajo | E1 |
| E4 | E | Tests UI end-to-end | 🟡 Alto | E1-E3 |
| E5 | E | Cleanup + docs | 🟢 Med | E4 |

---

## 11. Decisiones Tomadas

| # | Decisión | Opción elegida | Razón |
|---|----------|---------------|-------|
| 1 | Schema de datos | Service layer only (sin migraciones) | Menor riesgo, no rompe Sprint 7/8.5 |
| 2 | Trigger del QA | Botón manual "Quick Assess" | Control del usuario |
| 3 | Agent S en Discovery | Mover a Fase ② Deep Discovery | Evita duplicación, Agent S pertenece al análisis profundo |
| 4 | Prioridad fases | A → C → B → D → E (backend first) | Todo el backend primero, visual al final |
| 5 | Re-ejecutar manifest en Triage | Sí | Más simple que cachear, es rápido (2-15 seg) |
| 6 | Endpoint Agent S | No eliminar | Se reutiliza en Fase ② |
| 7 | LLM en QA | Sí, via Agent Matrix existente | 1 INSERT en catálogo. Cliente decide modelo y paga |
| 8 | Cruce SSIS↔DDL | En KnowledgePacket (Fase B) | QA se mantiene simple |
| 9 | Score numérico | Mantener 0-100 + semáforo | Score interno + semáforo visual |
| 10 | Naming Stage 4 | "Re-Architecture" no "Medallion" | Medallion es un patrón, no el único |
| 11 | Table Impact vs conflictos | Mostrar impactos, no asumir conflicto | Puede que no sea conflicto (columnas distintas) — pero hay que verlo |
| 12 | Nueva tabla | Sí, `utm_table_impacts` | No cabe en JSONB — es relacional (N tablas × M assets × K operaciones) |
| 13 | Frontend | AL FINAL, todo junto | No tocar visual hasta que backend esté testeado |
| 14 | columns_affected | Inferir cuando se pueda | Permite distinguir conflicto real vs falso positivo |

---

## 12. Testing

### 12.1 Tests Quick Assessment (Fase A)

| Test | Descripción | Resultado esperado |
|------|-------------|-------------------|
| QA-01 | Upload 10 `.dtsx` + 2 `.sql` + 1 `.md` | Score ≥ 60, 🟢, 10 MIGRABLE, 2 SOPORTE, 1 DOC |
| QA-02 | Upload 3 `.jpg` + 2 `.exe` + 1 `.zip` | Score < 30, 🔴, 6 NO RECONOCIDO |
| QA-03 | Upload 5 `.dtsx` + 5 `.jpg` | Score ~30-59, 🟡 |
| QA-04 | Upload 0 archivos | Error 400 |
| QA-05 | Ejecutar QA, luego GET | GET retorna resultado cacheado |
| QA-06 | Re-ejecutar QA con nuevos archivos | Score recalculado |

### 12.2 Tests Table Impact (Fase C)

| Test | Descripción | Resultado esperado |
|------|-------------|-------------------|
| TI-01 | 3 paquetes SSIS, 2 escriben a misma tabla | Table summary muestra 2 writers |
| TI-02 | 2 UPDATE a misma tabla, columnas distintas | `columns_affected` diferentes, no conflicto |
| TI-03 | INSERT + SELECT en misma tabla | Un writer + un reader correctamente separados |
| TI-04 | MERGE operation | Clasificado como MERGE, columnas inferidas |
| TI-05 | Asset sin SqlCommand | Table impact vacío para ese asset |
| TI-06 | DAG: A→B→C lineal | execution_order = [[A], [B], [C]] |
| TI-07 | DAG: A+B→C paralelo | execution_order = [[A,B], [C]] |
| TI-08 | DAG: ciclo A↔B | cycles detectados |

### 12.3 Tests Knowledge Packet (Fase B)

| Test | Descripción | Resultado esperado |
|------|-------------|-------------------|
| KP-01 | Asset SSIS con DDL + profiling | Tipos del DDL, source_query, transformaciones |
| KP-02 | Asset sin DDL (solo SSIS) | Fallback a profiling → "STRING" |
| KP-03 | Prompt Agent C con KnowledgePacket | Incluye source_query, tipos reales, PII |
| KP-04 | Código generado before/after | Post-KP usa tipos correctos y lógica |

### 12.4 Tests Cruce SSIS ↔ DDL

| Test | Descripción | Resultado esperado |
|------|-------------|-------------------|
| CR-01 | SSIS + DDL con tabla exacta | Tipos resueltos como INT, VARCHAR(50) |
| CR-02 | SSIS referencia tabla sin DDL | Fallback "STRING", log de warning |
| CR-03 | SSIS con LOOKUP + DDL | Columnas del lookup resueltas |
| CR-04 | Conexión OLEDB → KnowledgePacket | Incluye server + database |
| CR-05 | 5 paquetes × 3 tablas DDL | Todos los KnowledgePackets cruzados |
| CR-06 | Solo SSIS sin DDL | Funciona con fallback, sin errors |

### 12.5 Tests Triage v2 (Fase D)

| Test | Descripción | Resultado esperado |
|------|-------------|-------------------|
| TR-01 | Pipeline completo sin Agent S | Completa en ~50% menos tiempo |
| TR-02 | Manifest enriquecido a Agent A | Incluye schema_ref + impacts |
| TR-03 | Assets con metadata enriquecida | utm_objects tiene source_query + tipos |
| TR-04 | Table impacts persistidos | utm_table_impacts tiene registros |
| TR-05 | KnowledgePacket disponible post-triage | GET /assets/{id}/knowledge retorna packet |

---

## 13. Archivos Afectados

### 13.1 Archivos Nuevos

| Archivo | Fase | Propósito |
|---------|------|-----------|
| `apps/api/services/quick_assessment_service.py` | A | Servicio QA |
| `apps/api/services/knowledge_packet_service.py` | B | Consolidación de silos |
| `apps/api/services/table_impact_service.py` | C | Vista table-centric |
| `migrations/v4.0_table_impacts.sql` | C | Tabla + agent-qa en catálogo |
| `tests/test_quick_assessment.py` | A | Tests |
| `tests/test_table_impact.py` | C | Tests |
| `tests/test_knowledge_packet.py` | B | Tests |

### 13.2 Archivos Modificados — Backend

| Archivo | Líneas | Cambio | Fase |
|---------|--------|--------|------|
| `apps/api/routers/projects.py` | ~400 | Agregar endpoints QA + tables + knowledge | A, B, C |
| `apps/api/routers/triage.py` | ~936 | Eliminar Agent S, integrar Librarian + TableImpact | A, D |
| `apps/api/services/agent_c_service.py` | ~1483 | Reemplazar SchemaMetadata con KnowledgePacket | B |

### 13.3 Archivos Modificados — Frontend (Fase E, AL FINAL)

| Archivo | Líneas | Cambio | Fase |
|---------|--------|--------|------|
| `apps/web/app/components/stages/DiscoveryView.tsx` | ~473 | Reescribir: QA cards, eliminar Agent S | E |
| `apps/web/app/components/stages/TriageView.tsx` | ~1531 | Agregar tab "Tables" | E |
| `apps/web/app/components/StageHeader.tsx` | ~50 | Cambiar textos | E |

### 13.4 Archivos NO Afectados

| Archivo | Razón |
|---------|-------|
| `apps/api/services/discovery_service.py` | Se reutiliza `generate_manifest()` tal cual |
| `apps/api/services/librarian_service.py` | Se reutiliza `scan_project()` tal cual |
| `apps/utm/cartridges/ssis/parser.py` | Parser ya extrae toda la info necesaria |
| `apps/api/services/persistence_service.py` | No cambia (ya tiene métodos necesarios) |
| `apps/api/services/agent_a_service.py` | Solo recibe manifest enriquecido, no cambia internamente |
| `apps/web/app/workspace/page.tsx` | Stage routing no cambia |

---

## Anexo: Flujo Completo Antes/Después

### ANTES

```
Upload → Agent S (LLM, 15-30s) → Conflicto → Triage → manifest + Agent A + Agent S → Drafting
                                                                                         │
                                                                Agent C prompt:
                                                                  columns = "STRING"
                                                                  SIN source queries
                                                                  SIN transformaciones
                                                                  SIN tipos reales
                                                                  SIN vista por tabla
```

### DESPUÉS (v4.0 completo)

```
Upload → Quick Assess (3-5s) → Semáforo + Score + Opinión → Triage
                                                               │
                                      manifest enriquecido + Librarian + TableImpact + Agent A
                                                               │
                                                          Drafting
                                                               │
                                                Agent C prompt:
                                                  ✅ KnowledgePacket:
                                                    tipos DDL reales
                                                    source_query
                                                    transformaciones
                                                    PII + masking
                                                    column mappings
                                                    business context
                                                  
                                                  ✅ Vista table-centric:
                                                    quién le pega a cada tabla
                                                    qué operación
                                                    qué columnas
                                                    dependency DAG
```

---

*Plan unificado v4.0 — Legacy2Lake UTM — Backend Intelligence Layer*
