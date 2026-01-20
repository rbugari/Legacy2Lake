# AI Infrastructure: Multi-LLM Strategy

Legacy2Lake is designed to be intelligent yet agnostic of the specific brain (LLM) powering it. This specification describes how to configure multiple LLM providers and assign models to specific agents.

## 1. Provider Abstraction (LLM Router)

The platform supports a routing layer for the following providers:
- **Azure OpenAI**: For secure, corporate environments.
- **OpenAI (Direct)**: For cutting-edge model access.
- **Groq**: For ultra-fast inference during massive transformations (Llama 3).
- **OpenRouter**: For diverse Open Source model access.

## 2. Agent-to-Model Mapping

Each agent in the Legacy2Lake workforce can be assigned a specific model to balance cost and performance:

| Agent | Task Profile | Suggested Model |
| :--- | :--- | :--- |
| **Detective** | Structrual Context | `GPT-4o` / `Claude 3.5` |
| **Kernel** | Logical Reasoning | `GPT-4o` / `Llama 3.1 405B` |
| **Generator** | Template Synthesis | `Llama 3 70B (Groq)` |
| **Critic (QA)** | Code Validation | `GPT-4o-turbo` |

## 3. Configuration Schema

```json
{
  "agent_id": "kernel_logic_mapper",
  "active_provider": "GROQ",
  "models": {
    "primary": "llama3-70b-8192",
    "fallback": "gpt-4-turbo"
  }
}
```

## 4. Stability & Failover

In future releases, if a primary provider fails or hits rate limits, the **LLM Router** will automatically switch to the defined fallback model, ensuring modernization processes are never interrupted.
