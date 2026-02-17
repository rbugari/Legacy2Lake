"""
Parameter Extractor Service - Sprint 9
=======================================

Purpose:
    Extracts parameters from utm_design_registry for dynamic code generation.
    Eliminates hardcoded values by reading from project configuration.

Features:
    - Extract medallion architecture paths (bronze_path, silver_path, gold_path)
    - Extract schema names (bronze_schema, silver_schema, gold_schema)
    - Extract naming conventions (prefixes, suffixes)
    - Extract target technology stack
    - Extract source connection details
    - Resolve table name mappings

Usage:
    extractor = ParameterExtractor(tenant_id, project_id)
    
    params = await extractor.extract_parameters()
    
    # Access parameters
    bronze_path = params['paths']['bronze_path']
    target_tech = params['target']['tech_stack']
    table_mapping = params['table_mappings']['Customers']  # 'dim_customers'

Integration:
    - Used by Agent C for parameter injection
    - Used by Template Engine for code generation
    - Used by Cartridges for schema-aware generation

Author: Legacy2Lake Engineering
Date: 2026-02-11 (Sprint 9)
Version: v1.0
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import json

try:
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.services.knowledge_service import KnowledgeService
    from apps.api.utils.logger import logger
except ImportError:
    from services.persistence_service import SupabasePersistence
    from services.knowledge_service import KnowledgeService
    from utils.logger import logger


# ================================================================
# DATA CLASSES
# ================================================================

@dataclass
class ProjectParameters:
    """Complete project parameters extracted from design registry"""
    project_id: str
    
    # Paths
    bronze_path: str = "/mnt/datalake/bronze"
    silver_path: str = "/mnt/datalake/silver"
    gold_path: str = "/mnt/datalake/gold"
    
    # Schemas
    bronze_schema: str = "bronze_raw"
    silver_schema: str = "silver_curated"
    gold_schema: str = "gold_business"
    
    # Naming conventions
    bronze_prefix: str = "raw_"
    silver_prefix: str = "stg_"
    gold_prefix: str = ""
    
    bronze_suffix: str = ""
    silver_suffix: str = ""
    gold_suffix: str = ""
    
    # Target technology
    target_tech: str = "pyspark"
    target_dialect: str = "delta"
    
    # Source technology
    source_tech: str = "mssql"
    source_dialect: str = "tsql"
    
    # Catalog/Database
    catalog_name: str = "main"
    database_name: Optional[str] = None
    
    # Table mappings
    table_mappings: Dict[str, str] = field(default_factory=dict)  # {'Source': 'target_name'}
    
    # Metadata
    raw_registry: Dict[str, Any] = field(default_factory=dict)


# ================================================================
# PARAMETER EXTRACTOR SERVICE
# ================================================================

class ParameterExtractor:
    """
    Service for extracting parameters from utm_design_registry.
    Provides configuration for zero-hardcode code generation.
    """
    
    # Default values (fallback if registry is empty)
    DEFAULTS = {
        'paths': {
            'bronze_path': '/mnt/datalake/bronze',
            'silver_path': '/mnt/datalake/silver',
            'gold_path': '/mnt/datalake/gold'
        },
        'naming': {
            'bronze_schema': 'bronze_raw',
            'silver_schema': 'silver_curated',
            'gold_schema': 'gold_business',
            'bronze_prefix': 'raw_',
            'silver_prefix': 'stg_',
            'gold_prefix': ''
        },
        'target': {
            'tech_stack': 'pyspark',
            'dialect': 'delta'
        },
        'source': {
            'tech_stack': 'mssql',
            'dialect': 'tsql'
        }
    }
    
    def __init__(self, tenant_id: Optional[str] = None, project_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.project_id = project_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=None)
        self._cache: Optional[ProjectParameters] = None
    
    
    async def extract_parameters(self, project_id: Optional[str] = None, use_cache: bool = True) -> ProjectParameters:
        """
        Extract parameters from design registry.
        
        Args:
            project_id: Project ID (defaults to self.project_id)
            use_cache: If True, use cached parameters if available
        
        Returns:
            ProjectParameters with all extracted values
        """
        project_id = project_id or self.project_id
        
        if not project_id:
            raise ValueError("project_id required")
        
        # Check cache
        if use_cache and self._cache and self._cache.project_id == project_id:
            logger.info(f"[ParameterExtractor] Using cached parameters for project_id={project_id}", "ParameterExtractor")
            return self._cache
        
        logger.info(f"[ParameterExtractor] Extracting parameters for project_id={project_id}", "ParameterExtractor")
        
        # Get design registry
        registry_raw = await self.db.get_design_registry(project_id)
        
        if not registry_raw:
            logger.warning(f"[ParameterExtractor] Design registry empty, using defaults", "ParameterExtractor")
            registry = {}
        else:
            # Flatten registry
            registry = KnowledgeService.flatten_knowledge(registry_raw)
        
        # Extract parameters
        params = self._parse_registry(project_id, registry, registry_raw)
        
        # Cache
        self._cache = params
        
        logger.info(
            f"[ParameterExtractor] Parameters extracted: "
            f"target_tech={params.target_tech}, "
            f"bronze_schema={params.bronze_schema}, "
            f"{len(params.table_mappings)} table mappings",
            "ParameterExtractor"
        )
        
        return params
    
    
    def _parse_registry(
        self,
        project_id: str,
        registry: Dict[str, Any],
        registry_raw: List[Dict[str, Any]]
    ) -> ProjectParameters:
        """
        Parse design registry into ProjectParameters.
        
        Registry structure:
        {
            "paths": {
                "bronze_path": "/mnt/datalake/bronze",
                "silver_path": "/mnt/datalake/silver",
                "gold_path": "/mnt/datalake/gold",
                "target_stack": "pyspark"
            },
            "naming": {
                "bronze_schema": "bronze_raw",
                "silver_schema": "silver_curated",
                "gold_schema": "gold_business",
                "bronze_prefix": "raw_",
                "silver_prefix": "stg_",
                "gold_prefix": ""
            },
            "source": {
                "tech_stack": "mssql",
                "dialect": "tsql"
            }
        }
        """
        params = ProjectParameters(project_id=project_id)
        
        # Extract paths
        paths = registry.get('paths', self.DEFAULTS['paths'])
        params.bronze_path = paths.get('bronze_path', self.DEFAULTS['paths']['bronze_path'])
        params.silver_path = paths.get('silver_path', self.DEFAULTS['paths']['silver_path'])
        params.gold_path = paths.get('gold_path', self.DEFAULTS['paths']['gold_path'])
        
        # Extract schemas
        naming = registry.get('naming', self.DEFAULTS['naming'])
        params.bronze_schema = naming.get('bronze_schema', self.DEFAULTS['naming']['bronze_schema'])
        params.silver_schema = naming.get('silver_schema', self.DEFAULTS['naming']['silver_schema'])
        params.gold_schema = naming.get('gold_schema', self.DEFAULTS['naming']['gold_schema'])
        
        # Extract prefixes/suffixes
        params.bronze_prefix = naming.get('bronze_prefix', self.DEFAULTS['naming']['bronze_prefix'])
        params.silver_prefix = naming.get('silver_prefix', self.DEFAULTS['naming']['silver_prefix'])
        params.gold_prefix = naming.get('gold_prefix', self.DEFAULTS['naming']['gold_prefix'])
        
        params.bronze_suffix = naming.get('bronze_suffix', '')
        params.silver_suffix = naming.get('silver_suffix', '')
        params.gold_suffix = naming.get('gold_suffix', '')
        
        # Extract target technology
        target = registry.get('target', self.DEFAULTS['target'])
        params.target_tech = str(paths.get('target_stack') or target.get('tech_stack', self.DEFAULTS['target']['tech_stack'])).lower()
        params.target_dialect = target.get('dialect', self.DEFAULTS['target']['dialect'])
        
        # Extract source technology
        source = registry.get('source', self.DEFAULTS['source'])
        params.source_tech = source.get('tech_stack', self.DEFAULTS['source']['tech_stack'])
        params.source_dialect = source.get('dialect', self.DEFAULTS['source']['dialect'])
        
        # Extract catalog/database
        params.catalog_name = registry.get('catalog', {}).get('name', 'main')
        params.database_name = registry.get('database', {}).get('name')
        
        # Extract table mappings (from registry_raw)
        params.table_mappings = self._extract_table_mappings(registry_raw)
        
        # Store raw registry
        params.raw_registry = registry
        
        return params
    
    
    def _extract_table_mappings(self, registry_raw: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Extract table name mappings from registry.
        
        Looks for entries with key='table_mapping' or similar.
        
        Returns:
            Dict mapping source table names to target names
            {'Customers': 'dim_customers', 'Orders': 'fact_orders'}
        """
        mappings = {}
        
        for entry in registry_raw:
            key = entry.get('key', '')
            value = entry.get('value', '')
            
            # Look for table mapping entries
            if 'table_mapping' in key.lower() or 'table_name' in key.lower():
                if isinstance(value, dict):
                    mappings.update(value)
                elif isinstance(value, str):
                    try:
                        value_dict = json.loads(value)
                        if isinstance(value_dict, dict):
                            mappings.update(value_dict)
                    except:
                        pass
        
        return mappings
    
    
    def resolve_table_name(
        self,
        source_table: str,
        layer: str,
        params: Optional[ProjectParameters] = None
    ) -> str:
        """
        Resolve target table name based on source table and layer.
        
        Args:
            source_table: Source table name (e.g., 'Customers')
            layer: Target layer ('bronze', 'silver', 'gold')
            params: ProjectParameters (if None, uses cached)
        
        Returns:
            Target table name (e.g., 'stg_customers')
        """
        if params is None:
            if self._cache is None:
                raise ValueError("No cached parameters available. Call extract_parameters() first.")
            params = self._cache
        
        # Check if there's an explicit mapping
        if source_table in params.table_mappings:
            base_name = params.table_mappings[source_table]
        else:
            # Default: lowercase source table name
            base_name = source_table.lower()
        
        # Apply layer-specific prefix/suffix
        if layer == 'bronze':
            target_name = f"{params.bronze_prefix}{base_name}{params.bronze_suffix}"
        elif layer == 'silver':
            target_name = f"{params.silver_prefix}{base_name}{params.silver_suffix}"
        elif layer == 'gold':
            target_name = f"{params.gold_prefix}{base_name}{params.gold_suffix}"
        else:
            target_name = base_name
        
        return target_name
    
    
    def get_full_table_path(
        self,
        table_name: str,
        layer: str,
        params: Optional[ProjectParameters] = None
    ) -> str:
        """
        Get full table path including catalog.schema.table.
        
        Args:
            table_name: Table name (resolved target name)
            layer: Layer ('bronze', 'silver', 'gold')
            params: ProjectParameters (if None, uses cached)
        
        Returns:
            Full table path (e.g., 'main.silver_curated.stg_customers')
        """
        if params is None:
            if self._cache is None:
                raise ValueError("No cached parameters available. Call extract_parameters() first.")
            params = self._cache
        
        # Get schema for layer
        if layer == 'bronze':
            schema = params.bronze_schema
        elif layer == 'silver':
            schema = params.silver_schema
        elif layer == 'gold':
            schema = params.gold_schema
        else:
            schema = 'default'
        
        # Build full path
        full_path = f"{params.catalog_name}.{schema}.{table_name}"
        
        return full_path
    
    
    def get_file_path(
        self,
        table_name: str,
        layer: str,
        params: Optional[ProjectParameters] = None
    ) -> str:
        """
        Get file system path for table.
        
        Args:
            table_name: Table name (resolved target name)
            layer: Layer ('bronze', 'silver', 'gold')
            params: ProjectParameters (if None, uses cached)
        
        Returns:
            File path (e.g., '/mnt/datalake/silver/stg_customers')
        """
        if params is None:
            if self._cache is None:
                raise ValueError("No cached parameters available. Call extract_parameters() first.")
            params = self._cache
        
        # Get base path for layer
        if layer == 'bronze':
            base_path = params.bronze_path
        elif layer == 'silver':
            base_path = params.silver_path
        elif layer == 'gold':
            base_path = params.gold_path
        else:
            base_path = '/mnt/datalake'
        
        # Build file path
        file_path = f"{base_path}/{table_name}"
        
        return file_path
    
    
    def to_dict(self, params: Optional[ProjectParameters] = None) -> Dict[str, Any]:
        """
        Convert ProjectParameters to dictionary.
        
        Args:
            params: ProjectParameters (if None, uses cached)
        
        Returns:
            Dictionary representation
        """
        if params is None:
            if self._cache is None:
                raise ValueError("No cached parameters available. Call extract_parameters() first.")
            params = self._cache
        
        return {
            'project_id': params.project_id,
            'paths': {
                'bronze_path': params.bronze_path,
                'silver_path': params.silver_path,
                'gold_path': params.gold_path
            },
            'schemas': {
                'bronze_schema': params.bronze_schema,
                'silver_schema': params.silver_schema,
                'gold_schema': params.gold_schema
            },
            'naming': {
                'bronze_prefix': params.bronze_prefix,
                'silver_prefix': params.silver_prefix,
                'gold_prefix': params.gold_prefix,
                'bronze_suffix': params.bronze_suffix,
                'silver_suffix': params.silver_suffix,
                'gold_suffix': params.gold_suffix
            },
            'target': {
                'tech_stack': params.target_tech,
                'dialect': params.target_dialect,
                'catalog_name': params.catalog_name,
                'database_name': params.database_name
            },
            'source': {
                'tech_stack': params.source_tech,
                'dialect': params.source_dialect
            },
            'table_mappings': params.table_mappings
        }
    
    
    def clear_cache(self):
        """Clear cached parameters"""
        self._cache = None
        logger.info("[ParameterExtractor] Cache cleared", "ParameterExtractor")
