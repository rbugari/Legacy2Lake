from pathlib import Path
from typing import Dict, Any, List
import json
from .base_cartridge import Cartridge

class SFCartridge(Cartridge):
    """
    Generates Salesforce Ecosystem Code.
    - Processing: Data Cloud (SQL / Ingestion API Schemas)
    - Semantic: Tableau (.tds XML files)
    """

    def get_file_extension(self) -> str:
        return ".sql"

    def generate_scaffolding(self) -> Dict[str, str]:
        """Generates Data Cloud setup helpers."""
        return {
            "readme_salesforce.md": "# Salesforce Integration\n\nUse the generated JSON schemas to configure Data Cloud Ingestion API."
        }

    def generate_bronze(self, table_metadata: Dict[str, Any]) -> str:
        """Generates Data Cloud Ingestion API Schema (JSON)."""
        source_path = Path(table_metadata.get("source_path", "unknown"))
        
        # Mapping generic types to Data Cloud types
        # Placeholder logic: In real usage we would parse input types
        fields = [
            {"name": "id", "type": "Text"},
            {"name": "created_date", "type": "DateTime"},
            {"name": "_ingestion_timestamp", "type": "DateTime"}
        ]
        
        schema = {
            "name": f"bronze_{source_path.stem}",
            "fields": fields
        }
        
        return json.dumps(schema, indent=2)

    def generate_silver(self, table_metadata: Dict[str, Any]) -> str:
        """Generates Data Cloud SQL for Transforms (Calculated Insights / Batch)."""
        source_path = Path(table_metadata.get("source_path", "unknown"))
        output_table_name = table_metadata.get("output_table_name", source_path.stem)
        
        return f"""-- SALESFORCE DATA CLOUD (TRANSFORM)
-- Target DLO/DMO: {output_table_name}

SELECT 
    source.id,
    source.amount,
    CURRENT_TIMESTAMP() as _processed_at
FROM bronze_{source_path.stem} source
WHERE source.amount IS NOT NULL
"""

    def generate_gold(self, table_metadata: Dict[str, Any]) -> str:
        """Generates Data Cloud SQL for Business Layer."""
        output_table_name = table_metadata.get("output_table_name", "gold_table")
        
        return f"""-- SALESFORCE DATA CLOUD (GOLD/INSIGHT)
-- Insight: {output_table_name}

SELECT 
    custId,
    SUM(amount) as total_revenue
FROM silver_{output_table_name.replace('dim_', '').replace('fact_', '')}
GROUP BY 1
"""

    def generate_semantic_model(self, table_metadata: Dict[str, Any]) -> str:
        """Generates Tableau Data Source (.tds) XML."""
        output_table_name = table_metadata.get("output_table_name", "gold_table")
        
        # Simplified TDS structure
        return f"""<?xml version='1.0' encoding='utf-8' ?>
<datasource formatted-name='federated.sf_data_cloud' inline='true' version='18.1'>
  <connection class='federated'>
    <named-connections>
      <named-connection caption='Data Cloud' name='sf_dc'>
        <connection class='snowflake' server='sf_data_cloud_url' database='gold_db' warehouse='compute_wh' />
      </named-connection>
    </named-connections>
    <relation connection='sf_dc' name='{output_table_name}' table='[{output_table_name}]' type='table' />
  </connection>
  <column name='[number_of_records]' role='measure' type='quantitative' user:auto-column='numrec'>
    <calculation class='snowflake' formula='1' />
  </column>
  <layout dim-ordering='alphabetic' dim-percentage='0.5' measure-ordering='alphabetic' measure-percentage='0.5' show-structure='true' />
</datasource>
"""

    def generate_orchestration(self, tables_metadata: List[Dict[str, Any]]) -> str:
        """Generates documentation for Salesforce Data Cloud orchestration."""
        return """# Salesforce Data Cloud Orchestration

Salesforce Data Cloud manages orchestration internally via:
1. **Data Streams**: Configure the 'Refresh Schedule' in the Data Cloud UI for the Ingestion API.
2. **Calculated Insights / Batch Transforms**: These are scheduled via the Data Cloud interface under 'Calculated Insights' -> 'Schedules'.

No external Airflow/DAG is typically required unless you are triggerring the Ingestion API via external webhooks.
"""

    # Semantic alias
    def generate_bronze_sql(self, tm): return self.generate_bronze(tm)
    def generate_silver_sql(self, tm): return self.generate_silver(tm)
    def generate_gold_sql(self, tm): return self.generate_gold(tm)
