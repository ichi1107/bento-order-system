"""
データベーステーブルの再作成スクリプト
"""

from database import engine, Base
from sqlalchemy import text
from models import Store

# Storesテーブルを削除
with engine.begin() as conn:
    conn.execute(text('DROP TABLE IF EXISTS stores CASCADE'))
    print('✓ Stores table dropped')

# テーブルを再作成
Base.metadata.create_all(bind=engine)
print('✓ All tables created')
