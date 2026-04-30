# Documentation Index - Legacy2Lake v4.5

> Last Updated: 2026-04-30
> Architecture Version: v4.5 (stable)
> Status: Production - v4.5 stable release with late-April QA polish

This index points to the documents that describe the current operating model of the platform. Historical sprint and planning documents remain in the repo, but the files listed here are the ones that should be treated as authoritative for the present state.

## Canonical Docs

- [README](../README.md)
- [Business Summary v4.0 -> v4.4](BUSINESS_SUMMARY_V4_0_TO_V4_4.md)
- [Introduction](INTRODUCTION.md)
- [Installation](INSTALL.md)
- [Environment Vs Database](ENV_VS_DATABASE.md)
- [Release Notes](RELEASE_NOTES.md)
- [Roles And Onboarding](ROLES_AND_ONBOARDING.md)
- [System Architecture](SYSTEM_ARCHITECTURE.md)
- [AI Infrastructure](technical/ai_infrastructure.md)
- [System Prompts And Agents](technical/system_prompts_and_agents.md)
- [Cartridge Manual](technical/cartridge_manual.md)

## Current Platform Summary

- Prompt source of truth:
  - disk for Level 1 and Level 2
  - DB as runtime mirror
  - project settings for Level 3 optional custom rules
- Active canonical prompt inventory:
  - `48` prompts total
  - `7` agent prompts
  - `1` shared standards prompt
  - `40` cartridge prompts (`10` tech stacks x `4` layers)
- Active LLM agent roster:
  - `agent-qa`, `agent-s`, `agent-a`, `agent-c`, `agent-f`, `agent-g`, `agent-d`
- Deterministic engines still active:
  - `agent-p`, `agent-r`, `agent-o`
- v4.5 services added:
  - `ProjectAssistantService` (chat history persistence with thread versioning per triage rerun)
  - `TraceabilityService` (per-asset field/table mapping with PRESERVED/INFERRED/CHANGED/UNRESOLVED status)
- Real E2E validations:
  - Drafting validation executed on `2026-04-13` for project `1051e4b0-570d-443a-9412-0430a6ac3040` with 7/7 accepted packages
  - Full lifecycle validation executed on `2026-04-15` for project `1051e4b0-570d-443a-9412-0430a6ac3040` (Triage -> Drafting -> Refinement -> Governance(CERTIFIED, score 82) -> Handover)
  - v4.5 chat history + traceability validated and shipped on `2026-04-16`
  - Manual workspace QA polish applied on `2026-04-30` (Drafting recommendation gate, readiness loading clarity, reports catalog wiring, Governance/Handover sidebar status)
  - Latest E2E report: `test_results/e2e_workspace_1051e4b0-570d-443a-9412-0430a6ac3040.json`

## Core Workflow

Note: `Certification` is the terminal output of the `Governance` stage (status `CERTIFIED` with score), not a separate runtime stage. The legacy `STAGE_5_CERTIFICATION.md` file is preserved for the certification artifact contract.

1. [Stage 1: Discovery](stages/STAGE_1_DISCOVERY.md)
2. [Stage 2: Triage](stages/STAGE_2_TRIAGE.md)
3. [Stage 3: Drafting](stages/STAGE_3_DRAFTING.md)
4. [Stage 4: Refinement](stages/STAGE_4_REFINEMENT.md) (skipped when `post_drafting_mode = drafting_delivery`)
5. [Stage 5: Governance + Certification](stages/STAGE_5_CERTIFICATION.md)
6. [Stage 6: Handover](stages/STAGE_6_HANDOVER.md)

## Planning Material

Planning is intentionally kept small. If you need the current product thinking, use:

- [`docs/planning`](planning)
- [`docs/planning/V4_3_POST_DRAFTING_EXECUTION_MODES.md`](planning/V4_3_POST_DRAFTING_EXECUTION_MODES.md)
- [`docs/planning/V4_4_INTELLIGENT_REENGINEERING_MVP.md`](planning/V4_4_INTELLIGENT_REENGINEERING_MVP.md)
- [`docs/planning/V4_5_PROJECT_INTELLIGENCE_ASSISTANT_AND_READINESS_SUITE.md`](planning/V4_5_PROJECT_INTELLIGENCE_ASSISTANT_AND_READINESS_SUITE.md)

## v4.5 Final Implementation Status

Released on `2026-04-16`. See [Release Notes v4.5.0](RELEASE_NOTES.md#version-450---project-intelligence-assistant--readiness-suite---2026-04-16).

1. **Project Intelligence Assistant** - Chat history persisted (`utm_project_chat_threads`, `utm_project_chat_messages`); thread versioning per triage rerun; new endpoints `GET/DELETE /projects/{id}/assistant/history`; `ProjectAssistantModal` hydrates from API.
2. **Traceability Review** - `TraceabilityService` produces field/table mapping with statuses `PRESERVED | INFERRED | CHANGED | UNRESOLVED` and asset-level rollup `FULLY_MAPPED | MAPPED_WITH_CHANGES | MOSTLY_MAPPED | REQUIRES_REVIEW | NO_TARGET_OUTPUT`; `TraceabilityPanel` integrated in `GovernanceView` (sidebar `traceability`).
3. **Gap Workspace** - `GapWorkspace.tsx` wired in `GovernanceView` (closed in v4.4 work).

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
