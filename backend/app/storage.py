import io
import json
import uuid
from functools import lru_cache

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import get_settings


@lru_cache
def get_s3_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def ensure_bucket():
    settings = get_settings()
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.s3_bucket)
    except Exception:
        client.create_bucket(Bucket=settings.s3_bucket)
    ensure_bucket_public_read()


def ensure_bucket_public_read() -> None:
    """Публичное чтение объектов (локальный MinIO). API /api/assets — запасной вариант."""
    settings = get_settings()
    client = get_s3_client()
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{settings.s3_bucket}/*"],
            }
        ],
    }
    try:
        client.put_bucket_policy(Bucket=settings.s3_bucket, Policy=json.dumps(policy))
    except ClientError:
        pass


def upload_bytes(data: bytes, key: str, content_type: str) -> str:
    settings = get_settings()
    client = get_s3_client()
    client.put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return key


def upload_fileobj(fileobj: io.BufferedIOBase, key: str, content_type: str) -> str:
    settings = get_settings()
    client = get_s3_client()
    client.upload_fileobj(
        fileobj,
        settings.s3_bucket,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return key


def download_bytes(key: str) -> bytes:
    settings = get_settings()
    client = get_s3_client()
    buf = io.BytesIO()
    client.download_fileobj(settings.s3_bucket, key, buf)
    return buf.getvalue()


def delete_object(key: str) -> None:
    settings = get_settings()
    client = get_s3_client()
    client.delete_object(Bucket=settings.s3_bucket, Key=key)


def public_url(key: str) -> str:
    settings = get_settings()
    base = settings.api_public_url.rstrip("/")
    return f"{base}/api/assets/{key}"


def new_order_prefix(order_id: uuid.UUID) -> str:
    return f"orders/{order_id}"