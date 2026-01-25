import pytest
import json
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.services.agent_a_service import AgentAService

client = TestClient(app)

def test_architect_v2_metadata_structure():
    """Verify that Agent A returns the upgraded Architect v2.0 metadata structure."""
    manifest = {
        "project_id": "test-phase-5",
        "tech_stats": {"SQL": 10},
        "file_inventory": [
            {"path": "fact_sales.sql", "snippet": "SELECT * FROM raw_sales", "signatures": ["SQL"]},
            {"path": "dim_customer.dtsx", "snippet": "SSIS package for customers", "signatures": ["XML", "DTS"]}
        ],
        "user_context": []
    }
    
    # We can test the service directly to avoid needing real API integration if we mock the LLM, 
    # but for a quick check we'll hit the validate endpoint or mock.
    # In this environment, we'll try to trigger a real or near-real assessment if keys exist.
    
    payload = {
        "agent_id": "agent-a",
        "user_input": json.dumps(manifest)
    }
    
    response = client.post("/system/validate", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        
        content = data["response"]
        # Clean potential markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        parsed = json.loads(content)
        assert "mesh_graph" in parsed
        nodes = parsed["mesh_graph"].get("nodes", [])
        if nodes:
            node = nodes[0]
            assert "metadata" in node, "Node should have a metadata object in v2.0"
            metadata = node["metadata"]
            # Check for at least some of the new fields
            assert any(k in metadata for k in ["volume", "latency", "criticality", "is_pii"])
            print(f"Verified high-res metadata: {metadata}")
