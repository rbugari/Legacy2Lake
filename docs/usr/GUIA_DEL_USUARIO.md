# Guía de Usuario: Legacy2Lake v3.9 GA

Esta guía detalla el ciclo completo de vida dentro de la plataforma **Legacy2Lake**, desde la creación de una nueva solución hasta su despliegue en producción.

**Última Actualización**: 13 de febrero, 2026  
**Versión**: v3.9 GA (Visualización Integrada)

---

## ✨ Novedades V3.9 GA

### Nuevos Dashboards de Visualización
**En Triage (Fase 2)**: 4 dashboards avanzados
- 📏 **Quality Dashboard**: Métricas de calidad en 6 dimensiones
- 📑 **Schema Viewer**: Explorador interactivo de tablas/columnas
- 🔒 **PII Heatmap**: Detección de datos sensibles (GDPR/CCPA)
- ⚡ **Partition Recommendations**: Estrategias de optimización

**En Drafting (Fase 3)**: Nueva pestaña Quality
- Monitoreo de calidad durante generación de IR

**En Refinement (Fase 4)**: 4 nuevas tabs de validación
- 📝 **Code Review**: Comparación legacy vs moderno
- 📑 **Schema Validation**: Verificación de integridad DDL
- 🎯 **Quality Validation**: Chequeos end-to-end
- 🚀 **Performance Metrics**: Eficiencia y optimizaciones

---

## 🏗️ 0. Inicio: Creación de una Nueva Solución

El punto de partida es el **Dashboard Principal**. Aquí se centralizan todos los proyectos de migración.

### Pasos para crear una solución:
1.  **Localizar el Botón:** En la esquina superior derecha del Dashboard, busca el botón **"New Solution"** (o "Create Project").
2.  **Formulario de Configuración:**
    *   **Name (Nombre):** Asigna un identificador único al proyecto (ej: `Migracion_CRM_2024`).
    *   **Source Technology (Origen):** Selecciona la tecnología legada que vas a modernizar (ej: `Oracle PL/SQL`, `SQL Server T-SQL`, `SSIS`).
    *   **Target Technology (Destino):** Elige la arquitectura moderna deseada (ej: `Databricks (PySpark)`, `Snowflake (SQL)`, `AWS Glue`).
3.  **Acción:** Haz clic en **"Create Project"**.
    *   *¿Qué sucede internamente?* El sistema inicializa un nuevo espacio de trabajo, crea la estructura de carpetas en el servidor (`solutions/Migracion_CRM_...`) y te redirige automáticamente a la **Fase 1**.

---

## 🔍 Fase 1: Discovery (Descubrimiento Técnico)

**Objetivo:** Ingesta de código y análisis forense inicial.

### Interfaz y Acciones:
*   **Drop Zone (Zona de Carga):**
    *   Area central punteada. Arrastra aquí tus archivos fuenta (`.sql`, `.zip`, `.xml`, `.dtsx`).
    *   Al soltar los archivos, el sistema los carga al área de "Staging".
*   **Botón: "Run Discovery" (o "Analyze"):**
    *   *Agente:* Activa al **Agente A (Analista)**.
    *   *Acción:* Escanea línea por línea los archivos subidos. Identifica tablas, procedimientos, vistas y dependencias externas.
    *   *Resultado:* Genera un **Manifiesto de Inventario** y habilita el botón para avanzar.
*   **Botón: "Start Triage" (Aprobar):**
    *   Confirma que la ingesta es correcta y mueve los archivos a la siguiente etapa.

---

## 🚦 Fase 2: Triage (Estrategia y Clasificación)

**Objetivo:** Determinar el alcance del proyecto (Scoping).

### Interfaz y Acciones:
*   **Lienzo de Clasificación (Drag & Drop):**
    *   Verás una lista de objetos detectados (tablas, scripts).
    *   **Acción:** Arrastra los objetos críticos a la columna **"CORE"**.
    *   Arrastra lo obsoleto o innecesario a **"IGNORED"**.
*   **Botón: "Run Analysis" (Agente S):**
    *   *Agente:* Activa al **Agente S (Estratega/Scout)**.
    *   *Acción:* Calcula la complejidad ciclomática y estima el esfuerzo de migración para los objetos en "CORE".
    *   *Visualización:* Verás etiquetas de riesgo (Low, Medium, High) y un "Completeness Score".
*   **Botón: "Approve Triage":**
    *   Congela el alcance del proyecto. Nadie podrá añadir más archivos "CORE" sin reabrir esta fase. Prepara los archivos para la planificación.

---

## 📝 Fase 3: AI Drafting (Planificación y Diseño)

**Objetivo:** Diseño de la arquitectura de destino antes de codificar.

### Interfaz y Acciones:
*   **Botón: "Generate Plan" / "Run Pipeline":**
    *   *Agente:* **Agente C (Arquitecto)** en modo borrador.
    *   *Acción:* Analiza cada script SQL y propone su equivalente en la nube (ej: "Este `CREATE PROCEDURE` será un `Job` de Databricks"). Genera un "Blueprint".
*   **Tabs de Trabajo:**
    1.  **Output Explorer:** Permite ver los archivos de planificación generados (`plan.json` o borradores iniciales).
    2.  **Quality (NUEVO v3.9):** 🎨 Dashboard de calidad en tiempo real
        *   **6 Métricas de Calidad:** Completitud, Consistencia, Precisión, Validez, Unicidad, Puntualidad
        *   **Visualización:** Gauges circulares con código de colores (rojo/amarillo/verde)
        *   **Propósito:** Detectar problemas de calidad durante la generación del IR (Intermediate Representation)
        *   **Beneficio:** Permite ajustar el diseño antes de codificar
*   **Botón: "Approve and Refine":**
    *   Valida el plan técnico. Al hacer clic, el sistema queda listo para la generación masiva de código.

---

## 🛠️ Fase 4: Refinement (Modernización y Código)

**Objetivo:** Generación, optimización y prueba del código moderno.

### Interfaz y Acciones:
*   **Botón: "Refine & Modernize" (Play):**
    *   *Agentes:* Ejecuta en cadena a **Agente C (Coder)**, **Agente F (Fixer/Optimización)** y **Agente R (Reviewer)**.
    *   *Acción:* Transpila el código legado a código nativo de nube (PySpark/Snowflake) siguiendo la arquitectura "Medallion" (Bronze -> Silver -> Gold).
*   **Tabs de Trabajo (EXPANDIDO v3.9 - 2 → 6 tabs):**
    1.  **Orchestrator:** Muestra los logs en tiempo real de los agentes trabajando.
    2.  **Output Explorer:** Árbol de archivos con el código generado.
    3.  **Code Review (NUEVO v3.9):** 🎨 Comparación lado a lado
        *   **Panel Izquierdo:** Código **Legacy Original** (extraído automáticamente de Triage)
        *   **Panel Derecho:** Código **Refinado** generado por IA con resaltado de sintaxis
        *   **Características:** Diff visual, numeración de líneas, scroll sincronizado
        *   **Propósito:** Validar que la lógica de negocio se preservó durante la modernización
    4.  **Schema Validation (NUEVO v3.9):** 🎨 Explorador interactivo de DDL
        *   **Visualización:** Árbol expandible de tablas y columnas con metadatos
        *   **Contexto:** Muestra esquemas simulados de origen y destino
        *   **Validaciones:** Integridad referencial, tipos de datos compatibles
        *   **Propósito:** Verificar que todas las tablas están correctamente definidas
    5.  **Quality Validation (NUEVO v3.9):** 🎨 Suite de validación de calidad
        *   **6 Dimensiones:** Completitud, Consistencia, Precisión, Validez, Unicidad, Puntualidad
        *   **Características:** Tracking de violaciones, tendencias históricas, alertas
        *   **Propósito:** Asegurar calidad end-to-end del código generado
    6.  **Performance Metrics (NUEVO v3.9):** 🎨 Dashboard de optimización
        *   **Métricas:** Cache hit rates, paralelización, eficiencia de queries
        *   **Visualización:** Gráficos de líneas, barras de progreso, KPIs
        *   **Propósito:** Identificar cuellos de botella y oportunidades de optimización
*   **Botón: "Approve Phase 4":**
    *   Bloquea el código generado como "Candidato a Producción" y avanza a certificación.

---

## ✅ Fase 5: Certification (Governance & Audit)

**Objetivo:** Aseguramiento de calidad y cumplimiento normativo.

### Interfaz y Acciones:
*   **Panel de Métricas:** Muestra gráficos de "Architect Score", seguridad y performance.
*   **Botón: "Run AI Audit":**
    *   *Agente:* **Agente G (Guard/Auditor)**.
    *   *Acción:* Escanea el código Python/SQL generado buscando vulnerabilidades, hardcoded credentials o malas prácticas.
*   **Sección: "Design Standards":**
    *   Permite configurar reglas de nombrado (ej: "Todas las tablas deben empezar con `tbl_`").
*   **Botón: "Proceed to Handover":**
    *   *Condición:* Solo aparece si el "Compliance Score" es aprobatorio (verde).
    *   *Acción:* Autoriza el paso a la fase final de entrega.

---

## 📦 Fase 6: Handover (Entrega Final)

**Objetivo:** Empaquetado para despliegue por DevOps.

### Interfaz y Acciones:
*   **Editor de Variables de Entorno:**
    *   Tabla donde defines los valores reales para producción (conexiones, secretos, rutas S3/ADLS).
    *   La IA habrá identificado estas variables durante la refactorización.
*   **Generador de Runbook:**
    *   Visualiza el documento `RUNBOOK.md` generado automáticamente, con instrucciones de despliegue paso a paso.
*   **Botón: "Export Delivery" (Descargar):**
    *   *Acción Final:* Genera un archivo `.zip` ("Golden Bundle") que contiene:
        1.  Código fuente moderno (PySpark/SQL).
        2.  DAGs de orquestación (Airflow/Databricks Workflows).
        3.  Archivos de configuración (`.yaml`, `.json`).
        4.  Documentación técnica y Runbook.
    *   Descarga el paquete a tu máquina local.

---

## Resumen del Flujo de Trabajo

1.  **New Solution:** Creas el contenedor del proyecto.
2.  **Discovery:** La IA "lee" y entiende tu código viejo.
3.  **Triage:** Tú decides qué vale la pena migrar.
4.  **Drafting:** La IA propone cómo hacerlo.
5.  **Refinement:** La IA escribe y optimiza el código nuevo (aquí pasas la mayor parte del tiempo revisando).
6.  **Certification:** La IA audita la calidad y seguridad.
7.  **Handover:** Configuras variables y descargas el entregable final.
