import os
import glob
import re
import json
import sqlglot
from sqlglot import exp
from typing import Dict, Any, List
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
    from apps.api.services.persistence_service import PersistenceService
except ImportError:
    try:
        from services.persistence_service import PersistenceService
    except ImportError:
        from .persistence_service import PersistenceService

class LibrarianService:
    """
    The Librarian: Context Awareness Agent.
    Scans DDLs and Flat Files to build a 'Single Source of Truth' (schema_reference.json).
    """

    def __init__(self, project_id: str, tenant_id: str = None):
        # We assume project_id maps to a folder name or we resolve it.
        # For this implementation, we assume the persistence service has already ensured the folder exists.
        # But here we need to know the path.
        # TODO: Refactor to use PersistenceService to resolve paths cleanly.
        self.project_id = project_id
        # Strict I/O: Data flows IN from 'Data' folder
        self.base_path = PersistenceService.ensure_solution_dir(project_id, tenant_id=tenant_id)
        self.data_path = os.path.join(self.base_path, "Data")
        self.output_path = os.path.join(self.base_path, "Output")
        
        # Ensure Output exists
        os.makedirs(self.output_path, exist_ok=True)

        # Load platform spec using the dedicated class
        self.platform_spec_loader = PlatformSpec()
        self.platform_spec = self.platform_spec_loader.load_platform_spec()

    def scan_project(self) -> Dict[str, Any]:
        """Main entry point: Scans DDLs and returns the Schema Reference."""
        logger.info(f"Scanning project {self.project_id}...", "Librarian")
        
        schema_reference = {
            "project_id": self.project_id,
            "tables": {},
            "flat_files": []
        }

        # 1. Scan SQL DDLs
        sql_files = glob.glob(os.path.join(self.data_path, "*.sql"))
        logger.info(f"Found {len(sql_files)} SQL files.", "Librarian")
        
        for sql_file in sql_files:
            try:
                logger.debug(f"Parsing {os.path.basename(sql_file)}...", "Librarian")
                with open(sql_file, "r") as f:
                    ddl_content = f.read()
                
                # Pre-process content (remove GO, USE, etc.)
                clean_ddl = self._preprocess_sql(ddl_content)
                parsed_tables = self._parse_ddl(clean_ddl)
                
                for table_name, meta in parsed_tables.items():
                    schema_reference["tables"][table_name] = meta
                    
            except Exception as e:
                logger.error(f"Error parsing {sql_file}: {e}", "Librarian")

        # 2. Save Output
        output_file = os.path.join(self.output_path, "schema_reference.json")
        with open(output_file, "w") as f:
            json.dump(schema_reference, f, indent=2)
            
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

    def _parse_ddl(self, ddl_content: str) -> Dict[str, Any]:
        """Parses DDL string and extracts table info."""
        tables = {}
        try:
            for expression in sqlglot.parse(ddl_content, read="tsql"):
                if isinstance(expression, exp.Create):
                    table_def = self._extract_table_info(expression)
                    if table_def:
                        tables[table_def["name"]] = table_def
        except Exception as e:
            logger.error(f"SQLGlot Parse Error: {e}", "Librarian")
        return tables
