import os
import glob
import re
import json
import sqlglot
from sqlglot import exp
from typing import Dict, Any, List, Optional
try:
    from apps.api.config.platform_spec import PlatformSpec
except ImportError:
    try:
        from config.platform_spec import PlatformSpec
    except ImportError:
        from ..config.platform_spec import PlatformSpec

try:
    from apps.api.utils.logger import logger
except ImportError:
    try:
        from utils.logger import logger
    except ImportError:
        from ..utils.logger import logger

try:
    from apps.api.services.persistence_service import PersistenceService, SupabasePersistence
except ImportError:
    try:
        from services.persistence_service import PersistenceService, SupabasePersistence
    except ImportError:
        from .persistence_service import PersistenceService, SupabasePersistence

class LibrarianService:
    """
    The Librarian: Context Awareness Agent.
    Scans DDLs and Flat Files to build a 'Single Source of Truth' (schema_reference.json).
    """

    def __init__(self, project_id: str, tenant_id: str = None):
        self.project_id = project_id
        self.tenant_id = tenant_id
        # Strict I/O: Data flows IN from normalized project path
        self.base_path = PersistenceService.ensure_solution_dir(project_id, tenant_id=tenant_id)
        # In the new flow, we read from STAGE_TRIAGE where files were uploaded
        self.inbound_path = f"{self.base_path.rstrip('/')}/{PersistenceService.STAGE_TRIAGE}"
        self.output_path = f"{self.base_path.rstrip('/')}/{PersistenceService.STAGE_DRAFTING}"
        
        self.storage = PersistenceService.get_storage()

        # Load platform spec using the dedicated class
        self.platform_spec_loader = PlatformSpec()
        self.platform_spec = self.platform_spec_loader.load_platform_spec()
    
    def _map_source_tech_to_dialect(self, source_tech: Optional[str]) -> Optional[str]:
        """Maps project source_tech to valid SQLGlot dialect."""
        if not source_tech:
            return None
        
        tech_lower = source_tech.lower()
        
        # Explicit mapping to valid SQLGlot dialects
        dialect_map = {
            "microsoft ssis": "tsql",
            "sql server": "tsql",
            "sqlserver": "tsql",
            "mssql": "tsql",
            "t-sql": "tsql",
            "tsql": "tsql",
            "oracle": "oracle",
            "mysql": "mysql",
            "postgresql": "postgres",
            "postgres": "postgres",
            "databricks": "spark",
            "apache spark": "spark",
            "snowflake": "snowflake"
        }
        
        mapped_dialect = dialect_map.get(tech_lower)
        
        if mapped_dialect:
            logger.debug(f"Mapped source_tech '{source_tech}' → dialect '{mapped_dialect}'", "Librarian")
        else:
            logger.warning(f"Unknown source_tech '{source_tech}', will use auto-detection", "Librarian")
        
        return mapped_dialect

    async def scan_project(self) -> Dict[str, Any]:
        """Main entry point: Scans DDLs using StorageProvider."""
        logger.info(f"Scanning project {self.project_id} in {self.inbound_path}...", "Librarian")
        
        # Resolve Dialect from DB (Source Tech)
        source_tech = None
        try:
             # Instantiate Persistence to get metadata
             db = SupabasePersistence(tenant_id=self.tenant_id)
             # Resolve UUID if needed
             p_uuid = self.project_id
             if len(p_uuid) < 30: # If name provided, try to get ID, or rely on ensure_solution_dir logic
                 # For metadata, we need UUID or we search by name
                 try:
                     u = await db.get_project_id_by_name(self.project_id)
                     if u: p_uuid = u
                 except: pass
                 
             meta = await db.get_project_metadata(p_uuid)
             if meta:
                 # Check settings then config
                 source_tech = meta.get("settings", {}).get("source_tech") or meta.get("config", {}).get("source_tech")
                 
             if source_tech:
                 logger.info(f"Librarian detected configured source tech: {source_tech}", "Librarian")
        except Exception as e:
             logger.warning(f"Librarian could not fetch project metadata: {e}", "Librarian")

        schema_reference = {
            "project_id": self.project_id,
            "tables": {},
            "flat_files": []
        }

        # 1. Scan SQL DDLs via Storage
        try:
            items = self.storage.list_files(self.inbound_path, recursive=True)
            # Flatten files from tree
            def get_all_files(nodes):
                files = []
                for n in nodes:
                    if n["type"] == "folder" and n.get("children"):
                        files.extend(get_all_files(n["children"]))
                    elif n["type"] == "file":
                        files.append(n)
                return files
            
            sql_files = [f for f in get_all_files(items) if f["name"].lower().endswith(".sql")]
            logger.info(f"Found {len(sql_files)} SQL files in storage.", "Librarian")
            
            for sql_file in sql_files:
                try:
                    full_key = sql_file["path"]
                    logger.debug(f"Parsing {sql_file['name']} from {full_key}...", "Librarian")
                    
                    ddl_content = self.storage.read_file(full_key)
                    if isinstance(ddl_content, bytes):
                        ddl_content = ddl_content.decode("utf-8")
                    
                    # Pre-process content (remove GO, USE, etc.)
                    clean_ddl = self._preprocess_sql(ddl_content)
                    
                    # Map source_tech to valid SQLGlot dialect
                    dialect = self._map_source_tech_to_dialect(source_tech)
                    parsed_tables = self._parse_ddl(clean_ddl, dialect=dialect)
                    
                    for table_name, meta in parsed_tables.items():
                        schema_reference["tables"][table_name] = meta
                        
                except Exception as e:
                    logger.error(f"Error parsing {sql_file['name']}: {e}", "Librarian")
        except Exception as e:
            logger.error(f"Error listing storage files: {e}", "Librarian")

        # 2. Save Output to Storage (Drafting folder)
        output_key = f"{self.output_path.rstrip('/')}/schema_reference.json"
        self.storage.save_file(output_key, json.dumps(schema_reference, indent=2))
            
        return schema_reference

    def _extract_table_info(self, create_expr: exp.Create) -> Dict[str, Any]:
        """Extracts details from a CREATE TABLE expression."""
        if not create_expr.this or not isinstance(create_expr.this, exp.Schema):
            return None

        table_name = create_expr.this.this.this.this # Table name identifier
        # Safe extraction of schema/db if present
        # schema = create_expr.this.this.args.get("db") 
        
        columns = []
        constraints = {}
        
        # Iterate schema definitions (columns and constraints)
        for def_expr in create_expr.this.expressions:
            if isinstance(def_expr, exp.ColumnDef):
                col_name = def_expr.this.this
                # Use .sql() to get the string representation (e.g., "INT", "VARCHAR(25)")
                col_type_str = def_expr.kind.sql() if def_expr.kind else "UNKNOWN"
                
                # Check constraints in column definition
                is_pk = False
                is_identity = False
                nullable = True
                
                if def_expr.args.get("constraints"):
                    for constraint in def_expr.args.get("constraints"):
                        if isinstance(constraint.kind, exp.PrimaryKeyColumnConstraint):
                            is_pk = True
                        if isinstance(constraint.kind, exp.NotNullColumnConstraint):
                            nullable = False
                        # Identity check might vary by dialect, simplified here
                        # In sqlglot, identity often parses as a property or constraint
                        
                # Dirty check for IDENTITY strings in raw type or constraints if sqlglot didn't catch specific identity node
                # Or look at properties
                
                target_type = self._map_type(col_type_str)
                
                columns.append({
                    "name": col_name,
                    "source_type": col_type_str,
                    "target_type": target_type,
                    "is_pk": is_pk,
                    "nullable": nullable
                })

        return {
            "name": table_name,
            "columns": columns,
            "constraints": constraints,
            # Placeholder for logic inference
            "business_logic": "Standard Table" 
        }

    def _map_type(self, source_type: str) -> str:
        """Maps source SQL type to Target Spark type using platform_spec."""
        mapping = self.platform_spec.get("qa_rules", {}).get("data_type_mapping", {})
        # Simple lookup, normalize to lower case for key
        # Handle parameterized types like decimal(10,2) -> decimal({p},{s}) logic later
        # For now, direct string match or fallback
        
        # Strip precision/scale for lookup (e.g. varchar(25) -> varchar)
        base_type = source_type.split("(")[0].lower()
        
        if base_type in mapping:
            return mapping[base_type]
        
        return "STRING" # Default fallback

    def _preprocess_sql(self, sql_content: str) -> str:
        """Cleans SQL content to be parser-friendly."""
        lines = sql_content.splitlines()
        cleaned_lines = []
        for line in lines:
            stripped = line.strip().upper()
            if stripped == "GO":
                continue
            if stripped.startswith("USE "):
                continue
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    def _parse_ddl(self, ddl_content: str, dialect: str = None) -> Dict[str, Any]:
        """Parses DDL string and extracts table info."""
        tables = {}
        
        # Determine Dialect
        if not dialect:
            dialect = "tsql"
            upper = ddl_content.upper()
            # Oracle indicators: VARCHAR2, NUMBER, PLS_INTEGER, CREATE OR REPLACE
            if "VARCHAR2" in upper or "NUMBER" in upper or "CREATE OR REPLACE" in upper:
                dialect = "oracle"
        
        logger.debug(f"Parsing with dialect: {dialect}", "Librarian")

        try:
            for expression in sqlglot.parse(ddl_content, read=dialect):
                if isinstance(expression, exp.Create):
                    table_def = self._extract_table_info(expression)
                    if table_def:
                        tables[table_def["name"]] = table_def
        except Exception as e:
            logger.error(f"SQLGlot Parse Error ({dialect}): {e}", "Librarian")
            # Optional: Fallback to tsql if oracle failed?
            if dialect == "oracle":
                 logger.debug("Falling back to TSQL parser...", "Librarian")
                 try:
                    for expression in sqlglot.parse(ddl_content, read="tsql"):
                        if isinstance(expression, exp.Create):
                            table_def = self._extract_table_info(expression)
                            if table_def:
                                tables[table_def["name"]] = table_def
                 except: pass

        return tables
