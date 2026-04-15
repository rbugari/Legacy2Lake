# v4.5 Plan - Project Intelligence Assistant + Readiness Suite

> Last Updated: 2026-04-15
> Status: Proposed (implementation-ready)
> Scope: Backend + Frontend + Data model + Prompt/LLM integration + Stage UX

## 1. Purpose

v4.5 consolidates five high-value product capabilities into one coherent release:

1. Readiness + Confidence Model
2. Executive / Business Summary + Visible Gaps
3. Gap and Decision Workspace
4. Legacy-to-Target Traceability Review
5. Project Intelligence Assistant (simple chatbot modal in UI)

The intent is to move from static stage outputs to interactive, explainable decision support for operators and clients.

## 2. Product Goal

Enable users to ask practical project questions and receive evidence-based answers grounded in Discovery and Triage metadata, while simultaneously making readiness, gaps, decisions, and traceability explicit and operational.

v4.5 is complete when:

- users can understand project viability quickly
- users can review and resolve gaps with ownership and status
- users can audit legacy-to-target mapping in one place
- users can ask a chat assistant about project metadata and get bounded, non-hallucinated answers

## 3. Non-Negotiable Rules

1. Multi-tenant isolation first: all reads/writes tenant-scoped.
2. Chat answers must be evidence-grounded in project metadata.
3. If data is missing, assistant must answer: no registered information found.
4. No cross-project retrieval in MVP.
5. Use tenant default LLM provider and deployment config already stored in runtime config.
6. Triage rerun invalidates stale chat context and resets thread for that project.
7. Keep UI simple: modal workflow, no major navigation redesign.

## 4. Scope Summary

### In Scope

- project readiness summary model and API
- executive summary API and UI block
- visible grouped gaps
- gap/decision workspace (basic workflow)
- traceability review view for key assets
- modal chat assistant bound to project metadata
- tenant-default LLM usage for answers
- chat history persistence + clear history action
- automatic chat reset on triage rerun

### Out Of Scope

- cross-project semantic search
- autonomous recommendations that invent missing business semantics
- enterprise conversational memory beyond project context
- complex agent orchestration for chat in MVP

## 5. Capability 1 - Readiness + Confidence Model

### Objective

Expose a clear and explainable project-level readiness state.

### MVP Output

- status: READY | BASELINE_READY | REQUIRES_CONTEXT | NOT_RECOMMENDED_FOR_AUTOMATION
- confidence_score (0-100)
- top_reasons
- blockers
- recommended_next_action
- source_signals
- computed_at

### Backend

- service: aggregate existing signals from quick assessment, triage outputs, metadata coverage, governance hints
- endpoints:
  - GET /projects/{project_id}/readiness
  - POST /projects/{project_id}/readiness/recompute

### Data Model (MVP)

- add JSONB field on utm_projects:
  - readiness_summary

### UI

- readiness badge + explanation blocks in Discovery, Triage, Drafting

## 6. Capability 2 - Executive Summary + Visible Gaps

### Objective

Translate technical state into business language and highlight critical gaps.

### MVP Output

- migration posture
- top risks
- manual effort areas
- open blockers
- recommended delivery posture
- grouped gaps by category and severity

### Backend

- endpoints:
  - GET /projects/{project_id}/executive-summary
  - GET /projects/{project_id}/gaps-summary

### UI

- executive summary panel in Governance and Handover
- grouped gaps view with simple drilldown

## 7. Capability 3 - Gap and Decision Workspace

### Objective

Turn scattered findings into actionable and auditable items.

### MVP Data Model

- table: utm_project_gaps
  - id
  - tenant_id
  - project_id
  - category
  - severity
  - title
  - description
  - evidence_refs (jsonb)
  - recommended_owner
  - status (OPEN | IN_REVIEW | RESOLVED | WAIVED)
  - decision_note
  - source_stage
  - created_at / updated_at

### Backend

- CRUD endpoints + list filters
- simple transitions with audit log entries

### UI

- workspace tab with filters by status/category/severity
- edit panel for owner and decision note

## 8. Capability 4 - Legacy-to-Target Traceability Review

### Objective

Provide a clear review surface that explains what was preserved, inferred, changed, or unresolved.

### MVP Output

- asset-level traceability map with badges:
  - PRESERVED
  - INFERRED
  - CHANGED
  - UNRESOLVED

### Backend

- endpoint:
  - GET /projects/{project_id}/traceability/{asset_id}

### UI

- side-by-side review modal/panel in Governance and Handover

## 9. Capability 5 - Project Intelligence Assistant (Chat Modal)

### User Experience (Requested)

- button in stage UI opens a modal chat window
- modal validates project state before enabling conversation:
  - Discovery and Triage must exist
  - if not available: show cannot operate yet message
- when enabled: show help banner with sample questions
- while modal is open, it acts as focused interaction surface for that flow
- include:
  - send question
  - show answer
  - save conversation thread
  - clear history button
- if Triage runs again, chat history is reset automatically (context invalidation)

### Sample Supported Questions (MVP)

- where is this table used?
- where is this field used?
- what dependencies exist for this object?
- what critical gaps are open?
- what is the current readiness and why?

### Chat Behavior Rules

1. Retrieve metadata first, answer second.
2. LLM receives only retrieved project evidence.
3. If no evidence found, reply with explicit no info available message.
4. Include confidence label: high | medium | low.
5. Include evidence references when available.

### LLM Provider Rule

- use tenant default configured provider/model/deployment
- no hardcoded provider in chat service
- fallback to system default only if tenant config missing, with explicit log warning

### Backend Design (Simple MVP)

#### Service

- new service: ProjectAssistantService
  - classify intent (table_usage, field_usage, dependencies, gaps, readiness, unknown)
  - fetch evidence from existing project metadata tables/artifacts
  - compose bounded prompt
  - call tenant default LLM
  - return grounded answer + evidence refs

#### Endpoints

- POST /projects/{project_id}/assistant/chat
- GET /projects/{project_id}/assistant/history
- DELETE /projects/{project_id}/assistant/history

#### History Persistence (MVP)

Recommended minimal model:

- table: utm_project_chat_threads
  - id
  - tenant_id
  - project_id
  - thread_version
  - created_at
  - updated_at
- table: utm_project_chat_messages
  - id
  - tenant_id
  - project_id
  - thread_id
  - role (user | assistant)
  - intent
  - question
  - answer
  - evidence_refs (jsonb)
  - confidence
  - created_at

Rationale:

- simple to query and clear
- avoids bloating utm_projects JSONB with long conversations
- supports reset on triage rerun via thread_version

### Triage Rerun Reset Logic

On triage rerun completion for a project:

1. increment project triage generation/version
2. start new assistant thread version
3. mark old messages archived/inactive (or hard delete for MVP)
4. UI loads only current version
5. show notice: history reset after triage rerun due to metadata changes

Note: this aligns with existing rerun cleanup behavior already applied to stale triage artifacts.

## 10. Security, Isolation, and Explainability

1. Every assistant query filtered by tenant_id and project_id.
2. No cross-tenant vector/index retrieval.
3. Log prompt context references without logging sensitive payloads in plain text.
4. Return explainable answers with evidence refs.
5. Return explicit no information available when evidence is missing.

## 11. API Contracts (Draft)

### POST /projects/{project_id}/assistant/chat

Request:

{
  "message": "where is table customer_orders used?"
}

Response:

{
  "answer": "The table appears in 3 processes: ...",
  "confidence": "high",
  "intent": "table_usage",
  "evidence_refs": [
    {
      "type": "triage_dependency",
      "id": "dep_123",
      "label": "orders_etl -> customer_orders"
    }
  ],
  "thread_id": "...",
  "thread_version": 2,
  "metadata_generation": 2
}

### GET /projects/{project_id}/assistant/history

Response:

{
  "thread_id": "...",
  "thread_version": 2,
  "messages": [
    {
      "role": "user",
      "text": "where is field order_status used?",
      "created_at": "..."
    },
    {
      "role": "assistant",
      "text": "...",
      "confidence": "medium",
      "evidence_refs": []
    }
  ]
}

### DELETE /projects/{project_id}/assistant/history

Response:

{
  "ok": true,
  "cleared": true
}

## 12. Frontend UX Specification (Modal)

### Entry Points

- add Ask Project button in Triage and optional Discovery/Governance headers

### Modal States

1. loading: validating prerequisites
2. blocked: Discovery/Triage missing
3. ready: chat enabled + suggested prompts
4. empty history: helper message
5. active thread: messages list + composer + clear history

### UX Details

- compact modal width with scrollable message area
- show current project name and metadata version
- button: clear history (with confirm)
- if triage rerun detected: auto-refresh + thread reset banner

## 13. Execution Sequence (Recommended)

### Sprint 1 - Readiness + Assistant Core

Deliver:

- readiness summary service + API
- assistant chat endpoint with 3 intents (table, field, gaps)
- modal UI with prerequisite validation
- history persistence + clear history

### Sprint 2 - Executive/Gaps + Assistant Expansion

Deliver:

- executive summary + grouped gaps APIs/UI
- assistant intents for dependencies and readiness questions
- evidence refs in answers
- triage rerun reset integration

### Sprint 3 - Gap Workspace + Traceability Review

Deliver:

- gap workspace CRUD + status transitions
- legacy-to-target traceability panel
- assistant hooks to gap and traceability context

## 14. Definition Of Done (v4.5)

1. readiness state is visible, explainable, and persisted.
2. executive summary and grouped gaps are visible in Governance/Handover.
3. gap workspace allows actionable lifecycle (open to resolved/waived).
4. traceability review works for representative assets.
5. project chat modal answers metadata questions with evidence-bound responses.
6. assistant refuses unsupported questions with explicit no information messaging.
7. assistant uses tenant default LLM config.
8. assistant history can be cleared manually.
9. assistant history resets automatically after triage rerun.
10. all new routes and queries are tenant-safe.

## 15. Risks and Mitigations

1. Risk: hallucinated chat answers.
   - Mitigation: retrieval-first, strict prompt boundaries, no-info fallback.
2. Risk: stale context after re-triage.
   - Mitigation: generation/version reset and thread invalidation.
3. Risk: over-complex first release.
   - Mitigation: intent-limited MVP and modal-first UX.
4. Risk: scope creep into full agent platform.
   - Mitigation: keep one assistant service with deterministic retrieval.

## 16. Implementation Notes

- Reuse existing persistence and stage artifacts before introducing new abstractions.
- Keep prompt architecture stable: use existing L1/L2 model and tenant runtime config.
- Prefer concise UI that complements current stage views.
- Keep logs and reports explainable for operators and client-facing reviews.
