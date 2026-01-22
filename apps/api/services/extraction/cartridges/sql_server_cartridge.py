from .base_cartridge import SourceCartridge
from typing import List, Dict, Any

class SqlServerCartridge(SourceCartridge):
    """
    Extractor for Microsoft SQL Server (2012, 2016, 2019, Azure).
    """

    def test_connection(self) -> bool:
        # Placeholder for real ODBC/JDBC connection check
        print(f"[{self.source_type}] Testing connection to {self.config.get('host', 'localhost')}...")
        return True

    def scan_catalog(self) -> List[Dict[str, Any]]:
        # In a real scenario, this queries information_schema
        # For prototype, we might listing files if source is 'offline_dump'
        if self.config.get("mode") == "offline_dump":
            return self._scan_files()
        
        return [
            {"name": "dbo.Customers", "type": "TABLE", "metadata": {"rows": 1000}},
            {"name": "dbo.Orders", "type": "TABLE", "metadata": {"rows": 50000}},
            {"name": "sales.usp_CalculateTotals", "type": "PROCEDURE", "metadata": {"params": 2}}
        ]

    def extract_ddl(self, asset_name: str) -> str:
        # Placeholder DDL generation
        return f"CREATE TABLE {asset_name} (ID INT PRIMARY KEY, CheckSum VARCHAR(100));"

    def sample_data(self, asset_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        return [{"ID": i, "Val": f"Data_{i}"} for i in range(limit)]

    def _scan_files(self):
        # Logic to scan .sql files from a path
        path = self.config.get("path", ".")
        assets = []
        # Mock logic
        assets.append({"name": "mock_from_file.sql", "type": "FILE"})
        return assets
