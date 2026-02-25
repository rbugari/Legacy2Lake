import os
import re
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from .persistence_service import PersistenceService
from apps.utm.cartridges.ssis.parser import SSISCartridge

class DiscoveryService:
    @staticmethod
    def generate_manifest(project_id: str, tenant_id: str = None, user_context: List[Dict[str, Any]] = None, source_folder: str = None) -> Dict[str, Any]:
        """
        Generates a comprehensive 'Triage Manifest' for Agent A.
        Includes structure, snippets of logic, and detected invocations.
        Scans the specified folder (defaults to Triage) where uploaded objects are stored.
        Uses StorageProvider for abstraction (R2/Local).
        """
        # Get base project directory (key prefix)
        project_base = PersistenceService.ensure_solution_dir(project_id, tenant_id)
        storage = PersistenceService.get_storage()
        
        target_folder = source_folder or PersistenceService.STAGE_TRIAGE
        
        # [Refinement] Find target folder case-insensitively
        triage_path = None
        try:
            root_items = storage.list_files(project_base, recursive=False)
            triage_names = [target_folder.lower(), "source", "triage", "inbound"]
            
            for item in root_items:
                if item["type"] == "folder" and item["name"].lower() in triage_names:
                    triage_path = item["path"]
                    break
        except Exception as e:
            print(f"[Discovery] Error listing project root: {e}")

        # Fallback if not found: use default
        if not triage_path:
            triage_path = f"{project_base.rstrip('/')}/{target_folder}"
        
        inventory = []
        tech_counts = {}
        
        # 1. Deep Scan using StorageProvider
        try:
            files_tree = storage.list_files(triage_path, recursive=True)
        except Exception as e:
            print(f"Discovery Scan Error: {e}")
            files_tree = []

        # Helper to flatten tree
        def flatten_items(nodes):
            items = []
            for node in nodes:
                if node["type"] == "folder":
                    if node.get("children"):
                        items.extend(flatten_items(node["children"]))
                else:
                    items.append(node)
            return items

        flat_files = flatten_items(files_tree)
        
        for file_node in flat_files:
            file_name = file_node["name"]
            full_path = file_node["path"] # This is the storage Key
            
            # [Fix] Exclude system generated files
            if file_name in ['triage.log', 'layout.json', 'migration.log', 'refinement.log', 'manifest.json']:
                continue

            rel_path = full_path # Key is mostly the relative path in R2 context, or we can strip project prefix if needed for UI?
            # For Manifest, full path/key is fine as unique ID.
            
            # Basic Classification
            ext = file_name.split('.')[-1].lower() if '.' in file_name else 'no_ext'
            tech_counts[ext] = tech_counts.get(ext, 0) + 1
            
            # Deep Content Analysis
            # We pass 'storage' so it can read the file content
            analysis = DiscoveryService._analyze_file_content(storage, full_path, ext)
            
            inventory.append({
                "path": rel_path,
                "name": file_name,
                "type": DiscoveryService._map_extension_to_type(ext),
                "size": file_node["size"],
                "lines": analysis["line_count"],
                "signatures": analysis["signatures"],
                "invocations": analysis["invocations"],
                "snippet": analysis["snippet"], 
                "metadata": analysis.get("metadata", {})
            })

        # 2. Extract Support Intelligence (schemas, volumes, rules)
        # We consolidate snippets/metadata from files in the Source folder that look like support docs
        support_intel = []
        for item in inventory:
            if item["type"] in ["CONFIG", "XML_DATA", "OTHER"] or item["name"].lower() in ["readme.md", "volumes.txt", "schema.sql"]:
                # If it has specific signatures or interesting snippets
                if "Schema Definition" in item["signatures"] or "Volumetric Data" in item["signatures"]:
                    # Sanitize snippet to remove null bytes and non-printable chars (for binary files like DOCX)
                    sanitized_snippet = DiscoveryService._sanitize_snippet(item["snippet"])
                    if sanitized_snippet:  # Only add if there's meaningful content after sanitization
                        support_intel.append({
                            "file": item["name"],
                            "type": item["type"],
                            "intel": sanitized_snippet[:200] + "..." # Keep it concise for the report
                        })

        # 3. Construct Manifest
        return {
            "project_id": project_id,
            "root_path": triage_path,
            "tech_stats": tech_counts,
            "file_inventory": inventory,
            "support_intelligence": support_intel,
            "user_context": user_context or []
        }

    @staticmethod
    def _map_extension_to_type(ext: str) -> str:
        if ext == 'dtsx': return 'SSIS_PACKAGE'
        if ext == 'dsx': return 'DS_JOB'
        if ext == 'atl': return 'BODS_JOB'
        if ext == 'item': return 'TALEND_JOB'
        if ext == 'ktr': return 'PENTAHO_TRANS'
        if ext == 'kjb': return 'PENTAHO_JOB'
        if ext == 'sql': return 'SQL_SCRIPT'
        if ext == 'py': return 'PYTHON_SCRIPT'
        if ext == 'ipynb': return 'NOTEBOOK'
        if ext in ['json', 'config', 'yaml', 'yml']: return 'CONFIG'
        if ext == 'xml': return 'XML_DATA' 
        return 'OTHER'

    @staticmethod
    def _sanitize_snippet(snippet: str) -> str:
        """Remove null bytes and non-printable characters that cause PostgreSQL errors."""
        if not snippet:
            return ""
        # Remove null bytes and other problematic Unicode characters
        sanitized = snippet.replace('\x00', '').replace('\u0000', '')
        # Keep only printable ASCII + common Unicode (remove control chars)
        sanitized = ''.join(char for char in sanitized if char.isprintable() or char in ['\n', '\r', '\t'])
        return sanitized.strip()

    @staticmethod
    def _analyze_file_content(storage, file_path_key: str, ext: str) -> Dict[str, Any]:
        """Reads file from Storage, extracts snippets, and uses parsers if available."""
        import tempfile
        from pathlib import Path
        
        signatures = []
        invocations = []
        snippet_lines = []
        metadata = {}
        
        # Skip binary or huge files
        if ext in ['exe', 'dll', 'png', 'jpg', 'zip']:
            return {"signatures": [], "invocations": [], "snippet": "[BINARY FILE]", "metadata": {}}

        temp_path = None
        try:
            # READ CONTENT FROM STORAGE
            content_bytes = storage.read_file(file_path_key, is_binary=True)
            if content_bytes is None:
                 return {"signatures": ["Read Error"], "invocations": [], "snippet": "", "metadata": {}}

            try:
                content_str = content_bytes.decode('utf-8', errors='ignore')
            except:
                content_str = "[Binary Content]"
                
            # Line Count & Snippet (first 20 lines)
            lines = content_str.splitlines()
            line_count = len(lines)
            snippet_lines = lines[:20] 
            
            # --- SUPPORT INTELLIGENCE HEURISTICS ---
            # Search for volume patterns (e.g., "1.5 TB", "100M rows", "Volume:")
            if re.search(r'(\d+(\.\d+)?\s*(TB|GB|MB|Rows|Registros))|Volume:', content_str, re.IGNORECASE):
                signatures.append("Volumetric Data")
            
            # Search for schema patterns (e.g., "CREATE TABLE", "Schema:", "Column")
            if re.search(r'CREATE\s+TABLE|Schema:|Columna|Column\s+\w+', content_str, re.IGNORECASE):
                signatures.append("Schema Definition")
            
            # --- SPECIALIZED PARSERS (Require File Path usually) ---
            # We create a temp file for parsers
            
            # Only create temp file if we have a parser for this extension
            if ext in ['dtsx', 'dsx', 'xml', 'atl', 'item', 'ktr', 'kjb']:
                fd, temp_path = tempfile.mkstemp(suffix=f".{ext}")
                os.close(fd)
                with open(temp_path, 'wb') as f:
                    f.write(content_bytes)


                # SSIS (DTSX)
                if ext == 'dtsx':
                    try:
                        parser = SSISCartridge()
                        meta_obj = parser.parse(temp_path)
                        
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
                        
                        # Sprint 10: Extract column metadata from components
                        columns = []
                        for comp in meta_obj.components:
                            # Extract from mappings (inputColumn/outputColumn)
                            for mapping in comp.get("mappings", []):
                                col_name = mapping.get("name") or mapping.get("target")
                                if col_name and col_name not in [c["name"] for c in columns]:
                                    columns.append({
                                        "name": col_name,
                                        "data_type": "STRING",  # Default, parser doesn't extract types
                                        "nullable": True,
                                        "is_primary_key": False,
                                        "source_component": comp.get("name")
                                    })
                        
                        if columns:
                            metadata["columns"] = columns
                            signatures.append(f"Schema: {len(columns)} columns detected")
                        
                        # Invocations (semantic detection)
                        for comp in meta_obj.components:
                            if comp.get("intent") == "SOURCE":
                                invocations.append(f"Reads from: {comp.get('name')}")
                            if comp.get("intent") == "DESTINATION":
                                invocations.append(f"Writes to: {comp.get('name')}")

                    except Exception as ssis_err:
                        signatures.append(f"SSIS Parse Error: {str(ssis_err)}")

                # DataStage (DSX)
                elif ext == 'dsx':
                    try:
                        from .extraction.cartridges.datastage_cartridge import DataStageCartridge
                        parser = DataStageCartridge({"path": temp_path})
                        jobs = parser._get_jobs_from_dsx(Path(temp_path))
                        
                        signatures.append("DataStage Export (PX)")
                        if jobs:
                            signatures.append(f"Found {len(jobs)} Jobs")
                            # Extract logic for the first job as a sample for Agent A
                            metadata["ds_logic"] = parser._parse_dsx_job_logic(Path(temp_path), jobs[0])
                            
                    except Exception as dsx_err:
                        signatures.append(f"DataStage Parse Error: {str(dsx_err)}")

                # Informatica (XML)
                elif ext == 'xml':
                    if '<POWERMART' in content_str:
                        try:
                            from .extraction.cartridges.informatica_cartridge import InformaticaCartridge
                            parser = InformaticaCartridge({"path": temp_path})
                            mappings = parser._get_mappings_from_xml(Path(temp_path))
                            
                            signatures.append("Informatica PowerCenter XML")
                            if mappings:
                                signatures.append(f"Found {len(mappings)} Mappings")
                                metadata["infa_logic"] = parser._parse_mapping_logic(Path(temp_path), mappings[0])
                        except Exception as infa_err:
                            signatures.append(f"Informatica Parse Error: {str(infa_err)}")
                    else:
                        signatures.append("Generic XML Config")

                # SAP BODS (ATL)
                elif ext == 'atl':
                    try:
                        from .extraction.cartridges.sap_bods_cartridge import SapBodsCartridge
                        parser = SapBodsCartridge({"path": temp_path})
                        assets = parser._get_jobs_from_atl(Path(temp_path))
                        
                        signatures.append("SAP BODS / Data Integrator ATL")
                        if assets:
                            signatures.append(f"Found {len(assets)} Jobs/DFs")
                            # Extract logic for the first asset
                            metadata["bods_logic"] = parser._parse_atl_logic(Path(temp_path), assets[0])
                    except Exception as bods_err:
                        signatures.append(f"SAP BODS Parse Error: {str(bods_err)}")

                # Talend (Item)
                elif ext == 'item':
                    if 'talendfile:ProcessType' in content_str:
                        try:
                            from .extraction.cartridges.talend_cartridge import TalendCartridge
                            parser = TalendCartridge({"path": temp_path})
                            # Scan returns basic list, we extract logic for the specific item
                            job_name = os.path.splitext(os.path.basename(file_path_key))[0]
                            signatures.append("Talend Open Studio Job")
                            metadata["talend_logic"] = parser._parse_talend_logic(Path(temp_path), job_name)
                        except Exception as tal_err:
                            signatures.append(f"Talend Parse Error: {str(tal_err)}")

                # Pentaho (Kettle)
                elif ext in ['ktr', 'kjb']:
                    if '<transformation>' in content_str or '<job>' in content_str:
                        try:
                            from .extraction.cartridges.pentaho_cartridge import PentahoCartridge
                            parser = PentahoCartridge({"path": temp_path})
                            # Extract logic for the specific file
                            trans_name = os.path.splitext(os.path.basename(file_path_key))[0]
                            signatures.append("Pentaho Data Integration (Kettle)")
                            metadata["kettle_logic"] = parser._parse_kettle_logic(Path(temp_path), trans_name)
                        except Exception as pdi_err:
                            signatures.append(f"Pentaho Parse Error: {str(pdi_err)}")

            # SQL (No temp file needed, parse string)
            elif ext == 'sql':
                content_upper = content_str.upper()
                if 'CREATE PROCEDURE' in content_upper: signatures.append("Stored Procedure")
                if 'MERGE INTO' in content_upper: signatures.append("Merge Logic")
                # Grep for EXEC
                exec_matches = re.findall(r'EXEC\s+\[?([\w\.]+)\]?', content_str, re.IGNORECASE)
                invocations.extend([f"Calls SP: {m}" for m in exec_matches])

            # Python (No temp file needed)
            elif ext == 'py':
                if 'pyspark' in content_str: signatures.append("PySpark")
                if 'pandas' in content_str: signatures.append("Pandas")
                if 'os.system' in content_str: invocations.append("System Call (os.system)")
                    
        except Exception as e:
            snippet_lines = [f"Error reading/analyzing file: {str(e)}"]
        finally:
            # Cleanup temp file if created
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except: pass

        return {
            "signatures": signatures,
            "invocations": list(set(invocations)), # unique
            "line_count": line_count,
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
                 "lines": item["lines"],
                 "dependencies": [], # populated by Agent A now
                 "frequency": item.get("frequency", "DAILY"),
                 "load_strategy": item.get("load_strategy", "FULL_OVERWRITE"),
                 "criticality": item.get("criticality", "P3"),
                 "is_pii": item.get("is_pii", False),
                 "masking_rule": item.get("masking_rule"),
                 "business_entity": item.get("business_entity"),
                 "target_name": item.get("target_name")
             })
             
        return {"assets": simple_assets}
