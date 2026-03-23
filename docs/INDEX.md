# Documentation Index - Legacy2Lake v4.0

> Last Updated: 2026-03-21
> Architecture Version: v4.0 stabilized
> Status: Production

This index points to the documents that describe the current operating model of the platform. Historical sprint and planning documents remain in the repo, but the files listed here are the ones that should be treated as authoritative for the present state.

## Canonical Docs

- [README](C:\proyectos_dev\UTM\README.md)
- [Introduction](C:\proyectos_dev\UTM\docs\INTRODUCTION.md)
- [Installation](C:\proyectos_dev\UTM\docs\INSTALL.md)
- [Environment Vs Database](C:\proyectos_dev\UTM\docs\ENV_VS_DATABASE.md)
- [Release Notes](C:\proyectos_dev\UTM\docs\RELEASE_NOTES.md)
- [Roles And Onboarding](C:\proyectos_dev\UTM\docs\ROLES_AND_ONBOARDING.md)
- [System Architecture](C:\proyectos_dev\UTM\docs\SYSTEM_ARCHITECTURE.md)
- [AI Infrastructure](C:\proyectos_dev\UTM\docs\technical\ai_infrastructure.md)
- [System Prompts And Agents](C:\proyectos_dev\UTM\docs\technical\system_prompts_and_agents.md)
- [Cartridge Manual](C:\proyectos_dev\UTM\docs\technical\cartridge_manual.md)

## Current Platform Summary

- Prompt source of truth:
  - disk for Level 1 and Level 2
  - DB as runtime mirror
  - project settings for Level 3 optional custom rules
- Active canonical prompt inventory:
  - `48` prompts total
  - `7` agent prompts
  - `1` shared standards prompt
  - `40` cartridge prompts
- Active LLM agent roster:
  - `agent-qa`, `agent-s`, `agent-a`, `agent-c`, `agent-f`, `agent-g`, `agent-d`
- Deterministic engines still active:
  - `agent-p`, `agent-r`, `agent-o`
- Real E2E validation:
  - SSIS fixture executed on `2026-03-21`
  - Azure `gpt-4.1`
  - `Agent A -> Agent C -> Agent F -> Agent G` chain validated

## Core Workflow

1. [Stage 1: Discovery](C:\proyectos_dev\UTM\docs\stages\STAGE_1_DISCOVERY.md)
2. [Stage 2: Triage](C:\proyectos_dev\UTM\docs\stages\STAGE_2_TRIAGE.md)
3. [Stage 3: Drafting](C:\proyectos_dev\UTM\docs\stages\STAGE_3_DRAFTING.md)
4. [Stage 4: Refinement](C:\proyectos_dev\UTM\docs\stages\STAGE_4_REFINEMENT.md)
5. [Stage 5: Certification](C:\proyectos_dev\UTM\docs\stages\STAGE_5_CERTIFICATION.md)
6. [Stage 6: Handover](C:\proyectos_dev\UTM\docs\stages\STAGE_6_HANDOVER.md)

## Planning Material

Planning is intentionally kept small. If you need the current product thinking, use:

- [`docs/planning`](C:\proyectos_dev\UTM\docs\planning)
