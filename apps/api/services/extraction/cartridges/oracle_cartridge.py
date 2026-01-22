from .base_cartridge import SourceCartridge
from typing import List, Dict, Any

class OracleCartridge(SourceCartridge):
    """
    Extractor for Oracle Database (11g, 12c, 19c, Autonomous).
    """

    def test_connection(self) -> bool:
        print(f"[{self.source_type}] Testing connection to {self.config.get('tns', 'ORCL')}...")
        return True

    def scan_catalog(self) -> List[Dict[str, Any]]:
        # In real world: SELECT table_name FROM all_tables WHERE owner = ...
        return [
            {"name": "HR.EMPLOYEES", "type": "TABLE", "metadata": {"tablespace": "USERS"}},
            {"name": "HR.DEPARTMENTS", "type": "TABLE", "metadata": {"tablespace": "USERS"}},
            {"name": "HR.EMP_DETAILS_VIEW", "type": "VIEW", "metadata": {}}
        ]

    def extract_ddl(self, asset_name: str) -> str:
        return f"CREATE TABLE {asset_name} (ID NUMBER(10) PRIMARY KEY, NAME VARCHAR2(50));"

    def sample_data(self, asset_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        return [{"ID": i, "NAME": f"EMP_{i}"} for i in range(limit)]
