from abc import ABC, abstractmethod
from typing import Dict, Any, List

class Cartridge(ABC):
    """
    Abstract Base Class for generation strategies (PySpark, dbt, SQL).
    Defines the contract for generating Medallion Architecture code.
    """

    def __init__(self, project_id: str, design_registry: Dict[str, Any]):
        self.project_id = project_id
        self.registry = design_registry

    @abstractmethod
    def generate_bronze(self, table_metadata: Dict[str, Any]) -> str:
        """Generates the Raw/Ingestion layer code."""
        pass

    @abstractmethod
    def generate_silver(self, table_metadata: Dict[str, Any]) -> str:
        """Generates the Cleaning/Standardization layer code."""
        pass

    @abstractmethod
    def generate_gold(self, table_metadata: Dict[str, Any]) -> str:
        """Generates the Curated/Business layer code."""
        pass

    @abstractmethod
    def generate_scaffolding(self) -> Dict[str, str]:
        """
        Generates project-level scaffolding files (e.g., config.py, dbt_project.yml).
        Returns a dictionary of {filename: content}.
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Returns the file extension for generated scripts (e.g., .py, .sql)."""
        pass
