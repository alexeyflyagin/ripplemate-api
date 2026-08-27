"""add public id to account and card

Revision ID: a1b2c3d4e5f6
Revises: d6d6331ab9c3
Create Date: 2026-08-27 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd6d6331ab9c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from nanoid import generate

    op.add_column('account', sa.Column('public_id', sa.String(length=16), nullable=True))
    op.add_column('card', sa.Column('public_id', sa.String(length=16), nullable=True))

    conn = op.get_bind()
    for table in ('account', 'card'):
        rows = conn.execute(sa.text(f"SELECT id FROM {table}")).fetchall()
        for (row_id,) in rows:
            conn.execute(
                sa.text(f"UPDATE {table} SET public_id = :pid WHERE id = :id"),
                {"pid": generate(size=16), "id": row_id},
            )

    op.alter_column('account', 'public_id', nullable=False)
    op.alter_column('card', 'public_id', nullable=False)
    op.create_index(op.f('ix_account_public_id'), 'account', ['public_id'], unique=True)
    op.create_index(op.f('ix_card_public_id'), 'card', ['public_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_account_public_id'), table_name='account')
    op.drop_column('account', 'public_id')
    op.drop_index(op.f('ix_card_public_id'), table_name='card')
    op.drop_column('card', 'public_id')
