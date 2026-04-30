# Release Notes

## Version 4.5.1 - Workspace QA And Operator Visibility Polish - 2026-04-30

### Frontend Workflow Polish

- Restored the full post-Drafting decision experience in `DraftingView.tsx`: when Drafting completes, the user now sees the three post-Drafting paths again, with the persisted selection preselected and the recommended next stage still available as a direct CTA.
- Improved readiness visibility in `ReadinessBadge.tsx`: card-mode readiness now renders an explicit loading state while background computation is still running, instead of silently appearing later.
- Wired `ReportsCatalogModal.tsx` to the real report/export endpoints instead of mock zero-count data. The catalog now exposes Triage analysis PDF, certification/delivery PDF, governance ZIP, and handover ZIP according to stage availability.
- Corrected Governance/Handover sidebar readiness state via `projects.py`, `SidebarHeader.tsx`, and `useSidebarMetrics.ts`: later-stage statuses such as `CERTIFIED`, `GOVERNED`, and `DELIVERED` now resolve to the expected stage and no longer leave the UI stuck on a generic “No data yet” warning.

### Repo Hygiene

- Removed noisy debug `console.log` traces from the sidebar metrics and Drafting sidebar flow touched during this QA pass.
- Updated core documentation timestamps and index links to use repository-relative paths so the docs remain portable when published outside the original local machine.

### Notes

- No schema migration was required for this patch.
- This patch is focused on operator-facing UX and repository readiness for publication after manual QA.

## Version 4.5.0 - Project Intelligence Assistant + Readiness Suite - 2026-04-16

### 1. Project Intelligence Assistant — Chat History Persistence

**New DB tables:** `utm_project_chat_threads` and `utm_project_chat_messages`  
- Every question/answer pair is persisted with `role`, `intent`, `confidence` and `question`/`answer`
- Thread versioning: each triage rerun increments `thread_version` — old context is preserved for audit, new chats go to a new thread
- `ProjectAssistantService` gains: `_get_or_create_thread()`, `_persist_exchange()`, `get_history()`, `clear_history()`, `reset_for_triage_rerun()`
- `chat()` method now persists automatically (non-blocking, does not fail the LLM call)

**New API endpoints:**
- `GET  /projects/{project_id}/assistant/history` — returns conversation pairs for the active thread
- `DELETE /projects/{project_id}/assistant/history` — clears all messages and opens a fresh thread

**Frontend — `ProjectAssistantModal.tsx`:**
- History is loaded from the API on modal open (hydrates the chat window with previous exchanges)
- "Clear History" button (Trash2 icon) calls the DELETE endpoint; disabled when empty or loading
- `RefreshCw` icon replaced with `Trash2` for semantic clarity

**Triage reset hook (`triage.py`):**
- After a project reaches `TRIAGED` status, `reset_for_triage_rerun()` is called automatically
- Injected with full import fallback; errors are logged but never fail the triage run

---

### 2. Traceability Review

**New DB table:** `utm_asset_traceability` (from `v4.5_chat_history_and_traceability.sql`)

**New service: `TraceabilityService`** (`apps/api/services/traceability_service.py`)
- Builds a field-level and table-level traceability map per asset
- Data sources: `utm_asset_columns`, `utm_table_impacts`, `utm_objects`, `utm_code_validations`
- Status classification:
  - `PRESERVED` — exact column/table match found in generated output
  - `INFERRED`  — matched by substring or rename pattern
  - `CHANGED`   — explicit transformation found in `understanding_payload`
  - `UNRESOLVED` — no match in generated output
- Computes overall asset status: `FULLY_MAPPED`, `MAPPED_WITH_CHANGES`, `MOSTLY_MAPPED`, `REQUIRES_REVIEW`, `NO_TARGET_OUTPUT`
- Results cached in `utm_asset_traceability` for fast retrieval

**New API endpoints:**
- `GET /projects/{project_id}/traceability`             — list cached summaries for all assets
- `GET /projects/{project_id}/traceability/{asset_id}` — build (or rebuild) traceability for one asset

**Frontend — `TraceabilityPanel.tsx`:**
- Lists all cached asset statuses with stacked progress bars (preserved/inferred/changed/unresolved)
- Click an asset → slide-out modal with full column and table entry tables
- PII column markers, note tooltips, collapsible section headers
- Real-time recompute on click (always reads latest data)

**GovernanceView.tsx:**
- New sidebar section `"Traceability Review"` (stage 4) with `GitCompare` icon
- Renders `TraceabilityPanel` at `activeSection === 'traceability'`

---

### 3. Gap Workspace (confirmed complete from v4.4 work)

- `GapWorkspace.tsx` was already wired in `GovernanceView.tsx` at `activeSection === 'gaps'`
- No changes needed — DoD item closed

---

### DB Migration

File: `migrations/v4.5_chat_history_and_traceability.sql`

Tables:
- `utm_project_chat_threads` — thread versioning per project
- `utm_project_chat_messages` — per-message persistence with role, intent, question, answer, confidence
- `utm_asset_traceability` — cached traceability map per project + asset (UNIQUE key)

All tables include RLS policies and GRANT statements consistent with prior migrations.

---

### DoD Status

| # | Item | Status |
|---|------|--------|
| 1 | DB migration: chat threads + messages + traceability | ✅ |
| 2 | Backend: history persistence in ProjectAssistantService | ✅ |
| 3 | Backend: GET/DELETE history endpoints | ✅ |
| 4 | Backend: triage rerun resets chat thread | ✅ |
| 5 | Frontend: history load on open + clear history button | ✅ |
| 6 | Backend: TraceabilityService with 4-status classification | ✅ |
| 7 | Backend: traceability router + main.py registration | ✅ |
| 8 | Frontend: TraceabilityPanel + GovernanceView wiring | ✅ |
| 9 | Release Notes v4.5 | ✅ |

---

## Version 4.4.3 - DoD Closure: Frontend Tests + Prompt Reengineering Documentation - 2026-04-15

### Frontend Automated Coverage (DoD Item 1)

- Created `apps/web/app/components/stages/RefinementView.test.tsx` with comprehensive test suite
- 12 test cases covering all three post-drafting modes:
  - `intelligent_reengineering`: Manifest rendering, artifact paths (reengineered/shared|core|publish), consolidation evidence
  - `structured_refinement`: Medallion-layer messaging, Bronze/Silver/Gold metadata
  - `drafting_delivery`: Terminal path validation (no refinement entry)
- Cross-mode consistency tests: Schema viewer mode differentiation, asset loading
- Error handling: Missing mode, API failures, graceful degradation
- Status: ✅ All tests integrated, frontend builds successful (20.0s)

### Prompt Documentation Alignment (DoD Item 2)

- **Agent C (agent_c_interpreter.md)**: Added "Intelligent Reengineering Mode" section
  - Consolidation strategies: shared dimensions, repeated transformations, common ingestion paths
  - Manifest traceability requirements with concrete examples
  - Artifact layout specification and acceptance criteria
  - Pseudo-consolidation warnings (what NOT to do)

- **Agent F (agent_f_critic.md)**: Added "Step 5: Intelligent Reengineering Mode Validation"
  - Consolidation explainability criteria
  - Source traceability validation
  - Business key preservation rules
  - Consolidation count validation (material reduction required)
  - Manifest presence requirement
  - Scoring guidelines: 9-10 (full compliance), 7-8 (incomplete), <7 (rejected)
  - APPROVED and REJECTED examples with rationale

- **Prompt Consistency Validator**: Created `scripts/validate_prompt_consistency.py`
  - Validates all 7 agent prompts for presence and consistency
  - Checks critical keywords, mode references, layer-aware validation
  - Report: 13 passed, 0 errors, 2 non-blocking warnings

### Validation Results

- Backend tests: 5/5 refinement mode strategy tests passing
- Prompt validation: All agents compliant (critical keywords, mode references, validations present)
- Frontend build: ✅ Successful (20.0s, no TypeScript errors)
- Regression suite: 50+ tests passing across refinement, governance, mode strategy

### Status = PRODUCTION STABLE 🚀

---

## Version 4.4.2 - Intelligent Reengineering Artifact Separation And Full Lifecycle Validation - 2026-04-15

### Refinement Artifact Layout

- `intelligent_reengineering` now emits explicit reengineering artifact paths:
  - `reengineered/shared`
  - `reengineered/core`
  - `reengineered/publish`
- architect keeps backward-compatible indexing in legacy `bronze/silver/gold` buckets so existing validators and packaging flows continue to work.

### Consolidation Validation

- added unit validation that executes `ArchitectService.refine_project` with consolidation metadata and verifies:
  - multiple drafted sources are consolidated into one processing unit
  - artifacts are generated under `reengineered/*`
  - manifest contains traceability and `reengineering_summary`

### Full Lifecycle E2E (Workspace)

- executed full cycle for workspace/project `1051e4b0-570d-443a-9412-0430a6ac3040`:
  - Triage
  - Drafting
  - Refinement
  - Governance
  - Handover
- result: `overall_ok=true`
- report: `test_results/e2e_workspace_1051e4b0-570d-443a-9412-0430a6ac3040.json`

## Version 4.4.1 - Drafting Direct Compliance Stabilization - 2026-04-13

### Drafting Compliance Behavior

- Agent F now separates execution-layer metadata from review-layer criteria in Drafting Delivery.
- direct drafting reviews can normalize `REJECTED -> IMPROVED` when code is executable and blockers are non-structural refinement concerns.
- normalization now validates real code signals (read/write/config + literal hardcode checks) instead of relying only on critique wording.

### Direct Zero-Hardcode Enforcement

- direct mode validation now rejects literal defaults inside `config.get(...)` for table/schema/catalog/path keys.
- added helper-assignment hardcode detection for variables like `source_table`, `target_table`, `schema`, and similar aliases.
- preserved cross-tech direct checks for PySpark, Fabric, and AWS Glue direct transpilation paths.

### Drafting Run Outcome

- validated end-to-end drafting run for project `1051e4b0-570d-443a-9412-0430a6ac3040` with final compliance result: 7/7 assets accepted (`APPROVED` or `IMPROVED`).

## Version 4.4.0 - Intelligent Reengineering MVP (Medallion-First) - Released - 2026-04-15

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
