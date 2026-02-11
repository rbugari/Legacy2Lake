import snowflake.snowpark as snowpark
from snowflake.snowpark import Session
import snowflake.snowpark.functions as F
import logging

# LOGGING SETUP
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(session: Session) -> str:
    """
    Bronze layer ingestion function for RAW_DATA.BRONZE_CUSTOMERS.
    Reads CSV from S3 stage and loads to Snowflake Bronze table with audit columns.
    Args:
        session (Session): Snowpark session
    Returns:
        str: Status message
    """
    SCHEMA_BRONZE = "RAW_DATA"
    SOURCE_SYSTEM = "AMAZON_S3"
    TABLE_NAME = "BRONZE_CUSTOMERS"
    SOURCE_FILE = "customers.csv"
    SOURCE_STAGE_PATH = "@CUSTOMER_STAGE/customers.csv"

    try:
        logger.info(f"Starting Bronze ingestion for {SCHEMA_BRONZE}.{TABLE_NAME}")

        # READ SOURCE DATA FROM STAGE
        df_source = session.read \
            .option("FIELD_DELIMITER", ",") \
            .option("SKIP_HEADER", 1) \
            .option("FIELD_OPTIONALLY_ENCLOSED_BY", '"') \
            .csv(SOURCE_STAGE_PATH)

        logger.info(f"Read {df_source.count()} records from source CSV {SOURCE_STAGE_PATH}")

        # ADD MANDATORY AUDIT/METADATA COLUMNS
        df_bronze = df_source \
            .with_column("_INGESTION_TIMESTAMP", F.current_timestamp()) \
            .with_column("_INGESTION_DATE", F.current_date()) \
            .with_column("_SOURCE_FILE", F.lit(SOURCE_FILE)) \
            .with_column("_SOURCE_SYSTEM", F.lit(SOURCE_SYSTEM))

        # DATA VALIDATION
        record_count = df_bronze.count()
        if record_count == 0:
            raise ValueError(f"No records to ingest for {TABLE_NAME}")
        logger.info(f"Validated: {record_count} records ready for ingestion")

        # LOAD TO BRONZE TABLE
        target_table = f"{SCHEMA_BRONZE}.{TABLE_NAME}"
        df_bronze.write \
            .mode("append") \
            .save_as_table(target_table)

        success_msg = f"✅ Successfully ingested {record_count} records to {target_table}"
        logger.info(success_msg)
        return success_msg

    except Exception as e:
        error_msg = f"❌ Bronze ingestion failed for {TABLE_NAME}: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    finally:
        logger.info("Bronze ingestion process completed")

if __name__ == "__main__":
    session = snowpark.Session.builder.getOrCreate()
    result = main(session)
    print(result)
