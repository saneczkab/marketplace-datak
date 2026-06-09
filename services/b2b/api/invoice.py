from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from core.db import get_db
from database.models.catalog.inventory import InvoiceStatusEnum
from schemas.invoice import InvoiceCreate, InvoiceResponse, InvoiceListResponse
from services import invoice_service
from exceptions.invoice import (
	InvoiceError,
	InvoiceNotFoundError,
	InvalidInvoiceStatusError,
	EmptyInvoiceError,
	InvoiceOwnershipError,
	SkuNotModeratedError,
	InvalidQuantityError,
)
from exceptions.sku import SkuNotFoundError


router = APIRouter(prefix="/invoices", tags=["Invoices"])


def get_seller_id_from_request(request: Request) -> UUID:
	seller_id = getattr(request.state, "seller_id", None) or getattr(
		request.state, "user_id", None
	)
	if not seller_id:
		raise HTTPException(
			status_code=401,
			detail={"code": "UNAUTHORIZED", "message": "Missing authentication"},
		)
	return UUID(str(seller_id))


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice_endpoint(
	request: Request,
	invoice_data: InvoiceCreate,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
	try:
		seller_id = get_seller_id_from_request(request)
		return await invoice_service.create_new_invoice(db, invoice_data, seller_id)
	except EmptyInvoiceError as e:
		raise HTTPException(
			status_code=400,
			detail={
				"code": "INVALID_REQUEST",
				"message": "At least one item is required",
			},
		) from e
	except InvalidQuantityError as e:
		raise HTTPException(
			status_code=400,
			detail={"code": "INVALID_REQUEST", "message": "quantity must be > 0"},
		) from e
	except SkuNotFoundError as e:
		raise HTTPException(
			status_code=404, detail={"code": "NOT_FOUND", "message": "SKU not found"}
		) from e
	except InvoiceOwnershipError as e:
		raise HTTPException(
			status_code=403,
			detail={
				"code": "NOT_OWNER",
				"message": "One or more SKUs do not belong to the authenticated seller",
			},
		) from e
	except SkuNotModeratedError as e:
		raise HTTPException(
			status_code=400,
			detail={
				"code": "INVALID_REQUEST",
				"message": "Invoice can only be created for MODERATED products",
			},
		) from e
	except InvoiceError as e:
		raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice_endpoint(
	invoice_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
) -> InvoiceResponse:
	try:
		return await invoice_service.get_invoice(db, invoice_id)
	except InvoiceNotFoundError as e:
		raise HTTPException(status_code=404, detail=str(e)) from e
	except InvoiceError as e:
		raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{invoice_id}/accept", response_model=InvoiceResponse)
async def accept_invoice_endpoint(
	invoice_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
) -> InvoiceResponse:
	try:
		return await invoice_service.accept_invoice(db, invoice_id)
	except InvoiceNotFoundError as e:
		raise HTTPException(status_code=404, detail=str(e)) from e
	except InvalidInvoiceStatusError as e:
		raise HTTPException(status_code=400, detail=str(e)) from e
	except InvoiceError as e:
		raise HTTPException(status_code=400, detail=str(e)) from e


@router.get(
	"",
	response_model=InvoiceListResponse,
)
async def get_all_invoices_endpoint(
	request: Request,
	db: Annotated[AsyncSession, Depends(get_db)],
	limit: Annotated[int, Query()] = 20,
	offset: Annotated[int, Query()] = 0,
	status: Annotated[InvoiceStatusEnum | None, Query()] = None,
) -> InvoiceListResponse:
	seller_id = get_seller_id_from_request(request)

	total, invoices = await invoice_service.get_all_invoices(
		db, seller_id=seller_id, skip=offset, limit=limit, status=status
	)

	return {"total": total, "items": invoices, "limit": limit, "offset": offset}


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice_endpoint(
	invoice_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
	try:
		await invoice_service.delete_invoice(db, invoice_id)
	except InvoiceNotFoundError as e:
		raise HTTPException(status_code=404, detail=str(e)) from e
	except InvalidInvoiceStatusError as e:
		raise HTTPException(status_code=400, detail=str(e)) from e
	except InvoiceError as e:
		raise HTTPException(status_code=400, detail=str(e)) from e
	return None
