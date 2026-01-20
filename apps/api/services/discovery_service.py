import os
import re
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from .persistence_service import PersistenceService
from apps.utm.cartridges.ssis.parser import SSISCartridge

class DiscoveryService:
    @staticmethod
    def generate_manifest(project_id: str) -> Dict[str, Any]:
        """
        Generates a comprehensive 'Triage Manifest' for Agent A.
        Includes structure, snippets of logic, and detected invocations.
        """
        project_path = PersistenceService.ensure_solution_dir(project_id)
        
        inventory = []
        tech_counts = {}
        
        # 1. Deep Scan
        for root, dirs, files in os.walk(project_path):
            if '.git' in dirs: dirs.remove('.git')
            if '__pycache__' in dirs: dirs.remove('__pycache__')
            
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, project_path).replace("\\", "/")
                
                # Basic Classification
                ext = file.split('.')[-1].lower() if '.' in file else 'no_ext'
                tech_counts[ext] = tech_counts.get(ext, 0) + 1
                
                # Deep Content Analysis
                analysis = DiscoveryService._analyze_file_content(full_path, ext)
                
                inventory.append({
                    "path": rel_path,
                    "name": file,
                    "type": DiscoveryService._map_extension_to_type(ext),
                    "size": os.path.getsize(full_path),
                    "signatures": analysis["signatures"],
                    "invocations": analysis["invocations"],
                    "snippet": analysis["snippet"], # First N chars or relevant lines
                    "metadata": analysis.get("metadata", {})
                })

        # 2. Construct Manifest
        return {
            "project_id": project_id,
            "root_path": project_path,
            "tech_stats": tech_counts,
            "file_inventory": inventory
        }

    @staticmethod
    def _map_extension_to_type(ext: str) -> str:
        if ext == 'dtsx': return 'SSIS_PACKAGE'
        if ext == 'sql': return 'SQL_SCRIPT'
        if ext == 'py': return 'PYTHON_SCRIPT'
        if ext == 'ipynb': return 'NOTEBOOK'
        if ext in ['json', 'xml', 'config', 'yaml', 'yml']: return 'CONFIG'
        return 'OTHER'

    @staticmethod
    def _analyze_file_content(file_path: str, ext: str) -> Dict[str, Any]:
        """Reads file, extracts snippets, and uses parsers if available."""
        signatures = []
        invocations = []
        snippet_lines = []
        metadata = {}
        
        # Skip binary or huge files
        if ext in ['exe', 'dll', 'png', 'jpg', 'zip']:
            return {"signatures": [], "invocations": [], "snippet": "[BINARY FILE]", "metadata": {}}

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content_str = f.read()
                
                # Snippet (first 20 lines)
                lines = content_str.splitlines()
                snippet_lines = lines[:20] 
                
                # --- SPECIALIZED PARSERS ---
                
                # SSIS (DTSX)
                if ext == 'dtsx':
                    try:
                    try:
                        parser = SSISCartridge()
                        meta_obj = parser.parse(file_path)
                        
                        summary = meta_obj.metadata.get("summary", {})
                        medulla = {
                            "data_flow_logic": meta_obj.components,
                            "control_flow_topology": meta_obj.metadata.get("control_flow_topology"),
                            "constraints": meta_obj.metadata.get("constraints")
                        }
                        
                        signatures.append("SSIS Package (Optimized Scan)")
                        if summary.get("executable_count", 0) > 0:
                            signatures.append(f"Contains {summary['executable_count']} Executables")
                        
                        # High-Quality Metadata for Architect Agents
                        metadata["logical_medulla"] = medulla
                        metadata["connections"] = summary.get("connection_managers", [])
                        
                        # Invocations (semantic detection)
                        for comp in meta_obj.components:
                            if comp.get("intent") == "SOURCE":
                                invocations.append(f"Reads from: {comp.get('name')}")
                            if comp.get("intent") == "DESTINATION":
                                invocations.append(f"Writes to: {comp.get('name')}")

                    except Exception as ssis_err:
                        signatures.append(f"SSIS Parse Error: {str(ssis_err)}")

                    
                # SQL
                elif ext == 'sql':
                    content_upper = content_str.upper()
                    if 'CREATE PROCEDURE' in content_upper: signatures.append("Stored Procedure")
                    if 'MERGE INTO' in content_upper: signatures.append("Merge Logic")
                    # Grep for EXEC
                    exec_matches = re.findall(r'EXEC\s+\[?([\w\.]+)\]?', content_str, re.IGNORECASE)
                    invocations.extend([f"Calls SP: {m}" for m in exec_matches])

                # Python
                elif ext == 'py':
                    if 'pyspark' in content_str: signatures.append("PySpark")
                    if 'pandas' in content_str: signatures.append("Pandas")
                    if 'os.system' in content_str: invocations.append("System Call (os.system)")
                    
        except Exception as e:
            snippet_lines = [f"Error reading file: {str(e)}"]

        return {
            "signatures": signatures,
            "invocations": list(set(invocations)), # unique
            "snippet": "\n".join(snippet_lines),
            "metadata": metadata
        }
    
    # Keeping scan_project for backward compatibility if needed, 
    # but re-implementing it to wrap generate_manifest could be cleaner.
    @staticmethod
    def scan_project(project_id: str) -> Dict[str, Any]:
        """Legacy wrapper: returns the simple assets list expected by frontend initially."""
        manifest = DiscoveryService.generate_manifest(project_id)
        # Map manifest back to simple assets list
        simple_assets = []
        for item in manifest["file_inventory"]:
             simple_type = 'package' if item['type'] == 'SSIS_PACKAGE' else \
                           'script' if 'SCRIPT' in item['type'] else \
                           'config' if 'CONFIG' in item['type'] else 'unused'
             
             status = 'connected' if item['invocations'] else 'pending'
             
             simple_assets.append({
                 "id": item["path"],
                 "name": item["name"],
                 "type": simple_type,
                 "status": status,
                 "tags": item["signatures"],
                 "path": item["path"],
                 "dependencies": [] # populated by Agent A now
             })
             
        return {"assets": simple_assets}
