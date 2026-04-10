"""Integration-like tests for Agent C mode guidance and PromptAssembler context rendering."""

from apps.api.services.agent_c_service import AgentCService
from apps.api.services.prompts.prompt_assembler import PromptAssembler


def test_agent_c_strategy_mapping_by_mode():
    assert (
        AgentCService._resolve_refinement_strategy("drafting_delivery")
        == "Terminal path selected. Keep output faithful and avoid additional refinement assumptions."
    )
    assert "bounded medallion optimization" in AgentCService._resolve_refinement_strategy("structured_refinement").lower()
    assert "advanced optimization" in AgentCService._resolve_refinement_strategy("intelligent_reengineering").lower()
    assert "standard direct modernization guidance" in AgentCService._resolve_refinement_strategy(None).lower()


def test_agent_c_mode_context_renders_with_prompt_assembler_defaults():
    assembler = PromptAssembler()

    mode = "structured_refinement"
    strategy = AgentCService._resolve_refinement_strategy(mode)

    context = {
        "table_name": "dim_customer",
        "catalog_name": "analytics",
        "silver_schema": "silver",
        "silver_path": "/mnt/lake/silver/dim_customer",
        "post_drafting_mode": mode,
        "refinement_strategy": strategy,
    }

    enriched = assembler.enrich_context(context)

    template = (
        "mode={{post_drafting_mode}}; "
        "strategy={{refinement_strategy}}; "
        "target={{target_table}}; "
        "project={{project}}; "
        "dataset={{silver_dataset}}; "
        "out={{output_path}}"
    )

    rendered = assembler.build(template, enriched, format="simple")

    assert "mode=structured_refinement" in rendered
    assert "strategy=Apply bounded medallion optimization" in rendered
    assert "target=dim_customer" in rendered
    assert "project=analytics" in rendered
    assert "dataset=silver" in rendered
    assert "out=/mnt/lake/silver/dim_customer" in rendered
