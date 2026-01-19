# Fase 4: Governance & Compliance (Guía Completa)

## 📌 Introducción
La fase de **Governance (Stage 4)** es el cierre del ciclo de vida de modernización en Shift-T. Su propósito es proporcionar las evidencias técnicas, el linaje de datos y los paquetes de despliegue necesarios para garantizar que la nueva arquitectura de datos no solo es funcional, sino que cumple con todos los estándares de gobernanza corporativa.

---

## 👨‍💻 Para el Usuario: Certificación de Modernización

En esta etapa final, el sistema genera la "Partida de Nacimiento" y el "Pasaporte" de tu nueva solución de datos.

### Entregables de Gobernanza
1.  **Certificado de Modernización:** Un informe ejecutivo que incluye el score de calidad de la migración, estadísticas de archivos procesados y líneas de código modernizadas.
2.  **Mapeo de Linaje (End-to-End):** Una visualización (o JSON estructurado) que muestra exactamente de qué paquete legado proviene cada nueva tabla en las capas Bronze, Silver y Gold.
3.  **Logs de Cumplimiento:** Registro de todas las auditorías de seguridad y performance realizadas por los agentes OpsAuditor y Refactoring.

---

## ⚙️ Para el Equipo Técnico: Servicios de Gobernanza

La fase de gobernanza es principalmente un servicio de agregación y empaquetado de metadatos persistidos durante todo el workflow.

### 1. Certification Engine (`get_certification_report`)
Este servicio escanea el directorio `Refinement/` para extraer métricas reales:
*   **Recuento de Activos:** Cuántos scripts se generaron para cada capa Medallion.
*   **Volumetría de Código:** Tamaño total de la nueva base de código.
*   **Compliance Score:** Un puntaje dinámico que valida:
    *   Existencia de la capa Gold.
    *   Validación de idempotencia (`MERGE` vs claves primarias detectadas).
    *   Ausencia de credenciales hardcodeadas.

### 2. Lineage Mapper (`_generate_lineage`)
Utiliza una heurística basada en los metadatos de los assets originales para mapear el flujo de datos:
*   **Source:** Archivo `.dtsx` o SQL original.
*   **Targets:** Referencias unívocas en el Lakehouse (e.g., `main.silver_curated.my_table`).
*   **Estándar:** Sigue principios de OpenLineage para facilitar la integración con catálogos externos.

### 3. Solution Bundler (`create_export_bundle`)
Crea un paquete ZIP comprimido que contiene la solución completa lista para ser entregada al equipo de DevOps:
*   Código fuente optimizado (Bronze/Silver/Gold).
*   Logs de migración.
*   Documentación técnica generada.
*   Metadatos de gobernanza.

---

## 🚀 Cierre y Entrega
Al completar esta fase, el usuario puede descargar el **Bundle de Solución**. Este archivo representa la versión final, auditada y certificada de la modernización.

---
*Shift-T Documentation Framework v1.0 - Stage 4*
