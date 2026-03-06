# 🏭 Microsoft Fabric Warehouse SQL Cartridge

**Created:** 2026-03-04
**Status:** Active

## Overview

This cartridge generates **native Fabric Warehouse T-SQL** for all three Medallion layers.
It is **different from the `ms_fabric` cartridge** which generates **PySpark Lakehouse Notebooks**.

| Cartridge | Language | Target | Pattern |
|---|---|---|---|
| `ms_fabric` | PySpark | Fabric Lakehouse | Delta, saveAsTable, V-Order |
| `ms_fabric_sql` | T-SQL (Fabric subset) | Fabric Warehouse | COPY INTO, CTAS, TRUNCATE+INSERT |

## ⚠️ Critical Fabric Warehouse Limitations

| ❌ NOT Supported | ✅ Alternative |
|---|---|
| `MERGE INTO` | `DELETE matched rows + INSERT` |
| `IDENTITY` columns | `ROW_NUMBER() OVER (ORDER BY ...)` |
| `VARCHAR(MAX)` | `VARCHAR(4000)` max |
| `DEFAULT GETDATE()` on columns | Populate via UPDATE/INSERT |
| Recursive CTEs | Iterative logic with temp tables |
| `ALTER TABLE DROP COLUMN` | Recreate the table |
| Multi-row `INSERT VALUES (r1),(r2)` | `INSERT INTO ... SELECT` |
| Materialized Views | Pre-aggregated Gold tables |
| Triggers | Pipeline orchestration |
| Enforced PK/FK/UNIQUE | Declarative only (NOT ENFORCED) |

## Available Prompts

- [bronze_layer.md](bronze_layer.md) — COPY INTO from ADLS Gen2 + UPDATE for audit columns
- [silver_layer.md](silver_layer.md) — DELETE + INSERT upsert pattern (no MERGE)
- [gold_layer.md](gold_layer.md) — TRUNCATE + INSERT star schema, ROW_NUMBER surrogates
