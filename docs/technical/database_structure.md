# Estructura de la Base de Datos (Supabase / PostgreSQL)

Este documento detalla la estructura física actual de la base de datos, incluyendo todas las tablas, columnas y tipos de datos. Esta referencia es ideal para generar Diagramas Entidad-Relación (ER).

## 1. Core Project & Tenants

### `utm_clients`
Representa la organización o cliente dueño de los datos.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `client_id` | `uuid` | NO | PK. Identificador único del cliente. |
| `name` | `text` | NO | Nombre de la organización. |
| `created_at` | `timestamptz` | YES | Fecha de creación. |

### `utm_tenants`
Usuarios individuales asociados a un cliente.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `tenant_id` | `uuid` | NO | PK. Identificador único del usuario. |
| `client_id` | `uuid` | YES | FK -> `utm_clients.client_id`. |
| `username` | `text` | NO | Nombre de usuario para login. |
| `password_hash` | `text` | NO | Hash de contraseña (Legacy). |
| `password_hash_bcrypt` | `text` | YES | Hash seguro (Bcrypt) para autenticación nueva. |
| `role` | `text` | NO | Rol RBAC (ej. `ADMIN`, `USER`). |
| `is_active` | `boolean` | YES | Estado de la cuenta. |
| `created_at` | `timestamptz` | YES | Fecha de registro. |

### `utm_projects`
Entidad central que agrupa todo el proceso de modernización.
| Columna | Tipo | Nullable | Descripción |
| :--- | :--- | :--- | :--- |
| `project_id` | `uuid` | NO | PK. Identificador único del proyecto. |
| `tenant_id` | `uuid` | YES | FK -> `utm_tenants.tenant_id`. Dueño del proyecto. |
| `client_id` | `uuid` | YES | FK -> `utm_clients.client_id`. Contexto organizacional. |
| `name` | `varchar` | NO | Nombre del proyecto. |
| `description` | `text` | YES | Descripción opcional. |
| `status` | `varchar` | YES | Estado (ej. `TRIAGE`, `DRAFTING`). |
| `stage` | `text` | YES | Etapa numérica (ej. "1", "2"). |
| `settings` | `jsonb` | YES | Configuración global (Source/Target Tech). |
| `config` | `jsonb` | YES | Variables de entorno y rutas. |
| `repo_url` | `text` | YES | URL del repo git. |
| `prompt` | `text` | YES | Prompt de sistema customizado. |
| `triage_approved_at` | `timestamptz` | YES | Fecha de aprobación de triage. |
| `is_active` | `boolean` | YES | Soft delete flag. |
| `created_at` | `timestamptz` | YES | Fecha de creación. |

## 2. Asset Management & Intelligence

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

## 3. Configuration & Governance

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

## 4. System & Audit

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
