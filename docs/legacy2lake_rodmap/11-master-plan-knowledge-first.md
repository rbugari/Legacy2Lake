# Master Plan Knowledge-First

## Objetivo

Definir un plan maestro por fases y sprints para llevar Legacy2Lake desde su estado actual, ya fuerte en Discovery y Triage operativos, hacia una plataforma que comprenda, documente y estructure sistemas de carga de datos con profundidad suficiente para multiples downstreams.

El objetivo no es solo generar mejor codigo target. El objetivo es que el producto pueda:

1. explicar que hace un sistema legado
2. explicar como corre y de que depende
3. distinguir hechos, inferencias y recomendaciones
4. producir documentacion util para humanos
5. activar downstreams distintos con el mismo conocimiento base
6. aprovechar modelos LLM cada vez mejores sin reescribir el nucleo cada trimestre

## Principio rector

Los modelos van a mejorar. La ventaja competitiva no va a estar en el modelo solo, sino en el contexto util, estructurado, trazable y reusable que les demos.

Por eso, este plan asume:

1. deterministic-first para hechos nucleares
2. evidence-backed para toda inferencia importante
3. knowledge package versionado como contrato intermedio
4. UX orientada a revision humana, no a ocultar incertidumbre
5. agentes mejorados a futuro, pero siempre montados sobre mejor contexto y mejor retrieval

## Punto de partida real

Hoy el producto ya tiene una base valiosa:

1. Discovery con intake estructurado, evidencia y clasificacion manual
2. Triage con contexto global y por asset, rerun guiado y mejor visibilidad operacional
3. readiness, executive summary y gap workspace utilizables
4. packet de conocimiento fuerte a nivel asset
5. persistencia suficiente para empezar a consolidar un knowledge package de proyecto

Lo que falta para cumplir el objetivo mayor es:

1. consolidar el contrato de conocimiento a nivel proyecto
2. formalizar facts, inferences, recommendations y uncertainty
3. reconstruir mejor procesos, orquestacion y mapas operacionales
4. volver la documentacion un output de primera clase
5. desacoplar downstreams para documentacion, catalogo, generacion y rule candidates

## Regla de construccion

Cada bloque del plan debe ejecutarse en este orden:

1. contrato
2. persistencia
3. servicio o motor
4. tests deterministas
5. fixture real
6. exposicion en UI o export

Si hay que recortar alcance, se recorta primero UX cosmetica, despues adapters concretos, y ultimo el contrato de conocimiento.

## Fases

### Fase 1
Context substrate y knowledge package de proyecto.

### Fase 2
Discovery V2 factual y reconstruccion operacional.

### Fase 3
Triage V2 como comprension explicativa.

### Fase 4
Downstreams y documentacion de primera clase.

### Fase 5
Escalado, calidad y preparacion para mejores LLMs.

## Sprint 0 - Baseline ejecutable

### Objetivo

Congelar el marco tecnico del plan y convertir el knowledge-first en contrato operativo, no solo en intencion.

### Alcance

1. definir el `project knowledge package v1`
2. definir esquema comun de `fact`, `inference`, `recommendation`, `uncertainty`
3. definir versionado y compatibilidad hacia adelante del package
4. definir matriz de pruebas por capa
5. fijar lista de tecnologias fuente prioritarias para las siguientes fases

### Entregables

1. documento de contrato del package v1
2. schemas iniciales para entidades nucleares
3. decision de versionado y migracion del package
4. fixtures objetivo por tecnologia
5. tablero de cobertura del roadmap contra estado actual

### Criterios de cierre

1. existe un contrato estable de package de proyecto
2. existe una definicion clara de que entra y que no entra en v1
3. el equipo puede construir sin reinterpretar el objetivo cada sprint

## Sprint 1 - Project knowledge package foundation

### Objetivo

Pasar de persistencias dispersas a un contrato consolidado de conocimiento a nivel proyecto.

### Alcance

1. agregar ensamblado del package desde discovery, triage, evidencia, contexts y impacts
2. separar claramente hechos confirmados de interpretaciones
3. introducir referencias de evidencia normalizadas
4. introducir estado de completitud del package
5. exponer una lectura consistente del package para otros servicios

### Entregables

1. `project_knowledge_package` serializable y persistente
2. `evidence_ref` reutilizable en servicios y UI
3. ensamblador de package de proyecto
4. tests de contrato del package
5. endpoint de inspeccion del package

### Criterios de cierre

1. un proyecto puede exportar su package completo en formato consistente
2. summary, gaps y triage pueden leer del mismo contrato
3. no hace falta recomponer el estado desde texto libre para entender el proyecto

## Sprint 2 - Discovery V2 factual hardening

### Objetivo

Convertir Discovery en la capa que produce hechos estructurados y no solo inventario y support para triage.

### Alcance

1. enriquecer file inventory con `parse_status`, `technology`, `role_hint`, `confidence`
2. formalizar `asset_registry`
3. formalizar `evidence_registry`
4. capturar mejor referencias a tablas, jobs, scripts y configuraciones
5. mejorar heuristicas manuales para que alimenten hechos persistentes y no solo settings auxiliares

### Entregables

1. asset registry inicial de proyecto
2. evidence registry inicial de proyecto
3. package factual poblado desde Discovery
4. fixtures de discovery por tecnologia prioritaria
5. scorecard de calidad factual

### Criterios de cierre

1. Discovery produce un output factual reusable por multiples consumers
2. el porcentaje de elementos no clasificados baja de forma medible en fixtures reales
3. hay trazabilidad entre asset, evidencia y rutas fuente

## Sprint 3 - Process y dependency reconstruction

### Objetivo

Describir la solucion como sistema conectado y no como coleccion de archivos.

### Alcance

1. formalizar `process_registry`
2. reconstruir `asset -> process`
3. reconstruir `process -> dataset`
4. construir dependency graph inicial
5. persistir relaciones consultables y serializables

### Entregables

1. process registry inicial
2. dependency graph inicial
3. relaciones process-dataset y asset-process
4. consultas API para leer dependencias
5. fixtures validando grafos minimos esperados

### Criterios de cierre

1. el sistema identifica procesos principales en fixtures representativos
2. un revisor puede seguir el hilo de una carga principal sin leer todo el repo
3. los grafos se integran al package de proyecto

## Sprint 4 - Orchestration intelligence

### Objetivo

Sumar comportamiento operacional minimo viable para explicar como corre el sistema.

### Alcance

1. detectar triggers, schedules y depends_on
2. introducir `orchestration_step`
3. introducir `operational_constraint`
4. detectar retries, gating y puntos de fragilidad cuando haya senales suficientes
5. exponer una vista operacional inicial

### Entregables

1. orchestration graph inicial
2. modelo operacional minimo viable
3. resumen de interpretacion operacional por proyecto
4. trazabilidad de restricciones operativas a evidencia
5. fixtures con secuencias reconocibles

### Criterios de cierre

1. el proyecto puede explicarse como flujo
2. el sistema diferencia transformacion de coordinacion
3. el package ya sirve para reconstruir operacion, no solo estructura

## Sprint 5 - Triage V2 foundation

### Objetivo

Hacer que Triage produzca comprension util y no solo preparacion a generacion.

### Alcance

1. formalizar `project understanding summary`
2. formalizar `functional map`
3. formalizar `risk and gap map`
4. introducir `uncertainty report`
5. separar lo que es inferencia de lo que es recomendacion downstream

### Entregables

1. summary de proyecto basado en package
2. mapa funcional inicial
3. mapa de riesgos y gaps inicial
4. reporte de incertidumbre con motivos
5. servicios y tests de consistencia facts -> inferences

### Criterios de cierre

1. un humano puede entender el sistema usando el output de Triage
2. las principales incertidumbres quedan visibles y justificadas
3. el resumen ya no depende de prompts ad hoc sin contrato fuerte

## Sprint 6 - Triage operacional y conocimiento reusable

### Objetivo

Convertir Triage en una capa que decide que conocimiento merece externalizacion o revision humana.

### Alcance

1. detectar rule signals y reusable mappings
2. distinguir logica reusable contra logica local
3. priorizar activos y procesos core
4. producir `rule candidate summary`
5. enriquecer executive summary con prioridad operativa y funcional real

### Entregables

1. rule candidate summary
2. reusable knowledge classification
3. ranking de procesos y entidades core
4. ajustes de summary y gap workspace sobre el nuevo contrato
5. tests sobre deduplicacion y evidencia asociada

### Criterios de cierre

1. el sistema no solo entiende, tambien separa lo reusable de lo incidental
2. gaps y decisiones aparecen con contexto y prioridad creible
3. la salida se vuelve util para arquitectura y gobierno, no solo para migracion

## Sprint 7 - Downstream recommendation set

### Objetivo

Decidir que hacer con el conocimiento generado, sin forzar una sola salida.

### Alcance

1. formalizar `downstream recommendation set`
2. etiquetar destino recomendado por activo, proceso o hallazgo
3. modelar readiness por downstream
4. separar documentacion, catalogo, generacion y human review
5. introducir reglas de automatizacion segun incertidumbre

### Entregables

1. recommendation set versionado
2. readiness matrix por downstream
3. reglas de activacion por confianza e incertidumbre
4. endpoints y UI para revisar recomendaciones
5. trazabilidad recommendation -> evidence -> owner component

### Criterios de cierre

1. Triage ya no desemboca automaticamente en generacion
2. el mismo package puede activar mas de un downstream
3. la automatizacion baja cuando falta evidencia o sube la incertidumbre

## Sprint 8 - Documentation-first outputs

### Objetivo

Volver la documentacion enriquecida un producto de salida de primera clase.

### Alcance

1. definir `documentation export contract`
2. producir summary tecnico, funcional y operacional navegable
3. producir lineage y mapas exportables
4. generar anexos de evidencia y zonas de incertidumbre
5. permitir export de paquete de revision humana

### Entregables

1. documentation export contract
2. project dossier v1
3. anexos de evidencia por seccion
4. export JSON y formato humano legible
5. validacion manual con fixture real representativo

### Criterios de cierre

1. el sistema puede demostrar valor aunque no se genere codigo target
2. un tercero puede entender el sistema legado con el dossier exportado
3. documentacion y evidencia quedan conectadas y navegables

## Sprint 9 - Generation and catalog contracts hardening

### Objetivo

Mejorar downstreams existentes y futuros usando el package estructurado.

### Alcance

1. endurecer contrato para drafting agents
2. introducir export contract para catalogos
3. introducir adapter generico para gobierno externo
4. reducir contexto ambiguo que reciben agentes A, C, F y G donde aplique
5. mantener separacion entre direct translation y modernization

### Entregables

1. contract comun para downstreams
2. adapter de catalogo generico
3. nuevo input estructurado para generacion
4. trazabilidad knowledge -> output downstream
5. pruebas de no regresion en flujos productivos actuales

### Criterios de cierre

1. downstreams consumen el mismo package sin reanalisis total
2. los agentes reciben menos texto ambiguo y mas estructura util
3. la salida sigue respetando tenant isolation y stage model actual

## Sprint 10 - Human review cockpit

### Objetivo

Hacer visible el conocimiento del sistema en una UX de revision seria.

### Alcance

1. vista de procesos
2. vista de dependencias
3. vista de orquestacion
4. drill-down a evidencia y incertidumbre
5. decision workspace unificado para gaps, reglas y recomendaciones

### Entregables

1. cockpit de revision humana
2. filtros y recorridos por proceso, activo y downstream
3. drill-down a evidencia desde cualquier hallazgo importante
4. modo de revision operativa para proyectos grandes
5. telemetria de uso de revision humana

### Criterios de cierre

1. un analista puede revisar sin abrir cien archivos fuente
2. la incertidumbre no queda escondida
3. la UX consume contratos estables y no logica improvisada

## Sprint 11 - Quality, fixtures y future-ready LLM substrate

### Objetivo

Dejar la plataforma lista para escalar con mejores modelos sin romper repetibilidad.

### Alcance

1. contrato de retrieval por tipo de tarea
2. contexto empaquetado por objetivo de agente
3. scorecards de calidad factual, explicativa y downstream
4. fixtures curados por tecnologia y complejidad
5. regression suite para verificar que un mejor modelo mejora resultado y no destabiliza contrato

### Entregables

1. retrieval packs por tarea
2. evaluation harness de contexto y output
3. suite de fixtures reales y semi-reales
4. scorecard de calidad y cobertura
5. backlog de v2 posterior al plan base

### Criterios de cierre

1. cambiar de modelo no obliga a redisenar el producto
2. el sistema mejora porque el contexto es mejor y el contrato es estable
3. existe base medible para comparar modelos, prompts y pipelines

## Como aprovechar LLMs cada vez mejores sin rehacer todo

### Lo que debe quedar estable

1. knowledge package
2. evidence refs
3. contratos de downstream
4. taxonomia de incertidumbre
5. retrieval packs por tarea

### Lo que debe poder mejorar sprint a sprint

1. calidad de inferencias
2. cobertura semantica
3. deteccion de entidades y reglas
4. calidad del summary funcional y operacional
5. precision de recomendaciones downstream

### Regla practica

Si aparece un modelo mejor, se cambia el motor de inferencia. No se rompe el package, no se rompe la evidencia y no se reescribe la UX.

## Secuencia recomendada de ejecucion

### Tramo 1
Sprints 0 a 2.

Resultado esperado:
contrato de proyecto y base factual estable.

### Tramo 2
Sprints 3 a 6.

Resultado esperado:
comprension estructural, operacional y funcional creible.

### Tramo 3
Sprints 7 a 9.

Resultado esperado:
downstreams desacoplados y documentacion de primera clase.

### Tramo 4
Sprints 10 a 11.

Resultado esperado:
revision humana fuerte, calidad medible y base lista para modelos futuros.

## Prioridad si hay que recortar

1. mantener completos sprints 0 a 8
2. recortar cockpit antes que contratos
3. recortar adapters concretos antes que recommendation set y documentation export
4. recortar cobertura de tecnologias secundarias antes que debilitar el package central

## Definicion de exito del plan

Se considerara cumplido cuando Legacy2Lake pueda tomar un sistema legado heterogeneo y producir un paquete de conocimiento y documentacion que permita a un humano:

1. entender que hace el sistema
2. entender como opera
3. ver donde falta evidencia
4. decidir que downstream activar
5. confiar en que la mejora de modelos futuros aumentara la calidad del entendimiento sin obligar a reconstruir el producto desde cero