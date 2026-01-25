import pytest
import json
from unittest.mock import AsyncMock, patch
from apps.api.services.agent_c_service import AgentCService

@pytest.mark.asyncio
async def test_variable_injection_in_context():
    """Verify that variables are correctly injected into the LLM context."""
    
    # Mock node data with variables
    node_data = {
        "id": "node-1",
        "name": "TestTask",
        "type": "Data Flow",
        "description": "Test",
        "variables": [
            {"key": "S3_ROOT", "value": "s3://my-bucket/root"},
            {"key": "ENV", "value": "prouction"}
        ]
    }
    
    context = {
        "project_id": "proj_123"
    }
    
    # Initialize Service
    service = AgentCService()
    
    # Mock LLM to inspect the prompt sent to it
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value.content = json.dumps({"pyspark_code": "spark.read.load(f'{S3_ROOT}/data')"})
    
    with patch.object(service, '_get_llm', return_value=mock_llm):
        result = await service.transpile_task(node_data, context)
        
        # Capture the prompt passed to LLM
        call_args = mock_llm.ainvoke.call_args[0][0]
        human_message = call_args[1].content
        
        # Verify variables presence in context
        assert "S3_ROOT" in human_message
        assert "s3://my-bucket/root" in human_message
        assert "ENV" in human_message
        
        print(f"Variables found in prompt context: {human_message.count('S3_ROOT')} occurrences")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_variable_injection_in_context())
