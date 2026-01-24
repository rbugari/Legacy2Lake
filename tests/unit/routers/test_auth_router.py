"""
Unit Tests for Auth Router
Tests login functionality, password hashing, and authentication.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import bcrypt


class TestPasswordUtilities:
    """Tests for password hashing and verification utilities."""
    
    def test_sha256_verification_correct_password(self):
        """Test SHA256 password verification with correct password."""
        from apps.api.routers.auth import verify_password_sha256
        
        # SHA256 hash of 'password123'
        stored_hash = "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f"
        
        assert verify_password_sha256("password123", stored_hash) is True
    
    def test_sha256_verification_wrong_password(self):
        """Test SHA256 password verification with wrong password."""
        from apps.api.routers.auth import verify_password_sha256
        
        stored_hash = "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f"
        
        assert verify_password_sha256("wrongpassword", stored_hash) is False
    
    def test_bcrypt_hash_generation(self):
        """Test bcrypt hash generation produces valid hash."""
        from apps.api.routers.auth import hash_password_bcrypt, verify_password_bcrypt
        
        password = "securePassword123!"
        hashed = hash_password_bcrypt(password)
        
        # Hash should be a valid bcrypt hash
        assert hashed.startswith("$2")
        assert len(hashed) == 60
        
        # Should verify correctly
        assert verify_password_bcrypt(password, hashed) is True
        assert verify_password_bcrypt("wrongPassword", hashed) is False
    
    def test_bcrypt_verification_correct_password(self):
        """Test bcrypt password verification with correct password."""
        from apps.api.routers.auth import verify_password_bcrypt
        
        password = "testPassword123"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
        
        assert verify_password_bcrypt(password, hashed) is True
    
    def test_bcrypt_verification_wrong_password(self):
        """Test bcrypt password verification with wrong password."""
        from apps.api.routers.auth import verify_password_bcrypt
        
        password = "testPassword123"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
        
        assert verify_password_bcrypt("differentPassword", hashed) is False
    
    def test_bcrypt_verification_invalid_hash(self):
        """Test bcrypt verification handles invalid hash gracefully."""
        from apps.api.routers.auth import verify_password_bcrypt
        
        # Invalid hash should return False, not raise exception
        assert verify_password_bcrypt("password", "invalid-hash") is False
        assert verify_password_bcrypt("password", "") is False


class TestAuthEndpoints:
    """Tests for auth router endpoints."""
    
    def test_ping_antigravity(self, test_client):
        """Test the ping-antigravity health check endpoint."""
        response = test_client.get("/ping-antigravity")
        
        assert response.status_code == 200
        assert response.json() == {"message": "pong-antigravity"}
    
    def test_login_missing_credentials(self, test_client):
        """Test login with missing credentials returns 400."""
        response = test_client.post("/login", json={
            "username": "",
            "password": ""
        })
        
        assert response.status_code == 400
    
    def test_login_invalid_content_type(self, test_client):
        """Test login with unsupported content type returns 400."""
        response = test_client.post(
            "/login",
            content="username=test&password=test",
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == 400
    
    def test_login_user_not_found(self, test_client, mock_supabase):
        """Test login with non-existent user returns 401."""
        # Setup mock to return no user
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = test_client.post("/login", json={
            "username": "nonexistent",
            "password": "password123"
        })
        
        assert response.status_code == 401
        assert "Invalid Credentials" in response.json()["detail"]
    
    def test_login_success_sha256(self, test_client, mock_supabase, sample_user):
        """Test successful login with SHA256 password."""
        # Setup mock to return user with SHA256 hash
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_user]
        
        response = test_client.post("/login", json={
            "username": "testuser",
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tenant_id"] == sample_user["tenant_id"]
        assert data["client_id"] == sample_user["client_id"]
    
    def test_login_success_bcrypt(self, test_client, mock_supabase, sample_user):
        """Test successful login with bcrypt password."""
        # Generate bcrypt hash
        bcrypt_hash = bcrypt.hashpw("password123".encode(), bcrypt.gensalt(rounds=12)).decode()
        sample_user["password_hash_bcrypt"] = bcrypt_hash
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_user]
        
        response = test_client.post("/login", json={
            "username": "testuser",
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_login_wrong_password(self, test_client, mock_supabase, sample_user):
        """Test login with wrong password returns 401."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_user]
        
        response = test_client.post("/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
    
    def test_login_form_data(self, test_client, mock_supabase, sample_user):
        """Test login with form data instead of JSON."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_user]
        
        response = test_client.post("/login", data={
            "username": "testuser",
            "password": "password123"
        })
        
        assert response.status_code == 200
        assert response.json()["success"] is True
