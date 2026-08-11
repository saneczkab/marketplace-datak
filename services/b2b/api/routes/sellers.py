import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from b2b.api.deps.auth import get_current_seller
from b2b.core.security import hash_password
from b2b.db.session import get_db
from b2b.models.seller import Seller
from b2b.schemas.seller import SellerResponse, SellerUpdate

router = APIRouter(prefix="/api/sellers", tags=["sellers"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentSeller = Annotated[Seller, Depends(get_current_seller)]


@router.get("/me", response_model=SellerResponse)
async def get_current_seller_profile(current_seller: CurrentSeller) -> Seller:
	return current_seller


@router.patch("/me", response_model=SellerResponse)
async def update_current_seller_profile(
	payload: SellerUpdate,
	current_seller: CurrentSeller,
	db: DbSession,
) -> Seller:
	if payload.email != current_seller.email:
		existing_seller = await db.scalar(
			select(Seller).where(
				Seller.email == payload.email,
				Seller.id != current_seller.id,
			)
		)
		if existing_seller:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Email is already in use",
			)

	update_data = payload.model_dump(exclude={"password"})
	for field, value in update_data.items():
		setattr(current_seller, field, value)

	if payload.password is not None:
		current_seller.hashed_password = hash_password(payload.password)

	await db.commit()
	await db.refresh(current_seller)
	return current_seller


@router.get("/{seller_id}", response_model=SellerResponse)
async def get_seller(seller_id: uuid.UUID, db: DbSession) -> Seller:
	seller = await db.get(Seller, seller_id)
	if seller is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Seller not found",
		)
	return seller
