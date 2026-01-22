from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os

class SourceCartridge(ABC):
    """
    Abstract Base Class for all Source Extractors (Extractors).
    Release 4.0: universal_connector
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with source-specific config (e.g. connection string, version).
        """
        self.config = config
        self.source_type = config.get("type", "generic")
        self.version = config.get("version", "latest")

    @abstractmethod
    def test_connection(self) -> bool:
        """Verify connectivity to the source."""
        pass

    @abstractmethod
    def scan_catalog(self) -> List[Dict[str, Any]]:
        """
        Return a list of assets (tables, views, stored procs).
        Format: [{'name': 'dbo.Users', 'type': 'TABLE', 'metadata': {...}}]
        """
        pass

    @abstractmethod
    def extract_ddl(self, asset_name: str) -> str:
        """
        Return the raw DDL or Code for a specific asset.
        """
        pass

    @abstractmethod
    def sample_data(self, asset_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Return sample rows for context injection (optional).
        """
        pass
