from typing import BinaryIO, Optional
from boto3 import client
from botocore.exceptions import ClientError
from loguru import logger
from app.config import settings
import os


class StorageService:
    """Service for handling document storage with MinIO/S3."""

    def __init__(self):
        """Initialize MinIO client."""
        self.client = client(
            "s3",
            endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name="us-east-1",
        )
        self.bucket_name = settings.minio_bucket_name
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' exists")
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Error creating bucket: {e}")
                raise

    def upload_file(
        self,
        file_obj: BinaryIO,
        object_name: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload file to MinIO.

        Args:
            file_obj: File object to upload
            object_name: Name to give the object in storage
            content_type: MIME type of the file

        Returns:
            The object name (path) in storage
        """
        try:
            self.client.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_name,
                ExtraArgs={"ContentType": content_type}
            )
            logger.info(f"Uploaded file: {object_name}")
            return object_name
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise

    def download_file(self, object_name: str, local_path: str) -> str:
        """
        Download file from MinIO to local path.

        Args:
            object_name: Name of the object in storage
            local_path: Local path to save the file

        Returns:
            Local file path
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            self.client.download_file(self.bucket_name, object_name, local_path)
            logger.info(f"Downloaded file: {object_name} -> {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise

    def get_file_url(self, object_name: str, expiration: int = 3600) -> str:
        """
        Get a presigned URL for file access.

        Args:
            object_name: Name of the object in storage
            expiration: URL expiration time in seconds

        Returns:
            Presigned URL
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise

    def delete_file(self, object_name: str) -> bool:
        """
        Delete file from MinIO.

        Args:
            object_name: Name of the object to delete

        Returns:
            True if successful
        """
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info(f"Deleted file: {object_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

    def file_exists(self, object_name: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            object_name: Name of the object to check

        Returns:
            True if file exists
        """
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError:
            return False


# Singleton instance
storage_service = StorageService()
