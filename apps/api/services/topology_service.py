import os
import json
import uuid
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

    def _resolve_task_extensions(self, filenames: List[str] | None = None) -> set[str]:
        valid_extensions = {".dtsx", ".sql"}
        if filenames and any(name.lower().endswith(".dtsx") for name in filenames):
            return {".dtsx"}
        return valid_extensions

    def _resolve_project_uuid(self) -> str:
        candidate = str(self.project_id or "").strip()
        if not candidate:
            return candidate

        try:
            return str(uuid.UUID(candidate))
        except ValueError:
            pass

        query = self.persistence.client.table("utm_projects").select("project_id").eq("name", candidate)
        if self.tenant_id:
            query = query.eq("tenant_id", self.tenant_id)

        res = query.limit(1).execute()
        if res.data:
            return res.data[0].get("project_id") or candidate
        return candidate

    def _load_selected_assets(self) -> List[Dict[str, Any]]:
        project_uuid = self._resolve_project_uuid()
        query = self.persistence.client.table("utm_objects").select(
            "object_id, source_name, source_path, raw_content, type, selected, metadata"
        ).eq("project_id", project_uuid).eq("selected", True)
        if self.tenant_id:
            query = query.eq("tenant_id", self.tenant_id)

        rows = query.execute().data or []
        assets = []
        seen_paths = set()
        for row in rows:
            source_name = (row.get("source_name") or "").strip()
            source_path = (row.get("source_path") or source_name).strip()
            asset_type = str(row.get("type") or "").upper()

            if not source_name or asset_type == "LAYOUT":
                continue
            if source_path in seen_paths:
                continue

            seen_paths.add(source_path)
            assets.append({
                "object_id": row.get("object_id"),
                "name": source_name,
                "path": source_path,
                "type": asset_type,
                "selected": True,
                "raw_content": row.get("raw_content") or "",
                "metadata": row.get("metadata") or {},
                "extension": os.path.splitext(source_name.lower())[1],
            })
        return assets

    def _read_asset_content(self, asset: Dict[str, Any]) -> str:
        raw_content = asset.get("raw_content")
        if raw_content:
            return raw_content

        source_path = asset.get("path") or asset.get("name")
        try:
            content = self.storage.read_file(source_path)
            if isinstance(content, bytes):
                return content.decode("utf-8", errors="ignore")
            return content or ""
        except Exception as e:
            logger.warning(f"Failed to read source for {source_path}: {e}", "Topology")
            return ""

    def _extract_asset_metadata(self, asset: Dict[str, Any], content: str) -> Dict[str, Any]:
        pkg_name = asset["name"]
        extension = asset.get("extension") or os.path.splitext(pkg_name.lower())[1]
        metadata = asset.get("metadata") or {}
        inputs = list(set(metadata.get("inputs") or []))
        outputs = list(set(metadata.get("outputs") or []))
        lookups = list(set(metadata.get("lookups") or []))
        complexity = metadata.get("complexity") or ("MEDIUM" if content else "LOW")

        if extension == ".dtsx" and content:
            parser = SSISCartridge()
            parsed = parser.parse_legacy(content, name=pkg_name)
            data_flow = parsed.components

            inputs = []
            outputs = []
            lookups = []
            complexity = "LOW"

            for comp in data_flow:
                logic = comp.get("raw_properties", {})
                table_ref = logic.get("OpenRowset") or logic.get("TableOrViewName")
                sql_command = logic.get("SqlCommand")
                if not table_ref and sql_command:
                    table_ref = f"QUERY: {sql_command}"

                intent = comp.get("original_intent", "UNKNOWN")
                if intent == "SOURCE" and table_ref:
                    inputs.append(table_ref)
                elif intent == "DESTINATION" and table_ref:
                    outputs.append(table_ref)
                elif intent == "LOOKUP" and table_ref:
                    lookups.append(table_ref)

            if len(lookups) > 2:
                complexity = "HIGH"

        elif extension == ".sql" and content:
            import re
            upper_sql = content.upper()
            outputs = re.findall(r'(?:INSERT\s+INTO|MERGE\s+INTO|UPDATE|CREATE\s+TABLE|CREATE\s+VIEW)\s+([a-zA-Z0-9_$.]+)', upper_sql)
            inputs = re.findall(r'(?:FROM|JOIN)\s+([a-zA-Z0-9_$.]+)', upper_sql)
            lookups = list(set(lookups))
            if len(inputs) > 3 or len(content.splitlines()) > 50:
                complexity = "MEDIUM"
            if len(content.splitlines()) > 200:
                complexity = "HIGH"

        return {
            "asset_id": asset.get("object_id"),
            "package_name": pkg_name,
            "path": asset.get("path") or pkg_name,
            "source_type": asset.get("type") or "OTHER",
            "source_extension": extension,
            "inputs": list(set(inputs)),
            "outputs": list(set(outputs)),
            "lookups": list(set(lookups)),
            "complexity": complexity,
            "raw_content": content,
        }

    def build_orchestration_plan(self) -> Dict[str, Any]:
        """Build the dependency graph from the assets selected in Triage."""
        logger.info(f"Building orchestration plan for {self.project_id}...", "Topology")
        package_metadatas = []
        selected_assets = self._load_selected_assets()
        logger.info(f"Found {len(selected_assets)} selected task assets from triage.", "Topology")

        if not selected_assets:
            logger.warning("Topology did not find selected assets in utm_objects.", "Topology")

        for asset in selected_assets:
            try:
                content = self._read_asset_content(asset)
                package_metadatas.append(self._extract_asset_metadata(asset, content))
            except Exception as e:
                logger.warning(
                    f"Could not derive detailed metadata for selected asset {asset.get('path') or asset.get('name')}: {e}. Skipping this asset in the current orchestration pass.",
                    "Topology"
                )

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
