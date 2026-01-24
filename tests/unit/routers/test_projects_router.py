"""
Unit Tests for Projects Router
Tests project CRUD operations, settings, and lifecycle management.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestProjectEndpoints:
    """Tests for project CRUD endpoints."""
    
    def test_list_projects_empty(self, test_client, mock_supabase):
        """Test listing projects when none exist."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = test_client.get("/projects", headers={"X-Tenant-ID": "test-tenant"})
        
        assert response.status_code == 200
    
    def test_list_projects_with_data(self, test_client, mock_supabase, sample_project):
        """Test listing projects returns project data."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.get("/projects", headers={"X-Tenant-ID": "test-tenant"})
        
        assert response.status_code == 200
    
    def test_get_project_by_id(self, test_client, mock_supabase, sample_project):
        """Test getting a project by UUID."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.get(
            f"/projects/{sample_project['id']}", 
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 200
    
    def test_get_project_not_found(self, test_client, mock_supabase):
        """Test getting a non-existent project."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = test_client.get(
            "/projects/nonexistent-uuid", 
            headers={"X-Tenant-ID": "test-tenant"}
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
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 403
        assert "Kill-switch" in response.json()["detail"]


class TestProjectAssets:
    """Tests for project asset endpoints."""
    
    def test_get_project_assets_empty(self, test_client, mock_supabase, sample_project):
        """Test getting assets for a project with no assets."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = test_client.get(
            f"/projects/{sample_project['id']}/assets",
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 200
        assert response.json()["assets"] == []
    
    def test_get_project_assets_with_data(self, test_client, mock_supabase, sample_project, sample_asset):
        """Test getting assets returns asset data."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_asset]
        
        response = test_client.get(
            f"/projects/{sample_project['id']}/assets",
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 200


class TestProjectLayout:
    """Tests for project layout/graph endpoints."""
    
    def test_get_layout_empty(self, test_client, mock_supabase, sample_project):
        """Test getting layout when none exists."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = test_client.get(
            f"/projects/{sample_project['id']}/layout",
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 200
    
    def test_save_layout(self, test_client, mock_supabase, sample_project):
        """Test saving layout data."""
        layout_data = {
            "nodes": [{"id": "node1", "position": {"x": 100, "y": 100}}],
            "edges": []
        }
        
        mock_supabase.table.return_value.upsert.return_value.execute.return_value.data = [{"id": "layout-id"}]
        
        response = test_client.post(
            f"/projects/{sample_project['id']}/layout",
            json=layout_data,
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 200


class TestProjectLifecycle:
    """Tests for project lifecycle endpoints."""
    
    def test_update_stage(self, test_client, mock_supabase, sample_project):
        """Test updating project stage."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.post(
            f"/projects/{sample_project['id']}/stage",
            json={"stage": "2"},
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 200
    
    def test_approve_triage(self, test_client, mock_supabase, sample_project):
        """Test approving triage transitions to DRAFTING."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.post(
            f"/projects/{sample_project['id']}/approve",
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DRAFTING"
    
    def test_unlock_triage(self, test_client, mock_supabase, sample_project):
        """Test unlocking returns to TRIAGE state."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.post(
            f"/projects/{sample_project['id']}/unlock",
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "TRIAGE"
    
    def test_reset_project(self, test_client, mock_supabase, sample_project):
        """Test resetting project clears triage data."""
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []
        
        response = test_client.post(
            f"/projects/{sample_project['id']}/reset",
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 200


class TestProjectSettings:
    """Tests for project settings endpoints."""
    
    def test_get_settings(self, test_client, mock_supabase, sample_project):
        """Test getting project settings."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.get(
            f"/projects/{sample_project['id']}/settings",
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 200
    
    def test_update_settings(self, test_client, mock_supabase, sample_project):
        """Test updating project settings."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [sample_project]
        
        response = test_client.patch(
            f"/projects/{sample_project['id']}/settings",
            json={"source_tech": "ORACLE", "target_tech": "SNOWFLAKE"},
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 200
