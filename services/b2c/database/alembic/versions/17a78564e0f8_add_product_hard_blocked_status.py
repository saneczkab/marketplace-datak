"""add_product_hard_blocked_status

Revision ID: 17a78564e0f8
Revises: 9a7064f8074c
Create Date: 2026-06-04 06:57:47.165598

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "17a78564e0f8"
down_revision: Union[str, Sequence[str], None] = "9a7064f8074c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Upgrade schema."""
	op.execute("""ALTER TYPE public.productstatusenum ADD VALUE 'HARD_BLOCKED'""")


def downgrade() -> None:
	"""Downgrade schema."""
	op.execute("""ALTER TYPE public.productstatusenum DROP ATTRIBUTE 'HARD_BLOCKED'""")
