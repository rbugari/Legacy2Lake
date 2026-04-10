# v4.3 Sprint 2 - Drafting Branching And Terminal Path

> Last Updated: 2026-04-10
> Status: Implemented
> Scope: project-scoped only, no cross-project mixing

## 1. Purpose

Sprint 2 exists to make Drafting a real decision point.

The product must stop assuming that Refinement is the only possible next step after Drafting.

This sprint implements the branching behavior, the persisted mode choice, and the terminal Drafting path.

## 2. Sprint Outcome

At the end of Sprint 2, the platform should be able to:

- persist the user's post-Drafting choice on the project
- let a project stop at Drafting and move directly to later review and delivery flows
- keep the existing Structured Refinement path available as an explicit option
- avoid any implicit assumption that Refinement must always run
- preserve project-scoped behavior only

## 3. Sprint 2 Goal

Turn Drafting into a product branching point instead of a forced transition into one Refinement concept.

This sprint is about flow control, not reengineering logic.

## 4. Non-Negotiable Rules

- Drafting Delivery must be a valid path.
- `post_drafting_mode` is the persisted project decision.
- Refinement is optional, not mandatory.
- The sprint must not mix projects or tenant context.
- No Intelligent Reengineering work is allowed in this sprint.

## 5. In Scope

### Backend Flow

- persist the selected post-Drafting mode on the project
- update Drafting completion behavior
- make Drafting Delivery route to later review / certification flow
- keep Structured Refinement as a separate path
- ensure status and stage transitions stay coherent

### Frontend Flow

- add a decision gate after Drafting completes
- present the three mode choices clearly
- make the default path understandable without forcing a refinement action
- preserve current project-scoped UX patterns

### Validation

- test Drafting-only completion path
- test existing Structured Refinement entry path
- verify manual walkthrough of the decision gate

## 6. Out of Scope

- no Intelligent Reengineering implementation
- no structured refinement redesign yet
- no governance rewording beyond what is needed for the new path
- no new database tables if a project-level field is enough
- no cross-project logic

## 7. Execution Order

Use this order exactly.

1. Persist `post_drafting_mode` on the project.
2. Make Drafting Delivery a valid terminal path.
3. Update status and stage transition logic.
4. Add the UI decision gate after Drafting.
5. Add tests for Drafting-only progression.
6. Validate the Structured Refinement entry path still works.

## 8. Primary Files Likely To Change

The exact files will be confirmed during implementation, but the main areas should be:

- project metadata persistence surfaces
- Drafting completion / transpile flow
- stage routing and project status transitions
- frontend stage action or decision components
- tests around Drafting and project transitions

## 9. Suggested Subtasks

### Task 1 - Metadata Persistence

Add or wire the project-level field for the post-Drafting mode.

Acceptance:

- the field is saved reliably
- the value survives reloads
- the field is project-scoped only

### Task 2 - Drafting Terminal Path

Allow Drafting to finish without invoking Refinement.

Acceptance:

- the project can continue directly to later review or certification
- no automatic Refinement trigger runs
- the final state remains coherent

### Task 3 - Decision Gate UI

Expose the three mode choices in the post-Drafting UI.

Acceptance:

- Drafting Delivery is clearly visible as an option
- Structured Refinement is clearly visible as an option
- Intelligent Reengineering is visible but not the default dependency

### Task 4 - Status Transition Cleanup

Make sure project state progression works with and without Refinement.

Acceptance:

- no hidden assumption that Refinement is mandatory
- Drafting-only projects do not error
- later review flows accept Drafting Delivery

### Task 5 - Tests And Validation

Add or update tests for the new branching behavior.

Acceptance:

- Drafting-only path is covered
- Structured Refinement path is not broken
- the decision gate logic behaves predictably

## 10. Definition Of Done

Sprint 2 is done when all of the following are true:

- the user can explicitly choose Drafting Delivery after Drafting
- the user can explicitly choose Structured Refinement after Drafting
- the project persists that choice
- the project can continue without running Refinement
- no backend flow assumes Refinement must always run
- tests cover the new branching behavior

## 11. Cost Estimate

Estimated effort:

- 3 to 5 working days

Risk level:

- medium

Why:

- this is the first place where runtime behavior changes
- the path must remain coherent across backend and frontend
- state transitions are easy to break if the contract is not respected

## 12. Launch Notes

Do not start Sprint 3 until Sprint 2 is operational.

If Sprint 2 is incomplete, the refinement vocabulary work in Sprint 3 will sit on top of a broken flow.

The safe release principle is:

- Sprint 1 freezes the contract
- Sprint 2 makes the branching path real
- Sprint 3 clarifies the refinement mode