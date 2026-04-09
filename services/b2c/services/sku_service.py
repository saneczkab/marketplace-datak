import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from crud import sku as sku_crud
from database.models import Sku
from exceptions.sku import SkuNotFoundError


async def get_sku_by_id(db: AsyncSession, sku_id: uuid.UUID) -> Sku:
	"""

	:param db:
	:param sku_id:
	:return:
	"""
	sku = await sku_crud.get_sku_by_id(db, sku_id)
	if not sku:
		raise SkuNotFoundError

	return sku
