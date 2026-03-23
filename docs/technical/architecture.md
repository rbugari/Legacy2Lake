# Technical Architecture

> Last Updated: 2026-03-23
> Status: Current technical overview

Legacy2Lake is a multi-tenant modernization platform that ingests legacy artifacts, extracts operational logic, and synthesizes modern outputs through a staged orchestration of agent prompts, cartridges, deterministic services, and tenant-scoped LLM routing.

## 1. Runtime Layers

### Ingestion Layer

- reads legacy inputs such as `SQL`, `SSIS .dtsx`, DDL, manifests, and support files
- classifies source and support assets
- builds inventory and discovery metadata

### Analysis Layer

- evaluates project viability
- detects source technology and contextual gaps
- parses schema and dependency hints
- constructs the modernization mesh used by downstream generation

### Synthesis Layer

- resolves the active agent prompt
- resolves the cartridge prompt for the selected target and layer
- appends optional project custom rules
- invokes the tenant-configured LLM
- validates generated output

### Governance Layer

- reviews generated assets
- scores code quality and target compliance
- emits governance audit and runbook artifacts

## 2. Prompt Architecture

The current prompt model is:

1. Level 1 agent prompt
2. Level 2 cartridge prompt
3. Level 3 optional custom project instructions

Source of truth:

- disk for Levels 1 and 2
- Supabase as runtime mirror
- project settings for Level 3

## 3. Agent And Service Roles

### LLM agents

- `agent-qa`
- `agent-s`
- `agent-a`
- `agent-c`
- `agent-f`
- `agent-g`
- `agent-d`

### Deterministic services

- discovery, librarian, topology, validation, profiling, refactoring, ops audit, packaging

## 4. Cartridge Model

Cartridges specialize generation by:

- target technology
- layer

Current supported layers:

- `bronze`
- `silver`
- `gold`
- `direct`

Current active canonical cartridge inventory:

- `40` prompts
- `10` technologies x `4` layers

## 5. LLM Routing

Agents do not use hardcoded models. Runtime model resolution is tenant-scoped through:

- `utm_agent_matrix`
- `utm_model_catalog`
- `utm_provider_vault`

This lets the same prompt stack run against different providers and deployments per tenant.

## 6. Validation Status

The current architecture was validated end-to-end on `2026-03-21` against the SSIS fixture [`tests/fixtures/ssis_test_repo`](C:\proyectos_dev\UTM\tests\fixtures\ssis_test_repo), including:

- viability assessment
- mesh generation
- direct output generation for SQL and PySpark
- code review
- governance runbook generation

## 7. Workspace Navigation

The workspace UX is aligned to the staged runtime model:

- each phase has a dedicated `overview` landing page
- phase transitions do not reuse unrelated sections from previous phases
- the UI remembers the last meaningful subsection inside the same phase
- transient execution actions do not become future landing points

## 8. Recommended References

For the current source of truth, prefer:

- [`README.md`](C:\proyectos_dev\UTM\README.md)
- [`docs/SYSTEM_ARCHITECTURE.md`](C:\proyectos_dev\UTM\docs\SYSTEM_ARCHITECTURE.md)
- [`docs/technical/system_prompts_and_agents.md`](C:\proyectos_dev\UTM\docs\technical\system_prompts_and_agents.md)
- [`docs/technical/cartridge_manual.md`](C:\proyectos_dev\UTM\docs\technical\cartridge_manual.md)
- [`docs/technical/ai_infrastructure.md`](C:\proyectos_dev\UTM\docs\technical\ai_infrastructure.md)
