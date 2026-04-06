"""Unit tests for reports router catalog endpoints."""


class TestReportsCatalogEndpoints:
    def test_list_reports_catalog(self, test_client):
        response = test_client.get("/projects/reports/catalog?stage=3")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        assert any(report["report_id"] == "discovery-analysis" for report in data["reports"])

    def test_list_reports_catalog_filters_product_line(self, test_client):
        response = test_client.get("/projects/reports/catalog?product_line=source_intelligence")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        assert all(report["product_line"] == "source_intelligence" for report in data["reports"])

    def test_get_report_metadata(self, test_client):
        response = test_client.get("/projects/reports/catalog/discovery-analysis")

        assert response.status_code == 200
        data = response.json()
        assert data["report"]["report_id"] == "discovery-analysis"
        assert data["report"]["product_line"] == "source_intelligence"

    def test_get_report_metadata_not_found(self, test_client):
        response = test_client.get("/projects/reports/catalog/not-real")

        assert response.status_code == 404

    def test_get_catalog_summary(self, test_client):
        response = test_client.get("/projects/reports/catalog-summary")

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "by_product_line" in data["summary"]
        assert "source_intelligence" in data["summary"]["by_product_line"]
        assert "migration_factory" in data["summary"]["by_product_line"]
