"""
Unit Tests for Phase A - Quick Assessment Service
===================================================

Tests:
    - File classification by category (migrable, support, doc, unrecognized)
    - Technology detection (SSIS, DataStage, Pentaho, SQL)
    - Complexity estimation (LOW, MEDIUM, HIGH)
    - Viability score calculation
    - Semaphore assignment (green, yellow, red)
    - Blocker identification
    - Summary generation for LLM
    - Complete assessment flow

Coverage Areas:
    - QuickAssessmentService.assess()
    - QuickAssessmentService._classify_file()
    - QuickAssessmentService._calculate_score()
    - QuickAssessmentService._get_semaforo()
    - QuickAssessmentService._identify_blockers()

Author: Legacy2Lake Engineering
Date: 2026-02-15 (Phase A - Sprint 14)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import service and models
from apps.api.services.quick_assessment_service import (
    QuickAssessmentService,
    QuickAssessmentResult,
    FileClassification
)


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def qa_service():
    """QuickAssessmentService instance"""
    return QuickAssessmentService(tenant_id="test-tenant-123")


@pytest.fixture
def sample_file_inventory():
    """Sample file inventory with various file types"""
    return [
        {"name": "LoadCustomers.dtsx", "size": 1024, "lines": 250},
        {"name": "LoadOrders.dtsx", "size": 2048, "lines": 380},
        {"name": "UpdateProducts.dtsx", "size": 1500, "lines": 420},
        {"name": "schema.sql", "size": 4096, "lines": 180},
        {"name": "reference_data.csv", "size": 512, "lines": 50},
        {"name": "README.md", "size": 256, "lines": 30},
        {"name": "config.json", "size": 128, "lines": 15},
        {"name": "random.xyz", "size": 64, "lines": 0}
    ]


@pytest.fixture
def mock_manifest(sample_file_inventory):
    """Mock manifest from DiscoveryService"""
    return {
        "file_inventory": sample_file_inventory,
        "tech_counts": {"SSIS": 3, "SQL": 1}
    }


# ================================================================
# UNIT TESTS - File Classification
# ================================================================

def test_classify_ssis_file(qa_service):
    """Test classification of SSIS package"""
    item = {"name": "Package1.dtsx", "size": 1024, "lines": 200}
    category, tech = qa_service._classify_file(item)
    
    assert category == "migratable"
    assert tech == "SSIS"


def test_classify_datastage_file(qa_service):
    """Test classification of DataStage job"""
    item = {"name": "Job1.dsx", "size": 2048, "lines": 350}
    category, tech = qa_service._classify_file(item)
    
    assert category == "migratable"
    assert tech == "DataStage"


def test_classify_pentaho_files(qa_service):
    """Test classification of Pentaho job and transformation"""
    # Job file
    item1 = {"name": "extract_data.kjb", "size": 1024, "lines": 150}
    category1, tech1 = qa_service._classify_file(item1)
    assert category1 == "migratable"
    assert tech1 == "Pentaho"
    
    # Transformation file
    item2 = {"name": "transform.ktr", "size": 1024, "lines": 200}
    category2, tech2 = qa_service._classify_file(item2)
    assert category2 == "migratable"
    assert tech2 == "Pentaho"


def test_classify_informatica_file(qa_service):
    """Test classification of Informatica workflow"""
    item = {"name": "workflow.pmx", "size": 1500, "lines": 300}
    category, tech = qa_service._classify_file(item)
    
    assert category == "migratable"
    assert tech == "Informatica"


def test_classify_sql_file(qa_service):
    """Test classification of SQL file as support"""
    item = {"name": "schema.sql", "size": 4096, "lines": 180}
    category, tech = qa_service._classify_file(item)
    
    assert category == "support"
    assert tech == "SQL"


def test_classify_csv_file(qa_service):
    """Test classification of CSV file as support"""
    item = {"name": "data.csv", "size": 512, "lines": 50}
    category, tech = qa_service._classify_file(item)
    
    assert category == "support"
    assert tech is None


def test_classify_documentation_file(qa_service):
    """Test classification of documentation"""
    # Markdown
    item1 = {"name": "README.md", "size": 256, "lines": 30}
    category1, tech1 = qa_service._classify_file(item1)
    assert category1 == "documentation"
    assert tech1 is None
    
    # Text file
    item2 = {"name": "notes.txt", "size": 128, "lines": 15}
    category2, tech2 = qa_service._classify_file(item2)
    assert category2 == "documentation"
    assert tech2 is None


def test_classify_unrecognized_file(qa_service):
    """Test classification of unrecognized file"""
    item = {"name": "random.xyz", "size": 64, "lines": 0}
    category, tech = qa_service._classify_file(item)
    
    assert category == "unrecognized"
    assert tech is None


# ================================================================
# UNIT TESTS - Complexity Estimation
# ================================================================

def test_estimate_complexity_low(qa_service):
    """Test LOW complexity estimation"""
    item = {"name": "simple.dtsx", "size": 512, "lines": 150}
    complexity = qa_service._estimate_complexity(item)
    assert complexity == "LOW"


def test_estimate_complexity_medium(qa_service):
    """Test MEDIUM complexity estimation"""
    item = {"name": "medium.dtsx", "size": 1024, "lines": 350}
    complexity = qa_service._estimate_complexity(item)
    assert complexity == "MEDIUM"


def test_estimate_complexity_high(qa_service):
    """Test HIGH complexity estimation"""
    item = {"name": "complex.dtsx", "size": 4096, "lines": 650}
    complexity = qa_service._estimate_complexity(item)
    assert complexity == "HIGH"


def test_estimate_complexity_no_lines(qa_service):
    """Test complexity when lines=0 (binary file)"""
    item = {"name": "binary.dat", "size": 2048, "lines": 0}
    complexity = qa_service._estimate_complexity(item)
    assert complexity == "LOW"


# ================================================================
# UNIT TESTS - Score Calculation
# ================================================================

def test_calculate_score_all_migrable(qa_service):
    """Test score when all files are migrable (score=100)"""
    breakdown = {"migratable": 5, "support": 0, "documentation": 0, "unrecognized": 0}
    score = qa_service._calculate_score(breakdown, total=5)
    assert score == 100


def test_calculate_score_mixed(qa_service):
    """Test score with mixed file types"""
    breakdown = {"migratable": 3, "support": 2, "documentation": 1, "unrecognized": 1}
    total = 7
    # Formula: (3*4 + 2*2 + 1*1 + 1*0) / (7*4) * 100 = 17/28 * 100 = 60.7 ≈ 60
    score = qa_service._calculate_score(breakdown, total)
    assert score == 60


def test_calculate_score_no_migrable(qa_service):
    """Test score when no migrable files (low score)"""
    breakdown = {"migratable": 0, "support": 2, "documentation": 3, "unrecognized": 0}
    total = 5
    # Formula: (0*4 + 2*2 + 3*1 + 0*0) / (5*4) * 100 = 7/20 * 100 = 35
    score = qa_service._calculate_score(breakdown, total)
    assert score == 35


def test_calculate_score_empty(qa_service):
    """Test score with no files (should return 0)"""
    breakdown = {"migratable": 0, "support": 0, "documentation": 0, "unrecognized": 0}
    score = qa_service._calculate_score(breakdown, total=0)
    assert score == 0


# ================================================================
# UNIT TESTS - Semaphore Assignment
# ================================================================

def test_semaforo_green(qa_service):
    """Test green semaphore (score ≥ 60)"""
    assert qa_service._get_semaforo(100) == "green"
    assert qa_service._get_semaforo(75) == "green"
    assert qa_service._get_semaforo(60) == "green"


def test_semaforo_yellow(qa_service):
    """Test yellow semaphore (30 ≤ score < 60)"""
    assert qa_service._get_semaforo(59) == "yellow"
    assert qa_service._get_semaforo(45) == "yellow"
    assert qa_service._get_semaforo(30) == "yellow"


def test_semaforo_red(qa_service):
    """Test red semaphore (score < 30)"""
    assert qa_service._get_semaforo(29) == "red"
    assert qa_service._get_semaforo(15) == "red"
    assert qa_service._get_semaforo(0) == "red"


# ================================================================
# UNIT TESTS - Blocker Identification
# ================================================================

def test_identify_blockers_no_migrable(qa_service):
    """Test blocker: no migrable files"""
    breakdown = {"migratable": 0, "support": 5, "documentation": 2, "unrecognized": 1}
    blockers = qa_service._identify_blockers(breakdown, total=8)
    
    assert len(blockers) > 0
    assert any("No migratable files" in b for b in blockers)


def test_identify_blockers_too_many_unrecognized(qa_service):
    """Test blocker: >70% unrecognized files"""
    breakdown = {"migratable": 1, "support": 0, "documentation": 1, "unrecognized": 8}
    blockers = qa_service._identify_blockers(breakdown, total=10)
    
    assert len(blockers) > 0
    assert any("unrecognized" in b for b in blockers)


def test_identify_blockers_missing_support(qa_service):
    """Test blocker: migrable files but no support files"""
    breakdown = {"migratable": 3, "support": 0, "documentation": 1, "unrecognized": 0}
    blockers = qa_service._identify_blockers(breakdown, total=4)
    
    assert len(blockers) > 0
    assert any("support files" in b for b in blockers)


def test_identify_blockers_none(qa_service):
    """Test no blockers when project is viable"""
    breakdown = {"migratable": 5, "support": 2, "documentation": 1, "unrecognized": 0}
    blockers = qa_service._identify_blockers(breakdown, total=8)
    
    # Since score would be high, this test shouldn't call _identify_blockers
    # But if called, it should return empty or minimal blockers
    assert len(blockers) == 0


# ================================================================
# UNIT TESTS - Summary Generation
# ================================================================

def test_build_summary(qa_service):
    """Test LLM summary generation"""
    breakdown = {"migratable": 3, "support": 2, "documentation": 1, "unrecognized": 0}
    techs = {"SSIS", "SQL"}
    
    summary = qa_service._build_summary(breakdown, techs, total=6, lines=1000)
    
    assert "6" in summary  # Total files
    assert "1,000" in summary or "1000" in summary  # Total lines
    assert "3" in summary  # Migrable count
    assert "SSIS" in summary
    assert "SQL" in summary


def test_build_summary_no_techs(qa_service):
    """Test summary when no technologies detected"""
    breakdown = {"migratable": 0, "support": 2, "documentation": 1, "unrecognized": 2}
    techs = set()
    
    summary = qa_service._build_summary(breakdown, techs, total=5, lines=100)
    
    assert "None detected" in summary


# ================================================================
# INTEGRATION TEST - Full Assessment
# ================================================================

@pytest.mark.asyncio
async def test_assess_complete_flow(qa_service, mock_manifest):
    """Test complete assessment flow with mocked dependencies"""
    
    # Mock DiscoveryService.generate_manifest
    with patch('apps.api.services.quick_assessment_service.DiscoveryService') as mock_discovery:
        mock_discovery.generate_manifest.return_value = mock_manifest

        with patch.object(qa_service.db, 'get_project_metadata', new_callable=AsyncMock) as mock_meta:
            mock_meta.return_value = None
            with patch.object(qa_service.db, 'get_project_settings', new_callable=AsyncMock) as mock_settings:
                mock_settings.return_value = {}
                with patch.object(qa_service, '_get_llm_opinion', new_callable=AsyncMock) as mock_llm:
                    mock_llm.return_value = None

                    result = await qa_service.assess("test-project-123")

                    # Verify result structure
                    assert isinstance(result, QuickAssessmentResult)
                    assert result.score >= 0 and result.score <= 100
                    assert result.semaforo in ["green", "yellow", "red"]
                    assert result.total_files == 8
                    assert len(result.file_details) == 8

                    # Verify breakdown
                    assert result.file_breakdown["migratable"] == 3  # 3 SSIS files
                    assert result.file_breakdown["support"] == 3  # SQL, CSV, JSON
                    assert result.file_breakdown["documentation"] == 1  # MD
                    assert result.file_breakdown["unrecognized"] == 1  # XYZ

                    # Verify technologies detected
                    assert "SSIS" in result.detected_techs
                    assert "SQL" in result.detected_techs

                    # Verify file details
                    ssis_files = [f for f in result.file_details if f.category == "MIGRATABLE"]
                    assert len(ssis_files) == 3
                    assert all(f.detected_tech == "SSIS" for f in ssis_files)


@pytest.mark.asyncio
async def test_assess_with_llm_opinion(qa_service, mock_manifest):
    """Test assessment with LLM opinion included"""
    
    with patch('apps.api.services.quick_assessment_service.DiscoveryService') as mock_discovery:
        mock_discovery.generate_manifest.return_value = mock_manifest

        mock_llm_opinion = "This is a standard SSIS migration scenario. Low risk. Proceed with confidence."
        with patch.object(qa_service.db, 'get_project_metadata', new_callable=AsyncMock) as mock_meta:
            mock_meta.return_value = None
            with patch.object(qa_service.db, 'get_project_settings', new_callable=AsyncMock) as mock_settings:
                mock_settings.return_value = {}
                with patch.object(qa_service, '_get_llm_opinion', new_callable=AsyncMock) as mock_llm:
                    mock_llm.return_value = mock_llm_opinion

                    result = await qa_service.assess("test-project-123")

                    assert result.llm_opinion == mock_llm_opinion


@pytest.mark.asyncio
async def test_assess_empty_folder(qa_service):
    """Test assessment when no files found (should raise ValueError)"""
    
    empty_manifest = {"file_inventory": []}

    with patch('apps.api.services.quick_assessment_service.DiscoveryService') as mock_discovery:
        mock_discovery.generate_manifest.return_value = empty_manifest

        with patch.object(qa_service.db, 'get_project_metadata', new_callable=AsyncMock) as mock_meta:
            mock_meta.return_value = None
            with patch.object(qa_service.db, 'get_project_settings', new_callable=AsyncMock) as mock_settings:
                mock_settings.return_value = {}

                with pytest.raises(ValueError, match="No files found"):
                    await qa_service.assess("empty-project")

# ================================================================
# RUN TESTS
# ================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
