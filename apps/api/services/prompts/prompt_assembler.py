"""
Prompt Assembler - v4.0 Zero-Hardcode Core

Assembles dynamic prompts with context injection.
Replaces variable placeholders with actual values.

Features:
- Template variable substitution ({{variable}})
- Context enrichment
- JSON schema injection
- Column metadata injection
- Conditional sections

Author: Legacy2Lake Engineering
Date: February 14, 2026
Version: v4.0.0
"""

try:
    from apps.api.utils.logger import logger
except ImportError:
    try:
        from utils.logger import logger
    except ImportError:
        from ..utils.logger import logger

from typing import Dict, Any, Optional, List
import re
import json


class PromptAssembler:
    """
    Assembles prompts with dynamic context injection.
    
    Supports:
    - Simple variables: {{variable_name}}
    - Nested variables: {{object.field}}
    - Conditional blocks: {{#if condition}}...{{/if}}
    - List iteration: {{#each items}}...{{/each}}
    """
    
    def __init__(self):
        """Initialize Prompt Assembler"""
        pass
    
    def build(
        self,
        base_prompt: str,
        context: Dict[str, Any],
        format: str = "simple"
    ) -> str:
        """
        Build final prompt by injecting context into template
        
        Args:
            base_prompt: Template prompt with placeholders
            context: Dictionary with values to inject
            format: Assembly format ('simple', 'handlebars', 'jinja2')
            
        Returns:
            Assembled prompt with context injected
        """
        try:
            if format == "simple":
                return self._build_simple(base_prompt, context)
            elif format == "handlebars":
                return self._build_handlebars(base_prompt, context)
            elif format == "jinja2":
                return self._build_jinja2(base_prompt, context)
            else:
                raise ValueError(f"Unknown format: {format}")
                
        except Exception as e:
            logger.error(
                f"[PromptAssembler] Error building prompt: {e}",
                "PromptAssembler"
            )
            raise
    
    def _build_simple(self, template: str, context: Dict[str, Any]) -> str:
        """
        Simple variable substitution: {{variable}}
        
        Supports:
        - Simple variables: {{table_name}}
        - Nested access: {{source.table_name}}
        - JSON serialization: {{schema | json}}
        """
        result = template
        
        # Find both {{variable}} and {variable} patterns
        # We use a pattern that matches 1 or 2 braces, but captures the content inside
        pattern = r'\{{1,2}([^{}]+)\}{1,2}'
        matches = re.finditer(pattern, template)
        
        for match in matches:
            placeholder = match.group(0)  # Full {{variable}} or {variable}
            variable_path = match.group(1).strip()  # variable
            
            # Check for filters (e.g., {{schema | json}})
            filters = []
            if "|" in variable_path:
                parts = variable_path.split("|")
                variable_path = parts[0].strip()
                filters = [f.strip() for f in parts[1:]]
            
            # Get value from context
            value = self._get_nested_value(context, variable_path)
            
            # Apply filters
            for filter_name in filters:
                value = self._apply_filter(value, filter_name)
            
            # Replace placeholder with value
            if value is not None:
                result = result.replace(placeholder, str(value))
            else:
                # Keep placeholder if value not found
                logger.warning(
                    f"[PromptAssembler] Variable not found in context: {variable_path}",
                    "PromptAssembler"
                )
        
        return result
    
    def _build_handlebars(self, template: str, context: Dict[str, Any]) -> str:
        """
        Handlebars-style template with conditionals and loops
        
        Supports:
        - {{#if condition}}...{{/if}}
        - {{#each items}}...{{/each}}
        - {{variable}}
        
        Note: Simplified implementation. For full Handlebars, use pybars3 library.
        """
        # For v4.0, we'll use simple substitution
        # Full Handlebars support can be added in v5.0 if needed
        return self._build_simple(template, context)
    
    def _build_jinja2(self, template: str, context: Dict[str, Any]) -> str:
        """
        Jinja2 template engine integration
        
        Supports full Jinja2 syntax.
        Requires: pip install jinja2
        """
        try:
            from jinja2 import Template
            jinja_template = Template(template)
            return jinja_template.render(**context)
        except ImportError:
            logger.warning(
                "[PromptAssembler] Jinja2 not installed, falling back to simple substitution",
                "PromptAssembler"
            )
            return self._build_simple(template, context)
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        Get nested value from dictionary using dot notation
        
        Example:
            data = {"source": {"table": "customers"}}
            path = "source.table"
            returns: "customers"
        """
        parts = path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return None
            else:
                return None
        
        return current
    
    def _apply_filter(self, value: Any, filter_name: str) -> Any:
        """
        Apply filter to value
        
        Supported filters:
        - json: Convert to JSON string
        - upper: Convert to uppercase
        - lower: Convert to lowercase
        - trim: Remove whitespace
        - lines: Join list with newlines
        """
        if value is None:
            return None
        
        if filter_name == "json":
            return json.dumps(value, indent=2)
        elif filter_name == "upper":
            return str(value).upper()
        elif filter_name == "lower":
            return str(value).lower()
        elif filter_name == "trim":
            return str(value).strip()
        elif filter_name == "lines":
            if isinstance(value, list):
                return "\n".join(str(v) for v in value)
            return str(value)
        else:
            logger.warning(
                f"[PromptAssembler] Unknown filter: {filter_name}",
                "PromptAssembler"
            )
            return value
    
    def build_column_context(
        self,
        columns: List[Dict[str, Any]],
        include_types: bool = True,
        include_constraints: bool = True
    ) -> str:
        """
        Build formatted column context for prompts
        
        Args:
            columns: List of column dictionaries
            include_types: Include data types
            include_constraints: Include constraints (nullable, unique, etc.)
            
        Returns:
            Formatted column context string
        """
        lines = []
        
        for col in columns:
            col_name = col.get("name", "unknown")
            col_type = col.get("type", "unknown")
            nullable = col.get("nullable", True)
            
            line = f"- {col_name}"
            
            if include_types:
                line += f" ({col_type})"
            
            if include_constraints:
                constraints = []
                if not nullable:
                    constraints.append("NOT NULL")
                if col.get("primary_key"):
                    constraints.append("PK")
                if col.get("unique"):
                    constraints.append("UNIQUE")
                
                if constraints:
                    line += f" [{', '.join(constraints)}]"
            
            # Add description if available
            description = col.get("description")
            if description:
                line += f" - {description}"
            
            lines.append(line)
        
        return "\n".join(lines)
    
    def build_schema_context(
        self,
        schema: Dict[str, Any],
        format: str = "markdown"
    ) -> str:
        """
        Build formatted schema context for prompts
        
        Args:
            schema: Schema dictionary
            format: Output format ('markdown', 'json', 'sql')
            
        Returns:
            Formatted schema context string
        """
        if format == "json":
            return json.dumps(schema, indent=2)
        
        elif format == "markdown":
            lines = ["### Schema"]
            
            table_name = schema.get("table_name", "unknown")
            lines.append(f"**Table:** `{table_name}`")
            lines.append("")
            
            columns = schema.get("columns", [])
            if columns:
                lines.append("**Columns:**")
                lines.append(self.build_column_context(columns))
            
            return "\n".join(lines)
        
        elif format == "sql":
            table_name = schema.get("table_name", "unknown")
            columns = schema.get("columns", [])
            
            col_defs = []
            for col in columns:
                col_name = col.get("name", "unknown")
                col_type = col.get("type", "VARCHAR(255)")
                nullable = col.get("nullable", True)
                
                col_def = f"    {col_name} {col_type}"
                if not nullable:
                    col_def += " NOT NULL"
                
                col_defs.append(col_def)
            
            sql = f"CREATE TABLE {table_name} (\n"
            sql += ",\n".join(col_defs)
            sql += "\n);"
            
            return sql
        
        else:
            return json.dumps(schema, indent=2)
    
    def build_transformation_context(
        self,
        transformations: List[Dict[str, Any]]
    ) -> str:
        """
        Build formatted transformation context for prompts
        
        Args:
            transformations: List of transformation dictionaries
            
        Returns:
            Formatted transformation context string
        """
        if not transformations:
            return "No transformations required."
        
        lines = ["### Transformations"]
        
        for i, trans in enumerate(transformations, 1):
            trans_type = trans.get("type", "unknown")
            source_col = trans.get("source_column", "")
            target_col = trans.get("target_column", "")
            expression = trans.get("expression", "")
            
            lines.append(f"{i}. **{trans_type}**")
            if source_col:
                lines.append(f"   - Source: `{source_col}`")
            if target_col:
                lines.append(f"   - Target: `{target_col}`")
            if expression:
                lines.append(f"   - Expression: `{expression}`")
            lines.append("")
        
        return "\n".join(lines)
    
    def enrich_context(
        self,
        context: Dict[str, Any],
        asset: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enrich context with additional computed fields and unified aliases
        
        Args:
            context: Base context
            asset: Optional asset data
            
        Returns:
            Enriched context dictionary
        """
        enriched = context.copy()
        
        # Add timestamp
        from datetime import datetime
        enriched["timestamp"] = datetime.now().isoformat()
        
        # Add asset summary if provided
        if asset:
            enriched["asset_summary"] = {
                "name": asset.get("name", "unknown"),
                "type": asset.get("type", "unknown"),
                "tech": asset.get("source_tech", "unknown"),
                "columns_count": len(asset.get("columns", []))
            }
        
        # Multi-Target Aliases (e.g., Fabric Spark vs SQL)
        if "table_name" in enriched:
            enriched["TABLE_NAME"] = str(enriched["table_name"]).upper()
        
        # Schema/Warehouse Aliases
        if "gold_schema" in enriched:
            enriched["warehouse"] = enriched["gold_schema"]
            enriched["lakehouse_gold"] = enriched["gold_schema"]
        
        if "silver_schema" in enriched:
            enriched["lakehouse_silver"] = enriched["silver_schema"]
            
        if "bronze_schema" in enriched:
            enriched["lakehouse_bronze"] = enriched["bronze_schema"]
            
        # Path Aliases
        if "bronze_path" in enriched:
            enriched["adls_path"] = enriched["bronze_path"]
            
        # Primary Key Aliases
        if "primary_key" in enriched:
            pk = enriched["primary_key"]
            if isinstance(pk, list):
                enriched["pk_columns"] = ", ".join(pk)
                for i, p in enumerate(pk[:5]): # Support up to 5 individual PKs
                    enriched[f"pk{i+1}"] = p
            else:
                enriched["pk_columns"] = str(pk)
                enriched["pk1"] = str(pk)

        # Source System Aliases
        if "source_system" not in enriched and "source_tech" in enriched:
            enriched["source_system"] = enriched["source_tech"]
            enriched["source_system_name"] = enriched["source_tech"]

        # Add formatted columns if present
        if "columns" in context:
            enriched["columns_formatted"] = self.build_column_context(context["columns"])
        
        # Add formatted schema if present
        if "schema" in context:
            enriched["schema_formatted"] = self.build_schema_context(context["schema"])
        
        # Add formatted transformations if present
        if "transformations" in context:
            enriched["transformations_formatted"] = self.build_transformation_context(
                context["transformations"]
            )
        
        return enriched
