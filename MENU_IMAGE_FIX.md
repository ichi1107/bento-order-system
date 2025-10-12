# メニュー画像表示問題 - 解決レポート

## 📅 対応日
2025年10月12日

## 🐛 問題の詳細

### 症状
お客様がメニュー画面を開いても、お弁当の画像が表示されない

### 環境
- 画像ファイルの保存場所: `static/images/menus/`
- 画像ファイル一覧:
  - karaage.jpg (108KB)
  - yakiniku.jpg (136KB)
  - makunouchi.jpg (100KB)
  - salmon.jpg (98KB)
  - vegetarian.jpg (136KB)
  - sushi.jpg (136KB)

## 🔍 原因

画像ファイルは正しく配置されていましたが、**データベースのメニューテーブルに登録されている`image_url`がプレースホルダーURLのままでした**。

### データベースの状態（修正前）
```
から揚げ弁当: https://via.placeholder.com/300x200?text=Karaage
焼き肉弁当: https://via.placeholder.com/300x200?text=Yakiniku
幕の内弁当: https://via.placeholder.com/300x200?text=Makunouchi
...
```

これらのURLは外部サービス（placeholder.com）を指しており、実際の画像ファイル（`/static/images/menus/karaage.jpg`など）を参照していませんでした。

## ✅ 実施した対応

### 1. データベースの画像URLを更新

**更新スクリプト作成**: `update_menu_images.py`

```python
image_mapping = {
    'から揚げ弁当': '/static/images/menus/karaage.jpg',
    '焼き肉弁当': '/static/images/menus/yakiniku.jpg',
    '幕の内弁当': '/static/images/menus/makunouchi.jpg',
    'サーモン弁当': '/static/images/menus/salmon.jpg',
    'ベジタリアン弁当': '/static/images/menus/vegetarian.jpg',
    '特上寿司弁当': '/static/images/menus/sushi.jpg',
}
```

### 2. 実行結果

```
✅ 6件のメニュー画像URLを更新しました

更新後のメニュー画像URL:
から揚げ弁当: /static/images/menus/karaage.jpg
焼き肉弁当: /static/images/menus/yakiniku.jpg
幕の内弁当: /static/images/menus/makunouchi.jpg
サーモン弁当: /static/images/menus/salmon.jpg
ベジタリアン弁当: /static/images/menus/vegetarian.jpg
特上寿司弁当: /static/images/menus/sushi.jpg
```

## 🧪 動作確認

### 1. API確認
```
GET /api/customer/menus
→ 全てのメニューで正しい画像パス（/static/images/menus/*.jpg）が返される ✅
```

### 2. 画像ファイルアクセス確認
```
http://localhost:8000/static/images/menus/karaage.jpg → 200 OK ✅
http://localhost:8000/static/images/menus/yakiniku.jpg → 200 OK ✅
http://localhost:8000/static/images/menus/makunouchi.jpg → 200 OK ✅
```

## 🌐 ブラウザでの確認方法

1. **ブラウザのキャッシュをクリア**
   - Chrome/Edge: `Ctrl + Shift + R`（スーパーリロード）
   - Firefox: `Ctrl + Shift + Delete` → キャッシュのみ削除

2. **http://localhost:8000 にアクセス**

3. **顧客アカウントでログイン**
   - ユーザー名: `customer1`
   - パスワード: `password123`

4. **メニュー画面で画像を確認**
   - ✅ から揚げ弁当の写真が表示される
   - ✅ 焼き肉弁当の写真が表示される
   - ✅ 幕の内弁当の写真が表示される
   - ✅ サーモン弁当の写真が表示される
   - ✅ ベジタリアン弁当の写真が表示される
   - ✅ 特上寿司弁当の写真が表示される

## 🛠️ トラブルシューティング

### 画像が表示されない場合

1. **ブラウザの開発者ツールを開く（F12）**
2. **ネットワークタブを確認**
3. **画像URLのリクエストを探す**
   - ステータス: `200 OK` → 正常
   - ステータス: `404 Not Found` → ファイルが見つからない
   - ステータス: `403 Forbidden` → アクセス権限の問題

4. **コンソールタブでエラーを確認**
   - CORSエラー
   - Mixed Content警告（HTTPSページでHTTP画像を読み込もうとしている）

## 📝 今後のメニュー追加時の注意点

新しいメニューを追加する際は、以下の手順で画像を設定してください:

### 1. 画像ファイルを配置
```bash
# 画像を static/images/menus/ に保存
static/images/menus/new_menu.jpg
```

### 2. データベースに登録
```python
new_menu = Menu(
    name="新メニュー",
    price=800,
    description="美味しい新メニュー",
    image_url="/static/images/menus/new_menu.jpg",  # ← 実際のパスを指定
    is_available=True,
    store_id=1
)
```

### 3. 画像の推奨仕様
- **形式**: JPEG, PNG, WebP
- **サイズ**: 300px × 200px 程度（縦横比 3:2）
- **ファイルサイズ**: 100KB以下（ページ読み込み速度のため）
- **命名規則**: 半角英数字、ハイフン、アンダースコアのみ

## 📁 関連ファイル

### 作成したスクリプト
- `update_menu_images.py` - 画像URL一括更新スクリプト
- `verify_image_urls.py` - 画像URL確認スクリプト

### 画像ディレクトリ
- `static/images/menus/` - メニュー画像保存場所
- `static/images/no-image.svg` - 画像がない場合のフォールバック

## ✅ 解決状況

- ✅ データベースの画像URLを実際のファイルパスに更新
- ✅ APIが正しい画像パスを返すことを確認
- ✅ 画像ファイルにアクセスできることを確認
- ✅ ブラウザでの表示確認手順を提供

**問題は完全に解決しました！**

ブラウザでメニュー画面を開くと、実際のお弁当の写真が表示されるようになります。

## 🎯 根本原因

初期データ投入時（`init_data.py`）にプレースホルダーURLを使用していたため、その後画像ファイルを追加してもデータベースが更新されていませんでした。

## 💡 改善提案

1. **初期データスクリプトの更新**
   - `init_data.py`で実際の画像パスを使用するように変更
   
2. **画像アップロード機能の追加**
   - 店舗管理画面からメニュー画像をアップロードできる機能
   - アップロード時に自動でリサイズ・最適化

3. **画像の存在確認**
   - メニュー保存時に画像ファイルの存在をチェック
   - 存在しない場合は警告を表示

---

**対応者**: GitHub Copilot  
**対応日時**: 2025年10月12日
