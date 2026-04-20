# v4.3 Sprint 3 - Structured Refinement Clarification

> Last Updated: 2026-04-10
> Status: Implemented
> Scope: project-scoped only, no cross-project mixing

## 1. Purpose

Sprint 3 exists to align the current refinement behavior with the new product contract.

By this point, Drafting Delivery must already be operational.

Now the team clarifies the meaning, language, prompts, and audit expectations for the existing refinement path so it is correctly understood as Structured Refinement.

## 2. Sprint Outcome

At the end of Sprint 3, the platform should be able to:

- explain Drafting Delivery and Structured Refinement as two different paths
- avoid describing current refinement as full reengineering
- align prompts, logs, stage copy, and governance language with the selected mode
- evaluate Drafting-only and Structured Refinement projects differently
- preserve project-scoped behavior only

## 3. Sprint 3 Goal

Reframe the current refinement capability honestly as a bounded modernization mode.

This sprint does not introduce Intelligent Reengineering.

It only clarifies and stabilizes the meaning of the existing refinement path.

## 4. Non-Negotiable Rules

- Drafting Delivery remains a valid terminal path.
- Structured Refinement is not the same thing as Intelligent Reengineering.
- The sprint must not add new cross-project behavior.
- Governance must respect the chosen execution mode.
- No reengineering MVP is allowed in this sprint.

## 5. In Scope

### Product Language

- rename current refinement narrative to Structured Refinement where appropriate
- update stage copy and user-facing labels
- make the difference between Drafting Delivery and Structured Refinement obvious

### Prompt Model

- update prompts so they explicitly understand the mode
- keep direct mode faithful translation behavior unchanged
- make refinement prompts emphasize layered modernization, not deep reengineering

### Governance And Audit

- update critic rules to respect the selected mode
- ensure governance does not expect the same artifacts from Drafting Delivery and Structured Refinement
- align summaries and audit narratives with the new vocabulary

### Validation

- test Drafting-only certification path
- test Structured Refinement certification path
- ensure mode vocabulary stays consistent across docs and runtime-facing text

## 6. Out Of Scope

- no Intelligent Reengineering implementation
- no new post-Drafting modes
- no extra database schema for reengineering
- no cross-project consolidation
- no major redesign of the existing refinement pipeline beyond language and mode alignment

## 7. Execution Order

Use this order exactly.

1. Rename the current refinement narrative to Structured Refinement where needed.
2. Update prompt wording for mode clarity.
3. Update critic behavior to respect the selected mode.
4. Update governance summaries and audit expectations.
5. Add tests for mode-aware certification behavior.
6. Validate Drafting-only and Structured Refinement certification paths.

## 8. Primary Files Likely To Change

The exact files will be confirmed during implementation, but the main areas should be:

- refinement orchestrator messaging
- prompt definitions for the architect and critic roles
- governance / certification logic
- documentation and stage wording
- tests for mode-aware behavior

## 9. Suggested Subtasks

### Task 1 - Rename And Reframe

Update user-facing language so the current refinement flow is clearly structured refinement.

Acceptance:

- no place implies the current path is full solution-level reengineering
- users can tell Drafting Delivery from Structured Refinement

### Task 2 - Prompt Alignment

Update the relevant prompts so they respect the selected mode.

Acceptance:

- direct remains direct
- structured refinement expects layering and maintainability
- no prompt assumes Intelligent Reengineering unless that mode exists explicitly

### Task 3 - Governance Mode Awareness

Update governance scoring, summaries, and audit language.

Acceptance:

- Drafting Delivery is not penalized for missing medallion structure
- Structured Refinement is evaluated as a bounded modernization path
- the narrative does not overclaim architectural redesign

### Task 4 - Validation And Regression Coverage

Add or update tests for mode-aware certification behavior.

Acceptance:

- Drafting-only path still passes
- Structured Refinement path still passes
- terminology is consistent across the tested surfaces

## 10. Definition Of Done

Sprint 3 is done when all of the following are true:

- the refinement path is clearly labeled and understood as Structured Refinement
- prompts, logs, and governance speak the same language
- Drafting Delivery and Structured Refinement are evaluated differently
- no runtime or doc path oversells current refinement as reengineering
- tests cover the mode-aware behavior

## 11. Cost Estimate

Estimated effort:

- 3 to 4 working days

Risk level:

- medium

Why:

- this sprint changes language and evaluation behavior across multiple layers
- it is lower risk than Sprint 2 because branching already exists
- it still needs tight consistency across prompts, governance, and docs

## 12. Launch Notes

Do not start an Intelligent Reengineering MVP inside Sprint 3.

If the team needs the stronger reengineering mode, that should be a separate block after the core v4.3 contract is stable.

The safe release principle is:

- Sprint 1 freezes the contract
- Sprint 2 makes branching real
- Sprint 3 clarifies the refinement mode