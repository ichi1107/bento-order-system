"""simplify order status to four states

Revision ID: 003_simplify_status
Revises: 002_perf_indexes
Create Date: 2025-10-13

注文ステータスを4つ(pending, ready, completed, cancelled)に簡素化
- confirmed → pending に移行
- preparing → pending に移行（安全側に倒す）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '003_simplify_status'
down_revision = '002_perf_indexes'  # パフォーマンスインデックスの後に実行
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    ステータス簡素化のアップグレード処理
    
    1. 既存データの移行:
       - confirmed → pending (再確認の機会を提供)
       - preparing → pending (安全側に倒す)
    
    2. 新しいステータス体系:
       - pending: 注文受付（確認・在庫確認・決済処理）
       - ready: 準備完了（弁当完成、顧客通知）
       - completed: 受取完了（顧客が受取済み）
       - cancelled: キャンセル（注文取消）
    """
    # Step 1: 既存データの移行
    # confirmed と preparing を pending に統一
    connection = op.get_bind()
    
    # confirmed → pending
    connection.execute(
        text("""
            UPDATE orders 
            SET status = 'pending' 
            WHERE status = 'confirmed'
        """)
    )
    
    # preparing → pending (安全側に倒す: 再確認の機会を提供)
    connection.execute(
        text("""
            UPDATE orders 
            SET status = 'pending' 
            WHERE status = 'preparing'
        """)
    )
    
    # Step 2: ログ出力（オプション）
    result = connection.execute(
        text("""
            SELECT status, COUNT(*) as count 
            FROM orders 
            GROUP BY status
        """)
    )
    
    print("\n=== 注文ステータス移行完了 ===")
    for row in result:
        print(f"  {row.status}: {row.count}件")
    print("================================\n")


def downgrade() -> None:
    """
    ダウングレード処理
    
    注意: confirmed と preparing の区別が失われているため、
    完全な復元は不可能。すべて confirmed に戻す。
    """
    connection = op.get_bind()
    
    # pending → confirmed (ダウングレード時の推定値)
    # 注: preparing との区別は復元できない
    connection.execute(
        text("""
            UPDATE orders 
            SET status = 'confirmed' 
            WHERE status = 'pending'
        """)
    )
    
    print("\n=== ダウングレード完了 ===")
    print("  注意: confirmed と preparing の区別は失われています")
    print("  すべて confirmed に統一されました")
    print("============================\n")
