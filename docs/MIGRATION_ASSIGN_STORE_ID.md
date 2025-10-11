# データ移行マイグレーション - 既存データへの店舗ID割り当て

## 概要

このマイグレーションは、マルチテナント化に伴い、既存の`menus`, `orders`, `users`データにデフォルトの店舗IDを割り当てるものです。

## 実施内容

### 1. Storeテーブルの作成
- 店舗情報を管理する`stores`テーブルを新規作成
- 営業時間、住所、連絡先などの店舗基本情報を格納

### 2. デフォルト店舗の作成
- 店舗名: **「本店」**
- 住所: 東京都渋谷区サンプル1-2-3
- 電話: 03-1234-5678
- メール: honten@bento.com
- 営業時間: 9:00 - 20:00

### 3. 既存データへの店舗ID設定

#### Users テーブル
- `store_id`カラムを追加(nullable, 外部キー制約: SET NULL)
- `role = 'store'`の既存ユーザーに店舗ID = 1 を設定

#### Menus テーブル
- `store_id`カラムを追加(NOT NULL, 外部キー制約: CASCADE)
- 既存の全メニューに店舗ID = 1 を設定

#### Orders テーブル
- `store_id`カラムを追加(NOT NULL, 外部キー制約: CASCADE)
- 既存の全注文に店舗ID = 1 を設定

## マイグレーション実行手順

### 前提条件
```bash
# Python仮想環境がアクティブであること
# 必要なパッケージがインストールされていること
pip install alembic sqlalchemy
```

### 実行コマンド

1. **現在のマイグレーション状態を確認**
```bash
python -m alembic current
```

2. **マイグレーションを実行**
```bash
python -m alembic upgrade head
```

3. **実行結果の確認**
```bash
# データベースに接続して確認
python
>>> from database import SessionLocal
>>> from models import Store, User, Menu, Order
>>> db = SessionLocal()
>>> 
>>> # 店舗が作成されたことを確認
>>> store = db.query(Store).first()
>>> print(f"Store: {store.name}, ID: {store.id}")
>>> 
>>> # メニューに店舗IDが設定されたことを確認
>>> menus = db.query(Menu).all()
>>> print(f"Total menus: {len(menus)}, All have store_id: {all(m.store_id for m in menus)}")
>>> 
>>> # 注文に店舗IDが設定されたことを確認
>>> orders = db.query(Order).all()
>>> print(f"Total orders: {len(orders)}, All have store_id: {all(o.store_id for o in orders)}")
>>> 
>>> # 店舗スタッフに店舗IDが設定されたことを確認
>>> store_users = db.query(User).filter(User.role == 'store').all()
>>> print(f"Store staff: {len(store_users)}, All have store_id: {all(u.store_id for u in store_users)}")
>>> 
>>> db.close()
```

## ロールバック手順

万が一問題が発生した場合:

```bash
# 1つ前のマイグレーションに戻す
python -m alembic downgrade -1
```

## init_data.py の更新内容

新規データ生成時にも店舗IDが自動的に設定されるよう、`init_data.py`を更新しました:

- デフォルト店舗を最初に作成
- メニュー、ユーザー、注文すべてに`store_id`を設定

### 使用方法

```bash
# データベースを初期化してテストデータを投入
python init_data.py
```

## 検証項目

マイグレーション後、以下を確認してください:

- [ ] `stores`テーブルにデフォルト店舗(ID=1)が作成されている
- [ ] すべての`menus`レコードに`store_id = 1`が設定されている
- [ ] すべての`orders`レコードに`store_id = 1`が設定されている
- [ ] `role = 'store'`の`users`レコードに`store_id = 1`が設定されている
- [ ] 既存のアプリケーション機能(ログイン、注文など)が正常に動作する
- [ ] `init_data.py`で新しいテストデータを生成できる

## トラブルシューティング

### エラー: "table stores already exists"

既にstoresテーブルが存在する場合:

```bash
# マイグレーション履歴を確認
python -m alembic history

# 必要に応じて、マイグレーションバージョンを手動設定
python -m alembic stamp head
```

### エラー: "foreign key constraint fails"

外部キー制約エラーが発生した場合:

1. データベースの整合性を確認
2. 既存データに不正なレコードがないか確認
3. 必要に応じてデータをクリーンアップしてから再実行

## 関連ファイル

- `alembic/versions/assign_default_store_id_to_existing_data.py` - マイグレーションスクリプト
- `models.py` - Store, User, Menu, Order モデル定義(store_id追加済み)
- `init_data.py` - テストデータ生成スクリプト(店舗ID対応済み)

## 次のステップ

このマイグレーション完了後:

1. 店舗プロフィールAPIが正常に動作することを確認
2. E2Eテストを実行して全機能の動作を検証
3. 必要に応じて追加の店舗を作成
4. ユーザーと店舗の紐付けを更新
