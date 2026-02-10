# 🔀 Architecture Variants Strategy - v5.0 Design

**Status:** DRAFT - Future Enhancement  
**Target:** v5.0 (Post Agent C testing & Sprint 1)  
**Created:** 2026-02-10

---

## 🎯 Core Concept

**Variantes arquitecturales = Decisión del usuario en Layer 3, NO defaults de UTM**

Las arquitecturas alternativas (Warehouse vs Lakehouse, SQL vs PySpark, etc.) deben:
1. **Respetar** el prompt del usuario en su configuración de agente/cartucho
2. **Adaptarse** dinámicamente según contexto del tenant/project
3. **Coexistir** sin conflictos en el mismo sistema

---

## 📐 Layer System Design

```
Layer 1: Base Agent (utm_prompts)
├─ Instrucciones genéricas de agente
└─ NO menciona arquitecturas específicas

Layer 2: Tech Cartridge (utm_system_prompts) - DEFAULTS
├─ fabric/lakehouse/* (default)
├─ databricks/pyspark/* (default)
└─ snowflake/snowpark/* (default)

Layer 3: User Override (runtime composition)
├─ Tenant config: "architecture_type": "warehouse"
├─ Project prompt: "Use T-SQL stored procedures instead of PySpark"
└─ OVERRIDE Layer 2 defaults con arquitectura específica del usuario
```

---

## 🏗️ Real-World Variant Examples

### Fabric (Lakehouse vs Warehouse vs SQL)
```yaml
# DEFAULT (v2.0.0 actual)
cartridge: fabric
architecture: lakehouse
engine: pyspark
storage: delta_parquet
layer_2_prompt: "prompt_lab/cartridges/fabric/bronze_layer.md"

# USER VARIANT 1 (Layer 3 override)
tenant_override:
  architecture: warehouse
  engine: tsql
  storage: sql_tables
  custom_prompt: |
    "En Fabric Warehouse, usa T-SQL stored procedures.
    Bronze: CREATE EXTERNAL TABLE, Silver: MERGE statements"

# USER VARIANT 2 (Layer 3 override)
project_override:
  architecture: sql_endpoint
  engine: spark_sql
  custom_prompt: |
    "Usa Spark SQL notebooks, no PySpark.
    Define todo con CREATE OR REPLACE TABLE AS SELECT"
```

### Databricks (PySpark vs Delta Live Tables vs SQL)
```yaml
# DEFAULT (v2.0.0 actual)
cartridge: databricks
architecture: delta_lake
engine: pyspark
layer_2_prompt: "prompt_lab/cartridges/pyspark/bronze_layer.md"

# USER VARIANT 1 (DLT pipelines)
tenant_override:
  architecture: delta_live_tables
  engine: dlt_python
  custom_prompt: |
    "@dlt.table decorators, expectations, live tables.
    Bronze: @dlt.table, Silver: @dlt.view, Gold: materialized views"

# USER VARIANT 2 (SQL Warehouses)
project_override:
  architecture: sql_warehouse
  engine: databricks_sql
  custom_prompt: |
    "Databricks SQL Warehouse. CREATE LIVE TABLE statements.
    Use SQL Queries dashboard-ready"
```

### Snowflake (Snowpark vs Streams/Tasks vs dbt)
```yaml
# DEFAULT (v2.0.0 actual)
cartridge: snowflake
architecture: snowpark
engine: python
layer_2_prompt: "prompt_lab/cartridges/snowflake/bronze_layer.md"

# USER VARIANT 1 (Native SQL)
tenant_override:
  architecture: native_sql
  engine: snowflake_sql
  custom_prompt: |
    "Snowflake SQL nativo. COPY INTO, MERGE, TASK scheduling.
    No Python, solo CREATE OR REPLACE TABLE AS"

# USER VARIANT 2 (dbt orchestrated)
project_override:
  architecture: dbt_managed
  engine: dbt_sql
  layer_2_override: "prompt_lab/cartridges/dbt/bronze_layer.md"
  custom_prompt: |
    "Todo en dbt. {{ source() }}, {{ ref() }}, models/bronze/*.sql"
```

---

## 🚀 Implementation Strategy (v5.0)

### Phase 1: Detection System
```python
def detect_architecture_override(user_prompt: str, layer_2_default: str):
    """
    Analiza el prompt del usuario para detectar arquitecturas alternativas.
    """
    keywords = {
        "warehouse": ["warehouse", "t-sql", "stored procedure"],
        "sql_only": ["sql only", "no python", "create table as"],
        "dlt": ["delta live tables", "@dlt.table", "expectations"],
        "dbt": ["dbt", "{{ ref() }}", "{{ source() }}"]
    }
    
    detected = scan_keywords(user_prompt, keywords)
    
    if detected:
        return {
            "override_layer_2": True,
            "architecture_type": detected,
            "custom_instructions": extract_custom_instructions(user_prompt)
        }
    
    return {"override_layer_2": False, "use_default": layer_2_default}
```

### Phase 2: Prompt Composition
```python
def compose_final_prompt(layer_1, layer_2, layer_3_overrides):
    """
    Layer 3 override REEMPLAZA secciones de Layer 2, no las complementa.
    """
    if layer_3_overrides.get("architecture_override"):
        # REPLACE Layer 2 architecture-specific sections
        final_prompt = layer_1 + layer_3_overrides["custom_instructions"]
    else:
        # DEFAULT composition
        final_prompt = layer_1 + layer_2
    
    return final_prompt
```

### Phase 3: Variant Catalog (v5.0 database schema)
```sql
-- Nueva tabla para variantes arquitecturales conocidas
CREATE TABLE utm_architecture_variants (
    id UUID PRIMARY KEY,
    tech_id VARCHAR(50),  -- 'fabric', 'databricks', etc.
    variant_name VARCHAR(100),  -- 'warehouse', 'dlt', 'sql_only'
    layer VARCHAR(20),  -- 'bronze', 'silver', 'gold'
    
    -- Detection patterns
    detection_keywords TEXT[],  -- ['warehouse', 't-sql']
    detection_regex TEXT,
    
    -- Override instructions
    architecture_type VARCHAR(50),
    processing_engine VARCHAR(50),
    custom_prompt_template TEXT,  -- Template con placeholders
    
    -- Compatibility
    compatible_with TEXT[],  -- Otros cartridges compatibles
    conflicts_with TEXT[],   -- Variantes incompatibles
    
    -- Metadata
    doc_url TEXT,
    examples JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ejemplo de registro
INSERT INTO utm_architecture_variants VALUES (
    gen_random_uuid(),
    'fabric',
    'warehouse_tsql',
    'bronze',
    ARRAY['warehouse', 't-sql', 'stored procedure'],
    '(warehouse|t-sql|tsql)',
    'warehouse',
    'tsql',
    'En Fabric Warehouse, usa T-SQL stored procedures para {{ layer }}.
    Bronze: CREATE EXTERNAL TABLE con Polybase.
    Silver: MERGE statements con window functions.',
    ARRAY['snowflake_sql', 'bigquery_sql'],
    ARRAY['lakehouse_pyspark'],
    'https://docs.microsoft.com/fabric/warehouse',
    '{"example_1": "CREATE EXTERNAL TABLE...", "example_2": "MERGE INTO..."}'::jsonb,
    NOW()
);
```

---

## 💡 Key Design Principles

1. **User Intent > System Defaults**
   - Si usuario dice "Warehouse", Layer 3 override reemplaza Lakehouse default

2. **Explicit > Implicit**
   - Usuario debe ser explícito en su prompt: "Use Warehouse architecture"
   - No adivinamos, detectamos keywords claros

3. **Backward Compatible**
   - v2.0.0 prompts siguen funcionando sin cambios
   - Variantes son opt-in, no breaking changes

4. **Composable, Not Monolithic**
   - Layer 2 = biblioteca de defaults bien documentados
   - Layer 3 = mezcla/reemplaza según contexto del usuario

5. **Test Before Scale**
   - Sprint 0 Day 4: probar defaults con Agent C
   - Sprint 1-2: si usuarios piden variantes, implementar UNA sola
   - v5.0: si hay demanda real, construir sistema completo

---

## 📊 Decision Matrix: When to Use Variants?

| Scenario | Solution | Layer |
|----------|----------|-------|
| 80% casos comunes | Use default prompts (Lakehouse, PySpark) | Layer 2 |
| Cliente tiene estándar arquitectural | Layer 3 tenant override | Layer 3 |
| Proyecto específico con constraint | Layer 3 project override | Layer 3 |
| Nueva tecnología sin cartridge | Base generic + custom prompt | Layer 3 |
| Variante MUY común (50%+ requests) | Promote to Layer 2 sub-cartridge | Layer 2 |

---

## 🔄 Migration Path: v2.0 → v5.0

**v2.0 (actual)**: Single default per cartridge  
**v3.0**: Layer 3 override detection (keyword-based)  
**v4.0**: Variant catalog (database-driven)  
**v5.0**: Full composability with conflict detection

---

## 📝 Open Questions (to resolve in Sprint 1-2)

1. **Conflict Resolution**: ¿Qué pasa si Layer 2 = PySpark pero Layer 3 = SQL-only?
   - Opción A: Layer 3 wins (REPLACE)
   - Opción B: Hybrid merge (COMPLEMENT)
   - **Decision pending**: Test with Agent C first

2. **Performance**: ¿Cache compiled prompts o compose runtime?
   - Impacto: Latency vs flexibility

3. **Validation**: ¿Cómo validar que override es compatible con tech stack?
   - Ejemplo: No puedes usar Warehouse si no tienes Fabric Capacity

4. **UI/UX**: ¿Cómo exponer variantes al usuario?
   - Dropdown en UI vs free-text prompt vs JSON config

---

## 🎯 Success Metrics (v5.0)

- [ ] Usuarios pueden definir arquitectura en prompt sin editar código
- [ ] 90% casos cubiertos con defaults + 5 variantes por cartucho
- [ ] Zero breaking changes para v2.0-v4.0 prompts
- [ ] Detección automática de conflictos (ej: PySpark + SQL-only = error)

---

**Next Steps:**
1. Complete Sprint 0 Day 4 (Agent C testing with v2.0 defaults)
2. Collect user feedback on architecture preferences
3. Implement ONE variant as proof-of-concept (Sprint 1)
4. If successful, build full system (v5.0)

**Remember:** Don't build features users don't need. Test defaults first, add variants only if demanded.

---

**Last Updated:** 2026-02-10  
**Status:** Design document - NOT implemented  
**Review after:** Sprint 0 Day 4 Agent C testing complete
