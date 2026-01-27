import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_cartridge import SourceCartridge

class DataStageCartridge(SourceCartridge):
    """
    Extractor for IBM DataStage (PX) jobs via .dsx exports.
    Identifies SQL logic and transformations.
    """

    def test_connection(self) -> bool:
        # Offline mode only for now (parsing files)
        path = self.config.get("path")
        if path and Path(path).exists():
            return True
        return False

    def scan_catalog(self) -> List[Dict[str, Any]]:
        """Scans the path for .dsx files and extracts job names."""
        path = self.config.get("path", ".")
        root = Path(path)
        assets = []
        
        if root.is_file() and root.suffix == ".dsx":
            jobs = self._get_jobs_from_dsx(root)
            for job in jobs:
                assets.append({"name": job, "type": "DS_JOB", "metadata": {"file": str(root)}})
        elif root.is_dir():
            for dsx_file in root.glob("*.dsx"):
                jobs = self._get_jobs_from_dsx(dsx_file)
                for job in jobs:
                    assets.append({"name": job, "type": "DS_JOB", "metadata": {"file": str(dsx_file)}})
        
        return assets

    def extract_ddl(self, asset_name: str) -> str:
        """
        Parses the DSX for a specific job and returns a represented 'SQL-like' 
        logic that the Architect Agent can understand.
        """
        path = self.config.get("path")
        # In a real scenario we'd find which file contains asset_name
        # For now, we assume we parse the config path
        dsx_path = Path(path)
        if dsx_path.is_dir():
            # Search in directory (simplified)
            for f in dsx_path.glob("*.dsx"):
                content = f.read_text(errors="ignore")
                if f'Identifier "{asset_name}"' in content:
                    dsx_path = f
                    break

        return self._parse_dsx_job_logic(dsx_path, asset_name)

    def sample_data(self, asset_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        return [] # DataStage jobs don't have direct data samples in DSX

    def _get_jobs_from_dsx(self, file_path: Path) -> List[str]:
        content = file_path.read_text(errors="ignore")
        # Regex to find BEGIN DSJOB ... Identifier "JobName"
        jobs = re.findall(r'BEGIN DSJOB\s+Identifier "([^"]+)"', content)
        return jobs

    def _parse_dsx_job_logic(self, file_path: Path, job_name: str) -> str:
        """
        Extracts Stages, Queries and Transformers from a DSX job.
        """
        content = file_path.read_text(errors="ignore")
        # Extract the specific job block
        job_pattern = rf'BEGIN DSJOB\s+Identifier "{job_name}".*?END DSJOB'
        job_block_match = re.search(job_pattern, content, re.DOTALL)
        
        if not job_block_match:
            return "-- Job not found in DSX"
        
        job_block = job_block_match.group(0)
        
        # Extract stages
        stages = re.findall(r'BEGIN DSSTAGE\s+(.*?)END DSSTAGE', job_block, re.DOTALL)
        
        logic_output = [f"-- DataStage Job: {job_name}\n"]
        
        for stage in stages:
            stage_name = re.search(r'Identifier "([^"]+)"', stage)
            stage_type = re.search(r'StageType "([^"]+)"', stage)
            
            if not stage_name: continue
            s_name = stage_name.group(1)
            s_type = stage_type.group(1) if stage_type else "Unknown"
            
            logic_output.append(f"-- Stage: {s_name} ({s_type})")
            
            # Look for SQL queries (Source/Target/Lookup)
            query = re.search(r'Name "QueryText"\s+Value "([^"]+)"', stage)
            if query:
                clean_q = query.group(1).replace('\\"', '"').replace('\\n', '\n')
                logic_output.append(f"/* Source Query */\n{clean_q}\n")
            
            table = re.search(r'Name "TableName"\s+Value "([^"]+)"', stage)
            if table:
                logic_output.append(f"-- Target Table: {table.group(1)}")
                
            # Transformer logic (simplified)
            if "PxTransformer" in s_type:
                logic_output.append("-- Transformer Mapping detected (Derivations omitted for brevity in placeholder)")

        return "\n".join(logic_output)
