import asyncio
import uuid

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from fastapi import HTTPException, UploadFile
from starlette import status

from app.core.config import settings


class S3Client:
    """S3 client for AWS/minIO"""

    def __init__(self):
        if settings.S3_ENDPOINT_URL:
            access_key = settings.MINIO_ROOT_USER
            secret_key = settings.MINIO_ROOT_PASSWORD
            region = settings.MINIO_REGION_NAME
            self.bucket_name = settings.MINIO_BUCKET_NAME
        else:
            access_key = settings.AWS_ACCESS_KEY_ID
            secret_key = settings.AWS_SECRET_ACCESS_KEY
            region = settings.AWS_REGION_NAME
            self.bucket_name = settings.AWS_S3_BUCKET_NAME

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            endpoint_url=settings.S3_ENDPOINT_URL,
        )

    def _upload_sync(self, file_data: bytes, file_key: str, content_type: str) -> None:
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=file_key,
            Body=file_data,
            ContentType=content_type,
        )

    async def upload_file(self, file: UploadFile, folder: str, entity_id: str) -> str:
        """Asynchronous uploading. Returns file key."""
        file_extension = file.filename.split(".")[-1]
        unique_id = str(uuid.uuid4())
        file_key = f"{folder}/{entity_id}/{unique_id}.{file_extension}"

        file_data = await file.read()
        try:
            await asyncio.to_thread(self._upload_sync, file_data, file_key, file.content_type)
        except EndpointConnectionError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Storage service is currently unavailable. Please try again later.",
            ) from e
        return file_key

    def _delete_sync(self, file_key: str) -> None:
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)

    async def delete_file(self, file_key: str) -> None:
        """Deleting file from S3 bucket"""
        if file_key:
            try:
                await asyncio.to_thread(self._delete_sync, file_key)
            except EndpointConnectionError:
                pass

    def generate_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        """Dynamic generation of presigned url"""
        if not file_key:
            return ""
        if file_key.startswith("http"):
            return file_key

        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_key},
                ExpiresIn=expires_in,
            )
            if settings.S3_ENDPOINT_URL and "minio:9000" in url:
                url = url.replace("minio:9000", "localhost:9000")
            return url
        except ClientError:
            return ""


s3_client_instance = S3Client()


def get_s3_client() -> S3Client:
    return s3_client_instance
