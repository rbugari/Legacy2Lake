# Legacy2Lake UTM - System Architecture

> Version: v4.0 stabilized
> Last Updated: 2026-03-23
> Status: Production

This document describes the current architecture after the v4.0 prompt consolidation and stabilization work.

## 1. Core Principles

1. Multi-tenancy first
2. DB-backed runtime with disk-backed canonical prompt definitions
3. Agent-centered orchestration
4. Cartridge-based target specialization
5. Clear separation between platform rules and project-specific context

## 2. Prompt Architecture

Legacy2Lake uses a 3-level prompt model:

1. Level 1: agent prompt
2. Level 2: cartridge prompt
3. Level 3: optional project custom instructions

Current source-of-truth model:

- disk is canonical for Level 1 and Level 2
- Supabase is the runtime mirror
- project settings hold Level 3 custom instructions

Current active prompt inventory:

- `48` canonical prompts active in DB
- `7` agent prompts
- `1` shared standards prompt
- `40` cartridge prompts

## 3. Runtime Pipeline

The production flow is organized as:

1. Discovery
2. Triage
3. Drafting
4. Refinement
5. Certification
6. Handover

### Phase Navigation Model

The workspace now follows the staged runtime more explicitly.

Current navigation behavior:

- each phase exposes an `overview` landing page
- entering a new phase lands on that phase home or its closest operational equivalent
- the UI remembers the last meaningful subsection only inside the same phase
- transient execution actions such as `run-*` do not become sticky landing states
- running phases prioritize progress and logs, while completed phases prioritize summary or report views

Important supporting services in that flow include:

- `DiscoveryService`
- `QuickAssessmentService`
- `LibrarianService`
- `TopologyService`
- `PromptService`
- `ValidationService`

## 4. Agent Architecture

### LLM agents

- `agent-qa`
- `agent-s`
- `agent-a`
- `agent-c`
- `agent-f`
- `agent-g`
- `agent-d`

### Deterministic engines

- `agent-p`
- `agent-r`
- `agent-o`

The main validated drafting chain is:

`Agent A -> Agent C -> Agent F -> Agent G`

## 5. Cartridge Architecture

Cartridges define target- and layer-specific behavior for `Agent C` and the downstream review process.

Current cartridge matrix:

- `10` tech stacks
- `4` layers each
- `40` active canonical cartridge prompts

Layers:

- `bronze`
- `silver`
- `gold`
- `direct`

The `direct` layer is intentionally non-redesign-oriented and is used for faithful transliteration cases such as `SSIS -> SQL` or `SSIS -> PySpark`.

## 6. LLM Resolution

LLM configuration is tenant-scoped through:

- `utm_agent_matrix`
- `utm_model_catalog`
- `utm_provider_vault`

Agents do not own hardcoded models. They resolve provider and deployment dynamically for the active tenant.

## 7. Storage And Isolation

- metadata and runtime configuration: Supabase
- prompt runtime mirror: Supabase
- source and generated artifacts: tenant-scoped storage paths
- tenant isolation enforced through persistence and identity layers

## 8. Current Validation Snapshot

On `2026-03-21`, the platform was validated against the real fixture [`tests/fixtures/ssis_test_repo`](C:\proyectos_dev\UTM\tests\fixtures\ssis_test_repo) using Azure `gpt-4.1`.

Validated outcomes:

- `Agent A` generated a usable modernization mesh
- `Agent C` generated valid `snowflake_sql:direct` and `pyspark:direct` artifacts
- `Agent F` reviewed both outputs with target-aware scoring
- `Agent G` generated parsed governance audit plus runbook

Key report artifacts:

- [`test_results/ssis_fixture_evaluation.json`](C:\proyectos_dev\UTM\test_results\ssis_fixture_evaluation.json)
- [`test_results/ssis_generation_pipeline.json`](C:\proyectos_dev\UTM\test_results\ssis_generation_pipeline.json)

## 9. What This Architecture Does Not Assume

- not every project has Level 3 custom instructions
- not every migration should introduce modernization enhancements
- `direct` mode is not equivalent to full medallion redesign
- governance findings such as PII masking or SCD2 gaps may be legitimate outputs of evaluation rather than runtime failures
