import os
import boto3
from dotenv import load_dotenv

def read_log():
    load_dotenv()
    
    r2_endpoint = os.getenv("R2_ENDPOINT_URL")
    r2_access = os.getenv("R2_ACCESS_KEY_ID")
    r2_secret = os.getenv("R2_SECRET_ACCESS_KEY")
    r2_bucket = os.getenv("R2_BUCKET_NAME")
    
    s3 = boto3.client(
        's3',
        endpoint_url=r2_endpoint,
        aws_access_key_id=r2_access,
        aws_secret_access_key=r2_secret,
        region_name="auto"
    )
    
    project_root = "f98edb5e-4165-4c49-9fce-18894e8a818c/test10"
    
    try:
        key = f"{project_root}/migration.log"
        obj = s3.get_object(Bucket=r2_bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')
        print("--- migration.log ---")
        print(content)
    except Exception as e:
        print(f"Error reading log: {e}")

if __name__ == "__main__":
    read_log()
