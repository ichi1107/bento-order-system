"""
初期データ投入スクリプト
"""
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, User, Menu, Order
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
        
        # 1. メニューデータ
        print("  - Inserting menus...")
        menus = [
            Menu(name="から揚げ弁当", price=500, description="ジューシーなから揚げがたっぷり。", image_url="https://via.placeholder.com/300x200?text=Karaage"),
            Menu(name="焼き肉弁当", price=700, description="特製タレの焼き肉が自慢。", image_url="https://via.placeholder.com/300x200?text=Yakiniku"),
            Menu(name="幕の内弁当", price=600, description="バランスの良い和食弁当。", image_url="https://via.placeholder.com/300x200?text=Makunouchi"),
            Menu(name="サーモン弁当", price=800, description="新鮮なサーモンを使用。", image_url="https://via.placeholder.com/300x200?text=Salmon"),
            Menu(name="ベジタリアン弁当", price=550, description="野菜たっぷりヘルシー弁当。", image_url="https://via.placeholder.com/300x200?text=Vegetarian"),
            Menu(name="特上寿司弁当", price=1200, description="厳選ネタの特上寿司。", image_url="https://via.placeholder.com/300x200?text=Sushi")
        ]
        db.add_all(menus)
        db.commit()
        print(f"    ✓ {len(menus)} menus inserted")
        
        # 2. ユーザーデータ
        print("  - Inserting store staff...")
        store_users = [
            User(username="admin", email="admin@bento.com", hashed_password=get_password_hash("admin@123"), role="store", full_name="管理者"),
            User(username="store1", email="store1@bento.com", hashed_password=get_password_hash("password123"), role="store", full_name="佐藤花子"),
            User(username="store2", email="store2@bento.com", hashed_password=get_password_hash("password123"), role="store", full_name="鈴木一郎")
        ]
        db.add_all(store_users)
        db.commit()
        print(f"    ✓ {len(store_users)} store staff inserted")
        
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
        
        # 3. 販売データ
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
                user_id=order_data["user"].id, menu_id=order_data["menu"].id, quantity=order_data["quantity"],
                total_price=total_price, status=order_data["status"], delivery_time=delivery_time_obj,
                notes=order_data["notes"], ordered_at=ordered_at
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