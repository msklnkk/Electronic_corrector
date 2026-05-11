from minio import Minio
from minio.error import S3Error

client = Minio(
    endpoint="minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

BUCKET_NAME = "documents"


def create_bucket():
    found = client.bucket_exists(BUCKET_NAME)

    if not found:
        client.make_bucket(BUCKET_NAME)


create_bucket()