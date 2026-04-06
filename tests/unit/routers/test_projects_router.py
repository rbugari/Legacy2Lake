"""
Unit Tests for Projects Router
Tests project CRUD operations, settings, and lifecycle management.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from apps.api.services.quick_assessment_service import QuickAssessmentResult
from apps.api.routers.projects import _build_evidence_review_key


class TestProjectEndpoints:
    """Tests for project CRUD endpoints."""

    VALID_HEADERS = {
        "X-Tenant-ID": "550e8400-e29b-41d4-a716-446655440010",
        "X-Client-ID": "550e8400-e29b-41d4-a716-446655440011",
    }
    
    def test_list_projects_empty(self, test_client, mock_supabase):
        """Test listing projects when none exist."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = test_client.get("/projects", headers=self.VALID_HEADERS)
        
        assert response.status_code == 200
    
    def test_list_projects_with_data(self, test_client, mock_supabase, sample_project):
        """Test listing projects returns project data."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.get("/projects", headers=self.VALID_HEADERS)
        
        assert response.status_code == 200
    
    def test_get_project_by_id(self, test_client, mock_supabase, sample_project):
        """Test getting a project by UUID."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.get(
            f"/projects/{sample_project['id']}", 
            headers=self.VALID_HEADERS
        )
        
        assert response.status_code == 200
    
    def test_get_project_not_found(self, test_client, mock_supabase):
        """Test getting a non-existent project."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = test_client.get(
            "/projects/550e8400-e29b-41d4-a716-446655440099", 
            headers=self.VALID_HEADERS
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
    
    def test_get_project_inactive_returns_403(self, test_client, mock_supabase, sample_project):
        """Test getting an inactive project returns 403."""
        sample_project["is_active"] = False
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.get(
            f"/projects/{sample_project['id']}", 
            headers=self.VALID_HEADERS
        )
        
        assert response.status_code == 403


class TestProjectAssets:
    """Tests for project asset endpoints."""

    VALID_HEADERS = TestProjectEndpoints.VALID_HEADERS
    
    def test_get_project_assets_empty(self, test_client, mock_supabase, sample_project):
        """Test getting assets for a project with no assets."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = test_client.get(
            f"/projects/{sample_project['id']}/assets",
            headers=self.VALID_HEADERS
        )
        
        assert response.status_code == 200
        assert response.json()["assets"] == []
    
    def test_get_project_assets_with_data(self, test_client, mock_supabase, sample_project, sample_asset):
        """Test getting assets returns asset data."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_asset]
        
        response = test_client.get(
            f"/projects/{sample_project['id']}/assets",
            headers=self.VALID_HEADERS
        )
        
        assert response.status_code == 200


class TestProjectLayout:
    """Tests for project layout/graph endpoints."""

    VALID_HEADERS = TestProjectEndpoints.VALID_HEADERS
    
    def test_get_layout_empty(self, test_client, mock_supabase, sample_project):
        """Test getting layout when none exists."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = test_client.get(
            f"/projects/{sample_project['id']}/layout",
            headers=self.VALID_HEADERS
        )
        
        assert response.status_code == 200
    
    def test_save_layout(self, test_client, mock_supabase, sample_project):
        """Test saving layout data."""
        layout_data = {
            "nodes": [{"id": "node1", "position": {"x": 100, "y": 100}}],
            "edges": []
        }

        with patch("apps.api.routers.projects.SupabasePersistence.save_project_layout", AsyncMock(return_value="layout-id")):
            response = test_client.post(
                f"/projects/{sample_project['id']}/layout",
                json=layout_data,
                headers=self.VALID_HEADERS
            )

        assert response.status_code == 200


class TestProjectLifecycle:
    """Tests for project lifecycle endpoints."""

    VALID_HEADERS = TestProjectEndpoints.VALID_HEADERS
    
    def test_update_stage(self, test_client, mock_supabase, sample_project):
        """Test updating project stage."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.post(
            f"/projects/{sample_project['id']}/stage",
            json={"stage": "2"},
            headers=self.VALID_HEADERS
        )
        
        assert response.status_code == 200
    
    def test_approve_triage(self, test_client, mock_supabase, sample_project):
        """Test approving triage transitions to DRAFTING."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.post(
            f"/projects/{sample_project['id']}/approve",
            headers=self.VALID_HEADERS
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "TRIAGE_APPROVED"
    
    def test_unlock_triage(self, test_client, mock_supabase, sample_project):
        """Test unlocking returns to TRIAGE state."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.post(
            f"/projects/{sample_project['id']}/unlock",
            headers=self.VALID_HEADERS
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "TRIAGE"
    
    def test_reset_project(self, test_client, mock_supabase, sample_project):
        """Test resetting project clears triage data."""
        from apps.api.services.project_cleanup_service import ProjectCleanupService

        with patch.object(ProjectCleanupService, "reset_project", AsyncMock(return_value={
            "backup_created": True,
            "backup_path": "backups/test.zip",
            "stages_cleaned": ["drafting"],
            "files_removed": 3,
            "database_reset": True,
            "errors": [],
        })):
            response = test_client.post(
                f"/projects/{sample_project['id']}/reset",
                headers=self.VALID_HEADERS
            )
        
        assert response.status_code == 200


class TestProjectSettings:
    """Tests for project settings endpoints."""

    VALID_HEADERS = {
        "X-Tenant-ID": "550e8400-e29b-41d4-a716-446655440010",
        "X-Client-ID": "550e8400-e29b-41d4-a716-446655440011",
    }
    
    def test_get_settings(self, test_client, mock_supabase, sample_project):
        """Test getting project settings."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.get(
            f"/projects/{sample_project['id']}/settings",
            headers=self.VALID_HEADERS
        )
        
        assert response.status_code == 200
    
    def test_update_settings(self, test_client, mock_supabase, sample_project):
        """Test updating project settings."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.patch(
            f"/projects/{sample_project['id']}/settings",
            json={"source_tech": "ORACLE", "target_tech": "SNOWFLAKE"},
            headers=self.VALID_HEADERS
        )
        
        assert response.status_code == 200

    def test_update_settings_triggers_readiness_recompute(self, test_client, mock_supabase, sample_project):
        """Test that relevant settings changes trigger readiness recomputation."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [sample_project]

        with patch("apps.api.routers.projects.ReadinessService") as MockReadiness:
            MockReadiness.return_value.compute_and_persist = AsyncMock(return_value={"status": "READY"})

            response = test_client.patch(
                f"/projects/{sample_project['id']}/settings",
                json={"source_tech": "ORACLE"},
                headers=self.VALID_HEADERS
            )

        assert response.status_code == 200
        MockReadiness.return_value.compute_and_persist.assert_awaited_once_with(sample_project["id"])

    def test_update_settings_without_tech_change_skips_readiness_recompute(self, test_client, mock_supabase, sample_project):
        """Test that unrelated settings changes do not force a readiness recompute."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [sample_project]

        with patch("apps.api.routers.projects.ReadinessService") as MockReadiness:
            response = test_client.patch(
                f"/projects/{sample_project['id']}/settings",
                json={"migration_limit": 10},
                headers=self.VALID_HEADERS
            )

        assert response.status_code == 200
        MockReadiness.assert_not_called()


class TestDiscoveryClassificationAndEvidence:
    """Tests for discovery inventory overrides and evidence review flows."""

    VALID_HEADERS = {
        "X-Tenant-ID": "550e8400-e29b-41d4-a716-446655440030",
        "X-Client-ID": "550e8400-e29b-41d4-a716-446655440031",
    }

    def test_file_inventory_applies_saved_pre_classification(self, test_client, mock_supabase, sample_project):
        """Saved manual classification should override the suggested inventory classification."""
        manifest = {
            "file_inventory": [
                {
                    "name": "load_customer.dtsx",
                    "path": "Triage/load_customer.dtsx",
                    "size": 1200,
                    "lines": 12,
                    "signatures": [],
                    "invocations": [],
                    "snippet": "",
                    "metadata": {},
                    "evidence_count": 0,
                }
            ]
        }

        with patch("apps.api.routers.projects.SupabasePersistence.get_project_settings", AsyncMock(return_value={
            "pre_classification": {
                "Triage/load_customer.dtsx": {
                    "classification": "SUPPORT",
                    "include": False,
                }
            }
        })), \
             patch("apps.api.routers.projects.DiscoveryService.generate_manifest", return_value=manifest), \
             patch("apps.api.routers.projects.QuickAssessmentService") as MockQuickAssessment:
            MockQuickAssessment.return_value._classify_file.return_value = ("migrable", "SQLSERVER")

            response = test_client.get(
                f"/projects/{sample_project['id']}/file-inventory",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["files"][0]["classification"] == "SUPPORT"
        assert data["files"][0]["include"] is False
        assert data["files"][0]["has_override"] is True
        assert data["files"][0]["classification_source"] == "manual"

    def test_update_project_evidence_review_persists_settings(self, test_client, mock_supabase, sample_project):
        """Updating evidence state should merge into project settings."""
        review_key = "abc123"

        with patch("apps.api.routers.projects.SupabasePersistence.get_project_settings", AsyncMock(return_value={})), \
             patch("apps.api.routers.projects.SupabasePersistence.update_project_settings", AsyncMock(return_value=True)) as mock_update_settings:
            response = test_client.patch(
                f"/projects/{sample_project['id']}/evidence/review",
                json={
                    "review_key": review_key,
                    "state": "reviewed",
                    "note": "Looks valid",
                },
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 200
        mock_update_settings.assert_awaited_once()
        updated_settings = mock_update_settings.await_args.args[1]
        assert updated_settings["evidence_review"][review_key]["state"] == "reviewed"
        assert updated_settings["evidence_review"][review_key]["note"] == "Looks valid"


class TestQuickAssessment:
    """Tests for quick assessment flow."""

    VALID_HEADERS = {
        "X-Tenant-ID": "550e8400-e29b-41d4-a716-446655440020",
        "X-Client-ID": "550e8400-e29b-41d4-a716-446655440021",
    }

    def test_quick_assessment_triggers_readiness_recompute(self, test_client, mock_supabase, sample_project):
        """Test that quick assessment persists the result and refreshes readiness."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [sample_project]

        assessment_result = QuickAssessmentResult(
            score=78,
            semaforo="green",
            file_breakdown={"migrable": 3, "soporte": 2, "documentacion": 0, "no_reconocido": 0},
            detected_techs=["SQLSERVER"],
            blockers=[],
            file_details=[],
            total_files=5,
            total_lines=120,
            llm_opinion=None,
            assessed_at="2026-04-01T00:00:00Z",
        )

        with patch("apps.api.routers.projects.QuickAssessmentService") as MockQuickAssessment, \
             patch("apps.api.routers.projects.ReadinessService") as MockReadiness:
            MockQuickAssessment.return_value.assess = AsyncMock(return_value=assessment_result)
            MockReadiness.return_value.compute_and_persist = AsyncMock(return_value={"status": "READY"})

            response = test_client.post(
                f"/projects/{sample_project['id']}/quick-assessment",
                headers=self.VALID_HEADERS
            )

        assert response.status_code == 200
        MockReadiness.return_value.compute_and_persist.assert_awaited_once_with(sample_project["id"])


class TestExecutiveSummaryEndpoints:
    """Tests for executive summary and gaps summary endpoints."""

    VALID_HEADERS = {
        "X-Tenant-ID": "550e8400-e29b-41d4-a716-446655440060",
        "X-Client-ID": "550e8400-e29b-41d4-a716-446655440061",
    }

    def test_get_executive_summary_returns_readiness_fields(self, test_client, sample_project):
        """Executive summary endpoint should expose readiness warnings and next steps."""
        payload = {
            "migration_posture": "Moderate — Proceed with monitoring",
            "confidence_score": 72,
            "source_tech": "SQLSERVER",
            "target_tech": "SNOWFLAKE",
            "detected_techs": ["SQLSERVER"],
            "total_assets": 5,
            "migrable_assets": 4,
            "pii_assets": 1,
            "top_risks": ["Quick assessment is YELLOW — proceed with guarded review"],
            "manual_effort_areas": ["Compliance / PII handling (1 item(s))"],
            "open_blockers": [],
            "readiness_warnings": ["Quick assessment is YELLOW — proceed with guarded review"],
            "readiness_next_steps": ["Address the top warnings and recompute readiness."],
            "recommended_next_action": "Address the top warnings and recompute readiness.",
            "readiness_status": "BASELINE_READY",
            "total_gaps": 1,
            "decision_queue": [],
            "decision_focus": "No pending decision queue detected.",
            "decision_open_count": 0,
            "computed_at": "2026-04-05T00:00:00Z",
        }

        with patch("apps.api.routers.projects.ExecutiveSummaryService") as MockService:
            MockService.return_value.get_executive_summary = AsyncMock(return_value=payload)

            response = test_client.get(
                f"/projects/{sample_project['id']}/executive-summary",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["readiness_warnings"] == ["Quick assessment is YELLOW — proceed with guarded review"]
        assert data["readiness_next_steps"] == ["Address the top warnings and recompute readiness."]
        assert data["recommended_next_action"] == "Address the top warnings and recompute readiness."

    def test_get_executive_summary_returns_404_when_project_missing(self, test_client, sample_project):
        """Executive summary endpoint should surface not-found as 404."""
        with patch("apps.api.routers.projects.ExecutiveSummaryService") as MockService:
            MockService.return_value.get_executive_summary = AsyncMock(side_effect=ValueError("Project not found"))

            response = test_client.get(
                f"/projects/{sample_project['id']}/executive-summary",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 404


class TestProjectUnderstandingEndpoints:
    """Tests for Block 3 understanding endpoints exposed by projects router."""

    VALID_HEADERS = {
        "X-Tenant-ID": "550e8400-e29b-41d4-a716-446655440050",
        "X-Client-ID": "550e8400-e29b-41d4-a716-446655440051",
    }

    @pytest.mark.parametrize(
        "path_suffix,mock_method,mock_payload",
        [
            ("functional-map", "get_functional_map", {"domains": [], "version": "v1"}),
            ("operational-map", "get_operational_map", {"processes": [], "version": "v1"}),
            ("recommendations", "get_recommendation_set", {"items": [], "version": "v1"}),
            ("rule-candidates", "get_rule_candidates", {"candidates": [], "version": "v1"}),
        ],
    )
    def test_understanding_get_endpoints_return_payload(
        self,
        test_client,
        sample_project,
        path_suffix,
        mock_method,
        mock_payload,
    ):
        """Understanding read endpoints should return service payload as-is."""
        with patch("apps.api.routers.projects.UnderstandingService") as MockUnderstanding:
            setattr(MockUnderstanding.return_value, mock_method, AsyncMock(return_value=mock_payload))

            response = test_client.get(
                f"/projects/{sample_project['id']}/understanding/{path_suffix}",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 200
        assert response.json() == mock_payload

    def test_understanding_rebuild_returns_status_and_payload(self, test_client, sample_project):
        """Rebuild endpoint should include status, generated_at and payload."""
        rebuilt_payload = {
            "generated_at": "2026-04-01T00:00:00Z",
            "version": "v1",
            "project_id": sample_project["id"],
            "functional_map": {"domains": []},
            "operational_map": {"processes": []},
            "recommendation_set": {"items": []},
            "rule_candidate_summary": {"candidates": []},
        }

        with patch("apps.api.routers.projects.UnderstandingService") as MockUnderstanding:
            MockUnderstanding.return_value.rebuild = AsyncMock(return_value=rebuilt_payload)

            response = test_client.post(
                f"/projects/{sample_project['id']}/understanding/rebuild",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rebuilt"
        assert data["generated_at"] == "2026-04-01T00:00:00Z"
        assert data["payload"] == rebuilt_payload
        assert set(data["payload"].keys()) == {
            "generated_at",
            "version",
            "project_id",
            "functional_map",
            "operational_map",
            "recommendation_set",
            "rule_candidate_summary",
        }
        assert data["payload"]["generated_at"] == data["generated_at"]

    def test_understanding_refresh_alias_reuses_rebuild_and_resolves_project_name(self, test_client, sample_project):
        """Refresh endpoint should behave as alias of rebuild and resolve non-UUID project ids."""
        rebuilt_payload = {
            "generated_at": "2026-04-01T12:00:00Z",
            "version": "v1",
            "project_id": sample_project["id"],
            "functional_map": {"domains": [{"name": "Finance"}]},
            "operational_map": {"processes": []},
            "recommendation_set": {"items": []},
            "rule_candidate_summary": {"candidates": []},
        }

        with patch(
            "apps.api.routers.projects.SupabasePersistence.get_project_id_by_name",
            AsyncMock(return_value=sample_project["id"]),
        ), patch("apps.api.routers.projects.UnderstandingService") as MockUnderstanding:
            MockUnderstanding.return_value.rebuild = AsyncMock(return_value=rebuilt_payload)

            response = test_client.post(
                "/projects/TestProject/understanding/refresh",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rebuilt"
        assert data["generated_at"] == "2026-04-01T12:00:00Z"
        assert data["payload"] == rebuilt_payload
        assert data["payload"]["generated_at"] == data["generated_at"]
        MockUnderstanding.assert_called_once_with(
            project_id=sample_project["id"],
            tenant_id=self.VALID_HEADERS["X-Tenant-ID"],
            client_id=self.VALID_HEADERS["X-Client-ID"],
        )
        MockUnderstanding.return_value.rebuild.assert_awaited_once()

    def test_understanding_rebuild_returns_500_when_payload_missing_required_keys(self, test_client, sample_project):
        """Rebuild should fail with controlled error when payload contract is incomplete."""
        incomplete_payload = {
            "version": "v1",
            "project_id": sample_project["id"],
            "functional_map": {"domains": []},
            "operational_map": {"processes": []},
            "recommendation_set": {"items": []},
            "rule_candidate_summary": {"candidates": []},
        }

        with patch("apps.api.routers.projects.UnderstandingService") as MockUnderstanding:
            MockUnderstanding.return_value.rebuild = AsyncMock(return_value=incomplete_payload)

            response = test_client.post(
                f"/projects/{sample_project['id']}/understanding/rebuild",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 500
        assert "missing keys" in response.text

    def test_understanding_refresh_returns_500_when_nested_section_contract_is_invalid(self, test_client, sample_project):
        """Refresh alias should enforce the same section-level contract validation as rebuild."""
        invalid_payload = {
            "generated_at": "2026-04-01T12:00:00Z",
            "version": "v1",
            "project_id": sample_project["id"],
            "functional_map": {},
            "operational_map": {"processes": []},
            "recommendation_set": {"items": []},
            "rule_candidate_summary": {"candidates": []},
        }

        with patch("apps.api.routers.projects.UnderstandingService") as MockUnderstanding:
            MockUnderstanding.return_value.rebuild = AsyncMock(return_value=invalid_payload)

            response = test_client.post(
                f"/projects/{sample_project['id']}/understanding/refresh",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 500
        assert "functional_map" in response.text


class TestProjectExportEndpoints:
    """Tests for export endpoints (Block 4 Downstreams)."""

    VALID_HEADERS = {
        "X-Tenant-ID": "550e8400-e29b-41d4-a716-446655440010",
        "X-Client-ID": "550e8400-e29b-41d4-a716-446655440011",
    }

    def test_export_documentation_markdown(self, test_client, sample_project):
        """Test export documentation in markdown format."""
        mock_result = {
            "format": "markdown",
            "project_id": sample_project["id"],
            "project_name": sample_project["name"],
            "content": "# Documentation\n...",
            "metadata": {"lines": 100, "sections": 5},
            "toc": [{"level": 2, "title": "Test"}],
            "generated_at": "2026-04-01T12:00:00Z",
        }

        with patch(
            "apps.api.services.documentation_export_service.DocumentationExportService"
        ) as MockExport:
            mock_export_instance = MagicMock()
            mock_export_instance.export_full_documentation = AsyncMock(
                return_value=mock_result
            )
            MockExport.return_value = mock_export_instance

            response = test_client.get(
                f"/projects/{sample_project['id']}/export/documentation?format=markdown",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "markdown"
        assert data["project_id"] == sample_project["id"]
        assert "content" in data

    def test_export_documentation_html(self, test_client, sample_project):
        """Test export documentation in HTML format."""
        mock_result = {
            "format": "html",
            "project_id": sample_project["id"],
            "content": "<!DOCTYPE html>...",
            "metadata": {"lines": 150},
            "generated_at": "2026-04-01T12:00:00Z",
        }

        with patch(
            "apps.api.services.documentation_export_service.DocumentationExportService"
        ) as MockExport:
            mock_export_instance = MagicMock()
            mock_export_instance.export_full_documentation = AsyncMock(
                return_value=mock_result
            )
            MockExport.return_value = mock_export_instance

            response = test_client.get(
                f"/projects/{sample_project['id']}/export/documentation?format=html",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "html"
        assert "<!DOCTYPE" in data["content"]

    def test_export_documentation_json(self, test_client, sample_project):
        """Test export documentation in JSON format."""
        mock_result = {
            "format": "json",
            "project_id": sample_project["id"],
            "content": '{"project": {...}}',
            "metadata": {"lines": 50},
            "generated_at": "2026-04-01T12:00:00Z",
        }

        with patch(
            "apps.api.services.documentation_export_service.DocumentationExportService"
        ) as MockExport:
            mock_export_instance = MagicMock()
            mock_export_instance.export_full_documentation = AsyncMock(
                return_value=mock_result
            )
            MockExport.return_value = mock_export_instance

            response = test_client.get(
                f"/projects/{sample_project['id']}/export/documentation?format=json",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "json"

    def test_export_documentation_invalid_format(self, test_client, sample_project):
        """Test export with invalid format parameter."""
        response = test_client.get(
            f"/projects/{sample_project['id']}/export/documentation?format=invalid",
            headers=self.VALID_HEADERS,
        )

        assert response.status_code == 400
        assert "Invalid format" in response.text

    def test_export_documentation_missing_understanding(self, test_client, sample_project):
        """Test export fails gracefully when understanding not found."""
        mock_result = {"error": "understanding_not_found", "message": "No understanding found"}

        with patch(
            "apps.api.services.documentation_export_service.DocumentationExportService"
        ) as MockExport:
            mock_export_instance = MagicMock()
            mock_export_instance.export_full_documentation = AsyncMock(
                return_value=mock_result
            )
            MockExport.return_value = mock_export_instance

            response = test_client.get(
                f"/projects/{sample_project['id']}/export/documentation",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 404

    def test_export_rule_candidates(self, test_client, sample_project):
        """Test export rule candidates endpoint."""
        mock_result = {
            "project_id": sample_project["id"],
            "rule_candidates": [
                {
                    "name": "Rule1",
                    "description": "Test rule",
                    "reusability_score": "HIGH",
                    "implementation_status": "DRAFT",
                }
            ],
            "consolidation_opportunities": [],
            "generated_at": "2026-04-01T12:00:00Z",
        }

        with patch(
            "apps.api.services.documentation_export_service.DocumentationExportService"
        ) as MockExport:
            mock_export_instance = MagicMock()
            mock_export_instance.export_rule_candidates_with_tracking = AsyncMock(
                return_value=mock_result
            )
            MockExport.return_value = mock_export_instance

            response = test_client.get(
                f"/projects/{sample_project['id']}/export/rule-candidates",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == sample_project["id"]
        assert "rule_candidates" in data
        assert len(data["rule_candidates"]) == 1

    def test_export_recommendation_actions(self, test_client, sample_project):
        """Test export recommendation actions endpoint."""
        mock_result = {
            "project_id": sample_project["id"],
            "recommendation_actions": [
                {
                    "recommendation_id": "rec-001",
                    "title": "Test recommendation",
                    "severity": "HIGH",
                    "actions": [{"action_type": "create", "artifact_type": "documentation"}],
                    "implementation_path": "next_sprint",
                    "estimated_effort": "MEDIUM",
                }
            ],
            "generated_at": "2026-04-01T12:00:00Z",
        }

        with patch(
            "apps.api.services.documentation_export_service.DocumentationExportService"
        ) as MockExport:
            mock_export_instance = MagicMock()
            mock_export_instance.export_recommendation_actions = AsyncMock(
                return_value=mock_result
            )
            MockExport.return_value = mock_export_instance

            response = test_client.get(
                f"/projects/{sample_project['id']}/export/recommendation-actions",
                headers=self.VALID_HEADERS,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == sample_project["id"]
        assert "recommendation_actions" in data
        assert len(data["recommendation_actions"]) == 1

