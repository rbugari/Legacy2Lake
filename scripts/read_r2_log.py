
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def read_r2_log():
    s3 = boto3.client(
        's3',
        endpoint_url=os.getenv("R2_ENDPOINT_URL"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name='auto'
    )
    
    bucket = os.getenv("R2_BUCKET_NAME")
    tenant_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    
    # Try both cases
    for proj in ["TEST9", "test9"]:
        key = f"{tenant_id}/{proj}/Triage/triage.log"
        print(f"Checking {key}...")
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            print(f"--- LOG CONTENT FROM {proj} ---")
            print(content)
            print("------------------------------")
        except Exception as e:
            print(f"Could not read {key}: {e}")

if __name__ == "__main__":
    read_r2_log()
