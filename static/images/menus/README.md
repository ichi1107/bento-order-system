# メニュー画像フォルダ

## 概要
このフォルダには弁当メニューの画像を保存します。

## 画像の要件

### ファイル形式
- **推奨**: JPEG (`.jpg`, `.jpeg`)
- **対応**: PNG (`.png`), WebP (`.webp`)

### 画像サイズ
- **推奨サイズ**: 800×600 ピクセル（横長）
- **最小サイズ**: 600×450 ピクセル
- **最大ファイルサイズ**: 500KB以下（表示速度のため）
- **アスペクト比**: 4:3 または 16:9

### ファイル命名規則
- **形式**: `[メニュー名の英語小文字].jpg`
- **例**: 
  - `karaage.jpg` - 唐揚げ弁当
  - `yakiniku.jpg` - 焼肉弁当
  - `salmon.jpg` - サーモン弁当

## 画像の配置方法

1. 画像をこのフォルダ (`static/images/menus/`) に配置
2. データベースの`menus`テーブルの`image_url`カラムを更新

### SQLで画像URLを更新する例

```sql
-- 画像URLを更新
UPDATE menus SET image_url = '/static/images/menus/karaage.jpg' WHERE id = 1;
UPDATE menus SET image_url = '/static/images/menus/yakiniku.jpg' WHERE id = 2;
UPDATE menus SET image_url = '/static/images/menus/makunouchi.jpg' WHERE id = 3;
UPDATE menus SET image_url = '/static/images/menus/salmon.jpg' WHERE id = 4;
UPDATE menus SET image_url = '/static/images/menus/vegetarian.jpg' WHERE id = 5;
UPDATE menus SET image_url = '/static/images/menus/sushi.jpg' WHERE id = 6;
```

### Pythonスクリプトで更新する例

既に `scripts/update_menu_images.py` が用意されています。

```python
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
```

### Dockerコンテナで実行する方法

画像ファイルを配置した後、以下のコマンドでデータベースを更新します：

```bash
# Dockerコンテナ内で直接実行（推奨）
docker-compose exec web python scripts/update_menu_images.py

# または、コンテナ内に入ってから実行
docker-compose exec web bash
python scripts/update_menu_images.py
exit
```

実行結果の例：
```
✅ メニュー画像URLを更新しました
  - から揚げ弁当: /static/images/menus/karaage.jpg
  - 焼き肉弁当: /static/images/menus/yakiniku.jpg
  - 幕の内弁当: /static/images/menus/makunouchi.jpg
  - サーモン弁当: /static/images/menus/salmon.jpg
  - ベジタリアン弁当: /static/images/menus/vegetarian.jpg
  - 特上寿司弁当: /static/images/menus/sushi.jpg
```

## 画像の最適化

### ImageMagickを使用した一括リサイズ（オプション）

```bash
# すべての画像を800x600にリサイズ
mogrify -resize 800x600 -quality 85 *.jpg

# または個別に
convert original.jpg -resize 800x600 -quality 85 karaage.jpg
```

### オンラインツール
- [TinyPNG](https://tinypng.com/) - 画像圧縮
- [Squoosh](https://squoosh.app/) - Google製の画像最適化ツール

## 注意事項

- 著作権に注意してください（自分で撮影した写真、または商用利用可能な素材を使用）
- ファイル名は英数字と `-`, `_` のみ使用（日本語不可）
- 画像は必ずこのフォルダに配置（サブフォルダは作成しない）
