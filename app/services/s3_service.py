import os
import uuid
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import UploadFile, HTTPException, status
from app.config import get_settings

settings = get_settings()


class S3Service:
    def __init__(self):
        self.region = settings.AWS_REGION
        self.bucket_name = settings.S3_BUCKET_NAME
        self.folder = settings.S3_FOLDER.strip("/")
        if self.folder:
            self.folder += "/"

        # Create boto3 client with explicit credentials if provided,
        # otherwise boto3 automatically falls back to IAM Role / EC2 Instance Profile / ~/.aws/credentials
        client_kwargs = {
            "region_name": self.region
        }
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

        self.s3_client = boto3.client("s3", **client_kwargs)

    def check_bucket_access(self) -> bool:
        """Verifies connectivity to S3 bucket."""
        if not self.bucket_name:
            return False
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception:
            return False

    def upload_file(self, file: UploadFile) -> dict:
        """
        Uploads a FastAPI UploadFile to the configured S3 bucket.
        Returns metadata: {s3_key, s3_url, file_size, content_type}
        """
        if not self.bucket_name:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="S3_BUCKET_NAME is not configured in environment variables."
            )

        # Generate unique key to prevent name collisions
        file_ext = os.path.splitext(file.filename)[1]
        unique_id = uuid.uuid4().hex
        s3_key = f"{self.folder}{unique_id}{file_ext}"

        try:
            # Read file content and get size
            file.file.seek(0, os.SEEK_END)
            file_size = file.file.tell()
            file.file.seek(0)

            # Upload to S3
            extra_args = {}
            if file.content_type:
                extra_args["ContentType"] = file.content_type

            self.s3_client.upload_fileobj(
                Fileobj=file.file,
                Bucket=self.bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args
            )

            # Construct public URL
            s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"

            return {
                "s3_key": s3_key,
                "s3_url": s3_url,
                "file_size": file_size,
                "content_type": file.content_type or "application/octet-stream"
            }

        except NoCredentialsError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AWS Credentials not found or invalid."
            )
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AWS S3 error: {e.response['Error']['Message']}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to S3: {str(e)}"
            )

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """Generates a presigned download URL valid for `expiration` seconds."""
        if not self.bucket_name:
            raise HTTPException(status_code=500, detail="S3_BUCKET_NAME not set.")
        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate presigned URL: {e.response['Error']['Message']}"
            )

    def delete_file(self, s3_key: str) -> bool:
        """Deletes an object from the S3 bucket."""
        if not self.bucket_name:
            raise HTTPException(status_code=500, detail="S3_BUCKET_NAME not set.")
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete S3 object: {e.response['Error']['Message']}"
            )


# Singleton instance
s3_service = S3Service()
