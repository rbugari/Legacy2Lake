"""
Pytest Configuration and Fixtures
Provides shared fixtures for all tests including mocked Supabase, test clients, and sample data.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import os
import sys

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment variables BEFORE importing app modules
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("AZURE_OPENAI_API_KEY", "test-azure-key")
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")


# --- Supabase Mocks ---

@pytest.fixture
def mock_supabase_client():
    """Creates a mock Supabase client."""
    mock_client = MagicMock()
    
    # Mock table operations
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.neq.return_value = mock_table
    mock_table.execute.return_value = MagicMock(data=[])
    
    mock_client.table.return_value = mock_table
    
    return mock_client


@pytest.fixture
def mock_supabase(mock_supabase_client):
    """Patches the Supabase client creation."""
    with patch('supabase.create_client', return_value=mock_supabase_client):
        with patch('services.persistence_service.create_client', return_value=mock_supabase_client):
            yield mock_supabase_client


# --- Test Client ---

@pytest.fixture
def test_client(mock_supabase):
    """Creates a FastAPI TestClient with mocked dependencies."""
    # Import here to ensure mocks are in place
    from apps.api.main_refactored import app
    return TestClient(app)


@pytest.fixture
def test_client_legacy(mock_supabase):
    """Creates a TestClient using the legacy main.py (for comparison)."""
    from apps.api.main import app
    return TestClient(app)


# --- Sample Data Fixtures ---

@pytest.fixture
def sample_project():
    """Returns a sample project dictionary."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "TestProject",
        "stage": "1",
        "status": "TRIAGE",
        "source_tech": "SQLSERVER",
        "target_tech": "DATABRICKS",
        "is_active": True,
        "created_at": "2026-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_asset():
    """Returns a sample asset dictionary."""
    return {
        "id": "asset-uuid-12345",
        "filename": "test_procedure.sql",
        "type": "CORE",
        "source_path": "/source/test_procedure.sql",
        "selected": True,
        "metadata": {
            "size": 1024,
            "complexity": "MEDIUM"
        }
    }


@pytest.fixture
def sample_user():
    """Returns a sample user/tenant dictionary."""
    return {
        "tenant_id": "tenant-uuid-12345",
        "client_id": "client-uuid-12345",
        "username": "testuser",
        "password_hash": "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f",  # SHA256 of 'password123'
        "password_hash_bcrypt": None,  # Not migrated yet
        "role": "admin"
    }


@pytest.fixture
def sample_manifest():
    """Returns a sample discovery manifest."""
    return {
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "file_inventory": [
            {
                "name": "procedure1.sql",
                "path": "/source/procedure1.sql",
                "size": 2048,
                "signatures": ["CREATE PROCEDURE", "SELECT"],
                "metadata": {}
            },
            {
                "name": "package1.dtsx",
                "path": "/source/package1.dtsx",
                "size": 15360,
                "signatures": ["DTS:Executable", "OLE DB"],
                "metadata": {}
            }
        ],
        "tech_stats": {
            "sql": 1,
            "dtsx": 1
        }
    }


# --- Authentication Fixtures ---

@pytest.fixture
def auth_headers():
    """Returns sample authentication headers."""
    return {
        "X-Tenant-ID": "tenant-uuid-12345",
        "X-Client-ID": "client-uuid-12345"
    }


# --- LLM Mock Fixtures ---

@pytest.fixture
def mock_llm_response():
    """Returns a mock LLM response for agent tests."""
    return {
        "mesh_graph": {
            "nodes": [
                {
                    "id": "/source/procedure1.sql",
                    "label": "procedure1.sql",
                    "category": "CORE",
                    "complexity": "MEDIUM",
                    "confidence": 0.9
                }
            ],
            "edges": []
        },
        "summary": "Analysis complete"
    }


@pytest.fixture
def mock_agent_a(mock_llm_response):
    """Patches AgentAService to return mock responses."""
    with patch('services.agent_a_service.AgentAService') as MockAgentA:
        instance = MockAgentA.return_value
        instance._load_prompt.return_value = "Test system prompt"
        instance.analyze_manifest = AsyncMock(return_value=mock_llm_response)
        yield instance


@pytest.fixture
def mock_agent_c():
    """Patches AgentCService to return mock responses."""
    with patch('services.agent_c_service.AgentCService') as MockAgentC:
        instance = MockAgentC.return_value
        instance._load_prompt.return_value = "Test transpiler prompt"
        instance.transpile_task = AsyncMock(return_value={
            "pyspark_code": "# Generated PySpark code\ndf = spark.read.csv('test.csv')",
            "explanation": "Test explanation"
        })
        yield instance


@pytest.fixture
def mock_agent_f():
    """Patches AgentFService to return mock responses."""
    with patch('services.agent_f_service.AgentFService') as MockAgentF:
        instance = MockAgentF.return_value
        instance._load_prompt.return_value = "Test critic prompt"
        instance.review_code = AsyncMock(return_value={
            "optimized_code": "# Optimized PySpark code\ndf = spark.read.csv('test.csv').cache()",
            "score": 85,
            "suggestions": ["Added caching"]
        })
        yield instance
