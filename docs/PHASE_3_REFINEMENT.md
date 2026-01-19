# Fase 3: Refinement & Medallion Architecture (Guía Completa)

## 📌 Introducción
La fase de **Refinement (Stage 3)** es el paso final de la transformación técnica en Shift-T. Su objetivo es tomar el código PySpark generado en la fase de Drafting y transformarlo en una arquitectura de datos organizada, eficiente y lista para operaciones empresariales siguiendo el modelo **Medallion (Bronze/Silver/Gold)**.

---

## 👨‍💻 Para el Usuario: ¿Qué es el "Shift-T Loop"?

En esta etapa, el sistema aplica una capa de "Súper-Ingeniería" a tus scripts. No solo tenemos código que funciona, sino una arquitectura que escala.

### Beneficios del Refinado
1.  **Organización Medallion:** Tus scripts se separan automáticamente en:
    *   **Bronze:** Carga cruda y preservación de historia.
    *   **Silver:** Limpieza, tipado estricto y deduplicación.
    *   **Gold:** Agregaciones de negocio y tablas finales listas para BI.
2.  **Optimización Automática:** La IA detecta patrones de Spark ineficientes y los corrige (ej: evitando *shuffles* innecesarios o *small files problem*).
3.  **Seguridad & Auditoría:** Se inyectan controles de acceso y se valida que no existan vulnerabilidades en el código generado.

---

## ⚙️ Para el Equipo Técnico: El Refinement Orchestrator

El proceso de Refinement es una cadena de agentes especializados operando sobre el sistema de archivos del proyecto.

### 1. Profiler (Agent P)
Realiza un análisis estático de la "solución borracha" (Draft). Identifica cuántos archivos hay, sus dependencias cruzadas y prepara el contexto para los arquitectos.

### 2. Architect (Agent A)
Es el responsable de la segmentación. Crea carpetas físicas (`Bronze/`, `Silver/`, `Gold/`) y distribuye la lógica basándose en el propósito del dato. Inyecta los "headers" y configuraciones globales de Databricks necesarios para cada capa.

### 3. Refactoring (Agent R)
El "pulidor" de código. Aplica transformaciones de bajo nivel:
*   **Vectorización:** Asegura que las operaciones usen funciones nativas de Spark.
*   **Security Injection:** Reemplaza cualquier rastro de configuración manual por llamadas seguras a *Secret Scopes*.
*   **Data Quality:** Añade bloques de validación de esquemas (`.cast()`) obligatorios.

## 4. Ops Auditor: Gobernanza y Calidad

El auditor garantiza que el código cumpla con las "Golden Rules" de Shift-T antes de pasar a producción:

### ✅ Reglas de Oro (The Golden Rules)
1.  **Seguridad**: Credenciales reemplazadas por `dbutils.secrets.get()`.
2.  **Idempotencia**: Implementación estricta de `MERGE` (Upsert) en Silver/Gold.
3.  **Dynamic Key Detection**:
    *   El sistema detecta automáticamente claves compuestas analizando `dropDuplicates(['A','B'])` o `Window.partitionBy`.
    *   Esto genera condiciones `MERGE` precisas: `tgt.A=src.A AND tgt.B=src.B`.
4.  **Optimización**: Inyección de `OPTIMIZE` y `ZORDER` en claves de alta cardinalidad.

---

## 🚀 Resultados del Proceso
Al finalizar el pipeline de refinamiento, el directorio `Refinement` (Stage 3) contendrá:

```text
Project_Name/
├── Refinement/
│   ├── Bronze/       # Ingesta Cruda (+metadata)
│   ├── Silver/       # Limpieza, Deduplicación y MERGE
│   └── Gold/         # Agregaciones de Negocio
├── refinement.log    # Trazabilidad completa
└── profile_metadata  # Estadísticas y claves detectadas
```

## ⏭️ Próximos Pasos: Certificación y Entrega
Una vez validado por el Ops Auditor (verificando que la lógica MERGE coincida con las claves primarias detectadas), el proyecto está listo para la **Fase 4: Governance**.

---
*Shift-T Documentation Framework v1.0 - Stage 3*
