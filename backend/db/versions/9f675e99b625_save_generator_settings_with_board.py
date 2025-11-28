"""Save generator settings with board

Revision ID: 9f675e99b625
Revises: dceb0fca8c2a
Create Date: 2025-11-28 01:05:12.982653

"""

from typing import Sequence, Union

from alembic import op

from backend.repositories.orm.board_orm import BoardORM

# revision identifiers, used by Alembic.
revision: str = "9f675e99b625"
down_revision: Union[str, Sequence[str], None] = "dceb0fca8c2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("boards")
    BoardORM.__table__.create(op.get_bind())  # type: ignore


def downgrade() -> None:
    op.drop_column("boards", "generation_settings")
