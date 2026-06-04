"""postgresql_mvp_hardening

Revision ID: 3f0c2e5a7b91
Revises: eacf4f46c7ce
Create Date: 2026-06-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3f0c2e5a7b91"
down_revision: Union[str, None] = "eacf4f46c7ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "backfill_jobs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("exchange", sa.String(), nullable=False),
        sa.Column("data_type", sa.String(), nullable=False),
        sa.Column("interval", sa.String(), nullable=False),
        sa.Column("start_time", sa.BigInteger(), nullable=False),
        sa.Column("end_time", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(), server_default="pending", nullable=True),
        sa.Column("records_fetched", sa.Integer(), server_default="0", nullable=True),
        sa.Column("records_inserted", sa.Integer(), server_default="0", nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.BigInteger(), nullable=True),
        sa.Column("completed_at", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_jobs_status", "backfill_jobs", ["status", "exchange"])
    op.create_index(
        "idx_jobs_lookup",
        "backfill_jobs",
        ["symbol", "exchange", "data_type", "status"],
    )


def downgrade() -> None:
    op.drop_index("idx_jobs_lookup", table_name="backfill_jobs")
    op.drop_index("idx_jobs_status", table_name="backfill_jobs")
    op.drop_table("backfill_jobs")
