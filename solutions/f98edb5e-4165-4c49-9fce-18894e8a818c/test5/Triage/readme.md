Proyecto ETL - Data Warehouse de Ventas (Star Schema)

Este repositorio contiene la arquitectura de datos y los procesos de integración (ETL) para la construcción de un almacén de datos orientado al análisis de ventas.

📋 Descripción Funcional

El proyecto se encarga de transformar datos operacionales en un Modelo en Estrella. Funcionalmente, la solución realiza:

Carga Incremental de Maestros: Extrae nuevos registros de empleados, clientes, transportistas y proveedores basándose en marcas de agua (Max ID).

Gestión de Productos (SCD): Implementa la técnica de Slowly Changing Dimension para productos. Permite rastrear cambios históricos en categorías y proveedores, mientras mantiene actualizaciones directas en precios y nombres.

Integridad Referencial de Hechos: El proceso de ventas valida que cada transacción tenga dimensiones válidas asociadas antes de su inserción definitiva.

Optimización por Staging: Utiliza tablas temporales para el cruce masivo de datos de órdenes y detalles de órdenes, minimizando el impacto en el sistema fuente.

📂 Estructura del Repositorio

Scripts de Base de Datos

Origen_Transaccional.sql: Contiene el DDL para crear el ecosistema fuente (tablas de RRHH, Producción y Ventas).

Destino_DataWarehouse.sql: Contiene el DDL para el almacén de datos, incluyendo claves subrogadas para uniones eficientes y tablas de paso.

Paquetes ETL (SSIS)

Dim*.dtsx: Paquetes dedicados a la población de dimensiones.

FactSales.dtsx: Paquete principal para la orquestación de la tabla de hechos.

⚙️ Requisitos Técnicos

Motor: SQL Server 2012 o superior.

Herramienta: SQL Server Data Tools (SSDT) para la edición de paquetes .dtsx.

Estándar: ANSI SQL básico para máxima compatibilidad.

Generado por Ingeniería de Datos para el pipeline de Business Intelligence.