from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from crud.seller import get_seller_by_email, get_seller_by_id, update_seller
from schemas.seller import SellerResponse, SellerUpdate

router = APIRouter(prefix="/sellers", tags=["sellers"])


@router.get("/{seller_id}", response_model=SellerResponse)
async def get_seller_account(
	seller_id: str, db: AsyncSession = Depends(get_db)
) -> SellerResponse:
	seller = await get_seller_by_id(db, seller_id)
	if seller is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Seller not found",
		)
	return SellerResponse.model_validate(seller)


@router.patch("/{seller_id}", response_model=SellerResponse)
async def update_seller_account(
	seller_id: str,
	update: SellerUpdate,
	request: Request,
	db: AsyncSession = Depends(get_db),
) -> SellerResponse:
	if request.state.user_id != seller_id:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="You can update only your own seller account",
		)

	seller = await get_seller_by_id(db, seller_id)
	if seller is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Seller not found",
		)

	update_data = update.model_dump(exclude_unset=True)
	if email := update_data.get("email"):
		existing_seller = await get_seller_by_email(db, email)
		if existing_seller is not None and existing_seller.id != seller.id:
			raise HTTPException(
				status_code=status.HTTP_409_CONFLICT,
				detail="Seller with this email already exists",
			)

	try:
		seller = await update_seller(db, seller, update_data)
	except IntegrityError as exc:
		await db.rollback()
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail="Seller data conflicts with an existing account",
		) from exc

	return SellerResponse.model_validate(seller)
