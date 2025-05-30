"""empty message

Revision ID: 71e2c8de4b19
Revises: 81e4579915ed
Create Date: 2025-05-28 01:31:16.940395

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "71e2c8de4b19"
down_revision: Union[str, None] = "81e4579915ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "slackspecialchanneltype",
        sa.Column("type_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "friendly_type_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="fcm",
    )
    op.create_index(
        op.f("ix_fcm_slackspecialchanneltype_type_name"),
        "slackspecialchanneltype",
        ["type_name"],
        unique=True,
        schema="fcm",
    )
    op.create_table(
        "slackspecialchannel",
        sa.Column("reason", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slack_channel_id", sa.Integer(), nullable=False),
        sa.Column("slack_special_channel_type_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["slack_channel_id"],
            ["fcm.slackchannel.id"],
        ),
        sa.ForeignKeyConstraint(
            ["slack_special_channel_type_id"],
            ["fcm.slackspecialchanneltype.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="fcm",
    )
    op.create_index(
        op.f("ix_fcm_slackspecialchannel_slack_channel_id"),
        "slackspecialchannel",
        ["slack_channel_id"],
        unique=False,
        schema="fcm",
    )
    op.create_index(
        op.f("ix_fcm_slackspecialchannel_slack_special_channel_type_id"),
        "slackspecialchannel",
        ["slack_special_channel_type_id"],
        unique=False,
        schema="fcm",
    )
    op.add_column(
        "manmanstatusupdate",
        sa.Column("slack_message_id", sa.Integer(), nullable=True),
        schema="fcm",
    )
    op.create_index(
        "idx_as_of_service",
        "manmanstatusupdate",
        ["as_of", "service_id", "service_type"],
        unique=False,
        schema="fcm",
    )
    op.create_index(
        "idx_service",
        "manmanstatusupdate",
        ["service_id", "service_type"],
        unique=False,
        schema="fcm",
    )
    op.create_index(
        op.f("ix_fcm_manmanstatusupdate_slack_message_id"),
        "manmanstatusupdate",
        ["slack_message_id"],
        unique=False,
        schema="fcm",
    )
    op.create_foreign_key(
        None,
        "manmanstatusupdate",
        "slackmessage",
        ["slack_message_id"],
        ["id"],
        source_schema="fcm",
        referent_schema="fcm",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "manmanstatusupdate", schema="fcm", type_="foreignkey")
    op.drop_index(
        op.f("ix_fcm_manmanstatusupdate_slack_message_id"),
        table_name="manmanstatusupdate",
        schema="fcm",
    )
    op.drop_index("idx_service", table_name="manmanstatusupdate", schema="fcm")
    op.drop_index("idx_as_of_service", table_name="manmanstatusupdate", schema="fcm")
    op.drop_column("manmanstatusupdate", "slack_message_id", schema="fcm")
    op.drop_index(
        op.f("ix_fcm_slackspecialchannel_slack_special_channel_type_id"),
        table_name="slackspecialchannel",
        schema="fcm",
    )
    op.drop_index(
        op.f("ix_fcm_slackspecialchannel_slack_channel_id"),
        table_name="slackspecialchannel",
        schema="fcm",
    )
    op.drop_table("slackspecialchannel", schema="fcm")
    op.drop_index(
        op.f("ix_fcm_slackspecialchanneltype_type_name"),
        table_name="slackspecialchanneltype",
        schema="fcm",
    )
    op.drop_table("slackspecialchanneltype", schema="fcm")
    # ### end Alembic commands ###
