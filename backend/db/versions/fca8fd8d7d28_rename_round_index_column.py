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
        if conn.dialect.name == "postgresql":
            batch.drop_constraint(
                "multiplayer_gameplays_session_id_round_number_fkey", type_="foreignkey"
            )

    with op.batch_alter_table("multiplayer_rounds") as batch:
        batch.drop_constraint("check_round_number_non_negative", type_="check")
        batch.alter_column("round_number", new_column_name="round_index")
        batch.create_check_constraint(
            "check_round_index_non_negative", "round_index >= 0"
        )

    with op.batch_alter_table("multiplayer_gameplays") as batch:
        batch.add_column(
            sa.Column("flagged_cells", sa.JSON(), nullable=False, server_default="[]")
        )

    with op.batch_alter_table("multiplayer_gameplays") as batch:
        batch.alter_column("round_number", new_column_name="round_index")

    with op.batch_alter_table("multiplayer_gameplays") as batch:
        batch.create_foreign_key(
            "multiplayer_gameplays_session_id_round_index_fkey",
            "multiplayer_rounds",
            ["session_id", "round_index"],
            ["session_id", "round_index"],
        )


def downgrade() -> None:
    # Drop foreign key in multiplayer_gameplays
    with op.batch_alter_table("multiplayer_gameplays") as batch:
        if conn.dialect.name == "postgresql":
            batch.drop_constraint(
                "multiplayer_gameplays_session_id_round_index_fkey", type_="foreignkey"
            )

    with op.batch_alter_table("multiplayer_rounds") as batch:
        batch.drop_constraint("check_round_index_non_negative", type_="check")
        batch.alter_column("round_index", new_column_name="round_number")
        batch.create_check_constraint(
            "check_round_number_non_negative", "round_number >= 0"
        )

    with op.batch_alter_table("multiplayer_gameplays") as batch:
        batch.drop_column("flagged_cells")

    with op.batch_alter_table("multiplayer_gameplays") as batch:
        batch.alter_column("round_index", new_column_name="round_number")

    with op.batch_alter_table("multiplayer_gameplays") as batch:
        batch.create_foreign_key(
            "multiplayer_gameplays_session_id_round_number_fkey",
            "multiplayer_rounds",
            ["session_id", "round_number"],
            ["session_id", "round_number"],
        )
