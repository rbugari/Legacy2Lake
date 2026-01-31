from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class StorageProvider(ABC):
    """Abstract Base Class for Storage Providers (Local, S3/R2)."""

    @abstractmethod
    def ensure_directory(self, path: str) -> str:
        """Ensures a directory (or prefix) exists. Returns the effective path."""
        pass

    @abstractmethod
    def save_file(self, path: str, content: str, is_binary: bool = False) -> str:
        """Saves content to a file. Returns the file path/key."""
        pass

    @abstractmethod
    def read_file(self, path: str, is_binary: bool = False) -> Any:
        """Reads content from a file."""
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """Deletes a specific file."""
        pass
    
    @abstractmethod
    def delete_directory(self, path: str) -> bool:
        """Deletes a directory (prefix) and all contents."""
        pass

    @abstractmethod
    def list_files(self, path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        Lists files in a directory. 
        Returns structure compatible with frontend tree view:
        [{ "name": "foo.txt", "path": "path/foo.txt", "type": "file", "size": 123, "last_modified": 0.0 }]
        """
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """Checks if a file or directory exists."""
        pass

    @abstractmethod
    def resolve_absolute_path(self, path: str) -> str:
        """
        Returns an absolute system path (Local) or a URL/Key (Cloud).
        Used for cases where the app expects a string identifier for the location.
        """
        pass

    def generate_signed_url(self, path: str, expiration: int = 3600) -> Optional[str]:
        """
        Generates a temporary signed URL for direct download.
        Default implementation returns None (unsupported).
        """
        return None
