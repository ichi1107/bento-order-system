"""既存のrolesとuser_rolesテーブルを削除"""
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import engine

with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS user_roles CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS roles CASCADE'))
    conn.commit()
    print('✅ Dropped roles and user_roles tables')
