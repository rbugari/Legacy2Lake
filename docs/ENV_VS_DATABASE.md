# CONFIGURACIÓN: .ENV vs BASE DE DATOS

## 🔧 Variables de Entorno (.env) - v3.9

### ✅ QUÉ VA EN .ENV

Variables de **INFRAESTRUCTURA** que son únicas por deployment (DEV, PROD):

```bash
# 1. BASE DE DATOS (Supabase)
SUPABASE_URL                  # URL del proyecto Supabase
SUPABASE_SERVICE_ROLE_KEY     # Key con permisos service_role
SUPABASE_ANON_KEY             # Key anónima (opcional)

# 2. ALMACENAMIENTO (R2 o Local)
STORAGE_PROVIDER              # "R2" o "LOCAL"
R2_ACCOUNT_ID                 # Cloudflare account ID
R2_ACCESS_KEY_ID              # R2 access key
R2_SECRET_ACCESS_KEY          # R2 secret key
R2_BUCKET_NAME                # Nombre del bucket
R2_ENDPOINT_URL               # URL del endpoint R2

# 3. EMAIL (SMTP)
SMTP_HOST                     # Servidor SMTP
SMTP_PORT                     # Puerto SMTP
SMTP_USER                     # Usuario email
SMTP_PASS                     # Password email
SENDER_EMAIL                  # Email remitente
FRONTEND_URL                  # URL del frontend

# 4. SERVIDOR
DEBUG_MODE                    # true/false
SERVER_PORT                   # Puerto del backend
NEXT_PUBLIC_API_URL           # URL pública del API
```

---

## ❌ QUÉ NO VA EN .ENV (ahora en DB)

Variables que antes estaban en .env pero **desde v3.9 están en la BASE DE DATOS**:

### Credenciales LLM → `utm_provider_vault`

```sql
-- ANTES (v3.8 y anteriores): En .env compartido
OPENAI_API_KEY="sk-proj-..."
GROQ_API_KEY="gsk_..."
AZURE_OPENAI_API_KEY="..."
ANTHROPIC_API_KEY="sk-ant-..."

-- AHORA (v3.9+): En utm_provider_vault por tenant
INSERT INTO utm_provider_vault (tenant_id, provider_name, api_key, base_url)
VALUES (
  '<tenant_id>',
  'openai',
  'sk-proj-...',
  'https://api.openai.com/v1'
);
```

**Razón**:
- ❌ Antes: Una sola API key compartida entre todos los clientes
- ✅ Ahora: Cada tenant tiene sus propias API keys
- 💰 Cada tenant **paga por su propio uso**
- 🔒 Aislamiento completo entre clientes

### Modelos LLM → `utm_model_catalog`

```sql
-- ANTES (v3.8 y anteriores): En .env
DEFAULT_MODEL="gpt-4o"
MODEL_NAME="gpt-4o"

-- AHORA (v3.9+): En utm_model_catalog por tenant
INSERT INTO utm_model_catalog (tenant_id, model_id, provider, label)
VALUES (
  '<tenant_id>',
  'gpt-4o',
  'openai',
  'GPT-4 Optimized'
);
```

**Razón**:
- Cada tenant selecciona qué modelos habilitar
- Modelos privados, no compartidos
- MANAGER controla catálogo de modelos

---

## 📊 COMPARACIÓN: Legacy vs Multi-Tenant

### Legacy (v3.8 y anteriores)

```
┌─────────────────────────────────┐
│         .env (compartido)       │
├─────────────────────────────────┤
│ OPENAI_API_KEY="sk-..."         │  ← UNA key para TODOS
│ DEFAULT_MODEL="gpt-4o"          │  ← UN modelo para TODOS
│ SUPABASE_URL="..."              │
│ R2_BUCKET_NAME="..."            │
└─────────────────────────────────┘
         ↓
   TODOS los clientes
   usan la misma key
```

### Multi-Tenant (v3.9+)

```
┌─────────────────────────────────┐
│    .env (infraestructura)       │
├─────────────────────────────────┤
│ SUPABASE_URL="..."              │  ← Solo infra
│ R2_BUCKET_NAME="..."            │  ← Solo storage
│ SMTP_HOST="..."                 │  ← Solo email
└─────────────────────────────────┘

┌─────────────────────────────────┐
│  utm_provider_vault (DB)        │
├─────────────────────────────────┤
│ Tenant A:                       │
│  • OpenAI: sk-proj-AAA...       │  ← Su propia key
│  • Groq: gsk_BBB...             │
│                                 │
│ Tenant B:                       │
│  • Azure: azure-key-CCC...      │  ← Su propia key
│  • Anthropic: sk-ant-DDD...     │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│  utm_model_catalog (DB)         │
├─────────────────────────────────┤
│ Tenant A:                       │
│  • gpt-4o                       │  ← Sus modelos
│  • gpt-4o-mini                  │
│                                 │
│ Tenant B:                       │
│  • azure-gpt-4o                 │  ← Sus modelos
│  • claude-3-5-sonnet            │
└─────────────────────────────────┘
```

---

## 🔄 MIGRACIÓN DESDE v3.8

### Paso 1: Limpiar .env

```bash
# Comentar/eliminar estas líneas de .env:
# OPENAI_API_KEY="..."
# GROQ_API_KEY="..."
# AZURE_OPENAI_API_KEY="..."
# AZURE_OPENAI_ENDPOINT="..."
# DEFAULT_MODEL="..."
```

### Paso 2: Configurar proveedores en DB

**Opción A: Via UI** (recomendado)
1. Login como MANAGER
2. Settings → Provider Vault
3. Add Provider (OpenAI, Groq, Azure, etc.)
4. Pegar API key
5. Select Models

**Opción B: Via SQL**
```sql
-- 1. Agregar proveedor
INSERT INTO utm_provider_vault (tenant_id, provider_name, api_key, base_url)
VALUES (
  'your-tenant-id',
  'openai',
  'sk-proj-YOUR-KEY',
  'https://api.openai.com/v1'
);

-- 2. Habilitar modelos
INSERT INTO utm_model_catalog (tenant_id, model_id, provider, label)
VALUES
  ('your-tenant-id', 'gpt-4o', 'openai', 'GPT-4 Optimized'),
  ('your-tenant-id', 'gpt-4o-mini', 'openai', 'GPT-4 Mini');
```

---

## 🔒 SEGURIDAD

### .env (Infraestructura)
- ✅ Debe estar en `.gitignore`
- ✅ Una copia por environment (DEV, PROD)
- ✅ Acceso restringido a DevOps/Admin
- ⚠️ NO debe tener API keys de LLM

### utm_provider_vault (Credenciales LLM)
- ✅ Encriptado en DB (TODO: implementar pgcrypto)
- ✅ RLS policies para aislamiento tenant
- ✅ Cada MANAGER configura sus propias keys
- ⚠️ Solo visible para service_role y MANAGER del tenant

---

## 🎯 RESUMEN

| Variable | v3.8 (Legacy) | v3.9 (Multi-Tenant) | Responsable |
|----------|---------------|---------------------|-------------|
| `SUPABASE_URL` | .env | .env | DevOps |
| `R2_BUCKET_NAME` | .env | .env | DevOps |
| `SMTP_HOST` | .env | .env | DevOps |
| `OPENAI_API_KEY` | .env | utm_provider_vault | MANAGER |
| `GROQ_API_KEY` | .env | utm_provider_vault | MANAGER |
| `AZURE_OPENAI_*` | .env | utm_provider_vault | MANAGER |
| `DEFAULT_MODEL` | .env | utm_model_catalog | MANAGER |

**Regla de oro**: 
- .env = Infraestructura compartida (DB, Storage, Email)
- DB = Configuración por tenant (LLM keys, modelos, usuarios)
