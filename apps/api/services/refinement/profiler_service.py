import os
import re
import json
import datetime
from typing import List, Dict, Any

try:
    from apps.api.services.persistence_service import PersistenceService
except ImportError:
    try:
        from services.persistence_service import PersistenceService
    except ImportError:
        from ..persistence_service import PersistenceService

class ProfilerService:
    """
    The Global Profiler (Agent 3.1)
    Analyzes all Stage 2 output files to detect cross-package patterns, 
    shared connections, and dependency candidates.
    """

    def __init__(self, tenant_id: str = None, client_id: str = None):
        self.tenant_id = tenant_id
        self.client_id = client_id

    def _log(self, log: List[str], msg: str, level: str = "Profiler", model: str = "Pattern Discovery"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.append(f"[{timestamp}] [{level}] [{model}] {msg}")

    def _build_reengineering_units(self, refinement_units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        units: List[Dict[str, Any]] = []

        for unit in refinement_units:
            source_files = unit.get("source_files", [])
            shared_connections = unit.get("shared_connections", [])
            source_count = int(unit.get("source_count", len(source_files) or 0))
            needs_consolidation = source_count > 1 or bool(shared_connections)

            units.append(
                {
                    "unit_name": unit.get("unit_name"),
                    "target_asset_name": unit.get("output_table_name") or unit.get("unit_name"),
                    "source_files": source_files,
                    "pk_columns": unit.get("pk_columns", ["id"]),
                    "table_type": unit.get("table_type", "DIMENSION"),
                    "reuse_strategy": "project_wide_consolidation" if needs_consolidation else "bounded_enhancement",
                    "shared_connections": shared_connections,
                    "consolidation_score": source_count + len(shared_connections),
                }
            )

        return sorted(units, key=lambda item: item.get("consolidation_score", 0), reverse=True)

    def _build_shared_entities(self, reengineering_units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        entities: List[Dict[str, Any]] = []
        for unit in reengineering_units:
            if unit.get("consolidation_score", 0) < 2:
                continue
            entities.append(
                {
                    "entity": unit.get("target_asset_name") or unit.get("unit_name"),
                    "source_count": len(unit.get("source_files", [])),
                    "signals": {
                        "shared_connections": len(unit.get("shared_connections", [])),
                        "table_type": unit.get("table_type", "DIMENSION"),
                    },
                }
            )
        return entities

    def _build_consolidation_candidates(self, reengineering_units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        for unit in reengineering_units:
            if unit.get("consolidation_score", 0) < 2:
                continue
            candidates.append(
                {
                    "candidate": unit.get("target_asset_name") or unit.get("unit_name"),
                    "source_files": unit.get("source_files", []),
                    "rationale": "Multiple sources and/or shared connections detected; eligible for project-scoped consolidation.",
                    "traceability_required": True,
                }
            )
        return candidates

    def _build_common_ingestion_paths(self, shared_connections: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        paths: List[Dict[str, Any]] = []
        for connection, files in shared_connections.items():
            paths.append(
                {
                    "connection": connection,
                    "source_files": sorted(files),
                    "source_count": len(files),
                }
            )
        return sorted(paths, key=lambda item: item["source_count"], reverse=True)

    async def analyze_codebase(self, project_id: str, log: List[str] = None, project_name: str = None, target_tech: str = None) -> Dict[str, Any]:
        """
        Executes the profiling logic.
        1. Scans .py files in {project}/drafting (R2)
        2. Generates Global Profile
        """
        if log is None: log = []
        
        storage = PersistenceService.get_storage()
        
        # [Fix] Use project_name for R2 paths if provided
        folder_id = project_name or project_id
        base_path = PersistenceService.ensure_solution_dir(folder_id, tenant_id=self.tenant_id)
        self._log(log, f"Target Project Directory (R2): {base_path}")

        input_dir = f"{base_path.rstrip('/')}/{PersistenceService.STAGE_DRAFTING}"
        profile_output_key = f"{base_path.rstrip('/')}/{PersistenceService.STAGE_REFINEMENT}/profile_metadata.json"

        # List files via storage
        items = storage.list_files(input_dir, recursive=False)
        def get_all_files(nodes):
            files = []
            for n in nodes:
                if n["type"] == "folder" and n.get("children"):
                    files.extend(get_all_files(n["children"]))
                elif n["type"] == "file":
                    files.append(n)
            return files
        
        # Determine file extensions to scan based on target technology
        target = str(target_tech or "").lower()
        extensions = [".py"]
        if "sql" in target or target in ["snowflake", "fabric", "redshift", "bigquery"]:
            if ".sql" not in extensions:
                extensions.append(".sql")
        
        all_files = get_all_files(items)
        candidate_files = [f["name"] for f in all_files if any(f["name"].endswith(ext) for ext in extensions)]
        
        # Debug logging
        print(f"[PROFILER DEBUG] target_tech: {target_tech}")
        print(f"[PROFILER DEBUG] extensions to scan: {extensions}")
        print(f"[PROFILER DEBUG] input_dir: {input_dir}")
        print(f"[PROFILER DEBUG] items returned from storage.list_files: {len(items)} items")
        print(f"[PROFILER DEBUG] all_files after get_all_files: {len(all_files)} files")
        print(f"[PROFILER DEBUG] candidate_files: {candidate_files}")
        
        if not candidate_files:
            self._log(log, f"No source files ({'/'.join(extensions)}) found in {PersistenceService.STAGE_DRAFTING}.", level="Profiler", model="System")
            return {"total_files": 0, "analyzed_files": []}

        self._log(log, f"Found {len(candidate_files)} source files in {PersistenceService.STAGE_DRAFTING}.")
        
        shared_connections = {}
        bronze_candidates = {}
        
        for source_file in candidate_files:
            file_key = f"{input_dir.rstrip('/')}/{source_file}"
            self._log(log, f"Analyzing file: {source_file}...")
            
            content = storage.read_file(file_key)
            if not content: continue
            if isinstance(content, bytes):
                content = content.decode("utf-8")
                
            # Detect JDBC URLs (Basic Heuristic)
            jdbc_matches = re.findall(r'option\("url",\s*"([^"]+)"\)', content)
            for jdbc in jdbc_matches:
                self._log(log, f"  > Found JDBC Connection: {jdbc}")
                if jdbc not in shared_connections:
                    shared_connections[jdbc] = []
                shared_connections[jdbc].append(source_file)
            
            # Detect Table Type (Fact vs Dim)
            table_type = self._detect_table_type(source_file, content)
            
            # Detect PK candidates (Basic Heuristic)
            pks = self._detect_primary_keys(content, log)
            if pks:
                self._log(log, f"  > Detected PK candidates for {source_file} ({table_type}): {pks}")
                bronze_candidates[source_file] = {
                    "pk": pks,
                    "type": table_type
                }

        refinement_units = self._build_refinement_units(candidate_files, shared_connections, bronze_candidates)
        reengineering_units = self._build_reengineering_units(refinement_units)

        profile_data = {
            "analyzed_files": candidate_files,
            "shared_connections": shared_connections,
            "table_metadata": bronze_candidates,
            "primary_keys": {k: v["pk"] for k, v in bronze_candidates.items()},
            "refinement_units": refinement_units,
            "reengineering_units": reengineering_units,
            "shared_entities": self._build_shared_entities(reengineering_units),
            "consolidation_candidates": self._build_consolidation_candidates(reengineering_units),
            "common_ingestion_paths": self._build_common_ingestion_paths(shared_connections),
            "file_to_unit": self._build_file_to_unit_map(candidate_files),
            "unit_primary_keys": self._build_unit_primary_keys(candidate_files, bronze_candidates),
            "total_files": len(candidate_files)
        }

        # Save metadata directly to R2
        storage.save_file(profile_output_key, json.dumps(profile_data, indent=4))
        
        log.append(f"[Profiler] Profile metadata saved to {profile_output_key}")

        return profile_data

    def _build_refinement_units(self, candidate_files: List[str], shared_connections: Dict[str, List[str]], table_metadata: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        grouped_units: Dict[str, Dict[str, Any]] = {}

        for source_file in candidate_files:
            unit_name = self._normalize_refinement_unit_name(source_file)
            unit = grouped_units.setdefault(
                unit_name,
                {
                    "unit_name": unit_name,
                    "output_table_name": unit_name,
                    "source_files": [],
                    "pk_columns": [],
                    "table_type": "DIMENSION",
                    "shared_connections": [],
                    "reuse_strategy": "single_source",
                },
            )

            unit["source_files"].append(source_file)
            if table_metadata.get(source_file, {}).get("type") == "FACT":
                unit["table_type"] = "FACT"

            for pk_column in table_metadata.get(source_file, {}).get("pk", []):
                if pk_column not in unit["pk_columns"]:
                    unit["pk_columns"].append(pk_column)

        for jdbc_url, source_files in shared_connections.items():
            for source_file in source_files:
                unit_name = self._normalize_refinement_unit_name(source_file)
                unit = grouped_units.get(unit_name)
                if unit and jdbc_url not in unit["shared_connections"]:
                    unit["shared_connections"].append(jdbc_url)

        units: List[Dict[str, Any]] = []
        for unit_name in sorted(grouped_units.keys()):
            unit = grouped_units[unit_name]
            if len(unit["source_files"]) > 1:
                unit["reuse_strategy"] = "multi_source_consolidation"
            elif unit["shared_connections"]:
                unit["reuse_strategy"] = "knowledge_guided_reuse"
            unit["source_count"] = len(unit["source_files"])
            units.append(unit)

        return units

    def _build_file_to_unit_map(self, candidate_files: List[str]) -> Dict[str, str]:
        return {
            source_file: self._normalize_refinement_unit_name(source_file)
            for source_file in candidate_files
        }

    def _build_unit_primary_keys(self, candidate_files: List[str], table_metadata: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        unit_primary_keys: Dict[str, List[str]] = {}

        for source_file in candidate_files:
            unit_name = self._normalize_refinement_unit_name(source_file)
            pk_columns = table_metadata.get(source_file, {}).get("pk", [])
            unit_primary_keys.setdefault(unit_name, [])
            for pk_column in pk_columns:
                if pk_column not in unit_primary_keys[unit_name]:
                    unit_primary_keys[unit_name].append(pk_column)

        for unit_name, pk_columns in unit_primary_keys.items():
            if not pk_columns:
                unit_primary_keys[unit_name] = ["id"]

        return unit_primary_keys

    def _normalize_refinement_unit_name(self, filename: str) -> str:
        stem = filename.rsplit(".", 1)[0].lower()
        tokens = [token for token in re.split(r"[^a-z0-9]+", stem) if token]
        stop_words = {
            "bronze", "silver", "gold", "raw", "curated", "stage", "stg", "tmp", "temp",
            "pkg", "package", "ssis", "sql", "sp", "proc", "procedure", "job", "task",
            "etl", "elt", "load", "sync", "pipeline", "flow", "data", "dbo", "fact", "dim"
        }
        filtered = [token for token in tokens if token not in stop_words]
        if not filtered:
            filtered = tokens or ["refined_asset"]
        return "_".join(filtered[:4])

    def _detect_primary_keys(self, content: str, log: List[str] = None) -> List[str]:
        """
        Heuristic to detect Primary Key candidates from PySpark code.
        Looks for logic-based patterns like dropDuplicates, Window partitions, and explicit assignments.
        Returns a LIST of keys (supporting composite keys).
        """
        # 1. Explicit Business/Surrogate Keys (Highest Priority)
        # bk_cols = ["ProductID", "Date"]
        bk_match = re.search(r'bk_cols\s*=\s*\[(.*?)\]', content, re.IGNORECASE | re.DOTALL)
        if bk_match:
            raw_list = bk_match.group(1)
            keys = [k.strip().strip('"').strip("'") for k in raw_list.split(",") if k.strip()]
            if keys: return keys
            
        sk_match = re.search(r'sk_col\s*=\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
        if sk_match: return [sk_match.group(1)]

        # 2. Logic Inference: dropDuplicates (Strong Indicator of Unique Keys)
        # .dropDuplicates(['col1', 'col2']) or .dropDuplicates( ['col1'] )
        dd_pattern = r'\.dropDuplicates\(\s*\[\s*(.*?)\s*\]\s*\)'
        dd_match = re.search(dd_pattern, content, re.IGNORECASE | re.DOTALL)
        if log: log.append(f"[Profiler DEBUG] Checking dropDuplicates pattern: {dd_pattern} on content snippet...")
        
        if dd_match:
            raw_list = dd_match.group(1)
            if log: log.append(f"[Profiler DEBUG] dropDuplicates MATCH: {raw_list}")
            keys = [k.strip().strip('"').strip("'") for k in raw_list.split(",") if k.strip()]
            if keys: return keys
        else:
            if "dropDuplicates" in content and log:
                log.append(f"[Profiler DEBUG] Content has 'dropDuplicates' but regex failed.")
                # log.append(f"[Profiler DEBUG] Snippet: {content[max(0, content.find('dropDuplicates')-20):content.find('dropDuplicates')+50]}")

        # 3. Logic Inference: Window.partitionBy (Composite Candidate)
        # Window.partitionBy("col1", "col2") or .partitionBy(["col1"])
        win_match = re.search(r'\.partitionBy\(\s*(?:\[)?(.*?)(?:\])?\s*\)', content, re.IGNORECASE | re.DOTALL)
        if win_match:
            raw_list = win_match.group(1)
            keys = [k.strip().strip('"').strip("'") for k in raw_list.split(",") if k.strip()]
            if keys: return keys

        # 4. Join Conditions - "ON" Clause
        # .join(other, on=["col1"], ...) or on="col1"
        join_match = re.search(r'on\s*=\s*(?:\[)?["\'](.*?)["\'](?:\])?', content, re.IGNORECASE)
        if join_match:
             # This usually finds the first join, which is often the main grain
             return [join_match.group(1)]

        # 5. Fallback: Naming Convention (*ID, *Key)
        # Only if no logic flow is found
        patterns = [
            r'["\']([^"\']*(?:ID|Key|Code|Num))["\']', 
        ]
        candidates = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for m in matches:
                # Filter out very short strings or obvious junk
                if len(m) > 1 and m not in candidates:
                    candidates.append(m)
        
        sanitized = []
        for c in candidates:
            c_clean = c.strip()
            if " " in c_clean or "\n" in c_clean or len(c_clean) > 50: continue
            if any(sql in c_clean.upper() for sql in ["SELECT", "FROM", "JOIN", "WHERE", "INNER", "LEFT", "RIGHT"]): continue
            sanitized.append(c_clean)

        return sorted(sanitized, key=len)[:1] if sanitized else ["id"]

    def _detect_table_type(self, filename: str, content: str) -> str:
        """
        Heuristic to distinguish between Fact and Dimension tables.
        """
        name_lower = filename.lower()
        if "fact" in name_lower: return "FACT"
        if "dim" in name_lower: return "DIMENSION"
        
        # Check content for aggregations or volume indicators
        if any(agg in content.upper() for agg in ["SUM(", "COUNT(", "GROUP BY"]):
            return "FACT"
            
        return "DIMENSION" # Default
