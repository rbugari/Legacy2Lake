from apps.utm.core.interfaces import BaseParser, MetadataObject
import xml.etree.ElementTree as ET
import os

class SSISParser(BaseParser):
    def parse(self, file_path: str) -> MetadataObject:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Namespaces mostly used in SSIS 2012+
        ns = {'DTS': 'www.microsoft.com/SqlServer/Dts'}
        
        package_name = root.attrib.get(f"{{{ns['DTS']}}}ObjectName", "UnknownPackage")
        
        components_metadata = []
        
        # Find all Executables (Pipelines)
        # We recursively search for Pipelines
        for pipeline in root.findall(".//DTS:Executable[@DTS:CreationName='Microsoft.Pipeline']", ns):
            pipeline_name = pipeline.attrib.get(f"{{{ns['DTS']}}}ObjectName")
            
            # Inside Pipeline, find ObjectData -> pipeline -> components
            obj_data = pipeline.find(f"DTS:ObjectData", ns)
            if obj_data is not None:
                pipeline_xml = obj_data.find("pipeline") 
                if pipeline_xml is not None:
                    components = pipeline_xml.find("components")
                    if components is not None:
                        for component in components.findall("component"):
                            comp_name = component.attrib.get("name")
                            comp_class_id = component.attrib.get("componentClassID")
                            
                            # Extract Properties
                            props = {}
                            properties_node = component.find("properties")
                            if properties_node is not None:
                                for prop in properties_node.findall("property"):
                                    p_name = prop.attrib.get("name")
                                    p_val = prop.text
                                    props[p_name] = p_val
                            
                            # Identify Component Type
                            tech_type = "UNKNOWN"
                            if "OLEDBSource" in comp_class_id:
                                tech_type = "SOURCE_DB"
                            elif "OLEDBDestination" in comp_class_id:
                                tech_type = "DESTINATION_DB"
                            elif "Lookup" in comp_class_id:
                                tech_type = "LOOKUP"
                            elif "DerivedColumn" in comp_class_id:
                                tech_type = "TRANSFORM"
                            elif "SlowlyChangingDimension" in comp_class_id:
                                tech_type = "SCD"
                            
                            components_metadata.append({
                                "pipeline": pipeline_name,
                                "name": comp_name,
                                "type": tech_type,
                                "raw_properties": props,
                                "refId": component.attrib.get("refId")
                            })

        # Read raw content for traceability
        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()

        return MetadataObject(
            source_name=os.path.basename(file_path),
            source_tech="SSIS",
            raw_content=raw_content,
            components=components_metadata
        )
