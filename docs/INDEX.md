# Documentation Index - Legacy2Lake v4.4

> Last Updated: 2026-04-15
> Architecture Version: v4.4 (stable)
> Status: Production - v4.4 stable release

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
- Real E2E validations:
  - Drafting validation executed on `2026-04-13` for project `1051e4b0-570d-443a-9412-0430a6ac3040` with 7/7 accepted packages
  - Full lifecycle validation executed on `2026-04-15` for project `1051e4b0-570d-443a-9412-0430a6ac3040` (Triage -> Drafting -> Refinement -> Governance -> Handover)
  - Latest E2E report: `test_results/e2e_workspace_1051e4b0-570d-443a-9412-0430a6ac3040.json`

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
- [`docs/planning/V4_3_POST_DRAFTING_EXECUTION_MODES.md`](C:\proyectos_dev\UTM\docs\planning\V4_3_POST_DRAFTING_EXECUTION_MODES.md)
- [`docs/planning/V4_4_INTELLIGENT_REENGINEERING_MVP.md`](C:\proyectos_dev\UTM\docs\planning\V4_4_INTELLIGENT_REENGINEERING_MVP.md)
- [`docs/planning/V4_5_PROJECT_INTELLIGENCE_ASSISTANT_AND_READINESS_SUITE.md`](C:\proyectos_dev\UTM\docs\planning\V4_5_PROJECT_INTELLIGENCE_ASSISTANT_AND_READINESS_SUITE.md)

## v4.4 Final Implementation Status

✅ **Release Complete** - All Definition of Done items closed:

1. **Intelligent Reengineering Runtime** (Fully Implemented)
   - Mode-aware orchestration branching by `post_drafting_mode`
   - Profiler emits `reengineering_units`, `shared_entities`, `consolidation_candidates`, `common_ingestion_paths`
   - Architect generates reengineering artifacts: `reengineered/shared`, `reengineered/core`, `reengineered/publish`
   - Backward compatibility: legacy `bronze/silver/gold` indexing preserved

2. **Governance & Operator Visibility** (Production-Ready)
   - Mode-aware context in governance reports
   - Manifest summaries in refinement state endpoint
   - Consolidation and traceability signals visible in UI

3. **Frontend Test Coverage** (Automated DoD Item 1)
   - RefinementView.test.tsx: 12 mode-specific test cases
   - Cross-mode validation (intelligent_reengineering, structured_refinement, drafting_delivery)
   - Schema viewer asset loading and error handling

4. **Prompt Documentation Alignment** (Complete DoD Item 2)
   - Agent C: Intelligent Reengineering Mode section with consolidation strategy guidance
   - Agent F: Reengineering validation criteria with scoring examples
   - Prompt consistency validator: All 7 agents validated (0 errors, 13 passed checks)

5. **End-to-End Validation** (Successful)
   - Full lifecycle run: Triage→Drafting→Refinement→Governance→Handover (100% ok)
   - Project: 1051e4b0-570d-443a-9412-0430a6ac3040
   - Drafting: 7/7 assets accepted
   - Governance: Score generated, export ZIP produced

For detailed v4.4 changes, see [RELEASE_NOTES.md](docs/RELEASE_NOTES.md#version-440-intelligent-reengineering-mvp---released---2026-04-15).
