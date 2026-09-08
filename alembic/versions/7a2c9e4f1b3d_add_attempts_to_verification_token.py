"""add attempts to verification_token

Revision ID: 7a2c9e4f1b3d
Revises: 6fcf84e7326f
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a2c9e4f1b3d'
down_revision: Union[str, Sequence[str], None] = '6fcf84e7326f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'verification_token',
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('verification_token', 'attempts')
