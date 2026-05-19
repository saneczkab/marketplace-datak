import uuid
from typing import Annotated

import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from core import db
from exceptions.product import ProductNotFoundError
from exceptions.subscription import (
	InvalidSubscriptionTypeError,
	SubscriptionAlreadyExistsError,
	SubscriptionNotFoundError,
)
from schemas.subscription import SubscribeRequest, SubscriptionResponse
from services import subscription_service
from fastapi.security import HTTPBearer

security = HTTPBearer()

router = fastapi.APIRouter(
	prefix="/api/v1/favorites",
	tags=["Подписка"],
	dependencies=[fastapi.Depends(security)],
)


@router.post(
	"/{product_id}/subscribe", response_model=SubscriptionResponse, status_code=201
)
async def subscribe_to_product(
	product_id: uuid.UUID,
	body: SubscribeRequest,
	http_request: fastapi.Request,
	db_session: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
) -> SubscriptionResponse:
	user_id = uuid.UUID(str(getattr(http_request.state, "user_id", None)))
	try:
		return await subscription_service.subscribe_to_product(
			db_session, user_id, product_id, body
		)
	except InvalidSubscriptionTypeError as e:
		raise fastapi.HTTPException(
			status_code=400,
			detail={"code": "INVALID_NOTIFY_ON", "message": str(e)},
		) from e
	except ProductNotFoundError as e:
		raise fastapi.HTTPException(
			status_code=404,
			detail={"code": "PRODUCT_NOT_FOUND", "message": str(e)},
		) from e
	except SubscriptionAlreadyExistsError as e:
		raise fastapi.HTTPException(
			status_code=409,
			detail={"code": "SUBSCRIPTION_ALREADY_EXISTS", "message": str(e)},
		) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


@router.delete("/{product_id}/subscribe", status_code=204)
async def unsubscribe(
	product_id: uuid.UUID,
	http_request: fastapi.Request,
	db_session: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
) -> fastapi.Response:
	user_id = uuid.UUID(str(getattr(http_request.state, "user_id", None)))
	try:
		await subscription_service.unsubscribe_from_product(
			db_session, user_id, product_id
		)
		return fastapi.Response(status_code=204)
	except SubscriptionNotFoundError as e:
		raise fastapi.HTTPException(
			status_code=404,
			detail={"code": "SUBSCRIPTION_NOT_FOUND", "message": str(e)},
		) from e
	except Exception as e:
		raise fastapi.HTTPException(
			status_code=500,
			detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
		) from e
