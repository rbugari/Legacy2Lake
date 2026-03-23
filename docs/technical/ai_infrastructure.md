# AI Infrastructure: Multi-LLM Strategy (v4.0 Stabilized)

> Last Updated: 2026-03-21
> Status: Production

Legacy2Lake is LLM-agnostic at the platform level and tenant-specific at runtime. Agents resolve their provider and deployment dynamically from tenant configuration.

## 1. Resolution Model

Each LLM agent resolves configuration through:

1. `utm_agent_matrix`
2. `utm_model_catalog`
3. `utm_provider_vault`

This produces runtime configuration such as:

- provider
- deployment or model name
- endpoint
- API key
- api version
- temperature

There is no hardcoded model ownership inside the agents.

## 2. LLM Agents

The active LLM roster is:

- `agent-qa`
- `agent-s`
- `agent-a`
- `agent-c`
- `agent-f`
- `agent-g`
- `agent-d`

## 3. Prompt And Model Separation

Prompt governance and model governance are separate concerns:

- prompts:
  - disk canonical for Levels 1 and 2
  - DB runtime mirror
- models:
  - always tenant-resolved through Agent Matrix and Provider Vault

This means two tenants can use the same prompt set with different LLM providers or deployments.

## 4. Typical Provider Patterns

Common provider families include:

- Azure OpenAI
- OpenAI direct
- Anthropic
- Groq

The exact available models depend on tenant configuration in the database.

## 5. Current Validation Example

On `2026-03-21`, the stabilized runtime was validated with Azure `gpt-4.1` on a real SSIS fixture through the chain:

- `agent-a`
- `agent-c`
- `agent-f`
- `agent-g`

This confirms that:

- tenant-specific model resolution is working
- prompt assembly and runtime prompt loading are working
- the same orchestration can support SQL and Python-family outputs

## 6. Operational Notes

- if an agent has no active model assignment, that agent should fail clearly rather than silently falling back
- Level 3 project custom instructions do not alter model selection
- project context and cartridge selection change the prompt package, not the LLM resolution path
