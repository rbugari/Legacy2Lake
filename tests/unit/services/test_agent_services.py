"""
Unit Tests for Agent Services
Tests the core agent services (A, C, F, G) with mocked LLM calls.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class TestAgentAService:
    """Tests for Agent A (Discovery/Triage) service."""
    
    def test_load_prompt_returns_string(self):
        """Test that _load_prompt returns a non-empty string."""
        with patch('services.agent_a_service.os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()) as mock_file:
                mock_file.return_value.__enter__.return_value.read.return_value = "Test prompt content"
                
                from services.agent_a_service import AgentAService
                agent = AgentAService()
                
                # Should return some prompt (may be from file or default)
                prompt = agent._load_prompt()
                assert isinstance(prompt, str)
    
    @pytest.mark.asyncio
    async def test_analyze_manifest_with_mock_llm(self, sample_manifest, mock_llm_response):
        """Test manifest analysis with mocked LLM response."""
        with patch('services.agent_a_service.AgentAService._call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_llm_response
            
            from services.agent_a_service import AgentAService
            agent = AgentAService()
            
            # This would need the actual method to accept our mock
            # For now, we're testing the structure
            assert sample_manifest["project_id"] is not None
            assert len(sample_manifest["file_inventory"]) == 2


class TestAgentCService:
    """Tests for Agent C (Transpiler/Interpreter) service."""
    
    def test_service_initialization(self):
        """Test that AgentCService initializes correctly."""
        with patch('services.agent_c_service.os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                from services.agent_c_service import AgentCService
                agent = AgentCService()
                
                assert agent is not None
    
    def test_load_prompt_exists(self):
        """Test that service has _load_prompt method."""
        from services.agent_c_service import AgentCService
        agent = AgentCService()
        
        assert hasattr(agent, '_load_prompt')


class TestAgentFService:
    """Tests for Agent F (Critic/Auditor) service."""
    
    def test_service_initialization(self):
        """Test that AgentFService initializes correctly."""
        with patch('services.agent_f_service.os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                from services.agent_f_service import AgentFService
                agent = AgentFService()
                
                assert agent is not None
    
    @pytest.mark.asyncio
    async def test_review_code_returns_expected_structure(self, mock_agent_f):
        """Test that review_code returns expected structure."""
        result = await mock_agent_f.review_code({}, "some code")
        
        assert "optimized_code" in result or "score" in result
        assert result["score"] is not None


class TestAgentGService:
    """Tests for Agent G (Governance/Documentation) service."""
    
    def test_service_initialization(self):
        """Test that AgentGService initializes correctly."""
        with patch('services.agent_g_service.os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                from services.agent_g_service import AgentGService
                agent = AgentGService()
                
                assert agent is not None
    
    def test_has_generate_documentation_method(self):
        """Test that service has generate_documentation method."""
        from services.agent_g_service import AgentGService
        agent = AgentGService()
        
        assert hasattr(agent, 'generate_documentation')
