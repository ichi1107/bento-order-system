"""データベースの状態を確認"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from database import engine, SessionLocal
from models import Role, UserRole, User

# テーブル一覧
inspector = inspect(engine)
tables = inspector.get_table_names()
print('📊 Tables:', ', '.join(tables))

# Alembicバージョン
with engine.connect() as conn:
    result = conn.execute(text('SELECT version_num FROM alembic_version'))
    version = result.fetchone()[0]
    print(f'\n🔖 Alembic version: {version}')

# 役割データ
db = SessionLocal()
print('\n👥 Roles:')
roles = db.query(Role).all()
for r in roles:
    print(f'  {r.id}: {r.name} - {r.description}')

# ユーザー役割割り当て
print('\n🔐 User Role Assignments:')
user_roles = db.query(UserRole).join(User).join(Role).all()
for ur in user_roles:
    print(f'  {ur.user.username} ({ur.user.email}) → {ur.role.name}')

db.close()
