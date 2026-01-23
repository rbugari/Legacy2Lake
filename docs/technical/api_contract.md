# Listado de APIs (Contrato Backend-Frontend)

Este documento describe la interfaz de comunicación entre el Frontend (React) y el Backend (FastAPI), detallando los endpoints principales, los flujos de orquestación y cómo se integran los motores de IA.

## 1. Orquestación y Transpilación

Estos son los endpoints críticos que conectan la UI de diseño con los motores de generación de código (Spark/Snowflake).

### Ejecución de Transpilación (Unitario)
*   **Endpoint:** `POST /transpile/task`
*   **Descripción:** Recibe la definición de un nodo individual (paquete SSIS o script SQL) y orquesta la conversión a tecnología moderna.
*   **Lógica Interna:**
    1.  Invoca a **Agent C (Interpreter)** para generar el primer borrador de código (PySpark/SQL).
    2.  Pasa el resultado a **Agent F (Critic)** para auditoría y optimización.
    3.  Persiste el resultado en disco y base de datos.
*   **Payload (Request):**
    ```json
    {
      "node_data": { 
        "name": "Load_Customer_Data",
        "type": "SSIS_Package",
        "content": "<xml>..." 
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

## 2. Gestión de Proyectos y Activos

Endpoints para la navegación y estructura del proyecto.

*   **`GET /projects`**: Lista todos los proyectos disponibles con su estado (`TRIAGE`, `DRAFTING`, etc.).
*   **`GET /projects/{project_id}`**: Obtiene metadatos detallados de un proyecto.
*   **`GET /discovery/project/{project_id}`**: Carga el "manifiesto" completo del proyecto para el Frontend:
    *   `assets`: Lista plana de archivos y objetos detectados.
    *   `prompt`: Prompt de sistema activo.

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

## 4. Gobernanza y Documentación

*   **`POST /governance/document`**: Dispara la generación de documentación técnica (Markdown) para el proyecto completo, utilizando el **Agent G**.
*   **`POST /projects/{project_id}/layout`**: Guarda la posición visual de los nodos en el grafo (ReactFlow) para mantener el ordenamiento del usuario.

## Resumen de Integración

1.  **¿Qué dispara la transpilación?**
    La UI llama a `POST /transpile/task` cuando el usuario hace clic en "Transpile" sobre un nodo específico, o `POST /transpile/all` para el lote completo.

2.  **Comunicación con Spark:**
    El backend **NO** ejecuta el código Spark en tiempo real durante la fase de diseño. En su lugar, utiliza los **Agentes (C y F)** para *escribir* el código Python/Scala que luego se ejecutará en el clúster (Databricks). La validación es sintáctica y lógica (vía LLM), no de ejecución.
