from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class DestinationCartridge(ABC):
    """
    Abstract Base Class for all Destination Generators (Generators).
    Controls how the target code is structured and formatted.
    Release 4.0: universal_connector
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with destination-specific config (e.g. Spark version, cloud provider).
        """
        self.config = config
        self.target_type = config.get("type", "generic")
        self.dialect = config.get("dialect", "ansi")

    @abstractmethod
    def generate_ddl(self, table_metadata: Dict[str, Any]) -> str:
        """
        Convert internal metadata schema to target DDL (e.g. CREATE TABLE delta...).
        """
        pass

    @abstractmethod
    def generate_code(self, source_asset: Dict[str, Any], transformation_logic: str) -> str:
        """
        Generate the actual pipeline code (PySpark, Snowpark, PL/SQL).
        """
        pass

    @abstractmethod
    def get_supported_types(self) -> Dict[str, str]:
        """
        Return mapping of generic types to target types (e.g. INTEGER -> LONG).
        """
        pass
