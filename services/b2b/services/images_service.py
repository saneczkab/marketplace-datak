from schemas.images import ImageUploadRequest, ImageUploadResponse
from boto3 import client
from core import s3

async def post_image(
	data: ImageUploadRequest, s3_client: client
) -> ImageUploadResponse:
	await s3.upload_file(data.file, s3_client)
