"""Unit tests for ReportsCatalogService."""

from apps.api.services.reports_catalog_service import ReportsCatalogService


def test_catalog_summary_exposes_dual_product_lines():
    summary = ReportsCatalogService.get_catalog_summary()

    assert summary["total_reports"] >= 7
    assert "source_intelligence" in summary["by_product_line"]
    assert "migration_factory" in summary["by_product_line"]
    assert summary["by_product_line"]["source_intelligence"] > 0
    assert summary["by_product_line"]["migration_factory"] > 0
    assert "product_line_descriptions" in summary


def test_get_all_reports_filters_by_product_line():
    reports = ReportsCatalogService.get_all_reports(product_line="source_intelligence")

    assert reports
    assert all(report["product_line"] == "source_intelligence" for report in reports)
    assert any(report["report_id"] == "discovery-analysis" for report in reports)
    assert all(report["report_id"] != "migration-delivery" for report in reports)


def test_get_all_reports_filters_by_stage_and_product_line():
    reports = ReportsCatalogService.get_all_reports(stage=2, product_line="migration_factory")

    assert reports == []


def test_specific_report_includes_product_story_metadata():
    report = ReportsCatalogService.get_report("migration-delivery")

    assert report is not None
    assert report["product_line"] == "migration_factory"
    assert "product_story" in report["metadata"]
