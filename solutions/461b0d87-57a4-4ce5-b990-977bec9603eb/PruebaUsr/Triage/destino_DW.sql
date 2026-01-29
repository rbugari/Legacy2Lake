/* SCRIPT DE TABLAS DE DESTINO (Data Warehouse) */

-- Dimensión de Empleados
CREATE TABLE DimEmployee (
    empkey INT IDENTITY(1,1) PRIMARY KEY,
    empid INT,
    fullname NVARCHAR(31),
    title NVARCHAR(30),
    city NVARCHAR(15),
    country NVARCHAR(15),
    address NVARCHAR(60),
    phone NVARCHAR(24)
); [cite: 278, 305-314]

-- Dimensión de Categorías (Clave Natural)
CREATE TABLE DimCategory (
    categoryid INT PRIMARY KEY,
    categoryname NVARCHAR(15)
); [cite: 401, 420-422]

-- Dimensión de Proveedores
CREATE TABLE DimSupplier (
    supplierKay INT IDENTITY(1,1) PRIMARY KEY,
    supplierid INT,
    companyname NVARCHAR(100),
    address NVARCHAR(200),
    postalcode NVARCHAR(100),
    phone NVARCHAR(100),
    city NVARCHAR(100),
    country NVARCHAR(100)
); [cite: 1011, 1038-1047]

-- Dimensión de Transportistas
CREATE TABLE DimShipper (
    shipperkey INT IDENTITY(1,1) PRIMARY KEY,
    shipperid INT,
    companyname NVARCHAR(40),
    phone NVARCHAR(24)
); [cite: 1133, 1154-1157]

-- Dimensión de Clientes
CREATE TABLE DimCustomer (
    custkey INT IDENTITY(1,1) PRIMARY KEY,
    custid INT,
    contactname NVARCHAR(30),
    city NVARCHAR(15),
    country NVARCHAR(15),
    address NVARCHAR(60),
    phone NVARCHAR(24),
    postalcode NVARCHAR(10)
); [cite: 484, 511-520]

-- Dimensión de Productos (Soporta SCD Tipo 2)
CREATE TABLE DimProduct (
    productkey INT IDENTITY(1,1) PRIMARY KEY,
    productid INT,
    productname NVARCHAR(100),
    supplierid INT,
    categoryid INT,
    unitprice MONEY,
    discontinued BIT,
    Flag BIT DEFAULT 1 -- Columna de versión actual [cite: 1002]
); [cite: 640, 666-673]

-- Tabla Temporal de Staging
CREATE TABLE tempStage (
    keys INT IDENTITY(1,1) PRIMARY KEY,
    orderid INT,
    custid INT,
    empid INT,
    shipperid INT,
    categoryid INT,
    supplierid INT,
    qty SMALLINT,
    unitprice MONEY,
    discount NUMERIC(4,3),
    productid INT
); [cite: 2-4]

-- Tabla de Hechos Final
CREATE TABLE FactSales (
    factKey BIGINT IDENTITY(1,1) PRIMARY KEY,
    orderid INT,
    custid INT,
    empid INT,
    shipperid INT,
    categoryid INT,
    supplierid INT,
    qty SMALLINT,
    unitprice MONEY,
    discount NUMERIC(4,3),
    productid INT
); [cite: 10, 40-50]