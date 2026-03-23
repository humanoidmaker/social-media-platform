#!/usr/bin/env python3
"""Initialize MinIO buckets for Social Media Platform."""
import os
from minio import Minio

ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "social_media_minio")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "social_media_minio_secret")

BUCKETS = [
    "social_media-media",
    "social_media-avatars",
    "social_media-banners",
    "social_media-stories",
    "social_media-attachments",
]

PUBLIC_POLICY = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": ["*"]},
            "Action": ["s3:GetObject"],
            "Resource": ["arn:aws:s3:::%s/*"]
        }
    ]
}"""


def init_buckets():
    client = Minio(
        ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False,
    )

    for bucket in BUCKETS:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            client.set_bucket_policy(bucket, PUBLIC_POLICY % bucket)
            print(f"Created bucket: {bucket}")
        else:
            print(f"Bucket already exists: {bucket}")

    print("MinIO initialization complete.")


if __name__ == "__main__":
    init_buckets()
