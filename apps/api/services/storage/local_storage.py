import os
import shutil
import stat
from typing import List, Dict, Any, Optional
from .storage_provider import StorageProvider

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_fs_path(self, path: str) -> str:
        """Joins path with base_dir if strictly relative, else normalizes."""
        # Sanitize common S3-style keys just in case (e.g. "prefix/file")
        path = path.replace("/", os.sep)
        
        if os.path.isabs(path):
            # Security check: must be within base_dir
            if not path.startswith(os.path.abspath(self.base_dir)):
                # If it's not in the base dir, we might want to allow temp files?
                # For now, simplistic check.
                pass
            return path
        return os.path.join(self.base_dir, path)

    def ensure_directory(self, path: str) -> str:
        fs_path = self._resolve_fs_path(path)
        os.makedirs(fs_path, exist_ok=True)
        return fs_path

    def save_file(self, path: str, content: Any, is_binary: bool = False) -> str:
        fs_path = self._resolve_fs_path(path)
        # Ensure parent dir exists
        os.makedirs(os.path.dirname(fs_path), exist_ok=True)
        
        mode = "wb" if is_binary else "w"
        encoding = None if is_binary else "utf-8"
        
        with open(fs_path, mode, encoding=encoding) as f:
            f.write(content)
        return fs_path

    def read_file(self, path: str, is_binary: bool = False) -> Any:
        fs_path = self._resolve_fs_path(path)
        if not os.path.exists(fs_path):
            return None
            
        mode = "rb" if is_binary else "r"
        encoding = None if is_binary else "utf-8"
        
        with open(fs_path, mode, encoding=encoding) as f:
            return f.read()

    def delete_file(self, path: str) -> bool:
        fs_path = self._resolve_fs_path(path)
        if os.path.exists(fs_path) and os.path.isfile(fs_path):
            os.remove(fs_path)
            return True
        return False

    def robust_rmtree(self, path: str):
        """Robustly deletes a directory tree."""
        def on_error(func, path, exc_info):
            if not os.access(path, os.W_OK):
                os.chmod(path, stat.S_IWUSR)
                func(path)
            else:
                raise

        if os.path.exists(path):
            shutil.rmtree(path, onerror=on_error)

    def delete_directory(self, path: str) -> bool:
        fs_path = self._resolve_fs_path(path)
        if os.path.exists(fs_path):
            self.robust_rmtree(fs_path)
            return True
        return False

    def list_files(self, path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        # This mirrors the logic in PersistenceService.get_project_files
        fs_path = self._resolve_fs_path(path)
        if not os.path.exists(fs_path):
            return []

        def _scan_dir(current_path: str, relative_root: str) -> List[Dict[str, Any]]:
            children = []
            try:
                with os.scandir(current_path) as it:
                    for entry in it:
                        if entry.name.startswith('.') or entry.name == "__pycache__":
                            continue
                        
                        # Calculate relative path similar to how S3 listing works
                        rel_path = os.path.relpath(entry.path, self.base_dir).replace("\\", "/")
                        
                        node = {
                            "name": entry.name,
                            "path": rel_path, 
                            "type": "folder" if entry.is_dir() else "file",
                            "last_modified": entry.stat().st_mtime,
                            "size": entry.stat().st_size if entry.is_file() else 0
                        }
                        
                        if entry.is_dir() and recursive:
                            node["children"] = _scan_dir(entry.path, relative_root)
                            node["children"].sort(key=lambda x: (x["type"] != "folder", x["name"]))
                            
                        children.append(node)
            except Exception as e:
                print(f"Error scanning {current_path}: {e}")
                
            children.sort(key=lambda x: (x["type"] != "folder", x["name"]))
            return children

        return _scan_dir(fs_path, fs_path)

    def exists(self, path: str) -> bool:
        return os.path.exists(self._resolve_fs_path(path))

    def resolve_absolute_path(self, path: str) -> str:
        return self._resolve_fs_path(path)

    def generate_signed_url(self, path: str, expiration: int = 3600) -> Optional[str]:
        """For local storage, we just return the absolute file path as a pseudo-URL."""
        abs_path = self.resolve_absolute_path(path)
        if os.path.exists(abs_path):
            return f"file:///{abs_path.replace(os.sep, '/')}"
        return None
