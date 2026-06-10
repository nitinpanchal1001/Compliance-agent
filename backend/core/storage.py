"""S3 object storage — upload, download, and presigned URLs for raw documents."""

from functools import lru_cache

import boto3
from botocore.config import Config

from core.config import get_settings

settings = get_settings()


@lru_cache
def get_s3_client():
    kwargs: dict = {
        "region_name": settings.s3_region,
        "config": Config(signature_version="s3v4"),
    }
    if settings.s3_access_key:
        kwargs["aws_access_key_id"] = settings.s3_access_key
        kwargs["aws_secret_access_key"] = settings.s3_secret_key
    # endpoint_url lets us point at S3-compatible stores; empty = real AWS
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    return boto3.client("s3", **kwargs)


def upload_bytes(data: bytes, key: str, content_type: str | None = None) -> None:
    extra = {"ContentType": content_type} if content_type else {}
    get_s3_client().put_object(
        Bucket=settings.s3_bucket_name, Key=key, Body=data, **extra
    )


def download_bytes(key: str) -> bytes:
    obj = get_s3_client().get_object(Bucket=settings.s3_bucket_name, Key=key)
    return obj["Body"].read()


def generate_presigned_url(key: str, expires_seconds: int = 3600) -> str:
    return get_s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket_name, "Key": key},
        ExpiresIn=expires_seconds,
    )


def delete_object(key: str) -> None:
    get_s3_client().delete_object(Bucket=settings.s3_bucket_name, Key=key)
