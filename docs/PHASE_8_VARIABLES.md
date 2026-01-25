# Phase 8: Variable Injection Framework

## Overview
**Phase 8** enables **environment-agnostic artifact generation** through a centralized variable management system. Instead of hardcoded paths, the generated code uses placeholders that are replaced during deployment.

## The Problem
Traditional migrations produce environment-specific code:
```python
# Hardcoded DEV path
df.write.save("s3://dev-bucket/bronze/customers")
```

**Issues:**
- Requires manual find/replace for PROD
- Risk of deploying with wrong paths
- No audit trail of environment configs

## The Solution: Variable Injection

### Concept
Define once, use everywhere:
```python
# In Project Settings UI
S3_ROOT = "s3://prod-bucket"
ENV = "production"

# Generated Code
df.write.save(f"{S3_ROOT}/bronze/customers")
```

## Implementation

### 1. Variable Registry (UI)
New section in **Project Settings**:

| Variable Name | Value | Description |
|:---|:---|:---|
| `S3_ROOT` | `s3://my-bucket/datalake` | Root storage path |
| `ENV` | `prod` | Environment identifier |
| `DB_SCHEMA` | `analytics_prod` | Target schema |

**Features:**
- Key-value editor
- Auto-uppercase keys
- Validation for reserved names

### 2. Agent C Integration
Updated prompt:
```markdown
## Input
4. **Project Variables**:
    - You may receive a `variables` dictionary
    - **CRITICAL**: Use f-string placeholders instead of hardcoded values
    
Example:
- Instead of: `"s3://bucket/data"`
- Generate: `f"{S3_ROOT}/data"`
```

### 3. Export Manifest
`variables_manifest.json` included in ZIP:
```json
{
  "S3_ROOT": "s3://prod-bucket",
  "ENV": "production",
  "TABLE_PREFIX": "fact_"
}
```

**Handover Team Uses This To:**
- Set environment variables in cluster config
- Update values for different regions
- Maintain consistency across pipelines

## Backend Architecture

### Service: `agent_c_service.py`
```python
# Inject variables into LLM context
context = {
    "variables": node_data.get("variables", {}),
    ...
}

# Agent C receives:
{
    "variables": {
        "S3_ROOT": "s3://bucket",
        "ENV": "prod"
    }
}
```

### Export: `governance_service.py`
```python
async def create_export_bundle(self, project_id):
    # Fetch variables from project settings
    settings = await db.get_project_settings(project_id)
    variables = settings.get("variables", {})
    
    # Add to ZIP
    zip_file.writestr("variables_manifest.json", 
                     json.dumps(variables, indent=2))
```

## Frontend Components

### `VariableEditor.tsx`
Reusable component:
```tsx
interface Variable {
    key: string;
    value: string;
    description?: string;
}

<VariableEditor 
    variables={settings.variables}
    onChange={(vars) => setSettings({...settings, variables: vars})}
/>
```

**Features:**
- Add/Remove rows
- Inline editing
- Auto-formatting (uppercase keys)
- Info tooltips

### `ProjectSettingsPanel.tsx`
Integrates VariableEditor under new section:
```tsx
<div className="bg-gray-50 rounded-2xl p-6">
    <h4>Variables & Environment Parameters</h4>
    <VariableEditor variables={settings.variables || []} />
</div>
```

## Usage Examples

### Example 1: Storage Paths
```python
# Variables defined
S3_BRONZE = "s3://lake/bronze"
S3_SILVER = "s3://lake/silver"

# Generated code
df_raw.write.save(f"{S3_BRONZE}/orders")
df_clean.write.save(f"{S3_SILVER}/orders_enriched")
```

### Example 2: Connection Strings
```python
# Variable
JDBC_URL = "jdbc:sqlserver://prod-sql.database.windows.net"

# Generated code
df = spark.read \
    .format("jdbc") \
    .option("url", f"{JDBC_URL}") \
    .load()
```

### Example 3: Environment Logic
```python
# Variable
ENV = "production"

# Generated code
if ENV == "production":
    enable_monitoring()
```

## Optionality
- **If variables defined**: Agent C uses them
- **If no variables**: Agent C generates standard code
- **Graceful degradation**: Missing variables don't break generation

## Testing
See `test_phase8_variables.py`:
- ✅ Variables passed to Agent C context
- ✅ Manifest included in export
- ✅ Empty case handled gracefully

## Benefits
- **Environment Agnostic**: Same code for DEV/PROD
- **Audit Trail**: Variables logged in manifest
- **Zero Manual Edits**: Deployment team just sets env vars
- **Consistency**: All assets use same naming
