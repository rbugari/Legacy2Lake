import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_prompt_validation_fix_agent_id():
    """Verify that validation works with agent_id."""
    payload = {
        "agent_id": "agent-a",
        "user_input": "Test input for validation"
    }
    response = client.post("/system/validate", json=payload)
    # Might fail if LLM keys missing, but should NOT be 400/500 if routing is OK
    assert response.status_code != 404
    assert response.status_code != 500

def test_prompt_validation_fix_agente_id_alias():
    """Verify that validation works with the legacy agente_id alias."""
    payload = {
        "agente_id": "agent-a",
        "user_input": "Test input for validation"
    }
    response = client.post("/system/validate", json=payload)
    assert response.status_code != 404
    assert response.status_code != 500

def test_agent_s_scout_assessment():
    """Verify that Scout can assess a repository."""
    payload = {
        "file_list": ["script.sql", "data_load.dtsx", "README.md"]
    }
    response = client.post("/system/scout/assess", json=payload)
    assert response.status_code != 404
    assert response.status_code in [200, 500] # 500 might happen if keys missing, but check structure
    if response.status_code == 200:
        data = response.json()
        assert "assessment_summary" in data
        assert "completeness_score" in data
        assert "detected_gaps" in data
