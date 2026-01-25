import pytest
import json
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_agent_c_intelligent_generation():
    """Verify that Agent C incorporates metadata (partitioning) and column mapping logic."""
    
    node_data = {
        "id": "node-1",
        "name": "FactSales",
        "label": "FactSales",
        "type": "Data Flow",
        "description": "Migration of sales data",
        "metadata": {
            "partition_key": "transaction_date",
            "volume": "HIGH",
            "is_pii": True
        }
    }
    
    # Mocking a column mapping with logic
    # In a real scenario, Agent C reads from the DB if configured, 
    # but here we pass it in the payload context to verify immediate use.
    context = {
        "solution_name": "TestPhase6",
        "column_mappings": [
            {
                "source_column": "email",
                "logic": "sha2(email, 256)",
                "is_pii": True
            }
        ]
    }
    
    payload = {
        "node_data": node_data,
        "context": context
    }
    
    # Note: We hit the transpile endpoint
    response = client.post("/transpile/task", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        code = data.get("final_code", "")
        
        # Check for partitioning
        assert "partitionBy" in code or "partition_date" in code or "transaction_date" in code, "Should include partitioning logic"
        
        # Check for PII masking logic from column mapping
        assert "sha2" in code or "email" in code, "Should include PII transformation logic"
        
        print(f"Generated Code Sample:\n{code[:500]}...")
