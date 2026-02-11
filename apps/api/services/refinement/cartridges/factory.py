from typing import Dict, Any, Type
from .base_cartridge import Cartridge
from .pyspark_cartridge import PySparkCartridge

try:
    from services.persistence_service import SupabasePersistence
except ImportError:
    from apps.api.services.persistence_service import SupabasePersistence

class CartridgeFactory:
    """
    Factory to create the appropriate refined cartridge.
    """
    
    @staticmethod
    def get_cartridge(project_id: str, registry: Dict[str, Any], tenant_id: str = None, target_tech: str = None) -> Cartridge:
        """
        Determines the correct cartridge based on Design Registry settings.
        Fetches compliance rules from DB and injects them.
        
        Args:
            target_tech: Optional override for target technology (takes priority over registry)
        """
        # Priority: Explicit parameter > Registry > Default
        target = str(target_tech or registry.get("paths", {}).get("target_stack", "pyspark")).lower()
        print(f"[CartridgeFactory] DEBUG: target_tech={target_tech}, registry_target={registry.get('paths', {}).get('target_stack')}, final_target={target}")
        
        # Resolve Tech Config from DB
        try:
            # Map target string to tech_id (e.g. 'ms_fabric' -> 'fabric')
            tech_map = {
                "ms_fabric": "fabric", "microsoft_fabric": "fabric",
                "aws": "redshift", "amazon": "redshift",
                "gcp": "bigquery", "google": "bigquery",
                "salesforce": "salesforce", "sf": "salesforce", "sfdc": "salesforce"
            }
            tech_id = tech_map.get(target, target)
            
            db = SupabasePersistence(tenant_id=tenant_id)
            # Use direct sync execution as our Persistence client is sync
            response = db.client.table("utm_system_catalog").select("config").eq("tech_id", tech_id).execute()
            
            if response.data and len(response.data) > 0:
                tech_config = response.data[0].get("config", {})
                registry['tech_config'] = tech_config
            
        except Exception as e:
            print(f"Warning: Failed to fetch tech config for {target}: {e}")

        if target in ["dbt"]:
            # Lazy import to avoid circular dependencies or import errors if not ready
            print(f"[CartridgeFactory] DEBUG: Matched 'dbt', importing DbtCartridge...")
            from .dbt_cartridge import DbtCartridge
            print(f"[CartridgeFactory] DEBUG: DbtCartridge imported successfully")
            return DbtCartridge(project_id, registry)
            
        elif target in ["snowflake"]:
            print(f"[CartridgeFactory] DEBUG: Matched 'snowflake', importing SnowflakeCartridge...")
            from .snowflake_cartridge import SnowflakeCartridge
            print(f"[CartridgeFactory] DEBUG: SnowflakeCartridge imported successfully")
            return SnowflakeCartridge(project_id, registry)

        elif target in ["fabric", "ms_fabric", "microsoft_fabric"]:
            from .ms_fabric_cartridge import MSFabricCartridge
            return MSFabricCartridge(project_id, registry)

        elif target in ["gcp", "google", "bigquery"]:
            from .gcp_cartridge import GCPCartridge
            return GCPCartridge(project_id, registry)

        elif target in ["aws", "amazon", "redshift"]:
            from .aws_cartridge import AWSCartridge
            return AWSCartridge(project_id, registry)

        elif target in ["salesforce", "sf", "sfdc"]:
            from .sf_cartridge import SFCartridge
            return SFCartridge(project_id, registry)

        elif target in ["sql", "ansi_sql"]:
            # Placeholder for Pure SQL
            return PySparkCartridge(project_id, registry)
            
        elif target == "both":
            # Special mode: We use PySparkCartridge but we expect the prompt 
            # (which includes the registry) to trigger dual generation.
            # In a more advanced version, we might return a MultiCartridge.
            print(f"[CartridgeFactory] DEBUG: Matched 'both', using PySparkCartridge for dual mode")
            return PySparkCartridge(project_id, registry)

        else:
            print(f"[CartridgeFactory] DEBUG: No match for target='{target}', defaulting to PySparkCartridge")
            return PySparkCartridge(project_id, registry)
