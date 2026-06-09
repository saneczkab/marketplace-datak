from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from crud import invoice as invoice_crud
from crud import sku as sku_crud
from database.models.catalog.inventory import Invoice, InvoiceStatusEnum
from database.models.catalog.base import ProductStatusEnum
from schemas.invoice import InvoiceCreate
from exceptions.invoice import (
	InvoiceNotFoundError,
	InvalidInvoiceStatusError,
	EmptyInvoiceError,
	InvoiceOwnershipError,
	SkuNotModeratedError,
	InvalidQuantityError,
)
from exceptions.sku import SkuNotFoundError


async def create_new_invoice(
	db: AsyncSession, invoice_data: InvoiceCreate, seller_id: UUID
) -> Invoice:
	if not invoice_data.items or len(invoice_data.items) == 0:
		raise EmptyInvoiceError("At least one item is required")

	validated_items = []
	for item in invoice_data.items:
		if item.quantity <= 0:
			raise InvalidQuantityError("quantity must be > 0")

		sku_and_product = await sku_crud.get_sku_and_product(db, item.sku_id)
		if not sku_and_product:
			raise SkuNotFoundError("SKU not found")

		sku, product = sku_and_product

		if product.seller_id != seller_id:
			raise InvoiceOwnershipError(
				"One or more SKUs do not belong to the authenticated seller"
			)

		if product.status != ProductStatusEnum.MODERATED:
			raise SkuNotModeratedError(
				"Invoice can only be created for MODERATED products"
			)

		validated_items.append((sku, product))

	return await invoice_crud.create_invoice(db, invoice_data, seller_id)


async def get_invoice(db: AsyncSession, invoice_id: UUID) -> Invoice | None:
	invoice = await invoice_crud.get_invoice_by_id(db, invoice_id)
	if not invoice:
		raise InvoiceNotFoundError()
	return invoice


async def accept_invoice(db: AsyncSession, invoice_id: UUID) -> Invoice:
	invoice = await invoice_crud.get_invoice_by_id(db, invoice_id)
	if not invoice:
		raise InvoiceNotFoundError(str(invoice_id))

	if invoice.status != InvoiceStatusEnum.CREATED:
		raise InvalidInvoiceStatusError(invoice.status, "accept")

	for item in invoice.items:
		sku = await sku_crud.get_sku_by_id(db, item.sku_id)
		if sku:
			sku.active_quantity += item.quantity

	return await invoice_crud.update_invoice_to_accepted(db, invoice)


async def get_all_invoices(
	db: AsyncSession,
	seller_id: UUID,
	skip: int = 0,
	limit: int = 10,
	status: InvoiceStatusEnum | None = None,
) -> tuple[int, list[Invoice]]:
	return await invoice_crud.get_all_invoices(
		db, seller_id=seller_id, skip=skip, limit=limit, status=status
	)


async def delete_invoice(db: AsyncSession, invoice_id: UUID) -> None:
	invoice = await invoice_crud.get_invoice_by_id(db, invoice_id)
	if not invoice:
		raise InvoiceNotFoundError(str(invoice_id))

	if invoice.status != "CREATED":
		raise InvalidInvoiceStatusError(invoice.status, "delete")

	await invoice_crud.delete_invoice(db, invoice)
