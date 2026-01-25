import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.utils.logger import logger
from unittest.mock import patch

client = TestClient(app)

def test_health_check():
    """Verify that /health endpoint returns expected status and DB connectivity."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "db_connection" in data
    assert "timestamp" in data
    assert "version" in data

def test_request_logging_middleware():
    """Verify that requests are logged by the middleware."""
    with patch.object(logger, 'http_log') as mock_log:
        response = client.get("/ping")
        assert response.status_code == 200
        # Check if http_log was called
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert kwargs['method'] == "GET"
        assert kwargs['path'] == "/ping"
        assert kwargs['status_code'] == 200

def test_global_exception_handler_logging():
    """Verify that unhandled exceptions log a traceback."""
    # We trigger a 500 by making a route fail or calling one that doesn't exist 
    # but the middleware/app should handle it.
    # To force a real unhandled Exception we can mock a route.
    
    with patch("apps.api.services.agent_a_service.AgentAService._load_prompt") as mock_method:
        mock_method.side_effect = Exception("Simulated Crash")
        
        with patch.object(logger, 'error') as mock_error:
            response = client.get("/prompts/agent-a")
            # If the app catches it and returns 500
            if response.status_code == 500:
                mock_error.assert_called()
                # Verify exception was passed
                found_exc = False
                for call in mock_error.call_args_list:
                    if "exc" in call.kwargs and isinstance(call.kwargs["exc"], Exception):
                        found_exc = True
                assert found_exc, "Traceback (exc) should be passed to logger.error"
            else:
                # If it didn't return 500, let's see what it returned
                print(f"DEBUG: Response was {response.status_code}, content: {response.text}")
                assert response.status_code == 500

def test_health_noise_filter():
    """Verify that /health calls are NOT logged to avoid noise."""
    with patch.object(logger, 'http_log') as mock_log:
        client.get("/health")
        mock_log.assert_not_called()
