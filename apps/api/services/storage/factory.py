import os
from dotenv import load_dotenv

from .storage_provider import StorageProvider
from .local_storage import LocalStorageProvider
from .r2_storage import R2StorageProvider

load_dotenv()

class StorageFactory:
    _instance: StorageProvider = None

    @classmethod
    def get_provider(cls) -> StorageProvider:
        if cls._instance:
            return cls._instance

        provider_type = os.getenv("STORAGE_PROVIDER", "LOCAL").upper()
        
        if provider_type == "R2":
            print("INFO: Initializing R2 Storage Provider...")
            endpoint = os.getenv("R2_ENDPOINT_URL")
            access = os.getenv("R2_ACCESS_KEY_ID")
            secret = os.getenv("R2_SECRET_ACCESS_KEY")
            bucket = os.getenv("R2_BUCKET_NAME")
            
            if not all([endpoint, access, secret, bucket]):
                print("WARNING: R2 Configuration missing. Falling back to LOCAL.")
                provider_type = "LOCAL"
            else:
                cls._instance = R2StorageProvider(
                    endpoint_url=endpoint,
                    access_key=access,
                    secret_key=secret,
                    bucket_name=bucket
                )
                return cls._instance

        if provider_type == "LOCAL":
            print("INFO: Initializing Local Storage Provider...")
            # Default to 'solutions' dir in root (relative to this factory file -> ../../../../solutions)
            # apps/api/services/storage/factory.py -> apps/api/services/storage -> apps/api/services -> apps/api -> apps -> root -> solutions
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "solutions"))
            cls._instance = LocalStorageProvider(base_dir=base_path)
            return cls._instance
            
        return cls._instance
