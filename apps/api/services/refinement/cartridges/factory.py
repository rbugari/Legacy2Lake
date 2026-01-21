from typing import Dict, Any, Type
from .base_cartridge import Cartridge
from .pyspark_cartridge import PySparkCartridge

class CartridgeFactory:
    """
    Factory to create the appropriate refined cartridge.
    """
    
    @staticmethod
    def get_cartridge(project_id: str, registry: Dict[str, Any]) -> Cartridge:
        """
        Determines the correct cartridge based on Design Registry settings.
        Defaults to PySparkCartridge if not specified.
        """
        # Feature Flag: Check registry for 'target_stack'
        target = registry.get("paths", {}).get("target_stack", "pyspark")
        
        if target == "dbt":
            # Lazy import to avoid circular dependencies or import errors if not ready
            from .dbt_cartridge import DbtCartridge
            return DbtCartridge(project_id, registry)
            
        elif target == "sql":
            # Placeholder for Pure SQL
            return PySparkCartridge(project_id, registry)
            
        else:
            return PySparkCartridge(project_id, registry)
