# Listado de APIs (Contrato Backend-Frontend) - v3.2

Este documento describe la interfaz de comunicación entre el Frontend (React) y el Backend (FastAPI), detallando los endpoints principales, los flujos de orquestación y cómo se integran los motores de IA.

## v3.2 New Endpoints

| Endpoint | Method | Purpose | Phase |
|:---|:---|:---|:---|
| `GET /projects/{id}/architect` | GET | Retrieve Architect v2.0 inferred metadata (Volume, PII, Partition Keys) | Phase 5 |
| `GET /projects/{id}/settings` | GET | Retrieve project settings (including variables) | Phase 8 |
| `PATCH /projects/{id}/settings` | PATCH | Update project settings (variables, migration_limit) | Phase 8 |
| `GET /api/governance/certification/{id}` | GET | Get AI compliance audit report (score, checks) | Phase 7 |
| `GET /api/governance/export/{id}` | GET | Download SaaS export bundle (ZIP with runbook, variables, quality contracts) | Phase 7/9 |

---

## 1. Orquestación y Transpilación

Estos son los endpoints críticos que conectan la UI de diseño con los motores de generación de código (Spark/Snowflake).

### Ejecución de Transpilación (Unitario)
*   **Endpoint:** `POST /transpile/task`
*   **Descripción:** Recibe la definición de un nodo individual (paquete SSIS o script SQL) y orquesta la conversión a tecnología moderna.
*   **Lógica Interna (v3.2 Enhanced):**
    1.  Invoca a **Agent C (Interpreter)** para generar el primer borrador de código (PySpark/SQL).
    2.  **[Phase 6]** Agent C now uses **Architect v2.0 metadata** to auto-inject partitioning, PII masking, and variable placeholders.
    3.  Pasa el resultado a **Agent F (Critic)** para auditoría y optimización.
    4.  Persiste el resultado en disco y base de datos.
*   **Payload (Request) - Enhanced:**
    ```json
    {
      "node_data": { 
        "name": "Load_Customer_Data",
        "type": "SSIS_Package",
        "content": "<xml>...",
        "metadata": {
          "volume": "HIGH",
          "partition_key": "transaction_date",
          "is_pii": true
        },
        "variables": {
          "S3_ROOT": "s3://bucket",
          "ENV": "prod"
        }
      },
      "context": { 
        "solution_name": "Project_Alpha",
        "asset_id": "uuid..."
      }
    }
    ```
*   **Respuesta:** Objeto con el código generado (`final_code`), reporte del crítico y rutas de archivos guardados.

### Ejecución Masiva (Mesh)
*   **Endpoint:** `POST /transpile/all`
*   **Descripción:** Itera sobre todos los nodos de un grafo (malla) para convertirlos secuencialmente.
*   **Uso:** Se dispara desde el botón "Run Migration" en la vista de *Drafting*.

---

## 2. Gestión de Proyectos y Activos

Endpoints para la navegación y estructura del proyecto.

*   **`GET /projects`**: Lista todos los proyectos disponibles con su estado (`TRIAGE`, `DRAFTING`, etc.).
*   **`GET /projects/{project_id}`**: Obtiene metadatos detallados de un proyecto.
*   **`GET /discovery/project/{project_id}`**: Carga el "manifiesto" completo del proyecto para el Frontend:
    *   `assets`: Lista plana de archivos y objetos detectados.
    *   `metadata`: **[Phase 5]** Includes Architect v2.0 forensics (PII heatmap data).
    *   `prompt`: Prompt de sistema activo.
*   **`GET /projects/{id}/settings`**: **[Phase 8]** Retrieves project settings including `variables`.
*   **`PATCH /projects/{id}/settings`**: **[Phase 8]** Updates project settings (e.g., adding new variables).

---

## 3. Configuración y Know-How

Endpoints que permiten a la UI ajustar el comportamiento del motor de migración.

*   **Generadores (Motores de Destino):**
    *   **`GET /config/generators`**: Lista los motores soportados (Databricks, Snowflake, BigQuery) y cuál está activo por defecto.
    *   **`POST /config/generators/default`**: Cambia el motor de destino predeterminado.
    *   **`POST /config/generators/update`**: Actualiza el *Instruction Prompt* específico para un generador (ej. "Usa Pandas on Spark en lugar de RDDs").

*   **Cartuchos (Funcionalidades):**
    *   **`GET /cartridges`**: Lista módulos funcionales (ej. "PySpark Native", "dbt Core").
    *   **`POST /cartridges/update`**: Habilita o deshabilita cartuchos específicos.

*   **Configuración Global:**
    *   **`GET /config/technologies`**: Devuelve las tecnologías de origen/destino soportadas oficialmente por el sistema.

---

## 4. Gobernanza y Documentación (Enhanced in v3.2)

*   **`POST /governance/document`**: **[Legacy]** Dispara la generación de documentación técnica (Markdown) para el proyecto completo.
*   **`GET /api/governance/certification/{project_id}`**: **[Phase 7]** Retrieves AI compliance audit:
    ```json
    {
      "score": 95,
      "checks": [
        {"name": "PII Masking", "status": "PASSED"},
        {"name": "Partition Key Used", "status": "PASSED"}
      ],
      "recommendations": [],
      "lineage": [...],
      "runbook": "# Modernization Runbook..."
    }
    ```
*   **`GET /api/governance/export/{project_id}`**: **[Phase 7/9]** Downloads complete SaaS bundle:
    ```
    solution_export.zip
    ├── Modernization_Runbook.md
    ├── variables_manifest.json
    ├── quality_contracts/
    │   ├── gx/*.json
    │   └── soda/*.yaml
    └── [Bronze/Silver/Gold scripts]
    ```
*   **`POST /projects/{project_id}/layout`**: Guarda la posición visual de los nodos en el grafo (ReactFlow).

---

## 5. Architect v2.0 & Metadata (Phase 5)

*   **`GET /api/architect/{project_id}/heatmap`**: Returns PII and Criticality heatmap data for Discovery UI visualization.
*   **`POST /api/architect/infer`**: Manually trigger metadata inference for a specific asset.

---

## 6. Quality Contracts (Phase 9)

*   **`GET /api/quality/{project_id}/preview`**: Preview generated Great Expectations or Soda contracts for an asset.
*   Contracts are **not stored via API**—they are generated on-demand during export.

---

## Resumen de Integración

1.  **¿Qué dispara la transpilación?**
    La UI llama a `POST /transpile/task` cuando el usuario hace clic en "Transpile" sobre un nodo específico, o `POST /transpile/all` para el lote completo.

2.  **Comunicación con Spark:**
    El backend **NO** ejecuta el código Spark en tiempo real durante la fase de diseño. En su lugar, utiliza los **Agentes (C y F)** para *escribir* el código Python/Scala que luego se ejecutará en el clúster (Databricks). La validación es sintáctica y lógica (vía LLM), no de ejecución.

3.  **Flow v3.2 (With Intelligence):**
    - User uploads SSIS → **Agent A (Architect v2.0)** infers metadata
    - User reviews **Discovery Heatmaps** (PII, Criticality)
    - User proceeds to **Drafting** → **Agent C** generates optimized code using metadata
    - User defines **Variables** in Project Settings
    - **Agent G** audits final code and generates **Certification Report**
    - Export includes **Runbook**, **Variable Manifest**, and **Quality Contracts** (if applicable)
