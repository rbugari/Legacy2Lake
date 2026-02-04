import os
import sys
import boto3
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

TENANT_ID = "f98edb5e-4165-4c49-9fce-18894e8a818c"
PROJECT_FOLDER = "test9" # Local folder name
DEST_FOLDER = "test9"    # R2 destination name (matching local)

def upload_missing_files():
    print(f"--- Uploading Missing Files for {PROJECT_FOLDER} ---")
    
    endpoint = os.getenv("R2_ENDPOINT_URL")
    access = os.getenv("R2_ACCESS_KEY_ID")
    secret = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket = os.getenv("R2_BUCKET_NAME")
    
    s3 = boto3.client('s3',
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name="auto"
    )
    
    # Source: solutions/{tenant}/{project}
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "solutions", TENANT_ID, PROJECT_FOLDER))
    print(f"Source: {base_dir}")
    
    if not os.path.exists(base_dir):
        print("❌ Source not found!")
        return

    # Walk and Upload
    count = 0
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            local_path = os.path.join(root, file)
            
            # Destination Key: {tenant}/{project}/{file_rel_path}
            # rel_path relative to project folder
            rel = os.path.relpath(local_path, base_dir).replace("\\", "/")
            
            key = f"{TENANT_ID}/{DEST_FOLDER}/{rel}"
            
            print(f"Uploading {key} ...", end="")
            try:
                with open(local_path, 'rb') as f:
                    s3.put_object(Bucket=bucket, Key=key, Body=f)
                print(" OK")
                count += 1
            except Exception as e:
                print(f" FAILED: {e}")
                
    print(f"--- Uploaded {count} files ---")

if __name__ == "__main__":
    upload_missing_files()
