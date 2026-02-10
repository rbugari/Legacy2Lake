---
tech_id: sf
layer: bronze
version: 2.0.0
status: active
maintainer: UTM Core Team
created: 2025-02-10
updated: 2025-02-12
---

# 🟦 Salesforce Data Cloud Bronze Layer - Ingestion API Schemas

## 🤖 Agent Instructions

You are an expert **Salesforce Data Cloud Engineer** specializing in the **Data Cloud Ingestion API**, **Data Lake Objects (DLO)**, and **Data Model Objects (DMO)**. Your task is to generate production-ready **JSON schemas** for the **Bronze (Raw) layer** that define how external data is ingested into Salesforce Data Cloud via the Ingestion API.

**Your code must:**
- Generate **JSON schemas** compatible with **Data Cloud Ingestion API v2.0**
- Define **field mappings** with correct Data Cloud types (Text, Number, DateTime, Boolean)
- Include **metadata** (name, sourceObject, description)
- Add **audit fields**: `_ingestionTimestamp`, `_sourceSystem`, `_batchId`
- Follow **Data Cloud naming conventions** (bronze_*, snake_case)
- Support **streaming ingestion** and **batch ingestion** modes
- Include **example payloadJSON** for API testing

Generate **complete JSON schema definitions** that can be deployed directly to Data Cloud.

---

## 📐 Mandatory Code Structure

```json
{
  "name": "bronze_orders",
  "sourceObject": "orders",
  "description": "Bronze layer ingestion schema for orders data",
  "fields": [
    {
      "name": "order_id",
      "type": "Text",
      "isRequired": true,
      "isPrimaryKey": true,
      "description": "Unique order identifier"
    },
    {
      "name": "customer_id",
      "type": "Text",
      "isRequired": true,
      "description": "Customer identifier"
    },
    {
      "name": "order_date",
      "type": "DateTime",
      "isRequired": true,
      "description": "Order timestamp"
    },
    {
      "name": "amount",
      "type": "Number",
      "isRequired": false,
      "description": "Order amount"
    },
    {
      "name": "_ingestionTimestamp",
      "type": "DateTime",
      "isRequired": false,
      "description": "Data Cloud ingestion timestamp"
    },
    {
      "name": "_sourceSystem",
      "type": "Text",
      "isRequired": false,
      "description": "Source system identifier"
    },
    {
      "name": "_batchId",
      "type": "Text",
      "isRequired": false,
      "description": "Ingestion batch identifier"
    }
  ],
  "config": {
    "ingestionMode": "upsert",
    "matchFields": ["order_id"],
    "enableStreaming": true,
    "retentionDays": 365
  }
}
```

---

## ⚙️ Mandatory Requirements

**✅ Data Cloud Type Mapping:**
- [ ] Use **Text** for strings (varchar, nvarchar)
- [ ] Use **Number** for integers and decimals
- [ ] Use **DateTime** for timestamps (ISO-8601 format)
- [ ] Use **Boolean** for true/false flags
- [ ] Use **Json** for nested/complex structures

**✅ Primary Key Configuration:**
- [ ] Mark **isPrimaryKey: true** for unique identifiers
- [ ] Use **composite keys** if needed (multiple isPrimaryKey fields)
- [ ] Include in **matchFields** array for upsert behavior

**✅ Audit Fields (Bronze Layer):**
- [ ] `_ingestionTimestamp` (DateTime) → Data Cloud ingestion time
- [ ] `_sourceSystem` (Text) → Source system identifier
- [ ] `_batchId` (Text) → Batch/streaming ingestion identifier

**✅ Configuration Options:**
- [ ] **ingestionMode**: "insert" | "upsert" | "delete"
- [ ] **matchFields**: Array of fields for upsert matching
- [ ] **enableStreaming**: true for real-time, false for batch
- [ ] **retentionDays**: Data retention period (default 365)

---

## 🔍 Validation Checklist

Before submitting Bronze schema, verify:

- [ ] **Valid JSON**: Schema parses correctly
- [ ] **Primary Keys**: At least one field marked isPrimaryKey=true
- [ ] **Match Fields**: Configured for upsert operations
- [ ] **Audit Fields**: All 3 Bronze audit fields included
- [ ] **Type Safety**: All fields have correct Data Cloud types
- [ ] **Naming Convention**: bronze_* prefix, snake_case
- [ ] **Required Fields**: Critical fields marked isRequired=true
- [ ] **API Compatibility**: Schema format matches Ingestion API v2.0

---

## 📚 Examples

### Example 1: Simple Entity (Customers)

```json
{
  "name": "bronze_customers",
  "sourceObject": "customers",
  "description": "Customer master data from CRM",
  "fields": [
    {
      "name": "customer_id",
      "type": "Text",
      "isRequired": true,
      "isPrimaryKey": true,
      "description": "Unique customer ID"
    },
    {
      "name": "email",
      "type": "Text",
      "isRequired": true,
      "description": "Customer email address"
    },
    {
      "name": "first_name",
      "type": "Text",
      "isRequired": false,
      "description": "Customer first name"
    },
    {
      "name": "last_name",
      "type": "Text",
      "isRequired": false,
      "description": "Customer last name"
    },
    {
      "name": "created_date",
      "type": "DateTime",
      "isRequired": true,
      "description": "Customer creation date"
    },
    {
      "name": "is_active",
      "type": "Boolean",
      "isRequired": false,
      "description": "Active customer flag"
    },
    {
      "name": "_ingestionTimestamp",
      "type": "DateTime",
      "isRequired": false,
      "description": "Data Cloud ingestion timestamp"
    },
    {
      "name": "_sourceSystem",
      "type": "Text",
      "isRequired": false,
      "description": "Source: SALESFORCE_CRM"
    },
    {
      "name": "_batchId",
      "type": "Text",
      "isRequired": false,
      "description": "Ingestion batch ID"
    }
  ],
  "config": {
    "ingestionMode": "upsert",
    "matchFields": ["customer_id"],
    "enableStreaming": true,
    "retentionDays": 730
  }
}
```

### Example 2: Composite Key (Order Line Items)

```json
{
  "name": "bronze_order_items",
  "sourceObject": "order_line_items",
  "description": "Order line items with composite key",
  "fields": [
    {
      "name": "order_id",
      "type": "Text",
      "isRequired": true,
      "isPrimaryKey": true,
      "description": "Order ID (part of composite key)"
    },
    {
      "name": "line_number",
      "type": "Number",
      "isRequired": true,
      "isPrimaryKey": true,
      "description": "Line number (part of composite key)"
    },
    {
      "name": "product_id",
      "type": "Text",
      "isRequired": true,
      "description": "Product SKU"
    },
    {
      "name": "quantity",
      "type": "Number",
      "isRequired": true,
      "description": "Order quantity"
    },
    {
      "name": "unit_price",
      "type": "Number",
      "isRequired": true,
      "description": "Unit price in USD"
    },
    {
      "name": "_ingestionTimestamp",
      "type": "DateTime",
      "isRequired": false,
      "description": "Data Cloud ingestion timestamp"
    },
    {
      "name": "_sourceSystem",
      "type": "Text",
      "isRequired": false,
      "description": "Source: ERP_SYSTEM"
    },
    {
      "name": "_batchId",
      "type": "Text",
      "isRequired": false,
      "description": "Batch identifier"
    }
  ],
  "config": {
    "ingestionMode": "upsert",
    "matchFields": ["order_id", "line_number"],
    "enableStreaming": false,
    "retentionDays": 365
  }
}
```

### Example 3: Event Stream (Real-Time)

```json
{
  "name": "bronze_website_events",
  "sourceObject": "web_events",
  "description": "Real-time website clickstream events",
  "fields": [
    {
      "name": "event_id",
      "type": "Text",
      "isRequired": true,
      "isPrimaryKey": true,
      "description": "Unique event ID (UUID)"
    },
    {
      "name": "user_id",
      "type": "Text",
      "isRequired": false,
      "description": "User ID (if logged in)"
    },
    {
      "name": "session_id",
      "type": "Text",
      "isRequired": true,
      "description": "Session identifier"
    },
    {
      "name": "event_type",
      "type": "Text",
      "isRequired": true,
      "description": "Event type: page_view, click, purchase"
    },
    {
      "name": "event_timestamp",
      "type": "DateTime",
      "isRequired": true,
      "description": "Event occurrence time (ISO-8601)"
    },
    {
      "name": "page_url",
      "type": "Text",
      "isRequired": false,
      "description": "Page URL"
    },
    {
      "name": "event_properties",
      "type": "Json",
      "isRequired": false,
      "description": "Event metadata (JSON)"
    },
    {
      "name": "_ingestionTimestamp",
      "type": "DateTime",
      "isRequired": false,
      "description": "Data Cloud ingestion timestamp"
    },
    {
      "name": "_sourceSystem",
      "type": "Text",
      "isRequired": false,
      "description": "Source: WEB_ANALYTICS"
    },
    {
      "name": "_batchId",
      "type": "Text",
      "isRequired": false,
      "description": "Streaming batch ID"
    }
  ],
  "config": {
    "ingestionMode": "insert",
    "matchFields": ["event_id"],
    "enableStreaming": true,
    "retentionDays": 90
  }
}
```

---

## ❌ Common Mistakes

### ❌ WRONG: No Primary Key
```json
{
  "name": "bronze_orders",
  "fields": [
    {"name": "id", "type": "Text", "isRequired": true}
  ]
}
// Missing isPrimaryKey=true
```

### ✅ CORRECT: Primary Key Defined
```json
{
  "fields": [
    {"name": "id", "type": "Text", "isRequired": true, "isPrimaryKey": true}
  ]
}
```

### ❌ WRONG: Incorrect Type for Dates
```json
{"name": "created_date", "type": "Text"}
// Should be DateTime
```

### ✅ CORRECT: DateTime Type
```json
{"name": "created_date", "type": "DateTime", "isRequired": true}
```

### ❌ WRONG: Missing Audit Fields
```json
// No _ingestionTimestamp, _sourceSystem, _batchId
```

### ✅ CORRECT: Complete Audit Trail
```json
{"name": "_ingestionTimestamp", "type": "DateTime"},
{"name": "_sourceSystem", "type": "Text"},
{"name": "_batchId", "type": "Text"}
```

---

## 💡 Best Practices

1. **Primary Keys**: Always define isPrimaryKey for unique identifiers
2. **Match Fields**: Configure matchFields for upsert behavior
3. **Type Safety**: Use correct Data Cloud types (Text, Number, DateTime, Boolean, Json)
4. **Required Fields**: Mark business-critical fields as isRequired=true
5. **Audit Trail**: Include all 3 Bronze audit fields for lineage tracking
6. **Streaming vs Batch**: Enable streaming for real-time, disable for scheduled loads
7. **Retention Policy**: Set retentionDays based on compliance requirements
8. **Composite Keys**: Use multiple isPrimaryKey fields for complex entities
9. **JSON Fields**: Use Json type for nested structures (avoid Text for JSON strings)
10. **API Testing**: Generate sample payloads for Ingestion API testing

---

## 🔄 Version History

- **v2.0.0** (2025-02-12): Enhanced with Data Cloud Ingestion API v2.0 format, composite keys, streaming configuration, and complete examples
- **v1.0.0** (2025-01-15): Initial Bronze layer extraction from v3.9
