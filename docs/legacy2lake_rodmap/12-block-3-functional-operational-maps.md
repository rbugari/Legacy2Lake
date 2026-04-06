# Block 3 Execution Pack - Functional and Operational Maps

## Purpose

Freeze the current direction in a single document and define an executable plan for Block 3 so the team can continue without reinterpreting intent.

This block turns project knowledge into explainable outputs:

1. functional map
2. operational map
3. recommendation set
4. rule candidate summary

## Context Lock (2026-04-01)

Current platform baseline already available:

1. Discovery intake and evidence review are persisted and reusable.
2. Triage rerun is operational with better context handling.
3. Executive summary and gaps already consume structured project signals.
4. Knowledge-first roadmap is documented and staged.

What this block must solve now:

1. formalize explainable outputs from existing facts and inferences
2. make uncertainty explicit per output section
3. keep one contract for multiple downstream consumers

## Block 3 Scope

Included:

1. project-level `functional_map`
2. project-level `operational_map`
3. project-level `recommendation_set`
4. project-level `rule_candidate_summary`
5. confidence and uncertainty model for each output section
6. API read endpoints and UI read panels
7. deterministic tests and fixtures

Excluded for this block:

1. new autonomous agents
2. long-running graph engines
3. enterprise export formats beyond JSON/Markdown initial output

## Contract First

### 1) Functional Map

`functional_map` should answer: what business-capable flows exist and which assets support each flow.

Minimum structure:

```json
{
  "version": "v1",
  "generated_at": "2026-04-01T00:00:00Z",
  "domains": [
    {
      "name": "sales",
      "capabilities": [
        {
          "name": "daily_sales_load",
          "assets": ["asset:pkg_sales_etl"],
          "datasets": ["dbo.fact_sales"],
          "evidence_refs": ["ev:123"],
          "confidence": 0.82,
          "uncertainty": []
        }
      ]
    }
  ]
}
```

### 2) Operational Map

`operational_map` should answer: how execution happens over time, dependencies, and likely bottlenecks.

Minimum structure:

```json
{
  "version": "v1",
  "generated_at": "2026-04-01T00:00:00Z",
  "processes": [
    {
      "id": "proc:daily_sales",
      "trigger": "schedule",
      "schedule_hint": "0 2 * * *",
      "depends_on": ["proc:stage_orders"],
      "inputs": ["stg.orders"],
      "outputs": ["dbo.fact_sales"],
      "constraints": ["window_before_06_00"],
      "fragility_signals": ["single_failure_blocks_chain"],
      "evidence_refs": ["ev:456"],
      "confidence": 0.76,
      "uncertainty": ["retry_policy_not_confirmed"]
    }
  ]
}
```

### 3) Recommendation Set

`recommendation_set` should separate recommendation from fact.

Minimum structure:

```json
{
  "version": "v1",
  "generated_at": "2026-04-01T00:00:00Z",
  "items": [
    {
      "id": "rec:001",
      "category": "migration_strategy",
      "statement": "Migrate orchestration first, then transformation packages.",
      "rationale": "Current chain has central scheduler dependency.",
      "based_on": ["proc:daily_sales", "ev:456"],
      "impact": "high",
      "effort": "medium",
      "confidence": 0.73,
      "uncertainty": ["nightly_peak_variation_unknown"]
    }
  ]
}
```

### 4) Rule Candidate Summary

`rule_candidate_summary` should capture reusable logic candidates, not final enterprise rules.

Minimum structure:

```json
{
  "version": "v1",
  "generated_at": "2026-04-01T00:00:00Z",
  "candidates": [
    {
      "id": "rulecand:tax_rounding_01",
      "pattern": "round_tax_2_decimals",
      "observed_in_assets": ["asset:pkg_tax_a", "asset:pkg_tax_b"],
      "sample_expression": "ROUND(tax_amount, 2)",
      "reuse_scope": "project",
      "evidence_refs": ["ev:789"],
      "confidence": 0.81,
      "uncertainty": []
    }
  ]
}
```

## Persistence Strategy

Use JSONB-first on `utm_projects` to move fast, then split to dedicated tables only when lifecycle complexity requires it.

Fields to add or confirm in project-level settings or summary payload:

1. `functional_map_v1`
2. `operational_map_v1`
3. `recommendation_set_v1`
4. `rule_candidate_summary_v1`
5. `understanding_generated_at`
6. `understanding_version`

## Service and API Plan

Backend service layer:

1. extend executive/understanding service to build the four artifacts from current facts
2. enforce confidence and uncertainty presence in every item
3. keep evidence references normalized (`evidence_refs`)

API surface (read-first):

1. `GET /projects/{project_id}/understanding/functional-map`
2. `GET /projects/{project_id}/understanding/operational-map`
3. `GET /projects/{project_id}/understanding/recommendations`
4. `GET /projects/{project_id}/understanding/rule-candidates`
5. `POST /projects/{project_id}/understanding/rebuild` (manual deterministic rebuild)

## UI Plan

Add read panels in existing workspace flow, no new top-level route:

1. functional map panel in Triage or Executive summary
2. operational map panel with dependency chain and fragility hints
3. recommendations panel grouped by impact and effort
4. rule candidates panel with evidence drill-down

Each panel must show:

1. confidence
2. uncertainty
3. evidence links
4. last generation timestamp

## Test Plan

Minimum deterministic coverage:

1. service tests for each map contract shape
2. tests validating confidence and uncertainty are always present
3. router tests for all read endpoints
4. fixture tests for at least one ETL-heavy and one SQL-heavy project sample

Acceptance checks:

1. a reviewer can understand main business flows without reading raw source files
2. a reviewer can trace each recommendation to evidence
3. uncertainty is explicit and not hidden
4. outputs are serializable and reusable by downstream consumers

## Execution Sequence (Recommended)

1. lock schemas and payload contracts
2. implement service builder for the four outputs
3. expose read endpoints
4. expose UI panels
5. add tests and fixture validations
6. run manual rebuild and inspect one real project end-to-end

## Definition of Done

Block 3 is done when:

1. all four artifacts are generated with stable v1 schema
2. each artifact item includes confidence, uncertainty, and evidence refs
3. API and UI can read outputs without ad hoc parsing
4. deterministic test suite is green for this block

## Handoff Note

If work pauses, resume from step 1 in the execution sequence and do not change contracts without updating this document and the roadmap index.