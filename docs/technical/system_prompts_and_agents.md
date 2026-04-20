# System Prompts And Agents (v4.0 Stabilized)

> Last Updated: 2026-04-15
> Status: Current operating model

This document describes the real agent roster, the prompt architecture in production, and how prompt resolution works after the v4.0 prompt consolidation.

## 1. Agent Roster

Legacy2Lake currently operates with `10` named agents or engines:

### LLM agents

| Agent ID | Name | Responsibility |
|---|---|---|
| `agent-qa` | Quick Assessor | Pre-triage viability assessment |
| `agent-s` | Scout | Repository forensics and gap detection |
| `agent-a` | Detective | Triage mesh construction and modernization reasoning |
| `agent-c` | Developer | Code generation and transpilation |
| `agent-f` | Critic | Per-asset review and scoring |
| `agent-g` | Governor | Governance audit and runbook generation |
| `agent-d` | Auditor | Final audit in later refinement/certification flows |

### Deterministic engines

| Agent ID | Name | Responsibility |
|---|---|---|
| `agent-p` | Profiler | Static analysis of generated assets |
| `agent-r` | Refactoring | Deterministic optimization/refactoring |
| `agent-o` | OpsAuditor | Operational readiness and DevOps packaging |

## 2. Prompt Architecture

Legacy2Lake uses a 3-level prompt model.

### Level 1: Agent prompt

- Owned by the application
- Canonical source lives on disk
- Synchronized to `utm_prompts`
- Not editable by tenant users

Examples:

- `agent_qa_assessment`
- `agent_s_scout`
- `agent_a_discovery`
- `agent_c_interpreter`
- `agent_f_critic`
- `agent_g_governance`
- `agent_d_auditor`

### Level 2: Cartridge prompt

- Owned by the application
- Canonical source lives on disk
- Synchronized to `utm_prompts`
- Specializes behavior by `tech_stack` and `layer`
- Not editable by tenant users

Layers currently in scope:

- `bronze`
- `silver`
- `gold`
- `direct`

### Level 3: Project custom instructions

- Optional
- Empty by default
- Stored as project settings / overrides
- Used only for project-specific rules or context the user knows and the platform cannot infer safely

Level 3 is not a replacement for Level 1 or Level 2. The system is expected to behave correctly without it.

## 3. Canonical Prompt Source

The current model is:

- disk = canonical source for app-governed prompts
- Supabase = runtime mirror
- project settings = optional Level 3 custom rules

The active canonical prompt inventory is `48` prompts:

- `7` agent prompts
- `1` shared standards prompt
- `40` cartridge prompts

Legacy `cartridge_*` prompt ids are no longer part of the active runtime path.

## 4. Prompt Resolution

At runtime, the platform resolves prompts in this order:

1. load the agent prompt
2. load the cartridge prompt for the selected `tech_stack` and `layer`
3. load optional project custom instructions if present
4. assemble final prompt package for the target agent

The important design rule is:

- Level 1 should remain technology-neutral where possible
- Level 2 should define target-specific behavior
- Level 3 should only add project context, not redefine platform architecture

## 5. Agent Contracts

### Agent QA

- Input: discovery summary and project context
- Output: viability assessment JSON
- Notes: now part of the canonical prompt model

### Agent S

- Input: repository inventory and contextual signals
- Output: forensic assessment and gaps

### Agent A

- Input: manifest plus runtime context such as `tech_stats`, `file_inventory`, `user_context`, `support_intelligence`, and `schema_reference`
- Output: modernization mesh and triage reasoning

### Agent C

- Input:
  - task context
  - agent prompt
  - cartridge rules
  - optional custom rules
  - neighboring and metadata context when available
- Output:
  - code
  - explanation
  - assumptions
  - requirements
  - validation metadata
- Notes:
  - multi-target by design
  - no longer PySpark-first in the core prompt
  - applies mode-aware runtime context (drafting delivery vs refinement modes)

### Agent F

- Input: generated asset plus the same target-aware cartridge context
- Output: review object with score and critique
- Notes: evaluates against the actual target, not a fixed PySpark worldview
  - in drafting delivery/direct review, can normalize rejection outcomes when code is executable and only non-structural objections remain
  - hardcoded-literal violations remain explicit blockers

### Agent G

- Input: transformed assets, metadata, mesh
- Output:
  - `audit_json`
  - `runbook_markdown`
- Notes: supports SQL and Python outputs and was validated against fenced JSON with embedded markdown

## 6. Cartridge Matrix

The current cartridge matrix is `10` tech stacks x `4` layers:

| Tech Stack | bronze | silver | gold | direct |
|---|---|---|---|---|
| `base` | yes | yes | yes | yes |
| `pyspark` | yes | yes | yes | yes |
| `snowflake` | yes | yes | yes | yes |
| `snowflake_sql` | yes | yes | yes | yes |
| `sf` | yes | yes | yes | yes |
| `aws` | yes | yes | yes | yes |
| `dbt` | yes | yes | yes | yes |
| `gcp` | yes | yes | yes | yes |
| `ms_fabric` | yes | yes | yes | yes |
| `ms_fabric_sql` | yes | yes | yes | yes |

## 7. Direct Layer

The `direct` layer is intentionally different from medallion layers:

- goal is faithful translation, not architectural redesign
- prompts require explicit `L2L DIRECT TRANSLATION` headers
- prompts prohibit invented enhancements
- prompts prefer parameterization over hardcoded values
- prompts prefer explicit column mapping when metadata exists

This is especially important for `SQL` and `PySpark` direct outputs derived from SSIS or legacy SQL.

## 8. v4.4 Runtime Notes

- post-drafting mode (`drafting_delivery`, `structured_refinement`, `intelligent_reengineering`) is resolved at runtime and passed through generation/review flows
- direct-mode validation includes strict no-hardcode checks for literal defaults and helper assignments
- refinement/governance consume mode context for manifest summaries and mode-aware scoring narratives
