# ROLES Y FLUJO DE ONBOARDING - Legacy2Lake v3.9 ✅

> **Status**: v3.9 RELEASED - Feb 10, 2026
> 
> Multi-user support fully implemented with User Management UI in Tenant Console (`/settings`)

## 📋 JERARQUÍA DE ROLES

### 1. ADMIN (Plataforma)
- **Alcance**: Toda la plataforma Legacy2Lake
- **Responsabilidades**:
  - ✅ Crear nuevos tenants/clientes
  - ✅ Asignar PLAN del tenant (STANDARD, PREMIUM, ENTERPRISE)
  - ✅ Asignar el PRIMER usuario MANAGER de cada tenant
  - ✅ **Gestionar CATÁLOGOS GLOBALES**:
    - **Agentes del sistema** (utm_agent_catalog): Agent S, Agent A, Agent B, etc.
    - **Cartuchos de tecnología** (utm_system_catalog): SQL Server, Oracle, Snowflake, Databricks, etc.
    - Origins (tecnologías fuente) y Destinations (tecnologías destino)
  - ✅ **Impersonar usuarios** para dar soporte (Ghost Mode)
  - ✅ **Reset password** de cualquier usuario (All Users Dashboard)
  - ✅ **Ver y filtrar** todos los usuarios cross-tenant
  - ❌ **NO** configura proveedores LLM específicos del tenant (eso lo hace el MANAGER)
  - ❌ **NO** es responsable del gasto del tenant (eso es del MANAGER)

### 2. MANAGER (Tenant)
- **Alcance**: Un tenant específico
- **Responsabilidades**:
  - ✅ **Configurar PROVEEDORES LLM del tenant** (utm_provider_vault):
    - Agregar API keys (OpenAI, Groq, Azure, Anthropic, etc.)
    - Configurar base URLs y endpoints
    - Habilitar/deshabilitar proveedores
  - ✅ **Seleccionar MODELOS LLM** disponibles para el tenant (utm_model_catalog):
    - gpt-4o, claude-3-5-sonnet, llama-3, etc.
    - Cada tenant PAGA por sus propios modelos
  - ✅ **Gestionar usuarios** en Tenant Console (`/settings` > User Management):
    - Crear usuarios con password temporal
    - Editar roles (COLLABORATOR, VIEWER, MANAGER)
    - Activar/desactivar usuarios
    - Reset passwords
  - ✅ **Gestionar acceso a proyectos** (`/settings` > Project Access):
    - Asignar usuarios a proyectos específicos
    - Control granular de permisos por proyecto
  - ✅ Crear soluciones/proyectos
  - ⚠️ **RESPONSABLE DEL GASTO**: El tenant PAGA por todo el uso (API calls, tokens)
  - ⚠️ Si invita usuarios que gastan mucho, es SU responsabilidad, no de la plataforma
  - ⚠️ Debe controlar quién invita y monitorear el consumo
  - ❌ **NO** puede crear nuevos agentes del sistema (globales)
  - ❌ **NO** puede agregar nuevos cartuchos de tecnología (globales)

### 3. COLLABORATOR (Proyecto)
- **Alcance**: Proyectos específicos donde fue invitado
- **Responsabilidades**:
  - ✅ Trabajar en proyectos asignados
  - ✅ Generar código, modificar componentes
  - ✅ Ver y editar contenido del proyecto
  - ❌ NO puede eliminar proyectos
  - ❌ NO puede invitar otros usuarios
  - ❌ NO puede configurar proveedores

### 4. VIEWER (Proyecto)
- **Alcance**: Proyectos específicos donde fue invitado
- **Responsabilidades**:
  - ✅ Ver contenido del proyecto (solo lectura)
  - ❌ NO puede modificar nada
  - ❌ NO puede generar código
  - ❌ NO puede invitar usuarios

---

## 🔄 FLUJO DE ONBOARDING

### Paso 1: ADMIN crea tenant (via UI o SQL)

**Opción A: Via Platform Admin UI** (`/admin` > Identity > Create Tenant)
- Ingresa Display Name (nombre de la organización)
- Selecciona Tier (STANDARD, PREMIUM, ENTERPRISE)
- Crea primer usuario MANAGER automáticamente

**Opción B: Via SQL (directo en Supabase)**
```sql
-- 1. Crear tenant (organización)
INSERT INTO utm_tenants (display_name, tier)
VALUES ('Acme Corp', 'STANDARD');

-- 2. Crear primer usuario MANAGER
INSERT INTO utm_users (tenant_id, email, username, password_hash_bcrypt, role)
VALUES (
  '<tenant_id>',
  'manager@acmecorp.com',
  'manager_acme',
  '<bcrypt_hash>',
  'MANAGER'
);
```

**Catálogos globales ya disponibles**:
- ✅ **Agentes**: Agent S, Agent A, Agent B, etc. (utm_agent_catalog)
- ✅ **Cartuchos**: SQL Server, Oracle, Snowflake, Databricks (utm_system_catalog)
- ✅ Estos NO se crean por tenant, son compartidos por toda la plataforma
- ⚠️ Solo el ADMIN puede agregar nuevos agentes o cartuchos

### Paso 2: MANAGER configura el tenant

**A. Configurar proveedores LLM** (utm_provider_vault):
```sql
-- MANAGER agrega API keys de proveedores LLM
INSERT INTO utm_provider_vault (tenant_id, provider_name, api_key, base_url)
VALUES 
  ('<tenant_id>', 'openai', 'sk-proj-...', 'https://api.openai.com/v1'),
  ('<tenant_id>', 'groq', 'gsk_...', 'https://api.groq.com/openai/v1'),
  ('<tenant_id>', 'azure', '<azure_key>', 'https://<resource>.openai.azure.com');
```

**B. Habilitar modelos LLM** (utm_model_catalog):
```sql
-- MANAGER selecciona qué modelos usar (tenant PAGA por estos)
INSERT INTO utm_model_catalog (tenant_id, model_id, provider, label)
VALUES
  ('<tenant_id>', 'gpt-4o', 'openai', 'GPT-4 Optimized'),
  ('<tenant_id>', 'gpt-4o-mini', 'openai', 'GPT-4 Mini'),
  ('<tenant_id>', 'llama-3.1-70b', 'groq', 'Llama 3.1 70B');
```

**C. IMPORTANTE - Proveedores vs Cartuchos**:
- **Proveedores LLM** (OpenAI, Groq, Azure): TENANT-level, MANAGER configura
- **Cartuchos tecnológicos** (SQL Server, Snowflake): GLOBAL, ADMIN maneja
- **Agentes** (Agent S, Agent A): GLOBAL, ADMIN maneja

### Paso 3: MANAGER crea solución/proyecto

**Via UI** (`/dashboard` > New Project):
- Ingresa nombre del proyecto
- El proyecto queda asignado al tenant del MANAGER

### Paso 4: MANAGER crea usuarios y asigna acceso

**A. Crear usuarios** (`/settings` > User Management > Create User):
1. Click "Create User" button
2. Ingresa username, email, y rol (COLLABORATOR/VIEWER)
3. Sistema genera password temporal automáticamente
4. MANAGER comparte password con el usuario

**B. Asignar acceso a proyectos** (`/settings` > Project Access):
1. Selecciona el proyecto
2. Click "Add User"
3. Selecciona usuario de la lista
4. Asigna rol para ese proyecto (COLLABORATOR/VIEWER)

**Nota**: El sistema de invitaciones por email (`utm_user_invitations`) está implementado pero pendiente de activación. Por ahora, los MANAGER crean usuarios directamente.

---

## 📊 NIVELES DE CONFIGURACIÓN

### Nivel PLATAFORMA (ADMIN)
- Catálogo global de agentes
- Catálogo global de providers disponibles
- Gestión de tenants

### Nivel TENANT (MANAGER)
- ✅ **API Keys de proveedores** (el tenant paga)
- ✅ **Modelos habilitados** (según proveedor contratado)
- ✅ **Usuarios del tenant** (otros managers)
- ✅ **Proyectos/Soluciones**

### Nivel PROYECTO (COLLABORATOR/VIEWER)
- Acceso a proyectos específicos
- Generación de código (solo COLLABORATOR)
- Visualización (VIEWER)

---

## 🔐 MATRIZ DE PERMISOS

| Acción | ADMIN | MANAGER | COLLABORATOR | VIEWER |
|--------|-------|---------|--------------|--------|
| Crear tenant | ✅ | ❌ | ❌ | ❌ |
| Configurar proveedor | ❌ | ✅ | ❌ | ❌ |
| Seleccionar modelos | ❌ | ✅ | ❌ | ❌ |
| Crear MANAGER | ADMIN: 1er MANAGER<br>MANAGER: otros | ✅ (mismo tenant) | ❌ | ❌ |
| Crear proyecto | ❌ | ✅ | ❌ | ❌ |
| Invitar a proyecto | ❌ | ✅ | ❌ | ❌ |
| Generar código | ❌ | ✅ | ✅ | ❌ |
| Ver proyecto | ❌ | ✅ | ✅ (asignados) | ✅ (asignados) |
| Eliminar proyecto | ❌ | ✅ | ❌ | ❌ |

---

## �️ SOPORTE Y ADMINISTRACIÓN

### Impersonación de Usuario (ADMIN)

El ADMIN puede **actuar como cualquier usuario** para dar soporte:

**1. Iniciar impersonación**:
```bash
POST /api/auth/admin/impersonate
{
  "target_user_id": "<manager_user_id>"
}
```

**Respuesta**:
```json
{
  "success": true,
  "impersonate": {
    "user_id": "abc-123",
    "tenant_id": "tenant-456",
    "username": "manager_acme",
    "role": "MANAGER",
    "org_name": "Acme Corp"
  },
  "message": "Now impersonating manager_acme (MANAGER) from Acme Corp"
}
```

**2. Frontend envía header**:
```
X-User-ID: <admin_user_id>
X-Impersonate-User-ID: <manager_user_id>
```

**3. Terminar impersonación**:
```bash
POST /api/auth/admin/stop-impersonate
```

**Casos de uso**:
- ✅ ADMIN ayuda a MANAGER a configurar proveedores
- ✅ ADMIN diagnostica problemas del tenant
- ✅ ADMIN verifica configuración sin pedir credenciales
- ⚠️ Todas las acciones se registran con `admin_id` para auditoría

---

## 📊 CATÁLOGOS DEL SISTEMA

### Catálogos GLOBALES (ADMIN maneja)

**1. utm_agent_catalog** - Agentes del sistema
```
┌──────────┬──────────────────┬─────────────────────────────┐
│ agent_id │ display_name     │ description                 │
├──────────┼──────────────────┼─────────────────────────────┤
│ agent-s  │ Agent Scout      │ Technology detection        │
│ agent-a  │ Agent Architect  │ Medallion structure design  │
│ agent-b  │ Agent Builder    │ Code generation (Bronze)    │
└──────────┴──────────────────┴─────────────────────────────┘
```
- ⚠️ **NO hay tenant_id**: Todos los tenants usan los mismos agentes
- ✅ ADMIN puede agregar nuevos agentes
- ❌ MANAGER NO puede crear agentes custom

**2. utm_system_catalog** - Cartuchos de tecnología
```
┌────────────┬──────────────────┬──────────────┬─────────────┐
│ tech_id    │ name             │ type         │ description │
├────────────┼──────────────────┼──────────────┼─────────────┤
│ sqlserver  │ SQL Server       │ origin       │ MS SQL DB   │
│ oracle     │ Oracle Database  │ origin       │ Oracle RDBMS│
│ snowflake  │ Snowflake        │ destination  │ Cloud DW    │
│ databricks │ Databricks       │ destination  │ Lakehouse   │
└────────────┴──────────────────┴──────────────┴─────────────┘
```
- ⚠️ **NO hay tenant_id**: Catálogo global compartido
- ✅ ADMIN puede agregar nuevas tecnologías
- ❌ MANAGER solo SELECCIONA de las disponibles

### Catálogos TENANT-LEVEL (MANAGER maneja)

**3. utm_provider_vault** - Proveedores LLM del tenant
```
┌────────────┬───────────────┬──────────────┬──────────────┐
│ tenant_id  │ provider_name │ api_key      │ base_url     │
├────────────┼───────────────┼──────────────┼──────────────┤
│ tenant-123 │ openai        │ sk-proj-...  │ api.openai..│
│ tenant-123 │ groq          │ gsk_...      │ api.groq... │
│ tenant-456 │ azure         │ <azure_key>  │ azure.com   │
└────────────┴───────────────┴──────────────┴──────────────┘
```
- ✅ **Tiene tenant_id**: Cada tenant sus propias API keys
- ✅ MANAGER configura sus proveedores
- ⚠️ Tenant PAGA por el uso

**4. utm_model_catalog** - Modelos LLM habilitados
```
┌────────────┬──────────────┬──────────┬─────────────────┐
│ tenant_id  │ model_id     │ provider │ label           │
├────────────┼──────────────┼──────────┼─────────────────┤
│ tenant-123 │ gpt-4o       │ openai   │ GPT-4 Optimized │
│ tenant-123 │ gpt-4o-mini  │ openai   │ GPT-4 Mini      │
│ tenant-456 │ llama-3.1    │ groq     │ Llama 3.1 70B   │
└────────────┴──────────────┴──────────┴─────────────────┘
```
- ✅ **Tiene tenant_id**: Modelos privados del tenant
- ✅ MANAGER selecciona qué modelos habilitar
- ⚠️ NO hay modelos públicos compartidos
- ⚠️ Cada tenant PAGA por sus propios modelos

---

## �💡 EJEMPLOS

### Ejemplo 1: Nuevo cliente corporativo
1. **ADMIN** crea tenant "ACME_CORP"
2. **ADMIN** crea primer MANAGER: john.doe@acmecorp.com
3. **John (MANAGER)**:
   - Configura OpenAI con su API key corporativa
   - Selecciona modelos: gpt-4o, gpt-4o-mini
   - Crea proyecto "ERP Migration"
   - Invita a dev1@acmecorp.com como COLLABORATOR
   - Invita a manager2@acmecorp.com como MANAGER (para ayudar)

### Ejemplo 2: Proyecto con equipo externo
1. **MANAGER** crea proyecto "Mobile App"
2. **MANAGER** invita:
   - developer@external.com (COLLABORATOR)
   - qa@external.com (VIEWER)
3. Los usuarios externos SOLO ven ese proyecto específico
4. NO pueden ver otros proyectos del tenant

---

## ⚠️ REGLAS IMPORTANTES

1. **Un tenant SIEMPRE tiene al menos 1 MANAGER**
2. **Los MANAGERS configuran los proveedores** (porque el tenant paga)
3. **COLLABORATOR y VIEWER son roles A NIVEL PROYECTO**, no tenant
4. **Un MANAGER puede crear otros MANAGERS del mismo tenant**
5. **Los modelos son del TENANT**, no públicos/compartidos
6. **💰 RESPONSABILIDAD DE GASTO**:
   - El MANAGER es responsable del consumo del tenant
   - Si invita usuarios que gastan mucho → responsabilidad del MANAGER
   - La plataforma NO es responsable del gasto de los tenants
   - El MANAGER debe monitorear y controlar el uso
7. **PLANES**: ADMIN asigna plan (STANDARD/PREMIUM/ENTERPRISE) aunque ahora no haya diferencias funcionales
