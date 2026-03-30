from apps.utm.core.interfaces import BaseParser, MetadataObject, CartridgeBase, EvidenceItem, ProcessHint
from lxml import etree
import hashlib
from typing import Dict, List, Any
import json

class SSISCartridge(CartridgeBase, BaseParser):
    """
    Cartridge for SSIS (.dtsx) Ingestion.
    Implements CartridgeBase (V5) and optionally BaseParser (V4) for backwards compatibility.
    """
    
    def __init__(self):
        self.namespaces = {
            'DTS': 'www.microsoft.com/SqlServer/Dts',
            'SQLTask': 'www.microsoft.com/sqlserver/dts/tasks/sqltask'
        }

    def can_handle(self, ext: str, content_hint: str = None) -> bool:
        return ext.lower() == 'dtsx'

    def parse(self, file_path: str, content: bytes) -> List[EvidenceItem]:
        """[V5] Extracts deterministic evidence items from the file."""
        try:
            content_str = content.decode('utf-8')
        except:
            content_str = content.decode('latin1', errors='ignore')

        parser = _LegacySSISLogic(content_str, self.namespaces)
        medulla = parser.get_logical_medulla()
        
        items = []
        
        # 1. Package Summary as Evidence
        summary = medulla.get("summary", {})
        items.append(EvidenceItem(
            source_path=file_path,
            source_block_type="package_summary",
            snippet=json.dumps(summary, indent=2),
            line_start=None,
            line_end=None,
            parser_name="SSISCartridge",
            extraction_method="parser_deterministic",
            confidence=1.0,
            rationale="Deterministic extraction from SSIS Root Properties"
        ))
        
        # 2. Control Flow Executables
        topology = medulla.get("control_flow_topology", [])
        for ex in topology:
            items.append(EvidenceItem(
                source_path=file_path,
                source_block_type="executable",
                snippet=json.dumps(ex, indent=2),
                line_start=None, line_end=None,
                parser_name="SSISCartridge",
                extraction_method="parser_deterministic",
                confidence=1.0,
                rationale=f"Extracted Executable: {ex.get('name')}"
            ))
            
        # 3. Data Flow Components
        components = medulla.get("data_flow_logic", [])
        for comp in components:
            items.append(EvidenceItem(
                source_path=file_path,
                source_block_type="data_flow_component",
                snippet=json.dumps(comp, indent=2),
                line_start=None, line_end=None,
                parser_name="SSISCartridge",
                extraction_method="parser_deterministic",
                confidence=1.0,
                rationale=f"Extracted Component: {comp.get('name')} ({comp.get('type')})"
            ))

        return items

    def parse_legacy(self, content_or_path: str, name: str = None) -> MetadataObject:
        """[V4] Parses a .dtsx (either raw content or path) and returns a MetadataObject."""
        if "<DTS:Executable" in content_or_path or "<?xml" in content_or_path:
            content = content_or_path
            source_name = name or "unknown.dtsx"
        else:
            # Legacy Path support
            with open(content_or_path, 'r', encoding='utf-8') as f:
                content = f.read()
            source_name = content_or_path.split("\\")[-1]
            
        parser = _LegacySSISLogic(content, self.namespaces)
        medulla = parser.get_logical_medulla()
        
        # Transform legacy 'medulla' dict into standardized MetadataObject
        # This acts as the Adapter layer
        return MetadataObject(
            source_name=source_name,
            source_tech="SSIS",
            raw_content=content,
            components=medulla.get("data_flow_logic", []),
            metadata={
                "summary": medulla.get("summary"),
                "control_flow_topology": medulla.get("control_flow_topology"),
                "constraints": medulla.get("constraints")
            }
        )

# --- Internal Logic Implementation (Moved from old service) ---

class _LegacySSISLogic:
    """Encapsulates the XML parsing logic to keep the Cartridge clean."""
    
    def __init__(self, content: str, namespaces: dict):
        self.content = content
        # Handle potential encoding issues in XML string
        try:
            self.tree = etree.fromstring(content.encode('utf-8'))
        except:
             # Fallback for some windows encodings
            self.tree = etree.fromstring(content.encode('latin1'))
            
        self.namespaces = namespaces

    def get_summary(self) -> Dict[str, Any]:
        """Returns a high-level summary of the package."""
        return {
            "creator_name": self.tree.xpath('//@DTS:CreatorName', namespaces=self.namespaces),
            "version_id": self.tree.xpath('//@DTS:VersionID', namespaces=self.namespaces),
            "executable_count": len(self.tree.xpath('//DTS:Executable', namespaces=self.namespaces)),
            "connection_managers": self.get_connection_managers()
        }

    def get_connection_managers(self) -> List[Dict[str, str]]:
        connections = []
        for conn in self.tree.xpath('//DTS:ConnectionManager', namespaces=self.namespaces):
            # Extract connection string from child property (use conn.xpath, not self.tree.xpath)
            conn_strings = conn.xpath('.//DTS:Property[@DTS:Name="ConnectionString"]/text()', namespaces=self.namespaces)
            conn_string = str(conn_strings[0]) if conn_strings else ""
            
            connections.append({
                "name": conn.get(f'{{{self.namespaces["DTS"]}}}ObjectName'),
                "id": conn.get(f'{{{self.namespaces["DTS"]}}}DTSID'),
                "connection_string": conn_string
            })
        return connections

    def extract_executables(self) -> List[Dict[str, Any]]:
        execs = []
        for ex in self.tree.xpath('//DTS:Executable', namespaces=self.namespaces):
            execs.append({
                "id": ex.get(f'{{{self.namespaces["DTS"]}}}DTSID'),
                "name": ex.get(f'{{{self.namespaces["DTS"]}}}ObjectName'),
                "type": ex.get(f'{{{self.namespaces["DTS"]}}}ExecutableType'),
                "description": ex.get(f'{{{self.namespaces["DTS"]}}}Description')
            })
        return execs

    def extract_precedence_constraints(self) -> List[Dict[str, str]]:
        constraints = []
        for pc in self.tree.xpath('//DTS:PrecedenceConstraint', namespaces=self.namespaces):
            constraints.append({
                "source": pc.get(f'{{{self.namespaces["DTS"]}}}From'),
                "target": pc.get(f'{{{self.namespaces["DTS"]}}}To'),
                "id": pc.get(f'{{{self.namespaces["DTS"]}}}DTSID')
            })
        return constraints

    def get_logical_medulla(self) -> Dict[str, Any]:
        return {
            "summary": self.get_summary(),
            "data_flow_logic": self.get_data_flow_components(),
            "control_flow_topology": self.extract_executables(),
            "constraints": self.extract_precedence_constraints()
        }

    def get_data_flow_components(self) -> List[Dict[str, Any]]:
        components = []
        for comp in self.tree.xpath('//*[local-name()="component"]'):
            ref_id = comp.get('refId') 
            name = comp.get('name')
            contact_info = comp.get('contactInfo') or ""
            
            comp_type = "UNKNOWN"
            if any(x in contact_info or x in name for x in ["Lookup", "Búsqueda"]):
                comp_type = "LOOKUP"
            elif any(x in contact_info or x in name for x in ["Source", "Origen"]):
                comp_type = "SOURCE"
            elif any(x in contact_info or x in name for x in ["Destination", "Destino"]):
                comp_type = "DESTINATION"
            elif "Derived column" in contact_info.lower():
                comp_type = "TRANSFORMATION_DERIVED"
            
            logic = {}
            for prop in comp.xpath('.//*[local-name()="property"]'):
                p_name = prop.get('name')
                if p_name in ["SqlCommand", "OpenRowset", "TableOrViewName", "SqlStatementSource"]:
                    logic[p_name] = prop.text.strip() if prop.text else ""

            mappings = []
            for input_col in comp.xpath('.//*[local-name()="inputColumn"]'):
                mappings.append({
                    "source": input_col.get("externalMetadataColumnId"),
                    "target": input_col.get("name"),
                    "usage": "INPUT"
                })
            for output_col in comp.xpath('.//*[local-name()="outputColumn"]'):
                 mappings.append({
                    "name": output_col.get("name"),
                    "usage": "OUTPUT"
                })

            # Type Mapping for LogicMapper (Universal Kernel)
            mapper_type = "UNKNOWN"
            if comp_type == "SOURCE": mapper_type = "SOURCE_DB"
            elif comp_type == "DESTINATION": mapper_type = "DESTINATION_DB"
            elif comp_type == "LOOKUP": mapper_type = "LOOKUP"
            elif comp_type == "TRANSFORMATION_DERIVED": mapper_type = "DERIVED_COLUMN"
            else: mapper_type = comp_type # Fallback

            components.append({
                "type": mapper_type, # Fixed key for LogicMapper
                "name": name,
                "raw_properties": logic, # Fixed key for LogicMapper
                "mappings": mappings,
                "ref_id": ref_id,
                "original_intent": comp_type
            })
            
        return components
