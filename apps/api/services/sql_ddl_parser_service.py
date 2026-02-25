"""
SQL DDL Parser Service
Parses SQL DDL files (CREATE TABLE) and extracts column metadata
"""
import re
from typing import Dict, List, Any, Optional
from uuid import uuid4

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


class SQLDDLParserService:
    """
    Parses SQL DDL files to extract table and column metadata
    """
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
    
    def parse_sql_content(self, sql_content: str) -> List[Dict[str, Any]]:
        """
        Parse SQL DDL content and extract table definitions
        
        Returns list of tables with their columns:
        [
            {
                "table_name": "DimEmployee",
                "columns": [
                    {
                        "column_name": "empkey",
                        "data_type": "INT",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                        "is_nullable": False
                    },
                    ...
                ]
            },
            ...
        ]
        """
        tables = []
        
        # Regex to find CREATE TABLE statements
        # Pattern handles: CREATE TABLE name ( ... );
        create_table_pattern = r'CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);'
        
        matches = re.finditer(create_table_pattern, sql_content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            table_name = match.group(1)
            columns_block = match.group(2)
            
            columns = self._parse_columns(columns_block)
            
            if columns:
                tables.append({
                    "table_name": table_name,
                    "columns": columns
                })
        
        return tables
    
    def _parse_columns(self, columns_block: str) -> List[Dict[str, Any]]:
        """
        Parse column definitions from CREATE TABLE block
        """
        columns = []
        
        # Split by comma (but be careful with nested commas in constraints)
        lines = columns_block.split('\n')
        current_line = ""
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            
            current_line += " " + line
            
            # Check if this is a complete column definition
            if ',' in current_line or ')' in current_line:
                # Process the column
                col_def = current_line.strip().rstrip(',').strip()
                
                if col_def:
                    column_info = self._parse_column_definition(col_def)
                    if column_info:
                        columns.append(column_info)
                
                current_line = ""
        
        return columns
    
    def _parse_column_definition(self, col_def: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single column definition
        
        Examples:
            empkey INT IDENTITY(1,1) PRIMARY KEY
            fullname NVARCHAR(31)
            unitprice MONEY
            orderid INT,
        """
        # Skip table-level constraints
        if col_def.upper().startswith('PRIMARY KEY') or \
           col_def.upper().startswith('FOREIGN KEY') or \
           col_def.upper().startswith('CONSTRAINT') or \
           col_def.upper().startswith('UNIQUE'):
            return None
        
        # Pattern: column_name data_type [constraints]
        parts = col_def.split()
        
        if len(parts) < 2:
            return None
        
        column_name = parts[0]
        data_type = parts[1]
        
        # Extract data type with potential size: NVARCHAR(31), NUMERIC(4,3)
        data_type_match = re.match(r'(\w+)(\([^)]+\))?', data_type)
        if data_type_match:
            base_type = data_type_match.group(1)
            type_size = data_type_match.group(2) or ""
            data_type = base_type + type_size
        
        # Check for PRIMARY KEY
        is_primary_key = 'PRIMARY KEY' in col_def.upper()
        
        # Check for FOREIGN KEY (rare in column def, usually separate constraint)
        is_foreign_key = 'FOREIGN KEY' in col_def.upper() or 'REFERENCES' in col_def.upper()
        
        # Check for NULL/NOT NULL
        is_nullable = True  # Default
        if 'NOT NULL' in col_def.upper():
            is_nullable = False
        elif 'PRIMARY KEY' in col_def.upper():
            is_nullable = False  # PKs are implicitly NOT NULL
        
        return {
            "column_name": column_name,
            "data_type": data_type,
            "is_primary_key": is_primary_key,
            "is_foreign_key": is_foreign_key,
            "is_nullable": is_nullable,
            "cardinality_ratio": None  # Will be computed later if needed
        }
    
    async def parse_and_save(self, project_id: str, asset_id: str, sql_content: str) -> Dict[str, Any]:
        """
        Parse SQL DDL and save columns to utm_asset_columns
        
        Returns:
            {
                "tables_parsed": 3,
                "columns_saved": 25,
                "tables": ["DimEmployee", "DimCategory", ...]
            }
        """
        logger.info(f"[SQLDDLParser] Parsing SQL DDL for asset: {asset_id}", "SQLDDLParser")
        
        # Parse SQL content
        tables = self.parse_sql_content(sql_content)
        
        if not tables:
            logger.warning(f"[SQLDDLParser] No CREATE TABLE statements found in asset {asset_id}", "SQLDDLParser")
            return {
                "tables_parsed": 0,
                "columns_saved": 0,
                "tables": []
            }
        
        total_columns_saved = 0
        table_names = []
        
        for table in tables:
            table_name = table["table_name"]
            columns = table["columns"]
            table_names.append(table_name)
            
            logger.info(f"[SQLDDLParser] Table '{table_name}' has {len(columns)} columns", "SQLDDLParser")
            
            # Save columns to utm_asset_columns
            for col in columns:
                try:
                    self.db.client.table("utm_asset_columns").insert({
                        "project_id": project_id,
                        "asset_id": asset_id,
                        "column_name": col["column_name"],
                        "data_type": col["data_type"],
                        "is_primary_key": col["is_primary_key"],
                        "is_foreign_key": col["is_foreign_key"],
                        "is_nullable": col["is_nullable"],
                        "cardinality_ratio": col.get("cardinality_ratio")
                    }).execute()
                    
                    total_columns_saved += 1
                
                except Exception as e:
                    logger.error(f"[SQLDDLParser] Error saving column {col['column_name']}: {e}", "SQLDDLParser")
        
        logger.info(
            f"[SQLDDLParser] Parsed {len(tables)} tables, saved {total_columns_saved} columns",
            "SQLDDLParser"
        )
        
        return {
            "tables_parsed": len(tables),
            "columns_saved": total_columns_saved,
            "tables": table_names
        }
    
    async def parse_sql_assets_in_project(self, project_id: str) -> Dict[str, Any]:
        """
        Find all SQL DDL assets (category='soporte') in project and parse them
        
        Returns:
            {
                "assets_parsed": 2,
                "total_tables": 15,
                "total_columns": 120,
                "assets": [
                    {
                        "asset_id": "...",
                        "asset_name": "destino_DW.sql",
                        "tables_parsed": 8,
                        "columns_saved": 60
                    },
                    ...
                ]
            }
        """
        logger.info(f"[SQLDDLParser] Starting SQL DDL parsing for project: {project_id}", "SQLDDLParser")
        
        # Get SQL assets with category='soporte'
        assets_result = self.db.client.table("utm_objects") \
            .select("object_id, source_name, source_path, raw_content") \
            .eq("project_id", project_id) \
            .eq("category", "soporte") \
            .execute()
        
        if not assets_result.data:
            logger.info(f"[SQLDDLParser] No SQL DDL assets found (category='soporte')", "SQLDDLParser")
            return {
                "assets_parsed": 0,
                "total_tables": 0,
                "total_columns": 0,
                "assets": []
            }
        
        import boto3
        import os
        
        # R2 config
        r2_client = boto3.client(
            's3',
            endpoint_url=os.getenv("R2_ENDPOINT_URL"),
            aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY")
        )
        bucket = os.getenv("R2_BUCKET_NAME")
        
        results = []
        total_tables = 0
        total_columns = 0
        
        for asset in assets_result.data:
            asset_id = asset["object_id"]
            asset_name = asset["source_name"]
            source_path = asset.get("source_path")
            raw_content = asset.get("raw_content")
            
            # Get SQL content (prefer raw_content, fallback to R2)
            sql_content = raw_content
            
            if not sql_content and source_path:
                try:
                    response = r2_client.get_object(Bucket=bucket, Key=source_path)
                    sql_content = response['Body'].read().decode('utf-8', errors='ignore')
                except Exception as e:
                    logger.error(f"[SQLDDLParser] Error downloading {asset_name}: {e}", "SQLDDLParser")
                    continue
            
            if not sql_content:
                logger.warning(f"[SQLDDLParser] No content found for {asset_name}", "SQLDDLParser")
                continue
            
            # Parse and save
            result = await self.parse_and_save(project_id, asset_id, sql_content)
            
            results.append({
                "asset_id": asset_id,
                "asset_name": asset_name,
                "tables_parsed": result["tables_parsed"],
                "columns_saved": result["columns_saved"],
                "tables": result["tables"]
            })
            
            total_tables += result["tables_parsed"]
            total_columns += result["columns_saved"]
        
        logger.info(
            f"[SQLDDLParser] Completed: {len(results)} assets, {total_tables} tables, {total_columns} columns",
            "SQLDDLParser"
        )
        
        return {
            "assets_parsed": len(results),
            "total_tables": total_tables,
            "total_columns": total_columns,
            "assets": results
        }
