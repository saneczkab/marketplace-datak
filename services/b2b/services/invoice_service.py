from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from crud import invoice as invoice_crud
from crud import sku as sku_crud
from database.models.catalog.inventory import InvoiceStatusEnum
from database.models.catalog.base import ProductStatusEnum
from schemas.invoice import (
	InvoiceCreate,
	InvoiceListResponse,
	InvoiceResponse,
	InvoiceAccept,
)
from exceptions.invoice import (
	InvoiceNotFoundError,
	InvalidInvoiceStatusError,
	EmptyInvoiceError,
	InvoiceOwnershipError,
	SkuNotModeratedError,
	InvalidQuantityError,
	InvoiceError,
)
from exceptions.sku import SkuNotFoundError


async def create_new_invoice(
	db: AsyncSession, invoice_data: InvoiceCreate, seller_id: UUID
) -> InvoiceResponse:
	if not invoice_data.items or len(invoice_data.items) == 0:
		raise EmptyInvoiceError("At least one item is required")

	for item in invoice_data.items:
		if item.quantity <= 0:
			raise InvalidQuantityError("quantity must be > 0")

		sku_and_product = await sku_crud.get_sku_and_product(db, item.sku_id)
		if not sku_and_product:
			raise SkuNotFoundError("SKU not found")

		_, product = sku_and_product

		if product.seller_id != seller_id:
			raise InvoiceOwnershipError(
				"One or more SKUs do not belong to the authenticated seller"
			)

		if product.status != ProductStatusEnum.MODERATED:
			raise SkuNotModeratedError(
				"Invoice can only be created for MODERATED products"
			)

	db_invoice = await invoice_crud.create_invoice(db, invoice_data, seller_id)
	return InvoiceResponse.model_validate(db_invoice)


async def get_invoice(db: AsyncSession, invoice_id: UUID) -> InvoiceResponse:
	invoice = await invoice_crud.get_invoice_by_id(db, invoice_id)
	if not invoice:
		raise InvoiceNotFoundError(f"Invoice {invoice_id} not found")
	return InvoiceResponse.model_validate(invoice)


async def accept_invoice(
	db: AsyncSession, invoice_id: UUID, accept_data: InvoiceAccept, accepted_by: UUID
) -> InvoiceResponse:
	invoice = await invoice_crud.get_invoice_by_id(db, invoice_id)
	if not invoice:
		raise InvoiceNotFoundError(f"Invoice {invoice_id} not found")

	if invoice.status != InvoiceStatusEnum.CREATED:
		raise InvalidInvoiceStatusError(
			f"Cannot accept invoice in status {invoice.status.value}"
		)

	invoice_items_map = {item.id: item for item in invoice.items}

	for accept_item in accept_data.accepted_items:
		db_item = invoice_items_map.get(accept_item.invoice_item_id)
		if not db_item:
			raise InvoiceError(
				f"Item {accept_item.invoice_item_id} does not belong to this invoice"
			)

		if accept_item.accepted_quantity < 0:
			raise InvoiceError("Accepted quantity cannot be negative")

		if accept_item.accepted_quantity > db_item.quantity:
			raise InvoiceError(
				f"Accepted quantity ({accept_item.accepted_quantity}) cannot exceed original invoice quantity ({db_item.quantity})"
			)

	updated_invoice = await invoice_crud.accept_invoice_transaction(
		db, invoice=invoice, accept_data=accept_data, accepted_by=accepted_by
	)

	return InvoiceResponse.model_validate(updated_invoice)


async def get_all_invoices(
	db: AsyncSession,
	seller_id: UUID,
	skip: int,
	limit: int,
	status: InvoiceStatusEnum | None,
) -> InvoiceListResponse:
	total_count, invoices = await invoice_crud.get_all_invoices(
		db, seller_id=seller_id, skip=skip, limit=limit, status=status
	)

	return InvoiceListResponse(
		total_count=total_count,
		items=[InvoiceResponse.model_validate(inv) for inv in invoices],
		limit=limit,
		offset=skip,
	)


async def delete_invoice(db: AsyncSession, invoice_id: UUID) -> None:
	invoice = await invoice_crud.get_invoice_by_id(db, invoice_id)
	if not invoice:
		raise InvoiceNotFoundError(f"Invoice {invoice_id} not found")

	if invoice.status != InvoiceStatusEnum.CREATED:
		raise InvalidInvoiceStatusError(
			f"Cannot delete invoice in status {invoice.status.value}"
		)

	await invoice_crud.delete_invoice(db, invoice)
