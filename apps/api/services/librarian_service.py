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

    def __init__(self, project_id: str, tenant_id: str = None, source_folder: str = None):
        self.project_id = project_id
        self.tenant_id = tenant_id
        self.base_path = PersistenceService.ensure_solution_dir(project_id, tenant_id=tenant_id)
        self.storage = PersistenceService.get_storage()
        
        target_folder = source_folder or PersistenceService.STAGE_SOURCE
        
        # [Fix] Discover Triage/Source folder case-insensitively (identical to DiscoveryService)
        self.inbound_path = None
        try:
            root_items = self.storage.list_files(self.base_path, recursive=False)
            
            # 1. Prioritize explicit target_folder
            for item in root_items:
                if item["type"] == "folder" and item["name"].lower() == target_folder.lower():
                    self.inbound_path = item["path"]
                    break
            
            # 2. Try fallbacks if target_folder not found
            if not self.inbound_path:
                triage_names = [PersistenceService.STAGE_SOURCE.lower(), PersistenceService.STAGE_TRIAGE.lower(), "source", "triage", "triaje", "inbound"]
                for item in root_items:
                    if item["type"] == "folder" and item["name"].lower() in triage_names:
                        # Prefer "source" if multiple are found
                        if not self.inbound_path or item["name"].lower() == PersistenceService.STAGE_SOURCE.lower():
                            self.inbound_path = item["path"]
                            
        except Exception as e:
            logger.warning(f"Librarian discovery error: {e}", "Librarian")

        if not self.inbound_path:
            self.inbound_path = f"{self.base_path.rstrip('/')}/{target_folder}"
        
        logger.info(f"Librarian resolved inbound path to: {self.inbound_path}", "Librarian")
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
            
            all_files = get_all_files(items)
            sql_files = [f for f in all_files if f["name"].lower().endswith((".sql", ".ddl"))]
            logger.info(f"Librarian found {len(sql_files)} DDL files out of {len(all_files)} total files in {self.inbound_path}", "Librarian")
            
            for sql_file in sql_files:
                try:
                    full_key = sql_file["path"]
                    sql_filename = sql_file["name"]
                    logger.info(f"[Librarian] Parsing DDL file: {sql_filename}", "Librarian")
                    
                    ddl_content = self.storage.read_file(full_key)
                    if isinstance(ddl_content, bytes):
                        ddl_content = ddl_content.decode("utf-8")
                    
                    # Pre-process content (remove GO, USE, etc.)
                    clean_ddl = self._preprocess_sql(ddl_content)
                    
                    # Map source_tech to valid SQLGlot dialect
                    dialect = self._map_source_tech_to_dialect(source_tech)
                    parsed_tables = self._parse_ddl(clean_ddl, dialect=dialect)
                    
                    for table_name, meta in parsed_tables.items():
                        # Tag each table with the SQL file it came from
                        meta["source_file"] = sql_filename
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

        # Robustly extract table name using sqlglot's find or dedicated properties
        # create_expr.this is the Schema, create_expr.this.this is the Table
        table_expr = create_expr.this.this
        if not isinstance(table_expr, exp.Table):
            # Fallback for complex structures
            table_expr = create_expr.find(exp.Table)
        
        if not table_expr:
            return None
            
        # Extract name, handle schema-qualified names (e.g. [dbo].[Table])
        table_name = table_expr.name
        if not table_name:
            # Last resort: try to get the string representation of the identifier
            table_name = str(table_expr.this) if hasattr(table_expr, 'this') else "UNKNOWN_TABLE"
        
        columns_dict = {} # Use a dictionary for easier lookup by column name
        table_constraints = [] # To store table-level constraints

        # First pass: Extract column definitions and column-level constraints
        for def_expr in create_expr.this.expressions:
            if isinstance(def_expr, exp.ColumnDef):
                col_name = def_expr.this.name
                col_type_str = def_expr.kind.sql() if def_expr.kind else "UNKNOWN"
                
                is_pk = False
                nullable = True
                is_foreign_key = False # Initialize for column-level FKs

                if def_expr.args.get("constraints"):
                    for constraint in def_expr.args.get("constraints"):
                        if isinstance(constraint.kind, exp.PrimaryKeyColumnConstraint):
                            is_pk = True
                        # Column-level NOT NULL constraint
                        if isinstance(constraint.kind, exp.NotNullColumnConstraint):
                            nullable = False
                
                target_type = self._map_type(col_type_str)
                
                columns_dict[col_name] = {
                    "name": col_name,
                    "source_type": col_type_str,
                    "target_type": target_type,
                    "is_pk": is_pk,
                    "nullable": nullable,
                    "is_foreign_key": is_foreign_key # Add FK flag
                }
            elif isinstance(def_expr, exp.Constraint):
                # Named constraint (e.g., CONSTRAINT PK_xxx PRIMARY KEY (...))
                table_constraints.append(def_expr)
            elif isinstance(def_expr, exp.PrimaryKey):
                # Unnamed table-level PRIMARY KEY (e.g., PRIMARY KEY (col1, col2))
                for pk_col_expr in def_expr.expressions:
                    col_name = pk_col_expr.name
                    if col_name in columns_dict:
                        columns_dict[col_name]["is_pk"] = True
            elif isinstance(def_expr, exp.ForeignKey):
                # Unnamed table-level FOREIGN KEY
                for fk_col_expr in def_expr.expressions:
                    col_name = fk_col_expr.name
                    if col_name in columns_dict:
                        columns_dict[col_name]["is_foreign_key"] = True

        # Second pass: Apply named table-level constraints (CONSTRAINT PK_xxx PRIMARY KEY (...))
        for constraint_expr in table_constraints:
            if isinstance(constraint_expr.kind, exp.PrimaryKey):
                # Table-level PRIMARY KEY (e.g., CONSTRAINT PK_xxx PRIMARY KEY (col1, col2))
                for pk_col_expr in constraint_expr.kind.expressions:
                    col_name = pk_col_expr.name
                    if col_name in columns_dict:
                        columns_dict[col_name]["is_pk"] = True
            elif isinstance(constraint_expr.kind, exp.ForeignKey):
                # Table-level FOREIGN KEY (e.g., CONSTRAINT FK_xxx FOREIGN KEY (col1) REFERENCES ...)
                for fk_col_expr in constraint_expr.kind.expressions:
                    col_name = fk_col_expr.name
                    if col_name in columns_dict:
                        columns_dict[col_name]["is_foreign_key"] = True
        
        # Convert columns_dict back to a list
        columns = list(columns_dict.values())

        return {
            "name": table_name,
            "columns": columns,
            "constraints": {}, # Placeholder for general constraints, not column-specific flags
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
        """Cleans SQL content to be parser-friendly by removing huge DML blocks and useless commands."""
        # 1. Remove [cite: ...] markers (from document export tools)
        sql_content = re.sub(r'\[cite:[^\]]*\]', '', sql_content)
        
        # 2. Sequential Filter (Fast line-by-line)
        lines = sql_content.splitlines()
        cleaned_lines = []
        
        # Keywords that indicate we should skip the line or start skipping a block
        # We target DML and PL/SQL blocks which the Librarian doesn't need for schema mapping.
        skip_line_keywords = {
            "INSERT INTO", "UPDATE ", "DELETE FROM", "VALUES", "SET ", 
            "COMMIT", "LOCK TABLES", "UNLOCK TABLES", "/*!", 
            "DELIMITER", "DROP PROCEDURE", "DROP FUNCTION", "DROP TRIGGER",
            "SET @", "SET NAMES", "SET CHARACTER"
        }
        
        block_start_keywords = {
            "CREATE PROCEDURE", "CREATE FUNCTION", "CREATE TRIGGER", "CREATE DEFINER",
            "CREATE OR REPLACE PROCEDURE", "CREATE OR REPLACE FUNCTION",
            "CREATE PROCEDURE IF NOT EXISTS", "CREATE FUNCTION IF NOT EXISTS"
        }
        
        in_large_block = False
        in_plsql_block = False
        
        for line in lines:
            stripped = line.strip()
            upper_stripped = stripped.upper()
            
            # 1. Skip empty lines
            if not stripped:
                continue
                
            # 2. Block Termination (Check first to ensure we close blocks)
            if in_plsql_block:
                if upper_stripped == "END" or upper_stripped.startswith("END;") or "$$" in upper_stripped or (upper_stripped.startswith("END") and upper_stripped.endswith(";")):
                    in_plsql_block = False
                continue

            if in_large_block:
                if upper_stripped.endswith(";"):
                    in_large_block = False
                continue

            # 3. Skip T-SQL specific flow/context commands
            if upper_stripped == "GO" or upper_stripped.startswith("USE "):
                continue
            
            # 4. Skip MySQL comments and variable assignments that might break parser
            if stripped.startswith("@") or upper_stripped.startswith("SET @"):
                continue

            # 5. Normalize comments (ensure space after --)
            if stripped.startswith("--") and not stripped.startswith("-- "):
                line = "-- " + line[2:]
                stripped = line.strip()
                upper_stripped = stripped.upper()

            # 6. Detect start of blocks
            if any(upper_stripped.startswith(k) for k in block_start_keywords):
                in_plsql_block = True
                continue

            # MySQL/MariaDB routines sometimes reach here without explicit CREATE line
            # after preprocessing delimiters/comments. Treat DECLARE blocks as procedural.
            if upper_stripped.startswith("DECLARE "):
                in_plsql_block = True
                continue

            if any(upper_stripped.startswith(k) for k in skip_line_keywords):
                if not upper_stripped.endswith(";"):
                    in_large_block = True
                continue

            # 7. Additional check for lines that are just data tuples in a multi-line INSERT
            if stripped.startswith("(") and (stripped.endswith(",") or stripped.endswith(");")):
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

        # MySQL/MariaDB projects often include routines and DELIMITER blocks in the same
        # files as CREATE TABLE statements. Parsing only CREATE TABLE statements first
        # avoids noisy false parse errors while keeping schema extraction deterministic.
        if dialect == "mysql":
            recovered = self._parse_create_table_statements(ddl_content, dialect)
            if recovered:
                logger.debug(
                    f"MySQL CREATE TABLE parser extracted {len(recovered)} table(s)",
                    "Librarian",
                )
                tables.update(recovered)
                return tables

        try:
            for expression in sqlglot.parse(ddl_content, read=dialect):
                if isinstance(expression, exp.Create):
                    table_def = self._extract_table_info(expression)
                    if table_def:
                        tables[table_def["name"]] = table_def
        except Exception as e:
            logger.warning(f"SQLGlot parse warning ({dialect}): {e}", "Librarian")

            # For MySQL/MariaDB mixed scripts (DDL + routines), salvage CREATE TABLE statements
            # individually so one invalid routine block does not drop all table metadata.
            if dialect == "mysql":
                recovered = self._parse_create_table_statements(ddl_content, dialect)
                if recovered:
                    logger.info(
                        f"Recovered {len(recovered)} table(s) from MySQL statement-level fallback",
                        "Librarian",
                    )
                    tables.update(recovered)

            # Optional: Fallback to tsql if oracle failed
            if not tables and dialect == "oracle":
                logger.debug("Falling back to TSQL parser...", "Librarian")
                try:
                    for expression in sqlglot.parse(ddl_content, read="tsql"):
                        if isinstance(expression, exp.Create):
                            table_def = self._extract_table_info(expression)
                            if table_def:
                                tables[table_def["name"]] = table_def
                except Exception:
                    pass

        return tables

    def _parse_create_table_statements(self, ddl_content: str, dialect: str) -> Dict[str, Any]:
        """Fallback parser that extracts CREATE TABLE blocks and parses them independently."""
        recovered_tables: Dict[str, Any] = {}

        statements = re.findall(r"(?is)\bCREATE\s+TABLE\b.*?;", ddl_content)
        for stmt in statements:
            try:
                expr = sqlglot.parse_one(stmt, read=dialect)
                if isinstance(expr, exp.Create):
                    table_def = self._extract_table_info(expr)
                    if table_def:
                        recovered_tables[table_def["name"]] = table_def
            except Exception:
                # Ignore statement-level failures and continue with the next table block.
                continue

        return recovered_tables
