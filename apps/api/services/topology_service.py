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

try:
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from .persistence_service import SupabasePersistence

class TopologyService:
    """
    The Topology Architect: Orchestration Agent.
    Builds the execution DAG by analyzing inter-package dependencies (Lookups/Sources).
    """

    def __init__(self, project_id: str, tenant_id: str = None, source_folder: str = None):
        self.project_id = project_id
        self.tenant_id = tenant_id
        self.persistence = SupabasePersistence(tenant_id=tenant_id)
        self.base_path = PersistenceService.ensure_solution_dir(project_id, tenant_id=tenant_id)
        self.storage = PersistenceService.get_storage()
        
        target_folder = source_folder or PersistenceService.STAGE_SOURCE
        
        # [Fix] Discover Triage/Source folder case-insensitively (identical to Librarian/Discovery)
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
                        if not self.inbound_path or item["name"].lower() == PersistenceService.STAGE_SOURCE.lower():
                            self.inbound_path = item["path"]
        except Exception as e:
            logger.warning(f"Topology discovery error: {e}", "Topology")

        if not self.inbound_path:
            self.inbound_path = f"{self.base_path.rstrip('/')}/{target_folder}"

        # Stage folders
        self.output_path = f"{self.base_path.rstrip('/')}/{PersistenceService.STAGE_DRAFTING}"
        logger.info(f"Topology resolved inbound path to: {self.inbound_path}", "Topology")

    def build_orchestration_plan(self) -> Dict[str, Any]:
        """Scans all .dtsx files and constructs the dependency graph."""
        logger.info(f"Building orchestration plan for {self.project_id}...", "Topology")
        
        # 1. Inventory Packages & Extract Metadata via Storage
        package_metadatas = []
        # 1. Scan SSIS Packages via Storage (from inbound_path only)
        try:
            items = self.storage.list_files(self.inbound_path, recursive=True)
            def get_all_files(nodes):
                files = []
                for n in nodes:
                    if n["type"] == "folder" and n.get("children"):
                        files.extend(get_all_files(n["children"]))
                    elif n["type"] == "file":
                        files.append(n)
                return files
            
            # Find migrable task files (.dtsx for SSIS, .sql for DB logic)
            all_files = get_all_files(items)
            
            # De-duplicate task files by path AND name to prevent multiple entries for same file
            seen_task_paths = set()
            seen_task_names = set()
            task_files = []
            valid_extensions = {".dtsx", ".sql"}
            
            for f in all_files:
                f_name_lower = f["name"].lower()
                ext = os.path.splitext(f_name_lower)[1]
                
                if ext in valid_extensions and f["path"] not in seen_task_paths and f_name_lower not in seen_task_names:
                    # [Exception] Ignore DDL files if they are just schema definitions
                    if "ddl" in f_name_lower:
                        continue
                        
                    task_files.append(f)
                    seen_task_paths.add(f["path"])
                    seen_task_names.add(f_name_lower)
        except Exception as e:
            logger.error(f"Error listing packages for topology: {e}", "Topology")
        
        logger.info(f"Found {len(task_files)} unique task files (migration assets) in storage.", "Topology")

        # Storage can be empty for older/imported projects where assets live in DB only.
        # In that case, build a minimal package inventory from utm_objects.
        if not task_files:
            try:
                query = self.persistence.client.table("utm_objects").select("source_name, metadata")
                query = query.eq("project_id", self.project_id)
                if self.tenant_id:
                    query = query.eq("tenant_id", self.tenant_id)

                db_rows = (query.execute().data or [])
                seen_names = set()

                for row in db_rows:
                    source_name = (row.get("source_name") or "").strip()
                    if not source_name:
                        continue

                    source_name_lower = source_name.lower()
                    ext = os.path.splitext(source_name_lower)[1]
                    if ext not in {".dtsx", ".sql"}:
                        continue
                    if source_name_lower in seen_names:
                        continue

                    seen_names.add(source_name_lower)
                    md = row.get("metadata") or {}
                    task_files.append({
                        "name": source_name,
                        "path": source_name,
                        "type": "file",
                        "from_db_fallback": True,
                        "metadata": md
                    })

                logger.info(
                    f"Topology DB fallback discovered {len(task_files)} task files from utm_objects.",
                    "Topology"
                )
            except Exception as e:
                logger.warning(f"Topology DB fallback failed: {e}", "Topology")

        for f_node in task_files:
            p_path = f_node["path"]
            try:
                if f_node.get("from_db_fallback"):
                    pkg_name = f_node["name"]
                    md = f_node.get("metadata") or {}

                    # Preserve known dependency hints if they were persisted in metadata.
                    inputs = md.get("inputs") or []
                    outputs = md.get("outputs") or []
                    lookups = md.get("lookups") or []

                    package_metadatas.append({
                        "package_name": pkg_name,
                        "path": p_path,
                        "inputs": list(set(inputs)),
                        "outputs": list(set(outputs)),
                        "lookups": list(set(lookups)),
                        "complexity": md.get("complexity") or "MEDIUM"
                    })
                    continue

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
