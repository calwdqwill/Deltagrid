"""bigint_market_timestamps

Revision ID: 7c1f2a8d9e34
Revises: 3f0c2e5a7b91
Create Date: 2026-06-05 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c1f2a8d9e34"
down_revision: Union[str, None] = "3f0c2e5a7b91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


BIGINT_COLUMNS = {
    "ohlcv": {"timestamp": False},
    "funding_rates": {"timestamp": False, "next_funding_time": True},
    "open_interest": {"timestamp": False},
    "liquidations": {"timestamp": False},
    "long_short_ratio": {"timestamp": False},
    "basis_premium": {"timestamp": False},
    "provider_sync_runs": {"start_time": True, "end_time": True},
    "data_quality_logs": {"timestamp": True},
    "backfill_jobs": {
        "start_time": False,
        "end_time": False,
        "started_at": True,
        "completed_at": True,
    },
    "backtest_configs": {"start_time": False, "end_time": False},
    "backtest_trades": {"entry_time": False, "exit_time": True},
    "backtest_equity": {"timestamp": False},
}


def upgrade() -> None:
    for table_name, columns in BIGINT_COLUMNS.items():
        with op.batch_alter_table(table_name) as batch_op:
            for column_name, nullable in columns.items():
                batch_op.alter_column(
                    column_name,
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=nullable,
                )


def downgrade() -> None:
    for table_name, columns in BIGINT_COLUMNS.items():
        with op.batch_alter_table(table_name) as batch_op:
            for column_name, nullable in columns.items():
                batch_op.alter_column(
                    column_name,
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=nullable,
                )
