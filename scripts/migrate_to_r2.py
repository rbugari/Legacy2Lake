import os
import sys
import boto3
from dotenv import load_dotenv

# Add apps/api to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

load_dotenv()

def migrate_local_to_r2():
    print("--- Migrating Local Solutions to R2 ---")
    
    # 1. R2 Config
    endpoint = os.getenv("R2_ENDPOINT_URL")
    access = os.getenv("R2_ACCESS_KEY_ID")
    secret = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket = os.getenv("R2_BUCKET_NAME")
    
    if not all([endpoint, access, secret, bucket]):
        print("Error: Missing R2 configuration in .env")
        return

    print(f"Target Bucket: {bucket}")
    
    client = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name="auto"
    )

    # 2. Local Source
    # Relative to this script: ../solutions
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "solutions"))
    print(f"Source Directory: {base_dir}")
    
    if not os.path.exists(base_dir):
        print("Source directory not found. Nothing to migrate.")
        return

    # 3. Walk and Upload
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            local_path = os.path.join(root, file)
            
            # Calculate Key
            # We want the key to be relative to 'solutions'.
            # e.g. solutions/project1/file.txt -> project1/file.txt
            rel_path = os.path.relpath(local_path, base_dir).replace("\\", "/")
            
            print(f"Uploading: {rel_path} ...", end="")
            try:
                # Guess content type or just verify binary?
                # For R2StorageProvider we treated string as utf-8, but here we read raw bytes.
                with open(local_path, 'rb') as f:
                    client.put_object(
                        Bucket=bucket,
                        Key=rel_path,
                        Body=f
                    )
                print(" OK")
            except Exception as e:
                print(f" FAILED: {e}")

    print("\n--- Migration Complete ---")

if __name__ == "__main__":
    migrate_local_to_r2()
