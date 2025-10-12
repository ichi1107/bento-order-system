"""メニュー画像URLを実際のファイルパスに更新するスクリプト"""
from database import SessionLocal
from models import Menu

# 画像ファイル名のマッピング
image_mapping = {
    'から揚げ弁当': '/static/images/menus/karaage.jpg',
    '焼き肉弁当': '/static/images/menus/yakiniku.jpg',
    '幕の内弁当': '/static/images/menus/makunouchi.jpg',
    'サーモン弁当': '/static/images/menus/salmon.jpg',
    'ベジタリアン弁当': '/static/images/menus/vegetarian.jpg',
    '特上寿司弁当': '/static/images/menus/sushi.jpg',
}

db = SessionLocal()

print('メニュー画像URLを更新中...')
print('=' * 60)

updated_count = 0
for menu in db.query(Menu).all():
    if menu.name in image_mapping:
        old_url = menu.image_url
        new_url = image_mapping[menu.name]
        
        menu.image_url = new_url
        updated_count += 1
        
        print(f'✓ {menu.name}')
        print(f'  旧: {old_url}')
        print(f'  新: {new_url}')
        print()

db.commit()
print('=' * 60)
print(f'✅ {updated_count}件のメニュー画像URLを更新しました')

# 確認
print('\n更新後のメニュー画像URL:')
print('=' * 60)
for menu in db.query(Menu).all():
    print(f'{menu.name}: {menu.image_url}')

db.close()
