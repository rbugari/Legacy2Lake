import os
import boto3
from dotenv import load_dotenv

def list_all():
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
    
    print(f"Full Listing for bucket: {r2_bucket}")
    response = s3.list_objects_v2(Bucket=r2_bucket)
    
    if 'Contents' in response:
        for obj in response['Contents']:
            print(f" - {obj['Key']}")
    else:
        print("Empty bucket.")

if __name__ == "__main__":
    list_all()
