# Estructura de la Base de Datos (Supabase / PostgreSQL)

**Version:** v4.0 (Zero-Hardcode Architecture)  
**Last Updated:** 2026-02-17  
**Sprint:** Sprint 14 Phase 2 (85% complete)

Este documento detalla la estructura física actual de la base de datos, incluyendo todas las tablas, columnas y tipos de datos. Esta referencia es ideal para generar Diagramas Entidad-Relación (ER).

> **v4.0 Major Update**: 6 nuevas tablas agregadas (utm_prompts, utm_prompts_history, utm_column_profiles, utm_generation_outcomes, utm_parser_catalog, utm_source_tech_catalog). Total: 22 tablas core.

---

## ⚠️ v4.0 Breaking Changes Summary

**Zero-Hardcode Architecture**: Todos los prompts migrados de archivos a base de datos con versionamiento automático.

### New Tables (v4.0):
- ✅ **`utm_prompts`**: Global prompts con versionamiento automático (14 activos)
- ✅ **`utm_prompts_history`**: Historia inmutable de versiones anteriores
- ✅ **`utm_column_profiles`**: Análisis forense a nivel de campo (22 columnas, 6 índices)
- ✅ **`utm_generation_outcomes`**: Analytics de generación de código para ML
- ✅ **`utm_parser_catalog`**: Configuraciones de parsers dinámicos (10 tecnologías)
- ✅ **`utm_source_tech_catalog`**: Definiciones de tecnologías (15+ registrados)

### v3.9 Legacy Changes:

### Removed Tables:
- ❌ **`utm_clients`**: Eliminado en migración 024. Concepto consolidado en `utm_tenants`.

### Modified Tables:
- 🔄 **`utm_tenants`**: Ahora representa SOLO organizaciones. Eliminadas columnas: `client_id`, `org_name`, `username`, `password_hash`, `password_hash_bcrypt`, `role`.
- 🔄 **`utm_projects`**: Agregada `created_by_user_id` (FK -> utm_users). Eliminada `client_id`.
- 🔄 **`utm_process_locks`**: Agregada `locked_by_user_email` para auditoría.

### New Tables (Multi-User Support):
- ✅ **`utm_users`**: Identidad de usuarios con email, username, password, role.
- ✅ **`utm_user_invitations`**: Onboarding basado en email con tokens de invitación.
- ✅ **`utm_project_members`**: Control de acceso granular a nivel proyecto.

### Migration Path:
- **Migration 020**: Project-level invitations foundation
- **Migration 021**: Project members table (+ 021b RLS fix)
- **Migration 022**: Global system catalog (tech_id simplification)
- **Migration 023**: Admin role + deployment fields
- **Migration 024**: Remove client_id simplification
- **Migration 025**: Remove org_name simplification

---

## 1. Multi-User & Organization Core (v3.9)

### `utm_tenants`
Representa organizaciones o empresas clientes. **Simplificado en v3.9** para representar solo entidades organizacionales.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `tenant_id` | `uuid` | NO | PK. Identificador único de la organización. |
| `display_name` | `text` | NO | Nombre visible de la organización. |
| `tier` | `text` | YES | Plan de suscripción (ej. `FREE`, `PRO`, `ENTERPRISE`). |
| `is_active` | `boolean` | YES | Estado activo de la organización. |
| `created_at` | `timestamptz` | YES | Fecha de creación. |
| `updated_at` | `timestamptz` | YES | Última actualización. |

> **v3.9 Breaking Change**: Se eliminaron las columnas `client_id`, `org_name`, `username`, `password_hash`, `password_hash_bcrypt`, y `role`. Los datos de usuario ahora residen en `utm_users`.

### `utm_users` (NEW in v3.9)
Identidad de usuarios individuales, separada de la organización.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `user_id` | `uuid` | NO | PK. Identificador único del usuario. |
| `tenant_id` | `uuid` | NO | FK -> `utm_tenants.tenant_id`. Organización a la que pertenece. |
| `email` | `text` | NO | Email único del usuario (UNIQUE). |
| `username` | `text` | NO | Nombre de usuario para login. |
| `password_hash_bcrypt` | `text` | NO | Hash Bcrypt de contraseña. |
| `role` | `text` | NO | Rol RBAC: `ADMIN`, `MANAGER`, `COLLABORATOR`, `VIEWER`. |
| `is_active` | `boolean` | YES | Estado de la cuenta. |
| `display_name` | `text` | YES | Nombre completo del usuario. |
| `last_login` | `timestamptz` | YES | Última sesión. |
| `created_at` | `timestamptz` | YES | Fecha de registro. |
| `updated_at` | `timestamptz` | YES | Última modificación. |

> **Role Hierarchy**: `ADMIN` (platform-level), `MANAGER` (tenant-level), `COLLABORATOR` (project-level editor), `VIEWER` (project-level read-only).

### `utm_user_invitations` (NEW in v3.9)
Gestión de invitaciones por email para onboarding de usuarios.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `invitation_id` | `uuid` | NO | PK. Identificador único de la invitación. |
| `tenant_id` | `uuid` | NO | FK -> `utm_tenants.tenant_id`. |
| `email` | `text` | NO | Email del usuario invitado. |
| `role` | `text` | NO | Rol asignado al aceptar. |
| `token` | `text` | NO | Token único para validación (UNIQUE). |
| `expires_at` | `timestamptz` | NO | Fecha de expiración del token. |
| `status` | `text` | NO | Estado: `PENDING`, `ACCEPTED`, `EXPIRED`, `CANCELLED`. |
| `invited_by` | `uuid` | YES | FK -> `utm_users.user_id`. Usuario que envió invitación. |
| `invited_at` | `timestamptz` | YES | Fecha de envío. |
| `accepted_at` | `timestamptz` | YES | Fecha de aceptación. |

### `utm_project_members` (NEW in v3.9)
Control de acceso granular a nivel de proyecto.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `member_id` | `uuid` | NO | PK. Identificador único del miembro. |
| `project_id` | `uuid` | NO | FK -> `utm_projects.project_id`. |
| `user_id` | `uuid` | NO | FK -> `utm_users.user_id`. |
| `role` | `text` | NO | Rol específico en el proyecto: `COLLABORATOR`, `VIEWER`. |
| `added_by` | `uuid` | YES | FK -> `utm_users.user_id`. Usuario que asignó acceso. |
| `added_at` | `timestamptz` | YES | Fecha de asignación. |

> **UNIQUE Constraint**: `(project_id, user_id)` - Un usuario solo puede tener un rol por proyecto.

## 2. Projects & Process Governance

### `utm_projects`
Entidad central que agrupa todo el proceso de modernización.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `project_id` | `uuid` | NO | PK. Identificador único del proyecto. |
| `tenant_id` | `uuid` | NO | FK -> `utm_tenants.tenant_id`. Organización propietaria. |
| `name` | `varchar` | NO | Nombre del proyecto. |
| `description` | `text` | YES | Descripción opcional. |
| `status` | `varchar` | YES | Estado (ej. `TRIAGE`, `DRAFTING`, `COMPLETED`). |
| `stage` | `text` | YES | Etapa numérica (ej. "1", "2"). |
| `settings` | `jsonb` | YES | Configuración global (Source/Target Tech). |
| `config` | `jsonb` | YES | Variables de entorno y rutas. |
| `repo_url` | `text` | YES | URL del repo git. |
| `prompt` | `text` | YES | Prompt de sistema customizado. |
| `triage_approved_at` | `timestamptz` | YES | Fecha de aprobación de triage. |
| `created_by_user_id` | `uuid` | YES | FK -> `utm_users.user_id`. Usuario creador (v3.9). |
| `is_active` | `boolean` | YES | Soft delete flag. |
| `created_at` | `timestamptz` | YES | Fecha de creación. |
| `updated_at` | `timestamptz` | YES | Última actualización. |

> **v3.9 Changes**: Agregada columna `created_by_user_id` para rastrear autoría. Eliminada referencia `client_id` (migración 024).

### `utm_process_locks` (v3.8)
Bloqueo de ejecución concurrente para proyectos.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `lock_id` | `uuid` | NO | PK. Identificador único del bloqueo. |
| `project_id` | `uuid` | NO | FK -> `utm_projects.project_id` (UNIQUE). |
| `phase` | `text` | NO | Fase en ejecución (ej. `DRAFTING`, `MIGRATION`). |
| `locked_by_user_email` | `text` | YES | Email del usuario ejecutando (v3.9). |
| `locked_at` | `timestamptz` | NO | Timestamp del bloqueo. |
| `expires_at` | `timestamptz` | NO | Expiración automática (30 min default). |

> **Governance**: Solo un proceso puede ejecutarse por proyecto. Admin puede liberar bloqueos vía RPC `force_expire_lock(project_id)`.

## 3. Asset Management & Intelligence

### `utm_objects`
(Antiguo `assets`) Almacena cada archivo o artefacto descubierto.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `object_id` | `uuid` | NO | PK. Identificador del activo. |
| `project_id` | `uuid` | YES | FK -> `utm_projects.project_id`. |
| `source_name` | `text` | NO | Nombre del archivo. |
| `source_path` | `text` | NO | Ruta relativa. |
| `type` | `text` | NO | Tipo (e.g. `LAYOUT`, `SQL`, `DTSX`). |
| `raw_content` | `text` | YES | Contenido original. |
| `metadata` | `jsonb` | YES | Inferencia IA (Volumen, PII, Latencia). |
| `hash` | `text` | YES | Checksum para cambios. |
| `selected` | `boolean` | YES | Si se incluye en la migración. |
| `created_at` | `timestamptz` | YES | Fecha de ingesta. |

### `utm_logical_steps`
Representación Intermedia (IR) normalizada.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `step_id` | `uuid` | NO | PK. Identificador del paso lógico. |
| `object_id` | `uuid` | YES | FK -> `utm_objects.object_id`. |
| `step_order` | `int4` | NO | Orden de ejecución secuencial. |
| `step_type` | `text` | NO | Verbo (READ, WRIT, JOIN, etc.). |
| `ir_payload` | `jsonb` | NO | Definición formal del paso en JSON. |
| `status` | `text` | YES | Estado de validación. |
| `description` | `text` | YES | Explicación en lenguaje natural. |
| `created_at` | `timestamptz` | YES | Fecha de generación. |

### `utm_column_mappings`
Linaje y transformación a nivel de columna.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `uuid` | NO | PK. |
| `asset_id` | `uuid` | YES | FK -> `utm_objects.object_id`. |
| `source_column` | `text` | NO | Columna origen. |
| `target_column` | `text` | NO | Columna destino sugerida. |
| `source_type` | `text` | YES | Tipo de dato origen. |
| `target_type` | `text` | YES | Tipo de dato destino. |
| `logic` | `text` | YES | Lógica de transformación SQL/Expr. |
| `is_pii` | `boolean` | YES | Flag de confidencialidad. |
| `description` | `text` | YES | Contexto de negocio. |
| `confidence_score` | `float4` | YES | Nivel de confianza de la IA. |
| `created_at` | `timestamptz` | YES | Fecha de creación. |
| `updated_at` | `timestamptz` | YES | Fecha de actualización. |

### `utm_transformations`
Código final generado.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `uuid` | NO | PK. |
| `asset_id` | `uuid` | YES | FK -> `utm_objects.object_id`. |
| `source_code` | `text` | YES | Snippet original. |
| `target_code` | `text` | YES | Código moderno generado. |
| `status` | `text` | YES | Estado de generación. |
| `created_at` | `timestamptz` | YES | Fecha de generación. |

## 4. Configuration & Governance

### `utm_agent_matrix`
Asignación estratégica de Agentes a Modelos LLM.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `uuid` | NO | PK. |
| `agent_id` | `text` | NO | ID del Agente (ej. `agent-a`). |
| `provider` | `text` | NO | Proveedor (ej. `openai`, `azure`). |
| `model_id` | `text` | NO | Modelo específico (ej. `gpt-4o`). |
| `temperature` | `numeric` | YES | Creatividad (0.0 - 1.0). |
| `is_active` | `boolean` | YES | Si la asignación está vigente. |
| `updated_at` | `timestamptz` | YES | Última modificación. |

### `utm_agent_catalog`
Catálogo de roles de Agentes disponibles.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `agent_id` | `text` | NO | PK. Identificador (ej. `agent-s`). |
| `name` | `text` | NO | Nombre legible (ej. `Agent S (Scout)`). |
| `role_description` | `text` | YES | Descripción de responsabilidades. |
| `is_active` | `boolean` | YES | Disponibilidad. |

### `utm_provider_vault`
Almacén seguro de credenciales de proveedores LLM.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `uuid` | NO | PK. |
| `tenant_id` | `uuid` | NO | FK -> `utm_tenants.tenant_id`. Dueño de la llave. |
| `provider_name` | `text` | NO | Nombre del proveedor (ej. `openai`). |
| `api_key` | `text` | YES | API Key (Debería estar encriptada). |
| `base_url` | `text` | YES | URL base para endpoints custom. |
| `model_name` | `text` | YES | Override de nombre de modelo. |
| `is_active` | `boolean` | YES | Estado de la credencial. |
| `created_at` | `timestamptz` | YES | Fecha de registro. |

### `utm_model_catalog`
Catálogo técnico de Modelos soportados.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `model_id` | `text` | NO | PK. ID del modelo (ej. `gpt-4-turbo`). |
| `provider` | `text` | YES | Proveedor (ej. `openai`). |
| `label` | `text` | YES | Nombre legible. |
| `context_window` | `int4` | YES | Tamaño de ventana de contexto. |
| `input_price_1k` | `numeric` | YES | Costo por 1k tokens entrada. |
| `output_price_1k` | `numeric` | YES | Costo por 1k tokens salida. |
| `is_active` | `boolean` | YES | Disponibilidad. |
| `created_at` | `timestamptz` | YES | Fecha de alta. |

### `utm_system_catalog` (v3.6)
Catálogo de configuraciones técnicas y reglas de cumplimiento por tecnología.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `tech_id` | `text` | NO | PK. ID de la tecnología (ej. `oracle`, `fabric`). |
| `label` | `text` | YES | Nombre legible (ej. "Oracle Database"). |
| `category` | `text` | YES | Tipo (ej. `source`, `destination`). |
| `config` | `jsonb` | YES | Configuración completa (rules, features, templates). |
| `is_active` | `boolean` | YES | Disponibilidad. |
| `created_at` | `timestamptz` | YES | Fecha de alta. |

> **v3.6 Note**: El campo `config` almacena reglas de cumplimiento específicas por tecnología (e.g., `oracle.compliance.rules`). Los cartuchos obtienen estas reglas dinámicamente durante la generación de código.

### `utm_design_registry`
Configuraciones y patrones de diseño (Knowledge Base).
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `uuid` | NO | PK. |
| `project_id` | `uuid` | YES | FK -> `utm_projects.project_id`. |
| `category` | `text` | NO | Grupo (ej. `NAMING`). |
| `key` | `text` | NO | Clave de configuración. |
| `value` | `jsonb` | YES | Valor o estructura JSON. |
| `updated_at` | `timestamptz` | YES | Última actualización. |

## 5. System & Audit

### `utm_execution_logs`
Logs de auditoría detallados.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `log_id` | `uuid` | NO | PK. |
| `project_id` | `uuid` | YES | FK -> `utm_projects.project_id`. |
| `phase` | `text` | YES | Fase (ej. `MIGRATION`). |
| `step` | `text` | YES | Paso o Agente. |
| `message` | `text` | YES | Detalle del evento. |
| `level` | `text` | YES | Severidad (`INFO`, `ERROR`). |
| `timestamp` | `timestamptz` | YES | Momento del evento. |

### `utm_file_inventory`
Índice rápido del sistema de archivos.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `uuid` | NO | PK. |
| `project_id` | `uuid` | YES | FK -> `utm_projects.project_id`. |
| `file_path` | `text` | NO | Ruta relativa. |
| `is_directory` | `boolean` | YES | Es carpeta. |
| `size_bytes` | `int8` | YES | Tamaño en bytes. |
| `last_modified` | `timestamptz` | YES | Última modificación en disco. |
| `updated_at` | `timestamptz` | YES | Último escaneo. |

### `utm_user_overrides`
Overrides manuales de usuario a la lógica generada.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `uuid` | NO | PK. |
| `project_id` | `uuid` | YES | FK -> `utm_projects.project_id`. |
| `step_id` | `uuid` | YES | FK opcional -> `utm_logical_steps`. |
| `field_path` | `varchar` | NO | JSON Path afectado. |
| `old_value` | `text` | YES | Valor original. |
| `new_value` | `text` | YES | Nuevo valor manual. |
| `comment` | `text` | YES | Justificación. |
| `applied_at` | `timestamptz` | YES | Fecha de aplicación. |

### `utm_asset_context`
Contexto y reglas adicionales para activos.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `uuid` | NO | PK. |
| `project_id` | `uuid` | YES | FK -> `utm_projects.project_id`. |
| `source_path` | `text` | NO | Ruta del activo. |
| `notes` | `text` | YES | Anotaciones humanas. |
| `rules` | `jsonb` | YES | Reglas específicas. |
| `updated_at` | `timestamptz` | YES | Última actualización. |

### `utm_solution_context`
Contexto global de solución.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `context_id` | `uuid` | NO | PK. |
| `project_id` | `uuid` | YES | FK -> `utm_projects.project_id`. |
| `business_domain` | `text` | YES | Dominio de negocio. |
| `technical_constraints` | `text` | YES | Restricciones técnicas. |
| `compliance_level` | `text` | YES | Nivel de compliance requerido. |
| `created_at` | `timestamptz` | YES | Fecha de creación. |
