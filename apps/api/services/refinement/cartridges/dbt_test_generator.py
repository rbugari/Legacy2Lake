"""
dbt Schema Tests Generator

This module provides test generation capabilities for dbt models.
Generated tests ensure data quality in the Silver layer.
"""

from typing import Dict, Any, List
from pathlib import Path

class DbtTestGenerator:
    """Generates dbt schema.yml with data quality tests."""
    
    @staticmethod
    def generate_schema_tests(table_metadata: Dict[str, Any]) -> str:
        """
        Generates dbt schema.yml with tests for a Silver model.
        
        Args:
            table_metadata: Dictionary containing:
                - output_table_name: Name of the model
                - pk_columns: List of primary key columns
                - columns: Optional list of all columns with metadata
                
        Returns:
            YAML string for schema.yml
            
        Example:
            >>> metadata = {
            ...     "output_table_name": "stg_customers",
            ...     "pk_columns": ["customer_id"],
            ...     "columns": [
            ...         {"name": "customer_id", "type": "integer", "nullable": False},
            ...         {"name": "email", "type": "string", "nullable": False}
            ...     ]
            ... }
            >>> DbtTestGenerator.generate_schema_tests(metadata)
        """
        model_name = table_metadata.get("output_table_name", "model")
        pk_columns = table_metadata.get("pk_columns", ["id"])
        all_columns = table_metadata.get("columns", [])
        
        # Ensure pk_columns is a list
        if isinstance(pk_columns, str):
            pk_columns = [pk_columns]
        
        yaml_content = f"""version: 2

models:
  - name: {model_name}
    description: "Silver layer model for {model_name} - cleaned and deduplicated"
    
    columns:
"""
        
        # Add PK column tests
        for pk in pk_columns:
            yaml_content += f"""      - name: {pk}
        description: "Primary key column"
        tests:
          - not_null
          - unique
"""
        
        # Add other column tests if available
        if all_columns:
            for col in all_columns:
                col_name = col.get("name", "")
                if col_name in pk_columns:
                    continue  # Already added
                    
                col_tests = []
                if not col.get("nullable", True):
                    col_tests.append("not_null")
                
                # Add accepted_values test for known enum columns
                if col.get("type") == "enum" and col.get("values"):
                    values_str = ", ".join([f"'{v}'" for v in col["values"]])
                    col_tests.append(f"accepted_values:\\n              values: [{values_str}]")
                
                if col_tests:
                    yaml_content += f"""      - name: {col_name}
        description: "{col.get('description', f'Column {col_name}')}"
        tests:
"""
                    for test in col_tests:
                        if ":" in test:  # Multi-line test like accepted_values
                            yaml_content += f"          - {test}\\n"
                        else:
                            yaml_content += f"          - {test}\\n"
        
        # Add standard audit column tests
        yaml_content += """      - name: _ingested_at
        description: "Timestamp of data ingestion"
        tests:
          - not_null

    # Model-level tests
    tests:
      - dbt_utils.recency:
          datepart: day
          field: _ingested_at
          interval: 2
          config:
            severity: warn
"""
        
        return yaml_content
    
    @staticmethod
    def generate_source_tests(source_name: str, tables: List[str]) -> str:
        """
        Generates dbt sources.yml for Bronze layer sources.
        
        Args:
            source_name: Name of the source system (e.g., 'legacy_erp')
            tables: List of table names in the source
            
        Returns:
            YAML string for sources.yml
        """
        yaml_content = f"""version: 2

sources:
  - name: {source_name}
    description: "Legacy source system data"
    database: "{{{{ target.database }}}}"
    schema: bronze_raw
    
    tables:
"""
        
        for table in tables:
            yaml_content += f"""      - name: {table}
        description: "Raw {table} data from source"
        tests:
          - dbt_utils.recency:
              datepart: hour
              field: _ingestion_timestamp
              interval: 24
              config:
                severity: warn
"""
        
        return yaml_content
