"""tasks

Revision ID: ee99d554acba
Revises: faba61bbecf4
Create Date: 2024-11-30 00:47:48.938839

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ee99d554acba"
down_revision: Union[str, None] = "faba61bbecf4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "task",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema="fcm",
    )
    op.create_table(
        "taskinstance",
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("as_of", sa.DateTime(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "UNKNOWN",
                "OK",
                "FAIL",
                "SKIPPED",
                "EXCEPTION",
                name="taskinstancestatus",
            ),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["fcm.task.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="fcm",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("taskinstance", schema="fcm")
    op.drop_table("task", schema="fcm")
    # ### end Alembic commands ###
