# Skill: API-to-Database Mapping & Orphan Table Auditor

## Purpose
Analizar el código fuente para mapear qué APIs interactúan con qué tablas de Supabase, detallando acciones y parámetros en formato JSON, e identificar tablas en la base de datos que no están siendo utilizadas por ninguna API.

## Tools (Required)
1. **File System / Grep:** Para escanear el código buscando llamadas al cliente de Supabase (ej: `.from('table_name')`).
2. **Supabase MCP (`supabase_mcp.list_tables`):** Para obtener la lista maestra de tablas reales en la base de datos.
3. **Markdown Generator:** Para estructurar el informe final.

## Critical Constraints
- **Acceso Real:** El agente DEBE obtener la lista de tablas directamente desde el MCP de Supabase, no de archivos de configuración locales o tipos de TypeScript.
- **Formato JSON:** Los parámetros detectados en el código (filtros, inserts, updates) deben extraerse y representarse fielmente en bloques JSON dentro del informe.
- **Detección de Huérfanos:** Se considera "tabla huérfana" cualquier tabla devuelta por el MCP que no aparezca explícitamente en una cadena de texto dentro de las llamadas `.from()` del código.

## Workflow (Step-by-Step)

### Step 1: Data Discovery (Code)
El agente escaneará el directorio de la aplicación buscando patrones de uso de Supabase. Para cada coincidencia, extraerá:
- **Ruta del archivo:** Donde reside la API/Función.
- **Nombre de la Tabla:** El argumento del método `.from()`.
- **Acción:** El método encadenado (`select`, `insert`, `update`, `delete`, `rpc`).
- **Parámetros:** Los objetos pasados como argumentos a los métodos de filtrado o de payload.

### Step 2: Database Discovery (Real DB)
Llamar a `supabase_mcp.list_tables()` para obtener el inventario actual de la base de datos.

### Step 3: Analysis & Cross-Referencing
Cruzar los datos del Step 1 con el Step 2 para identificar inconsistencias y tablas no vinculadas.

### Step 4: Report Generation
Generar un archivo `API_DB_AUDIT.md` con la siguiente estructura:

# Reporte de Interacción API-DB
## 1. Mapeo de APIs
| Archivo | Tabla | Acción | Parámetros (JSON) |
| :--- | :--- | :--- | :--- |
| `path/to/api.ts` | `nombre_tabla` | `INSERT` | `{ "field": "value" }` |

## 2. Auditoría de Tablas Huérfanas
> **Alerta:** Las siguientes tablas existen en Supabase pero no se detectó ninguna referencia en el código de las APIs:
- [ ] `tabla_desconocida_1`
- [ ] `tabla_antigua_2`

## 5. Execution Trigger
"Agente, ejecuta la skill 'API-to-Database Mapping' y genera el informe de auditoría cruzando el código con el MCP de Supabase."