# L2L MODERNIZATION TRACE
# Source: Unknown Asset 'None'
# Component: None
# Logic: Transpiled from Unknown
# Refactoring: FULL_OVERWRITE (static partition, not overwrite mode)
# Generated At: 2024-06-09T00:00:00Z

def execute_task(spark, context):
    """
    Principal Engineer Transpilation
    This function performs a FULL_OVERWRITE load for all dimension tables listed in the project set overview.
    Each dimension is loaded using a high-fidelity, idempotent MERGE INTO pattern, with strict type casting.
    """
    import logging
    from pyspark.sql import functions as F
    from delta.tables import DeltaTable
    from datetime import datetime

    # 1. PARAMETERS & CONFIG
    # Table mapping: source query -> target table
    table_configs = [
        {
            "name": "dim_category",
            "source_query": "SELECT categoryid, categoryname FROM Production.Categories",
            "target_table": "dim_category",
            "business_keys": ["categoryid"],
            "ddl": [
                ("categoryid", "Long"),
                ("categoryname", "String")
            ]
        },
        {
            "name": "dim_customer",
            "source_query": "SELECT custid, contactname, city, country, address, phone, postalcode FROM Sales.Customers",
            "target_table": "dim_customer",
            "business_keys": ["custid"],
            "ddl": [
                ("custid", "Long"),
                ("contactname", "String"),
                ("city", "String"),
                ("country", "String"),
                ("address", "String"),
                ("phone", "String"),
                ("postalcode", "String")
            ]
        },
        {
            "name": "dim_employee",
            "source_query": "SELECT empid, (firstname || ' ' || lastname) as fullname, title, city, country, address, phone FROM HR.Employees",
            "target_table": "dim_employee",
            "business_keys": ["empid"],
            "ddl": [
                ("empid", "Long"),
                ("fullname", "String"),
                ("title", "String"),
                ("city", "String"),
                ("country", "String"),
                ("address", "String"),
                ("phone", "String")
            ]
        },
        {
            "name": "dim_product",
            "source_query": "SELECT * FROM Production.Products",
            "target_table": "dim_product",
            "business_keys": ["productid"],
            "ddl": None  # To be inferred from target schema
        },
        {
            "name": "dim_shipper",
            "source_query": "SELECT * FROM Sales.Shippers",
            "target_table": "dim_shipper",
            "business_keys": ["shipperid"],
            "ddl": None  # To be inferred from target schema
        },
        {
            "name": "dim_supplier",
            "source_query": "SELECT supplierid, companyname, address, postalcode, phone, city, country FROM Production.Suppliers",
            "target_table": "dim_supplier",
            "business_keys": ["supplierid"],
            "ddl": [
                ("supplierid", "Long"),
                ("companyname", "String"),
                ("address", "String"),
                ("postalcode", "String"),
                ("phone", "String"),
                ("city", "String"),
                ("country", "String")
            ]
        }
    ]

    # 2. PROCESS EACH DIMENSION
    for cfg in table_configs:
        try:
            logging.info(f"Processing {cfg['name']} ...")

            # 2.1 EXTRACT
            df_src = spark.sql(cfg["source_query"])

            # 2.2 TRANSFORM (No lookups, no PII masking required)
            # For dim_employee, ensure fullname is constructed
            if cfg["name"] == "dim_employee":
                df_src = df_src.withColumn(
                    "fullname",
                    F.concat_ws(" ", F.col("firstname"), F.col("lastname"))
                )

            # 2.3 TYPE SAFETY LOOP
            if cfg["ddl"] is not None:
                for col_name, col_type in cfg["ddl"]:
                    df_src = df_src.withColumn(col_name, F.col(col_name).cast(col_type))
            else:
                # Infer from target table schema
                target_schema = spark.table(cfg["target_table"]).schema
                for field in target_schema:
                    df_src = df_src.withColumn(field.name, F.col(field.name).cast(field.dataType))

            # 2.4 LOAD (MERGE INTO)
            # FULL_OVERWRITE: static partition delete + merge
            target_table = cfg["target_table"]
            business_keys = cfg["business_keys"]
            delta_target = DeltaTable.forName(spark, target_table)

            # Delete all rows (static partition delete)
            delta_target.delete()

            # Prepare merge condition
            merge_cond = " AND ".join([f"target.{k} = source.{k}" for k in business_keys])

            # Merge (insert all rows)
            (
                delta_target.alias("target")
                .merge(
                    df_src.alias("source"),
                    merge_cond
                )
                .whenNotMatchedInsertAll()
                .execute()
            )

            # 2.5 OPTIMIZATION HINTS
            # spark.sql(f"OPTIMIZE {target_table}")
            # spark.sql(f"VACUUM {target_table} RETAIN 168 HOURS")

            logging.info(f"{cfg['name']} loaded successfully.")
        except Exception as e:
            logging.error(f"Error processing {cfg['name']}: {str(e)}")
            raise

    return True
