# v4.3 Sprint 1 - Product Contract Freeze

> Last Updated: 2026-04-10
> Status: Implemented
> Scope: project-scoped only, no cross-project mixing

## 1. Purpose

Sprint 1 exists to freeze the product contract before any implementation starts.

The team should leave this sprint with one shared answer to four questions:

1. Can Drafting be a terminal delivery state?
2. What exactly is Structured Refinement?
3. What exactly is Intelligent Reengineering?
4. What project-level field will store the user's post-Drafting choice?

If those questions are not answered clearly, the implementation will drift and the next sprints will be expensive to undo.

## 2. Sprint Outcome

At the end of Sprint 1, the team should have:

- approved naming for the three post-Drafting modes
- approved scope boundaries for each mode
- approved project metadata contract for the selected mode
- approved release packaging for v4.3
- frozen backlog for Sprint 2 and Sprint 3
- explicit confirmation that Intelligent Reengineering is optional and project-scoped

## 3. Sprint 1 Goal

Freeze the contract for post-Drafting behavior so the rest of v4.3 can be executed without reinterpretation.

This sprint does not implement branching behavior yet.

It defines the rules that all later work must follow.

## 4. Non-Negotiable Rules

- Everything remains project-scoped.
- Drafting is a valid delivery baseline.
- Structured Refinement is a bounded modernization mode, not the same thing as Intelligent Reengineering.
- Intelligent Reengineering is a separate, higher-risk mode.
- Governance must eventually evaluate each mode differently.

## 5. What Must Be Decided In Sprint 1

### 5.1 Naming

Approve the canonical names for the three modes.

Recommended names:

- `drafting_delivery`
- `structured_refinement`
- `intelligent_reengineering`

### 5.2 Project Metadata Field

Approve the persisted field that will store the user's choice after Drafting.

Recommended field:

- `post_drafting_mode`

Allowed values should match the approved mode names.

### 5.3 Delivery Contract

Confirm that Drafting can end the delivery path.

That means a project may go:

- Discovery -> Triage -> Drafting -> Certification/Handover

without necessarily passing through Refinement.

### 5.4 Refinement Contract

Confirm that the current refinement behavior is to be understood as Structured Refinement.

That means:

- it may preserve package boundaries more than it redesigns them
- it may layer outputs into Bronze/Silver/Gold
- it is not the full reengineering story

### 5.5 Reengineering Contract

Confirm that Intelligent Reengineering is a separate, more ambitious mode.

That means:

- it works within one project only
- it looks across the drafted solution as a whole
- it may consolidate or reduce redundant outputs
- it is not required for v4.3 release

## 6. Sprint 1 Execution Order

Use this order exactly.

1. Confirm the three mode names.
2. Confirm the project field and allowed values.
3. Confirm that Drafting can be terminal.
4. Confirm that current Refinement is Structured Refinement.
5. Confirm that Intelligent Reengineering is optional and higher risk.
6. List all files and services that assume Refinement is mandatory.
7. List all UI screens that assume a single linear path after Drafting.
8. List all prompts and governance rules that need mode awareness.
9. Freeze the acceptance criteria for Sprint 2 and Sprint 3.

## 7. In Scope

### Product and Architecture

- define post-Drafting execution modes
- define project-scoped storage of the selected mode
- define how Drafting can be terminal
- define how structured refinement differs from reengineering

### Documentation

- update the authoritative v4.3 plan
- update stage docs so Drafting and Refinement are aligned with the new model
- update planning index if needed

### Inventory Work

- identify backend flows that assume Refinement is mandatory
- identify frontend views that assume a single post-Drafting path
- identify prompts and audit logic that need mode-aware rules

## 8. Out of Scope

- no runtime behavior changes yet
- no new database migrations yet
- no router changes yet
- no UI implementation yet
- no prompt logic changes yet
- no governance logic changes yet
- no Intelligent Reengineering implementation yet

## 9. Primary Files To Review

- [docs/planning/V4_3_POST_DRAFTING_EXECUTION_MODES.md](docs/planning/V4_3_POST_DRAFTING_EXECUTION_MODES.md)
- [docs/stages/STAGE_3_DRAFTING.md](docs/stages/STAGE_3_DRAFTING.md)
- [docs/stages/STAGE_4_REFINEMENT.md](docs/stages/STAGE_4_REFINEMENT.md)
- [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)
- [apps/api/services/migration_orchestrator.py](apps/api/services/migration_orchestrator.py)
- [apps/api/services/refinement/refinement_orchestrator.py](apps/api/services/refinement/refinement_orchestrator.py)
- [apps/api/prompts/agent_c_interpreter.md](apps/api/prompts/agent_c_interpreter.md)
- [apps/api/prompts/agent_f_critic.md](apps/api/prompts/agent_f_critic.md)

## 10. Suggested Subtasks

### Task 1 - Contract Freeze Notes

Produce a short internal note with:

- approved mode names
- approved metadata field
- approved scope boundaries
- approved v4.3 packaging recommendation

### Task 2 - Dependency Inventory

List every place in runtime and UI that currently assumes:

- Refinement must always follow Drafting
- medallion layering is the same as solution-level reengineering
- Governance only audits one post-Drafting path

### Task 3 - Acceptance Criteria Draft

Write the acceptance criteria for each mode:

- Drafting Delivery
- Structured Refinement
- Intelligent Reengineering

### Task 4 - Sprint 2 Readiness

Prepare the exact backlog that Sprint 2 will need so the team can branch Drafting without re-litigating terminology.

## 11. Exit Criteria

Sprint 1 is complete when all of the following are true:

- the team agrees on the three mode names
- the team agrees on the persisted project field
- Drafting as a terminal path is explicitly accepted
- Structured Refinement is clearly distinct from Intelligent Reengineering
- the v4.3 backlog is frozen for Sprint 2 and Sprint 3
- no ambiguous wording remains in the authoritative docs for this contract

## 12. Cost Estimate

Sprint 1 should be quick because it is mostly contract and alignment work.

Estimated effort:

- 1 to 2 working days

Risk level:

- low

Why:

- there is no code implementation yet
- the main work is decision-making and documentation
- it reduces rework risk for the rest of v4.3

## 13. Launch Notes

Do not start Sprint 2 until Sprint 1 exits cleanly.

If Sprint 1 is vague, Sprint 2 will probably build the wrong branching behavior.

If Sprint 1 is clear, the rest of the release becomes mostly execution rather than interpretation.