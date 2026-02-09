
import os
import boto3
from dotenv import load_dotenv

def main():
    load_dotenv()
    endpoint = os.getenv("R2_ENDPOINT_URL")
    access = os.getenv("R2_ACCESS_KEY_ID")
    secret = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket = os.getenv("R2_BUCKET_NAME")

    print(f"Testing R2 Connectivity:")
    print(f"Endpoint: {endpoint}")
    print(f"Bucket: {bucket}")

    try:
        s3 = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access,
            aws_secret_access_key=secret,
            region_name='auto'  # R2 expects 'auto' or similar
        )
        
        # Try to list objects
        response = s3.list_objects_v2(Bucket=bucket, MaxKeys=10)
        print("Successfully connected to R2!")
        if 'Contents' in response:
            print(f"Found {len(response['Contents'])} objects in bucket.")
            for obj in response['Contents']:
                print(f"- {obj['Key']}")
        else:
            print("Bucket is empty.")
            
    except Exception as e:
        print(f"Error connecting to R2: {e}")

if __name__ == "__main__":
    main()
