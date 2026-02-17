"""
Knowledge Packet Service (Phase B - v4.0)

Consolidates 6 data silos into unified KnowledgePacket per asset:
1. utm_objects.metadata (SSIS components)
2. utm_asset_columns (Sprint 7 - profiled columns with types)
3. schema_reference.json (DDL tables/columns from Discovery)
4. utm_origin_analysis_columns (Sprint 8.5 - source query intelligence)
5. utm_column_mappings (explicit source→target mappings)
6. utm_solution_context (business rules and notes)

Type resolution priority: DDL > profiled > metadata > "STRING"
"""

import re
import json
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

# Multi-context imports
try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence, PersistenceService
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence, PersistenceService
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence, PersistenceService


# ============================================
# Pydantic Models
# ============================================

class ColumnKnowledge(BaseModel):
    """Complete knowledge about a single column."""
    name: str
    source_type: str  # Real type (from DDL/profiling, not "STRING")
    target_type: Optional[str] = None  # Mapped target type
    is_pk: bool = False
    is_fk: bool = False
    is_nullable: bool = True
    is_pii: bool = False
    pii_category: Optional[str] = None  # ssn, email, phone, etc.
    cardinality_ratio: Optional[float] = None
    partition_candidate: Optional[bool] = None
    sample_values: Optional[List[str]] = None
    resolution_source: str = "fallback"  # ddl | profiled | metadata | fallback


class ColumnMapping(BaseModel):
    """Explicit source→target column mapping."""
    source_column: str
    target_column: str
    transformation: Optional[str] = None
    mapping_type: str = "direct"  # direct | derived | lookup | constant


class TransformationStep(BaseModel):
    """SSIS transformation component."""
    type: str  # DERIVED_COLUMN, LOOKUP, SORT, UNION_ALL, etc.
    component_name: str
    expression: Optional[str] = None
    target_table: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SourceConnection(BaseModel):
    """Source connection details."""
    connection_name: str
    server: Optional[str] = None
    database: Optional[str] = None
    connection_type: str  # OLEDB, ODBC, ADO.NET


class TableImpactInfo(BaseModel):
    """Impact of this asset on a table (from Phase C)."""
    table_name: str
    operation: str  # SELECT, INSERT, UPDATE, DELETE, MERGE, TRUNCATE
    access_pattern: Optional[str] = None  # FULL_LOAD, INCREMENTAL, LOOKUP, UPSERT, SCD
    is_source: bool
    is_target: bool
    columns_affected: Optional[List[str]] = None


class KnowledgePacket(BaseModel):
    """
    Complete knowledge packet for an asset.
    Everything Agent C needs to generate high-quality code.
    """
    # Identity
    object_id: str
    source_name: str
    source_tech: str
    
    # Columns (type resolved by priority: DDL > profiled > metadata > STRING)
    columns: List[ColumnKnowledge] = Field(default_factory=list)
    
    # Source intelligence (Sprint 8.5)
    source_query: Optional[str] = None  # SQL query from SqlCommand
    transformations: List[TransformationStep] = Field(default_factory=list)
    source_connections: List[SourceConnection] = Field(default_factory=list)
    complexity_score: Optional[int] = None  # 0-100
    
    # Column mappings (utm_column_mappings)
    column_mappings: List[ColumnMapping] = Field(default_factory=list)
    
    # Business context (utm_solution_context)
    business_context: Optional[str] = None
    
    # PII/Privacy
    pii_columns: List[str] = Field(default_factory=list)
    masking_rules: Optional[Dict[str, str]] = None  # column → masking rule
    
    # Table impacts (from Phase C)
    table_impacts: List[TableImpactInfo] = Field(default_factory=list)
    
    # Metadata
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ============================================
# Knowledge Packet Service (Librarian)
# ============================================

class KnowledgePacketService:
    """
    Read-only service that consolidates 6 data silos into unified KnowledgePacket.
    No migrations, no new tables — just reads and consolidates.
    """
    
    def __init__(self, tenant_id: Optional[str] = None, project_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.project_id = project_id
        self.db = SupabasePersistence(tenant_id=tenant_id)
        self.storage = PersistenceService.get_storage()  # R2 or local storage abstraction
    
    async def get_packet(self, asset_id: str) -> KnowledgePacket:
        """
        Consolidate all knowledge about an asset from 6 silos.
        
        Steps:
        1. Read utm_objects (metadata + Sprint 8.5 columns)
        2. Read utm_asset_columns (profiled types, PII)
        3. Read utm_column_mappings (source→target rules)
        4. Read utm_solution_context (business notes)
        5. Load schema_reference.json from R2 (DDL types)
        6. Resolve types by priority: DDL > profiled > metadata
        7. Read table impacts (from Phase C, if exists)
        8. Assemble KnowledgePacket
        """
        logger.info(f"[Librarian] Building knowledge packet: asset_id={asset_id}", "Librarian")
        
        # 1. Read utm_objects
        asset = await self._get_asset(asset_id)
        if not asset:
            raise ValueError(f"Asset not found: {asset_id}")
        
        project_id = asset.get("project_id")
        metadata = asset.get("metadata", {})
        
        # Ensure source_tech is in metadata for tech-agnostic extraction
        if "source_tech" not in metadata:
            metadata["source_tech"] = asset.get("source_tech", "UNKNOWN")
        
        # 2. Read utm_asset_columns (profiled)
        profiled_columns = await self._get_profiled_columns(asset_id)
        
        # 3. Read utm_column_mappings
        column_mappings = await self._get_column_mappings(asset_id)
        
        # 4. Read utm_solution_context
        business_context = await self._get_business_context(project_id, asset_id)
        
        # 5. Load schema_reference.json from R2
        schema_ref = await self._load_schema_reference(project_id)
        
        # 6. Extract source intelligence (Sprint 8.5)
        source_intelligence = await self._extract_source_intelligence(metadata)
        
        # 7. Resolve column types (DDL > profiled > metadata > fallback)
        resolved_columns = await self._resolve_column_types(
            metadata, profiled_columns, schema_ref, source_intelligence
        )
        
        # 8. Read table impacts (Phase C)
        table_impacts = await self._get_table_impacts(project_id, asset_id)
        
        # 9. Identify PII columns
        pii_columns, masking_rules = self._identify_pii(resolved_columns, profiled_columns)
        
        # Assemble packet
        packet = KnowledgePacket(
            object_id=asset_id,
            source_name=asset.get("name", ""),
            source_tech=asset.get("source_tech", ""),
            columns=resolved_columns,
            source_query=source_intelligence.get("source_query"),
            transformations=source_intelligence.get("transformations", []),
            source_connections=source_intelligence.get("connections", []),
            complexity_score=source_intelligence.get("complexity_score"),
            column_mappings=column_mappings,
            business_context=business_context,
            pii_columns=pii_columns,
            masking_rules=masking_rules,
            table_impacts=table_impacts
        )
        
        logger.info(
            f"[Librarian] Knowledge packet built: {len(resolved_columns)} columns, "
            f"{len(table_impacts)} table impacts",
            "Librarian"
        )
        
        return packet
    
    # ============================================
    # Data fetchers
    # ============================================
    
    async def _get_asset(self, asset_id: str) -> Optional[Dict]:
        """Read asset from utm_objects."""
        query = (
            self.db.client.table("utm_objects")
            .select("*")
            .eq("object_id", asset_id)
        )
        
        # Multi-tenant isolation via tenant_id
        if self.tenant_id:
            query = query.eq("tenant_id", self.tenant_id)
        
        result = query.execute()
        return result.data[0] if result.data else None
    
    async def _get_profiled_columns(self, asset_id: str) -> List[Dict]:
        """Read profiled columns from utm_asset_columns (Sprint 7)."""
        try:
            query = (
                self.db.client.table("utm_asset_columns")
                .select("*")
                .eq("object_id", asset_id)
            )
            
            # Multi-tenant isolation
            if self.tenant_id:
                query = query.eq("tenant_id", self.tenant_id)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.warning(f"[Librarian] No profiled columns found: {e}", "Librarian")
            return []
    
    async def _get_column_mappings(self, asset_id: str) -> List[ColumnMapping]:
        """Read column mappings from utm_column_mappings."""
        try:
            query = (
                self.db.client.table("utm_column_mappings")
                .select("*")
                .eq("source_object_id", asset_id)
            )
            
            # Multi-tenant isolation
            if self.tenant_id:
                query = query.eq("tenant_id", self.tenant_id)
            
            result = query.execute()
            
            mappings = []
            for row in result.data or []:
                mappings.append(ColumnMapping(
                    source_column=row.get("source_column", ""),
                    target_column=row.get("target_column", ""),
                    transformation=row.get("transformation"),
                    mapping_type=row.get("mapping_type", "direct")
                ))
            
            return mappings
        except Exception as e:
            logger.warning(f"[Librarian] No column mappings found: {e}", "Librarian")
            return []
    
    async def _get_business_context(self, project_id: str, asset_id: str) -> Optional[str]:
        """Read business context from utm_solution_context."""
        try:
            query = (
                self.db.client.table("utm_solution_context")
                .select("notes")
                .eq("project_id", project_id)
                .eq("object_id", asset_id)
            )
            
            if self.tenant_id:
                query = query.eq("tenant_id", self.tenant_id)
            
            result = query.execute()
            
            if result.data and result.data[0].get("notes"):
                return result.data[0]["notes"]
            
            return None
        except Exception as e:
            logger.warning(f"[Librarian] No business context found: {e}", "Librarian")
            return None
    
    async def _load_schema_reference(self, project_id: str) -> Dict[str, Any]:
        """Load schema_reference.json from storage (R2/local - DDL types)."""
        try:
            # Build storage key
            project_base = PersistenceService.ensure_solution_dir(project_id, self.tenant_id)
            key = f"{project_base}/Discovery/schema_reference.json"
            
            # Read file content
            content = self.storage.read_file(key)
            
            if content:
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                return json.loads(content)
            
            return {}
        except Exception as e:
            logger.warning(f"[Librarian] No schema_reference.json found: {e}", "Librarian")
            return {}
    
    async def _get_table_impacts(self, project_id: str, asset_id: str) -> List[TableImpactInfo]:
        """Read table impacts from utm_table_impacts (Phase C)."""
        try:
            query = (
                self.db.client.table("utm_table_impacts")
                .select("*")
                .eq("project_id", project_id)
                .eq("asset_id", asset_id)
            )
            
            if self.tenant_id:
                query = query.eq("tenant_id", self.tenant_id)
            
            result = query.execute()
            
            impacts = []
            for row in result.data or []:
                impacts.append(TableImpactInfo(
                    table_name=row.get("full_name", ""),
                    operation=row.get("operation", "UNKNOWN"),
                    access_pattern=row.get("access_pattern"),
                    is_source=row.get("is_source", False),
                    is_target=row.get("is_target", False),
                    columns_affected=row.get("columns_affected")
                ))
            
            return impacts
        except Exception as e:
            logger.warning(f"[Librarian] No table impacts found: {e}", "Librarian")
            return []
    
    # ============================================
    # Source Intelligence Extraction (Sprint 14 - Zero-Hardcode v4.0)
    # ============================================
    
    async def _resolve_parser_config(self, source_tech: str) -> Optional[Dict[str, Any]]:
        """
        Resolve parser configuration from database (ZERO-HARDCODE).
        
        Uses utm_parser_catalog + utm_source_tech_catalog to find parser config.
        Returns medulla_config JSONB that defines structure dynamically.
        
        Example config:
        {
            "main_key": "data_flow_logic",
            "sql_keys": ["SqlCommand", "OpenRowset"],
            "transformation_types": ["DerivedColumn", "Lookup", ...],
            "complexity_weights": {"Lookup": 3, "Script": 8}
        }
        """
        try:
            # Call DB function to resolve parser
            result = self.client.rpc(
                "resolve_parser_by_tech",
                {"p_source_tech": source_tech}
            ).execute()
            
            if result.data and len(result.data) > 0:
                parser = result.data[0]
                logger.info(
                    f"[Librarian] Resolved parser: {parser['parser_id']} for tech: {source_tech}",
                    "Librarian"
                )
                return parser["medulla_config"]
            
            logger.warning(f"[Librarian] No parser found for tech: {source_tech}", "Librarian")
            return None
        
        except Exception as e:
            logger.error(f"[Librarian] Parser resolution failed: {e}", "Librarian")
            return None
    
    async def _extract_source_intelligence(self, metadata: Dict) -> Dict[str, Any]:
        """
        Extract source intelligence from metadata.logical_medulla (TRULY TECH-AGNOSTIC).
        
        ✅ ZERO-HARDCODE: Uses database-driven parser configuration.
        
        Flow:
        1. Query utm_parser_catalog for medulla_config JSONB
        2. Use config to locate data dynamically (no if/elif tech checks)
        3. Extract SQL, transformations, complexity using config weights
        
        Supports ANY source technology with registered parser.
        Adding new tech = INSERT into catalog, NO code changes.
        
        Returns:
        - Source query (SQL)
        - Transformation chain
        - Source connections
        - Complexity score
        """
        medulla = metadata.get("logical_medulla", {})
        source_tech = metadata.get("source_tech", "UNKNOWN")
        
        source_query = None
        transformations = []
        connections = []
        complexity_score = 0
        
        # Extract connections (standardized across ALL techs)
        for conn in medulla.get("connections", []):
            connections.append(SourceConnection(
                connection_name=conn.get("name", ""),
                server=conn.get("server"),
                database=conn.get("database"),
                connection_type=conn.get("type", "OLEDB")
            ))
        
        # 🔥 ZERO-HARDCODE: Resolve parser from database
        parser_config = await self._resolve_parser_config(source_tech)
        
        if not parser_config:
            logger.warning(f"[Librarian] No parser config for {source_tech}, using generic fallback", "Librarian")
            parser_config = {
                "main_key": "components",
                "sql_keys": ["sql_query", "query", "sql_command", "source_query"],
                "transformation_types": ["UNKNOWN"],
                "complexity_weights": {"default": 2}
            }
        
        # 🔥 DATA-DRIVEN EXTRACTION (no tech-specific code)
        source_query, transformations, complexity_score = self._extract_intelligence_dynamic(
            medulla, 
            parser_config
        )
        
        return {
            "source_query": source_query,
            "transformations": transformations,
            "connections": connections,
            "complexity_score": complexity_score
        }
    
    def _extract_intelligence_dynamic(self, medulla: Dict, config: Dict) -> tuple:
        """
        Dynamic intelligence extraction using parser configuration (DATA-DRIVEN).
        
        This method replaces ALL tech-specific _extract_{tech}_intelligence() methods.
        Uses config JSONB from utm_parser_catalog to locate data.
        
        Args:
            medulla: Logical medulla structure
            config: Parser config with main_key, sql_keys, transformation_types, complexity_weights
        
        Returns:
            (source_query, transformations, complexity_score)
        """
        source_query = None
        transformations = []
        complexity_score = 0
        
        # Extract configuration keys
        main_key = config.get("main_key", "components")
        sql_keys = config.get("sql_keys", [])
        transformation_types = config.get("transformation_types", [])
        complexity_weights = config.get("complexity_weights", {})
        
        # Iterate over main data structure (data-driven)
        for component in medulla.get(main_key, []):
            comp_type = component.get("type", "").lower()
            comp_name = component.get("name", "")
            props = component.get("raw_properties", {}) or component.get("properties", {})
            
            # 🔥 Extract SQL from dynamic sql_keys
            for sql_key in sql_keys:
                if sql_key in props and props[sql_key]:
                    if not source_query:  # Take first SQL as primary source
                        source_query = props[sql_key]
                    break
                elif sql_key in component and component[sql_key]:
                    if not source_query:
                        source_query = component[sql_key]
                    break
            
            # 🔥 Track transformations (data-driven)
            if any(t.lower() in comp_type for t in transformation_types):
                transformations.append(TransformationStep(
                    type=comp_type.upper(),
                    component_name=comp_name,
                    expression=props.get("Expression") or props.get("expression"),
                    target_table=props.get("TableOrViewName") or props.get("target_table"),
                    details={"properties": props}
                ))
            
            # 🔥 Complexity scoring (configurable weights)
            weight = complexity_weights.get(comp_type.lower(), complexity_weights.get("default", 1))
            complexity_score += weight
        
        # Normalize to 0-100
        complexity_score = min(complexity_score, 100)
        
        return source_query, transformations, complexity_score
    
    # ==============================================================================
    # DEPRECATED: Tech-specific methods removed (Sprint 14 - Zero-Hardcode refactor)
    # ==============================================================================
    # Previous methods:
    #   - _extract_ssis_intelligence()
    #   - _extract_oracle_intelligence()
    #   - _extract_datastage_intelligence()
    #   - _extract_informatica_intelligence()
    #   - _extract_generic_intelligence()
    #   - _calculate_component_complexity()
    #
    # Replaced by: _extract_intelligence_dynamic() (data-driven from utm_parser_catalog)
    # ==============================================================================
    
    # ============================================
    # Type Resolution (Key Algorithm)
    # ============================================
    
    async def _resolve_column_types(
        self,
        metadata: Dict,
        profiled_columns: List[Dict],
        schema_ref: Dict,
        source_intelligence: Dict
    ) -> List[ColumnKnowledge]:
        """
        Resolve column types by priority: DDL > profiled > metadata > "STRING".
        
        Cross-link SSIS table names with DDL schema (key innovation).
        """
        # 1. Extract columns from metadata (SSIS parser)
        metadata_columns = self._extract_metadata_columns(metadata)
        
        # 2. Extract table names from source query (SSIS↔DDL linking)
        referenced_tables = self._extract_table_names_from_query(source_intelligence.get("source_query"))
        
        # 3. Build DDL column map from schema_reference.json
        ddl_columns = self._build_ddl_column_map(schema_ref, referenced_tables)
        
        # 4. Build profiled column map
        profiled_map = {col.get("column_name", "").lower(): col for col in profiled_columns}
        
        # 5. Resolve each column by priority
        resolved = []
        for meta_col in metadata_columns:
            col_name = meta_col.get("name", "").lower()
            
            # Priority 1: DDL (most precise)
            if col_name in ddl_columns:
                ddl_col = ddl_columns[col_name]
                resolved.append(ColumnKnowledge(
                    name=meta_col["name"],
                    source_type=ddl_col.get("data_type", "STRING"),
                    is_pk=ddl_col.get("is_primary_key", False),
                    is_nullable=ddl_col.get("is_nullable", True),
                    resolution_source="ddl"
                ))
            
            # Priority 2: Profiled
            elif col_name in profiled_map:
                prof_col = profiled_map[col_name]
                resolved.append(ColumnKnowledge(
                    name=meta_col["name"],
                    source_type=prof_col.get("inferred_type", "STRING"),
                    is_nullable=prof_col.get("nullable_flag", True),
                    is_pii=prof_col.get("is_pii", False),
                    pii_category=prof_col.get("pii_category"),
                    cardinality_ratio=prof_col.get("cardinality_ratio"),
                    sample_values=prof_col.get("sample_values"),
                    resolution_source="profiled"
                ))
            
            # Priority 3: Metadata (SSIS parser)
            elif meta_col.get("type"):
                resolved.append(ColumnKnowledge(
                    name=meta_col["name"],
                    source_type=meta_col.get("type", "STRING"),
                    resolution_source="metadata"
                ))
            
            # Priority 4: Fallback
            else:
                resolved.append(ColumnKnowledge(
                    name=meta_col["name"],
                    source_type="STRING",
                    resolution_source="fallback"
                ))
        
        return resolved
    
    def _extract_metadata_columns(self, metadata: Dict) -> List[Dict]:
        """Extract column list from metadata.logical_medulla."""
        medulla = metadata.get("logical_medulla", {})
        
        # Look for columns in various places
        columns = []
        
        # From data_flow_logic components
        for comp in medulla.get("data_flow_logic", []):
            if comp.get("columns"):
                columns.extend(comp["columns"])
        
        # From columns array (Sprint 8.5)
        if medulla.get("columns"):
            columns.extend(medulla["columns"])
        
        # Deduplicate by name
        seen = set()
        unique_columns = []
        for col in columns:
            name = col.get("name", "").lower()
            if name and name not in seen:
                seen.add(name)
                unique_columns.append(col)
        
        return unique_columns
    
    def _extract_table_names_from_query(self, sql_query: Optional[str]) -> List[str]:
        """
        Extract table names from SQL query using regex (MULTI-DIALECT).
        
        Supports SQL dialects from multiple sources:
        - SQL Server: [dbo].[Table], dbo.Table
        - Oracle: SCHEMA.TABLE, "SCHEMA"."TABLE"
        - PostgreSQL: "schema"."table", schema.table
        - MySQL: `schema`.`table`, schema.table
        
        Returns list of table names in format: schema.table or table
        """
        if not sql_query:
            return []
        
        tables = set()
        
        # Regex patterns for SQL table extraction (MULTI-DIALECT)
        # Supports: [brackets], "quotes", `backticks`, plain names
        patterns = [
            r'\bFROM\s+(?:[\["`]?(\w+)[\]"`]?\.)?[\["`]?(\w+)[\]"`]?',  # FROM
            r'\b(?:INNER\s+|LEFT\s+|RIGHT\s+|CROSS\s+|FULL\s+)?(?:OUTER\s+)?JOIN\s+(?:[\["`]?(\w+)[\]"`]?\.)?[\["`]?(\w+)[\]"`]?',  # JOIN
            r'\bINTO\s+(?:[\["`]?(\w+)[\]"`]?\.)?[\["`]?(\w+)[\]"`]?',  # INSERT INTO
            r'\bUPDATE\s+(?:[\["`]?(\w+)[\]"`]?\.)?[\["`]?(\w+)[\]"`]?',  # UPDATE
            r'\bDELETE\s+FROM\s+(?:[\["`]?(\w+)[\]"`]?\.)?[\["`]?(\w+)[\]"`]?',  # DELETE
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, sql_query, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    schema = groups[0] if groups[0] else None
                    table = groups[1] if groups[1] else groups[0]
                    
                    if table:
                        # Format: schema.table or just table
                        full_name = f"{schema}.{table}" if schema else table
                        tables.add(full_name)
        
        # Clean names (remove brackets, quotes, backticks - support all SQL dialects)
        cleaned = []
        reserved_words = {'select', 'from', 'where', 'values', 'set', 'inner', 'left', 'right', 'join', 'outer', 'cross', 'full'}
        
        for t in tables:
            # Strip SQL Server brackets, PostgreSQL/Oracle quotes, MySQL backticks
            cleaned_name = t.replace('[', '').replace(']', '').replace('"', '').replace('`', '').strip()
            if cleaned_name and cleaned_name.lower() not in reserved_words:
                cleaned.append(cleaned_name)
        
        return cleaned
    
    def _build_ddl_column_map(self, schema_ref: Dict, referenced_tables: List[str]) -> Dict[str, Dict]:
        """
        Build column name → DDL info map from schema_reference.json.
        Only include columns from tables referenced in SSIS query.
        """
        ddl_map = {}
        
        tables_dict = schema_ref.get("tables", {})
        
        for table_name in referenced_tables:
            # Try exact match
            clean_name = table_name.split(".")[-1].strip("[]\"")
            
            if clean_name in tables_dict:
                table_info = tables_dict[clean_name]
                for col in table_info.get("columns", []):
                    col_name = col.get("name", "").lower()
                    if col_name:
                        ddl_map[col_name] = col
        
        return ddl_map
    
    def _identify_pii(self, columns: List[ColumnKnowledge], profiled: List[Dict]) -> tuple[List[str], Dict[str, str]]:
        """
        Identify PII columns and masking rules.
        Uses profiled data + heuristics on column names.
        """
        pii_columns = []
        masking_rules = {}
        
        pii_patterns = {
            r'ssn|social.?security': 'sha256',
            r'email': 'email_mask',
            r'phone|tel': 'phone_mask',
            r'credit.?card|cc.?number': 'cc_mask',
            r'password|pwd': 'hash',
            r'salary|income|wage': 'numeric_mask'
        }
        
        for col in columns:
            col_name_lower = col.name.lower()
            
            # Check if marked as PII in profiling
            if col.is_pii:
                pii_columns.append(col.name)
                if col.pii_category:
                    masking_rules[col.name] = f"{col.pii_category}_mask"
                continue
            
            # Heuristic detection
            for pattern, mask_type in pii_patterns.items():
                if re.search(pattern, col_name_lower):
                    pii_columns.append(col.name)
                    masking_rules[col.name] = mask_type
                    break
        
        return pii_columns, masking_rules if masking_rules else None
    
    # ============================================
    # Project-level scanning
    # ============================================
    
    async def scan_project(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Scan entire project and return consolidated metadata.
        Used by Triage Pipeline v2 (Phase D).
        
        Returns:
        {
            "total_assets": 12,
            "assets_with_ddl_types": 8,
            "assets_with_profiled_types": 10,
            "pii_columns_detected": 15,
            "schema_reference": {...},
            "summary": "8/12 assets have DDL types..."
        }
        """
        proj_id = project_id or self.project_id
        if not proj_id:
            raise ValueError("project_id required")
        
        logger.info(f"[Librarian] Scanning project: {proj_id}", "Librarian")
        
        # Load schema_reference.json
        schema_ref = await self._load_schema_reference(proj_id)
        
        # Get all assets (tenant isolation via project_id FK)
        query = (
            self.db.client.table("utm_objects")
            .select("*")
            .eq("project_id", proj_id)
        )
        # NOTE: Using SELECT * instead of specific columns to avoid RLS column-level restrictions
        # Tenant isolation maintained via project_id -> utm_projects.tenant_id FK
        
        assets = query.execute().data or []
        
        # Count assets with different type sources
        assets_with_ddl = 0
        assets_with_profiled = 0
        total_pii_columns = 0
        
        for asset in assets:
            asset_id = asset["object_id"]
            
            # Check if has profiled columns
            profiled = await self._get_profiled_columns(asset_id)
            if profiled:
                assets_with_profiled += 1
                total_pii_columns += sum(1 for p in profiled if p.get("is_pii"))
            
            # Check if has DDL types (via schema_reference)
            if schema_ref.get("tables"):
                assets_with_ddl += 1
        
        summary = (
            f"{assets_with_ddl}/{len(assets)} assets have DDL types, "
            f"{assets_with_profiled}/{len(assets)} have profiled types, "
            f"{total_pii_columns} PII columns detected"
        )
        
        return {
            "total_assets": len(assets),
            "assets_with_ddl_types": assets_with_ddl,
            "assets_with_profiled_types": assets_with_profiled,
            "pii_columns_detected": total_pii_columns,
            "schema_reference": schema_ref,
            "summary": summary
        }
