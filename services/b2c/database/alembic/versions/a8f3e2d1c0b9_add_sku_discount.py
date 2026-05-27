"""add_sku_discount

Revision ID: a8f3e2d1c0b9
Revises: cd188a7c0cf3
Create Date: 2026-05-27 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8f3e2d1c0b9"
down_revision: Union[str, Sequence[str], None] = "cd188a7c0cf3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Upgrade schema."""
	op.add_column(
		"skus",
		sa.Column("discount", sa.BigInteger(), server_default="0", nullable=False),
		schema="catalog",
	)


def downgrade() -> None:
	"""Downgrade schema."""
	op.drop_column("skus", "discount", schema="catalog")
