#!/usr/bin/env python3
"""
Generar diagrama del flujo de roles y onboarding
"""

mermaid = """
```mermaid
flowchart TB
    subgraph PLATAFORMA["🏢 PLATAFORMA LEGACY2LAKE"]
        ADMIN[👤 ADMIN<br/>Administrador Plataforma]
    end
    
    subgraph TENANT1["🏪 TENANT: ACME Corp"]
        M1[👤 MANAGER 1<br/>john@acme.com]
        M2[👤 MANAGER 2<br/>jane@acme.com]
        
        PROV1[🔌 PROVEEDORES<br/>OpenAI: sk-proj-ABC...]
        MODELS1[📦 MODELOS<br/>gpt-4o, gpt-4o-mini]
        
        subgraph PROJ1["📁 PROYECTO: ERP Migration"]
            C1[👤 COLLABORATOR<br/>dev1@acme.com]
            V1[👤 VIEWER<br/>qa@acme.com]
        end
        
        subgraph PROJ2["📁 PROYECTO: Mobile App"]
            C2[👤 COLLABORATOR<br/>dev2@external.com]
        end
    end
    
    subgraph TENANT2["🏪 TENANT: XYZ Inc"]
        M3[👤 MANAGER<br/>boss@xyz.com]
        
        PROV2[🔌 PROVEEDORES<br/>Groq: gsk-ABC...]
        MODELS2[📦 MODELOS<br/>llama3-8b, mixtral]
        
        subgraph PROJ3["📁 PROYECTO: Data Warehouse"]
            C3[👤 COLLABORATOR<br/>analyst@xyz.com]
            V2[👤 VIEWER<br/>client@external.com]
        end
    end
    
    %% ADMIN crea tenants y primer MANAGER
    ADMIN -->|1. Crea tenant| TENANT1
    ADMIN -->|2. Asigna 1er MANAGER| M1
    ADMIN -->|1. Crea tenant| TENANT2
    ADMIN -->|2. Asigna 1er MANAGER| M3
    
    %% MANAGER configura tenant
    M1 -->|3. Configura| PROV1
    M1 -->|4. Selecciona| MODELS1
    M1 -->|5. Invita otro MANAGER| M2
    
    M3 -->|3. Configura| PROV2
    M3 -->|4. Selecciona| MODELS2
    
    %% MANAGER crea proyectos
    M1 -->|6. Crea| PROJ1
    M1 -->|6. Crea| PROJ2
    M3 -->|6. Crea| PROJ3
    
    %% MANAGER invita a proyectos específicos
    M1 -->|7. Invita COLLABORATOR| C1
    M1 -->|7. Invita VIEWER| V1
    M2 -->|7. Invita COLLABORATOR| C2
    M3 -->|7. Invita COLLABORATOR| C3
    M3 -->|7. Invita VIEWER| V2
    
    style ADMIN fill:#ff6b6b,color:#fff
    style M1 fill:#4ecdc4,color:#fff
    style M2 fill:#4ecdc4,color:#fff
    style M3 fill:#4ecdc4,color:#fff
    style C1 fill:#95e1d3,color:#000
    style C2 fill:#95e1d3,color:#000
    style C3 fill:#95e1d3,color:#000
    style V1 fill:#f9ca24,color:#000
    style V2 fill:#f9ca24,color:#000
    style PROV1 fill:#a29bfe,color:#fff
    style PROV2 fill:#a29bfe,color:#fff
    style MODELS1 fill:#74b9ff,color:#fff
    style MODELS2 fill:#74b9ff,color:#fff
```

## 🎯 FLUJO COMPLETO

### Paso 1-2: ADMIN crea tenant y primer MANAGER
- 🔴 **ADMIN** crea el tenant (ACME Corp, XYZ Inc)
- 🔴 **ADMIN** asigna el primer MANAGER del tenant

### Paso 3-5: MANAGER configura el tenant
- 🔵 **MANAGER** configura proveedores LLM (API keys)
- 🔵 **MANAGER** selecciona modelos disponibles
- 🔵 **MANAGER** puede invitar otros MANAGERS del mismo tenant (opcional)

### Paso 6-7: MANAGER gestiona proyectos
- 🔵 **MANAGER** crea proyectos/soluciones
- 🔵 **MANAGER** invita COLLABORATOR (verde) a proyectos específicos
- 🔵 **MANAGER** invita VIEWER (amarillo) a proyectos específicos

## 📊 NIVELES DE ACCESO

| Rol | Nivel | Configuración | Proyectos |
|-----|-------|---------------|-----------|
| 🔴 **ADMIN** | Plataforma | ✅ Crea tenants | ❌ No accede |
| 🔵 **MANAGER** | Tenant | ✅ Proveedores, modelos | ✅ TODOS del tenant |
| 🟢 **COLLABORATOR** | Proyecto | ❌ Solo lectura | ✅ Solo asignados |
| 🟡 **VIEWER** | Proyecto | ❌ Solo lectura | ✅ Solo asignados (lectura) |

## 💾 ESTRUCTURA DE DATOS

### utm_tenants
- tenant_id (PK)
- client_id (ej: "ACME_CORP")

### utm_users
- user_id (PK)
- tenant_id (FK)
- role: **MANAGER** únicamente
- ⚠️ COLLABORATOR y VIEWER NO están en utm_users, están en utm_project_members

### utm_provider_vault
- tenant_id (FK)
- provider_name, api_key, base_url
- ✅ MANAGER configura (tenant paga)

### utm_model_catalog
- model_id (PK)
- tenant_id (FK) - **NOT NULL**
- ❌ NO hay modelos públicos

### utm_projects
- project_id (PK)
- tenant_id (FK)
- created_by (MANAGER user_id)

### utm_project_members
- project_id (FK)
- user_id (FK) - Usuario con acceso
- role: **COLLABORATOR** o **VIEWER**
- ⚠️ MANAGER NO está aquí (tiene acceso a TODOS los proyectos del tenant)

### utm_user_invitations
- invitation_id (PK)
- tenant_id (FK)
- project_id (FK) - **NULL** para MANAGER, **NOT NULL** para COLLABORATOR/VIEWER
- role: MANAGER | COLLABORATOR | VIEWER
- Logic: 
  - `role='MANAGER'` → `project_id=NULL` (invitación a tenant)
  - `role IN ('COLLABORATOR','VIEWER')` → `project_id NOT NULL` (invitación a proyecto)
"""

print(mermaid)

print("\n" + "="*70)
print("✅ MIGRACIONES CREADAS:")
print("="*70)
print("- 019_v3.9_remove_public_models.sql (eliminar is_public)")
print("- 020_v3.9_project_level_invitations.sql (agregar project_id a invitations)")
print("- 021_v3.9_project_members_table.sql (tabla de miembros de proyectos)")
print("\n" + "="*70)
print("📝 DOCUMENTACIÓN CREADA:")
print("="*70)
print("- docs/ROLES_AND_ONBOARDING.md")
print("\n" + "="*70)
