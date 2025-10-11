"""
初期データ投入スクリプト
"""
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, User, Menu, Order, Store, Role, UserRole
from auth import get_password_hash
from datetime import datetime, timedelta, time

def init_database():
    """データベースとテーブルの初期化"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")

def insert_initial_data():
    """初期データの投入"""
    db = SessionLocal()
    
    try:
        if db.query(User).count() > 0:
            print("Initial data already exists. Skipping...")
            return
        
        print("Inserting initial data...")
        
        # 1. デフォルト店舗データ
        print("  - Inserting default store...")
        default_store = Store(
            name="本店 - 弁当屋さん",
            address="東京都渋谷区1-2-3",
            phone_number="03-1234-5678",
            email="honten@bento.com",
            opening_time=time(9, 0),
            closing_time=time(20, 0),
            description="美味しい弁当をお届けする本店です。",
            image_url="https://via.placeholder.com/600x400?text=Main+Store",
            is_active=True
        )
        db.add(default_store)
        db.commit()
        db.refresh(default_store)
        print(f"    ✓ Default store inserted (ID: {default_store.id})")
        
        # 2. 役割データ（店舗スタッフ用）
        print("  - Inserting roles...")
        roles_data = [
            Role(name="owner", description="店舗オーナー - 全ての権限を持つ"),
            Role(name="manager", description="店舗マネージャー - 注文管理、レポート閲覧が可能"),
            Role(name="staff", description="店舗スタッフ - 注文管理のみ可能")
        ]
        db.add_all(roles_data)
        db.commit()
        print(f"    ✓ {len(roles_data)} roles inserted")
        
        # roleを取得（後で使用）
        owner_role = db.query(Role).filter(Role.name == "owner").first()
        manager_role = db.query(Role).filter(Role.name == "manager").first()
        staff_role = db.query(Role).filter(Role.name == "staff").first()
        
        # 3. メニューデータ
        print("  - Inserting menus...")
        menus = [
            Menu(name="から揚げ弁当", price=500, description="ジューシーなから揚げがたっぷり。", image_url="https://via.placeholder.com/300x200?text=Karaage", store_id=default_store.id),
            Menu(name="焼き肉弁当", price=700, description="特製タレの焼き肉が自慢。", image_url="https://via.placeholder.com/300x200?text=Yakiniku", store_id=default_store.id),
            Menu(name="幕の内弁当", price=600, description="バランスの良い和食弁当。", image_url="https://via.placeholder.com/300x200?text=Makunouchi", store_id=default_store.id),
            Menu(name="サーモン弁当", price=800, description="新鮮なサーモンを使用。", image_url="https://via.placeholder.com/300x200?text=Salmon", store_id=default_store.id),
            Menu(name="ベジタリアン弁当", price=550, description="野菜たっぷりヘルシー弁当。", image_url="https://via.placeholder.com/300x200?text=Vegetarian", store_id=default_store.id),
            Menu(name="特上寿司弁当", price=1200, description="厳選ネタの特上寿司。", image_url="https://via.placeholder.com/300x200?text=Sushi", store_id=default_store.id)
        ]
        db.add_all(menus)
        db.commit()
        print(f"    ✓ {len(menus)} menus inserted")
        
        # 4. ユーザーデータ
        print("  - Inserting store staff...")
        store_users = [
            User(username="admin", email="admin@bento.com", hashed_password=get_password_hash("admin@123"), role="store", full_name="管理者", store_id=default_store.id),
            User(username="store1", email="store1@bento.com", hashed_password=get_password_hash("password123"), role="store", full_name="佐藤花子", store_id=default_store.id),
            User(username="store2", email="store2@bento.com", hashed_password=get_password_hash("password123"), role="store", full_name="鈴木一郎", store_id=default_store.id)
        ]
        db.add_all(store_users)
        db.commit()
        print(f"    ✓ {len(store_users)} store staff inserted")
        
        # 店舗ユーザーに役割を割り当て
        print("  - Assigning roles to store staff...")
        admin_user = db.query(User).filter(User.username == "admin").first()
        store1_user = db.query(User).filter(User.username == "store1").first()
        store2_user = db.query(User).filter(User.username == "store2").first()
        
        user_roles = [
            UserRole(user_id=admin_user.id, role_id=owner_role.id),  # admin = owner
            UserRole(user_id=store1_user.id, role_id=manager_role.id),  # store1 = manager
            UserRole(user_id=store2_user.id, role_id=staff_role.id)  # store2 = staff
        ]
        db.add_all(user_roles)
        db.commit()
        print(f"    ✓ {len(user_roles)} role assignments created")
        
        print("  - Inserting customers...")
        customers = [
            User(username="customer1", email="customer1@example.com", hashed_password=get_password_hash("password123"), role="customer", full_name="山田太郎"),
            User(username="customer2", email="customer2@example.com", hashed_password=get_password_hash("password123"), role="customer", full_name="田中美咲"),
            User(username="customer3", email="customer3@example.com", hashed_password=get_password_hash("password123"), role="customer", full_name="伊藤健太"),
            User(username="customer4", email="customer4@example.com", hashed_password=get_password_hash("password123"), role="customer", full_name="高橋さくら"),
            User(username="customer5", email="customer5@example.com", hashed_password=get_password_hash("password123"), role="customer", full_name="渡辺健二")
        ]
        db.add_all(customers)
        db.commit()
        print(f"    ✓ {len(customers)} customers inserted")
        
        # 5. 販売データ
        print("  - Inserting orders...")
        customer_users = db.query(User).filter(User.role == "customer").all()
        menu_items = db.query(Menu).all()
        
        orders_data = [
            {"user": customer_users[0], "menu": menu_items[0], "quantity": 2, "status": "completed", "days_ago": 7, "hour": 10, "time": "12:00:00", "notes": "なし"},
            {"user": customer_users[1], "menu": menu_items[2], "quantity": 1, "status": "completed", "days_ago": 7, "hour": 11, "time": "12:30:00", "notes": "お箸不要"},
            {"user": customer_users[2], "menu": menu_items[1], "quantity": 1, "status": "completed", "days_ago": 7, "hour": 10, "time": "12:00:00", "notes": None},
            {"user": customer_users[0], "menu": menu_items[4], "quantity": 1, "status": "completed", "days_ago": 6, "hour": 10, "time": "12:00:00", "notes": None},
            {"user": customer_users[3], "menu": menu_items[3], "quantity": 2, "status": "completed", "days_ago": 6, "hour": 9, "time": "11:30:00", "notes": "温めてください"},
            {"user": customer_users[4], "menu": menu_items[0], "quantity": 3, "status": "completed", "days_ago": 6, "hour": 10, "time": "12:00:00", "notes": None},
            {"user": customer_users[1], "menu": menu_items[5], "quantity": 1, "status": "completed", "days_ago": 5, "hour": 11, "time": "13:00:00", "notes": "醤油多めで"},
            {"user": customer_users[2], "menu": menu_items[0], "quantity": 2, "status": "completed", "days_ago": 5, "hour": 10, "time": "12:00:00", "notes": None},
            {"user": customer_users[0], "menu": menu_items[1], "quantity": 1, "status": "completed", "days_ago": 4, "hour": 10, "time": "12:30:00", "notes": None},
            {"user": customer_users[3], "menu": menu_items[2], "quantity": 2, "status": "completed", "days_ago": 4, "hour": 10, "time": "12:00:00", "notes": "2つ別々に包装"},
            {"user": customer_users[4], "menu": menu_items[4], "quantity": 1, "status": "completed", "days_ago": 4, "hour": 9, "time": "11:30:00", "notes": None},
            {"user": customer_users[1], "menu": menu_items[0], "quantity": 1, "status": "completed", "days_ago": 3, "hour": 10, "time": "12:00:00", "notes": None},
            {"user": customer_users[2], "menu": menu_items[3], "quantity": 1, "status": "completed", "days_ago": 3, "hour": 10, "time": "12:30:00", "notes": None},
            {"user": customer_users[0], "menu": menu_items[5], "quantity": 1, "status": "completed", "days_ago": 3, "hour": 11, "time": "13:00:00", "notes": "わさび抜き"},
            {"user": customer_users[3], "menu": menu_items[1], "quantity": 2, "status": "completed", "days_ago": 2, "hour": 10, "time": "12:00:00", "notes": None},
            {"user": customer_users[4], "menu": menu_items[2], "quantity": 1, "status": "completed", "days_ago": 2, "hour": 10, "time": "12:00:00", "notes": None},
            {"user": customer_users[0], "menu": menu_items[0], "quantity": 2, "status": "completed", "days_ago": 1, "hour": 10, "time": "12:00:00", "notes": None},
            {"user": customer_users[1], "menu": menu_items[4], "quantity": 1, "status": "ready", "days_ago": 1, "hour": 10, "time": "12:30:00", "notes": None},
            {"user": customer_users[2], "menu": menu_items[1], "quantity": 1, "status": "preparing", "days_ago": 0, "hour": -2, "time": "12:00:00", "notes": None},
            {"user": customer_users[3], "menu": menu_items[3], "quantity": 1, "status": "confirmed", "days_ago": 0, "hour": -1, "time": "13:00:00", "notes": "レモン多めで"},
        ]
        
        orders = []
        for order_data in orders_data:
            if order_data["days_ago"] == 0:
                ordered_at = datetime.now() + timedelta(hours=order_data["hour"])
            else:
                ordered_at = datetime.now() - timedelta(days=order_data["days_ago"]) + timedelta(hours=order_data["hour"])
            total_price = order_data["menu"].price * order_data["quantity"]
            delivery_time_obj = None
            if order_data["time"]:
                hour, minute, second = map(int, order_data["time"].split(":"))
                delivery_time_obj = time(hour, minute, second)
            
            order = Order(
                user_id=order_data["user"].id, 
                menu_id=order_data["menu"].id, 
                store_id=default_store.id,
                quantity=order_data["quantity"],
                total_price=total_price, 
                status=order_data["status"], 
                delivery_time=delivery_time_obj,
                notes=order_data["notes"], 
                ordered_at=ordered_at
            )
            orders.append(order)
        
        db.add_all(orders)
        db.commit()
        print(f"    ✓ {len(orders)} orders inserted")
        
        print("\n✓ All initial data inserted successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error inserting initial data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
    insert_initial_data()
    print("\nDatabase initialization completed!")