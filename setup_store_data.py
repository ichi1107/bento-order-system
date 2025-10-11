"""
店舗データとユーザー紐付けスクリプト
"""
from database import SessionLocal
from models import Store, User, Role, UserRole
from datetime import time

db = SessionLocal()

try:
    # 店舗を作成
    store = db.query(Store).filter(Store.name == "テスト弁当屋").first()
    if not store:
        store = Store(
            name="テスト弁当屋",
            email="test@bento.com",
            phone="03-1234-5678",
            address="東京都渋谷区テスト1-2-3",
            opening_time=time(9, 0),
            closing_time=time(21, 0),
            description="美味しい弁当を提供する店舗です。",
            is_active=True
        )
        db.add(store)
        db.commit()
        db.refresh(store)
        print(f"✅ 店舗作成: {store.name} (ID: {store.id})")
    else:
        print(f"✅ 既存店舗: {store.name} (ID: {store.id})")
    
    # Rolesを作成
    roles_data = [
        ("owner", "店舗オーナー"),
        ("manager", "店舗マネージャー"),
        ("staff", "店舗スタッフ")
    ]
    
    for role_name, role_desc in roles_data:
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name, description=role_desc)
            db.add(role)
            print(f"✅ Role作成: {role_name}")
    
    db.commit()
    
    # 店舗ユーザーに店舗を割り当て
    store_users = db.query(User).filter(User.role == "store").all()
    
    for user in store_users:
        if not user.store_id:
            user.store_id = store.id
            print(f"✅ ユーザー '{user.username}' に店舗を割り当て")
        
        # ownerロールを割り当て (admin と store1)
        if user.username in ["admin", "store1"]:
            owner_role = db.query(Role).filter(Role.name == "owner").first()
            existing_user_role = db.query(UserRole).filter(
                UserRole.user_id == user.id,
                UserRole.role_id == owner_role.id
            ).first()
            
            if not existing_user_role:
                user_role = UserRole(user_id=user.id, role_id=owner_role.id)
                db.add(user_role)
                print(f"✅ ユーザー '{user.username}' にownerロールを割り当て")
        
        # managerロールを割り当て (store2)
        elif user.username == "store2":
            manager_role = db.query(Role).filter(Role.name == "manager").first()
            existing_user_role = db.query(UserRole).filter(
                UserRole.user_id == user.id,
                UserRole.role_id == manager_role.id
            ).first()
            
            if not existing_user_role:
                user_role = UserRole(user_id=user.id, role_id=manager_role.id)
                db.add(user_role)
                print(f"✅ ユーザー '{user.username}' にmanagerロールを割り当て")
    
    db.commit()
    print("\n✅ すべての設定が完了しました!")

except Exception as e:
    print(f"❌ エラー: {e}")
    db.rollback()
finally:
    db.close()
