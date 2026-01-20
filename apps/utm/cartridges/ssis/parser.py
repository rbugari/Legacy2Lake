from apps.utm.core.interfaces import BaseParser, MetadataObject
from lxml import etree
import hashlib
from typing import Dict, List, Any

class SSISCartridge(BaseParser):
    """
    Cartridge for SSIS (.dtsx) Ingestion.
    Implements BaseParser to standardize the 'Ear' of the system.
    """
    
    def __init__(self):
        self.namespaces = {
            'DTS': 'www.microsoft.com/SqlServer/Dts',
            'SQLTask': 'www.microsoft.com/sqlserver/dts/tasks/sqltask'
        }

    def parse(self, file_path: str) -> MetadataObject:
        """
        Reads a .dtsx file and returns a standardized MetadataObject.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        parser = _LegacySSISLogic(content, self.namespaces)
        medulla = parser.get_logical_medulla()
        
        # Transform legacy 'medulla' dict into standardized MetadataObject
        # This acts as the Adapter layer
        return MetadataObject(
            source_name=file_path.split("\\")[-1],
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
            connections.append({
                "name": conn.get(f'{{{self.namespaces["DTS"]}}}ObjectName'),
                "id": conn.get(f'{{{self.namespaces["DTS"]}}}DTSID'),
                "connection_string": self.tree.xpath(f'.//DTS:Property[@DTS:Name="ConnectionString"]/text()', namespaces=self.namespaces)
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
