from typing import Annotated
from fastapi import APIRouter, HTTPException, UploadFile, Depends
import uuid
from schemas.images import ImageEntityTypeEnum, ImageUploadResponse, ImageUploadRequest
import services.images_service as images_service
from boto3 import client
from core.s3 import get_s3_client

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("")
async def post_image(
	file: UploadFile,
	entity_type: ImageEntityTypeEnum,
	entity_id: uuid.UUID | None,
	ordering: int | None,
	s3_client: Annotated[client, Depends(get_s3_client)],
) -> ImageUploadResponse:
	try:
		await images_service.post_image(
			ImageUploadRequest(file, entity_type, entity_id, ordering), s3_client
		)
	except Exception as e:
		raise HTTPException(status_code=418, detail=f"{e}") from e
