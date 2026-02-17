# PROPUESTA: Dashboard Discovery & Triage
## Problema Actual

**Sprint 13 actual muestra RESULTADOS (código generado)**:
- ✅ CodeViewer: Código PySpark (ya visible en VS Code - REDUNDANTE)
- ✅ SchemaViewer: Esquema extraído del código generado
- ✅ QualityDashboard: Métricas de calidad del código
- ✅ PerformanceDashboard: Métricas de performance del código

**❌ PERO NO MUESTRA EL ANÁLISIS DEL ORIGEN (donde está el valor real)**

---

## Datos Disponibles en el Parser SSIS

El `SSISCartridge` YA extrae:

### 1. Conexiones (`get_connection_managers()`)
```json
{
  "name": "OLEDB_SourceConnection",
  "id": "{ABC-123}",
  "connection_string": "Data Source=SERVER01;Initial Catalog=Northwind;..."
}
```

### 2. Componentes Data Flow (`get_data_flow_components()`)
```json
{
  "type": "SOURCE_DB",
  "name": "OLE DB Source - Customers",
  "raw_properties": {
    "SqlCommand": "SELECT custid, contactname, city FROM dbo.Customers"
  }
},
{
  "type": "LOOKUP",
  "name": "Lookup - Countries",
  "raw_properties": {
    "SqlCommand": "SELECT country_code, country_name FROM dbo.Countries"
  }
},
{
  "type": "DERIVED_COLUMN",
  "name": "Add LoadDate",
  "mappings": [...]
}
```

### 3. Control Flow & Topology
```json
{
  "executables": [
    {"name": "Data Flow Task 1", "type": "DTS:ExecutablePath"},
    {"name": "Execute SQL Task", "type": "DTS:ExecutablePath"}
  ],
  "constraints": [
    {"source": "{Task1-ID}", "target": "{Task2-ID}"}
  ]
}
```

---

## Propuesta: 3 Componentes Nuevos para Discovery & Triage

### 📊 **Component 1: Origin Analysis Panel**
**Ubicación**: Tab "Origin Analysis" (antes de CodeViewer)

**Muestra**:
```
┌─────────────────────────────────────────────┐
│ 🔍 ORIGIN ANALYSIS                          │
├─────────────────────────────────────────────┤
│ Source System: SQL Server (OLEDB)          │
│ Server: SERVER01                            │
│ Database: Northwind                         │
│ Package: DimCustomers.dtsx                  │
│                                             │
│ 📊 Statistics:                              │
│   • Source Tables: 2 (Customers, Countries) │
│   • Total Rows: ~10,000 (estimated)         │
│   • Columns: 7 detected                     │
│                                             │
│ 🔗 Connections:                             │
│   [OLEDB_SourceConnection]                  │
│     └─ Data Source: SERVER01\Northwind     │
│   [OLEDB_DestConnection]                    │
│     └─ Data Source: DW01\DataWarehouse     │
└─────────────────────────────────────────────┘
```

### 🔧 **Component 2: Transformations Matrix**
**Ubicación**: Tab "Transformations" (entre Origin y CodeViewer)

**Muestra**:
```
┌─────────────────────────────────────────────────────────┐
│ 🔧 TRANSFORMATIONS DETECTED                             │
├──────────────────┬──────────────┬───────────────────────┤
│ Type             │ Count        │ Details               │
├──────────────────┼──────────────┼───────────────────────┤
│ 🔍 LOOKUP        │ 2            │ Countries, Regions    │
│ 📝 DERIVED COL   │ 1            │ LoadDate              │
│ 🔀 MERGE         │ 0            │ -                     │
│ ⚙️  AGGREGATE    │ 0            │ -                     │
│ 🔄 CONDITIONAL   │ 1            │ FilterActive          │
│ 📊 DATA CONVERT  │ 3            │ custid, postalcode... │
├──────────────────┴──────────────┴───────────────────────┤
│ 🎯 Complexity Score: 42/100 (Medium)                    │
│                                                          │
│ ⚠️  Warnings:                                            │
│   • Lookup without cache may impact performance         │
│   • Derived column uses complex expression              │
└──────────────────────────────────────────────────────────┘
```

### 📜 **Component 3: Source Queries Viewer**
**Ubicación**: Tab "Source Queries" (entre Transformations y CodeViewer)

**Muestra**:
```
┌─────────────────────────────────────────────┐
│ 📜 SOURCE QUERIES                           │
├─────────────────────────────────────────────┤
│ [SOURCE] OLE DB Source - Customers          │
│                                             │
│ SELECT                                      │
│     custid,                                 │
│     contactname,                            │
│     city,                                   │
│     country,                                │
│     address,                                │
│     phone,                                  │
│     postalcode                              │
│ FROM dbo.Customers                          │
│ WHERE active = 1                            │
│                                             │
│ [LOOKUP] Lookup - Countries                 │
│                                             │
│ SELECT                                      │
│     country_code,                           │
│     country_name                            │
│ FROM dbo.Countries                          │
└─────────────────────────────────────────────┘
```

---

## Implementación: 3 Pasos

### PASO 1: Persistir Datos Sprint 8
Modificar `agent_c_service.py` para guardar análisis SSIS:

```python
# Después del parsing SSIS, antes de generar código
medulla = parser_result.metadata  # Ya tiene todo el análisis

# Extract origin data
origin_analysis = {
    "connections": medulla.get("summary", {}).get("connection_managers", []),
    "source_type": "SQL Server (OLEDB)",  # Extraer del connection_string
    "server": "SERVER01",  # Parsear de connection_string
    "database": "Northwind"  # Parsear de connection_string
}

# Extract transformations
transformations_list = []
for comp in medulla.get("data_flow_logic", []):
    transformations_list.append({
        "type": comp["type"],
        "name": comp["name"],
        "sql_query": comp["raw_properties"].get("SqlCommand"),
        "complexity": calculate_complexity(comp)
    })

# Calculate complexity score
complexity_score = calculate_package_complexity(transformations_list)

# UPDATE utm_objects con Sprint 8 data
await persistence.update_utm_object(
    project_id=project_id,
    object_name=object_name,
    updates={
        "source_connection": json.dumps(origin_analysis["connections"]),
        "source_type": origin_analysis["source_type"],
        "source_query": extract_main_query(transformations_list),
        "transformations": json.dumps(transformations_list),
        "complexity_score": complexity_score,
        "data_flow_analysis": json.dumps(medulla.get("data_flow_logic", []))
    }
)
```

### PASO 2: Crear APIs Backend
Agregar 3 endpoints en `visualization.py`:

```python
@router.get("/projects/{project_id}/origin-analysis")
async def get_origin_analysis(project_id: str):
    """Devuelve análisis del sistema origen"""
    # Query utm_objects: source_connection, source_type, source_query
    ...

@router.get("/projects/{project_id}/transformations")
async def get_transformations(project_id: str):
    """Devuelve matriz de transformaciones detectadas"""
    # Query utm_objects: transformations, complexity_score
    ...

@router.get("/projects/{project_id}/source-queries")
async def get_source_queries(project_id: str):
    """Devuelve queries SQL originales"""
    # Query utm_objects: data_flow_analysis
    ...
```

### PASO 3: Crear Componentes Frontend
Crear 3 componentes React:

```
apps/web/src/components/sprint13/
├── OriginAnalysisPanel.tsx      (Component 1)
├── TransformationsMatrix.tsx    (Component 2)
└── SourceQueriesViewer.tsx      (Component 3)
```

Integrar en la página principal:
```tsx
<Tabs>
  <Tab label="Origin Analysis">
    <OriginAnalysisPanel projectId={projectId} />
  </Tab>
  <Tab label="Transformations">
    <TransformationsMatrix projectId={projectId} />
  </Tab>
  <Tab label="Source Queries">
    <SourceQueriesViewer projectId={projectId} />
  </Tab>
  <Tab label="Generated Code">
    <CodeViewer projectId={projectId} />
  </Tab>
  <Tab label="Schema">
    <SchemaViewer projectId={projectId} />
  </Tab>
</Tabs>
```

---

## Valor para el Usuario

### ❌ **Antes (Sprint 13 actual)**:
- "Muestra código que ya puedo ver en VS Code"
- "Esquema que no sé de dónde viene"
- "No veo qué analizó el sistema"

### ✅ **Después (con Discovery & Triage Dashboard)**:
- "Veo qué conexiones detectó del SSIS"
- "Veo qué transformaciones identificó (2 LOOKUPS, 1 Derived Column)"
- "Veo las queries SQL originales del paquete"
- "Veo el score de complejidad (42/100 - Medium)"
- **"AHORA ENTIENDO QUÉ HIZO EL SISTEMA EN DISCOVERY & TRIAGE"** 🎯

---

## Demostración con 7 Paquetes

**Antes**:
- Solo veo 7 códigos generados (iguales a archivos en disco)

**Después**:
```
Project: Northwind Migration (7 packages)

📊 ORIGIN ANALYSIS SUMMARY
├─ SQL Server: SERVER01\Northwind
├─ Total Tables: 12
├─ Total Transformations: 24
│   ├─ LOOKUP: 8
│   ├─ DERIVED_COLUMN: 5
│   ├─ MERGE: 2
│   └─ CONDITIONAL: 9
├─ Avg Complexity: 38/100 (Medium-Low)
└─ Warnings: 3

[View Details per Package] →
```

**Esto SÍ muestra valor** - análisis agregado de 7 paquetes con insights accionables.

---

## Siguiente Paso Recomendado

**¿Quieres que implemente el PASO 1 (persistir datos Sprint 8)?**

Esto incluye:
1. Modificar `agent_c_service.py` para extraer y guardar análisis SSIS
2. Función `calculate_complexity()` basada en # transformaciones
3. Parsear connection strings para extraer server/database
4. Test con DimCustomers.dtsx para validar

**Tiempo estimado**: 30-45 minutos

Una vez persistido, podemos crear los 3 componentes visuales.
