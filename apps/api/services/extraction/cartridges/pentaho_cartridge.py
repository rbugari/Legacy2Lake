import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_cartridge import SourceCartridge

class PentahoCartridge(SourceCartridge):
    """
    Extractor for Pentaho Data Integration (Kettle) via .ktr (XML) files.
    Identifies TableInput (SQL Source) and TableOutput/InsertUpdate (Targets).
    """

    def test_connection(self) -> bool:
        path = self.config.get("path")
        if path and Path(path).exists():
            return True
        return False

    def scan_catalog(self) -> List[Dict[str, Any]]:
        """Scans for Pentaho .ktr/.kjb files."""
        path = self.config.get("path", ".")
        root = Path(path)
        assets = []
        
        if root.is_file() and root.suffix in [".ktr", ".kjb"]:
            assets.append({"name": root.stem, "type": "PENTAHO_TRANS", "metadata": {"file": str(root)}})
        elif root.is_dir():
            for ktr in root.glob("*.ktr"):
                assets.append({"name": ktr.stem, "type": "PENTAHO_TRANS", "metadata": {"file": str(ktr)}})
            for kjb in root.glob("*.kjb"):
                assets.append({"name": kjb.stem, "type": "PENTAHO_JOB", "metadata": {"file": str(kjb)}})
        
        return assets

    def extract_ddl(self, asset_name: str) -> str:
        """Parses the .ktr XML for a specific Transformation."""
        path = self.config.get("path")
        file_path = Path(path)
        
        if file_path.is_dir():
            # Search logic
            found = False
            for f in file_path.glob("*.*"):
                if f.stem == asset_name:
                    file_path = f
                    found = True
                    break
        
        return self._parse_kettle_logic(file_path, asset_name)

    def sample_data(self, asset_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        return []

    def _parse_kettle_logic(self, file_path: Path, trans_name: str) -> str:
        """Extracts steps and logic from Pentaho XML."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            logic_output = [f"-- Pentaho Transformation: {trans_name}\n"]
            
            # Pentaho Steps are usually directly under root as <step>
            for step in root.findall("step"):
                name = step.find("name")
                step_type = step.find("type")
                
                if name is None or step_type is None: continue
                
                s_name = name.text
                s_type = step_type.text
                
                # 1. Table Input (Source SQL)
                if s_type == "TableInput":
                    logic_output.append(f"-- Step: {s_name} ({s_type})")
                    sql = step.find("sql")
                    if sql is not None and sql.text:
                        logic_output.append(f"/* Source Query */\n{sql.text.strip()}\n")

                # 2. Table Output / Insert Update
                elif s_type in ["TableOutput", "InsertUpdate", "DimensionLookup"]:
                    logic_output.append(f"-- Step: {s_name} ({s_type})")
                    table = step.find("table")
                    schema = step.find("schema") # Some use schema tag
                    
                    tbl_name = table.text if table is not None else "Unknown"
                    sch_name = schema.text if schema is not None else ""
                    
                    full_table = f"{sch_name}.{tbl_name}" if sch_name else tbl_name
                    logic_output.append(f"-- Target Table: {full_table}")

                # 3. Calculator / Formula / Javascript (Transformations)
                elif s_type in ["Calculator", "Formula", "ScriptValueMod"]:
                     logic_output.append(f"-- Transformation Found: {s_name} ({s_type})")

            return "\n".join(logic_output)

        except Exception as e:
            return f"-- Error parsing Pentaho KTR: {str(e)}"
