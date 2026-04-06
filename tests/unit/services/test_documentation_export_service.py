"""
Tests for DocumentationExportService - Block 4 Downstreams

Covers:
- Markdown/HTML/JSON export generation
- Rule candidate extraction and tracking
- Recommendation action mapping
- Consolidation opportunity detection
- Metadata calculation
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from apps.api.services.documentation_export_service import (
    DocumentationExportService,
    ExportFormat,
)


# ==================== FIXTURES ====================


@pytest.fixture
def tenant_id():
    return "test-tenant-123"


@pytest.fixture
def client_id():
    return "test-client-456"


@pytest.fixture
def project_id():
    return "proj-789"


@pytest.fixture
def mock_db():
    """Mock SupabasePersistence."""
    db = MagicMock()
    db.tenant_id = "test-tenant-123"
    db.client_id = "test-client-456"
    db.execute_query = AsyncMock()
    return db


@pytest.fixture
def sample_understanding():
    """Sample understanding snapshot for testing."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "v1",
        "project_id": "proj-789",
        "functional_map": {
            "domains": [
                {"name": "Sales", "description": "Sales order processing", "asset_count": 5},
                {"name": "Product", "description": "Product catalog", "asset_count": 3},
            ],
            "components": [
                {"name": "OrderProcessing", "domain": "Sales", "type": "etl"},
                {"name": "ProductCatalog", "domain": "Product", "type": "data_store"},
            ],
            "data_assets": [
                {
                    "name": "DimCustomer",
                    "type": "table",
                    "description": "Customer dimension",
                    "columns": [
                        {"name": "customer_id", "type": "int", "nullable": False},
                        {"name": "name", "type": "varchar", "nullable": False},
                        {"name": "email", "type": "varchar", "nullable": True},
                    ],
                },
                {
                    "name": "FactSales",
                    "type": "table",
                    "description": "Sales fact table",
                    "columns": [
                        {"name": "sales_id", "type": "int", "nullable": False},
                        {"name": "customer_id", "type": "int", "nullable": False},
                        {"name": "amount", "type": "decimal", "nullable": False},
                    ],
                },
            ],
            "dependencies": [
                {"source": "DimCustomer", "target": "FactSales", "type": "foreign_key"},
                {"source": "RawCustomer", "target": "DimCustomer", "type": "etl"},
            ],
        },
        "operational_map": {
            "processes": [
                {
                    "name": "DailyCustomerLoad",
                    "description": "Daily customer dimension load",
                    "steps": [
                        {"description": "Extract from source database", "order": 1},
                        {"description": "Data quality validation", "order": 2},
                        {"description": "Load to staging", "order": 3},
                        {"description": "Merge to dimension", "order": 4},
                    ],
                    "frequency": "daily",
                    "parallelism": 1,
                },
                {
                    "name": "MonthlySalesAggregate",
                    "description": "Monthly sales aggregation",
                    "steps": [
                        {"description": "Group sales by period", "order": 1},
                        {"description": "Calculate aggregates", "order": 2},
                        {"description": "Store results", "order": 3},
                    ],
                    "frequency": "monthly",
                    "parallelism": 4,
                },
            ],
            "dependencies": [
                {"from": "DailyCustomerLoad", "to": "MonthlySalesAggregate"},
            ],
        },
        "recommendation_set": {
            "recommendations": [
                {
                    "id": "rec-001",
                    "title": "Document customer SLA constraints",
                    "description": "Create data quality SLA documentation",
                    "severity": "CRITICAL",
                    "category": "documentation",
                    "confidence": 0.95,
                    "dependencies": [],
                },
                {
                    "id": "rec-002",
                    "title": "Implement data quality checks",
                    "description": "Add validation checks for null values in keys",
                    "severity": "HIGH",
                    "category": "data_quality",
                    "confidence": 0.92,
                    "dependencies": ["rec-001"],
                },
                {
                    "id": "rec-003",
                    "title": "Optimize customer load performance",
                    "description": "Implement parallel extraction",
                    "severity": "MEDIUM",
                    "category": "optimization",
                    "confidence": 0.85,
                    "dependencies": [],
                },
                {
                    "id": "rec-004",
                    "title": "Archive old transactions",
                    "description": "Implement archival policy",
                    "severity": "LOW",
                    "category": "governance",
                    "confidence": 0.70,
                    "dependencies": [],
                },
            ],
        },
        "rule_candidate_summary": {
            "rules": [
                {
                    "name": "CustomerKey_Surrogate",
                    "description": "Generate surrogate key for customer",
                    "source_columns": ["customer_id"],
                    "output_format": "int",
                    "reusability_score": "HIGH",
                    "extraction_logic": "ROW_NUMBER() OVER (ORDER BY customer_id)",
                    "applicable_to": ["customer", "dimension"],
                },
                {
                    "name": "SalesAmount_Rounding",
                    "description": "Round sales amounts to 2 decimals",
                    "source_columns": ["amount"],
                    "output_format": "decimal(18,2)",
                    "reusability_score": "HIGH",
                    "extraction_logic": "ROUND(amount, 2)",
                    "applicable_to": ["sales", "transactions"],
                },
                {
                    "name": "DateKey_Format",
                    "description": "Format dates to YYYYMMDD",
                    "source_columns": ["date"],
                    "output_format": "int",
                    "reusability_score": "MEDIUM",
                    "extraction_logic": "CONVERT(INT, REPLACE(CAST(date AS VARCHAR(10)), '-', ''))",
                    "applicable_to": ["time"],
                },
            ],
        },
    }


@pytest.fixture
def sample_project():
    """Sample project metadata."""
    return {
        "id": "proj-789",
        "name": "Customer Data Warehouse",
        "status": "TRIAGED",
        "created_at": "2026-01-01T00:00:00Z",
        "asset_count": 8,
        "governance_findings": {
            "data_classification": "INTERNAL",
            "retention_policy": "7 years",
            "access_control": "RBAC",
        },
    }


@pytest.fixture
def runtime_understanding(project_id):
    """Runtime-shaped understanding payload from the actual UnderstandingService."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "v1",
        "project_id": project_id,
        "functional_map": {
            "domains": [
                {
                    "name": "product",
                    "capabilities": [
                        {
                            "name": "DimProduct.dtsx",
                            "asset_ref": "asset:1",
                            "source_tech": "SSIS",
                            "datasets": ["dbo.DimProduct"],
                            "reads_from": ["src.Products"],
                            "evidence_refs": ["asset:1"],
                            "confidence": 0.82,
                            "uncertainty": [],
                        }
                    ],
                },
                {
                    "name": "customer",
                    "capabilities": [
                        {
                            "name": "DimCustomers.dtsx",
                            "asset_ref": "asset:2",
                            "source_tech": "SSIS",
                            "datasets": ["dbo.DimCustomer"],
                            "reads_from": ["src.Customers"],
                            "evidence_refs": ["asset:2"],
                            "confidence": 0.79,
                            "uncertainty": ["domain_not_inferred_from_name"],
                        }
                    ],
                },
                {
                    "name": "layout",
                    "capabilities": [
                        {
                            "name": "layout.json",
                            "asset_ref": "asset:3",
                            "source_tech": "unknown",
                            "datasets": [],
                            "reads_from": [],
                            "evidence_refs": [],
                            "confidence": 0.30,
                            "uncertainty": ["no_table_impacts_recorded"],
                        }
                    ],
                },
            ],
            "total_assets": 5,
            "total_domains": 2,
        },
        "operational_map": {
            "processes": [
                {
                    "id": "proc:1",
                    "name": "DimProduct.dtsx",
                    "asset_ref": "asset:1",
                    "source_tech": "SSIS",
                    "trigger": "schedule",
                    "schedule_hint": "0 0 * * *",
                    "depends_on": [],
                    "depends_on_names": [],
                    "inputs": ["src.Products"],
                    "outputs": ["dbo.DimProduct"],
                    "fragility_signals": [],
                    "evidence_refs": ["asset:1"],
                    "confidence": 0.75,
                    "uncertainty": [],
                },
                {
                    "id": "proc:2",
                    "name": "DimCustomers.dtsx",
                    "asset_ref": "asset:2",
                    "source_tech": "SSIS",
                    "trigger": "schedule",
                    "schedule_hint": "0 1 * * *",
                    "depends_on": [],
                    "depends_on_names": [],
                    "inputs": ["src.Customers"],
                    "outputs": ["dbo.DimCustomer"],
                    "fragility_signals": ["high_downstream_fan_out"],
                    "evidence_refs": ["asset:2"],
                    "confidence": 0.71,
                    "uncertainty": [],
                },
            ],
            "execution_levels": [["proc:1", "proc:2"]],
            "total_processes": 2,
        },
        "recommendation_set": {
            "items": [
                {
                    "id": "rec:001",
                    "category": "discovery",
                    "statement": "Run table impact analysis on blind assets.",
                    "rationale": "Assets without impacts block lineage and export quality.",
                    "impact": "medium",
                    "effort": "low",
                    "confidence": 0.78,
                },
                {
                    "id": "rec:002",
                    "category": "compliance",
                    "statement": "Mask customer PII before migration.",
                    "rationale": "Target platform must not expose raw PII.",
                    "impact": "high",
                    "effort": "medium",
                    "confidence": 0.88,
                    "based_on": ["asset:2"],
                },
            ]
        },
        "rule_candidate_summary": {
            "candidates": [
                {
                    "id": "rulecand:001",
                    "pattern": "type_cast",
                    "sample_expression": "CAST(product_id AS INT)",
                    "observed_in_assets": ["DimProduct.dtsx"],
                    "occurrence_count": 1,
                    "reuse_scope": "asset",
                    "confidence": 0.65,
                    "uncertainty": ["single_occurrence_no_reuse_confirmed"],
                },
                {
                    "id": "rulecand:002",
                    "pattern": "custom_expression",
                    "sample_expression": "OUTPUT",
                    "observed_in_assets": ["DimCustomers.dtsx"],
                    "occurrence_count": 4,
                    "reuse_scope": "project",
                },
                {
                    "id": "rulecand:003",
                    "pattern": "custom_expression",
                    "sample_expression": "SOURCE_DB",
                    "observed_in_assets": ["DimProduct.dtsx"],
                    "occurrence_count": 10,
                    "reuse_scope": "project",
                }
            ],
            "total": 1,
            "project_scope_count": 0,
        },
    }


@pytest.fixture
def service(tenant_id, client_id, mock_db):
    """Create DocumentationExportService with mocked dependencies."""
    with patch("apps.api.services.documentation_export_service.SupabasePersistence") as mock_persistence, \
         patch("apps.api.services.documentation_export_service.UnderstandingService") as mock_understanding:
        
        mock_persistence.return_value = mock_db
        mock_understanding_instance = AsyncMock()
        mock_understanding.return_value = mock_understanding_instance
        
        svc = DocumentationExportService(tenant_id, client_id)
        svc.understanding = mock_understanding_instance
        svc.db = mock_db
        return svc


# ==================== MARKDOWN EXPORT TESTS ====================


@pytest.mark.anyio
async def test_export_markdown_generation(service, mock_db, project_id, sample_project, sample_understanding):
    """Test markdown export generation ends-to-end."""
    # Setup mocks
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    mock_db.execute_query = AsyncMock(return_value=[sample_project])
    
    # Execute
    result = await service.export_full_documentation(project_id, ExportFormat.MARKDOWN)
    
    # Verify
    assert result["format"] == "markdown"
    assert result["project_id"] == project_id
    assert result["project_name"] == "Customer Data Warehouse"
    assert result["project_status"] == "TRIAGED"
    assert "generated_at" in result
    assert "content" in result
    assert "metadata" in result
    assert "toc" in result
    
    # Verify content structure
    content = result["content"]
    assert "# Data Warehouse Documentation" in content
    assert "## Data Assets" in content
    assert "## Data Flows" in content
    assert "## Process Orchestration" in content
    assert "## Extraction Rules" in content
    assert "## Recommendations" in content
    assert "DimCustomer" in content
    assert "DailyCustomerLoad" in content
    assert "CustomerKey_Surrogate" in content


@pytest.mark.anyio
async def test_markdown_includes_toc(service, mock_db, project_id, sample_project, sample_understanding):
    """Test markdown export includes table of contents."""
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    mock_db.execute_query = AsyncMock(return_value=[sample_project])
    
    result = await service.export_full_documentation(project_id, ExportFormat.MARKDOWN)
    
    # Verify TOC
    toc = result["toc"]
    assert isinstance(toc, list)
    assert any("Data Assets" in item.get("title", "") for item in toc)
    assert any("Recommendations" in item.get("title", "") for item in toc)


@pytest.mark.anyio
async def test_markdown_recommendation_priority_sorting(service, mock_db, project_id, sample_project, sample_understanding):
    """Test recommendations appear in correct priority order."""
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    mock_db.execute_query = AsyncMock(return_value=[sample_project])
    
    result = await service.export_full_documentation(project_id, ExportFormat.MARKDOWN)
    
    content = result["content"]
    # CRITICAL should appear before HIGH in markdown
    critical_pos = content.find("### CRITICAL")
    high_pos = content.find("### HIGH")
    assert 0 < critical_pos < high_pos


# ==================== HTML EXPORT TESTS ====================


@pytest.mark.anyio
async def test_export_html_generation(service, mock_db, project_id, sample_project, sample_understanding):
    """Test HTML export generation."""
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    mock_db.execute_query = AsyncMock(return_value=[sample_project])
    
    result = await service.export_full_documentation(project_id, ExportFormat.HTML)
    
    assert result["format"] == "html"
    assert "<!DOCTYPE html>" in result["content"]
    assert "<title>" in result["content"]
    assert "</html>" in result["content"]
    assert "<h1>" in result["content"]
    assert "Customer Data Warehouse" in result["content"]


# ==================== JSON EXPORT TESTS ====================


@pytest.mark.anyio
async def test_export_json_generation(service, mock_db, project_id, sample_project, sample_understanding):
    """Test JSON export generation."""
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    mock_db.execute_query = AsyncMock(return_value=[sample_project])
    
    result = await service.export_full_documentation(project_id, ExportFormat.JSON)
    
    assert result["format"] == "json"
    content = json.loads(result["content"])
    assert content["project"]["name"] == "Customer Data Warehouse"
    assert "understanding" in content
    assert "structure" in content


# ==================== RULE CANDIDATE TRACKING TESTS ====================


@pytest.mark.anyio
async def test_export_rule_candidates_with_tracking(service, mock_db, project_id, sample_understanding):
    """Test rule candidates export with implementation tracking."""
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    
    result = await service.export_rule_candidates_with_tracking(project_id)
    
    assert result["project_id"] == project_id
    assert "rule_candidates" in result
    assert len(result["rule_candidates"]) == 3
    
    # Verify tracked fields
    for rule in result["rule_candidates"]:
        assert "implementation_status" in rule
        assert "subset_extraction" in rule
        assert "reusability_markers" in rule
        assert rule["implementation_status"] == "DRAFT"


@pytest.mark.anyio
async def test_rule_consolidation_detection(service, mock_db, project_id, sample_understanding):
    """Test detection of consolidation opportunities."""
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    
    result = await service.export_rule_candidates_with_tracking(project_id)
    
    assert "consolidation_opportunities" in result
    # Can be empty or have items depending on matching logic


@pytest.mark.anyio
async def test_rule_reusability_markers(service, mock_db, project_id, sample_understanding):
    """Test reusability marker extraction."""
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    
    result = await service.export_rule_candidates_with_tracking(project_id)
    
    # Check for high-reusability rules
    high_reusable = [r for r in result["rule_candidates"] 
                     if r.get("reusability_score") == "HIGH"]
    assert len(high_reusable) >= 2
    
    # Each high-reusable rule should have markers
    for rule in high_reusable:
        assert "highly-reusable" in rule.get("reusability_markers", [])


# ==================== RECOMMENDATION ACTION MAPPING TESTS ====================


@pytest.mark.anyio
async def test_export_recommendation_actions(service, mock_db, project_id, sample_understanding):
    """Test recommendation action mapping."""
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    
    result = await service.export_recommendation_actions(project_id)
    
    assert result["project_id"] == project_id
    assert "recommendation_actions" in result
    assert len(result["recommendation_actions"]) == 4  # CRITICAL, HIGH, MEDIUM, LOW
    
    # Verify action structure
    for action_group in result["recommendation_actions"]:
        assert "recommendation_id" in action_group
        assert "title" in action_group
        assert "severity" in action_group
        assert "actions" in action_group
        assert "implementation_path" in action_group
        assert "estimated_effort" in action_group


@pytest.mark.anyio
async def test_recommendation_implementation_paths(service, mock_db, project_id, sample_understanding):
    """Test that CRITICAL/HIGH recommendations get correct implementation paths."""
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    
    result = await service.export_recommendation_actions(project_id)
    
    # Find CRITICAL and HIGH recommendations
    critical = [r for r in result["recommendation_actions"] if r["severity"] == "CRITICAL"]
    high = [r for r in result["recommendation_actions"] if r["severity"] == "HIGH"]
    
    assert len(critical) > 0
    assert len(high) > 0
    assert critical[0]["implementation_path"] == "immediate_action"
    assert high[0]["implementation_path"] == "next_sprint"


# ==================== METADATA CALCULATION TESTS ====================


@pytest.mark.anyio
async def test_metadata_calculation_markdown(service, mock_db, project_id, sample_project, sample_understanding):
    """Test metadata calculation for markdown."""
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    mock_db.execute_query = AsyncMock(return_value=[sample_project])
    
    result = await service.export_full_documentation(project_id, ExportFormat.MARKDOWN)
    
    metadata = result["metadata"]
    assert metadata["lines"] > 0
    assert metadata["size_bytes"] > 0
    assert metadata["headers"] > 0


@pytest.mark.anyio
async def test_metadata_calculation_html(service, mock_db, project_id, sample_project, sample_understanding):
    """Test metadata calculation for HTML."""
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    mock_db.execute_query = AsyncMock(return_value=[sample_project])
    
    result = await service.export_full_documentation(project_id, ExportFormat.HTML)
    
    metadata = result["metadata"]
    assert metadata["lines"] > 0
    assert metadata["size_bytes"] > 0


# ==================== ERROR HANDLING TESTS ====================


@pytest.mark.anyio
async def test_export_missing_understanding(service, mock_db, project_id):
    """Test export fails gracefully when understanding not found."""
    service.understanding.get_snapshot = AsyncMock(return_value=None)
    
    result = await service.export_full_documentation(project_id, ExportFormat.MARKDOWN)
    
    assert "error" in result
    assert result["error"] == "understanding_not_found"


@pytest.mark.anyio
async def test_export_database_error(service, mock_db, project_id):
    """Test export fails gracefully on database error."""
    service.understanding.get_snapshot = AsyncMock(side_effect=Exception("DB connection failed"))
    
    result = await service.export_full_documentation(project_id, ExportFormat.MARKDOWN)
    
    assert "error" in result


@pytest.mark.anyio
async def test_recommendation_action_mapping_missing_dependencies(service, mock_db, project_id):
    """Test recommendation action mapping without dependencies field."""
    understanding = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "v1",
        "project_id": project_id,
        "recommendation_set": {
            "recommendations": [
                {
                    "id": "rec-001",
                    "title": "Test recommendation",
                    "severity": "HIGH",
                    "category": "documentation",
                    # No dependencies field
                },
            ],
        },
    }
    service.understanding.get_snapshot = AsyncMock(return_value=understanding)
    
    result = await service.export_recommendation_actions(project_id)
    
    assert "error" not in result
    assert len(result["recommendation_actions"]) > 0


# ==================== INTEGRATION TESTS ====================


@pytest.mark.anyio
async def test_full_export_workflow(service, mock_db, project_id, sample_project, sample_understanding):
    """Test complete export workflow with all formats."""
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    mock_db.execute_query = AsyncMock(return_value=[sample_project])
    
    # Export all formats
    markdown_result = await service.export_full_documentation(project_id, ExportFormat.MARKDOWN)
    html_result = await service.export_full_documentation(project_id, ExportFormat.HTML)
    json_result = await service.export_full_documentation(project_id, ExportFormat.JSON)
    
    # All should succeed
    assert "error" not in markdown_result
    assert "error" not in html_result
    assert "error" not in json_result
    
    # All should have same project_id and generated_at
    assert markdown_result["project_id"] == html_result["project_id"] == json_result["project_id"]
    
    # Content should exist for all
    assert len(markdown_result["content"]) > 0
    assert len(html_result["content"]) > 0
    assert len(json_result["content"]) > 0


@pytest.mark.anyio
async def test_full_downstreams_workflow(service, mock_db, project_id, sample_understanding):
    """Test complete downstreams workflow."""
    service.understanding.get_snapshot = AsyncMock(return_value=sample_understanding)
    
    # Generate all downstream artifacts
    docs = await service.export_full_documentation(project_id, ExportFormat.MARKDOWN)
    rules = await service.export_rule_candidates_with_tracking(project_id)
    actions = await service.export_recommendation_actions(project_id)
    
    # All should contain valid data
    assert docs["project_id"] == project_id
    assert "content" in docs
    
    assert rules["project_id"] == project_id
    assert "rule_candidates" in rules
    assert len(rules["rule_candidates"]) > 0
    
    assert actions["project_id"] == project_id
    assert "recommendation_actions" in actions


@pytest.mark.anyio
async def test_export_runtime_understanding_shape(service, mock_db, project_id, sample_project, runtime_understanding):
    """The exporter should derive counts and sections from the real understanding payload shape."""
    runtime_project = {**sample_project, "asset_count": 0, "status": "TRIAGED"}
    service.understanding.get_snapshot = AsyncMock(return_value=runtime_understanding)
    mock_db.get_project_metadata = AsyncMock(return_value=runtime_project)

    result = await service.export_full_documentation(project_id, ExportFormat.MARKDOWN)

    assert "error" not in result
    content = result["content"]
    assert "**Asset Count:** 2" in content
    assert "Total Domains: 2" in content
    assert "Total Components: 2" in content
    assert "Total Data Assets: 4" in content
    assert "DimProduct.dtsx" in content
    assert "dbo.DimProduct" in content
    assert "Mask customer PII before migration." in content
    assert "CAST(product_id AS INT)" in content
    assert "layout.json" not in content
    assert "(SSIS package)" in content
    assert "Suppressed 2 low-signal rule candidate" in content
    assert "Category: compliance" in content
    assert "Confidence: 0.88" in content
    assert "Based On: DimCustomers.dtsx" in content
    assert "data_classification: INTERNAL" in content


@pytest.mark.anyio
async def test_documentable_asset_filter_excludes_layout_and_plain_json(service):
    """Layout artifacts and JSON files without lineage signals should be filtered out."""
    assert service._is_documentable_asset({
        "name": "layout.json",
        "type": "Layout artifact",
        "datasets": [],
        "reads_from": [],
    }) is False

    assert service._is_documentable_asset({
        "name": "pipeline_meta.json",
        "type": "Asset",
        "datasets": [],
        "reads_from": [],
    }) is False

    assert service._is_documentable_asset({
        "name": "lineage.json",
        "type": "Data pipeline",
        "datasets": ["dbo.Target"],
        "reads_from": ["src.Input"],
    }) is True


@pytest.mark.anyio
async def test_meaningful_rule_filter_boundaries(service):
    """Low-signal placeholders and short tokens should be suppressed, while real logic is kept."""
    assert service._is_meaningful_rule({"sample_expression": "N/A"}) is False
    assert service._is_meaningful_rule({"sample_expression": "NULL"}) is False
    assert service._is_meaningful_rule({"description": "abc"}) is False

    assert service._is_meaningful_rule({
        "pattern": "custom_expression",
        "sample_expression": "OUTPUT_VALUE",
    }) is False

    assert service._is_meaningful_rule({
        "pattern": "custom_expression",
        "sample_expression": "ROUND(amount, 2)",
    }) is True


@pytest.mark.anyio
async def test_format_recommendation_details_humanizes_asset_refs(service):
    """Recommendation detail formatter should resolve asset refs when map exists."""
    report = {
        "asset_ref_to_name": {
            "asset:2": "DimCustomers.dtsx",
        }
    }
    recommendation = {
        "category": "compliance",
        "impact": "high",
        "effort": "medium",
        "confidence": 0.88,
        "based_on": ["asset:2", "impact:orders"],
        "uncertainty": ["schema_not_verified"],
    }

    details = service._format_recommendation_details_with_context(recommendation, report)

    assert any("Category: compliance" in line for line in details)
    assert any("Impact: high" in line for line in details)
    assert any("Effort: medium" in line for line in details)
    assert any("Confidence: 0.88" in line for line in details)
    assert any("Based On: DimCustomers.dtsx, table orders" in line for line in details)
    assert any("Uncertainty: schema_not_verified" in line for line in details)


@pytest.mark.anyio
async def test_get_project_metadata_falls_back_to_execute_query(service, mock_db, project_id):
    """When get_project_metadata is unavailable, exporter should use legacy execute_query fallback."""
    if hasattr(mock_db, "get_project_metadata"):
        delattr(mock_db, "get_project_metadata")

    expected = {
        "id": project_id,
        "name": "Fallback Project",
        "status": "TRIAGED",
        "asset_count": 3,
    }
    mock_db.execute_query = AsyncMock(return_value=[expected])

    result = await service._get_project_metadata(project_id)

    assert result["id"] == project_id
    assert result["name"] == "Fallback Project"
    assert result["status"] == "TRIAGED"
