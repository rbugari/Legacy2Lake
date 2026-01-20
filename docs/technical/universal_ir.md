# Universal Intermediate Representation (IR) Grammar

The **Universal IR** is a data contract that describes logical operations declaratively. Each record in the `UTM_Logical_Step` table contains a JSON object following this grammar.

## 1. Operation Definitions (The Step Schema)

### 1.1 Operation: `READ`
Extracts data from a source.
```json
{
  "type": "READ",
  "source_alias": "src_sales",
  "params": {
    "connection_ref": "DB_CONNECTION_ID",
    "source_object": "Sales.OrderHeader",
    "query": null,
    "schema_discovery": "AUTOMATIC",
    "columns_metadata": [
      {"name": "SalesID", "type": "INTEGER"},
      {"name": "SubTotal", "type": "DECIMAL(18,2)"}
    ]
  }
}
```

### 1.2 Operation: `TRANSFORM`
Modifies or creates columns using logic.
```json
{
  "type": "TRANSFORM",
  "columns": [
    {
      "name": "TotalWithTax",
      "formula": "SubTotal + TaxAmt",
      "canonical_func": "ADD",
      "data_type": "DECIMAL(18,2)",
      "is_new": true
    }
  ]
}
```

### 1.3 Operation: `JOIN`
Joins two data streams (Equivalent to Lookups).
```json
{
  "type": "JOIN",
  "params": {
    "left_source": "src_sales",
    "right_source": "ref_customer",
    "join_type": "LEFT",
    "join_condition": [
      {"left": "CustomerID", "operator": "==", "right": "ID"}
    ],
    "on_missing": {
      "strategy": "ASSIGN_DEFAULT",
      "defaults": {"CustomerKey": -1}
    }
  }
}
```

### 1.4 Operation: `WRITE`
Persists data to the final target.
```json
{
  "type": "WRITE",
  "target": "gold.sales_fact",
  "params": {
    "mode": "MERGE",
    "primary_keys": ["SalesID"],
    "partition_by": ["Year", "Month"]
  }
}
```

## 2. Canonical Data Types

To avoid conflicts between source types (like SSIS `DT_WSTR`) and target types (like Snowflake `VARCHAR`), Legacy2Lake uses these universal types:

| Type | Description |
| :--- | :--- |
| **STRING** | Variable-length character strings. |
| **INTEGER** | 32 or 64-bit integers. |
| **DECIMAL(p,s)** | Fixed-precision numbers. |
| **BOOLEAN** | True/False values. |
| **TIMESTAMP** | Date and full time. |
| **DATE** | Date without time component. |

## 3. Validation Logic

Before saving a step, the Kernel must validate the JSON against a schema to ensure:
1. The `type` field is valid.
2. `source_alias` references in a `JOIN` exist in a previous `READ` step.
3. Formulas use the **Pseudo-SQL** syntax defined in the Function Registry.
