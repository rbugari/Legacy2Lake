# Sprint 9: Zero-Hardcode Generation - Quick Reference

**Version:** v3.11  
**Status:** ✅ Production Ready  
**Last Updated:** 2026-02-11

---

## 🚀 Quick Start (3 Minutes)

### 1. Extract Schema Metadata
```python
from apps.api.services.schema_metadata_service import SchemaMetadataService

schema_service = SchemaMetadataService(tenant_id="your-tenant", project_id="your-project")
schema = await schema_service.get_table_schema("asset-uuid-here")

# Access properties
print(schema.table_name)      # "Customers"
print(schema.primary_key)     # ["customer_id"]
print(schema.columns)         # [ColumnMetadata(...), ...]
```

### 2. Extract Project Parameters
```python
from apps.api.services.parameter_extractor_service import ParameterExtractor

extractor = ParameterExtractor(tenant_id="your-tenant", project_id="your-project")
params = await extractor.extract_parameters()

# Access properties
print(params.bronze_schema)   # "raw_staging"
print(params.catalog_name)    # "main"
```

### 3. Generate Code with Template Engine
```python
from apps.api.services.template_engine_service import TemplateEngine

engine = TemplateEngine()
code = await engine.render_template(
    template_name='pyspark_bronze',
    schema=schema,
    params=params,
    layer='bronze'
)

print(code)  # Fully generated PySpark code!
```

### 4. Use in Agent C
```python
from apps.api.services.agent_c_service import AgentCService

agent_c = AgentCService(tenant_id="your-tenant", client_id="your-client")

result = await agent_c.transpile_task({
    'project_id': 'project-123',
    'asset_id': 'asset-456',
    'tech_id': 'pyspark',
    'layer': 'bronze'
})

print(result['code'])        # Generated code
print(result['schema'])      # Extracted schema
print(result['parameters'])  # Extracted parameters
```

---

## 📋 Common Use Cases

### Use Case 1: Generate Bronze Layer Code
```python
# Step 1: Get schema
schema_service = SchemaMetadataService(tenant_id, project_id)
schema = await schema_service.get_table_schema(asset_id)

# Step 2: Get parameters
param_extractor = ParameterExtractor(tenant_id, project_id)
params = await param_extractor.extract_parameters()

# Step 3: Generate code
engine = TemplateEngine()
bronze_code = await engine.render_template('pyspark_bronze', schema, params, 'bronze')

# Result: PySpark code with dynamic table names, columns, schemas
```

### Use Case 2: Generate Silver Layer Code with Primary Key
```python
# Same setup as above

# Generate silver code (includes SCD Type 2 merge logic)
silver_code = await engine.render_template('pyspark_silver', schema, params, 'silver')

# Uses schema.primary_key for merge condition:
# merge_condition = "target.customer_id = source.customer_id"  ← DYNAMIC!
```

### Use Case 3: Resolve Table Names Across Layers
```python
extractor = ParameterExtractor(tenant_id, project_id)
params = await extractor.extract_parameters()

source_table = "Customers"

# Bronze
bronze_table = extractor.resolve_table_name(source_table, 'bronze', params)
bronze_path = extractor.get_full_table_path(bronze_table, 'bronze', params)
# Result: "main.raw_staging.raw_customers"

# Silver
silver_table = extractor.resolve_table_name(source_table, 'silver', params)
silver_path = extractor.get_full_table_path(silver_table, 'silver', params)
# Result: "main.curated_silver.stg_customers"

# Gold
gold_table = extractor.resolve_table_name(source_table, 'gold', params)
gold_path = extractor.get_full_table_path(gold_table, 'gold', params)
# Result: "main.business_gold.dim_customers"
```

### Use Case 4: Infer Join Conditions from Foreign Keys
```python
schema_service = SchemaMetadataService(tenant_id, project_id)

orders = await schema_service.get_table_schema("asset-orders")
customers = await schema_service.get_table_schema("asset-customers")

join_info = schema_service.infer_join_conditions(orders, customers)

# Result:
# {
#     'left_table': 'Orders',
#     'right_table': 'Customers',
#     'left_column': 'customer_id',
#     'right_column': 'customer_id'
# }

# Use in SQL:
# SELECT * FROM Orders o
# JOIN Customers c ON o.customer_id = c.customer_id
```

### Use Case 5: Get Column Names (Excluding Audit Columns)
```python
schema_service = SchemaMetadataService(tenant_id, project_id)
schema = await schema_service.get_table_schema(asset_id)

# Exclude audit columns (_ingestion_timestamp, _ingestion_date, etc.)
columns = schema_service.get_column_names(schema, exclude_audit=True)

# Result: ["customer_id", "customer_name", "email"]
# (No _ingestion_* columns)
```

---

## 🗂️ Data Structures

### TableSchema
```python
@dataclass
class TableSchema:
    asset_id: str                        # "asset-123"
    table_name: str                      # "Customers"
    columns: List[ColumnMetadata]        # [ColumnMetadata(...), ...]
    primary_key: List[str]               # ["customer_id"]
    foreign_keys: List[ForeignKeyMetadata]  # [ForeignKeyMetadata(...), ...]
    row_count: int                       # 1000000
    sample_data: List[Dict[str, Any]]    # [{...}, {...}]
```

### ColumnMetadata
```python
@dataclass
class ColumnMetadata:
    name: str                  # "customer_id"
    data_type: str             # "int"
    nullable: bool             # False
    is_primary_key: bool       # True
    is_foreign_key: bool       # False
    max_length: Optional[int]  # 100 (for varchar)
    precision: Optional[int]   # 10 (for decimal)
    scale: Optional[int]       # 2 (for decimal)
```

### ForeignKeyMetadata
```python
@dataclass
class ForeignKeyMetadata:
    column: str                # "customer_id"
    ref_table: str             # "Customers"
    ref_column: str            # "customer_id"
    constraint_name: str       # "fk_orders_customers"
```

### ProjectParameters
```python
@dataclass
class ProjectParameters:
    # Paths
    bronze_path: str           # "/mnt/datalake/bronze"
    silver_path: str           # "/mnt/datalake/silver"
    gold_path: str             # "/mnt/datalake/gold"
    
    # Schemas
    bronze_schema: str         # "raw_staging"
    silver_schema: str         # "curated_silver"
    gold_schema: str           # "business_gold"
    
    # Naming
    bronze_prefix: str         # "raw_"
    silver_prefix: str         # "stg_"
    gold_prefix: str           # "dim_" or "fact_"
    bronze_suffix: str         # ""
    silver_suffix: str         # ""
    gold_suffix: str           # ""
    
    # Target
    catalog_name: str          # "main"
    target_tech_stack: str     # "pyspark"
    
    # Mappings
    table_mappings: Dict[str, str]  # {"Customers": "customers"}
```

---

## 📚 API Reference

### SchemaMetadataService

#### Constructor
```python
SchemaMetadataService(tenant_id: str, project_id: str)
```

#### Methods
| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `get_table_schema()` | `asset_id: str` | `TableSchema` | Get schema for asset |
| `get_project_tables()` | None | `List[TableSchema]` | Get all project tables |
| `get_column_names()` | `schema, exclude_audit=True` | `List[str]` | Extract column names |
| `get_column_types_map()` | `schema` | `Dict[str, str]` | Map column -> type |
| `infer_join_conditions()` | `left, right` | `Optional[Dict]` | Infer FK-based joins |
| `clear_cache()` | None | `None` | Clear schema cache |

### ParameterExtractor

#### Constructor
```python
ParameterExtractor(tenant_id: str, project_id: str)
```

#### Methods
| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `extract_parameters()` | `project_id: str` | `ProjectParameters` | Extract config |
| `resolve_table_name()` | `source, layer, params` | `str` | Apply prefix/suffix |
| `get_full_table_path()` | `table, layer, params` | `str` | Build catalog.schema.table |
| `get_file_path()` | `table, layer, params` | `str` | Build /path/to/table |
| `to_dict()` | `params` | `Dict` | Convert to dict |
| `clear_cache()` | None | `None` | Clear params cache |

### TemplateEngine

#### Constructor
```python
TemplateEngine()
```

#### Methods
| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `render_template()` | `template_name, schema, params, layer` | `str` | Render template |

#### Built-in Templates
- `pyspark_bronze` - Bronze layer (ingestion)
- `pyspark_silver` - Silver layer (SCD Type 2)
- `pyspark_gold` - Gold layer (dimension/fact)

---

## 🧪 Testing

### Run All Sprint 9 Tests
```bash
pytest tests/test_sprint9_*.py -v
```

### Run Specific Test Suite
```bash
# Template Engine tests
pytest tests/test_sprint9_template_engine.py -v

# Schema Metadata tests
pytest tests/test_sprint9_schema_metadata.py -v

# Parameter Extractor tests
pytest tests/test_sprint9_parameter_extractor.py -v

# Integration tests
pytest tests/test_sprint9_integration.py -v
```

### Run with Coverage
```bash
pytest tests/test_sprint9_*.py --cov=apps.api.services --cov-report=html
```

---

## 🔧 Configuration

### Database Schema Requirements

#### utm_objects Table
```sql
CREATE TABLE utm_objects (
    object_id UUID PRIMARY KEY,
    project_id UUID,
    source_name TEXT,
    source_tech VARCHAR,
    type VARCHAR,
    metadata JSONB  -- Required structure below
);
```

#### metadata JSONB Structure
```json
{
    "columns": [
        {
            "name": "customer_id",
            "type": "int",
            "nullable": false,
            "maxLength": null,
            "precision": null,
            "scale": null
        }
    ],
    "primaryKey": ["customer_id"],
    "foreignKeys": [
        {
            "name": "fk_constraint_name",
            "column": "customer_id",
            "refTable": "Customers",
            "refColumn": "customer_id"
        }
    ],
    "rowCount": 1000000,
    "sampleData": [
        {"customer_id": 1, "customer_name": "Alice"}
    ]
}
```

#### utm_design_registry Table
```sql
CREATE TABLE utm_design_registry (
    registry_id UUID PRIMARY KEY,
    project_id UUID,
    key TEXT,
    value JSONB
);
```

#### Sample Registry Entries
```sql
-- Paths
INSERT INTO utm_design_registry (project_id, key, value) VALUES
('project-123', 'paths', '{"bronze_path": "/mnt/datalake/bronze", "silver_path": "/mnt/datalake/silver", "gold_path": "/mnt/datalake/gold"}');

-- Schemas
INSERT INTO utm_design_registry (project_id, key, value) VALUES
('project-123', 'schemas', '{"bronze_schema": "raw_staging", "silver_schema": "curated_silver", "gold_schema": "business_gold"}');

-- Naming
INSERT INTO utm_design_registry (project_id, key, value) VALUES
('project-123', 'naming', '{"bronze_prefix": "raw_", "silver_prefix": "stg_", "gold_prefix": "dim_"}');

-- Target
INSERT INTO utm_design_registry (project_id, key, value) VALUES
('project-123', 'target', '{"tech_stack": "pyspark", "catalog_name": "main"}');
```

### Default Values

If `utm_design_registry` is empty, these defaults are used:

```python
DEFAULTS = {
    'bronze_path': '/mnt/datalake/bronze',
    'silver_path': '/mnt/datalake/silver',
    'gold_path': '/mnt/datalake/gold',
    'bronze_schema': 'bronze',
    'silver_schema': 'silver',
    'gold_schema': 'gold',
    'bronze_prefix': 'raw_',
    'silver_prefix': 'stg_',
    'gold_prefix': 'dim_',
    'catalog_name': 'main',
    'database_name': 'datalake',
    'target_tech_stack': 'pyspark',
    'target_dialect': 'spark_sql',
    'source_tech_stack': 'mssql',
    'source_dialect': 'tsql'
}
```

---

## 🐛 Troubleshooting

### Issue: Schema is None
**Symptom:** `schema` returned is `None` when calling `get_table_schema()`

**Causes:**
1. Asset ID doesn't exist in utm_objects
2. utm_objects.metadata is NULL
3. metadata JSONB has invalid structure

**Solution:**
```python
# Check if asset exists
result = db.client.table("utm_objects").select("*").eq("object_id", asset_id).execute()
if not result.data:
    print("Asset not found!")

# Check metadata
if result.data[0]['metadata'] is None:
    print("Metadata is NULL - need to run Sprint 7 profiling")
```

### Issue: Parameters Return Defaults
**Symptom:** `extract_parameters()` returns default values instead of project-specific config

**Causes:**
1. Project ID doesn't have entries in utm_design_registry
2. Registry keys are misspelled ('path' vs 'paths')

**Solution:**
```python
# Check registry
result = db.client.table("utm_design_registry").select("*").eq("project_id", project_id).execute()
if not result.data:
    print("No registry entries - using defaults")
else:
    print(f"Found {len(result.data)} registry entries")
```

### Issue: Template Rendering Fails
**Symptom:** Jinja2 error when rendering template

**Causes:**
1. Invalid template name
2. Schema or params is None
3. Missing required properties

**Solution:**
```python
# Validate inputs before rendering
if schema is None:
    raise ValueError("Schema is required for template rendering")
if params is None:
    raise ValueError("Parameters are required for template rendering")

# Use try-except
try:
    code = await engine.render_template('pyspark_bronze', schema, params, 'bronze')
except Exception as e:
    print(f"Template rendering failed: {e}")
```

### Issue: LLM Doesn't Use Schema/Params
**Symptom:** Generated code still has hardcoded values despite schema + params injection

**Causes:**
1. LLM didn't receive schema context (check prompt)
2. LLM ignores instructions (increase temperature=0)
3. Schema/params not serializable to JSON

**Solution:**
```python
# Enable debug logging to see LLM prompts
import logging
logging.basicConfig(level=logging.DEBUG)

# Check that prompt includes schema + params
# Look for log: "[AgentC Sprint9] ✅ Schema extracted: ..."
```

---

## 💡 Best Practices

### 1. Always Cache Services
```python
# ✅ GOOD: Reuse service instances
schema_service = SchemaMetadataService(tenant_id, project_id)
schema1 = await schema_service.get_table_schema(asset1)
schema2 = await schema_service.get_table_schema(asset2)  # Uses cache

# ❌ BAD: Create new instance each time
schema1 = await SchemaMetadataService(tenant_id, project_id).get_table_schema(asset1)
schema2 = await SchemaMetadataService(tenant_id, project_id).get_table_schema(asset2)
```

### 2. Validate Schema Before Template Rendering
```python
# ✅ GOOD: Check schema validity
schema = await schema_service.get_table_schema(asset_id)
if schema and schema.primary_key:
    code = await engine.render_template('pyspark_silver', schema, params, 'silver')
else:
    # Fallback to bronze (no PK required)
    code = await engine.render_template('pyspark_bronze', schema, params, 'bronze')

# ❌ BAD: Assume schema is valid
code = await engine.render_template('pyspark_silver', schema, params, 'silver')
```

### 3. Use Exclude Audit Columns When Selecting
```python
# ✅ GOOD: Exclude audit columns in business logic
columns = schema_service.get_column_names(schema, exclude_audit=True)
df = df.select(*columns)  # Only business columns

# ❌ BAD: Include audit columns in business logic
columns = schema_service.get_column_names(schema, exclude_audit=False)
df = df.select(*columns)  # Includes _ingestion_timestamp, etc.
```

### 4. Clear Cache When Schema Changes
```python
# If schema changes (e.g., after Sprint 7 re-profiling)
schema_service.clear_cache()
param_extractor.clear_cache()

# Re-extract fresh data
schema = await schema_service.get_table_schema(asset_id)
params = await param_extractor.extract_parameters()
```

---

## 📖 Examples by Layer

### Bronze Layer (Ingestion)
```python
engine = TemplateEngine()
code = await engine.render_template('pyspark_bronze', schema, params, 'bronze')

# Generated code includes:
# - Dynamic source path
# - Dynamic column selection from schema
# - Dynamic target table (catalog.schema.raw_table)
# - Audit columns (_ingestion_timestamp)
```

### Silver Layer (Transformation + SCD Type 2)
```python
engine = TemplateEngine()
code = await engine.render_template('pyspark_silver', schema, params, 'silver')

# Generated code includes:
# - Reads from bronze (dynamic)
# - Deduplication using schema.primary_key
# - Null filtering on PK columns
# - SCD Type 2 merge/upsert
# - Dynamic target table (catalog.schema.stg_table)
```

### Gold Layer (Business)
```python
engine = TemplateEngine()
code = await engine.render_template(
    'pyspark_gold', 
    schema, 
    params, 
    'gold',
    table_type='DIMENSION'  # or 'FACT'
)

# Generated code includes:
# - Reads from silver (dynamic)
# - Business logic based on table_type
# - Dynamic target table (catalog.schema.dim_table or fact_table)
```

---

## 📞 Support

### Questions?
- See full documentation: `SPRINT_9_ZERO_HARDCODE_GENERATION_REPORT.md`
- Run tests: `pytest tests/test_sprint9_*.py -v`

### Debugging
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# You'll see:
# [SchemaMetadataService] Schema extracted: Customers, 5 columns
# [ParameterExtractor] Parameters extracted: catalog=main
# [TemplateEngine] Template rendered: 1200 chars
# [AgentC Sprint9] ✅ Schema extracted
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-11  
**Status:** Production Ready ✅
