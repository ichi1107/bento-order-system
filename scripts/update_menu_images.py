# scripts/update_menu_images.py
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import update
from database import SessionLocal
from models import Menu

def update_menu_images():
    """メニュー画像URLを更新"""
    menu_images = {
        1: '/static/images/menus/karaage.jpg',
        2: '/static/images/menus/yakiniku.jpg',
        3: '/static/images/menus/makunouchi.jpg',
        4: '/static/images/menus/salmon.jpg',
        5: '/static/images/menus/vegetarian.jpg',
        6: '/static/images/menus/sushi.jpg',
    }
    
    db = SessionLocal()
    try:
        for menu_id, image_url in menu_images.items():
            stmt = update(Menu).where(Menu.id == menu_id).values(image_url=image_url)
            db.execute(stmt)
        db.commit()
        print("✅ メニュー画像URLを更新しました")
        
        # 更新結果を確認
        menus = db.query(Menu).all()
        for menu in menus:
            print(f"  - {menu.name}: {menu.image_url}")
    except Exception as e:
        db.rollback()
        print(f"❌ エラーが発生しました: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_menu_images()