# Plan Fase ① — Quick Assessment + Consolidación de Conocimiento

**Fecha:** 15 de febrero de 2026  
**Estado:** APROBADO CONCEPTUALMENTE — Pendiente implementación  
**Prioridad:** QA primero, luego Knowledge Schema

---

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Diagnóstico del Estado Actual](#2-diagnóstico-del-estado-actual)
3. [Parte A — Quick Assessment (QA)](#3-parte-a--quick-assessment)
4. [Parte B — Consolidación del Esquema de Conocimiento](#4-parte-b--consolidación-del-esquema-de-conocimiento)
5. [Impacto Visual — Cambios en la UI](#5-impacto-visual--cambios-en-la-ui)
6. [Endpoints API — Nuevos y Modificados](#6-endpoints-api--nuevos-y-modificados)
7. [Archivos Afectados](#7-archivos-afectados)
8. [Plan de Ejecución](#8-plan-de-ejecución)
9. [Decisiones Tomadas](#9-decisiones-tomadas)
10. [Verificación / Testing](#10-verificación--testing)

---

## 1. Resumen Ejecutivo

### ¿Qué vamos a hacer?

Dos mejoras interrelacionadas que atacan dos problemas fundamentales:

**Problema 1 — No hay pre-evaluación rápida:**  
Hoy el usuario sube archivos y la primera respuesta que recibe requiere una llamada LLM (Agent S "Forensic Scan"), que tarda 15-30 segundos y cuesta dinero. No hay forma rápida de saber si un proyecto es migrable antes de invertir en análisis profundo.

**Problema 2 — Los datos recolectados no alimentan la generación de código:**  
El sistema recolecta datos ricos (queries fuente, transformaciones SSIS, tipos de datos perfilados, flags PII, mappings de columnas) distribuidos en 6+ silos de datos, pero Agent C **nunca los ve**. Agent C genera código con columnas tipadas como "STRING" y convenciones de nombres — sin conocer qué hace realmente el paquete fuente.

### Solución

| Parte | Qué | Cómo |
|-------|-----|------|
| **A. Quick Assessment** | Evaluación determinística pre-triage (sin LLM, 3-5 seg) | Nuevo servicio + endpoint + tarjeta en UI |
| **B. Knowledge Packet** | Unificar los 6 silos de datos en un solo paquete que alimente a Agent C | Nuevo servicio read-only (sin migraciones DB) |

### Decisiones Clave (ya aprobadas)

| Decisión | Opción elegida | Alternativas descartadas |
|----------|---------------|--------------------------|
| Esquema de datos | **Service layer only** (sin migraciones) | Nueva tabla materializada, reestructurar utm_objects |
| Trigger del QA | **Botón manual** "Quick Assess" | Auto después de upload, ambos |
| Agent S en Discovery | **Mover a Fase ②** Deep Discovery | Mantener como opcional, eliminar |
| Prioridad | **QA primero**, luego Knowledge | Knowledge primero, ambos en paralelo |

---

## 2. Diagnóstico del Estado Actual

### 2.1 Flujo Actual del Usuario (Discovery → Triage)

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: DISCOVERY (DiscoveryView.tsx — 473 líneas)           │
│                                                                 │
│  ┌─────────┐     ┌──────────────────┐     ┌──────────────────┐ │
│  │ Upload  │────▶│ Start Forensic   │────▶│ Resolver         │ │
│  │ archivos│     │ Scan (Agent S)   │     │ conflictos tech  │ │
│  │ (drag)  │     │ 🤖 LLM $$$      │     │                  │ │
│  │         │     │ 15-30 seg        │     │                  │ │
│  └─────────┘     └──────────────────┘     └──────────────────┘ │
│                                                                 │
│  Botón: "Start Triage" → avanza a Stage 2                      │
│  (deshabilitado hasta que scan complete + sin conflictos)       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: TRIAGE (TriageView.tsx — 1531 líneas)                │
│                                                                 │
│  Botón: "Run Analysis" ejecuta pipeline:                        │
│    1. generate_manifest()  ← determinístico, 2-15 seg           │
│    2. Agent A (classify)   ← 🤖 LLM $$$                        │
│    3. Agent S (assess)     ← 🤖 LLM $$$ (duplicado!)           │
│    4. Persistir assets + grafo                                  │
│                                                                 │
│  Botón: "Start Drafting" → avanza a Stage 3                    │
└─────────────────────────────────────────────────────────────────┘
```

### Problemas identificados:

1. **El usuario no recibe feedback hasta que paga por Agent S** (LLM)
2. **`generate_manifest()` ya hace todo lo que QA necesita** pero corre escondido dentro del Triage, no se expone al usuario durante Discovery
3. **Agent S se llama 2 veces** — una en Discovery (forensic scan) y otra dentro del pipeline de Triage
4. **Agent S en Discovery es redundante** — QA cubre detección de tecnología y viabilidad de forma determinística

### 2.2 Los 6 Silos de Datos Desconectados

| # | Silo | Qué guarda | ¿Lo lee Agent C? |
|---|------|------------|-------------------|
| 1 | `utm_objects.metadata` (JSONB) | columns, logical_medulla, connections, size — todo mezclado | ⚠️ Solo columns (tipadas como "STRING") |
| 2 | `utm_asset_columns` (Sprint 7) | 25+ campos: tipos reales, PII, cardinalidad, particionamiento | ❌ **NO** |
| 3 | `schema_reference.json` (archivo en R2) | Tipos DDL precisos parseados por Librarian con sqlglot | ❌ **NO** |
| 4 | Sprint 8.5 cols en `utm_objects` | source_connection, transformations, source_query, complexity_score | ❌ **NO** |
| 5 | `utm_column_mappings` | Reglas source→target por columna (CAST, MASK, HASH) | ❌ **NO** |
| 6 | `utm_solution_context` | Contexto de negocio editable por usuario | ❌ **NO** |

### Lo que Agent C SÍ recibe en su prompt:

```
1. Registry aplanado (paths, naming, target_stack)     ← configuración, NO conocimiento
2. Columnas de utm_objects.metadata                    ← a menudo todo tipado "STRING"
3. Reglas del cartridge (utm_prompts)                  ← constraints técnicos genéricos
4. Template v4.0 (Jinja2)                              ← esqueleto con schema+params
```

### Lo que Agent C DEBERÍA recibir pero NO recibe:

```
✗ Source SQL queries              → extraídas, guardadas, NUNCA inyectadas al prompt
✗ Cadena de transformación        → LOOKUPs, MERGEs, DERIVED_COLUMNs — invisibles para el LLM
✗ Tipos de datos precisos         → del DDL parser o column profiling — desconectados
✗ Flags PII y reglas de masking   → perfilados pero no alimentados
✗ Column mappings source→target   → nunca consultados por Agent C
✗ Contexto de negocio             → nunca leído por Agent C
✗ Relaciones entre tablas         → no existen
```

---

## 3. Parte A — Quick Assessment

### 3.1 Concepto

Quick Assessment es una **evaluación determinística** (sin LLM) que clasifica los archivos subidos y calcula un puntaje de viabilidad de migración en 3-5 segundos.

### 3.2 Clasificación de Archivos (4 categorías)

| Categoría | Color | Extensiones / Reglas |
|-----------|-------|---------------------|
| **MIGRABLE** | 🟢 Verde | `.dtsx`, `.sql` (con DML/procedures), `.py`, `.kjb`, `.ktr`, `.ds`, `.rep`, `.workflow`, `.dsx` |
| **SOPORTE** | 🔵 Azul | `.ddl`, `.sql` (schema-only), `.csv`, `.xlsx`, `.xls`, `.json`, `.xml` (no-package) |
| **DOCUMENTACIÓN** | ⚪ Gris | `.md`, `.txt`, `.docx`, `.pdf`, `.html`, `.rtf` |
| **NO RECONOCIDO** | 🔴 Rojo | Todo lo demás (`.jpg`, `.exe`, `.zip`, `.dll`, etc.) |

### 3.3 Fórmula del Score de Viabilidad

```
score = min(100, (migrable_count × 15 + soporte_count × 5) × 100 / max(total_files × 10, 1))
```

Ajustes:
- Si se detecta tecnología homogénea (todo SSIS, o todo SQL): +10 puntos
- Si hay archivos DDL de soporte: +5 puntos
- Si % no_reconocido > 50%: score × 0.5

### 3.4 Semáforo

| Rango | Semáforo | Significado |
|-------|----------|-------------|
| ≥ 60 | 🟢 **VERDE** | Proyecto viable. Proceder al Triage. |
| 30–59 | 🟡 **AMARILLO** | Viable con riesgos. Revisar archivos no reconocidos. |
| < 30 | 🔴 **ROJO** | No viable o faltan archivos. Bloqueadores listados. |

### 3.5 Nuevo Servicio: `QuickAssessmentService`

**Archivo:** `apps/api/services/quick_assessment_service.py`

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
    
    async def assess(self, project_id: str) -> QuickAssessmentResult:
        """
        Evaluación híbrida:
        - Fase 1: Determinística (generate_manifest + clasificación + score)
        - Fase 2: Opinión LLM (resumen del manifest → opinión profesional rápida)
        
        El modelo LLM se resuelve desde el Agent Matrix (configurable por tenant).
        Nosotros recomendamos un modelo barato/rápido, pero el cliente decide.
        """
        # 1. Reusar DiscoveryService.generate_manifest()
        # 2. Clasificar cada archivo en 4 categorías
        # 3. Calcular score y semáforo
        # 4. Detectar tecnologías presentes
        # 5. Identificar bloqueadores si score < 30
        # 6. Generar resumen compacto del manifest
        # 7. Enviar resumen al LLM (agent-qa vía Agent Matrix) para opinión
        # 8. Incorporar opinión LLM al resultado
        pass
```

### 3.6 Nuevo Endpoint API

```
POST /api/v1/projects/{project_id}/quick-assessment
GET  /api/v1/projects/{project_id}/quick-assessment
```

**POST** ejecuta el QA y persiste resultado en `utm_projects.settings.quick_assessment`.  
**GET** retorna el resultado cacheado (o 404 si no existe).

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
    "llm_opinion": "Escenario estándar de migración SSIS/SQL Server → Databricks. Los DDL de soporte proveen tipos de datos reales. Complejidad estimada media. Recomendación: proceder con triage.",
    "assessed_at": "2026-02-15T14:30:00Z"
  }
}
```

### 3.8 Opinión LLM — Usa el Agent Matrix existente

El QA incluye una llamada LLM para generar una **opinión profesional rápida** sobre la viabilidad.

**No hay nada que tocar en la infraestructura de modelos.** El sistema de Agent Matrix (`utm_agent_matrix` + `utm_provider_vault` + `utm_model_catalog` + `utm_agent_catalog`) ya es 100% data-driven y extensible. El método `resolve_agent_model(agent_id)` acepta cualquier string — solo necesitamos:

1. **Un INSERT en `utm_agent_catalog`** para registrar `agent-qa` (global, una vez)
2. **El cliente asigna modelo** desde la UI existente (`POST /config/matrix`) o se pre-configura

```sql
-- Único cambio: registrar el agente en el catálogo (seed global)
INSERT INTO utm_agent_catalog (agent_id, name, display_name, description, phases, is_active)
VALUES ('agent-qa', 'Agent QA', 'Quick Assessment', 
        'Genera opinión profesional rápida sobre viabilidad de migración',
        ARRAY['assessment'], TRUE)
ON CONFLICT (agent_id) DO NOTHING;
```

| Aspecto | Detalle |
|---------|--------|
| **Agent ID** | `agent-qa` |
| **Resolución de modelo** | `resolve_agent_model("agent-qa")` (ya existe) |
| **Fallback** | Si el tenant no configuró `agent-qa`, cae a `agent-helper` (ya implementado) |
| **Prompt** | Se carga desde `utm_prompts` (prompt_id: `agent_qa_opinion`) |
| **Config UI** | Ya existe: `POST /config/matrix` + pantalla de Admin |

**Input al LLM** (resumen compacto del manifest):
```
Proyecto de migración. Archivos subidos:
- 12 paquetes SSIS (.dtsx)
- 3 scripts SQL
- 2 DDL schemas
- 1 documentación (.md)
Tecnología fuente detectada: SSIS / SQL Server
Target configurado: Databricks (PySpark)
¿Es viable esta migración? ¿Riesgos principales? Responde en 3-4 líneas.
```

**Output esperado** (3-4 líneas):
```
Migración estándar DW. Los SSIS son Data Flow simples con transformaciones
básicas. Los DDL cubren la mayoría de las tablas referenciadas. Riesgo:
verificar si hay lógica de orquestación compleja (ForEach Loop, Execute Task).
Recomendación: proceder con triage.
```

### 3.9 Cambios en el Pipeline de Triage

En `apps/api/routers/triage.py`:

| Paso actual | Acción |
|-------------|--------|
| Step 1: `generate_manifest()` | ✅ Se mantiene (re-ejecuta, es rápido) |
| Step 2: Agent A `analyze_manifest()` | ✅ Se mantiene (clasifica assets en mesh graph) |
| Step 3: Agent S `assess_repository()` | ❌ **SE ELIMINA** del pipeline de Triage |
| Step 4: Persistir assets + grafo | ✅ Se mantiene |

**Resultado:** Triage pasa de **2 llamadas LLM** a **1 llamada LLM** (solo Agent A). Reduce tiempo ~50% y costo ~50%.

---

## 4. Parte B — Consolidación del Esquema de Conocimiento

### 4.1 Concepto

Crear un `KnowledgePacketService` que **unifica los 6 silos** en un solo objeto por asset, sin migrar datos ni cambiar tablas existentes. Es una capa de lectura que hace JOINs entre las tablas existentes.

### 4.2 Nuevo Servicio: `KnowledgePacketService`

**Archivo:** `apps/api/services/knowledge_packet_service.py`

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
    source_query: Optional[str]            # SQL fuente extraído
    transformations: Optional[List[dict]]   # Cadena de transformaciones SSIS
    source_connections: Optional[List[dict]] # Conexiones OLEDB/ODBC
    complexity_score: Optional[int]         # 0-100
    
    # Column Mappings (utm_column_mappings)
    column_mappings: Optional[List[ColumnMapping]]
    
    # Contexto de negocio (utm_solution_context)
    business_context: Optional[str]
    
    # PII/Privacy
    pii_columns: List[str]                  # Columnas marcadas como PII
    masking_rules: Optional[Dict[str, str]] # columna → regla

class ColumnKnowledge(BaseModel):
    name: str
    source_type: str       # Tipo real (de DDL/profiling, no "STRING")
    target_type: str       # Tipo mapeado al target
    is_pk: bool
    is_fk: bool
    is_nullable: bool
    is_pii: bool
    pii_category: Optional[str]
    cardinality_ratio: Optional[float]
    partition_candidate: Optional[bool]
    sample_values: Optional[List[str]]

class KnowledgePacketService:
    """
    Servicio read-only que unifica los 6 silos de datos
    en un KnowledgePacket coherente por asset.
    """
    
    async def get_packet(self, asset_id: str) -> KnowledgePacket:
        # 1. Leer utm_objects (metadata + Sprint 8.5 columns)
        # 2. Leer utm_asset_columns (tipos perfilados, PII)
        # 3. Leer utm_column_mappings (reglas source→target)
        # 4. Leer utm_solution_context (contexto de negocio)
        # 5. Intentar cargar schema_reference.json de R2 (tipos DDL)
        # 6. Resolver tipos por prioridad: DDL > profiled > metadata
        # 7. Ensamblar KnowledgePacket
        pass
```

### 4.3 Prioridad de Resolución de Tipos

Cuando hay múltiples fuentes para el tipo de dato de una columna:

```
1. DDL (Librarian/schema_reference.json)  → "VARCHAR(50)"    ← MÁS PRECISO
2. Profiled (utm_asset_columns)           → "varchar"         
3. Metadata (utm_objects.metadata)        → "STRING"          ← MENOS PRECISO (fallback SSIS)
```

### 4.4 Cruce Inteligente: SSIS Connections ↔ DDL Schema (El Eslabón Clave)

Este es el punto más importante de la consolidación. Hoy tenemos **dos mundos de datos que nunca se cruzan**:

#### Mundo 1: Lo que el parser SSIS extrae del `.dtsx`

El parser SSIS (`apps/utm/cartridges/ssis/parser.py`) ya extrae de cada paquete:

```
connection_managers: [
  {
    "name": "OLE DB Source",
    "connection_string": "Data Source=SERVIDOR01;Initial Catalog=AdventureWorksDW;Provider=SQLOLEDB"
  }
]

data_flow_components: [
  {
    "type": "SOURCE_DB",
    "name": "OLE DB Source",
    "raw_properties": {
      "SqlCommand": "SELECT c.CustomerKey, c.CustomerName, c.SSN FROM dbo.DimCustomers c WHERE c.Active = 1"
    }
  },
  {
    "type": "LOOKUP",
    "name": "Lookup Region",
    "raw_properties": {
      "SqlCommand": "SELECT RegionKey, RegionName FROM dbo.DimRegion"
    }
  },
  {
    "type": "DESTINATION_DB",
    "name": "OLE DB Destination",
    "raw_properties": {
      "OpenRowset": "[staging].[DimCustomers]"
    }
  }
]

columns: [
  {"name": "CustomerKey", "data_type": "STRING"},   ← ¡Todo es STRING!
  {"name": "CustomerName", "data_type": "STRING"},
  {"name": "SSN", "data_type": "STRING"}
]
```

**Problema:** El parser SSIS no conoce los tipos reales. Extrae nombres de columnas de los inputColumn/outputColumn del XML, pero SSIS no guarda el tipo en un formato fácilmente parseable — solo tiene `STRING` como fallback.

#### Mundo 2: Lo que el Librarian extrae de los DDL de soporte

Si el usuario subió un archivo `.sql` con los DDL de la base de datos fuente (ej: `AdventureWorksDW_schema.sql`), el Librarian (`apps/api/services/librarian_service.py`) produce:

```json
// schema_reference.json
{
  "tables": {
    "DimCustomers": {
      "name": "DimCustomers",
      "columns": [
        {"name": "CustomerKey", "source_type": "INT", "target_type": "INT", "is_pk": true},
        {"name": "CustomerName", "source_type": "VARCHAR(50)", "target_type": "STRING", "is_pk": false},
        {"name": "SSN", "source_type": "VARCHAR(11)", "target_type": "STRING", "is_pk": false}
      ]
    },
    "DimRegion": {
      "name": "DimRegion",
      "columns": [
        {"name": "RegionKey", "source_type": "INT", "target_type": "INT", "is_pk": true},
        {"name": "RegionName", "source_type": "NVARCHAR(100)", "target_type": "STRING", "is_pk": false}
      ]
    }
  }
}
```

#### El cruce que DEBE hacer el `KnowledgePacketService`

```
SSIS dice: SqlCommand = "SELECT c.CustomerKey, c.CustomerName FROM dbo.DimCustomers c"
                                                                    ^^^^^^^^^^^^^^^^
                                                                    nombre de tabla

Librarian dice: schema_reference.tables["DimCustomers"].columns = [
  CustomerKey → INT (PK),
  CustomerName → VARCHAR(50),
  SSN → VARCHAR(11)
]

CRUCE → Para este asset, las columnas reales son:
  CustomerKey  → INT (no STRING) ← del DDL
  CustomerName → VARCHAR(50) (no STRING) ← del DDL
  SSN          → VARCHAR(11) (no STRING) ← del DDL
  + es PK: CustomerKey
  + tabla fuente: dbo.DimCustomers
  + servidor: SERVIDOR01
  + base de datos: AdventureWorksDW
```

#### Algoritmo de cruce en `KnowledgePacketService.get_packet()`:

```python
async def _resolve_columns_from_ddl(self, asset_metadata: dict, schema_ref: dict) -> List[ColumnKnowledge]:
    """
    Cruza las columnas del parser SSIS con las del Librarian (DDL).
    
    Pasos:
    1. Extraer nombres de tablas del SqlCommand/OpenRowset/TableOrViewName
       del asset (raw_properties del SSIS parser)
    2. Buscar esas tablas en schema_reference.json
    3. Si hay match → usar tipos del DDL en vez de "STRING"
    4. Si no hay DDL → fallback a tipos de utm_asset_columns (profiling)
    5. Si no hay profiling → fallback a "STRING" del parser SSIS
    """
    
    resolved_columns = []
    medulla = asset_metadata.get("logical_medulla", {})
    ssis_columns = asset_metadata.get("columns", [])
    
    # 1. Extraer tablas referenciadas desde la medulla
    referenced_tables = set()
    for comp in medulla.get("data_flow_logic", []):
        props = comp.get("raw_properties", {})
        for key in ["SqlCommand", "OpenRowset", "TableOrViewName"]:
            if key in props and props[key]:
                # Extraer nombres de tabla del SQL
                tables = self._extract_table_names(props[key])
                referenced_tables.update(tables)
    
    # 2. Buscar en schema_reference.json
    ddl_columns_by_name = {}
    for table_name in referenced_tables:
        # Buscar exacto o sin schema (dbo.DimCustomers → DimCustomers)
        clean_name = table_name.split(".")[-1].strip("[]\"")
        if clean_name in schema_ref.get("tables", {}):
            table_def = schema_ref["tables"][clean_name]
            for col in table_def.get("columns", []):
                ddl_columns_by_name[col["name"].lower()] = col
    
    # 3. Resolver cada columna del SSIS
    for ssis_col in ssis_columns:
        col_name = ssis_col["name"]
        ddl_match = ddl_columns_by_name.get(col_name.lower())
        
        if ddl_match:
            # ✅ Match con DDL → tipos reales
            resolved_columns.append(ColumnKnowledge(
                name=col_name,
                source_type=ddl_match["source_type"],     # "INT", "VARCHAR(50)"
                target_type=ddl_match["target_type"],       # mapeado por Librarian
                is_pk=ddl_match.get("is_pk", False),
                is_nullable=ddl_match.get("nullable", True),
                # ... resto de campos
            ))
        else:
            # ❌ Sin DDL → fallback
            resolved_columns.append(ColumnKnowledge(
                name=col_name,
                source_type=ssis_col.get("data_type", "STRING"),
                target_type="STRING",
                is_pk=False,
                # ... resto de campos
            ))
    
    return resolved_columns

def _extract_table_names(self, sql_or_identifier: str) -> List[str]:
    """
    Extrae nombres de tabla de un SQL query o identificador.
    
    Ejemplos:
      "SELECT * FROM dbo.DimCustomers c" → ["dbo.DimCustomers"]
      "[staging].[DimCustomers]"          → ["staging.DimCustomers"]
      "SELECT a.*, b.Name FROM dbo.Fact f JOIN dbo.Dim d ON ..." → ["dbo.Fact", "dbo.Dim"]
    """
    import re
    # Patrón: FROM/JOIN seguido de nombre de tabla
    # Soporta esquema.tabla, [esquema].[tabla], "esquema"."tabla"
    tables = re.findall(
        r'(?:FROM|JOIN)\s+[\[\"]?(\w+)[\]\"]?\.[\[\"]?(\w+)[\]\"]?',
        sql_or_identifier, re.IGNORECASE
    )
    result = [f"{schema}.{table}" for schema, table in tables]
    
    # También buscar tabla simple sin schema
    if not result:
        simple = re.findall(
            r'(?:FROM|JOIN|INSERT\s+INTO|UPDATE)\s+[\[\"]?(\w+)[\]\"]?',
            sql_or_identifier, re.IGNORECASE
        )
        result = simple
    
    # Si es solo un identificador (OpenRowset), retornarlo directo
    if not result and sql_or_identifier.strip():
        clean = sql_or_identifier.strip().strip("[]\"")
        if "SELECT" not in clean.upper():  # No es un query, es un nombre
            result = [clean]
    
    return result
```

#### Diagrama del cruce:

```
┌──────────────────┐          ┌──────────────────┐
│   SSIS Parser    │          │    Librarian      │
│   (.dtsx)        │          │    (.sql DDL)     │
├──────────────────┤          ├──────────────────┤
│ SqlCommand:      │          │ DimCustomers:     │
│  SELECT * FROM   │ ──CRUCE──│  CustomerKey INT  │
│  dbo.DimCustomers│    ▲     │  CustomerName     │
│                  │    │     │   VARCHAR(50)     │
│ columns:         │    │     │  SSN VARCHAR(11)  │
│  CustomerKey     │    │     │                   │
│   → STRING ❌    │    │     │ DimRegion:        │
│  CustomerName    │    │     │  RegionKey INT    │
│   → STRING ❌    │    │     │  RegionName       │
└──────────────────┘    │     │   NVARCHAR(100)   │
                        │     └──────────────────┘
                        │
                        ▼
              ┌────────────────────┐
              │  KnowledgePacket   │
              ├────────────────────┤
              │ CustomerKey → INT  │
              │  (PK, del DDL) ✅  │
              │ CustomerName →     │
              │  VARCHAR(50) ✅     │
              │ SSN → VARCHAR(11)  │
              │  (PII detected) ✅  │
              │                    │
              │ source_query:      │
              │  SELECT * FROM     │
              │  dbo.DimCustomers  │
              │                    │
              │ server: SERVIDOR01 │
              │ db: AdventureWorks │
              └────────────────────┘
                        │
                        ▼
              ┌────────────────────┐
              │    Agent C (LLM)   │
              │ Ahora genera código│
              │ con tipos REALES   │
              └────────────────────┘
```

#### Caso especial: Sin DDL de soporte

Si el usuario **no subió DDL** (solo subió `.dtsx`), el cruce no aplica y se usa el fallback:

```
Prioridad:
1. DDL (schema_reference.json)          → si hay DDL subido ✅
2. Profiled (utm_asset_columns)         → si se corrió column profiling
3. Metadata (utm_objects.metadata)      → siempre disponible (STRING fallback)
```

El sistema **no se rompe sin DDL**, simplemente genera código con tipos menos precisos. Pero cuando hay DDL, **la calidad del código generado mejora dramáticamente**.

#### Impacto en Quick Assessment (Parte A)

El Quick Assessment también puede beneficiarse de este cruce:
- Si hay archivos `.dtsx` Y archivos `.sql` DDL → el QA puede reportar: *"Se detectaron DDL de soporte que proveen tipos de datos reales para las tablas referenciadas"*
- Esto sube el score de viabilidad porque es un proyecto mejor preparado
- En la tarjeta "Desglose de Archivos", los DDL se clasifican como **SOPORTE** con badge: *"Provee schema para 5 tablas referenciadas"*

---

### 4.5 Conexión con Agent C

En `apps/api/services/agent_c_service.py`, el prompt que se envía al LLM cambia:

**Antes (actual):**
```
SCHEMA METADATA:
  columns: [{"name": "CustomerKey", "type": "STRING"}, ...]
  (sin queries fuente, sin transformaciones, sin PII)
```

**Después (con KnowledgePacket):**
```
SCHEMA METADATA:
  columns: [
    {"name": "CustomerKey", "type": "INT", "is_pk": true, "is_pii": false},
    {"name": "CustomerName", "type": "VARCHAR(50)", "is_pii": false},
    {"name": "SSN", "type": "VARCHAR(11)", "is_pii": true, "masking": "sha256"}
  ]

SOURCE INTELLIGENCE:
  source_query: "SELECT c.CustomerKey, c.CustomerName, c.SSN FROM dbo.DimCustomers c"
  transformations: [
    {"type": "DERIVED_COLUMN", "name": "Add LoadDate", "expression": "GETDATE()"},
    {"type": "LOOKUP", "name": "Lookup Region", "target": "dbo.DimRegion"}
  ]

COLUMN MAPPINGS:
  CustomerKey → customer_key (INT → BIGINT)
  SSN → ssn_hash (VARCHAR → STRING, MASK: sha256)

BUSINESS CONTEXT:
  "Tabla de dimensión clientes. SCD Tipo 2. Clave de negocio: CustomerKey."
```

---

## 5. Impacto Visual — Cambios en la UI

### 5.1 Vista General de Impacto

| Componente | Impacto | Detalle |
|------------|---------|---------|
| **WorkflowToolbar** | 🔴 Cambia | Renombrar labels de stages |
| **DiscoveryView** | 🔴 Cambia significativamente | Eliminar Forensic Scan, agregar botón QA + tarjeta resultados |
| **StageHeader** (Discovery) | 🟡 Ajuste menor | Cambiar textos y condición de aprobación |
| **TriageView** | 🟡 Ajuste menor | Eliminar llamada a Agent S del pipeline |
| **WorkspaceSidebar** | ⚪ Sin cambio | — |
| **DraftingView** | ⚪ Sin cambio (hasta Parte B) | Con KnowledgePacket, el código generado será mejor |
| **RefinementView** | ⚪ Sin cambio | — |
| **GovernanceView** | ⚪ Sin cambio | — |
| **HandoverView** | ⚪ Sin cambio | — |

---

### 5.2 WorkflowToolbar — Renombrar Stages

**Archivo:** `apps/web/app/components/WorkflowToolbar.tsx`

**Estado actual:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Orígenes   │ ──▶ │  Core Logic │ ──▶ │   Salida    │
│             │     │             │     │             │
│ Discovery   │     │  Drafting   │     │   Audit     │
│ Triage      │     │ Refinement  │     │  Handover   │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Propuesta — sin cambio funcional todavía** (los nombres actuales son correctos para la Fase ①).

El cambio de nombres de stages sería para cuando se implemente el concepto completo de 6 fases:

```
Futuro (Fase completa):
┌──────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Análisis   │ ──▶ │    Generación    │ ──▶ │   Entrega   │
│              │     │                  │     │             │
│  Assessment  │     │  Direct          │     │ Governance  │
│  Discovery   │     │  Re-Architecture │     │  Deploy     │
└──────────────┘     └──────────────────┘     └─────────────┘
```

> **Nota:** "Re-Architecture" en vez de "Medallion" porque Medallion (bronze/silver/gold) es solo
> un patrón posible. El stage puede generar Medallion, Star Schema, Data Vault, u otro patrón moderno.
> El nombre refleja la acción (re-arquitecturar) no el patrón específico.

**Para Fase ① solo cambiamos los textos descriptivos, no los labels del toolbar.**

---

### 5.3 DiscoveryView — Cambios Significativos

**Archivo:** `apps/web/app/components/stages/DiscoveryView.tsx` (473 líneas)

#### Layout actual (2 columnas):

```
┌──────────────────────────────────────────────────────────────────────┐
│  StageHeader: "Stage 1: Technical Discovery"                         │
│  Subtítulo: "Agent S: Forensic repository audit..."                  │
│  Botones: [Start Forensic Scan]  ───────────────── [Start Triage]    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────┐   ┌──────────────────────────────┐    │
│  │  COLUMNA IZQUIERDA (7)  │   │  COLUMNA DERECHA (5)         │    │
│  │                          │   │                              │    │
│  │  ┌────────────────────┐  │   │  ┌──────────────────────┐   │    │
│  │  │ Agent S: Forensic  │  │   │  │ Technology           │   │    │
│  │  │ Audit              │  │   │  │ Validation           │   │    │
│  │  │ (Consola terminal) │  │   │  │                      │   │    │
│  │  │ 500px alto         │  │   │  │ User Input: SSIS     │   │    │
│  │  │                    │  │   │  │ Detected: PENDING    │   │    │
│  │  │ muestra logs del   │  │   │  │                      │   │    │
│  │  │ scan en tiempo     │  │   │  │ [Conflict resolution │   │    │
│  │  │ real               │  │   │  │  si hay mismatch]    │   │    │
│  │  └────────────────────┘  │   │  └──────────────────────┘   │    │
│  │                          │   │                              │    │
│  │  ┌────────────────────┐  │   │  ┌──────────────────────┐   │    │
│  │  │ 📊 Forensic       │  │   │  │ 📄 Tribal Knowledge  │   │    │
│  │  │ Assessment         │  │   │  │ Ingest               │   │    │
│  │  │                    │  │   │  │                      │   │    │
│  │  │ Completeness: 85%  │  │   │  │ [Drag & drop upload] │   │    │
│  │  │ Summary: "..."     │  │   │  │                      │   │    │
│  │  │ Gaps: [list]       │  │   │  │ • doc1.pdf ✓         │   │    │
│  │  │                    │  │   │  │ • rules.md ✓         │   │    │
│  │  └────────────────────┘  │   │  └──────────────────────┘   │    │
│  │                          │   │                              │    │
│  └──────────────────────────┘   └──────────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### Layout propuesto (después del cambio):

```
┌──────────────────────────────────────────────────────────────────────┐
│  StageHeader: "Stage 1: Quick Assessment"                            │
│  Subtítulo: "Evaluación rápida de viabilidad de migración"           │
│  Botones: [Quick Assess]  ──────────────────────── [Start Triage]    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────┐   ┌──────────────────────────────┐    │
│  │  COLUMNA IZQUIERDA (7)  │   │  COLUMNA DERECHA (5)         │    │
│  │                          │   │                              │    │
│  │  ┌────────────────────┐  │   │  ┌──────────────────────┐   │    │
│  │  │ 🚦 SEMÁFORO       │  │   │  │ 📊 Desglose de       │   │    │
│  │  │                    │  │   │  │ Archivos              │   │    │
│  │  │    ████████████    │  │   │  │                      │   │    │
│  │  │    ██  🟢  75  ██ │  │   │  │ 🟢 Migrables    12  │   │    │
│  │  │    ████████████    │  │   │  │ 🔵 Soporte       5  │   │    │
│  │  │                    │  │   │  │ ⚪ Documentación  3  │   │    │
│  │  │  VIABLE            │  │   │  │ 🔴 No reconocido 1  │   │    │
│  │  │  Score: 75/100     │  │   │  │                      │   │    │
│  │  │                    │  │   │  │ ━━━━━━━━━━━━━━━━━━   │   │    │
│  │  └────────────────────┘  │   │  │ Total: 21 archivos   │   │    │
│  │                          │   │  │ ~45,200 líneas       │   │    │
│  │  ┌────────────────────┐  │   │  └──────────────────────┘   │    │
│  │  │ 🔍 Tecnologías    │  │   │                              │    │
│  │  │ Detectadas         │  │   │  ┌──────────────────────┐   │    │
│  │  │                    │  │   │  │ 📄 Tribal Knowledge  │   │    │
│  │  │ ┌──────┐ ┌──────┐ │  │   │  │ Ingest               │   │    │
│  │  │ │ SSIS │ │ SQL  │ │  │   │  │                      │   │    │
│  │  │ │      │ │Server│ │  │   │  │ [Drag & drop upload] │   │    │
│  │  │ └──────┘ └──────┘ │  │   │  │                      │   │    │
│  │  └────────────────────┘  │   │  │ (se mantiene igual)  │   │    │
│  │                          │   │  └──────────────────────┘   │    │
│  │  ┌────────────────────┐  │   │                              │    │
│  │  │ ⚠️ Bloqueadores   │  │   │  ┌──────────────────────┐   │    │
│  │  │ (solo si 🔴)      │  │   │  │ 📋 Detalle por      │   │    │
│  │  │                    │  │   │  │ Archivo (expandible) │   │    │
│  │  │ • No se detectaron │  │   │  │                      │   │    │
│  │  │   archivos SSIS    │  │   │  │ LoadCustomers.dtsx   │   │    │
│  │  │ • 80% archivos no  │  │   │  │  → MIGRABLE | SSIS  │   │    │
│  │  │   reconocidos      │  │   │  │  → Complejidad: MED  │   │    │
│  │  │                    │  │   │  │ schema.ddl           │   │    │
│  │  └────────────────────┘  │   │  │  → SOPORTE | DDL     │   │    │
│  │                          │   │  │ readme.md            │   │    │
│  └──────────────────────────┘   │  │  → DOCUMENTACIÓN     │   │    │
│                                  │  │ foto.jpg             │   │    │
│                                  │  │  → NO RECONOCIDO     │   │    │
│                                  │  └──────────────────────┘   │    │
│                                  │                              │    │
│                                  └──────────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### Cambios detallados en DiscoveryView:

| # | Elemento | Acción | Detalle |
|---|----------|--------|---------|
| 1 | **StageHeader title** | ✏️ Cambiar | `"Stage 1: Technical Discovery"` → `"Stage 1: Quick Assessment"` |
| 2 | **StageHeader subtitle** | ✏️ Cambiar | `"Agent S: Forensic..."` → `"Evaluación rápida de viabilidad de migración"` |
| 3 | **Botón "Start Forensic Scan"** | 🗑️ Eliminar | Eliminado completamente (Agent S se va a Fase ②) |
| 4 | **Botón "Quick Assess"** | ✨ Nuevo | Reemplaza al Forensic Scan. Estilo similar (cyan, mismo tamaño) |
| 5 | **Consola "Agent S: Forensic Audit"** | 🗑️ Eliminar | El terminal de logs de Agent S se elimina |
| 6 | **Tarjeta "Forensic Assessment"** | 🗑️ Eliminar | Completeness score + gaps + summary se eliminan |
| 7 | **Tarjeta SEMÁFORO** | ✨ Nueva | Gran indicador visual con score numérico y color (columna izquierda, arriba) |
| 8 | **Tarjeta "Tecnologías Detectadas"** | ✨ Nueva | Badges de tecnologías (columna izquierda, medio) |
| 9 | **Tarjeta "Bloqueadores"** | ✨ Nueva | Solo visible cuando semáforo = 🔴 (columna izquierda, abajo) |
| 10 | **Tarjeta "Desglose de Archivos"** | ✨ Nueva | 4 categorías con conteo + barra visual (columna derecha, arriba) |
| 11 | **Tarjeta "Detalle por Archivo"** | ✨ Nueva | Lista expandible con clasificación individual (columna derecha, abajo) |
| 12 | **Tarjeta "Technology Validation"** | 🗑️ Eliminar | La detección de tech ahora es parte del QA |
| 13 | **Tarjeta "Tribal Knowledge Ingest"** | ✅ Se mantiene | Upload de documentos de soporte, sin cambios |
| 14 | **Condición `isApproveDisabled`** | ✏️ Cambiar | Antes: `scanProgress < 100 \|\| showConflict`. Después: `!qaResult` (QA debe haberse ejecutado) |
| 15 | **Estado vacío (antes del QA)** | ✨ Nuevo | Ícono de búsqueda + "Suba archivos y ejecute Quick Assess para evaluar viabilidad" |

#### Estados eliminados de DiscoveryView:

```typescript
// SE ELIMINAN:
const [isScanning, setIsScanning] = useState(false);      // ← usado por Agent S
const [scanProgress, setScanProgress] = useState(0);       // ← usado por Agent S
const [scanLogs, setScanLogs] = useState<string[]>([]);    // ← logs de Agent S
const [showConflict, setShowConflict] = useState(false);   // ← conflicto tech (ahora en QA)
const [assessment, setAssessment] = useState(...)           // ← resultado Agent S

// SE AGREGAN:
const [qaResult, setQaResult] = useState<QuickAssessmentResult | null>(null);
const [isAssessing, setIsAssessing] = useState(false);
```

#### Funciones eliminadas de DiscoveryView:

```typescript
// SE ELIMINAN:
const runScan = async () => { ... }           // ← llamaba a Agent S (LLM)
const handleScan = () => { runScan(); }       // ← wrapper del scan
const handleUpdateTech = async () => { ... }  // ← actualizar tech por conflicto

// SE AGREGAN:
const runQuickAssess = async () => { ... }    // ← POST /quick-assessment
```

---

### 5.4 StageHeader (Discovery) — Ajustes

**Archivo:** `apps/web/app/components/StageHeader.tsx`

No cambia el componente en sí, solo los props que recibe desde DiscoveryView:

| Prop | Valor actual | Valor nuevo |
|------|-------------|-------------|
| `title` | `"Stage 1: Technical Discovery"` | `"Stage 1: Quick Assessment"` |
| `subtitle` | `"Agent S: Forensic repository audit and gap detection"` | `"Evaluación rápida de viabilidad de migración"` |
| `approveLabel` | `"Start Triage"` | `"Start Triage"` (sin cambio) |
| `isApproveDisabled` | `scanProgress < 100 \|\| showConflict` | `!qaResult` |
| `icon` | `<Activity>` (cyan) | `<Zap>` (cyan) — más acorde a "rápido" |

---

### 5.5 TriageView — Ajustes Menores

**Archivo:** `apps/web/app/components/stages/TriageView.tsx` (1531 líneas)

Los cambios son **solo en el backend** (eliminar Agent S del pipeline). La UI de Triage no cambia visualmente:

| Elemento | Cambio |
|----------|--------|
| Botón "Run Analysis" | ✅ Se mantiene igual |
| Pipeline de ejecución | ⚙️ Backend: eliminar paso Agent S (de 4 pasos a 3) |
| Logs de ejecución | Los logs ya no mostrarán "Agent S assessing..." |
| Resultado visible | El mismo (assets clasificados en grafo) |

---

### 5.6 Resumen Visual — Antes vs Después

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    ANTES (estado actual)                             ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                     ║
║  Discovery:                                                         ║
║    Upload → Forensic Scan (Agent S, LLM) → Resolver conflictos      ║
║                                                                     ║
║  Triage:                                                            ║
║    Run Analysis → manifest + Agent A (LLM) + Agent S (LLM) → persist║
║                                                                     ║
║  Llamadas LLM totales: 3 (1 en Discovery + 2 en Triage)             ║
║  Tiempo sin feedback: 15-30 seg (primera respuesta tras upload)     ║
║  Costo: $$$ (3 llamadas GPT-4)                                     ║
║                                                                     ║
╚═══════════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════════════╗
║                   DESPUÉS (con Quick Assessment)                     ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                     ║
║  Discovery:                                                         ║
║    Upload → Quick Assess (determ. + LLM opinión) → Semáforo + Score  ║
║                                                                     ║
║  Triage:                                                            ║
║    Run Analysis → manifest + Agent A (LLM) → persist                 ║
║                                                                     ║
║  Llamadas LLM totales: 2 (QA opinión + Agent A en Triage)            ║
║  Tiempo sin feedback: 3-5 seg (QA rápido)                           ║
║  Costo: configurable por cliente (Agent Matrix)                     ║
║  Modelo QA: el cliente elige (recomendamos barato/rápido)           ║
║                                                                     ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 6. Endpoints API — Nuevos y Modificados

### 6.1 Endpoints Nuevos

| Método | Ruta | Propósito |
|--------|------|-----------|
| `POST` | `/api/v1/projects/{id}/quick-assessment` | Ejecutar Quick Assessment |
| `GET` | `/api/v1/projects/{id}/quick-assessment` | Obtener resultado cacheado |

#### POST `/projects/{id}/quick-assessment`

**Request:** Sin body (usa archivos ya subidos en Triage folder)

**Response (200):**
```json
{
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
  "file_details": [
    {
      "filename": "LoadCustomers.dtsx",
      "category": "MIGRABLE",
      "detected_tech": "SSIS",
      "complexity_hint": "MEDIUM",
      "size_bytes": 45230,
      "line_count": 1200
    }
  ],
  "total_files": 21,
  "total_lines": 45200,
  "assessed_at": "2026-02-15T14:30:00Z"
}
```

**Errores:**
- `404` — Proyecto no encontrado
- `400` — No hay archivos subidos en la carpeta Triage

### 6.2 Endpoints Modificados

| Método | Ruta | Cambio |
|--------|------|--------|
| `POST` | `/api/v1/projects/{id}/triage` | Eliminar paso Agent S del pipeline |

### 6.3 Endpoints Eliminados (de Discovery)

| Método | Ruta | Estado |
|--------|------|--------|
| `POST` | `/api/v1/system/scout/assess` | **No se elimina el endpoint**, pero ya no se llama desde Discovery. Se usará en Fase ② Deep Discovery. |

---

## 7. Archivos Afectados

### 7.1 Archivos Nuevos

| Archivo | Tipo | Propósito |
|---------|------|-----------|
| `apps/api/services/quick_assessment_service.py` | Backend | Servicio QA: clasificación + score + semáforo |
| `apps/api/services/knowledge_packet_service.py` | Backend | Servicio Knowledge: unifica 6 silos (Parte B) |

### 7.2 Archivos Modificados — Backend

| Archivo | Líneas | Cambio |
|---------|--------|--------|
| `apps/api/routers/projects.py` | ~500 | Agregar endpoints `quick-assessment` (POST + GET) |
| `apps/api/routers/triage.py` | 936 | Eliminar llamada a Agent S del pipeline (~20 líneas) |
| `apps/api/services/agent_c_service.py` | 1483 | (Parte B) Reemplazar `SchemaMetadataService` con `KnowledgePacketService` |

### 7.3 Archivos Modificados — Frontend

| Archivo | Líneas | Cambio | Impacto |
|---------|--------|--------|---------|
| `apps/web/app/components/stages/DiscoveryView.tsx` | 473 | **Reescritura parcial (~60%)** — eliminar Agent S UI, agregar QA UI | 🔴 Alto |
| `apps/web/app/components/WorkflowToolbar.tsx` | 114 | Sin cambio funcional para Fase ① | ⚪ Ninguno |
| `apps/web/app/workspace/page.tsx` | 520 | Sin cambio (DiscoveryView ya recibe onStageChange) | ⚪ Ninguno |
| `apps/web/app/components/StageHeader.tsx` | 139 | Sin cambio (solo recibe props diferentes) | ⚪ Ninguno |
| `apps/web/app/components/stages/TriageView.tsx` | 1531 | Sin cambio visual (Agent S se elimina del backend, no de la UI) | ⚪ Ninguno |

### 7.4 Archivos NO Afectados

| Archivo | Razón |
|---------|-------|
| `apps/api/services/discovery_service.py` | `generate_manifest()` se reutiliza tal cual |
| `apps/api/services/agent_s_service.py` | No se elimina, se mueve a Fase ② |
| `apps/api/services/agent_a_service.py` | Se mantiene en pipeline de Triage |
| `apps/api/services/persistence_service.py` | Sin cambios de schema |
| Toda la base de datos | **Sin migraciones** |

---

## 8. Plan de Ejecución

### Fase A: Quick Assessment (Prioridad)

| Step | Tarea | Esfuerzo | Dependencia |
|------|-------|----------|-------------|
| A1 | Crear `QuickAssessmentService` con modelos Pydantic | 🟢 Med | Ninguna |
| A2 | Crear endpoints POST/GET en `projects.py` | 🟢 Med | A1 |
| A3 | Eliminar Agent S del pipeline de Triage (`triage.py`) | 🟢 Bajo | Ninguna |
| A4 | Reescribir `DiscoveryView.tsx` — eliminar Agent S UI | 🟡 Alto | Ninguna |
| A5 | Agregar tarjetas QA en `DiscoveryView.tsx` | 🟡 Alto | A2, A4 |
| A6 | Cambiar condición `isApproveDisabled` | 🟢 Bajo | A5 |
| A7 | Testing end-to-end | 🟢 Med | A1-A6 |

### Fase B: Knowledge Packet (Después de A)

| Step | Tarea | Esfuerzo | Dependencia |
|------|-------|----------|-------------|
| B1 | Crear `KnowledgePacketService` con modelos Pydantic | 🟡 Alto | Ninguna |
| B2 | Implementar resolución de tipos (DDL > profiled > metadata) | 🟡 Alto | B1 |
| B3 | Wiring: integrar KnowledgePacket en Agent C prompt | 🟡 Alto | B1 |
| B4 | Testing: comparar prompts antes/después | 🟢 Med | B3 |

### Orden de implementación propuesto:

```
Semana 1: A1 → A2 → A3 (backend QA completo)
Semana 2: A4 → A5 → A6 (frontend QA completo)
Semana 3: A7 + B1 → B2 (testing QA + inicio Knowledge)
Semana 4: B3 → B4 (Knowledge integrado en Agent C)
```

---

## 9. Decisiones Tomadas

| # | Decisión | Opción elegida | Razón |
|---|----------|---------------|-------|
| 1 | Schema de datos | Service layer only (sin migraciones) | Menor riesgo, no rompe Sprint 7/8.5, más rápido |
| 2 | Trigger del QA | Botón manual "Quick Assess" | Control del usuario sobre cuándo ejecutar |
| 3 | Agent S en Discovery | Mover a Fase ② Deep Discovery | Evita duplicación con QA, Agent S pertenece al análisis profundo con RAG |
| 4 | Prioridad | QA primero, luego Knowledge | Win visible para el usuario, valida concepto antes de invertir en plumbing |
| 5 | Re-ejecutar manifest en Triage | Sí, re-ejecutar | Más simple que cachear, `generate_manifest()` es rápido (2-15 seg) |
| 6 | Endpoint Agent S | No eliminar | Se reutilizará en Fase ② Deep Discovery |
| 7 | Frontend: layout 2 columnas | Mantener grid 7+5 | Mismo layout, diferentes tarjetas |
| 8 | LLM en QA | Sí, opinión rápida via Agent Matrix (ya existente) | Solo 1 INSERT en `utm_agent_catalog`. Modelo/costo lo decide el cliente desde la UI de Admin que ya existe |
| 9 | Cruce SSIS↔DDL en QA | No, solo en KnowledgePacket (Parte B) | QA se mantiene simple. El cruce profundo es parte de la consolidación de conocimiento |
| 10 | Score numérico | Mantener score 0-100 + semáforo | Score como indicador interno + semáforo como visual principal |
| 11 | Naming Stage 4 | "Re-Architecture" en vez de "Medallion" | Medallion es un patrón, no el único. Re-Architecture abraza Medallion, Star Schema, Data Vault, etc. |

---

## 10. Verificación / Testing

### 10.1 Tests Quick Assessment

| Test | Descripción | Resultado esperado |
|------|-------------|-------------------|
| QA-01 | Upload 10 `.dtsx` + 2 `.sql` + 1 `.md` | Score ≥ 60, semáforo 🟢, 10 MIGRABLE, 2 SOPORTE, 1 DOC |
| QA-02 | Upload 3 `.jpg` + 2 `.exe` + 1 `.zip` | Score < 30, semáforo 🔴, 6 NO RECONOCIDO, blockers listados |
| QA-03 | Upload 5 `.dtsx` + 5 `.jpg` | Score ~30-59, semáforo 🟡 |
| QA-04 | Upload 0 archivos, ejecutar QA | Error 400: "No hay archivos en la carpeta Triage" |
| QA-05 | Ejecutar QA, luego GET | GET retorna el resultado cacheado |
| QA-06 | Subir más archivos, ejecutar QA de nuevo | Score recalculado con los nuevos archivos |

### 10.2 Tests Triage (post-cambio)

| Test | Descripción | Resultado esperado |
|------|-------------|-------------------|
| TR-01 | Run Triage sin Agent S | Pipeline completa en ~50% menos tiempo |
| TR-02 | Assets clasificados correctamente | Misma calidad de clasificación (Agent A sigue presente) |
| TR-03 | Logs de ejecución | No aparece "Agent S assessing..." en los logs |

### 10.3 Tests Knowledge Packet (Parte B)

| Test | Descripción | Resultado esperado |
|------|-------------|-------------------|
| KP-01 | Asset SSIS con medulla + DDL + profiling | KnowledgePacket contiene tipos DDL, source_query, transformaciones |
| KP-02 | Asset sin DDL (solo SSIS) | KnowledgePacket usa tipos de profiling, fallback a "STRING" |
| KP-03 | Prompt de Agent C con KnowledgePacket | Prompt incluye source_query, transformaciones, tipos reales, PII |
| KP-04 | Código generado antes/después | Código post-KP referencia columnas con tipos correctos y lógica de transformación |

### 10.4 Tests Cruce SSIS ↔ DDL (el eslabón clave)

| Test | Descripción | Resultado esperado |
|------|-------------|-------------------|
| CR-01 | `.dtsx` con SqlCommand `SELECT * FROM dbo.DimCustomers` + DDL con `CREATE TABLE DimCustomers` | Columnas resueltas con tipos del DDL (`INT`, `VARCHAR(50)`), no `STRING` |
| CR-02 | `.dtsx` referencia tabla `dbo.Fact_Sales` pero NO hay DDL para esa tabla | Columnas mantienen tipo `STRING` (fallback). Log indica "No DDL match found for Fact_Sales" |
| CR-03 | `.dtsx` con LOOKUP a `dbo.DimRegion` + DDL de DimRegion | Las columnas del lookup también se resuelven con tipos del DDL |
| CR-04 | `.dtsx` con conexión OLEDB → KnowledgePacket incluye server + database | `source_connections` incluye `server: SERVIDOR01`, `database: AdventureWorksDW` extraído del connection string |
| CR-05 | Proyecto con 5 `.dtsx` que referencian 3 tablas + DDL con esas 3 tablas | Todos los KnowledgePackets tienen tipos reales cruzados |
| CR-06 | Solo `.dtsx` sin ningún DDL subido | Sistema funciona normalmente con fallback a `STRING`. Sin errores. |

---

## Anexo: Diagrama de Flujo Completo (Antes/Después)

### ANTES

```
Upload → [nada] → Agent S (LLM, 15-30seg) → Resolver conflicto → Approve
   │                                                                  │
   │                                                                  ▼
   │                                                         Stage 2: Triage
   │                                                                  │
   │                                        manifest + Agent A (LLM) + Agent S (LLM)
   │                                                                  │
   │                                                                  ▼
   │                                                         Stage 3: Drafting
   │                                                                  │
   │                                                       Agent C (LLM, prompt con:
   │                                                         • columns = ["STRING"]
   │                                                         • registry = paths/naming
   │                                                         • SIN source queries
   │                                                         • SIN transformaciones
   │                                                         • SIN tipos reales
   │                                                         • SIN PII flags)
```

### DESPUÉS (Fase ① + Parte B)

```
Upload → Quick Assess (determinístico, 3-5seg) → Semáforo + Score → Approve
   │                                                                  │
   │                                                                  ▼
   │                                                         Stage 2: Triage
   │                                                                  │
   │                                              manifest + Agent A (LLM) ← solo 1 LLM
   │                                                                  │
   │                                                                  ▼
   │                                                         Stage 3: Drafting
   │                                                                  │
   │                                                       Agent C (LLM, prompt con:
   │                                                         • KnowledgePacket:
   │                                                           ✓ tipos DDL reales
   │                                                           ✓ source_query
   │                                                           ✓ transformaciones
   │                                                           ✓ PII flags
   │                                                           ✓ column mappings
   │                                                           ✓ contexto de negocio)
```

---

*Documento generado como parte del replanteo conceptual v4.0+ de Legacy2Lake UTM.*
