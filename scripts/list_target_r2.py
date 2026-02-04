import os
import boto3
from dotenv import load_dotenv

def list_target():
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
    
    # DEMO3 Tenant and project test10
    prefix = "f98edb5e-4165-4c49-9fce-18894e8a818c/test10/"
    
    print(f"Listing for prefix: {prefix}")
    response = s3.list_objects_v2(Bucket=r2_bucket, Prefix=prefix)
    
    if 'Contents' in response:
        for obj in response['Contents']:
            key = obj['Key']
            print(f"KEY: {key}")
    else:
        print("No objects found.")

if __name__ == "__main__":
    list_target()
