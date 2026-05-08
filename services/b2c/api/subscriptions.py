import uuid
from typing import Annotated

import fastapi
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from core import db
from schemas.subscription import SubscribeRequest, SubscriptionResponse
from services import subscription_service

router = fastapi.APIRouter(prefix="/api/v1/favorites", tags=["Подписка"])

security = HTTPBearer()


@router.post(
	"/{product_id}/subscribe", response_model=SubscriptionResponse, status_code=201
)
async def subscribe_to_product(
	product_id: uuid.UUID,
	request: SubscribeRequest,
	db_session: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	creds: Annotated[HTTPAuthorizationCredentials, fastapi.Depends(security)],
) -> SubscriptionResponse:
	"""Подписка на уведомления о товаре"""

	user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")

	try:
		return await subscription_service.subscribe_to_product(
			db_session, user_id, product_id, request
		)
	except ValueError as e:
		error_msg = str(e)
		status_code = 400
		if "PRODUCT_NOT_FOUND" in error_msg:
			status_code = 404
		if "SUBSCRIPTION_ALREADY_EXISTS" in error_msg:
			status_code = 409

		raise fastapi.HTTPException(
			status_code=status_code,
			detail={"code": error_msg.split(":")[0], "message": error_msg},
		)
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


@router.delete("/{product_id}/subscribe", status_code=204)
async def unsubscribe(
	product_id: uuid.UUID,
	db_session: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	token: Annotated[HTTPAuthorizationCredentials, fastapi.Depends(security)],
):
	"""
	Отписка от уведомлений о товаре.
	Требует авторизации (Bearer token).
	"""

	user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")

	try:
		await subscription_service.unsubscribe_from_product(
			db_session, user_id, product_id
		)
		return fastapi.Response(status_code=204)
	except ValueError as e:
		raise fastapi.HTTPException(
			status_code=404,
			detail={"code": "SUBSCRIPTION_NOT_FOUND", "message": str(e)},
		)
	except Exception as e:
		raise fastapi.HTTPException(
			status_code=500, detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)}
		)
