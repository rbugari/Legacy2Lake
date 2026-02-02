# Cartridge Developer Manual (Synthesis Layer) - v3.5

A **Cartridge** is an independent module that translates the Universal Intermediate Representation (IR) into executable source code for a specific platform. It uses **Jinja2 templates** to ensure code is clean, readable, and follows technology-specific best practices.

> **v3.5 Update**: 6 production cartridges available, with dynamic knowledge injection from Prompt Laboratory.

## 1. Available Cartridges (v3.5)

### Production-Ready Cartridges

| Cartridge | Target Platform | Output Format | Key Features |
|-----------|----------------|---------------|--------------|
| **DatabricksCartridge** | Databricks/Spark | PySpark Notebooks (`.py`) | Delta Lake, Z-Order, Auto-optimize |
| **SnowflakeCartridge** | Snowflake | SQL Scripts | Tasks, Streams, Clustering |
| **FabricCartridge** | Microsoft Fabric | Notebooks + Pipelines | Lakehouse integration |
| **BigQueryCartridge** | Google BigQuery | SQL Procedures | Partitioned tables, Clustering |
| **RedshiftCartridge** | AWS Redshift | SQL Scripts | Distribution keys, Sort keys |
| **SalesforceCartridge** | Salesforce | Apex Classes | SOQL queries, Bulk API |

### Cartridge Selection Logic

```python
def select_cartridge(target_tech: str):
    cartridge_map = {
        "DATABRICKS": "apps/utm/cartridges/databricks_pyspark",
        "SNOWFLAKE": "apps/utm/cartridges/snowflake_sql",
        "FABRIC": "apps/utm/cartridges/fabric_notebook",
        "BIGQUERY": "apps/utm/cartridges/bigquery_sql",
        "REDSHIFT": "apps/utm/cartridges/redshift_sql",
        "SALESFORCE": "apps/utm/cartridges/salesforce_apex"
    }
    return cartridge_map.get(target_tech)
```

## 2. Cartridge Structure

Each cartridge resides in `/apps/utm/cartridges/` and follows this structure:

```plaintext
/databricks_pyspark/
├── manifest.json           # Cartridge metadata
├── mapping/
│   ├── types.json          # Canonical → PySpark type mapping
│   └── functions.json      # Canonical → PySpark function mapping
├── templates/              # Jinja2 Templates
│   ├── base_notebook.j2    # Master file structure
│   ├── op_read.j2          # Reading logic
│   ├── op_transform.j2     # Transformation logic
│   ├── op_join.j2          # Join/Lookup logic
│   ├── op_aggregate.j2     # Aggregation logic
│   └── op_write.j2         # Persistence (MERGE) logic
└── engine.py               # Python logic to process the IR
```

## 3. The Manifest (`manifest.json`)

Defines the cartridge's capabilities and configuration:

```json
{
  "cartridge_id": "databricks_pyspark_v3",
  "target_tech": "DATABRICKS",
  "version": "3.5.0",
  "description": "PySpark code generation for Databricks with Delta Lake optimization",
  "output_format": "python",
  "file_extension": ".py",
  "supported_operations": [
    "READ",
    "TRANSFORM",
    "JOIN",
    "AGGREGATE",
    "FILTER",
    "WRITE",
    "MERGE"
  ],
  "features": {
    "delta_lake": true,
    "z_order": true,
    "auto_optimize": true,
    "partition_evolution": true,
    "schema_evolution": true
  },
  "medallion_support": {
    "bronze": true,
    "silver": true,
    "gold": true
  }
}
```

## 4. Type Mapping (`mapping/types.json`)

Maps canonical IR types to target platform types:

**Databricks Example**:
```json
{
  "STRING": "StringType()",
  "INTEGER": "IntegerType()",
  "BIGINT": "LongType()",
  "DECIMAL": "DecimalType({precision}, {scale})",
  "DATE": "DateType()",
  "TIMESTAMP": "TimestampType()",
  "BOOLEAN": "BooleanType()",
  "BINARY": "BinaryType()"
}
```

**Snowflake Example**:
```json
{
  "STRING": "VARCHAR",
  "INTEGER": "INTEGER",
  "BIGINT": "BIGINT",
  "DECIMAL": "NUMBER({precision}, {scale})",
  "DATE": "DATE",
  "TIMESTAMP": "TIMESTAMP_NTZ",
  "BOOLEAN": "BOOLEAN",
  "BINARY": "BINARY"
}
```

## 5. Function Mapping (`mapping/functions.json`)

Maps canonical functions to platform-specific implementations:

```json
{
  "CURRENT_DATE": {
    "databricks": "current_date()",
    "snowflake": "CURRENT_DATE()",
    "bigquery": "CURRENT_DATE()"
  },
  "CONCAT": {
    "databricks": "concat({args})",
    "snowflake": "CONCAT({args})",
    "bigquery": "CONCAT({args})"
  },
  "COALESCE": {
    "databricks": "coalesce({args})",
    "snowflake": "COALESCE({args})",
    "bigquery": "COALESCE({args})"
  },
  "SUBSTRING": {
    "databricks": "substring({col}, {start}, {length})",
    "snowflake": "SUBSTRING({col}, {start}, {length})",
    "bigquery": "SUBSTR({col}, {start}, {length})"
  }
}
```

## 6. Template Development (Jinja2)

Templates allow generated code to look human-written and follow platform best practices.

### Example 1: Databricks - Read Operation (`op_read.j2`)

```python
# READ Operation - {{ step_name }}
# Source: {{ source_table }}
# Generated from step_id: {{ step_id }}

df_{{ source_alias }} = (
    spark.read
    .format("delta")
    .table("{{ catalog }}.{{ schema }}.{{ source_table }}")
)

{% if partition_filter %}
# Apply partition filter for optimization
df_{{ source_alias }} = df_{{ source_alias }}.filter(
    col("{{ partition_key }}") >= "{{ partition_start }}"
)
{% endif %}

{% if select_columns %}
# Select only required columns
df_{{ source_alias }} = df_{{ source_alias }}.select(
    {% for col in select_columns %}
    "{{ col }}"{% if not loop.last %},{% endif %}
    {% endfor %}
)
{% endif %}
```

### Example 2: Databricks - MERGE Operation (`op_write.j2`)

```python
# MERGE Operation - {{ step_name }}
# Target: {{ target_table }}
# Generated from step_id: {{ step_id }}

from delta.tables import DeltaTable

# Create or get target Delta table
if not spark.catalog.tableExists("{{ catalog }}.{{ schema }}.{{ target_table }}"):
    # Create table with schema
    df_{{ source_alias }}.limit(0).write \
        .format("delta") \
        .mode("overwrite") \
        {% if partition_keys %}
        .partitionBy({{ partition_keys | tojson }}) \
        {% endif %}
        .saveAsTable("{{ catalog }}.{{ schema }}.{{ target_table }}")

# Perform MERGE (Upsert)
target_table = DeltaTable.forName(spark, "{{ catalog }}.{{ schema }}.{{ target_table }}")

target_table.alias("target").merge(
    df_{{ source_alias }}.alias("source"),
    {% if match_keys %}
    " AND ".join([
        {% for key in match_keys %}
        f"target.{{ key }} = source.{{ key }}"{% if not loop.last %},{% endif %}
        {% endfor %}
    ])
    {% else %}
    "FALSE"  # Force INSERT only if no keys
    {% endif %}
) \
.whenMatchedUpdateAll(
    {% if update_condition %}
    condition="{{ update_condition }}"
    {% endif %}
) \
.whenNotMatchedInsertAll() \
.execute()

{% if optimize_after_write %}
# Optimize Delta table
spark.sql("OPTIMIZE {{ catalog }}.{{ schema }}.{{ target_table }}")
{% if z_order_columns %}
# Z-Order for query performance
spark.sql("OPTIMIZE {{ catalog }}.{{ schema }}.{{ target_table }} ZORDER BY ({{ z_order_columns | join(', ') }})")
{% endif %}
{% endif %}

print(f"✅ Merge completed for {{ target_table }}")
```

### Example 3: Snowflake - MERGE Operation (`op_write.j2`)

```sql
-- MERGE Operation - {{ step_name }}
-- Target: {{ target_table }}
-- Generated from step_id: {{ step_id }}

MERGE INTO {{ database }}.{{ schema }}.{{ target_table }} AS target
USING (
    SELECT 
        {% for col in columns %}
        {{ col.name }}{% if not loop.last %},{% endif %}
        {% endfor %}
    FROM {{ source_view }}
) AS source
ON {% for key in match_keys %}
    target.{{ key }} = source.{{ key }}{% if not loop.last %} AND {% endif %}
{% endfor %}

WHEN MATCHED {% if update_condition %}AND {{ update_condition }}{% endif %} THEN
    UPDATE SET
        {% for col in update_columns %}
        {{ col }} = source.{{ col }}{% if not loop.last %},{% endif %}
        {% endfor %}

WHEN NOT MATCHED THEN
    INSERT (
        {% for col in columns %}
        {{ col.name }}{% if not loop.last %},{% endif %}
        {% endfor %}
    )
    VALUES (
        {% for col in columns %}
        source.{{ col.name }}{% if not loop.last %},{% endif %}
        {% endfor %}
    );

{% if cluster_keys %}
-- Apply clustering for query optimization
ALTER TABLE {{ database }}.{{ schema }}.{{ target_table }} 
    CLUSTER BY ({{ cluster_keys | join(', ') }});
{% endif %}
```

## 7. The Cartridge Engine (`engine.py`)

The engine inherits from `BaseCartridge` and orchestrates IR processing:

```python
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader
import json

class DatabricksCartridge:
    def __init__(self, cartridge_path: str):
        self.cartridge_path = cartridge_path
        self.manifest = self._load_manifest()
        self.type_mapping = self._load_mapping('types.json')
        self.function_mapping = self._load_mapping('functions.json')
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(f"{cartridge_path}/templates"),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def transpile(self, ir_step: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """
        Transpile a single IR step into PySpark code
        """
        step_type = ir_step['step_type']
        operations = ir_step['logical_operations']
        
        code_blocks = []
        
        # Process each operation in the IR
        for op in operations:
            operation_type = op['operation']
            template_name = f"op_{operation_type.lower()}.j2"
            
            # Render template with IR data + metadata
            template = self.jinja_env.get_template(template_name)
            code = template.render(
                **op,  # Operation-specific fields
                **metadata,  # Step metadata (partition keys, PII, etc.)
                step_type=step_type
            )
            code_blocks.append(code)
        
        # Combine all operations
        return "\n\n".join(code_blocks)
    
    def _load_manifest(self) -> Dict:
        with open(f"{self.cartridge_path}/manifest.json") as f:
            return json.load(f)
    
    def _load_mapping(self, filename: str) -> Dict:
        with open(f"{self.cartridge_path}/mapping/{filename}") as f:
            return json.load(f)
```

## 8. Golden Rules for Cartridge Development

### 1. Mandatory Idempotency
All output cartridges must generate code that can be re-run without duplicating data. **Always prefer `MERGE` over `APPEND`**.

**Good** (Idempotent):
```python
# Creates or updates records
target_table.merge(source_df, "id").whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

**Bad** (Non-Idempotent):
```python
# Creates duplicates on re-run
 source_df.write.mode("append").saveAsTable("target")
```

### 2. Schema Evolution
Include logic for handling schema changes gracefully:

```python
.option("mergeSchema", "true")  # Databricks
.option("autoCreateTable", "true")  # BigQuery
```

### 3. Traceability Comments
Include comments indicating which `step_id` generated each block:

```python
# Generated from step_id: a1b2c3d4-5678-90ab-cdef-1234567890ab
# Source IR: utm_logical_steps.logical_operations[2]
```

### 4. Native Platform Optimization
Implement platform-specific features based on IR metadata:

**Databricks**:
- Z-ORDER on high-cardinality columns
- Auto-optimize for small files
- Photon engine compatibility

**Snowflake**:
- Clustering keys on filter columns
- Materialized views for aggregations
- Tasks for orchestration

**BigQuery**:
- Partitioning on DATE columns
- Clustering on filter/join columns
- Table expiration policies

### 5. PII Handling
If `metadata.pii_fields` exists, apply masking:

```python
{% for field in pii_fields %}
.withColumn("{{ field }}", sha2(col("{{ field }}"), 256))  # Hash PII
{% endfor %}
```

## 9. Testing Your Cartridge

```python
# Test script
from apps.utm.cartridges.databricks_pyspark.engine import DatabricksCartridge

# Sample IR
ir_step = {
    "step_id": "test-123",
    "step_type": "DATA_TRANSFORMATION",
    "logical_operations": [
        {
            "operation": "READ",
            "source": "staging.customers",
            "columns": ["customer_id", "name", "email"]
        },
        {
            "operation": "MERGE",
            "target": "dim.customers",
            "match_keys": ["customer_id"]
        }
    ]
}

metadata = {
    "partition_key": "created_date",
    "pii_fields": ["email"],
    "volume": "MEDIUM"
}

# Generate code
cartridge = DatabricksCartridge("apps/utm/cartridges/databricks_pyspark")
code = cartridge.transpile(ir_step, metadata)

print(code)
```

---

> [!TIP]
> **Cartridge Versioning**: Use semantic versioning in `manifest.json`. Breaking template changes require major version bump.

> [!IMPORTANT]
> **Knowledge Injection**: Cartridges receive additional context from `destinations/{tech}/config_v1.json` via Agent C, including dialect-specific best practices.
