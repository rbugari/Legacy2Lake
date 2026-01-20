from apps.utm.core.interfaces import MetadataObject, LogicalStep
from typing import List, Dict, Any

from apps.utm.kernel.function_matcher import FunctionMatcher

class LogicMapper:
    """
    The Kernel Agent: Normalizes raw metadata into Universal IR.
    """
    
    def __init__(self):
        self.matcher = FunctionMatcher()
    
    def normalize(self, metadata: MetadataObject) -> List[LogicalStep]:
        steps = []
        step_counter = 0
        
        # Sort components to attempt a logical flow (simple heuristic for now)
        # In a real scenario, we'd traverse the 'paths' from the XML to build the DAG.
        # For MVP, we assume Source -> Transform -> Dest order if possible, 
        # or we just map them and rely on the Cartridge to chain them (or the parser provided order).
        
        # Simple heuristic sorting: Source < Transform < Dest
        type_priority = {
            "SOURCE_DB": 1,
            "LOOKUP": 2, 
            "TRANSFORM": 2,
            "DERIVED_COLUMN": 2,
            "SCD": 2,
            "DESTINATION_DB": 3
        }
        
        sorted_components = sorted(
            metadata.components, 
            key=lambda c: type_priority.get(c.get("type"), 99)
        )
        
        for comp in sorted_components:
            step_counter += 1
            ir_step = None
            
            comp_type = comp.get("type")
            props = comp.get("raw_properties", {})
            
            if comp_type == "SOURCE_DB":
                ir_step = self._map_read(comp, props)
            elif comp_type == "DESTINATION_DB":
                ir_step = self._map_write(comp, props)
            elif comp_type == "SCD":
                ir_step = self._map_scd(comp, props)
            elif comp_type == "LOOKUP": # Treat as JOIN
                ir_step = self._map_join(comp, props)
            elif comp_type == "DERIVED_COLUMN":
                ir_step = self._map_derived_column(comp, props)
            
            if ir_step:
                steps.append(LogicalStep(
                    step_type=ir_step["type"],
                    step_order=step_counter,
                    ir_payload=ir_step
                ))
                
        return steps

    def _map_read(self, comp, props):
        sql_command = props.get("SqlCommand") or ""
        table = (props.get("OpenRowset") or "").replace("[", "").replace("]", "")
        
        return {
            "type": "READ",
            "source_alias": f"src_{comp['name'].replace(' ', '_').lower()}",
            "params": {
                "source_object": table,
                "query": self.matcher.match(sql_command) if "SELECT" in sql_command.upper() else None,
                "schema_discovery": "AUTOMATIC"
            }
        }

    def _map_write(self, comp, props):
        table = (props.get("OpenRowset") or "").replace("[", "").replace("]", "")
        return {
            "type": "WRITE",
            "target": table,
            "params": {
                "mode": "MERGE", # Defaulting to MERGE for idempotency preference
                "primary_keys": ["_auto_detect_"], # Placeholder for enrichment
            }
        }

    def _map_scd(self, comp, props):
        # In a real parsing, we'd extract these from the custom input/outputs of the SCD component
        # For MVP, resolving to the structure expected by the IR Grammar
        return {
            "type": "TRANSFORM",
            "subtype": "SCD_TYPE_2",
            "params": {
                "business_key": ["_detect_from_scd_props_"], 
                "changing_attributes": ["_detect_"],
                "history_flag": "Flag", 
                "default_values": {"Flag": "1"}
            }
        }
    
    def _map_join(self, comp, props):
        return {
            "type": "JOIN",
            "params": {
                "join_type": "LEFT", # Lookup default
                "left_source": "previous_step", # Simplified implication
                "right_source": props.get("SqlCommand", "lookup_table"),
                "on_missing": {"strategy": "IGNORE"}
            }
        }

    def _map_derived_column(self, comp, props):
        """
        Maps a Derived Column component.
        Iterates over input/output properties to find expressions.
        """
        transformations = []
        
        # For MVP, we need a better structure in parse output to hold column expressions.
        # Since SSISParser currently puts everything in 'raw_properties', 
        # let's assume raw_properties might contain a list of derivations if the parser was richer.
        # For now, we stub this:
        
        return {
            "type": "TRANSFORM",
            "subtype": "EXPRESSION",
            "params": {
                "expressions": [
                    {
                        "target_col": "NewColumn",
                        "expr": self.matcher.match("ISNULL(Col1, 'N/A')") # Stub to demonstrate matcher
                    }
                ]
            }
        }
