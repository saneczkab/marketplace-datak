"""add_deleted_product_status

Revision ID: 52a3dd662571
Revises: bbab6851ac09
Create Date: 2026-06-07 10:20:16.839656

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "52a3dd662571"
down_revision: Union[str, Sequence[str], None] = "29f73a29d3a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.execute("ALTER TYPE public.productstatusenum ADD VALUE IF NOT EXISTS 'DELETED';")


def downgrade() -> None:
	# PostgreSQL does not support removing enum values.
	pass
