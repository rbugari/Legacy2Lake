# Legacy2Lake Documentation Index (v4.0)

> Version: v4.0.2 Stabilized
> Last Updated: March 21, 2026
> Status: Production, post-GA stabilization completed for canonical prompts and SSIS E2E validation

Legacy2Lake is a multi-tenant data modernization factory that ingests legacy assets such as `SQL`, `SSIS .dtsx`, DDL, manifests, and support files, then orchestrates specialized agents to produce modern outputs such as `Snowflake SQL`, `PySpark`, `dbt`, `MS Fabric`, and related governance artifacts.

## Current State

- Canonical prompt source is now disk for app-governed prompts.
- Runtime prompt source is Supabase, synchronized from disk.
- Project custom rules remain optional and start empty by default.
- The active canonical prompt set is `48` prompts:
  - `7` agent prompts
  - `1` shared standards prompt
  - `40` cartridge prompts (`10` tech stacks x `4` layers: `bronze`, `silver`, `gold`, `direct`)
- Legacy `cartridge_*` prompts were deprecated from the active runtime path.
- End-to-end validation was executed on `March 21, 2026` against the real fixture [`tests/fixtures/ssis_test_repo`](C:\proyectos_dev\UTM\tests\fixtures\ssis_test_repo) using Azure `gpt-4.1`.

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

## What Is New In The Stabilized v4.0 Line

- Canonical prompt catalog introduced and synchronized to DB
- `agent-qa` incorporated into the canonical prompt model
- Agent and cartridge taxonomy normalized
- `Agent C`, `Agent F`, and `Agent G` aligned for multi-target outputs instead of PySpark-first assumptions
- Direct-layer cartridges hardened for parameterization, `L2L DIRECT TRANSLATION` traceability, and no invented enhancements
- Fabric SQL cartridge/generator alignment improved
- End-to-end `Agent A -> Agent C -> Agent F -> Agent G` flow validated on SSIS fixture

## Getting Started

- [Installation Guide](C:\proyectos_dev\UTM\docs\INSTALL.md)
- [Documentation Index](C:\proyectos_dev\UTM\docs\INDEX.md)
- [Introduction](C:\proyectos_dev\UTM\docs\INTRODUCTION.md)
- [Release Notes](C:\proyectos_dev\UTM\docs\RELEASE_NOTES.md)
- [System Architecture](C:\proyectos_dev\UTM\docs\SYSTEM_ARCHITECTURE.md)
- [System Prompts And Agents](C:\proyectos_dev\UTM\docs\technical\system_prompts_and_agents.md)
- [Cartridge Manual](C:\proyectos_dev\UTM\docs\technical\cartridge_manual.md)
- [AI Infrastructure](C:\proyectos_dev\UTM\docs\technical\ai_infrastructure.md)

## Project Lifecycle

1. [Stage 1: Discovery](C:\proyectos_dev\UTM\docs\stages\STAGE_1_DISCOVERY.md)
2. [Stage 2: Triage](C:\proyectos_dev\UTM\docs\stages\STAGE_2_TRIAGE.md)
3. [Stage 3: Drafting](C:\proyectos_dev\UTM\docs\stages\STAGE_3_DRAFTING.md)
4. [Stage 4: Refinement](C:\proyectos_dev\UTM\docs\stages\STAGE_4_REFINEMENT.md)
5. [Stage 5: Certification](C:\proyectos_dev\UTM\docs\stages\STAGE_5_CERTIFICATION.md)
6. [Stage 6: Handover](C:\proyectos_dev\UTM\docs\stages\STAGE_6_HANDOVER.md)

## Notes On Historical Docs

The repository still contains planning and sprint documents under [`docs/planning`](C:\proyectos_dev\UTM\docs\planning). Those are valuable historical artifacts, but they may describe intermediate states that have already been superseded. For the current operating model, prefer:

- [`README.md`](C:\proyectos_dev\UTM\README.md)
- [`docs/INDEX.md`](C:\proyectos_dev\UTM\docs\INDEX.md)
- [`docs/SYSTEM_ARCHITECTURE.md`](C:\proyectos_dev\UTM\docs\SYSTEM_ARCHITECTURE.md)
- [`docs/technical/system_prompts_and_agents.md`](C:\proyectos_dev\UTM\docs\technical\system_prompts_and_agents.md)
- [`docs/technical/cartridge_manual.md`](C:\proyectos_dev\UTM\docs\technical\cartridge_manual.md)
- [`docs/technical/ai_infrastructure.md`](C:\proyectos_dev\UTM\docs\technical\ai_infrastructure.md)
