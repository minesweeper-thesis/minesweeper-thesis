"""Save generator settings with board

Revision ID: 9f675e99b625
Revises: dceb0fca8c2a
Create Date: 2025-11-28 01:05:12.982653

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f675e99b625"
down_revision: Union[str, Sequence[str], None] = "dceb0fca8c2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.delete(sa.table("multiplayer_gameplays")))
    op.execute(sa.delete(sa.table("multiplayer_rounds")))
    op.execute(sa.delete(sa.table("singleplayer_gameplays")))
    op.execute(sa.delete(sa.table("boards")))
    op.add_column(
        "boards",
        sa.Column("generation_settings", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("boards", "generation_settings")
