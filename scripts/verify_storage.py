import os
import sys

# Add apps/api to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from services.storage.factory import StorageFactory
from services.persistence_service import PersistenceService

def test_storage():
    print("--- Testing Storage Configuration ---")
    
    # 1. Check Provider
    provider = StorageFactory.get_provider()
    print(f"Provider: {type(provider).__name__}")
    
    if type(provider).__name__ == "LocalStorageProvider":
        print(f"Base Dir: {provider.base_dir}")
    elif type(provider).__name__ == "R2StorageProvider":
        print(f"Bucket from Env: {provider.bucket_name}")
        try:
             print("Listing buckets...")
             resp = provider.client.list_buckets()
             for b in resp.get('Buckets', []):
                 print(f" - {b['Name']}")
        except Exception as e:
             print(f"List Buckets Failed: {e}")
        
    # 2. Key Check (Safe)
    test_key = "test_connectivity.txt"
    original_bucket = provider.bucket_name
    candidates = [original_bucket, "Legacy2Lake", "legacy-2-lake"]
    
    for b in candidates:
        print(f"\nTrying bucket: {b}")
        provider.bucket_name = b 
        try:
            provider.save_file(test_key, "Hello Cloudflare R2 via UTM!")
            print(f"Write Success with bucket: {b}")
            
            content = provider.read_file(test_key)
            print(f"Read Content: {content}")
            
            provider.delete_file(test_key)
            print("Delete Success")
            break # Success
        except Exception as e:
            print(f"Operation Failed with {b}: {e}")

if __name__ == "__main__":
    test_storage()
