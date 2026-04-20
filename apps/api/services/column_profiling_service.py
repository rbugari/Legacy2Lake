"""
Column Profiling Service - Sprint 7: Deep Forensic Triage
==========================================================

Purpose:
    Analyzes database/file columns to extract detailed metrics:
    - Cardinality (distinct values)
    - Nullability (null percentage)
    - Data type inference
    - PII detection (email, SSN, phone, etc.)
    - Partition recommendations

Usage:
    profiler = ColumnProfilingService()
    columns = await profiler.profile_asset(asset_id, sample_data)
    await profiler.persist_to_db(asset_id, project_id, columns)

Integration:
    - Called by Agent A during triage analysis
    - Stores results in utm_asset_columns table
    - Used by Triage UI for heatmaps and visualizations

Author: Legacy2Lake Engineering
Date: 2026-02-11
Version: v1.0 (Sprint 7)
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    from utils.logger import logger
    from services.persistence_service import SupabasePersistence


class ColumnProfilingService:
    """
    Service for deep column-level analysis of data assets.
    Provides 10+ metrics per column for forensic triage.
    """
    
    # PII Detection Patterns (Regex)
    PII_PATTERNS = {
        'EMAIL': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'SSN': r'^\d{3}-?\d{2}-?\d{4}$',
        'PHONE': r'^(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}$',
        'CREDIT_CARD': r'^\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}$',
        'ZIP_CODE': r'^\d{5}(-\d{4})?$',
        'IP_ADDRESS': r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',
        'URL': r'^https?://[^\s/$.?#].[^\s]*$',
        'DATE': r'^\d{4}-\d{2}-\d{2}$',
        'GUID': r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    }
    
    # Sensitive keywords in column names (for PII inference)
    PII_KEYWORDS = {
        'EMAIL': ['email', 'e-mail', 'mail', 'correo'],
        'SSN': ['ssn', 'social', 'security', 'seguro'],
        'PHONE': ['phone', 'tel', 'telefono', 'mobile', 'cell'],
        'NAME': ['name', 'nombre', 'firstname', 'lastname', 'fullname'],
        'ADDRESS': ['address', 'street', 'ciudad', 'city', 'zip', 'postal'],
        'CREDIT_CARD': ['card', 'credit', 'tarjeta', 'payment'],
        'SALARY': ['salary', 'salario', 'wage', 'income', 'compensation'],
        'BIRTH_DATE': ['birth', 'dob', 'birthdate', 'nacimiento'],
        'PASSPORT': ['passport', 'pasaporte', 'document'],
        'TAX_ID': ['tax', 'tin', 'rfc', 'cuit', 'dni']
    }
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.version = "v1.0"
    
    
    async def profile_from_mappings(
        self,
        project_id: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Generate inferred profiling data from utm_column_mappings (without real data sampling).
        
        This method is called during Triage when column mappings are created but
        actual data sampling is not performed. It creates placeholder profiling metrics
        based on column names, data types, and heuristics.
        
        Args:
            project_id: UUID of the project to profile
            force_refresh: If True, delete existing profiling data before generating new
            
        Returns:
            Dict with profiling results:
            {
                "success": bool,
                "columns_profiled": int,
                "pii_columns": int,
                "partition_candidates": int,
                "message": str
            }
        """
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        
        try:
            logger.info(
                f"[ColumnProfiling] Starting inferred profiling: project_id={project_id}",
                "Profiler"
            )
            
            # 1. Optionally clear existing profiling data
            if force_refresh:
                logger.info("[ColumnProfiling] Force refresh - clearing existing data", "Profiler")
                db.client.table("utm_asset_columns") \
                    .delete() \
                    .eq("project_id", project_id) \
                    .execute()
            
            # 2. Get all column mappings for project (via utm_objects join)
            mappings_query = db.client.table("utm_column_mappings") \
                .select("*, utm_objects!asset_id(object_id, project_id, source_name)") \
                .execute()
            
            # Filter to project (RLS handles tenant isolation)
            mappings = [
                m for m in mappings_query.data 
                if m.get("utm_objects", {}).get("project_id") == project_id
            ]
            
            logger.info(
                f"[ColumnProfiling] Found {len(mappings)} column mappings to profile",
                "Profiler"
            )
            
            if not mappings:
                return {
                    "success": False,
                    "columns_profiled": 0,
                    "pii_columns": 0,
                    "partition_candidates": 0,
                    "message": "No column mappings found. Run Triage first."
                }
            
            # 3. Group mappings by asset
            from collections import defaultdict
            assets_map = defaultdict(list)
            for mapping in mappings:
                asset_id = mapping["asset_id"]
                assets_map[asset_id].append(mapping)
            
            # 4. Generate profiled columns for each asset
            total_profiled = 0
            total_pii = 0
            total_partition_candidates = 0
            
            for asset_id, asset_mappings in assets_map.items():
                profiled_columns = []
                
                for idx, mapping in enumerate(asset_mappings, 1):
                    source_col = mapping["source_column"]
                    target_col = mapping.get("target_column", source_col)
                    source_type = mapping.get("source_datatype") or "STRING"
                    target_type = mapping.get("target_datatype") or "STRING"
                    is_nullable = mapping.get("is_nullable", True)
                    
                    # Infer PII using existing keyword detection
                    is_pii, pii_category, pii_confidence = self._infer_pii_from_name(source_col)
                    if is_pii:
                        total_pii += 1
                    
                    # Infer cardinality
                    is_pk = "id" in source_col.lower() and "parent" not in source_col.lower()
                    is_fk = "id" in source_col.lower() and ("parent" in source_col.lower() or "ref" in source_col.lower())
                    cardinality = self._infer_cardinality(target_type, is_pk, is_fk)
                    
                    # Infer partition suitability
                    is_partition, partition_score = self._infer_partition_score(source_col, target_type)
                    if is_partition:
                        total_partition_candidates += 1
                    
                    # Generate profiling record
                    column_record = {
                        "column_name": source_col,
                        "column_position": idx,
                        "data_type": source_type,
                        "inferred_type": target_type,
                        "distinct_count": None,
                        "cardinality_ratio": cardinality,
                        "null_count": None,
                        "null_percentage": 5.0 if is_nullable else 0.0,
                        "sample_values": None,
                        "min_value": None,
                        "max_value": None,
                        "is_pii": is_pii,
                        "pii_category": pii_category,
                        "pii_confidence": pii_confidence,
                        "is_primary_key": is_pk,
                        "is_foreign_key": is_fk,
                        "is_nullable": is_nullable,
                        "is_indexed": is_pk or is_fk,
                        "partition_candidate": is_partition,
                        "partition_score": partition_score,
                        "analysis_version": "v1.0-inferred"
                    }
                    
                    profiled_columns.append(column_record)
                
                # Persist columns for this asset
                success = await self.persist_to_db(asset_id, project_id, profiled_columns)
                if success:
                    total_profiled += len(profiled_columns)
            
            logger.info(
                f"[ColumnProfiling] ✅ Inferred profiling complete: "
                f"{total_profiled} columns, {total_pii} PII, {total_partition_candidates} partition candidates",
                "Profiler"
            )
            
            return {
                "success": True,
                "columns_profiled": total_profiled,
                "pii_columns": total_pii,
                "partition_candidates": total_partition_candidates,
                "message": f"Successfully profiled {total_profiled} columns (inferred from mappings)"
            }
            
        except Exception as e:
            logger.error(
                f"[ColumnProfiling] Error in inferred profiling: {str(e)}",
                "Profiler"
            )
            return {
                "success": False,
                "columns_profiled": 0,
                "pii_columns": 0,
                "partition_candidates": 0,
                "message": f"Profiling failed: {str(e)}"
            }
    
    
    def _infer_pii_from_name(self, column_name: str) -> tuple:
        """
        Infer PII category from column name using keyword matching.
        
        Args:
            column_name: Name of the column
            
        Returns:
            Tuple of (is_pii, category, confidence)
        """
        col_lower = column_name.lower()
        
        for category, keywords in self.PII_KEYWORDS.items():
            for keyword in keywords:
                if keyword in col_lower:
                    # Higher confidence for exact matches
                    confidence = 0.95 if col_lower == keyword else 0.75
                    return (True, category, confidence)
        
        return (False, None, 0.0)
    
    
    def _infer_cardinality(self, data_type: str, is_pk: bool, is_fk: bool) -> float:
        """
        Infer cardinality ratio based on column characteristics.
        
        Args:
            data_type: Target data type
            is_pk: True if primary key
            is_fk: True if foreign key
            
        Returns:
            Estimated cardinality ratio (0.0-1.0)
        """
        if is_pk:
            return 1.0  # 100% unique
        elif is_fk:
            return 0.3  # ~30% unique
        elif data_type in ['STRING', 'TEXT']:
            return 0.5  # ~50% unique
        elif data_type in ['INTEGER', 'NUMERIC']:
            return 0.6  # ~60% unique
        else:
            return 0.4
    
    
    def _infer_partition_score(self, column_name: str, data_type: str) -> tuple:
        """
        Infer partition suitability for optimization.
        
        Args:
            column_name: Name of the column
            data_type: Data type
            
        Returns:
            Tuple of (is_candidate, score)
        """
        col_lower = column_name.lower()
        
        # Date/time columns are excellent for partitioning
        if any(kw in col_lower for kw in ['date', 'fecha', 'time', 'timestamp', 'year', 'month']):
            return (True, 0.95)
        
        # Region/location columns are good
        if any(kw in col_lower for kw in ['region', 'country', 'pais', 'estado', 'state']):
            return (True, 0.85)
        
        # ID columns with high cardinality
        if ('id' in col_lower or 'key' in col_lower) and data_type in ['INTEGER', 'STRING']:
            return (True, 0.70)
        
        return (False, 0.0)
    
    
    async def profile_asset(
        self, 
        asset_id: str, 
        columns_data: List[Dict[str, Any]],
        asset_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Main entry point: Profile all columns in an asset.
        
        Args:
            asset_id: UUID of the asset (utm_objects.object_id)
            columns_data: List of column definitions with sample data
                Format: [
                    {
                        "column_name": "CustomerID",
                        "data_type": "INT",
                        "sample_values": [1, 2, 3, ...],
                        "is_nullable": True,
                        "is_primary_key": False,
                        "is_indexed": False
                    },
                    ...
                ]
            asset_metadata: Optional asset-level metadata (for context)
        
        Returns:
            List of profiled column dictionaries (ready for DB insert)
        """
        logger.info(f"[ColumnProfiler] Profiling {len(columns_data)} columns for asset {asset_id}", "Profiler")
        
        profiled_columns = []
        
        for idx, col_info in enumerate(columns_data):
            try:
                profile = await self._profile_single_column(col_info, idx, asset_metadata)
                profiled_columns.append(profile)
            except Exception as e:
                logger.error(f"[ColumnProfiler] Failed to profile column '{col_info.get('column_name')}': {e}", "Profiler")
                # Continue with other columns even if one fails
                continue
        
        logger.info(f"[ColumnProfiler] Successfully profiled {len(profiled_columns)}/{len(columns_data)} columns", "Profiler")
        return profiled_columns
    
    
    async def _profile_single_column(
        self, 
        col_info: Dict[str, Any], 
        position: int,
        asset_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Profile a single column with 10+ metrics.
        
        Args:
            col_info: Column definition with samples
            position: Ordinal position in table
            asset_metadata: Asset context (optional)
        
        Returns:
            Dictionary with profiling results
        """
        column_name = col_info.get('column_name', 'UNKNOWN')
        data_type = col_info.get('data_type', 'UNKNOWN')
        sample_values = col_info.get('sample_values', [])
        is_nullable = col_info.get('is_nullable', True)
        is_primary_key = col_info.get('is_primary_key', False)
        is_indexed = col_info.get('is_indexed', False)
        
        # Calculate cardinality
        distinct_count = len(set(sample_values)) if sample_values else 0
        total_count = len(sample_values)
        cardinality_ratio = (distinct_count / total_count) if total_count > 0 else 0.0
        
        # Calculate nulls
        null_count = sum(1 for v in sample_values if v is None or v == '')
        null_percentage = (null_count / total_count * 100) if total_count > 0 else 0.0
        
        # Infer data type from samples
        inferred_type = self._infer_type(sample_values)
        
        # PII Detection
        pii_result = self._detect_pii(column_name, sample_values, data_type)
        
        # Partition Recommendation
        partition_result = self._recommend_partition(
            column_name, 
            data_type, 
            inferred_type, 
            cardinality_ratio, 
            is_primary_key,
            is_indexed
        )
        
        # Get min/max values
        non_null_values = [v for v in sample_values if v is not None and v != '']
        min_value = str(min(non_null_values)) if non_null_values else None
        max_value = str(max(non_null_values)) if non_null_values else None
        
        # Get precision/scale for numeric types
        precision_scale = self._extract_precision_scale(data_type)
        
        # Build profile dictionary
        profile = {
            'column_name': column_name,
            'column_position': position,
            'data_type': data_type,
            'inferred_type': inferred_type,
            'max_length': self._calculate_max_length(sample_values),
            'precision_scale': precision_scale,
            
            # Cardinality
            'distinct_count': distinct_count,
            'cardinality_ratio': round(cardinality_ratio, 4),
            
            # Nulls
            'null_count': null_count,
            'null_percentage': round(null_percentage, 2),
            
            # Samples
            'sample_values': json.dumps(sample_values[:10]),  # First 10 samples
            'min_value': min_value,
            'max_value': max_value,
            
            # PII
            'is_pii': pii_result['is_pii'],
            'pii_category': pii_result.get('category'),
            'pii_confidence': pii_result.get('confidence', 0.0),
            'pii_pattern': pii_result.get('pattern'),
            
            # Business Intelligence
            'is_primary_key': is_primary_key,
            'is_foreign_key': self._detect_foreign_key(column_name),
            'is_nullable': is_nullable,
            'is_indexed': is_indexed,
            
            # Partition Recommendation
            'partition_candidate': partition_result['is_candidate'],
            'partition_score': partition_result.get('score', 0.0),
            'partition_reason': partition_result.get('reason'),
            
            # Metadata
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'analysis_version': self.version,
            'raw_metadata': json.dumps({
                'total_samples': total_count,
                'unique_samples': distinct_count,
                'inferred_patterns': pii_result.get('patterns', [])
            })
        }
        
        return profile
    
    
    def _infer_type(self, sample_values: List[Any]) -> str:
        """
        Infer semantic data type from sample values.
        
        Returns:
            'STRING', 'NUMERIC', 'DATE', 'DATETIME', 'BOOLEAN', 'GUID', 'UNKNOWN'
        """
        if not sample_values:
            return 'UNKNOWN'
        
        # Filter out nulls
        non_null = [v for v in sample_values if v is not None and v != '']
        if not non_null:
            return 'UNKNOWN'
        
        # Check first few samples
        test_samples = non_null[:10]
        
        # Boolean
        if all(str(v).upper() in ['TRUE', 'FALSE', '1', '0', 'YES', 'NO'] for v in test_samples):
            return 'BOOLEAN'
        
        # Numeric
        if all(isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).replace('-', '', 1).isdigit()) for v in test_samples):
            return 'NUMERIC'
        
        # Date patterns
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        if all(isinstance(v, str) and date_pattern.match(v) for v in test_samples):
            return 'DATE'
        
        # DateTime patterns
        datetime_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}')
        if all(isinstance(v, str) and datetime_pattern.match(v) for v in test_samples):
            return 'DATETIME'
        
        # GUID
        guid_pattern = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', re.IGNORECASE)
        if all(isinstance(v, str) and guid_pattern.match(v) for v in test_samples):
            return 'GUID'
        
        # Default to STRING
        return 'STRING'
    
    
    def _detect_pii(self, column_name: str, sample_values: List[Any], data_type: str) -> Dict[str, Any]:
        """
        Detect if column contains Personally Identifiable Information (PII).
        
        Returns:
            {
                'is_pii': bool,
                'category': str (EMAIL, SSN, etc.),
                'confidence': float (0.0-1.0),
                'pattern': str (regex matched),
                'patterns': list (all patterns matched)
            }
        """
        result = {
            'is_pii': False,
            'category': None,
            'confidence': 0.0,
            'pattern': None,
            'patterns': []
        }
        
        # Step 1: Check column name for PII keywords
        column_lower = column_name.lower()
        name_matches = []
        
        for pii_type, keywords in self.PII_KEYWORDS.items():
            if any(kw in column_lower for kw in keywords):
                name_matches.append(pii_type)
        
        if name_matches:
            result['is_pii'] = True
            result['category'] = name_matches[0]  # Take first match
            result['confidence'] = 0.7  # Moderate confidence from name only
            result['patterns'].append(f"NAME_MATCH:{name_matches[0]}")
        
        # Step 2: Check sample values against regex patterns
        if sample_values:
            non_null = [str(v) for v in sample_values if v is not None and v != ''][:50]  # Check first 50
            
            for pii_type, pattern_str in self.PII_PATTERNS.items():
                pattern = re.compile(pattern_str)
                matches = sum(1 for v in non_null if pattern.match(v))
                
                if matches > 0:
                    match_ratio = matches / len(non_null)
                    
                    if match_ratio >= 0.8:  # 80%+ match = high confidence
                        result['is_pii'] = True
                        result['category'] = pii_type
                        result['confidence'] = 0.95
                        result['pattern'] = pattern_str
                        result['patterns'].append(f"REGEX_MATCH:{pii_type}:{matches}/{len(non_null)}")
                        break  # Use first strong match
                    elif match_ratio >= 0.5:  # 50%+ match = medium confidence
                        result['is_pii'] = True
                        result['category'] = pii_type
                        result['confidence'] = max(result['confidence'], 0.75)
                        result['pattern'] = pattern_str
                        result['patterns'].append(f"PARTIAL_MATCH:{pii_type}:{matches}/{len(non_null)}")
        
        return result
    
    
    def _recommend_partition(
        self, 
        column_name: str, 
        data_type: str, 
        inferred_type: str,
        cardinality_ratio: float,
        is_primary_key: bool,
        is_indexed: bool
    ) -> Dict[str, Any]:
        """
        Recommend if column is a good partition key candidate.
        
        Scoring Criteria:
        - Date/DateTime columns: High score (0.8-1.0)
        - Low-to-medium cardinality STRING: Medium score (0.5-0.7)
        - Indexed columns: Bonus +0.1
        - Primary keys: Penalty -0.3 (usually not good for partitioning)
        - High cardinality (>0.9): Penalty -0.2
        
        Returns:
            {
                'is_candidate': bool,
                'score': float (0.0-1.0),
                'reason': str
            }
        """
        score = 0.0
        reasons = []
        
        # Date/DateTime = Strong candidate
        if inferred_type in ['DATE', 'DATETIME']:
            score += 0.8
            reasons.append("Date/DateTime type - ideal for time-based partitioning")
        
        # Low cardinality STRING (e.g., status, region, category)
        elif inferred_type == 'STRING' and 0.05 <= cardinality_ratio <= 0.3:
            score += 0.6
            reasons.append(f"Low cardinality ({cardinality_ratio:.2%}) - good for categorical partitioning")
        
        # Medium cardinality
        elif 0.3 < cardinality_ratio <= 0.7:
            score += 0.4
            reasons.append(f"Medium cardinality ({cardinality_ratio:.2%})")
        
        # High cardinality (penalty)
        elif cardinality_ratio > 0.9:
            score -= 0.2
            reasons.append(f"Very high cardinality ({cardinality_ratio:.2%}) - may cause too many partitions")
        
        # Indexed = Bonus
        if is_indexed:
            score += 0.1
            reasons.append("Already indexed - efficient for filtering")
        
        # Primary key = Penalty (usually not ideal for partitioning)
        if is_primary_key:
            score -= 0.3
            reasons.append("Primary key - not recommended for partitioning")
        
        # Column name hints
        partition_keywords = ['date', 'year', 'month', 'day', 'quarter', 'region', 'country', 'status', 'type']
        if any(kw in column_name.lower() for kw in partition_keywords):
            score += 0.2
            reasons.append("Column name suggests partitioning use case")
        
        # Clamp score to 0.0-1.0
        score = max(0.0, min(1.0, score))
        
        return {
            'is_candidate': score >= 0.5,  # Threshold for recommendation
            'score': round(score, 2),
            'reason': '; '.join(reasons) if reasons else 'No strong partitioning signals detected'
        }
    
    
    def _detect_foreign_key(self, column_name: str) -> bool:
        """
        Heuristic to detect likely foreign keys based on naming conventions.
        
        Returns:
            True if column name suggests FK (e.g., ends with _id, _key, ID suffix)
        """
        fk_patterns = [r'_id$', r'_key$', r'ID$', r'Key$', r'Ref$']
        column_lower = column_name.lower()
        
        return any(re.search(pattern, column_lower) for pattern in fk_patterns)
    
    
    def _calculate_max_length(self, sample_values: List[Any]) -> Optional[int]:
        """Calculate maximum string length from samples."""
        if not sample_values:
            return None
        
        str_values = [str(v) for v in sample_values if v is not None and v != '']
        if not str_values:
            return None
        
        return max(len(v) for v in str_values)
    
    
    def _extract_precision_scale(self, data_type: str) -> Optional[str]:
        """
        Extract precision and scale from data type definition.
        
        Examples:
            DECIMAL(18,2) -> "18,2"
            NUMERIC(10,4) -> "10,4"
            VARCHAR(255) -> None
        
        Returns:
            String in format "precision,scale" or None
        """
        match = re.search(r'(\d+),\s*(\d+)', data_type)
        if match:
            return f"{match.group(1)},{match.group(2)}"
        return None
    
    
    async def persist_to_db(
        self, 
        asset_id: str, 
        project_id: str, 
        columns: List[Dict[str, Any]]
    ) -> bool:
        """
        Persist profiled columns to utm_asset_columns table.
        
        Args:
            asset_id: UUID of parent asset
            project_id: UUID of parent project
            columns: List of profiled column dictionaries
        
        Returns:
            True if successful, False otherwise
        """
        if not columns:
            logger.warning(f"[ColumnProfiler] No columns to persist for asset {asset_id}", "Profiler")
            return False
        
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        
        try:
            # Prepare records for insert
            records = []
            for col in columns:
                record = {
                    'asset_id': asset_id,
                    'project_id': project_id,
                    **col  # Spread all column metrics
                }
                records.append(record)
            
            # Insert into utm_asset_columns (upsert on conflict)
            result = db.client.table('utm_asset_columns') \
                .upsert(records, on_conflict='asset_id,column_name') \
                .execute()
            
            if result.data:
                logger.info(f"[ColumnProfiler] Persisted {len(records)} columns for asset {asset_id}", "Profiler")
                return True
            else:
                logger.error(f"[ColumnProfiler] Failed to persist columns: {result}", "Profiler")
                return False
                
        except Exception as e:
            logger.error(f"[ColumnProfiler] Database error: {e}", "Profiler")
            return False
    
    
    async def get_asset_columns(self, asset_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve profiled columns for an asset from database.
        
        Args:
            asset_id: UUID of the asset
        
        Returns:
            List of column dictionaries
        """
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        
        try:
            result = db.client.table('utm_asset_columns') \
                .select('*') \
                .eq('asset_id', asset_id) \
                .order('column_position') \
                .execute()
            
            return result.data if result.data else []
        
        except Exception as e:
            logger.error(f"[ColumnProfiler] Failed to retrieve columns: {e}", "Profiler")
            return []
    
    
    async def get_project_pii_heatmap(self, project_id: str) -> Dict[str, Any]:
        """
        Generate PII heatmap data for entire project.
        
        Returns:
            {
                'total_columns': int,
                'pii_columns': int,
                'pii_percentage': float,
                'pii_by_category': {category: count},
                'high_risk_assets': [
                    {
                        'asset_id': str,
                        'asset_name': str,
                        'pii_columns': int,
                        'pii_types': [str],
                        'pii_column_names': [str]  # NEW: Names of PII columns
                    }
                ]
            }
        """
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        
        try:
            # Get all columns for project with asset names
            result = db.client.table('utm_asset_columns') \
                .select('asset_id, column_name, is_pii, pii_category, pii_confidence, utm_objects!asset_id(source_name)') \
                .eq('project_id', project_id) \
                .execute()
            
            columns = result.data if result.data else []
            total_columns = len(columns)
            pii_columns = [c for c in columns if c.get('is_pii')]
            
            # Count by category
            pii_by_category = {}
            for col in pii_columns:
                category = col.get('pii_category', 'UNKNOWN')
                pii_by_category[category] = pii_by_category.get(category, 0) + 1
            
            # Find high-risk assets (assets with multiple PII columns)
            # Group by asset_id and collect PII types + column names
            from collections import defaultdict
            asset_pii_data = defaultdict(lambda: {
                'count': 0, 
                'types': set(), 
                'column_names': [],
                'asset_name': None
            })
            
            for col in pii_columns:
                asset_id = col['asset_id']
                asset_pii_data[asset_id]['count'] += 1
                asset_pii_data[asset_id]['types'].add(col.get('pii_category', 'UNKNOWN'))
                asset_pii_data[asset_id]['column_names'].append(col['column_name'])
                
                # Extract asset name from join
                if not asset_pii_data[asset_id]['asset_name']:
                    asset_obj = col.get('utm_objects', {})
                    asset_pii_data[asset_id]['asset_name'] = asset_obj.get('source_name', 'Unknown') if isinstance(asset_obj, dict) else 'Unknown'
            
            # Build high_risk_assets list (3+ PII columns)
            high_risk_assets = []
            for asset_id, data in asset_pii_data.items():
                if data['count'] >= 3:
                    high_risk_assets.append({
                        'asset_id': asset_id,
                        'asset_name': data['asset_name'],
                        'pii_columns': data['count'],
                        'pii_types': sorted(list(data['types'])),
                        'pii_column_names': data['column_names']  # NEW: List of column names
                    })
            
            # Sort by pii_columns descending
            high_risk_assets.sort(key=lambda x: x['pii_columns'], reverse=True)
            
            # Asset PII counts for backward compatibility
            asset_pii_counts = {aid: data['count'] for aid, data in asset_pii_data.items()}
            
            return {
                'total_columns': total_columns,
                'pii_columns': len(pii_columns),
                'pii_percentage': (len(pii_columns) / total_columns * 100) if total_columns > 0 else 0.0,
                'pii_by_category': pii_by_category,
                'high_risk_assets': high_risk_assets,
                'asset_pii_counts': asset_pii_counts
            }
        
        except Exception as e:
            logger.error(f"[ColumnProfiler] Failed to generate PII heatmap: {e}", "Profiler")
            return {
                'total_columns': 0,
                'pii_columns': 0,
                'pii_percentage': 0.0,
                'pii_by_category': {},
                'high_risk_assets': [],
                'asset_pii_counts': {}
            }
