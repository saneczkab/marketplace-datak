"""blocking_reasons

Revision ID: 261215519b86
Revises: 524876555327
Create Date: 2026-06-13 15:19:59.310286

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from reference_data.blocking_reasons import BLOCKING_REASONS

revision: str = "261215519b86"
down_revision: Union[str, Sequence[str], None] = "524876555327"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.create_table(
		"blocking_reasons",
		sa.Column(
			"id",
			sa.UUID(),
			server_default=sa.text("gen_random_uuid()"),
			nullable=False,
		),
		sa.Column("code", sa.String(length=64), nullable=False),
		sa.Column("title", sa.String(length=200), nullable=False),
		sa.Column("description", sa.Text(), nullable=True),
		sa.Column("hard_block", sa.Boolean(), nullable=False),
		sa.Column("is_active", sa.Boolean(), nullable=False),
		sa.PrimaryKeyConstraint("id"),
		sa.UniqueConstraint("code"),
	)
	blocking_reasons_table = sa.table(
		"blocking_reasons",
		sa.column("code", sa.String()),
		sa.column("title", sa.String()),
		sa.column("description", sa.Text()),
		sa.column("hard_block", sa.Boolean()),
		sa.column("is_active", sa.Boolean()),
	)
	op.bulk_insert(blocking_reasons_table, BLOCKING_REASONS)


def downgrade() -> None:
	op.drop_table("blocking_reasons")
