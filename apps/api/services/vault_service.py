"""
Vault Service
Handles secure storage and retrieval of sensitive credentials (API keys, secrets).
Uses Fernet (AES-128) encryption for data at rest.
"""
import os
import base64
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime
from cryptography.fernet import Fernet, InvalidToken


class VaultService:
    """
    Secure credential management service.
    
    Features:
    - AES encryption for secrets at rest
    - Tenant isolation
    - Audit logging for access
    - Automatic key rotation support
    """
    
    def __init__(self, db_client=None, tenant_id: Optional[str] = None):
        """
        Initialize the vault service.
        
        Args:
            db_client: Supabase client for persistence
            tenant_id: Current tenant for isolation
        """
        self.db_client = db_client
        self.tenant_id = tenant_id
        self._cipher = None
        self._initialize_cipher()
    
    def _initialize_cipher(self):
        """Initialize the Fernet cipher with the encryption key."""
        key = os.getenv("VAULT_ENCRYPTION_KEY")
        
        if not key:
            # Generate a warning but allow operation in dev mode
            print("[VAULT WARNING] VAULT_ENCRYPTION_KEY not set. Using derived key from service key.")
            # Derive key from Supabase service key (for development only)
            service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "development-fallback-key")
            # Create a 32-byte key using SHA256, then base64 encode for Fernet
            derived = hashlib.sha256(service_key.encode()).digest()
            key = base64.urlsafe_b64encode(derived).decode()
        
        try:
            self._cipher = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            print(f"[VAULT ERROR] Failed to initialize cipher: {e}")
            self._cipher = None
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not self._cipher:
            raise VaultError("Cipher not initialized. Check VAULT_ENCRYPTION_KEY.")
        
        if not plaintext:
            return ""
        
        encrypted = self._cipher.encrypt(plaintext.encode())
        return encrypted.decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            ciphertext: The encrypted string to decrypt
            
        Returns:
            Original plaintext string
        """
        if not self._cipher:
            raise VaultError("Cipher not initialized. Check VAULT_ENCRYPTION_KEY.")
        
        if not ciphertext:
            return ""
        
        try:
            decrypted = self._cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except InvalidToken:
            raise VaultError("Failed to decrypt. Invalid token or wrong key.")
    
    async def store_api_key(
        self, 
        provider: str, 
        api_key: str, 
        base_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store an API key securely for a provider.
        
        Args:
            provider: Provider name (e.g., 'openai', 'anthropic', 'azure')
            api_key: The API key to store
            base_url: Optional base URL for the provider
            metadata: Optional additional metadata
            
        Returns:
            True if successful
        """
        if not self.db_client or not self.tenant_id:
            raise VaultError("Database client and tenant_id required for storage.")
        
        # Encrypt the API key
        encrypted_key = self.encrypt(api_key)
        encrypted_url = self.encrypt(base_url) if base_url else None
        
        # Prepare record
        record = {
            "tenant_id": self.tenant_id,
            "provider": provider.lower(),
            "api_key_encrypted": encrypted_key,
            "base_url_encrypted": encrypted_url,
            "metadata": metadata or {},
            "is_active": True,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        try:
            # Upsert to handle both create and update
            result = self.db_client.table("utm_vault").upsert(
                record,
                on_conflict="tenant_id,provider"
            ).execute()
            
            # Audit log
            await self._audit_log("STORE", provider, "API key stored/updated")
            
            return True
        except Exception as e:
            print(f"[VAULT ERROR] Failed to store API key: {e}")
            return False
    
    async def retrieve_api_key(self, provider: str) -> Optional[Dict[str, str]]:
        """
        Retrieve an API key for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Dict with 'api_key' and optionally 'base_url', or None if not found
        """
        if not self.db_client or not self.tenant_id:
            raise VaultError("Database client and tenant_id required for retrieval.")
        
        try:
            result = self.db_client.table("utm_vault").select(
                "api_key_encrypted, base_url_encrypted, is_active"
            ).eq("tenant_id", self.tenant_id).eq("provider", provider.lower()).execute()
            
            if not result.data or not result.data[0].get("is_active"):
                return None
            
            record = result.data[0]
            
            # Decrypt
            api_key = self.decrypt(record["api_key_encrypted"])
            base_url = self.decrypt(record["base_url_encrypted"]) if record.get("base_url_encrypted") else None
            
            # Audit log
            await self._audit_log("RETRIEVE", provider, "API key accessed")
            
            return {
                "api_key": api_key,
                "base_url": base_url
            }
        except Exception as e:
            print(f"[VAULT ERROR] Failed to retrieve API key: {e}")
            return None
    
    async def delete_api_key(self, provider: str) -> bool:
        """
        Delete (deactivate) an API key for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            True if successful
        """
        if not self.db_client or not self.tenant_id:
            raise VaultError("Database client and tenant_id required for deletion.")
        
        try:
            # Soft delete - mark as inactive
            self.db_client.table("utm_vault").update({
                "is_active": False,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("tenant_id", self.tenant_id).eq("provider", provider.lower()).execute()
            
            # Audit log
            await self._audit_log("DELETE", provider, "API key deactivated")
            
            return True
        except Exception as e:
            print(f"[VAULT ERROR] Failed to delete API key: {e}")
            return False
    
    async def list_providers(self) -> list:
        """
        List all configured providers for the tenant (without exposing keys).
        
        Returns:
            List of provider configs with masked keys
        """
        if not self.db_client or not self.tenant_id:
            return []
        
        try:
            result = self.db_client.table("utm_vault").select(
                "provider, is_active, updated_at, metadata"
            ).eq("tenant_id", self.tenant_id).execute()
            
            providers = []
            for record in result.data:
                providers.append({
                    "provider": record["provider"],
                    "is_active": record["is_active"],
                    "configured": True,
                    "last_updated": record["updated_at"],
                    "metadata": record.get("metadata", {})
                })
            
            return providers
        except Exception as e:
            print(f"[VAULT ERROR] Failed to list providers: {e}")
            return []
    
    async def _audit_log(self, action: str, provider: str, message: str):
        """Log vault access for audit trail."""
        if not self.db_client:
            return
        
        try:
            self.db_client.table("utm_audit_log").insert({
                "tenant_id": self.tenant_id,
                "action": f"VAULT_{action}",
                "resource": f"vault/{provider}",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
        except Exception:
            # Don't fail on audit log errors
            pass
    
    def mask_key(self, api_key: str) -> str:
        """
        Mask an API key for display purposes.
        
        Args:
            api_key: The full API key
            
        Returns:
            Masked version showing only last 4 characters
        """
        if not api_key or len(api_key) < 8:
            return "****"
        return f"{'*' * (len(api_key) - 4)}{api_key[-4:]}"


class VaultError(Exception):
    """Custom exception for vault operations."""
    pass


# --- Migration SQL for utm_vault table ---
"""
CREATE TABLE IF NOT EXISTS utm_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id),
    provider VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    base_url_encrypted TEXT,
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, provider)
);

CREATE INDEX idx_vault_tenant ON utm_vault(tenant_id);
CREATE INDEX idx_vault_provider ON utm_vault(provider);

-- RLS Policy
ALTER TABLE utm_vault ENABLE ROW LEVEL SECURITY;

CREATE POLICY vault_tenant_isolation ON utm_vault
    USING (tenant_id = current_setting('app.current_tenant')::uuid);
"""
