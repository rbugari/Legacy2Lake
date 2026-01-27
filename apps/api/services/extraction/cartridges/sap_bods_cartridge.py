import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_cartridge import SourceCartridge

class SapBodsCartridge(SourceCartridge):
    """
    Extractor for SAP BODS (Data Integrator) mappings via .atl exports.
    Parses Jobs, DataFlows and Query Transforms.
    """

    def test_connection(self) -> bool:
        # Offline mode only: check if ATL exists
        path = self.config.get("path")
        if path and Path(path).exists():
            return True
        return False

    def scan_catalog(self) -> List[Dict[str, Any]]:
        """Scans ATL files for Jobs and DataFlows."""
        path = self.config.get("path", ".")
        root = Path(path)
        assets = []
        
        if root.is_file() and root.suffix == ".atl":
            jobs = self._get_jobs_from_atl(root)
            for j in jobs:
                assets.append({"name": j, "type": "BODS_JOB", "metadata": {"file": str(root)}})
        elif root.is_dir():
            for atl_file in root.glob("*.atl"):
                jobs = self._get_jobs_from_atl(atl_file)
                for j in jobs:
                    assets.append({"name": j, "type": "BODS_JOB", "metadata": {"file": str(atl_file)}})
        
        return assets

    def extract_ddl(self, asset_name: str) -> str:
        """Parses the ATL for a specific Job/Dataflow and extracts its internal logic."""
        path = self.config.get("path")
        atl_path = Path(path)
        
        if atl_path.is_dir():
            for f in atl_path.glob("*.atl"):
                content = f.read_text(errors="ignore")
                if f'CREATE JOB {asset_name}' in content or f'CREATE DATAFLOW {asset_name}' in content:
                    atl_path = f
                    break
        
        return self._parse_atl_logic(atl_path, asset_name)

    def sample_data(self, asset_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        return []

    def _get_jobs_from_atl(self, file_path: Path) -> List[str]:
        content = file_path.read_text(errors="ignore")
        # Find JOBS and DATAFLOWS
        jobs = re.findall(r'CREATE JOB\s+([^\s\(]+)', content)
        dataflows = re.findall(r'CREATE DATAFLOW\s+([^\s\(]+)', content)
        return list(set(jobs + dataflows))

    def _parse_atl_logic(self, file_path: Path, asset_name: str) -> str:
        """Extracts SQL and Transformations from an ATL block."""
        content = file_path.read_text(errors="ignore")
        
        # Extract the specific block
        # BODS blocks end with ' ); ' usually
        pattern = rf'CREATE (JOB|DATAFLOW)\s+{asset_name}.*?\);'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return f"-- Asset {asset_name} not found in ATL"

        block = match.group(0)
        logic_output = [f"-- SAP BODS Asset: {asset_name}\n"]
        
        # 1. Identify Sources and Targets
        # BODS uses 'TABLE_Target' or 'TABLE_Source' markers or specific attributes
        sources = re.findall(r'source_table\s*=\s*\'([^\']+)\'', block)
        targets = re.findall(r'target_table\s*=\s*\'([^\']+)\'', block)
        
        for s in sources: logic_output.append(f"-- Source Table: {s}")
        for t in targets: logic_output.append(f"-- Target Table: {t}")

        # 2. Query Transforms (SQL-like logic)
        # Look for SQL patterns inside the ATL
        sql_matches = re.findall(r'sql_text\s*=\s*\'([^\']+)\'', block)
        for sql in sql_matches:
            clean_sql = sql.replace('\\\'', '\'').replace('\\n', '\n')
            logic_output.append(f"/* Transformation Query */\n{clean_sql}\n")
            
        # 3. Mappings (Simple attribute grep)
        mappings = re.findall(r'([^\s]+)\s*=\s*([^\s;]+)', block)
        if mappings:
            logic_output.append(f"-- Detected {len(mappings)} property assignments/mappings.")

        return "\n".join(logic_output)
