from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "fca8fd8d7d28"
down_revision: Union[str, Sequence[str], None] = "b9a86e473fd8"
branch_labels = None
depends_on = None
conn = op.get_bind()


def upgrade() -> None:
    with op.batch_alter_table("multiplayer_gameplays") as batch:
        batch.add_column(sa.Column("round_index", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("flagged_cells", sa.JSON(), nullable=True))

    op.execute(
        """
        UPDATE multiplayer_gameplays 
        SET round_index = round_number, flagged_cells = '[]'
    """
    )

    with op.batch_alter_table("multiplayer_gameplays") as batch:
        if conn.dialect.name == "postgresql":
            batch.drop_constraint(
                "multiplayer_gameplays_session_id_round_number_fkey", type_="foreignkey"
            )

    with op.batch_alter_table("multiplayer_rounds") as batch:
        batch.drop_constraint("check_round_number_non_negative", type_="check")
        batch.drop_column("round_number")
        batch.add_column(sa.Column("round_index", sa.Integer(), nullable=True))
        batch.create_check_constraint(
            "check_round_index_non_negative", "round_index >= 0"
        )

    with op.batch_alter_table("multiplayer_gameplays") as batch:
        batch.drop_column("round_number")

    with op.batch_alter_table("multiplayer_gameplays") as batch:
        batch.alter_column("round_index", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("flagged_cells", existing_type=sa.JSON(), nullable=False)
        batch.create_foreign_key(
            "multiplayer_gameplays_session_id_round_index_fkey",
            "multiplayer_rounds",
            ["session_id", "round_index"],
            ["session_id", "round_index"],
        )


def downgrade() -> None:
    with op.batch_alter_table("multiplayer_gameplays") as batch:
        batch.add_column(sa.Column("round_number", sa.Integer(), nullable=True))

    op.execute(
        """
        UPDATE multiplayer_gameplays 
        SET round_number = round_index
    """
    )

    with op.batch_alter_table("multiplayer_gameplays") as batch:
        if conn.dialect.name == "postgresql":
            batch.drop_constraint(
                "multiplayer_gameplays_session_id_round_index_fkey", type_="foreignkey"
            )

    with op.batch_alter_table("multiplayer_rounds") as batch:
        batch.drop_constraint("check_round_index_non_negative", type_="check")
        batch.drop_column("round_index")
        batch.add_column(sa.Column("round_number", sa.Integer(), nullable=True))
        batch.create_check_constraint(
            "check_round_number_non_negative", "round_number >= 0"
        )

    with op.batch_alter_table("multiplayer_gameplays") as batch:
        batch.drop_column("flagged_cells")
        batch.drop_column("round_index")

    with op.batch_alter_table("multiplayer_gameplays") as batch:
        batch.alter_column("round_number", existing_type=sa.Integer(), nullable=False)
        batch.create_foreign_key(
            "multiplayer_gameplays_session_id_round_number_fkey",
            "multiplayer_rounds",
            ["session_id", "round_number"],
            ["session_id", "round_number"],
        )
