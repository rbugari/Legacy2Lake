# Product Specification - v4.0 Next Adjustments

> Last Updated: 2026-03-21
> Author: Codex product review
> Scope: Product-level adjustments within the current v4.0 model
> Status: Proposed

## 1. Purpose

This document specifies the highest-value product adjustments that should be considered after the v4.0 stabilization work.

The goal is not to redesign the platform architecture. The goal is to increase product value inside the current operating model:

- staged workflow stays
- 3-level prompt architecture stays
- agent chain stays
- multi-tenant model stays
- disk canonical + DB runtime mirror stays

The focus is on making the product:

- easier to trust
- easier to adopt
- easier to explain to customers
- more useful in real delivery programs

## 2. Executive View

The biggest product opportunity is not "generate more code". It is to make Legacy2Lake better at:

1. telling the customer what is realistically migrable
2. exposing what is missing and why it matters
3. showing what was preserved, assumed, changed, or left unresolved
4. helping teams make decisions faster and with more confidence

For that reason, the proposed priorities are:

1. Confidence and readiness model
2. Gap and decision workspace
3. Legacy-to-target traceability review
4. Explicit modernization modes
5. Business-facing deliverables
6. Reusable approved knowledge library

## 3. Prioritized Changes

## Priority 1 - Confidence And Readiness Model

### Problem

The platform already produces technical outputs, but the user still has to infer:

- how reliable the result is
- whether it is usable as-is
- whether it is only a baseline
- whether more business context is required

That creates friction and uncertainty, especially in enterprise settings.

### Product Change

Introduce a visible confidence/readiness model at project level and asset level.

Suggested model:

- `READY`
- `BASELINE_READY`
- `REQUIRES_CONTEXT`
- `NOT_RECOMMENDED_FOR_AUTOMATION`

### What The User Should See

For each asset and for the project overall:

- readiness label
- confidence score
- top 3 reasons
- blocking gaps if any
- recommended next action

### Value

- increases trust
- sets expectations better
- helps commercial positioning
- gives PMs and architects a decision surface, not just a code artifact

### Implementation Impact

Frontend:

- add readiness badges and summary cards
- add explanations in Triage and Drafting views

Backend:

- define scoring rules and aggregation model
- combine signals from Quick Assessment, Agent A, Agent F, Agent G, validation, and metadata coverage

Data model:

- add persisted readiness fields at asset and/or project level
- optionally store explanation payloads

Prompt impact:

- low to medium
- mostly a synthesis/orchestration feature, not a prompt rewrite

### Complexity

Medium

### Risks

- false precision if scoring is too opaque
- score inflation if business gaps are ignored

### Recommendation

Implement first. This adds product value quickly without destabilizing the existing runtime.

---

## Priority 2 - Gap And Decision Workspace

### Problem

The platform detects gaps, but today those gaps are still too technical and too scattered.

The user needs a central place to answer:

- what is missing
- why it matters
- who should provide it
- what becomes better once it is resolved

### Product Change

Create a workspace for gaps and decisions.

Each item should have:

- category
- severity
- impacted assets
- why it matters
- recommended owner
- resolution status
- optional user decision or note

Suggested categories:

- schema
- mappings
- business rules
- orchestration
- data quality
- compliance
- target architecture choice

### Value

- turns the product into a guided migration workspace
- reduces repeated conversations
- makes Level 3 custom instructions more purposeful
- improves collaboration between business and engineering

### Implementation Impact

Frontend:

- new workspace tab or side panel
- item list with filtering and resolution states

Backend:

- normalize gaps from Agent S, Agent A, Agent F, Agent G, and deterministic services
- add CRUD endpoints for resolution and decision capture

Data model:

- new table for project decisions / unresolved gaps
- optional links to assets and stages

Prompt impact:

- low
- prompts can stay mostly the same

### Complexity

Medium to high

### Risks

- too much manual overhead if the UX is heavy
- duplicate signals if normalization is weak

### Recommendation

Implement second. This is one of the strongest product differentiators inside the current model.

---

## Priority 3 - Legacy To Target Traceability Review

### Problem

One of the hardest questions in modernization is:

- what did the system preserve
- what changed
- what is inferred
- what is still missing

Today that answer exists partially across artifacts, but not as a single product experience.

### Product Change

Add a comparison review between legacy asset and generated target artifact.

The review should highlight:

- preserved logic
- inferred logic
- omitted or unknown logic
- introduced changes
- unresolved assumptions

It should work especially well for:

- SQL -> SQL
- DTSX -> SQL
- DTSX -> PySpark

### Value

- dramatically improves reviewability
- increases customer confidence
- helps validation and sign-off
- reduces fear of "black box AI"

### Implementation Impact

Frontend:

- side-by-side review experience
- badges for preserved / inferred / unresolved sections

Backend:

- generate structured traceability metadata during or after Agent C / Agent F
- optionally enrich with Agent G summary

Data model:

- store traceability items per asset

Prompt impact:

- medium
- Agent C and/or Agent F may need to emit more structured mapping information

### Complexity

High

### Risks

- traceability quality depends on source parsing quality
- risk of noisy or shallow comparisons if the model is under-specified

### Recommendation

Implement third. This is expensive but highly defensible as product value.

---

## Priority 4 - Explicit Modernization Modes

### Problem

The platform already behaves differently for `direct` versus medallion-oriented modernization, but the product experience does not surface that distinction strongly enough.

That can create expectation mismatches.

### Product Change

Make modernization modes explicit in the product.

Suggested modes:

- `Direct Translation`
- `Modernized Target`
- `Governed Enterprise Output`

The exact labels can change, but the user must understand what each mode optimizes for.

### Value

- reduces confusion
- makes output intent clearer
- improves commercial narrative
- helps explain why some outputs do not include redesign features

### Implementation Impact

Frontend:

- mode selector and explanation text
- mode summary in project settings and output views

Backend:

- map mode to existing layer/cartucho strategy
- ensure downstream services understand the selected mode

Prompt impact:

- medium
- some prompts may need clearer mode-specific contracts

### Complexity

Medium

### Risks

- naming confusion if the modes overlap
- too many choices can hurt UX

### Recommendation

Implement in parallel with the gap workspace or immediately after it.

---

## Priority 5 - Business-Facing Deliverables

### Problem

The platform generates technically useful artifacts, but product value for sponsors, PMs, and non-engineering stakeholders is still underexposed.

### Product Change

Add concise business-facing summaries such as:

- project migrability summary
- top risks
- decision blockers
- expected manual effort areas
- delivery recommendation

This should not replace technical artifacts. It should sit above them.

### Value

- broadens the buyer and stakeholder audience
- supports steering committees and PMO workflows
- helps justify the product internally

### Implementation Impact

Frontend:

- executive summary view
- exportable report blocks

Backend:

- summarize technical findings into business-facing language

Prompt impact:

- low to medium
- mostly summarization and packaging

### Complexity

Medium

### Risks

- over-simplification
- summaries becoming too generic

### Recommendation

Implement after readiness model, because the executive view should be grounded in that signal.

---

## Priority 6 - Reusable Approved Knowledge Library

### Problem

Projects repeat patterns, but today those repeated lessons are not yet productized enough.

### Product Change

Create a governed library of approved reusable knowledge:

- approved mappings
- known migration patterns
- target-specific snippets
- common exceptions
- validated domain rules

This should be curated and reusable, not opaque model memory.

### Value

- increases repeatability
- reduces effort over time
- improves consistency across projects
- creates compounding product value

### Implementation Impact

Frontend:

- library browsing and linking

Backend:

- retrieval and relevance logic
- approval state and governance

Data model:

- library entities and references

Prompt impact:

- medium
- improves grounding quality

### Complexity

High

### Risks

- poor governance can create junk accumulation
- stale knowledge can mislead future projects

### Recommendation

Important, but not first. This becomes much more valuable after the decision workspace exists.

## 4. Suggested Delivery Order

### Wave 1 - High Value, Lower Disruption

1. Confidence and readiness model
2. Gap and decision workspace
3. Business-facing summaries

### Wave 2 - High Value, More Structural

4. Explicit modernization modes
5. Legacy-to-target traceability review

### Wave 3 - Compounding Value

6. Reusable approved knowledge library

## 5. Impact Summary

| Change | Product Value | Technical Impact | Prompt Impact | Complexity | Priority |
|---|---|---|---|---|---|
| Confidence/readiness model | Very high | Medium | Low | Medium | P1 |
| Gap/decision workspace | Very high | Medium/High | Low | Medium/High | P1 |
| Legacy-to-target traceability | Very high | High | Medium | High | P2 |
| Explicit modernization modes | High | Medium | Medium | Medium | P2 |
| Business-facing summaries | High | Medium | Low/Medium | Medium | P1 |
| Reusable knowledge library | High long-term | High | Medium | High | P3 |

## 6. What Should Not Change Yet

To protect delivery focus, these should remain stable during this phase:

- the 3-level prompt model
- disk canonical + DB runtime mirror
- main agent chain
- tenant-based LLM resolution
- current stage model

This specification is about increasing product value without reopening the architecture unnecessarily.

## 7. Final Recommendation

If only one theme is chosen, prioritize:

`confidence + gaps + decisions`

That combination gives the biggest product upgrade because it transforms Legacy2Lake from "a system that generates artifacts" into "a system that helps customers decide, prioritize, and move safely through modernization work."

If two themes are chosen, add:

`legacy-to-target traceability`

That is the feature most likely to increase trust during real customer review.
