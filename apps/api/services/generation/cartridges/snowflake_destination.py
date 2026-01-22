from .base_destination import DestinationCartridge
from typing import List, Dict, Any

class SnowflakeDestination(DestinationCartridge):
    """
    Generator for Snowflake (Snowpark Python / SQL).
    """

    def generate_ddl(self, table_metadata: Dict[str, Any]) -> str:
        table_name = table_metadata.get("name", "UNTITLED")
        return f"CREATE TABLE {table_name.upper()} (ID NUMBER, DATA VARIANT);"

    def generate_code(self, source_asset: Dict[str, Any], transformation_logic: str) -> str:
        """
        Generates Snowpark code.
        """
        source_name = source_asset.get("name", "SOURCE_TABLE")
        
        return f"""
import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import *

def main(session: snowpark.Session):
    # Read Source
    df = session.table("{source_name}")
    
    # Transformation
    # {transformation_logic}
    
    # Write to Table
    df.write.mode("overwrite").save_as_table("TARGET_{source_name}")
    return "Done"
"""

    def get_supported_types(self) -> Dict[str, str]:
        return {
            "INTEGER": "NUMBER",
            "VARCHAR": "VARCHAR",
            "DATE": "DATE",
            "TIMESTAMP": "TIMESTAMP_NTZ"
        }
