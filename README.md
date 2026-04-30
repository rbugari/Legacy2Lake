# Legacy2Lake UTM (v4.5)

> Version: v4.5.0 Stabilized
> Last Updated: April 30, 2026
> Status: Production - v4.5 stabilized with late-April QA polish applied

Legacy2Lake is a multi-tenant data modernization factory that ingests legacy assets such as `SQL`, `SSIS .dtsx`, DDL, manifests, and support files, then orchestrates specialized agents to produce modern outputs such as `Snowflake SQL`, `Snowpark`, `PySpark`, `dbt`, `Microsoft Fabric` (Lakehouse and Warehouse), `AWS Glue`, `BigQuery`, and related governance artifacts.

## Current State

- Canonical prompt source is disk for app-governed prompts.
- Runtime prompt source is Supabase, synchronized from disk.
- Project custom rules remain optional and start empty by default.
- The active canonical prompt set is `48` prompts:
  - `7` agent prompts
  - `1` shared standards prompt
  - `40` cartridge prompts (`10` tech stacks x `4` layers: `bronze`, `silver`, `gold`, `direct`)
- Legacy `cartridge_*` prompts were deprecated from the active runtime path.
- Latest validated full lifecycle run executed on `2026-04-15` for project `1051e4b0-570d-443a-9412-0430a6ac3040`: Triage -> Drafting (9/9 succeeded) -> Refinement -> Governance (CERTIFIED, score 82) -> Handover (DELIVERED).
- Late-April manual QA polish restored the automatic post-Drafting mode chooser, added visible readiness loading feedback, wired the Reports Library to real exports, and corrected Governance/Handover sidebar readiness messaging.

## Prompt Model

Legacy2Lake uses a 3-level prompt architecture:

1. Level 1: Agent system prompt
   - Owned by the application
   - Not tenant-editable
2. Level 2: Cartridge prompt
   - Owned by the application
   - Specializes behavior by target technology and layer
   - Not tenant-editable
3. Level 3: Project custom instructions
   - Optional
   - Empty by default
   - Used only for project-specific rules or context that the user knows and the platform cannot infer safely

This means the core system must work correctly with Level 1 plus Level 2 alone. Level 3 is a contextual modifier, not a patch layer for weak prompts.

## Executive Summary v4.0 -> v4.5

### v4.0 (March 2026) - Stabilized GA

- Canonical prompt catalog introduced and synchronized to DB
- `agent-qa` incorporated into the canonical prompt model
- Agent and cartridge taxonomy normalized
- `Agent C`, `Agent F`, and `Agent G` aligned for multi-target outputs instead of PySpark-first assumptions
- Direct-layer cartridges hardened for parameterization, `L2L DIRECT TRANSLATION` traceability, and no invented enhancements
- End-to-end `Agent A -> Agent C -> Agent F -> Agent G` chain validated on SSIS fixture

### v4.1 / v4.2 - Drafting And Topology Hardening

- SSIS parser compatibility bridge for legacy and v5 evidence extraction
- Prompt resolution hardening (`databricks_pyspark` normalized to `pyspark`)
- Drafting topology stability fixes against mixed parser interfaces

### v4.3 - Post-Drafting Execution Modes

- Three execution modes formalized at runtime:
  - `drafting_delivery`: terminal path, direct to Governance (no Refinement)
  - `structured_refinement`: bounded medallion optimization (Bronze -> Silver -> Gold)
  - `intelligent_reengineering`: project-scoped consolidation and redesign with traceability
- Mode-aware UI in `PostDraftingDecisionGate` and `RefinementView`
- Mode-specific governance error responses with next-step guidance

### v4.4 - Intelligent Reengineering MVP + Microsoft Fabric

- `ms_fabric` (Lakehouse / PySpark) and `ms_fabric_sql` (Warehouse) cartridges added across all four layers
- Cartridge matrix covers `10` tech stacks x `4` layers = `40` cartridges (`ms_fabric` and `ms_fabric_sql` added in v4.4)
- Refinement pipeline runtime branching by `post_drafting_mode`
- Profiler emits `reengineering_units`, `shared_entities`, `consolidation_candidates`, `common_ingestion_paths`
- Architect emits reengineering artifact paths (`reengineered/shared|core|publish`) while preserving medallion compatibility
- Drafting Direct compliance stabilization: zero-hardcode validation in `config.get(...)` and helper assignments

### v4.5 - Project Intelligence Assistant + Readiness Suite (current)

- **Project Intelligence Assistant**: chat persistence with thread versioning per triage rerun (`utm_project_chat_threads`, `utm_project_chat_messages`); `ProjectAssistantService` exposes `get_history`, `clear_history`, `reset_for_triage_rerun`; new endpoints `GET/DELETE /projects/{id}/assistant/history`; UI hydration in `ProjectAssistantModal`.
- **Traceability Review**: new `TraceabilityService` and `utm_asset_traceability` table; field-level and table-level mapping with statuses `PRESERVED | INFERRED | CHANGED | UNRESOLVED`; new endpoints `GET /projects/{id}/traceability` and `GET /projects/{id}/traceability/{asset_id}`; new `TraceabilityPanel` integrated into `GovernanceView`.
- **Gap Workspace**: `GapWorkspace.tsx` wired in `GovernanceView` for explicit gap lifecycle.

## Supported Inputs And Outputs

### Inputs

- `SQL` and `DDL` files
- `SSIS .dtsx` packages
- Project manifests
- Support files (column dictionaries, business rules, sample data)

### Output Targets (cartridge matrix)

| Tech Stack | Family | Bronze | Silver | Gold | Direct |
|---|---|---|---|---|---|
| `base` | fallback | yes | yes | yes | yes |
| `pyspark` | Spark / Delta | yes | yes | yes | yes |
| `snowflake` | Snowpark Python | yes | yes | yes | yes |
| `snowflake_sql` | native Snowflake SQL | yes | yes | yes | yes |
| `dbt` | dbt SQL projects | yes | yes | yes | yes |
| `aws` | AWS Glue / S3 | yes | yes | yes | yes |
| `gcp` | BigQuery SQL | yes | yes | yes | yes |
| `sf` | Salesforce-oriented | yes | yes | yes | yes |
| `ms_fabric` | Fabric Lakehouse PySpark | yes | yes | yes | yes |
| `ms_fabric_sql` | Fabric Warehouse SQL | yes | yes | yes | yes |

Plus governance and handover artifacts: audit JSON, runbook markdown, certification reports, ZIP delivery package.

## Lifecycle Stages

The runtime is staged. `Certification` is the terminal output of the `Governance` stage (artifact: `CERTIFIED` status with score), not a separate stage.

1. [Stage 1: Discovery](docs/stages/STAGE_1_DISCOVERY.md)
2. [Stage 2: Triage](docs/stages/STAGE_2_TRIAGE.md)
3. [Stage 3: Drafting](docs/stages/STAGE_3_DRAFTING.md)
4. [Stage 4: Refinement](docs/stages/STAGE_4_REFINEMENT.md) (skipped when `post_drafting_mode = drafting_delivery`)
5. [Stage 5: Governance + Certification](docs/stages/STAGE_5_CERTIFICATION.md)
6. [Stage 6: Handover](docs/stages/STAGE_6_HANDOVER.md)

## Getting Started

- [Installation Guide](docs/INSTALL.md)
- [Documentation Index](docs/INDEX.md)
- [Introduction](docs/INTRODUCTION.md)
- [Release Notes](docs/RELEASE_NOTES.md)
- [System Architecture](docs/SYSTEM_ARCHITECTURE.md)
- [System Prompts And Agents](docs/technical/system_prompts_and_agents.md)
- [Cartridge Manual](docs/technical/cartridge_manual.md)
- [AI Infrastructure](docs/technical/ai_infrastructure.md)
- [Business Summary v4.0 -> v4.4](docs/BUSINESS_SUMMARY_V4_0_TO_V4_4.md)

## Notes On Historical Docs

The repository still contains planning and sprint documents under [`docs/planning`](docs/planning). Those are valuable historical artifacts, but they may describe intermediate states that have already been superseded. For the current operating model, prefer:

- [README.md](README.md)
- [docs/INDEX.md](docs/INDEX.md)
- [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)
- [docs/technical/system_prompts_and_agents.md](docs/technical/system_prompts_and_agents.md)
- [docs/technical/cartridge_manual.md](docs/technical/cartridge_manual.md)
- [docs/technical/ai_infrastructure.md](docs/technical/ai_infrastructure.md)
