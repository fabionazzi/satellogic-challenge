"""Create planner lock table

Revision ID: a3c9e5d17b42
Revises:
Create Date: 2026-11-19 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "a3c9e5d17b42"
down_revision: Union[str, Sequence[str], None] = "d6a587e798b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    planner_lock = op.create_table(
        "planner_lock",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("active_plan_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("id = 1", name="ck_planner_lock_singleton"),
        sa.ForeignKeyConstraint(
            ["active_plan_id"], ["plan.plan_id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.bulk_insert(planner_lock, [{"id": 1, "active_plan_id": None}])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("planner_lock")
