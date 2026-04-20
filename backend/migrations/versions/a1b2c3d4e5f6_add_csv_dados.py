"""add csv_dados table

Revision ID: a1b2c3d4e5f6
Revises: e75126a31a9d
Create Date: 2026-04-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "e75126a31a9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "csv_dados",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("id_fonte", sa.Integer(), nullable=False),
        sa.Column("numero_linha", sa.Integer(), nullable=False),
        sa.Column("dados", JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["id_fonte"],
            ["catalogo_fontes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_csv_dados_id", "csv_dados", ["id"], unique=False)
    op.create_index("ix_csv_dados_id_fonte", "csv_dados", ["id_fonte"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_csv_dados_id_fonte", table_name="csv_dados")
    op.drop_index("ix_csv_dados_id", table_name="csv_dados")
    op.drop_table("csv_dados")
