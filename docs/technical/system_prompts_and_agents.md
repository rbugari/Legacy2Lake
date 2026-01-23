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

### Agent A: El Detective (Discovery Service)
**Misión:** Entender qué hace el repositorio sin ejecutarlo. Construye el mapa (grafo) de dependencias.

**System Prompt Actual (`agent_a_discovery.md`):**
> "Eres el Agente de Triaje... Tu misión es procesar un 'Manifiesto de Repositorio' para reconstruir la malla de orquestación."

**Reglas Clave:**
1.  **Clasificación Funcional:** Separa `CORE` (Lógica migratable) de `SUPPORT` (Configs) y `IGNORED` (Basura).
2.  **Inferencia de Negocio:** Deduce entidades del mundo real (ej. `DimCustomer.dtsx` -> Entity: `CUSTOMER`).
3.  **Detección de Orquestación:** Busca llamadas explícitas (`Execute Package`) para crear flechas en el grafo.

---

### Agent C: El Arquitecto (Interpreter Service)
**Misión:** Traducir la *intención de negocio* a código moderno (PySpark/Databricks). No traduce línea por línea, re-imagina el proceso.

**System Prompt Actual (`agent_c_interpreter.md`):**
> "You are a Principal Data Engineer... Your goal is NOT to translate text, but to migrate **business intent** into high-performance, idempotent, and resilient code."

**Reglas Clave:**
1.  **Idempotencia Obligatoria:** Prohibido usar `mode("overwrite")`. Debe generar lógica `MERGE INTO` con claves de negocio.
2.  **Integridad Referencial:** Debe inyectar manejo de "Miembros Desconocidos" (`COALESCE(col, -1)`) en los Lookups, algo que SSIS suele ignorar.
3.  **Arquitectura Medallion:** Organiza el código en celdas claras: `Config` -> `Extract` -> `Transform` -> `Load`.
4.  **Surgical Logic:** Ignora el ruido del XML y extrae solo la "médula lógica" (queries y transformaciones).

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

### Agent G: Gobernanza (Governance Service)
**Misión:** Generar la documentación técnica y de negocio que los desarrolladores humanos odian escribir.

**System Prompt Actual (`agent_g_governance.md`):**
> "Your mission is to provide clarity, control, and documentation... transform raw Generated Code into high-level intelligence."

**Reglas Clave:**
1.  **Linaje:** Extrae tablas de origen y destino para crear una matriz de trazabilidad.
2.  **PII Detection:** Escanea el código en busca de campos sensibles no enmascarados.
3.  **Business Language:** Explica la lógica en inglés técnico, no solo repitiendo el código.

---

## 3. Conclusión: El "Cerebro" de Shift-T

Lo que diferencia a UTM de un simple "convertidor de regex" es esta estructura de roles:

1.  **Contexto:** El Agente A entiende el "Todo" antes de tocar una línea de código.
2.  **Intención:** El Agente C ignora la sintaxis legacy y se enfoca en la lógica de datos.
3.  **Calidad:** El Agente F impide que la deuda técnica se propague al nuevo sistema.
4.  **Control:** El Agente G asegura que lo construido sea gobernable y entendible.

*Nota: Los prompts completos están disponibles en el directorio `apps/api/prompts/`.*
