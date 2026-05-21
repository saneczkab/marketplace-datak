"""add_product_fiels

Revision ID: 83e4a34fab48
Revises: 60b7a0add8e0
Create Date: 2026-05-21 08:43:03.528028

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "83e4a34fab48"
down_revision: Union[str, Sequence[str], None] = "60b7a0add8e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.execute("""ALTER TYPE public.productstatusenum
			   ADD VALUE IF NOT EXISTS 'HARD_BLOCKED';
			   """)
	op.add_column(
		"products",
		sa.Column("deleted", sa.Boolean(), server_default="false"),
		schema="catalog",
	)
	op.add_column(
		"products",
		sa.Column("blocked_reason_id", sa.UUID(), nullable=True),
		schema="catalog",
	)
	op.add_column(
		"products", sa.Column("moderator_comment", sa.String(1000)), schema="catalog"
	)


def downgrade() -> None:
	op.execute("""
        ALTER TYPE public.productstatusenum 
        RENAME VALUE 'HARD_BLOCKED' TO 'DELETED'
    """)
	op.drop_column("products", "moderator_comment")
	op.drop_column("products", "blocked_reason_id")
	op.drop_column("products", "deleted")
