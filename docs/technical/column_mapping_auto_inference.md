# Column Mapping Auto-Inference (Sprint 14.5)

## 🎯 Overview

Durante el proceso de **Triage**, el sistema ahora **automáticamente extrae y persiste** los column mappings (source→target) desde archivos SSIS a la tabla `utm_column_mappings`.

## 🔄 Flujo de Implementación

### 1. Parsing (apps/utm/cartridges/ssis/parser.py)
```python
# El parser SSIS ya extraía mappings desde línea 140-150:
for input_col in comp.xpath('.//*[local-name()="inputColumn"]'):
    mappings.append({
        "source": input_col.get("externalMetadataColumnId"),
        "target": input_col.get("name"),
        "usage": "INPUT"
    })
```

### 2. Persistencia (apps/api/routers/triage.py línea 88-169)

Nueva función `_persist_column_mappings()`:
- Extrae mappings INPUT (source → target)
- Extrae mappings OUTPUT (derived/calculated columns)
- Detecta tipo de transformación:
  - `DERIVED` - Columnas calculadas (Derived Column)
  - `LOOKUP` - Búsquedas
  - `AGGREGATE` - Agregaciones
  - `RENAME` - Simple renombrado
  - `OUTPUT` - Columnas de salida nuevas
- **Deduplicación** automática de pares (source, target)
- Bulk insert a `utm_column_mappings`

### 3. Integración en Triage (línea 643-649)
```python
# Después de persistir data_flow_analysis
mapping_count = await _persist_column_mappings(object_id, medulla, db)
total_mappings += mapping_count
if mapping_count > 0:
    await _log(f"  └─ Persisted {mapping_count} column mapping(s)", agent="TRIAGE")
```

## 📊 Resultado

### En Logs de Triage
```
[TRIAGE] Extracting origin analysis from SSIS assets...
[TRIAGE]   └─ Persisted 23 column mapping(s) for Package_DimCustomers.dtsx
[TRIAGE]   └─ Persisted 15 column mapping(s) for Package_FactSales.dtsx
[TRIAGE] ✅ Extracted origin analysis from 12 SSIS asset(s) | 187 total column mappings
```

### En Base de Datos (utm_column_mappings)
| asset_id | source_column | target_column | transformation_rule |
|----------|---------------|---------------|---------------------|
| abc-123  | CustomerID    | CustomerID    | NULL (passthrough)  |
| abc-123  | FirstName     | FullName      | DERIVED             |
| abc-123  | Price         | TotalPrice    | LOOKUP              |

### En UI (Transformations Tab)
- **Total Assets:** 12
- **Total Transformations:** 187
- **Breakdown:**
  - Renames: 45
  - Type Conversions: 12
  - Business Logic: 8
  - Derived: 23
  - Passthrough: 99

## 🔑 Ventajas

1. ✅ **Zero configuración manual** - Auto-inferred durante Triage
2. ✅ **Trazabilidad completa** - Cada columna trackeada source→target
3. ✅ **Base para IA** - Knowledge Packet tiene datos granulares
4. ✅ **Debugging facilitado** - Saber qué columnas faltan/cambian
5. ✅ **Transformations Tab funcional** - Muestra datos reales inmediatamente

## 🧪 Testing

### Caso de Prueba 1: Re-Triage de Proyecto Existente
```bash
# Tu proyecto ec771d1a-4fe4-4499-970d-54e28de4d926
# 1. Ejecutar Triage nuevamente
POST /api/v1/triage/run
{
    "project_id": "ec771d1a-4fe4-4499-970d-54e28de4d926",
    "params": {}
}

# 2. Verificar utm_column_mappings
SELECT COUNT(*) FROM utm_column_mappings 
WHERE asset_id IN (
    SELECT object_id FROM utm_objects 
    WHERE project_id = 'ec771d1a-4fe4-4499-970d-54e28de4d926'
);

# 3. Ver Transformations Tab - debería mostrar datos
```

### Caso de Prueba 2: Nuevo Proyecto
```bash
# 1. Subir SSIS files
# 2. Ejecutar Triage
# 3. Inmediatamente ver column mappings en UI
```

## 🚧 Limitaciones Actuales

1. **Solo SSIS** - Otros parsers (Informatica, Talend) necesitan implementación similar
2. **Sin data types** - Por ahora solo nombres, tipos de datos vendrán de parser mejorado
3. **Sin detección PII** - is_pii queda en FALSE (feature futura)
4. **Limpieza de nombres** - Solo quita prefijos XML, no normaliza mayúsculas/espacios

## 🔮 Futuras Mejoras

- [ ] Detectar tipos de datos (source_datatype/target_datatype) desde XML
- [ ] PII detection usando regex en nombres de columnas
- [ ] Integrar con parser de Informatica/Talend
- [ ] Sugerir mejores nombres (IA-powered renaming suggestions)
- [ ] Validar que target_column existe en schema destino

## 📚 Referencias

- **Parser SSIS:** `apps/utm/cartridges/ssis/parser.py` línea 140-160
- **Triage Router:** `apps/api/routers/triage.py` línea 88-169, 643-649
- **Column Mapping Service:** `apps/api/services/column_mapping_service.py`
- **Transformations Endpoint:** `apps/api/routers/visualization.py` línea 1135-1270
- **Database Schema:** `supabase_migrations/004_column_mappings.sql`

---

**Implementado:** Sprint 14.5 (2026-02-19)  
**Autor:** AI-Assisted Development
