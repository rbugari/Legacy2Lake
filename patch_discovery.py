import re

with open("apps/api/services/discovery_service.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add evidence_items to the returned dict of _analyze_file_content
content = content.replace(
'''        return {
            "signatures": signatures,
            "invocations": list(set(invocations)), # unique
            "line_count": line_count,
            "snippet": "\\n".join(snippet_lines),
            "metadata": metadata
        }''',
'''        return {
            "signatures": signatures,
            "invocations": list(set(invocations)), # unique
            "line_count": line_count,
            "snippet": "\\n".join(snippet_lines),
            "metadata": metadata,
            "evidence_items": evidence_items
        }'''
)

# 2. Add evidence_items = [] initialization
content = content.replace(
'''        signatures = []
        invocations = []
        snippet_lines = []
        metadata = {}
        line_count = 0''',
'''        signatures = []
        invocations = []
        snippet_lines = []
        metadata = {}
        line_count = 0
        evidence_items = []'''
)

# 3. Add to the skipped files list
content = content.replace(
'''            return {
                "signatures": [],
                "invocations": [],
                "line_count": 0,
                "snippet": "[BINARY FILE]",
                "metadata": {}
            }''',
'''            return {
                "signatures": [],
                "invocations": [],
                "line_count": 0,
                "snippet": "[BINARY FILE]",
                "metadata": {},
                "evidence_items": []
            }'''
)

# 4. Add to the Read Error fallback
content = content.replace(
'''                 return {
                     "signatures": ["Read Error"],
                     "invocations": [],
                     "line_count": 0,
                     "snippet": "",
                     "metadata": {}
                 }''',
'''                 return {
                     "signatures": ["Read Error"],
                     "invocations": [],
                     "line_count": 0,
                     "snippet": "",
                     "metadata": {},
                     "evidence_items": []
                 }'''
)


# 5. Connect CartridgeRegistry
old_ssis = '''                # SSIS (DTSX)
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
                        signatures.append(f"SSIS Parse Error: {str(ssis_err)}")'''

new_cartridge_logic = '''                # V5 Cartridge Registry
                from apps.utm.cartridges.registry import CartridgeRegistry
                cartridge = CartridgeRegistry.get_cartridge(ext)
                
                if cartridge:
                    try:
                        evidence_items = cartridge.parse(temp_path, content_bytes)
                        # Process backwards compatibility
                        if hasattr(cartridge, 'parse_legacy'):
                            meta_obj = cartridge.parse_legacy(temp_path)
                            summary = meta_obj.metadata.get("summary", {})
                            medulla = {
                                "data_flow_logic": meta_obj.components,
                                "control_flow_topology": meta_obj.metadata.get("control_flow_topology"),
                                "constraints": meta_obj.metadata.get("constraints")
                            }
                            signatures.append(f"{meta_obj.source_tech} Package (Optimized Scan)")
                            if summary.get("executable_count", 0) > 0:
                                signatures.append(f"Contains {summary['executable_count']} Executables")
                            metadata["logical_medulla"] = medulla
                            metadata["connections"] = summary.get("connection_managers", [])
                            
                            columns = []
                            for comp in meta_obj.components:
                                for mapping in comp.get("mappings", []):
                                    col_name = mapping.get("name") or mapping.get("target")
                                    if col_name and col_name not in [c["name"] for c in columns]:
                                        columns.append({
                                            "name": col_name,
                                            "data_type": "STRING",
                                            "nullable": True,
                                            "is_primary_key": False,
                                            "source_component": comp.get("name")
                                        })
                            if columns:
                                metadata["columns"] = columns
                                signatures.append(f"Schema: {len(columns)} columns detected")
                                
                            for comp in meta_obj.components:
                                intent = comp.get("original_intent")
                                if intent == "SOURCE":
                                    invocations.append(f"Reads from: {comp.get('name')}")
                                if intent == "DESTINATION":
                                    invocations.append(f"Writes to: {comp.get('name')}")
                                    
                    except Exception as err:
                        signatures.append(f"Cartridge Parse Error: {str(err)}")
                
                elif ext == 'dtsx':
                    signatures.append("SSIS Parse Error: Cartridge logic missing")'''

content = content.replace(old_ssis, new_cartridge_logic)

with open("apps/api/services/discovery_service.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Discovery service patched successfully.")
