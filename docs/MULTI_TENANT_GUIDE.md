# マルチテナント機能 完全ガイド

## 📖 目次

- [概要](#概要)
- [アーキテクチャ](#アーキテクチャ)
- [店舗の作成と管理](#店舗の作成と管理)
- [店舗スタッフの管理](#店舗スタッフの管理)
- [API実装ガイドライン](#api実装ガイドライン)
- [セキュリティ](#セキュリティ)
- [トラブルシューティング](#トラブルシューティング)

## 概要

### マルチテナントシステムとは

本システムは**複数の店舗（テナント）が独立してサービスを提供できるマルチテナント設計**です。

#### 主な特徴

| 特徴 | 説明 |
|-----|------|
| **データ分離** | 各店舗のメニュー・注文・売上が物理的に分離 |
| **アクセス制御** | 店舗スタッフは自店舗データのみアクセス可能 |
| **お客様の自由** | お客様は全店舗から自由にメニューを選択・注文可能 |
| **権限管理** | owner / manager / staff の3段階の権限レベル |

### ユースケース

```
【店舗A】弁当屋さん
├── オーナー: 田中さん（全権限）
├── マネージャー: 佐藤さん（メニュー管理・売上閲覧）
└── スタッフ: 鈴木さん（注文確認のみ）

【店舗B】お寿司屋さん
├── オーナー: 山田さん（全権限）
└── スタッフ: 高橋さん（注文確認のみ）

【お客様】
├── 太郎さん → 店舗Aと店舗Bから注文可能
└── 花子さん → 全店舗のメニューを閲覧・注文可能
```

## アーキテクチャ

### データモデル

```
┌─────────────────────────────────────────────┐
│              STORES (店舗)                  │
│  - id (PK)                                  │
│  - name, address, phone, email              │
│  - opening_time, closing_time               │
└─────────────┬───────────────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌────────┐
│ USERS │ │ MENUS │ │ ORDERS │
├───────┤ ├───────┤ ├────────┤
│store_│ │store_│ │store_  │
│  _id  │ │  _id  │ │  _id   │ ← すべてstore_idで分離
└───────┘ └───────┘ └────────┘
```

### アクセス制御フロー

```
┌──────────────┐
│  APIリクエスト │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  JWT認証         │
│  current_user取得│
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  role='store'?   │
└──────┬───────────┘
       │ YES
       ▼
┌──────────────────┐
│ current_user     │
│   .store_id 取得 │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────┐
│  DBクエリにstore_idフィルタ│
│  WHERE store_id = ?      │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────┐
│  自店舗データのみ │
│  を返却          │
└──────────────────┘
```

## 店舗の作成と管理

### 初期セットアップ（開発環境）

#### ステップ1: Docker環境を起動

```bash
# プロジェクトのルートディレクトリで実行
cd bento-order-system

# Dockerコンテナを起動
docker-compose up -d

# データベースマイグレーション
docker-compose run --rm web alembic upgrade head
```

#### ステップ2: 初期データを投入

```bash
# デモユーザー・デモ店舗を作成
docker-compose exec web python init_data.py

# 店舗スタッフと店舗を紐付け
docker-compose exec web python setup_store_data.py
```

**作成される内容:**
- デモ店舗「テスト弁当屋」
- お客様アカウント: customer1
- 店舗オーナー: admin
- 店舗スタッフ: store1
- サンプルメニュー数種類

#### ステップ3: 動作確認

```bash
# ログインしてみる
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin@123"

# レスポンス例
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer",
  "role": "store"
}
```

### 新しい店舗を作成する

#### 方法1: Pythonスクリプト

```python
# create_new_store.py
from database import SessionLocal
from models import Store
from datetime import time

db = SessionLocal()

# 新店舗を作成
new_store = Store(
    name="新規オープン弁当屋",
    email="newstore@example.com",
    phone="03-1111-2222",
    address="東京都渋谷区渋谷1-2-3 渋谷ビル1F",
    opening_time=time(10, 0),   # 10:00
    closing_time=time(21, 0),   # 21:00
    description="新鮮な食材を使った美味しい弁当をご提供します。",
    image_url="https://example.com/store-image.jpg",  # オプション
    is_active=True
)

db.add(new_store)
db.commit()
db.refresh(new_store)

print(f"✅ 店舗作成完了")
print(f"   店舗ID: {new_store.id}")
print(f"   店舗名: {new_store.name}")
print(f"   住所: {new_store.address}")
```

実行:
```bash
docker-compose exec web python create_new_store.py
```

#### 方法2: データベース直接操作

```bash
docker-compose exec db psql -U postgres -d bento_db

# SQL実行
INSERT INTO stores (name, email, phone_number, address, opening_time, closing_time, description, is_active)
VALUES (
  '新規オープン弁当屋',
  'newstore@example.com',
  '03-1111-2222',
  '東京都渋谷区渋谷1-2-3',
  '10:00:00',
  '21:00:00',
  '新鮮な食材を使った美味しい弁当をご提供します。',
  true
);

# 作成した店舗を確認
SELECT id, name, address FROM stores ORDER BY created_at DESC LIMIT 1;
```

### 店舗情報を更新する

#### 方法1: 店舗プロフィールAPI（推奨）

```bash
# 店舗スタッフとしてログイン
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin@123" \
  | jq -r '.access_token')

# 店舗情報を更新（オーナー・マネージャー権限が必要）
curl -X PUT "http://localhost:8000/api/store/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "リニューアルした弁当屋",
    "phone": "03-9999-8888",
    "address": "東京都渋谷区新住所2-3-4",
    "opening_time": "09:00:00",
    "closing_time": "22:00:00",
    "description": "リニューアルオープンしました！新メニュー多数！",
    "image_url": "https://example.com/renewed-store.jpg"
  }'
```

#### 方法2: Pythonスクリプト

```python
# update_store.py
from database import SessionLocal
from models import Store
from datetime import time

db = SessionLocal()

# 更新したい店舗を取得
store = db.query(Store).filter(Store.id == 1).first()

if store:
    # 情報を更新
    store.name = "リニューアルした弁当屋"
    store.phone_number = "03-9999-8888"
    store.address = "東京都渋谷区新住所2-3-4"
    store.opening_time = time(9, 0)
    store.closing_time = time(22, 0)
    store.description = "リニューアルオープンしました！"
    
    db.commit()
    print(f"✅ 店舗情報を更新しました: {store.name}")
else:
    print("❌ 店舗が見つかりません")
```

### 店舗の一覧を確認する

```python
# list_all_stores.py
from database import SessionLocal
from models import Store

db = SessionLocal()
stores = db.query(Store).filter(Store.is_active == True).all()

print(f"登録店舗数: {len(stores)}\n")
print("=" * 80)

for store in stores:
    print(f"店舗ID: {store.id}")
    print(f"店舗名: {store.name}")
    print(f"住所: {store.address}")
    print(f"電話: {store.phone_number}")
    print(f"メール: {store.email}")
    print(f"営業時間: {store.opening_time} - {store.closing_time}")
    print(f"説明: {store.description or '(なし)'}")
    print(f"状態: {'営業中' if store.is_active else '休業中'}")
    print(f"作成日: {store.created_at}")
    print("-" * 80)

db.close()
```

## 店舗スタッフの管理

### 新しいスタッフを追加する

#### ステップ1: ユーザーを作成

```python
# create_staff.py
from database import SessionLocal
from models import User, Role, UserRole
from auth import get_password_hash

db = SessionLocal()

# 新しいスタッフユーザーを作成
new_user = User(
    username="tanaka_staff",
    email="tanaka@example.com",
    hashed_password=get_password_hash("secure_password"),
    role="store",           # 店舗スタッフ
    full_name="田中 太郎",
    store_id=1,             # 所属店舗ID
    is_active=True
)

db.add(new_user)
db.commit()
db.refresh(new_user)

print(f"✅ ユーザー作成完了: {new_user.username} (ID: {new_user.id})")
```

#### ステップ2: 職位を割り当て

```python
# assign_role.py
from database import SessionLocal
from models import User, Role, UserRole

db = SessionLocal()

# ユーザーと職位を取得
user = db.query(User).filter(User.username == "tanaka_staff").first()
role = db.query(Role).filter(Role.name == "staff").first()  # owner, manager, または staff

# 職位を割り当て
user_role = UserRole(
    user_id=user.id,
    role_id=role.id
)
db.add(user_role)
db.commit()

print(f"✅ {user.username} に {role.name} 職位を割り当てました")
```

#### 一括実行スクリプト

```python
# add_new_staff_complete.py
from database import SessionLocal
from models import User, Role, UserRole
from auth import get_password_hash

db = SessionLocal()

# 設定
USERNAME = "tanaka_staff"
EMAIL = "tanaka@example.com"
PASSWORD = "secure_password"
FULL_NAME = "田中 太郎"
STORE_ID = 1
ROLE_NAME = "staff"  # owner, manager, または staff

# ユーザー作成
new_user = User(
    username=USERNAME,
    email=EMAIL,
    hashed_password=get_password_hash(PASSWORD),
    role="store",
    full_name=FULL_NAME,
    store_id=STORE_ID,
    is_active=True
)
db.add(new_user)
db.commit()
db.refresh(new_user)

# 職位割り当て
role = db.query(Role).filter(Role.name == ROLE_NAME).first()
if not role:
    print(f"❌ 職位 '{ROLE_NAME}' が見つかりません")
    exit(1)

user_role = UserRole(user_id=new_user.id, role_id=role.id)
db.add(user_role)
db.commit()

print(f"✅ スタッフ追加完了")
print(f"   ユーザー名: {new_user.username}")
print(f"   氏名: {new_user.full_name}")
print(f"   店舗ID: {new_user.store_id}")
print(f"   職位: {ROLE_NAME}")
print(f"   パスワード: {PASSWORD}")
```

### 既存ユーザーを店舗に紐付ける

```python
# assign_existing_user_to_store.py
from database import SessionLocal
from models import User, Role, UserRole

db = SessionLocal()

# 既存のお客様ユーザーを取得
user = db.query(User).filter(User.username == "customer1").first()

if not user:
    print("❌ ユーザーが見つかりません")
    exit(1)

# 店舗スタッフに変更
user.role = "store"
user.store_id = 1  # 所属店舗ID

# 職位を割り当て
staff_role = db.query(Role).filter(Role.name == "staff").first()
user_role = UserRole(user_id=user.id, role_id=staff_role.id)
db.add(user_role)

db.commit()

print(f"✅ {user.username} を店舗スタッフに変更しました")
print(f"   店舗ID: {user.store_id}")
print(f"   職位: staff")
```

### スタッフの職位を変更する

```python
# change_staff_role.py
from database import SessionLocal
from models import User, Role, UserRole

db = SessionLocal()

# ユーザーを取得
user = db.query(User).filter(User.username == "tanaka_staff").first()

# 現在の職位を削除
db.query(UserRole).filter(UserRole.user_id == user.id).delete()

# 新しい職位を割り当て
new_role = db.query(Role).filter(Role.name == "manager").first()  # staffからmanagerに昇格
user_role = UserRole(user_id=user.id, role_id=new_role.id)
db.add(user_role)

db.commit()

print(f"✅ {user.username} の職位を {new_role.name} に変更しました")
```

### スタッフの一覧を確認する

```python
# list_store_staff.py
from database import SessionLocal
from models import User, Role, UserRole
from sqlalchemy.orm import joinedload

db = SessionLocal()

# 店舗IDを指定
STORE_ID = 1

# 店舗のスタッフを取得
staff_users = db.query(User).filter(
    User.role == "store",
    User.store_id == STORE_ID
).options(joinedload(User.user_roles).joinedload(UserRole.role)).all()

print(f"店舗ID {STORE_ID} のスタッフ一覧\n")
print("=" * 80)

for user in staff_users:
    roles = [ur.role.name for ur in user.user_roles]
    print(f"ユーザー名: {user.username}")
    print(f"氏名: {user.full_name}")
    print(f"メール: {user.email}")
    print(f"職位: {', '.join(roles) if roles else '(未割り当て)'}")
    print(f"状態: {'アクティブ' if user.is_active else '無効'}")
    print("-" * 80)
```

## API実装ガイドライン

### 必須チェックリスト

新しい店舗向けAPIエンドポイントを実装する際は、以下をすべて満たしてください：

- [ ] **1. store_id存在確認**
- [ ] **2. すべてのDBクエリにstore_idフィルタ**
- [ ] **3. データ作成時はサーバー側でstore_id設定**
- [ ] **4. 存在しないリソースは404を返す**
- [ ] **5. データ分離のテストを追加**

### 実装パターン集

#### パターン1: リソース一覧取得

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Menu
from dependencies import require_role

router = APIRouter()

@router.get("/menus")
def get_menus(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """メニュー一覧取得（自店舗のみ）"""
    # ✅ 1. store_id存在確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with any store"
        )
    
    # ✅ 2. store_idでフィルタリング
    menus = db.query(Menu).filter(
        Menu.store_id == current_user.store_id
    ).all()
    
    return menus
```

#### パターン2: リソース作成

```python
@router.post("/menus")
def create_menu(
    menu: MenuCreate,  # Pydanticスキーマ（store_idを含まない）
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """メニュー作成（自動的に自店舗に紐付け）"""
    # ✅ 1. store_id存在確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with any store"
        )
    
    # ✅ 3. サーバー側でstore_id設定
    db_menu = Menu(
        **menu.dict(),
        store_id=current_user.store_id  # クライアントから受け取らない
    )
    
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    
    return db_menu
```

#### パターン3: リソース更新

```python
@router.put("/menus/{menu_id}")
def update_menu(
    menu_id: int,
    menu: MenuUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """メニュー更新（自店舗データのみ）"""
    # ✅ 1. store_id存在確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with any store"
        )
    
    # ✅ 2. store_idでフィルタリング
    db_menu = db.query(Menu).filter(
        Menu.id == menu_id,
        Menu.store_id == current_user.store_id  # 必須
    ).first()
    
    # ✅ 4. 存在しない場合は404
    if not db_menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    # 更新処理
    for key, value in menu.dict(exclude_unset=True).items():
        setattr(db_menu, key, value)
    
    db.commit()
    db.refresh(db_menu)
    
    return db_menu
```

#### パターン4: リソース削除

```python
@router.delete("/menus/{menu_id}")
def delete_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner']))  # オーナーのみ
):
    """メニュー削除（自店舗データのみ）"""
    # ✅ 1. store_id存在確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with any store"
        )
    
    # ✅ 2. store_idでフィルタリング
    db_menu = db.query(Menu).filter(
        Menu.id == menu_id,
        Menu.store_id == current_user.store_id
    ).first()
    
    # ✅ 4. 存在しない場合は404
    if not db_menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    db.delete(db_menu)
    db.commit()
    
    return {"message": "Menu deleted successfully"}
```

#### パターン5: 集計クエリ

```python
from sqlalchemy import func

@router.get("/reports/sales")
def get_sales_report(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """売上レポート取得（自店舗のみ）"""
    # ✅ 1. store_id存在確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with any store"
        )
    
    # ✅ 2. すべての集計クエリにstore_idフィルタ
    
    # 日別売上
    daily_sales = db.query(
        func.date(Order.ordered_at).label('date'),
        func.sum(Order.total_price).label('total')
    ).filter(
        Order.store_id == current_user.store_id,  # 必須
        Order.ordered_at >= start_date,
        Order.ordered_at <= end_date,
        Order.status != 'cancelled'
    ).group_by(func.date(Order.ordered_at)).all()
    
    # 合計売上
    total_sales = db.query(
        func.sum(Order.total_price)
    ).filter(
        Order.store_id == current_user.store_id,  # 必須
        Order.ordered_at >= start_date,
        Order.ordered_at <= end_date,
        Order.status != 'cancelled'
    ).scalar() or 0
    
    # 人気メニュー
    popular_menus = db.query(
        Menu.name,
        func.count(Order.id).label('order_count')
    ).join(Order).filter(
        Order.store_id == current_user.store_id,  # 必須
        Order.ordered_at >= start_date,
        Order.ordered_at <= end_date,
        Order.status != 'cancelled'
    ).group_by(Menu.name).order_by(
        func.count(Order.id).desc()
    ).limit(10).all()
    
    return {
        "daily_sales": daily_sales,
        "total_sales": total_sales,
        "popular_menus": popular_menus
    }
```

### テストコード例

```python
# tests/test_menu_isolation.py
import pytest
from fastapi.testclient import TestClient

def test_store_a_cannot_access_store_b_menu(
    client: TestClient,
    auth_headers_store_a,  # 店舗Aのスタッフ
    menu_store_b           # 店舗Bのメニュー
):
    """店舗Aのスタッフが店舗Bのメニューにアクセスできないこと"""
    # ✅ 5. データ分離のテスト
    
    # 店舗Bのメニューを取得しようとする
    response = client.get(
        f"/api/store/menus/{menu_store_b.id}",
        headers=auth_headers_store_a
    )
    
    # 404が返ることを確認（403ではなく）
    assert response.status_code == 404
    assert response.json()["detail"] == "Menu not found"

def test_menu_list_contains_only_own_store(
    client: TestClient,
    auth_headers_store_a,
    menu_store_a,
    menu_store_b
):
    """メニュー一覧に自店舗のメニューのみ含まれること"""
    response = client.get(
        "/api/store/menus",
        headers=auth_headers_store_a
    )
    
    assert response.status_code == 200
    menus = response.json()
    
    # 店舗Aのメニューが含まれている
    menu_ids = [m["id"] for m in menus]
    assert menu_store_a.id in menu_ids
    
    # 店舗Bのメニューは含まれていない
    assert menu_store_b.id not in menu_ids
```

## セキュリティ

### セキュリティチェックリスト

- [ ] すべての店舗向けエンドポイントで認証を要求
- [ ] すべてのDBクエリに`store_id`フィルタを追加
- [ ] データ作成時は`current_user.store_id`を使用（クライアントから受け取らない）
- [ ] 存在しないリソースは404を返す（403は使わない）
- [ ] エラーメッセージに機密情報を含めない
- [ ] 集計クエリも`store_id`でフィルタリング
- [ ] JOINを使う場合も`store_id`フィルタを忘れない

### セキュリティテストの実行

```bash
# マルチテナントセキュリティテストを実行
docker-compose exec web pytest tests/test_store_isolation.py -v

# 全テスト結果
# ✅ test_store_a_cannot_get_store_b_order_status
# ✅ test_store_b_cannot_get_store_a_order_status
# ✅ test_order_list_contains_only_own_store_orders
# ✅ test_order_list_isolation_with_multiple_orders
# ✅ test_store_a_cannot_update_store_b_menu
# ✅ test_store_b_cannot_delete_store_a_menu
# ✅ test_menu_list_contains_only_own_store_menus
# ✅ test_created_menu_has_correct_store_id
# ✅ test_dashboard_shows_only_own_store_data
# ✅ test_sales_report_contains_only_own_store_data
# ✅ test_manager_cannot_access_other_store_data
# ✅ test_staff_cannot_access_other_store_data
# ✅ test_no_data_leakage_in_error_messages

# 13 passed, 0 failed ✅
```

詳細なレポート:
- [セキュリティテストレポート](SECURITY_TEST_REPORT_MULTI_TENANT.md)
- [セキュリティ修正完了レポート](SECURITY_FIX_COMPLETE_REPORT.md)

## トラブルシューティング

### よくある問題と解決方法

#### Q1: 店舗スタッフがログインできるが、APIがエラーを返す

**症状:**
```json
{
  "detail": "User is not associated with any store"
}
```

**原因:** ユーザーの`store_id`が設定されていない

**解決方法:**
```bash
# ユーザーのstore_idを確認
docker-compose exec db psql -U postgres -d bento_db -c \
  "SELECT id, username, role, store_id FROM users WHERE username='your_username';"

# store_idがNULLの場合、設定する
docker-compose exec web python -c "
from database import SessionLocal
from models import User
db = SessionLocal()
user = db.query(User).filter(User.username == 'your_username').first()
user.store_id = 1  # 店舗ID
db.commit()
print(f'✅ {user.username} を店舗ID {user.store_id} に紐付けました')
"
```

#### Q2: 店舗スタッフに職位（role）が割り当てられていない

**症状:**
```json
{
  "detail": "Insufficient permissions"
}
```

**原因:** user_rolesテーブルに職位が登録されていない

**解決方法:**
```bash
# 職位を確認
docker-compose exec web python -c "
from database import SessionLocal
from models import User, Role, UserRole
db = SessionLocal()
user = db.query(User).filter(User.username == 'your_username').first()
roles = db.query(Role).join(UserRole).filter(UserRole.user_id == user.id).all()
print(f'ユーザー: {user.username}')
print(f'職位: {[r.name for r in roles]}')
"

# 職位を割り当て
docker-compose exec web python -c "
from database import SessionLocal
from models import User, Role, UserRole
db = SessionLocal()
user = db.query(User).filter(User.username == 'your_username').first()
role = db.query(Role).filter(Role.name == 'staff').first()
user_role = UserRole(user_id=user.id, role_id=role.id)
db.add(user_role)
db.commit()
print(f'✅ {user.username} に {role.name} を割り当てました')
"
```

#### Q3: 他店舗のデータにアクセスできてしまう（セキュリティ脆弱性）

**症状:** テストが失敗する

**原因:** エンドポイントに`store_id`フィルタが実装されていない

**解決方法:**

1. セキュリティテストを実行して問題箇所を特定:
```bash
docker-compose exec web pytest tests/test_store_isolation.py -v
```

2. 失敗したテストに対応するエンドポイントのコードを確認

3. `store_id`フィルタを追加:
```python
# ❌ 修正前
orders = db.query(Order).all()

# ✅ 修正後
orders = db.query(Order).filter(
    Order.store_id == current_user.store_id
).all()
```

4. テストを再実行して確認:
```bash
docker-compose exec web pytest tests/test_store_isolation.py -v
```

#### Q4: メニュー作成時に422エラーが発生する

**症状:**
```json
{
  "detail": [
    {
      "loc": ["body", "store_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**原因:** Pydanticスキーマに`store_id`が含まれている

**解決方法:**

schemas.pyを修正:
```python
# ❌ 修正前
class MenuCreate(BaseModel):
    name: str
    price: int
    description: Optional[str] = None
    store_id: int  # クライアントが指定（危険）

# ✅ 修正後
class MenuCreate(BaseModel):
    name: str
    price: int
    description: Optional[str] = None
    # store_idは削除（サーバー側で自動設定）
```

エンドポイントでサーバー側で設定:
```python
db_menu = Menu(
    **menu.dict(),
    store_id=current_user.store_id  # サーバー側で設定
)
```

#### Q5: 売上レポートに他店舗のデータが混在している

**症状:** 売上金額が異常に大きい

**原因:** 集計クエリに`store_id`フィルタが抜けている

**解決方法:**

すべての集計クエリに`store_id`フィルタを追加:
```python
# ❌ 修正前
total_sales = db.query(func.sum(Order.total_price)).filter(
    Order.ordered_at >= start_date,
    Order.ordered_at <= end_date
).scalar()

# ✅ 修正後
total_sales = db.query(func.sum(Order.total_price)).filter(
    Order.store_id == current_user.store_id,  # 追加
    Order.ordered_at >= start_date,
    Order.ordered_at <= end_date
).scalar()
```

## 参考資料

- [README.md](../README.md) - プロジェクト全体の説明
- [ER_DIAGRAM.md](ER_DIAGRAM.md) - データベース設計詳細
- [SECURITY_FIX_COMPLETE_REPORT.md](SECURITY_FIX_COMPLETE_REPORT.md) - セキュリティ修正レポート
- [SECURITY_TEST_REPORT_MULTI_TENANT.md](SECURITY_TEST_REPORT_MULTI_TENANT.md) - セキュリティテスト詳細

---

**作成日:** 2025年10月12日  
**最終更新:** 2025年10月12日  
**バージョン:** 1.0
