# Function Registry: Logical Normalization

To ensure Legacy2Lake is truly universal, we do not translate source code to target code directly. We use a normalization step:

1. **Source Agent**: Identifies a legacy function (e.g., `ISNULL` in SSIS).
2. **Kernel Agent**: Maps it to a **Canonical Function** (e.g., `COALESCE`).
3. **Cartridge Agent**: Translates the Canonical function to target syntax (e.g., `F.coalesce` in PySpark).

## 1. Registry Structure

The registry resides in the `UTM_Function_Registry` table and is organized by Domain Modules.

| Module | Canonical (IR) | SSIS (Source) | Databricks (Target) |
| :--- | :--- | :--- | :--- |
| **NULLS** | `COALESCE(a, b)` | `ISNULL(a, b)` | `F.coalesce(a, b)` |
| **DATES** | `CURR_TS()` | `GETDATE()` | `F.current_timestamp()` |
| **TEXT** | `TO_UPPER(s)` | `UPPER(s)` | `F.upper(s)` |

## 2. Expression Engine

The Kernel processes nested expressions recursively.

**Example Transformation:**
- **In**: `UPPER(ISNULL(City, "N/A"))`
- **Normalization**: `TO_UPPER(COALESCE(City, "N/A"))`
- **Resulting IR**:
```json
{
  "op": "TRANSFORM",
  "canonical_expr": {
    "func": "TO_UPPER",
    "args": [
      { "func": "COALESCE", "args": ["City", "'N/A'"] }
    ]
  }
}
```

## 3. Complexity Handling

Some legacy functions (like Fuzzy Lookups) have no direct equivalent in standard SQL/Spark.

- **Complexity Flag**: Records are marked with `requires_manual_mapping = TRUE`.
- **User Fallback**: The original expression is presented in the UI for manual override.
- **UDF Generation**: Cartridges can opt to generate a Custom Function (UDF) to replicate complex behaviors.

## 4. Extending the Registry

To add functions:
1. Identify the source function (e.g., `DATEDIFF`).
2. Check if a Canonical function exists. If not, create one (e.g., `DIFF_TIME`).
3. Add rendering templates for each active cartridge in the `UTM_Function_Registry`.
