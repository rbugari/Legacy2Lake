# v4.3 Plan - Post-Drafting Execution Modes

> Last Updated: 2026-04-06
> Status: Proposed scope for v4.3
> Constraint: project-scoped only, no cross-project mixing

## 1. Why This Exists

The platform already has strong Discovery and Triage behavior and a validated Drafting baseline. The current gap is not in understanding legacy assets, but in what happens immediately after Drafting.

Today, the product language still makes it too easy to treat Refinement as a single mandatory follow-up stage. That is too blunt for the real operating model we want.

The intended model for v4.3 is:

1. understand the project deeply
2. generate a valid Drafting output
3. let the user choose the next execution mode based on risk, urgency, and desired modernization depth

This preserves Drafting as a valid delivery state while creating room for two different post-Drafting modernization paths.

## 2. Non-Negotiable Scope Rule

For v4.3, everything remains project-scoped.

That means:

- no reuse across different projects
- no cross-project shared semantic entities
- no global customer, product, or vendor consolidation across tenants or projects
- all consolidation and reengineering happen only inside the currently analyzed project's own assets

This keeps the architecture simpler, avoids tenant and project contamination, and makes the first version of the branching model viable.

## 3. Operating Model

### Phase 1 and Phase 2 remain unchanged

Discovery and Triage should continue to maximize understanding:

- open and inspect every supported asset type
- classify what is migratable versus support knowledge
- capture business context, dependencies, evidence, and constraints
- produce the strongest possible factual base for Drafting

### Drafting remains a valid endpoint

Drafting should be defined as:

- a functionally valid migration
- faithful to the original package or SQL asset structure
- minimally redesigned
- suitable for implementation in many projects without additional modernization

This means Drafting is not a "half-done" state by definition. It is the first delivery-grade state.

### Post-Drafting becomes an explicit decision point

When Drafting completes, the platform should expose three execution modes.

## 4. Execution Modes

### Mode A - Drafting Delivery

Use Drafting as the final implementation candidate.

Characteristics:

- direct migration output is accepted as the delivery baseline
- project can move directly into Certification and Handover
- best for lower-risk migrations, deadlines, or cases where structural redesign is not needed yet

Success criteria:

- functional equivalence is acceptable
- target code is reviewable and executable
- governance can certify the project without requiring medallion artifacts

### Mode B - Structured Refinement

Take the Drafting output and reorganize it into Bronze, Silver, and Gold with limited semantic redesign.

Characteristics:

- mostly preserves per-asset or per-package boundaries
- separates ingest, validation/cleansing, and publish layers
- improves maintainability and operational clarity
- Gold can still be thin or imperfect when original business modeling lived outside ETL

Success criteria:

- the solution is better layered and easier to evolve
- architecture is clearer than raw Drafting
- the team gets a stronger modernization baseline without large semantic risk

### Mode C - Intelligent Reengineering

Use the full project solution and support knowledge to redesign toward reusable target-native ELT assets.

Characteristics:

- looks across the full project, not one package at a time
- identifies shared entities, common ingestion paths, and repeated transformation logic
- consolidates redundant legacy flows into fewer reusable target assets
- may produce fewer outputs than the original package count
- carries higher value and higher risk than Structured Refinement

Success criteria:

- redundancy is materially reduced
- shared dimensions or reusable business entities are consolidated inside the project
- the result is architecturally closer to real ELT than to lifted ETL choreography

## 5. Product Decision Gate

The user decision should happen immediately after Drafting completes.

Recommended options in the UI:

1. Approve Drafting and continue to Certification
2. Run Structured Refinement
3. Run Intelligent Reengineering

The decision gate should explain:

- expected value
- expected risk
- expected runtime and cost
- whether the selected mode preserves package boundaries or redesigns them

## 6. Why The Separation Matters

Without this separation, the product collapses three very different intents into one label:

- a faithful migration baseline
- a layered modernization pass
- a true reengineering pass

That creates bad outcomes:

- Drafting looks weaker than it is
- current Refinement looks smarter than it really is
- users cannot choose the risk profile they want
- Governance ends up assuming the same standard for all outputs

## 7. Required Architecture Changes For v4.3

### Workstream 1 - Terminology and State Model

Goal:

- make the execution mode explicit in project metadata and runtime decisions

Changes:

- introduce a project-level field such as `post_drafting_mode`
- supported values should be equivalent to `drafting_delivery`, `structured_refinement`, `intelligent_reengineering`
- keep stage progression separate from delivery mode

Complexity:

- low

### Workstream 2 - Drafting As Terminal Path

Goal:

- allow projects to move from Drafting directly into Certification/Governance

Changes:

- UI needs an explicit stop-at-Drafting path
- routers and project status transitions must not assume Refinement is mandatory
- Governance must accept Drafting-only deliveries

Complexity:

- medium

### Workstream 3 - Structured Refinement As Explicit Mode

Goal:

- rename and bound the current refinement behavior as a legitimate but limited mode

Changes:

- clarify in UI and docs that this mode is mostly structural layering
- preserve project-scoped operation
- keep current per-project consolidation logic but do not oversell it as full reengineering

Complexity:

- low to medium

### Workstream 4 - Intelligent Reengineering Strategy

Goal:

- define a separate orchestration strategy for real cross-asset consolidation within one project

Changes:

- strategy selection in refinement orchestration
- richer profile model focused on reusable business entities and shared target assets
- prompt and critic behavior specialized for solution-level redesign
- explicit distinction between "layer the same thing" and "redesign the solution"

Complexity:

- high

### Workstream 5 - Governance and Audit Mode Awareness

Goal:

- evaluate outputs according to the chosen execution mode

Changes:

- Governance rules must branch by delivery mode
- Drafting-only projects should not be penalized for lacking medallion outputs
- Intelligent Reengineering should be audited for reuse, consolidation, and architectural lift

Complexity:

- medium

### Workstream 6 - Prompt Model Alignment

Goal:

- make prompts mode-aware without breaking the stable Level 1 / Level 2 architecture

Changes:

- direct mode remains faithful translation
- structured refinement prompts should emphasize layering and maintainability
- intelligent reengineering prompts should emphasize project-wide consolidation and ELT redesign

Complexity:

- medium to high

## 8. Recommended v4.3 Scope

### v4.3 Minimum Viable Scope

This is the version recommended if the goal is to ship v4.3 soon and safely.

Include:

- explicit post-Drafting decision gate
- Drafting as terminal path
- project metadata for execution mode
- Governance aware of Drafting-only versus refinement outputs
- current refinement behavior relabeled as Structured Refinement
- documentation and product language cleanup

Do not fully include yet:

- full Intelligent Reengineering automation
- aggressive semantic consolidation heuristics
- multi-strategy planner that rewrites the whole project topology deeply

Why:

- this gives the product the correct shape immediately
- it avoids pretending that current refinement is already solution-level reengineering
- it creates the contract needed to add Intelligent Reengineering in a later increment without breaking the UX

### v4.3 Extended Scope

Include everything in the minimum scope plus:

- first real Intelligent Reengineering orchestration path
- project-wide consolidation heuristics
- dedicated audit criteria for solution-level redesign

Why this is riskier:

- prompt tuning is harder
- success criteria are more subjective
- regression surface is wider
- runtime behavior can become less predictable

## 9. Cost Estimate

The estimates below assume one experienced engineer working in this repo, with current architecture preserved and no cross-project mixing.

### Option A - v4.3 Minimum Viable Scope

Work estimate:

1. terminology, docs, and project mode state: 1 to 2 days
2. Drafting terminal path in UI and backend flow: 2 to 3 days
3. Governance and critic mode-awareness: 2 to 3 days
4. structured refinement relabeling and UX cleanup: 1 to 2 days
5. focused tests and flow validation: 2 to 3 days

Estimated total:

- 8 to 13 working days

Risk level:

- medium

Expected outcome:

- product model becomes correct
- users can choose how far to go after Drafting
- current platform behavior is no longer conceptually misleading

### Option B - v4.3 Extended Scope With Intelligent Reengineering MVP

Work estimate:

1. everything from Option A: 8 to 13 days
2. intelligent reengineering strategy in orchestrator: 3 to 5 days
3. richer project-wide profile model: 2 to 4 days
4. prompt and audit specialization for reengineering: 2 to 4 days
5. fixture testing and iteration on output quality: 3 to 5 days

Estimated total:

- 18 to 31 working days

Risk level:

- medium-high to high

Expected outcome:

- the platform starts showing true IA-driven reengineering value inside a single project
- output quality can improve significantly, but tuning and validation burden increase materially

## 10. Recommendation

The recommended v4.3 plan is:

1. ship Option A as the official v4.3 contract
2. keep everything project-scoped
3. keep current refinement behavior, but rename it clearly as Structured Refinement
4. add Intelligent Reengineering as a new mode behind a controlled MVP scope, either late in v4.3 or early in v4.4 depending on capacity

This gives the product the right mental model immediately without pretending that the hardest part is already solved.

## 11. Execution Plan By Blocks

The safest way to execute v4.3 is not as one large undifferentiated sprint.

The recommended structure is:

1. lock the product contract
2. enable the branching path after Drafting
3. make Governance and UX mode-aware
4. optionally add the first Intelligent Reengineering MVP only if the first three blocks land cleanly

### Recommended Delivery Shape

#### Block 1 - Product Contract Freeze

Goal:

- freeze naming, state model, and expected user choices before implementation spreads across backend, frontend, and prompts

In scope:

- finalize delivery mode names
- define the project-level field for post-Drafting choice
- align docs and authoritative wording
- identify all places that currently assume Refinement is mandatory

Expected outputs:

- approved terminology for the three execution modes
- approved state contract for project metadata
- implementation backlog split by backend, frontend, prompts, and governance

Primary files likely impacted later:

- project settings / metadata persistence surfaces
- stage docs and architecture docs
- frontend stage navigation and action surfaces

Dependencies:

- none

Estimated effort:

- 1 to 2 days

Exit criteria:

- the team can answer without ambiguity:
	- can Drafting be terminal?
	- what is Structured Refinement?
	- what is Intelligent Reengineering?
	- what remains project-scoped?

#### Block 2 - Drafting Branching And Terminal Path

Goal:

- make Drafting a true decision point instead of an automatic handoff into a single Refinement concept

In scope:

- add project-level `post_drafting_mode` handling
- allow direct move from Drafting into Certification / Governance
- expose explicit user choices after Drafting
- preserve current project-scoped behavior

Expected outputs:

- backend flow that supports Drafting-only delivery
- UI decision gate after Drafting
- project status logic no longer assumes Refinement always follows

Primary work areas:

- project metadata persistence
- Drafting completion flow
- stage routing / action panels
- certification / governance entry conditions

Dependencies:

- Block 1 terminology and state contract

Estimated effort:

- 3 to 5 days

Exit criteria:

- a user can finish Drafting and explicitly choose Drafting Delivery
- the project can continue without running Refinement
- status and stage transitions remain coherent

#### Block 3 - Structured Refinement Clarification

Goal:

- keep the current refinement capability, but reframe it honestly as a bounded modernization mode

In scope:

- rename current refinement behavior as Structured Refinement in product language
- align prompts, logs, stage copy, and audit language
- ensure Governance understands that this mode is layered modernization, not full reengineering

Expected outputs:

- updated product copy and logs
- clearer structured refinement run mode
- critic and governance rules aligned with the selected mode

Primary work areas:

- refinement orchestrator messaging
- prompt wording
- critic mode-awareness
- governance scoring / narrative output

Dependencies:

- Block 2 branching path must exist

Estimated effort:

- 3 to 4 days

Exit criteria:

- the product no longer overstates current refinement as solution-level redesign
- governance can evaluate Drafting Delivery and Structured Refinement differently
- users understand that Structured Refinement is a safer, lower-risk step than reengineering

#### Block 4 - Intelligent Reengineering MVP

Goal:

- introduce the first real project-level reengineering mode inside one project boundary

In scope:

- new orchestration strategy for Intelligent Reengineering
- richer per-project profile focused on shared entities and repeated logic
- mode-specific prompts and critic rules
- fixture-based validation of reengineering outcomes

Expected outputs:

- a separate run mode for Intelligent Reengineering
- first project-scoped consolidation heuristics
- governance criteria for reuse and architectural lift

Primary work areas:

- refinement orchestrator strategy selection
- profiling model
- prompt model alignment
- audit logic and report language

Dependencies:

- Blocks 1 to 3 completed first

Estimated effort:

- 7 to 12 days

Exit criteria:

- the platform can produce a materially different result from Structured Refinement
- outputs show real within-project consolidation, not just layered copies
- governance can describe the architectural tradeoff and residual risk

### Recommended Sprint Packaging

There are three reasonable ways to package the blocks.

#### Packaging A - Two Sprint Plan

Sprint 1:

- Block 1
- Block 2

Sprint 2:

- Block 3
- decision on whether Block 4 is approved for next release

Use this when:

- v4.3 needs to ship quickly
- the main goal is product correctness and clean branching after Drafting
- the team does not want to promise Intelligent Reengineering yet

Estimated total:

- 6 to 9 working days

#### Packaging B - Three Sprint Plan

Sprint 1:

- Block 1

Sprint 2:

- Block 2

Sprint 3:

- Block 3

Use this when:

- the team wants cleaner checkpoints
- product review and UX review need time between changes
- governance behavior must be validated carefully before release

Estimated total:

- 7 to 11 working days

#### Packaging C - Four Block Plan With Reengineering MVP

Sprint 1:

- Block 1

Sprint 2:

- Block 2

Sprint 3:

- Block 3

Sprint 4:

- Block 4

Use this when:

- the team explicitly wants v4.3 to include the first Intelligent Reengineering MVP
- extra tuning and fixture validation time is available
- release risk is acceptable

Estimated total:

- 14 to 23 working days

### Recommended Default For Execution

The default recommendation is Packaging B for the official v4.3 delivery decision.

Why:

- it is still short enough to execute quickly
- it gives clear review checkpoints
- it avoids coupling the release to the hardest AI-driven block
- it leaves Block 4 available as a controlled extension instead of a release dependency

## 12. Ready-To-Launch Execution Order

This section is the practical handoff order to execute v4.3.

If the team wants the safest path, use this sequence exactly and do not overlap blocks unless the previous gate is explicitly approved.

### Official Launch Order

1. Launch Sprint 1: Product Contract Freeze
2. Review and approve Gate After Block 1
3. Launch Sprint 2: Drafting Branching And Terminal Path
4. Review and approve Gate After Block 2
5. Launch Sprint 3: Structured Refinement Clarification
6. Review and approve Gate After Block 3
7. Release v4.3
8. Decide separately whether Block 4 becomes late-v4.3 or v4.4 work

### Do Not Parallelize These By Default

Do not start these in parallel unless the team explicitly accepts rework risk:

- Block 2 before Block 1 naming and state contract are frozen
- Block 3 before the Drafting branching path exists
- Block 4 before Governance and product language are already mode-aware

Why:

- too many downstream files depend on the final names and mode contract
- UI and governance logic will otherwise be built against unstable assumptions
- Block 4 becomes expensive if the first three blocks are still moving

### Sprint 1 - Launch Packet

Objective:

- freeze the v4.3 contract so implementation work can start without reinterpretation

Execution order inside Sprint 1:

1. confirm the three mode names
2. confirm the persisted project field and values
3. list affected backend flows
4. list affected frontend views and stage actions
5. list affected prompts and governance rules
6. freeze acceptance criteria for each mode

Definition of done:

- names are approved
- project-scoped rule is reaffirmed
- Drafting terminal path is explicitly approved
- current Refinement is explicitly classified as Structured Refinement, not Intelligent Reengineering
- the implementation backlog for Sprint 2 and Sprint 3 is frozen

Suggested decision meeting output:

- approved naming
- approved scope exclusions
- approved target packaging for v4.3

### Sprint 2 - Launch Packet

Objective:

- make Drafting a real branching point in the product flow

Execution order inside Sprint 2:

1. persist `post_drafting_mode` on the project
2. enable Drafting Delivery as a real terminal path
3. update status / stage transition logic
4. add UI choice after Drafting completes
5. add tests for Drafting-only progression

Definition of done:

- a user can complete Drafting and choose Drafting Delivery
- the project can proceed to later review without Refinement
- no backend flow assumes Refinement must run next
- status transitions are stable

Mandatory validation before moving on:

- one happy-path test for Drafting Delivery
- one regression test for existing Structured Refinement entry path
- manual walkthrough of the Drafting decision gate in UI

### Sprint 3 - Launch Packet

Objective:

- align the existing refinement behavior, prompts, and governance under the new product contract

Execution order inside Sprint 3:

1. rename current refinement language to Structured Refinement where needed
2. update prompt wording for mode clarity
3. update critic behavior to respect the selected mode
4. update governance summaries and audit expectations
5. add tests for mode-aware certification behavior

Definition of done:

- Drafting Delivery and Structured Refinement are explained and audited differently
- product language no longer implies a single mandatory Refinement path
- current refinement behavior is no longer oversold as reengineering
- release notes and docs are aligned with runtime behavior

Mandatory validation before release:

- one Drafting-only certification path validated
- one Structured Refinement certification path validated
- docs, UI copy, and governance narrative use the same mode vocabulary

### Optional Sprint 4 - Launch Packet

Objective:

- add the first controlled Intelligent Reengineering MVP without destabilizing v4.3 core behavior

Execution order inside Sprint 4:

1. add Intelligent Reengineering orchestration strategy
2. expand profiling toward shared entities and repeated logic
3. add mode-specific prompts and critic checks
4. validate on real fixture projects
5. compare against Structured Refinement baseline

Definition of done:

- outputs materially differ from Structured Refinement
- within-project consolidation is visible and intentional
- governance can explain benefits and residual risk clearly

Release note:

- this block should not block the main v4.3 release unless leadership explicitly chooses the higher-risk packaging

## 13. Detailed Backlog By Block

### Block 1 Backlog

1. Define canonical names for the three execution modes.
2. Define the persisted project field and allowed values.
3. List every backend route or service that assumes Refinement is mandatory.
4. List every UI view that assumes stage progression is linear.
5. List every prompt and audit rule that currently conflates layering with reengineering.
6. Freeze the acceptance criteria for Drafting Delivery, Structured Refinement, and Intelligent Reengineering.

### Block 2 Backlog

1. Persist the selected post-Drafting mode on the project.
2. Add post-Drafting choice UI and action copy.
3. Allow Drafting Delivery to transition directly into later review flow.
4. Prevent automatic assumptions that Refinement must run next.
5. Add tests for Drafting-only path and state transitions.

### Block 3 Backlog

1. Rename the current refinement narrative to Structured Refinement where appropriate.
2. Adjust governance expectations for Drafting Delivery versus Structured Refinement.
3. Update critic guidance so mode-specific checks are applied consistently.
4. Update logs, summaries, and UX wording to match the new model.
5. Add tests for mode-aware governance behavior.

### Block 4 Backlog

1. Add a separate Intelligent Reengineering strategy entry point.
2. Expand profiling toward shared entities, repeated transformations, and reusable targets.
3. Add mode-specific prompt instructions for project-level redesign.
4. Add critic rules for consolidation quality and architectural lift.
5. Validate on one or more real fixture projects.
6. Measure output quality against Structured Refinement baseline.

## 14. Go / No-Go Gates

### Gate After Block 1

Proceed only if:

- the team agrees on naming
- the team agrees that Drafting can be terminal
- the team agrees that current Refinement is not the same as Intelligent Reengineering

### Gate After Block 2

Proceed only if:

- Drafting Delivery works as a real path
- status transitions remain coherent
- the UX makes the choice understandable to users

### Gate After Block 3

Proceed to release v4.3 if:

- Drafting Delivery and Structured Refinement are both stable
- Governance is mode-aware
- product language is no longer conceptually misleading

### Gate Before Block 4

Proceed only if:

- the team explicitly wants to absorb higher delivery risk
- fixture-based validation capacity exists
- output quality can be judged with clear acceptance criteria

## 15. What Success Looks Like

## 16. Execution Summary For Handoff

If this plan is handed to an execution team, the instruction should be:

1. execute Packaging B by default
2. treat Sprint 1 as contract freeze, not coding sprawl
3. do not begin Sprint 3 until Drafting Delivery is operational
4. release v4.3 after Block 3 if gates are green
5. treat Intelligent Reengineering as an optional follow-up block, not a hidden dependency

This is the correct launch order unless product leadership explicitly chooses the higher-risk Packaging C.

After v4.3, the product story should be easy to explain:

- Discovery and Triage understand the project deeply
- Drafting produces a valid migration baseline
- the user then chooses one of three paths
- Governance evaluates the result according to the chosen path
- all reengineering remains inside the current project boundary

If that is true, the product becomes much easier to position and much easier to evolve.