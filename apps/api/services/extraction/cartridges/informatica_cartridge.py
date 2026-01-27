import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_cartridge import SourceCartridge

class InformaticaCartridge(SourceCartridge):
    """
    Extractor for Informatica PowerCenter mappings via XML exports.
    Identifies SQL (Source Qualifiers) and Transformation logic.
    """

    def test_connection(self) -> bool:
        # Offline mode only: check if XML exists
        path = self.config.get("path")
        if path and Path(path).exists():
            return True
        return False

    def scan_catalog(self) -> List[Dict[str, Any]]:
        """Scans XML/Directories for Informatica Mappings."""
        path = self.config.get("path", ".")
        root = Path(path)
        assets = []
        
        if root.is_file() and root.suffix == ".xml":
            mappings = self._get_mappings_from_xml(root)
            for m in mappings:
                assets.append({"name": m, "type": "INFA_MAPPING", "metadata": {"file": str(root)}})
        elif root.is_dir():
            for xml_file in root.glob("*.xml"):
                mappings = self._get_mappings_from_xml(xml_file)
                for m in mappings:
                    assets.append({"name": m, "type": "INFA_MAPPING", "metadata": {"file": str(xml_file)}})
        
        return assets

    def extract_ddl(self, asset_name: str) -> str:
        """Parses the XML for a specific Mapping and extracts its internal logic."""
        path = self.config.get("path")
        xml_path = Path(path)
        
        # If directory, find the right file (simplified)
        if xml_path.is_dir():
            for f in xml_path.glob("*.xml"):
                content = f.read_text(errors="ignore")
                if f'MAPPING NAME="{asset_name}"' in content:
                    xml_path = f
                    break
        
        return self._parse_mapping_logic(xml_path, asset_name)

    def sample_data(self, asset_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        return []

    def _get_mappings_from_xml(self, file_path: Path) -> List[str]:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            # Informatica structure: POWERMART -> REPOSITORY -> FOLDER -> MAPPING
            mappings = []
            for mapping in root.findall(".//MAPPING"):
                mappings.append(mapping.get("NAME"))
            return mappings
        except:
            return []

    def _parse_mapping_logic(self, file_path: Path, mapping_name: str) -> str:
        """Extracts Source Qualifiers (SQL) and Transformations from a mapping."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            mapping_node = None
            for m in root.findall(".//MAPPING"):
                if m.get("NAME") == mapping_name:
                    mapping_node = m
                    break
            
            if mapping_node is None:
                return f"-- Mapping {mapping_name} not found in XML"

            logic_output = [f"-- Informatica Mapping: {mapping_name}\n"]
            
            # 1. Sources & Source Qualifiers
            # In Informatica, SOURCE_QUALIFIER is a TRANSFORMATION type
            for trans in mapping_node.findall("TRANSFORMATION"):
                t_type = trans.get("TYPE")
                t_name = trans.get("NAME")
                
                logic_output.append(f"-- Transformation: {t_name} ({t_type})")
                
                # Extract SQL Override if present (Source Qualifier)
                if t_type == "Source Qualifier":
                    for field in trans.findall(".//TABLEATTRIBUTE"):
                        if field.get("NAME") == "Sql Query":
                            sql = field.get("VALUE")
                            if sql:
                                logic_output.append(f"/* Source Query Override */\n{sql}\n")
            
            # 2. Target Information (Simplified)
            for instance in mapping_node.findall("INSTANCE"):
                if instance.get("TRANSFORMATION_TYPE") == "Target Definition":
                    logic_output.append(f"-- Target Table: {instance.get('TRANSFORMATION_NAME')}")

            # 3. Mappings / Expressions (Detection)
            exp_count = len(mapping_node.findall(".//TRANSFORMATION[@TYPE='Expression']"))
            if exp_count > 0:
                logic_output.append(f"-- Detected {exp_count} Expression transformations with business logic.")

            return "\n".join(logic_output)
            
        except Exception as e:
            return f"-- Error parsing Informatica XML: {str(e)}"
