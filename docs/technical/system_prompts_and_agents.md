# Arquitectura de Agentes y System Prompts

El "cerebro" de la plataforma UTM (Legacy2Lake) no es un modelo monolítico, sino una orquestación de múltiples agentes especializados que colaboran para escanear, interpretar, auditar y documentar la migración.

Este documento detalla el rol de cada agente y expone sus **System Prompts reales**, revelando las reglas de comportamiento que gobiernan la IA.

## 1. El Ecosistema de Agentes (The Mesh)

La arquitectura sigue el patrón "Chain of Thought" y "Actor-Critic", donde un agente propone y otro valida.

```mermaid
graph TD
    User[Input Repository] -->|Discovery| A[Agent A: Detective]
    A -->|Mesh Graph| B[Human Validation]
    B -->|Approved Spec| C[Agent C: Architect]
    C -->|Draft Code| F[Agent F: The Auditor]
    F -->|Critique & Fix| F_Loop{Quality OK?}
    F_Loop -->|Yes| P[Persistence (Git/DB)]
    F_Loop -->|No| C
    P -->|Final Assets| G[Agent G: Governance]
    G -->|Docs & Lineage| Output[Documentation]
```

---

## 2. Detalle de Agentes y Prompts

### Agent A: El Detective (Discovery Service) → **UPGRADED TO ARCHITECT v2.0**
**Misión:** Ya no solo descubre archivos, ahora **infiere metadatos operacionales** automáticamente (Volume, PII, Latency).

**System Prompt Actual (`agent_a_discovery.md`):**
> "Eres el Agente de Triaje... Tu misión es procesar un 'Manifiesto de Repositorio' para reconstruir la malla de orquestación."

**Nuevas Capacidades (Phase 5):**
1. **Inferencia de Volumen:** Estima `LOW | MED | HIGH` basándose en el row count del esquema fuente.
2. **Detección de PII:** Analiza nombres de columnas (`email`, `ssn`, `phone`) y marca `is_pii = true`.
3. **Sugerencia de Particionamiento:** Si detecta columnas de tipo DATE con alta cardinalidad, sugiere `partition_key`.
4. **Heatmaps en UI:** Los datos de Discovery ahora se visualizan como heatmaps (PII Exposure, Criticality).

**Reglas Clave:**
1. **Clasificación Funcional:** Separa `CORE` (Lógica migratable) de `SUPPORT` (Configs) y `IGNORED` (Basura).
2. **Inferencia de Negocio:** Deduce entidades del mundo real (ej. `DimCustomer.dtsx` → Entity: `CUSTOMER`).
3. **Detección de Orquestación:** Busca llamadas explícitas (`Execute Package`) para crear flechas en el grafo.

---

### Agent C: El Arquitecto (Interpreter Service) → **CONTEXT-AWARE GENERATION**
**Misión:** Traducir la *intención de negocio* a código moderno (PySpark/Databricks). Ahora usa los metadatos de Architect v2.0 para **optimizar automáticamente**.

**System Prompt Actual (`agent_c_interpreter.md`):**
> "You are a Principal Data Engineer... Your goal is NOT to translate text, but to migrate **business intent** into high-performance, idempotent, and resilient code."

**Nuevas Capacidades (Phase 6):**
1. **Inyección de Particionamiento:** Si `metadata.partition_key` existe, genera `.partitionBy(col)`.
2. **Masking Automático de PII:** Si `metadata.is_pii = true`, genera `sha2(col("email"), 256)`.
3. **Optimización por Volumen:** Si `metadata.volume = HIGH`, prioriza shuffles eficientes.
4. **Variable Injection (Phase 8):** Usa placeholders `${VAR}` en lugar de valores hardcodeados.

**Reglas Clave:**
1. **Idempotencia Obligatoria:** Prohibido usar `mode("overwrite")`. Debe generar lógica `MERGE INTO` con claves de negocio.
2. **Integridad Referencial:** Debe inyectar manejo de "Miembros Desconocidos" (`COALESCE(col, -1)`) en los Lookups.
3. **Arquitectura Medallion:** Organiza el código en celdas claras: `Config` → `Extract` → `Transform` → `Load`.
4. **Surgical Logic:** Ignora el ruido del XML y extrae solo la "médula lógica" (queries y transformaciones).

---

### Agent F: El Auditor (Critic Service)
**Misión:** Garantizar la calidad antes de que el código toque el repositorio. Actúa como un "Senior Code Reviewer" despiadado.

**System Prompt Actual (`agent_f_critic.md`):**
> "You are a Senior Data Architect and the ultimate guardian of code quality... ensure it is not just functional, but **architecturally superior**."

**Reglas Clave (Checklist Estricto):**
1.  **Reject Hardcoding:** Si ve credenciales o rutas absolutas -> `REJECTED`.
2.  **Precision Casting:** Verifica que los `cast()` de Spark coincidan exactamente con el DDL de destino (ej. `Decimal(18,2)` vs `Double`).
3.  **Merge Validation:** Si es una carga Delta y no hay `MERGE`, rechaza el código.

---

### Agent G: Gobernanza (Governance Service) → **AI-DRIVEN CERTIFICATION**
**Misión:** Ya no solo genera documentación, ahora **audita el código** y certifica su calidad con un score numérico.

**System Prompt Actual (`agent_g_governance.md`):**
> "Your mission is to provide clarity, control, and documentation... transform raw Generated Code into high-level intelligence."

**Nuevas Capacidades (Phase 7):**
1. **Compliance Audit:** Verifica que las recomendaciones de Architect v2.0 fueron aplicadas (particionamiento, masking).
2. **Scoring (0-100):** Calcula un puntaje de certificación basado en checks automatizados.
3. **Runbook Automation:** Genera un documento técnico de handover (`Modernization_Runbook.md`).
4. **Variable Manifest:** Incluye `variables_manifest.json` en el ZIP de export.
5. **Data Quality Contracts (Phase 9):** Opcionalmente genera suites de Great Expectations y Soda.

**Reglas Clave:**
1. **Linaje:** Extrae tablas de origen y destino para crear una matriz de trazabilidad.
2. **PII Detection:** Escanea el código en busca de campos sensibles no enmascarados.
3. **Business Language:** Explica la lógica en inglés técnico, no solo repitiendo el código.
4. **Dual Output:** Retorna tanto `audit_json` (checks estructurados) como `runbook_markdown` (documentación).

---

## 3. Conclusión: El "Cerebro" de Shift-T

Lo que diferencia a UTM de un simple "convertidor de regex" es esta estructura de roles:

1.  **Contexto:** El Agente A entiende el "Todo" antes de tocar una línea de código.
2.  **Intención:** El Agente C ignora la sintaxis legacy y se enfoca en la lógica de datos.
3.  **Calidad:** El Agente F impide que la deuda técnica se propague al nuevo sistema.
4.  **Control:** El Agente G asegura que lo construido sea gobernable y entendible.

*Nota: Los prompts completos están disponibles en el directorio `apps/api/prompts/`.*
