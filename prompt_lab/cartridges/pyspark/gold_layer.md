---
tech_id: pyspark
layer: gold
version: 2.1.0
created: 2026-02-10
updated: 2026-04-29
status: active
maintainer: UTM Development Team
---

# PySpark - Gold Layer Generation Prompt

Purpose: generate production-ready, generic Spark 3.x PySpark code for the Gold layer. Gold is the analytics and presentation layer for facts, dimensions, and aggregates.

## Non-Negotiable Output Contract

Return runnable Python code in the JSON `pyspark_code` field. The code must:

1. Start with this exact trace pattern: `# L2L MODERNIZATION TRACE: GOLD - {{asset_name}}`
2. Define `execute_task(spark, config)` as the orchestration entry point.
3. Keep all executable logic inside `execute_task` or helper functions called by it.
4. Never define `main()`, create a SparkSession, execute work at import time, or include sample config dictionaries.
5. Never hardcode catalogs, schemas, table names, paths, package filenames, dimension tables, fact grain, credentials, or environment names.
6. Use only config/metadata for names and options: `catalog_name`, `silver_schema`, `gold_schema`, `source_table_name`, `target_table_name`, `model_type`, `business_keys`, `dimension_tables`, `fact_measures`, `group_by_cols`, `agg_definitions`, `grain_level`, `table_format`, `write_mode`.
7. Never use a legacy `*.dtsx` filename as a physical table name. Use `config['source_table_name']` and `config['target_table_name']`.
8. Do not emit unconditional Databricks-only commands (`OPTIMIZE`, `VACUUM`, `ZORDER`, `dbutils`) for generic PySpark. Such operations are allowed only behind explicit config flags.
9. Add Gold governance columns exactly as `_aggregated_at` and `_grain_level`.

## Required Header

```python
# ==============================================================================
# L2L MODERNIZATION TRACE: GOLD - {{asset_name}}
# Source Asset: {{source_asset_name}}
# Source Technology: {{source_tech}}
# Target Platform: PySpark Generic
# Medallion Layer: gold
# Component Type: Analytical Model
# Load Strategy: {{load_strategy}}
# ==============================================================================
```

## Required Code Shape

```python
import logging
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)

def _qualified_table(catalog, schema, table):
    return f"{catalog}.{schema}.{table}" if catalog else f"{schema}.{table}"

def _build_aggregations(agg_definitions):
    functions = {
        "sum": F.sum,
        "avg": F.avg,
        "count": F.count,
        "count_distinct": F.countDistinct,
        "min": F.min,
        "max": F.max,
    }
    return [
        functions.get(item.get("func", "sum").lower(), F.sum)(F.col(item["col"])).alias(item.get("alias", item["col"]))
        for item in agg_definitions
    ]

def execute_task(spark, config):
    catalog = config.get("catalog_name")
    silver_schema = config["silver_schema"]
    gold_schema = config["gold_schema"]
    source_table_name = config["source_table_name"]
    target_table_name = config["target_table_name"]
    model_type = config.get("model_type", "FACT").upper()
    table_format = config.get("table_format", config.get("output_format", "delta"))
    write_mode = config.get("write_mode", "overwrite")
    grain_level = config.get("grain_level", model_type.lower())

    source_table = _qualified_table(catalog, silver_schema, source_table_name)
    target_table = _qualified_table(catalog, gold_schema, target_table_name)

    try:
        logger.info("[EXTRACT] Reading Silver table %s", source_table)
        df_source = spark.read.table(source_table)
        if "_is_current" in df_source.columns:
            df_source = df_source.filter(F.col("_is_current") == True)
        source_count = df_source.count()

        # [TRANSFORM] Build the requested Gold model from config and source metadata.
        if model_type == "DIMENSION":
            business_keys = config.get("business_keys", [])
            if not business_keys:
                raise ValueError("Gold DIMENSION requires config['business_keys']")
            sk_column = config.get("sk_column", f"{target_table_name}_sk")
            concat_expr = F.concat_ws("||", *[F.coalesce(F.col(key).cast("string"), F.lit("NULL")) for key in business_keys])
            df_gold = df_source.withColumn(sk_column, F.sha2(concat_expr, 256))
            df_gold = df_gold.withColumn("_is_current", F.lit(True)).withColumn("_valid_from", F.current_timestamp()).withColumn("_valid_to", F.lit(None).cast("timestamp"))
        elif model_type == "FACT":
            df_gold = df_source
            for dim_cfg in config.get("dimension_tables", []):
                dim_table = _qualified_table(catalog, gold_schema, dim_cfg["table"])
                dim_df = spark.read.table(dim_table)
                if "_is_current" in dim_df.columns:
                    dim_df = dim_df.filter(F.col("_is_current") == True)
                dim_df = dim_df.select(F.col(dim_cfg["dim_bk"]), F.col(dim_cfg["sk_col"]))
                df_gold = df_gold.join(dim_df, df_gold[dim_cfg["source_bk"]] == dim_df[dim_cfg["dim_bk"]], "left").drop(dim_cfg["dim_bk"])
            fact_measures = config.get("fact_measures", [])
            group_by_cols = config.get("group_by_cols", [])
            if fact_measures and group_by_cols:
                df_gold = df_gold.groupBy(*[F.col(col_name) for col_name in group_by_cols]).agg(*_build_aggregations(fact_measures))
        elif model_type == "AGGREGATE":
            group_by_cols = config.get("group_by_cols", [])
            agg_definitions = config.get("agg_definitions", [])
            if not group_by_cols or not agg_definitions:
                raise ValueError("Gold AGGREGATE requires group_by_cols and agg_definitions")
            df_gold = df_source.groupBy(*[F.col(col_name) for col_name in group_by_cols]).agg(*_build_aggregations(agg_definitions))
        else:
            raise ValueError(f"Unsupported Gold model_type: {model_type}")

        df_gold = (
            df_gold
            .withColumn("_aggregated_at", F.current_timestamp())
            .withColumn("_grain_level", F.lit(grain_level))
        )

        logger.info("[TRANSFORM] Source rows=%s, Gold rows=%s", source_count, df_gold.count())

        # [LOAD] Gold is normally rebuilt, unless config requests another safe mode.
        df_gold.write.format(table_format).mode(write_mode).option("overwriteSchema", "true").saveAsTable(target_table)

        if config.get("run_table_maintenance", False):
            for command in config.get("maintenance_commands", []):
                spark.sql(command)

        target_count = spark.read.table(target_table).count()
        logger.info("[LOAD] Gold table %s rows=%s", target_table, target_count)
        return {"status": "SUCCESS", "model_type": model_type, "source_rows": source_count, "gold_rows": target_count}
    except Exception:
        logger.exception("Gold transformation failed for %s", target_table_name)
        raise
```

## Model Requirements

- DIMENSION: create a deterministic surrogate key from configured business keys and include SCD-style current validity columns when relevant.
- FACT: resolve configured dimension surrogate keys and compute measures from `fact_measures`; do not merely rename a raw table when measure metadata exists.
- AGGREGATE: require `group_by_cols` and `agg_definitions`, then use `groupBy().agg()`.
- Always add `_aggregated_at` and `_grain_level`.
- Preserve explicit source-derived calculations and mappings when metadata provides them.
- Never cast every column to string.
- Apply platform maintenance only behind explicit config flags.
- Log extract, transform, and load row counts.
