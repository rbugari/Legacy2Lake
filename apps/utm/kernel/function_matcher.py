from typing import Dict, Optional
import os
from supabase import create_client, Client

class FunctionMatcher:
    """
    Maps source-specific functions (e.g., SSIS Expression 'GETDATE()') 
    to Universal Canonical Functions (e.g., 'CANONICAL_NOW').
    
    It uses the UTM_Function_Registry table as the knowledge base.
    """
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        self.client: Optional[Client] = None
        
        if url and key:
            try:
                self.client = create_client(url, key)
                # Cache registry for performance in MVP
                self.registry_cache = self._load_registry()
            except Exception as e:
                print(f"[WARN] FunctionMatcher failed to connect to DB: {e}")
                self.registry_cache = {}
        else:
            self.registry_cache = {}

    def _load_registry(self) -> Dict[str, str]:
        """Loads valid mappings from DB."""
        if not self.client: return {}
        
        try:
            # Fetch the JSON templates where we have an implementation for 'sqlserver' (our source tech)
            res = self.client.table("utm_function_registry").select("canonical_name, implementation_templates").execute()
            
            mapping = {}
            for row in res.data:
                templates = row.get("implementation_templates", {})
                # We assume the input is SSIS/SQL Server, so we look for the 'sqlserver' template
                # to identify what the raw function looks like.
                source_template = templates.get("sqlserver")
                
                if source_template:
                    # Heuristic: Extract function name from template like "ISNULL({{args}})"
                    # We take the part before the first parenthesis
                    import re
                    match = re.match(r"([A-Za-z0-9_]+)\(", source_template)
                    if match:
                        source_func_name = match.group(1).upper()
                        mapping[source_func_name] = row["canonical_name"]
                    elif "CASE WHEN" in source_template.upper():
                         # Special case/Hack for MVP logic matching (if needed)
                         pass
                         
            return mapping
        except Exception as e:
            print(f"[WARN] Failed to load function registry: {e}")
            return {}

    def match(self, expression: str) -> str:
        """
        Translates a raw expression string into a canonical IR string.
        
        Example: 
            Input:  "ISNULL(MyCol, 'Default')"
            Output: "COALESCE(MyCol, 'Default')"
        """
        if not expression: return expression
        
        # very naive parser for MVP: direct replacement of known function names
        # In a real compiler, we would use an Abstract Syntax Tree (AST) parser.
        
        canonical_expr = expression
        
        for source_func, canonical_func in self.registry_cache.items():
            # Check for function call pattern (Upper Case)
            # This is risky (e.g. replacing substrings), but sufficient for MVP scope
            # Improved regex would be better
            if source_func in canonical_expr.upper():
                # We do a case-insensitive replace of the function name
                import re
                # Pattern: Word boundary or start, func names, opening parenthesis
                # e.g. GETDATE() -> CANONICAL_NOW()
                
                # Simple string replace for now (assuming function names are unique enough)
                # Using replace is dangerous if a column is named "ISNULL_VAL"
                # so we try to be slightly smarter
                
                canonical_expr = re.sub(
                    f"(?i)\\b{re.escape(source_func)}\\b", 
                    canonical_func, 
                    canonical_expr
                )
                
        return canonical_expr
