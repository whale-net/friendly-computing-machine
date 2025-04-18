"""empty message

Revision ID: ae220408773c
Revises: a4fe22aef5af
Create Date: 2025-02-14 19:17:04.418663

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ae220408773c"
down_revision: Union[str, None] = "a4fe22aef5af"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "genaitext", "response", existing_type=sa.VARCHAR(), nullable=True, schema="fcm"
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "genaitext",
        "response",
        existing_type=sa.VARCHAR(),
        nullable=False,
        schema="fcm",
    )
    # ### end Alembic commands ###
