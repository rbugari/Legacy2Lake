import os
import boto3
import json
from dotenv import load_dotenv

def read_artifacts():
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
    
    # Project test10
    project_root = "f98edb5e-4165-4c49-9fce-18894e8a818c/test10"
    
    # 1. Read orchestration_plan.json
    try:
        key = f"{project_root}/drafting/orchestration_plan.json"
        obj = s3.get_object(Bucket=r2_bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')
        print("--- orchestration_plan.json ---")
        print(content)
    except Exception as e:
        print(f"Error reading orchestration plan: {e}")

    # 2. Read schema_reference.json
    try:
        key = f"{project_root}/drafting/schema_reference.json"
        obj = s3.get_object(Bucket=r2_bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')
        print("\n--- schema_reference.json ---")
        # Just first few lines
        print("\n".join(content.splitlines()[:10]))
    except Exception as e:
        print(f"Error reading schema reference: {e}")

    # 3. Read Refinement Metadata & Logs
    try:
        print("\n--- REFINEMENT STAGE ---")
        ref_keys = [
            f"{project_root}/refinement/profile_metadata.json",
            f"{project_root}/refinement/refinement.log",
            f"{project_root}/refinement/workflows.yaml",
            f"{project_root}/refinement/README_DEVOPS.md"
        ]
        for key in ref_keys:
            try:
                obj = s3.get_object(Bucket=r2_bucket, Key=key)
                content = obj['Body'].read().decode('utf-8')
                print(f"\n>> Artifact: {key.split('/')[-1]}")
                print("\n".join(content.splitlines()[:15])) # Show preview
            except:
                print(f">> Artifact: {key.split('/')[-1]} (Not found or error)")

        # List Medallion folders
        print("\n--- Medallion Layers (First few keys) ---")
        paginator = s3.get_paginator('list_objects_v2')
        for prefix in ["bronze", "silver", "gold"]:
            full_prefix = f"{project_root}/refinement/{prefix}/"
            result = s3.list_objects_v2(Bucket=r2_bucket, Prefix=full_prefix)
            if 'Contents' in result:
                for obj in result['Contents'][:5]:
                    print(f"[{prefix.upper()}] {obj['Key'].split('/')[-1]}")
    except Exception as e:
        print(f"Error listing refinement artifacts: {e}")

if __name__ == "__main__":
    read_artifacts()
