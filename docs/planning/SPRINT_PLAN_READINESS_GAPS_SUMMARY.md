# Sprint Plan - Readiness, Gaps, and Executive Summary

> Last Updated: 2026-03-26
> Status: Proposed before implementation
> Scope: Delivery plan before any code changes

## 1. Purpose

This document captures the proposed sprint sequence for three related product lines:

- Readiness + confidence model
- Gap and decision workspace
- Executive / business summary

The intent is to freeze the product direction in writing before changing database schema, backend services, or frontend flows.

## 2. Planning Principle

These are not three isolated features.

They form a sequence:

1. Normalize the signal
2. Translate the signal
3. Operationalize the signal

That means:

1. Readiness + confidence model comes first
2. Executive / business summary comes next
3. Gap and decision workspace becomes much stronger once the first two exist

If the workspace is built before the readiness model, the likely result is a noisy backlog of scattered issues with weak prioritization.

## 3. Recommended Sprint Sequence

### Sprint 1

`Readiness + Confidence Model`

### Sprint 2

`Executive / Business Summary + Visible Gaps`

### Sprint 3

`Gap And Decision Workspace`

## 4. Sprint 1 - Readiness + Confidence Model

### Goal

Provide a visible and explainable project-level readiness state.

The user should immediately understand:

- how ready the project is for automation
- why it has that status
- what blocks progress
- what the recommended next action is

### In Scope

- project-level readiness state
- project-level confidence score
- top reasons for the current status
- main blockers
- recommended next action
- readiness badge in Discovery
- readiness badge or summary in Triage
- readiness summary in Drafting
- backend aggregation logic for readiness
- persisted readiness payload on project

### Out Of Scope

- asset-level readiness
- editable readiness overrides
- gap workflow or decision workflow
- executive export package changes
- tenant-specific scoring customization

### Product Output

Suggested labels:

- `READY`
- `BASELINE_READY`
- `REQUIRES_CONTEXT`
- `NOT_RECOMMENDED_FOR_AUTOMATION`

Suggested payload:

- `status`
- `confidence_score`
- `top_reasons`
- `blockers`
- `recommended_next_action`
- `source_signals`
- `computed_at`

### Database Impact

Recommended approach for Sprint 1:

- do not create a new table
- add a JSONB field on `utm_projects`

Suggested field name:

- `readiness_summary`

Rationale:

- fastest path to value
- low migration risk
- avoids over-modeling before the signal is proven useful

### Backend Impact

Add a readiness aggregation service that combines existing signals, for example:

- `quick_assessment`
- blockers from Quick Assessment
- triage findings
- metadata coverage
- validation state where available
- governance score or readiness hints where available

Suggested API surface:

- `GET /projects/{project_id}/readiness`
- optional `POST /projects/{project_id}/readiness/recompute`

### Frontend Impact

Expected UI changes:

- Discovery: readiness card or badge near assessment output
- Triage: readiness summary card and reasons
- Drafting: compact readiness strip showing trust level and next step
- optional sidebar summary for quick orientation

### Business Impact

This sprint should improve trust without changing the core workflow.

The user still uses the same stages, but with a much clearer answer to:

- can I continue?
- is this reliable enough?
- what is missing?

### Risks

- false precision if score logic is opaque
- inflated confidence if business gaps are ignored

### Mitigation

- never show score alone
- always show reasons and blockers
- always show recommended next action

### Exit Criteria

Sprint 1 is complete when:

- a project shows a visible readiness state
- the readiness state is explainable
- the user can see blockers and next action
- no new workspace or process burden was introduced

## 5. Sprint 2 - Executive / Business Summary + Visible Gaps

### Goal

Translate technical state into a business-facing view and make major gaps visible in a grouped, reviewable format.

### In Scope

- executive summary at project level
- summary section in Governance and/or Handover overview
- summarized migration viability
- top risks
- likely manual effort areas
- delivery recommendation
- grouped gaps visible to the user
- gap groupings by category and severity
- inclusion of summary content in reports or export bundles if feasible

### Out Of Scope

- formal gap CRUD
- owner assignment workflow
- resolution status workflow beyond simple derived visibility
- dedicated gap table
- Slack/Teams or notification flows

### Product Output

The executive summary should answer:

- how migrable is this project?
- what are the biggest risks?
- where will manual effort still be needed?
- what is blocking final confidence?
- what is the recommended delivery posture?

Suggested summary sections:

- migration posture
- top risks
- manual effort areas
- open blockers
- recommended next action

Suggested gap categories:

- schema
- mappings
- business rules
- orchestration
- data quality
- compliance
- target architecture choice

### Database Impact

Recommended approach for Sprint 2:

- avoid a new table in the first pass
- derive executive summary on demand
- optionally persist later if export/versioning requires snapshots

Optional future field on `utm_projects` if needed:

- `executive_summary`

### Backend Impact

Add or extend a summary service to consolidate:

- readiness summary
- quick assessment
- detected blockers and gaps
- governance signals
- project metadata and technology selection

Suggested API surface:

- `GET /projects/{project_id}/executive-summary`
- `GET /projects/{project_id}/gaps-summary`

### Frontend Impact

Expected UI changes:

- Governance overview gains executive summary block
- Handover overview gains business-facing handoff summary
- grouped gaps panel or list for review

The UI should remain lightweight.

This sprint is about visibility and communication, not yet about workflow management.

### Business Impact

This sprint broadens the product audience.

It should help:

- sponsors
- project managers
- steering committees
- customer reviewers who do not want raw technical detail first

### Risks

- summary becomes generic or marketing-like
- summary is not grounded in system evidence

### Mitigation

- anchor summary in readiness and observed gaps
- keep top risks concrete and short
- include explicit blockers when present

### Exit Criteria

Sprint 2 is complete when:

- Governance or Handover shows a clear executive summary
- grouped gaps are visible and understandable
- summary language matches the underlying technical state

## 6. Sprint 3 - Gap And Decision Workspace

### Goal

Turn scattered findings into an actionable workspace where gaps can be reviewed, owned, resolved, or escalated.

### In Scope

- dedicated gap and decision entity
- formal storage model for gaps
- CRUD operations
- resolution status
- decision notes
- recommended owner
- filtering by severity, category, and status
- linking gaps to project and optionally asset
- workspace tab or panel with actionable controls

### Out Of Scope

- advanced approval chains
- Slack/Teams notifications
- automatic assignments
- enterprise workflow automation
- multi-step governance workflows

### Product Output

Each item should support at least:

- category
- severity
- title
- description
- why it matters
- recommended owner
- resolution status
- decision note
- impacted asset if available
- source stage

### Database Impact

Recommended approach for Sprint 3:

- create a dedicated table

Suggested name:

- `utm_project_gaps`

Suggested fields:

- `gap_id`
- `tenant_id`
- `project_id`
- `asset_id` nullable
- `source_stage`
- `category`
- `severity`
- `title`
- `description`
- `why_it_matters`
- `recommended_owner`
- `resolution_status`
- `decision_note`
- `created_by`
- `resolved_by`
- `created_at`
- `updated_at`
- `resolved_at`

Recommended indexes:

- `(tenant_id, project_id)`
- `(tenant_id, resolution_status)`
- `(tenant_id, severity)`

### Backend Impact

Needed capabilities:

- normalize gaps from existing signals
- create new gap items when needed
- edit metadata and notes
- resolve and reopen
- basic deduplication

Suggested API surface:

- `GET /projects/{project_id}/gaps`
- `POST /projects/{project_id}/gaps`
- `PATCH /projects/{project_id}/gaps/{gap_id}`
- `POST /projects/{project_id}/gaps/{gap_id}/resolve`
- `POST /projects/{project_id}/gaps/{gap_id}/reopen`

### Frontend Impact

Expected UI changes:

- dedicated gap workspace tab or panel
- grouped and filtered gap list
- detail panel for explanation and decision note
- actions to resolve, reopen, or mark as needs-customer-input

### Business Impact

This sprint changes the operating model more than the first two.

It moves the product from passive diagnosis to active migration coordination.

### Risks

- too much manual overhead
- duplicate or low-value gaps
- workspace becomes administrative clutter

### Mitigation

- keep required fields minimal
- start with lightweight statuses
- deduplicate aggressively enough to avoid noise

### Exit Criteria

Sprint 3 is complete when:

- gap items can be created, reviewed, and resolved
- decisions are visible and durable
- the project can show open versus resolved issues clearly

## 7. Recommended MVP Cut

If the team wants the safest path, use this cut:

### MVP Sprint 1

- project-level readiness only

### MVP Sprint 2

- executive summary derived from readiness and known findings
- visible grouped gaps without full workflow

### MVP Sprint 3

- formal gap and decision workspace with minimal statuses

## 8. What Should Not Be Added Yet

To protect focus, do not combine these sprints with:

- asset-level readiness from day one
- Slack/Teams integration
- Git integration work
- legacy-to-target traceability review
- advanced approval chains
- multi-role workflow engines
- tenant-specific score policy engines

Those themes can be addressed later once the core signal, summary, and gap workflow are stable.

## 9. Delivery Summary

### Sprint 1 Demo

- project shows readiness clearly
- reasons and blockers are visible
- next action is explicit

### Sprint 2 Demo

- Governance or Handover shows a business-facing summary
- major gaps are grouped and visible
- review conversations no longer require reading raw technical output first

### Sprint 3 Demo

- a gap can be reviewed and resolved
- a decision can be stored
- open versus resolved gaps are visible at project level

## 10. Final Recommendation

Use the following execution order:

1. Sprint 1: Readiness + confidence model
2. Sprint 2: Executive summary + visible grouped gaps
3. Sprint 3: Formal gap and decision workspace

This gives the best balance of:

- visible product value
- controlled database change
- limited UX disruption early
- low rework risk before the workflow model is formalized