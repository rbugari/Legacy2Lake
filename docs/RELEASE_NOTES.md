# Release Notes

## Version 4.4.0 - Intelligent Reengineering MVP (Medallion-First) - In Progress - 2026-04-11

### Runtime Strategy

- refinement pipeline now resolves and logs execution mode at runtime
- intelligent reengineering no longer relies only on prompt wording; runtime now branches with explicit mode-aware behavior
- medallion-first contract enforced for v4.4: Bronze/Silver/Gold remains the target architecture

### Consolidation Rules

- consolidation is applied only when multiple drafted packages/files map to the same logical source object
- shared connections alone no longer trigger consolidation
- reengineering metadata now includes explicit consolidation candidates and traceability requirements

### Profiling & Architecting

- profiler emits reengineering-focused fields:
  - `reengineering_units`
  - `shared_entities`
  - `consolidation_candidates`
  - `common_ingestion_paths`
- architect consumes reengineering units but still produces medallion outputs for v4.4 scope
- reengineering manifest now captures objective, execution mode, processing units, and source traceability summary

### Governance & UI Alignment

- governance responses now include `mode_context` to make evaluation intent explicit per post-drafting mode
- governance background logs distinguish medallion consolidation lineage when intelligent reengineering is selected
- refinement state endpoint now exposes `manifest_summary` (manifest name, mode, objective, counts)
- refinement UI surfaces consolidation and manifest traceability signals in overview and status views

### Validation Coverage

- added/expanded tests for v4.4 mode-aware behavior and resilience:
  - governance mode context in cached and generated report flows
  - background governance persistence with mode-aware context
  - manifest summary extraction and fallback behavior
  - invalid manifest payload tolerance
- latest regression block executed successfully with 50 passing tests across refinement, governance, mode strategy, and prompt integration suites

## Version 4.3.0 - Sprint 3: Post-Drafting Execution Modes Vocabulary & Semantics Clarification - 2026-04-10

### Vocabulary & Semantics Clarification

- **Refined Mode Terminology:** Clarified semantic differences between three post-Drafting execution paths:
  - **Drafting Delivery (Terminal Path):** No refinement; direct to Governance for audit and certification
  - **Structured Refinement (Bounded Path):** Multi-layer medallion optimization (Bronze → Silver → Gold) with quality rules and governance compliance
  - **Intelligent Reengineering (Advanced Path):** Architectural improvements and schema redesigns; higher-order transformations acceptable

### Backend Updates

- **Governance Router:** Mode-specific error messages explaining why refinement is blocked (if drafting_delivery) and clarifying next actions
- **Error Responses:** Now include mode context, options, and recommended next steps
- **Mode Validation:** Enhanced error messages distinguish between all three modes and provide clear guidance
- **Agent C Prompt Context:** Added post-drafting mode and strategy guidance directly into transpilation prompt context
- **PromptAssembler Hardening:** Improved placeholder parser and consolidated "missing variable" warnings to reduce log noise while preserving unresolved placeholders safely
- **Context Defaults:** Added resilient aliases (`target_table`, `source_table`, `schema_name`, `output_path`) to reduce false warnings from mixed cartridge templates

### Frontend Updates

- **PostDraftingDecisionGate Component:**
  - All three modes now visible with risk level badges (low/medium)
  - Detailed descriptions, recommendations, and use-case guidance for each mode
  - Cards display: title, description, detailed explanation, recommendation, and risk level
  
- **RefinementView Component:**
  - Mode-aware status summaries (shows "Stage Skipped," "Ready," etc. based on selection)
  - StageHeader reflects selected mode with appropriate subtitle and help text
  - Mode-specific action labels ("Run Refinement" vs "Run Reengineering" vs "Skip to Governance")
  - Refinement status card shows strategy and explanation specific to chosen mode
  - Disabled button with clear messaging when refinement not allowed

### Documentation

- **New Reference:** `docs/VOCABULARY_REFERENCE.md` — Quick reference guide for all three modes with code examples
- **Updated:** `docs/PLANNING/V4_3_SPRINT_3_VOCABULARY_SPECIFICATION.md` — Complete semantic definitions and implementation mapping
- **Updated:** `docs/PLANNING/V4_3_SPRINT_3_IMPLEMENTATION_PLAN.md` — Detailed change log and checklist

### User Impact

- **Clarity:** UI now explicitly shows consequences of each mode choice within the decision gate interface
- **Guidance:** Better understanding of bounded (structured_refinement) vs unrestricted (intelligent_reengineering) optimization strategies
- **Control:** Users see mode-aware status throughout Refinement stage; understand why refinement is blocked or available
- **Handover:** Artifacts now document which execution mode was selected for traceability

### Data Schema

No schema changes. Existing `post_drafting_mode` VARCHAR(50) column with CHECK constraint supports all modes.

### Backward Compatibility

✅ Fully compatible. Existing projects retain their mode selection; new decision gate displays all three options clearly.

### Testing

- **Backend:** Enhanced tests verify mode-specific error messages and governance logic
- **Frontend:** Component tests verify mode-aware rendering and UI state
- **PromptAssembler:** Added focused unit tests for substitution behavior and context default aliases

---

## Version 4.2.0 - Drafting Stability And Prompt/Cache Hardening - 2026-04-06

### Drafting Topology Stability

- fixed SSIS parser compatibility in topology orchestration for mixed parser interfaces
- added a compatibility bridge in topology to support both:
  - legacy metadata parsing (`parse_legacy`) used by DAG component extraction
  - v5 evidence extraction (`parse(file_path, content_bytes)`) with component reconstruction
- resolved `.dtsx` parse runtime failures that were collapsing the DAG to SQL-only assets

### Prompt Resolution Hardening

- normalized `databricks_pyspark` to canonical `pyspark` in prompt tech aliases
- aligned Agent C and Agent F prompt lookup to use normalized target tech values
- improved cartridge prompt resolution for `direct` mode in Databricks/PySpark projects

### Performance And Correctness

- fixed Agent C transpilation cache key collisions when `asset_id` is null
- cache key now includes package/task identity fields (`package_name`, `name`, source path)
- prevents accidental cache reuse across different assets in the same run

### Expected Runtime Impact

- topology now keeps SSIS packages in orchestration instead of silently skipping them due to signature mismatches
- prompt loading for direct PySpark cartridges is more reliable in tenant runtime DB lookups
- compliance outcomes are no longer affected by cross-asset cached developer outputs

## Version 4.0.4 - Sprint v4.0.3 Test Coverage - 2026-03-30

### Testing

- added `tests/test_sprint_v4_0_3.py` with 59 tests covering the v4.0.3 sprint
- fixed `tests/conftest.py`: corrected module paths, UUID headers, and `sample_project` fixture
- validated all tests green: 59 passed, 0 failed

### Test Coverage Added

- `TestDetectStageFromStatus` — status → stage mapping for all 15 known statuses
- `TestCalculateProgressFromLogs` — agent-based progress estimation (A/C/F/G chain)
- `TestExtractCurrentAgent` — active agent extraction from execution logs
- `TestSidebarMetricsEndpoint` — sidebar metrics endpoint for all stages (0–4)
- `TestPhaseLandingLifecycle` — approve and unlock phase transitions
- `TestSidebarSectionsConfig` — navigation config: overview as canonical landing, run-action variants
- `TestStageHelpContent` — Markdown and HTML help files for all 6 stages

### conftest.py Fixes

- corrected Supabase mock patch path (`services.persistence_service` → `apps.api.services.persistence_service`)
- corrected app import (`apps.api.main_refactored` → `apps.api.main`)
- updated `auth_headers` fixture to use valid UUID values
- added `project_id` key to `sample_project` fixture (required by `SupabasePersistence.get_project_metadata`)

## Version 4.0.3 - Phase Landing Consistency And Help Refresh - 2026-03-23

### Workspace Navigation

- added a consistent `overview` landing for each stage in the workspace
- stopped carrying arbitrary subsections across phase changes
- preserved the last useful subsection only inside the same phase
- prevented transient `run-*` actions from becoming sticky landing targets
- aligned phase entry behavior with ready, running, and completed states

### Help And Guidance

- refreshed the stage help guides to reflect the current workflow
- aligned the help content with the real stage actions and views
- switched the stage help modal to consume Markdown as the editable source of truth

### Product UX

- the phase home now acts as the operational entry point for each stage
- users can leave a phase to configure or inspect something and return to a coherent landing point
- sidebar fallback behavior now prefers meaningful sections instead of `quick-info`

## Version 4.0.2 - Prompt Consolidation And SSIS E2E Validation - 2026-03-21

### Prompt Architecture

- consolidated the platform on `disk canonical + DB runtime mirror`
- normalized the active prompt taxonomy
- incorporated `agent_qa_assessment` into the canonical prompt set
- synchronized the active canonical inventory to `48` prompts
- deprecated active legacy `cartridge_*` runtime prompts

### Agent Prompt Alignment

- aligned `Agent A` prompt with the real runtime payload
- aligned `Agent S` prompt with its actual assessment contract
- made `Agent C`, `Agent F`, and `Agent G` less PySpark-centric in the core prompt layer
- clarified `direct` mode behavior to prevent invented enhancements

### Cartridge And Generator Alignment

- strengthened `direct` cartridges for:
  - trace headers
  - parameterization
  - no hardcoded placeholders
  - explicit mapping preference when metadata exists
- improved Fabric SQL generator behavior to better match cartridge guidance

### Runtime Fixes

- improved prompt resolution and override handling
- hardened placeholder validation for valid Python interpolation cases
- improved `Agent G` JSON parsing for fenced responses containing markdown and nested code blocks
- kept `Agent QA` in the same canonical prompt circuit as the rest of the LLM agents

### Validation

Executed real end-to-end validation on `2026-03-21` using:

- fixture: [`tests/fixtures/ssis_test_repo`](C:\proyectos_dev\UTM\tests\fixtures\ssis_test_repo)
- provider: Azure
- model: `gpt-4.1`

Validated chain:

- `Agent A`
- `Agent C`
- `Agent F`
- `Agent G`

Validated outputs:

- `snowflake_sql:direct`
- `pyspark:direct`

Generated reports:

- [`test_results/ssis_fixture_evaluation.json`](C:\proyectos_dev\UTM\test_results\ssis_fixture_evaluation.json)
- [`test_results/ssis_generation_pipeline.json`](C:\proyectos_dev\UTM\test_results\ssis_generation_pipeline.json)

### Current Interpretation

The platform is stable at the orchestration and prompt-assembly level. Remaining findings in governance are mostly semantic modernization decisions for the tested artifact, such as:

- PII masking
- SCD2 logic
- partitioning strategy
- ingestion metadata

Those are not infrastructure failures of the prompt/runtime chain.

## Previous Notes

Earlier v4.0 release and stabilization notes remain available in git history and older planning documents. This file now prioritizes the current stabilized state over the intermediate sprint narrative.
