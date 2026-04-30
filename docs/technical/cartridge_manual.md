# Cartridge Manual (v4.5 Stabilized)

> Last Updated: 2026-04-16
> Status: Current cartridge model

Cartridges are the Level 2 prompts of the platform. They specialize generation for a specific target technology and layer while the agent prompt stays comparatively neutral.

## 1. What A Cartridge Is

A cartridge is not a user-editable prompt and not a runtime-generated document. It is an app-governed artifact that:

- lives canonically on disk
- is synchronized to `utm_prompts`
- is selected by `tech_stack` and `layer`
- provides target-specific generation rules

## 2. Cartridge Layers

Legacy2Lake currently supports four layers:

- `bronze`
- `silver`
- `gold`
- `direct`

The first three align with medallion-style modernization. The `direct` layer exists for faithful 1:1 transpilation when redesign is not desired.

## 3. Active Cartridge Inventory

There are `40` active canonical cartridges:

- `10` technology stacks
- `4` layers each

| Tech Stack | Description |
|---|---|
| `base` | generic fallback rules |
| `pyspark` | PySpark / Spark-style generation |
| `snowflake` | Snowpark or Snowflake-oriented Python patterns |
| `snowflake_sql` | native Snowflake SQL |
| `sf` | Salesforce-oriented patterns |
| `aws` | AWS / Glue-oriented patterns |
| `dbt` | dbt SQL and project conventions |
| `gcp` | BigQuery / GCP-oriented SQL |
| `ms_fabric` | Fabric Lakehouse / PySpark notebooks (added in v4.4) |
| `ms_fabric_sql` | Fabric Warehouse SQL (added in v4.4) |

## 4. Cartridge Resolution

At runtime, the platform resolves a cartridge by:

1. target `tech_stack`
2. requested `layer`
3. optional project custom rules layered afterward

The runtime should not depend on legacy `cartridge_*` identifiers. The normalized prompt ids follow the `agent_c_<layer>_<tech_stack>` pattern.

## 5. Design Rules

### Bronze, Silver, Gold

These layers can express modernization intent such as:

- staging and curation boundaries
- lineage-aware structure
- platform-appropriate optimization
- governance and quality expectations
- consolidation of repeated legacy logic into reusable target assets
- redesign from legacy ETL package choreography into target-native ELT patterns when supported by the evidence

For `intelligent_reengineering` in v4.4, runtime refinement can materialize artifacts using reengineering-specific paths (`reengineered/shared`, `reengineered/core`, `reengineered/publish`) while preserving compatibility indexes expected by legacy downstream consumers.

### Direct

The `direct` layer has stricter constraints:

- preserve source intent closely
- do not invent architectural enhancements
- require clear trace headers
- use runtime parameterization instead of unresolved placeholders
- avoid hardcoded object names
- prefer explicit column mapping when metadata is available
- reject invented literal defaults in configuration access for dynamic object keys (table/schema/catalog/path)

Examples of enhancements that should not be invented in `direct` mode unless the source explicitly requires them:

- SCD2 redesign
- masking logic
- audit columns
- partitioning strategy upgrades
- MERGE-based redesign
- medallion restructuring

## 6. Output Flexibility

Cartridges are expected to support multiple output families depending on target:

- SQL
- Python / PySpark
- dbt SQL
- platform-specific output such as Fabric variants

Future formats such as XML or technology-native artifacts can be added without changing the 3-level prompt model.

## 7. Prompt Governance

Cartridges are application-governed. Tenant users do not edit them directly.

The governance split is:

- Level 1 agent prompt: app-owned
- Level 2 cartridge: app-owned
- Level 3 custom instructions: tenant/project contextual

## 8. Current Validation Status

As of `2026-03-21`, direct cartridges were validated in a real SSIS fixture flow:

- source: `SSIS .dtsx`
- targets tested:
  - `snowflake_sql:direct`
  - `pyspark:direct`
- chain tested:
  - `Agent A`
  - `Agent C`
  - `Agent F`
  - `Agent G`

This validation confirmed:

- prompt assembly works end to end
- direct headers and parameterization are being used
- `Agent F` can approve or improve according to target-specific rules
- `Agent G` can audit and document the generated outputs

## 9. Known Functional Boundaries

Some gaps detected by governance in real validation are not cartridge failures but business/semantic modernization decisions. For example:

- PII masking
- SCD2 implementation
- ingestion metadata
- partitioning strategy

Those may be intentionally absent in `direct` mode and should be handled by selecting a richer modernization layer or by explicitly asking for those behaviors.

For avoidance of doubt: medallion modernization does not mean blindly turning each migrated package into one Bronze, one Silver, and one Gold artifact. The intended use is solution-level redesign guided by shared entities, common business rules, and reusable target assets.
