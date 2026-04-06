"""
Sprint v4.0.3 Tests — Phase Landing Consistency And Help Refresh
Covers:
  - Sidebar metrics endpoint by stage (backend)
  - Status → stage mapping (_detect_stage_from_status)
  - Progress and agent extraction from logs
  - Phase lifecycle: approve, unlock
  - Sidebar auto-correction and section config (sidebar-sections config)
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


# ---------------------------------------------------------------------------
# Helpers / unit tests for pure functions (no HTTP needed)
# ---------------------------------------------------------------------------

class TestDetectStageFromStatus:
    """Unit tests for _detect_stage_from_status helper."""

    @pytest.fixture(autouse=True)
    def import_fn(self):
        from apps.api.routers.projects import _detect_stage_from_status
        self.detect = _detect_stage_from_status

    def test_discovery_statuses_map_to_stage_0(self):
        assert self.detect("DISCOVERY") == 0
        assert self.detect("UPLOADING") == 0

    def test_triage_statuses_map_to_stage_1(self):
        assert self.detect("TRIAGE") == 1
        assert self.detect("PROCESSING") == 1
        assert self.detect("TRIAGED") == 1

    def test_drafting_statuses_map_to_stage_2(self):
        assert self.detect("TRIAGE_APPROVED") == 2
        assert self.detect("DRAFTING") == 2
        assert self.detect("ORCHESTRATING") == 2
        assert self.detect("DRAFTED") == 2

    def test_refinement_statuses_map_to_stage_3(self):
        assert self.detect("REFINEMENT") == 3
        assert self.detect("REFINING") == 3
        assert self.detect("REFINED") == 3

    def test_governance_statuses_map_to_stage_4(self):
        assert self.detect("GOVERNANCE") == 4
        assert self.detect("DOCUMENTING") == 4
        assert self.detect("COMPLETED") == 4

    def test_unknown_status_defaults_to_stage_0(self):
        assert self.detect("UNKNOWN_STATUS") == 0
        assert self.detect("") == 0

    def test_case_insensitive(self):
        assert self.detect("triage") == 1
        assert self.detect("Drafting") == 2
        assert self.detect("completed") == 4


class TestCalculateProgressFromLogs:
    """Unit tests for _calculate_progress_from_logs helper."""

    @pytest.fixture(autouse=True)
    def import_fn(self):
        from apps.api.routers.projects import _calculate_progress_from_logs
        self.calc = _calculate_progress_from_logs

    def test_empty_logs_returns_zero(self):
        assert self.calc([]) == 0

    def test_agent_a_in_logs_returns_low_progress(self):
        logs = [{"log_message": "Agent-A started analysis"}]
        result = self.calc(logs)
        assert 10 <= result <= 30

    def test_agent_c_in_logs_returns_mid_progress(self):
        logs = [{"log_message": "Agent-C transpiling object"}]
        result = self.calc(logs)
        assert 50 <= result <= 80

    def test_agent_f_in_logs_returns_high_progress(self):
        logs = [{"log_message": "Agent-F reviewing code quality"}]
        result = self.calc(logs)
        assert result == 80

    def test_agent_g_in_logs_returns_near_complete(self):
        logs = [{"log_message": "Agent-G generating governance artifacts"}]
        result = self.calc(logs)
        assert result == 95

    def test_no_agent_mention_returns_minimal_progress(self):
        logs = [{"log_message": "Execution started"}]
        result = self.calc(logs)
        assert result == 5


class TestExtractCurrentAgent:
    """Unit tests for _extract_current_agent helper."""

    @pytest.fixture(autouse=True)
    def import_fn(self):
        from apps.api.routers.projects import _extract_current_agent
        self.extract = _extract_current_agent

    def test_empty_logs_returns_none(self):
        assert self.extract([]) is None

    def test_extracts_agent_g_from_latest_log(self):
        logs = [
            {"log_message": "Agent-G producing output"},
            {"log_message": "Agent-C transpiling"},
        ]
        assert self.extract(logs) == "Agent-G"

    def test_extracts_agent_a_when_only_agent_present(self):
        logs = [{"log_message": "Agent-A running discovery"}]
        assert self.extract(logs) == "Agent-A"

    def test_returns_none_when_no_agent_in_log(self):
        logs = [{"log_message": "System initializing"}]
        assert self.extract(logs) is None


# ---------------------------------------------------------------------------
# Sidebar Metrics — HTTP endpoint tests
# ---------------------------------------------------------------------------

class TestSidebarMetricsEndpoint:
    """Tests for GET /projects/{id}/sidebar-metrics."""

    def _make_project(self, status="TRIAGE"):
        return {
            "project_id": "550e8400-e29b-41d4-a716-446655440000",
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "TestProject",
            "stage": "1",
            "status": status,
            "source_tech": "SQLSERVER",
            "target_tech": "SNOWFLAKE",
            "settings": {"source_tech": "SQLSERVER", "target_tech": "SNOWFLAKE"},
            "is_active": True,
            "created_at": "2026-01-01T00:00:00Z",
        }

    HEADERS = {"X-Tenant-ID": "550e8400-e29b-41d4-a716-446655440001", "X-Client-ID": "550e8400-e29b-41d4-a716-446655440002"}

    def test_sidebar_metrics_returns_200(self, test_client, mock_supabase, sample_project):
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_project]

        with patch("apps.api.routers.projects.QuickAssessmentService") as MockQA, \
             patch("apps.api.routers.projects.TableImpactService") as MockTI:
            MockQA.return_value.assess = AsyncMock(return_value=MagicMock(score=75, semaforo="green"))
            MockTI.return_value.get_table_summary = AsyncMock(return_value=[])

            response = test_client.get(
                f"/projects/{sample_project['id']}/sidebar-metrics?stage=1",
                headers=self.HEADERS,
            )

        assert response.status_code == 200

    def test_sidebar_metrics_stage_0_has_required_keys(self, test_client, mock_supabase):
        project = self._make_project(status="DISCOVERY")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [project]

        response = test_client.get(
            f"/projects/{project['id']}/sidebar-metrics?stage=0",
            headers=self.HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert "fileCount" in data
        assert "uploadStatus" in data
        assert "executionStatus" in data

    def test_sidebar_metrics_stage_1_has_required_keys(self, test_client, mock_supabase, sample_project):
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_project]

        with patch("apps.api.routers.projects.QuickAssessmentService") as MockQA, \
             patch("apps.api.routers.projects.TableImpactService") as MockTI:
            MockQA.return_value.assess = AsyncMock(return_value=MagicMock(score=70, semaforo="yellow"))
            MockTI.return_value.get_table_summary = AsyncMock(return_value=[{}, {}])

            response = test_client.get(
                f"/projects/{sample_project['id']}/sidebar-metrics?stage=1",
                headers=self.HEADERS,
            )

        assert response.status_code == 200
        data = response.json()
        assert "assetCount" in data
        assert "tableCount" in data
        assert "executionStatus" in data

    def test_sidebar_metrics_stage_2_has_required_keys(self, test_client, mock_supabase):
        project = self._make_project(status="DRAFTING")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [project]

        response = test_client.get(
            f"/projects/{project['id']}/sidebar-metrics?stage=2",
            headers=self.HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert "filesGenerated" in data
        assert "generationProgress" in data
        assert "bronzeNodes" in data
        assert "silverNodes" in data
        assert "goldNodes" in data

    def test_sidebar_metrics_stage_3_has_required_keys(self, test_client, mock_supabase):
        project = self._make_project(status="REFINEMENT")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [project]

        response = test_client.get(
            f"/projects/{project['id']}/sidebar-metrics?stage=3",
            headers=self.HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert "refinementStatus" in data
        assert "issueCount" in data
        assert "validationCount" in data

    def test_sidebar_metrics_stage_4_has_required_keys(self, test_client, mock_supabase):
        project = self._make_project(status="COMPLETED")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [project]

        response = test_client.get(
            f"/projects/{project['id']}/sidebar-metrics?stage=4",
            headers=self.HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert "docsGenerated" in data
        assert "bundleReady" in data

    def test_sidebar_metrics_completed_project_bundle_ready(self, test_client, mock_supabase):
        project = self._make_project(status="COMPLETED")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [project]

        response = test_client.get(
            f"/projects/{project['id']}/sidebar-metrics?stage=4",
            headers=self.HEADERS,
        )

        assert response.status_code == 200
        assert response.json()["bundleReady"] is True

    def test_sidebar_metrics_returns_404_for_missing_project(self, test_client, mock_supabase):
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        response = test_client.get(
            "/projects/550e8400-e29b-41d4-a716-446655440099/sidebar-metrics?stage=0",
            headers=self.HEADERS,
        )

        assert response.status_code == 404

    def test_sidebar_metrics_auto_detects_stage_from_status(self, test_client, mock_supabase):
        """When no ?stage param, stage is inferred from project status."""
        project = self._make_project(status="DISCOVERY")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [project]

        response = test_client.get(
            f"/projects/{project['id']}/sidebar-metrics",
            headers=self.HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        # Stage 0 keys should be present since status=DISCOVERY
        assert "fileCount" in data
        assert "uploadStatus" in data

    def test_sidebar_metrics_all_stages_include_execution_status(self, test_client, mock_supabase):
        """executionStatus must be present at every stage."""
        project = self._make_project(status="DRAFTING")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [project]

        for stage in [0, 2, 3, 4]:
            response = test_client.get(
                f"/projects/{project['id']}/sidebar-metrics?stage={stage}",
                headers=self.HEADERS,
            )
            assert response.status_code == 200
            assert "executionStatus" in response.json(), f"Missing executionStatus at stage {stage}"


# ---------------------------------------------------------------------------
# Phase Lifecycle — approve / unlock (stage landing consistency)
# ---------------------------------------------------------------------------

class TestPhaseLandingLifecycle:
    """
    Tests that approve/unlock transitions produce the correct status and stage,
    ensuring the workspace can land on the correct phase.
    """

    def test_approve_triage_transitions_to_drafting_stage(self, test_client, mock_supabase, sample_project, auth_headers):
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [sample_project]

        response = test_client.post(
            f"/projects/{sample_project['id']}/approve",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "TRIAGE_APPROVED"

    def test_unlock_triage_reverts_to_triage_stage(self, test_client, mock_supabase, sample_project, auth_headers):
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [sample_project]

        response = test_client.post(
            f"/projects/{sample_project['id']}/unlock",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "TRIAGE"

    def test_approve_maps_to_stage_2_via_status_detection(self):
        """TRIAGE_APPROVED status should map to stage 2 (Drafting landing)."""
        from apps.api.routers.projects import _detect_stage_from_status
        assert _detect_stage_from_status("TRIAGE_APPROVED") == 2

    def test_unlock_maps_to_stage_1_via_status_detection(self):
        """TRIAGE status should map to stage 1 (Triage landing)."""
        from apps.api.routers.projects import _detect_stage_from_status
        assert _detect_stage_from_status("TRIAGE") == 1


# ---------------------------------------------------------------------------
# Sidebar sections config — overview as canonical first landing
# ---------------------------------------------------------------------------

class TestSidebarSectionsConfig:
    """
    Tests for apps/web/app/config/sidebar-sections.ts logic equivalents.
    Validates that overview is defined as the first section per stage
    and that helper utilities behave correctly.
    The actual TS config is validated here through its Python-equivalent
    structure check against the actual file on disk.
    """

    SIDEBAR_SECTIONS_PATH = r"C:\proyectos_dev\UTM\apps\web\app\config\sidebar-sections.ts"

    def _load_sidebar_source(self):
        with open(self.SIDEBAR_SECTIONS_PATH, "r", encoding="utf-8") as f:
            return f.read()

    def test_sidebar_sections_file_exists(self):
        import os
        assert os.path.exists(self.SIDEBAR_SECTIONS_PATH), \
            "sidebar-sections.ts not found — navigation config is missing"

    def test_all_stages_declare_overview_section(self):
        """Each stage block must declare an 'overview' id entry."""
        source = self._load_sidebar_source()
        # Every stage should contain id: 'overview'
        assert source.count("id: 'overview'") >= 6, \
            "Expected at least one overview section per stage (6 stages)"

    def test_overview_appears_before_other_sections_in_source(self):
        """overview must appear before run-* and action entries in the file."""
        source = self._load_sidebar_source()
        overview_pos = source.find("id: 'overview'")
        run_triage_pos = source.find("id: 'run-triage'")
        run_translation_pos = source.find("id: 'run-translation'")

        assert overview_pos != -1, "overview section not found"
        if run_triage_pos != -1:
            assert overview_pos < run_triage_pos, \
                "overview must appear before run-triage in sidebar config"
        if run_translation_pos != -1:
            assert overview_pos < run_translation_pos, \
                "overview must appear before run-translation in sidebar config"

    def test_getSectionsForStage_helper_is_exported(self):
        source = self._load_sidebar_source()
        assert "getSectionsForStage" in source, \
            "getSectionsForStage helper must be exported from sidebar-sections.ts"

    def test_getAllSectionIds_helper_is_exported(self):
        source = self._load_sidebar_source()
        assert "getAllSectionIds" in source, \
            "getAllSectionIds helper must be exported from sidebar-sections.ts"

    def test_run_actions_have_action_variant(self):
        """run-* actions must use variant: 'action' not variant: 'view'."""
        source = self._load_sidebar_source()
        # Find a run- block and check it's followed by action variant before next section
        run_idx = source.find("'run-triage'")
        if run_idx == -1:
            pytest.skip("run-triage section not found, skipping variant check")
        snippet = source[run_idx: run_idx + 200]
        assert "'action'" in snippet, \
            "run-triage must have variant: 'action' to prevent sticky landing"

    def test_overview_sections_have_view_variant(self):
        """overview sections must use variant: 'view'."""
        source = self._load_sidebar_source()
        overview_idx = source.find("id: 'overview'")
        assert overview_idx != -1
        snippet = source[overview_idx: overview_idx + 200]
        assert "'view'" in snippet, \
            "overview section must have variant: 'view'"


# ---------------------------------------------------------------------------
# Help content — Markdown source files for each stage
# ---------------------------------------------------------------------------

class TestStageHelpContent:
    """
    Validates that all stage help content files (0.md–5.md) exist and
    reference 'overview' as the landing entry point.
    """

    HELP_DIR = r"C:\proyectos_dev\UTM\apps\web\public\help\stages"

    def _read_stage_md(self, stage_id: int) -> str:
        path = f"{self.HELP_DIR}\\{stage_id}.md"
        import os
        if not os.path.exists(path):
            pytest.skip(f"Help file {stage_id}.md not found")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @pytest.mark.parametrize("stage_id", [0, 1, 2, 3, 4, 5])
    def test_stage_help_file_exists(self, stage_id):
        import os
        path = f"{self.HELP_DIR}\\{stage_id}.md"
        assert os.path.exists(path), f"Help file {stage_id}.md is missing"

    @pytest.mark.parametrize("stage_id", [1, 2, 3])
    def test_stage_help_mentions_overview_landing(self, stage_id):
        """Key stages must document landing on Overview first."""
        content = self._read_stage_md(stage_id)
        assert "overview" in content.lower() or "Overview" in content, \
            f"Stage {stage_id} help file should mention the Overview landing page"

    @pytest.mark.parametrize("stage_id", [0, 1, 2, 3, 4, 5])
    def test_stage_help_file_is_not_empty(self, stage_id):
        content = self._read_stage_md(stage_id)
        assert len(content.strip()) > 50, \
            f"Stage {stage_id} help file appears empty or too short"

    @pytest.mark.parametrize("stage_id", [0, 1, 2, 3, 4, 5])
    def test_stage_html_file_exists(self, stage_id):
        """Pre-compiled HTML versions must exist alongside Markdown source."""
        import os
        html_path = f"{self.HELP_DIR}\\{stage_id}.html"
        assert os.path.exists(html_path), \
            f"Compiled help HTML {stage_id}.html is missing (run md→html compilation)"
