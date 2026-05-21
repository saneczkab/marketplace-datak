import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile
from core.config import settings


def get_s3_client() -> boto3.client:
	client: boto3.client = boto3.client(
		"s3",
		endpoint_url=settings.S3_ENDPOINT,
		aws_access_key_id=settings.S3_ACCESS_KEY,
		aws_secret_access_key=settings.S3_SECRET_KEY,
		config=Config(signature_version="s3v4"),
	)

	try:
		client.head_bucket(Bucket=settings.S3_BUCKET)
	except ClientError:
		client.create_bucket(Bucket=settings.S3_BUCKET)
	return client


def upload_file(file: UploadFile, bucket_name: str, client: boto3.client) -> None:
	path = file.filename
	client.upload_fileobj(file.file, bucket_name, path)
