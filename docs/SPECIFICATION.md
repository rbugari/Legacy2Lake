# **Proyecto Shift-T: Marco de Modernización de Datos Inteligente**

## **1\. Visión y Propósito**

**Shift-T** es una plataforma de ingeniería de datos asistida por IA diseñada para automatizar y optimizar la transición de arquitecturas legacy (ETL tradicional) a ecosistemas modernos de Cloud Lakehouse (ELT/ETLT). El concepto central del proyecto, "Mover la T", no es solo un cambio de siglas; representa una reubicación estratégica de la lógica de transformación.

Mientras que en el ETL tradicional la transformación ocurre en un servidor intermedio rígido que suele ser un cuello de botella, en el modelo **Shift-T** buscamos que la lógica se ejecute directamente sobre procesadores distribuidos y elásticos (como Spark o Snowflake). Esto elimina la latencia de movimiento de datos y permite que las empresas escalen su capacidad analítica de manera independiente al volumen de datos, reduciendo drásticamente los costos operativos y el mantenimiento de infraestructura propia.

## **2\. Definiciones de Misión para Antigravity**

Para asegurar el éxito del desarrollo, el sistema debe cumplir con los siguientes pilares de diseño:

* **Agnosticismo de Origen y Formato:** La herramienta debe ser capaz de procesar repositorios heterogéneos. Esto incluye desde archivos XML complejos de SSIS (.dtsx) y exportaciones de Informatica, hasta scripts SQL procedimentales o código Python legacy. La meta es que el sistema "entienda" la intención detrás del código, independientemente de su sintaxis original.  
* **Transpilación de Alta Fidelidad (Semantic Mapping):** No buscamos una traducción literal "línea por línea", la cual suele generar código ineficiente en la nube. Shift-T debe adaptar paradigmas: por ejemplo, convertir un bucle manual que itera sobre filas en SQL Server hacia una operación vectorizada en PySpark o una consulta declarativa optimizada en SQL de nube.  
* **Linaje Nativo y Observabilidad:** El linaje de datos no debe ser una tarea posterior. Shift-T genera metadatos de linaje de columna (Column-level lineage) en tiempo real mientras traduce. Esto significa que cada columna en la tabla de destino tendrá una "partida de nacimiento" digital que explica qué transformaciones sufrió y de qué campo origen provino.  
* **Bucle de Refinamiento (Shift-T Loop):** Implementación de una capa de auditoría donde un modelo de razonamiento avanzado (como o1-preview) evalúa la primera versión del código generado para detectar ineficiencias, riesgos de seguridad o falta de estándares, permitiendo una iteración de mejora antes de que el desarrollador vea el resultado.

## **3\. Arquitectura Técnica Detallada**

### **3.1. Stack de Software y Justificación**

* **Backend (Cerebro):** Python 3.11+. Se elige por su ecosistema maduro en IA y procesamiento de datos. Se integrará **FastAPI** para gestionar solicitudes asíncronas de larga duración, permitiendo que el usuario reciba actualizaciones parciales del estado de la migración.  
* **Orquestación de Agentes (Flujo):** **LangGraph**. A diferencia de los flujos lineales, LangGraph permite que los agentes "conversen" y vuelvan a estados anteriores si el Agente F detecta un error en la traducción del Agente C, creando un sistema auto-corrector.  
* **Parser de SQL (Dialectos):** sqlglot. Fundamental para descomponer consultas complejas en árboles de sintaxis abstracta (AST) y reconstruirlas en el dialecto de destino sin perder la semántica de la consulta.  
* **Base de Datos y Persistencia:** **Supabase (PostgreSQL \+ pgvector)**. Supabase actuará como el "Mission Control", almacenando:  
  * El estado global de cada migración para permitir reanudaciones.  
  * Embebedores vectoriales de transformaciones comunes para acelerar futuras migraciones mediante memoria de contexto.  
* **Frontend (Interfaz):** Next.js con Tailwind CSS. Se utilizará **React Flow** para renderizar la malla de orquestación, permitiendo que el usuario mueva nodos, ajuste dependencias y valide visualmente el linaje antes de generar el código.

### **3.2. Esquema de Datos en Supabase (Estructura de soporte)**

* projects: Almacena el contexto global, credenciales anonimizadas y configuraciones de temperatura de los LLMs.  
* assets: Registro individual de cada archivo cargado, incluyendo hashes de contenido para evitar procesamientos duplicados y clasificaciones de complejidad inicial.  
* nodes\_edges: Persistencia del grafo de la malla, esencial para que el frontend pueda reconstruir la vista de orquestación sin re-procesar todo el repositorio.  
* transformations: Tabla de mapeo crítico que guarda el fragmento de código original y su versión traducida, sirviendo de base para auditorías de calidad.  
* lineage\_metadata: JSON estructurado que sigue el estándar de OpenLineage para facilitar la importación a catálogos externos.

## **4\. Sistema Multi-Agente (Responsabilidades)**

### **Agente A: Detective (Discovery)**

Realiza un escaneo profundo de la estructura del repositorio. Identifica no solo tipos de archivos, sino versiones de herramientas legacy y dependencias externas no declaradas. Clasifica los paquetes por riesgo: aquellos con "Script Tasks" personalizadas se marcan para atención especial del Agente F.

### **Agente B: Cartógrafo (Lineage & Mesh)**

Su objetivo es la visualización. Escanea las restricciones de precedencia y flujos de control para construir el grafo de ejecución. Determina qué procesos pueden ejecutarse en paralelo en la nueva arquitectura de nube, optimizando el tiempo total de ejecución.

### **Agente C: Intérprete (Transpiler)**

El motor de ejecución de código. Utiliza prompts de ingeniería de pocos pasos para aplicar patrones de diseño específicos de la tecnología de destino (ej. implementar SCD Type 2 usando Delta Lake Merge en lugar de lógica manual de actualización).

### **Agente F: Crítico (Refinement & Optimization)**

Actúa como un arquitecto senior. Analiza el proyecto completo en busca de:

1. **Anti-patrones:** Uso de cursores, bucles anidados o gestión manual de transacciones que son ineficientes en entornos distribuidos.  
2. **Implicaciones de Costo:** Sugiere cambios en el código que reduzcan el consumo de computación (FinOps).  
3. **Consistencia:** Asegura que todas las transformaciones sigan el mismo estándar de nomenclatura y manejo de errores definido en el 00\_config.

## **5\. Workflow Paso a Paso (Ciclo de Vida de Shift-T)**

### **Paso 1: Ingesta e Identificación**

El proceso comienza con la carga de los activos. El **Agente A** no solo lista archivos, sino que genera un informe de "Huella Tecnológica", informando al usuario si hay componentes que la herramienta no soporta nativamente (ej. componentes de terceros en SSIS) para gestionar expectativas desde el inicio.

### **Paso 2: Construcción de la Malla de Control**

El **Agente B** traduce el flujo de control legacy a una representación de grafos. En este punto, el usuario interactúa con la interfaz web para validar que el orden de ejecución es el correcto, pudiendo agrupar procesos que antes estaban dispersos en una única capa del modelo Medallion (Bronze/Silver/Gold).

### **Paso 3: Transpilación y Extracción de Metadata**

Se inicia la generación masiva de código. Mientras el **Agente C** escribe los notebooks o scripts, el **Agente E** (Escribano) documenta cada transformación en la base de datos de metadata. Este proceso es asíncrono; el usuario ve una barra de progreso por cada paquete o script procesado.

### **Paso 4: El Bucle de Refinamiento (Iteración de Calidad)**

Una vez terminado el "Draft", el **Agente F** presenta un reporte de hallazgos. Por ejemplo: *"He notado que usas la misma lógica de limpieza en 5 tablas distintas; he creado una función compartida en el notebook de utilidades para reducir la redundancia"*. El usuario aprueba estas sugerencias y el sistema regenera las partes afectadas.

### **Paso 5: Despliegue y Entrega de Documentación**

Se empaqueta un archivo ZIP que contiene el repositorio de código listo para Git, los archivos de orquestación (YAML para Workflows) y, crucialmente, el **Manual de Operación** generado por IA que explica cómo funciona la nueva arquitectura y qué paquetes originales fueron reemplazados por cada nuevo componente.

## **6\. Instrucciones de Implementación para Antigravity**

1. **Priorización de Parsers:** Implementar primero el parser de archivos .dtsx (SSIS XML), ya que presenta el mayor desafío de ingeniería inversa. Utilizar esquemas XSD para validar la estructura antes del procesamiento.  
2. **Manejo de Estados:** La clase MigrationState debe persistir cada 10 segundos en Supabase. Esto asegura que, en migraciones grandes que duren horas, el sistema pueda recuperarse de cualquier fallo de red sin perder el progreso.  
3. **Seguridad y Privacidad:** El sistema debe incluir un filtro de anonimización. Antes de enviar cualquier fragmento de código a los LLMs, se deben detectar y enmascarar IPs, nombres de servidores, usuarios y contraseñas mediante expresiones regulares y NER (Named Entity Recognition).  
4. **Gestión de Rate Limits:** Implementar una cola de tareas con **Exponential Backoff** para las llamadas a las APIs de los modelos de lenguaje, asegurando que la herramienta no falle ante picos de demanda o limitaciones de cuota.

## **7. Anexo Técnico: Estándares de Cumplimiento (v2.0)**

### **7.1 Estabilidad de Llaves Surrogadas (Stable Keys)**
Para garantizar la **Idempotencia** en tablas de dimensiones, Shift-T implementa obligatoriamente el patrón "Lookup + New":
1.  **Lectura del Target**: Se cargan las llaves de negocio y surrogadas existentes.
2.  **Join**: Se cruzan los datos entrantes con los existentes.
3.  **Preservación**: Si ya existe una llave surrogada, se mantiene intacta.
4.  **Generación Incremental**: Solo se generan nuevas llaves (`row_number + max_sk`) para registros nuevos.

### **7.2 Tipado Estricto (Type Safety)**
El Agente C debe inyectar un bucle de casting explícito antes de cualquier escritura. No se permite la inferencia de tipos de Spark. Cada columna debe ser convertida explícitamente (`.cast()`) al tipo de dato definido en el esquema target (JSON Schema) para asegurar la integridad total de los datos.