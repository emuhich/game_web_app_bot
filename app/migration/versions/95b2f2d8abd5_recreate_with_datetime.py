"""Recreate with DateTime

Revision ID: 95b2f2d8abd5
Revises: 51ec4699b913
Create Date: 2025-11-27 20:21:41.081007

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95b2f2d8abd5'
down_revision: Union[str, None] = '51ec4699b913'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Для SQLite прямой ALTER COLUMN DROP DEFAULT невозможен.
    # batch_alter_table пересоздает таблицу и переносит данные.
    for table in ['users', 'masters', 'services']:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column('created_at', existing_type=sa.DateTime(), server_default=None, existing_nullable=False)
            batch_op.alter_column('updated_at', existing_type=sa.DateTime(), server_default=None, existing_nullable=False)
    # applications последней, так как имеет внешние ключи на предыдущие таблицы
    with op.batch_alter_table('applications') as batch_op:
        batch_op.alter_column('created_at', existing_type=sa.DateTime(), server_default=None, existing_nullable=False)
        batch_op.alter_column('updated_at', existing_type=sa.DateTime(), server_default=None, existing_nullable=False)


def downgrade() -> None:
    # Возврат к предыдущему состоянию (устанавливаем обратно CURRENT_TIMESTAMP)
    for table in ['users', 'masters', 'services']:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column('created_at', existing_type=sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), existing_nullable=False)
            batch_op.alter_column('updated_at', existing_type=sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), existing_nullable=False)
    with op.batch_alter_table('applications') as batch_op:
        batch_op.alter_column('created_at', existing_type=sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), existing_nullable=False)
        batch_op.alter_column('updated_at', existing_type=sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), existing_nullable=False)
