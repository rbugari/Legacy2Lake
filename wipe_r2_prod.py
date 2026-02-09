
import os
import boto3
from dotenv import load_dotenv

def wipe_r2_bucket():
    load_dotenv()
    endpoint = os.getenv("R2_ENDPOINT_URL")
    access = os.getenv("R2_ACCESS_KEY_ID")
    secret = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket = os.getenv("R2_BUCKET_NAME")

    print(f"Wiping R2 Bucket: {bucket}")
    
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access,
            aws_secret_access_key=secret,
            region_name='auto'
        )
        
        # List all objects
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket)
        
        deleted_count = 0
        for page in pages:
            if 'Contents' in page:
                delete_keys = {'Objects': [{'Key': obj['Key']} for obj in page['Contents']]}
                s3.delete_objects(Bucket=bucket, Delete=delete_keys)
                deleted_count += len(page['Contents'])
                print(f"Deleted {len(page['Contents'])} objects...")
        
        print(f"Total objects deleted: {deleted_count}")
        print("R2 Bucket is now empty.")
            
    except Exception as e:
        print(f"Error wiping R2 bucket: {e}")

if __name__ == "__main__":
    wipe_r2_bucket()
