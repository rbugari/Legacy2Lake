# SQL Server T-SQL Migration Patterns (v3.5)

> **Last Updated**: 2026-02-01  
> **Purpose**: Translate SQL Server T-SQL code to modern cloud-native platforms

## SQL Dialect Translation

| SQL Server Feature | Databricks (PySpark) | Snowflake SQL |
|-------------------|---------------------|---------------|
| **`TOP N`** | `.limit(N)` | `LIMIT N` |
| **`IDENTITY` column** | Auto-increment via Delta | `AUTOINCREMENT` or `SEQ...NEXTVAL` |
| **`@@ROWCOUNT`** | `df.count()` | `SQLROWCOUNT` (deprecated, use RETURNING) |
| **`GETDATE()`** | `current_timestamp()` | `CURRENT_TIMESTAMP` |
| **`DATEADD()`** | `date_add()` or `expr()` | `DATEADD()` (same syntax!) |
| **`ISNULL(col, default)`** | `coalesce(col, default)` | `COALESCE(col, default)` or `NVL` |
| **`LEN(string)`** | `length(col)` | `LENGTH(string)` |
| **Window functions** | Same | Same (ANSI SQL compliant) |
| **CTEs** | Same | Same |
| **`MERGE`** | Delta `MERGE` | `MERGE` (same syntax) |
| **`TRY_CAST`** | `try_cast()` (Spark SQL) | `TRY_CAST()` |
| **`STRING_AGG`** | `collect_list()` + `concat_ws()` | `LISTAGG()` |
| **Temp tables (`#temp`)** | Global temp view or DataFrame | Transient/Temporary tables |
| **Table variables (`@table`)** | DataFrame variables | CTEs or temp tables |
| **`PIVOT`** | `.pivot()` or `CASE WHEN` | `PIVOT` (same syntax!) |
| **`UNPIVOT`** | `.unpivot()` or `stack()` | `UNPIVOT` |

---

## Stored Procedure Translation

### SQL Server Stored Procedure
```sql
CREATE PROCEDURE usp_UpdateCustomerSales
    @CustomerID INT,
    @SalesAmount DECIMAL(18,2),
    @TransactionDate DATE
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRANSACTION;
    BEGIN TRY
        -- Update customer record
        UPDATE Customers
        SET TotalSales = TotalSales + @SalesAmount,
            LastPurchaseDate = @TransactionDate
        WHERE CustomerID = @CustomerID;
        
        -- Insert into audit log
        INSERT INTO SalesAudit (CustomerID, Amount, TransactionDate)
        VALUES (@CustomerID, @SalesAmount, @TransactionDate);
        
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END
```

### Databricks Python Function
```python
from pyspark.sql.functions import col, lit
from delta.tables import DeltaTable

def update_customer_sales(customer_id: int, sales_amount: float, transaction_date: str):
    """
    Update customer sales total and log audit record.
    
    Args:
        customer_id: Customer ID
        sales_amount: Sales amount to add
        transaction_date: Transaction date (YYYY-MM-DD)
    """
    try:
        # Update customer record using MERGE
        customers = DeltaTable.forName(spark, "customers")
        
        update_df = spark.createDataFrame([
            (customer_id, sales_amount, transaction_date)
        ], ["customer_id", "sales_amount", "transaction_date"])
        
        customers.alias("t").merge(
            update_df.alias("s"),
            "t.customer_id = s.customer_id"
        ).whenMatchedUpdate(
            set={
                "total_sales": col("t.total_sales") + col("s.sales_amount"),
                "last_purchase_date": col("s.transaction_date")
            }
        ).execute()
        
        # Insert audit record
        audit_df = spark.createDataFrame([
            (customer_id, sales_amount, transaction_date)
        ], ["customer_id", "amount", "transaction_date"])
        
        audit_df.write.mode("append").saveAsTable("sales_audit")
        
    except Exception as e:
        print(f"Error updating customer sales: {e}")
        raise
```

### Snowflake Stored Procedure
```sql
CREATE OR REPLACE PROCEDURE update_customer_sales(
    customer_id INT,
    sales_amount DECIMAL(18,2),
    transaction_date DATE
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    -- Update customer record
    UPDATE customers
    SET total_sales = total_sales + sales_amount,
        last_purchase_date = transaction_date
    WHERE customer_id = :customer_id;
    
    -- Insert audit record
    INSERT INTO sales_audit (customer_id, amount, transaction_date)
    VALUES (:customer_id, :sales_amount, :transaction_date);
    
    RETURN 'Success';
EXCEPTION
    WHEN OTHER THEN
        RETURN 'Error: ' || SQLERRM;
END;
$$;

-- Execute
CALL update_customer_sales(123, 99.99, '2024-01-15');
```

---

## Common T-SQL Patterns

### 1. Cursor Pattern (Row-by-Row Processing)

#### SQL Server (Cursor)
```sql
DECLARE @CustomerID INT;
DECLARE customer_cursor CURSOR FOR
    SELECT CustomerID FROM Customers WHERE Status = 'Active';

OPEN customer_cursor;
FETCH NEXT FROM customer_cursor INTO @CustomerID;

WHILE @@FETCH_STATUS = 0
BEGIN
    -- Process each customer
    EXEC ProcessCustomer @CustomerID;
    FETCH NEXT FROM customer_cursor INTO @CustomerID;
END

CLOSE customer_cursor;
DEALLOCATE customer_cursor;
```

#### Modern Equivalent (Set-Based)
**Databricks/Snowflake**: Avoid cursors! Use set-based operations.

```python
# Databricks: Process all customers at once
active_customers = spark.read.table("customers").filter("status = 'Active'")

# Apply transformation to entire dataset
processed = active_customers.withColumn(
    "processed_result",
    process_customer_udf(col("customer_id"))  # User-defined function if needed
)

processed.write.mode("overwrite").saveAsTable("processed_customers")
```

```sql
-- Snowflake: Set-based processing
INSERT INTO processed_customers
SELECT 
    customer_id,
    process_customer(customer_id) AS processed_result  -- UDF if needed
FROM customers
WHERE status = 'Active';
```

### 2. Temporary Tables

#### SQL Server
```sql
-- Local temp table (session-scoped)
CREATE TABLE #TempCustomers (
    CustomerID INT,
    CustomerName VARCHAR(100)
);

INSERT INTO #TempCustomers
SELECT CustomerID, CustomerName
FROM Customers
WHERE Region = 'US';

SELECT * FROM #TempCustomers;
-- Auto-dropped at session end
```

#### Databricks
```python
# Create temporary view (session-scoped)
temp_df = spark.read.table("customers").filter("region = 'US'")
temp_df.createOrReplaceTempView("temp_customers")

# Use in SQL
spark.sql("SELECT * FROM temp_customers")

# Or use DataFrame directly
temp_df.show()
```

#### Snowflake
```sql
-- Temporary table (session-scoped, auto-dropped)
CREATE TEMPORARY TABLE temp_customers AS
SELECT customer_id, customer_name
FROM customers
WHERE region = 'US';

SELECT * FROM temp_customers;
```

### 3. Dynamic SQL

#### SQL Server
```sql
DECLARE @TableName VARCHAR(100) = 'Customers';
DECLARE @SQL NVARCHAR(MAX);

SET @SQL = 'SELECT * FROM ' + QUOTENAME(@TableName);
EXEC sp_executesql @SQL;
```

#### Databricks
```python
# Option 1: f-string (simple cases)
table_name = "customers"
df = spark.sql(f"SELECT * FROM {table_name}")

# Option 2: Parameters (safer for user input)
from pyspark.sql.functions import col
table_name = "customers"  # Validate against whitelist!
df = spark.table(table_name)
```

#### Snowflake
```sql
-- Use session variables
SET table_name = 'customers';
EXECUTE IMMEDIATE 'SELECT * FROM ' || $table_name;
```

### 4. Window Functions

#### SQL Server
```sql
SELECT 
    CustomerID,
    OrderDate,
    Amount,
    SUM(Amount) OVER (
        PARTITION BY CustomerID 
        ORDER BY OrderDate 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS RunningTotal,
    ROW_NUMBER() OVER (
        PARTITION BY CustomerID 
        ORDER BY OrderDate DESC
    ) AS RowNum
FROM Orders;
```

#### Databricks
```python
from pyspark.sql.window import Window
from pyspark.sql.functions import sum, row_number

window_spec = Window.partitionBy("customer_id").orderBy("order_date")
running_window = window_spec.rowsBetween(Window.unboundedPreceding, Window.currentRow)
row_num_window = Window.partitionBy("customer_id").orderBy(col("order_date").desc())

df = spark.read.table("orders").withColumn(
    "running_total",
    sum("amount").over(running_window)
).withColumn(
    "row_num",
    row_number().over(row_num_window)
)
```

#### Snowflake
```sql
-- Same syntax as SQL Server!
SELECT 
    customer_id,
    order_date,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id 
        ORDER BY order_date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id 
        ORDER BY order_date DESC
    ) AS row_num
FROM orders;
```

---

## Index Translation

### SQL Server Indexes
```sql
-- Clustered index (determines physical storage order)
CREATE CLUSTERED INDEX IX_Orders_OrderDate
ON Orders(OrderDate);

-- Non-clustered index (separate structure)
CREATE NONCLUSTERED INDEX IX_Orders_CustomerID
ON Orders(CustomerID)
INCLUDE (OrderDate, Amount);  -- Covering index
```

### Databricks Equivalent
Databricks doesn't have traditional indexes. Use:
- **Liquid Clustering** or **Z-ORDER** for physical data layout
- **Partitioning** for range queries

```python
# Liquid Clustering (replaces indexes)
CREATE TABLE orders
CLUSTER BY (customer_id, order_date)
AS SELECT * FROM source_orders

# Or Z-ORDER for read-heavy workloads
OPTIMIZE orders
ZORDER BY (customer_id, order_date)
```

### Snowflake Equivalent
Snowflake doesn't have traditional indexes. Use:
- **CLUSTER BY** for frequently filtered columns
- **Search Optimization Service** (for point lookups)

```sql
-- Clustering (similar to clustered index)
ALTER TABLE orders
CLUSTER BY (order_date, customer_id);

-- Search Optimization (for high-cardinality point lookups)
ALTER TABLE orders ADD SEARCH OPTIMIZATION ON EQUALITY(customer_id);
```

---

## Transaction Handling

### SQL Server
```sql
BEGIN TRANSACTION;
BEGIN TRY
    UPDATE Account SET Balance = Balance - 100 WHERE AccountID = 1;
    UPDATE Account SET Balance = Balance + 100 WHERE AccountID = 2;
    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    THROW;
END CATCH
```

### Databricks
Delta Lake supports ACID transactions automatically:
```python
# Transactions are implicit in Delta Lake operations
from delta.tables import DeltaTable

# Each MERGE is atomic
accounts = DeltaTable.forName(spark, "accounts")

# Debit
accounts.alias("t").merge(
    spark.createDataFrame([(1, -100)], ["account_id", "delta"]).alias("s"),
    "t.account_id = s.account_id"
).whenMatchedUpdate(
    set={"balance": col("t.balance") + col("s.delta")}
).execute()

# Credit (separate transaction, but Delta ensures consistency)
accounts.alias("t").merge(
    spark.createDataFrame([(2, 100)], ["account_id", "delta"]).alias("s"),
    "t.account_id = s.account_id"
).whenMatchedUpdate(
    set={"balance": col("t.balance") + col("s.delta")}
).execute()

# For multi-statement transactions, use Delta Lake Transactions API (DBR 12.0+)
```

### Snowflake
```sql
-- Multi-statement transactions
BEGIN TRANSACTION;

UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
UPDATE accounts SET balance = balance + 100 WHERE account_id = 2;

COMMIT;
-- Or ROLLBACK on error
```

---

## Error Handling

### SQL Server
```sql
BEGIN TRY
    -- Risky operation
    INSERT INTO Customers VALUES (...);
END TRY
BEGIN CATCH
    SELECT 
        ERROR_NUMBER() AS ErrorNumber,
        ERROR_MESSAGE() AS ErrorMessage;
END CATCH
```

### Databricks
```python
try:
    # Risky operation
    df.write.mode("append").saveAsTable("customers")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    # Log to error table
    error_df = spark.createDataFrame([
        (str(e), current_timestamp())
    ], ["error_message", "error_timestamp"])
    error_df.write.mode("append").saveAsTable("error_log")
    raise
```

### Snowflake
```sql
BEGIN
    INSERT INTO customers VALUES (...);
EXCEPTION
    WHEN OTHER THEN
        INSERT INTO error_log (error_message, error_timestamp)
        VALUES (SQLERRM, CURRENT_TIMESTAMP);
        RETURN SQLERRM;
END;
```

---

## Migration Checklist

When translating SQL Server T-SQL:
- [ ] Replace cursors with set-based operations
- [ ] Convert temp tables to temp views (Databricks) or transient tables (Snowflake)
- [ ] Translate stored procedures to Python functions (Databricks) or Snowflake procedures
- [ ] Replace indexes with clustering/optimization
- [ ] Convert TRY/CATCH to try/except (Databricks) or EXCEPTION blocks (Snowflake)
- [ ] Replace proprietary functions (GETDATE, ISNULL) with standards (CURRENT_TIMESTAMP, COALESCE)
- [ ] Ensure MERGE operations for idempotency
- [ ] Test window functions (syntax may differ slightly in PySpark)

---

## Performance Best Practices

### Avoid These SQL Server Habits:
1. **❌ Row-by-row processing (cursors)** → Use set-based operations
2. **❌ Excessive temp tables** → Use CTEs or DataFrames
3. **❌ `SELECT *`** → Specify columns explicitly
4. **❌ Functions in WHERE clauses** → Use SARGable predicates
5. **❌ Missing indexes** → Use clustering/partitioning in modern platforms

### Modern Equivalent Best Practices:
1. **✅ Set-based operations** (entire DataFrames/tables at once)
2. **✅ Clustering/partitioning** instead of indexes
3. **✅ MERGE for idempotency** (not INSERT/UPDATE separately)
4. **✅ Early filtering** (push down predicates)
5. **✅ Broadcast small tables** (Databricks) or let optimizer decide (Snowflake)
