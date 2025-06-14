"""replace chat title by name

Revision ID: db0241027eaa
Revises: 0beed97bfdc5
Create Date: 2025-05-29 17:40:17.666292

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "db0241027eaa"
down_revision: Union[str, None] = "0beed97bfdc5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("chats", sa.Column("name", sa.String(length=256), nullable=False))
    op.drop_column("chats", "title")
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "chats",
        sa.Column("title", sa.VARCHAR(length=256), autoincrement=False, nullable=False),
    )
    op.drop_column("chats", "name")
    # ### end Alembic commands ###
