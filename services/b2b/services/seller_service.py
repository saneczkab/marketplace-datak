from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

import crud.seller as seller_crud
from exceptions.seller import SellerNotFoundError
from schemas.seller import SellerInfoResponse


async def get_seller_info(db: AsyncSession, id: UUID) -> SellerInfoResponse:
	seller = await seller_crud.get_seller_by_id(id, db)
	if seller is None:
		raise SellerNotFoundError()

	return SellerInfoResponse(
		id=id,
		first_name=seller.first_name,
		last_name=seller.last_name,
		middle_name=seller.middle_name,
		company_name=seller.company_name,
	)
