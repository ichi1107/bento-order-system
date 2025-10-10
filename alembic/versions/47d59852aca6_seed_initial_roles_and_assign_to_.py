"""seed initial roles and assign to existing users

Revision ID: 47d59852aca6
Revises: ad04b74f4777
Create Date: 2025-10-10 13:08:28.101481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47d59852aca6'
down_revision: Union[str, None] = 'ad04b74f4777'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 役割データを投入
    connection = op.get_bind()
    
    # 3つの役割を登録
    connection.execute(sa.text("""
        INSERT INTO roles (name, description) VALUES
        ('owner', '店舗オーナー - 全権限'),
        ('manager', 'マネージャー - 店舗管理権限'),
        ('staff', 'スタッフ - 基本的な注文管理')
    """))
    
    # 既存の店舗ユーザーに役割を割り当て
    # admin → owner (role_id=1)
    connection.execute(sa.text("""
        INSERT INTO user_roles (user_id, role_id)
        SELECT id, 1 FROM users WHERE username = 'admin' AND role = 'store'
    """))
    
    # store1 → manager (role_id=2)
    connection.execute(sa.text("""
        INSERT INTO user_roles (user_id, role_id)
        SELECT id, 2 FROM users WHERE username = 'store1' AND role = 'store'
    """))
    
    # store2 → staff (role_id=3)
    connection.execute(sa.text("""
        INSERT INTO user_roles (user_id, role_id)
        SELECT id, 3 FROM users WHERE username = 'store2' AND role = 'store'
    """))


def downgrade() -> None:
    # 割り当てられた役割を削除
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM user_roles"))
    
    # 役割データを削除
    connection.execute(sa.text("DELETE FROM roles"))
