"""add_accepted_quantity_to_invoice_items

Revision ID: 9a1b2c3d4e5f
Revises: 809035676680
Create Date: 2026-06-08 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "809035676680"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Upgrade schema."""
	# Add accepted_quantity column
	op.add_column(
		"invoice_items",
		sa.Column("accepted_quantity", sa.Integer(), nullable=True),
		schema="catalog",
	)

	# Add check constraints for accepted_quantity
	op.create_check_constraint(
		"chk_invoice_accepted_quantity_non_negative",
		"invoice_items",
		"accepted_quantity IS NULL OR accepted_quantity >= 0",
		schema="catalog",
	)

	op.create_check_constraint(
		"chk_invoice_accepted_quantity_not_exceeding",
		"invoice_items",
		"accepted_quantity IS NULL OR accepted_quantity <= quantity",
		schema="catalog",
	)


def downgrade() -> None:
	"""Downgrade schema."""
	# Drop check constraints
	op.drop_constraint(
		"chk_invoice_accepted_quantity_not_exceeding",
		"invoice_items",
		schema="catalog",
		type_="check",
	)

	op.drop_constraint(
		"chk_invoice_accepted_quantity_non_negative",
		"invoice_items",
		schema="catalog",
		type_="check",
	)

	# Drop column
	op.drop_column("invoice_items", "accepted_quantity", schema="catalog")
