import json
from typing import List, Dict, Any, Optional

class QualityService:
    def __init__(self):
        pass

    def generate_great_expectations_json(self, asset_name: str, mappings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Generates a Great Expectations (GX) Validation Suite from column mappings.
        Returns None if no relevant rules exist.
        """
        expectations = []

        for mapping in mappings:
            col = mapping.get("source_column")
            if not col: continue
            
            # Rule 1: Not Null
            if mapping.get("is_nullable") is False:
                expectations.append({
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": col},
                    "meta": {"notes": "Derived from is_nullable=False"}
                })
            
            # Rule 2: PII Format Check (Simple Heuristic for now)
            if mapping.get("is_pii") is True:
                # We expect PII columns to be at least present (can be refined to regex later)
                 expectations.append({
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": col},
                    "meta": {"notes": "PII Requirement: Field must be present"}
                })

            # Rule 3: Type Checking (Basic)
            dtype = mapping.get("source_datatype", "").lower()
            gx_type = None
            if "int" in dtype or "long" in dtype: gx_type = "Integer"
            elif "float" in dtype or "double" in dtype: gx_type = "Float"
            elif "bool" in dtype: gx_type = "Boolean"
            elif "char" in dtype or "string" in dtype or "text" in dtype: gx_type = "String"
            
            if gx_type:
                expectations.append({
                    "expectation_type": "expect_column_values_to_be_of_type",
                    "kwargs": {"column": col, "type_": gx_type},
                     "meta": {"notes": f"Derived from datatype={dtype}"}
                })

        if not expectations:
            return None

        return {
            "data_asset_type": "Dataset",
            "expectation_suite_name": f"{asset_name}.warning",
            "expectations": expectations,
            "meta": {
                "great_expectations_version": "0.15.50",
                "generated_by": "Legacy2Lake QualityService (Phase 9)"
            }
        }

    def generate_soda_yaml(self, asset_name: str, mappings: List[Dict[str, Any]]) -> Optional[str]:
        """
        Generates a Soda Core YAML check file.
        Returns None if no rules.
        """
        checks = []
        for mapping in mappings:
            col = mapping.get("source_column")
            if not col: continue
            
            if mapping.get("is_nullable") is False:
                checks.append(f"  - missing_count({col}) = 0")
                
            if mapping.get("is_pii") is True:
                # Just an example check
                 checks.append(f"  - invalid_percent({col}) < 5%")

        if not checks:
            return None
            
        yaml_content = f"checks for {asset_name}:\n" + "\n".join(checks)
        return yaml_content
