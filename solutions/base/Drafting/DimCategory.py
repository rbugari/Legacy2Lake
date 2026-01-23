import logging
from pyspark.sql import functions as F
from pyspark.sql import SparkSession
from delta.tables import DeltaTable

def execute_task(spark, context):
    """
    Principal Engineer Transpilation for FULL_OVERWRITE Dimensional Loads
    Applies strict casting, idempotency, and medallion architecture standards.
    """
    # PARAMETERS & CONFIG
    try:
        # Table mapping (prefix enforced)
        table_map = {
            'DimCategory': 'dim_category',
            'DimCustomer': 'dim_customer',
            'DimEmployee': 'dim_employee',
            'DimProduct': 'dim_product',
            'DimShipper': 'dim_shipper',
            'DimSupplier': 'dim_supplier'
        }
        # Source queries (from context)
        source_queries = {
            'dim_category': "SELECT categoryid, categoryname FROM Production.Categories",
            'dim_customer': "SELECT custid, contactname, city, country, address, phone, postalcode FROM Sales.Customers",
            'dim_employee': "SELECT empid, (firstname + ' ' + lastname) as fullname, title, city, country, address, phone FROM HR.Employees",
            'dim_product': "SELECT * FROM Production.Products",
            'dim_shipper': "SELECT * FROM Sales.Shippers",
            'dim_supplier': "SELECT supplierid, companyname, address, postalcode, phone, city, country FROM Production.Suppliers"
        }
        # Target DDLs (example, must be replaced with actual DDLs in real use)
        target_ddls = {
            'dim_category': [
                {'name': 'categoryid', 'type': 'LongType'},
                {'name': 'categoryname', 'type': 'StringType'}
            ],
            'dim_customer': [
                {'name': 'custid', 'type': 'LongType'},
                {'name': 'contactname', 'type': 'StringType'},
                {'name': 'city', 'type': 'StringType'},
                {'name': 'country', 'type': 'StringType'},
                {'name': 'address', 'type': 'StringType'},
                {'name': 'phone', 'type': 'StringType'},
                {'name': 'postalcode', 'type': 'StringType'}
            ],
            'dim_employee': [
                {'name': 'empid', 'type': 'LongType'},
                {'name': 'fullname', 'type': 'StringType'},
                {'name': 'title', 'type': 'StringType'},
                {'name': 'city', 'type': 'StringType'},
                {'name': 'country', 'type': 'StringType'},
                {'name': 'address', 'type': 'StringType'},
                {'name': 'phone', 'type': 'StringType'}
            ],
            'dim_product': [
                # Example: must be replaced with actual DDL
                {'name': 'productid', 'type': 'LongType'},
                {'name': 'productname', 'type': 'StringType'},
                {'name': 'supplierid', 'type': 'LongType'},
                {'name': 'categoryid', 'type': 'LongType'},
                {'name': 'unitprice', 'type': 'DecimalType(18,2)'},
                {'name': 'discontinued', 'type': 'BooleanType'}
            ],
            'dim_shipper': [
                {'name': 'shipperid', 'type': 'LongType'},
                {'name': 'companyname', 'type': 'StringType'},
                {'name': 'phone', 'type': 'StringType'}
            ],
            'dim_supplier': [
                {'name': 'supplierid', 'type': 'LongType'},
                {'name': 'companyname', 'type': 'StringType'},
                {'name': 'address', 'type': 'StringType'},
                {'name': 'postalcode', 'type': 'StringType'},
                {'name': 'phone', 'type': 'StringType'},
                {'name': 'city', 'type': 'StringType'},
                {'name': 'country', 'type': 'StringType'}
            ]
        }
        # Loop through each dimension table
        for logical_name, target_table in table_map.items():
            # 2. EXTRACT
            df_source = spark.sql(source_queries[target_table])
            # 3. TRANSFORM (No lookups, so direct mapping)
            # 3.1 TYPE SAFETY LOOP
            for field in target_ddls[target_table]:
                col_name = field['name']
                col_type = field['type']
                if col_type.startswith('DecimalType'):
                    # Extract precision and scale
                    import re
                    m = re.match(r'DecimalType\((\d+),(\d+)\)', col_type)
                    if m:
                        precision, scale = int(m.group(1)), int(m.group(2))
                        df_source = df_source.withColumn(col_name, F.col(col_name).cast(f"decimal({precision},{scale})"))
                elif col_type == 'LongType':
                    df_source = df_source.withColumn(col_name, F.col(col_name).cast('long'))
                elif col_type == 'BooleanType':
                    df_source = df_source.withColumn(col_name, F.col(col_name).cast('boolean'))
                else:
                    df_source = df_source.withColumn(col_name, F.col(col_name).cast('string'))
            # 4. LOAD (FULL_OVERWRITE for dimensions)
            df_source.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(target_table)
            # OPTIMIZATION HINTS
            # spark.sql(f"OPTIMIZE {target_table}")
            # spark.sql(f"VACUUM {target_table} RETAIN 168 HOURS")
        return True
    except Exception as e:
        logging.error(f"Error in execute_task: {str(e)}")
        raise
