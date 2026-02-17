# AI Infrastructure: Multi-LLM Strategy (v4.0)

**Last Updated:** Febrero 17, 2026  
**Sprint:** Sprint 14 Phase 2 (85% complete)  
**Status:** Production Ready (Multi-Tenant Agent Matrix)

Legacy2Lake está diseñado para ser inteligente pero agnóstico del "cerebro" (LLM) específico que lo impulsa. Este documento describe cómo configurar múltiples proveedores LLM y asignar modelos a agentes específicos mediante el sistema **Agent Matrix** multi-tenant.

---

## 1. Provider Abstraction (LLM Router)

La plataforma soporta los siguientes proveedores mediante abstracción en la capa de persistencia:

### Proveedores Soportados

| Proveedor | Uso Recomendado | Modelos Típicos | Storage DB |
|-----------|-----------------|-----------------|------------|
| **Azure OpenAI** | Ambientes corporativos seguros | GPT-4o, GPT-4-turbo, GPT-3.5-turbo | `utm_provider_vault` |
| **OpenAI (Direct)** | Acceso a modelos de última generación | GPT-4o, GPT-4-turbo, o1-preview | `utm_provider_vault` |
| **Anthropic** | Claude 3.5 Sonnet para tareas complejas | Claude 3.5 Sonnet, Claude 3 Opus | `utm_provider_vault` |
| **Groq** | Inferencia ultra-rápida (Llama 3) | Llama 3 70B, Llama 3.1 405B | `utm_provider_vault` |

### Base de Datos: utm_provider_vault

**Tabla para credenciales LLM por tenant:**
```sql
CREATE TABLE utm_provider_vault (
    vault_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id),
    provider_name TEXT NOT NULL, -- 'openai', 'azure', 'anthropic', 'groq'
    api_key TEXT NOT NULL,
    base_url TEXT,
    deployment_name TEXT, -- Solo para Azure
    api_version TEXT, -- Solo para Azure
    metadata JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Ejemplo de inserción:**
```sql
-- Azure OpenAI provider
INSERT INTO utm_provider_vault (tenant_id, provider_name, api_key, base_url, deployment_name, api_version)
VALUES (
    'abc-123-tenant-id',
    'azure',
    'your-azure-api-key',
    'https://your-endpoint.openai.azure.com',
    'gpt-4o-deployment',
    '2024-05-01-preview'
);

-- OpenAI (Direct) provider
INSERT INTO utm_provider_vault (tenant_id, provider_name, api_key, base_url)
VALUES (
    'abc-123-tenant-id',
    'openai',
    'sk-proj-...',
    'https://api.openai.com/v1'
);
```

---

## 2. Agent Matrix: Multi-Tenant Agent-to-Model Mapping

**Nuevo en v3.9:** Cada tenant configura qué modelo LLM usa cada agente mediante la tabla `utm_agent_matrix`.

### Los 6 Agentes del Sistema

| Agent ID | Nombre | Fase | Responsabilidad | Modelo Sugerido |
|----------|--------|------|-----------------|-----------------|
| **agent-s** | Scout | Discovery | Detección de tecnología origen | GPT-3.5-turbo, Azure GPT-35 |
| **agent-a** | Architect | Triage & Refinement | Análisis forense + diseño Medallion | GPT-4o, Claude 3.5 |
| **agent-c** | Coder | Drafting | Generación de código con cartridges | GPT-4o, Claude 3.5 Sonnet |
| **agent-f** | Critic | Drafting | Validación y scoring (0-10) | GPT-4o, Claude 3.5 |
| **agent-p** | Profiler | Refinement | Análisis de código generado | GPT-3.5-turbo (análisis simple) |
| **agent-g** | Governance | Certification | Auditoría compliance + Runbook | GPT-4o, Claude 3.5 |

### Base de Datos: utm_agent_matrix

**Tabla de mapeo agent → model por tenant:**
```sql
CREATE TABLE utm_agent_matrix (
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id),
    agent_id TEXT NOT NULL, -- 'agent-a', 'agent-c', etc.
    model_id TEXT NOT NULL, -- 'azure-gpt-4o', 'claude-3-5-sonnet', etc.
    phase TEXT, -- 'discovery', 'drafting', 'refinement', 'certification'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (tenant_id, agent_id, phase)
);
```

**Ejemplo de configuración:**
```sql
-- Configuración para tenant ejemplar (todos Azure GPT-4o)
INSERT INTO utm_agent_matrix (tenant_id, agent_id, model_id, phase, is_active) VALUES
('abc-123', 'agent-s', 'azure-gpt-35-turbo', 'discovery', true),
('abc-123', 'agent-a', 'azure-gpt-4o', 'triage', true),
('abc-123', 'agent-c', 'azure-gpt-4o', 'drafting', true),
('abc-123', 'agent-f', 'azure-gpt-4o', 'drafting', true),
('abc-123', 'agent-p', 'azure-gpt-35-turbo', 'refinement', true),
('abc-123', 'agent-a', 'azure-gpt-4o', 'refinement', true),
('abc-123', 'agent-g', 'azure-gpt-4o', 'certification', true);
```

### Base de Datos: utm_model_catalog

**Catálogo de modelos habilitados por tenant:**
```sql
CREATE TABLE utm_model_catalog (
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id),
    model_id TEXT NOT NULL, -- Identificador único: 'azure-gpt-4o', 'openai-gpt-4-turbo'
    provider TEXT NOT NULL, -- 'azure', 'openai', 'anthropic', 'groq'
    label TEXT NOT NULL, -- Nombre amigable: "GPT-4 Optimized"
    context_window INTEGER DEFAULT 8192,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (tenant_id, model_id)
);
```

**Ejemplo de catálogo:**
```sql
INSERT INTO utm_model_catalog (tenant_id, model_id, provider, label, context_window) VALUES
('abc-123', 'azure-gpt-4o', 'azure', 'GPT-4 Optimized', 128000),
('abc-123', 'azure-gpt-35-turbo', 'azure', 'GPT-3.5 Turbo', 16385),
('abc-123', 'claude-3-5-sonnet', 'anthropic', 'Claude 3.5 Sonnet', 200000);
```

---

## 3. Resolución de Modelos en Tiempo de Ejecución

Cada agente resuelve su modelo LLM dinámicamente desde la base de datos:

### Código Python (Agent Service Pattern)

```python
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_anthropic import ChatAnthropic

class AgentCService:
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
    
    async def _get_llm(self, project_id: Optional[str] = None):
        """Resolves LLM client strictly from Agent Matrix (DB)"""
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        
        # Query utm_agent_matrix + utm_model_catalog + utm_provider_vault
        config = await db.resolve_agent_model("agent-c")
        
        # Returns: {
        #   "provider": "azure",
        #   "model": "gpt-4o",
        #   "deployment_name": "gpt-4o-deployment",
        #   "api_key": "...",
        #   "endpoint": "https://..."
        # }
        
        if config["provider"] == "azure":
            return AzureChatOpenAI(
                deployment_name=config["deployment_name"],
                api_key=config["api_key"],
                azure_endpoint=config["endpoint"],
                api_version=config.get("api_version", "2024-05-01-preview")
            )
        elif config["provider"] == "anthropic":
            return ChatAnthropic(
                model=config["model"],
                api_key=config["api_key"]
            )
        else:  # openai, groq
            return ChatOpenAI(
                model=config["model"],
                api_key=config["api_key"],
                base_url=config.get("base_url")
            )
```

### Flujo de Resolución

1. **Agent Service** llama `db.resolve_agent_model("agent-c")`
2. **SupabasePersistence** ejecuta JOIN:
   ```sql
   SELECT 
     am.model_id,
     mc.provider,
     mc.label,
     pv.api_key,
     pv.base_url,
     pv.deployment_name,
     pv.api_version
   FROM utm_agent_matrix am
   JOIN utm_model_catalog mc ON am.model_id = mc.model_id
   JOIN utm_provider_vault pv ON mc.provider = pv.provider_name
   WHERE am.tenant_id = $1 AND am.agent_id = $2 AND am.is_active = true
   ```
3. **Config** se pasa a LangChain para instanciar el cliente correcto
4. **Agent** usa el LLM resuelto para ejecutar su tarea

---

## 4. Stability & Failover (Future v4.1+)

**Roadmap para v4.1:**
- **Automatic Failover:** Si un proveedor falla o alcanza rate limits, el LLM Router cambiará automáticamente al modelo de fallback definido
- **Load Balancing:** Distribuir carga entre múltiples deployments del mismo modelo
- **Cost Optimization:** Selección automática del modelo más económico que cumpla con SLA de calidad
- **A/B Testing:** Pruebas simultáneas de prompts en diferentes modelos para optimización continua

**Estado Actual (v3.9 GA):**
- ✅ Multi-tenant agent matrix operacional
- ✅ Soporte para 4 proveedores (Azure, OpenAI, Anthropic, Groq)
- ✅ Resolución dinámica de modelos desde BD
- ⏳ Failover automático (próxima versión)

---

## 5. Best Practices

### Para Platform Admins (MANAGER)

1. **Habilitar Modelos:** Insertar entries en `utm_model_catalog` con modelos disponibles
2. **Configurar Proveedores:** Agregar API keys en `utm_provider_vault` por tenant
3. **Agent Matrix por Default:** Configurar mapeo estándar para nuevos tenants

### Para Tenant Admins

1. **Revisar Catálogo:** Ver modelos habilitados por el MANAGER
2. **Asignar Agentes:** Configurar qué modelo usa cada agente en `utm_agent_matrix`
3. **Monitorear Costos:** Elegir modelos balanceando performance vs. costo
   - **GPT-3.5-turbo:** Tareas simples (Agent S, Agent P)
   - **GPT-4o:** Tareas complejas (Agent A, Agent C, Agent F, Agent G)
   - **Claude 3.5:** Análisis de contexto largo

### Recomendaciones por Fase

| Fase | Agent | Modelo Recomendado | Justificación |
|------|-------|--------------------|---------------|
| Discovery | Agent S | GPT-3.5-turbo | Detección simple de patrones |
| Triage | Agent A | GPT-4o / Claude 3.5 | Análisis forense complejo |
| Drafting | Agent C + F | GPT-4o / Claude 3.5 | Generación de código de calidad |
| Refinement | Agent P + A | GPT-3.5 (P) + GPT-4o (A) | Profiling simple + diseño complejo |
| Certification | Agent G | GPT-4o / Claude 3.5 | Auditoría y documentación detallada |

---

## 6. Migración desde v3.8 (Legacy)

**v3.8 y anteriores:** Variables de entorno hardcodeadas (.env)
```bash
OPENAI_API_KEY="sk-proj-..."  # ❌ Compartido entre todos los tenants
DEFAULT_MODEL="gpt-4o"         # ❌ Mismo modelo para todos
```

**v3.9 GA:** Base de datos multi-tenant
```sql
-- ✅ Cada tenant tiene sus propias API keys
-- ✅ Cada tenant configura sus propios modelos por agente
-- ✅ Aislamiento total entre clientes
```

**Proceso de Migración:**
1. Ejecutar `sprint_v3.9_agent_matrix.sql` migration
2. Insertar API keys en `utm_provider_vault` por tenant  
3. Habilitar modelos en `utm_model_catalog`
4. Configurar `utm_agent_matrix` con mapeos agent → model
5. Eliminar variables de entorno LLM del `.env`

---

**Documentos Relacionados:**
- [System Prompts and Agents](./system_prompts_and_agents.md)
- [ENV vs Database Configuration](../ENV_VS_DATABASE.md)
- [Database Schema](../DATABASE_SCHEMA.md)
