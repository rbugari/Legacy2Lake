# v4.4 Plan - Intelligent Reengineering MVP

> Last Updated: 2026-04-10
> Status: Ready to execute
> Scope: Backend + Frontend + Prompt alignment + Governance
> Constraint: project-scoped only, no cross-project or cross-tenant consolidation

## 1. Why v4.4 Exists

v4.3 introduced the correct product contract:

1. Drafting can be a valid delivery endpoint.
2. Structured Refinement is a bounded modernization path.
3. Intelligent Reengineering is a separate, higher-value path.

What v4.3 did not finish is the runtime separation behind that third path.

Today, the system accepts `intelligent_reengineering` as a valid user choice in UI, persistence, governance eligibility, and prompt guidance. However, once refinement starts, both refinement-capable modes still fall into the same orchestration pipeline and the same medallion-first architecture flow.

That means the product contract is ahead of the implementation. v4.4 closes that gap.

## 2. Current Gap

The current runtime behavior is effectively:

- `drafting_delivery`: blocked from refinement and sent to Governance
- `structured_refinement`: runs the existing profiler -> architect -> refactor -> ops audit pipeline
- `intelligent_reengineering`: runs the same pipeline with stronger wording, but without a distinct orchestration strategy

The missing behavior for `intelligent_reengineering` is:

- project-wide consolidation strategy instead of medallion-only restructuring
- reusable target-native ELT asset design across drafted outputs
- explicit detection of shared entities, repeated transformations, and common ingestion patterns
- audit criteria that reward architectural lift without losing traceability

## 3. v4.4 Objective

Ship the first real runtime implementation of Intelligent Reengineering as a distinct project-scoped execution mode.

At the end of v4.4, selecting `intelligent_reengineering` should produce materially different refinement outputs than `structured_refinement`, while preserving tenant safety, traceability, and the existing prompt architecture.

## 4. Non-Negotiable Rules

1. Project-scoped only. No cross-project consolidation.
2. Tenant-safe access paths only. No bypass of existing persistence patterns.
3. Disk-canonical plus DB-mirrored prompt architecture remains intact.
4. `direct` mode remains faithful translation, not redesign.
5. Structured Refinement must remain available and stable while the new path is added.
6. Governance findings remain explainable, not opaque pass/fail magic.

## 5. MVP Outcomes

v4.4 is complete when all of the following are true:

1. The orchestrator branches by `post_drafting_mode` after eligibility checks.
2. The profiler emits a richer project-wide reengineering profile, not only medallion grouping metadata.
3. The architect produces consolidated target assets for `intelligent_reengineering`, not just Bronze/Silver/Gold derivations.
4. Agent prompts and critic instructions differentiate layering from redesign using the existing Level 1 / Level 2 model.
5. Governance and ops audit report mode-aware criteria for reengineering outputs.
6. The UI makes it visible that reengineering is a different execution path with different artifacts and success criteria.

## 6. Scope Boundaries

### In Scope

- mode-specific orchestration branching
- project-wide profile model for reusable entities and consolidation candidates
- intelligent reengineering architect strategy
- mode-aware Agent C and Agent F prompt/runtime context
- governance and ops audit alignment for redesign outputs
- UI labels, progress text, and summary artifacts for the new path
- focused unit, integration, and end-to-end validation

### Out of Scope

- cross-project semantic reuse
- new workflow tables unless the MVP proves they are required
- generic semantic modeling platform work
- autonomous business rule invention
- replacing Structured Refinement with a new default

## 7. Execution Plan

### Workstream 1 - Runtime Strategy Branching

Goal:

- separate `structured_refinement` from `intelligent_reengineering` in actual refinement execution

Required changes:

- update `apps/api/services/refinement/refinement_orchestrator.py`
- resolve `post_drafting_mode` once at pipeline start
- introduce explicit strategy branching after profiling
- keep the current path as the implementation for `structured_refinement`
- add a new project-wide redesign path for `intelligent_reengineering`

Implementation notes:

- do not fork the whole pipeline if only one phase differs
- prefer `mode -> strategy object` or `mode -> execution path` selection over scattered `if` chains
- preserve the current profiler/refactor/audit flow where possible, but allow the architect phase and output manifest to change by mode

Acceptance criteria:

1. Logs clearly state which strategy is executing.
2. Structured Refinement continues to produce medallion outputs.
3. Intelligent Reengineering executes a distinct path and emits a different manifest objective.

### Workstream 2 - Reengineering Profile Model

Goal:

- enrich the refinement profile so reengineering can reason over the whole drafted solution

Primary file:

- `apps/api/services/refinement/profiler_service.py`

Required additions:

- detect candidate reusable entities from file names, joins, PK heuristics, and repeated source references
- detect repeated transformations and converging source patterns
- emit `reengineering_units` separate from current `refinement_units`
- emit `shared_entities`, `common_ingestion_paths`, and `consolidation_candidates`
- keep current `refinement_units` for backward compatibility with Structured Refinement

Recommended output shape:

```json
{
  "refinement_units": [],
  "reengineering_units": [],
  "shared_entities": [],
  "consolidation_candidates": [],
  "common_ingestion_paths": [],
  "file_to_unit": {},
  "unit_primary_keys": {}
}
```

Acceptance criteria:

1. Profile metadata distinguishes layering candidates from redesign candidates.
2. The profiler remains usable for projects with only one drafted file.
3. Existing Structured Refinement behavior does not regress.

### Workstream 3 - Intelligent Reengineering Architect

Goal:

- design target-native reusable outputs instead of always generating one Bronze, one Silver, and one Gold asset per logical unit

Primary file:

- `apps/api/services/refinement/architect_service.py`

Required changes:

- preserve the current medallion generation path for `structured_refinement`
- add a second path that consumes `reengineering_units`
- generate consolidated outputs around reusable business entities or shared ingestion flows
- emit a manifest that explains source-to-target consolidation decisions
- preserve traceability from each generated asset back to contributing drafted files

Recommended MVP output pattern:

- `Refined/reengineered/core/`
- `Refined/reengineered/publish/`
- `Refined/reengineered/shared/`
- `Refined/reengineering_manifest.json`

Manifest minimum fields:

- generated asset name
- contributing drafted files
- reused entities or transformations
- rationale for consolidation
- traceability notes

Acceptance criteria:

1. At least one fixture project produces fewer consolidated assets than the original drafted package count.
2. Every generated output keeps source traceability.
3. No reengineering path invents unsupported business defaults.

### Workstream 4 - Prompt And Critic Alignment

Goal:

- make prompts support redesign intentionally without breaking the stable prompt architecture

Primary files:

- `apps/api/services/agent_c_service.py`
- `apps/api/services/agent_f_service.py`
- `apps/api/services/prompts/prompt_assembler.py`
- relevant prompt markdown files under `apps/api/prompts/`

Required changes:

- keep Level 1 agent prompts as the canonical behavioral layer
- keep Level 2 cartridge prompts technology-specific
- add explicit reengineering objective and constraints where needed
- preserve the current strict guidance for `drafting_delivery` and `direct`
- ensure critic instructions validate architectural lift, consolidation quality, and traceability for reengineering mode

Prompt rules for MVP:

1. Reengineering may consolidate multiple drafted assets into one target asset.
2. Reengineering may redesign structure, but not fabricate unknown business semantics.
3. Output must remain explainable and auditable.
4. Structured Refinement must stay bounded and medallion-oriented.

Acceptance criteria:

1. Agent C receives mode-aware context with reengineering-specific objectives.
2. Agent F reviews reengineering outputs with mode-specific acceptance criteria.
3. No prompt changes weaken `direct` mode fidelity.

### Workstream 5 - Governance And Ops Audit Awareness

Goal:

- evaluate reengineered outputs according to the selected mode instead of medallion-only assumptions

Primary files:

- `apps/api/routers/governance.py`
- `apps/api/services/refinement/ops_auditor_service.py`

Required changes:

- preserve existing Drafting Delivery and Structured Refinement behavior
- add reengineering-aware audit checks for:
  - source traceability
  - consolidation rationale
  - reusable asset quality
  - operational completeness of consolidated outputs
- make governance summaries explain why fewer outputs may be the correct result

Acceptance criteria:

1. Intelligent Reengineering outputs are not penalized for lacking one-to-one medallion mirrors.
2. Governance report explains architectural lift in concrete terms.
3. Ops audit continues to validate deployment readiness and safety controls.

### Workstream 6 - UI, State, And Operator Clarity

Goal:

- make the runtime distinction visible during and after execution

Primary files:

- `apps/web/app/components/stages/DraftingView.tsx`
- `apps/web/app/components/stages/PostDraftingDecisionGate.tsx`
- `apps/web/app/components/stages/RefinementView.tsx`

Required changes:

- keep v4.3 decision gate semantics
- update Refinement stage copy for reengineering-specific runtime and outputs
- show mode-aware progress text and completion summaries
- surface the manifest or summary artifact that explains consolidation decisions

Acceptance criteria:

1. The operator can tell which path ran without reading raw logs.
2. Reengineering artifacts and summary language differ from Structured Refinement.
3. Drafting Delivery remains the terminal path with unchanged operator expectations.

## 8. File-Level Delivery Map

### Backend

- `apps/api/services/refinement/refinement_orchestrator.py`
- `apps/api/services/refinement/profiler_service.py`
- `apps/api/services/refinement/architect_service.py`
- `apps/api/services/refinement/ops_auditor_service.py`
- `apps/api/routers/governance.py`
- `apps/api/services/agent_c_service.py`
- `apps/api/services/agent_f_service.py`
- `apps/api/services/prompts/prompt_assembler.py`

### Frontend

- `apps/web/app/components/stages/PostDraftingDecisionGate.tsx`
- `apps/web/app/components/stages/DraftingView.tsx`
- `apps/web/app/components/stages/RefinementView.tsx`

### Prompts

- `apps/api/prompts/agent_c_interpreter.md`
- any Level 2 cartridge prompts that need reengineering-safe guidance

### Tests

- `tests/unit/services/test_refinement_units.py`
- new orchestrator tests for mode branching
- new profiler tests for `reengineering_units`
- new architect tests for consolidated outputs and manifest traceability
- governance tests for reengineering-aware audit behavior
- frontend tests for mode-aware summaries and labels

## 9. Recommended Delivery Sequence

### Sprint 1 - Orchestration And Profile Contract

Deliver:

- strategy branching in orchestrator
- profile schema extension for `reengineering_units`
- focused unit tests for profiler and orchestrator

Estimated effort:

- 1.5 to 2 days

### Sprint 2 - Architect And Manifest

Deliver:

- reengineering-specific architect path
- consolidated output layout
- reengineering manifest with traceability
- fixture-backed tests

Estimated effort:

- 2 to 3 days

### Sprint 3 - Prompt, Governance, And UI Alignment

Deliver:

- Agent C and Agent F alignment
- governance and ops audit criteria
- refinement UI copy and artifact surfacing
- integration tests and smoke validation

Estimated effort:

- 1.5 to 2 days

## 10. Test Plan

### Unit Tests

- profiler emits both `refinement_units` and `reengineering_units`
- orchestrator chooses the correct strategy by mode
- architect preserves traceability in reengineering outputs
- ops auditor validates reengineering manifests and outputs

### Integration Tests

- set `post_drafting_mode=intelligent_reengineering`, start refinement, assert distinct manifest objective and artifact layout
- set `post_drafting_mode=structured_refinement`, assert medallion output path remains unchanged
- verify governance accepts both paths with different explanations

### Smoke Tests

1. Drafting complete -> choose `drafting_delivery` -> refinement blocked -> governance allowed
2. Drafting complete -> choose `structured_refinement` -> medallion refinement runs
3. Drafting complete -> choose `intelligent_reengineering` -> consolidated output path runs and manifest explains source consolidation

## 11. Risks And Guardrails

### Main Risks

1. Over-promising semantic redesign from weak evidence.
2. Regressing Structured Refinement while adding the new path.
3. Producing fewer artifacts without enough explanation.
4. Prompt drift that weakens `direct` mode or stable cartridge behavior.

### Guardrails

1. Keep project scope explicit in all profile and architect logic.
2. Require manifest-based traceability for consolidated outputs.
3. Preserve current `refinement_units` contract while extending profile metadata.
4. Keep prompt changes additive and mode-scoped.
5. Prefer JSON or manifest outputs over new schema changes for MVP.

## 12. Definition Of Done

v4.4 is done when:

1. `intelligent_reengineering` no longer uses the same runtime path as `structured_refinement`.
2. At least one validated fixture demonstrates real within-project consolidation.
3. The UI, logs, and governance outputs all explain the selected path coherently.
4. Tests cover mode branching, reengineering profile generation, manifest traceability, and governance expectations.
5. Structured Refinement and Drafting Delivery continue to behave as shipped in v4.3.

## 13. Immediate First Tasks

If execution starts now, the first implementation batch should be:

1. Add mode resolution and strategy branching to `refinement_orchestrator.py`.
2. Extend `profiler_service.py` with `reengineering_units` and `consolidation_candidates`.
3. Add tests that prove the orchestrator and profiler diverge by mode before touching UI or prompts.

That ordering keeps the runtime contract honest before polishing messaging.