---
tech_id: pyspark
layer: silver
version: 2.1.0
created: 2026-02-10
updated: 2026-04-29
status: active
maintainer: UTM Development Team
---

# PySpark - Silver Layer Generation Prompt

Purpose: generate production-ready, generic Spark 3.x PySpark code for the Silver layer. Silver is the cleansed, deduplicated, conformed zone and must preserve source semantics while adding layer governance.

## Non-Negotiable Output Contract

Return runnable Python code in the JSON `pyspark_code` field. The code must:

1. Start with this exact trace pattern: `# L2L MODERNIZATION TRACE: SILVER - {{asset_name}}`
2. Define `execute_task(spark, config)` as the orchestration entry point.
3. Keep all executable logic inside `execute_task` or helper functions called by it.
4. Never define `main()`, create a SparkSession, execute work at import time, or include sample config dictionaries.
5. Never hardcode catalogs, schemas, table names, paths, prefixes, package filenames, credentials, watermarks, or environment names.
6. Use only config/metadata for names and options: `catalog_name`, `bronze_schema`, `silver_schema`, `source_table_name`, `target_table_name`, `business_keys`, `columns`, `watermark_column`, `watermark_value`, `pii_columns`, `masking_rules`, `table_format`, `write_mode`.
7. Never use a legacy `*.dtsx` filename as a table name. Use `config['source_table_name']` and `config['target_table_name']`.
8. Do not emit unconditional Databricks-only commands (`OPTIMIZE`, `VACUUM`, `ZORDER`, `dbutils`) for generic PySpark. Such operations are allowed only behind explicit config flags.

## Required Header

```python
# ==============================================================================
# L2L MODERNIZATION TRACE: SILVER - {{asset_name}}
# Source Asset: {{source_asset_name}}
# Source Technology: {{source_tech}}
# Target Platform: PySpark Generic
# Medallion Layer: silver
# Component Type: Cleansed Conformed Transformation
# Load Strategy: {{load_strategy}}
# ==============================================================================
```

## Required Code Shape

```python
import logging
from pyspark.sql import functions as F
from pyspark.sql.window import Window

logger = logging.getLogger(__name__)

def _qualified_table(catalog, schema, table):
    return f"{catalog}.{schema}.{table}" if catalog else f"{schema}.{table}"

def execute_task(spark, config):
    catalog = config.get("catalog_name")
    bronze_schema = config["bronze_schema"]
    silver_schema = config["silver_schema"]
    source_table_name = config["source_table_name"]
    target_table_name = config["target_table_name"]
    business_keys = config.get("business_keys", [])
    columns = config.get("columns", [])
    table_format = config.get("table_format", config.get("output_format", "delta"))

    if not business_keys:
        raise ValueError("Silver transformation requires config['business_keys']")

    source_table = _qualified_table(catalog, bronze_schema, source_table_name)
    target_table = _qualified_table(catalog, silver_schema, target_table_name)

    try:
        logger.info("[EXTRACT] Reading Bronze table %s", source_table)
        df_bronze = spark.read.table(source_table)
        bronze_count = df_bronze.count()

        # [TRANSFORM] Keep explicit, traceable projections from metadata when available.
        df_projected = df_bronze
        if columns:
            projected_exprs = []
            for column in columns:
                source_name = column.get("source_name") or column.get("name")
                target_name = column.get("target_name") or source_name
                data_type = column.get("target_type") or column.get("data_type")
                expr = F.col(source_name)
                if data_type:
                    expr = expr.cast(data_type)
                projected_exprs.append(expr.alias(target_name))
            df_projected = df_bronze.select(*projected_exprs)

        for key in business_keys:
            df_projected = df_projected.filter(F.col(key).isNotNull())

        dedup_order_column = config.get("dedup_order_column", "_ingestion_timestamp")
        if dedup_order_column not in df_projected.columns:
            dedup_order_column = business_keys[0]
        window_spec = Window.partitionBy(*business_keys).orderBy(F.col(dedup_order_column).desc_nulls_last())
        df_deduped = (
            df_projected
            .withColumn("_row_number", F.row_number().over(window_spec))
            .filter(F.col("_row_number") == 1)
            .drop("_row_number")
        )

        pii_columns = set(config.get("pii_columns", []))
        masking_rules = config.get("masking_rules", {})
        df_masked = df_deduped
        for column_name in pii_columns:
            if column_name in df_masked.columns:
                rule = masking_rules.get(column_name, "sha2")
                if rule == "redact":
                    df_masked = df_masked.withColumn(column_name, F.lit("REDACTED"))
                else:
                    df_masked = df_masked.withColumn(column_name, F.sha2(F.col(column_name).cast("string"), 256))

        df_silver = (
            df_masked
            .withColumn("_updated_at", F.current_timestamp())
            .withColumn("_is_current", F.lit(True))
            .withColumn("_valid_from", F.current_timestamp())
            .withColumn("_valid_to", F.lit(None).cast("timestamp"))
        )

        logger.info("[TRANSFORM] Bronze rows=%s, deduped rows=%s", bronze_count, df_silver.count())

        # [LOAD] Prefer platform-safe merge when Spark table format supports SQL MERGE; otherwise initialize table.
        if spark.catalog.tableExists(target_table):
            staging_view = config.get("staging_view_name", f"silver_stage_{target_table_name}")
            df_silver.createOrReplaceTempView(staging_view)
            merge_condition = " AND ".join([f"target.{key} = source.{key}" for key in business_keys])
            spark.sql(f"""
                MERGE INTO {target_table} target
                USING {staging_view} source
                ON {merge_condition} AND target._is_current = true
                WHEN MATCHED THEN UPDATE SET target._is_current = false, target._valid_to = current_timestamp(), target._updated_at = current_timestamp()
                WHEN NOT MATCHED THEN INSERT *
            """)
        else:
            df_silver.write.format(table_format).mode("overwrite").option("mergeSchema", "true").saveAsTable(target_table)

        if config.get("run_table_maintenance", False):
            for command in config.get("maintenance_commands", []):
                spark.sql(command)

        silver_count = spark.read.table(target_table).filter(F.col("_is_current") == True).count()
        logger.info("[LOAD] Silver table %s active rows=%s", target_table, silver_count)
        return {"status": "SUCCESS", "bronze_rows": bronze_count, "silver_active_rows": silver_count}
    except Exception:
        logger.exception("Silver transformation failed for %s", target_table_name)
        raise
```

## Quality Requirements

- Include `# [EXTRACT]`, `# [TRANSFORM]`, and `# [LOAD]` comments.
- Use explicit column casts from `config['columns']`; never cast all columns to string.
- Preserve legacy query/filter/watermark semantics when metadata provides them. Do not invent new watermark rules.
- Add Silver governance columns exactly as `_updated_at`, `_is_current`, `_valid_from`, `_valid_to`.
- Apply masking only to configured PII columns. Do not mask unflagged columns.
- Log row counts before and after major steps.
- Return a small status dictionary.
