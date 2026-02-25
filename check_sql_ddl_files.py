"""
Download and check SQL DDL files
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
R2_ENDPOINT = os.getenv("R2_ENDPOINT_URL")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")

client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

project_id = "ec771d1a-4fe4-4499-970d-54e28de4d926"

# Get SQL files
result = client.table("utm_objects") \
    .select("*") \
    .eq("project_id", project_id) \
    .eq("category", "soporte") \
    .execute()

print(f"\n{'='*80}")
print(f"SQL DDL Files (category='soporte')")
print(f"{'='*80}\n")

for asset in result.data:
    print(f"📄 {asset['source_name']}")
    print(f"   Fields: {', '.join(asset.keys())}")
    print(f"   ID: {asset['object_id']}")
    print()

# Download one to check content
if result.data:
    import boto3
    
    s3 = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY
    )
    
    for asset in result.data[:2]:  # First 2 files
        path = asset.get('source_path', '')
        if path:
            try:
                response = s3.get_object(Bucket=R2_BUCKET, Key=path)
                content = response['Body'].read().decode('utf-8', errors='ignore')
                
                print(f"\n{'='*80}")
                print(f"Content of {asset['source_name']}")
                print(f"{'='*80}\n")
                print(content[:3000])  # First 3000 chars
                if len(content) > 3000:
                    print("\n... (truncated)")
            except Exception as e:
                print(f"❌ Error downloading {asset['source_name']}: {e}")
