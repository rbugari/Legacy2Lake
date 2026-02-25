"""
Table Impact Service
Provides table-centric view of asset impacts on database tables.
Solves the "¿quién le pega a cada tabla?" problem.

Phase C - Sprint 14
"""
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from pydantic import BaseModel, Field
from collections import defaultdict, deque

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence


# ============================================
# Pydantic Models
# ============================================

class TableImpact(BaseModel):
    """Single table impact record."""
    table_name: str
    schema_name: Optional[str] = None
    full_name: str
    asset_name: str
    operation: str  # SELECT, INSERT, UPDATE, DELETE, MERGE, TRUNCATE
    access_pattern: Optional[str] = None  # FULL_LOAD, INCREMENTAL, LOOKUP, UPSERT, SCD
    is_source: bool = False
    is_target: bool = False
    sql_statement: Optional[str] = None
    columns_affected: List[str] = Field(default_factory=list)


class TableSummary(BaseModel):
    """Summary of impacts on a single table."""
    full_name: str
    readers_count: int
    writers_count: int
    total_impacts: int
    operations: List[str]


class TableDetail(BaseModel):
    """Detailed impacts on a specific table."""
    table_name: str
    total_impacts: int
    readers: List[Dict[str, Any]] = Field(default_factory=list)
    writers: List[Dict[str, Any]] = Field(default_factory=list)
    notes: Optional[str] = None


class DependencyDAG(BaseModel):
    """Dependency graph between assets."""
    nodes: List[str]
    edges: List[Dict[str, str]]  # [{from, to, via}, ...]
    execution_order: List[List[str]] = Field(default_factory=list)  # [[level0], [level1], ...]
    cycles: List[List[str]] = Field(default_factory=list)


# ============================================
# Service
# ============================================

class TableImpactService:
    """
    Table Impact Service - Phase C
    
    Provides table-centric view of asset impacts:
    - Which assets READ from which tables (SELECT)
    - Which assets WRITE to which tables (INSERT, UPDATE, DELETE, MERGE)
    - Which columns are affected by each operation
    - Dependency graph (writer→reader relationships)
    
    Solves: "¿quién le pega a tabla X y de qué forma?"
    """
    
    def __init__(self, project_id: str, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.project_id = project_id
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
    
    async def analyze_impacts(self) -> Dict[str, Any]:
        """
        Analyzes all assets in project and registers table impacts.
        
        For each asset:
        1. Read metadata.logical_medulla
        2. Extract tables from each component (SqlCommand, OpenRowset, TableOrViewName)
        3. Determine operation (SELECT, INSERT, UPDATE, etc.)
        4. Infer columns_affected
        5. Register in utm_table_impacts
        
        Returns:
            Summary with stats
        """
        logger.info(
            f"[TableImpact] Starting analysis: project_id={self.project_id}",
            "TableImpact"
        )
        
        # Read all assets from project
        # Query assets (tenant isolation via project_id FK)
        query = (
            self.db.client.table("utm_objects")
            .select("*")
            .eq("project_id", self.project_id)
        )
        # NOTE: Using SELECT * instead of specific columns to avoid RLS column-level restrictions
        # Security maintained via project_id -> utm_projects.tenant_id FK
        
        assets = query.execute().data
        
        total_impacts = 0
        total_tables = set()
        errors = []
        
        for asset in assets:
            try:
                metadata = asset.get("metadata", {})
                medulla = metadata.get("logical_medulla", {})
                
                if not medulla:
                    continue
                
                # Extract impacts from all components
                impacts = self._extract_impacts_from_asset(asset, medulla)
                
                # Save to database
                for impact in impacts:
                    await self._save_impact(impact)
                    total_impacts += 1
                    total_tables.add(impact["full_name"])
            
            except Exception as e:
                asset_name = asset.get("source_name", asset.get("name", "unknown"))
                logger.error(
                    f"[TableImpact] Error analyzing {asset_name}: {e}",
                    "TableImpact"
                )
                errors.append({"asset": asset_name, "error": str(e)})
        
        logger.info(
            f"[TableImpact] Completed: {total_impacts} impacts on {len(total_tables)} tables",
            "TableImpact"
        )
        
        return {
            "status": "completed",
            "total_assets": len(assets),
            "total_impacts": total_impacts,
            "unique_tables": len(total_tables),
            "errors": errors
        }
    
    async def get_table_summary(self) -> List[TableSummary]:
        """
        Returns summary of ALL tables in project with reader/writer counts.
        
        Returns:
            List of TableSummary objects sorted by impact count
        """
        query = f"SELECT * FROM get_table_summary('{self.project_id}'::uuid)"
        
        result = self.db.client.rpc('get_table_summary', {'p_project_id': self.project_id}).execute()
        
        summaries = []
        for row in result.data:
            summaries.append(TableSummary(
                full_name=row["table_name"],
                readers_count=row["readers_count"],
                writers_count=row["writers_count"],
                total_impacts=row["total_impacts"],
                operations=row["operations"]
            ))
        
        return summaries
    
    async def get_table_detail(self, table_name: str) -> TableDetail:
        """
        Returns all impacts on a specific table.
        
        Args:
            table_name: Full table name (schema.table or table)
            
        Returns:
            TableDetail with readers and writers lists
        """
        result = self.db.client.rpc(
            'get_table_detail',
            {'p_project_id': self.project_id, 'p_table_name': table_name}
        ).execute()
        
        readers = []
        writers = []
        
        for row in result.data:
            impact = {
                "asset": row["asset_name"],
                "operation": row["operation"],
                "pattern": row["access_pattern"],
                "sql": row["sql_statement"],
                "columns": row["columns_affected"] or []
            }
            
            if row["is_source"]:
                readers.append(impact)
            if row["is_target"]:
                writers.append(impact)
        
        # Generate notes if multiple writers
        notes = None
        if len(writers) > 1:
            # Check if different writers affect same columns
            operations = [w["operation"] for w in writers]
            if "INSERT" in operations and "UPDATE" in operations:
                notes = "Multiple writers detected: INSERT + UPDATE. Verify if same columns are affected (potential conflict)."
            elif operations.count("UPDATE") > 1:
                notes = "Multiple UPDATE operations detected. Check columns_affected to determine if real conflict exists."
        
        return TableDetail(
            table_name=table_name,
            total_impacts=len(readers) + len(writers),
            readers=readers,
            writers=writers,
            notes=notes
        )
    
    async def build_dependency_dag(self) -> DependencyDAG:
        """
        Builds asset dependency DAG based on table impacts.
        
        Logic:
        - If Asset A WRITES to table X (INSERT/UPDATE/MERGE)
        - And Asset B READS from table X (SELECT)
        - Then: B depends on A (edge: A → B)
        
        Returns:
            DependencyDAG with nodes, edges, execution_order, and cycles
        """
        # Get dependency pairs from database function
        result = self.db.client.rpc(
            'get_dependency_pairs',
            {'p_project_id': self.project_id}
        ).execute()
        
        # Build graph structures
        all_assets = set()
        edges = []
        dependencies = defaultdict(set)  # asset → {assets it depends on}
        
        for row in result.data:
            from_asset = row["from_asset"]
            to_asset = row["to_asset"]
            via_table = row["via_table"]
            
            all_assets.add(from_asset)
            all_assets.add(to_asset)
            
            edges.append({
                "from": from_asset,
                "to": to_asset,
                "via": via_table
            })
            
            dependencies[to_asset].add(from_asset)
        
        # Detect cycles
        cycles = self._detect_cycles(all_assets, dependencies)
        
        # Calculate execution order (topological sort)
        execution_order = []
        if not cycles:
            execution_order = self._topological_sort(all_assets, dependencies)
        
        return DependencyDAG(
            nodes=sorted(list(all_assets)),
            edges=edges,
            execution_order=execution_order,
            cycles=cycles
        )
    
    # ============================================
    # Private Helper Methods
    # ============================================
    
    def _extract_impacts_from_asset(self, asset: Dict, medulla: Dict) -> List[Dict]:
        """
        Extracts all table impacts from an SSIS asset.
        
        Returns:
            List of dicts with utm_table_impacts structure
        """
        impacts = []
        
        # Iterate over all data flow components
        for comp in medulla.get("data_flow_logic", []):
            tables_and_ops = self._extract_tables_from_component(comp)
            
            for table_info in tables_and_ops:
                # Infer columns_affected
                columns = self._infer_columns_affected(
                    table_info.get("sql_statement", ""),
                    table_info["operation"]
                )
                
                impact = {
                    "tenant_id": self.tenant_id,
                    "project_id": self.project_id,
                    "schema_name": table_info.get("schema_name"),
                    "table_name": table_info["table_name"],
                    "full_name": table_info["full_name"],
                    "asset_id": asset["object_id"],
                    "asset_name": asset.get("source_name", asset.get("name", "unknown")),
                    "operation": table_info["operation"],
                    "access_pattern": table_info.get("access_pattern"),
                    "is_source": table_info["operation"] == "SELECT",
                    "is_target": table_info["operation"] in ["INSERT", "UPDATE", "MERGE", "DELETE", "TRUNCATE"],
                    "sql_statement": table_info.get("sql_statement"),
                    "columns_affected": columns
                }
                
                impacts.append(impact)
        
        return impacts
    
    def _extract_tables_from_component(self, comp: Dict) -> List[Dict]:
        """
        Extracts tables and operation from an SSIS component.
        
        Uses raw_properties (priority order):
        1. OpenRowset: direct table name (most reliable for SSIS)
        2. TableOrViewName: table/view name
        3. SqlCommand: full SQL query (only if not empty)
        4. SqlCommandVariable: variable containing SQL
        
        Returns:
            List of dicts: [{full_name, schema_name, table_name, operation, sql_statement, access_pattern}, ...]
        """
        props = comp.get("raw_properties", {})
        results = []
        
        # Determine operation
        operation = self._classify_operation(comp)
        
        # Extract table names by property type
        tables = []
        sql_statement = None
        
        # 1. OpenRowset (HIGHEST PRIORITY - most common in SSIS)
        if "OpenRowset" in props and props["OpenRowset"]:
            raw_table = props["OpenRowset"]
            tables = [self._clean_table_name(raw_table)]
        
        # 2. TableOrViewName (OLE DB Destination components)
        elif "TableOrViewName" in props and props["TableOrViewName"]:
            raw_table = props["TableOrViewName"]
            tables = [self._clean_table_name(raw_table)]
        
        # 3. SqlCommand (only if not empty)
        elif "SqlCommand" in props and props["SqlCommand"]:
            sql_statement = props["SqlCommand"]
            tables = self._extract_table_names(sql_statement)
        
        # 4. SqlCommandVariable (variable containing SQL)
        elif "SqlCommandVariable" in props and props["SqlCommandVariable"]:
            sql_statement = f"/* Variable: {props['SqlCommandVariable']} */"
            tables = []  # Cannot extract from variables at static analysis time
        
        # Create result for each detected table
        for table in tables:
            # Split schema and table
            parts = table.split('.')
            if len(parts) == 2:
                schema_name, table_name = parts
            else:
                schema_name = None
                table_name = parts[0]
            
            results.append({
                "full_name": table,
                "schema_name": schema_name,
                "table_name": table_name,
                "operation": operation,
                "sql_statement": sql_statement,
                "access_pattern": self._infer_access_pattern(comp, operation)
            })
        
        return results
    
    def _extract_table_names(self, sql: str) -> List[str]:
        """
        Extracts table names from SQL command using regex parsing.
        Supports patterns with/without schemas, with/without brackets.
        """
        if not sql:
            return []
        
        tables = set()
        
        # SQL patterns (capture optional schema + table)
        patterns = [
            # FROM table, FROM schema.table, FROM [dbo].[table]
            r'\bFROM\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
            # JOIN variants (INNER, LEFT, RIGHT, OUTER)
            r'\b(?:INNER\s+|LEFT\s+|RIGHT\s+|OUTER\s+)?JOIN\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
            # INTO table
            r'\bINTO\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
            # UPDATE table
            r'\bUPDATE\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
            # DELETE FROM table
            r'\bDELETE\s+FROM\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
            # INSERT INTO table
            r'\bINSERT\s+INTO\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, sql, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    schema = groups[0] if groups[0] else None
                    table = groups[1] if groups[1] else groups[0]
                    
                    if table:
                        # Format: schema.table or just table
                        full_name = f"{schema}.{table}" if schema else table
                        tables.add(full_name)
        
        # Clean names (remove residual brackets and reserved words)
        cleaned = []
        reserved_words = {'select', 'from', 'where', 'values', 'set', 'inner', 'left', 'right', 'outer', 'join'}
        
        for t in tables:
            cleaned_name = t.replace('[', '').replace(']', '').strip()
            if cleaned_name and cleaned_name.lower() not in reserved_words:
                cleaned.append(cleaned_name)
        
        return sorted(list(set(cleaned)))
    
    def _clean_table_name(self, raw_name: str) -> str:
        """
        Cleans table name: removes brackets and quotes.
        [dbo].[Table] → dbo.Table
        "dbo"."Table" → dbo.Table
        """
        cleaned = re.sub(r'[\[\]"]', '', raw_name)
        return cleaned.strip()
    
    def _classify_operation(self, comp: Dict) -> str:
        """
        Classifies operation based on:
        1. Component type (SOURCE_DB → SELECT, DESTINATION_DB → INSERT default)
        2. SqlCommand parsing (more precise)
        
        Returns:
            "SELECT" | "INSERT" | "UPDATE" | "DELETE" | "MERGE" | "TRUNCATE" | "UNKNOWN"
        """
        # FIXED: Use "type" field (not "intent") and check for _DB suffix
        comp_type = comp.get("type", "").upper()
        props = comp.get("raw_properties", {})
        
        # If SqlCommand exists and is not empty, parse it (most accurate)
        sql_command = props.get("SqlCommand", "")
        
        if sql_command and not sql_command.startswith("/*"):
            operation = self._parse_sql_operation(sql_command)
            if operation != "UNKNOWN":
                return operation
        
        # Fallback to inference by type (FIXED: use "type" instead of "intent")
        if "SOURCE" in comp_type:
            return "SELECT"
        elif "DESTINATION" in comp_type:
            return "INSERT"  # Default assumption for destinations
        
        return "UNKNOWN"
    
    def _parse_sql_operation(self, sql: str) -> str:
        """
        Parses SQL to determine operation type using sqlglot (if available) or regex fallback.
        """
        try:
            import sqlglot
            
            # Parse SQL (T-SQL dialect)
            parsed = sqlglot.parse_one(sql, dialect="tsql")
            
            if not parsed:
                return "UNKNOWN"
            
            # Determine statement type
            stmt_type = type(parsed).__name__
            
            if "Select" in stmt_type:
                return "SELECT"
            elif "Insert" in stmt_type:
                return "INSERT"
            elif "Update" in stmt_type:
                return "UPDATE"
            elif "Delete" in stmt_type:
                return "DELETE"
            elif "Merge" in stmt_type:
                return "MERGE"
            elif "Truncate" in stmt_type or "TRUNCATE" in sql.upper():
                return "TRUNCATE"
            
            return "UNKNOWN"
        
        except Exception as e:
            # Fallback to regex if sqlglot fails or not available
            sql_upper = sql.strip().upper()
            if sql_upper.startswith("SELECT"):
                return "SELECT"
            elif sql_upper.startswith("INSERT"):
                return "INSERT"
            elif sql_upper.startswith("UPDATE"):
                return "UPDATE"
            elif sql_upper.startswith("DELETE"):
                return "DELETE"
            elif sql_upper.startswith("MERGE"):
                return "MERGE"
            elif sql_upper.startswith("TRUNCATE"):
                return "TRUNCATE"
            
            return "UNKNOWN"
    
    def _infer_columns_affected(self, sql: str, operation: str) -> List[str]:
        """
        Infers which columns are affected by SQL operation.
        
        - UPDATE dbo.X SET col1 = ..., col2 = ... → ["col1", "col2"]
        - INSERT INTO dbo.X (col1, col2) → ["col1", "col2"]
        - SELECT col1, col2 FROM → ["col1", "col2"]
        - SELECT * FROM → ["*"]
        
        Uses sqlglot for precise parsing, regex fallback if unavailable.
        """
        if not sql:
            return []
        
        try:
            import sqlglot
            from sqlglot import expressions as exp
            
            parsed = sqlglot.parse_one(sql, dialect="tsql")
            columns = []
            
            if operation == "UPDATE":
                # Find SET clauses
                for node in parsed.find_all(exp.Update):
                    for set_item in node.find_all(exp.EQ):
                        if isinstance(set_item.left, exp.Column):
                            columns.append(set_item.left.name)
            
            elif operation == "INSERT":
                # Find columns in INSERT INTO table (col1, col2)
                for node in parsed.find_all(exp.Insert):
                    if node.this:
                        # Explicit columns
                        if hasattr(node, 'columns') and node.columns:
                            columns.extend([col.name for col in node.columns])
                        else:
                            # No explicit columns = all columns
                            columns = ["*"]
            
            elif operation == "SELECT":
                # Find columns in SELECT
                for node in parsed.find_all(exp.Select):
                    for col in node.expressions:
                        if isinstance(col, exp.Star):
                            return ["*"]
                        elif isinstance(col, exp.Column):
                            columns.append(col.name)
                        elif isinstance(col, exp.Alias):
                            # Alias (col AS alias) → use original name
                            if isinstance(col.this, exp.Column):
                                columns.append(col.this.name)
            
            elif operation == "DELETE":
                # DELETE affects entire row
                return ["*"]
            
            elif operation == "MERGE":
                # MERGE can UPDATE and INSERT
                update_cols = []
                insert_cols = []
                
                for node in parsed.find_all(exp.Merge):
                    # WHEN MATCHED THEN UPDATE SET ...
                    for update in node.find_all(exp.Update):
                        for set_item in update.find_all(exp.EQ):
                            if isinstance(set_item.left, exp.Column):
                                update_cols.append(set_item.left.name)
                    
                    # WHEN NOT MATCHED THEN INSERT ...
                    for insert in node.find_all(exp.Insert):
                        if hasattr(insert, 'columns') and insert.columns:
                            insert_cols.extend([col.name for col in insert.columns])
                
                columns = list(set(update_cols + insert_cols))
            
            return sorted(list(set(columns))) if columns else []
        
        except Exception as e:
            logger.warning(
                f"[TableImpact] Column inference error: {e}",
                "TableImpact"
            )
            return []
    
    def _infer_access_pattern(self, comp: Dict, operation: str) -> Optional[str]:
        """
        Infers access pattern based on component properties and operation.
        
        Returns:
            "FULL_LOAD" | "INCREMENTAL" | "LOOKUP" | "UPSERT" | "SCD" | None
        """
        props = comp.get("raw_properties", {})
        sql = props.get("SqlCommand", "").upper()
        
        # LOOKUP: specific SSIS component type
        if comp.get("type") == "Lookup":
            return "LOOKUP"
        
        # INCREMENTAL: WHERE clause with date/ID filter
        if "WHERE" in sql and any(word in sql for word in ["GETDATE", "DATE", "TIMESTAMP", ">"]):
            return "INCREMENTAL"
        
        # UPSERT/SCD: MERGE operation
        if operation == "MERGE":
            return "UPSERT"
        
        # FULL_LOAD: SELECT without WHERE or with WHERE 1=1
        if operation == "SELECT" and ("WHERE 1=1" in sql or "WHERE" not in sql):
            return "FULL_LOAD"
        
        return None
    
    async def _save_impact(self, impact: Dict) -> None:
        """
        Saves impact to utm_table_impacts using UPSERT.
        UNIQUE constraint prevents duplicates.
        """
        try:
            # Remove generated column (full_name is generated in DB)
            data = {k: v for k, v in impact.items() if k != 'full_name'}
            
            # UPSERT
            self.db.client.table("utm_table_impacts").upsert(data).execute()
        
        except Exception as e:
            logger.error(
                f"[TableImpact] Error saving impact: {e}",
                "TableImpact"
            )
            raise
    
    def _detect_cycles(self, nodes: Set[str], dependencies: Dict[str, Set[str]]) -> List[List[str]]:
        """
        Detects cycles in dependency graph using DFS.
        
        Returns:
            List of cycles (each cycle is list of asset names)
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in dependencies.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Cycle detected
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for node in nodes:
            if node not in visited:
                dfs(node)
        
        return cycles
    
    def _topological_sort(self, nodes: Set[str], dependencies: Dict[str, Set[str]]) -> List[List[str]]:
        """
        Sorts assets by execution levels using Kahn's algorithm.
        
        Returns:
            [[level0_assets], [level1_assets], ...] where:
            - Level 0: no dependencies (can execute first)
            - Level 1: depend only on level 0
            - ...
        """
        # Calculate in-degree (how many assets each one depends on)
        in_degree = {node: 0 for node in nodes}
        reverse_deps = defaultdict(list)  # asset → [assets that depend on it]
        
        for node, deps in dependencies.items():
            in_degree[node] = len(deps)
            for dep in deps:
                reverse_deps[dep].append(node)
        
        # Initialize with nodes having no dependencies (in-degree = 0)
        queue = deque([node for node in nodes if in_degree[node] == 0])
        execution_order = []
        
        while queue:
            # All nodes in current queue can execute in parallel
            current_level = []
            for _ in range(len(queue)):
                node = queue.popleft()
                current_level.append(node)
                
                # Reduce in-degree of neighbors
                for neighbor in reverse_deps[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            
            execution_order.append(sorted(current_level))
        
        return execution_order
