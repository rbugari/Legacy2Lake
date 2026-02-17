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

    def __init__(self, project_id: str, tenant_id: str = None):
        self.project_id = project_id
        self.tenant_id = tenant_id
        self.base_path = PersistenceService.ensure_solution_dir(project_id, tenant_id=tenant_id)
        # Stage folders
        self.output_path = f"{self.base_path.rstrip('/')}/{PersistenceService.STAGE_DRAFTING}"
        self.storage = PersistenceService.get_storage()

    def build_orchestration_plan(self) -> Dict[str, Any]:
        """Scans all .dtsx files and constructs the dependency graph."""
        logger.info(f"Building orchestration plan for {self.project_id}...", "Topology")
        
        # 1. Inventory Packages & Extract Metadata via Storage
        package_metadatas = []
        dtsx_files = []
        
        try:
            items = self.storage.list_files(self.base_path, recursive=True)
            def get_all_files(nodes):
                files = []
                for n in nodes:
                    if n["type"] == "folder" and n.get("children"):
                        files.extend(get_all_files(n["children"]))
                    elif n["type"] == "file":
                        files.append(n)
                return files
            
            # Find all .dtsx files (migrable packages)
            # SQL files are support/DDL files, NOT migration tasks
            all_files = get_all_files(items)
            task_files = [f for f in all_files if f["name"].lower().endswith(".dtsx")]
        except Exception as e:
            logger.error(f"Error listing packages for topology: {e}", "Topology")
        
        logger.info(f"Found {len(task_files)} task files (dtsx/sql) in storage.", "Topology")

        for f_node in task_files:
            p_path = f_node["path"]
            try:
                # Read content instead of passing path
                content = self.storage.read_file(p_path)
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="ignore")
                
                pkg_name = os.path.basename(p_path)
                inputs = []
                outputs = []
                lookups = []
                complexity = "LOW"

                if pkg_name.lower().endswith(".dtsx"):
                    parser = SSISCartridge()
                    metadata = parser.parse(content, name=f_node["name"])
                    data_flow = metadata.components
                    
                    for comp in data_flow:
                        logic = comp.get("raw_properties", {})
                        table_ref = logic.get("OpenRowset") or logic.get("TableOrViewName")
                        sql_command = logic.get("SqlCommand")
                        
                        if not table_ref and sql_command:
                            table_ref = f"QUERY: {sql_command}"
                            
                        intent = comp.get("original_intent", "UNKNOWN")

                        if intent == "SOURCE":
                            if table_ref: inputs.append(table_ref)
                        elif intent == "DESTINATION":
                            if table_ref: outputs.append(table_ref)
                        elif intent == "LOOKUP":
                            if table_ref: lookups.append(table_ref)
                            
                    if len(lookups) > 2: complexity = "HIGH"
                
                elif pkg_name.lower().endswith(".sql"):
                     # Basic SQL Dependency Parsing
                     import re
                     upper_sql = content.upper()
                     
                     # Heuristic for Outputs: INSERT INTO, MERGE INTO, UPDATE, CREATE TABLE/VIEW
                     # Regex matches: INSERT INTO [schema.]table
                     out_matches = re.findall(r'(?:INSERT\s+INTO|MERGE\s+INTO|UPDATE|CREATE\s+TABLE|CREATE\s+VIEW)\s+([a-zA-Z0-9_$.]+)', upper_sql)
                     outputs.extend(out_matches)
                     
                     # Heuristic for Inputs: FROM, JOIN
                     in_matches = re.findall(r'(?:FROM|JOIN)\s+([a-zA-Z0-9_$.]+)', upper_sql)
                     inputs.extend(in_matches)
                     
                     if len(inputs) > 3 or len(content.splitlines()) > 50:
                         complexity = "MEDIUM"
                     if len(content.splitlines()) > 200:
                         complexity = "HIGH"

                package_metadatas.append({
                    "package_name": pkg_name,
                    "path": p_path,
                    "inputs": list(set(inputs)),
                    "outputs": list(set(outputs)),
                    "lookups": list(set(lookups)),
                    "complexity": complexity
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

        # Save Artifact to Storage (Drafting folder)
        output_key = f"{self.output_path.rstrip('/')}/orchestration_plan.json"
        self.storage.save_file(output_key, json.dumps(orchestration, indent=2))
            
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
