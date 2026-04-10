"""Tests for Agent F post-drafting mode strategy mapping."""

from apps.api.services.agent_f_service import AgentFService


def test_agent_f_strategy_mapping_by_mode():
    assert "Terminal delivery path" in AgentFService._resolve_refinement_strategy("drafting_delivery")
    assert "Bounded refinement path" in AgentFService._resolve_refinement_strategy("structured_refinement")
    assert "Advanced path" in AgentFService._resolve_refinement_strategy("intelligent_reengineering")
    assert "Default review path" in AgentFService._resolve_refinement_strategy(None)
