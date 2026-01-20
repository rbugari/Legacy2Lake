import os
import json
from typing import Dict, Any, List
from apps.utm.cartridges.ssis.parser import SSISCartridge
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

class TopologyService:
    """
    The Topology Architect: Orchestration Agent.
    Builds the execution DAG by analyzing inter-package dependencies (Lookups/Sources).
    """

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.base_path = PersistenceService.ensure_solution_dir(project_id)
        self.output_path = os.path.join(self.base_path, "Output")

    def build_orchestration_plan(self) -> Dict[str, Any]:
        """Scans all .dtsx files and constructs the dependency graph."""
        logger.info(f"Building orchestration plan for {self.project_id}...", "Topology")
        
        # 1. Inventory Packages & Extract Metadata
        package_metadatas = []
        dtsx_files = []
        
        # Recursive scan
        for root, dirs, files in os.walk(self.base_path):
            for f in files:
                if f.lower().endswith(".dtsx"):
                   dtsx_files.append(os.path.join(root, f))
        
        logger.info(f"Found {len(dtsx_files)} packages.", "Topology")

        for p_path in dtsx_files:
            try:
                parser = SSISCartridge()
                metadata = parser.parse(p_path)
                
                summary = metadata.metadata["summary"]
                data_flow = metadata.components
                
                pkg_name = os.path.basename(p_path)
                
                # Analyze INPUTS (Sources) and OUTPUTS (Destinations)
                inputs = []
                outputs = []
                lookups = []
                
                for comp in data_flow:
                    table_ref = comp["logic"].get("OpenRowset") or comp["logic"].get("TableOrViewName")
                    sql_command = comp["logic"].get("SqlCommand")
                    
                    if not table_ref and sql_command:
                        table_ref = f"QUERY: {sql_command}" # Embed query for now, or use a struct
                        
                    if comp["intent"] == "SOURCE":
                        if table_ref: inputs.append(table_ref)
                    elif comp["intent"] == "DESTINATION":
                        if table_ref: outputs.append(table_ref)
                    elif comp["intent"] == "LOOKUP":
                        if table_ref: lookups.append(table_ref)

                package_metadatas.append({
                    "package_name": pkg_name,
                    "path": p_path,
                    "inputs": list(set(inputs)),
                    "outputs": list(set(outputs)),
                    "lookups": list(set(lookups)),
                    "complexity": "HIGH" if len(lookups) > 2 else "MEDIUM"
                })
            except Exception as e:
                logger.error(f"Failed to parse {p_path}: {e}", "Topology")

        # 2. Build DAG (Naive Approach: Layers)
        # Rule 1: Bronze = No Lookups, or lookups to static config. Reads from Flat File/Source.
        # Rule 2: Silver = Reads from Bronze/Source, Looks up Dimensions.
        # Rule 3: Gold = Reads from Silver, Aggregates.
        
        # Implicit Dependency: If PkgA looks up TableX, and PkgB outputs to TableX -> PkgB MUST run before PkgA.
        
        # Dependency Map: Table -> [ProducerPackages]
        producers = {}
        for pm in package_metadatas:
            for out_table in pm["outputs"]:
                clean_table = self._clean_table_name(out_table)
                if clean_table not in producers:
                    producers[clean_table] = []
                producers[clean_table].append(pm["package_name"])
                
        # Assign Layers & Dependencies
        execution_plan = []
        
        # In this simplified pass, we'll bucket by logic:
        # Phase 1: Dimensions (Independent)
        # Phase 2: Dimensions (Dependent / having lookups)
        # Phase 3: Facts
        
        orchestration = {
            "project_id": self.project_id,
            "dag_execution": []
        }
        
        # Identify "Bronze" / independent loaders
        bronze_layer = []
        silver_layer = []
        gold_layer = []
        
        for pm in package_metadatas:
            # Heuristic: Name contains 'Dim' -> Dimension
            if "Dim" in pm["package_name"]:
                # If it has dependencies on other tables that are produced by us?
                has_internal_dependency = False
                for lookup in pm["lookups"]:
                    clean_lookup = self._clean_table_name(lookup)
                    if clean_lookup in producers:
                        # Depends on something we produce
                         has_internal_dependency = True
                
                if not has_internal_dependency:
                    bronze_layer.append(pm["package_name"])
                else:
                    silver_layer.append(pm["package_name"])
            elif "Fact" in pm["package_name"]:
                gold_layer.append(pm["package_name"])
            else:
                # Fallback
                silver_layer.append(pm["package_name"])

        if bronze_layer:
            orchestration["dag_execution"].append({
                "phase": "Bronze_Ingestion",
                "description": "Independent Dimensions & Raw Loads",
                "packages": bronze_layer
            })
            
        if silver_layer:
            orchestration["dag_execution"].append({
                "phase": "Silver_Refinement",
                "dependencies": ["Bronze_Ingestion"],
                "description": "Dependent Dimensions & Transformations",
                "packages": silver_layer
            })

        if gold_layer:
            orchestration["dag_execution"].append({
                "phase": "Gold_Delivery",
                "dependencies": ["Silver_Refinement"],
                "description": "Fact Tables & Aggregations",
                "packages": gold_layer
            })

        # Save Artifact
        self._ensure_output_dir()
        with open(os.path.join(self.output_path, "orchestration_plan.json"), "w", encoding="utf-8") as f:
            json.dump(orchestration, f, indent=2)
            
        logger.debug("Orchestration Plan Generated", "Topology", orchestration)
        return {
            "orchestration": orchestration,
            "package_metadatas": package_metadatas
        }

    def _clean_table_name(self, raw: str) -> str:
        """Standardizes table names helpers (remove brackets, schema)."""
        if not raw: return ""
        # Remove [ ]
        cl = raw.replace("[", "").replace("]", "")
        # Remove dbo.
        if "." in cl:
            cl = cl.split(".")[-1]
        return cl.lower()

    def _ensure_output_dir(self):
        os.makedirs(self.output_path, exist_ok=True)
