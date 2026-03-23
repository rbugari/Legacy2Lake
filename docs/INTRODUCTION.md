# Introduction

> Last Updated: 2026-03-23
> Status: current

Legacy2Lake is a multi-tenant modernization platform for legacy data and ETL assets.

It ingests assets such as:

- SQL
- DDL
- SSIS `.dtsx`
- project manifests
- support files and metadata

It then orchestrates discovery, triage, drafting, refinement, certification, and handover to help teams understand, prioritize, translate, review, and document modernization work.

The workspace experience follows the same model: each phase has its own landing page, main action, and result views.

## What The Product Does

Legacy2Lake is not just a code generator. The product is designed to help teams:

- understand what they actually have
- identify gaps and blockers
- produce migration baselines
- review technical outputs with governance in mind
- generate runbooks and delivery artifacts

## Core Model

The platform currently runs on a staged workflow plus a 3-level prompt model:

1. agent prompt
2. cartridge prompt
3. optional project custom instructions

The canonical prompt source is disk for Levels 1 and 2, while Supabase acts as the runtime mirror.

## Main Agents

LLM agents:

- `agent-qa`
- `agent-s`
- `agent-a`
- `agent-c`
- `agent-f`
- `agent-g`
- `agent-d`

Deterministic engines:

- `agent-p`
- `agent-r`
- `agent-o`

## Current Scope

The current platform supports multiple target families, including:

- Snowflake SQL
- PySpark
- dbt
- MS Fabric variants

It also supports both modernization-style layers and `direct` translation mode where the goal is a faithful baseline rather than redesign.

## Current State

As of `2026-03-21`, the platform has:

- canonical prompt consolidation completed
- active prompt runtime aligned with disk
- real SSIS end-to-end validation completed with Azure `gpt-4.1`

For the current operating model, continue with:

- [README](C:\proyectos_dev\UTM\README.md)
- [Documentation Index](C:\proyectos_dev\UTM\docs\INDEX.md)
- [System Architecture](C:\proyectos_dev\UTM\docs\SYSTEM_ARCHITECTURE.md)
- [System Prompts And Agents](C:\proyectos_dev\UTM\docs\technical\system_prompts_and_agents.md)
