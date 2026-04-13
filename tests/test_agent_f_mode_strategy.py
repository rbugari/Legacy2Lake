"""Tests for Agent F post-drafting mode strategy mapping."""

from copy import deepcopy

from apps.api.services.agent_f_service import AgentFService


def test_agent_f_strategy_mapping_by_mode():
    assert "Terminal delivery path" in AgentFService._resolve_refinement_strategy("drafting_delivery")
    assert "Bounded refinement path" in AgentFService._resolve_refinement_strategy("structured_refinement")
    assert "Advanced path" in AgentFService._resolve_refinement_strategy("intelligent_reengineering")
    assert "Default review path" in AgentFService._resolve_refinement_strategy(None)


def test_agent_f_review_layer_defaults_to_direct_in_drafting_delivery():
    assert AgentFService._resolve_review_layer("silver", "drafting_delivery") == "direct"
    assert AgentFService._resolve_review_layer("gold", None) == "direct"


def test_agent_f_review_layer_respects_refinement_modes():
    assert AgentFService._resolve_review_layer("silver", "structured_refinement") == "silver"
    assert AgentFService._resolve_review_layer("gold", "intelligent_reengineering") == "gold"


def test_agent_f_direct_drafting_normalizes_soft_rejection_to_improved():
    audit_report = {
        "status": "REJECTED",
        "score": 4,
        "critique": [
            "The header format is incorrect for direct translation.",
            "The source query structure is not faithfully preserved.",
            "The code uses overwrite semantics instead of the exact SSIS control-flow semantics.",
        ],
    }
    generated_code = '''
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
config = globals().get("config", {})
source_table = config.get("source_table")
target_table = config.get("target_table")
df = spark.read.table(source_table)
df.write.mode("overwrite").saveAsTable(target_table)
'''

    result = AgentFService._normalize_drafting_direct_review(
        deepcopy(audit_report),
        generated_code,
        "pyspark",
        "direct",
        None,
    )

    assert result["status"] == "IMPROVED"
    assert result["score"] >= 7
    assert result["optimized_code"] == generated_code


def test_agent_f_direct_drafting_keeps_hardcode_rejection():
    audit_report = {
        "status": "REJECTED",
        "score": 4,
        "critique": [
            "The code violates the direct-translation zero-hardcode rule by hardcoded table references.",
        ],
    }
    generated_code = '''
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
config = globals().get("config", {})
df = spark.read.table("main.bronze_raw.tbl")
df.write.mode("overwrite").saveAsTable("main.silver.tbl")
'''

    result = AgentFService._normalize_drafting_direct_review(
        deepcopy(audit_report),
        generated_code,
        "pyspark",
        "direct",
        None,
    )

    assert result["status"] == "REJECTED"
    assert result["score"] == 4
