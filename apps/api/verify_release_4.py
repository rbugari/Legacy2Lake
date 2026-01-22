from services.extraction.cartridges.sql_server_cartridge import SqlServerCartridge
from services.extraction.cartridges.mysql_cartridge import MysqlCartridge
from services.extraction.cartridges.oracle_cartridge import OracleCartridge
from services.generation.cartridges.spark_destination import SparkDestination
from services.generation.cartridges.snowflake_destination import SnowflakeDestination

def test_cartridges():
    print("--- Verifying Release 4.0 Cartridges ---")
    
    # Sources
    sources = [
        ("SQL Server", SqlServerCartridge({'type': 'sqlserver'})),
        ("MySQL", MysqlCartridge({'type': 'mysql'})),
        ("Oracle", OracleCartridge({'type': 'oracle'}))
    ]
    
    for name, instance in sources:
        try:
            instance.scan_catalog()
            print(f"[SUCCESS] {name} initialized and interface check passed.")
        except Exception as e:
            print(f"[ERROR] {name} failed: {e}")

    # Destinations
    destinations = [
        ("Spark", SparkDestination({'type': 'spark'})),
        ("Snowflake", SnowflakeDestination({'type': 'snowflake'}))
    ]
    
    for name, instance in destinations:
        try:
            instance.generate_ddl({'name': 'test'})
            print(f"[SUCCESS] {name} initialized and interface check passed.")
        except Exception as e:
            print(f"[ERROR] {name} failed: {e}")

if __name__ == "__main__":
    test_cartridges()
