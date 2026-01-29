CREATE TABLE Dim_Customers (
    CustomerID INT NOT NULL PRIMARY KEY,
    CustomerName VARCHAR(255),
    Email VARCHAR(255),
    Phone VARCHAR(50),
    CreatedAt DATETIME
);
