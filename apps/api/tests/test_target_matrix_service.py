from pathlib import Path

from apps.api.services.target_matrix_service import build_execution_plan, create_run_bundle


def test_build_execution_plan_from_boolean_matrix():
    config = {
        "project_id": "84d8da3f-dacf-4b1f-8ecd-2a9bd63c8c18",
        "modes": {
            "drafting_delivery": True,
            "structured_refinement": False,
            "intelligent_reengineering": True,
        },
        "targets": {
            "snowflake_sql": True,
            "bigquery": False,
            "pyspark": {
                "enabled": True,
                "modes": {
                    "drafting_delivery": False,
                    "structured_refinement": True,
                    "intelligent_reengineering": False,
                },
            },
        }
    }

    plan = build_execution_plan(config)

    assert plan == [
        {"target": "snowflake_sql", "mode": "drafting_delivery", "label": "snowflake_sql"},
        {"target": "snowflake_sql", "mode": "intelligent_reengineering", "label": "snowflake_sql"},
        {"target": "pyspark", "mode": "structured_refinement", "label": "pyspark"},
    ]


def test_create_run_bundle_packages_run_root(tmp_path: Path):
    run_root = tmp_path / "matrix_run"
    run_root.mkdir()
    (run_root / "matrix_summary.json").write_text("{}", encoding="utf-8")
    nested = run_root / "snowflake_sql__structured_refinement"
    nested.mkdir()
    (nested / "run_summary.json").write_text('{"ok": true}', encoding="utf-8")

    bundle_path = create_run_bundle(run_root, "result.zip")

    assert bundle_path.exists()
    assert bundle_path.name == "result.zip"