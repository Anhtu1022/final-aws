#!/usr/bin/env python3
"""
Task 3.3 Deliverable: Standalone Test S3 Storage Script.
Verifies bucket connectivity, uploads a temporary test file,
downloads it, and confirms S3 bucket access.
"""
import sys
import os
import uuid

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from app.config import get_settings

def test_s3():
    settings = get_settings()

    print("=" * 60)
    print(" AWS S3 Bucket Connectivity Test (Task 3.1 & 3.3) ")
    print("=" * 60)
    print(f"[*] Target Region  : {settings.AWS_REGION}")
    print(f"[*] S3 Bucket Name : {settings.S3_BUCKET_NAME}")
    print(f"[*] Access Key ID  : {settings.AWS_ACCESS_KEY_ID[:4] + '****' if settings.AWS_ACCESS_KEY_ID else '(using IAM role/default)'}")
    print("-" * 60)

    if not settings.S3_BUCKET_NAME:
        print("[ERROR] S3_BUCKET_NAME is not configured in .env!")
        return 1

    client_kwargs = {"region_name": settings.AWS_REGION}
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

    try:
        s3 = boto3.client("s3", **client_kwargs)

        # 1. Check head_bucket
        print("[*] Step 1: Checking bucket existence...")
        s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        print("    -> Bucket exists and is accessible!")

        # 2. Put object test
        test_key = f"test-diagnostics/ping-{uuid.uuid4().hex[:8]}.txt"
        test_payload = b"Hello from FastAPI AWS S3 integration test!"
        print(f"[*] Step 2: Uploading diagnostic object '{test_key}'...")
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=test_key,
            Body=test_payload,
            ContentType="text/plain"
        )
        print("    -> Upload successful!")

        # 3. Read object test
        print("[*] Step 3: Verifying object retrieval...")
        response = s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=test_key)
        body = response["Body"].read()
        assert body == test_payload
        print("    -> Object verified successfully!")

        # 4. Clean up test object
        print("[*] Step 4: Cleaning up diagnostic object...")
        s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=test_key)
        print("    -> Test object deleted cleanly.")

        print("-" * 60)
        print("[SUCCESS] S3 file upload integration is 100% operational!")
        print("=" * 60)
        return 0

    except NoCredentialsError:
        print("[ERROR] AWS credentials not found! Check AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY.")
        return 1
    except ClientError as e:
        print(f"[ERROR] AWS S3 ClientError: {e.response['Error']['Message']}")
        print(f"Error Code: {e.response['Error']['Code']}")
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(test_s3())
