from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
try:
    from services.persistence_service import SupabasePersistence
except ImportError:
    from apps.api.services.persistence_service import SupabasePersistence

class Cartridge(ABC):
    """
    Abstract Base Class for generation strategies (PySpark, dbt, SQL).
    Defines the contract for generating Medallion Architecture code.
    
    Sprint 9 Enhancement:
        Added tenant_id parameter to support schema-aware generation.
    """

    def __init__(self, project_id: str, design_registry: Dict[str, Any], tenant_id: str = None):
        self.project_id = project_id
        self.registry = design_registry
        self.tenant_id = tenant_id  # Sprint 9: For schema-aware services

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

    def generate_semantic_model(self, table_metadata: Dict[str, Any]) -> str:
        """
        Optional: Generates semantic layer code (e.g., LookML views, dbt metrics).
        Defaults to returning an empty string if the cartridge doesn't support it.
        """
        return ""

    def generate_orchestration(self, tables_metadata: List[Dict[str, Any]]) -> str:
        """
        Optional: Generates orchestration code (e.g., Airflow DAGs, Fabric Pipelines).
        Defaults to returning an empty string.
        """
        return ""

    def get_rules(self, node_data: Dict[str, Any]) -> str:
        """
        Returns specific architectural rules for the LLM based on the node context.
        Prioritizes rules injected from utm_system_catalog via factory.
        """
        # 1. Check for DB-injected rules (from Factory)
        tech_config = self.registry.get('tech_config', {}).get('compliance_rules', {})
        base_rules = tech_config.get('base', "")
        
        if base_rules:
            source_tech = str(node_data.get("source_tech", "mssql")).lower()
            overrides = tech_config.get('source_overrides', {})
            
            # Find matching source tech overrides
            override_rules = ""
            for key, rules in overrides.items():
                if key in source_tech:
                    override_rules += f"\n{rules}"
            
            return f"{base_rules}\n{override_rules}"
            
        return ""

    def _validate_and_normalize_pk(self, pk_columns) -> List[str]:
        """
        Ensures pk_columns is always a valid non-empty list.
        
        Args:
            pk_columns: Primary key columns (list, str, or None)
            
        Returns:
            List of PK column names (default ["id"] if invalid)
        """
        if not pk_columns:
            return ["id"]  # Safe default
        if isinstance(pk_columns, str):
            return [pk_columns]
        if isinstance(pk_columns, list) and len(pk_columns) > 0:
            return pk_columns
        return ["id"]  # Fallback for any other invalid type
