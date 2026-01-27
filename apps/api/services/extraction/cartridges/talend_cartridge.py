import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_cartridge import SourceCartridge

class TalendCartridge(SourceCartridge):
    """
    Extractor for Talend Open Studio / Data Fabric Jobs via .item (XML) files.
    Identifies tInput (SQL), tOutput, and tMap transformations.
    """

    def test_connection(self) -> bool:
        path = self.config.get("path")
        if path and Path(path).exists():
            return True
        return False

    def scan_catalog(self) -> List[Dict[str, Any]]:
        """Scans for Talend .item files."""
        path = self.config.get("path", ".")
        root = Path(path)
        assets = []
        
        if root.is_file() and root.suffix == ".item":
            assets.append({"name": root.stem, "type": "TALEND_JOB", "metadata": {"file": str(root)}})
        elif root.is_dir():
            for item in root.glob("*.item"):
                assets.append({"name": item.stem, "type": "TALEND_JOB", "metadata": {"file": str(item)}})
        
        return assets

    def extract_ddl(self, asset_name: str) -> str:
        """Parses the .item XML for a specific Job."""
        path = self.config.get("path")
        item_path = Path(path)
        
        if item_path.is_dir():
            for f in item_path.glob("*.item"):
                if f.stem == asset_name:
                    item_path = f
                    break
        
        return self._parse_talend_logic(item_path, asset_name)

    def sample_data(self, asset_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        return []

    def _parse_talend_logic(self, file_path: Path, job_name: str) -> str:
        """Extracts components and logic from Talend XML."""
        try:
            # Register namespaces to avoid "unbound prefix" errors
            ET.register_namespace('talendfile', "platform:/resource/org.talend.model/model/TalendFile.xsd")
            ET.register_namespace('xmi', "http://www.omg.org/XMI")
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            logic_output = [f"-- Talend Job: {job_name}\n"]
            
            # Talend Namespace issues are common, usually ignored in simple ElementTree usage 
            # if we use relative paths appropriately or strip namespaces.
            # Here we iterate all 'node' elements.
            
            for node in root.findall(".//node"):
                comp_name = node.get("componentName")
                unique_name = "Unknown"
                
                # Retrieve unique name (parameter name='UNIQUE_NAME')
                for param in node.findall("elementParameter"):
                    if param.get("name") == "UNIQUE_NAME":
                        unique_name = param.get("value")
                
                if not self._known_component(comp_name): continue

                # 1. Database Inputs (tMSSqlInput, tOracleInput, tDBInput, etc)
                if "Input" in comp_name:
                    logic_output.append(f"-- Component: {unique_name} ({comp_name})")
                    for param in node.findall("elementParameter"):
                        if param.get("name") == "QUERY":
                            query = param.get("value")
                            if query:
                                clean_q = query.replace('&quot;', '"').replace('\\n', '\n')
                                logic_output.append(f"/* Source Query */\n{clean_q}\n")

                # 2. Database Outputs
                elif "Output" in comp_name:
                    for param in node.findall("elementParameter"):
                        if param.get("name") == "TABLE":
                            table = param.get("value")
                            logic_output.append(f"-- Target Table: {table} ({comp_name})")

                # 3. tMap (Transformations)
                elif comp_name == "tMap":
                    logic_output.append(f"-- Transformation Stage: {unique_name} (tMap)")
                    # tMap logic is often nested in specific metadata structures distinct from standard nodes
                    # but typically inside node/nodeData section
                    node_data = node.find("nodeData")
                    if node_data is not None:
                         # Looking for MapperTableEntries (simplified)
                         # This needs more complex parsing for full logic, but we report presence
                         inputs = len(node_data.findall(".//inputTables"))
                         outputs = len(node_data.findall(".//outputTables"))
                         logic_output.append(f"-- tMap Complexity: {inputs} Inputs, {outputs} Outputs")

            return "\n".join(logic_output)

        except Exception as e:
            return f"-- Error parsing Talend Item: {str(e)}"

    def _known_component(self, name):
        # Expanded list of relevant components
        relevant = ["Input", "Output", "Row", "Map"]
        if not name: return False
        return any(r in name for r in relevant)
