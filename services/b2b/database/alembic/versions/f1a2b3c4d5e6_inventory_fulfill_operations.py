"""inventory_fulfill_operations

Revision ID: f1a2b3c4d5e6
Revises: 9a1b2c3d4e5f
Create Date: 2026-06-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "9a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Upgrade schema."""
	op.create_table(
		"inventory_fulfill_operations",
		sa.Column("order_id", sa.UUID(), nullable=False),
		sa.Column(
			"processed_at",
			sa.DateTime(timezone=True),
			server_default=sa.text("now()"),
			nullable=False,
		),
		sa.PrimaryKeyConstraint("order_id"),
		schema="catalog",
	)


def downgrade() -> None:
	"""Downgrade schema."""
	op.drop_table("inventory_fulfill_operations", schema="catalog")
