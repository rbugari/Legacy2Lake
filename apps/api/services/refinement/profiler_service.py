import os
import re
import json
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

    def __init__(self):
        pass

    def analyze_codebase(self, project_id: str, log: List[str] = None) -> Dict[str, Any]:
        """
        Executes the profiling logic.
        1. Scans .py files in {project}/Output
        2. Generates Global Profile
        """
        if log is None: log = []
        
        # Resolve project path robustly
        project_path = PersistenceService.ensure_solution_dir(project_id)
        log.append(f"[Profiler] Target Project Directory: {project_path}")

        input_dir = os.path.join(project_path, PersistenceService.STAGE_DRAFTING)
        profile_output = os.path.join(project_path, PersistenceService.STAGE_REFINEMENT, "profile_metadata.json")

        if not os.path.exists(input_dir):
            error_msg = f"Input directory not found: {input_dir}"
            log.append(f"[Profiler] ERROR: {error_msg}")
            return {"error": error_msg, "total_files": 0}

        py_files = [f for f in os.listdir(input_dir) if f.endswith(".py")]
        log.append(f"[Profiler] Found {len(py_files)} Python files in {PersistenceService.STAGE_DRAFTING}.")
        
        shared_connections = {}
        bronze_candidates = {}
        
        for py_file in py_files:
            file_path = os.path.join(input_dir, py_file)
            log.append(f"[Profiler] Analyzing file: {py_file}...")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Detect JDBC URLs (Basic Heuristic)
                jdbc_matches = re.findall(r'option\("url",\s*"([^"]+)"\)', content)
                for jdbc in jdbc_matches:
                    log.append(f"[Profiler]   > Found JDBC Connection: {jdbc}")
                    if jdbc not in shared_connections:
                        shared_connections[jdbc] = []
                    shared_connections[jdbc].append(py_file)
                
                # Detect Table Type (Fact vs Dim)
                table_type = self._detect_table_type(py_file, content)
                
                # Detect PK candidates (Basic Heuristic)
                pks = self._detect_primary_keys(content, log)
                if pks:
                    log.append(f"[Profiler]   > Detected PK candidates for {py_file} ({table_type}): {pks}")
                    bronze_candidates[py_file] = {
                        "pk": pks,
                        "type": table_type
                    }

        profile_data = {
            "analyzed_files": py_files,
            "shared_connections": shared_connections,
            "table_metadata": bronze_candidates,
            "primary_keys": {k: v["pk"] for k, v in bronze_candidates.items()},
            "total_files": len(py_files)
        }

        # Ensure output dir exists
        os.makedirs(os.path.dirname(profile_output), exist_ok=True)
        
        with open(profile_output, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=4)
        
        log.append(f"[Profiler] Profile metadata saved to {profile_output}")

        return profile_data

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
