"""
E2Eテスト用のデータセットアップスクリプト
店舗情報とテストユーザーのロールを設定します
"""

from datetime import time
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Store, Role, UserRole
from auth import get_password_hash

def setup_test_data():
    """テストデータの作成"""
    db = SessionLocal()
    
    try:
        # 1. 店舗情報の作成（存在しない場合）
        store = db.query(Store).first()
        if not store:
            store = Store(
                name="テスト弁当店",
                email="test@bento-shop.com",
                phone_number="03-1234-5678",
                address="東京都渋谷区テスト1-2-3",
                opening_time=time(9, 0),
                closing_time=time(20, 0),
                description="テスト用の弁当店です",
                is_active=True
            )
            db.add(store)
            db.commit()
            db.refresh(store)
            print(f"✓ Store created: {store.name} (ID: {store.id})")
        else:
            print(f"✓ Store already exists: {store.name} (ID: {store.id})")
        
        # 2. ロールの作成（存在しない場合）
        roles_data = [
            {"name": "owner", "description": "店舗オーナー（全権限）"},
            {"name": "manager", "description": "店舗マネージャー（管理権限）"},
            {"name": "staff", "description": "店舗スタッフ（基本権限）"},
        ]
        
        for role_data in roles_data:
            role = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not role:
                role = Role(**role_data)
                db.add(role)
                db.commit()
                db.refresh(role)
                print(f"✓ Role created: {role.name}")
            else:
                print(f"✓ Role already exists: {role.name}")
        
        # 3. テストユーザーの作成/更新
        test_users = [
            {"username": "store1", "email": "store1@test.com", "password": "password123", "role": "store", "full_name": "テストオーナー", "roles": ["owner"]},
            {"username": "store2", "email": "store2@test.com", "password": "password123", "role": "store", "full_name": "テストマネージャー", "roles": ["manager"]},
            {"username": "admin", "email": "admin@test.com", "password": "admin@123", "role": "store", "full_name": "管理者", "roles": ["owner"]},
        ]
        
        for user_data in test_users:
            # ユーザーの作成または取得
            user = db.query(User).filter(User.username == user_data["username"]).first()
            if not user:
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                    full_name=user_data["full_name"],
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"✓ User created: {user.username}")
            else:
                print(f"✓ User already exists: {user.username}")
            
            # ユーザーロールの割り当て
            for role_name in user_data["roles"]:
                role = db.query(Role).filter(Role.name == role_name).first()
                if role:
                    # 既存のロール割り当てをチェック
                    existing_user_role = db.query(UserRole).filter(
                        UserRole.user_id == user.id,
                        UserRole.role_id == role.id
                    ).first()
                    
                    if not existing_user_role:
                        user_role = UserRole(user_id=user.id, role_id=role.id)
                        db.add(user_role)
                        db.commit()
                        print(f"  ✓ Assigned role '{role_name}' to user '{user.username}'")
                    else:
                        print(f"  ✓ Role '{role_name}' already assigned to user '{user.username}'")
        
        print("\n✅ Test data setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    setup_test_data()
