/* SCRIPT DE TABLAS DE ORIGEN (SQL Server Básico) */

-- Dimensiones de Producción
CREATE TABLE Categories (
    categoryid INT PRIMARY KEY,
    categoryname NVARCHAR(15)
); [cite: 433, 442-446]

CREATE TABLE Suppliers (
    supplierid INT PRIMARY KEY,
    companyname NVARCHAR(40),
    address NVARCHAR(60),
    postalcode NVARCHAR(10),
    phone NVARCHAR(24),
    city NVARCHAR(15),
    country NVARCHAR(15)
); [cite: 1058, 1067-1083]

CREATE TABLE Products (
    productid INT PRIMARY KEY,
    productname NVARCHAR(40),
    supplierid INT,
    categoryid INT,
    unitprice MONEY,
    discontinued BIT
); [cite: 795, 802-815]

-- Dimensiones de Ventas y RRHH
CREATE TABLE Employees (
    empid INT PRIMARY KEY,
    firstname NVARCHAR(10),
    lastname NVARCHAR(20),
    title NVARCHAR(30),
    city NVARCHAR(15),
    country NVARCHAR(15),
    address NVARCHAR(60),
    phone NVARCHAR(24)
); [cite: 325, 334-350]

CREATE TABLE Shippers (
    shipperid INT PRIMARY KEY,
    companyname NVARCHAR(40),
    phone NVARCHAR(24)
); [cite: 1169, 1178-1184]

CREATE TABLE Customers (
    custid INT PRIMARY KEY,
    contactname NVARCHAR(30),
    city NVARCHAR(15),
    country NVARCHAR(15),
    address NVARCHAR(60),
    phone NVARCHAR(24),
    postalcode NVARCHAR(10)
); [cite: 531, 540-556]

-- Transaccional de Ventas
CREATE TABLE Orders (
    orderid INT PRIMARY KEY,
    custid INT,
    empid INT,
    shipperid INT
); [cite: 182]

CREATE TABLE OrderDetails (
    orderid INT,
    productid INT,
    unitprice MONEY,
    qty SMALLINT,
    discount NUMERIC(4,3),
    PRIMARY KEY (orderid, productid)
); [cite: 182-183]