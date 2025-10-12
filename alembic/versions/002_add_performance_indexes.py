"""add performance indexes

Revision ID: 002_perf_indexes
Revises: 82c749cdf529
Create Date: 2025-10-12

ダッシュボードAPIのパフォーマンス最適化のためのインデックス追加
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_perf_indexes'
down_revision = '82c749cdf529'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ordersテーブルにパフォーマンス最適化のためのインデックスを追加
    
    # 1. ordered_at カラムにインデックス（日付範囲検索の高速化）
    op.create_index(
        'ix_orders_ordered_at',
        'orders',
        ['ordered_at'],
        unique=False
    )
    
    # 2. status カラムにインデックス（ステータス別集計の高速化）
    op.create_index(
        'ix_orders_status',
        'orders',
        ['status'],
        unique=False
    )
    
    # 3. 複合インデックス: store_id + ordered_at（店舗別の日付範囲検索を最適化）
    op.create_index(
        'ix_orders_store_ordered',
        'orders',
        ['store_id', 'ordered_at'],
        unique=False
    )
    
    # 4. 複合インデックス: store_id + status（店舗別のステータス検索を最適化）
    op.create_index(
        'ix_orders_store_status',
        'orders',
        ['store_id', 'status'],
        unique=False
    )
    
    # 5. 複合インデックス: store_id + ordered_at + status（最も頻繁なクエリパターンを最適化）
    op.create_index(
        'ix_orders_store_ordered_status',
        'orders',
        ['store_id', 'ordered_at', 'status'],
        unique=False
    )


def downgrade() -> None:
    # インデックスを削除
    op.drop_index('ix_orders_store_ordered_status', table_name='orders')
    op.drop_index('ix_orders_store_status', table_name='orders')
    op.drop_index('ix_orders_store_ordered', table_name='orders')
    op.drop_index('ix_orders_status', table_name='orders')
    op.drop_index('ix_orders_ordered_at', table_name='orders')
