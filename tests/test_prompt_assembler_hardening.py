"""Unit tests for PromptAssembler hardening defaults and substitution behavior."""

from apps.api.services.prompts.prompt_assembler import PromptAssembler


def test_build_simple_replaces_known_variables_and_keeps_unknown():
    assembler = PromptAssembler()
    template = "table={{table_name}} schema={{silver_schema}} unknown={{missing_value}}"
    context = {"table_name": "dim_customer", "silver_schema": "silver"}

    rendered = assembler.build(template, context, format="simple")

    assert "table=dim_customer" in rendered
    assert "schema=silver" in rendered
    # Unknown placeholders should remain intact
    assert "{{missing_value}}" in rendered


def test_enrich_context_sets_common_defaults():
    assembler = PromptAssembler()
    context = {
        "table_name": "dim_customer",
        "silver_schema": "silver",
        "silver_path": "/mnt/lake/silver/dim_customer",
        "gold_path": "/mnt/lake/gold/dim_customer",
    }

    enriched = assembler.enrich_context(context)

    assert enriched["target_table"] == "dim_customer"
    assert enriched["source_table"] == "dim_customer"
    assert enriched["schema_name"] == "silver"
    assert enriched["output_path"] == "/mnt/lake/silver/dim_customer"
    assert enriched["gold_output_path"] == "/mnt/lake/gold/dim_customer"


def test_build_with_filter_json_still_works():
    assembler = PromptAssembler()
    template = "payload={{schema | json}}"
    context = {"schema": {"table_name": "dim_customer", "columns": ["id", "name"]}}

    rendered = assembler.build(template, context, format="simple")

    assert "payload=" in rendered
    assert '"table_name": "dim_customer"' in rendered


def test_build_simple_preserves_single_brace_code_examples():
    assembler = PromptAssembler()
    template = 'table={{table_name}} code=f"{catalog}.{schema}.{table}" sql="MERGE INTO {target_table}"'
    context = {"table_name": "dim_customer"}

    rendered = assembler.build(template, context, format="simple")

    assert "table=dim_customer" in rendered
    assert 'f"{catalog}.{schema}.{table}"' in rendered
    assert 'MERGE INTO {target_table}' in rendered
