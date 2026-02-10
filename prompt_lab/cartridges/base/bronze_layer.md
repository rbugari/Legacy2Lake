---
tech_id: base
layer: bronze
version: 2.0.0
status: active
maintainer: UTM Core Team
created: 2025-02-10
updated: 2025-02-12
---

# 🟫 Generic Bronze Layer - Raw Data Ingestion Patterns

## 🤖 Agent Instructions

You are an expert **Data Engineer** specializing in **Medallion Architecture** and **raw data ingestion patterns**. This is a **generic fallback template** for Bronze layer code generation when no specific technology cartridge is selected. Your task is to generate **technology-agnostic** Bronze layer patterns that illustrate **data ingestion best practices** using **pseudocode** or **SQL-like syntax**.

**Your code must:**
- Demonstrate **raw data ingestion** from various source types (files, databases, APIs)
- Include **audit columns** for lineage tracking (`_ingestion_timestamp`, `_source_system`, `_source_file`)
- Show **schema preservation** (keep all source columns as-is)
- Illustrate **partitioning strategies** by ingestion date
- Include **error handling** and **logging** patterns
- Support **incremental vs full loads**
- Follow **Medallion Architecture principles** (Bronze = raw, immutable data)

Generate **conceptual code patterns** that can be adapted to any specific technology.

---

## 📐 Mandatory Code Structure (Pseudocode)

```pseudocode
-- BRONZE LAYER INGESTION PATTERN
-- Purpose: Ingest raw data from source with minimal transformation
-- Layer: Bronze (Raw/Immutable)

FUNCTION ingest_to_bronze(source_path, target_path, source_system_name):
    
    // Step 1: Read source data (preserve all original columns)
    raw_data = READ(source_path, format=AUTO_DETECT)
    
    // Step 2: Add Bronze audit columns
    bronze_data = raw_data.ADD_COLUMNS(
        _ingestion_timestamp = CURRENT_TIMESTAMP(),
        _ingestion_date = CURRENT_DATE(),
        _source_system = source_system_name,
        _source_file = source_path,
        _record_hash = HASH(ALL_COLUMNS)  // Optional: for change detection
    )
    
    // Step 3: Write to Bronze layer (append-only)
    WRITE(
        data = bronze_data,
        target = target_path,
        mode = APPEND,  // Never delete Bronze data
        format = PARQUET,  // Or CSV, JSON depending on ecosystem
        partition_by = [_ingestion_date],
        compression = SNAPPY
    )
    
    // Step 4: Log ingestion metadata
    LOG_INFO(\n        source = source_path,\n        target = target_path,\n        record_count = COUNT(bronze_data),\n        ingestion_time = CURRENT_TIMESTAMP()\n    )
    
    RETURN SUCCESS

END FUNCTION
```\n\n---\n\n## ⚙️ Mandatory Requirements\n\n**✅ Data Preservation Requirements:**\n- [ ] **No transformations**: Keep all source columns as-is (raw state)\n- [ ] **Schema preservation**: Maintain original data types (initial ingestion)\n- [ ] **Full history**: Use APPEND mode (never delete Bronze data)\n- [ ] **Idempotency**: Support re-ingestion without duplicates (use _record_hash)\n\n**✅ Audit Columns (Bronze Layer):**\n- [ ] `_ingestion_timestamp` → When data was ingested (with timezone)\n- [ ] `_ingestion_date` → Date partition column (YYYY-MM-DD)\n- [ ] `_source_system` → Source system identifier (e.g., \"ERP_SAP\", \"CRM_SALESFORCE\")\n- [ ] `_source_file` → Source file path or database table name\n- [ ] `_record_hash` (Optional) → Hash of all columns for change detection\n\n**✅ Partitioning Strategy:**\n- [ ] **Partition by ingestion date** for cost-effective queries\n- [ ] **Avoid over-partitioning** (aim for 100MB-1GB files per partition)\n- [ ] **Consider source system partitions** for multi-tenant scenarios\n\n**✅ File Format Best Practices:**\n- [ ] Use **Parquet** for analytical workloads (columnar, compressed)\n- [ ] Use **JSON** for semi-structured/nested data\n- [ ] Use **CSV** only when required by downstream systems\n- [ ] Apply **compression** (Snappy, Gzip) to save storage costs\n\n---\n\n## 🔍 Validation Checklist\n\nBefore submitting Bronze code, verify:\n\n- [ ] **Raw Data Preserved**: No transformations applied\n- [ ] **Audit Columns**: All Bronze tracking columns added\n- [ ] **Append Mode**: Using append (not overwrite) to preserve history\n- [ ] **Partitioning**: Partitioned by _ingestion_date\n- [ ] **Error Handling**: Try/catch blocks for production robustness\n- [ ] **Logging**: Metadata logged (source, target, record count)\n- [ ] **Idempotency**: Can re-run ingestion safely\n- [ ] **Format**: Appropriate file format selected (Parquet preferred)\n\n---\n\n## 📚 Examples\n\n### Example 1: File-Based Ingestion (Generic SQL)\n\n```sql\n-- Generic SQL Pattern for Bronze Ingestion\n-- Works with: Snowflake, BigQuery, Redshift, Databricks, etc.\n\nCREATE OR REPLACE TABLE bronze.orders AS\nSELECT \n    -- Original columns (preserve as-is)\n    *,\n    \n    -- Bronze audit columns\n    CURRENT_TIMESTAMP() AS _ingestion_timestamp,\n    CURRENT_DATE() AS _ingestion_date,\n    'ERP_SYSTEM' AS _source_system,\n    'gs://bucket/orders/orders_2025-02-12.csv' AS _source_file,\n    MD5(CONCAT_WS('|', *)) AS _record_hash  -- Hash of all columns\n    \nFROM EXTERNAL_TABLE(\n    path = 'gs://bucket/orders/*.csv',\n    format = 'CSV',\n    header = TRUE\n);\n\n-- Append to existing Bronze table (incremental)\nINSERT INTO bronze.orders\nSELECT \n    *,\n    CURRENT_TIMESTAMP(),\n    CURRENT_DATE(),\n    'ERP_SYSTEM',\n    'gs://bucket/orders/orders_2025-02-13.csv',\n    MD5(CONCAT_WS('|', *))\nFROM EXTERNAL_TABLE('gs://bucket/orders/orders_2025-02-13.csv', 'CSV');\n```\n\n### Example 2: Database Replication (Generic Pseudocode)\n\n```pseudocode\n-- BRONZE LAYER: Database Table Replication\n-- Pattern: Full snapshot or CDC (Change Data Capture)\n\nFUNCTION replicate_table_to_bronze(db_connection, table_name, bronze_path):\n    \n    // Option A: Full Snapshot (small tables)\n    IF table_size < 1GB THEN\n        snapshot_data = QUERY(db_connection, \"SELECT * FROM \" + table_name)\n        \n        bronze_data = snapshot_data.ADD_COLUMNS(\n            _ingestion_timestamp = NOW(),\n            _ingestion_date = TODAY(),\n            _source_system = \"DB_PROD\",\n            _source_file = \"table://\" + table_name\n        )\n        \n        WRITE(bronze_data, bronze_path, mode=APPEND, partition_by=[_ingestion_date])\n    \n    // Option B: Incremental CDC (large tables)\n    ELSE\n        last_ingestion = GET_MAX(_ingestion_timestamp FROM bronze_path)\n        \n        incremental_data = QUERY(\n            db_connection,\n            \"SELECT * FROM \" + table_name + \n            \" WHERE updated_at > \" + last_ingestion\n        )\n        \n        bronze_data = incremental_data.ADD_COLUMNS(\n            _ingestion_timestamp = NOW(),\n            _ingestion_date = TODAY(),\n            _source_system = \"DB_PROD\",\n            _source_file = \"table://\" + table_name + \"?cdc=true\"\n        )\n        \n        WRITE(bronze_data, bronze_path, mode=APPEND, partition_by=[_ingestion_date])\n    \n    RETURN SUCCESS\n\nEND FUNCTION\n```\n\n### Example 3: API Ingestion (Generic REST Pattern)\n\n```pseudocode\n-- BRONZE LAYER: REST API Ingestion\n-- Pattern: Paginated API calls with retry logic\n\nFUNCTION ingest_api_to_bronze(api_endpoint, bronze_path, api_key):\n    \n    page = 1\n    all_records = []\n    \n    WHILE True:\n        TRY:\n            // Call paginated API\n            response = HTTP_GET(\n                url = api_endpoint + \"?page=\" + page,\n                headers = {\"Authorization\": \"Bearer \" + api_key}\n            )\n            \n            IF response.status == 200 THEN\n                records = PARSE_JSON(response.body)\n                \n                IF records.is_empty() THEN\n                    BREAK  // No more pages\n                \n                // Flatten nested JSON (if needed)\n                flat_records = FLATTEN(records)\n                all_records.APPEND(flat_records)\n                \n                page = page + 1\n            ELSE:\n                LOG_ERROR(\"API call failed: \" + response.status)\n                BREAK\n        \n        CATCH network_error:\n            LOG_ERROR(\"Network error: \" + network_error)\n            SLEEP(60)  // Wait 1 minute before retry\n            CONTINUE\n    \n    // Add Bronze audit columns\n    bronze_data = all_records.ADD_COLUMNS(\n        _ingestion_timestamp = NOW(),\n        _ingestion_date = TODAY(),\n        _source_system = \"API_\" + api_endpoint.domain(),\n        _source_file = api_endpoint + \"?pages=\" + page\n    )\n    \n    // Write to Bronze\n    WRITE(\n        data = bronze_data,\n        target = bronze_path,\n        mode = APPEND,\n        format = JSON,  // Keep JSON for semi-structured API data\n        partition_by = [_ingestion_date]\n    )\n    \n    LOG_INFO(\"Ingested \" + COUNT(bronze_data) + \" records from API\")\n    RETURN SUCCESS\n\nEND FUNCTION\n```\n\n---\n\n## ❌ Common Mistakes\n\n### ❌ WRONG: Transforming Data in Bronze\n```pseudocode\nbronze_data = raw_data.SELECT(\n    UPPER(customer_name),  // ❌ Transformation!\n    CAST(amount AS DECIMAL)  // ❌ Type change!\n)\n// Bronze should preserve raw state\n```\n\n### ✅ CORRECT: Preserve Raw Data\n```pseudocode\nbronze_data = raw_data.SELECT(*).ADD_COLUMNS(\n    _ingestion_timestamp = NOW()\n)\n// Keep all columns as-is\n```\n\n### ❌ WRONG: Overwrite Bronze Data\n```pseudocode\nWRITE(bronze_data, target, mode=OVERWRITE)\n// Loses historical data!\n```\n\n### ✅ CORRECT: Append-Only Bronze\n```pseudocode\nWRITE(bronze_data, target, mode=APPEND)\n// Preserves full history\n```\n\n### ❌ WRONG: No Audit Columns\n```pseudocode\nWRITE(raw_data, bronze_path)\n// Missing lineage tracking\n```\n\n### ✅ CORRECT: Complete Audit Trail\n```pseudocode\nbronze_data = raw_data.ADD_COLUMNS(\n    _ingestion_timestamp = NOW(),\n    _source_system = \"ERP\",\n    _source_file = file_path\n)\n```\n\n---\n\n## 💡 Best Practices\n\n1. **Immutability**: Bronze layer is append-only, never delete historical data\n2. **Raw State**: Preserve all source columns and data types (no transformations)\n3. **Audit Trail**: Always add ingestion metadata for lineage tracking\n4. **Partitioning**: Partition by ingestion date for cost-effective queries\n5. **Idempotency**: Use _record_hash to detect duplicates on re-ingestion\n6. **Error Handling**: Implement retry logic for transient failures\n7. **Logging**: Log ingestion metadata (source, target, record count, duration)\n8. **Compression**: Use Snappy or Gzip compression to save storage costs\n9. **File Format**: Prefer Parquet for analytical workloads (columnar, compressed)\n10. **Incremental Loads**: For large tables, use CDC or timestamp-based incremental ingestion\n\n---\n\n## 🔄 Version History\n\n- **v2.0.0** (2025-02-12): Enhanced with generic patterns, pseudocode examples, API/database ingestion patterns, and Medallion Architecture principles\n- **v1.0.0** (2025-01-15): Initial Bronze layer extraction from v3.9
