# Cartridge Developer Manual (Synthesis Layer)

A **Cartridge** is an independent module that translates the Universal Intermediate Representation (IR) into executable source code for a specific platform. It uses **Jinja2** to ensure code is clean, readable, and follows technology-specific best practices.

## 1. Cartridge Structure

Each cartridge resides in `/apps/utm/cartridges/` and follows this structure:

```plaintext
/cartridge_name/
├── manifest.json           # Cartridge metadata
├── mapping/
│   ├── types.json          # Canonical -> Target Type mapping
│   └── functions.json      # Canonical -> Target Function mapping
├── templates/              # Jinja2 Templates
│   ├── base_notebook.j2    # Master file structure
│   ├── op_read.j2          # Reading logic
│   ├── op_join.j2          # Join/Lookup logic
│   └── op_write.j2         # Persistence (MERGE) logic
└── engine.py               # Python logic to process the IR
```

## 2. The Manifest (`manifest.json`)

Defines the cartridge's capabilities:
```json
{
  "cartridge_id": "databricks_lts_13_3",
  "target_tech": "Databricks",
  "version": "1.0.0",
  "supported_operations": ["READ", "TRANSFORM", "JOIN", "FILTER", "WRITE"]
}
```

## 3. Template Development (Jinja2)

Templates allow generated code to look human-written.

**Example: `op_write.j2` (Delta Lake Merge)**
```python
{# Generate a MERGE in Delta Lake #}
(spark.read.table("{{ source_view }}")
  .alias("source")
  .merge(
    spark.read.table("{{ target_table }}").alias("target"),
    "{% for key in primary_keys %}target.{{ key }} = source.{{ key }}{% if not loop.last %} AND {% endif %}{% endfor %}"
  )
  .whenMatchedUpdateAll()
  .whenNotMatchedInsertAll()
  .execute())
```

## 4. The Cartridge Engine (`engine.py`)

The engine inherits from a base class and iterates through IR steps, resolving functions before rendering templates.

## 5. Golden Rules for Cartridge Development

1. **Mandatory Idempotency**: All output cartridges must generate code that can be re-run without duplicating data (prefer `MERGE` over `APPEND`).
2. **Schema Handling**: Include logic for `mergeSchema = true` or explicit schema evolution where applicable.
3. **Traceability Comments**: Include comments indicating which `step_id` generated the block.
4. **Native Optimization**: Implement platform-specific optimizations (like `Z-ORDER` or `CLUSTER BY`) based on IR metadata.
