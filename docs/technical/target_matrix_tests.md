# Target Matrix Tests

## Objetivo

El runner de Target Matrix permite ejecutar un mismo proyecto contra multiples salidas target y comparar los resultados de Drafting + post-Drafting en una corrida controlada.

Casos de uso principales:

- comparar un mismo proyecto entre varios cartuchos de salida
- comparar el mismo target en distintos modos post-Drafting
- guardar bundles ZIP por corrida para analisis posterior
- evitar perder artefactos cuando se relanza otro test sobre el mismo proyecto

## Fuente de verdad para targets

Los targets configurables deben coincidir con el catalogo real de la API y de la base de datos `utm_system_catalog`.

Targets canonicos actuales:

- `aws`
- `databricks`
- `dbt`
- `gcp`
- `ms_fabric`
- `ms_fabric_sql`
- `pyspark`
- `salesforce`
- `snowflake`
- `snowflake_sql`

No usar aliases historicos en la configuracion del runner, por ejemplo:

- `bigquery`
- `microsoft_fabric`
- `snowflake_snowpark`

Esos nombres pueden existir como alias internos en prompts o compatibilidad, pero el runner de tests debe usar los `tech_id` canonicos del catalogo.

## Archivo de configuracion

Archivo de ejemplo:

- [scripts/target_matrix_config.example.json](scripts/target_matrix_config.example.json)

Campos principales:

- `project_id`: UUID del proyecto. Desde este valor el runner resuelve `tenant_id` automaticamente.
- `target_labels`: ayuda visual. No afecta la ejecucion.
- `targets`: mapa `tech_id -> true/false`. Define que cartuchos participan en la corrida.
- `target_help`: ayuda visual. No afecta la ejecucion.
- `modes`: activa los modos post-Drafting a comparar.
- `exports`: define que bundles ZIP se descargan y si se genera el ZIP consolidado final.
- `options`: timeouts, polling y volumen de contenido descargado.

Ejemplo minimo:

```json
{
  "project_id": "84d8da3f-dacf-4b1f-8ecd-2a9bd63c8c18",
  "targets": {
    "snowflake_sql": true,
    "snowflake": false,
    "ms_fabric_sql": false
  },
  "modes": {
    "drafting_delivery": false,
    "structured_refinement": true,
    "intelligent_reengineering": false
  }
}
```

## Modos post-Drafting

- `drafting_delivery`: camino terminal. El runner no llama Refinement en este modo.
- `structured_refinement`: refinement medallion acotado.
- `intelligent_reengineering`: refinement con reingenieria adicional.

## Ejecucion

Comando recomendado:

```powershell
c:/proyectos_dev/UTM/.venv/Scripts/python.exe scripts/run_project_target_matrix.py --config-file scripts/target_matrix_config.example.json
```

Notas:

- no hace falta pasar `tenant-id` si el JSON ya tiene `project_id`
- el runner resuelve `tenant_id` desde metadata del proyecto
- si queres una plantilla nueva, se puede generar con `--write-config-template`

## Outputs generados

Carpeta base:

- `test_results/target_matrix_runs/<project_id>/<timestamp>_matrix/`

Archivos principales:

- `matrix_manifest.json`: configuracion efectiva de la corrida
- `matrix_run_status.json`: estado incremental de la corrida
- `matrix_summary.json`: resumen final de plan, resultados y fallas
- `<target>__<mode>/run_summary.json`: resumen detallado por combinacion
- `<target>__<mode>/after_drafting/`: snapshot de artefactos tras Drafting
- `<target>__<mode>/after_refinement/`: snapshot de artefactos tras Refinement, si aplica
- `<target>__<mode>/downloads/`: ZIPs descargados por combinacion
- `downloads/<timestamp>_matrix_bundle.zip`: ZIP consolidado de toda la corrida

## Interpretacion rapida

En `matrix_summary.json`:

- `plan`: combinaciones target + modo pedidas
- `results`: combinaciones completadas
- `failures`: combinaciones con error
- `status`: `COMPLETED` o `COMPLETED_WITH_ERRORS`
- `bundle_path`: ZIP consolidado final

En cada `run_summary.json`:

- `drafting`: resultado de la fase de migracion
- `refinement`: resultado de refinement, si aplica
- `refinement_skipped_reason`: razon del salto si el modo fue terminal
- `exports`: ZIPs descargados para esa combinacion
- `lifecycle`: secuencia de pasos ejecutados

## Validacion basica

Despues de tocar el runner o el parser de config, validar al menos:

```powershell
c:/proyectos_dev/UTM/.venv/Scripts/python.exe -m pytest apps/api/tests/test_target_matrix_service.py
```

Cobertura actual de esa prueba:

- parser del plan a partir de la matriz booleana
- generacion del bundle ZIP consolidado

## Estado actual

Estado validado durante esta sesion:

- corrida minima con `snowflake_sql + structured_refinement`: OK
- corrida ampliada con `ms_fabric_sql`, `snowflake` y `snowflake_sql` en `structured_refinement`: OK
- sin errores pendientes detectados en los archivos modificados para este feature