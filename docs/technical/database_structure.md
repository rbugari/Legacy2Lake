# Estructura de la Base de Datos (Supabase / PostgreSQL)

Este documento detalla la estructura de la base de datos utilizada por el sistema, basada en la implementación del servicio de persistencia (`persistence_service.py`).

## Tablas Principales

### 1. `utm_projects`
Almacena la información fundamental de cada proyecto de migración.

*   **`project_id`** (UUID): Identificador único del proyecto (Clave Primaria).
*   **`name`** (TEXT): Nombre descriptivo del proyecto.
*   **`repo_url`** (TEXT): URL del repositorio de GitHub asociado (si aplica).
*   **`status`** (TEXT): Estado general del proyecto (ej. `TRIAGE`, `DRAFTING`, `COMPLETED`).
*   **`stage`** (TEXT): Etapa numérica actual del proceso (ej. "1", "2").
*   **`prompt`** (TEXT): Prompt de sistema personalizado para el proyecto.
*   **`settings`** (JSONB): Configuración flexible del proyecto.
*   **`config`** (JSONB): Configuraciones adicionales de plataforma o entorno.
*   **`triage_approved_at`** (TIMESTAMP): Fecha y hora de aprobación del triaje.

### 2. `utm_objects`
Tabla central para todos los activos y archivos del proyecto (anteriormente referida como `assets`).

*   **`object_id`** (UUID): Identificador único del objeto/activo.
*   **`project_id`** (UUID): Referencia al proyecto (`utm_projects`).
*   **`source_name`** (TEXT): Nombre del archivo (ej. `paquete.dtsx`).
*   **`source_path`** (TEXT): Ruta relativa o absoluta del archivo.
*   **`raw_content`** (TEXT): Contenido en texto del archivo (si es leíble).
*   **`type`** (TEXT): Tipo de activo (ej. `LAYOUT`, `DTSX`, `SQL`, `OTHER`).
*   **`hash`** (TEXT): Hash del contenido para control de versiones/cambios.
*   **`metadata`** (JSONB): Metadatos técnicos extraídos del archivo.
*   **`selected`** (BOOLEAN): Indica si el activo ha sido seleccionado para migración.
*   **Campos de Metadatos de Negocio (Release 1.2+):**
    *   **`frequency`** (TEXT): Frecuencia de carga (Default: 'DAILY').
    *   **`load_strategy`** (TEXT): Estrategia de carga (Default: 'FULL_OVERWRITE').
    *   **`criticality`** (TEXT): Nivel de criticidad (Default: 'P3').
    *   **`is_pii`** (BOOLEAN): Indica si contiene información personal identificable.
    *   **`masking_rule`** (TEXT): Regla de enmascaramiento de datos.
    *   **`business_entity`** (TEXT): Entidad de negocio relacionada.
    *   **`target_name`** (TEXT): Nombre sugerido para el destino.

### 3. `utm_transformations`
Almacena el resultado del proceso de conversión de código.

*   **`id`** (UUID/INT): Identificador único de la transformación.
*   **`asset_id`** (UUID): Referencia al objeto original (`utm_objects.object_id`).
*   **`source_code`** (TEXT): Fragmento de código original procesado.
*   **`target_code`** (TEXT): Código generado/transformado (ej. PySpark, SQL).
*   **`status`** (TEXT): Estado de la transformación (ej. `completed`).

### 4. `utm_asset_context`
Almacena el contexto humano y reglas específicas aportadas por el usuario para un activo.

*   **`project_id`** (UUID): Referencia al proyecto.
*   **`source_path`** (TEXT): Ruta del archivo al que aplica el contexto.
*   **`notes`** (TEXT): Notas en lenguaje natural del usuario.
*   **`rules`** (JSONB): Reglas específicas o restricciones para la IA.
*   **`updated_at`**: (TIMESTAMP) Fecha de actualización (Implícito).

### 5. `utm_design_registry`
Registro global de decisiones de diseño y estándares (Knowledge Registry).

*   **`project_id`** (UUID): Referencia al proyecto.
*   **`category`** (TEXT): Categoría de la regla (ej. `NAMING`, `ARCHITECTURE`).
*   **`key`** (TEXT): Clave única de la regla.
*   **`value`** (JSONB/TEXT): Valor de la regla o estándar.
*   **`updated_at`** (TIMESTAMP): Fecha de última modificación.

## Tablas de Sistema y Logs

### 6. `utm_execution_logs`
Registro de auditoría y traza de ejecución de los agentes.

*   **`project_id`** (UUID): Referencia al proyecto.
*   **`phase`** (TEXT): Fase de ejecución (ej. `MIGRATION`).
*   **`step`** (TEXT): Agente o paso específico (ej. `Librarian`, `Topology`).
*   **`message`** (TEXT): Mensaje de log.
*   **`level`** (TEXT): Nivel de severidad (ej. `INFO`, `ERROR`).

### 7. `utm_file_inventory`
Caché de la estructura de archivos del sistema de archivos para acceso rápido.

*   **`project_id`** (UUID): Referencia al proyecto.
*   **`file_path`** (TEXT): Ruta relativa del archivo.
*   **`is_directory`** (BOOLEAN): Indica si es una carpeta.
*   **`size_bytes`** (BIGINT): Tamaño del archivo.
*   **`last_modified`** (TIMESTAMP): Fecha de modificación del archivo.

### 8. `utm_logical_steps`
*Tabla referenciada en operaciones de limpieza, relacionada con la lógica de negocio interna.*

*   **`object_id`** (UUID): Clave foránea hacia `utm_objects`.

## Notas Adicionales
*   Las tablas usan UUIDs para identificadores primarios.
*   La lógica de eliminación en cascada se maneja parcialmente en el código (`reset_project_data` en `persistence_service.py`), asegurando limpieza en `utm_logical_steps` y `utm_transformations` antes de borrar los objetos base.
