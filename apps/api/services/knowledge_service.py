from typing import Dict, Any, List, Optional
try:
    from apps.api.utils.logger import logger
except ImportError:
    from ..utils.logger import logger

class KnowledgeService:
    @staticmethod
    def flatten_knowledge(registry: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Converts a list of registry entries into a flat dictionary for LLM context."""
        flattened = {}
        for entry in registry:
            category = entry.get('category', 'GENERAL').lower()
            key = entry.get('key')
            value = entry.get('value')
            
            if category not in flattened:
                flattened[category] = {}
            
            flattened[category][key] = value
        return flattened

    @staticmethod
    def get_default_registry_entries(project_id: str) -> List[Dict[str, Any]]:
        """Returns the base set of design standards for a new project."""
        return [
            {
                "project_id": project_id,
                "category": "NAMING",
                "key": "silver_prefix",
                "value": "stg_"
            },
            {
                "project_id": project_id,
                "category": "NAMING",
                "key": "gold_prefix",
                "value": "dim_"
            },
            {
                "project_id": project_id,
                "category": "PATHS",
                "key": "root_path",
                "value": "abfss://lakehouse@storage.dfs.core.windows.net/"
            },
            {
                "project_id": project_id,
                "category": "PRIVACY",
                "key": "masking_method",
                "value": "sha256"
            }
        ]
