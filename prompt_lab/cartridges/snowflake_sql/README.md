# ❄️ Snowflake SQL Cartridge Prompts

**Created:** 2026-03-04
**Status:** Active

## Overview

This cartridge generates **native Snowflake SQL** for all three Medallion layers.
It is **different from the `snowflake` cartridge** which generates **Snowpark Python** code.

| Cartridge | Language | Pattern |
|---|---|---|
| `snowflake` | Snowpark Python | Session-based, DataFrame API |
| `snowflake_sql` | Native SQL | COPY INTO, MERGE INTO, CTAS |

## Available Prompts

- [bronze_layer.md](bronze_layer.md) — COPY INTO from Stages
- [silver_layer.md](silver_layer.md) — MERGE INTO with deduplication CTEs
- [gold_layer.md](gold_layer.md) — Star Schema CTAS + Dynamic Tables

## Key SQL Patterns

- **Bronze**: `COPY INTO` + `METADATA$FILENAME` + File Formats
- **Silver**: `MERGE INTO` + `ROW_NUMBER()` window dedup + `TRY_TO_*` casting
- **Gold**: `CREATE OR REPLACE TABLE AS` + Sequences + `DIV0()` + `CLUSTER BY`
