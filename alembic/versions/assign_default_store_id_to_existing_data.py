"""assign default store id to existing data

Revision ID: assign_store_ids
Revises: 47d59852aca6
Create Date: 2025-10-12 00:00:00.000000

このマイグレーションは、既存のデータにデフォルトの店舗IDを割り当てます。
1. デフォルト店舗「本店」を作成
2. すべての既存 menus, orders, users に店舗IDを設定
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import time as datetime_time


# revision identifiers, used by Alembic.
revision: str = 'assign_store_ids'
down_revision: Union[str, None] = '82c749cdf529'  # initial_migration に変更
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    既存データにデフォルト店舗IDを割り当てるマイグレーション
    """
    
    # 1. stores テーブルの作成
    op.create_table(
        'stores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('opening_time', sa.Time(), nullable=False),
        sa.Column('closing_time', sa.Time(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stores_id'), 'stores', ['id'], unique=False)
    op.create_index(op.f('ix_stores_name'), 'stores', ['name'], unique=False)
    
    # 2. デフォルト店舗「本店」を作成
    stores_table = table('stores',
        column('name', sa.String),
        column('address', sa.String),
        column('phone_number', sa.String),
        column('email', sa.String),
        column('opening_time', sa.Time),
        column('closing_time', sa.Time),
        column('description', sa.Text),
        column('is_active', sa.Boolean)
    )
    
    op.execute(
        stores_table.insert().values(
            name='本店',
            address='東京都渋谷区サンプル1-2-3',
            phone_number='03-1234-5678',
            email='honten@bento.com',
            opening_time=datetime_time(9, 0),
            closing_time=datetime_time(20, 0),
            description='当店の本店です。美味しい弁当を提供しています。',
            is_active=True
        )
    )
    
    # 3. users テーブルに store_id カラムを追加
    op.add_column('users', sa.Column('store_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_users_store_id'), 'users', ['store_id'], unique=False)
    op.create_foreign_key(
        'fk_users_store_id_stores',
        'users', 'stores',
        ['store_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # 4. 既存の store ロールユーザーに店舗IDを設定
    # デフォルト店舗のIDは1（最初に作成したため）
    op.execute(
        """
        UPDATE users 
        SET store_id = 1 
        WHERE role = 'store'
        """
    )
    
    # 5. menus テーブルに store_id カラムを追加
    op.add_column('menus', sa.Column('store_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_menus_store_id'), 'menus', ['store_id'], unique=False)
    
    # 6. 既存のすべてのメニューに店舗IDを設定
    op.execute(
        """
        UPDATE menus 
        SET store_id = 1
        """
    )
    
    # 7. menus.store_id を NOT NULL に変更し、外部キー制約を追加
    op.alter_column('menus', 'store_id', nullable=False)
    op.create_foreign_key(
        'fk_menus_store_id_stores',
        'menus', 'stores',
        ['store_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 8. orders テーブルに store_id カラムを追加
    op.add_column('orders', sa.Column('store_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_orders_store_id'), 'orders', ['store_id'], unique=False)
    
    # 9. 既存のすべての注文に店舗IDを設定
    op.execute(
        """
        UPDATE orders 
        SET store_id = 1
        """
    )
    
    # 10. orders.store_id を NOT NULL に変更し、外部キー制約を追加
    op.alter_column('orders', 'store_id', nullable=False)
    op.create_foreign_key(
        'fk_orders_store_id_stores',
        'orders', 'stores',
        ['store_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """
    マイグレーションのロールバック
    """
    # orders から store_id を削除
    op.drop_constraint('fk_orders_store_id_stores', 'orders', type_='foreignkey')
    op.drop_index(op.f('ix_orders_store_id'), table_name='orders')
    op.drop_column('orders', 'store_id')
    
    # menus から store_id を削除
    op.drop_constraint('fk_menus_store_id_stores', 'menus', type_='foreignkey')
    op.drop_index(op.f('ix_menus_store_id'), table_name='menus')
    op.drop_column('menus', 'store_id')
    
    # users から store_id を削除
    op.drop_constraint('fk_users_store_id_stores', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_store_id'), table_name='users')
    op.drop_column('users', 'store_id')
    
    # stores テーブルを削除
    op.drop_index(op.f('ix_stores_name'), table_name='stores')
    op.drop_index(op.f('ix_stores_id'), table_name='stores')
    op.drop_table('stores')
