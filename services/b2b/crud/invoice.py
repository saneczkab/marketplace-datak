from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import joinedload
from uuid import UUID
from datetime import datetime
from database.models.catalog.inventory import Invoice, InvoiceItem, InvoiceStatusEnum
from database.models.catalog.variants import Sku
from schemas.invoice import InvoiceCreate, InvoiceAccept


async def create_invoice(
	db: AsyncSession, invoice_data: InvoiceCreate, seller_id: UUID
) -> Invoice:
	"""Creates an invoice and its items in one transaction."""
	db_invoice = Invoice(seller_id=seller_id, status=InvoiceStatusEnum.CREATED)
	db.add(db_invoice)
	await db.flush()

	for item in invoice_data.items:
		db_item = InvoiceItem(
			invoice_id=db_invoice.id,
			sku_id=item.sku_id,
			quantity=item.quantity,
			accepted_quantity=0,
		)
		db.add(db_item)

	await db.commit()

	return await get_invoice_by_id(db, db_invoice.id)


async def get_invoice_by_id(db: AsyncSession, invoice_id: UUID) -> Invoice | None:
	"""Receives a invoice by ID with loading of its items"""
	result = await db.execute(
		select(Invoice)
		.options(joinedload(Invoice.items))
		.filter(Invoice.id == invoice_id)
	)
	return result.unique().scalar_one_or_none()


async def get_all_invoices(
	db: AsyncSession,
	seller_id: UUID,
	skip: int = 0,
	limit: int = 100,
	status: InvoiceStatusEnum | None = None,
) -> tuple[int, list[Invoice]]:
	"""Gets a list of seller's invoices with pagination and status filter."""
	count_query = select(func.count(Invoice.id)).filter(Invoice.seller_id == seller_id)
	select_query = select(Invoice).filter(Invoice.seller_id == seller_id)

	if status:
		count_query = count_query.filter(Invoice.status == status)
		select_query = select_query.filter(Invoice.status == status)

	total_result = await db.execute(count_query)
	total = total_result.scalar_one()

	result = await db.execute(
		select_query.options(joinedload(Invoice.items))
		.offset(skip)
		.limit(limit)
		.order_by(Invoice.created_at.desc())
	)
	invoices = result.unique().scalars().all()

	return total, invoices


async def accept_invoice_transaction(
	db: AsyncSession, invoice: Invoice, accept_data: InvoiceAccept, accepted_by: UUID
) -> Invoice:
	"""Atomically updates quantities on the invoice and increments the active_quantity of the SKU."""

	for accept_item in accept_data.accepted_items:
		for db_item in invoice.items:
			if db_item.id == accept_item.invoice_item_id:
				db_item.accepted_quantity = accept_item.accepted_quantity

				await db.execute(
					update(Sku)
					.where(Sku.id == db_item.sku_id)
					.values(
						active_quantity=Sku.active_quantity
						+ accept_item.accepted_quantity
					)
				)
				break

	invoice.status = InvoiceStatusEnum.ACCEPTED
	invoice.accepted_by = accepted_by
	invoice.accepted_at = datetime.utcnow()
	invoice.updated_at = datetime.utcnow()

	await db.commit()
	await db.refresh(invoice)

	return invoice


async def delete_invoice(db: AsyncSession, db_invoice: Invoice) -> None:
	await db.delete(db_invoice)
	await db.commit()
