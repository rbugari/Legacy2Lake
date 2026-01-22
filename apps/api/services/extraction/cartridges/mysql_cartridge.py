from .base_cartridge import SourceCartridge
from typing import List, Dict, Any

class MysqlCartridge(SourceCartridge):
    """
    Extractor for MySQL / MariaDB (5.7, 8.0, Aurora).
    """

    def test_connection(self) -> bool:
        print(f"[{self.source_type}] Testing connection to {self.config.get('host', 'localhost')} on port {self.config.get('port', 3306)}...")
        # Mock connection success
        return True

    def scan_catalog(self) -> List[Dict[str, Any]]:
        # In real world: SELECT table_name FROM information_schema.tables WHERE table_schema = ...
        return [
            {"name": "users", "type": "TABLE", "metadata": {"engine": "InnoDB", "rows": 2500}},
            {"name": "products", "type": "TABLE", "metadata": {"engine": "InnoDB", "rows": 150}},
            {"name": "orders_view", "type": "VIEW", "metadata": {}}
        ]

    def extract_ddl(self, asset_name: str) -> str:
        return f"CREATE TABLE `{asset_name}` (id INT AUTO_INCREMENT PRIMARY KEY, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"

    def sample_data(self, asset_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        return [{"id": i, "status": "active"} for i in range(limit)]
