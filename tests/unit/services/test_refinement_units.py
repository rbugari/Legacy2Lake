import pytest

from apps.api.services.refinement.profiler_service import ProfilerService
from apps.api.services.refinement.architect_service import ArchitectService


def test_profiler_groups_related_files_into_refinement_units():
    profiler = ProfilerService()

    candidate_files = [
        "load_customer.dtsx",
        "sync_customer.sql",
        "fact_sales.py",
    ]
    shared_connections = {
        "jdbc://crm": ["load_customer.dtsx", "sync_customer.sql"],
    }
    table_metadata = {
        "load_customer.dtsx": {"pk": ["customer_id"], "type": "DIMENSION"},
        "sync_customer.sql": {"pk": ["customer_id"], "type": "DIMENSION"},
        "fact_sales.py": {"pk": ["sale_id"], "type": "FACT"},
    }

    units = profiler._build_refinement_units(candidate_files, shared_connections, table_metadata)
    unit_map = {unit["unit_name"]: unit for unit in units}

    assert "customer" in unit_map
    assert unit_map["customer"]["reuse_strategy"] == "multi_source_consolidation"
    assert unit_map["customer"]["source_files"] == ["load_customer.dtsx", "sync_customer.sql"]
    assert unit_map["customer"]["pk_columns"] == ["customer_id"]
    assert unit_map["sales"]["table_type"] == "FACT"


def test_architect_prefers_refinement_units_over_analyzed_files():
    architect = ArchitectService()
    profile_metadata = {
        "analyzed_files": ["load_customer.dtsx", "sync_customer.sql"],
        "refinement_units": [
            {
                "unit_name": "customer",
                "output_table_name": "customer",
                "source_files": ["load_customer.dtsx", "sync_customer.sql"],
                "pk_columns": ["customer_id"],
                "table_type": "DIMENSION",
                "reuse_strategy": "multi_source_consolidation",
            }
        ],
    }

    units = architect._resolve_processing_units(profile_metadata)

    assert len(units) == 1
    assert units[0]["unit_name"] == "customer"
    assert units[0]["source_files"] == ["load_customer.dtsx", "sync_customer.sql"]


def test_profiler_builds_unit_primary_keys_with_default_fallback():
    profiler = ProfilerService()
    candidate_files = ["load_customer.dtsx", "load_inventory.dtsx"]
    table_metadata = {
        "load_customer.dtsx": {"pk": ["customer_id"], "type": "DIMENSION"},
        "load_inventory.dtsx": {"pk": [], "type": "DIMENSION"},
    }

    unit_primary_keys = profiler._build_unit_primary_keys(candidate_files, table_metadata)

    assert unit_primary_keys["customer"] == ["customer_id"]
    assert unit_primary_keys["inventory"] == ["id"]