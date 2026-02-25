"""
Column Mapping Service - Manages source→target column mappings
Phase A - Column Mapping Engine

Handles CRUD operations for utm_column_mappings table which stores
granular column-level transformations and metadata.
"""

from typing import List, Dict, Optional
from supabase import Client

class ColumnMapping:
    def __init__(
        self,
        asset_id: str,
        source_column: str,
        source_datatype: str = None,
        target_column: str = None,
        target_datatype: str = None,
        transformation_rule: str = None,
        is_pii: bool = False,
        is_nullable: bool = True,
        default_value: str = None
    ):
        self.asset_id = asset_id
        self.source_column = source_column
        self.source_datatype = source_datatype
        self.target_column = target_column or source_column  # Default to same name
        self.target_datatype = target_datatype
        self.transformation_rule = transformation_rule
        self.is_pii = is_pii
        self.is_nullable = is_nullable
        self.default_value = default_value

class ColumnMappingService:
    """Service for managing column-level mappings"""
    
    def __init__(self, supabase_client: Client):
        self.db = supabase_client
    
    async def get_mappings_for_asset(self, asset_id: str) -> List[Dict]:
        """Get all column mappings for an asset"""
        result = self.db.table('utm_column_mappings')\
            .select('*')\
            .eq('asset_id', asset_id)\
            .order('source_column')\
            .execute()
        
        return result.data or []
    
    async def upsert_mapping(self, mapping: ColumnMapping) -> Dict:
        """Create or update a column mapping"""
        data = {
            'asset_id': mapping.asset_id,
            'source_column': mapping.source_column,
            'source_datatype': mapping.source_datatype,
            'target_column': mapping.target_column,
            'target_datatype': mapping.target_datatype,
            'transformation_rule': mapping.transformation_rule,
            'is_pii': mapping.is_pii,
            'is_nullable': mapping.is_nullable,
            'default_value': mapping.default_value
        }
        
        result = self.db.table('utm_column_mappings')\
            .upsert(data, on_conflict='asset_id,source_column')\
            .execute()
        
        return result.data[0] if result.data else None
    
    async def bulk_upsert(self, mappings: List[ColumnMapping]) -> int:
        """Upsert multiple mappings at once"""
        data_list = [
            {
                'asset_id': m.asset_id,
                'source_column': m.source_column,
                'source_datatype': m.source_datatype,
                'target_column': m.target_column,
                'target_datatype': m.target_datatype,
                'transformation_rule': m.transformation_rule,
                'is_pii': m.is_pii,
                'is_nullable': m.is_nullable,
                'default_value': m.default_value
            }
            for m in mappings
        ]
        
        result = self.db.table('utm_column_mappings')\
            .upsert(data_list, on_conflict='asset_id,source_column')\
            .execute()
        
        return len(result.data) if result.data else 0
    
    async def delete_mapping(self, asset_id: str, source_column: str) -> bool:
        """Delete a specific column mapping"""
        result = self.db.table('utm_column_mappings')\
            .delete()\
            .eq('asset_id', asset_id)\
            .eq('source_column', source_column)\
            .execute()
        
        return True if result.data else False
    
    async def get_pii_columns(self, asset_id: str) -> List[str]:
        """Get list of PII column names for an asset"""
        result = self.db.table('utm_column_mappings')\
            .select('source_column')\
            .eq('asset_id', asset_id)\
            .eq('is_pii', True)\
            .execute()
        
        return [row['source_column'] for row in (result.data or [])]
    
    async def suggest_mapping(
        self, 
        source_column: str, 
        source_datatype: str
    ) -> Dict:
        """AI-powered mapping suggestion (placeholder for future LLM integration)"""
        # Basic heuristic mappings
        type_map = {
            'INT': 'BIGINT',
            'VARCHAR': 'STRING',
            'DATETIME': 'TIMESTAMP',
            'DECIMAL': 'DOUBLE'
        }
        
        # PII detection heuristics
        pii_keywords = ['email', 'phone', 'ssn', 'address', 'name', 'password']
        is_pii = any(kw in source_column.lower() for kw in pii_keywords)
        
        suggested_type = type_map.get(source_datatype.upper(), source_datatype)
        
        return {
            'target_column': source_column.lower(),  # Snake_case convention
            'target_datatype': suggested_type,
            'is_pii': is_pii,
            'transformation_rule': 'CAST' if suggested_type != source_datatype else None
        }
