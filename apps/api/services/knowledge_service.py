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
                "category": "PATHS",
                "key": "target_stack",
                "value": "pyspark"
            },
            {
                "project_id": project_id,
                "category": "PRIVACY",
                "key": "masking_method",
                "value": "sha256"
            },
            {
                "project_id": project_id,
                "category": "PATHS",
                "key": "gcp_project_id",
                "value": "my-gcp-project"
            },
            {
                "project_id": project_id,
                "category": "PATHS",
                "key": "aws_s3_bucket",
                "value": "my-aws-bucket"
            },
            {
                "project_id": project_id,
                "category": "PATHS",
                "key": "aws_redshift_host",
                "value": "redshift-cluster-1.abc.us-east-1.redshift.amazonaws.com"
            }
        ]
