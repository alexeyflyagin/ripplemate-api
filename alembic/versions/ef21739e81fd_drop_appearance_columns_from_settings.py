"""drop appearance columns from settings

Revision ID: ef21739e81fd
Revises: 0b6798721741
Create Date: 2026-08-26 23:16:44.584461

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef21739e81fd'
down_revision: Union[str, Sequence[str], None] = '0b6798721741'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('ck_settings_font', 'settings', type_='check')
    op.drop_constraint('ck_settings_language', 'settings', type_='check')
    op.drop_constraint('ck_settings_theme', 'settings', type_='check')
    op.drop_column('settings', 'theme')
    op.drop_column('settings', 'font')
    op.drop_column('settings', 'language')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('settings', sa.Column('language', sa.VARCHAR(length=4), server_default=sa.text("'auto'::character varying"), autoincrement=False, nullable=False))
    op.add_column('settings', sa.Column('font', sa.VARCHAR(length=10), server_default=sa.text("'sans-serif'::character varying"), autoincrement=False, nullable=False))
    op.add_column('settings', sa.Column('theme', sa.VARCHAR(length=10), server_default=sa.text("'auto'::character varying"), autoincrement=False, nullable=False))
    op.create_check_constraint('ck_settings_font', 'settings', "font IN ('serif', 'sans-serif')")
    op.create_check_constraint('ck_settings_language', 'settings', "language IN ('ru', 'en', 'auto')")
    op.create_check_constraint('ck_settings_theme', 'settings', "theme IN ('dark', 'light', 'auto')")
